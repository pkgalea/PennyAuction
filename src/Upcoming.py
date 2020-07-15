import requests
from PrevInfo import PrevInfo
import time
from bs4 import BeautifulSoup
import pymongo
from backports import configparser
import sys
from ParseMongo import MongoParser
from datetime import timedelta, datetime
from  BidTrackerScraper import BidTrackerScraper
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from LiveAuctionProcessor import LiveAuctionProcessor
import pickle
import pandas as pd
import threading
import os
from colorama import Fore
from colorama import Style
from QuiBidsSniffer import QuiBidsSniffer



class Upcoming:

    def __init__(self, headless=True):
        self.headless = headless
        self.upcoming_collection = None
        self.tracking_collection = None
        self.prev_info = None
        self.penny_model = None
        self.bts = BidTrackerScraper() 
        self.mp = MongoParser()
        self.driver = None
        self.launched_auction_ids = []
        self.upcoming_auctions = []
        self.live_auction_dict = {}
        self.quibids_sniffer = QuiBidsSniffer()



    def launch_driver(self):
        options = Options()
        options.headless = self.headless
        driver = webdriver.Firefox(options=options, executable_path=r'/bin/geckodriver')
        return driver


    def connect_to_mongo(self):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.upcoming_collection = db["upcoming"]
        self.tracking_collection = db["tracking"]
        self.tracking_collection.delete_many({})

    def load_pickles(self):
        self.prev_info = pickle.load( open( "pi.pkl", "rb" ) )
        self.penny_model = pickle.load( open( "rf.pkl", "rb" ) )

    def process_auction(self, auction_dict, auction_driver):
        """
            Takes the upcoming auction and launches a Live Auction Processor class.   Also closes the web page once it's done.
            Parameters:
                auction_dict (dict): dictionary of auction info 
                handle (str): the selenium handle for the window 
        """
        lap = LiveAuctionProcessor(auction_dict, self.prev_info, self.penny_model)
        last_refresh = time.time()
        while True:
            time_since_last_refresh = time.time() -  last_refresh
            if (time_since_last_refresh > 1200):
                last_refresh = time.time()
                auction_driver.refresh()
            out_dict = lap.get_expected_value()
            auction_id = auction_dict["auctionid"]
           # print(out_dict)
            self.live_auction_dict[auction_id] = out_dict
            if (not out_dict):
                print ("Closing " + auction_id)
                del self.live_auction_dict[auction_id]
                auction_driver.close()

                return   # auction is sold
            time.sleep(.5)


    def set_viewport_size(self, driver, width, height):
        window_size = driver.execute_script("""
            return [window.outerWidth - window.innerWidth + arguments[0],
            window.outerHeight - window.innerHeight + arguments[1]];
            """, width, height)
        driver.set_window_size(*window_size)

    def get_upcoming_auctions(self):
        self.upcoming_auctions =  self.mp.parse_upcoming_auction_page(self.bts.scrape_upcoming_auctions())
        self.upcoming_auctions = [ua for ua in self.upcoming_auctions if ua["auctionid"] not in self.launched_auction_ids and (ua["cardtype"]=="None" or ua["cardtype"] == "Buster" or ua["cardvalue"]>=25)] 
        if self.upcoming_collection.count_documents({"_id": "upcoming"}) == 0:
            self.upcoming_collection.insert_one ({"_id": "upcoming", "auctions": self.upcoming_auctions})
        else:
            self.upcoming_collection.update_one ({"_id": "upcoming"}, {"$set": {"auctions": self.upcoming_auctions}})
        #print(self.upcoming_auctions[0])
 
    def launch_auction(self, auction):
        pre_launch_handles = self.driver.window_handles
        auction["fee"] = 0 if auction["cardvalue"] == 0 else (1 if auction["cardvalue"] < 50 else 1.99)
        self.upcoming_auctions.pop()
        self.launched_auction_ids.append(auction["auctionid"])
        elems = self.driver.find_elements_by_id(auction["auctionid"])
        auction_driver = None
        for element in elems:
            link = element.find_elements_by_tag_name('a')[0]
            href = link.get_attribute('href')
            auction_driver = self.launch_driver()
            auction_driver.get(href)
            time.sleep(2)
            break
        if auction_driver:
            print("OPENING" + auction["auctionid"])
            t1 = threading.Thread(target=self.process_auction, args=(auction,auction_driver,))
            t1.start()
        else:
            print ("FAIL TO START" + auction["auctionid"])


    def check_for_new_auctions(self):
       last_refresh = time.time()
       while (True):
            time_since_last_refresh = time.time() -  last_refresh
            if (time_since_last_refresh > 1200):
                last_refresh = time.time()
                self.driver.refresh()
            
            self.get_upcoming_auctions()
            for auction   in self.upcoming_auctions:
                if (auction["seconds_left"] < 350):
                    self.launch_auction(auction)
            time.sleep(5)
    
    def get_live_auctions_str(self):
        dict_copy = self.live_auction_dict.copy()
        auction_str = ""
        for auction_id, data in dict_copy.items():
            auction_str  += auction_id 
            if (data["cardtype"] == "None"):
                auction_str  += ": Bid Pack "  + str(data["bidvalue"]) 
            else:
                auction_str  += ": " + data["cardtype"] + " $" + str(data["cardvalue"])
            
            mev = data["manual_ev"]
            bomev = data["bom_ev"]
            bid = data["bid"]
            tracking_OK = data['tracking_OK']
            if (mev >= 0):
                mcolor = Fore.GREEN
            else:
                mcolor = Fore.RED
            if (bomev >= 0):
                bomcolor = Fore.GREEN
            else:
                bomcolor = Fore.RED
            auction_str += f"\n          cur_bid:{bid} manual:{mcolor}{mev:.2f}{Style.RESET_ALL} bom:{bomcolor}{bomev:.2f}{Style.RESET_ALL} {tracking_OK}\n"
        return auction_str 
 
    def get_upcoming_auctions_str(self):
        upcoming_str = ""
        for ua in self.upcoming_auctions:
            upcoming_str += str(ua["seconds_left"]//60) + "m " + str(ua["seconds_left"] % 60)  + "s :"
            if (ua["cardtype"] == "None"):
                upcoming_str  +=  "Bid Pack "  + str(ua["bidvalue"]) + " (" +str(ua["auctionid"])  + ")\n"
            else:
                upcoming_str  +=  ua["cardtype"] + " $" + str(ua["cardvalue"]) + " (" + str(ua["auctionid"]) + ")\n"
        return upcoming_str

    def print_stuff(self):
   #     os.system('cls' if os.name == 'nt' else 'clear')
        live_auction_str = self.get_live_auctions_str()
        upcoming_auction_str = self.get_upcoming_auctions_str()
        f = open("display.txt", "w")
        f.write(live_auction_str + "\n" + upcoming_auction_str)
        f.close()   

    def start_sniffer(self):
        self.qbs.capture_auction()

    def run(self):
        print("Logging in to BTS")
        self.bts.login(2)
        print("Connecting to Mongo")
        self.connect_to_mongo()
        self.load_pickles()
        print("Going to Quibids")
        self.driver = self.launch_driver()
        self.driver.get("http://quibids.com/en/")
        print([x[:100] for x in self.driver.page_source.split("quibids")])
        #self.driver.get("http://www.google.com")
        t1 = threading.Thread(target=self.check_for_new_auctions)
        t1.start()
        print ("Starting Threading")
        # t2 = threading.Thread(target=self.start_sniffer)
        # t2.start()
        while True:
            self.print_stuff()
            time.sleep(.5)

 
if __name__ == "__main__": 
    upcoming = Upcoming(True)
    upcoming.run()

    






