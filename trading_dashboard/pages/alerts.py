import streamlit as st
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.risk_management.dashboard import RiskManagementDashboard
from kiteconnect.risk_management.alerts import PnLAlert

def app():
    st.title("Alerts")

    api_key = st.text_input("API Key")
    api_secret = st.text_input("API Secret", type="password")
    request_token = st.text_input("Request Token")
    pnl_threshold = st.number_input("PnL Threshold", value=-1000)

    if st.button("Start Monitoring"):
        try:
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(request_token, api_secret=api_secret)
            kite.set_access_token(data["access_token"])

            ticker = KiteTicker(api_key, data["access_token"])
            dashboard = RiskManagementDashboard(kite, ticker)

            pnl_alert = PnLAlert(
                threshold=pnl_threshold,
                callback=lambda pnl: st.warning(f"PnL Alert: Total PnL has crossed {pnl}")
            )
            dashboard.add_alert(pnl_alert)

            dashboard.start()
            st.success("Monitoring started.")

        except Exception as e:
            st.error(f"Error: {e}")
