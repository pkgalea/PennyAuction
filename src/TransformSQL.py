import psycopg2 as pg2
from datetime import datetime, date, timedelta
import subprocess
import pandas as pd
import sys

# TODO:  Pass in the dates.

class SQLAuctionTransformer:
    """
    simply calls the sql transform scripts
    Attributes: None
    """
    def __init__(self):
        """
            The constructor for the SQLAuctionTransformer
            Parameters: None
            Returns: None
        """
        pass

    def get_list_of_dates(self):
        """
            creates a list of dates between the two dates provided
            Parameters: None
            Returns: 
                list(str): A list of dates
        """
        sdate = date(2019, 9, 20)   # start date
        edate = date(2020, 3, 3)   # end date

        delta = edate - sdate       # as timedelta

        return [str(sdate + timedelta(days=i)) for i in range(delta.days + 1)]


    def run_sql_transformations(self):
        """
            Calls the new_transformations.sql script on a date by date basis
            Parameters: None
            Returns: None
        """ 
        conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')
        for d in self.get_list_of_dates():
            print(d)                
            df = pd.read_sql("Select count(*) as acount from auctions where auctiontime < '" + d + "' and qauctionID not in (SELECT DISTINCT AuctionID from bid_transform)", conn)
            print (df.acount[0])
            if (df.acount[0] > 0):
                bashCommand = "sudo -u postgres psql -d penny -f new_transformations.sql -v auction_date='" + d + "'"
                process = subprocess.Popen(bashCommand.split())
                output, error = process.communicate()
        conn.close

if __name__ == "__main__": 
    sat = SQLAuctionTransformer()
    sat.run_sql_transformations()