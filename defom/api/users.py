
from flask_restful import Resource

from defom.db import get_user_by_name

class User(Resource):

    def get(self,name):
        user = get_user_by_name(name)
        userdata = {
            "name" : user['username'],
            "password" : user['password'],
        }
        # userdata = {'name' : name}
        return userdata