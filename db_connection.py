from flask_pymongo import pymongo

# secure connection url
__url__ = "insert mongo client authentication url"

# mongodb atlas client
client = pymongo.MongoClient(__url__)

# db and collection
db = pymongo.uri_parser.parse_uri(__url__)

atlas = client.get_database('flask_mongodb_atlas')
collection = pymongo.collection.Collection(atlas, 'resume_collection')
