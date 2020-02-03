

Select bids.auctionid, cardvalue, auctiontime, bidvalue, cardtype, limited_allowed, bid, username, is_bidomatic, 
	   bid=MAX(bid) OVER (PARTITION BY bids.auctionid) AS is_winner,
	   bid=MAX(bid) OVER (PARTITION BY bids.auctionid)-1 AS is_pen,
	   MAX(bid) OVER (PARTITION BY bids.auctionid) AS eventual_win_price,
           Sum(1) OVER (PARTITION by bids.auctionid, username ORDER BY bid) as bids_so_far,
           count(*) OVER (PARTITION BY bids.auctionid, username) as eventual_bids, 
           bid=max(bid) OVER (PARTITION by bids.auctionid, username) and not bid=MAX(bid) OVER (PARTITION BY bids.auctionid) as giveup,
           (CASE WHEN is_bidomatic THEN Sum(1) OVER (PARTITION by bids.auctionid, username, is_bidomatic ORDER BY bid)
		ELSE  Sum(1) OVER (PARTITION by bids.auctionid, username ORDER BY bid) - sum(1) OVER (PARTITION by bids.auctionid, username, is_bidomatic ORDER BY bid) END)
		as bidomatic_bids_so_far
           from bids  INNER JOIN Auctions on Auctions.qauctionid = bids.auctionID WHERE bids.auctionid = 783108868 
           order by auctionId, bid;
        
