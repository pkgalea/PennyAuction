

BEGIN;

create temp table ministeve on commit drop as
with bozo as
(
Select bids.auctionid, 
	cashvalue, cardvalue, auctiontime, bidvalue, cardtype, limited_allowed, bid, username, is_bidomatic, 
       (lock_price != 0 and bid >= lock_price) as is_locked,
	   MAX(bid) OVER (PARTITION BY bids.auctionid) AS eventual_win_price,
           Sum(1) OVER (PARTITION by bids.auctionid, username ORDER BY bid) as bids_so_far,
           count(*) OVER (PARTITION BY bids.auctionid, username) as eventual_bids,
            Sum(1) OVER (PARTITION by bids.auctionid, username, is_bidomatic ORDER BY bid) as bids_of_this_type,
	   row_number() over (partition by username, bids.auctionid order by bid) -
	   row_number() over (partition by username, is_bidomatic, bids.auctionid order by bid) as prestreak, 
	   (CASE WHEN row_number() over (partition by bids.auctionid, username order by bid)=1 THEN 1 ELSE 0 END) as debut,
	   (CASE WHEN cardvalue = 0 THEN 0 WHEN cardvalue < 50 THEN 1 ELSE 1.99 END) as fee
           from bids  INNER JOIN Auctions on Auctions.qauctionid = bids.auctionID         

           WHERE bids.auctionID % 100 = :mod_num and bids.AuctionID not in (SELECT DISTINCT AuctionID from auction_full) 
 )
 select bozo.*, 
 (CASE WHEN is_bidomatic THEN row_number() over (partition by prestreak, auctionid, username order by bid) ELSE 0 END) as bom_streak,
 sum(debut) over (partition by auctionid order by bid)-1 as prevusers,
 bid=eventual_win_price as is_winner,
 bid=eventual_win_price -1 as is_pen,
 bid=eventual_bids and bid != eventual_win_price as giveup,
 (CASE when is_bidomatic THEN bids_of_this_type ELSE bids_so_far-bids_of_this_type END) as bom_bids_so_far,
 (CASE WHEN LAG(bid=eventual_win_price, bids_so_far::int) OVER (PARTITION by username order by auctiontime, bid) THEN 
 LAG(bidvalue, bids_so_far::int) OVER (PARTITION by username order by auctiontime, bid) ELSE 0 END) as prev_win_bids,
 bids_so_far/(cashvalue*2.5) as perc_to_bin

  from bozo order by auctionid, bid;

 
  CREATE INDEX av_username_idx ON ministeve USING btree (username);
  CREATE INDEX av_auctionid_idx ON ministeve USING btree (auctionid);
  CREATE INDEX av_bid_idx ON ministeve USING btree (bid);



CREATE temp table ministeve_pivot on commit drop as
Select n.auctionid, n.bid, max(p.bid) as max_bid, p.username from ministeve n inner join ministeve p 
on n.auctionid = p.auctionid and p.bid < n.bid and n.username <> p.username
group by p.username, n.auctionid, n.bid
order by n.bid;



CREATE temp table ministeve_joined  on commit drop as
Select m.is_winner, m.auctionid, m.cardtype, m.cashvalue, m.cardvalue, m.auctiontime, m.bidvalue, m.limited_allowed, m.bid,
 m.username, m.is_locked, m.is_bidomatic, m.bids_so_far,  m.prevusers,
m.fee,
m.bid - piv.max_bid as distance, 
piv.username as p_username,
p.is_bidomatic as p_is_bidomatic,
p.bids_so_far as p_bids_so_far, 
p.bom_bids_so_far as p_bom_bids_so_far, 
p.bom_streak as p_bom_streak,
p.perc_to_bin as p_perc_to_bin,
p.prev_win_bids as p_prev_win_bids
from ministeve m left join ministeve_pivot piv on m.auctionid = piv.auctionid and m.bid = piv.bid
left join ministeve p on p.auctionid = m.auctionid and p.bid = piv.max_bid;


CREATE temp table ministeve_lagged on commit drop as
select auctionid, is_winner, cardtype, cashvalue, cardvalue, bidvalue, limited_allowed, is_locked, auctiontime, bid, is_bidomatic, bids_so_far, username, prevusers,
lag(p_username,0) over (partition by auctionid, bid order by distance DESC) as username0,
lag(distance,0) over (partition by auctionID, bid order by distance DESC) as distance0,
lag(p_is_bidomatic, 0) over (partition by auctionID, bid order by distance DESC) as is_bidomatic0,
lag(p_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bids_so_far0,
lag(p_bom_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far0,
lag(p_bom_streak, 0) over (partition by auctionID, bid order by distance DESC) as bom_streak0,
lag(p_perc_to_bin, 0) over (partition by auctionID, bid order by distance DESC) as perc_to_bin0,
lag(p_prev_win_bids, 0) over (partition by auctionID, bid order by distance DESC) as prev_win_bids0,


lag(p_username,1) over (partition by auctionid, bid order by distance DESC) as username1,
lag(distance,1) over (partition by auctionID, bid order by distance DESC) as distance1,
lag(p_is_bidomatic, 1) over (partition by auctionID, bid order by distance DESC) as is_bidomatic1,
lag(p_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bids_so_far1,
lag(p_bom_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far1,
lag(p_bom_streak, 1) over (partition by auctionID, bid order by distance DESC) as bom_streak1,
lag(p_perc_to_bin, 1) over (partition by auctionID, bid order by distance DESC) as perc_to_bin1,
lag(p_prev_win_bids, 1) over (partition by auctionID, bid order by distance DESC) as prev_win_bids1,


lag(p_username,2) over (partition by auctionid, bid order by distance DESC) as username2,
lag(distance,2) over (partition by auctionID, bid order by distance DESC) as distance2,
lag(p_is_bidomatic, 2) over (partition by auctionID, bid order by distance DESC) as is_bidomatic2,
lag(p_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bids_so_far2,
lag(p_bom_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far2,
lag(p_bom_streak, 2) over (partition by auctionID, bid order by distance DESC) as bom_streak2,
lag(p_perc_to_bin, 2) over (partition by auctionID, bid order by distance DESC) as perc_to_bin2,
lag(p_prev_win_bids, 2) over (partition by auctionID, bid order by distance DESC) as prev_win_bids2,


lag(p_username,3) over (partition by auctionid, bid order by distance DESC) as username3,
lag(distance,3) over (partition by auctionID, bid order by distance DESC) as distance3,
lag(p_is_bidomatic, 3) over (partition by auctionID, bid order by distance DESC) as is_bidomatic3,
lag(p_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bids_so_far3,
lag(p_bom_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far3,
lag(p_bom_streak, 3) over (partition by auctionID, bid order by distance DESC) as bom_streak3,
lag(p_perc_to_bin, 3) over (partition by auctionID, bid order by distance DESC) as perc_to_bin3,
lag(p_prev_win_bids, 3) over (partition by auctionID, bid order by distance DESC) as prev_win_bids3

FROM ministeve_joined ;

INSERT INTO auction_full
/*create table auction_full as */
Select * from ministeve_lagged where distance0 is null or distance0 = 1;


COMMIT;





