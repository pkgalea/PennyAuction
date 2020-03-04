import pandas as pd
import psycopg2 as pg2
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
    """ 
    The Model for the penny auction.   Takes a sklearn classifier and fits the model after transformation.

    Attributes: 
        model (SklearnClassifier): The model for the regression
        user_scaler (bool): Whether or not to scale the data first
        sampling_ratio (float):  The ratio of the minority class to the majority class
        numeric_features (list(str)):  The numerical features of the model
        cateogorical_features (list(str)): The categorical features of the model
    """
    def __init__ (self, model,  use_scaler=False, sampling_ratio = 1):
        """

        Parameters:
        Returns:
        """
        self.model = model
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
        """
        Returns all the features of the model.

        Parameters:
        Returns:
        """
        return ",".join(self.categorical_features + self.numeric_features)

    def get_column_names_from_ColumnTransformer(self, column_transformer):    
        """

        Parameters:
        Returns:
        """
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
        """

        Parameters:
        Returns:
        """

        rX = X.copy()
        return transform_no_copy(rX)
    
    def transform_no_copy(self, X):
        """

        Parameters:
        Returns:
        """

        #rX = X.copy()
        #print ("2. Transforming data")
        X.is_bidomatic0 = X.is_bidomatic0.astype(str)
        X.is_bidomatic1 = X.is_bidomatic1.astype(str)
        X.is_bidomatic2 = X.is_bidomatic2.astype(str)
        X.is_bidomatic3 = X.is_bidomatic3.astype(str)

        X["fee"]=[0 if x == 0 else (1 if x < 50 else 1.99) for x in X["cardvalue"]]
        X["time_of_day"]=[x.hour*60+x.minute for x in X["auctiontime"]]
        X["is_weekend"] = [x.weekday() >=6 for x in X["auctiontime"]]


    def internal_fit (self, X, y):
        """
        Fits self.model 

        Parameters:
        Returns:
        """
        self.train_pop = X.shape[0]
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
        steps.append(('sampler', RandomUnderSampler(sampling_strategy=self.sampling_ratio)))
        steps.append(('classifier', self.model))
        
        self.pipeline = Pipeline_imb(steps=steps)

        print ("4. Fitting model")
        self.pipeline.fit(X, y)


    def fit_already_transformed (self, X, y):
        """
        fits X if it's already been transformed.

        Parameters:
        Returns:
        """
        self.internal_fit(X, y)

    def fit_transform(self, X, y):
        """
        fits and transforms X.

        Parameters:
        Returns:
        """
        self.transform_no_copy(X)
        self.internal_fit(X, y)

    def pickle(self, filename):
        """
        Writes this class as a pickle file to filename

        Parameters:
        Returns:
        """
        print ("5. Pickling model as penny_auction.pickle")
        pickle.dump( self, open( filename, "wb" ) )

 
    def predict_proba(self, X):
        """
        Returns the predicted probabilities that the auction will end, in the UNDERSAMPLED data set.

        Parameters:
        Returns:
        """
       return self.pipeline.predict_proba(self.transform(X))
    
    def predict_proba_calibrated(self, X):
        """
        Returns the probabilities from the model AFTER accounting for the undersampling.

        Parameters:
        Returns:
        """
        return self.calibrate_probabilties(self.predict_proba(X))

    def predict(self, X):
        """
        Calls predict on the model to get binary whether or not the auction will end.

        Parameters:
        Returns:
        """
        return self.pipeline.predict(self.transform(X))


    def get_feature_scores(self):
        """
        Returns the feature importances from the model

        Parameters:
        Returns:
        """
        return pd.Series(self.pipeline.steps[2][1].feature_importances_, index=self.get_column_names_from_ColumnTransformer(self.pipeline.named_steps['preprocessor']))

    def calibrate_probabilties(self, data):
        """
        Recalibrates the probabilities to account for the undersampling.  So if the model says 20%, it will comeout as something like 1.2%

        Parameters:
        Returns:
        """

        calibrated_data = \
        ((data * (self.target_pop / self.train_pop) / (self.sampled_target_pop / self.sampled_train_pop)) /
        ((
            (1 - data) * (1 - self.target_pop / self.train_pop) / (1 - self.sampled_target_pop / self.sampled_train_pop)
        ) +
        (
            data * (self.target_pop / self.train_pop) / (self.sampled_target_pop / self.sampled_train_pop)
        )))
        return calibrated_data

    def get_actual_and_potential_profits(self, X, y):
        """
        returns the actual and potential profits over X

        Parameters:
        Returns:
        """
        potential_profits =  (X.cashvalue - X.fee - X.bid/100) -.4
        actual_profits = y * (X.cashvalue - X.fee - X.bid/100) -.4
        return potential_profits, actual_profits

    def get_score(self, X, y):
        """
        Returns the expected profit over the set X

        Parameters:
        Returns:
        """
        cprobs = self.predict_proba_calibrated(X)[:,1]
        pp, ap = self.get_actual_and_potential_profits(X,y)
        expected_value = np.multiply(cprobs, pp) -  (1-cprobs)*.4
        return sum(ap[expected_value > 0])
   #     (sum(ap[expected_value>0]), X_test.shape[0], sum(expected_value>0), sum((ap > 0) & (expected_value >0)), 
   #     sum((ap > 0) & (expected_value < 0)), sum((ap < 0)&(expected_value > 0)), sum((ap < 0)&(expected_value < 0))))


