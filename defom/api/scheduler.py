
from flask import make_response, request, jsonify
from flask_restful import Resource


from datetime import date, datetime, timedelta
import numpy as np
import pickle

from pymongo import UpdateOne

from defom.db import (get_all_forest_tiles, save_forestTile, 
get_forest_ids, get_latest_forest_tiles, forestTile_bulkWrite, 
forests_bulkWrite, get_all_forests_tile_details, get_forests_pred_bnd, 
get_forest_tile_inf, get_tile_view_id, forestPage_bulkWrite, get_tile_all_details)
from defom.src.SentinelhubClient import SentilhubClient
from defom.src.DLClient import ClassiModel, MaskModel

## REST access point to test daily satellite feed extraction
class GetTiles(Resource):

    def get(self):
        dict_list = get_all_forest_tiles()
        sentinel_client = SentilhubClient()

        today = date.today()
        end_date = today - timedelta(days=1)
        start_date = today - timedelta(days=2)

        documents = []
        for doc in dict_list:
            try:
                forest_id = doc['forest_id']
                forest_tile_list = doc['tile_list']
                for tile in forest_tile_list:
                    tile_id = tile['tile_id']
                    coords = tile['bbox']

                    try:
                        sat_image = sentinel_client.get_tile(coords, 10, start_date, end_date)
                        preprocessed_image = np.clip(sat_image[0]*3.5/255, 0,1)
                        binary_image = pickle.dumps(preprocessed_image)
                    except Exception as e:
                        return make_response(jsonify({'error': str(e)}), 400)

                    forest_tile = {
                    "forest_id" : forest_id,
                    "tile_id" : tile_id,
                    "image" : binary_image, 
                    "image_shape" : sat_image[0].shape,
                    "save_time" : datetime.combine(today, datetime.min.time())
                    }
                    documents.append(forest_tile)
            except Exception as e:
                return make_response(jsonify({'error': str(e)}), 400)
        try:
            # TODO : to output actual result as json response
            result = save_forestTile(documents)
            return {"status" : 'OKay'}
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

## daily satellite feed extraction
def save_tiles_daily():
    dict_list = get_all_forest_tiles()
    sentinel_client = SentilhubClient()

    today = date.today()
    end_date = today - timedelta(days=1)
    start_date = today - timedelta(days=2)

    documents = []
    for doc in dict_list:
        try:
            forest_id = doc['forest_id']
            forest_tile_list = doc['tile_list']
            for tile in forest_tile_list:
                tile_id = tile['tile_id']
                coords = tile['bbox']

                try:
                    sat_image = sentinel_client.get_tile(coords, 10, start_date, end_date)
                    preprocessed_image = np.clip(sat_image[0]*3.5/255, 0, 1)
                    binary_image = pickle.dumps(preprocessed_image)
                except Exception as e:
                    return make_response(jsonify({'error': str(e)}), 400)

                forest_tile = {
                "forest_id" : forest_id,
                "tile_id" : tile_id,
                "image" : binary_image, 
                "image_shape" : sat_image[0].shape,
                "save_time" : datetime.combine(today, datetime.min.time()),
                "status" : "new"
                }
                documents.append(forest_tile)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)
    try:
        # TODO : to output actual result as json response
        result = save_forestTile(documents)
        return {"status" : 'OKay'}
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 400)

## REST access point to test daily threat type inference on latest collected data
class MakeClassInf(Resource):

    def _class_inf(self, forest_id, date):
        try:
            image_list, image_id_list = get_latest_forest_tiles(forest_id, date)
            np_image_list = np.array(image_list)

            class_model = ClassiModel.getInstance()
            inferences = class_model.inference(np_image_list)
            return image_id_list, inferences
        except Exception as e:
            return e

    def get(self):
        yesterday = datetime.combine(date.today(), datetime.min.time())

        try:
            forests = get_forest_ids()
            for id in forests:
                image_id_list, inferences = self._class_inf(id, yesterday)

                update_requests = []
                for i in range(len(image_id_list)):
                    query = UpdateOne({'_id': image_id_list[i]}, {'$set' : {'classification_result' : inferences[i], 'status' : 'class_inf'}})
                    update_requests.append(query)

                forestTile_bulkWrite(update_requests)
                return {"status" : 'OKay'}
        except Exception as e:
                return make_response(jsonify({'error': str(e)}), 400)

## daily threat type inference on latest collected data
def class_inf(forest_id, date):
    try:
        image_list, image_id_list = get_latest_forest_tiles(forest_id, date)
        np_image_list = np.array(image_list)

        class_model = ClassiModel.getInstance()
        inferences = class_model.inference(np_image_list)
        return image_id_list, inferences
    except Exception as e:
        return e

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

            forestTile_bulkWrite(update_requests)
    except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

## daily update threat type on forest tiles
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
            return make_response(jsonify({'error': str(e)}), 400)
    
## set entire forest view if any new threat appears
def set_forest_view():
    today = datetime.combine(date.today(), datetime.min.time())
    sentinel_client = SentilhubClient()
    try:
        forests = get_forests_pred_bnd()
        update_requests = []
        for forest in forests:
            forest_id = forest['_id']
            forest_boundary = forest['boundary']
            updatable = any(i['infered_threat_class'] != [] for i in forest['forest_tiles'])
            if updatable:
                forest_view = sentinel_client.get_forest(forest_boundary)
                preprocessed_view = np.clip(forest_view* 3.5/255, 0,1)
                bin_image = pickle.dumps(preprocessed_view)
                update_requests.append(UpdateOne({'_id' : forest_id}, {'$set' : {'entire_forest_view' : bin_image, 'forest_view_updated_date' : today}}))

        forestPage_bulkWrite(update_requests)
    except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

## daily threat location mask prediction and update in forest documents
def input_creator(image1, image2):
    image1_ch1, image2_ch1 = image1[:, :, 0], image2[:, :, 0]
    image1_ch1, image2_ch1 = image1_ch1[np.newaxis, ...], image2_ch1[np.newaxis, ...]
    inf_img = np.vstack((image1_ch1, image2_ch1))
    inf_img = np.moveaxis(inf_img, (0,1,2), (2,0,1))
    return inf_img

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
                    
            inf_images = np.array(list(inf_image_dict.values()))

            inferences = mask_model.inference(inf_images)

            tile_ids = list(image_td_dict.keys())

            update_requests = []
            for i, id in enumerate(tile_ids):
                query = UpdateOne({'_id': image_id_td_dict[i]}, {'$set' : {'forest_tiles.$.infered_mask' : pickle.dumps(inferences[i, ...]), "mask_update_date": today}})
                update_requests.append(query)

            forestTile_bulkWrite(update_requests)
    except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)
    


