import matplotlib.pyplot as plt
import pandas as pd

def plot_equity_curve(equity_curve: pd.Series, title: str = "Equity Curve"):
    """
    Plots the equity curve.

    Args:
        equity_curve (pd.Series): A pandas Series representing the equity curve.
        title (str, optional): The title of the plot. Defaults to "Equity Curve".
    """
    plt.figure(figsize=(10, 6))
    equity_curve.plot()
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.show()
