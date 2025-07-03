import logging
import datetime
import pandas as pd
from kiteconnect import KiteConnect, get_historical_data_dataframe, calculate_sma, train_price_prediction_model, predict_price

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
        # Calculate some features for the model
        df['SMA_10'] = calculate_sma(df, window=10)
        df['SMA_20'] = calculate_sma(df, window=20)

        # Drop rows with NaN values created by SMA calculation
        df.dropna(inplace=True)

        if not df.empty:
            features = ['open', 'high', 'low', 'volume', 'SMA_10', 'SMA_20']
            target = 'close'

            # Train the model
            logging.info("Training price prediction model...")
            model = train_price_prediction_model(df, features, target)
            logging.info("Model training complete.")

            # Make a prediction for the last available data point
            last_data_point = df.iloc[[-1]][features]
            predicted_price = predict_price(model, last_data_point)
            logging.info(f"Predicted price for the next period: {predicted_price[0]:.2f}")
        else:
            logging.info("Not enough data after feature engineering to train the model.")

    else:
        logging.info("No historical data fetched to train the model.")

except Exception as e:
    logging.error(f"Failed to run predictive model example: {e.message}")
