import unittest
from unittest.mock import patch, Mock
from mongomock import MongoClient
import requests
import json
import glob

import unittest
import os

from defom.factory import create_api
from defom import db


class UsersTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### setting up flask server ###')
        super(UsersTest, cls).setUpClass()
        app = create_api()
        cls.test_db = db.get_db("test")
        app.config['TESTING'] = True
        cls.app = app.test_client()

    @classmethod
    def tearDownClass(cls):
        # cls.test_db.dropDatabase()
        ...

    def tearDown(self):
        ...
    
    def setUp(self):
        self.sample_req = {
            "email" : "deelak@gmail.com",
            "name" : "Nipun Deelaka",
            "password" : "mypassword"
        }
        ...

    def test_user_register(self):
        ## test backend validation of request
        sample_1 = self.sample_req.copy()
        sample_1.pop("name")
        result = self.app.post('/user/register',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("name", f'{err_sms}')

        sample_2 = self.sample_req.copy()
        result = self.app.post('/user/register',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)
        # err_sms = data['error'].replace('\'', '')
        self.assertEqual("True", data['status'])

    def test_user_login(self):
        sample_req = {
            "email" : "wt.nirasha@gmail.com",
            "password" : "mypassword",
        }

        sample_1 = sample_req.copy()
        sample_1["email"] = "wt.nirasha@gmail.co"
        result = self.app.post('/user/login',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 401)
        err_sms = data['error']
        self.assertEqual("{'email': 'Make sure your email is correct.'}", f'{err_sms}')
        
    def test_handle_forest_admin(self):
        sample_req = {
            "first_name" : "Thushan",
            "password" : "mypassword",
            "username" : "thushann.18@cse.mrt.ac.lk",
            "last_name" : "Nirasha",
            "forest_id" : "614cb90c8d20534162164fc9",
            "phone" : "0769253114"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("first_name")
        result = self.app.post('/user/forestAdmin',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'first_name'", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/forestAdmin',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)
        # err_sms = data['error'].replace('\'', '')
        self.assertEqual("True", data['status'])

    def test_handle_forest_officer(self):
        sample_req = {
            "username" : "thushan@gmail.com",
            "first_name" : "Thushan",
            "last_name" : "Nirasha",
            "forest_id" : "614cb90c8d20534162164fc9",
            "password" : "mypassword",
            "phone" : "0775776781"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("first_name")
        result = self.app.post('/user/forestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'first_name'", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/forestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)
        # err_sms = data['error'].replace('\'', '')
        self.assertEqual("True", data['status'])

        response = self.app.get(f'user/forestOfficer')
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue(len(data)>0)
        self.assertTrue(all(list(i.keys()) == ['_id', 'username','first_name','last_name','phone','status','id'] for i in data))   

    def test_delete_forest_officer(self):

        sample_req = {
            "email" : "thushan@gmail.com"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("email")
        result = self.app.post('/user/deleteForestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'email'", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/deleteForestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("True", data['status'])

    def test_update_forest_officer(self):
        sample_req = {
            "oldUsername" : "user3@gmail.com",
            "username" : "user1@gmail.com",
            "forest_id" : "61580ff5fef18721b56c75d4"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("username")
        result = self.app.post('/user/updateForestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'username'", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/updateForestOfficer',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("True", data['status'])

    def test_forest_officer_self_update(self):
        sample_req = {
            "username" : "user1@gmail.com",
            "first_name" : "Nirasha",
            "last_name" : "Thushan",
            "phone" : "0769253114"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("username")
        result = self.app.post('/user/forestOfficer/update',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'username'", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/forestOfficer/update',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)
        self.assertEqual("True", data['status'])

    def test_user_logout(self):
        sample_req = {
            "email" : "deelak@gmail.com",
        }

        sample_1 = sample_req.copy()
        sample_1.pop("email")
        result = self.app.post('/user/logout',
                            headers={"Authorization": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual("'NoneType' object is not subscriptable", f'{err_sms}')

        sample_2 = sample_req.copy()
        result = self.app.post('/user/logout',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 201)
        self.assertEqual("logged out", data['status'])



        

