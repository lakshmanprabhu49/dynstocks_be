from email import message
from re import I
from ks_api_client import ks_api
from flask import current_app
from flask_restful import Resource, Api, abort, request, reqparse
import ks_api_client
from mongo import mongoDB_DynStocks_Collection
import uuid
from json import loads
from bson.json_util import dumps
from dotenv import load_dotenv, find_dotenv
import os
import jwt
import datetime
import pytz
from src.APIs.static import checkXRequestIdHeader

load_dotenv(find_dotenv())

client_global = None

def orderReportStatusSort(e):
    return e['status']

def orderReportOrderIdSort(e):
    return e['orderId']

class KotakStock(Resource):
    def kotak_login(self, userId):
        try:
            access_code = request.args.get('accessCode', default=None)
            if (access_code == None or access_code == ''):
                abort(409, message= 'Please provide the access code')
            user = mongoDB_DynStocks_Collection.find_one({
                'userId': userId,
            })
            if (not user):
                abort(404, message='User not found')
            kotakStockAPICreds = jwt.decode(user['kotakStockAPICreds'], os.environ.get('KOTAK_STOCK_API_SECRET'), algorithms=[
                os.environ.get('KOTAK_STOCK_API_ENCODE_ALGO')
            ])
            access_token = kotakStockAPICreds['KOTAK_STOCK_API_ACCESS_TOKEN']
            consumer_key = kotakStockAPICreds['KOTAK_STOCK_API_CONSUMER_KEY']
            consumer_secret = kotakStockAPICreds['KOTAK_STOCK_API_CONSUMER_SECRET']
            app_id = kotakStockAPICreds['KOTAK_STOCK_API_APP_ID']
            user_id = kotakStockAPICreds['KOTAK_STOCK_API_USER_ID']
            password = kotakStockAPICreds['KOTAK_STOCK_API_PASSWORD']
            client = ks_api.KSTradeApi(access_token = access_token, userid = user_id, consumer_key = consumer_key,
                                       ip = "127.0.0.1",
                                        app_id = app_id, consumer_secret = consumer_secret, host="https://ctradeapi.kotaksecurities.com/apim")

            client.login(password = password)
            client.session_2fa(access_code = access_code)
            os.environ["accessCode " + userId] = str(access_code) 
            os.environ["lastDay"] = str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')).day)
            temp_file = open('temp.txt', 'w')
            temp_file.write('lastDay:'+ os.environ.get('lastDay'))
            #  + '\n' + 'accessCode ' +userId + ': '+ os.environ.get("accessCode " + userId))
            temp_file.close()
            return (client)
        except ks_api_client.ApiException as e:
            print(e)
            abort(400, message= e['fault']['message'])


    def get(self, userId, type, typeValue = None):
        try:
            checkXRequestIdHeader(request= request)
            if ('Authorization' not in request.headers):
                abort(403, message = 'You are unauthorized to make the request') 
            jwt_token = request.headers["Authorization"].split(" ")
            access_code = request.args.get('accessCode', default=None)
            if (access_code != os.environ.get("accessCode " + userId)):
                abort(403, message = 'Please enter a valid Access Code')
            expected_jwt_token = jwt.encode({
                'access_code': access_code,
            }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get('DYNSTOCKS_JWT_ALGO'))
            if (len(jwt_token) != 2 or jwt_token[1] != expected_jwt_token):
                abort(403, message = 'You are unauthorized to make the request') 
            client = self.kotak_login(userId)
            if (type == 'orderReport'):
                res = client.order_report()
                instrumentToken = request.args.get('instrumentToken', default= None)
                if (instrumentToken is not None):
                    res["success"] = [order for order in res["success"] if order["instrumentToken"] == int(instrumentToken)]
                if (typeValue is not None):
                    orderId = typeValue
                    res["success"] = [order for order in res["success"] if order["orderId"] == int(orderId)]
                success = list(res["success"])
                success.sort(key=orderReportOrderIdSort, reverse=True)
                success.sort(key=orderReportStatusSort)
                res["success"] = success
                client.logout()
                return res, 200
            if (type == 'tradeReport'):
                if (typeValue is not None):
                    orderId = typeValue
                    res = client.trade_report(order_id= orderId)
                    client.logout()
                    return res, 200
                else:
                    res = client.trade_report()
                    client.logout()
                    return res, 200
            if (type == 'positions'):
                positionType = typeValue
                instrumentToken = request.args.get('instrumentToken', default= None)
                res = client.positions(position_type= positionType)
                if (instrumentToken is not None):
                    successArray = list(res['Success'])
                    successArray = [stockDetails for stockDetails in successArray if stockDetails['instrumentToken'] == int(instrumentToken)]
                    res['Success'] = successArray
                client.logout()
                return res, 200
            if (type == 'orderStatus'):
                orderId = typeValue
                res = client.order_report(order_id = orderId)
                # res has the history of that particular order, but we don't want it. We only want the last element
                success = list(res["success"])
                finalStatus = success[-1]['status']
                client.logout()
                return finalStatus, 200
            if (type == 'orderCategories'):
                instrumentToken = request.args.get('instrumentToken', default= None)
                if (instrumentToken is None):
                    abort(400, message= 'Please enter the instrument token')
                res = client.order_report()
                res["success"] = [order for order in res["success"] if order["instrumentToken"] == int(instrumentToken)]
                success = list(res["success"])
                success.sort(key=orderReportOrderIdSort, reverse=True)
                success.sort(key=orderReportStatusSort)
                OPN_Orders = []
                OPF_Orders = []
                CAN_Orders = []
                TRAD_Orders = [] 
                for orderReport in success:
                    if (orderReport['status'] == 'OPN'):
                        OPN_Orders.append(orderReport['orderId'])
                    elif (orderReport['status'] == 'OPF'):
                        OPF_Orders.append(orderReport['orderId'])
                    elif (orderReport['status'] == 'CAN'):
                        CAN_Orders.append(orderReport['orderId'])
                    elif (orderReport['status'] == 'TRAD'):
                        TRAD_Orders.append(orderReport['orderId'])
                client.logout()
                return {
                    'OPN': OPN_Orders,
                    'OPF': OPF_Orders,
                    'CAN': CAN_Orders,
                    'TRAD': TRAD_Orders,
                }, 200
            if (type == 'quotes'):
                quotes = typeValue
                print(typeValue)
                try:
                    quoteDetails = client.quote(instrument_token = quotes)
                    return loads(dumps(quoteDetails)), 200
                except e:
                    abort(400, message = "Error while obtaining quotes")
            client.logout()
            return None
        except ks_api_client.ApiException as e:
            print(e)
            abort(400, message = e['fault']['message'])
    def post(self, userId, type, typeValue = None):
        try: 
            checkXRequestIdHeader(request= request)
            if (type == 'login'):
                client = self.kotak_login(userId)
                access_code = request.args.get('accessCode', default=None)
                token = jwt.encode({
                    'access_code': access_code
                }, os.environ.get("DYNSTOCKS_SECRET"), algorithm=os.environ.get("DYNSTOCKS_JWT_ALGO"))
                client.logout()
                return {
                    'message': 'Login Successful',
                    'token': token,
                    # Need Authentication Token
                }, 200
                
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
            client = self.kotak_login(userId)

            content_type = request.headers.get('Content-Type')
            if ('application/json' in content_type):
                if (type == 'placeOrder'):
                    body = request.get_json()
                    order_type = body['orderType']
                    instrument_token = int(body['instrumentToken'])
                    transaction_type = body['transactionType']
                    quantity = int(body['quantity'])
                    price = body['price'] / 1.0
                    try:
                        res = client.place_order(order_type=order_type, instrument_token=instrument_token,
                        transaction_type=transaction_type, quantity=quantity, price=price,
                            )
                        client.logout()
                        return loads(dumps(res)), 200
                    except ks_api_client.ApiException as e:
                        abort(400, message = e['fault']['message'])
                if (type == 'cancelOrder'):
                    print("Inside cancelOrder")
                    order_id = typeValue
                    if (not order_id):
                        abort(400, message='Please enter a valid Order Id')
                    try:
                        res = client.cancel_order(order_id= order_id)
                        client.logout()
                        return loads(dumps(res)), 200
                    except ks_api_client.ApiException as e:
                        abort(400, message = e['fault']['message'])
                if (type == 'modifyOrder'):
                    order_id = typeValue
                    body = request.get_json()
                    order_type = body['orderType']
                    instrument_token = int(body['instrumentToken'])
                    transaction_type = body['transactionType']
                    quantity = int(body['quantity'])
                    price = body['price'] / 1.0
                    try: 
                        res = client.modify_order(order_id = order_id, price = price, quantity = quantity)
                        client.logout()
                        return loads(dumps(res)), 200
                    except ks_api_client.ApiException as e:
                        abort(400, message = e['fault']['message'])
                if (type == 'logout'):
                    client.logout()
        except ks_api_client.ApiException as e:
            print(e)
            abort(400, message= e['fault']['message'])
            