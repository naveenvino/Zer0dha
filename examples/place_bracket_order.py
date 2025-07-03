import logging
from kiteconnect import KiteConnect, place_bracket_order

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Place a Bracket Order
try:
    order_id = place_bracket_order(
        kite=kite,
        tradingsymbol="INFY",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=1,
        price=1500.00,  # Limit price for the main order
        squareoff=5.0,  # Target profit in points
        stoploss=3.0,   # Stop loss in points
        trailing_stoploss=1.0, # Trailing stop loss in points
    )

    logging.info("Bracket Order placed. ID is: {}".format(order_id))
except Exception as e:
    logging.info("Bracket Order placement failed: {}".format(e.message))
