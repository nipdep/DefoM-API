

from flask import make_response, request, jsonify
from flask_restful import Resource, fields, marshal_with

from defom.api.utils import expect
from defom.db import save_forest, save_forestTile, create_forest_page
from defom.src.SentinelhubClient import SentilhubClient

class Forest(object):

    def __init__(self, name, country, district, location, boundary):
        self.name = name
        self.country = country
        self.district = district
        self.location = location
        self.boundary = boundary


class ForestTile(object):

    def __init__(self, forest_id, tile_coordinates):
        self.forest_id = forest_id
        self.coords = tile_coordinates

    @staticmethod
    def create_tile(forest_id, tile_coordinates):
        try:
            save_forestTile(forest_id, tile_coordinates)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

class RegisterForest(Resource):
    def post(self):        
        try:
            post_data = request.get_json()
            forest_data = {}
            forest_data['forest_name'] = expect(post_data['name'], str, 'forest')
            forest_data['district'] = expect(post_data['district'], str, 'district')
            forest_data['country'] = expect(post_data['country'], str, 'country')
            forest_data['boundary'] = expect(post_data['forest_boundary'], dict, 'forest_boundary')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)
        
        try:
            boundary_coords = forest_data['boundary']
            sentinel_client = SentilhubClient()
            bbox_doc_list = sentinel_client.split_forest_area(boundary_coords)
            forest_data['forest_tiles'] = bbox_doc_list
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)


        try:
            res = save_forest(forest_data)
            # return make_response(jsonify({"status" : str(res.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)

        try:
            new_fid = res.inserted_id
            res1 = create_forest_page({'forest_id':new_fid})
            return make_response(jsonify({"status" : str(res1.acknowledged)}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 411)