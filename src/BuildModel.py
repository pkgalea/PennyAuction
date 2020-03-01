import pandas as pd
import psycopg2 as pg2
#from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as Pipeline_imb
import numpy as np
import pickle

class PennyModel:

    def __init__ (self, model, is_regressor=False, use_scaler=False, sampling_ratio = 1):
        self.model = model
        self.is_regressor = is_regressor
        self.sampling_ratio = sampling_ratio
        self.use_scaler = use_scaler
        self.categorical_features = ['cardtype', 'limited_allowed', 'is_locked', 'is_bidomatic', 'is_bidomatic0', 
                                'is_bidomatic1', 'is_bidomatic2', 'is_bidomatic3']
        self.numeric_features = ['bid', 'cashvalue','bidvalue', 'prevusers', 
                            'bids_so_far0', 'perc_to_bin0', 'bom_bids_so_far0', 'bom_streak0', 
                            'prev_is_new_user0', 'prev_auction_count0', 'prev_overbid0', 'prev_giveup_one0', 'prev_give_before_six0', 'prev_wins0', 'prev_bids0', 'prev_bom_bids0',
                            'distance1', 'bids_so_far1',  'perc_to_bin1', 'bom_bids_so_far1', 'bom_streak1', 
                            'prev_is_new_user1', 'prev_auction_count1', 'prev_overbid1', 'prev_giveup_one1', 'prev_give_before_six1', 'prev_wins1', 'prev_bids1', 'prev_bom_bids1',
                            'distance2', 'bids_so_far2',  'perc_to_bin2', 'bom_bids_so_far2', 'bom_streak2', 
                            'prev_is_new_user2', 'prev_auction_count2', 'prev_overbid2', 'prev_giveup_one2', 'prev_give_before_six2', 'prev_wins2', 'prev_bids2', 'prev_bom_bids2',
                            'distance3', 'bids_so_far3', 'perc_to_bin3', 'bom_bids_so_far3', 'bom_streak3', 
                            'prev_is_new_user3', 'prev_auction_count3', 'prev_overbid3', 'prev_giveup_one3', 'prev_give_before_six3', 'prev_wins3', 'prev_bids3', 'prev_bom_bids3',
                            'is_weekend', 'time_of_day'                            
                            ]
    def get_features_as_string(self):
        return ",".join(self.categorical_features + self.numeric_features)

    def get_column_names_from_ColumnTransformer(self, column_transformer):    
        col_name = []
        for transformer_in_columns in column_transformer.transformers_[:-1]:#the last transformer is ColumnTransformer's 'remainder'
            raw_col_name = transformer_in_columns[2]
            if isinstance(transformer_in_columns[1],Pipeline): 
                transformer = transformer_in_columns[1].steps[-1][1]
            else:
                transformer = transformer_in_columns[1]
            try:
                names = transformer.get_feature_names(self.categorical_features)
            except AttributeError: # if no 'get_feature_names' function, use raw column name
                names = raw_col_name
            if isinstance(names,np.ndarray): # eg.
                col_name += names.tolist()
            elif isinstance(names,list):
                col_name += names    
            elif isinstance(names,str):
                col_name.append(names)
        return col_name    

    def transform(self, X):

        rX = X.copy()
        #print ("2. Transforming data")
        rX.is_bidomatic0 = rX.is_bidomatic0.astype(str)
        rX.is_bidomatic1 = rX.is_bidomatic1.astype(str)
        rX.is_bidomatic2 = rX.is_bidomatic2.astype(str)
        rX.is_bidomatic3 = rX.is_bidomatic3.astype(str)

        rX["fee"]=[0 if x == 0 else (1 if x < 50 else 1.99) for x in rX["cardvalue"]]
        rX["time_of_day"]=[x.hour*60+x.minute for x in rX["auctiontime"]]
        rX["is_weekend"] = [x.weekday() >=6 for x in rX["auctiontime"]]

        return rX

    def fit(self, X, y):

        local_X = self.transform(X)
        self.train_pop = local_X.shape[0]
        self.target_pop = sum(y)
        self.sampled_train_pop = self.target_pop/self.sampling_ratio + self.target_pop
        self.sampled_target_pop = self.target_pop

        numeric_transformer = Pipeline_imb(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value=-1))
       #     ('scaler', StandardScaler())
        ])
        categorical_transformer = Pipeline_imb(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='unknown')),
            ('onehot', OneHotEncoder(handle_unknown='error', drop='first'))])
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, self.numeric_features),
                ('cat', categorical_transformer, self.categorical_features)])
        steps = [('preprocessor', preprocessor)]
        if self.is_regressor:
            steps.append (('regressor', self.model))
        else:
            steps.append(('sampler', RandomUnderSampler(sampling_strategy=self.sampling_ratio)))
            steps.append(('classifier', self.model))
        
        self.pipeline = Pipeline_imb(steps=steps)

        print ("4. Fitting model")
        self.pipeline.fit(local_X, y)

    def pickle(self, filename):
        print ("5. Pickling model as penny_auction.pickle")
        pickle.dump( self, open( filename, "wb" ) )

    def predict_proba_from_json(self, X_json):
        X = pd.DataFrame.from_dict(X_json)
        return self.predict_proba(X)

    def predict_proba(self, X):
        return self.pipeline.predict_proba(self.transform(X))
    
    def predict_proba_calibrated(self, X):
        return self.calibrate_probabilties(self.predict_proba(X))

    def predict(self, X):
        return self.pipeline.predict(self.transform(X))


    def get_feature_scores(self):
        return pd.Series(self.pipeline.steps[2][1].feature_importances_, index=self.get_column_names_from_ColumnTransformer(self.pipeline.named_steps['preprocessor']))

    def calibrate_probabilties(self, data):

        calibrated_data = \
        ((data * (self.target_pop / self.train_pop) / (self.sampled_target_pop / self.sampled_train_pop)) /
        ((
            (1 - data) * (1 - self.target_pop / self.train_pop) / (1 - self.sampled_target_pop / self.sampled_train_pop)
        ) +
        (
            data * (self.target_pop / self.train_pop) / (self.sampled_target_pop / self.sampled_train_pop)
        )))
        return calibrated_data

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
