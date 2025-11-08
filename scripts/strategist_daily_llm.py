#!/usr/bin/env python
import sys, pathlib, sqlite3, yaml, datetime as dt, os, json, re
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from textwrap import shorten
from src.utils.env import load_env
from src.api_router import route
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
DATA = ROOT / "data"

def avg_sentiment(con, day: str) -> float:
    cur = con.cursor()
    cur.execute("""
      SELECT AVG(score) FROM sentiments s
      JOIN news n ON n.id = s.news_id
      WHERE n.published_at IS NULL
         OR date(n.published_at) BETWEEN date(?,'-1 day') AND date(?,'+1 day')
    """, (day, day))
    row = cur.fetchone()
    return float(row[0]) if row and row[0] is not None else 0.0

def get_tech(con, symbol: str, day: str):
    cur = con.cursor()
    cur.execute("SELECT rsi_14, macd, macd_signal, macd_hist, trend_label, summary FROM tech_signals WHERE symbol=? AND date=?", (symbol, day))
    row = cur.fetchone()
    if not row:
        return None
    keys = ["rsi_14","macd","macd_signal","macd_hist","trend_label","summary"]
    return dict(zip(keys, row))

def fallback_rule(symbol: str, s_avg: float, tech: dict):
    rsi = tech.get("rsi_14") or 50.0
    hist = tech.get("macd_hist") or 0.0
    score = 0.0
    score += (rsi - 50.0)/50.0 * 0.6
    score += (1.0 if hist > 0 else -1.0 if hist < 0 else 0.0) * 0.3
    score += (s_avg) * 0.1
    score = max(-1.0, min(1.0, score))
    if score > 0.15: rec = "BUY"
    elif score < -0.15: rec = "SELL"
    else: rec = "HOLD"
    confidence = abs(score)
    pos = round(min(1.0, max(0.0, 0.2 + 0.6*confidence)), 2) if rec != "HOLD" else 0.0
    reasoning = f"Rule-based: RSI={rsi:.1f}, MACD_hist={hist:.3f}, mkt_sent={s_avg:.2f} → score={score:.2f}."
    return rec, reasoning, pos, round(confidence, 2)

def llm_strategy(symbol: str, day: str, s_avg: float, tech: dict):
    load_env()
    d = route("strategy_synthesis")
    groq = GroqClient(os.getenv("GROQ_API_KEY"))
    gemi = GeminiClient(os.getenv("GEMINI_API_KEY"))
    prompt = (
        f"Today={day}. Symbol={symbol}. Inputs: avg_sentiment={s_avg:.2f}, RSI14={tech.get('rsi_14')}, "
        f"MACD_hist={tech.get('macd_hist')}, trend={tech.get('trend_label')}\n"
        "Return a concise JSON with keys: recommendation ('BUY'|'SELL'|'HOLD'), reasoning (<=40 words), position_size (0..1), confidence (0..1)."
    )
    out = groq.summarize(prompt, model=d.model, timeout=15.0) if d.provider == "groq" else gemi.analyze(prompt, model=d.model, timeout=15.0)
    if out.get("status") != "OK":
        return None
    text = out.get("output","");
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m: return None
    try:
        js = json.loads(m.group(0))
        rec = (js.get("recommendation") or "HOLD").upper()
        reasoning = shorten(js.get("reasoning") or "", width=200, placeholder="…")
        pos = float(js.get("position_size") or 0.0)
        conf = float(js.get("confidence") or 0.0)
        pos = max(0.0, min(1.0, pos)); conf = max(0.0, min(1.0, conf))
        return rec, reasoning, pos, conf
    except Exception:
        return None

def ensure_table(con):
    con.execute("""CREATE TABLE IF NOT EXISTS strategies (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date DATE NOT NULL,
      symbol TEXT NOT NULL,
      recommendation TEXT,
      reasoning TEXT,
      position_size REAL,
      confidence REAL,
      is_executed BOOLEAN DEFAULT 0,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );""")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_strategies_date_symbol ON strategies(date, symbol);")
    con.commit()

def run(day: str|None):
    if day is None:
        day = dt.date.today().isoformat()
    con = sqlite3.connect(DB); ensure_table(con)
    ypath = DATA / "symbols.yaml"
    if not ypath.exists():
        universe = ["SPY"]
    else:
        y = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        universe = y.get("universe", ["SPY"])

    s_avg = avg_sentiment(con, day)
    upserts = 0
    for sym in universe:
        tech = get_tech(con, sym, day)
        if not tech:
            print({"symbol": sym, "day": day, "error": "no tech_signals"})
            continue
        res = llm_strategy(sym, day, s_avg, tech) or fallback_rule(sym, s_avg, tech)
        rec, reasoning, pos, conf = res
        cur = con.cursor()
        cur.execute("DELETE FROM strategies WHERE date=? AND symbol=?", (day, sym))
        cur.execute("""INSERT INTO strategies(date, symbol, recommendation, reasoning, position_size, confidence, is_executed)
                      VALUES (?,?,?,?,?,?,0)""", (day, sym, rec, reasoning, pos, conf))
        upserts += 1
        print({"symbol": sym, "rec": rec, "pos": pos, "conf": conf})
    con.commit(); con.close()
    print({"strategies_upserted": upserts, "day": day})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None)
    args = ap.parse_args()
    run(args.day)
