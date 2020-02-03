import pandas as pd
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import bs4
import time


class BidTrackerDownloader:
    """ 
    __init__ 
  
    Connects to MongoDB and gets the scrabble collections
  
    Parameters: 
    none
  
    Returns: 
    none
  
    """
    def __init__(self):
        client = MongoClient("mongodb://localhost:27017/")
        self._penny_db = client[ "penny" ]
        self._pages_collection = self._penny_db[ "auctions" ]
        self._fgames_collection = self._penny_db[ "histories"]


    def add_game_to_collection(self, gameid, lexicon, p1_id, p1_name, p2_id, p2_name):
        if (self._fgames_collection.find({'game_num': gameid}).count() != 0):
            return False
        else:
            with open("download.log", "w+") as logf:
                print ("     GameID: {:}   Lexicon: {:}   P1:({:},{:}) P2:({:},{:})".format(gameid, lexicon, p1_name, p1_id, p2_name, p2_id))
                    
                try:
                        url = "https://www.cross-tables.com/annotated.php?u=" + gameid
                        r = requests.get(url, headers={"User-Agent": "XY"})
                        if (r.status_code==200):
                            self._fgames_collection.insert_one({"game_num": gameid, "lexicon": lexicon, "p1_name": p1_name, "p1_id": p1_id, "p2_name": p2_name, "p2_id": p2_id, "content": r.text})
                        else:
                            print ("error", gameid)
                        time.sleep(1)

                except Exception as e:     
                    logf.write("Failed to download {0}\n".format(gameid))
        return True

    def get_list_of_games_page(self, page_index):
           url = "https://www.cross-tables.com/annolistself.php?offset=" + str(page_index)
           r = requests.get(url, headers={"User-Agent": "XY"})
           print(page_index, r.status_code)
           if (r.status_code==200):
               pass
#                new_pages_collection.insert_one({"page_num": i, "content": r.text})
           else:
                print ("error", page_index)
                return None
           return r
    
    def download_games(self):
        c = 0
        all_games_found = False
        page_index = 1
        while not all_games_found:
#        games_collection = scrabble_db[ "games_collection" ]
#        for p in self._pages_collection.find({'page_num': {"$gt": 0}}):  #({'page_num':15501}):
 
            r = self.get_list_of_games_page(page_index)

            print(c)
            c+=1
        #    print(p['content'])
  #          page_num = p['page_num']
  #          print (page_num)
            soup = BeautifulSoup(r.content, 'html.parser')
            for i in range (1, 101):
                game = soup.find(id="row"+str(i))
                if not game:
                    return

                gameid, lexicon, p1_id, p1_name, p2_id, p2_name = self.get_game_info(game)              
                if not self.add_game_to_collection(gameid, lexicon, p1_id, p1_name, p2_id, p2_name):
                    return;   
            page_index +=1

    def login(self, session):
        r = session.get("http://www.bidtracker.info/Account/Login" )
        print (r.status_code)
        soup = BeautifulSoup(r.text, 'html.parser')
        vs = soup.find(id='__VIEWSTATE')
        vsg = soup.find(id='__VIEWSTATEGENERATOR')
        ev = soup.find(id='__EVENTVALIDATION')
        payload['__EVENTTARGET']=''
        payload['__EVENTARGUMENT']='' 
        payload['__VIEWSTATE']=vs["value"]
        payload['__VIEWSTATEGENERATOR'] = vsg["value"]
        payload['__EVENTVALIDATION'] = ev["value"] #+ "&ctl00%$MainContent$UserName=pkgalea&&ctl00$MainContent$Password=p3T3two8!&ctl00$MainContent$ctl05=Log+in"
        payload['ctl00$MainContent$UserName'] = "pkgalea"
        payload['ctl00$MainContent$Password'] = "p3T3two8!"
        payload['ctl00$MainContent$ctl05'] = "Log+in"

    time.sleep(4)
    post = session.post("http://www.bidtracker.info/Account/Login", data=payload)
    print (post.status_code)
    time.sleep(4)
    r = session.get("http://www.bidtracker.info/AllAuctionsByDesc?hash=1119122541&site=quibids") 
    split = r.text.split("auction_id=")
    auctionIDs = [s.split('"')[0] for s in split[1:]]
    time.sleep(4)

    def update_auctions(self):
        session = requests.Session()
        cat_dict = {
            "url":"http://www.bidtracker.info/AuctionListByDesc?site=quibids&hash=113345535",
            "type": "Amazon",
            "value": "75",
            "bids": "30"
        }
        self.login(session)
        with open("download.log", "w+") as logf:
            try:
                url = cat_dict["url"]
                print(url)
                r = session.get(url)
                if (r.status_code==200):
                    print (r.text)
                else:
                    print ("error", r.status_code)
        #      time.sleep(10)
            except Exception as e:
                print(r.status_code)     
                #logf.write("Failed to download {0}\n".format(gameid))

                
if __name__ == "__main__":
    ctd = BidTrackerDownloader()
    ctd.update_auctions()
