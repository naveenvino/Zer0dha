import logging
import time
from datetime import datetime, timedelta
import json
from flask import current_app

from kiteconnect import KiteConnect

from trading_app.db import get_db

# --- Mock KiteConnect for Paper Trading ---
class MockKiteConnect:
    VARIETY_REGULAR = "regular"
    TRANSACTION_TYPE_SELL = "SELL"
    TRANSACTION_TYPE_BUY = "BUY"
    PRODUCT_NRML = "NRML"
    ORDER_TYPE_MARKET = "MARKET"
    VALIDITY_DAY = "DAY"

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.access_token = None

    def set_access_token(self, access_token):
        self.access_token = access_token

    def profile(self):
        logging.info("Mock KiteConnect: Profile fetched.")
        return {"user_name": "Paper Trader"}

    def instruments(self, exchange):
        logging.info(f"Mock KiteConnect: Fetching instruments for {exchange}.")
        # Return a dummy instrument list for NFO
        if exchange == 'NFO':
            return [
                {"instrument_token": 12345, "tradingsymbol": "NIFTY25JULC23500", "exchange": "NFO", "instrument_type": "CE", "strike": 23500, "expiry": "2025-07-25", "name": "NIFTY"},
                {"instrument_token": 12346, "tradingsymbol": "NIFTY25JULP23500", "exchange": "NFO", "instrument_type": "PE", "strike": 23500, "expiry": "2025-07-25", "name": "NIFTY"},
                {"instrument_token": 12347, "tradingsymbol": "NIFTY25JULC23700", "exchange": "NFO", "instrument_type": "CE", "strike": 23700, "expiry": "2025-07-25", "name": "NIFTY"},
                {"instrument_token": 12348, "tradingsymbol": "NIFTY25JULP23300", "exchange": "NFO", "instrument_type": "PE", "strike": 23300, "expiry": "2025-07-25", "name": "NIFTY"},
            ]
        return []

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, validity):
        order_id = f"MOCK_ORDER_{int(time.time())}"
        logging.info(f"Mock KiteConnect: Placed {transaction_type} order for {tradingsymbol} quantity {quantity}. Order ID: {order_id}")
        return order_id

# --- Helper Functions ---
def load_config_from_db():
    db = get_db()
    config = db.execute('SELECT api_key, api_secret, access_token, hedge_offset FROM config').fetchone()
    return dict(config) if config else {}

def get_kite_instance():
    """Initializes and returns a KiteConnect instance (mock or real)."""
    config = load_config_from_db()
    paper_trading_mode = config.get("paper_trading_mode", False)

    if paper_trading_mode:
        logging.info("Running in Paper Trading Mode. Using MockKiteConnect.")
        return MockKiteConnect()
    else:
        api_key = config.get("api_key")
        access_token = config.get("access_token")

        if not api_key or not access_token:
            logging.warning("API Key or Access Token not found in config.")
            return None

        try:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            kite.profile()
            logging.info("KiteConnect instance created and authenticated successfully.")
            return kite
        except Exception as e:
            logging.error(f"Error initializing KiteConnect: {e}")
            return None

NFO_INSTRUMENTS = []
INSTRUMENTS_CACHE_TIME = None
CACHE_EXPIRY_SECONDS = 3600 # Cache instruments for 1 hour

def get_and_cache_instruments(kite):
    """Fetches and caches NFO instruments from Kite."""
    global NFO_INSTRUMENTS, INSTRUMENTS_CACHE_TIME
    now = time.time()
    
    if NFO_INSTRUMENTS and INSTRUMENTS_CACHE_TIME and (now - INSTRUMENTS_CACHE_TIME < CACHE_EXPIRY_SECONDS):
        logging.info("Using cached NFO instruments.")
        return NFO_INSTRUMENTS

    try:
        logging.info("Fetching NFO instruments from Kite API...")
        NFO_INSTRUMENTS = kite.instruments('NFO')
        INSTRUMENTS_CACHE_TIME = now
        logging.info(f"Fetched and cached {len(NFO_INSTRUMENTS)} NFO instruments.")
        return NFO_INSTRUMENTS
    except Exception as e:
        logging.error(f"Could not fetch instruments: {e}")
        return []


def find_instrument_by_strike(kite, strike_price, option_type, expiry_date):
    """Finds a specific option instrument by exact strike and expiry."""
    instruments = get_and_cache_instruments(kite)
    if not instruments:
        raise Exception("Instrument list is empty.")

    for inst in instruments:
        if (inst['name'] == 'NIFTY' and 
            inst['strike'] == strike_price and 
            inst['instrument_type'] == option_type and
            inst['expiry'] == str(expiry_date)):
            return inst
    
    raise Exception(f"Could not find NIFTY {option_type} with strike {strike_price} for expiry {expiry_date}.")

def get_nearest_weekly_expiry():
    """Calculates the date of the nearest weekly expiry (Thursday)."""
    today = datetime.now()
    days_to_thursday = (3 - today.weekday() + 7) % 7
    expiry_date = today + timedelta(days=days_to_thursday)
    if days_to_thursday == 0 and today.hour >= 16:
        expiry_date += timedelta(days=7)
    return expiry_date.date()
