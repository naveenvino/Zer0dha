from typing import Any, Callable, Dict, List, Tuple
import pandas as pd
from .core import run_backtest
from .metrics import calculate_performance_metrics

def optimize_strategy_parameters(
    historical_data: List[Dict[str, Any]],
    strategy_builder: Callable[..., Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]],
    param_grid: Dict[str, List[Any]],
    metric: str = "total_profit_loss"
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Optimizes strategy parameters using grid search.

    Args:
        historical_data (List[Dict[str, Any]]): A list of historical data points.
        strategy_builder (Callable[..., Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]]): A function that builds a strategy.
        param_grid (Dict[str, List[Any]]): A dictionary of parameter grids to search.
        metric (str, optional): The metric to optimize for. Defaults to "total_profit_loss".

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing the best parameters and the best performance.
    """
    best_params = None
    best_performance = None

    from sklearn.model_selection import ParameterGrid
    for params in ParameterGrid(param_grid):
        strategy = strategy_builder(**params)
        simulated_trades = run_backtest(historical_data, strategy)
        performance = calculate_performance_metrics(simulated_trades)

        if best_performance is None or performance[metric] > best_performance[metric]:
            best_performance = performance
            best_params = params

    return best_params, best_performance
