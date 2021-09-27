
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from datetime import date, datetime, timedelta
from bson.objectid import ObjectId
from time import sleep
import numpy as np
import pickle
import cv2

from pymongo import UpdateOne

from defom.db import get_all_forest_tiles, save_forestTile, get_forest_ids, get_latest_forest_tiles, forestTile_bulkWrite, forests_bulkWrite, get_all_forests_tile_details, get_forests_pred_bnd, get_forest_tile_inf, get_tile_view_id, forestPage_bulkWrite, add_user_name
from defom.src.SentinelhubClient import SentilhubClient
from defom.src.DLClient import ClassiModel, MaskModel

import logging

logging.basicConfig()
logger = logging.getLogger('apscheduler')
logger.setLevel(logging.DEBUG)

CLASS_INPUT_SHAPE = (241, 242)
MASK_INPUT_SHAPE = (128, 128)

sched = BlockingScheduler()


def class_inf(image_list):
    try:
        np_image_list = np.array(image_list)

        class_model = ClassiModel.getInstance()
        inferences = class_model.inference(np_image_list)
        return inferences
    except Exception as e:
        return e

def set_forest_view(acceptable_forests, start_date, end_date):
    today = datetime.combine(date.today(), datetime.min.time())
    sentinel_client = SentilhubClient()
    try:
        forests = get_forests_pred_bnd()
        update_requests = []
        for forest in forests:
            forest_id = forest['_id']
            forest_boundary = forest['boundary']
            updatable = forest_id in acceptable_forests
            if updatable:
                forest_view = sentinel_client.get_forest(forest_boundary, start_date, end_date)
                preprocessed_view = np.clip(forest_view* 3.5/255, 0,1)
                bin_image = pickle.dumps(preprocessed_view)
                update_requests.append(UpdateOne({'_id' : forest_id}, {'$set' : {'entire_forest_view' : bin_image, 'forest_view_updated_date' : today}}))

        forestPage_bulkWrite(update_requests)
    except Exception as e:
            return print(e)

def input_creator(image1, image2):
    image1_ch1, image2_ch1 = image1[:, :, 0], image2[:, :, 0]
    image1_ch1, image2_ch1 = image1_ch1[np.newaxis, ...], image2_ch1[np.newaxis, ...]
    inf_img = np.vstack((image1_ch1, image2_ch1))
    inf_img = np.moveaxis(inf_img, (0,1,2), (2,0,1))
    return inf_img

## daily satellite feed extraction
@sched.scheduled_job('cron', hour=9, minute=56, name="get_forest_tiles")
def save_tiles_daily():
    dict_list = get_all_forest_tiles()
    sentinel_client = SentilhubClient()    ## Init sentinelHUb invoker
    threat_list = ['agriculture', 'cultivation', 'habitation', 'road', 'water']
    mask_model = MaskModel.getInstance()    ## Init mask classification model

    ## define date details 
    today = date.today()
    end_date = today - timedelta(days=1)
    start_date = today - timedelta(days=2)

    today_dt = datetime.combine(today, datetime.min.time())
    end_date_dt = datetime.combine(end_date, datetime.min.time())

    all_documents = []     ## list of all the forestTiles documents 
    updatable_forests = []  ## forest list with threat detected
    for doc in dict_list:  ## run over all the forests in the db
        documents = []
        try:
            ## extract single forest details
            forest_id = doc['forest_id']
            forest_tile_list = doc['tile_list']
            forest_status = doc['status']
            image_list = []

            ## create ForestTile raw document for all the tiles in forest
            for tile in forest_tile_list:
                tile_id = tile['tile_id']
                coords = tile['bbox']

                try:
                    ## get forest tile satellite image of yesterday.
                    s_image = sentinel_client.get_tile(coords, 10, start_date, end_date)[0]
                    sat_image = s_image[:,:,:5]
                    image_list.append(sat_image[:,:,:3])
                    ## binarize forest image to send in json request
                    binary_image = pickle.dumps(sat_image)
                except Exception as e:
                    return print(e)

                ## compose data into document
                forest_tile = {
                "_id" : ObjectId(),
                "forest_id" : forest_id,
                "tile_id" : tile_id,
                "image" : binary_image, 
                "raw_image" : sat_image,
                "image_shape" : sat_image.shape,
                "save_time" : today_dt,
                }
                documents.append(forest_tile)
            logger.info(f"[SAVE FOREST TILES] | forest_id : {forest_id}, num of forest tiles : {len(forest_tile_list)}")

            try:
                ## get classification inference result on forest tiles
                inferences  = class_inf(image_list)
                for i, doc in enumerate(documents):
                    ## add infer. to forestTile documents 
                    doc['class_infered'] = inferences[i]

                logger.info(f"[INFERENCE FOREST TILES] | forest_id : {forest_id}, num of forest tiles : {len(inferences)}")
            except Exception as e:
                return print(e)
                # logger.error(e)

            
            try:
                ## Init bulk-request list and data passing dictionary
                update_requests_1 = []
                masking_tiles = {'tile_id' : [], 'tile_image' : []}
                view_collectable = False

                if forest_status != "new":
                    ## get last forest tile view in the system
                    forest_tile_today_pred = get_latest_forest_tiles(forest_id, end_date_dt, 2)
                    for doc in documents:
                        ## find new threat type in the today forest tile
                        cur_threat = set(doc['class_infered'])
                        latest_threat = set(forest_tile_today_pred[doc['tile_id']]['res'])
                        diff_threat = list(latest_threat - cur_threat)
                        valid_threat = [x for x in diff_threat if x in threat_list]
                        if valid_threat != []:
                            ## if there are new threat set forest into entire view updatable list
                            view_collectable = True
                            ## add new threat to forestTile doc.
                            doc['infered_threat_present'] = valid_threat
                            ## update data-passing dict.
                            masking_tiles['tile_id'].append(doc['tile_id'])
                            masking_tiles['tile_image'].append(doc['raw_image'])
                            ## create update query to forest on new tile 
                            query = UpdateOne({'_id': doc['forest_id'], 'forest_tiles.tile_id':doc['tile_id']}, {'$set' : {'forest_tiles.$.infered_threat_present' : True, 'forest_tiles.$.inference_updated_date' : today_dt, 'forest_tiles.$.update_view_id': doc['_id']}})
                            update_requests_1.append(query) 
                        else:
                            query = UpdateOne({'_id': doc['forest_id'], 'forest_tiles.tile_id':doc['tile_id']}, {'$set' : {'forest_tiles.$.infered_threat_present' : False}})
                            update_requests_1.append(query) 
                else:
                    ## if forest is new then update all the forest tile reference and set into entire view updatable list
                    view_collectable = True
                    update_requests_1.append(UpdateOne({'_id': doc['forest_id']}, {'$set' : {'status' : "active"}}))
                    for doc in documents:
                        query = UpdateOne({'_id': doc['forest_id'], 'forest_tiles.tile_id':doc['tile_id']}, {'$set' : {'forest_tiles.$.infered_threat_present' : True, 'forest_tiles.$.inference_updated_date' : today_dt, 'forest_tiles.$.update_view_id': doc['_id']}})
                        update_requests_1.append(query)  

                if view_collectable:
                    updatable_forests.append(forest_id)
                logger.info(f"[FOREST VIEW REFERENCE UPDATE] | forest_id : {forest_id}, num of forest tiles : {len(update_requests_1)}")
            except Exception as e:
                return print(e)
                # logger.error(e)


            try:
                if (forest_status != "new") and (masking_tiles['tile_id'] != []):
                    ## take updatable forest tiles from data-passing dict.
                    accessing_tiles = masking_tiles['tile_id']
                    ## take yesterday forest view
                    acc_ys_tiles = get_tile_view_id(forest_id, accessing_tiles, end_date_dt)
                    # logger.info(f"masking_tiles {masking_tiles}")
                    image_td_dict = {}
                    for i, iid in enumerate(masking_tiles['tile_id']):
                        image_td_dict[iid] = masking_tiles['tile_image'][i]
                    # logger.info(f"image_td_dict {image_td_dict}")
                    # image_id_td_dict = {}
                    # for tile in acc_td_tiles:
                    #     image_id_td_dict[tile['tile_id']] = pickle.loads(tile['_id'])

                    ## load images from json
                    image_ys_dict = {}
                    for tile in acc_ys_tiles:
                        image_ys_dict[tile['tile_id']] = pickle.loads(tile['image'])
                    # logger.info(f"image_ys_dict : {image_ys_dict}")

                    inf_image_dict = {}
                    for i in image_td_dict:
                        inf_image_dict[i] = input_creator(image_td_dict[i], image_ys_dict[i])
                    # logger.info(f"inf_image_dict : {inf_image_dict}")

                    # rgb_inf_images = [get_RGB(im)[:,:,1] for im in list(inf_image_dict.values())]      
                    inf_images = np.array([img for i,img in inf_image_dict.items()])
                    # logger.info(f"get single channel inputs : {inf_images.shape}")
                    ## get segmentation model inference results
                    
                    mask_inferences = mask_model.inference(inf_images)
                    # logger.info(f"get inference : {mask_inferences.shape}")

                    j = 0
                    for doc in documents:
                        if doc['tile_id'] in accessing_tiles:
                            ## update forestTile doc. by mask
                            doc['mask'] = pickle.dumps(mask_inferences[j,...])
                            doc['mask_present'] = True
                            j+=1
                        else:
                            doc['mask_present'] = False
                            
                    logger.info(f"[INFERENCE FOREST MASK] | forest_id : {forest_id}, num of forest tiles : {len(mask_inferences)}")
                else:
                    for doc in documents:
                        doc['mask_present'] = False

                    logger.info(f"[INFERENCE FOREST MASK] | forest_id : {forest_id}, is new.")
            except Exception as e:
                return print(e)
                # logger.error(e)

            try:
                for doc in documents:
                    doc.pop('raw_image', None)

                all_documents.extend(documents)
            except Exception as e:
                return print(e)

        except Exception as e:
            return print(e)
       
    try:
        ## insert all the today forestTile doc. to db
        result = save_forestTile(documents)
        logger.info(f"[WRITE FOREST TILES] | forest_id : {forest_id}")
        ## update forests on todays results
        forests_bulkWrite(update_requests_1)
        logger.info(f"[UPDATE FOREST DETAIL] | forest_id : {forest_id}")
        ## set new forest view in forestPage Collection
        set_forest_view(updatable_forests, end_date_dt, today_dt)
        logger.info(f"[SET FOREST VIEW] | forest_id : {forest_id}")
    except Exception as e:
        return print(e)

def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')


sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    

if __name__ == '__main__':
    sched.start()
