
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





drop table ministeve_pivot;

CREATE table ministeve_pivot as
Select n.auctionid, n.bid, max(p.bid) as max_bid, p.username from ministeve n inner join ministeve p 
on n.auctionid = p.auctionid and p.bid < n.bid and n.username <> p.username
group by p.username, n.auctionid, n.bid
order by n.bid;


Select m.auctionid, m.cashvalue, m.cardvalue, m.auctiontime, m.bidvalue, m.cardtype, m.limited_allowed, m.bid, m.username, m.is_locked,
m.bid - piv.max_bid as distance, piv.username
from ministeve m left join ministeve_pivot piv on m.auctionid = piv.auctionid and m.bid = piv.bid;



