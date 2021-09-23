
import unittest
import json

from defom import db  
from defom.factory import create_api

class Inittest(unittest.TestCase):

    def setUp(self):
        "set up test fixtures"
        print('### Setting up flask server ###')
        app = create_api()
        self.db = db.get_db()
        app.config['TESTING'] = True
        self.app = app.test_client()
        # self.client = self.app.test_client(use_cookie=True)

    def test_successful_working(self):
        response = self.app.get('/enter')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual('Hello, World', data['data'])

    def test_db_connectivity(self):
        response = self.app.get('/user/nipun')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(200, response.status_code)
        self.assertEqual('pwd_nipun', data['password'])
        

    def tearDown(self):
        "tear down test fixtures"
        print('### Tearing down the flask server ###')
