import streamlit as st
import pandas as pd
from kiteconnect import KiteConnect

def app():
    st.title("Portfolio")

    api_key = st.text_input("API Key")
    api_secret = st.text_input("API Secret", type="password")
    request_token = st.text_input("Request Token")

    if st.button("Get Portfolio"):
        try:
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(request_token, api_secret=api_secret)
            kite.set_access_token(data["access_token"])

            positions = pd.DataFrame(kite.positions()["net"])
            st.dataframe(positions)
        except Exception as e:
            st.error(f"Error: {e}")
