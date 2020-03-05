# Penny Auction Bet Optimizer  


## Abstract

QuiBids (http://www.quibids.com/) is website where items are sold for ridiculously cheap amounts, but there is a catch.  Users pay a set amount for packs "bids" ($.40 per bid).  Items start at 1 penny.  For every bid, the price of the auction goes up by 1 cent and 10 seconds are added to the clock. If the clock runs out, the winner (the final bidder) is allowed to purchase the item for a (usually) ridiculously cheap price.  The site makes money by selling the bid packs

This goal of this machine learning project is two fold:

  -Train a model to predict when an auction is going to end based upon auction data, current player actions, and past player history.
  -Live Auction Tracking that feeds auction information to the model in real-time.  The model will return the expected value.
  
## Results

  -The model to predict when an auction will end performed very well on unseen data. 
  -The Live Auction Tracking seems to function well but needs more testing before deployment.
  
---  
  
## Model

The general idea is to build a model that returns a probability that the auction will end at any given point.  This will later be used to evaluate the expected value of I were to be the NEXT bidder.

### Output

The output of the machine learning model is simple:  0: Do not bid on this auction,  1: Bid on this auction.  It is therefore a supervised, binary classification model. 

#### Features

The features used can be divided into 3 categories:

1) Auction Level Features.
       Value of the Item Being Sold
       Type of the Item Being Sold
       Time Of Day
       Current Bid Price
       Number of users in the auction
       
![image](https://github.com/pkgalea/PennyAuction/blob/master/images/auctionlevel.png)
Auction Level Features
       
2) In-Auction User Features:
       These are features that relate to one player in the auction that is NOT the current winner.  Examples include:
       Bids So Far in this Auction
       Are they using an autobidder
       How far away was this user's last bid from the current winning price

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/user-inauction.png)
In-Auction User Features

3) User's past history:
       These are features of each user in the auction from PREVIOUS auctions.  They include:
       Average number of bids per auction
       Percentage of time the user gives up after 1 bid
       Percentage of time the user overbids on an item.
       Percentage of time the user uses a Bid-O-Matic

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/past.png)
Past User History Features

## Dealing with unbalance

The data is very unbalanced with only .41% positive values.  To account for this I used the ```imbalanced-learn``` library and random undersampling.

I tried serveral ANN's with Keras, but the best model ending up being a Random Forest Classifier with undersampling of 2 to 1 Majority to Minority class and 200 evaluators.

The Roc curve indicates that the model performed quite well, with an area under the curve of .82

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/roc.png)

## Data

Data to build the model was scraped from a website that tracks historical penny auction information with the owner's permission.  The raw html was stored into a Mongo Database.  A parser pulled the relevant information and stored the info into a PSQL Database.  

Each individual datapoint is a single bid in the auction. 

Bids: 8,374,298
Distinct Users: 9,327
Winners: 34,659

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


