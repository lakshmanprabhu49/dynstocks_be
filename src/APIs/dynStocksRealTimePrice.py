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
        # POST userId
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
    
    def post(self, userId):
        # Create a new Stock Code entry
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
            currentStockDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId,
            }, {'stockDetails': 1})['stockDetails']
            existingStockCodes = set()
            for currentStockDetail in currentStockDetails:
                existingStockCodes.add(currentStockDetail['stockCode'])
            if (body['stockCode'] in existingStockCodes):
                abort(400, message = 'Real Time price already present for stock code')
            if (not currentStockDetails):
                currentStockDetails = []
            updatedStockDetails = currentStockDetails
            updatedStockDetails.append({
                'stockCode': body['stockCode'],
                'currentLocalMaximumPrice': body['currentLocalMaximumPrice'],
                'currentLocalMinimumPrice': body['currentLocalMinimumPrice']
            })
            res = mongoDB_DynStocks_RealTime_Price_Collection.find_one_and_update({
                'userId': userId
            }, {
                '$set': {
                    'userId': userId,
                    'stockDetails': updatedStockDetails
                }
            })
            if (not res):
                abort(400, message = "Error while creating the real time prices")
            return {
                'userId': userId,
                'stockDetails': updatedStockDetails
            }, 200

    def put(self, userId):
        # PUT localMaxima and localMimima, only for stockCodes where prices got updated 
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
            # Body contains only the stockCode whose currentLocalMaximum and currentLocalMinimum are updated 
            newStockDetails = body['stockDetails']
            requiredUserDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId,
            })
            if (not requiredUserDetails):
                abort(404, message = "User not found")
            currentStockDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId,
            }, {'stockDetails': 1})['stockDetails'] 
            res = None
            newStockDetailsMap = {}
            for newStockDetail in newStockDetails:
                newStockDetailsMap[newStockDetail['stockCode']] = newStockDetail
            print(newStockDetailsMap)
            updatedStockDetails = []
            for currentStockDetail in currentStockDetails:
                stockCode = currentStockDetail['stockCode']
                if (newStockDetailsMap.get(stockCode) is not None):
                    # Update with new value
                    updatedStockDetails.append(newStockDetailsMap[stockCode])
                else:
                    updatedStockDetails.append(currentStockDetail)
            print(updatedStockDetails)
            res = mongoDB_DynStocks_RealTime_Price_Collection.find_one_and_update({
                'userId': userId
            }, {
                '$set': {
                    'userId': userId,
                    'stockDetails': updatedStockDetails
                }
            })
            if (not res):
                abort(400, message="Error while updating the real time prices")
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
    
    def delete(self, userId, stockCode):
        # Delete stock Code real time price subscription
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
        requiredUserDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
                'userId': userId,
            })
        if (not requiredUserDetails):
            abort(404, message = "User not found")
        currentStockDetails = mongoDB_DynStocks_RealTime_Price_Collection.find_one({
            'userId': userId,
        }, {'stockDetails': 1})['stockDetails']
        existingStockCodes = set()
        for currentStockDetail in currentStockDetails:
            existingStockCodes.add(currentStockDetail['stockCode'])
        if (stockCode not in existingStockCodes):
            abort(400, message = 'Real Time price not present for stock code')
        updatedStockDetails = [stockDetail for stockDetail in currentStockDetails if not (stockDetail['stockCode'] == stockCode)] 
        res = mongoDB_DynStocks_RealTime_Price_Collection.find_one_and_update({
            'userId': userId
        }, {
            '$set': {
                'userId': userId,
                'stockDetails': updatedStockDetails
            }
        })
        if (not res):
            abort(400, message = "Error while deleting the real time prices")
        return {
            'userId': userId,
            'stockDetails': updatedStockDetails
        }, 200