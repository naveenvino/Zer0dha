import logging
import datetime
import pandas as pd
from kiteconnect import KiteConnect, get_historical_data_dataframe, calculate_sma, calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_stochastic_oscillator, calculate_atr

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
    from_date = datetime.datetime.now() - datetime.timedelta(days=90)
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

        # Calculate 14-period RSI
        df['RSI_14'] = calculate_rsi(df, window=14)
        logging.info("DataFrame with RSI_14:")
        logging.info(df.tail())

        # Calculate MACD
        macd_data = calculate_macd(df)
        df = pd.concat([df, macd_data], axis=1)
        logging.info("DataFrame with MACD:")
        logging.info(df.tail())

        # Calculate Bollinger Bands
        bollinger_bands_data = calculate_bollinger_bands(df)
        df = pd.concat([df, bollinger_bands_data], axis=1)
        logging.info("DataFrame with Bollinger Bands:")
        logging.info(df.tail())

        # Calculate Stochastic Oscillator
        stochastic_data = calculate_stochastic_oscillator(df)
        df = pd.concat([df, stochastic_data], axis=1)
        logging.info("DataFrame with Stochastic Oscillator:")
        logging.info(df.tail())

        # Calculate ATR
        df['ATR_14'] = calculate_atr(df, window=14)
        logging.info("DataFrame with ATR_14:")
        logging.info(df.tail())

    else:
        logging.info("No historical data fetched.")

except Exception as e:
    logging.error(f"Failed to calculate indicators: {e.message}")
