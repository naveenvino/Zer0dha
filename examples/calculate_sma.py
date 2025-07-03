import logging
import datetime
from kiteconnect import KiteConnect, get_historical_data_dataframe, calculate_sma

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
    instrument_token = 408065 # Example: INFY instrument token
    from_date = datetime.datetime.now() - datetime.timedelta(days=30)
    to_date = datetime.datetime.now()
    interval = "day"

    df = get_historical_data_dataframe(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval
    )

    if not df.empty:
        # Calculate 10-period SMA
        df['SMA_10'] = calculate_sma(df, window=10)
        logging.info("DataFrame with SMA_10:")
        logging.info(df.tail())
    else:
        logging.info("No historical data fetched.")

except Exception as e:
    logging.error(f"Failed to calculate SMA: {e.message}")
