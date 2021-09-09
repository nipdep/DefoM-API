
from flask import current_app, g
from werkzeug.local import LocalProxy

import pickle
from pprint import pprint

from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.write_concern import WriteConcern
from pymongo.errors import DuplicateKeyError, OperationFailure, BulkWriteError
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo.read_concern import ReadConcern


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)
    DB_URI = current_app.config["DB_URI"]
    DB_NAME = current_app.config["NS"]
    if db is None:
        db = g._database = MongoClient(
        DB_URI,
        )[DB_NAME]
        print(db['__my_database__'])
    return db


# Use LocalProxy to read the global db instance with just `db`
db = LocalProxy(get_db)

def get_user_by_name(name):
    return db.users.find_one({'username' : name})

######################### FOREST SATELLITE related function ##########################################

def save_forest(forest_data):
    try:
        res = db.forests.insert_one(forest_data)
        # db.create_index("forest_tiles")
        return res
    except Exception as e:
        return e
    
def create_forest_page(forest_data):
    try:
        res = db.forestPage.insert_one(forest_data)
        # db.create_index("forest_tiles")
        return res
    except Exception as e:
        return e

def get_all_forest_tiles():
    try:
        cursor = db.forests.find({}, {'forest_tiles' : 1})
        dict_list = []
        for fr in cursor:
            fr_dict = {}
            fr_dict['forest_id'] = fr['_id']
            fr_dict['tile_list'] = fr['forest_tiles']
            dict_list.append(fr_dict)
        return dict_list
    except Exception as e:
        return e

def save_forestTile(tile_list):
    try:
        result = db.forestTiles.insert_many(tile_list)
        return result
    except Exception as e:
        return e

def get_forest_ids():
    try:
        return [x['_id'] for x in list(db.forests.find({}, {'_id':1}))]
    except Exception as e:
        return e

def get_all_forests_tile_details():
    try:
        forest_det = list(db.forests.find({}, {'forest_tiles.tile_id':1, 'forest_tiles.infered_threat_class':1}))
        return forest_det
    except Exception as e:
        return e

def get_latest_forest_tiles(forest_id, date, state=1):
    try:
        if state == 1:
            cursor = db.forestTiles.find({
                'save_time' : date, 
                'forest_id': forest_id},
                {'image' : 1})

            image_list = []
            image_id_list = []
            for doc in cursor:
                np_image = pickle.loads(doc['image'])
                image_list.append(np_image)
                image_id_list.append(doc['_id'])
            return image_list, image_id_list
        elif  state == 2:
            latest_pred_in_id = list(db.forestTiles.find({'forest_id' : forest_id,
                                                         'save_time': date}, 
                                                        {'tile_id' : 1, 
                                                        'classification_result':1, 
                                                        '_id':0}))
            pred_dict = {}
            for pred in latest_pred_in_id:
                pred_dict[pred['tile_id']] = pred['classification_result']
            pred_dict
            return pred_dict
    except Exception as e:
        return e

def forestTile_bulkWrite(update_requests):
    try:
        db.forestTiles.bulk_write(update_requests, ordered=False)
    except BulkWriteError as bwe:
        pprint(bwe.details)

def forests_bulkWrite(update_requests):
    try:
        db.forests.bulk_write(update_requests, ordered=False)
    except BulkWriteError as bwe:
        pprint(bwe.details)

def forestPage_bulkWrite(update_requests):
    try:
        db.forestPage.bulk_write(update_requests, ordered=False)
    except BulkWriteError as bwe:
        pprint(bwe.details)

def get_forests_pred_bnd():
    try:
        forests = list(db.forests.find({}, {'boundary' : 1, 'forest_tiles.infered_threat_class':1}))
        return forests
    except Exception as e:
        return e

def get_forest_tile_inf():
    try:
        forests = list(db.forests.find({}, {'forest_tiles.tile_id' : 1,'forest_tiles.infered_threat_class':1}))
        return forests
    except Exception as e:
        return e

def get_tile_view_id(forest_id, tile_ids, date):
    try:
        acc_tiles = list(db.forestTiles.find({"forest_id" : forest_id, "tile_id" : {'$in' : tile_ids}, 'save_time':date}, {'image':1, 'tile_id':1}))
        return acc_tiles
    except Exception as e:
        return e

################### USER realted function ###############################

def add_user(username, email, password):
    try:
        return db.users.insert_one({'username' : username, 'password' : password, 'email' : email, 'user_type' : 'Citizen'})
    except Exception as e:
        return e

def get_user(email):
    try:
        return db.users.find_one({'email' : email})
    except Exception as e:
        return e

def login_user(email, jwt):
    """
    Given an email and JWT, logs in a user by updating the JWT corresponding
    with that user's email in the `sessions` collection.

    In `sessions`, each user's email is stored in a field called "user_id".
    """
    try:
        db.sessions.update_one(
            { "user_id": email },
            { "$set": { "jwt": jwt } }
        )
        return {"success": True}
    except Exception as e:
        return {"error": e}  

def logout_user(email):
    """
    In `sessions`, each user's email is stored in a field called "user_id".
    """
    try:
        db.sessions.delete_one({ "user_id": email })
        return {"success": True}
    except Exception as e:
        return {"error": e}   