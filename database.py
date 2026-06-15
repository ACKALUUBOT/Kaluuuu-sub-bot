from pymongo import MongoClient
import config

client = MongoClient(config.MONGO_URI)
db = client['sub_management']

channels_col = db['channels']
users_col = db['users']

utr_col = db['verified_utrs']
