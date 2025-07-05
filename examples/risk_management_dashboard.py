import logging
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.risk_management.dashboard import RiskManagementDashboard
from kiteconnect.risk_management.alerts import PnLAlert

logging.basicConfig(level=logging.DEBUG)

# --- Initialize KiteConnect and KiteTicker ---
api_key = "your_api_key"
api_secret = "your_api_secret"
request_token = "your_request_token"

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
kite.set_access_token(data["access_token"])

ticker = KiteTicker(api_key, data["access_token"])

# --- Create a RiskManagementDashboard instance ---
dashboard = RiskManagementDashboard(kite, ticker)

# --- Add a P&L alert ---
pnl_alert = PnLAlert(
    threshold=-1000,
    callback=lambda pnl: logging.warning(f"PnL Alert: Total PnL has crossed {pnl}")
)
dashboard.add_alert(pnl_alert)

# --- Start the dashboard ---
dashboard.start()
