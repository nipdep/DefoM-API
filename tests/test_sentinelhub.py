import unittest
from unittest.mock import patch, Mock

import numpy as np
from datetime import datetime, timedelta, date

from defom.src.SentinelhubClient import SentilhubClient


class SentinelHubTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('### Setting up DL Mask model ###')
        super(SentinelHubTest, cls).setUpClass()
        cls.client = SentilhubClient()

    def tearDown(self):
        ...

    def setUp(self):
        self.margin = {
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
                    80.91001510620116,
                    7.974067735995213
                    ],
                    [
                    80.90932846069336,
                    7.969307664180269
                    ],
                    [
                    80.90932846069336,
                    7.964887547921648
                    ],
                    [
                    80.9062385559082,
                    7.9580872759081895
                    ],
                    [
                    80.90211868286131,
                    7.952816987486306
                    ],
                    [
                    80.89868545532227,
                    7.947716643884279
                    ],
                    [
                    80.89130401611328,
                    7.944486393482047
                    ],
                    [
                    80.88460922241211,
                    7.939895993930101
                    ]
                ]]}
                }
            ]
        }

    def test_config(self):
        self.assertIsNotNone(self.client.config.sh_client_id)
        self.assertIsNotNone(self.client.config.sh_client_secret)

    def test_forest_split(self):
        bboxs = self.client.split_forest_area(self.margin)

        self.assertTrue(len(bboxs) > 0)
        self.assertTrue(type(bboxs[0]) is dict)
        self.assertEqual(bboxs[0]['tile_id'], 0)
        self.assertEqual(len(bboxs[0]['bbox']), 2)
        self.assertEqual(bboxs[0]['infered_threat_class'], [])

    def test_get_forest(self):
        # test black image
        end_date = datetime.combine(datetime.today(), datetime.min.time())
        start_date = datetime.combine(datetime.today() - timedelta(days=1), datetime.min.time())

        res_image = self.client.get_forest(self.margin, start_date, end_date)

        self.assertEqual(res_image.shape, (256, 256, 3))
        self.assertEqual(np.min(res_image), 0)
        self.assertEqual(np.max(res_image), 0)

        # test accessible time period

        start_date = datetime.combine(datetime.today() - timedelta(days=2), datetime.min.time())
        res_image = self.client.get_forest(self.margin, start_date, end_date)

        self.assertEqual(res_image.shape, (256, 256, 3))
        self.assertTrue(np.min(res_image) >= 0)
        self.assertTrue(np.max(res_image) <= 255)

    def test_get_tile(self):
        bbox_coord = [
            [81.29882812499999, 7.144498849647327], 
            [81.34277343749999, 7.188100871179018]
        ]
        end_date = datetime.combine(datetime.today(), datetime.min.time())
        start_date = datetime.combine(datetime.today() - timedelta(days=1), datetime.min.time())
        resolution = 10

        tile_image = self.client.get_tile(bbox_coord, resolution, start_date, end_date)[0]

        self.assertEqual(tile_image.shape[:2], (242, 242))
        self.assertEqual(tile_image.shape[-1], 12)

        original_image = tile_image[..., :5]
        self.assertTrue(np.max(original_image) <= 65365)
        self.assertTrue(np.min(original_image) >= 0)

        padding_image = tile_image[..., 5:]
        self.assertTrue(np.max(padding_image) == 0)
        self.assertTrue(np.min(padding_image) == 0)


