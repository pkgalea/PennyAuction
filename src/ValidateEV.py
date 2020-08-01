
import psycopg2 as pg2
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import auc, confusion_matrix, precision_score, recall_score, accuracy_score, roc_curve
import numpy as np
import pickle
from datetime import datetime, date, timedelta
import importlib
import pymongo

print ("Connecting to SQL")
conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')

print ("Reading Dataset")
true_df = pd.read_sql ("""Select *  from auction_full where auctiontime >= '2020-03-01' and auctionid in (select distinct auctionid from auction_full where is_bidomatic)""", conn)

print ("Loading Model")
penny_model = pickle.load( open( "rf.pkl", "rb" ) )

my_df = true_df[true_df.username=='AAAAAAHH']
my_df.shape
my_winners = my_df[my_df.is_winner]
np.sum(my_winners.cashvalue - my_winners.fee- my_winners.bid/100) - my_df.shape[0]*.4

evs = []
aps = []
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["penny"]
validation_collection = db["validation"]
for v in validation_collection.find():
    df_row = df[(df.auctionid==int(v["auctionid"]))&(df.bid==v["bid"])]
    if (df_row.shape[0]==0):
        print("Shapeless")
        continue
    proba = penny_model.predict_proba_calibrated(df_row)[:,1]
    df_row.reset_index(inplace=True)
    if (df_row["is_bidomatic"][0]):
        vproba = v["bom_proba"]
    else:
        vproba = v["manual_proba"]
    potential_profit = v["cashvalue"] - v["fee"]- v["bid"]/100
    print("{}, {}, {}, {}, {}, {:.3f}, {:.3f}, {:.2f}, {:.2f}".format(v["cashvalue"], v["auctionid"], v["auctiontime"], df_row['auctiontime'][0], v["bid"], proba[0], vproba, potential_profit*proba[0]-.4, potential_profit* vproba-.4))
    evs.append(potential_profit*proba[0]-.4)
    if (df_row["is_winner"][0]):
        aps.append(potential_profit)
    else:
        aps.append(-.4)
    if df_row['auctionid'][0]==761247367:

        for k in v.keys():
            if (k in df_row.columns):
                print(k, df_row[k][0], v[k])
    print("**************************************")