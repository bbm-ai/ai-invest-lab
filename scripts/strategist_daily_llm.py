#!/usr/bin/env python
# Day 12+13 — Strategist：先按 APIRouter 推理；若低置信度/衝突→依政策升級到 Claude（含 cap 與總開關）

import sys, pathlib, sqlite3, yaml, datetime as dt, os, json, re
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from textwrap import shorten
from src.utils.env import load_env
from src.api_router import route, escalate_to_claude
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient
from src.llm_clients.claude_client import ClaudeClient
from src.router_policies import should_use_claude
import yaml as _yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
DATA = ROOT / "data"
CONFIG = ROOT / "config.yaml"

def load_cfg():
    if CONFIG.exists():
        return _yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    return {}

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
    rec = "BUY" if score > 0.15 else ("SELL" if score < -0.15 else "HOLD")
    confidence = abs(score)
    pos = round(min(1.0, max(0.0, 0.2 + 0.6*confidence)), 2) if rec != "HOLD" else 0.0
    reasoning = f"Rule-based: RSI={rsi:.1f}, MACD_hist={hist:.3f}, mkt_sent={s_avg:.2f}."
    return rec, reasoning, pos, round(confidence, 2)

def _parse_llm_json(text: str):
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m: return None
    try:
        js = json.loads(m.group(0))
        rec = (js.get("recommendation") or "HOLD").upper()
        reasoning = shorten(js.get("reasoning") or "", width=200, placeholder="…")
        pos = float(js.get("position_size") or 0.0)
        conf = float(js.get("confidence") or 0.0)
        return rec, reasoning, max(0.0, min(1.0, pos)), max(0.0, min(1.0, conf))
    except Exception:
        return None

def llm_strategy(symbol: str, day: str, s_avg: float, tech: dict, provider: str, model: str):
    load_env()
    prompt = (
        f"Today={day}. Symbol={symbol}. "
        f"Inputs: avg_sentiment={s_avg:.2f}, RSI14={tech.get('rsi_14')}, MACD_hist={tech.get('macd_hist')}, trend={tech.get('trend_label')}.\n"
        "Return a concise JSON with keys: recommendation ('BUY'|'SELL'|'HOLD'), reasoning (<=40 words), position_size (0..1), confidence (0..1)."
    )
    if provider == "groq":
        out = GroqClient(os.getenv("GROQ_API_KEY")).summarize(prompt, model=model, timeout=15.0)
    elif provider == "gemini":
        out = GeminiClient(os.getenv("GEMINI_API_KEY")).analyze(prompt, model=model, timeout=15.0)
    else:
        out = ClaudeClient(os.getenv("ANTHROPIC_API_KEY")).analyze(prompt, model=model, timeout=15.0)
    if out.get("status") != "OK":
        return None, out
    parsed = _parse_llm_json(out.get("output",""))
    return parsed, out

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
    cfg = load_cfg()
    enable_claude = bool(cfg.get("router", {}).get("enable_claude", False))
    claude_model = str(cfg.get("router", {}).get("claude_model", "claude-3-5-haiku-latest"))
    min_conf = float(cfg.get("policy", {}).get("min_conf_for_no_escalation", 0.55))
    cap = int(cfg.get("policy", {}).get("daily_claude_call_cap", 3))

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

        d = route("strategy_synthesis")
        res, raw = llm_strategy(sym, day, s_avg, tech, d.provider, d.model)
        escalated = False

        if not res or (res and res[3] < min_conf):  # res[3] = confidence
            use, why = should_use_claude(
                conf=(res[3] if res else 0.0),
                avg_sent=s_avg,
                trend_label=tech.get("trend_label"),
                cap_limit=cap,
                enable=enable_claude
            )
            if use:
                d2 = escalate_to_claude(d, claude_model=claude_model)
                res2, raw2 = llm_strategy(sym, day, s_avg, tech, d2.provider, d2.model)
                if res2: 
                    res = res2
                    escalated = True

        if not res:
            res = fallback_rule(sym, s_avg, tech)

        rec, reasoning, pos, conf = res
        cur = con.cursor()
        cur.execute("DELETE FROM strategies WHERE date=? AND symbol=?", (day, sym))
        cur.execute("""INSERT INTO strategies(date, symbol, recommendation, reasoning, position_size, confidence, is_executed)
                      VALUES (?,?,?,?,?,?,0)""", (day, sym, rec, reasoning, pos, conf))
        upserts += 1
        print({"symbol": sym, "rec": rec, "pos": pos, "conf": conf, "escalated": escalated})
    con.commit(); con.close()
    print({"strategies_upserted": upserts, "day": day})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None)
    args = ap.parse_args()
    run(args.day)
