import requests
import ast
import time
from datetime import datetime
import pytz
import threading
import math

import logging
from logsconfig import console_logger
logger = logging.getLogger(__name__)



def market_from_slug(slug):
    # Gamma API endpoint for fetching market by its URL slug
    url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        
        #ast.literal_eval is necessary because otherwise its a string of IDs, not a list of strings
        upID, downID = ast.literal_eval(data['clobTokenIds'])
        conditionID = data['conditionId']
        question = data['question']
        
        return question, conditionID, upID, downID
    else:
        print("Error fetching market data")
        return None




KNOWN_COIN_MARKETS = {
    'btc':['5min','15min','1hour','4hour'],
    'eth':['5min','15min','1hour','4hour'],
    'xrp':['5min','15min','1hour','4hour'],
    'sol':['5min','15min','1hour','4hour']
}



class MarketIdentifier:
    def __init__(self,coin,duration,timeframe='now'):
        assert (coin in KNOWN_COIN_MARKETS), f'Coin name {coin} not recognized'
        assert (duration in KNOWN_COIN_MARKETS[coin]), f'Duration {duration} not recognized for coin {coin}'
        assert (timeframe=='now' or timeframe=='next'), f"Timeframe entered is '{timeframe}', must be either 'now' or 'next'"

        self.coin = coin
        self.duration = duration
        self.timeframe = timeframe

        self.slug = self._make_slug()

        self.durationtime = self._duration_in_seconds()
        self.starttime = int(self._interval_timestamp())
        self.stoptime = self.starttime + self.durationtime

        self.question, self.conditionID, self.upID, self.downID = self.market_from_slug(self.slug)

    def market_from_slug(self,slug):
        # Gamma API endpoint for fetching market by its URL slug
        url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            #ast.literal_eval is necessary because otherwise its a string of IDs, not a list of strings
            upID, downID = ast.literal_eval(data['clobTokenIds'])
            conditionID = data['conditionId']
            question = data['question']
            
            return question, conditionID, upID, downID
        else:
            raise Exception(f"Error fetching market data for slug {slug}")

    def _duration_slug_part(self):
        duration = self.duration
        duration_slug_dict = {
            '5min':'5m-',
            '15min':'15m-',
            '1hour':'',
            '4hour':'4h-'
        }
        return duration_slug_dict[duration]

    def _crypto_slug_part(self):
        coin = self.coin
        duration = self.duration
        if duration == '1hour':
            crypto_slug_dict = {
                'btc':'bitcoin-up-or-down-',
                'eth':'ethereum-up-or-down-',
                'xrp':'xrp-up-or-down-',
                'sol':'solana-up-or-down-'
            }
            return crypto_slug_dict[coin]
        else:
            crypto_slug_dict = {
                'btc':'btc-updown-',
                'eth':'eth-updown-',
                'xrp':'xrp-updown-',
                'sol':'sol-updown-'
            }
            return crypto_slug_dict[coin]

    def _duration_in_seconds(self):
        duration = self.duration
        duration_time_dict = {
            '5min':300,
            '15min':900,
            '1hour':3600,
            '4hour':14400
        }
        return duration_time_dict[duration]

    def _interval_timestamp(self):
        timeframe = self.timeframe
        if timeframe == 'now': timeref = time.time()
        if timeframe == 'next': timeref = time.time() + self._duration_in_seconds()

        duration_s = self._duration_in_seconds()
        roundtime = round(timeref - (timeref%duration_s))
        return str(roundtime)

    def _timestamp_slug_part(self):
        duration = self.duration

        if duration == '1hour':
            interval_stamp = int(self._interval_timestamp())
            est_tz = pytz.timezone("America/New_York")
            dt_object = datetime.fromtimestamp(interval_stamp, tz=est_tz)
            monthname = dt_object.strftime('%B').lower()
            day = dt_object.day
            year = dt_object.year
            time_ = dt_object.strftime('%#I%p').lower()
            return f'{monthname}-{day}-{year}-{time_}-et'
        else:
            return self._interval_timestamp()

    def _make_slug(self):
        coinpart = self._crypto_slug_part()
        durationpart = self._duration_slug_part()
        timepart = self._timestamp_slug_part()
        return coinpart+durationpart+timepart

# if __name__ == "__main__":
#     slug = "btc-updown-15m-1771519500"
#     #print(market_from_slug(slug))
#     TestIdentifier1 = MarketIdentifier('btc','15min','now')
#     #print(TestIdentifier1._crypto_slug_part())
#     #print(TestIdentifier1._duration_slug_part())
#     #print(TestIdentifier1._timestamp_slug_part())
#     print(TestIdentifier1.slug)
#     TestIdentifier2 = MarketIdentifier('btc','1hour','now')
#     #print(TestIdentifier2._crypto_slug_part())
#     #print(TestIdentifier2._duration_slug_part())
#     #print(TestIdentifier2._timestamp_slug_part())
#     print(TestIdentifier2.slug)


class IDManager:
    def __init__(self,websocket):
        self.websocket = websocket
        self.focusdict = {} # duration: {coins:list, worker:thread}
        self.lock = threading.Lock()

    def add_focus(self,coin,duration):
        # tells manager which assets to focus on
        if coin not in KNOWN_COIN_MARKETS:
            logger.warning(f"Coin name '{coin}' not recognized and could not be added")
            return

        if duration not in KNOWN_COIN_MARKETS[coin]:
            logger.warning(f"Duration '{duration}' not recognized for coin '{coin}' and could not be added")
            return

        with self.lock:
            if duration not in self.focusdict:
                # There is not currently a thread timing the requested duration
                self.focusdict[duration] = {'coins':[coin],'queued_removals':[]}
                new_thread = threading.Thread(target=self._worker, args=[duration], daemon=True)
                new_thread.start()
                self.focusdict[duration]['worker'] = new_thread
                logger.info(f"Created new thread for duration '{duration}'")
                logger.info(f"Added coin '{coin}' to thread with duration '{duration}'")

            elif coin not in self.focusdict[duration]['coins']:
                # There is a thread timing the requested duration, but it does not have the requested coin
                self.focusdict[duration]['coins'].append(coin)
                logger.info(f"Added coin '{coin}' to thread with duration '{duration}'")

            elif (coin in self.focusdict[duration]['coins']) and (coin in self.focusdict[duration]['queued_removals']):
                # The duration+coind combination is already accounted for but it is also queued as a removal
                self.focusdict[duration]['queued_removals'].remove(coin)
                logger.info(f"Removal request for '{coin}' cancelled for thread '{duration}'")

            else:
                # The duration+coin combination is already accounted for
                logger.warning(f"Coin '{coin}' already in thread with duration '{duration}'")



    def remove_focus(self,coin,duration):
        # tells manager to stop focusing on an asset
        if coin not in KNOWN_COIN_MARKETS:
            logger.warning(f"Coin name '{coin}' not recognized and could not be removed")
            return

        if duration not in KNOWN_COIN_MARKETS[coin]:
            logger.warning(f"Duration '{duration}' not recognized for coin '{coin}' and could not be removed")
            return

        with self.lock:
            if duration not in self.focusdict:
                logger.info(f"Coin '{coin}' not in thread with duration '{duration}' and could not be removed")
                return
            
            elif coin not in self.focusdict[duration]['coins']:
                logger.info(f"Coin '{coin}' not in thread with duration '{duration}' and could not be removed")
                return 
            
            else:
                # add coin to queued removals so it can be unsubscribed from
                self.focusdict[duration]['queued_removals'].append(coin)
                # add log for this
                logger.info(f"Coin '{coin}' queued for removal in thread with duration '{duration}'")

    def _worker(self,duration):
        
        startup = True
        time.sleep(1) # wait 1 second for focusdict to populate on startup

        while True:
            with self.lock:
                # make a copy of coinlist from the focusdict for this duration
                coinlist = self.focusdict[duration]['coins'][:]
                # terminate loop if coin list is empty
                if len(coinlist) == 0:
                    del self.focusdict[duration] # remove now so new subscriptions arent added to threads that are shutting down
                    logger.info(f'{duration} Thread: Shutting Down')
                    return

            # gather all coin IDs for duration
            unsub_ids = {}
            sub_ids = {}
            for coin in coinlist:
                unsub_ids[coin] = MarketIdentifier(coin,duration,'now')
                sub_ids[coin] = MarketIdentifier(coin,duration,'next')
            
            # work out timing with random coin from coinlist
            market_end = unsub_ids[coinlist[0]].stoptime
            duration_s = unsub_ids[coinlist[0]].durationtime
            now = time.time()

            if now < market_end-60:
                # if not before next market sub time
                logger.info(f'{duration} Thread: waiting until {time.ctime(time.time()+(market_end-60-now))}')
                time.sleep(market_end-60-now) # wait until time is 4:00 or -1:00
            else:
                # if past halfway and subtime, wait until next loop and retry
                logger.info(f'{duration} Thread: waiting until next loop')
                time.sleep(duration_s/2)
                continue
            
            with self.lock:
                removals = self.focusdict[duration]['queued_removals'][:]
                for coin in removals:
                    sub_ids.pop(coin) # remove corresponding entries in sub_ids
                    self.focusdict[duration]['coins'].remove(coin) # also remove corresponding entries from next loop's coinlist
                    self.focusdict[duration]['queued_removals'].remove(coin)

            # sub to 'next' markets     -1:00
            for id in sub_ids.values():
                logger.info(f"{duration} Thread: subscribing to '{id.coin}' market start at {time.ctime(id.starttime)}")
            time.sleep(60)
            # markets officially start/end - do nothing       0:00
            time.sleep(60)
            # unsub from 'now' markets       1:00
            if not startup:
                for id in unsub_ids.values(): # ubsub from stale markets
                    logger.info(f"{duration} Thread: unsubscribing to '{id.coin}' market stop at {time.ctime(id.stoptime)}")
            
            startup = False # mark startup as false at end of first loop
            
            # loop ends at around 1:00


               

if __name__ == '__main__':

    listener = console_logger()

    logger.info('Logging started locally')

    testmanager = IDManager('test')
    # testmanager.add_focus('btc','15min')
    # testmanager.add_focus('btc','15min')
    testmanager.add_focus('btc','5min')
    #testmanager.add_focus('eth','5min')
    # testmanager.add_focus('sol','1hour')
    # testmanager.add_focus('xrp','4hour')
    # testmanager.add_focus('idk','idk')
    # testmanager.add_focus('btc','idk')
    #print(testmanager.focusdict)

    # try:
    #     while True:
    #         time.sleep(10)
    # except KeyboardInterrupt:
    #     pass

    try:
        while True:
            time.sleep(620)
            testmanager.remove_focus('btc','5min')
    except KeyboardInterrupt:
        pass