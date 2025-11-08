-- 001_init.sql — 初始 Schema（v2.2）
BEGIN;

CREATE TABLE IF NOT EXISTS prices (
  symbol TEXT NOT NULL,
  date   DATE NOT NULL,
  open REAL, high REAL, low REAL, close REAL, volume REAL,
  PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT, source TEXT, url TEXT, url_hash TEXT UNIQUE,
  published_at DATETIME
);

CREATE TABLE IF NOT EXISTS sentiments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  news_id INTEGER, score REAL, summary TEXT,
  FOREIGN KEY (news_id) REFERENCES news(id)
);

CREATE TABLE IF NOT EXISTS tech_signals (
  symbol TEXT NOT NULL, date DATE NOT NULL,
  rsi REAL, macd REAL, signal REAL, trend TEXT,
  PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS strategies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date DATE NOT NULL, symbol TEXT NOT NULL,
  recommendation TEXT, reasoning TEXT,
  position_size REAL, confidence REAL,
  is_executed BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
  ts DATETIME, level TEXT, agent TEXT, event TEXT,
  run_id TEXT, trace_id TEXT, message TEXT, meta TEXT
);

COMMIT;

-- DOWN
-- (No-op for initial schema)
