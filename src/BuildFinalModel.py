from BuildModel import PennyModel
from PrevInfo import PrevInfo
import psycopg2 as pg2
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

print ("Connecting to SQL")
conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')

print ("Reading Dataset")
df = pd.read_sql ("""Select *  from auction_full where auctiontime >= '2020-03-01' and auctionid in (select distinct auctionid from auction_full where is_bidomatic)""", conn)
conn.close()

X = df
y = df['is_winner']  

model = RandomForestClassifier(n_estimators=200)

pm = PennyModel(model,sampling_ratio=.5 )
pm.fit_transform(X, y)
pm.pickle("rf.pkl")
pi = PrevInfo()
pi.pickle("pi.pkl")
