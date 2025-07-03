import logging
from kiteconnect import KiteConnect, place_cover_order

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Place a Cover Order
try:
    order_id = place_cover_order(
        kite=kite,
        tradingsymbol="INFY",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=1,
        product=kite.PRODUCT_MIS,  # Cover orders are typically MIS product type
        order_type=kite.ORDER_TYPE_MARKET,
        trigger_price=1500.00,  # Required for Cover Orders
    )

    logging.info("Cover Order placed. ID is: {}".format(order_id))
except Exception as e:
    logging.info("Cover Order placement failed: {}".format(e.message))
