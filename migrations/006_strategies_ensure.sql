CREATE TABLE IF NOT EXISTS strategies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date DATE NOT NULL,
  symbol TEXT NOT NULL,
  recommendation TEXT,
  reasoning TEXT,
  position_size REAL,
  confidence REAL,
  is_executed BOOLEAN DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_strategies_date_symbol ON strategies(date, symbol);
