from flask import Flask, render_template, request, jsonify
import json
import os
import sys
import logging
from datetime import datetime, timedelta
import time

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Add Project Root to Path ---
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from kiteconnect import KiteConnect
except ImportError:
    logging.error("Could not import KiteConnect. Make sure it's in the parent directory.")
    sys.exit(1)

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Configuration ---
DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
STRATEGIES_FILE = os.path.join(DATA_DIR, "strategies.json") # Kept for any future use
INSTRUMENTS_FILE = os.path.join(DATA_DIR, "instruments.json")
ACTIVE_TRADES_FILE = os.path.join(DATA_DIR, "active_trades.json")
HEDGE_OFFSET = 200 # Points away for the hedge leg

# --- In-memory Cache ---
NFO_INSTRUMENTS = []
INSTRUMENTS_CACHE_TIME = None
CACHE_EXPIRY_SECONDS = 3600 # Cache instruments for 1 hour

# --- Ensure Directories and Files Exist ---
for path in [DATA_DIR, CONFIG_FILE, STRATEGIES_FILE, ACTIVE_TRADES_FILE]:
    if not os.path.exists(path):
        if '.' in os.path.basename(path): # It's a file
             with open(path, 'w') as f:
                json.dump({} if 'config' in path else [], f)
        else: # It's a directory
            os.makedirs(path)


# --- Helper Functions ---
def load_json_file(filepath, default_value):
    """Generic function to load a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return default_value

def write_json_file(filepath, data):
    """Generic function to write data to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_kite_instance():
    """Initializes and returns a KiteConnect instance."""
    config = load_json_file(CONFIG_FILE, {})
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
        write_json_file(INSTRUMENTS_FILE, NFO_INSTRUMENTS)
        logging.info(f"Fetched and cached {len(NFO_INSTRUMENTS)} NFO instruments.")
        return NFO_INSTRUMENTS
    except Exception as e:
        logging.error(f"Could not fetch instruments: {e}")
        return load_json_file(INSTRUMENTS_FILE, [])


def find_instrument_by_strike(kite, strike_price, option_type, expiry_date):
    """Finds a specific option instrument by exact strike and expiry."""
    instruments = get_and_cache_instruments(kite)
    if not instruments:
        raise Exception("Instrument list is empty.")

    for inst in instruments:
        if (inst['name'] == 'NIFTY' and 
            inst['strike'] == strike_price and 
            inst['instrument_type'] == option_type and
            inst['expiry'] == expiry_date):
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

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    if request.method == 'POST':
        write_json_file(CONFIG_FILE, request.json)
        logging.info("API configuration saved.")
        return jsonify({'status': 'success', 'message': 'Configuration saved successfully.'})
    else:
        return jsonify(load_json_file(CONFIG_FILE, {}))

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    return jsonify(load_json_file(STRATEGIES_FILE, []))

@app.route('/api/strategies', methods=['POST'])
def add_strategy():
    strategies = load_json_file(STRATEGIES_FILE, [])
    new_strategy = request.json
    new_strategy['id'] = int(time.time() * 1000)
    strategies.append(new_strategy)
    write_json_file(STRATEGIES_FILE, strategies)
    return jsonify({'status': 'success', 'message': 'Strategy saved.'})

@app.route('/api/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    strategies = load_json_file(STRATEGIES_FILE, [])
    strategies = [s for s in strategies if s.get('id') != strategy_id]
    write_json_file(STRATEGIES_FILE, strategies)
    return jsonify({'status': 'success', 'message': 'Strategy deleted.'})

def place_order_leg(kite, leg_details):
    """Places a single order and returns the response."""
    logging.info(f"Placing order for {leg_details['tradingsymbol']}: {leg_details}")
    order_id = kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=leg_details['exchange'],
        tradingsymbol=leg_details['tradingsymbol'],
        transaction_type=leg_details['transaction_type'],
        quantity=leg_details['quantity'],
        product=kite.PRODUCT_NRML,
        order_type=kite.ORDER_TYPE_MARKET,
        validity=kite.VALIDITY_DAY
    )
    logging.info(f"Order placed successfully for {leg_details['tradingsymbol']}. Order ID: {order_id}")
    return {'leg': leg_details, 'status': 'success', 'order_id': order_id}

@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Handles dynamic trade execution based on TradingView alerts.
    Expected Entry JSON: {"alert_type": "entry", "option_type": "CE", "strike_price": 23500, "quantity": 50}
    Expected Exit JSON:  {"alert_type": "exit", "strike_price": 23500}
    """
    logging.info("Webhook alert received.")
    try:
        data = request.json
        logging.info(f"Webhook data: {data}")
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Invalid JSON: {e}'}), 400

    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500

    alert_type = data.get('alert_type')
    strike_price = data.get('strike_price')

    if not alert_type or not strike_price:
        return jsonify({'status': 'error', 'message': 'Missing alert_type or strike_price'}), 400

    # --- HANDLE TRADE ENTRY ---
    if alert_type == 'entry':
        try:
            option_type = data.get('option_type')
            quantity = data.get('quantity')
            if not option_type or not quantity:
                return jsonify({'status': 'error', 'message': 'Entry alert requires option_type and quantity'}), 400

            expiry = get_nearest_weekly_expiry()
            
            # --- Define Sell Leg ---
            sell_strike = strike_price
            sell_instrument = find_instrument_by_strike(kite, sell_strike, option_type, expiry)
            
            # --- Define Hedge Leg ---
            hedge_strike = sell_strike + HEDGE_OFFSET if option_type == 'CE' else sell_strike - HEDGE_OFFSET
            hedge_instrument = find_instrument_by_strike(kite, hedge_strike, option_type, expiry)

            # --- Place Orders ---
            trade_legs = []
            # Place Sell Order
            sell_leg_details = {
                'tradingsymbol': sell_instrument['tradingsymbol'], 'exchange': sell_instrument['exchange'],
                'transaction_type': kite.TRANSACTION_TYPE_SELL, 'quantity': quantity
            }
            response = place_order_leg(kite, sell_leg_details)
            trade_legs.append(response)

            # Place Hedge Order
            hedge_leg_details = {
                'tradingsymbol': hedge_instrument['tradingsymbol'], 'exchange': hedge_instrument['exchange'],
                'transaction_type': kite.TRANSACTION_TYPE_BUY, 'quantity': quantity
            }
            response = place_order_leg(kite, hedge_leg_details)
            trade_legs.append(response)
            
            # --- Save Active Trade ---
            active_trades = load_json_file(ACTIVE_TRADES_FILE, [])
            active_trades.append({'id': strike_price, 'legs': [sell_leg_details, hedge_leg_details]})
            write_json_file(ACTIVE_TRADES_FILE, active_trades)

            return jsonify({'status': 'entry_success', 'details': trade_legs})

        except Exception as e:
            logging.error(f"Error during trade entry: {e}")
            return jsonify({'status': 'entry_error', 'message': str(e)}), 500

    # --- HANDLE TRADE EXIT (STOPLOSS) ---
    elif alert_type == 'exit':
        try:
            active_trades = load_json_file(ACTIVE_TRADES_FILE, [])
            trade_to_exit = next((t for t in active_trades if t['id'] == strike_price), None)

            if not trade_to_exit:
                return jsonify({'status': 'exit_error', 'message': f'No active trade found for strike {strike_price}'}), 404

            logging.info(f"Exiting trade for strike {strike_price}")
            exit_responses = []
            for leg in trade_to_exit['legs']:
                # Create opposite order to square off
                exit_leg = leg.copy()
                exit_leg['transaction_type'] = kite.TRANSACTION_TYPE_BUY if leg['transaction_type'] == kite.TRANSACTION_TYPE_SELL else kite.TRANSACTION_TYPE_SELL
                response = place_order_leg(kite, exit_leg)
                exit_responses.append(response)
            
            # --- Remove from Active Trades ---
            remaining_trades = [t for t in active_trades if t['id'] != strike_price]
            write_json_file(ACTIVE_TRADES_FILE, remaining_trades)

            return jsonify({'status': 'exit_success', 'details': exit_responses})

        except Exception as e:
            logging.error(f"Error during trade exit: {e}")
            return jsonify({'status': 'exit_error', 'message': str(e)}), 500

    else:
        return jsonify({'status': 'error', 'message': f'Invalid alert_type: {alert_type}'}), 400


# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
