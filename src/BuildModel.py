import pandas as pd
import psycopg2 as pg2
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import auc, confusion_matrix, precision_score, recall_score, accuracy_score, roc_curve
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as Pipeline_imb
import numpy as np
import pickle

class PennyModel:

    def __init__ (self):
        self.model = None

    def transform(self, X):

        rX = X.copy()
        print ("2. Transforming data")
        rX.is_bidomatic0 = rX.is_bidomatic0.astype(str)
        rX.is_bidomatic1 = rX.is_bidomatic1.astype(str)
        rX.is_bidomatic2 = rX.is_bidomatic2.astype(str)
        rX.is_bidomatic3 = rX.is_bidomatic3.astype(str)
        rX.prev_win_bids0 = rX.prev_win_bids0.astype(str)
        rX.prev_win_bids1 = rX.prev_win_bids1.astype(str)
        rX.prev_win_bids2 = rX.prev_win_bids2.astype(str)
        rX.prev_win_bids3 = rX.prev_win_bids3.astype(str)
        rX["fee"]=[0 if x == 0 else (1 if x < 50 else 1.99) for x in rX["cardvalue"]]
        rX["time_of_day"]=[x.hour*60+x.minute for x in rX["auctiontime"]]
        rX["is_weekend"] = [x.weekday() >=6 for x in rX["auctiontime"]]
        rX["is_bom_150_0"] = rX['bom_streak0']==150
        rX["is_bom_150_1"] = rX['bom_streak1']==150
        rX["is_bom_150_2"] = rX['bom_streak2']==150
        rX["is_bom_150_3"] = rX['bom_streak3']==150
        return rX

    def fit(self, X, y):

        self.X = self.transform(X)

        categorical_features = ['cardtype', 'limited_allowed', 'is_locked', 'is_bidomatic', 'is_bidomatic0', 
                                'is_bidomatic1', 'is_bidomatic2', 'is_bidomatic3', 'is_bom_150_0', 'is_bom_150_1', 'is_bom_150_2', 'is_bom_150_3']
        numeric_features = ['bid', 'cashvalue','bidvalue', 'prevusers', 
                            'bids_so_far0', 'perc_to_bin0', 
                            'distance1', 'bids_so_far1',  'perc_to_bin1',
                            'distance2', 'bids_so_far2',  'perc_to_bin2',
                            'distance3', 'bids_so_far3', 'perc_to_bin3', 'is_weekend', 'time_of_day']
        numeric_transformer = Pipeline_imb(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value=-1)),
        ])
        categorical_transformer = Pipeline_imb(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
            ('onehot', OneHotEncoder(handle_unknown='error', drop='first'))])
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)])
        self.model = Pipeline_imb(steps=[('preprocessor', preprocessor),
                                ('sampler', RandomUnderSampler()),
                            ('classifier', RandomForestClassifier())])

        print ("4. Fitting model")
        self.model.fit(self.X, y)

    def pickle(self, filename):
        print ("5. Pickling model as penny_auction.pickle")
        pickle.dump( self, open( filename, "wb" ) )



if __name__ == "__main__": 
    print ("1. Reading from database")
    conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='')
    df = pd.read_sql ("""Select * from auction_full""", conn)


    print ("3. Splitting into Train/Test Sets")
    y = df['is_winner']
    X = df
    X_train, X_test, y_train, y_test = train_test_split(X, y )#, random_state=0) 

    pm = PennyModel()
    pm.fit(X, y)
    pm.pickle ("pickle/pickle.pickle")
