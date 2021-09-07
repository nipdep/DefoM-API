import os

from flask import Flask, render_template
from flask.json import JSONEncoder
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from flask_restful import Resource, Api

from bson import json_util, ObjectId
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from defom.api.users import User
from defom.api.forests import RegisterForest
from defom.api.scheduler import GetTiles, save_tiles_daily, make_class_inf_daily, MakeClassInf, set_latest_threat_daily


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
    app.json_encoder = MongoJsonEncoder
    jwt = JWTManager(app)

    # @jwt.user_claims_loader
    # def add_claims(identity):
    #     return {
    #         'user': identity,
    #     }

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=save_tiles_daily, trigger="cron", hour='10-11')
    scheduler.add_job(func=make_class_inf_daily, trigger="cron", hour='11-12')
    scheduler.add_job(func=set_latest_threat_daily, trigger="cron", hour='12-13')


    app.config['JWT'] = jwt
    app.config['BCRYPT'] = Bcrypt(app)
    # app.config['CLAIMS_LOADER'] = add_claims
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

    api.add_resource(Fac, '/enter')
    api.add_resource(User, '/user/<string:name>')
    api.add_resource(RegisterForest, '/forest/register')
    api.add_resource(GetTiles, '/gettiles')  ## testing resources
    api.add_resource(MakeClassInf, '/classinf')

    return app