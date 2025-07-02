import logging
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

# Generate a new session using the ``api_secret`` parameter
data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Define the legs of the option spread
spread_legs = [
    {
        "variety": kite.VARIETY_REGULAR,
        "exchange": kite.EXCHANGE_NFO,
        "tradingsymbol": "NIFTY24AUG17450CE",
        "transaction_type": kite.TRANSACTION_TYPE_BUY,
        "quantity": 75,
        "product": kite.PRODUCT_MIS,
        "order_type": kite.ORDER_TYPE_MARKET,
    },
    {
        "variety": kite.VARIETY_REGULAR,
        "exchange": kite.EXCHANGE_NFO,
        "tradingsymbol": "NIFTY24AUG17650CE",
        "transaction_type": kite.TRANSACTION_TYPE_SELL,
        "quantity": 75,
        "product": kite.PRODUCT_MIS,
        "order_type": kite.ORDER_TYPE_MARKET,
    },
]

# Place the option spread
try:
    order_ids = kite.place_spread_order(spread_legs)
    logging.info("Spread order placed: %s", order_ids)
except Exception as e:
    logging.info("Spread order placement failed: %s", e)
