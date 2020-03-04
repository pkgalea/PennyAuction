Penny Auction Bet Optimizer  

### High Level Description:

QuiBids (http://www.quibids.com/) is website where items are sold for ridiculously cheap amounts, but there is a catch.  Users pay a set amount for packs "bids" ($.40 per bid).  Items start at 1 penny.  For every bid, the price of the auction goes up by 1 cent and 10 seconds are added to the clock. If the clock runs out, the winner (the final bidder) is allowed to purchase the item for the (usually) cheap price.  The site makes money by selling the bid packs

This machine learning project is two fold:

  1) Train a model to predict when an auction is going to end based upon auction data, current player actions, and past player history.
  2) Live Auction Tracking that feeds auction information to the model in real-time.  The model will return the expected value.
  
### Data:
ata was scraped from a website that tracks historical penny auction information with the owner's permission.

### Approach:

The output of the machine learning model is simple:  0: Do not bid on this auction,  1: Bid on this auction.  It is therefore a supervised, binary classification model.  Data was scraped from a website that tracks historical penny auction information with the owner's permission.



The features can 

The plan is keep it simple and attempt to make a model that will predict based upon how many bids each user has done and how many bidders there are and some basic user history.


### How Users will interact with the project:

The eventual plan is to build a live, threaded application that can monitor auctions as they occur and return an expected profit for if the user places a bid at the given moment. 

### Data Sources:

http://www.bidtracker.info/ is a site that stores historical auctions for penny auction sites.  They have nearly complete bid history for auctions and info on users.  This information can be scraped, but slowly as per the owner's request.  The live data comes from Quibids http://www.quibids.com/

### The data set

Bids: 5,615,461
Users: 8,791
Winners: 19,351

Less than 1 in 290 bids is a winner!
Very Unbalanced Data Set:  0.34% positives

### The model

To deal with the unbalanced data set, I I chose the random forest model becuase of it's resistance
