import logging
import datetime
from kiteconnect import KiteConnect, get_historical_data_dataframe

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
    from_date = datetime.datetime.now() - datetime.timedelta(days=7)
    to_date = datetime.datetime.now()
    interval = "minute"

    logging.info("Fetching historical data for the first time (should hit API and save to cache)...")
    df1 = get_historical_data_dataframe(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
        use_cache=True
    )

    logging.info("Historical Data (DataFrame) - First Fetch:")
    logging.info(df1.head())

    logging.info("\nFetching historical data for the second time (should load from cache)...")
    df2 = get_historical_data_dataframe(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
        use_cache=True
    )

    logging.info("Historical Data (DataFrame) - Second Fetch:")
    logging.info(df2.head())

    logging.info("\nFetching historical data without using cache (should hit API)...")
    df3 = get_historical_data_dataframe(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
        use_cache=False
    )

    logging.info("Historical Data (DataFrame) - Without Cache:")
    logging.info(df3.head())

except Exception as e:
    logging.error(f"Failed to fetch historical data: {e.message}")