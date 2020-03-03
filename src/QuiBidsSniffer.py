import pyshark
import json
import pymongo


class QuiBidsSniffer()

    def __init__(self):
        pass

    def capture_auction (self):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        sniffed_collection = db["sniffed_auctions"]
        sniffed_collection.delete_many({})
        capture = pyshark.LiveCapture(interface="wlp1s0", bpf_filter="host 35.153.120.167 or host 52.203.74.230")

        #capture = pyshark.LiveCapture()
        capture.set_debug()
        capture.sniff(timeout=10)
        for pkt in capture:


        #    print(pkt.layers)
            for l in pkt.layers:
                if l.layer_name == "http":
                        if ("response_for_uri" in l.field_names):
                            if ("lb_id" in l.get("response_for_uri")):
                            #  print(pkt.ip.src) 
                                auction = l.get("file_data")
                            #  print(auction)
                                if (auction):
    #                              print(auction)
                        #         print(l.get("response_for_uri"))
                                    auction = auction.split("(")[1].split(")")[0]
                                    auction = json.loads(auction)
            #                      print (auction)
                                    auction= auction['a']
                                    if (auction):

                                        auction_id = list(auction.keys())[0]
                                        auction = auction[auction_id]
                                        
                                        if ('bh' in auction.keys()):

                                            if ('s' in auction.keys()):
                                                print ("We're done")
                                                auction_dict = {"auction_id":auction_id, "auction_complete": True}
                                                sniffed_collection.insert_one(auction_dict) 
                                                #return
                                            else:
                                                bh = auction['bh'][0]
                                                #print(dict_str)
                                                bid = bh['id']
                                                username = bh['u']
                                                is_bidomatic = bh['t']==2
                                                print("*****************")
                                                print(auction_id, bid, username, is_bidomatic)
                                                auction_dict = {"auction_id":auction_id, "bid": bid, "username":username, "is_bidomatic":is_bidomatic}
                                                sniffed_collection.insert_one(auction_dict)    
                                                print("*****************")
                                        else:
                                            print(auction)


if __name__ == "__main__": 
    qbs = QuiBidsSniffer ()
    qbs.capture_auction()
