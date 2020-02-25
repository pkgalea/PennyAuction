import pymongo
from bson.objectid import ObjectId

class LiveAuctionProcessor:

    def __init__(self, auction_dict):
        self.auction_dict = auction_dict
        self.auction_id = auction_dict["auction_id"]
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.live_collection = db["live"]
        self.bh = []
        self.last_processed = 0
        self.opponents = {}

    def process(self):
        self.opponents = {}
        opponent_num = 0
        cur_bid = len(self.bh)
        for i in range(cur_bid-1, -1, -1):
            username = self.bh[i]["username"]
            is_bidomatic = self.bh[i]["is_bidomatic"]
            bid = self.bh[i]["bid"]
            if username not in self.opponents:
                self.opponents[username] = {"is_bidomatic": is_bidomatic, "opponent_num": opponent_num, "distance": cur_bid-bid}
                opponent_num += 1
            

    def update(self):
        for u in self.live_collection.find({"auction_id":self.auction_id}):
            print(u["_id"])
            self.bh.append({"bid":u["bid"], "usename":u["username"], "is_bidomatic": u["is_bidomatic"]})
            print(self.live_collection.delete_one({"auction_id":self.auction_id, "bid":u["bid"]}))#({"_id:": ObjectId(str(u["_id"]))}).deleted_count)
            print(self.bh)

if __name__ == "__main__":
    auction_dict = {"auction_id":"11111111"}
    bh = [
        {"bid":1, "username": "carl", "is_bidomatic":False},
        {"bid":2, "username": "jerry", "is_bidomatic":False},
        {"bid":3, "username": "carl", "is_bidomatic":True},
        {"bid":4, "username": "alan", "is_bidomatic":True},
        {"bid":5, "username": "jerry", "is_bidomatic":False},
        {"bid":6, "username": "alan", "is_bidomatic":False}
     ]
    lap = LiveAuctionProcessor(auction_dict)
    lap.bh = bh
    lap.process()
    print(lap.opponents)


