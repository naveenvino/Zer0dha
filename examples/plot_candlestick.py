import logging
import datetime
from kiteconnect import KiteConnect, get_historical_data_dataframe, plot_candlestick_chart, init_db, insert_trade, get_all_trades

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Initialize the database for trade journaling
init_db()

try:
    instrument_token = 408065 # Example: INFY instrument token
    from_date = datetime.datetime.now() - datetime.timedelta(days=30)
    to_date = datetime.datetime.now()
    interval = "day"

    df = get_historical_data_dataframe(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval
    )

    if not df.empty:
        logging.info("Generating candlestick chart...")

        # Example trades to plot (replace with actual trades from your journal)
        example_trades = [
            {
                "trade_time": (datetime.datetime.now() - datetime.timedelta(days=20)).isoformat(),
                "action": "BUY",
                "price": df['close'].iloc[-20] # Example price
            },
            {
                "trade_time": (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat(),
                "action": "SELL",
                "price": df['close'].iloc[-10] # Example price
            },
        ]

        plot_candlestick_chart(df, title=f"Candlestick Chart for INFY ({interval}) with Trades", trades=example_trades)
    else:
        logging.info("No historical data fetched to plot.")

except Exception as e:
    logging.error(f"Failed to plot candlestick chart: {e.message}")
