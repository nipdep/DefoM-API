
import unittest
from unittest.mock import patch, Mock
from mongomock import MongoClient
import requests
import json

from defom.factory import create_api
from defom import db

class PyMongoMock(MongoClient):
    def init_app(self, app):
        return super().__init__()

class ForestTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### Setting up flask server ###')
        super(ForestTest, cls).setUpClass()
        app = create_api()
        cls.test_db = db.get_db()
        app.config['TESTING'] = True
        cls.app = app.test_client()

    def tearDown(self):
        "tear down test fixtures"
        print('### Tearing down the flask server ###')

    def setUp(self):
        self.sample_req = {
            "name" : "Yala",
            "district" : "Hambanthota",
            "country" : "Sri lanka",
            "location" : [80.92443466186523, 7.921703906373413],
            "forest_boundary" : {
                    "type": "FeatureCollection",
                    "features": [
                        {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                            [
                                [
                                80.91156005859375,
                                7.98307772023843
                                ],
                                [
                                80.91190338134766,
                                7.978827752414819
                                ]
                            ]]}
                        }]}
        }

    def test_forest_register(self):
        ## test backend validation of request
        sample_1 = self.sample_req.copy()
        sample_1.pop("name", None)
        result = self.app.post('/forest/register',
                            data=json.dumps(sample_1))
        print(result.data)
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        self.assertEqual(data['error'], 'forest')

# if __name__ == '__main__':
#     unittest.main()