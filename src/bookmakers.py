from OpenSocket import WebSocketOrderBook
from dotenv import load_dotenv, find_dotenv
import os
from bookslots import OrderBook
import json
import queue
import threading


class Bookmaker:
    def __init__(self):
        self.load_details()
        self.message_queue = queue.Queue()

    def load_details(self):
        self.url = "wss://ws-subscriptions-clob.polymarket.com"
        env_path = find_dotenv()
        load_dotenv(env_path)
        api_key = os.getenv('POLY_API_KEY')
        api_secret = os.getenv('POLY_API_SECRET')
        api_passphrase = os.getenv('POLY_API_PASSPHRASE')
        self.auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}

    def calculate_latency(localtime,timestamp):
        pass

    def websocket_callback(self,message):
        self.message_queue.put_nowait(message)

    def queue_worker(self):
        while True:
            message = self.message_queue.get()
            self.interpret_message_string(message)
            self.message_queue.task_done()

    def start(self):
        t = threading.Thread(target=self.queue_worker, daemon=True)
        t.start()

    def interpret_message_string(self, message):
        # Placeholder - is overwritten by each subclass
        raise NotImplementedError("Subclasses must implement interpret_message")


class MarketBookmaker(Bookmaker):
    # TO DO:
    #   -make it so bookdict gets rid of books once a market expires
    #   -add timestamp functionality, possibly as a slot
    def __init__(self):
        super().__init__()
        self.bookdict = {} # assetID : OrderBook object from bookslots.py

    def interpret_message_string(self,message):
        try:
            # message originally comes in as a string
            message_json = json.loads(message)
            self.interpret_message_json(message_json)
        except Exception as e:
            print(e)

    def interpret_message_json(self,message):
        # message comes in a json
        if isinstance(message,list):
            for item in message: self.interpret_message_json(item)
        elif isinstance(message,dict):
            try: # try statement in case there is no event_type
                event_type = message['event_type'] # Get the variable once to save lookups
                if event_type == 'book':
                    if message['asset_id'] not in self.bookdict:
                        self.bookdict[message['asset_id']] = OrderBook(message['asset_id'])
                        self.bookdict[message['asset_id']].update_book(message)
                    else:
                        self.bookdict[message['asset_id']].update_book(message)
                elif event_type == 'price_change':
                    for change in message['price_changes']:
                        self.bookdict[change['asset_id']].update_asset(change)
            except Exception as e:
                print(e)

class UserBookmaker(Bookmaker):
    def __init__(self):
        super().__init__()

class RTDSBookmaker(Bookmaker):
    def __init__(self):
        super().__init__()




tstring = '[{"name": "John", "age": 30, "city": "New York"}]'
for key in json.loads(tstring):
    print(type(key))
