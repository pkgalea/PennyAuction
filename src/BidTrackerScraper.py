import requests
import time
from bs4 import BeautifulSoup
import pymongo
from backports import configparser
import sys

class BidTrackerScraper:
    
    def __init__ (self):
        self.pages_collection = None
        self._username = None
        self._password = None
        self._auction_pages = None
        self._session = requests.Session()
    
    def _connect_to_mongodb(self):     
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.pages_collection = db["pages"]

    def _read_config(self):
        config = configparser.ConfigParser() 
        configFilePath = 'PennyAuctions.config'
        config.read(configFilePath)
        self._username = config['login-info']['username']
        self._password = config['login-info']['password']
        self._auction_pages = dict(config['auction-pages'])        

    def login(self, sleep_time):
        self._read_config()
        payload = {}     
        r = self._session.get("https://www.bidtracker.info/Account/Login" )
        print (r.status_code)
        soup = BeautifulSoup(r.text, 'html.parser')
        vs = soup.find(id='__VIEWSTATE')
        vsg = soup.find(id='__VIEWSTATEGENERATOR')
        ev = soup.find(id='__EVENTVALIDATION')
        payload['__EVENTTARGET']=''
        payload['__EVENTARGUMENT']='' 
        payload['__VIEWSTATE']=vs["value"]
        payload['__VIEWSTATEGENERATOR'] = vsg["value"]
        payload['__EVENTVALIDATION'] = ev["value"]
        payload['ctl00$MainContent$UserName'] = self._username
        payload['ctl00$MainContent$Password'] = self._password
        payload['ctl00$MainContent$ctl05'] = "Log+in"

        time.sleep(sleep_time)
        post = self._session.post("http://www.bidtracker.info/Account/Login", data=payload)
        print (post.status_code)

        time.sleep(sleep_time)

    def _get_all_auction_ids_for_group(self, auction_group):
        url = "http://www.bidtracker.info/AllAuctionsByDesc?hash="+self._auction_pages[auction_group]+"&site=quibids"
        r = self._session.get(url)
        split = r.text.split("auction_id=")
        auction_ids = [s.split('"')[0] for s in split[1:]]
        time.sleep(4)
        return auction_ids

    
    
    def _scrape_auction(self, aID, auction_group, sleep_time=1):
        page_dict = {"_id": aID, "AuctionGroup": auction_group}
        time.sleep(sleep_time)
        r = self._session.get("http://www.bidtracker.info/Auction?site=quibids&auction_id=" + aID)  
        page_dict ["Auction"] =  r.text
        if 'class="sold"' not in r.text:
            return None
        time.sleep(sleep_time)
        r = self._session.get("http://www.bidtracker.info/AuctionTable?site=quibids&auction_id=" + aID)
        page_dict ["AuctionTable"] = r.text
        time.sleep(sleep_time)
        r = self._session.get("http://www.bidtracker.info/History?site=quibids&auction_id=" + aID)        
        page_dict ["AuctionHistory"] = r.text
        return page_dict


    def _scrape_auction_group(self, auction_group, break_after):
        i = 0
        auction_ids = self._get_all_auction_ids_for_group(auction_group)
        for aID in auction_ids:
            print (i, aID, auction_group)
            if not (self.pages_collection.find_one({"_id": aID}, {"AuctionGroup":auction_group})):
                page_dict = self._scrape_auction(aID, auction_group)
                if (page_dict):
                    self.pages_collection.insert_one(page_dict)
            i += 1
            if i==break_after:
                break

    def single_scrape(self,auctionID):
        with requests.Session() as self._session:
            self.login(0)
            return self._scrape_auction(auctionID, "whatever", 0)

    def scrape(self, break_after):
        self._connect_to_mongodb()
        with requests.Session() as self._session:
            self.login(3)
            for auction_group in self._auction_pages.keys():
                self._scrape_auction_group(auction_group, break_after)
            
    def scrape_upcoming_auctions(self):
        r = self._session.get("http://www.bidtracker.info/AllAuctionsTable?site=quibids&future=true")
        return r.text
 

if __name__ == "__main__": 
    if len(sys.argv) != 2:
        print ("Usage: BidTrackerScraper.py [#break_after]")
        sys.exit()
        
    break_after = int(sys.argv[1])
    bts = BidTrackerScraper()
    bts.scrape(break_after)