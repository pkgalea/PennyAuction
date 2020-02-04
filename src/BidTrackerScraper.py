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
        self._session = None
    
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

    def _login(self):
        payload = {} 
     #   headers = {
     #       'User-Agent': 'MMozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
     #       'Accept-Encoding': 'gzip, deflate',
     #       'Accept-Language': 'en-US,en;q=0.9'
     #   }     
    
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

        time.sleep(4)
        post = self._session.post("http://www.bidtracker.info/Account/Login", data=payload)
        print (post.status_code)

        time.sleep(4)

    def _get_all_auction_ids_for_group(self, auction_group):
        url = "http://www.bidtracker.info/AllAuctionsByDesc?hash="+self._auction_pages[auction_group]+"&site=quibids"
        r = self._session.get(url)
        split = r.text.split("auction_id=")
        auction_ids = [s.split('"')[0] for s in split[1:]]
        time.sleep(4)
        return auction_ids
    
    def _scrape_auction_group(self, auction_group, break_after):
        i = 0
        auction_ids = self._get_all_auction_ids_for_group(auction_group)
        for aID in auction_ids:
            print (i, aID, auction_group)
            if not (self.pages_collection.find_one({"_id": aID}, {"AuctionGroup":auction_group})):
                page_dict = {"_id": aID, "AuctionGroup": auction_group}
                time.sleep(1)
                r = self._session.get("http://www.bidtracker.info/Auction?site=quibids&auction_id=" + aID)
                page_dict ["Auction"] =  r.text
                if 'class="sold"' not in r.text:
                    continue
                time.sleep(1)
                r = self._session.get("http://www.bidtracker.info/AuctionTable?site=quibids&auction_id=" + aID)
                page_dict ["AuctionTable"] = r.text
                time.sleep(1)
                r = self._session.get("http://www.bidtracker.info/History?site=quibids&auction_id=" + aID)        
                page_dict ["AuctionHistory"] = r.text

                self.pages_collection.insert_one(page_dict)
            i += 1
            if i==break_after:
                break

            
    def scrape(self, break_after):
        self._connect_to_mongodb()
        self._read_config()
        with requests.Session() as self._session:
            self._login()
            for auction_group in self._auction_pages.keys():
                self._scrape_auction_group(auction_group, break_after)
            

if len(sys.argv) != 2:
    print ("Usage: BidTrackerScraper.py [#break_after]")
    sys.exit()

break_after = int(sys.argv[1])
bts = BidTrackerScraper()
bts.scrape(break_after)