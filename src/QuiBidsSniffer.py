import pyshark
import json
import pymongo


class QuiBidsSniffer():


    def __init__(self):
        """ 
        Constructor for the Quibids Sniffer Class

        Parameters: None

        Returns: None  
        """
        self.sniffed_collection = None
    
    def process_auction(self, auction):
        """ 
        Takes the auction string sniffed from the sniffer and inserts it into the sniffed_collection in mongoDB. 

        Parameters: 
            auction(json object): 

        Returns: None  
        """
        auction_id = list(auction.keys())[0]
        auction = auction[auction_id]
        if (not isinstance(auction, dict)):
            print ("not a dict", auction)
            return

        if ('bh' in auction.keys()):

            if ('s' in auction.keys()):
                print ("We're done")
                auction_dict = {"auction_id":auction_id, "auction_complete": True}
                self.sniffed_collection.insert_one(auction_dict) 
            else:
                auction_dict = {"auction_id":auction_id, "bid":auction['bh'][0]["id"], "bh":[]}
                for bh in auction['bh']:
                    bid = bh['id']
                    username = bh['u']
                    is_bidomatic = bh['t']==2
                    print("*****************")
                    print(auction_id, bid, username, is_bidomatic)
                    auction_dict["bh"].append({"bid": bid, "username":username, "is_bidomatic":is_bidomatic})  
                    print("*****************")
                self.sniffed_collection.insert_one(auction_dict)  
        else:
            print(auction)


    def capture_auction (self):
        """ 
        sniffs the packets coming in from only the quibids website, and puts them into the sniffed_collection in MongoDB

        Parameters: None
              
        Returns: None  
        """
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.sniffed_collection = db["sniffed_auctions"]
        self.sniffed_collection.delete_many({})
        capture = pyshark.LiveCapture(interface="wlp1s0", bpf_filter="host 35.153.120.167 or host 52.203.74.230")

        capture.set_debug()
        capture.sniff(timeout=10)
        for pkt in capture:
            for l in pkt.layers:
                if l.layer_name == "http":
                        if ("response_for_uri" in l.field_names):
                            if ("lb_id" in l.get("response_for_uri")):
                                auction = l.get("file_data")
                                if (auction):
                                    if ("(" in auction):
                                        auction = auction.split("(")[1].split(")")[0]
                                        auction = json.loads(auction)
                                        auction= auction['a']
                                        if (auction):
                                            self.process_auction(auction)

if __name__ == "__main__": 
    qbs = QuiBidsSniffer()
    qbs.capture_auction()
