import os

import pickle
from pprint import pprint

from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.write_concern import WriteConcern
from pymongo.errors import DuplicateKeyError, OperationFailure, BulkWriteError
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo.read_concern import ReadConcern


# DB_URI = os.environ.get('DB_URI', None)
# NS = os.environ.get('NS', None)
# SECRET_KEY = os.environ.get('SECRET_KEY', None)

def get_db():
    # uri = f"mongodb+srv://defomAdmin:{os.environ.get('password')}@defomdb.osisk.mongodb.net"
    uri = f"mongodb+srv://defomAdmin:pwd3202defom@defomdb.osisk.mongodb.net/?ssl=true&ssl_cert_reqs=CERT_NONE"
    # uri = f"mongodb+srv://defomAdmin:pwd3202defom@defomdb.osisk.mongodb.net/test?authSource=admin&replicaSet=atlas-d7vl2z-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true"
    client = MongoClient(uri)
    db = client.defom
    print("connected to database")
    return db


# Use LocalProxy to read the global db instance with just `db`
db = get_db()

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
        cursor = db.forests.find({}, {'forest_tiles' : 1, 'status':1})
        dict_list = []
        for fr in cursor:
            fr_dict = {}
            fr_dict['forest_id'] = fr['_id']
            fr_dict['tile_list'] = fr['forest_tiles']
            fr_dict['status'] = fr['status']
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
                                                        'class_infered':1, 
                                                        '_id':1}))
            pred_dict = {}
            for pred in latest_pred_in_id:
                pred_dict[pred['tile_id']] = {'id' : pred['_id'], 'res' : pred['class_infered']}
            return pred_dict
    except Exception as e:
        return e

def getTileAllDetails(forest_id, tile_id, date):
    try:
        tile_data = list(db.forestTiles.find({'forest_id':forest_id, 'tile_id' : tile_id, "save_time" : {"$lte" : date}}, {'image':0, 'mask':0}).sort("save_time",-1).limit(1))
        if tile_data != []:
            return tile_data[0]
        else:
            return None
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

def get_forest_tiles(forest_id, date_dt):
    try:
        acc_tiles = db.forests.find_one({'_id':forest_id}, {'forest_name':1, 'forest_tiles':1, 'location':1})
        inf_list = list(db.forestTiles.find({'forest_id' : forest_id,'save_time': date_dt}, {'infered_threat_present':1, '_id':0}))
        for i, doc in enumerate(acc_tiles['forest_tiles']):
            doc['infered_threat_present'] = True if inf_list[i] != {} else False
        return acc_tiles
    except Exception as e:
        return e

def getTileView(forest_id, tiles_id):
    try:
        id_dict = db.forests.find_one({"_id":  forest_id, 'forest_tiles.tile_id' : tiles_id}, {'forest_tiles.tile_id':1, 'forest_tiles.update_view_id':1})
        t_id = id_dict['forest_tiles'][tiles_id]['update_view_id']
        if t_id != None:
            tile_image = db.forestTiles.find_one({"_id": t_id}, {"image":1})
            return pickle.loads(tile_image['image'])
    except Exception as e:
        return e

def get_tile_view(tile_id):
    try:
        res = db.forestTiles.find_one({"_id":  tile_id}, {'image':1})
        if res != None:
            image = pickle.loads(res['image'])
            return image
        else:
            return None
    except Exception as e:
        return e

def get_tile_mask(tile_id):
    try:
        res = db.forestTiles.find_one({"_id":  tile_id}, {'mask':1})
        if res != None:
            mask = pickle.loads(res['mask'])
            return mask
        else:
            return None
    except Exception as e:
        return e

def get_forest_areas(forest_id):
    try:
        res = db.forests.find_one({"_id": forest_id}, {'boundary':1, 'sub_areas':1})
        return res
    except Exception as e:
        return e

def save_forest_areas(forest_id, data):
    try:
        res = db.forests.update({"_id": forest_id}, {'$push' : {'sub_areas': data}})
        return res
    except Exception as e:
        return e

################### USER realted function ###############################

def add_user(username, email, password):
    try:
        return db.users.insert_one({'username' : username, 'password' : password, 'email' : email, 'user_type' : 'forestAdmin'})
    except Exception as e:
        return e

def add_user_name():
    try:
        return db.users.insert_one({'username' : 'test'})
    except Exception as e:
        return e

def get_user(email):
    try:
        return db.users.find_one({'email' : email})   
    except Exception as e:
        return e

def get_forest_officer(email):
    try:
        return db.forestOfficers.find_one({'username' : email})   
    except Exception as e:
        return e

def login_user(email, jwt):
    """
    Given an email and JWT, logs in a user by updating the JWT corresponding
    with that user's email in the `sessions` collection.

    In `sessions`, each user's email is stored in a field called "user_id".
    """

    try:
        existing_user = db.session.find_one({'user_id' : email})
        if not existing_user:
            db.session.insert_one({'user_id' : email, 'jwt' : jwt})
    except Exception as e:
        return {"error" : e}

    try:
        db.session.update_one(
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
        db.session.delete_one({ "user_id": email })
        return {"success": True}
    except Exception as e:
        return {"error": e}   

def save_forest_admin(username, first_name, last_name, forest_id,hashed_password, phone, user_id):
    try:
        res = db.forestAdmins.insert_one({'username' : username, 'first_name' : first_name, 'last_name' : last_name, 'forest_id' : forest_id ,'password' : hashed_password, 'phone' : phone, 'user_id' : user_id, 'status' : 'New'})
        return res
    except Exception as e:
        return e

def add_forest_admin(username, email, password):
    try:
        return db.users.insert_one({'username' : username, 'password' : password, 'email' : email, 'user_type' : 'forestAdmin'})
    except Exception as e:
        return e

def add_forest_officer(username, email, password):
    try:
        return db.users.insert_one({'username' : username, 'password' : password, 'email' : email, 'user_type' : 'forestOfficer'})
    except Exception as e:
        return e

def save_forest_officer(username, first_name, last_name, forest_id, hashed_password, phone, user_id):
    try:
        res = db.forestOfficers.insert_one({'username' : username, 'first_name' : first_name, 'last_name' : last_name, 'forest_id' : forest_id, 'password' : hashed_password, 'phone' : phone, 'user_id' : user_id, 'status' : 'New'})
        return res
    except Exception as e:
        return e

def get_forest_officers():
    try:
        res = list(db.forestOfficers.find({}, {'_id':1, 'username': 1, 'first_name': 1, 'last_name': 1, 'forest_name': 1, 'phone': 1, 'status':1}))
        return res
    except Exception as e:
        return e

def delete_forest_officer(email):
    try:
        res1 = db.users.delete_one({"email": email})
        res2 = db.forestOfficers.delete_one({"username": email})
        return res2
    except Exception as e:
        return e

def update_forest_officer_in_users(old_username,username):
    try:
        result = db.users.update_one({'email': old_username},
            {
                "$set": {
                    'email': username
                }
            }
        )
        return result
    except Exception as e:
        return e

def update_forest_officer_in_forest_officers(old_username,username, forest_name):
    try:
        result = db.forestOfficers.update_one({ 'username' :old_username},
            {
                "$set" : {
                    'username' : username,
                    'forest_name' : forest_name
                }
            }
        )
        return result
    except Exception as e:
        return e

def self_update_forest_officer_in_users(username, first_name):
    try:
        result = db.users.update_one({ 'email' : username},
            {
                "$set" : {
                    'username' : first_name
                }
            }
        )
        return result
    except Exception as e:
        return e

def self_update_forest_officer_in_forest_officers(username,first_name, last_name, phone):
    try:
        result = db.forestOfficers.update_one({ 'username' : username},
            {
                "$set" : {
                    'first_name' : first_name,
                    'last_name' : last_name,
                    'phone' : phone
                }
            }
        )
        return result
    except Exception as e:
        return e


######################### MESSAGE related ##################################################

def get_thread_data(thread_id):
    try:
        return db.forumThreads.find_one({'_id':thread_id}, {'messages':0})
    except Exception as e:
        return e

def create_thread(thread_data):
    try:
        return db.forumThreads.insert_one(thread_data)
    except Exception as e:
        return e   

def get_message_data(sms_id):
    try:
        return db.forumThreads.find_one({'messages._id':sms_id}, {'messages':1})
    except Exception as e:
        return e

def add_message(thread_id,sms_data):
    try:
        return db.forumThreads.update({'_id':thread_id}, { '$push' : {'messages' : sms_data}})
    except Exception as e:
        return e

def add_comment(thread_id, sms_id, comment_data):
    try:
        return db.forumThreads.update({'_id':thread_id, 'message.id':sms_id}, { '$push' : {'messages.comments' : comment_data}})
    except Exception as e:
        return e

def forest_names_and_ids():
    try:
        result = list(db.forests.find({}, {'_id':1, "forest_name" : 1}))
        return result
    except Exception as e:
        return e

def get_forest_id(username):
    try:
        result = db.forestAdmins.find_one({ 'username' : username}, {'_id':0, 'forest_id':1})
        return result
    except Exception as e:
        return e

