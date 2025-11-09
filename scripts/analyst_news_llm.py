#!/usr/bin/env python
import sys, pathlib, sqlite3, datetime as dt
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

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
    d = route("news_summary")
    import os
    load_env()
    groq = GroqClient(os.getenv("GROQ_API_KEY"))
    gemi = GeminiClient(os.getenv("GEMINI_API_KEY"))
    prompt = f"Rate sentiment in [-1,1] and a 1-sentence reason. Title: {title}"
    if d.provider == "groq":
        out = groq.summarize(prompt, model=d.model, timeout=10.0)
    else:
        out = gemi.analyze(prompt, model=d.model, timeout=10.0)
    return out.get("status","ERROR"), out.get("output") or out.get("reason") or ""

def parse_llm_score(text: str) -> float:
    t = (text or "").lower()
    import re
    m = re.search(r"(-?\d+(?:\.\d+)?)", t)
    if not m: return 0.0
    try:
        v = float(m.group(1))
        return max(-1.0, min(1.0, v))
    except:
        return 0.0

def run(day: str | None):
    load_env()
    if day is None:
        day = dt.date.today().isoformat()
    con = sqlite3.connect(DB)
    ensure_tables(con)
    cur = con.cursor()
    cur.execute("""
      SELECT id, title, source FROM news
      WHERE published_at IS NULL
         OR date(published_at) BETWEEN date(?,'-1 day') AND date(?,'+1 day')
    """, (day, day))
    rows = cur.fetchall()
    upserts = 0
    for nid, title, source in rows:
        status, content = llm_sentiment(title or "")
        if status != "OK":
            score = score_rule(title or "")
            summary = shorten(title or "", width=160, placeholder="…")
        else:
            score = parse_llm_score(content)
            summary = shorten(content, width=200, placeholder="…")
        cur.execute("DELETE FROM sentiments WHERE news_id=?", (nid,))
        cur.execute("INSERT INTO sentiments(news_id, score, summary) VALUES (?,?,?)", (nid, score, summary))
        upserts += 1
    con.commit(); con.close()
    print({"sentiments_upserted": upserts, "day": day})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=None)
    args = ap.parse_args()
    run(args.day)
