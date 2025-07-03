
import os
import logging
import datetime
import pandas as pd
from kiteconnect import KiteConnect

# Configure logging
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# IMPORTANT: Set these parameters to define what data you want to fetch.

# The expiry date of the options you want to fetch.
# This must be a date in the past.
TARGET_EXPIRY_DATE = datetime.date(2024, 6, 27) # Example: June 27, 2024

# The range of strike prices you are interested in.
STRIKE_PRICE_MIN = 23000
STRIKE_PRICE_MAX = 24000

# The date range for which you want the historical data.
# Typically, this would be the week leading up to the expiry.
FROM_DATE = "2024-06-20 09:15:00"
TO_DATE = "2024-06-27 15:30:00"

# The timeframe for the data.
# Can be 'minute', '3minute', '5minute', '10minute', '15minute', '30minute', '60minute', 'day'.
TIMEFRAME = 'minute'

# Output file name
OUTPUT_CSV_FILE = "historical_options_data.csv"


def initialize_kite():
    """Initialize the Kite Connect client."""
    try:
        api_key = os.environ.get("KITE_API_KEY")
        access_token = os.environ.get("KITE_ACCESS_TOKEN")
        if not api_key or not access_token:
            logging.error("KITE_API_KEY or KITE_ACCESS_TOKEN environment variables not set.")
            return None
        
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        logging.info("Kite Connect client initialized successfully.")
        return kite
    except Exception as e:
        logging.error(f"Error during Kite Connect initialization: {e}")
        return None

def fetch_historical_options_data(kite):
    """Fetches historical data for specified NIFTY options and saves it to a CSV."""
    try:
        # 1. Fetch all NFO instruments
        nfo_instruments = kite.instruments("NFO")
        logging.info(f"Fetched {len(nfo_instruments)} instruments from NFO segment.")

        # 2. Filter for the specific NIFTY options we need
        target_instruments = []
        for inst in nfo_instruments:
            if (
                inst['name'] == 'NIFTY' and
                inst['expiry'].date() == TARGET_EXPIRY_DATE and
                inst['instrument_type'] in ['CE', 'PE'] and
                STRIKE_PRICE_MIN <= inst['strike'] <= STRIKE_PRICE_MAX
            ):
                target_instruments.append(inst)

        if not target_instruments:
            logging.warning("No instruments found for the specified criteria.")
            return

        logging.info(f"Found {len(target_instruments)} matching option contracts.")

        # 3. Fetch historical data for each instrument
        all_data = []
        for inst in target_instruments:
            instrument_token = inst['instrument_token']
            tradingsymbol = inst['tradingsymbol']
            logging.info(f"Fetching data for: {tradingsymbol}")
            
            try:
                records = kite.historical_data(instrument_token, FROM_DATE, TO_DATE, TIMEFRAME)
                df = pd.DataFrame(records)
                if not df.empty:
                    df['tradingsymbol'] = tradingsymbol # Add symbol for identification
                    all_data.append(df)
                else:
                    logging.warning(f"No data returned for {tradingsymbol}")
            except Exception as e:
                logging.error(f"Could not fetch data for {tradingsymbol}: {e}")

        # 4. Combine and save to CSV
        if not all_data:
            logging.warning("No historical data was fetched for any instrument.")
            return

        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv(OUTPUT_CSV_FILE, index=False)
        logging.info(f"Successfully saved data for {len(all_data)} instruments to {OUTPUT_CSV_FILE}")

    except Exception as e:
        logging.error(f"An error occurred during data fetching: {e}")


if __name__ == '__main__':
    kite_client = initialize_kite()
    if kite_client:
        # Before running, make sure you have pandas installed:
        # pip install pandas
        fetch_historical_options_data(kite_client)
