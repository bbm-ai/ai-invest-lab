#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, sqlite3, pathlib, argparse, datetime as dt
from typing import Tuple, Optional, Dict, Any

# --- bootstrap: 將專案根加入 sys.path，確保可以 import src.*
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in map(str, sys.path):
    sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "ai_invest.sqlite3"
CFG = ROOT / "config.yaml"

# ---- optional deps (不強制) ----
try:
    from ruamel.yaml import YAML
    _yaml_loader = "ruamel"
except Exception:
    import yaml as YAML  # type: ignore
    _yaml_loader = "pyyaml"

# ---- internal modules ----
from src.api_router import route, escalate_to_claude
from src.router_policies import should_use_claude

# llm cost log 非必需；存在才用
try:
    from src.llm_costs_log import log_call
except Exception:
    def log_call(*args, **kwargs):
        pass


def read_cfg() -> Dict[str, Any]:
    """讀取 config.yaml；缺檔時給預設值"""
    if not CFG.exists():
        return {
            "router": {"enable_claude": False},
            "policy": {
                "min_conf_for_no_escalation": 0.55,
                "sentiment_extreme": 0.40,
                "daily_claude_call_cap": 3,
            },
        }
    if _yaml_loader == "ruamel":
        y = YAML()
        return y.load(CFG.read_text(encoding="utf-8")) or {}
    else:
        return YAML.safe_load(CFG.read_text(encoding="utf-8")) or {}


def q(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    cur = con.cursor()
    cur.execute(sql, params)
    return cur.fetchall()


def upsert_strategy(con: sqlite3.Connection, d: Dict[str, Any]) -> None:
    """策略 upsert 到 strategies：(date, symbol) 為唯一鍵"""
    cur = con.cursor()
    cur.execute(
        """
    INSERT INTO strategies(date, symbol, recommendation, reasoning, position_size, confidence, is_executed)
    VALUES(?,?,?,?,?,?,COALESCE(?,0))
    ON CONFLICT(date, symbol) DO UPDATE SET
      recommendation=excluded.recommendation,
      reasoning=excluded.reasoning,
      position_size=excluded.position_size,
      confidence=excluded.confidence
    """,
        (
            d["date"],
            d["symbol"],
            d["rec"],
            d.get("reason", ""),
            d["pos"],
            d["conf"],
            d.get("is_executed", 0),
        ),
    )
    con.commit()


def simple_primary_decision(sent_avg: float, tech: Dict[str, Any]) -> Tuple[str, float, float, str]:
    """極簡規則法 primary 決策 → (rec,pos,conf,reason)"""
    rsi = float(tech.get("rsi_14") or 50.0)
    hist = float(tech.get("macd_hist") or 0.0)
    trend = (tech.get("trend_label") or "neutral").lower()

    bias = 0.0
    if sent_avg > 0.2:
        bias += 0.1
    if sent_avg < -0.2:
        bias -= 0.1
    if hist > 0:
        bias += 0.1
    if hist < 0:
        bias -= 0.1
    if trend == "up":
        bias += 0.1
    if trend == "down":
        bias -= 0.1

    if rsi > 65 and bias > 0.15:
        rec, pos = "BUY", min(1.0, 0.5 + bias)
    elif rsi < 35 and bias < -0.15:
        rec, pos = "SELL", min(1.0, 0.5 + abs(bias))
    else:
        rec, pos = "HOLD", 0.0

    conf = 0.55 + abs(bias) * 0.4
    reason = (
        f"rule-based | rsi={rsi:.2f} macd_hist={hist:.2f} trend={trend} "
        f"sent_avg={sent_avg:.2f} bias={bias:.2f}"
    )
    return rec, round(pos, 2), round(min(conf, 0.99), 2), reason


def llm_strategy(task: str, text: str, provider: str, model: str, timeout: float = 20.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    薄版 LLM 呼叫；無金鑰則回 SKIP，不丟例外。
    回傳 (parsed, raw)，demo 版預設不真的打 Claude（避免配額風險）。
    """
    raw = {"status": "SKIP", "provider": provider, "model": model, "error": None}
    try:
        if provider == "claude":
            import anthropic  # 需要你已 pip install anthropic
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raw["error"] = "ANTHROPIC_API_KEY missing"
                return {}, raw
            # Demo：不真的呼叫，避免配額與長延遲；若要真打，請在此加入 messages.create 並解析
            raw["status"] = "SKIP"
            raw["error"] = "demo: not calling Claude by default"
            return {}, raw
        elif provider == "groq":
            key = os.getenv("GROQ_API_KEY")
            if not key:
                raw["error"] = "GROQ_API_KEY missing"
                return {}, raw
            raw["status"] = "OK"
            return {}, raw
        elif provider == "gemini":
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raw["error"] = "GEMINI_API_KEY missing"
                return {}, raw
            raw["status"] = "OK"
            return {}, raw
        else:
            raw["error"] = f"unknown provider {provider}"
            return {}, raw
    except Exception as e:
        raw["status"] = "ERROR"
        raw["error"] = str(e)
        return {}, raw


def get_symbols(con: sqlite3.Connection) -> list:
    rows = q(con, "SELECT DISTINCT symbol FROM tech_signals ORDER BY symbol")
    return [r[0] for r in rows] or ["SPY"]


def get_sentiment_avg(con: sqlite3.Connection, day: str) -> float:
    """
    有些環境 sentiments 無 created_at 欄位；改用 news.published_at 來對齊「哪一天」。
    若 published_at 為 NULL，fallback 以目標日作為該筆新聞日期，避免漏計。
    """
    r = q(
        con,
        """
        SELECT AVG(s.score)
        FROM sentiments s
        LEFT JOIN news n ON n.id = s.news_id
        WHERE date(COALESCE(n.published_at, ?)) = date(?)
        """,
        (day, day),
    )
    val = r[0][0]
    return float(val) if val is not None else 0.0


def get_tech(con: sqlite3.Connection, sym: str, day: str) -> Dict[str, Any]:
    r = q(
        con,
        """
        SELECT rsi_14, macd_hist, trend_label
        FROM tech_signals WHERE symbol=? AND date=?
        """,
        (sym, day),
    )
    if not r:
        return {"rsi_14": None, "macd_hist": None, "trend_label": "neutral"}
    rsi, hist, tl = r[0]
    return {"rsi_14": rsi, "macd_hist": hist, "trend_label": tl}


def run(day: str) -> None:
    cfg = read_cfg()
    enable_claude = bool(cfg.get("router", {}).get("enable_claude", False))
    min_conf = float(cfg.get("policy", {}).get("min_conf_for_no_escalation", 0.55))
    sent_ext = float(cfg.get("policy", {}).get("sentiment_extreme", 0.40))
    cap = int(cfg.get("policy", {}).get("daily_claude_call_cap", 3))

    print(
        {
            "DEBUG_POLICY": True,
            "enable_claude": enable_claude,
            "min_conf": min_conf,
            "sent_ext": sent_ext,
            "cap": cap,
        }
    )

    con = sqlite3.connect(DB)
    s_avg = get_sentiment_avg(con, day)
    symbols = get_symbols(con)

    for sym in symbols:
        tech = get_tech(con, sym, day)

        # ---- primary 決策（先用規則法，或可替換為 LLM）----
        rec, pos, conf, reason = simple_primary_decision(s_avg, tech)
        d = route("strategy_synthesis")
        # 記 primary 呼叫（即使是規則法，也記一筆 OK）
        log_call("strategy_synthesis", d.provider, d.model, "OK", "primary", None)

        escalated = False
        escalated_attempt = False

        # 判斷 0：理論上沒有 primary 時以 conf=0.0 測（保持與你原設計一致）
        _use0, _why0 = should_use_claude(
            conf=0.0,
            avg_sent=s_avg,
            trend_label=tech.get("trend_label"),
            cap_limit=cap,
            enable=enable_claude,
            min_conf=min_conf,
            sent_ext=sent_ext,
        )

        # 判斷 1：用實際 conf 測政策（真正生效）
        use, why = should_use_claude(
            conf=conf,
            avg_sent=s_avg,
            trend_label=tech.get("trend_label"),
            cap_limit=cap,
            enable=enable_claude,
            min_conf=min_conf,
            sent_ext=sent_ext,
        )

        if use:
            escalated_attempt = True
            d2 = escalate_to_claude(d, claude_model="claude-3-5-haiku-latest")
            # 這裡示範 LLM 呼叫（預設不真的打，回 SKIP）
            _, raw2 = llm_strategy(
                "strategy_synthesis", f"{sym} daily context", d2.provider, d2.model
            )
            log_call(
                "strategy_synthesis",
                d2.provider,
                d2.model,
                raw2.get("status", "ERROR"),
                "escalated",
                raw2.get("error"),
            )
            if raw2.get("status") == "OK":
                escalated = True
                reason = (reason + " | escalated by claude").strip()

        # upsert -> strategies
        row = {
            "date": day,
            "symbol": sym,
            "rec": rec,
            "pos": pos,
            "conf": conf,
            "reason": reason,
        }
        upsert_strategy(
            con,
            {
                "date": row["date"],
                "symbol": row["symbol"],
                "rec": row["rec"],
                "reason": row["reason"],
                "pos": row["pos"],
                "conf": row["conf"],
            },
        )
        print(
            {
                "symbol": sym,
                "rec": rec,
                "pos": row["pos"],
                "conf": row["conf"],
                "escalated": escalated,
                "escalated_attempt": escalated_attempt,
            }
        )

    con.close()
    print({"strategies_upserted": len(symbols), "day": day})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=dt.date.today().isoformat())
    args = ap.parse_args()
    run(args.day)
