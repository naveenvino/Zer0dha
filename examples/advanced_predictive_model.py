import logging
import datetime
import pandas as pd
from kiteconnect import KiteConnect
from kiteconnect.ml.feature_engineering import create_features
from kiteconnect.ml.model import PredictiveModel

logging.basicConfig(level=logging.DEBUG)

# --- Initialize KiteConnect ---
api_key = "your_api_key"
api_secret = "your_api_secret"
request_token = "your_request_token"

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
kite.set_access_token(data["access_token"])

# --- Fetch historical data ---
instrument_token = 408065  # Example: INFY instrument token
from_date = datetime.datetime.now() - datetime.timedelta(days=365)
to_date = datetime.datetime.now()
interval = "day"

historical_data = kite.historical_data(
    instrument_token=instrument_token,
    from_date=from_date,
    to_date=to_date,
    interval=interval
)

df = pd.DataFrame(historical_data)
df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date")

# --- Create features ---
features_df = create_features(df.copy())

# --- Create target variable ---
features_df["target"] = (features_df["returns"].shift(-1) > 0).astype(int)
features_df.dropna(inplace=True)


# --- Train predictive model ---
model = PredictiveModel()
model.train(features_df[["returns", "sma_5", "sma_20", "rsi"]], features_df["target"])

# --- Make predictions ---
predictions = model.predict(features_df[["returns", "sma_5", "sma_20", "rsi"]])
logging.info(f"Predictions: {predictions}")
