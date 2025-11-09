#!/usr/bin/env python3
import os, pathlib, sqlite3, time, random

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB   = ROOT / "data" / "ai_invest.sqlite3"
os.environ.setdefault("PYTHONPATH",".")  # 保險

from src.api_router import route, next_best
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient
from src.llm_costs_log import log_call

def call_once(task: str, text: str = "Hello failover"):
    dec = route(task)
    primary = dec.provider
    try:
        if primary == "groq":
            out = GroqClient().summarize(text, route_primary="primary", timeout=2.0)
        else:
            out = GeminiClient().analyze({"task": task, "text": text}, route_primary="primary", timeout=2.0)
        return {"task": task, "provider": primary, "status": out.get("status","OK"), "route": "primary"}
    except Exception as e:
        # failover
        b = next_best(dec)
        try:
            if b.provider == "groq":
                out2 = GroqClient().summarize(text, route_primary="backup", timeout=2.0)
            else:
                out2 = GeminiClient().analyze({"task": task, "text": text}, route_primary="backup", timeout=2.0)
            return {"task": task, "provider": b.provider, "status": out2.get("status","OK"), "route": "backup", "error_primary": str(e)}
        except Exception as e2:
            log_call(task, b.provider, b.model, "ERROR", "backup", str(e2))
            return {"task": task, "provider": b.provider, "status": "ERROR", "route": "backup", "error_primary": str(e), "error_backup": str(e2)}

def run_matrix():
    scenarios = [
        ("none",            {}),
        ("groq_timeout",    {"FAULT_MODE":"groq_timeout"}),
        ("groq_429",        {"FAULT_MODE":"groq_429"}),
        ("gemini_timeout",  {"FAULT_MODE":"gemini_timeout"}),
        ("gemini_dns",      {"FAULT_MODE":"gemini_dns"}),
        ("all_random",      {"FAULT_MODE":"all_random","FAULT_PROB":"0.9"}),
    ]
    tasks = ["news_summary","tech_summary","strategy_synthesis"]
    results = []
    for name, env in scenarios:
        for k,v in env.items(): os.environ[k]=v
        if "FAULT_PROB" not in env: os.environ["FAULT_PROB"]="0.8"
        os.environ.setdefault("FAULT_LATENCY_MS","0")
        # 每情境跑 6 次（每 task *2），以便觀察備援占比
        for _ in range(2):
            for t in tasks:
                results.append({"scenario": name, **call_once(t)})
    return results

def summarize(results):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS _tmp_summary(
        scenario TEXT, route TEXT, status TEXT, n INTEGER
    )""")
    cur.execute("DELETE FROM _tmp_summary")
    from collections import Counter
    cnt = Counter((r["scenario"], r["route"], r["status"]) for r in results)
    rows = []
    for (sc, rt, st), n in sorted(cnt.items()):
        rows.append((sc, rt, st, n))
    cur.executemany("INSERT INTO _tmp_summary VALUES (?,?,?,?)", rows)
    con.commit(); con.close()

if __name__ == "__main__":
    rs = run_matrix()
    summarize(rs)
    print({"ok": True, "runs": len(rs)})
