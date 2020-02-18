import pyshark
import json


def capture_auction ():
    capture = pyshark.LiveCapture(interface="wlp1s0") #, bpf_filter="src net 52.203.74.230")

    #capture = pyshark.LiveCapture()
    capture.set_debug()
    capture.sniff(timeout=10)
    for pkt in capture:


    #    print(pkt.layers)
        for l in pkt.layers:
            if l.layer_name == "http":
                    if ("response_for_uri" in l.field_names):
                        if ("lb_id" in l.get("response_for_uri")):
                            auction = l.get("file_data")
                            if (auction):
  #                              print(auction)
                                print(l.get("response_for_uri"))
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
                                            return
                                        else:
                                            bh = auction['bh'][0]
                                            #print(dict_str)
                                            bid = bh['id']
                                            username = bh['u']
                                            is_bidomatic = bh['t']==2
                                            print("*****************")
                                            print(auction_id, bid, username, is_bidomatic)
                                            print("*****************")
                                    else:
                                        print(auction)

if __name__ == "__main__": 
    capture_auction()
