import pymongo
from bs4 import BeautifulSoup
import time
from datetime import datetime


""" 
    Parses the raw html pages downloaded by the BidTrackerScraper and stores the important features in the auctions colleciton in Mongo.  
      
    Attributes: 
        auction_list (list):  A list of auction dictonary objects.
    """
class MongoParser:

    def __init__(self):
        """ 
        The constructor for the MongoParser class. 
  
        Parameters: None  
        Returns: None
        """
        self.auction_list = []

    def parse_auction_title (self, auction_title):
        """ 
        Parses the title of an auction from the Bid tracker website to get the type of item, value and the number of voucher bids 
  
        Parameters: 
            auction_title(str): The auction title to be parsed  
        Returns:
            (str, str, str, str):  Cash Value, Card Value, Card Type and Bid Value for the auction as strings.  
        """
        card_value, auction_title = auction_title.split(" ", 1)
        has_bids = "Bids" in auction_title
        has_gift_card = "Gift Card" in auction_title
        is_vouchers = "Voucher" in auction_title
        is_limit_buster = "Buster" in auction_title
        cash_value = auction_title.split("(")[1]
        cash_value = cash_value.split(")")[0][1:]
        if has_bids and has_gift_card:
            #print("case1")
            card_type, bid_value = auction_title.split (" Gift Card AND", 1)
            bid_value = bid_value.split(" Bids")[0][1:]
            card_value = card_value[1:]
        elif has_gift_card and not has_bids:
            #print("case2")
            card_type = auction_title.split (" Gift Card")[0]
            card_value = card_value[1:]
            bid_value = str(int((float(cash_value) - int(card_value))*2.5))
        elif has_bids and not has_gift_card and is_vouchers:
            #print("case3")
            card_type = "None"
            bid_value = card_value
            card_value = "0"
        elif is_limit_buster:
            #print("case4")
            card_type = "Buster"
            if "Two" in auction_title:
                card_value = "30"
            elif "One" in auction_title:
                card_value = "15"
            elif "Four" in auction_title:
                card_value = "60"
            else:
                print("What is this?")
                return None, None, None, None
 
            bid_value = str(int((float(cash_value) - int(card_value))*2.5))
            card_value = card_value
            return cash_value, card_value, card_type, bid_value
        else:
            #print("what is this?") 
            return None, None, None, None
        return cash_value, card_value, card_type, bid_value


    def parse_upcoming_auction_page(self, html):
        """ 
        Parses the upcoming auction pages to be fed to the live auction monitor
  
        Parameters: 
            html:  The raw html of the upcoming auctions pages from BidTracker
        Returns: 
            list (dict): A list of auction dictionaries for the upcoming auctions
        """
        soup = BeautifulSoup(html, 'html.parser')
        upcoming_auctions = []
        for tr in soup.find_all("tr", {"class": "tr-inner"}):
            tds = tr.find_all("td")
            auction_id = tds[1].find("a").text
            description = tds[2].text
            #print(description)
            limited_allowed = description[0].startswith('L')
            if (limited_allowed):
                description=description[1:]
            cash_value, card_value, card_type, bid_value = self.parse_auction_title(description)
            #print(cash_value, card_value, card_type, bid_value )
            if (cash_value):
                time_str = tds[3].text
                #print(time_str)
                if time_str.startswith("00"):
                    t = time.strptime(tds[3].text, "%H:%M:%S")
                    #print(t.tm_min*60+t.tm_sec)
                else:
                    break

                auction_dict = {
                    "auctionid": auction_id,
                    "cashvalue": int(float(cash_value)),
                    "cardvalue": int(card_value),
                    "cardtype": card_type,
                    "bidvalue": int(bid_value),
                    "limited_allowed": limited_allowed,
                    "seconds_left": t.tm_min*60+t.tm_sec
                }
                upcoming_auctions.append(auction_dict)
        #print(upcoming_auctions)
        return upcoming_auctions        

    def parse_auction_page(self, qauction_id, html, auction_dict):
        """ 
        Parses the Auction.asp page from BidTracker, which has general auction info
  
        Parameters: 
            qauction_id(str): The QuiBids Auction ID to be scraped
            html(str): The raw html scraped for that auction
            auction_dict(dict):  The dictionary of features to be filled

        Returns: None
        """
        auction_title=html.split(qauction_id + " - ")[1]
        cash_value, card_value, card_type, bid_value = self.parse_auction_title(auction_title)      
        limited_allowed = "is NOT LIMITED" not in html
        auction_dict["cashvalue"] = int(cash_value)
        auction_dict["cardvalue"]=int(card_value)
        auction_dict["bidvalue"]=int(bid_value)
        auction_dict["cardtype"]=card_type
        auction_dict["limited_allowed"]=limited_allowed

        
    def parse_auction_table_page(self, qauction_id, html, auction_dict):
        """ 
        Parses the Auction Table Page from Bid Tracker which has info like run time, locked price and tracking
  
        Parameters: 
            qauction_id (str):  The id of the auction to be scraped
            html: The raw html of the auction table page scraped by the bid scraper.
            auction_dict: The auction dictionary to be filled in with features
        Returns: None
        """
        soup = BeautifulSoup(html, 'html.parser')
        tds = soup.find_all("td")
        tracking = str(tds[0]).split('%')[0].split()[1]
        last_update = str(tds[1]).split ("update: ")[1].split("</td>")[0]    
        run_time = str(tds[3]).split("runtime : ")[1].split("</td>")[0]
        auction_dict["tracking"] = float(tracking)
        auction_dict["auctiontime"] = datetime.strptime(last_update, '%m/%d/%Y %I:%M:%S %p') #last_update
        t = datetime.strptime(run_time, "%H:%M:%S")
        auction_dict["runtime"] = t.hour*3600+t.minute*60+t.second
        lock_price = html.split('<div id="div_lock_status" style="display: none;">')[1].split("<")[0]  
        if (lock_price):
            lock_price = int(float(lock_price)*100)
        auction_dict["lock_price"] = lock_price
        

    def parse_history_page(self, qauction_id, html):
        """ 
        Parse the history page from the Bid Tracker class which has the history of the bids of the auction.
  
        Parameters: 
            qauction_id (str):  The id of the auction to be scraped
            html: The raw html of the auction history page scraped by the bid scraper.

        Returns: 
            list (dict): A list of bid history dictionaries (auction_id, bid, user, is_bidomatic)
        """
        soup = BeautifulSoup(html, 'html.parser')
        tds = soup.find_all("td")[3:]
        bids_list = []
        for i in range(0, len(tds), 4):
            bid = tds[i].text.strip() 
            user = tds[i+2].text.strip() 
            bid_type = tds[i+3].text.strip()   
            is_bidomatic = bid_type=="Bidomatic"
            bids_list.append({"auction_id": int(qauction_id), "bid": int(bid), "user": user, "is_bidomatic": is_bidomatic})
        return bids_list

    def parse(self):
        """ 
        Goes through all pages in the page collection and parses the pages if the auction id is not already in the auction collection. 
  
        Parameters: None  
        Returns: None
        """
        
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        pages_collection = db["pages"]
        auction_collection = db["auctions"]
        bids_collection = db["bids"]
            
        i = 0 
        prev_auct_group = "bozo"
        for p in pages_collection.find({}):
            if i % 100 == 0:
                print(i)
            i += 1
            qauction_id = p['_id']
            if auction_collection.count_documents({"_id":int(qauction_id)})==0:
                if (prev_auct_group != p['AuctionGroup']):
                    print(qauction_id, p['AuctionGroup'])
                    prev_auct_group = p['AuctionGroup']
                auction_dict = {"_id": int(qauction_id)}
                self.parse_auction_page(qauction_id, p['Auction'], auction_dict)
                self.parse_auction_table_page(qauction_id, p['AuctionTable'], auction_dict)
                bids_list = self.parse_history_page(qauction_id, p['AuctionHistory'])
                auction_collection.insert_one(auction_dict,{"ordered":"True"})
                bids_collection.insert_many(bids_list)


if __name__ == "__main__": 
    mp = MongoParser()
    mp.parse()