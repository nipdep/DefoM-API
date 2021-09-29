from datetime import datetime
from flask import make_response, request, jsonify, send_file
from flask_restful import Resource, fields, marshal_with

import cv2
import os, glob
import pickle
from bson.objectid import ObjectId
import numpy as np


from defom.api.utils import expect
from defom.db import get_thread_data, create_thread, get_message_data, add_message, add_comment

class ThreadHandler(Resource):
    def get(self, thread_id):
        try:
            thr_id = ObjectId(thread_id)
            res = get_thread_data(thr_id)
            return jsonify(res)
        except Exception as e:
            return jsonify({'error': str(e)})
    
    def post(self):
        try:
            thread_data = request.get_json()
            res = create_thread(thread_data)
            return jsonify(res)
        except Exception as e:
            return jsonify({'error': str(e)})
        
    def update(self):
        ...   
    
    def delete(self):
        ...


class MessageHandler(Resource):
    def get(self, sms_id):
        try:
            sms_id = ObjectId(sms_id)
            res = get_message_data(sms_id)
            return jsonify(res)
        except Exception as e:
            return jsonify({'error': str(e)})
         
    
    def post(self):
        try:
            message_data = request.get_json()
            message_data['_id'] = ObjectId()
            thr_id = message_data.pop('thread_id', None)
            thread_id = ObjectId(str(thr_id))
            res = add_message(thread_id, message_data)
            return jsonify(res)
        except Exception as e:
            return jsonify({'error': str(e)})

    def update(self):
        ...   
    
    def delete(self):
        ...

class CommentHandler(Resource):
    def get(self):
        ... 
    
    def post(self):
        try:
            comment_data = request.get_json()
            comment_data['_id'] = ObjectId()
            thr_id = comment_data.pop('thread_id', None)
            thread_id = ObjectId(str(thr_id))
            sms_id = comment_data.pop('message_id', None)
            message_id = ObjectId(str(sms_id))
            res = add_message(thread_id, message_id, comment_data)
            return jsonify(res)
        except Exception as e:
            return jsonify({'error': str(e)})

    def update(self):
        ...   
    
    def delete(self):
        ...
