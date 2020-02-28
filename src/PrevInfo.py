import pandas as pd
import psycopg2 as pg2
import pickle

class PrevInfo:
        
    def __init__(self):
        self.prev_df = None
        self.connect_to_sql()

    def connect_to_sql(self):
        print ("Connecting to SQL")
        conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')
        self.prev_df = pd.read_sql("""
            with bozo as
            (
            Select username, max(auctiontime) as max_auctiontime from auction_full WHERE auctiontime <= '2020-01-16 22:53:19' group by username 
            )
            select bozo.username,  prev_auction_count0, prev_overbid0, prev_giveup_one0, prev_give_before_six0, 
            prev_wins0, prev_bids0, prev_bom_bids0 from bozo left join auction_full on bozo.username=Username0 
            and bozo.max_auctiontime=auction_full.auctiontime and auction_full.bids_so_far0=1
            """
            , conn)
        conn.close()

    def get_users_previous_info(self, username):
        return self.prev_df[self.prev_df.username==username]

    def pickle(self, filename):
        pickle.dump( self, open( filename, "wb" ) )


