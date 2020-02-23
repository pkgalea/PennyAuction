import pymongo
from bs4 import BeautifulSoup
import time
from datetime import datetime



def parse_auction_title (auction_title):
    card_value, auction_title = auction_title.split(" ", 1)
    has_bids = "Bids" in auction_title
    has_gift_card = "Gift Card" in auction_title
    is_vouchers = "Voucher" in auction_title
    cash_value = auction_title.split("(")[1]
    cash_value = cash_value.split(")")[0][1:]
    if has_bids and has_gift_card:
        card_type, bid_value = auction_title.split (" Gift Card AND", 1)
        bid_value = bid_value.split(" Bids")[0][1:]
    elif has_gift_card and not has_bids:
        card_type = auction_title.split (" Gift Card")[0]
        bid_value = "0"  
    elif has_bids and not has_gift_card and is_vouchers:
        card_type = "None"
        bid_value = card_value
        card_value = "$0"
    else:
        print("what is this?") 
        return None, None, None, None
    return cash_value, card_value, card_type, bid_value


class MongoParser:

    def __init__(self):
        self.auction_list = []



    def parse_auction_page(self, qauction_id, html, auction_dict):
        auction_title=html.split(qauction_id + " - ")[1]
        cash_value, card_value, card_type, bid_value = parse_auction_title(auction_title)      
        limited_allowed = "is NOT LIMITED" not in html
        auction_dict["cashvalue"] = int(cash_value)
        auction_dict["cardvalue"]=int(card_value[1:])
        auction_dict["bidvalue"]=int(bid_value)
        auction_dict["cardtype"]=card_type
        auction_dict["limited_allowed"]=limited_allowed

        
    def parse_auction_table_page(self, qauction_id, html, auction_dict):
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