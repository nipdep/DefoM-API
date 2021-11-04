import os

from flask import Flask, render_template
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Resource, Api

from bson import json_util, ObjectId
from datetime import datetime, timedelta



from defom.api.users import Hello, RegisterUser, LoginUser, logoutUser, HandleForestAdmin, HandleForestOfficer, DeleteForestOfficer, UpdateForestOfficer, ForestOfficerSelfUpdate, DBtest
from defom.api.forests import RegisterForest, ForestTiles, ForestTileDetails, ForestTileView, ForestSubAreaHandler, ForestNameHandler, ForestIdHandler, ForestPageDetail, ForestImage, ForestPageSummary, ForestName
from defom.api.message import ThreadHandler, MessageHandler, CommentHandler, ThreadCreator, MessageCreator, CommentCreator, GetThreadHandler, GetAllThreadHandler, GetThreadMessageHandler, ThreadDeletor, MessageDeletor

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

def create_api():

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
    # app.config['DB_URI'] = config['PROD']['DB_URI']
    # app.config['NS'] = config['PROD']['NS']
    # app.config['SECRET_KEY'] = config['PROD']['SECRET_KEY']

    app.config['JWT'] = jwt
    app.config['BCRYPT'] = Bcrypt(app)
    # app.config['CLAIMS_LOADER'] = add_claims
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

    api.add_resource(RegisterForest, '/forest/register')
    api.add_resource(RegisterUser, '/user/register')
    api.add_resource(LoginUser, '/user/login')
    api.add_resource(logoutUser, '/user/logout')
    api.add_resource(HandleForestAdmin, '/user/forestAdmin')
    api.add_resource(HandleForestOfficer, '/user/forestOfficer')
    api.add_resource(DeleteForestOfficer, '/user/deleteForestOfficer')
    api.add_resource(UpdateForestOfficer, '/user/updateForestOfficer')
    api.add_resource(ForestOfficerSelfUpdate, '/user/forestOfficer/update')
    api.add_resource(ForestIdHandler, '/user/forestAdmin/forestId')

    api.add_resource(ForestTiles, '/forest/get_tiles')
    api.add_resource(ForestTileDetails, '/forest/get_tile_details')
    api.add_resource(ForestTileView, '/forest/get_tile_view/<tile_id>/<mode>')
    api.add_resource(ForestSubAreaHandler, '/forest/area/<forest_id>')
    api.add_resource(ForestNameHandler, '/forest/forestNames')
    api.add_resource(ForestPageSummary, '/forestpage')
    api.add_resource(ForestPageDetail, '/forestpage/d/<forest_id>')
    api.add_resource(ForestImage, '/forestpage/i/<forest_id>')
    api.add_resource(ForestName, '/forest/get_forest_name')

    api.add_resource(MessageCreator, '/thread/message')
    api.add_resource(CommentCreator, '/comment')
    api.add_resource(ThreadHandler, '/thread')
    api.add_resource(GetThreadHandler, '/thread/<thread_id>')
    api.add_resource(GetAllThreadHandler, '/allThreads')
    api.add_resource(MessageHandler, '/thread/message')
    api.add_resource(GetThreadMessageHandler, '/thread/messages/<thread_id>')
    api.add_resource(CommentHandler, '/comment')
    api.add_resource(ThreadDeletor, '/thread/d/<thread_id>', methods=["GET"])
    api.add_resource(MessageDeletor, '/thread/message/d/<thread_id>/<sms_id>', methods=["GET"])

    api.add_resource(GetTiles, '/gettiles')  ## testing resources
    api.add_resource(MakeClassInf, '/classinf') ## testing resources
    api.add_resource(Hello, '/hello')  ## testing resources
    api.add_resource(Fac, '/enter')  ## testing resources
    api.add_resource(DBtest, '/users/<string:name>')  ## testing resources

    return app