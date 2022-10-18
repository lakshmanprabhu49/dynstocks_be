from flask_restful import Resource, Api, abort, request, reqparse
from pymongo import ReturnDocument
from mongo import mongo_DB_Collection
import uuid
from json import loads
from bson.json_util import dumps
import datetime
import pytz
import jwt
import os
from src.APIs.static import checkXRequestIdHeader


def transactionTimeSortFunc(e):
    return e['transactionTime']['$date']

def stockCodeSortFunc(e):
    return e['stockCode']

def transactionTypeSortFunc(e):
    return e['type']

def returnAmountSortFunc(e):
    return e['amount'] 

class Transactions(Resource):
        
    def get(self, userId = None, dynStockId = None):
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
        res = None
        limit = int(request.args.get('limit'))
        offset = int(request.args.get('offset'))
        sortCriterion = request.args.get('sortCriterion')
        sortDirection = request.args.get('sortDirection')
        filterCriterionStocks = request.args.get('filterCriterionStocks')
        filterCriterionDay = request.args.get('filterCriterionDay')
        if (dynStockId is not None):
            date_string = request.args.get('date')
            if (date_string is not None and not(date_string=='')):
                format = "%b %d %Y"
                date = datetime.datetime.strptime(date_string, format)
                next_date = date + datetime.timedelta(days=1)
                res = mongo_DB_Collection.aggregate([{
                    '$match': {
                        'userId': uuid.UUID(userId),
                    },
                }, {
                    '$unwind': '$dynStocks',
                }, {
                    '$match': {
                        'dynStocks.dynStockId': uuid.UUID(dynStockId) 
                    }
                }, {
                    '$project': {
                        'transactions': {
                            '$filter': {
                                'input': '$dynStocks.transactions',
                                'as': 'transaction',
                                'cond': {
                                    '$and': [{
                                        '$gte': ['$$transaction.transactionTime', date],
                                    }, {
                                        '$lt': ['$$transaction.transactionTime', next_date],
                                    }]
                                }
                            }
                        } 
                    }
                }])

                res = loads(dumps(list(res)))
                if (len(res) == 0):
                    return [], 200
                res = res[0]['transactions']
                transactions = [{
                    'userId': loads(dumps(transaction['userId'])),
                    'dynStockId': loads(dumps(transaction['dynStockId'])),
                    'transactionId': loads(dumps(transaction['transactionId'])),
                    'transactionTime': loads(dumps(transaction['transactionTime'])),
                    'type': transaction['type'],
                    'noOfStocks': transaction['noOfStocks'],
                    'stockCode': transaction['stockCode'],
                    'stockPrice': transaction['stockPrice'],
                    'amount': (transaction['amount'])
                    } for transaction in list(res)]
                hasMore = False if limit == 0 else limit + offset <= len(transactions)
                transactions = [transaction for transaction in transactions if transaction['dynStockId']['$uuid'] == dynStockId]
                sortDesc = False
                if (sortDirection is not None and not(sortDirection == '')):
                    if (sortDirection == 'DESC'):
                        sortDesc = True
                
                if (sortCriterion is not None and not(sortCriterion == '')):
                    if (sortCriterion == 'TransactionTime'):
                        transactions.sort(key=transactionTimeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'StockCode'):
                        transactions.sort(key=stockCodeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'TransactionType'):
                        transactions.sort(key=transactionTypeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'ReturnAmount'):
                        transactions.sort(key=returnAmountSortFunc, reverse= sortDesc)
                if (filterCriterionStocks is not None and not(filterCriterionStocks  == '')):
                    transactions = [transaction for transaction in transactions if filterCriterionStocks in transaction['stockCode']]
                if (filterCriterionDay is not None and not(filterCriterionDay == '')):
                    now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                    if (filterCriterionDay == 'Today'):
                        transactions = [transaction for transaction in transactions if now.day == datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day]
                if (limit is not None and offset is not None and (limit>0)):
                    transactions = transactions[offset: min(len(transactions), offset + limit)]
                return {
                    'hasMore': hasMore, 
                    'items': transactions}, 200
            else:
                res = mongo_DB_Collection.aggregate([{
                    '$match': {
                        'userId': uuid.UUID(userId),
                    },
                }, {
                    '$unwind': '$dynStocks',
                }, {
                    '$match': {
                        'dynStocks.dynStockId': uuid.UUID(dynStockId) 
                    }
                }, {
                    '$project': {
                        'dynStocks.transactions': 1
                    }
                }])
                res = loads(dumps(list(res)))
                if (len(res) == 0):
                    return [], 200
                res = res[0]['dynStocks']['transactions']
                transactions = [{
                    'userId': loads(dumps(transaction['userId'])),
                    'dynStockId': loads(dumps(transaction['dynStockId'])),
                    'transactionId': loads(dumps(transaction['transactionId'])),
                    'transactionTime': loads(dumps(transaction['transactionTime'])),
                    'type': transaction['type'],
                    'noOfStocks': transaction['noOfStocks'],
                    'stockCode': transaction['stockCode'],
                    'stockPrice': transaction['stockPrice'],
                    'amount': (transaction['amount'])
                    } for transaction in list(res)]

                hasMore = False if limit == 0 else limit + offset <= len(transactions)
                transactions = [transaction for transaction in transactions if transaction['dynStockId']['$uuid'] == dynStockId]
                sortDesc = False
                if (sortDirection is not None and not(sortDirection == '')):
                    if (sortDirection == 'DESC'):
                        sortDesc = True

                if (sortCriterion is not None and not(sortCriterion == '')):
                    if (sortCriterion == 'TransactionTime'):
                        transactions.sort(key=transactionTimeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'StockCode'):
                        transactions.sort(key=stockCodeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'TransactionType'):
                        transactions.sort(key=transactionTypeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'ReturnAmount'):
                        transactions.sort(key=returnAmountSortFunc, reverse= sortDesc)
                if (filterCriterionStocks is not None and not(filterCriterionStocks  == '')):
                    transactions = [transaction for transaction in transactions if filterCriterionStocks in transaction['stockCode']]
                if (filterCriterionDay is not None and not(filterCriterionDay == '')):
                    now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                    if (filterCriterionDay == 'Today'):
                        transactions = [transaction for transaction in transactions if now.day == datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day]
                if (limit is not None and offset is not None and (limit>0)):
                    transactions = transactions[offset: min(len(transactions), offset + limit)]
                return {
                    'hasMore': hasMore,
                    'items':transactions}, 200

        else:
            date_string = request.args.get('date')
            if (date_string is not None and not(date_string=='')):
                format = "%b %d %Y"
                date = datetime.datetime.strptime(date_string, format)
                next_date = date + datetime.timedelta(days=1)
                res = mongo_DB_Collection.aggregate([{
                    '$match': {
                        'userId': uuid.UUID(userId),
                    },
                }, {
                    '$unwind': '$dynStocks',
                }, {
                    '$project': {
                        'transactions': {
                            '$filter': {
                                'input': '$dynStocks.transactions',
                                'as': 'transaction',
                                'cond': {
                                    '$and': [{
                                        '$gte': ['$$transaction.transactionTime', date],
                                    }, {
                                        '$lt': ['$$transaction.transactionTime', next_date],
                                    }]
                                }
                            }
                        } 
                    }
                }])


                temp_res = loads(dumps(list(res)))
                result = []
                alreadyParsedTransactions = set();
                for item in temp_res:
                    transactions_to_be_added = []
                    for transaction in item['transactions']:
                        if (transaction['transactionTime']['$date'] not in alreadyParsedTransactions):
                            alreadyParsedTransactions.add(transaction['transactionTime']['$date'])
                            transactions_to_be_added.append(transaction)
                    result = result + transactions_to_be_added

                transactions = [{
                    'userId': loads(dumps(transaction['userId'])),
                    'dynStockId': loads(dumps(transaction['dynStockId'])),
                    'transactionId': loads(dumps(transaction['transactionId'])),
                    'transactionTime': loads(dumps(transaction['transactionTime'])),
                    'type': transaction['type'],
                    'noOfStocks': transaction['noOfStocks'],
                    'stockCode': transaction['stockCode'],
                    'stockPrice': float(transaction['stockPrice']),
                    'amount': float(transaction['amount'])
                    } for transaction in result]

                hasMore = False if limit == 0 else limit + offset <= len(transactions)
                sortDesc = False
                if (sortDirection is not None and not(sortDirection == '')):
                    if (sortDirection == 'DESC'):
                        sortDesc = True
                if (sortCriterion is not None and not(sortCriterion == '')):
                    if (sortCriterion == 'TransactionTime'):
                        transactions.sort(key=transactionTimeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'StockCode'):
                        transactions.sort(key=stockCodeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'TransactionType'):
                        transactions.sort(key=transactionTypeSortFunc, reverse= sortDesc)
                    elif (sortCriterion == 'ReturnAmount'):
                        transactions.sort(key=returnAmountSortFunc, reverse= sortDesc)
                if (filterCriterionStocks is not None and not(filterCriterionStocks  == '')):
                    transactions = [transaction for transaction in transactions if filterCriterionStocks in transaction['stockCode']]
                if (filterCriterionDay is not None and not(filterCriterionDay == '')):
                    now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                    if (filterCriterionDay == 'Today'):
                        transactions = [transaction for transaction in transactions if now.day == datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day]
                if (limit is not None and offset is not None and (limit>0)):
                    transactions = transactions[offset: min(len(transactions), offset + limit)]
                return {
                    'hasMore': hasMore,
                    'items':transactions}, 200

            res = mongo_DB_Collection.find_one({
                'userId': uuid.UUID(userId),
            })
            if (not res):
                abort(404, message='User not found')
            res = mongo_DB_Collection.aggregate([{
                '$match': {
                    'userId': uuid.UUID(userId),
                },
            }, {
                '$project': {
                    'transactions': {
                        '$reduce': {
                            'input': '$dynStocks.transactions',
                            'initialValue': [],
                            'in': {'$concatArrays': ['$$value', '$$this']}
                        }
                    }
                }
            }])

            temp_res = loads(dumps(list(res)))
            result = []
            alreadyParsedTransactions = set();
            for item in temp_res:
                transactions_to_be_added = []
                for transaction in item['transactions']:
                    if (transaction['transactionTime']['$date'] not in alreadyParsedTransactions):
                        alreadyParsedTransactions.add(transaction['transactionTime']['$date'])
                        transactions_to_be_added.append(transaction)
                result = result + transactions_to_be_added
            transactions = [{
                    'userId': loads(dumps(transaction['userId'])),
                    'dynStockId': loads(dumps(transaction['dynStockId'])),
                    'transactionId': loads(dumps(transaction['transactionId'])),
                    'transactionTime': loads(dumps(transaction['transactionTime'])),
                    'type': transaction['type'],
                    'noOfStocks': transaction['noOfStocks'],
                    'stockCode': transaction['stockCode'],
                    'stockPrice': float(transaction['stockPrice']),
                    'amount': float(transaction['amount'])
                    } for transaction in result]
            
            hasMore = False if limit == 0 else limit + offset <= len(transactions)
            sortDesc = False
            if (sortDirection is not None and not(sortDirection == '')):
                    if (sortDirection == 'DESC'):
                        sortDesc = True
            if (sortCriterion is not None and not(sortCriterion == '')):
                if (sortCriterion == 'TransactionTime'):
                    transactions.sort(key=transactionTimeSortFunc, reverse= sortDesc)
                elif (sortCriterion == 'StockCode'):
                    transactions.sort(key=stockCodeSortFunc, reverse= sortDesc)
                elif (sortCriterion == 'TransactionType'):
                    transactions.sort(key=transactionTypeSortFunc, reverse= sortDesc)
                elif (sortCriterion == 'ReturnAmount'):
                    transactions.sort(key=returnAmountSortFunc, reverse= sortDesc)
            if (filterCriterionStocks is not None and not(filterCriterionStocks  == '')):
                transactions = [transaction for transaction in transactions if filterCriterionStocks in transaction['stockCode']]
            if (filterCriterionDay is not None and not(filterCriterionDay == '')):
                now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
                if (filterCriterionDay == 'Today'):
                    transactions = [transaction for transaction in transactions if now.day == datetime.datetime.fromtimestamp(transaction['transactionTime']['$date']/ 1000.0).day]
            if (limit is not None and offset is not None and (limit>0)):
                transactions = transactions[offset: min(len(transactions), offset + limit)]
            return {
                    'hasMore': hasMore,
                    'items':transactions}, 200

    def post(self, userId, dynStockId):
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
            transactionId = body['transactionId']
            type = body['type']
            noOfStocks = body['noOfStocks']
            stockCode = body['stockCode']
            stockPrice = body['stockPrice']
            netReturns = user['netReturns']
            noOfTransactionsMade = user['noOfTransactionsMade'] + 1
            multiplier = 1.0 if type == 'SELL' else -1.0
            netReturns += multiplier * noOfStocks * stockPrice/1.0
            
            currentDynStocks = mongo_DB_Collection.find_one({
                'userId': uuid.UUID(userId),
                'dynStocks.dynStockId': uuid.UUID(dynStockId),
            }, {'dynStocks' : 1})['dynStocks']

            index = -1
            for i in range(len(currentDynStocks)):
                if (currentDynStocks[i]['dynStockId'] == uuid.UUID(dynStockId)):
                    index = i
                    break
            currentStocksAvailableForTrade = currentDynStocks[index]['stocksAvailableForTrade']
            currentTransactions = mongo_DB_Collection.find_one({
                'userId': uuid.UUID(userId),
                'dynStocks.dynStockId': uuid.UUID(dynStockId),
            }, {'dynStocks' : 1})['dynStocks'][index]['transactions']

            transactionId = uuid.uuid3(uuid.NAMESPACE_URL, str(transactionId))
            transactions = list(currentTransactions)
            transactionTime = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
            transactions.append({
                'userId': uuid.UUID(userId),
                'dynStockId': uuid.UUID(dynStockId),
                'transactionId': transactionId,
                'transactionTime': transactionTime,
                'type': type,
                'noOfStocks': noOfStocks,
                'stockCode': stockCode,
                'stockPrice': stockPrice / 1.0,
                'amount': (noOfStocks * stockPrice) / 1.0
            })

            updatedUser = mongo_DB_Collection.find_one_and_update({
                'userId': uuid.UUID(userId),
                'dynStocks.dynStockId': uuid.UUID(dynStockId),
            },{
                '$set': {
                    'netReturns': netReturns,
                    'noOfTransactionsMade': noOfTransactionsMade,
                    'dynStocks.$.lastTradedPrice': stockPrice/ 1.0,
                    'dynStocks.$.lastTransactionType': type,
                    'dynStocks.$.lastTransactionTime': transactionTime,
                    'dynStocks.$.stocksAvailableForTrade': (currentStocksAvailableForTrade + noOfStocks if type == 'BUY' else currentStocksAvailableForTrade - noOfStocks) ,
                    'dynStocks.$.transactions': transactions
                },
            }, None, None, None, ReturnDocument.AFTER)
            
            return {
                    'userId': loads(dumps(updatedUser['userId'])),
                    'dynStockId': loads(dumps(uuid.UUID(dynStockId))),
                    'transactionId': loads(dumps(transactionId)),
                    'transactionTime': loads(dumps(transactionTime)),
                    'type': type,
                    'noOfStocks': noOfStocks,
                    'stockCode': stockCode,
                    'stockPrice': stockPrice,
                    'amount': (noOfStocks * stockPrice)
                    }, 201