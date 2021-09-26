
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


def get_RGB(image):
    rgb = cv2.normalize(image[:,:,[2,1,0]], None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    return rgb

def resize(image, size=(242,242)):
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)

def class_inf(image_list):
    try:
        image_list = [get_RGB(im) for im in image_list]
        image_list = [resize(img) for img in image_list]
        np_image_list = np.array(image_list)/255

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
@sched.scheduled_job('cron', hour=21, minute=47, name="get_forest_tiles")
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

    documents = []     ## list of all the forestTiles documents 
    updatable_forests = []  ## forest list with threat detected
    for doc in dict_list:  ## run over all the forests in the db
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
                    image_list.append(sat_image)
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
                    forest_tile_today_pred = get_latest_forest_tiles(forest_id, end_date)
                    for doc in documents:
                        ## find new threat type in the today forest tile
                        cur_threat = set(doc['class_infered'])
                        latest_threat = set(forest_tile_today_pred[tile['tile_id']]['res'])
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
                if forest_status != "new":
                ## take updatable forest tiles from data-passing dict.
                    accessing_tiles = masking_tiles['tile_id']
                    ## take yesterday forest view
                    acc_ys_tiles = get_tile_view_id(forest_id, accessing_tiles, end_date_dt)

                    image_td_dict = {}
                    for i, iid in enumerate(masking_tiles['tile_id']):
                        image_td_dict[iid] = masking_tiles['tile_image'][i]
                    logger.info(f"image_td_dict {image_td_dict}")
                    # image_id_td_dict = {}
                    # for tile in acc_td_tiles:
                    #     image_id_td_dict[tile['tile_id']] = pickle.loads(tile['_id'])

                    ## load images from json
                    image_ys_dict = {}
                    for tile in acc_ys_tiles:
                        image_ys_dict[tile['tile_id']] = pickle.loads(tile['image'])
                    logger.info(f"image_ys_dict : {image_ys_dict}")
                    inf_image_dict = {}
                    for i in image_td_dict:
                        inf_image_dict[i] = input_creator(image_td_dict[i][...,1], image_ys_dict[i][...,1])
                    logger.info(f"image_ys_dict : {image_ys_dict}")
                    # rgb_inf_images = [get_RGB(im)[:,:,1] for im in list(inf_image_dict.values())]      
                    inf_images = np.array(inf_image_dict.values())
                    logger.info(f"get single channel inputs : {inf_images.shape}")
                    ## get segmentation model inference results
                    inferences = mask_model.inference(inf_images)
                    logger.info(f"get inference : {inferences.shape}")
                    j = 0
                    for doc in documents:
                        if doc['tile_id'] in accessing_tiles:
                            ## update forestTile doc. by mask
                            doc['mask'] = inferences[j,...]
                            j+=1
                            
                    logger.info(f"[INFERENCE FOREST MASK] | forest_id : {forest_id}, num of forest tiles : {len(inferences)}")
                else:
                    logger.info(f"[INFERENCE FOREST MASK] | forest_id : {forest_id}, is new.")
            except Exception as e:
                return print(e)
                # logger.error(e)

            try:
                for doc in documents:
                    doc.pop('raw_image', None)
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

## daily threat type inference on latest collected data
# @sched.scheduled_job('interval', days=1, name="forest_threat_detection")
def make_class_inf_daily():
    yesterday = datetime.combine(date.today()-timedelta(days=1), datetime.min.time())

    try:
        forests = get_forest_ids()
        for id in forests:
            image_id_list, inferences = class_inf(id, yesterday)

            update_requests = []
            for i in range(len(image_id_list)):
                query = UpdateOne({'_id': image_id_list[i]}, {'$set' : {'classification_result' : inferences[i], 'status' : 'class_inf'}})
                update_requests.append(query)

            logger.info(f"[INFERENCE FOREST TILES] | forest_id : {id}, num of forest tiles : {len(image_id_list)}")
            forestTile_bulkWrite(update_requests)
    except Exception as e:
           return print(e)

## daily update threat type on forest tiles
# @sched.scheduled_job('interval', days=1, name="define_new_forest_threats")
def set_latest_threat_daily():
    threat_list = ['agriculture', 'cultivation', 'habitation', 'road', 'water']
    today = datetime.combine(date.today(), datetime.min.time())
    # yesterday = datetime.combine(date.today()-timedelta(days=1), datetime.min.time())

    try:
        forests = get_all_forests_tile_details()
        for forest in forests:
            forest_id = forest['_id']
            forest_tiles = forest['forest_tiles']

            forest_tile_today_pred = get_latest_forest_tiles(forest_id, today)

            updated_threat_dict = {}
            for tile in forest_tiles:
                cur_threat = set(tile['infered_threat_class'])
                latest_threat = set(forest_tile_today_pred[tile['tile_id']]['res'])
                diff_threat = list(latest_threat - cur_threat)
                valid_threat = [x for x in diff_threat if x in threat_list]
                if valid_threat != []:
                    updated_threat_dict[tile['tile_id']] = {'threat' : valid_threat, 'id': forest_tile_today_pred[tile['tile_id']]['id']}

            update_requests = []
            update_requests_ft = []
            for i in updated_threat_dict:
                query = UpdateOne({'_id': forest_id, 'forest_tiles.tile_id':i}, {'$set' : {'forest_tiles.$.infered_threat_present' : True, 'inference_updated_date' : today, 'update_view_id': updated_threat_dict[i]['id']}})
                update_requests.append(query)
                query = UpdateOne({'_id': updated_threat_dict[i]['id']}, {'$set' : {'new_threat' : updated_threat_dict[i]['threat'], 'inference_updated_date' : today}})
                update_requests_ft.append(query)

            forests_bulkWrite(update_requests)
            forestTile_bulkWrite(update_requests_ft)
    except Exception as e:
            return print(e)
    
## set entire forest view if any new threat appears
# @sched.scheduled_job('interval', days=1, name="set_latest_forest_view")


## daily threat location mask prediction and update in forest documents



# @sched.scheduled_job('interval', days=1, name="generate_forest_masks")
def set_mask_daily():
    today = datetime.combine(date.today(), datetime.min.time())
    yesterday = datetime.combine(date.today()-timedelta(days=1), datetime.min.time())
    mask_model = MaskModel.getInstance()

    try:
        forests = get_forest_tile_inf()
        for forest in forests:
            forest_id = forest['_id']
            accessing_tiles = [x['tile_id'] for x in forest['forest_tiles'] if x['infered_threat_class'] != []]

            acc_td_tiles = get_tile_view_id(forest_id, accessing_tiles, today)
            acc_ys_tiles = get_tile_view_id(forest_id, accessing_tiles, yesterday)

            image_td_dict = {}
            for tile in acc_td_tiles:
                image_td_dict[tile['tile_id']] = pickle.loads(tile['image'])

            image_id_td_dict = {}
            for tile in acc_td_tiles:
                image_id_td_dict[tile['tile_id']] = pickle.loads(tile['_id'])

            image_ys_dict = {}
            for tile in acc_ys_tiles:
                image_ys_dict[tile['tile_id']] = pickle.loads(tile['image'])

            inf_image_dict = {}
            for i in image_td_dict:
                inf_image_dict[i] = input_creator(image_td_dict[i], image_ys_dict[i])

            rgb_inf_images = [get_RGB(im)[:,:,1] for im in list(inf_image_dict.values())]      
            inf_images = np.array(rgb_inf_images)

            inferences = mask_model.inference(inf_images)

            tile_ids = list(image_td_dict.keys())

            update_requests = []
            for i, id in enumerate(tile_ids):
                query = UpdateOne({'_id': image_id_td_dict[i]}, {'$set' : {'forest_tiles.$.infered_mask' : pickle.dumps(inferences[i, ...]), "mask_update_date": today}})
                update_requests.append(query)

            forestTile_bulkWrite(update_requests)
    except Exception as e:
            return print(e)

# @sched.scheduled_job('cron', name="job_1", second=50)
# def timed_job1():
#     # add_user_name()
#     sleep(10)
#     logger.info("JOB-1 is working..")


# @sched.scheduled_job('interval', name="job_2", seconds=30)
# def timed_job2():
#     # add_user_name()
#     sleep(20)
#     logger.info("JOB-2 is working..")

# @sched.scheduled_job('interval', name="job_3", seconds=30)
# def timed_job3():
#     # add_user_name()
#     sleep(30)
#     logger.info("JOB-3 is working..")

def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')

def execution_listener(event):
    job_list = ["get_forest_tiles", "forest_threat_detection", "define_new_forest_threats", "set_latest_forest_view", "generate_forest_masks"]
    job = sched.get_job(event.job_id)
    jobs = sched.get_jobs()
    if event.exception:
        logging.warning(f"the {job.name} crashed..")
    else:
        logging.info(f"the {job.name} executed successfully..")
        job_ind = job_list.index(job.name)
        if job_ind != len(job_list)-1 :
            next_job_name = job_list[job_ind+1]
            next_job = next((j for j in jobs if j.name == next_job_name), None)
            if next_job:
                next_job.modify(next_run_time=datetime.utcnow())
            else:
                logger.warning(f" the Job name {next_job_name} not found in scheduled jobs..")


# sched.add_listener(execution_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
sched.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    

# if __name__ == '__main__':
#     scheduler = BlockingScheduler()
#     scheduler.add_job(func=save_tiles_daily, trigger="cron", hour='10-11')
#     scheduler.add_job(func=make_class_inf_daily, trigger="cron", hour='11-12')
#     scheduler.add_job(func=set_latest_threat_daily, trigger="cron", hour='12-13')
#     scheduler.add_job(func=set_forest_view, trigger="cron", hour='13-14')
#     scheduler.add_job(func=set_mask_daily, trigger="cron", hour='14-15')
#     scheduler.add_job(func=timed_job, trigger='interval', seconds=10)
#     scheduler.start()

if __name__ == '__main__':
    sched.start()
