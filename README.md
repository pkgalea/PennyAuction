# Penny Auction Bet Optimizer  
<br><br>
### Abstract

QuiBids (http://www.quibids.com/) is website where items are sold for ridiculously cheap amounts, but there is a catch.  Users pay a set amount for packs "bids" ($.40 per bid).  Items start at 1 penny.  For every bid, the price of the auction goes up by 1 cent and 10 seconds are added to the clock. If the clock runs out, the winner (the final bidder) is allowed to purchase the item for a (usually) ridiculously cheap price.  The site makes money by selling the bid packs

This goal of this machine learning project is two fold:

  1) Train a model to predict when an auction is going to end based upon auction data, current player actions, and past player history.
  2) Live Auction Tracking that feeds auction information to the model in real-time.  The model will return the expected value.
  
### Results

  1) The model to predict when an auction will end performed very well on unseen data. 
  2) The Live Auction Tracking seems to function well but needs testing.
  
### Approach

![image](https://github.com/pkgalea/PennyAuction/blob/master/images/auctionlevel.png)
  
### Data

Data to build the model was scraped from a website that tracks historical penny auction information with the owner's permission.  The raw html was stored into a Mongo Database.  A parser pulled the relevant information and stored the info into a PSQL Database.  

Each individual datapoint is a single bid in the auction. 

Bids: 8,374,298
Distinct Users: 9,327
Winners: 34,659

### Approach:

The output of the machine learning model is simple:  0: Do not bid on this auction,  1: Bid on this auction.  It is therefore a supervised, binary classification model. 


The features used can be divided into 3 categories:

1) Auction Level Features.
       Value of the Item Being Sold
       Type of the Item Being Sold
       Time Of Day
       Current Bid Price
       Number of users in the auction
       
2) In-Auction User Features:
       These are features that relate to one player in the auction that is NOT the current winner.  Examples include:
       Bids So Far in this Auction
       Are they using an autobidder
       How far away was this user's last bid from the current winning price
 
3) User's past history:
       These are features of each user in the auction from PREVIOUS auctions.  They include:
       Average number of bids per auction
       Percentage of time the user gives up after 1 bid
       Percentage of time the user overbids on an item.
       Percentage of time the user uses a Bid-O-Matic
      


### Live Auction Tracker

The eventual plan is to build a live, threaded application that can monitor auctions as they occur and return an expected profit for if the user places a bid at the given moment. 


### The model

To deal with the unbalanced data set, I I chose the random forest model becuase of it's resistance

### Future Work

Because the initial Random Forest model performed so well, I decided to focus on the real-time appication instead.  There is probably a lot of lift to attain by trying some more complicated models.  


