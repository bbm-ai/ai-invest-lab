#!/usr/bin/env python
import sys, pathlib, sqlite3, datetime as dt
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True, parents=True)

def run(day: str|None):
    if day is None: day = dt.date.today().isoformat()
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT symbol, recommendation, position_size, confidence, substr(reasoning,1,200) FROM strategies WHERE date=? ORDER BY symbol", (day,))
    rows = cur.fetchall(); con.close()

    md = [f"# Daily Strategy — {day}", "", "| Symbol | Rec | Size | Conf | Reasoning |", "|---|---|---:|---:|---|"]
    for sym, rec, size, conf, reason in rows:
        md.append(f"| {sym} | {rec or ''} | {size or 0:.2f} | {conf or 0:.2f} | {reason or ''} |")
    out = "\n".join(md) + "\n"
    (REPORTS / f"strategy_{day}.md").write_text(out, encoding="utf-8")
    print({"report": str(REPORTS / f"strategy_{day}.md"), "rows": len(rows)})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None)
    args = ap.parse_args()
    run(args.day)
