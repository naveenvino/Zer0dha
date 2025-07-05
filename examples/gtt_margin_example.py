import logging
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize KiteConnect
kite = KiteConnect(api_key="your_api_key", access_token="your_access_token")

# Example GTT order parameters
gtt_orders = [
    {
        "exchange": "NSE",
        "tradingsymbol": "INFY",
        "transaction_type": "BUY",
        "quantity": 1,
        "price": 1500,
        "order_type": "LIMIT",
        "product": "CNC"
    }
]

try:
    # Get GTT margin details
    margin_details = kite.get_gtt_margins(gtt_orders)
    logging.info("GTT margin details: %s", margin_details)
except Exception as e:
    logging.error(f"Error getting GTT margin details: {e}", exc_info=True)
