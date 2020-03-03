import requests
import time
from bs4 import BeautifulSoup
import pymongo
from backports import configparser
import sys

class BidTrackerScraper:
    """ 
    Scrapes the BidTracker.com website to get the latest raw auction data into MongoDB.
      
    Attributes: 
        pages_collection (MongoDB collection): The collection of raw html pages for each auction
        _username(str): The bidtracker username read from the config file
        _password(str): The bidtracker password file read from the config file
        _auction_pages(dict): Dictionary of the different types of auction to be scraped (e.g. Amazon 50 + 30 bids)
        _session: The requests session for the scraper
    """
    def __init__ (self):
        """ 
        The constructor for BidTrackerScraper class. 
  
        Parameters: None  
        Returns: None  
        """
        self.pages_collection = None
        self._username = None
        self._password = None
        self._auction_pages = None
        self._session = requests.Session()
    
    def _connect_to_mongodb(self):     
        """ 
        Connects to Mongo Database and gets the pages collection.
  
        Parameters: None  
        Returns: None  
        """
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.pages_collection = db["pages"]

    def _read_config(self):
        """ 
        Reads the Bidtracker username/password and which auctions to read from the config file.
  
        Parameters: None  
        Returns: None  
        """        
        config = configparser.ConfigParser() 
        configFilePath = 'PennyAuctions.config'
        config.read(configFilePath)
        self._username = config['login-info']['username']
        self._password = config['login-info']['password']
        self._auction_pages = dict(config['auction-pages'])        

    def login(self, sleep_time=1):
        """ 
        Uses requests to log into bid tracker class.  
  
        Parameters: 
            sleep_time(float): How many seconds to sleep after logging in (to prevent server overload)
        Returns: None  
        """       
        self._read_config()  
        r = self._session.get("https://www.bidtracker.info/Account/Login" )
        print (r.status_code)
        soup = BeautifulSoup(r.text, 'html.parser')
        vs = soup.find(id='__VIEWSTATE')
        vsg = soup.find(id='__VIEWSTATEGENERATOR')
        ev = soup.find(id='__EVENTVALIDATION')
        payload = { 
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vs["value"],
            '__VIEWSTATEGENERATOR': vsg["value"],
            '__EVENTVALIDATION': ev["value"],
            'ctl00$MainContent$UserName': self._username,
            'ctl00$MainContent$Password': self._password,
            'ctl00$MainContent$ctl05': "Log+in"
        }

        time.sleep(sleep_time)
        post = self._session.post("http://www.bidtracker.info/Account/Login", data=payload)
        print (post.status_code)

        time.sleep(sleep_time)

    def _get_all_auction_ids_for_group(self, auction_group):
        """ 
        Returns a list of all the auctionIds for a particular auction group (e.g. Amazon $50 + 30 bids)
  
        Parameters: auction_group (str): The auction group to be read(e.g. Amazon $50 + 30 bids)  
        Returns: auction_ids (list): The list of all the auction_ids as strings 
        """       
        url = "http://www.bidtracker.info/AllAuctionsByDesc?hash="+self._auction_pages[auction_group]+"&site=quibids"
        r = self._session.get(url)
        split = r.text.split("auction_id=")
        auction_ids = [s.split('"')[0] for s in split[1:]]
        time.sleep(4)
        return auction_ids

    
    
    def _scrape_auction(self, aID, auction_group, sleep_time=1):
        """ 
        Scrapes all three relevant auction pages for a specific auction

        Parameters:
            aID(str): The id of the auction to be scraped
            auction_group(str): The group of the auction ("e.g. Amazon $50 + 30 bids)
            sleep_time(float): The number of seconds to sleep between each scrape.
        Returns: 
            page_dict(dict): A dictionary of the three raw html pages that were scraped (Auction, AuctionTable, AuctionHistory)
        """       
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
        """ 
        Scrapes all auctions for an auction group (e.g. Amazon $50 + 30)
  
        Parameters: 
            auction_group (str): The group to be scraped.
            break_after (int): The number of scrapes after which you should quit.
        Returns: 
            None  
        """       
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


    def scrape(self, break_after):
        """ 
        Reads the config file, logs into Bidtracker.com, and then proceeds to scape all auction groups.
  
        Parameters: 
            break_after (int): The number of scrapes after which you should quit.
        Returns: None  
        """        
        self._connect_to_mongodb()
        with requests.Session() as self._session:
            self.login(3)
            for auction_group in self._auction_pages.keys():
                self._scrape_auction_group(auction_group, break_after)
            
    def scrape_upcoming_auctions(self):
        """ 
        Scapes the page for immediately upcoming auctions (used by the live tracker)

        Parameters: None
        Returns:
            str: The raw HTML for the upcoming auctions
        """        
        r = self._session.get("http://www.bidtracker.info/AllAuctionsTable?site=quibids&future=true")
        return r.text
 

if __name__ == "__main__": 
    if len(sys.argv) != 2:
        print ("Usage: BidTrackerScraper.py [#break_after]")
        sys.exit()
        
    break_after = int(sys.argv[1])
    bts = BidTrackerScraper()
    bts.scrape(break_after)