#%%
import unittest
import json
import sys, os
import glob

# sys.path.append('../')

from defom import db  
from defom.factory import create_api

class Inittest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        print('### Setting up flask server ###')
        super(Inittest, cls).setUpClass()
        app = create_api()
        cls.test_db = db.get_db("test")
        app.config['TESTING'] = True
        cls.app = app.test_client()

    def setUp(self):
        # "set up test fixtures"
        # print('### Setting up flask server ###')
        # app = create_api()
        # self.db = db.get_db()
        # app.config['TESTING'] = True
        # self.app = app.test_client()
        # self.client = self.app.test_client(use_cookie=True)
        ...

    def test_successful_working(self):
        response = self.app.get('/enter')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual("Hello, World", data['data'])

    def test_db_connectivity(self):
        response = self.app.get('/users/Nipun')
        # response = response.decode('utf-8').replace('\0', '')
        data = json.loads(response.get_data(as_text=True))
        # data = json.load(response.data)
        self.assertEqual(200, response.status_code)
        self.assertEqual("$2b$12$kdidUxRq0Z5fsShdGP8EDejIkQvZL8FAHxDxoBfrHWJUdXMePvLr.", data['password'])
        

    def tearDown(self):
        "tear down test fixtures"
        # print('### Tearing down the flask server ###')

if __name__ == '__main__':
    unittest.main()


