from typing import List, Dict, Union
import datetime
import pandas as pd
from kiteconnect import KiteConnect
from kiteconnect.error_handling import DataFetchError
from kiteconnect.data_cache import save_historical_data, load_historical_data

def get_historical_data_dataframe(
    kite: KiteConnect,
    instrument_token: int,
    from_date: Union[str, datetime.datetime],
    to_date: Union[str, datetime.datetime],
    interval: str,
    continuous: bool = False,
    oi: bool = False,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetches historical data for a given instrument and returns it as a Pandas DataFrame.
    Optionally uses a cache to store and retrieve data.

    :param kite: An initialized KiteConnect object.
    :param instrument_token: The instrument identifier (retrieved from the instruments() call).
    :param from_date: The start date (datetime object or string in format of yyyy-mm-dd HH:MM:SS).
    :param to_date: The end date (datetime object or string in format of yyyy-mm-dd HH:MM:SS).
    :param interval: The candle interval (minute, day, 5 minute etc.).
    :param continuous: A boolean flag to get continuous data for futures and options instruments.
    :param oi: A boolean flag to get open interest.
    :param use_cache: If True, attempts to load from cache and saves to cache after fetching.
    :return: A Pandas DataFrame containing the historical data.
    """
    # Ensure from_date and to_date are datetime objects for consistent caching keys
    if isinstance(from_date, str):
        from_date = datetime.datetime.fromisoformat(from_date)
    if isinstance(to_date, str):
        to_date = datetime.datetime.fromisoformat(to_date)

    df = None
    if use_cache:
        df = load_historical_data(instrument_token, interval, from_date, to_date)
        if df is not None:
            print(f"Loaded historical data for {instrument_token} from cache.")
            return df

    try:
        data = kite.historical_data(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
            continuous=continuous,
            oi=oi,
        )
    except Exception as e:
        raise DataFetchError(f"Failed to fetch historical data for instrument {instrument_token}", original_exception=e)

    df = pd.DataFrame(data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        if use_cache:
            save_historical_data(instrument_token, interval, from_date, to_date, df)
            print(f"Saved historical data for {instrument_token} to cache.")

    return df