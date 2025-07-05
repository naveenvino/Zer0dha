from typing import Any, Callable, Dict, List

def run_backtest(
    historical_data: List[Dict[str, Any]],
    strategy: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Runs a backtest of a trading strategy.

    Args:
        historical_data (List[Dict[str, Any]]): A list of historical data points.
        strategy (Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]): The trading strategy to backtest.

    Returns:
        List[Dict[str, Any]]: A list of simulated trades.
    """
    trades = []
    for i in range(1, len(historical_data)):
        data_so_far = historical_data[:i]
        new_trades = strategy(data_so_far)
        trades.extend(new_trades)
    return trades
