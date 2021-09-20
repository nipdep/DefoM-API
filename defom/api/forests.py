

from flask import make_response, request, jsonify
from flask_restful import Resource, fields, marshal_with

import cv2
import pickle

from defom.api.utils import expect
from defom.db import save_forest, save_forestTile, create_forest_page, get_latest_forest_tiles
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

class ForestView(Resource):
    def _get_RGB(self,image):
        rgb = cv2.normalize(image[:,:,[2,1,0]], None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        return rgb
    
    def _get_FM(self,image):
        fm = image[:,:,4]/image[:,:,3]
        return fm

    def _get_NDWI(self,image):
        ndwi = (image[:,:,3]-image[:,:,4])/(image[:,:,3]+image[:,:,4])
        return ndwi

    def _get_MNDWI(self,image):
        mndwi = (image[:,:,1]-image[:,:,4])/(image[:,:,1]+image[:,:,4])
        return mndwi

    def _get_VARI(self,image):
        vari = (image[:,:,1]-image[:,:,2])/(image[:,:,1]+image[:,:,2]-image[:,:,0])
        return vari

    def _get_SAVI(self,image):
        L = 0.5
        savi = ((image[...,3]-image[...,2])/(image[...,3]+image[...,2]+L))*(1+L)
        return savi

    def _get_NDVI(self,image):
        ndvi = (image[...,3]-image[...,2])/(image[...,3]+image[...,2])
        return ndvi

    def get(self, forest_id, date, mode):
        
        try:
            resp = []
            image_list, image_id_list = get_latest_forest_tiles(forest_id, date)
            mode_map = {'rgb' : self._get_RGB, 'nvdi': self._get_NDVI, 'savi' : self._get_SAVI, 'vari' : self._get_VARI, 'mndwi' : self._get_MNDWI, 'ndwi' : self._get_NDWI, 'fm' : self._get_FM}
            image_list = [mode_map[mode](im) for im in image_list]
            for i, img in enumerate(image_list):
                doc = {
                    'forest_id' : forest_id,
                    'tile_id': image_id_list[i],
                    'tile_imge': pickle.dumps(img)
                }
                resp.append(doc)
            return resp
        except Exception as e:
                return make_response(jsonify(e), 411)


