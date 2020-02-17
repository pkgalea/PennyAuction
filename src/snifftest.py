from scapy.all import *
from scapy.layers.http import HTTPRequest, HTTPResponse # import HTTP packet
from colorama import init, Fore
import json

# initialize colorama
init()

# define colors
GREEN = Fore.GREEN
RED   = Fore.RED
RESET = Fore.RESET

def sniff_packets():
    sniff( filter = "ether src host f4:8c:eb:c2:7b:32", prn=process_packet, store=False)

def process_packet(packet):
 #   print(packet[HTTPRequest].Host)
#    print (packet.mysummary())
    """
    This function is executed whenever a packet is sniffed
    """
    if packet.haslayer(HTTPRequest):
        url = packet[HTTPRequest].Host.decode() + packet[HTTPRequest].Path.decode()
  #       if ("quibids.com" in url):
        print (url)
    if packet.haslayer(HTTPResponse):
        response = str(packet[HTTPResponse])
        print(packet.mysummary())
        print(type(packet))
        print (response)
        if ('({"a":{"' in response):
  #          print(response)
            jsonstr = '{"a":{' + response.split('({"a":{')[1]
            jsonstr = jsonstr.split(')')[0]
            auction_dict = json.loads(jsonstr)
  #          print("")
            auction = auction_dict['a']
 #           print(auction.keys())
            auction_id = list(auction.keys())[0]
            auction = auction[auction_id]
            print (type(auction))
            if (isinstance(auction, dict) and 'bh' in auction.keys()):
                last_bidder = auction['bh'][0]
                bid = last_bidder['id']
                username = last_bidder['u']
                is_bidomatic = last_bidder['t']==2
                print("*****************")
                print(auction_id, bid, username, is_bidomatic)
                print("*****************")
 #       else:
 #           print("inner no")
 #   else:
 #       print(" outer no")
            




if __name__ == "__main__":

    sniff_packets()