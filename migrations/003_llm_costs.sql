-- 003_llm_costs.sql — 記錄每次 LLM 路由與呼叫成本/狀態
CREATE TABLE IF NOT EXISTS llm_costs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            DATETIME DEFAULT CURRENT_TIMESTAMP,
  task_type     TEXT,                 -- news_summary / tech_summary / strategy_synthesis ...
  provider      TEXT,                 -- groq / gemini / (skip)
  model         TEXT,
  status        TEXT,                 -- OK / ERROR / SKIP
  latency_ms    INTEGER,              -- round-trip latency
  tokens_in     INTEGER,              -- 可留 0 或 NULL
  tokens_out    INTEGER,              -- 可留 0 或 NULL
  cost_usd      REAL,                 -- 可留 0 或 NULL
  route_primary TEXT,                 -- primary / backup
  error         TEXT                  -- 失敗時的錯誤訊息或 SKIP 理由
);
