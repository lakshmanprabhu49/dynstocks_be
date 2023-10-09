from dotenv import load_dotenv, find_dotenv
import os
from pymongo import MongoClient

load_dotenv(find_dotenv())

MONGO_CONNECTION_STRING = os.environ.get('MONGO_CONNECTION_STRING')

MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')

MONGO_CONNECTION_STRING = MONGO_CONNECTION_STRING.replace('<username>', MONGO_USERNAME)
MONGO_CONNECTION_STRING = MONGO_CONNECTION_STRING.replace('<password>', MONGO_PASSWORD)

mongo_client = MongoClient(MONGO_CONNECTION_STRING)

MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')
MONGO_DB_DYNSTOCKS_COLLECTION = os.environ.get('MONGO_DB_DYNSTOCKS_COLLECTION')
MONGO_DB_DYNSTOCKS_REALTIME_PRICE_COLLECTION = os.environ.get('MONGO_DB_DYNSTOCKS_REALTIME_PRICE_COLLECTION')

mongo_DB = mongo_client[MONGO_DB_NAME]
try:
    mongo_DB.create_collection(MONGO_DB_DYNSTOCKS_COLLECTION, {
    })
except: 
    pass
mongoDB_DynStocks_Collection = mongo_DB[MONGO_DB_DYNSTOCKS_COLLECTION]
mongoDB_DynStocks_RealTime_Price_Collection = mongo_DB[MONGO_DB_DYNSTOCKS_REALTIME_PRICE_COLLECTION]