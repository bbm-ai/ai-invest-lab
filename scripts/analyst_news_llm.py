#!/usr/bin/env python
import sys, pathlib, sqlite3, datetime as dt
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def _as_result(obj):
    if isinstance(obj, dict) and "status" in obj and "content" in obj:
        return obj
    return {"status": "OK", "content": str(obj) if obj is not None else ""}

from textwrap import shorten
from src.utils.env import load_env
from src.api_router import route
from src.llm_clients.groq_client import GroqClient
from src.llm_clients.gemini_client import GeminiClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"

POS = ["surge","rally","beat","beats","soar","soars","rise","rises","gain","gains","pop","pops","jump","jumps"]
NEG = ["plunge","plunges","fall","falls","drop","drops","miss","misses","slump","slumps","slide","slides","tumble","tumbles"]

def score_rule(text: str) -> float:
    t = (text or "").lower()
    pos = sum(1 for w in POS if w in t)
    neg = sum(1 for w in NEG if w in t)
    if pos == neg == 0: return 0.0
    raw = (pos - neg) / max(1, (pos + neg))
    return max(-1.0, min(1.0, raw))

def ensure_tables(con):
    con.execute("""CREATE TABLE IF NOT EXISTS sentiments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      news_id INTEGER, score REAL, summary TEXT,
      FOREIGN KEY (news_id) REFERENCES news(id)
    );""")
    con.commit()

def llm_sentiment(title: str):
    from src.api_router import route
    from src.llm_clients.groq_client import GroqClient
    from src.llm_clients.gemini_client import GeminiClient

    d = route("news_summary")
    prompt = f"Summarize sentiment for news title: {title!r}"

    if d.provider == "gemini":
        gemi = GeminiClient()
        out = gemi.summarize(prompt, model=d.model, timeout=10.0)
    else:
        groq = GroqClient()
        out = groq.summarize(prompt, model=d.model, timeout=10.0)

    res = _as_result(out)
    status = res["status"]
    content = res["content"]
    return status, content