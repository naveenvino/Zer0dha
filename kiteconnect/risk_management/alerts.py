from abc import ABC, abstractmethod
import pandas as pd

class Alert(ABC):
    @abstractmethod
    def check(self, positions: pd.DataFrame):
        pass

class PnLAlert(Alert):
    def __init__(self, threshold: float, callback):
        self.threshold = threshold
        self.callback = callback

    def check(self, positions: pd.DataFrame):
        if not positions.empty:
            total_pnl = positions["pnl"].sum()
            if total_pnl < self.threshold:
                self.callback(total_pnl)
