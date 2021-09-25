
from datetime import datetime
from flask import make_response, request, jsonify, send_file
from flask_restful import Resource, fields, marshal_with

import cv2
import os, glob
import pickle
from bson.objectid import ObjectId


from defom.api.utils import expect
from defom.db import (save_forest, save_forestTile, create_forest_page,
 get_latest_forest_tiles, get_user, get_forest_tiles, getTileAllDetails, getTileView)
from defom.src.SentinelhubClient import SentilhubClient


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask_jwt_extended import (
    jwt_required  
)

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
            forest_data['location'] = expect(post_data['location'], list, 'country')
            forest_data['boundary'] = expect(post_data['forest_boundary'], dict, 'forest_boundary')
            forest_data['status'] = "new"
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

class ForestTileDetails(Resource):
    # @jwt_required
    def post(self):

        try:
            post_data = request.get_json()
            forest_id = expect(post_data['forest_id'], str, 'forest_id')
            tile_id = expect(post_data['tile_id'], int, 'tile_id')
            date = expect(post_data['date'], str, 'date')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        try:
            dt_date = datetime.strptime(date, '%Y-%m-%d')
            dt_date = datetime.combine(dt_date, datetime.min.time())
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        
        try:
            forest_id = ObjectId(forest_id)
            tile_data = getTileAllDetails(forest_id, tile_id, dt_date)
            # mode_map = {'rgb' : self._get_RGB, 'nvdi': self._get_NDVI, 'savi' : self._get_SAVI, 'vari' : self._get_VARI, 'mndwi' : self._get_MNDWI, 'ndwi' : self._get_NDWI, 'fm' : self._get_FM}
            # image_list = [mode_map[mode](im) for im in image_list]
            # for i, img in enumerate(image_list):
            #     doc = {
            #         'forest_id' : forest_id,
            #         'tile_id': image_id_list[i],
            #         'tile_imge': pickle.dumps(img)
            #     }
            #     resp.append(doc)
            return make_response(jsonify(tile_data), 200)
        except Exception as e:
                return make_response(jsonify(e), 411)

class ForestTileView(Resource):

    def __init__(self):
        self.dir = './defom/images'
        self.cached_image = {}

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

    def folder_cleaner(self):
        filelist = glob.glob(os.path.join(self.dir, "*.png"))
        for f in filelist:
            os.remove(f)

    def get(self, forest_id, tile_id, mode):
        self.folder_cleaner()

        forest_id = str(forest_id)
        tile_id = int(tile_id)
        f_id = ObjectId(forest_id)
        ref_id = str(forest_id)+"_"+str(tile_id)
        if (self.cached_image == {}) or (self.cached_image["ref_id"] != ref_id):
            ch5_image = getTileView(f_id, tile_id)
            self.cached_image['ref_id'] = ref_id
            self.cached_image['image'] = ch5_image
        else:
            ch5_image = self.cached_image['image']

        mode_map = {'rgb' : self._get_RGB, 'nvdi': self._get_NDVI, 'savi' : self._get_SAVI, 'vari' : self._get_VARI, 'mndwi' : self._get_MNDWI, 'ndwi' : self._get_NDWI, 'fm' : self._get_FM}
        prep_image = mode_map[mode](ch5_image)

        f_path = f"./defom/images/{ref_id}_{mode}.png"
        if mode == "rgb":
            plt.imsave(f_path, prep_image)
        else:
            plt.imsave(f_path, prep_image, cmap='RdYlGn', vmin=-1, vmax=1)
        return send_file(f_path)
        


class ForestTiles(Resource):
    @jwt_required
    def post(self):
        try:
            post_data = request.get_json()
            email = expect(post_data['email'], str, 'email')
            date = expect(post_data['date'], str, 'date')
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        try:
            dt_date = datetime.strptime(date, '%Y-%m-%d')
            dt_date = datetime.combine(dt_date, datetime.min.time())
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)

        try:
            doc = get_user(email)
            forest_id = doc['forest_id']
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400)   

        try:
            res = get_forest_tiles(forest_id)
            ft = res['forest_tiles']
            for tile in ft:
                up, down = tile['bbox']
                up_bbox = [up[::-1],down[::-1]]
                tile['bbox'] = up_bbox
            res['location'] = res['location'][::-1]
            return make_response(jsonify(res), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 400) 

