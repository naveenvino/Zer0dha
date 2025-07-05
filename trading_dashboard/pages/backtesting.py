import streamlit as st
import pandas as pd
import datetime
from kiteconnect import KiteConnect
from kiteconnect.backtesting.core import run_backtest
from kiteconnect.backtesting.metrics import calculate_performance_metrics
from kiteconnect.backtesting.visualizer import plot_equity_curve

def simple_moving_average_strategy_builder(short_window, long_window):
    """
    A builder function for the simple moving average crossover strategy.
    Returns a strategy callable that uses the given window periods.
    """
    def strategy(historical_data):
        trades = []
        if len(historical_data) < long_window:
            return trades

        closes = [d["close"] for d in historical_data]
        sma_short = pd.Series(closes).rolling(window=short_window).mean().iloc[-1]
        sma_long = pd.Series(closes).rolling(window=long_window).mean().iloc[-1]

        prev_closes = [d["close"] for d in historical_data[:-1]]
        if len(prev_closes) >= long_window:
            prev_sma_short = pd.Series(prev_closes).rolling(window=short_window).mean().iloc[-1]
            prev_sma_long = pd.Series(prev_closes).rolling(window=long_window).mean().iloc[-1]

            if sma_short > sma_long and prev_sma_short <= prev_sma_long:
                trades.append({
                    "date": historical_data[-1]["date"],
                    "action": "BUY",
                    "price": historical_data[-1]["close"],
                    "quantity": 1
                })
            elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
                trades.append({
                    "date": historical_data[-1]["date"],
                    "action": "SELL",
                    "price": historical_data[-1]["close"],
                    "quantity": 1
                })
        return trades
    return strategy

def app():
    st.title("Backtesting")

    api_key = st.text_input("API Key")
    api_secret = st.text_input("API Secret", type="password")
    request_token = st.text_input("Request Token")
    instrument_token = st.number_input("Instrument Token", value=408065)
    from_date = st.date_input("From Date", datetime.date.today() - datetime.timedelta(days=365))
    to_date = st.date_input("To Date", datetime.date.today())
    short_window = st.slider("Short Window", 5, 50, 5)
    long_window = st.slider("Long Window", 10, 200, 20)

    if st.button("Run Backtest"):
        try:
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(request_token, api_secret=api_secret)
            kite.set_access_token(data["access_token"])

            historical_data = kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval="day"
            )

            strategy = simple_moving_average_strategy_builder(short_window, long_window)
            simulated_trades = run_backtest(historical_data, strategy)
            performance = calculate_performance_metrics(simulated_trades)

            st.subheader("Performance Metrics")
            st.write(performance)

            st.subheader("Equity Curve")
            fig = plot_equity_curve(performance["equity_curve"])
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}")
