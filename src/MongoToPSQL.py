import pymongo
import datetime
import psycopg2 as pg2
import sys

class MongoToPSQL:
    """ 
    Takes the parsed features from the Auctions collection in Mongo and fills the auctions and bids tables in psql
      
    Attributes: 
        db (MongoDBClient): The db client of the mongoDB
        password(str): The password for the PostgresSQL database
    """

    def __init__(self, password):
        """ 
        The constructor for MongoToPSQL class. 
  
        Parameters: 
            password(str): The password for the PostgresSQL database  
        Returns: None  
        """
        self.db = None
        self.password = password

    def migrate_auctions(self, cursor):
        """ 
        Migrates the auctions collection from Mongo to the auction table in PSQL
  
        Parameters: 
            cursor (MongoDBCursor): A cursor for the mongoDB auctions collection  
        Returns: None  
        """
        auction_collection = self.db["auctions"]
        sql = "SELECT qauctionid from auctions"
        cursor.execute(sql)
        already_found_qids = [x[0] for x in cursor.fetchall()]

        print ("auctions:")
        i = 0
        exclude_qauctionids = []
        for d in auction_collection.find({ "_id": { "$nin":  already_found_qids}}):
            if (i % 100 == 0):
                print (i)
            i += 1
            if d["tracking"] == 100.00 and d['auctiontime'] >= datetime.datetime(2019, 9, 19):
                lock_price = d['lock_price']
                if (not lock_price):
                    lock_price = 0
                sql = "INSERT INTO Auctions (qauctionid, cardvalue, bidvalue, tracking, auctiontime, runtime, limited_allowed, cashvalue, cardtype, lock_price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (d['_id'], d['cardvalue'], (d['cashvalue']-d['cardvalue'])*2.5, d['tracking'], d['auctiontime'], d['runtime'], d['limited_allowed'], d['cashvalue'], d['cardtype'], lock_price))
            else:
                exclude_qauctionids.append(d['_id'])

        return exclude_qauctionids

    def connect_to_mongo(self):
        """ 
        Connects to the MongoDB
  
        Parameters: None  
        Returns: None  
        """
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = myclient["penny"]

    def migrate_bids(self, cursor, exclude_qauctionids):
        """ 
        Migrates the bids collection from mongo to the bids table in PSQL
  
        Parameters:     
            cursor (MongoDBCursor): A cursor for the mongoDB auctions collection 
            exclude_qauctionids list(str):  A list of auctions to NOT migrate over to sql 
        Returns: None  
        """
        bids_collection = self.db["bids"]
        
        sql = "SELECT distinct auctionid from bids"
        cursor.execute(sql)
        already_found_qids = [x[0] for x in cursor.fetchall()] + exclude_qauctionids

        i = 0 
        for b in bids_collection.find({ "auction_id": { "$nin":  already_found_qids}}):
            sql = "SELECT count(*) from auctions where qauctionid = " + str(b['auction_id'])
            cursor.execute(sql)
            if (cursor.rowcount!=0):
                sql = "INSERT INTO bids (auctionid, bid, username, is_bidomatic) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (b['auction_id'], b['bid'], b['user'], b['is_bidomatic']))
            else:
                print ("ignoring" + b['auction_id'] + " not fully tracking")
            if (i % 1000 == 0):
                print (i)
            i += 1

    def migrate_to_sql(self):
        """ 
        Migrates the auctions and bids collections to psql 
  
        Parameters: None  
        Returns: None  
        """
        self.connect_to_mongo()

        conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password=self.password)
        with conn.cursor() as cursor:
        
            exclude_qauctionids = self.migrate_auctions(cursor)
            conn.commit()
   
            self.migrate_bids(cursor, exclude_qauctionids)
                
            conn.commit()
        conn.close()

if __name__ == "__main__": 
    if len(sys.argv) != 2:
        print ("Usage: MongoToPSQL.py [#usepassword]")
        sys.exit()
    if sys.argv[1] == "None":
        password = ''
    elif sys.argv[1] == "password":
        password = 'password'
    mts = MongoToPSQL(password)
    mts.migrate_to_sql()