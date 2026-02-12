from py_clob_client.client import ClobClient
from dotenv import load_dotenv, set_key, find_dotenv
import os

def derivekeys():
    # Set up environment access
    env_path = find_dotenv()
    load_dotenv(env_path)

    host: str = "https://clob.polymarket.com"
    key: str = os.getenv('WALLET_PRIVATE_KEY') #This is your Private Key. If using email login export from https://reveal.magic.link/polymarket otherwise export from your Web3 Application
    chain_id: int = 137 #No need to adjust this
    POLYMARKET_PROXY_ADDRESS: str = os.getenv('POLYMARKET_PROXY_ADDRESS') #This is the address you deposit/send USDC to to FUND your Polymarket account.

    #Select from the following 3 initialization options to matches your login method, and remove any unused lines so only one client is initialized.

    ### Initialization of a client using a Polymarket Proxy associated with an Email/Magic account. If you login with your email use this example.
    client = ClobClient(host, key=key, chain_id=chain_id, signature_type=1, funder=POLYMARKET_PROXY_ADDRESS)

    ### Initialization of a client using a Polymarket Proxy associated with a Browser Wallet(Metamask, Coinbase Wallet, etc)
    #client = ClobClient(host, key=key, chain_id=chain_id, signature_type=2, funder=POLYMARKET_PROXY_ADDRESS)

    ### Initialization of a client that trades directly from an EOA. 
    #client = ClobClient(host, key=key, chain_id=chain_id)

    creds = client.derive_api_key()

    set_key(env_path, "POLY_API_KEY", creds.api_key)
    set_key(env_path, "POLY_API_SECRET", creds.api_secret)
    set_key(env_path, "POLY_API_PASSPHRASE", creds.api_passphrase)

if __name__ == "__main__":
    derivekeys()