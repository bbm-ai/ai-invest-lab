#!/usr/bin/env python3
import sqlite3, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
OUT = ROOT / "reports" / "m2_costs_last7d.md"

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""
      SELECT date(ts) as d, provider,
             COUNT(*) as calls,
             SUM(CASE WHEN status='OK' THEN 1 ELSE 0 END) as ok,
             SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) as err,
             SUM(CASE WHEN status='SKIP' THEN 1 ELSE 0 END) as skip
      FROM llm_costs
      WHERE ts >= datetime('now', '-7 day')
      GROUP BY d, provider
      ORDER BY d DESC, provider
    """)
    rows = cur.fetchall()
    con.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("# LLM Routing & Cost (calls) — last 7 days\n\n")
        if not rows:
            f.write("_No data in last 7 days._\n")
            return
        f.write("| Day | Provider | Calls | OK | ERROR | SKIP |\n")
        f.write("|---|---|---:|---:|---:|---:|\n")
        for d, prov, calls, ok, err, skip in rows:
            f.write(f"| {d} | {prov} | {calls} | {ok} | {err} | {skip} |\n")

    print({"report": str(OUT)})

if __name__ == "__main__":
    main()
