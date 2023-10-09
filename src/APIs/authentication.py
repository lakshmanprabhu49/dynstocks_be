from flask_restful import Resource, Api, abort, request
from mongo import mongoDB_DynStocks_Collection, mongo_DB
from pymongo import ReturnDocument
import uuid
from json import loads
from bson.json_util import dumps
import datetime
import pytz
import jwt
import os
from src.APIs.static import checkXRequestIdHeader

class Authentication(Resource):
    def post(self, type, userId = None):
        checkXRequestIdHeader(request= request)
        if (type == 'login'):
            content_type = request.headers.get('Content-Type')
            if ('application/json' in content_type):
                body = request.get_json()
                username = body['username'] if 'username' in body else None
                password = body['password'] if 'password' in body else None
                if (username is None or password is None):
                    abort(409, message= "Please provide all the user credentials")
                user = mongoDB_DynStocks_Collection.find_one({
                    'username': username,
                    'password': jwt.encode({
                        'password': password
                    }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get('DYNSTOCKS_JWT_ALGO'),)
                })
                if (not user):
                    abort(404, message= 'Please provide valid credentials')
                return {'message': 'Login Successful',
                    'userId': loads(dumps(user['userId']))['$uuid']}, 200
        elif (type == 'logout'):
            if (userId is None):
                abort(409, message = "Please provide the userId")
            return {'message': 'Logged out Successfully', 'userId': userId}, 200
