import logging
from kiteconnect import KiteConnect, run_backtest, calculate_performance_metrics, plot_equity_curve
import datetime

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

def simple_moving_average_strategy(historical_data):
    """
    A simple moving average crossover strategy.
    Buys when 5-period SMA crosses above 20-period SMA, sells when it crosses below.
    """
    trades = []
    if len(historical_data) < 20:  # Need at least 20 data points for 20-period SMA
        return trades

    # Calculate SMAs
    closes = [d["close"] for d in historical_data]
    sma_5 = sum(closes[-5:]) / 5
    sma_20 = sum(closes[-20:]) / 20

    # Get previous SMAs for crossover detection
    prev_closes = [d["close"] for d in historical_data[:-1]]
    if len(prev_closes) >= 20:
        prev_sma_5 = sum(prev_closes[-5:]) / 5
        prev_sma_20 = sum(prev_closes[-20:]) / 20

        # Crossover logic
        if sma_5 > sma_20 and prev_sma_5 <= prev_sma_20:  # Golden Cross (Buy Signal)
            trades.append({
                "date": historical_data[-1]["date"],
                "action": "BUY",
                "price": historical_data[-1]["close"],
                "quantity": 1
            })
        elif sma_5 < sma_20 and prev_sma_5 >= prev_sma_20:  # Death Cross (Sell Signal)
            trades.append({
                "date": historical_data[-1]["date"],
                "action": "SELL",
                "price": historical_data[-1]["close"],
                "quantity": 1
            })
    return trades

# Fetch historical data (example for INFY, daily interval for 30 days)
try:
    instrument_token = 408065 # Example: INFY instrument token
    from_date = datetime.datetime.now() - datetime.timedelta(days=90)
    to_date = datetime.datetime.now()
    interval = "day"

    historical_data = kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval
    )

    logging.info("Fetched historical data for INFY.")

    # Run backtest
    simulated_trades = run_backtest(historical_data, simple_moving_average_strategy)

    logging.info("Simulated Trades:")
    for trade in simulated_trades:
        logging.info(trade)

    # Calculate and display performance metrics
    performance_metrics = calculate_performance_metrics(simulated_trades)
    logging.info("\nPerformance Metrics:")
    for metric, value in performance_metrics.items():
        if metric != "equity_curve": # Don't print the equity curve Series directly
            logging.info(f"{metric}: {value}")

    # Plot equity curve
    if "equity_curve" in performance_metrics and not performance_metrics["equity_curve"].empty:
        plot_equity_curve(performance_metrics["equity_curve"], title="SMA Crossover Strategy Equity Curve")

except Exception as e:
    logging.error(f"Backtesting failed: {e.message}")