import sqlite3
import pandas as pd
import json
import datetime
from typing import Optional, Dict, Any

CACHE_DB = "historical_data_cache.db"

def _init_cache_db():
    """
    Initializes the SQLite database for caching historical data.
    """
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_data (
            instrument_token INTEGER NOT NULL,
            interval TEXT NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            data TEXT NOT NULL,
            PRIMARY KEY (instrument_token, interval, from_date, to_date)
        )
    """
    )
    conn.commit()
    conn.close()

def save_historical_data(instrument_token: int, interval: str, from_date: datetime.datetime, to_date: datetime.datetime, data: pd.DataFrame):
    """
    Saves historical data to the cache database.
    """
    _init_cache_db()
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO historical_data (instrument_token, interval, from_date, to_date, data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            instrument_token,
            interval,
            from_date.isoformat(),
            to_date.isoformat(),
            data.to_json(orient='records')
        ))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving data to cache: {e}")
    finally:
        conn.close()

def load_historical_data(instrument_token: int, interval: str, from_date: datetime.datetime, to_date: datetime.datetime) -> Optional[pd.DataFrame]:
    """
    Loads historical data from the cache database.
    """
    _init_cache_db()
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT data FROM historical_data
            WHERE instrument_token = ? AND interval = ? AND from_date = ? AND to_date = ?
        """, (
            instrument_token,
            interval,
            from_date.isoformat(),
            to_date.isoformat()
        ))
        row = cursor.fetchone()
        if row:
            return pd.read_json(row[0])
    except sqlite3.Error as e:
        print(f"Error loading data from cache: {e}")
    finally:
        conn.close()
    return None
