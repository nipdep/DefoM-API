
from bson.objectid import ObjectId
from flask_restful import Resource
from flask import jsonify, Blueprint, make_response, request, session
from defom.api.utils import expect
from defom.db import get_user_by_name, add_user, get_user, login_user, logout_user, save_forest_admin, add_forest_admin, add_forest_officer, save_forest_officer, get_forest_officers, delete_forest_officer, update_forest_officer_in_users, update_forest_officer_in_forest_officers, self_update_forest_officer_in_users, self_update_forest_officer_in_forest_officers,add_citizen
from bson.json_util import dumps, loads
from werkzeug.security import generate_password_hash, check_password_hash
from jwt import PyJWT

from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_claims, jwt_required, create_access_token,   
)

from flask import current_app, g
from werkzeug.local import LocalProxy

def get_bcrypt():
    bcrypt = getattr(g, '_bcrypt', None)
    if bcrypt is None:
        bcrypt = g._bcrypt = current_app.config['BCRYPT']
    return bcrypt


def get_jwt():
    jwt = getattr(g, '_jwt', None)
    if jwt is None:
        jwt = g._jwt = current_app.config['JWT']

    return jwt


def init_claims_loader():
    add_claims = getattr(g, '_add_claims', None)
    if add_claims is None:
        add_claims = g._add_claims = current_app.config['ADD_CLAIMS']
    return add_claims


jwt = LocalProxy(get_jwt)
bcrypt = LocalProxy(get_bcrypt)
add_claims_to_access_token = LocalProxy(init_claims_loader)

# class RegisterUser(Resource):
#     def post(self):
#         post_data = request.get_json()
#         email = expect(post_data['email'], str, 'email')
#         name = expect(post_data['name'], str, 'name')
#         password = expect(post_data['password'], str, 'password')

#         if len(password) < 8:
#             return "Your password must be at least 8 characters.", 400

#         if len(name) < 3:
#             return "You must specify a name of at least 3 characters.", 400
        
#         existing_user = get_user(email)
#         if existing_user is None:
#             result = add_user(name, email, generate_password_hash(
#                 password, method="sha256"))
#             access_token = create_access_token(identity={"email" : email})
#             # return make_response('Successfully Registered',200,{"x-auth-token" : access_token} )
#             return {"access_token" : access_token}, 200
#         return "This user already exists", 400

class RegisterUser(Resource):
    
    def post(self):
        try:
            post_data = request.get_json()
            email = expect(post_data['email'], str, 'email')
            name = expect(post_data['name'], str, 'name')
            password = expect(post_data['password'], str, 'password')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        errors = {}
        if len(password) < 8:
            errors['password'] = "Your password must be at least 8 characters."

        if len(name) <= 3:
            errors['name'] = "You must specify a name of at least 3 characters."

        if len(errors.keys()) != 0:
            response_object = {
                'status': 'fail',
                'error': errors
            }
            return make_response(jsonify(response_object), 411)
        try:
            result = add_user(name, email, bcrypt.generate_password_hash(
                password=password.encode('utf8')).decode("utf-8"))
            response = add_citizen(name, email, bcrypt.generate_password_hash(
                password=password.encode('utf8')).decode("utf-8"))
        except Exception as e:
                return make_response(make_response(jsonify(e), 411))
       
class LoginUser(Resource):
    def post(self):
        post_data = request.get_json()
        email = expect(post_data['email'], str, 'email')
        password = expect(post_data['password'], str, 'password')
        userdata = get_user(email)
        if not userdata:
            response_object = {
                'error': {'email': 'Make sure your email is correct.'}
            }
            return make_response(jsonify(response_object), 401)
        if not bcrypt.check_password_hash(userdata['password'], password):
            response_object = {
                'error': {'password': 'Make sure your password is correct.'}
            }
            return make_response(jsonify(response_object), 401)

        userdata = {
            "email": userdata['email'],
            "name": userdata['username'],
            "preferences": userdata.get('preferences'),
            "isAdmin": userdata.get('isAdmin', False),
            "userType": userdata['user_type']
        }

        user = User(userdata)
        jwt = create_access_token(user.to_json())

        try:
            login_user(email, jwt)
            response_object = {
                'auth_token': jwt,
                'info': userdata,
            }
            return make_response(jsonify(response_object), 201)
        except Exception as e:
            response_object = {
                'error': {'internal': e}
            }
            return make_response(jsonify(response_object), 500)

class HandleForestAdmin(Resource):
    def post(self):        
        try:
            post_data = request.get_json()
            username = expect(post_data['first_name'], str, 'username')
            password = expect(post_data['password'], str, 'password')
            email = expect(post_data['username'], str, 'email')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        existing_user = get_user(email)

        if existing_user:
            return "This forest admin already in the system",401

        try:
            res = add_forest_admin(username,  email, bcrypt.generate_password_hash(password=password.encode('utf8')).decode("utf-8"))
            # return make_response(jsonify({"status" : str(res.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

        try:
            new_fid = res.inserted_id
            username = expect(post_data['username'], str, 'username')
            first_name = expect(post_data['first_name'], str, 'first_name')
            last_name = expect(post_data['last_name'], str, 'last_name')
            forest_id = ObjectId(expect(post_data['forest_id'], str, "forest id"))
            password = expect(post_data['password'], str, 'password')
            hashed_password = bcrypt.generate_password_hash(password=password.encode('utf8')).decode("utf-8")
            phone = expect(post_data['phone'], str, 'phone')
            user_id = new_fid
            result = save_forest_admin(username, first_name, last_name, forest_id, hashed_password, phone, user_id)
            return make_response(jsonify({"status" : str(result.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

class HandleForestOfficer(Resource):
    def post(self):        
        try:
            post_data = request.get_json()
            username = expect(post_data['first_name'], str, 'username')
            password = expect(post_data['password'], str, 'password')
            email = expect(post_data['username'], str, 'email')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        existing_user = get_user(email)

        if existing_user:
            return "This forest officer already in the system",401

        try:
            res = add_forest_officer(username,  email, bcrypt.generate_password_hash(password=password.encode('utf8')).decode("utf-8"))
            # return make_response(jsonify({"status" : str(res.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

        try:
            new_fid = res.inserted_id
            username = expect(post_data['username'], str, 'username')
            first_name = expect(post_data['first_name'], str, 'first_name')
            last_name = expect(post_data['last_name'], str, 'last_name')
            forest_id = ObjectId(expect(post_data['forest_id'], str, 'forest id'))
            password = expect(post_data['password'], str, 'password')
            hashed_password = bcrypt.generate_password_hash(password=password.encode('utf8')).decode("utf-8")
            phone = expect(post_data['phone'], str, 'phone')
            user_id = new_fid
            result = save_forest_officer(username, first_name, last_name, forest_id, hashed_password, phone, user_id)
            return make_response(jsonify({"status" : str(result.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

    def get(self):
        try:
            forest_officers = get_forest_officers()
            for i,doc in enumerate(forest_officers,1):
                doc['_id'] = str(doc['_id'])
                doc['id'] = i
            return forest_officers,200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

class DeleteForestOfficer(Resource):
    
    def post(self):
        try:
            post_data = request.get_json()
            email = expect(post_data['email'], str, "username")
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        try:
            result = delete_forest_officer(email)
            print(result)
            return "Forest Officer Deleted Successfully",200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}),411)

class UpdateForestOfficer(Resource):
    def post(self):
        try:
            post_data = request.get_json()
            old_username = expect(post_data['oldUsername'], str, "old username")
            username = expect(post_data['username'], str, "username")
            forest_id = ObjectId(expect(post_data['forest_id'], str, "forest id"))
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        existing_user = get_user(username)

        if existing_user:
            return "This forest officer already in the system",401

        try:
            result = update_forest_officer_in_users(old_username,username)
            # print(result)
            # new_fid = result.inserted_id
            res = update_forest_officer_in_forest_officers(old_username,username, forest_id)
            return make_response(jsonify({"status" : str(res.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}),411)

class ForestOfficerSelfUpdate(Resource):
    def post(self):
        try:
            post_data = request.get_json()
            username = expect(post_data['username'], str, "username")
            first_name = expect(post_data['first_name'], str, "firstName")
            last_name = expect(post_data['last_name'], str, "last Name")
            phone = expect(post_data['phone'], str, "phone")
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        try:
            result = self_update_forest_officer_in_users(username,first_name)
            res = self_update_forest_officer_in_forest_officers(username,first_name, last_name, phone)
            return make_response(jsonify({"status" : str(res.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error' : str(e)}), 411)

       
class logoutUser(Resource):
    @jwt_required
    def post(self):
        try:
            post_data = request.get_json()
            email = expect(post_data['email'],str, 'email')
        except Exception as e:
            return make_response(jsonify({'error' : str(e)}), 400)
        # claims = get_jwt_claims()
        # user = User.from_claims(claims)
        try:
            logout_user(email)
            response_object = {
                'status': 'logged out'
            }
            return make_response((jsonify(response_object)), 201)
        except Exception as e:
            response_object = {
                'error': {'internal': str(e)}
            }
            return make_response((jsonify(response_object)), 401)
            
# class User(Resource):

#     def get(self,name):
#         user = get_user_by_name(name)
#         userdata = {
#             "name" : user['username'],
#             "password" : user['password'],
#         }
#         # userdata = {'name' : name}
#         return userdata

class User(object):
    
    def __init__(self, userdata):
        self.email = userdata.get('email')
        self.name = userdata.get('name')
        self.password = userdata.get('password')
        self.preferences = userdata.get('preferences')
        self.is_admin = userdata.get('isAdmin', False)

    def to_json(self):
        return loads(dumps(self, default=lambda o: o.__dict__, sort_keys=True))

    @staticmethod
    def from_claims(claims):
        return User(claims.get('user'))

class Hello(Resource):
    @jwt_required
    def get(self):
        dictinary = {
            "message" : "Hello World"
        }
        return jsonify(dictinary)

class DBtest(Resource):
    def get(self, name):
        res= get_user_by_name(name)
        return jsonify(res)