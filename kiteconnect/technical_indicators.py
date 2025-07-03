import pandas as pd
import numpy as np
from collections import deque
from typing import Union, List, Dict

def calculate_sma(data: Union[pd.Series, List[float], deque], window: int) -> float:
    """
    Calculates the Simple Moving Average (SMA) for a given data series.

    :param data: A Pandas Series, list, or deque of numerical data.
    :param window: The rolling window for SMA calculation.
    :return: The latest SMA value.
    """
    if isinstance(data, (list, deque)):
        data = pd.Series(data)
    return data.rolling(window=window).mean().iloc[-1]

def calculate_rsi(data: Union[pd.Series, List[float], deque], window: int = 14) -> float:
    """
    Calculates the Relative Strength Index (RSI) for a given data series.

    :param data: A Pandas Series, list, or deque of numerical data.
    :param window: The rolling window for RSI calculation (default: 14).
    :return: The latest RSI value.
    """
    if isinstance(data, (list, deque)):
        data = pd.Series(data)

    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = 'close') -> Dict[str, float]:
    """
    Calculates the Moving Average Convergence Divergence (MACD) for a given DataFrame.

    :param df: Pandas DataFrame with historical data.
    :param fast_period: The period for the fast EMA (default: 12).
    :param slow_period: The period for the slow EMA (default: 26).
    :param signal_period: The period for the signal line EMA (default: 9).
    :param column: The column to calculate MACD on (default: 'close').
    :return: A dictionary containing the latest MACD, Signal Line, and Histogram values.
    """
    ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal_line

    return {
        'MACD': macd.iloc[-1],
        'Signal_Line': signal_line.iloc[-1],
        'Histogram': histogram.iloc[-1]
    }

def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std_dev: int = 2, column: str = 'close') -> Dict[str, float]:
    """
    Calculates Bollinger Bands for a given DataFrame.

    :param df: Pandas DataFrame with historical data.
    :param window: The rolling window for the moving average (default: 20).
    :param num_std_dev: The number of standard deviations for the upper and lower bands (default: 2).
    :param column: The column to calculate Bollinger Bands on (default: 'close').
    :return: A dictionary containing the latest Middle Band, Upper Band, and Lower Band values.
    """
    middle_band = df[column].rolling(window=window).mean()
    std_dev = df[column].rolling(window=window).std()

    upper_band = middle_band + (std_dev * num_std_dev)
    lower_band = middle_band - (std_dev * num_std_dev)

    return {
        'Middle_Band': middle_band.iloc[-1],
        'Upper_Band': upper_band.iloc[-1],
        'Lower_Band': lower_band.iloc[-1]
    }

def calculate_stochastic_oscillator(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
    """
    Calculates the Stochastic Oscillator (%K and %D) for a given DataFrame.

    :param df: Pandas DataFrame with historical data. Must contain 'high', 'low', and 'close' columns.
    :param k_period: The period for %K calculation (default: 14).
    :param d_period: The period for %D (SMA of %K) calculation (default: 3).
    :return: A dictionary containing the latest %K and %D values.
    """
    lowest_low = df['low'].rolling(window=k_period).min()
    highest_high = df['high'].rolling(window=k_period).max()

    k_percent = ((df['close'] - lowest_low) / (highest_high - lowest_low)) * 100
    d_percent = k_percent.rolling(window=d_period).mean()

    return {
        'K_Percent': k_percent.iloc[-1],
        'D_Percent': d_percent.iloc[-1]
    }

def calculate_atr(df: pd.DataFrame, window: int = 14) -> float:
    """
    Calculates the Average True Range (ATR) for a given DataFrame.

    :param df: Pandas DataFrame with historical data. Must contain 'high', 'low', and 'close' columns.
    :param window: The rolling window for ATR calculation (default: 14).
    :return: The latest ATR value.
    """
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.ewm(com=window - 1, min_periods=window).mean()

    return atr.iloc[-1]
