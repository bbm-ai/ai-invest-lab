-- 005_alter_tech_signals.sql — 升級 tech_signals 結構到 v2
-- 目標欄位：rsi_14, macd, macd_signal, macd_hist, trend_label, summary

BEGIN TRANSACTION;

-- 如果當前結構已是新版，就直接結束
-- 檢查是否已有 rsi_14 欄位
-- （SQLite 沒有 IF EXISTS on columns，直接用重建法）

-- 1) 以新版結構建立暫存表
CREATE TABLE IF NOT EXISTS tech_signals_v2 (
  symbol TEXT NOT NULL,
  date   DATE NOT NULL,
  rsi_14 REAL,
  macd REAL,
  macd_signal REAL,
  macd_hist REAL,
  trend_label TEXT,
  summary TEXT,
  PRIMARY KEY(symbol, date)
);

-- 2) 從舊表搬資料（若舊表欄位為 rsi/macd/signal/trend）
--    將 rsi -> rsi_14, signal -> macd_signal, trend -> trend_label
INSERT INTO tech_signals_v2 (symbol, date, rsi_14, macd, macd_signal, macd_hist, trend_label, summary)
SELECT
  symbol,
  date,
  rsi        AS rsi_14,
  macd       AS macd,
  signal     AS macd_signal,
  NULL       AS macd_hist,
  trend      AS trend_label,
  NULL       AS summary
FROM tech_signals;

-- 3) 刪除舊表並改名
DROP TABLE tech_signals;
ALTER TABLE tech_signals_v2 RENAME TO tech_signals;

-- 4) 索引
CREATE INDEX IF NOT EXISTS idx_tech_signals_date ON tech_signals(date);

COMMIT;
