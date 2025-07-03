from flask import Blueprint, request, jsonify, current_app
import logging
import json
from datetime import datetime # Import datetime
from trading_app.db import get_db
from trading_app.services.kite_service import get_kite_instance, get_and_cache_instruments, find_instrument_by_strike, get_nearest_weekly_expiry, get_current_portfolio
from trading_app.services.news_service import fetch_market_news
from trading_app.services.notification_service import send_email_notification
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from trading_app.models import User # Import the User class from models.py

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Routes ---

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400

    db_conn = get_db()
    existing_user = db_conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing_user:
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

    hashed_password = generate_password_hash(password)
    db_conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    db_conn.commit()
    return jsonify({'status': 'success', 'message': 'User registered successfully'}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.get_by_username(username)
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'status': 'success', 'message': 'Logged in successfully', 'username': user.username}), 200
    return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

@api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'}), 200

@api_bp.route('/user_status', methods=['GET'])
def user_status():
    if current_user.is_authenticated:
        return jsonify({'status': 'success', 'is_authenticated': True, 'username': current_user.username}), 200
    return jsonify({'status': 'success', 'is_authenticated': False}), 200


@api_bp.route('/config', methods=['GET', 'POST', 'PUT'])
@login_required
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
                'UPDATE config SET api_key = ?, api_secret = ?, access_token = ?, paper_trading_mode = ?, hedge_offset = ?, email_notifications_enabled = ?, email_recipients = ?, smtp_server = ?, smtp_port = ?, smtp_username = ?, smtp_password = ? WHERE id = ?',
                (config_data.get('api_key'), config_data.get('api_secret'), config_data.get('access_token'), paper_trading_mode_int, config_data.get('hedge_offset'), config_data.get('email_notifications_enabled', 0), config_data.get('email_recipients'), config_data.get('smtp_server'), config_data.get('smtp_port'), config_data.get('smtp_username'), config_data.get('smtp_password'), existing_config['id'])
            )
            message = 'Configuration updated successfully.'
        else:
            # Insert new config
            db.execute(
                'INSERT INTO config (api_key, api_secret, access_token, paper_trading_mode, hedge_offset, email_notifications_enabled, email_recipients, smtp_server, smtp_port, smtp_username, smtp_password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (config_data.get('api_key'), config_data.get('api_secret'), config_data.get('access_token'), paper_trading_mode_int, config_data.get('hedge_offset'), config_data.get('email_notifications_enabled', 0), config_data.get('email_recipients'), config_data.get('smtp_server'), config_data.get('smtp_port'), config_data.get('smtp_username'), config_data.get('smtp_password'))
            )
            message = 'Configuration saved successfully.'
        db.commit()
        logging.info(message)
        return jsonify({'status': 'success', 'message': message})
    else: # GET request
        config = db.execute('SELECT api_key, api_secret, access_token, paper_trading_mode, hedge_offset, email_notifications_enabled, email_recipients, smtp_server, smtp_port, smtp_username, smtp_password FROM config').fetchone()
        if config:
            # Convert paper_trading_mode and email_notifications_enabled back to boolean for the UI
            config_dict = dict(config)
            config_dict['paper_trading_mode'] = bool(config_dict['paper_trading_mode'])
            config_dict['email_notifications_enabled'] = bool(config_dict['email_notifications_enabled'])
            return jsonify(config_dict)
        return jsonify({})

@api_bp.route('/strategies', methods=['GET'])
@login_required
def get_strategies():
    db = get_db()
    strategies = db.execute('SELECT * FROM strategies').fetchall()
    return jsonify([dict(row) for row in strategies])

@api_bp.route('/strategies', methods=['POST'])
@login_required
def add_strategy():
    new_strategy = request.json
    db = get_db()
    db.execute(
        'INSERT INTO strategies (name, stop_loss, target_profit, legs, parameters) VALUES (?, ?, ?, ?, ?)',
        (new_strategy['name'], new_strategy.get('stop_loss'), new_strategy.get('target_profit'), json.dumps(new_strategy['legs']), json.dumps(new_strategy.get('parameters', {})))
    )
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy saved.'})

@api_bp.route('/strategies/<int:strategy_id>', methods=['DELETE'])
@login_required
def delete_strategy(strategy_id):
    db = get_db()
    db.execute('DELETE FROM strategies WHERE id = ?', (strategy_id,))
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy deleted.'})

@api_bp.route('/strategies/<int:strategy_id>', methods=['PUT'])
@login_required
def update_strategy(strategy_id):
    strategy_data = request.json
    db = get_db()
    db.execute(
        'UPDATE strategies SET name = ?, stop_loss = ?, target_profit = ?, legs = ?, parameters = ? WHERE id = ?',
        (strategy_data['name'], strategy_data.get('stop_loss'), strategy_data.get('target_profit'), json.dumps(strategy_data['legs']), json.dumps(strategy_data.get('parameters', {})), strategy_id)
    )
    db.commit()
    return jsonify({'status': 'success', 'message': 'Strategy updated.'})

def place_order_leg(kite, leg_details):
    """Places a single order and returns the response."""
    logging.info(f"Placing order for {leg_details['tradingsymbol']}: {leg_details}")
    order_id = kite.place_order(
        variety=leg_details.get('variety', kite.VARIETY_REGULAR),
        exchange=leg_details['exchange'],
        tradingsymbol=leg_details['tradingsymbol'],
        transaction_type=leg_details['transaction_type'],
        quantity=leg_details['quantity'],
        product=leg_details.get('product', kite.PRODUCT_NRML),
        order_type=leg_details.get('order_type', kite.ORDER_TYPE_MARKET),
        price=leg_details.get('price'),
        trigger_price=leg_details.get('trigger_price'),
        validity=leg_details.get('validity', kite.VALIDITY_DAY)
    )
    logging.info(f"Order placed successfully for {leg_details['tradingsymbol']}. Order ID: {order_id}")
    return {'leg': leg_details, 'status': 'success', 'order_id': order_id}

@api_bp.route('/webhook', methods=['POST'])
def tradingview_webhook():
    """
    Handles dynamic trade execution based on TradingView alerts.
    Expected JSON for strategy execution: {"strategy_name": "MyStrategy", "alert_type": "entry" or "exit", ...}
    Expected JSON for direct order: {"alert_type": "entry", "option_type": "CE", "strike_price": 23500, "quantity": 50}
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

    strategy_name = data.get('strategy_name')
    alert_type = data.get('alert_type')
    strike_price = data.get('strike_price') # Still relevant for direct orders and exit alerts

    db = get_db()

    # --- Handle Strategy-based Execution ---
    if strategy_name:
        strategy = db.execute('SELECT * FROM strategies WHERE name = ?', (strategy_name,)).fetchone()
        if not strategy:
            return jsonify({'status': 'error', 'message': f'Strategy "{strategy_name}" not found'}), 404

        strategy_legs = json.loads(strategy['legs'])
        trade_responses = []

        if alert_type == 'entry':
            try:
                for leg_details in strategy_legs:
                    response = place_order_leg(kite, leg_details)
                    trade_responses.append(response)
                
                # Save active trade for strategy
                db.execute(
                    'INSERT INTO active_trades (strategy_id, strategy_name, strike_price, legs) VALUES (?, ?, ?, ?)',
                    (strategy['id'], strategy_name, strike_price, json.dumps(trade_responses)) # strike_price might be null if not provided by webhook
                )
                db.commit()
                return jsonify({'status': 'strategy_entry_success', 'strategy': strategy_name, 'details': trade_responses})
            except Exception as e:
                logging.error(f"Error executing strategy '{strategy_name}' entry: {e}")
                return jsonify({'status': 'strategy_entry_error', 'message': str(e)}), 500

        elif alert_type == 'exit':
            try:
                # Find active trade by strategy name and optionally strike price
                if strike_price:
                    trade_to_exit = db.execute('SELECT * FROM active_trades WHERE strategy_name = ? AND strike_price = ?', (strategy_name, strike_price)).fetchone()
                else:
                    trade_to_exit = db.execute('SELECT * FROM active_trades WHERE strategy_name = ? ORDER BY entry_time DESC', (strategy_name,)).fetchone() # Get latest if no strike
                
                if not trade_to_exit:
                    return jsonify({'status': 'exit_error', 'message': f'No active trade found for strategy "{strategy_name}" and strike {strike_price}'}), 404

                logging.info(f"Exiting trade for strategy {strategy_name}")
                exit_responses = []
                legs_to_exit = json.loads(trade_to_exit['legs'])
                for leg in legs_to_exit:
                    # Create opposite order to square off
                    exit_leg = leg['leg'].copy()
                    exit_leg['transaction_type'] = kite.TRANSACTION_TYPE_BUY if leg['leg']['transaction_type'] == kite.TRANSACTION_TYPE_SELL else kite.TRANSACTION_TYPE_SELL
                    response = place_order_leg(kite, exit_leg)
                    exit_responses.append(response)
                
                # Remove from Active Trades
            db.execute('DELETE FROM active_trades WHERE id = ?', (trade_to_exit['id'],))
            db.commit()

            # Calculate P&L and save to trade_history
            total_pnl = 0
            entry_legs_data = json.loads(trade_to_exit['legs'])
            exit_legs_data_for_db = []

            for i, entry_leg in enumerate(entry_legs_data):
                exit_leg_response = exit_responses[i]
                exit_leg_details = exit_leg_response['leg']

                # Fetch LTP for P&L calculation
                try:
                    ltp_data = kite.ltp([f"{entry_leg['leg']['exchange']}:{entry_leg['leg']['tradingsymbol']}"])
                    exit_price = ltp_data[f"{entry_leg['leg']['exchange']}:{entry_leg['leg']['tradingsymbol']}"]['last_price']
                except Exception as e:
                    current_app.logger.warning(f"Could not fetch LTP for {entry_leg['leg']['tradingsymbol']} for P&L calculation: {e}")
                    exit_price = 0 # Default to 0 if LTP not available

                # Calculate P&L for the leg
                leg_pnl = 0
                if entry_leg['leg']['transaction_type'] == kite.TRANSACTION_TYPE_SELL:
                    # For a sell entry, P&L = (entry_price - exit_price) * quantity
                    leg_pnl = (entry_leg['leg']['price'] - exit_price) * entry_leg['leg']['quantity']
                else: # BUY transaction
                    # For a buy entry, P&L = (exit_price - entry_price) * quantity
                    leg_pnl = (exit_price - entry_leg['leg']['price']) * entry_leg['leg']['quantity']
                
                total_pnl += leg_pnl

                exit_legs_data_for_db.append({
                    "tradingsymbol": exit_leg_details['tradingsymbol'],
                    "exchange": exit_leg_details['exchange'],
                    "transaction_type": exit_leg_details['transaction_type'],
                    "quantity": exit_leg_details['quantity'],
                    "exit_price": exit_price,
                    "pnl": leg_pnl
                })

            db.execute(
                'INSERT INTO trade_history (strategy_id, strategy_name, entry_time, exit_time, entry_legs_data, exit_legs_data, total_pnl, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (trade_to_exit['strategy_id'], trade_to_exit['strategy_name'], trade_to_exit['entry_time'], datetime.now(), json.dumps(entry_legs_data), json.dumps(exit_legs_data_for_db), total_pnl, 'COMPLETED')
            )
            db.commit()

            return jsonify({'status': 'strategy_exit_success', 'strategy': strategy_name, 'details': exit_responses, 'total_pnl': total_pnl})

            except Exception as e:
                logging.error(f"Error during strategy '{strategy_name}' exit: {e}")
                return jsonify({'status': 'strategy_exit_error', 'message': str(e)}), 500
        else:
            return jsonify({'status': 'error', 'message': f'Invalid alert_type for strategy: {alert_type}'}), 400

    # --- Original Logic for Direct Order Execution (if no strategy_name) ---
    elif alert_type == 'entry':
        try:
            option_type = data.get('option_type')
            quantity = data.get('quantity')
            if not option_type or not quantity or not strike_price:
                return jsonify({'status': 'error', 'message': 'Entry alert requires option_type, quantity, and strike_price'}), 400

            expiry = get_nearest_weekly_expiry()
            
            # Define Sell Leg
            sell_strike = strike_price
            sell_instrument = find_instrument_by_strike(kite, sell_strike, option_type, expiry)
            
            # Define Hedge Leg
            config = db.execute('SELECT hedge_offset FROM config').fetchone()
            hedge_offset = config['hedge_offset'] if config else 200 # Default to 200 if not found
            hedge_strike = sell_strike + hedge_offset if option_type == 'CE' else sell_strike - hedge_offset
            hedge_instrument = find_instrument_by_strike(kite, hedge_strike, option_type, expiry)

            # Place Orders
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
            
            # Save Active Trade
            db.execute(
                'INSERT INTO active_trades (strategy_id, strike_price, legs) VALUES (?, ?, ?)',
                (data.get('strategy_id'), strike_price, json.dumps(trade_legs))
            )
            db.commit()

            return jsonify({'status': 'entry_success', 'details': trade_legs})

        except Exception as e:
            logging.error(f"Error during direct trade entry: {e}")
            return jsonify({'status': 'entry_error', 'message': str(e)}), 500

    elif alert_type == 'exit':
        try:
            if not strike_price:
                return jsonify({'status': 'error', 'message': 'Exit alert requires strike_price'}), 400

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
            
            # Remove from Active Trades
            db.execute('DELETE FROM active_trades WHERE id = ?', (trade_to_exit['id'],))
            db.commit()

            return jsonify({'status': 'exit_success', 'details': exit_responses})

        except Exception as e:
            logging.error(f"Error during direct trade exit: {e}")
            return jsonify({'status': 'exit_error', 'message': str(e)}), 500

    else:
        return jsonify({'status': 'error', 'message': f'Invalid alert_type: {alert_type}'}), 400

@api_bp.route('/active_trades', methods=['GET'])
@login_required
def get_active_trades():
    db = get_db()
    active_trades = db.execute('SELECT * FROM active_trades').fetchall()
    return jsonify([dict(row) for row in active_trades])

@api_bp.route('/portfolio', methods=['GET'])
@login_required
def get_portfolio_data():
    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500
    try:
        portfolio = get_current_portfolio(kite)
        return jsonify(portfolio)
    except Exception as e:
        current_app.logger.error(f"Error fetching portfolio data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@api_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500
    try:
        orders = kite.orders()
        return jsonify([dict(order) for order in orders])
    except Exception as e:
        current_app.logger.error(f"Error fetching orders: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/orders/<order_id>/modify', methods=['PUT'])
@login_required
def modify_order(order_id):
    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500
    data = request.json
    try:
        modified_order_id = kite.modify_order(
            variety=data.get('variety', kite.VARIETY_REGULAR),
            order_id=order_id,
            quantity=data.get('quantity'),
            price=data.get('price'),
            trigger_price=data.get('trigger_price')
        )
        return jsonify({'status': 'success', 'message': 'Order modified successfully', 'order_id': modified_order_id})
    except Exception as e:
        current_app.logger.error(f"Error modifying order {order_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/orders/<order_id>/cancel', methods=['DELETE'])
@login_required
def cancel_order(order_id):
    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500
    try:
        cancelled_order_id = kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=order_id)
        return jsonify({'status': 'success', 'message': 'Order cancelled successfully', 'order_id': cancelled_order_id})
    except Exception as e:
        current_app.logger.error(f"Error cancelling order {order_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/trades', methods=['GET'])
@login_required
def get_trades():
    kite = get_kite_instance()
    if not kite:
        return jsonify({'status': 'error', 'message': 'KiteConnect initialization failed'}), 500
    try:
        trades = kite.trades()
        return jsonify([dict(trade) for trade in trades])
    except Exception as e:
        current_app.logger.error(f"Error fetching trades: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/trade_history', methods=['GET'])
@login_required
def get_trade_history():
    db = get_db()
    trade_history = db.execute('SELECT * FROM trade_history ORDER BY exit_time DESC').fetchall()
    return jsonify([dict(row) for row in trade_history])

@api_bp.route('/news', methods=['GET'])
@login_required
def get_news():
    query = request.args.get('query', 'stock market')
    try:
        news_articles = fetch_market_news(query=query)
        return jsonify({'status': 'success', 'articles': news_articles})
    except Exception as e:
        current_app.logger.error(f"Error fetching news: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500