from flask_restful import Resource, Api, abort, request
from mongo import mongo_DB_Collection, mongo_DB
from pymongo import ReturnDocument
import uuid
from json import loads
from bson.json_util import dumps
import datetime
import pytz
import jwt
import os
from src.APIs.static import checkXRequestIdHeader

class DynStocks(Resource):
    def get(self, userId):
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
        res = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId)
        })
        if (not res):
            abort(404, message = 'User not found')
        return loads(dumps(res['dynStocks'])), 200

    def post(self, userId):
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
        user = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId),
        })
        if (not user):
            abort(404, message= 'User not found')
        
        content_type = request.headers.get('Content-Type')
        if ('application/json' in content_type):
            body = request.get_json()
            stockCode = body['stockCode']
            yFinStockCode = body['yFinStockCode']
            instrumentToken = body['instrumentToken']
            stockName = body['stockName']
            DSTPUnit = body['DSTPUnit']
            noOfStocks = body['noOfStocks']
            exchange = body['exchange']
            stockType = body['stockType']
            transactionForCreateDynStock = body['transactionForCreateDynStock'] if 'transactionForCreateDynStock' in body else None
            BTPr = 0.0
            STPr = 0.0
            BTPe = 0.0
            STPe = 0.0
            netReturns = user['netReturns']
            noOfDynStocksOwned = user['noOfDynStocksOwned']
            noOfTransactionsMade = user['noOfTransactionsMade']
            HETolerance = body['HETolerance'] / 1.0
            LETolerance = body['LETolerance'] / 1.0
            if (DSTPUnit == 'Price'):
                if ('BTPr' not in body.keys() or 'STPr' not in body.keys()):
                    abort(500, message = 'When DSTPUnit is Price, BTPr and STPr are required')
                BTPr = body['BTPr']
                STPr = body['STPr']
            elif (DSTPUnit == 'Percentage'):
                if ('BTPe' not in body.keys() or 'STPe' not in body.keys()):
                    abort(500, message = 'When DSTPUnit is Percentage, BTPe and STPe are required')
                BTPe = body['BTPe']
                STPe = body['STPe']
            else:
                abort(500, message = 'Allowed values for DSTPUnit are Price and Percentage')
            currentDynStocks = mongo_DB_Collection.find_one({
                'userId': uuid.UUID(userId),
            }, {'dynStocks' : 1})['dynStocks']
            dynStocks = list(currentDynStocks)
            dynStocks_Filtered = [dynStock for dynStock in dynStocks if (dynStock['stockCode'] == stockCode)]
            if (len(dynStocks_Filtered) > 0):
                abort(409, message= 'DynStock already created for the given stockCode')
            dynStockId = uuid.uuid4()
            transactionId = uuid.uuid3(uuid.NAMESPACE_URL, str(transactionForCreateDynStock['transactionId'])) if transactionForCreateDynStock is not None else None
            transactionTime = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) if transactionForCreateDynStock is not None else None
            transactionToBeCreated = {
                'userId': uuid.UUID(userId),
                'dynStockId': dynStockId,
                'transactionId': transactionId,
                'transactionTime': transactionTime,
                'type': transactionForCreateDynStock['type'],
                'noOfStocks': transactionForCreateDynStock['noOfStocks'],
                'stockCode': transactionForCreateDynStock['stockCode'],
                'stockPrice': transactionForCreateDynStock['stockPrice'] / 1.0,
                'amount': (noOfStocks * transactionForCreateDynStock['stockPrice']) / 1.0,
            } if transactionForCreateDynStock is not None else None
            if (BTPr):
                dynStocks.insert(0, {
                    'userId': uuid.UUID(userId),
                    'dynStockId': dynStockId,
                    'stockCode': stockCode,
                    'yFinStockCode': yFinStockCode,
                    'instrumentToken': instrumentToken,
                    'lastTradedPrice': transactionForCreateDynStock['stockPrice'] / 1.0,
                    'lastTransactionType': 'BUY',
                    'lastTransactionTime': transactionTime,
                    'stocksAvailableForTrade': noOfStocks,
                    'stockName': stockName,
                    'exchange': exchange,
                    'stockType': stockType,
                    'DSTPUnit': DSTPUnit,
                    'BTPr': BTPr,
                    'STPr': STPr,
                    'BTPe': 0.0,
                    'STPe': 0.0,
                    'noOfStocks': noOfStocks,
                    'stallTransactions': False,
                    'HETolerance': HETolerance,
                    'LETolerance': LETolerance,
                    'transactions': [transactionToBeCreated] if transactionToBeCreated is not None else [],
                })
            elif (BTPe):
                dynStocks.insert(0, {
                    'userId': uuid.UUID(userId),
                    'dynStockId': dynStockId,
                    'stockCode': stockCode,
                    'yFinStockCode': yFinStockCode,
                    'instrumentToken': instrumentToken,
                    'lastTradedPrice': transactionForCreateDynStock['stockPrice'] / 1.0,
                    'lastTransactionType': 'BUY',
                    'lastTransactionTime': transactionTime,
                    'stocksAvailableForTrade': noOfStocks,
                    'stockName': stockName,
                    'exchange': exchange,
                    'stockType': stockType,
                    'DSTPUnit': DSTPUnit,
                    'BTPr': 0.0,
                    'STPr': 0.0,
                    'BTPe': BTPe,
                    'STPe': STPe,
                    'noOfStocks': noOfStocks,
                    'stallTransactions': False,
                    'HETolerance': HETolerance,
                    'LETolerance': LETolerance,
                    'transactions': [transactionToBeCreated] if transactionToBeCreated is not None else [],
                })

            noOfTransactionsMade += 1
            noOfDynStocksOwned += 1
            multiplier = 1.0 if transactionToBeCreated['type'] == 'SELL' else -1.0
            netReturns += multiplier * noOfStocks * transactionForCreateDynStock['stockPrice']/1.0
            updatedUser = mongo_DB_Collection.find_one_and_update({
                'userId': uuid.UUID(userId),
            },{
                '$set': {
                    'noOfTransactionsMade': noOfTransactionsMade,
                    'noOfDynStocksOwned': noOfDynStocksOwned,
                    'netReturns': netReturns,
                    'dynStocks': dynStocks
                },
            }, None, None, None, ReturnDocument.AFTER)

            return {
                'userId': loads(dumps(updatedUser['userId'])),
                'dynStockId': loads(dumps(dynStockId)),
                'stockCode': stockCode,
                'yFinStockCode': yFinStockCode,
                'instrumentToken': instrumentToken,
                'lastTradedPrice': transactionForCreateDynStock['stockPrice'] / 1.0,
                'lastTransactionType': 'BUY',
                'lastTransactionTime': loads(dumps(transactionTime)),
                'stocksAvailableForTrade': noOfStocks,
                'stockName': stockName,
                'exchange': exchange,
                'stockType': stockType,
                'DSTPUnit': DSTPUnit,
                'BTPr': BTPr,
                'BTPe': BTPe,
                'STPr': STPr,
                'STPe': STPe,
                'noOfStocks': noOfStocks,
                'stallTransactions': False,
                'HETolerance': HETolerance,
                'LETolerance': LETolerance,
                'transactions': [{
                    'userId': loads(dumps(updatedUser['userId'])),
                    'dynStockId': loads(dumps(dynStockId)),
                    'transactionId': loads(dumps(transactionId)),
                    'transactionTime': loads(dumps(transactionTime)),
                    'type': transactionForCreateDynStock['type'],
                    'noOfStocks': noOfStocks,
                    'stockCode': stockCode,
                    'stockPrice': transactionForCreateDynStock['stockPrice'] / 1.0,
                    'amount': (noOfStocks * transactionForCreateDynStock['stockPrice'] / 1.0)
                }] if transactionToBeCreated is not None else [],
                }, 201

    def put(self, userId, dynStockId):
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
        res = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId),
        })
        if (not res):
            abort(404, message= 'User not found')
        content_type = request.headers.get('Content-Type')
        if ('application/json' in content_type):
            body = request.get_json()
            stockCode = body['stockCode']
            yFinStockCode = body['yFinStockCode'] if ('yFinStockCode' in body) else None
            instrumentToken = body['instrumentToken'] if ('instrumentToken' in body) else None
            stockName = body['stockName'] if ('stockName' in body) else None
            noOfStocks = body['noOfStocks'] if ('noOfStocks' in body) else None
            DSTPUnit = body['DSTPUnit']
            BTPr = None
            STPr = None
            BTPe = None
            STPe = None
            stallTransactions = body['stallTransactions']
            HETolerance = body['HETolerance'] / 1.0
            LETolerance = body['LETolerance'] / 1.0
            if (DSTPUnit == 'Price'):
                if ('BTPr' not in body.keys() or 'STPr' not in body.keys()):
                    abort(500, message = 'When DSTPUnit is Price, BTPr and STPr are required')
                BTPr = body['BTPr']
                STPr = body['STPr']
            elif (DSTPUnit == 'Percentage'):
                if ('BTPe' not in body.keys() or 'STPe' not in body.keys()):
                    abort(500, message = 'When DSTPUnit is Percentage, BTPe and STPe are required')
                BTPe = body['BTPe']
                STPe = body['STPe']
            else:
                abort(500, message = 'Allowed values for DSTPUnit are Price and Percentage')
            currentDynStocks = mongo_DB_Collection.find_one({
                'userId': uuid.UUID(userId),
                'dynStocks.dynStockId': uuid.UUID(dynStockId)
            }, {'dynStocks' : 1})['dynStocks']


            if (currentDynStocks is None or len(list(currentDynStocks)) == 0):
                abort(500, message = 'DynStock does not exist')
            
            currentDynStock = [dynStock for dynStock in list(currentDynStocks) if (dynStock['dynStockId'] == uuid.UUID(dynStockId))][0]
            currentDynStock['stockCode'] = stockCode if (stockCode is not None) else currentDynStock['stockCode']
            currentDynStock['stockName'] = stockName if (stockName is not None) else currentDynStock['stockName']
            currentDynStock['yFinStockCode'] = yFinStockCode if (yFinStockCode is not None) else currentDynStock['yFinStockCode']
            currentDynStock['instrumentToken'] = instrumentToken if (instrumentToken is not None) else currentDynStock['instrumentToken']
            currentDynStock['noOfStocks'] = noOfStocks if (noOfStocks is not None) else currentDynStock['noOfStocks']
            currentDynStock['stallTransactions'] = stallTransactions
            currentDynStock['HETolerance'] = HETolerance
            currentDynStock['LETolerance'] = LETolerance

            if (DSTPUnit == 'Price'):
                currentDynStock['DSTPUnit'] = DSTPUnit
                currentDynStock['BTPr'] = BTPr
                currentDynStock['STPr'] = STPr
                currentDynStock['BTPe'] = 0.0
                currentDynStock['STPe'] = 0.0
            elif (DSTPUnit == 'Percentage'):
                currentDynStock['DSTPUnit'] = DSTPUnit
                currentDynStock['BTPr'] = 0.0
                currentDynStock['STPr'] = 0.0
                currentDynStock['BTPe'] = BTPe
                currentDynStock['STPe'] = STPe
            
            res = mongo_DB_Collection.find_one_and_update({
                'userId': uuid.UUID(userId),
                'dynStocks.dynStockId': uuid.UUID(dynStockId)
            }, {
                '$set': {
                    'dynStocks.$': currentDynStock,
                }
            })

            return {
            'userId': loads(dumps(currentDynStock['userId'])),
            'dynStockId': loads(dumps(currentDynStock['dynStockId'])),
            'stockCode': currentDynStock['stockCode'],
            'yFinStockCode': currentDynStock['yFinStockCode'],
            'instrumentToken': currentDynStock['instrumentToken'],
            'lastTradedPrice': currentDynStock['lastTradedPrice'],
            'lastTransactionType': currentDynStock['lastTransactionType'],
            'lastTransactionTime': loads(dumps(currentDynStock['lastTransactionTime'])),
            'stocksAvailableForTrade': currentDynStock['stocksAvailableForTrade'],
            'stockName': currentDynStock['stockName'],
            'exchange': currentDynStock['exchange'],
            'stockType': currentDynStock['stockType'],
            'DSTPUnit': currentDynStock['DSTPUnit'],
            'BTPr': currentDynStock['BTPr'],
            'BTPe': currentDynStock['BTPe'],
            'STPr': currentDynStock['STPr'],
            'STPe': currentDynStock['STPe'],
            'noOfStocks': currentDynStock['noOfStocks'],
            'stallTransactions': stallTransactions,
            'HETolerance': HETolerance,
            'LETolerance': LETolerance,
            'transactions': [{
                'userId': loads(dumps(transaction['userId'])),
                'dynStockId': loads(dumps(transaction['dynStockId'])),
                'transactionId': loads(dumps(transaction['transactionId'])),
                'transactionTime': loads(dumps(transaction['transactionTime'])),
                'type': transaction['type'],
                'noOfStocks': transaction['noOfStocks'],
                'stockCode': transaction['stockCode'],
                'stockPrice': transaction['stockPrice'],
                'amount': (transaction['amount'])
            } for transaction in currentDynStock['transactions']],
            }, 200
            

    def delete(self, userId, dynStockId):
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
        user = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId),
        })
        if (not user):
            abort(404, message = 'User not found')
        dynStocks = mongo_DB_Collection.find_one({
            'userId': uuid.UUID(userId),
        }, { 'dynStocks': 1})['dynStocks']
        
        netReturns = user['netReturns']
        noOfDynStocksOwned = user['noOfDynStocksOwned'] - 1
        noOfTransactionsMade = user['noOfTransactionsMade']

        dynStocks_Filtered = [dynStock for dynStock in dynStocks if (dynStock['dynStockId'] == uuid.UUID(dynStockId))]
        if (len(dynStocks_Filtered) == 0):
            abort(404, message = 'DynStock does not exist')
        
        dynStocks_Filtered = [dynStock for dynStock in dynStocks if not(dynStock['dynStockId'] == uuid.UUID(dynStockId))]
        res = mongo_DB_Collection.find_one_and_update({
            'userId': uuid.UUID(userId),
        }, {
            '$set': {
                'netReturns': netReturns,
                'noOfDynStocksOwned': noOfDynStocksOwned,
                'noOfTransactionsMade': noOfTransactionsMade,
                'dynStocks': dynStocks_Filtered
            }
        })
        return '',204