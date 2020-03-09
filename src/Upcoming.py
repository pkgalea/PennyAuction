import requests
import time
from bs4 import BeautifulSoup
import pymongo
from backports import configparser
import sys
from ParseMongo import MongoParser
from datetime import timedelta
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


# TODO: Make this a class!
class Upcoming:

    def __init__(self):
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
        #driver = webdriver.Chrome()
        #driver.get ("http://quibids.com/en/")
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options, executable_path=r'/bin/geckodriver')
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)
        self.set_viewport_size(self.driver, 2000, 2000)
        self.driver.get("http://quibids.com/en/")
        time.sleep(2)


    def connect_to_mongo(self):
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.upcoming_collection = db["upcoming"]
        self.tracking_collection = db["tracking"]
        self.tracking_collection.delete_many({})

    def load_pickles(self):
        self.prev_info = pickle.load( open( "pi.pkl", "rb" ) )
        self.penny_model = pickle.load( open( "rf.pkl", "rb" ) )

    def process_auction(self, auction_dict, handle):
        """
            Takes the upcoming auction and launches a Live Auction Processror class.   Also closes the web page once it's done.
            Parameters:
                auction_dict (dict): dictionary of auction info 
                handle (str): the selenium handle for the window 
        """
        lap = LiveAuctionProcessor(auction_dict, self.prev_info, self.penny_model)
        while True:
            out_dict = lap.get_expected_value()
       
           # print(out_dict)
            self.live_auction_dict[auction_dict["auctionid"]] = out_dict
            if (not out_dict):
                del self.live_auction_dict[auction_dict["auctionid"]]
                self.driver.switch_to.window(handle)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return   # auction is sold
            time.sleep(.1)


    def set_viewport_size(self, driver, width, height):
        window_size = driver.execute_script("""
            return [window.outerWidth - window.innerWidth + arguments[0],
            window.outerHeight - window.innerHeight + arguments[1]];
            """, width, height)
        driver.set_window_size(*window_size)

    def get_upcoming_auctions(self):
        self.upcoming_auctions =  self.mp.parse_upcoming_auction_page(self.bts.scrape_upcoming_auctions())
        self.upcoming_auctions = [ua for ua in self.upcoming_auctions if ua["auctionid"] not in self.launched_auction_ids and (ua["cardtype"]=="None" or ua["cardvalue"]>=25)] 
        self.upcoming_collection.update_one ({"_id": "upcoming"}, {"$set": {"auctions": self.upcoming_auctions}})
        #print(self.upcoming_auctions[0])
 
    def launch_auction(self, auction):
        auction["fee"] = 0 if auction["cardvalue"] == 0 else (1 if auction["cardvalue"] < 50 else 1.99)
        self.upcoming_auctions.pop()
        self.launched_auction_ids.append(auction["auctionid"])
        print(auction["auctionid"])
        elems = self.driver.find_elements_by_id(auction["auctionid"])
        for element in elems:
            self.driver.execute_script("window.scrollTo(0, 400);")
            link = element.find_elements_by_tag_name('a')[0]
            ActionChains(self.driver).key_down(Keys.CONTROL).click(link).key_up(Keys.CONTROL).perform()
            break
        t1 = threading.Thread(target=self.process_auction, args=(auction,self.driver.window_handles[-1],))
        t1.start() 


    def check_for_new_auctions(self):
       while (True):
            self.get_upcoming_auctions()
            for auction in self.upcoming_auctions:
                if (auction["seconds_left"] < 350):
                    self.launch_auction(auction)
            time.sleep(5)
    
    def print_auctions(self):
        dict_copy = self.live_auction_dict.copy()
        for auction_id, data in dict_copy:
            auction_str  = auction_id 
            if (data["cardtype"] == "None"):
                auction_str  += ": Bid Pack "  + str(data["bidvalue"]) 
            else:
                auction_str  += ": " + data["cardtype"] + " $" + str(data["cardvalue"])
            print(auction_str)
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
            auction_str = f"          cur_bid:{bid} manual:{mcolor}{mev:.2f}{Style.RESET_ALL} bom:{bomcolor}{bomev:.2f}{Style.RESET_ALL} {tracking_OK}"
            print(auction_str) 
 
    def print_upcoming_auctions(self):
        upcoming_str = ""
        for ua in self.upcoming_auctions:
            if (ua["cardtype"] == "None"):
                upcoming_str  +=  str(ua["seconds_left"]) + ": Bid Pack "  + str(ua["bidvalue"]) + " (" +str(ua["auctionid"])  + ")\n"
            else:
                upcoming_str  += str(ua["seconds_left"]) + ": " + ua["cardtype"] + " $" + str(ua["cardvalue"]) + " (" + str(ua["auctionid"]) + ")\n"
        print(upcoming_str)

    def print_stuff(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_auctions()
        print()
        self.print_upcoming_auctions()

    def start_sniffer(self):
        self.qbs.capture_auction()

    def run(self):
        self.bts.login(2)
        self.connect_to_mongo()
        self.load_pickles()
        self.launch_driver()
        t1 = threading.Thread(target=self.check_for_new_auctions)
        t1.start()
       # t2 = threading.Thread(target=self.start_sniffer)
       # t2.start()
        while True:
            self.print_stuff()
            time.sleep(.1)

 
if __name__ == "__main__": 
    upcoming = Upcoming()
    upcoming.run()

    






