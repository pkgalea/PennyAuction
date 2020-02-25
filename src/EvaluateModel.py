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


def print_profit_threshold (y_test, probs, X_test):
    for thresh in np.arange(0, 1.1, .05): # threshes:
        y_pred = probs >= thresh
        cm = confusion_matrix(y_test, y_pred)
        print("*****************************")
        print("thresh:", thresh)
        acc = accuracy_score(y_test, y_pred) * 100
        prec = precision_score(y_test, y_pred) *100
        rec = recall_score(y_test, y_pred) *100
        print (f"Accuracy: {acc:.2f} Precision: {prec:.2f}  Recall:{rec:.2f} ")
        print(cm)
        true_positive_mask = (y_pred==True)&(y_test==True)
        profit = sum(X_test.cashvalue[true_positive_mask])-sum(y_pred)*.40 - sum(X_test.fee[true_positive_mask]) - sum(X_test.bid[true_positive_mask])/100
        profit_per_bid = profit/sum(y_pred)
        print(f"profit: {profit:.2f}")
        print(f"profit per bid: {profit_per_bid:.2f}")
        print("*****************************")
        print("")


print ("Connecting to SQL")
conn = pg2.connect(user='postgres',  dbname='penny', host='localhost', port='5432', password='')

print ("Reading Dataset")
df = pd.read_sql ("""Select * from auction_full where auctiontime > '2020-01-17' order by auctiontime""", conn)

print ("Splitting into Train/Test Sets")
df = df.sort_values("auctiontime")
y = df['is_winner']
X = df
X_train = X[X.auctiontime <= '2020-02-17']
y_train = y[X.auctiontime <= '2020-02-17']
X_test = X[X.auctiontime > '2020-02-17']
y_test = y[X.auctiontime > '2020-02-17']
#X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False)#, random_state=0) 
print(X_test.auctiontime.iloc[0])



print ("Fitting Model")
pm = PennyModel()
pm.fit(X_train, y_train)

print ("Plotting features")
# Plot the feature importance
feat_scores = pm.get_feature_scores()
feat_scores = feat_scores.sort_values()
fig, ax = plt.subplots()
ax = feat_scores.plot(kind='barh', 
                      figsize=(10,8),
                      color='b')
ax.set_title('Average Gini Importance')
ax.set_xlabel('Average contribution to information gain')

print ("Calculating predictions")
probs = pm.predict_proba(X_test)[:,1]
threshes = np.unique(probs)
threshes = threshes[threshes > .4]


print_profit_threshold(y_test, probs, X_test)

