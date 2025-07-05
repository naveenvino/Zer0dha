from flask import Blueprint, request, jsonify
from kiteconnect import KiteConnect
from kiteconnect.exceptions import TokenException, InputException, GeneralException, GTTMarginException

api_bp = Blueprint('api', __name__)

# This should ideally be stored securely and retrieved from environment variables or a config file
kite = None

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    api_key = data.get('api_key')
    access_token = data.get('access_token')

    if not api_key or not access_token:
        return jsonify({'status': 'error', 'message': 'API Key and Access Token are required'}), 400

    global kite
    try:
        kite = KiteConnect(api_key=api_key, access_token=access_token)
        # You might want to do a test API call here to validate the token
        user_profile = kite.profile()
        return jsonify({'status': 'success', 'message': 'Logged in successfully', 'user': user_profile}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid API Key or Access Token'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/user/profile', methods=['GET'])
def get_user_profile():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    try:
        profile = kite.profile()
        return jsonify({'status': 'success', 'data': profile}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/user/margins', methods=['GET'])
def get_user_margins():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    try:
        margins = kite.margins()
        return jsonify({'status': 'success', 'data': margins}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    try:
        orders = kite.orders()
        return jsonify({'status': 'success', 'data': orders}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/holdings', methods=['GET'])
def get_holdings():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    try:
        holdings = kite.holdings()
        return jsonify({'status': 'success', 'data': holdings}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/instruments', methods=['GET'])
def get_instruments():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    try:
        instruments = kite.instruments()
        return jsonify({'status': 'success', 'data': instruments}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/quote', methods=['GET'])
def get_quote():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    instrument = request.args.get('instrument')
    if not instrument:
        return jsonify({'status': 'error', 'message': 'Instrument is required'}), 400
    try:
        quote = kite.quote(instrument)
        return jsonify({'status': 'success', 'data': quote}), 200
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/place_order', methods=['POST'])
def place_order():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    data = request.get_json()
    try:
        order_id = kite.place_order(**data)
        return jsonify({'status': 'success', 'order_id': order_id}), 200
    except InputException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except GeneralException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/gtt_margins', methods=['POST'])
def get_gtt_margins():
    if not kite:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'status': 'error', 'message': 'Invalid request. Expected a list of GTT orders.'}), 400
    try:
        margins = kite.get_gtt_margins(data)
        return jsonify({'status': 'success', 'data': margins}), 200
    except GTTMarginException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except TokenException:
        return jsonify({'status': 'error', 'message': 'Invalid session. Please login again.'}), 401
    except GeneralException as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
