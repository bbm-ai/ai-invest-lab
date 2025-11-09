-- 004_tech_signals_extend.sql — 擴充 tech_signals 欄位與索引
CREATE TABLE IF NOT EXISTS tech_signals (
  symbol TEXT NOT NULL,
  date   DATE NOT NULL,
  rsi_14 REAL,
  macd REAL,
  macd_signal REAL,
  macd_hist REAL,
  trend_label TEXT,   -- up / down / neutral
  summary TEXT,       -- LLM/規則 產生的技術摘要
  PRIMARY KEY(symbol, date)
);
CREATE INDEX IF NOT EXISTS idx_tech_signals_date ON tech_signals(date);
