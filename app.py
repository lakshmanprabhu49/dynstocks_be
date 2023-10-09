from flask import Flask
from flask.json import JSONEncoder
from dotenv import load_dotenv, find_dotenv
import flask.scaffold

flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
from flask_restful import Api
from bson.json_util import dumps
import bson
from src.APIs.authentication import Authentication
from src.APIs.users import Users
from src.APIs.dynStocks import DynStocks
from src.APIs.dynStocksNetReturns import DynStocksNetReturns
from src.APIs.transactions import Transactions
from src.APIs.dynStocksRealTimePrice import DynStocksRealTimePrice
from src.APIs.kotakStock import KotakStock
import os
import datetime
import pytz

load_dotenv(find_dotenv())

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return bson.json_util.default(obj)

flask_app = Flask(__name__)
flask_app.json_encoder = CustomJSONEncoder
flask_api = Api(flask_app)



flask_api.add_resource(Authentication,'/auth/<string:type>', '/auth/<string:type>/<string:userId>')
flask_api.add_resource(Users, '/users', '/users/<string:userId>')
flask_api.add_resource(DynStocks ,'/<string:userId>/dynStocks', '/<string:userId>/dynStocks/<string:dynStockId>')
flask_api.add_resource(Transactions ,'/<string:userId>/transactions', '/<string:userId>/dynStocks/<string:dynStockId>/transactions')
flask_api.add_resource(KotakStock ,'/<string:userId>/kotakStock/<string:type>', '/<string:userId>/kotakStock/<string:type>/<string:typeValue>')
flask_api.add_resource(DynStocksNetReturns ,'/<string:userId>/dynStocks/<string:dynStockId>/netReturns')
flask_api.add_resource(DynStocksRealTimePrice ,'/realTimePrice','/realTimePrice/<string:userId>')

if (str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')).day) != os.environ.get("lastDay")):
    temp_file = open('temp.txt')
    content = temp_file.read()
    lastDay = content.splitlines()[0].split(':')[1]
    if (str(datetime.datetime.now(pytz.timezone('Asia/Kolkata')).day) != lastDay):
        os.environ["lastDay"] = ""
        for name, value in os.environ.items():
            if ('accessCode' in name):
                os.environ[name] = ""

if __name__ == '__main__':
    flask_app.run(debug=True, port=int(os.environ.get("PORT", 5000)), use_reloader=True)