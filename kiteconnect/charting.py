import pandas as pd
import mplfinance as mpf
from typing import List, Dict

def plot_candlestick_chart(df: pd.DataFrame, title: str = "Candlestick Chart", trades: List[Dict] = None):
    """
    Generates and displays a candlestick chart from historical data.

    :param df: Pandas DataFrame with historical data. Must contain 'Open', 'High', 'Low', 'Close' columns.
               The DataFrame index should be datetime.
    :param title: Title of the chart.
    :param trades: Optional list of trade dictionaries to plot on the chart.
                   Each trade should have 'trade_time', 'action' ('BUY' or 'SELL'), and 'price'.
    """
    # Rename columns to match mplfinance requirements (Open, High, Low, Close)
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    apds = []

    if trades:
        buys = []
        sells = []
        for trade in trades:
            trade_time = pd.to_datetime(trade['trade_time'])
            if trade['action'] == 'BUY':
                buys.append((trade_time, trade['price']))
            elif trade['action'] == 'SELL':
                sells.append((trade_time, trade['price']))

        if buys:
            apds.append(mpf.make_addplot(pd.DataFrame(buys, columns=['date', 'price']).set_index('date'),
                                        type='scatter', marker='^', markersize=100, color='green'))
        if sells:
            apds.append(mpf.make_addplot(pd.DataFrame(sells, columns=['date', 'price']).set_index('date'),
                                        type='scatter', marker='v', markersize=100, color='red'))

    mpf.plot(df, type='candle', style='yahoo', title=title, volume=True, addplot=apds)
