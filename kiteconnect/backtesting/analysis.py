from typing import Any, Callable, Dict, List
import pandas as pd
from .core import run_backtest
from .optimizer import optimize_strategy_parameters

def walk_forward_analysis(
    historical_data: pd.DataFrame,
    strategy_builder: Callable[..., Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]],
    param_grid: Dict[str, List[Any]],
    train_period: int,
    test_period: int,
    metric: str = "total_profit_loss"
) -> List[Dict[str, Any]]:
    """
    Performs walk-forward analysis.

    Args:
        historical_data (pd.DataFrame): A pandas DataFrame of historical data.
        strategy_builder (Callable[..., Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]]): A function that builds a strategy.
        param_grid (Dict[str, List[Any]]): A dictionary of parameter grids to search.
        train_period (int): The length of the training period.
        test_period (int): The length of the testing period.
        metric (str, optional): The metric to optimize for. Defaults to "total_profit_loss".

    Returns:
        List[Dict[str, Any]]: A list of performance results for each test period.
    """
    results = []
    for i in range(train_period, len(historical_data) - test_period, test_period):
        train_data = historical_data.iloc[i - train_period:i].to_dict("records")
        test_data = historical_data.iloc[i:i + test_period].to_dict("records")

        best_params, _ = optimize_strategy_parameters(
            historical_data=train_data,
            strategy_builder=strategy_builder,
            param_grid=param_grid,
            metric=metric
        )

        strategy = strategy_builder(**best_params)
        simulated_trades = run_backtest(test_data, strategy)
        performance = calculate_performance_metrics(simulated_trades)
        results.append(performance)

    return results
