from websocket import WebSocketApp
import json
import time
import threading

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"

class WebSocketOrderBook:
    def __init__(self, channel_type, url, data, auth, message_callback, verbose):
        self.channel_type = channel_type
        self.url = url
        self.data = data
        self.auth = auth
        self.message_callback = message_callback
        self.verbose = verbose
        furl = url + "/ws/" + channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        #self.orderbooks = {}

    def on_message(self, ws, message):
        print(message)
        self.message_callback(message)

    def on_error(self, ws, error):
        print("Error: ", error)
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        print("closing")
        exit(0)

    def on_open(self, ws):
        if self.channel_type == MARKET_CHANNEL:
            ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL}))
        elif self.channel_type == USER_CHANNEL and self.auth:
            ws.send(
                json.dumps(
                    {"markets": self.data, "type": USER_CHANNEL, "auth": self.auth}
                )
            )
        else:
            exit(1)

        self.pingthread = threading.Thread(target=self.ping, args=(ws,), daemon=True)
        self.pingthread.start()


    def subscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "subscribe"}))

    def unsubscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "unsubscribe"}))

    def ping(self, ws):
        while True:
            ws.send("PING")
            time.sleep(10)

    def run_blocking(self):
        self.ws.run_forever()

    def run_threaded(self):
        """Starts the websocket in a background thread."""
        self.mainthread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.mainthread.start()
        print(f"Connection to {self.channel_type} started in background.")

    def stop(self):
        """Closes the connection."""
        self.ws.close()


# Sample code from polymarket API docs - used to make sure the above class is working
if __name__ == "__main__":
    url = "wss://ws-subscriptions-clob.polymarket.com"

    from dotenv import load_dotenv, find_dotenv
    import os
    env_path = find_dotenv()
    load_dotenv(env_path)
    api_key = os.getenv('POLY_API_KEY')
    api_secret = os.getenv('POLY_API_SECRET')
    api_passphrase = os.getenv('POLY_API_PASSPHRASE')

    slug = "btc-updown-15m-1771790400"
    from GetIDs import market_from_slug
    question, conditionID, upID, downID = market_from_slug(slug)

    asset_ids = [upID]
    condition_ids = [] # no really need to filter by this one

    auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}

    market_connection = WebSocketOrderBook(
        MARKET_CHANNEL, url, asset_ids, auth, None, True
    )

    market_connection.run_threaded()

    try:    # necessary for keeping the thread alive if using run_threaded
        while True:
            time.sleep(1)
            market_connection.stop()
    except KeyboardInterrupt:
        market_connection.stop()
