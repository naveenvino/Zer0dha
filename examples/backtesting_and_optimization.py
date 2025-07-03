import logging
from kiteconnect import KiteConnect, run_backtest, calculate_performance_metrics, plot_equity_curve, optimize_strategy_parameters
import datetime
import pandas as pd

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

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

            if sma_short > sma_long and prev_sma_short <= prev_sma_long:  # Golden Cross (Buy Signal)
                trades.append({
                    "date": historical_data[-1]["date"],
                    "action": "BUY",
                    "price": historical_data[-1]["close"],
                    "quantity": 1
                })
            elif sma_short < sma_long and prev_sma_short >= prev_sma_long:  # Death Cross (Sell Signal)
                trades.append({
                    "date": historical_data[-1]["date"],
                    "action": "SELL",
                    "price": historical_data[-1]["close"],
                    "quantity": 1
                })
        return trades
    return strategy

# Fetch historical data (example for INFY, daily interval for 90 days)
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

    # --- Run a single backtest with default parameters ---
    logging.info("\nRunning single backtest with default parameters (SMA 5/20)...")
    default_strategy = simple_moving_average_strategy_builder(5, 20)
    simulated_trades_default = run_backtest(historical_data, default_strategy)
    performance_default = calculate_performance_metrics(simulated_trades_default)
    logging.info("Default Strategy Performance:")
    for metric, value in performance_default.items():
        if metric != "equity_curve":
            logging.info(f"{metric}: {value}")
    if "equity_curve" in performance_default and not performance_default["equity_curve"].empty:
        plot_equity_curve(performance_default["equity_curve"], title="Default SMA Strategy Equity Curve")

    # --- Optimize strategy parameters ---
    logging.info("\nOptimizing SMA strategy parameters...")
    param_grid = {
        'short_window': [5, 10, 15],
        'long_window': [20, 30, 40]
    }
    best_params, best_performance = optimize_strategy_parameters(
        historical_data=historical_data,
        strategy_builder=simple_moving_average_strategy_builder,
        param_grid=param_grid,
        metric="total_profit_loss"
    )

    logging.info("Optimization Complete.")
    if best_params:
        logging.info(f"Best Parameters: {best_params}")
        logging.info("Best Strategy Performance:")
        for metric, value in best_performance.items():
            if metric != "equity_curve":
                logging.info(f"{metric}: {value}")
        if "equity_curve" in best_performance and not best_performance["equity_curve"].empty:
            plot_equity_curve(best_performance["equity_curve"], title="Optimized SMA Strategy Equity Curve")
    else:
        logging.info("No optimal parameters found.")

except Exception as e:
    logging.error(f"Backtesting and optimization failed: {e.message}")
