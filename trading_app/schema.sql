DROP TABLE IF EXISTS strategies;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS active_trades;

CREATE TABLE strategies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  stop_loss REAL,
  target_profit REAL,
  legs TEXT NOT NULL
);

CREATE TABLE config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_key TEXT,
  api_secret TEXT,
  access_token TEXT,
  paper_trading_mode BOOLEAN DEFAULT 0,
  hedge_offset INTEGER DEFAULT 200
);

CREATE TABLE active_trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  strategy_id INTEGER NOT NULL,
  strike_price REAL NOT NULL,
  legs TEXT NOT NULL,
  entry_time DATETIME DEFAULT CURRENT_TIMESTAMP
);