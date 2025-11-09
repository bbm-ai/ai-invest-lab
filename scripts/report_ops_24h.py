#!/usr/bin/env python3
import os, sys, sqlite3, pathlib, datetime as dt, statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
OUT = ROOT / "reports" / "day18_ops_24h.md"

def q(con, sql, p=()):
    cur = con.cursor()
    cur.execute(sql, p)
    return cur.fetchall()

def within_24h_clause(col="ts"):
    # 以本機時區（direnv 載入 .env 不影響 SQLite）計算 24h 窗口
    return f"{col} >= datetime('now','-1 day','localtime')"

def main():
    if not DB.exists():
        print(f"[ERR] DB missing: {DB}", file=sys.stderr)
        sys.exit(2)
    ROOT.joinpath("reports").mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB)

    # 1) LLM 成本/路由
    calls = q(con, f"""
      SELECT date(ts,'localtime') as d, provider, status, route_primary, COUNT(*)
      FROM llm_costs
      WHERE {within_24h_clause('ts')}
      GROUP BY d, provider, status, route_primary
      ORDER BY d DESC, provider, status
    """)

    per_provider = q(con, f"""
      SELECT provider, COUNT(*), SUM(status='OK'), SUM(status='ERROR'), SUM(status='SKIP')
      FROM llm_costs
      WHERE {within_24h_clause('ts')}
      GROUP BY provider
      ORDER BY COUNT(*) DESC
    """)

    failovers = q(con, f"""
      SELECT route_primary, COUNT(*)
      FROM llm_costs
      WHERE {within_24h_clause('ts')}
      GROUP BY route_primary
      ORDER BY COUNT(*) DESC
    """)

    errors = q(con, f"""
      SELECT substr(COALESCE(error,''),1,60) AS err, COUNT(*)
      FROM llm_costs
      WHERE {within_24h_clause('ts')} AND status='ERROR'
      GROUP BY err ORDER BY COUNT(*) DESC
    """)

    # 2) 策略產出（最後 24 小時內）
    strat_rows = q(con, f"""
      SELECT date, symbol, recommendation, position_size, confidence
      FROM strategies
      WHERE {within_24h_clause('created_at')}
      ORDER BY date DESC, symbol
    """)
    strat_count = len(strat_rows)

    # 3) 備份檢視（最後 24h 最近 10 筆）
    backups = []
    bdir = ROOT / "backups"
    if bdir.exists():
        for p in sorted(bdir.glob("*.sqlite3.gz"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            mtime = dt.datetime.fromtimestamp(p.stat().st_mtime)
            within = (dt.datetime.now() - mtime) <= dt.timedelta(days=1)
            backups.append((p.name, p.stat().st_size, mtime.isoformat(timespec='seconds'), within))

    # 4) 產出 Markdown
    def tbl(rows, headers):
        out = []
        out.append("| " + " | ".join(headers) + " |")
        out.append("|" + "|".join(["---"]*len(headers)) + "|")
        for r in rows:
            out.append("| " + " | ".join(str(x) for x in r) + " |")
        return "\n".join(out)

    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"# Day 18 — 24h Ops Report\n\n")
        f.write(f"_Generated at: {dt.datetime.now().isoformat(timespec='seconds')}_\n\n")

        f.write("## LLM Routing & Cost (last 24h)\n\n")
        if per_provider:
            f.write(tbl([(p, c, ok, er, sk) for (p, c, ok, er, sk) in per_provider],
                       ["Provider","Calls","OK","ERROR","SKIP"]) + "\n\n")
        else:
            f.write("_No llm_costs rows in last 24h._\n\n")

        f.write("### Route mix\n\n")
        if failovers:
            f.write(tbl(failovers, ["Route","Count"]) + "\n\n")
        else:
            f.write("_No route records._\n\n")

        f.write("### Error samples\n\n")
        if errors:
            f.write(tbl(errors, ["Error(head)","Count"]) + "\n\n")
        else:
            f.write("_No errors._\n\n")

        f.write("## Strategies (last 24h)\n\n")
        f.write(f"Total rows: **{strat_count}**\n\n")
        if strat_rows:
            f.write(tbl(strat_rows[:12], ["Date","Symbol","Rec","Size","Conf"]) + "\n\n")

        f.write("## Backups (latest 10 files)\n\n")
        if backups:
            f.write(tbl(backups, ["File","Bytes","MTime","within_24h"]) + "\n\n")
        else:
            f.write("_No backups directory or files._\n\n")

    print({"report": str(OUT)})
    con.close()

if __name__ == "__main__":
    main()
