import sqlite3, pathlib, time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"

def ensure_table():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS llm_costs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts            DATETIME DEFAULT CURRENT_TIMESTAMP,
      task_type     TEXT,
      provider      TEXT,
      model         TEXT,
      status        TEXT,
      latency_ms    INTEGER,
      tokens_in     INTEGER,
      tokens_out    INTEGER,
      cost_usd      REAL,
      route_primary TEXT,
      error         TEXT
    );""")
    con.commit(); con.close()

def log_cost(
    *,
    task_type: str,
    provider: str,
    model: str,
    status: str,
    latency_ms: int,
    route_primary: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_usd: float = 0.0,
    error: Optional[str] = None
):
    ensure_table()
    con = sqlite3.connect(DB)
    con.execute("""INSERT INTO llm_costs
        (task_type, provider, model, status, latency_ms, tokens_in, tokens_out, cost_usd, route_primary, error)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (task_type, provider, model, status, latency_ms, tokens_in, tokens_out, cost_usd, route_primary, error))
    con.commit(); con.close()
