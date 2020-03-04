import pandas as pd
import psycopg2 as pg2
import pickle

class PrevInfo:
    """ 
    Creates a table of previous user history that gets pickled for the live auction tracker.
      
    Attributes: 
        prev_df(DataFrame): The db client of the mongoDB
    """
     
    def __init__(self):
        """ 
        The constructor for PrevInfo class. 
  
        Parameters: None
        Returns: None  
        """
        self.prev_df = None
        self.connect_to_sql()

    def connect_to_sql(self):
        """ 
        The constructor for PrevInfo class. 
  
        Parameters: None
        Returns: None  
        """
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
        """ 
        Gets all the previous auction information for a given user 
  
        Parameters: 
            username(str): The name of the user being checked.
        Returns: None  
        """
        return self.prev_df[self.prev_df.username==username]


    def pickle(self, filename):
        """ 
        pickles the model to the filename. 
  
        Parameters: 
            filename(str): The filename to pickle to.
        Returns: None  
        """
        pickle.dump( self, open( filename, "wb" ) )


