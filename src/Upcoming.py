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


# TODO: Make this a class!

def process_auction(auction_dict, handle):
    """
        Takes the upcoming auction and launches a Live Auction Processror class.   Also closes the web page once it's done.
        Parameters:
            auction_dict (dict): dictionary of auction info 
            handle (str): the selenium handle for the window 
    """
    lap = LiveAuctionProcessor(upcoming_auctions[0], prev_info, penny_model)
    while True:
        out_dict = lap.get_expected_value()
        if (not out_dict):
            driver.switch_to.window(handle)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return   # auction is sold
        time.sleep(.5)


def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
    driver.set_window_size(*window_size)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["penny"]
upcoming_collection = db["upcoming"]
tracking_collection = db["tracking"]
tracking_collection.delete_many({})
prev_info = pickle.load( open( "pi.pkl", "rb" ) )
penny_model = pickle.load( open( "rf.pkl", "rb" ) )
bts = BidTrackerScraper() 
bts.login(2)
mp = MongoParser()


#driver = webdriver.Chrome()
#driver.get ("http://quibids.com/en/")
options = Options()
#options.headless = True
driver = webdriver.Firefox(options=options, executable_path=r'/bin/geckodriver')
driver.set_window_position(0, 0)
driver.set_window_size(1024, 768)
set_viewport_size(driver, 2000, 2000)

driver.get("http://quibids.com/en/")
time.sleep(2)

launched_auction_ids = []
while (True):
    upcoming_auctions =  mp.parse_upcoming_auction_page(bts.scrape_upcoming_auctions())
    upcoming_auctions = [ua for ua in upcoming_auctions if ua["auctionid"] not in launched_auction_ids and (ua["cardtype"]=="None" or ua["cardvalue"]>=25)] 
    upcoming_collection.update_one ({"_id": "upcoming"}, {"$set": {"auctions": upcoming_auctions}})
    print(upcoming_auctions[0])
    for auction in upcoming_auctions:
        auction["fee"] = 0 if auction["cardvalue"] == 0 else (1 if auction["cardvalue"] < 50 else 1.99)
        if (auction["seconds_left"] < 800):
            upcoming_auctions.pop()
            launched_auction_ids.append(auction["auctionid"])
            print(auction["auctionid"])
            elems = driver.find_elements_by_id(auction["auctionid"])
            for element in elems:
                driver.execute_script("window.scrollTo(0, 400);")
                link = element.find_elements_by_tag_name('a')[0]
                ActionChains(driver).key_down(Keys.CONTROL).click(link).key_up(Keys.CONTROL).perform()
                break
            t1 = threading.Thread(target=process_auction, args=(auction,driver.window_handles[-1],))
            t1.start() 

    #print(upcoming_auctions)
    time.sleep(1)
    






