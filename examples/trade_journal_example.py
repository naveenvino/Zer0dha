import logging
import datetime
from kiteconnect import init_db, insert_trade, get_all_trades, analyze_trades, get_trades_dataframe

logging.basicConfig(level=logging.INFO)

# Initialize the database
init_db()
logging.info("Trade journal database initialized.")

# Example trade data
example_trades = [
    {
        "order_id": "ORDER123",
        "trade_id": "TRADE001",
        "tradingsymbol": "INFY",
        "exchange": "NSE",
        "transaction_type": "BUY",
        "quantity": 10,
        "price": 1500.00,
        "trade_time": datetime.datetime.now().isoformat(),
        "pnl": -50.00, # Example PnL
        "strategy_tag": "SMA_Crossover"
    },
    {
        "order_id": "ORDER123",
        "trade_id": "TRADE002",
        "tradingsymbol": "INFY",
        "exchange": "NSE",
        "transaction_type": "SELL",
        "quantity": 10,
        "price": 1495.00,
        "trade_time": datetime.datetime.now().isoformat(),
        "pnl": -50.00, # Example PnL
        "strategy_tag": "SMA_Crossover"
    },
    {
        "order_id": "ORDER456",
        "trade_id": "TRADE003",
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
        "transaction_type": "BUY",
        "quantity": 5,
        "price": 2500.00,
        "trade_time": datetime.datetime.now().isoformat(),
        "pnl": 100.00, # Example PnL
        "strategy_tag": "Breakout"
    },
    {
        "order_id": "ORDER456",
        "trade_id": "TRADE004",
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
        "transaction_type": "SELL",
        "quantity": 5,
        "price": 2520.00,
        "trade_time": datetime.datetime.now().isoformat(),
        "pnl": 100.00, # Example PnL
        "strategy_tag": "Breakout"
    },
]

# Insert example trades
for trade in example_trades:
    try:
        insert_trade(trade)
        logging.info(f"Inserted trade: {trade['trade_id']}")
    except Exception as e:
        logging.error(f"Error inserting trade {trade['trade_id']}: {e}")

# Retrieve all trades
all_trades = get_all_trades()
logging.info("\nAll recorded trades:")
for trade in all_trades:
    logging.info(trade)

# Get trades as DataFrame and analyze
df_trades = get_trades_dataframe()
logging.info("\nTrades DataFrame head:")
logging.info(df_trades.head())

analysis_results = analyze_trades(df_trades)
logging.info("\nTrade Analysis Results:")
for key, value in analysis_results.items():
    logging.info(f"{key}: {value}")
