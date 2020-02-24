delete from bids where auctionid in (select qauctionid from auctions where cardvalue = 50 and bidvalue=0);
delete from auctions where auctionid in (select auctionid from auctions where cardvalue = 50 and bidvalue=0);


BEGIN;


create temp table bid_transform on commit drop as
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

           WHERE  auctiontime < '2019-12-20' /*   bids.AuctionID not in (SELECT DISTINCT AuctionID from bid_transform)   */
 )
 select bozo.*, 
 (CASE WHEN is_bidomatic THEN row_number() over (partition by prestreak, auctionid, username order by bid) ELSE 0 END) as bom_streak,
 sum(debut) over (partition by auctionid order by bid)-1 as prevusers,
 bid=eventual_win_price as is_winner,
 bid=eventual_win_price -1 as is_pen,
 bids_so_far=eventual_bids and bid != eventual_win_price as giveup,
 (CASE when is_bidomatic THEN bids_of_this_type ELSE bids_so_far-bids_of_this_type END) as bom_bids_so_far,
 (CASE WHEN LAG(bid=eventual_win_price, bids_so_far::int) OVER (PARTITION by username order by auctiontime, bid) THEN 
 LAG(bidvalue, bids_so_far::int) OVER (PARTITION by username order by auctiontime, bid) ELSE 0 END) as prev_win_bids,
 bids_so_far/(cashvalue*2.5) as perc_to_bin
from bozo order by auctionid, bid;

 
CREATE INDEX av_username_idx ON bid_transform USING btree (username);
CREATE INDEX av_auctionid_idx ON bid_transform USING btree (auctionid);
CREATE INDEX av_bid_idx ON bid_transform USING btree (bid);



create temp table prev_auction_data on commit drop as
with bozo as 
(
Select  count(*) as bids, sum(is_bidomatic::int) as bidomatic_bids, min(bid) as entry, auctiontime, auctionid, username, sum(is_winner::int) as wins, 
max(CASE WHEN giveup and bids_so_far = 1 THEN 1 ELSE 0 END) as giveup_at_one,
max(CASE WHEN giveup and bids_so_far <=5 THEN 1 ELSE 0 END) as giveup_before_six,
max(CASE WHEN perc_to_bin >=1 THEN 1 ELSE 0 END) as overbid
from bid_transform  group by auctionid, username, auctiontime order by auctiontime
)
select auctiontime, username, auctionid, 
sum(overbid) over (partition by username order by auctiontime) - overbid as prev_overbid_count,
sum(giveup_at_one) over (partition by username order by auctiontime) - giveup_at_one as prev_giveup_one_count ,
sum(giveup_before_six) over (partition by username order by auctiontime) - giveup_before_six as prev_giveup_before_six_count ,
sum(wins) over (partition by username order by auctiontime) - wins as prev_wins_count, 
sum(bidomatic_bids) over (partition by username order by auctiontime) - bidomatic_bids as prev_bom_bid_count,
sum(bids) over (partition by username order by auctiontime) - bids as prev_bid_count, 
(CASE WHEN row_number() over (partition by username order by auctiontime) - 1 = 0 THEN 1 ELSE row_number() over (partition by username order by auctiontime) - 1 END) as prev_auction_count
from bozo order by auctiontime;

CREATE INDEX pad_username_idx ON prev_auction_data USING btree (username);
CREATE INDEX pad_auctionid_idx ON prev_auction_data USING btree (auctionid);


create temp table auction_unified on commit drop as
Select a.*, p.prev_auction_count, 
prev_overbid_count/prev_auction_count as prev_overbid ,
prev_giveup_one_count/prev_auction_count as prev_giveup_one,
prev_giveup_before_six_count/prev_auction_count as prev_giveup_before_six,
prev_wins_count/prev_auction_count as prev_wins,
prev_bid_count/prev_auction_count as prev_bids,
prev_bom_bid_count/prev_auction_count as prev_bom_bids
from bid_transform a inner join prev_auction_data p on a.auctionid = p.auctionid and a.username = p.username;

CREATE INDEX au_username_idx ON auction_unified USING btree (username);
CREATE INDEX au_auctionid_idx ON auction_unified USING btree (auctionid);
CREATE INDEX au_bid_idx ON auction_unified USING btree (bid);


CREATE temp table ab_pivot on commit drop as
Select n.auctionid, n.bid, max(p.bid) as max_bid, p.username from auction_unified n inner join auction_unified p 
on n.auctionid = p.auctionid and p.bid < n.bid and n.username <> p.username
group by p.username, n.auctionid, n.bid;


CREATE temp table full_joined on commit drop as
Select m.is_winner, m.auctionid, m.cardtype, m.cashvalue, m.cardvalue, m.auctiontime, m.bidvalue, m.limited_allowed, m.bid,
 m.username, m.is_locked, m.is_bidomatic, m.bids_so_far,  m.prevusers,
m.fee, m.giveup, m.eventual_bids, m.eventual_win_price, m.debut, m.bom_streak, m.bom_bids_so_far, m.perc_to_bin,
m.bid - piv.max_bid as distance, 
piv.username as p_username,
p.is_bidomatic as p_is_bidomatic,
p.bids_so_far as p_bids_so_far, 
p.bom_bids_so_far as p_bom_bids_so_far, 
p.bom_streak as p_bom_streak,
p.perc_to_bin as p_perc_to_bin,
p.prev_overbid as p_prev_overbid,
p.prev_giveup_one as p_prev_giveup_one,
p.prev_giveup_before_six as p_prev_giveup_before_six,
p.prev_wins as p_prev_wins,
p.prev_bids as p_prev_bids,
p.prev_bom_bids p_prev_bom_bids

from auction_unified m left join ab_pivot piv on m.auctionid = piv.auctionid and m.bid = piv.bid
left join auction_unified p on p.auctionid = m.auctionid and p.bid = piv.max_bid;



CREATE  temp table auction_lagged on commit drop as
select auctionid, is_winner, cardtype, cashvalue, cardvalue, fee, bidvalue, limited_allowed, is_locked, auctiontime, bid, is_bidomatic, bids_so_far,
 username, prevusers,
 giveup, eventual_bids, eventual_win_price, debut, bom_streak, bom_bids_so_far, perc_to_bin,
 
lag(p_username,0) over (partition by auctionid, bid order by distance DESC) as username0,
lag(distance,0) over (partition by auctionID, bid order by distance DESC) as distance0,
lag(p_is_bidomatic, 0) over (partition by auctionID, bid order by distance DESC) as is_bidomatic0,
lag(p_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bids_so_far0,
lag(p_bom_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far0,
lag(p_bom_streak, 0) over (partition by auctionID, bid order by distance DESC) as bom_streak0,
lag(p_perc_to_bin, 0) over (partition by auctionID, bid order by distance DESC) as perc_to_bin0,
lag(p_prev_overbid, 0) over (partition by auctionID, bid order by distance DESC) as prev_overbid0,
lag(p_prev_giveup_one, 0) over (partition by auctionID, bid order by distance DESC) as prev_giveup_one0,
lag(p_prev_giveup_before_six, 0) over (partition by auctionID, bid order by distance DESC) as prev_give_before_six0,
lag(p_prev_wins, 0) over (partition by auctionID, bid order by distance DESC) as prev_wins0,
lag(p_prev_bids, 0) over (partition by auctionID, bid order by distance DESC) as prev_bids0,
lag(p_prev_bom_bids, 0) over (partition by auctionID, bid order by distance DESC) as prev_bom_bids0,

lag(p_username,1) over (partition by auctionid, bid order by distance DESC) as username1,
lag(distance,1) over (partition by auctionID, bid order by distance DESC) as distance1,
lag(p_is_bidomatic, 1) over (partition by auctionID, bid order by distance DESC) as is_bidomatic1,
lag(p_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bids_so_far1,
lag(p_bom_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far1,
lag(p_bom_streak, 1) over (partition by auctionID, bid order by distance DESC) as bom_streak1,
lag(p_perc_to_bin, 1) over (partition by auctionID, bid order by distance DESC) as perc_to_bin1,
lag(p_prev_overbid, 1) over (partition by auctionID, bid order by distance DESC) as prev_overbid1,
lag(p_prev_giveup_one, 1) over (partition by auctionID, bid order by distance DESC) as prev_giveup_one1,
lag(p_prev_giveup_before_six, 1) over (partition by auctionID, bid order by distance DESC) as prev_give_before_six1,
lag(p_prev_wins, 1) over (partition by auctionID, bid order by distance DESC) as prev_wins1,
lag(p_prev_bids, 1) over (partition by auctionID, bid order by distance DESC) as prev_bids1,
lag(p_prev_bom_bids, 1) over (partition by auctionID, bid order by distance DESC) as prev_bom_bids1,


lag(p_username,2) over (partition by auctionid, bid order by distance DESC) as username2,
lag(distance,2) over (partition by auctionID, bid order by distance DESC) as distance2,
lag(p_is_bidomatic, 2) over (partition by auctionID, bid order by distance DESC) as is_bidomatic2,
lag(p_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bids_so_far2,
lag(p_bom_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far2,
lag(p_bom_streak, 2) over (partition by auctionID, bid order by distance DESC) as bom_streak2,
lag(p_perc_to_bin, 2) over (partition by auctionID, bid order by distance DESC) as perc_to_bin2,
lag(p_prev_overbid, 2) over (partition by auctionID, bid order by distance DESC) as prev_overbid2,
lag(p_prev_giveup_one, 2) over (partition by auctionID, bid order by distance DESC) as prev_giveup_one2,
lag(p_prev_giveup_before_six, 2) over (partition by auctionID, bid order by distance DESC) as prev_give_before_six2,
lag(p_prev_wins, 2) over (partition by auctionID, bid order by distance DESC) as prev_wins2,
lag(p_prev_bids, 2) over (partition by auctionID, bid order by distance DESC) as prev_bids2,
lag(p_prev_bom_bids, 2) over (partition by auctionID, bid order by distance DESC) as prev_bom_bids2,


lag(p_username,3) over (partition by auctionid, bid order by distance DESC) as username3,
lag(distance,3) over (partition by auctionID, bid order by distance DESC) as distance3,
lag(p_is_bidomatic, 3) over (partition by auctionID, bid order by distance DESC) as is_bidomatic3,
lag(p_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bids_so_far3,
lag(p_bom_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far3,
lag(p_bom_streak, 3) over (partition by auctionID, bid order by distance DESC) as bom_streak3,
lag(p_perc_to_bin, 3) over (partition by auctionID, bid order by distance DESC) as perc_to_bin3,
lag(p_prev_overbid, 3) over (partition by auctionID, bid order by distance DESC) as prev_overbid3,
lag(p_prev_giveup_one, 3) over (partition by auctionID, bid order by distance DESC) as prev_giveup_one3,
lag(p_prev_giveup_before_six, 3) over (partition by auctionID, bid order by distance DESC) as prev_give_before_six3,
lag(p_prev_wins, 3) over (partition by auctionID, bid order by distance DESC) as prev_wins3,
lag(p_prev_bids, 3) over (partition by auctionID, bid order by distance DESC) as prev_bids3,
lag(p_prev_bom_bids, 3) over (partition by auctionID, bid order by distance DESC) as prev_bom_bids3

FROM full_joined ;


create table auction_lagged as 
Select * from ministeve_lagged where distance0 is null or distance0 = 1;


END;