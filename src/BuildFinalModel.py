import BuildModel
import PrevInfo
import psycopg2 as pg2
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

print ("Connecting to SQL")
conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')

print ("Reading Dataset")
df = pd.read_sql ("""Select *  from auction_full where auctiontime >= '2020-01-01'""", conn)
conn.close()

X = df
y = df['is_winner']

model = RandomForestClassifier(n_estimators=200, n_jobs=-1)

pm = BuildModel.PennyModel(model, is_regressor=False,sampling_ratio=.5 )
pm.fit(X, y)
pm.pickle("rf.pkl")
pi = PrevInfo()
pi.pickle("pi.pkl")
