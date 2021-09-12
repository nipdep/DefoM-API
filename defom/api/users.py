
from flask_restful import Resource
from flask import jsonify, Blueprint, make_response, request

from defom.api.utils import expect
from defom.db import get_user_by_name, add_user, get_user, login_user, logout_user
from bson.json_util import dumps, loads

from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_claims
)

from flask import current_app, g
# from werkzeug.local import LocalProxy

# def get_bcrypt():
#     bcrypt = getattr(g, '_bcrypt', None)
#     if bcrypt is None:
#         bcrypt = g._bcrypt = current_app.config['BCRYPT']
#     return bcrypt


# def get_jwt():
#     jwt = getattr(g, '_jwt', None)
#     if jwt is None:
#         jwt = g._jwt = current_app.config['JWT']

#     return jwt


# def init_claims_loader():
#     add_claims = getattr(g, '_add_claims', None)
#     if add_claims is None:
#         add_claims = g._add_claims = current_app.config['ADD_CLAIMS']
#     return add_claims


# jwt = LocalProxy(get_jwt)
# bcrypt = LocalProxy(get_bcrypt)
# add_claims_to_access_token = LocalProxy(init_claims_loader)
bcrypt = ""   ## TODO

class RegisterUser(Resource):

    def post():
        try:
            post_data = request.get_json()
            email = expect(post_data['email'], str, 'email')
            name = expect(post_data['name'], str, 'name')
            password = expect(post_data['password'], str, 'password')
        except Exception as e:
            return jsonify({'error': str(e)}), 400

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
            return jsonify(response_object), 411
        try:
            result = add_user(name, email, bcrypt.generate_password_hash(
                password=password.encode('utf8')).decode("utf-8"))
        except Exception as e:
                return make_response(jsonify(e), 411)


class LoginUser(Resource):

    def post():
        email = ""
        password = ""
        try:
            post_data = request.get_json()
            email = expect(post_data['email'], str, 'email')
            password = expect(post_data['password'], str, 'email')
        except Exception as e:
            jsonify({'error': str(e)}), 400

        userdata = get_user(email)
        if not userdata:
            response_object = {
                'error': {'email': 'Make sure your email is correct.'}
            }
            return make_response(jsonify(response_object)), 401
        if not bcrypt.check_password_hash(userdata['password'], password):
            response_object = {
                'error': {'password': 'Make sure your password is correct.'}
            }
            return make_response(jsonify(response_object)), 401

        userdata = {
            "email": userdata['email'],
            "name": userdata['name'],
            "preferences": userdata.get('preferences'),
            "isAdmin": userdata.get('isAdmin', False)
        }

        user = User(userdata)
        jwt = create_access_token(user.to_json())

        try:
            login_user(user.email, jwt)
            response_object = {
                'auth_token': jwt,
                'info': userdata,
            }
            return make_response(jsonify(response_object)), 201
        except Exception as e:
            response_object = {
                'error': {'internal': e}
            }
            return make_response(jsonify(response_object)), 500


class logoutUser(Resource):

    @jwt_required
    def post():
        claims = get_jwt_claims()
        user = User.from_claims(claims)
        try:
            logout_user(user.email)
            response_object = {
                'status': 'logged out'
            }
            return make_response(jsonify(response_object)), 201
        except Exception as e:
            response_object = {
                'error': {'internal': str(e)}
            }
            return make_response(jsonify(response_object)), 401
            
class User(Resource):

    def get(self,name):
        user = get_user_by_name(name)
        userdata = {
            "name" : user['username'],
            "password" : user['password'],
        }
        # userdata = {'name' : name}
        return userdata