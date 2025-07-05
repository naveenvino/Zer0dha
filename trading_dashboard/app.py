import streamlit as st
from pages import portfolio, backtesting, alerts

st.set_page_config(page_title="Trading Dashboard", layout="wide")

PAGES = {
    "Portfolio": portfolio,
    "Backtesting": backtesting,
    "Alerts": alerts,
}

def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    page = PAGES[selection]
    page.app()

if __name__ == "__main__":
    main()
