from flask_restful import Resource, Api, abort, request
from mongo import mongo_DB_Collection
import uuid
from json import loads
from bson.json_util import dumps
import jwt
import os
from src.APIs.static import checkXRequestIdHeader

class Users(Resource):
    
    def get(self, userId = None):
        checkXRequestIdHeader(request= request)
        res = None
        expand = request.args.get('expand', default=None)
        if (expand is not None and expand == 'dynStocks'):
            if (not userId):
                res = mongo_DB_Collection.find()
                if (not res):
                    abort(404, message='No users are present')
            else:
                res = mongo_DB_Collection.find_one({
                    'userId': uuid.UUID(userId),
                })
                if (not res):
                    abort(404, message='User not found')
        else: 
            if (not userId):
                res = mongo_DB_Collection.find({}, {'dynStocks': 0, 'kotakStockAPICreds': 0})
                if (not res):
                    abort(404, message='No users are present')
            else:
                res = mongo_DB_Collection.find_one({
                    'userId': uuid.UUID(userId),
                }, {'dynStocks': 0, 'kotakStockAPICreds': 0, 'password': 0})
                if (not res):
                    abort(404, message='User not found') 
        return loads(dumps(res)), 200

    def post(self):
        checkXRequestIdHeader(request= request)
        content_type = request.headers.get('Content-Type')
        res = {}
        if (content_type == 'application/json'):
            body = request.get_json()
            username = body['username']
            password = body['password']

            KOTAK_STOCK_API_ACCESS_TOKEN = body['KOTAK_STOCK_API_ACCESS_TOKEN']
            KOTAK_STOCK_API_CONSUMER_KEY = body['KOTAK_STOCK_API_CONSUMER_KEY']
            KOTAK_STOCK_API_CONSUMER_SECRET = body['KOTAK_STOCK_API_CONSUMER_SECRET']
            KOTAK_STOCK_API_APP_ID = body['KOTAK_STOCK_API_APP_ID']
            KOTAK_STOCK_API_USER_ID = body['KOTAK_STOCK_API_USER_ID']
            KOTAK_STOCK_API_PASSWORD = body['KOTAK_STOCK_API_PASSWORD']

            kotakStockAPICreds = jwt.encode({
                'KOTAK_STOCK_API_ACCESS_TOKEN': KOTAK_STOCK_API_ACCESS_TOKEN,
                'KOTAK_STOCK_API_CONSUMER_KEY': KOTAK_STOCK_API_CONSUMER_KEY,
                'KOTAK_STOCK_API_CONSUMER_SECRET': KOTAK_STOCK_API_CONSUMER_SECRET,
                'KOTAK_STOCK_API_APP_ID': KOTAK_STOCK_API_APP_ID,
                'KOTAK_STOCK_API_USER_ID': KOTAK_STOCK_API_USER_ID,
                'KOTAK_STOCK_API_PASSWORD': KOTAK_STOCK_API_PASSWORD,
            },os.environ.get("KOTAK_STOCK_API_SECRET"), algorithm=os.environ.get('KOTAK_STOCK_API_ENCODE_ALGO'))

            user = mongo_DB_Collection.find_one({
                'username': username,
            })
            if (user):
                abort(409, message = 'User already exists')
            userId = uuid.uuid4()
            encoded_password = jwt.encode({
                    'password': password
                    }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get('DYNSTOCKS_JWT_ALGO'))
            res = mongo_DB_Collection.insert_one({
                'userId': userId,
                'username': username,
                'password': encoded_password,
                'noOfDynStocksOwned': 0,
                'noOfTransactionsMade': 0,
                'netReturns': 0.0,
                'dynStocks': [],
                'kotakStockAPICreds': kotakStockAPICreds
            })
            if (not res):
                abort(400, message = 'User creation unsuccessful')
        return {
                    '_id' : loads(dumps(res.inserted_id)),
                    'userId': loads(dumps(userId)),
                    'username': username,
                    'noOfDynStocksOwned': 0,
                    'noOfTransactionsMade': 0,
                    'netReturns': 0.0,
                    'dynStocks': []
                }, 201

    def delete(self, userId):
        checkXRequestIdHeader(request= request)
        res = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId),
        })
        if (not res):
            abort(404, message = 'User does not exist')
        user = mongo_DB_Collection.delete_one({
            'userId': uuid.UUID(userId),
        })
        if (not user):
            abort(409, message = 'Delete unsuccessful')
        return '', 204