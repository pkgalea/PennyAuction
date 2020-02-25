import psycopg2 as pg2
from datetime import datetime, date, timedelta
import subprocess
import pandas as pd
import sys

def get_list_of_dates():

    sdate = date(2019, 9, 20)   # start date
    edate = date(2020, 2, 27)   # end date

    delta = edate - sdate       # as timedelta

    return [str(sdate + timedelta(days=i)) for i in range(delta.days + 1)]
        
for d in get_list_of_dates():
    print(d)
    bashCommand = "sudo -u postgres psql -d penny -f new_transformations.sql -v auction_date='" + d + "'"
    process = subprocess.Popen(bashCommand.split())
    output, error = process.communicate()
    