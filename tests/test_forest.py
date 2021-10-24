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

# class PyMongoMock(MongoClient):
#     def init_app(self, app):
#         return super().__init__()

class ForestTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### Setting up flask server ###')
        super(ForestTest, cls).setUpClass()
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
                                ],
                                [
                                80.91190338134766,
                                7.978627752414819
                                ],
                                [
                                80.91156005859375,
                                7.98307772023843
                                ],
                            ]]}
                        }]}
        }

    def test_forest_register(self):
        ## test backend validation of request
        sample_1 = self.sample_req.copy()
        sample_1.pop("name")
        result = self.app.post('/forest/register',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("name", f'{err_sms}')

        sample_2 = self.sample_req.copy()
        sample_2["forest_boundary"] = {}
        result = self.app.post('/forest/register',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("features", f'{err_sms}')

        sample_3 = self.sample_req.copy()
        result = self.app.post('/forest/register',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_3),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)
        # err_sms = data['error'].replace('\'', '')
        self.assertEqual("True", data['status'])

    def test_forest_tile_details(self):
        sample_req = {
            "forest_id" : "614cb90c8d20534162164fc9",
            "tile_id" : 2,
            "date" : "2021-09-26"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("forest_id")
        result = self.app.post('/forest/get_tile_details',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("forest_id", f'{err_sms}')

        sample_2 = sample_req.copy()
        sample_2["date"] = "2021.10.24"
        result = self.app.post('/forest/get_tile_details',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error']
        self.assertEqual(err_sms, "time data '2021.10.24' does not match format '%Y-%m-%d'")

        sample_3 = sample_req.copy()
        result = self.app.post('/forest/get_tile_details',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_3),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        # print(data)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(data['image_shape'], [242, 242, 5])
        self.assertEqual(data['tile_id'], 2)
        self.assertEqual(data['save_time'], "2021-09-26 00:00:00")
        self.assertEqual(data['forest_id'], "614cb90c8d20534162164fc9")
        self.assertTrue(all(i in data.keys() for i in ['class_infered', '_id', 'infered_threat_present', 'mask_present']))
        
    def test_forest_tiles(self):
        sample_req = {
            "email" : "thushan@gmail.com",
            "date" : "2021-09-26"
        }

        sample_1 = sample_req.copy()
        sample_1.pop("email")
        result = self.app.post('/forest/get_tiles',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("email", f'{err_sms}')      

        sample_2 = sample_req.copy()
        sample_2['date'] = "2021.09.06"
        result = self.app.post('/forest/get_tiles',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        # err_sms = data['error'].replace('\'', '')
        self.assertEqual(data['error'], "time data '2021.09.06' does not match format '%Y-%m-%d'") 

        sample_3 = sample_req.copy()
        result = self.app.post('/forest/get_tiles',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_3),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(data['_id'], "614cb90c8d20534162164fc9")
        self.assertEqual(data['forest_name'], "Galoya National Park")
        self.assertTrue(all(i in data.keys() for i in ['_id', 'forest_name', 'forest_tiles', 'location']))
        self.assertEqual(len(data['forest_tiles']), 33)

    def test_forest_subarea_handler_get(self):
        forest_id = "614cb90c8d20534162164fc9"

        response = self.app.get(f'/forest/area/{forest_id}')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['_id'], "614cb90c8d20534162164fc9")
        self.assertNotEqual(data['boundary'], {})
        self.assertTrue(all(i in data.keys() for i in ['_id', 'boundary', 'sub_areas']))
        self.assertNotEqual(data['sub_areas'], [])

        forest_id = "614cb90c8d20334162164fc9"
        response = self.app.get(f'/forest/area/{forest_id}')
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data, None)

    def test_forest_subarea_handler_post(self):
        forest_id = "614cb90c8d20534162164fc9"
        sample_req = {
            "forest_id" : "614cb90c8d20534162164fc9",
            "restriction_level" : "restricted",
            "sub_area" : [
                                [
                                80.91156005859375,
                                7.98307772023843
                                ],
                                [
                                80.91190338134766,
                                7.978827752414819
                                ],
                                [
                                80.91190338134766,
                                7.978627752414819
                                ],
                                [
                                80.91156005859375,
                                7.98307772023843
                                ],
                            ]
        }

        sample_1 = sample_req.copy()
        sample_1.pop("forest_id")
        result = self.app.post(f'/forest/area/{forest_id}',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("forest_id", f'{err_sms}') 

        sample_2 = sample_req.copy()
        sample_2.pop("sub_area")
        result = self.app.post(f'/forest/area/{forest_id}',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_2),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 400)
        err_sms = data['error'].replace('\'', '')
        self.assertEqual("sub_area", f'{err_sms}') 

        sample_3 = sample_req.copy()
        result = self.app.post(f'/forest/area/{forest_id}',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_3),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)

    def test_forest_name_handler(self):
        response = self.app.get('/forest/forestNames')
        data = json.loads(response.get_data(as_text=True))  
        self.assertTrue(len(data)>0)
        self.assertTrue(all(list(i.keys()) == ['_id', 'forest_name'] for i in data))   

    def test_forest_id_handler(self):
        sample_req = {
            "username" : "user1@gmail.com"
        }

        sample_1 = sample_req.copy()
        result = self.app.post('/user/forestAdmin/forestId',
                            headers={"Content-Type": "application/json"},
                            data=json.dumps(sample_1),
                            charset='UTF-8')
        data = json.loads(result.get_data(as_text=True))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(data['forest_id'], "61580ff5fef18721b56c75d4")

    def test_forest_page_summary(self):
        response = self.app.get('/forestpage')
        data = json.loads(response.get_data(as_text=True))     
        # print(data[0].keys())   
        self.assertTrue(all(list(i.keys()) == ['_id', 'country', 'district', 'forest_name', 'location'] for i in data)) 
        self.assertTrue(len(data)>0)

    def test_forest_page_details(self):
        forest_id = "614cb90c8d20534162164fc9"
        response = self.app.get(f'/forestpage/d/{forest_id}')
        data = json.loads(response.get_data(as_text=True))     
        self.assertTrue(list(data.keys()) == ['_id', 'forest_id', 'forest_view_updated_date'])       

## have not unit test image file sending functions
##  - ForestImage()
##  - ForestTileView()

if __name__ == '__main__':
    unittest.main()