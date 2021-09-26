# from defom.factory import create_api

# import os
# import configparser

# # config = configparser.ConfigParser()
# # config.read(os.path.abspath(os.path.join(".ini")))

# # if __name__ == '__main__':
# app = create_api()
# # app.config['DEBUG'] = True
# # app.config['DB_URI'] = config['PROD']['DB_URI']
# # app.config['NS'] = config['PROD']['NS']
# # app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']


# app.run()

import os

from flask import Flask, render_template
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from flask_restful import Resource, Api

from bson import json_util, ObjectId
from datetime import datetime, timedelta


from defom.api.users import Hello, User, RegisterUser, LoginUser, logoutUser, HandleForestAdmin, HandleForestOfficer
from defom.api.forests import RegisterForest, ForestTiles, ForestTileDetails, ForestTileView

from defom.api.scheduler import GetTiles, save_tiles_daily, make_class_inf_daily, MakeClassInf, set_latest_threat_daily, set_forest_view, set_mask_daily

import configparser

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

class MongoJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(obj, ObjectId):
            return str(obj)
        return json_util.default(obj, json_util.CANONICAL_JSON_OPTIONS)

class Fac(Resource):
    def get(self):
        return {"data" : "Hello, World"}

# if __name__ == '__main__':

    # APP_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
api = Api(app)
CORS(app)
app.json_encoder = MongoJsonEncoder
jwt = JWTManager(app)

# @jwt.user_claims_loader
# def add_claims(identity):
#     return {
#         'user': identity,
#     }
app.config['DEBUG'] = True
app.config['DB_URI'] = config['PROD']['DB_URI']
app.config['NS'] = config['PROD']['NS']
app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']

app.config['JWT'] = jwt
app.config['BCRYPT'] = Bcrypt(app)
# app.config['CLAIMS_LOADER'] = add_claims
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

api.add_resource(Fac, '/enter')
# api.add_resource(User, '/user/<string:name>')
api.add_resource(RegisterForest, '/forest/register')
api.add_resource(RegisterUser, '/user/register')
api.add_resource(LoginUser, '/user/login')
api.add_resource(logoutUser, '/user/logout')
api.add_resource(HandleForestAdmin, '/user/forestAdmin')
api.add_resource(HandleForestOfficer, '/user/forestOfficer')
api.add_resource(ForestTiles, '/forest/get_tiles')
api.add_resource(ForestTileDetails, '/forest/get_tile_details')
api.add_resource(ForestTileView, '/forest/get_tile_view/<tile_id>/<mode>')
api.add_resource(GetTiles, '/gettiles')  ## testing resources
api.add_resource(MakeClassInf, '/classinf') ## testing resources
api.add_resource(Hello, '/hello')

if __name__ == '__main__':
    app.run()