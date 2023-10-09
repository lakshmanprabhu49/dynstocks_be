from flask_restful import Resource, Api, abort, request, reqparse
from pymongo import ReturnDocument
from mongo import mongoDB_DynStocks_RealTime_Price_Collection
import uuid
from json import loads
from bson.json_util import dumps
import datetime
import pytz
import jwt
import os
from src.APIs.static import checkXRequestIdHeader

class DynStocksRealTimePrice(Resource):
    def get(self, userId, stockCode):
        checkXRequestIdHeader(request= request)
        if ('Authorization' not in request.headers):
            abort(403, message = 'You are unauthorized to make the request') 
        jwt_token = request.headers["Authorization"].split(" ")
        access_code = request.args.get('accessCode', default=None)
        if (access_code != os.environ.get("accessCode " + userId)):
            abort(403, message = 'Please enter a valid Access Code')
        expected_jwt_token = jwt.encode({
            'access_code': access_code,
        }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get('DYNSTOCKS_JWT_ALGO') )
        if (len(jwt_token) != 2 or jwt_token[1] != expected_jwt_token):
            abort(403, message = 'You are unauthorized to make the request')
        res = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
            'userId': userId
        })
        if (not res):
            abort(404, message = 'User not found')
        return loads(dumps(res)), 200
    
    def post(self):
        # POST userId and stock cod
        checkXRequestIdHeader(request= request)
        content_type = request.headers.get('Content-Type')
        if ('application/json' in content_type):
            body = request.get_json()
            userId = body['userId']
            user = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId
            })

            if (user):
                abort(409, message = 'User already exists')
            res = mongoDB_DynStocks_RealTime_Price_Collection.insert_one({
                'userId': userId,
                'stockDetails': []
            })

            if (not res):
                return "Error while creating user in real time price DB", 400

            return "User details created successfully", 201

    def put(self, userId):
        # PUT localMaxima and localMimima
        checkXRequestIdHeader(request= request)
        if ('Authorization' not in request.headers):
            abort(403, message = 'You are unauthorized to make the request') 
        jwt_token = request.headers["Authorization"].split(" ")
        access_code = request.args.get('accessCode', default=None)
        print(os.environ.get("accessCode " + userId))
        if (access_code != os.environ.get("accessCode " + userId)):
            abort(403, message = 'Please enter a valid Access Code')
        expected_jwt_token = jwt.encode({
            'access_code': access_code,
        }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get('DYNSTOCKS_JWT_ALGO') )
        if (len(jwt_token) != 2 or jwt_token[1] != expected_jwt_token):
            abort(403, message = 'You are unauthorized to make the request')
        content_type = request.headers['content-type']
        if ('application/json' in content_type):
            body = request.get_json()
            stockDetails = body['stockDetails']
            requiredUserDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId,
            })
            if (not requiredUserDetails):
                abort(404, "User not found")
            res = None
            updatedStockDetails = stockDetails
            res = mongoDB_DynStocks_RealTime_Price_Collection.find_one_and_update({
                'userId': userId
            }, {
                '$set': {
                    'userId': userId,
                    'stockDetails': updatedStockDetails
                }
            })
            if (not res):
                abort(400, "Error while updating the real time prices")
            return {
                'userId': userId,
                'stockDetails': updatedStockDetails
            }, 200



    def delete(self, userId):
        # DELETE userId
        checkXRequestIdHeader(request= request)
        res = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
            'userId': userId,
        })
        if (not res):
            abort(404, message = 'User does not exist')
        user = mongoDB_DynStocks_RealTime_Price_Collection.delete_one({
            'userId': userId,
        })
        if (not user):
            abort(409, message = 'Delete unsuccessful')
        return '', 204