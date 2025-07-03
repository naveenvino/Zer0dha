import logging
from kiteconnect import KiteConnect, get_current_portfolio

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Get current portfolio (positions and holdings with live value)
try:
    portfolio_data = get_current_portfolio(kite)
    logging.info("Current Portfolio:")
    logging.info("Positions: {}".format(portfolio_data["positions"]))
    logging.info("Holdings: {}".format(portfolio_data["holdings"]))
except Exception as e:
    logging.info("Failed to retrieve portfolio: {}".format(e.message))
