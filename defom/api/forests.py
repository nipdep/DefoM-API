

from flask import make_response, request, jsonify
from flask_restful import Resource, fields, marshal_with

from defom.db import save_forest, save_forestTile

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
            return jsonify({'error': str(e)}), 400

class RegisterForest(Resource):
    ## TODO
    def post(self):
        try:
            post_data = request.get_json()

        except Exception as e:
            return jsonify({'error': str(e)}), 400
        