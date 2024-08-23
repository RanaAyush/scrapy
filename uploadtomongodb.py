import pymongo
import json

client = pymongo.MongoClient("mongodb+srv://ranaji:Ranaayush123@practicedb.0vihg.mongodb.net/")

db = client['mydatabase']
collection = db['mycollection']

with open('nobero_products.json') as file:
    data = json.load(file)

# Insert data into MongoDB
if isinstance(data, list):
    collection.insert_many(data)
else:
    collection.insert_one(data)

print("Data successfully inserted!")
