import logging
from kiteconnect import KiteConnect, place_iceberg_order

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Place an Iceberg Order
try:
    order_id = place_iceberg_order(
        kite=kite,
        tradingsymbol="INFY",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=100,  # Total quantity
        product=kite.PRODUCT_CNC,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=1500.00,
        iceberg_legs=5,  # Split into 5 legs
        iceberg_quantity=20, # 20 quantity per leg
    )

    logging.info("Iceberg Order placed. ID is: {}".format(order_id))
except Exception as e:
    logging.info("Iceberg Order placement failed: {}".format(e.message))
