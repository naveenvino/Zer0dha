import logging
from kiteconnect import KiteConnect, get_current_portfolio, set_stop_loss, set_target_profit

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
    # Get current positions
    portfolio_data = kite.positions()
    live_positions = portfolio_data["day"] + portfolio_data["overnight"]

    if not live_positions:
        logging.info("No live positions found to set risk management orders.")
    else:
        for position in live_positions:
            tradingsymbol = position['tradingsymbol']
            exchange = position['exchange']
            quantity = position['quantity']

            logging.info(f"Attempting to set risk management orders for {tradingsymbol} ({quantity} quantity)...")

            # Set a stop-loss order (e.g., 1% below current LTP)
            try:
                sl_order_id = set_stop_loss(
                    kite=kite,
                    position=position,
                    stop_loss_percentage=1.0, # 1% stop loss
                    tag=f"SL-{tradingsymbol}"
                )
                logging.info(f"Stop-loss order placed for {tradingsymbol}. Order ID: {sl_order_id}")
            except Exception as e:
                logging.error(f"Failed to place stop-loss order for {tradingsymbol}: {e.message}")

            # Set a target profit order (e.g., 2% above current LTP)
            try:
                tp_order_id = set_target_profit(
                    kite=kite,
                    position=position,
                    target_profit_percentage=2.0, # 2% target profit
                    tag=f"TP-{tradingsymbol}"
                )
                logging.info(f"Target profit order placed for {tradingsymbol}. Order ID: {tp_order_id}")
            except Exception as e:
                logging.error(f"Failed to place target profit order for {tradingsymbol}: {e.message}")

except Exception as e:
    logging.error(f"An error occurred: {e.message}")
