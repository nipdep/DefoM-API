import unittest
from unittest.mock import patch, Mock
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
        ...
        
    def test_get_all_threads(self):
        response = self.app.get(f'/allThreads')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(data, (list, tuple)))

    def test_get_thread(self):
        thread_id = "6156a20310c7ff830bc279f1"
        response = self.app.get(f'/thread/{thread_id}')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get("_id"))
        self.assertTrue(data.get('content'))
        self.assertTrue(data.get("title"))

    def test_get_thread_message(self):
        thread_id = "6156a20310c7ff830bc279f1"
        response = self.app.get(f'/thread/messages/{thread_id}')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get("_id"))
        self.assertTrue(data.get('content'))
        self.assertTrue(data.get("title"))

    def test_thread_creator(self):
        sample_req = {
            "content" : "redundant record",
            "title" : "testing input"
        }

        sample_1 = sample_req.copy()
        result = self.app.post('/thread',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        

    def test_message_creator(self):
        sample_req = {
            "thread_id" : "6156a20310c7ff830bc279f1",
            "message" : "testing message to testing thread"
        }

        sample_1 = sample_req.copy()
        result = self.app.post('/thread',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        # data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)

    


