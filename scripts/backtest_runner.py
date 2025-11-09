# scripts/backtest_runner.py
#!/usr/bin/env python3
import sys, os, sqlite3, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
# 先把專案根與 src 加進 sys.path，之後再做 import
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.backtester import load_prices_csv, equity_curve, simple_stats  # ← 修正重點

DB = ROOT / "data" / "ai_invest.sqlite3"
DATA = ROOT / "data" / "prices"
OUT = ROOT / "reports" / "backtest_readout.md"

MAP_POS = {"BUY": +1.0, "SELL": -1.0, "HOLD": 0.0}

def latest_strategy_day(con):
    cur = con.cursor()
    cur.execute("SELECT MAX(date) FROM strategies")
    return cur.fetchone()[0]

def backtest_one(symbol: str, position: float):
    path = DATA / f"{symbol}.csv"
    if not path.exists():
        return symbol, {"error": f"missing {path.name}"}
    px = load_prices_csv(path)
    if len(px) < 30:
        return symbol, {"error": "too few bars"}
    eq = equity_curve(px, position=position)
    st = simple_stats(eq)
    return symbol, {"final": st["final"], "maxdd": st["maxdd"], "sharpe": st["sharpe"], "bars": len(px)}

def main():
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    if not DB.exists():
        print({"error": f"DB missing: {DB}"})
        raise SystemExit(2)
    con = sqlite3.connect(DB)

    day = latest_strategy_day(con)
    cur = con.cursor()
    cur.execute("""
      SELECT symbol, recommendation, position_size
      FROM strategies WHERE date=date(?)
      ORDER BY symbol
    """, (day,))
    rows = cur.fetchall()

    lines = [f"# Backtest Readout — based on strategies of {day}", ""]
    lines += ["| Symbol | Pos | Final | MaxDD | Sharpe | Bars |",
              "|---|---:|---:|---:|---:|---:|"]

    for sym, rec, pos in rows:
        pos = MAP_POS.get(rec.upper(), 0.0) if (pos is None) else float(pos)
        sym, st = backtest_one(sym, position=pos)
        if "error" in st:
            lines.append(f"| {sym} | {pos:.2f} | - | - | - | - |")
        else:
            lines.append(f"| {sym} | {pos:.2f} | {st['final']:.4f} | {st['maxdd']:.3f} | {st['sharpe']:.3f} | {st['bars']} |")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print({"report": str(OUT), "day": day, "rows": len(rows)})

if __name__ == "__main__":
    main()
