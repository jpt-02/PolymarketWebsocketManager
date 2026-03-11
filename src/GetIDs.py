import requests
import ast
import asyncio
import time

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



if __name__ == "__main__":
    slug = "btc-updown-15m-1771519500"
    print(market_from_slug(slug))

class ValidCoin:
    def __init__(self,coin,valid_durations):
        known_coins = ['btc','eth','xrp','sol','hype','bnb']
        known_durations = ['5min','15min','1hour','4hour']
        
        for duration in valid_durations:
            assert (duration in known_durations), f'Duration {duration} Not Recognized'
        assert (coin in known_coins), f'Coin name {coin} Not Recognized'

        self.coinname = coin
        self.valid_durations = valid_durations

class MarketIdentifier:
    def __init__(self,coin,duration,time):
        self.coin = coin
        self.duration = duration
        #self.time = 

        self.valid_coins = [
            ValidCoin('btc')

        ]

    def _duration_slug_part(self,duration):
        assert (duration in ['5min','15min','1hour','4hour']), f'Duration {duration} Not Recognized'

        if duration == '5min'

    def _crypto_slug_part(self,coin,duration):
        assert (coin in ['btc','eth','xrp','sol']), f'Coin name {coin} Not Recognized'
        assert (duration in ['5min','15min','1hour','4hour']), f'Duration {duration} Not Recognized'
        
        if duration == '1hour':
            if coin == 'btc':
                return 'bitcoin-up-or-down-'
            elif coin == 'eth':
                return ''
            elif coin == 'xrp':
                return ''
            elif coin == 'sol':
                return ''

        else:
            if coin == 'btc':
                return 'btc-updown-'
            elif coin == 'eth':
                return 'eth-updown-'
            elif coin == 'xrp':
                return 'xrp-updown-'
            elif coin == 'sol':
                return 'sol-updown-'


    def _timestamp_slug_part(self,time):
        pass

    def make_slug(self,coin,duration,time):
        pass



class IDManager:
    def __init__(self,websocket):
        self.websocket = websocket
        self.current_assets = []
        self.queued_assets = []



