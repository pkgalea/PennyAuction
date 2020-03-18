import pymongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import PrevInfo
import pandas as pd
import numpy as np
import json
import os

class LiveAuctionProcessor:

    def __init__(self, auction_dict, prev_user_info, penny_model):
        self.auction_dict = auction_dict
        self.auction_id = auction_dict["auctionid"]
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        db = myclient["penny"]
        self.sniffed_collection = db["sniffed_auctions"]
        self.tracking_collection = db["tracking"]
        self.validation_collection = db["validation"]
        self.bh = []
        self.prev_user_info = prev_user_info
        self.my_username = "AAAAAAHH"
        self.penny_model = penny_model
        self.out_dict = {"cardvalue": auction_dict["cardvalue"], "bidvalue": auction_dict["bidvalue"], "cardtype": auction_dict["cardtype"]}
        self.tracking_collection.insert_one({"_id": self.auction_id, "data": self.out_dict})
        self.sold = False
        self.sl = 350
        self.is_live = False
        self.columns = ['auctionid', 'is_winner', 'cardtype', 'cashvalue', 'cardvalue', 'fee',
       'bidvalue', 'limited_allowed', 'is_locked', 'auctiontime', 'bid',
       'is_bidomatic', 'bids_so_far', 'username', 'prevusers', 'giveup',
       'eventual_bids', 'eventual_win_price', 'debut', 'bom_streak',
       'bom_bids_so_far', 'perc_to_bin', 'username0', 'distance0',
       'is_bidomatic0', 'bids_so_far0', 'bom_bids_so_far0', 'bom_streak0',
       'perc_to_bin0', 'prev_is_new_user0', 'prev_auction_count0',
       'prev_overbid0', 'prev_giveup_one0', 'prev_give_before_six0',
       'prev_wins0', 'prev_bids0', 'prev_bom_bids0', 'username1', 'distance1',
       'is_bidomatic1', 'bids_so_far1', 'bom_bids_so_far1', 'bom_streak1',
       'perc_to_bin1', 'prev_is_new_user1', 'prev_auction_count1',
       'prev_overbid1', 'prev_giveup_one1', 'prev_give_before_six1',
       'prev_wins1', 'prev_bids1', 'prev_bom_bids1', 'username2', 'distance2',
       'is_bidomatic2', 'bids_so_far2', 'bom_bids_so_far2', 'bom_streak2',
       'perc_to_bin2', 'prev_is_new_user2', 'prev_auction_count2',
       'prev_overbid2', 'prev_giveup_one2', 'prev_give_before_six2',
       'prev_wins2', 'prev_bids2', 'prev_bom_bids2', 'username3', 'distance3',
       'is_bidomatic3', 'bids_so_far3', 'bom_bids_so_far3', 'bom_streak3',
       'perc_to_bin3', 'prev_is_new_user3', 'prev_auction_count3',
       'prev_overbid3', 'prev_giveup_one3', 'prev_give_before_six3',
       'prev_wins3', 'prev_bids3', 'prev_bom_bids3']


    def add_auction_level_fields(self):
        self.auction_dict["idx"]=0
        self.auction_dict["is_winner"] = None
        self.auction_dict["auctiontime"] = datetime.now()+ timedelta(hours=-4) + timedelta(seconds=self.sl)
        self.auction_dict["is_bidomatic"] = True
        self.auction_dict["bids_so_far"] = None
        self.auction_dict["username"] = self.my_username
        self.auction_dict["giveup"] = None
        self.auction_dict["eventual_bids"] = None
        self.auction_dict["eventual_win_price"] = None
        self.auction_dict["debut"] = None
        self.auction_dict["bom_streak"] = None
        self.auction_dict["bom_bids_so_far"] = None
        self.auction_dict["perc_to_bin"] = None
        self.auction_dict["is_locked"] = False

    def process_bid_history(self):
        bid = len(self.bh)+1
        self.auction_dict["bid"] = bid
        user_dict = {}
        cur_opponent = 0
        found_users = {}
        for r in self.bh[-1::-1]:
            username = r['username']
            cur_bid = r['bid']
            is_bidomatic = r['is_bidomatic']
            if username == self.my_username:
                continue
            if (username not in found_users.keys()):
                user_dict[cur_opponent]={"username":username, "bids_so_far": 0.0, "bom_bids_so_far": 0.0, "distance": float(bid-cur_bid), "is_bidomatic": is_bidomatic, "bom_streak": 0.0,  "bom_streak_on": True}
                found_users[username] = cur_opponent
                cur_opponent += 1
            my_row = user_dict[found_users[username]] 
            my_row ["bids_so_far"] += 1
            if (is_bidomatic):
                my_row["bom_bids_so_far"]+=1
                if my_row["bom_streak_on"]:
                    my_row["bom_streak"] += 1
            else:
                my_row["bom_streak_on"] = False
        return user_dict

    def get_prev_user_info(self, user_dict, user_dict_len, prev_cols):   
        for i in range(user_dict_len):
            str_i = str(i)
            ud = user_dict[i]
            prev_info = self.prev_user_info.get_users_previous_info(ud["username"])
            if prev_info.shape[0]==0:
                ud["prev_is_new_user"] = 1
                ud["prev_auction_count"] = 1
                for pc in prev_cols[1:]:
                    ud[pc] = 0
            else:
                ud["prev_is_new_user"] = 0   #FixMe
                for pc in prev_cols:
                    ud[pc] = prev_info[pc+"0"][prev_info.index[0]]
            #, prev_overbid0, prev_giveup_one0, prev_give_before_six0, prev_wins0, prev_bids0, prev_bom_bids0
            ud["perc_to_bin"]=ud["bids_so_far"]/(self.auction_dict["cashvalue"]*2.5)
            for k in ud:
                self.auction_dict[k+str_i] = ud[k]


    def fill_in_info_if_less_than_4_users (self, user_dict_len, user_cols, prev_cols):
        for i in range (user_dict_len,4):
            for c in prev_cols + user_cols:
                self.auction_dict[c+str(i)] = np.nan
            self.auction_dict["is_bidomatic"+str(i)] = None
            self.auction_dict["perc_to_bin"+str(i)] = np.nan
            self.auction_dict["prev_is_new_user" + str(i)] = np.nan
       

    def process(self):
        user_cols = ["username", "bids_so_far", "bom_bids_so_far", "distance", "is_bidomatic", "bom_streak"]
        prev_cols = ['prev_auction_count', 'prev_overbid', 'prev_giveup_one', 'prev_give_before_six', 'prev_wins', 'prev_bids', 'prev_bom_bids']
        self.add_auction_level_fields()
        user_dict = self.process_bid_history()
        user_dict_len = min(4, len(user_dict)) 
                
        self.get_prev_user_info(user_dict, user_dict_len, prev_cols)
        self.fill_in_info_if_less_than_4_users(user_dict_len, user_cols, prev_cols)
            
        self.auction_dict["prevusers"] = len(user_dict)
        return {k:[v] for k, v in self.auction_dict.items()} 



    def check_for_new_bids(self):
        #print (self.auction_id)
        for u in self.sniffed_collection.find({"auction_id":self.auction_id}):
            if ("auction_complete" in u.keys()):
                return False
            if ("auction_live" in u.keys()):
                self.is_live = True
            else:
                my_last_bid = len(self.bh)
                new_bh = u["bh"]
                newest_bid = new_bh[0]["bid"]
                self.sl = u["sl"]
                bids_to_get = newest_bid - my_last_bid
                for a in new_bh[bids_to_get-1::-1]:
                    self.bh.append({"bid":a["bid"], "username":a["username"], "is_bidomatic": a["is_bidomatic"]})
                if len(self.bh)>0 0 and self.bh[-1]["bid"] != len(self.bh):
                    print ("*****************NOT FULLY TRACKING**************")
                    print (self.bh)
                self.sniffed_collection.delete_one({"auction_id":self.auction_id, "bid":u["bid"]})
        return True


    def calculate_ev(self):
        df_out = pd.DataFrame.from_dict({k:[v] for k, v in self.auction_dict.items()})
        df_out = df_out[self.columns]
        df_out["is_bidomatic"]=True
        bom_proba =  self.penny_model.predict_proba_calibrated(df_out)[:,1][0]
        df_out["is_bidomatic"]=False
        manual_proba =  self.penny_model.predict_proba_calibrated(df_out)[:,1][0]

        if (len(self.bh) > 0):
            bid = self.bh[-1]["bid"] + 1
            last_user = self.bh[-1]["username"]
        else:
            bid = 1
            last_user = "None yet"
        potential_profit = self.auction_dict["cashvalue"] - self.auction_dict["fee"] - bid/100 - .40
        potential_loss = -.40
        bom_ev = potential_profit * bom_proba + potential_loss * (1-bom_proba)
        manual_ev = potential_profit * manual_proba + potential_loss * (1-manual_proba)
        
        if (last_user == self.my_username):
            self.validation_collection.insert_one(self.prev_auction_dict)
            #filename = "../tracking/" + self.auction_dict["auctionid"] + "_" + str(bid)
            #if not os.path.exists(filename):
                #df_out.to_csv(filename)
                #print("Here", manual_proba, bom_proba, manual_ev, bom_ev)
                #f=open(filename, "a+")
                #f.write(f"{manual_proba}, {bom_proba}, {manual_ev}, {bom_ev}")
                #f.close()
            
        self.auction_dict["potential_profit"] = potential_profit
        self.auction_dict["bom_proba"] = bom_proba
        self.auction_dict["manual_proba"] = manual_proba
        self.auction_dict["bom_ev"] = bom_ev
        self.auction_dict["manual_ev"] = manual_ev
        self.out_dict["potential_profit"] = potential_profit
        self.out_dict["bom_proba"] = bom_proba
        self.out_dict["manual_proba"] = manual_proba
        self.out_dict["bom_ev"] = bom_ev
        self.out_dict["manual_ev"] = manual_ev
        self.out_dict["bid"] = bid-1
        self.out_dict["last_user"]= last_user
        self.out_dict["tracking_OK"] = len(self.bh)== 0 or self.bh[-1]["bid"] == len(self.bh)
        self.out_dict["sl"]=self.sl   
        self.out_dict["is_live"]=self.is_live
        self.tracking_collection.update_one({"_id":self.auction_id}, {"$set": {"data": self.out_dict}})


    def get_expected_value(self):
        prev_len = len(self.bh)
        is_not_yet_live = self.is_live
        if not self.check_for_new_bids():
            self.tracking_collection.delete_many({"_id":self.auction_id})
            return None
        if (prev_len != len(self.bh) or len(self.bh)==0 or is_not_yet_live != self.is_live):
            self.prev_auction_dict = self.auction_dict.copy()
            self.process()
            self.calculate_ev()
        return self.out_dict
  
if __name__ == "__main__":
    pass

