import psycopg2 as pg2
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import auc, confusion_matrix, precision_score, recall_score, accuracy_score, roc_curve
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import datetime, date, timedelta
import importlib
import pymongo

print ("Connecting to SQL")
conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')

print ("Reading Dataset")
df = pd.read_sql ("""Select *  from auction_full where auctiontime >= '2020-03-01' and auctionid in (select distinct auctionid from auction_full where is_bidomatic) and username='AAAAAAHH' order by bid""", conn)
df.to_csv("validation.csv")