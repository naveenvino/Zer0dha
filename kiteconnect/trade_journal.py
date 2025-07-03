import sqlite3
import os
from typing import List, Dict, Any
import pandas as pd

DATABASE_FILE = "trades.db"

def init_db():
    """
    Initializes the SQLite database and creates the trades table if it doesn't exist.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            trade_id TEXT UNIQUE,
            tradingsymbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            trade_time TEXT NOT NULL,
            pnl REAL,
            strategy_tag TEXT
        )
    """
    )
    conn.commit()
    conn.close()

def insert_trade(trade_data: Dict[str, Any]):
    """
    Inserts a single trade record into the database.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trades (order_id, trade_id, tradingsymbol, exchange, transaction_type, quantity, price, trade_time, pnl, strategy_tag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trade_data.get('order_id'),
        trade_data.get('trade_id'),
        trade_data.get('tradingsymbol'),
        trade_data.get('exchange'),
        trade_data.get('transaction_type'),
        trade_data.get('quantity'),
        trade_data.get('price'),
        trade_data.get('trade_time'),
        trade_data.get('pnl'),
        trade_data.get('strategy_tag'),
    ))
    conn.commit()
    conn.close()

def get_all_trades() -> List[Dict[str, Any]]:
    """
    Retrieves all trade records from the database.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trades")
    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

def get_trades_dataframe() -> pd.DataFrame:
    """
    Retrieves all trade records as a Pandas DataFrame.
    """
    trades = get_all_trades()
    df = pd.DataFrame(trades)
    if not df.empty:
        df['trade_time'] = pd.to_datetime(df['trade_time'])
    return df

def analyze_trades(df_trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Performs basic analysis on a DataFrame of trades.
    """
    if df_trades.empty:
        return {"total_trades": 0, "total_pnl": 0, "winning_trades": 0, "losing_trades": 0, "win_rate": 0}

    total_trades = len(df_trades)
    total_pnl = df_trades['pnl'].sum() if 'pnl' in df_trades.columns else 0
    winning_trades = df_trades[df_trades['pnl'] > 0].shape[0] if 'pnl' in df_trades.columns else 0
    losing_trades = df_trades[df_trades['pnl'] < 0].shape[0] if 'pnl' in df_trades.columns else 0
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    return {
        "total_trades": total_trades,
        "total_pnl": total_pnl,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate
    }