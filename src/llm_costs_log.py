import sqlite3, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
def log_call(task_type, provider, model, status, route_primary, error=None):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS llm_costs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      task_type TEXT, provider TEXT, model TEXT,
      status TEXT, route_primary TEXT, latency_ms INTEGER DEFAULT 0, error TEXT)""")
    cur.execute("INSERT INTO llm_costs(task_type,provider,model,status,route_primary,error) VALUES (?,?,?,?,?,?)",
                (task_type, provider, model, status, route_primary, error))
    con.commit(); con.close()
