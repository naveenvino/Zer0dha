from flask import Blueprint, request, jsonify, current_app
import logging
import json
from trading_app.db import get_db
from trading_app.services.kite_service import get_kite_instance, get_and_cache_instruments, find_instrument_by_strike, get_nearest_weekly_expiry

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Routes ---

@api_bp.route('/config', methods=['GET', 'POST', 'PUT'])
def manage_config():
    db = get_db()
    if request.method == 'POST' or request.method == 'PUT':
        config_data = request.json
        paper_trading_mode_int = 1 if config_data.get('paper_trading_mode') else 0

        # Check if a config entry already exists
        existing_config = db.execute('SELECT id FROM config').fetchone()

        if existing_config:
            # Update existing config
            db.execute(
                'UPDATE config SET api_key = ?, api_secret = ?, access_token = ?, paper_trading_mode = ?, hedge_offset = ? WHERE id = ?',
                (config_data.get('api_key'), config_data.get('api_secret'), config_data.get('access_token'), paper_trading_mode_int, config_data.get('hedge_offset'), existing_config['id'])
            )
            message = 'Configuration updated successfully.'
        else:
            # Insert new config
            db.execute(
                'INSERT INTO config (api_key, api_secret, access_token, paper_trading_mode, hedge_offset) VALUES (?, ?, ?, ?, ?)',
                (config_data.get('api_key'), config_data.get('api_secret'), config_data.get('access_token'), paper_trading_mode_int, config_data.get('hedge_offset'))
            )
            message = 'Configuration saved successfully.'
        db.commit()
        logging.info(message)
        return jsonify({'status': 'success', 'message': message})
    else: # GET request
        config = db.execute('SELECT api_key, api_secret, access_token, paper_trading_mode, hedge_offset FROM config').fetchone()
        if config:
            # Convert paper_trading_mode back to boolean for the UI
            config_dict = dict(config)
            config_dict['paper_trading_mode'] = bool(config_dict['paper_trading_mode'])
            return jsonify(config_dict)
        return jsonify({})

@api_bp.route('/strategies', methods=['GET'])
def get_strategies():
    db = get_db()
    strategies = db.execute('SELECT * FROM strategies').fetchall()
    return jsonify([dict(row) for row in strategies])

@api_bp.route('/strategies', methods=['POST'])
def add_strategy():
    new_strategy = request.json
    db = get_db()
    db.execute(
        'INSERT INTO strategies (name, stop_loss, target_profit, legs) VALUES (?, ?, ?, ?)',
        (new_strategy['name'], new_strategy.get('stop_loss'), new_strategy.get('target_profit'), json.dumps(new_strategy['legs']))
    )
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy saved.'})

@api_bp.route('/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    db = get_db()
    db.execute('DELETE FROM strategies WHERE id = ?', (strategy_id,))
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy deleted.'})

@api_bp.route('/strategies/<int:strategy_id>', methods=['PUT'])
def update_strategy(strategy_id):
    strategy_data = request.json
    db = get_db()
    db.execute(
        'UPDATE strategies SET name = ?, stop_loss = ?, target_profit = ?, legs = ? WHERE id = ?',
        (strategy_data['name'], strategy_data.get('stop_loss'), strategy_data.get('target_profit'), json.dumps(strategy_data['legs']), strategy_id)
    )
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy updated.'})

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

@api_bp.route('/webhook', methods=['POST'])
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
            config = db.execute('SELECT hedge_offset FROM config').fetchone()
            hedge_offset = config['hedge_offset'] if config else 200 # Default to 200 if not found
            hedge_strike = sell_strike + hedge_offset if option_type == 'CE' else sell_strike - hedge_offset
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
            db = get_db()
            db.execute(
                'INSERT INTO active_trades (strategy_id, strike_price, legs) VALUES (?, ?, ?)',
                (data.get('strategy_id'), strike_price, json.dumps(trade_legs))
            )
            db.commit()

            return jsonify({'status': 'entry_success', 'details': trade_legs})

        except Exception as e:
            logging.error(f"Error during trade entry: {e}")
            return jsonify({'status': 'entry_error', 'message': str(e)}), 500

    # --- HANDLE TRADE EXIT (STOPLOSS) ---
    elif alert_type == 'exit':
        try:
            db = get_db()
            trade_to_exit = db.execute('SELECT * FROM active_trades WHERE strike_price = ?', (strike_price,)).fetchone()

            if not trade_to_exit:
                return jsonify({'status': 'exit_error', 'message': f'No active trade found for strike {strike_price}'}), 404

            logging.info(f"Exiting trade for strike {strike_price}")
            exit_responses = []
            legs_to_exit = json.loads(trade_to_exit['legs'])
            for leg in legs_to_exit:
                # Create opposite order to square off
                exit_leg = leg['leg'].copy()
                exit_leg['transaction_type'] = kite.TRANSACTION_TYPE_BUY if leg['leg']['transaction_type'] == kite.TRANSACTION_TYPE_SELL else kite.TRANSACTION_TYPE_SELL
                response = place_order_leg(kite, exit_leg)
                exit_responses.append(response)
            
            # --- Remove from Active Trades ---
            db.execute('DELETE FROM active_trades WHERE id = ?', (trade_to_exit['id'],))
            db.commit()

            return jsonify({'status': 'exit_success', 'details': exit_responses})

        except Exception as e:
            logging.error(f"Error during trade exit: {e}")
            return jsonify({'status': 'exit_error', 'message': str(e)}), 500

    else:
        return jsonify({'status': 'error', 'message': f'Invalid alert_type: {alert_type}'}), 400

@api_bp.route('/active_trades', methods=['GET'])
def get_active_trades():
    db = get_db()
    active_trades = db.execute('SELECT * FROM active_trades').fetchall()
    return jsonify([dict(row) for row in active_trades])