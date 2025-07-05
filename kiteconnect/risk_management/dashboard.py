import logging
import pandas as pd
from kiteconnect import KiteConnect, KiteTicker

class RiskManagementDashboard:
    def __init__(self, kite: KiteConnect, ticker: KiteTicker):
        self.kite = kite
        self.ticker = ticker
        self.positions = pd.DataFrame()
        self.alerts = []

    def _update_positions(self):
        self.positions = pd.DataFrame(self.kite.positions()["net"])

    def _calculate_pnl(self):
        if not self.positions.empty:
            self.positions["pnl"] = self.positions.apply(
                lambda row: (row["last_price"] - row["average_price"]) * row["quantity"],
                axis=1
            )

    def _check_alerts(self):
        for alert in self.alerts:
            alert.check(self.positions)

    def add_alert(self, alert):
        self.alerts.append(alert)

    def on_tick(self, ws, ticks):
        for tick in ticks:
            if not self.positions.empty:
                self.positions.loc[
                    self.positions["instrument_token"] == tick["instrument_token"],
                    "last_price"
                ] = tick["last_price"]
        self._calculate_pnl()
        self._check_alerts()

    def start(self):
        self._update_positions()
        instrument_tokens = self.positions["instrument_token"].tolist()
        self.ticker.subscribe(instrument_tokens)
        self.ticker.on_tick = self.on_tick
        self.ticker.connect()
