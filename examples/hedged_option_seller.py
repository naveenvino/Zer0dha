
import os
import logging
import datetime
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)

'''
# --- Global variables ---
kite = None
instruments_list = None
nifty_instruments = []
weekly_expiry_date = None
# In-memory store for open positions
# Format: {"22500-CE": {"main": "NIFTY...", "hedge": "NIFTY..."}}
open_positions = {}


def initialize_kite():
    """Initialize the Kite Connect client."""
    global kite, instruments_list, nifty_instruments, weekly_expiry_date
    try:
        api_key = os.environ.get("KITE_API_KEY")
        access_token = os.environ.get("KITE_ACCESS_TOKEN")

        if not api_key or not access_token:
            logging.error("KITE_API_KEY or KITE_ACCESS_TOKEN environment variables not set.")
            return False

        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info("Kite Connect client initialized successfully.")
        
        # Fetch and cache instruments
        instruments_list = kite.instruments("NFO")
        logging.info(f"Fetched {len(instruments_list)} instruments from NFO segment.")

        # Filter for NIFTY options and find the nearest weekly expiry
        today = datetime.date.today()
        possible_expiries = set()
        for inst in instruments_list:
            if inst['name'] == 'NIFTY' and inst['instrument_type'] in ['CE', 'PE']:
                nifty_instruments.append(inst)
                expiry_date = inst['expiry'].date()
                # Consider expiries from today onwards
                if expiry_date >= today:
                    possible_expiries.add(expiry_date)
        
        if not possible_expiries:
            logging.error("Could not determine any future NIFTY expiry dates.")
            return False

        # Find the closest expiry date from today
        weekly_expiry_date = min(possible_expiries)
        logging.info(f"Determined NIFTY weekly expiry as: {weekly_expiry_date}")

        return True

    except Exception as e:
        logging.error(f"Error during Kite Connect initialization: {e}")
        return False

def find_tradingsymbol(strike, option_type):
    """Find the tradingsymbol for a given strike, option type, and the determined weekly expiry."""
    global nifty_instruments, weekly_expiry_date
    if not nifty_instruments or not weekly_expiry_date:
        logging.error("Instrument list or expiry date not available.")
        return None

    for inst in nifty_instruments:
        if (inst['strike'] == strike and
            inst['instrument_type'] == option_type and
            inst['expiry'].date() == weekly_expiry_date):
            return inst['tradingsymbol']
            
    logging.warning(f"Trading symbol not found for strike: {strike}, type: {option_type}, expiry: {weekly_expiry_date}")
    return None

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint to receive signals from TradingView.
    Expected JSON: {"strike": 22500, "type": "CE"}
    """
    if not kite:
        return jsonify({"status": "error", "message": "Kite client not initialized"}), 500

    try:
        data = request.get_json()
        logging.info(f"Received webhook signal: {data}")

        strike_price = data.get('strike')
        option_type = data.get('type') # "CE" or "PE"

        if not strike_price or not option_type:
            return jsonify({"status": "error", "message": "Missing 'strike' or 'type' in request"}), 400

        # 1. Find the symbol for the main leg (to be sold)
        main_tradingsymbol = find_tradingsymbol(strike_price, option_type)
        if not main_tradingsymbol:
            return jsonify({"status": "error", "message": f"Could not find instrument for main leg"}), 400

        # 2. Determine and find the symbol for the hedge leg (to be bought)
        hedge_strike_offset = 300
        if option_type == 'CE':
            hedge_strike = strike_price + hedge_strike_offset
        else: # PE
            hedge_strike = strike_price - hedge_strike_offset
        
        hedge_tradingsymbol = find_tradingsymbol(hedge_strike, option_type)
        if not hedge_tradingsymbol:
            return jsonify({"status": "error", "message": f"Could not find instrument for hedge leg"}), 400

        logging.info(f"Main leg: SELL {main_tradingsymbol} | Hedge leg: BUY {hedge_tradingsymbol}")

        # 3. Place orders
        order_responses = []
        successful_orders = 0
        
        # Place SELL order for the main leg
        try:
            order_id_sell = kite.place_order(
                tradingsymbol=main_tradingsymbol,
                exchange=kite.EXCHANGE_NFO,
                transaction_type=kite.TRANSACTION_TYPE_SELL,
                quantity=1, # Assuming 1 lot, adjust if necessary
                product=kite.PRODUCT_NRML,
                order_type=kite.ORDER_TYPE_MARKET,
                variety=kite.VARIETY_REGULAR
            )
            logging.info(f"Placed SELL order for {main_tradingsymbol}, ID: {order_id_sell}")
            order_responses.append({"symbol": main_tradingsymbol, "order_id": order_id_sell, "status": "success"})
            successful_orders += 1
        except Exception as e:
            logging.error(f"Failed to place SELL order for {main_tradingsymbol}: {e}")
            order_responses.append({"symbol": main_tradingsymbol, "error": str(e), "status": "failed"})


        # Place BUY order for the hedge leg
        try:
            order_id_buy = kite.place_order(
                tradingsymbol=hedge_tradingsymbol,
                exchange=kite.EXCHANGE_NFO,
                transaction_type=kite.TRANSACTION_TYPE_BUY,
                quantity=1, # Assuming 1 lot, adjust if necessary
                product=kite.PRODUCT_NRML,
                order_type=kite.ORDER_TYPE_MARKET,
                variety=kite.VARIETY_REGULAR
            )
            logging.info(f"Placed BUY order for {hedge_tradingsymbol}, ID: {order_id_buy}")
            order_responses.append({"symbol": hedge_tradingsymbol, "order_id": order_id_buy, "status": "success"})
            successful_orders += 1
        except Exception as e:
            logging.error(f"Failed to place BUY order for {hedge_tradingsymbol}: {e}")
            order_responses.append({"symbol": hedge_tradingsymbol, "error": str(e), "status": "failed"})

        # 4. Store the position if both orders were placed successfully
        if successful_orders == 2:
            position_key = f"{strike_price}-{option_type}"
            open_positions[position_key] = {
                "main": main_tradingsymbol,
                "hedge": hedge_tradingsymbol
            }
            logging.info(f"Stored new position: {position_key}")

        return jsonify({"status": "processed", "orders": order_responses})

    except Exception as e:
        logging.error(f"An error occurred in the webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/exit-webhook', methods=['POST'])
def exit_webhook():
    """
    Webhook to exit an open position based on a stop-loss signal.
    Expected JSON: {"strike": 22500, "type": "CE"}
    """
    if not kite:
        return jsonify({"status": "error", "message": "Kite client not initialized"}), 500

    try:
        data = request.get_json()
        logging.info(f"Received exit webhook signal: {data}")

        strike_price = data.get('strike')
        option_type = data.get('type')

        if not strike_price or not option_type:
            return jsonify({"status": "error", "message": "Missing 'strike' or 'type' in request"}), 400

        position_key = f"{strike_price}-{option_type}"
        position_to_exit = open_positions.get(position_key)

        if not position_to_exit:
            logging.warning(f"No open position found for key: {position_key}. Ignoring exit signal.")
            return jsonify({"status": "ignored", "message": "No open position found"}), 404

        main_tradingsymbol = position_to_exit["main"]
        hedge_tradingsymbol = position_to_exit["hedge"]
        logging.info(f"Exiting position: Main leg: BUY {main_tradingsymbol} | Hedge leg: SELL {hedge_tradingsymbol}")

        order_responses = []

        # Place BUY order to close the main leg (short position)
        try:
            order_id_buy = kite.place_order(
                tradingsymbol=main_tradingsymbol,
                exchange=kite.EXCHANGE_NFO,
                transaction_type=kite.TRANSACTION_TYPE_BUY,
                quantity=1,
                product=kite.PRODUCT_NRML,
                order_type=kite.ORDER_TYPE_MARKET,
                variety=kite.VARIETY_REGULAR
            )
            logging.info(f"Placed BUY order to close {main_tradingsymbol}, ID: {order_id_buy}")
            order_responses.append({"symbol": main_tradingsymbol, "order_id": order_id_buy, "status": "success"})
        except Exception as e:
            logging.error(f"Failed to place BUY order for {main_tradingsymbol}: {e}")
            order_responses.append({"symbol": main_tradingsymbol, "error": str(e), "status": "failed"})

        # Place SELL order to close the hedge leg (long position)
        try:
            order_id_sell = kite.place_order(
                tradingsymbol=hedge_tradingsymbol,
                exchange=kite.EXCHANGE_NFO,
                transaction_type=kite.TRANSACTION_TYPE_SELL,
                quantity=1,
                product=kite.PRODUCT_NRML,
                order_type=kite.ORDER_TYPE_MARKET,
                variety=kite.VARIETY_REGULAR
            )
            logging.info(f"Placed SELL order to close {hedge_tradingsymbol}, ID: {order_id_sell}")
            order_responses.append({"symbol": hedge_tradingsymbol, "order_id": order_id_sell, "status": "success"})
        except Exception as e:
            logging.error(f"Failed to place SELL order for {hedge_tradingsymbol}: {e}")
            order_responses.append({"symbol": hedge_tradingsymbol, "error": str(e), "status": "failed"})

        # Remove the position from our in-memory store
        del open_positions[position_key]
        logging.info(f"Removed position from store: {position_key}")

        return jsonify({"status": "processed", "orders": order_responses})

    except Exception as e:
        logging.error(f"An error occurred in the exit webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
''

if __name__ == '__main__':
    if initialize_kite():
        # You can use any port, 5000 is common for Flask apps
        app.run(host='0.0.0.0', port=5000)
    else:
        logging.error("Failed to initialize Kite Connect. Exiting.")
