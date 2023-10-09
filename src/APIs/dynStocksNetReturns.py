from flask_restful import Resource, Api, abort, request, reqparse
from pymongo import ReturnDocument
from mongo import mongoDB_DynStocks_Collection
import uuid
from json import loads
from bson.json_util import dumps
import datetime
import pytz
import jwt
import os
from src.APIs.static import checkXRequestIdHeader

class DynStocksNetReturns(Resource):
        
    def get(self, userId, dynStockId):
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
        res = mongoDB_DynStocks_Collection.find_one({
            'userId': userId
        })
        if (not res):
            abort(404, message = 'User not found')
        period = request.args.get('period', default=None)
        if (not period):
            abort(400, message = 'Please enter a valid period')
        currentDynStocks = mongoDB_DynStocks_Collection.find_one({
                'userId': userId,
                'dynStocks.dynStockId': dynStockId
            }, {'dynStocks' : 1})['dynStocks']
        currentDynStocks = [currentDynStock for currentDynStock in currentDynStocks if (currentDynStock['dynStockId'] == dynStockId)]
        if (currentDynStocks is None or len(list(currentDynStocks)) == 0):
            abort(500, message = 'DynStock does not exist')
        transactions = list(loads(dumps(currentDynStocks[0]['transactions'])))
        transactions.reverse()
        now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        netReturns = 0.0
        if (period == '1h'):
            for transaction in transactions:
                if now.hour > datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).hour:
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '1d'):
            for transaction in transactions:
                if now.day > datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day:
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '1w'):
            for transaction in transactions:
                if now.day > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day + 6):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '1m'):
            for transaction in transactions:
                if now.month > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).month):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '3m'):
            for transaction in transactions:
                if now.month > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).month + 2):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '6m'):
            for transaction in transactions:
                if now.month > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).month + 5):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '1y'):
            for transaction in transactions:
                if now.year > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).year):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '2y'):
            for transaction in transactions:
                if now.year > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).year + 1):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '3y'):
            for transaction in transactions:
                if now.year > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).year + 2):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '4y'):
            for transaction in transactions:
                if now.year > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).year + 3):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        elif (period == '5y'):
            for transaction in transactions:
                if now.year > (datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).year + 4):
                    break
                else:
                    multiplier = -1 if transaction['type'] == 'BUY' else 1
                    netReturns = netReturns + transaction['amount'] * multiplier
        else:
            for transaction in transactions:
                multiplier = -1 if transaction['type'] == 'BUY' else 1
                netReturns = netReturns + transaction['amount'] * multiplier
        return netReturns, 200