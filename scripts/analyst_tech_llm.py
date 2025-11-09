#!/usr/bin/env python
import sys, pathlib, csv, sqlite3, datetime as dt, yaml
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

def _as_result(obj):
    if isinstance(obj, dict) and "status" in obj and "content" in obj:
        return obj
    return {"status": "OK", "content": str(obj) if obj is not None else ""}

from src.utils.env import load_env
from src.api_router import route
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
DATA = ROOT / "data"

def read_prices_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "date": row["date"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })
    return rows

def ema(values, period):
    k = 2 / (period + 1)
    ema_vals = []
    prev = None
    for v in values:
        if prev is None:
            prev = v
        else:
            prev = v * k + prev * (1 - k)
        ema_vals.append(prev)
    return ema_vals

def rsi(values, period=14):
    gains = [0.0]; losses = [0.0]
    for i in range(1, len(values)):
        diff = values[i] - values[i-1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period if len(gains) >= period else 0.0
    avg_loss = sum(losses[:period]) / period if len(losses) >= period else 0.0
    rsis = [50.0] * len(values)
    for i in range(period, len(values)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = (avg_gain / avg_loss) if avg_loss != 0 else float('inf')
        rsis[i] = 100 - (100 / (1 + rs)) if rs != float('inf') else 100.0
    return rsis

def macd(values, fast=12, slow=26, signal=9):
    ema_fast = ema(values, fast)
    ema_slow = ema(values, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist

def trend_label_from_indicators(rsi_val, hist_val):
    if rsi_val is None or hist_val is None:
        return "neutral"
    if rsi_val > 55 and hist_val > 0:
        return "up"
    if rsi_val < 45 and hist_val < 0:
        return "down"
    return "neutral"

def llm_tech_summary(symbol, rsi_val, macd_hist_val):
    from textwrap import shorten
    d = route("tech_summary")
    prompt = f"Symbol {symbol}. RSI(14)={rsi_val:.1f}, MACD_hist={macd_hist_val:.3f}. Give 1-sentence technical summary with a directional word (up/down/neutral)."
    import os
    load_env()
    groq = GroqClient(os.getenv("GROQ_API_KEY"))
    gemi = GeminiClient(os.getenv("GEMINI_API_KEY"))
    if d.provider == "groq":
        out = groq.summarize(prompt, model=d.model, timeout=10.0)
    else:
        out = gemi.analyze(prompt, model=d.model, timeout=10.0)
    status = out.get("status","ERROR")
    if status != "OK":
        tl = trend_label_from_indicators(rsi_val, macd_hist_val)
        return f"{symbol}: {tl}; RSI={rsi_val:.1f}; MACD_hist={macd_hist_val:.3f} (rule)"
    return shorten(out.get("output",""), width=200, placeholder="…")

def ensure_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS tech_signals (
      symbol TEXT NOT NULL,
      date   DATE NOT NULL,
      rsi_14 REAL,
      macd REAL,
      macd_signal REAL,
      macd_hist REAL,
      trend_label TEXT,
      summary TEXT,
      PRIMARY KEY(symbol, date)
    );""")
    con.commit()

def run(day: str | None):
    load_env()
    if day is None:
        day = dt.date.today().isoformat()
    syspath = DATA / "symbols.yaml"
    if not syspath.exists():
        universe = ["SPY"]
    else:
        import yaml as _yaml
        y = _yaml.safe_load(syspath.read_text(encoding="utf-8"))
        universe = y.get("universe", ["SPY"])

    con = sqlite3.connect(DB); ensure_table(con); cur = con.cursor()
    for sym in universe:
        path = DATA / "prices" / f"{sym}.csv"
        if not path.exists():
            print({"symbol": sym, "error": "price csv missing", "path": str(path)})
            continue
        rows = read_prices_csv(path)
        closes = [r["close"] for r in rows]
        dates  = [r["date"] for r in rows]
        if not closes: continue
        rsi_vals = rsi(closes, 14)
        macd_line, macd_sig, macd_hist = macd(closes, 12, 26, 9)
        if day in dates:
            idx = dates.index(day)
        else:
            idx = len(dates) - 1
        rsi_val = rsi_vals[idx] if idx < len(rsi_vals) else None
        macd_v = macd_line[idx] if idx < len(macd_line) else None
        macd_s = macd_sig[idx] if idx < len(macd_sig) else None
        macd_h = macd_hist[idx] if idx < len(macd_hist) else None
        trend = trend_label_from_indicators(rsi_val, macd_h)
        summary = llm_tech_summary(sym, rsi_val or 0.0, macd_h or 0.0)
        cur.execute("DELETE FROM tech_signals WHERE symbol=? AND date=?", (sym, day))
        cur.execute("INSERT INTO tech_signals(symbol,date,rsi_14,macd,macd_signal,macd_hist,trend_label,summary) VALUES (?,?,?,?,?,?,?,?)",
                    (sym, day, rsi_val, macd_v, macd_s, macd_h, trend, summary))
        print({"symbol": sym, "date": day, "rsi_14": rsi_val, "macd_hist": macd_h, "trend_label": trend})
    con.commit(); con.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None)
    args = ap.parse_args()
    run(args.day)
