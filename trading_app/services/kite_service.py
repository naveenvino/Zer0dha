import logging
import time
from datetime import datetime, timedelta
import json
from flask import current_app

import logging
import time
from datetime import datetime, timedelta
import json
from flask import current_app

from kiteconnect import KiteConnect, KiteConnectError, KiteTicker

KITE_TICKER_INSTANCE = None
WEBSOCKET_CLIENT = None

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
        self.mock_orders = [] # Initialize mock orders list

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

    def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, validity, price=None, trigger_price=None):
        order_id = f"MOCK_ORDER_{int(time.time())}"
        logging.info(f"Mock KiteConnect: Placed {transaction_type} order for {tradingsymbol} quantity {quantity}. Order ID: {order_id}")
        # Store mock order
        self.mock_orders.append({
            "order_id": order_id,
            "tradingsymbol": tradingsymbol,
            "exchange": exchange,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "product": product,
            "order_type": order_type,
            "validity": validity,
            "price": price,
            "trigger_price": trigger_price,
            "status": "OPEN",
            "order_timestamp": datetime.now().isoformat()
        })
        return order_id

    def orders(self):
        logging.info("Mock KiteConnect: Fetching all orders.")
        return self.mock_orders

    def modify_order(self, variety, order_id, quantity=None, price=None, trigger_price=None):
        logging.info(f"Mock KiteConnect: Modifying order {order_id}.")
        for order in self.mock_orders:
            if order["order_id"] == order_id:
                if quantity: order["quantity"] = quantity
                if price: order["price"] = price
                if trigger_price: order["trigger_price"] = trigger_price
                order["status"] = "MODIFIED"
                return order_id
        raise Exception(f"Mock Order {order_id} not found.")

    def cancel_order(self, variety, order_id):
        logging.info(f"Mock KiteConnect: Cancelling order {order_id}.")
        for order in self.mock_orders:
            if order["order_id"] == order_id:
                order["status"] = "CANCELLED"
                return order_id
        raise Exception(f"Mock Order {order_id} not found.")

    def order_history(self, order_id):
        logging.info(f"Mock KiteConnect: Fetching history for order {order_id}.")
        for order in self.mock_orders:
            if order["order_id"] == order_id:
                return [order] # Return the order as a list for history
        return []

    def trades(self):
        logging.info("Mock KiteConnect: Fetching all trades.")
        # For simplicity, mock trades as executed orders
        return [order for order in self.mock_orders if order["status"] == "OPEN"] # Mocking open orders as trades for now

# --- Helper Functions ---
def load_config_from_db():
    db = get_db()
    config = db.execute('SELECT api_key, api_secret, access_token, paper_trading_mode, hedge_offset FROM config').fetchone()
    config_dict = dict(config) if config else {}

    # Override with environment variables if set
    config_dict['api_key'] = os.environ.get('KITE_API_KEY', config_dict.get('api_key'))
    config_dict['api_secret'] = os.environ.get('KITE_API_SECRET', config_dict.get('api_secret'))
    config_dict['access_token'] = os.environ.get('KITE_ACCESS_TOKEN', config_dict.get('access_token'))
    paper_trading_mode_env = os.environ.get('PAPER_TRADING_MODE')
    if paper_trading_mode_env is not None:
        config_dict['paper_trading_mode'] = bool(int(paper_trading_mode_env))

    return config_dict

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
            error_msg = "KiteConnect initialization failed: API Key or Access Token not found in config."
            logging.error(error_msg)
            raise KiteConnectError(error_msg)

        try:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            kite.profile() # Test the connection
            logging.info("KiteConnect instance created and authenticated successfully.")
            return kite
        except Exception as e:
            error_msg = f"Error initializing KiteConnect: {e}"
            logging.error(error_msg)
            raise KiteConnectError(error_msg, original_exception=e)

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

def get_current_portfolio(kite):
    """
    Fetches and formats current portfolio data (positions and holdings).
    """
    portfolio_data = {
        "positions": [],
        "holdings": []
    }
    try:
        # Fetch positions
        positions = kite.positions()
        day_positions = positions.get("day", [])
        net_positions = positions.get("net", [])

        # Combine day and net positions, prioritizing net for overall view
        all_positions = {p["tradingsymbol"]: p for p in day_positions}
        for p in net_positions:
            all_positions[p["tradingsymbol"]] = p

        for pos in all_positions.values():
            # Fetch LTP for each position
            try:
                ltp_data = kite.ltp([f"{pos['exchange']}:{pos['tradingsymbol']}"])
                ltp = ltp_data[f"{pos['exchange']}:{pos['tradingsymbol']}"]['last_price']
            except Exception as e:
                current_app.logger.warning(f"Could not fetch LTP for {pos['tradingsymbol']}: {e}")
                ltp = None

            current_value = ltp * pos['quantity'] if ltp else None
            pnl = current_value - (pos['average_price'] * pos['quantity']) if current_value and pos['average_price'] else None

            portfolio_data["positions"].append({
                "tradingsymbol": pos['tradingsymbol'],
                "exchange": pos['exchange'],
                "quantity": pos['quantity'],
                "average_price": pos['average_price'],
                "last_price": ltp,
                "current_value": current_value,
                "pnl": pnl
            })

        # Fetch holdings
        holdings = kite.holdings()
        for hld in holdings:
            # Fetch LTP for each holding
            try:
                ltp_data = kite.ltp([f"{hld['exchange']}:{hld['tradingsymbol']}"])
                ltp = ltp_data[f"{hld['exchange']}:{hld['tradingsymbol']}"]['last_price']
            except Exception as e:
                current_app.logger.warning(f"Could not fetch LTP for {hld['tradingsymbol']}: {e}")
                ltp = None
            
            current_value = ltp * hld['quantity'] if ltp else None
            pnl = current_value - (hld['average_price'] * hld['quantity']) if current_value and hld['average_price'] else None

            portfolio_data["holdings"].append({
                "tradingsymbol": hld['tradingsymbol'],
                "exchange": hld['exchange'],
                "quantity": hld['quantity'],
                "average_price": hld['average_price'],
                "last_price": ltp,
                "current_value": current_value,
                "pnl": pnl
            })

    except Exception as e:
        current_app.logger.error(f"Error fetching portfolio data: {e}")
        raise DataFetchError(f"Failed to fetch portfolio data: {e}")

    return portfolio_data

def start_ticker_websocket(ws_client):
    global KITE_TICKER_INSTANCE, WEBSOCKET_CLIENT
    WEBSOCKET_CLIENT = ws_client

    config = load_config_from_db()
    api_key = config.get("api_key")
    access_token = config.get("access_token")
    paper_trading_mode = config.get("paper_trading_mode", False)

    if paper_trading_mode:
        logging.info("Paper trading mode: Skipping KiteTicker connection.")
        return

    if not api_key or not access_token:
        logging.error("KiteTicker connection failed: API Key or Access Token not found in config.")
        return

    if KITE_TICKER_INSTANCE and KITE_TICKER_INSTANCE.is_connected():
        logging.info("KiteTicker already connected.")
        return

    try:
        KITE_TICKER_INSTANCE = KiteTicker(api_key, access_token)
        KITE_TICKER_INSTANCE.on_connect = on_connect
        KITE_TICKER_INSTANCE.on_ticks = on_ticks
        KITE_TICKER_INSTANCE.on_close = on_close
        KITE_TICKER_INSTANCE.on_error = on_error
        KITE_TICKER_INSTANCE.on_noreconnect = on_noreconnect
        KITE_TICKER_INSTANCE.on_reconnect = on_reconnect

        logging.info("Connecting to KiteTicker...")
        KITE_TICKER_INSTANCE.connect(disable_ssl_certs=True) # Disable SSL for local testing if needed

    except Exception as e:
        logging.error(f"Error starting KiteTicker: {e}")

def stop_ticker_websocket():
    global KITE_TICKER_INSTANCE, WEBSOCKET_CLIENT
    if KITE_TICKER_INSTANCE:
        logging.info("Stopping KiteTicker...")
        KITE_TICKER_INSTANCE.close()
        KITE_TICKER_INSTANCE = None
    WEBSOCKET_CLIENT = None

def on_connect(ws, response):
    logging.info("KiteTicker connected. Subscribing to NIFTY 50 and BANKNIFTY.")
    # Example: Subscribe to NIFTY 50 (256265) and BANKNIFTY (260105) instrument tokens
    # You would dynamically get these based on user's active trades/watchlist
    ws.subscribe([256265, 260105])
    ws.set_mode(ws.MODE_FULL, [256265, 260105])

def on_ticks(ws, ticks):
    if WEBSOCKET_CLIENT:
        try:
            # Send ticks to the connected Flask-Sock client
            WEBSOCKET_CLIENT.send(json.dumps({"type": "ticks", "data": ticks}))
        except Exception as e:
            logging.error(f"Error sending ticks to WebSocket client: {e}")

def on_close(ws, code, reason):
    logging.info(f"KiteTicker closed - Code: {code}, Reason: {reason}")
    stop_ticker_websocket()

def on_error(ws, code, reason):
    logging.error(f"KiteTicker error - Code: {code}, Reason: {reason}")

def on_noreconnect(ws):
    logging.warning("KiteTicker will not attempt to reconnect.")

def on_reconnect(ws, attempt_count):
    logging.info(f"KiteTicker reconnecting - Attempt: {attempt_count}")
