from BuildModel import PennyModel
import psycopg2 as pg2
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import auc, confusion_matrix, precision_score, recall_score, accuracy_score, roc_curve
import matplotlib.pyplot as plt
import numpy as np
import pickle
from datetime import datetime
import importlib


class ModelEvaluator:
    
    def __init__(self, model, sampling_ratio, train_cut_off, test_cut_off):
        self.model = model
        self.sampling_ratio = sampling_ratio
        self.train_cut_off = train_cut_off
        self.test_cut_off = test_cut_off

    def get_data(self):
        print ("Connecting to SQL")
        conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='password')

        print ("Reading Dataset")
        df = pd.read_sql ("""Select *  from auction_full where auctiontime >= '2020-01-01'""", conn)

        print ("Splitting into Train/Test Sets")
        df = df.sort_values("auctiontime")
        conn.close()
        X = df
        y = df['is_winner']
        return X, y
    
    def build_model():
        importlib.reload(BuildModel)
        print ("Fitting Model")
        #def create_model():
            # Define a Keras model
        #    model = Sequential()

        #    # Add a Dense layer that uses the sigmoid function
        #    model.add(Dense(units=30, kernel_initializer='random_uniform',
        #                bias_initializer='zeros', activation='relu', input_dim=74))
        #    model.add(Dense(units=30, kernel_initializer='random_uniform',
        #                bias_initializer='zeros',  activation='relu'))
        #    model.add(Dense(units=1, activation='sigmoid'))
        #    
        #    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
        #    return model

        #clf = KerasClassifier(build_fn=create_model,epochs=5,batch_size=10)

        model = self.model #RandomForestClassifier(n_estimators=200, n_jobs=-1)
        #model = clf

        pm = BuildModel.PennyModel(model, sampling_ratio=self.sampling_ratio )
        return pm
        
    def fit_model(self):
        train_cut_off = dates[i-1]
        test_cut_off = dates[i]
        print(train_cut_off, test_cut_off)
        X_train = X[X.auctiontime <= train_cut_off]
        y_train = y[X.auctiontime <= train_cut_off]

        X_test = X[(X.auctiontime > train_cut_off)&(X.auctiontime <= test_cut_off)]
        y_test = y[(X.auctiontime > train_cut_off)&(X.auctiontime <= test_cut_off)]

        pm.fit(X_train, y_train)

    def get_score(self)
        cprobs = pm.predict_proba_calibrated(X_test)[:,1]
        pp, ap = get_actual_and_potential_profits(X_test,y_test)
        expected_value = np.multiply(cprobs, pp) -  (1-cprobs)*.4
        return ap[expected_value>0]

    def evaluate_model(self, model):
        

        





