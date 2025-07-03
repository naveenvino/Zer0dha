DROP TABLE IF EXISTS strategies;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS active_trades;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS trade_history;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE strategies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  stop_loss REAL,
  target_profit REAL,
  legs TEXT NOT NULL,
  parameters TEXT
);

CREATE TABLE config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_key TEXT,
  api_secret TEXT,
  access_token TEXT,
  paper_trading_mode BOOLEAN DEFAULT 0,
  hedge_offset INTEGER DEFAULT 200,
  email_notifications_enabled BOOLEAN DEFAULT 0,
  email_recipients TEXT,
  smtp_server TEXT,
  smtp_port INTEGER,
  smtp_username TEXT,
  smtp_password TEXT
);

CREATE TABLE active_trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  strategy_id INTEGER,
  strategy_name TEXT,
  strike_price REAL,
  legs TEXT NOT NULL,
  entry_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trade_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  strategy_id INTEGER,
  strategy_name TEXT,
  entry_time DATETIME NOT NULL,
  exit_time DATETIME NOT NULL,
  entry_legs_data TEXT NOT NULL,
  exit_legs_data TEXT NOT NULL,
  total_pnl REAL,
  status TEXT NOT NULL
);