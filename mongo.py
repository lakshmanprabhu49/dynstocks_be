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
MONGO_DB_COLLECTION_NAME = os.environ.get('MONGO_DB_COLLECTION_NAME')

mongo_DB = mongo_client[MONGO_DB_NAME]
try:
    mongo_DB.create_collection(MONGO_DB_COLLECTION_NAME, {
    })
except: 
    pass
mongo_DB_Collection = mongo_DB[MONGO_DB_COLLECTION_NAME]