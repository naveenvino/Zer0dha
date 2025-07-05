from typing import Any, Dict, List
import pandas as pd

def calculate_performance_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates performance metrics for a set of trades.

    Args:
        trades (List[Dict[str, Any]]): A list of trades.

    Returns:
        Dict[str, Any]: A dictionary of performance metrics.
    """
    if not trades:
        return {
            "total_trades": 0,
            "total_profit_loss": 0,
            "equity_curve": pd.Series()
        }

    trades_df = pd.DataFrame(trades)
    trades_df["date"] = pd.to_datetime(trades_df["date"])
    trades_df = trades_df.set_index("date")

    trades_df["pnl"] = trades_df.apply(
        lambda row: row["price"] * row["quantity"] if row["action"] == "SELL" else -row["price"] * row["quantity"],
        axis=1
    )

    equity_curve = trades_df["pnl"].cumsum()

    return {
        "total_trades": len(trades_df),
        "total_profit_loss": trades_df["pnl"].sum(),
        "equity_curve": equity_curve
    }
