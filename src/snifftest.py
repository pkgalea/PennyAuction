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
    sniff( prn=process_packet, store=False)

def process_packet(packet):
    """
    This function is executed whenever a packet is sniffed
    """
    #if packet.haslayer(HTTPRequest):
    #     url = packet[HTTPRequest].Host.decode() + packet[HTTPRequest].Path.decode()
    #     if ("quibids.com" in url):
    #        print (url)
    if packet.haslayer(HTTPResponse):
        response = str(packet[HTTPResponse])
        if ('({"a":{"' in response):
            jsonstr = '{"a":{' + response.split('({"a":{')[1]
            jsonstr = jsonstr.split(')')[0]
            auction_dict = json.loads(jsonstr)
            print("")
            print(auction_dict)


if __name__ == "__main__":

    sniff_packets()