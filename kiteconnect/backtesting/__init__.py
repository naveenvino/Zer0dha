from typing import List, Dict, Callable, Tuple, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools

def run_backtest(
    historical_data: List[Dict],
    strategy: Callable[[List[Dict]], List[Dict]],
) -> List[Dict]:
    """
    A basic backtesting function to simulate a trading strategy on historical data.

    :param historical_data: A list of historical data points (e.g., candles).
                            Each data point should be a dictionary with at least 'date', 'open', 'high', 'low', 'close'.
    :param strategy: A callable representing the trading strategy. It should take
                     a list of historical data (up to the current point) and return
                     a list of simulated trades. Each trade should be a dictionary
                     with at least 'date', 'action' ('BUY' or 'SELL'), 'price', 'quantity'.
    :return: A list of simulated trades generated by the strategy.
    """
    simulated_trades = []
    for i in range(len(historical_data)):
        current_data = historical_data[:i+1]
        trades = strategy(current_data)
        simulated_trades.extend(trades)
    return simulated_trades

def calculate_performance_metrics(trades: List[Dict], initial_capital: float = 100000.0) -> Dict:
    """
    Calculates performance metrics for a list of simulated trades.

    :param trades: A list of simulated trades.
    :param initial_capital: The starting capital for the backtest.
    :return: A dictionary of performance metrics.
    """
    if not trades:
        return {
            "total_profit_loss": 0,
            "final_capital": initial_capital,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
        }

    # Convert trades to a DataFrame for easier processing
    df_trades = pd.DataFrame(trades)
    df_trades['date'] = pd.to_datetime(df_trades['date'])
    df_trades = df_trades.sort_values(by='date')

    # Calculate PnL for each trade (simplified: assuming immediate execution at trade price)
    # For a more accurate PnL, you'd need to track positions and actual buy/sell prices.
    df_trades['pnl'] = np.where(
        df_trades['action'] == 'BUY',
        -df_trades['price'] * df_trades['quantity'],
        df_trades['price'] * df_trades['quantity']
    )

    # Calculate cumulative PnL and equity curve
    equity_curve = initial_capital + df_trades['pnl'].cumsum()
    total_profit_loss = equity_curve.iloc[-1] - initial_capital

    # Max Drawdown
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = drawdown.min()

    # Sharpe Ratio (simplified: assuming daily returns and risk-free rate = 0)
    returns = equity_curve.pct_change().dropna()
    sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() != 0 else 0

    # Win Rate and Profit Factor (simplified: assuming each trade is a complete round trip)
    # This needs more sophisticated trade matching for accurate calculation.
    winning_trades = df_trades[df_trades['pnl'] > 0].shape[0]
    losing_trades = df_trades[df_trades['pnl'] < 0].shape[0]
    total_trades = winning_trades + losing_trades

    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    gross_profit = df_trades[df_trades['pnl'] > 0]['pnl'].sum()
    gross_loss = df_trades[df_trades['pnl'] < 0]['pnl'].sum()
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else np.inf

    return {
        "total_profit_loss": total_profit_loss,
        "final_capital": equity_curve.iloc[-1],
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "equity_curve": equity_curve # Return equity curve for plotting
    }

def plot_equity_curve(equity_curve: pd.Series, title: str = "Equity Curve"):
    """
    Plots the equity curve of a backtest.

    :param equity_curve: A Pandas Series representing the equity curve over time.
    :param title: The title of the plot.
    """
    plt.figure(figsize=(10, 6))
    equity_curve.plot(title=title)
    plt.xlabel("Date")
    plt.ylabel("Capital")
    plt.grid(True)
    plt.show()

def optimize_strategy_parameters(
    historical_data: List[Dict],
    strategy_builder: Callable[..., Callable[[List[Dict]], List[Dict]]],
    param_grid: Dict[str, List[Any]],
    metric: str = "total_profit_loss",
    initial_capital: float = 100000.0,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Optimizes strategy parameters by running multiple backtests.

    :param historical_data: Historical data for backtesting.
    :param strategy_builder: A function that takes parameters and returns a strategy callable.
    :param param_grid: A dictionary where keys are parameter names and values are lists of possible values.
    :param metric: The performance metric to optimize for (e.g., "total_profit_loss", "sharpe_ratio").
    :param initial_capital: Initial capital for backtests.
    :return: A tuple containing the best parameters and their corresponding performance metrics.
    """
    best_params = None
    best_metric_value = -np.inf
    best_performance = None

    # Generate all combinations of parameters
    keys = param_grid.keys()
    values = param_grid.values()
    param_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    for params in param_combinations:
        strategy = strategy_builder(**params)
        simulated_trades = run_backtest(historical_data, strategy)
        performance = calculate_performance_metrics(simulated_trades, initial_capital)

        if performance[metric] > best_metric_value:
            best_metric_value = performance[metric]
            best_params = params
            best_performance = performance

    return best_params, best_performance
