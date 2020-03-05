# Penny Auction Bet Optimizer  


## Abstract

QuiBids (http://www.quibids.com/) is website where items are sold for ridiculously cheap amounts, but there is a catch.  Users pay a set amount for packs "bids" ($.40 per bid).  Items start at 1 penny.  For every bid, the price of the auction goes up by 1 cent and 10 seconds are added to the clock. If the clock runs out, the winner (the final bidder) is allowed to purchase the item for a (usually) ridiculously cheap price.  The site makes money by selling the bid packs

This goal of this machine learning project is two fold:

  - Train a model to predict when an auction is going to end based upon auction data, current player actions, and past player history.
  - Live Auction Tracking that feeds auction information to the model in real-time.  The model will return the expected value.
  
## Results

  - The model to predict when an auction will end performed very well on unseen data. 
  - The Live Auction Tracking seems to function well but needs more testing before deployment.
  
---  

## Data

Data to build the model was scraped from a website that tracks historical penny auction information with the owner's permission.  The raw html was stored into a Mongo Database.  A parser pulled the relevant information and stored the info into a PSQL Database.  

Each individual datapoint is a single bid in the auction. 

Bids: 8,374,298
Distinct Users: 9,327
Winners: 34,659  
    
  
  
## Model

The general idea is to build a model that returns a probability that the auction will end at any given point.  This will later be used to evaluate the expected value of I were to be the NEXT bidder.

#### Output

The output of the machine learning model is simple:  0: Do not bid on this auction,  1: Bid on this auction.  It is therefore a supervised, binary classification model. 

#### Features

The features used can be divided into 3 categories:

  - __Auction Level Features__
       - Value of the Item Being Sold
       - Type of the Item Being Sold
       - Time Of Day
       - Current Bid Price
       - Number of users in the auction
       
![image](https://github.com/pkgalea/PennyAuction/blob/master/images/auctionlevel.png)
Auction Level Features
   <br><br><br>
   
   
   
  - __In-Auction User Features__ (features for individual users in the auction)  
    - Bids So Far in this Auction
    - Are they using an autobidder
    - How far away was this user's last bid from the current winning price

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/user-inauction.png)
In-Auction User Features
<br><br><br>


  - __User's past history__ (features for how a user has behaved in the past)
       - These are features of each user in the auction from PREVIOUS auctions.  They include:
       - Average number of bids per auction
       - Percentage of time the user gives up after 1 bid
       - Percentage of time the user overbids on an item.
       - Percentage of time the user uses a Bid-O-Matic

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/past.png)
Past User History Features
<br><br>


#### Dealing with unbalance

The data is very unbalanced with only .41% positive values.  To account for this I used the ```imbalanced-learn``` library and random undersampling.

I tried serveral ANN's with Keras, but the best model ending up being a Random Forest Classifier with undersampling of 2 to 1 Majority to Minority class and 200 evaluators.

#### Model Performance

The Roc curve indicates that the model performed quite well, with an area under the curve of .82

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/roc.png)


## Translating model probabilties to expected values

We now have an accurate model for predicting the probability that an auction will end. But what does it mean that the model says there is a 70% chance of the auction ending.  Can we use that information.

The first thing to remember is that that is coming from an undersampled data set. So the probability of winning is MUCH lower than that.  The key is to first adjust for the undersampling.

true_ratio = (#wins in full train set)/(# of bids in full train set)

sampled_ratio = (#wins in full train set)/(# of bids in full train set)

win_probs = prob x true_ratio/sampled_ratio prob 

lose_probs = (1 - prob) * (1-true_ratio)/(1-sampled_ratio)

adjusted probability = win_probs/(win_probs + lose_probs)

This will give more accurate probabilities to the actual probability of getting a win.

## Expected Value

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/ev.png)

To calculate the expected value we use the adjusted probability from the model and look at the profit we would win if we were to win now and subtract $.40 for the bid.

Now the question of when to bid is easy.  It's simply a question of is the expected value positive or not.

## Profit as a metric

Now we can use these expected values to calcuate our profit on unseen data.  By going through the Test set and adding up the profits or losses when the expected value is greater than 0, we get an idea of how our model will do.

The good news is that the expected and actual values in the test set correlate incredibly well with the training set.

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/ev_vs_actual.png)

So, how often do we bet. The answer is very rarely:

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/evdensity.png)

Here's the confusion matrix for a typical day.  We see that the model says to ignore nearly 60,000 bidding opportunities.  However out of the approximately 6,800 opportunities where the model says to bid, you win 168 auctions.  And that's enough for some big profits.

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/cm.png)

Here are the profits, per day, in the test set, if you were to only bid when the expected value is > 0.

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/profits.png)



## Workflow:

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/workflow.png)


### Model Building
The Model Building was done on an Amazon Ec2.  The downloaded data lives on an EC2 instance and the downloading, parsing, transforming and model building can be run with a single script.

```BuildTrackerScaper.py```

This file contains the class that downloads the raw HTML pages from BidTracker.info.

```ParseMongo.py```

This file contains the class the parses the raw HTML pages and extracts the relevant features and stores them in a MongoDB.

```MongoToPSQL.py```

This file migrates to the data from MongoDB to PSQL, storing the data in the data in two tables (bids, auctions).

```TransformSQL.py ```

This file transforms calls the new_transformations.sql file to transform the bids and auctions tables to the full_auction table which is in the form a machine learning model can understand.

```BuildModel.py```
This is the file which contains the Penny Auction class.  It is styled after the sklearn paradigm of init, transform, fit.  It takes an sklearn classifier so that different classifiers can be evaluated.

```EvaluateModel.py```
This class evaluates the diffrent models, using netprofit as a metric.

```BuildFinalModel.py```

This file trains builds the model on the whole data set up to the last data scraped to be deployed.




## Live Auction Tracker

The live auction tracker uses a selenium to open up upcoming auctions in chrome a few seconds before they are scheduled to begin.  It then returns 2 different expected values:

  -Expected Value if user places an auto-bid
  -Expected Value if user places a single bid

The Live auction Tracker consists of the following files:

```QuiBidsSniffer.py```  

Uses pyshark to sniff web traffic from QuiBids.  This prevents having to send many requests to quibids and instead just "watch" as the auction goes by.

```Upcoming.py``` Scrapes BidTracker to see which auctions are coming up and writes them to a mongo db.  Also opens up the auction in Chrome using selenium when the auction time is near.

```LiveAuctionProcessor.py```  Processes the live auction file stored by the sniffer and returns an expected value

```application.py```  The Flask app that shows the live auctions


### Future Work

Because the initial Random Forest model performed so well, I decided to focus on the real-time appication instead.  There is probably a lot of lift to attain by trying some more complicated models.  
