import pandas as pd

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates features for a predictive model.

    Args:
        df (pd.DataFrame): A pandas DataFrame of historical data.

    Returns:
        pd.DataFrame: A pandas DataFrame with the new features.
    """
    df["returns"] = df["close"].pct_change()
    df["sma_5"] = df["close"].rolling(5).mean()
    df["sma_20"] = df["close"].rolling(20).mean()
    df["rsi"] = _calculate_rsi(df["close"])
    df.dropna(inplace=True)
    return df

def _calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI).
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
