import pymongo
from bson.objectid import ObjectId

class LiveAuctionProcessor:

    def __init__(self, auction_id):
        self.auction_id = auction_id
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.live_collection = db["live"]
        self.bh = []

    def update(self):
        for u in self.live_collection.find({"auction_id":self.auction_id}):
            print(u["_id"])
            self.bh.append((u["bid"], u["username"], u["is_bidomatic"]))
            print(self.live_collection.delete_one({"auction_id":self.auction_id, "bid":u["bid"]}))#({"_id:": ObjectId(str(u["_id"]))}).deleted_count)
            print(self.bh)

