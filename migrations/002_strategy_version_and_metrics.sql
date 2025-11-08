-- 002_strategy_version_and_metrics.sql — add strategy version + metrics table
BEGIN;

-- 1) strategies 加上 version 欄（預設 v1）
ALTER TABLE strategies ADD COLUMN version TEXT DEFAULT 'v1';

-- 2) 新增策略績效彙總表（供 Dashboard 使用）
CREATE TABLE IF NOT EXISTS strategy_metrics (
  date DATE NOT NULL,
  symbol TEXT NOT NULL,
  sharpe_7d REAL,
  sharpe_30d REAL,
  maxdd_30d REAL,
  win_rate_30d REAL,
  PRIMARY KEY (date, symbol)
);

COMMIT;

-- DOWN
-- (SQLite 限制，移除欄位需重建；如需回滾，請建立新表後拷貝資料)
