import logging
from kiteconnect import KiteConnect, place_cover_order, modify_cover_order, cancel_advanced_order, cancel_all_orders

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

try:
    # --- Place a Cover Order ---
    logging.info("Placing a Cover Order...")
    co_order_id = place_cover_order(
        kite=kite,
        tradingsymbol="INFY",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=1,
        product=kite.PRODUCT_MIS,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=1500.00,
        trigger_price=1490.00,
        tag="my_co_order"
    )
    logging.info(f"Cover Order placed. ID: {co_order_id}")

    # --- Modify the Cover Order ---
    logging.info(f"Modifying Cover Order {co_order_id}...")
    modified_co_order_id = modify_cover_order(
        kite=kite,
        order_id=co_order_id,
        price=1505.00,
        trigger_price=1495.00,
    )
    logging.info(f"Cover Order modified. New ID (if any): {modified_co_order_id}")

    # --- Place a Bracket Order (example, not actually placed here) ---
    # For demonstration, assume a BO was placed and you have its ID
    # bo_order_id = "BO_ORDER_ID_HERE"

    # --- Cancel a specific advanced order (e.g., the CO) ---
    logging.info(f"Cancelling Cover Order {co_order_id}...")
    cancelled_co_id = cancel_advanced_order(
        kite=kite,
        variety=kite.VARIETY_CO,
        order_id=co_order_id,
    )
    logging.info(f"Cover Order cancelled. ID: {cancelled_co_id}")

    # --- Place a few more orders for bulk cancellation demo ---
    logging.info("Placing a few more orders for bulk cancellation demo...")
    place_cover_order(
        kite=kite,
        tradingsymbol="SBIN",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=1,
        product=kite.PRODUCT_MIS,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=500.00,
        trigger_price=495.00,
        tag="bulk_cancel_1"
    )
    place_cover_order(
        kite=kite,
        tradingsymbol="TCS",
        exchange=kite.EXCHANGE_NSE,
        transaction_type=kite.TRANSACTION_TYPE_SELL,
        quantity=1,
        product=kite.PRODUCT_MIS,
        order_type=kite.ORDER_TYPE_LIMIT,
        price=3500.00,
        trigger_price=3510.00,
        tag="bulk_cancel_2"
    )
    logging.info("Orders placed for bulk cancellation demo.")

    # --- Cancel all pending orders ---
    logging.info("Cancelling all pending orders...")
    cancelled_ids = cancel_all_orders(kite)
    logging.info(f"All pending orders cancelled. IDs: {cancelled_ids}")

except Exception as e:
    logging.error(f"An error occurred during advanced order management: {e.message}")