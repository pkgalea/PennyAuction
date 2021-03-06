
CREATE TABLE bids
(
  bidid serial NOT NULL,
  auctionid integer NOT NULL,
  bid integer NOT NULL,
  username character varying(20) NOT NULL,
  is_bidomatic boolean NOT NULL,
  CONSTRAINT qauctionid_bid_unique UNIQUE (auctionid, bid)
);

CREATE TABLE auctions
(
  auctionid serial NOT NULL , 
  qauctionid integer NOT NULL ,
  cardvalue integer NOT NULL ,
  bidvalue integer NOT NULL ,
  tracking double precision NOT NULL ,
  auctiontime timestamp without time zone NOT NULL ,
  limited_allowed boolean NOT NULL ,
  cashvalue integer NOT NULL ,
  cardtype character varying(20) NOT NULL ,
  runtime integer NOT NULL ,
  lock_price integer NOT NULL ,
  CONSTRAINT qauctionid_unique UNIQUE (qauctionid)
);


CREATE INDEX auctionid_idx ON public.bids USING btree (auctionid);
CREATE INDEX bid_idx ON public.bids USING btree (bid);
CREATE INDEX bidomatic_idx ON public.bids USING btree (is_bidomatic);
CREATE INDEX username_idx ON public.bids USING btree (username);


delete from bids where auctionid in (select distinct auctionid from bids where auctionid not in (SELECT qauctionid from auctions));
delete from bids where auctionid in (select distinct qauctionid from auctions where auctiontime <= '2019-09-19');
delete from auctions where qauctionid in (select distinct qauctionid from auctions where auctiontime <= '2019-09-19');



drop table steve;
create table auction_view as
with bozo as
(
Select bids.auctionid, cashvalue, cardvalue, auctiontime, bidvalue, cardtype, limited_allowed, bid, username, is_bidomatic, 
       (lock_price != 0 and bid >= lock_price) as is_locked,
	   MAX(bid) OVER (PARTITION BY bids.auctionid) AS eventual_win_price,
           Sum(1) OVER (PARTITION by bids.auctionid, username ORDER BY bid) as bids_so_far,
           count(*) OVER (PARTITION BY bids.auctionid, username) as eventual_bids,
            Sum(1) OVER (PARTITION by bids.auctionid, username, is_bidomatic ORDER BY bid) as bids_of_this_type,
	   row_number() over (partition by username, bids.auctionid order by bid) -
	   row_number() over (partition by username, is_bidomatic, bids.auctionid order by bid) as prestreak, 
	   (CASE WHEN row_number() over (partition by bids.auctionid, username order by bid)=1 THEN 1 ELSE 0 END) as debut
           from bids  INNER JOIN Auctions on Auctions.qauctionid = bids.auctionID 
          /* WHERE bids.auctionID = 100653479*/
 )
 select bozo.*, 
 row_number() over (partition by prestreak, auctionid, username order by bid) as streak,
 sum(debut) over (partition by auctionid order by bid)-1 as prevusers,
 bid=eventual_win_price as is_winner,
 bid=eventual_win_price -1 as is_pen,
 bid=eventual_bids and bid != eventual_win_price as giveup,
 (CASE when is_bidomatic THEN bids_of_this_type ELSE bids_so_far-bids_of_this_type END) as bom_bids_so_far
  from bozo order by auctionid, bid;

  CREATE INDEX av_username_idx ON auction_view USING btree (username);
  CREATE INDEX av_auctionid_idx ON auction_view USING btree (auctionid);
  CREATE INDEX av_bid_idx ON auction_view USING btree (bid);






drop table ministeve;
create table ministeve as
with bozo as
(
Select bids.auctionid, cashvalue, cardvalue, auctiontime, bidvalue, cardtype, limited_allowed, bid, username, is_bidomatic, 
       (lock_price != 0 and bid >= lock_price) as is_locked,
	   MAX(bid) OVER (PARTITION BY bids.auctionid) AS eventual_win_price,
           Sum(1) OVER (PARTITION by bids.auctionid, username ORDER BY bid) as bids_so_far,
           count(*) OVER (PARTITION BY bids.auctionid, username) as eventual_bids,
            Sum(1) OVER (PARTITION by bids.auctionid, username, is_bidomatic ORDER BY bid) as bids_of_this_type,
	   row_number() over (partition by username, bids.auctionid order by bid) -
	   row_number() over (partition by username, is_bidomatic, bids.auctionid order by bid) as prestreak, 
	   (CASE WHEN row_number() over (partition by bids.auctionid, username order by bid)=1 THEN 1 ELSE 0 END) as debut
           from bids  INNER JOIN Auctions on Auctions.qauctionid = bids.auctionID 
           WHERE bids.auctionID % 100 = 79
 )
 select bozo.*, 
 row_number() over (partition by prestreak, auctionid, username order by bid) as streak,
 sum(debut) over (partition by auctionid order by bid)-1 as prevusers,
 bid=eventual_win_price as is_winner,
 bid=eventual_win_price -1 as is_pen,
 bid=eventual_bids and bid != eventual_win_price as giveup,
 (CASE when is_bidomatic THEN bids_of_this_type ELSE bids_so_far-bids_of_this_type END) as bom_bids_so_far
  from bozo order by auctionid, bid;

  DROP INDEX av_username_idx;
  DROP INDEX av_auctionid_idx;
  DROP INDEX av_bid_idx;
  CREATE INDEX av_username_idx ON ministeve USING btree (username);
  CREATE INDEX av_auctionid_idx ON ministeve USING btree (auctionid);
  CREATE INDEX av_bid_idx ON ministeve USING btree (bid);


drop table ministeve_pivot;

CREATE table ministeve_pivot as
Select n.auctionid, n.bid, max(p.bid) as max_bid, p.username from ministeve n inner join ministeve p 
on n.auctionid = p.auctionid and p.bid < n.bid and n.username <> p.username
group by p.username, n.auctionid, n.bid
order by n.bid;

drop table ministeve_joined;

CREATE table ministeve_joined as
Select m.is_winner, m.auctionid, m.cashvalue, m.cardvalue, m.auctiontime, m.bidvalue, m.cardtype, m.limited_allowed, m.bid,
 m.username, m.is_locked, m.is_bidomatic, m.bids_so_far,  m.prevusers,
m.bid - piv.max_bid as distance, piv.username as p_username,
p.is_bidomatic as p_is_bidomatic,
p.bids_so_far as p_bids_so_far, 
p.bom_bids_so_far as p_bom_bids_so_far, 
p.streak as p_streak
from ministeve m left join ministeve_pivot piv on m.auctionid = piv.auctionid and m.bid = piv.bid
left join ministeve p on p.auctionid = m.auctionid and p.bid = piv.max_bid;


drop table ministeve_lagged;
CREATE table ministeve_lagged as
select auctionid, is_winner, auctiontime, bid, is_bidomatic, bids_so_far, username, prevusers,
lag(p_username,0) over (partition by auctionid, bid order by distance DESC) as username0,
lag(distance,0) over (partition by auctionID, bid order by distance DESC) as distance0,
lag(p_is_bidomatic, 0) over (partition by auctionID, bid order by distance DESC) as is_bidomatic0,
lag(p_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bids_so_far0,
lag(p_bom_bids_so_far, 0) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far0,
lag(p_streak, 0) over (partition by auctionID, bid order by distance DESC) as streak0,

lag(p_username,1) over (partition by auctionid, bid order by distance DESC) as username1,
lag(distance,1) over (partition by auctionID, bid order by distance DESC) as distance1,
lag(p_is_bidomatic, 1) over (partition by auctionID, bid order by distance DESC) as is_bidomatic1,
lag(p_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bids_so_far1,
lag(p_bom_bids_so_far, 1) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far1,
lag(p_streak, 1) over (partition by auctionID, bid order by distance DESC) as streak1,

lag(p_username,2) over (partition by auctionid, bid order by distance DESC) as username2,
lag(distance,2) over (partition by auctionID, bid order by distance DESC) as distance2,
lag(p_is_bidomatic, 2) over (partition by auctionID, bid order by distance DESC) as is_bidomatic2,
lag(p_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bids_so_far2,
lag(p_bom_bids_so_far, 2) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far2,
lag(p_streak, 2) over (partition by auctionID, bid order by distance DESC) as streak2,

lag(p_username,3) over (partition by auctionid, bid order by distance DESC) as username3,
lag(distance,3) over (partition by auctionID, bid order by distance DESC) as distance3,
lag(p_is_bidomatic, 3) over (partition by auctionID, bid order by distance DESC) as is_bidomatic3,
lag(p_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bids_so_far3,
lag(p_bom_bids_so_far, 3) over (partition by auctionID, bid order by distance DESC) as bom_bids_so_far3,
lag(p_streak, 3) over (partition by auctionID, bid order by distance DESC) as streak3


FROM ministeve_joined ;

Select * from ministeve_lagged where distance0 is null or distance0 = 1;


