#!/usr/bin/env python
"""
Day 6 helper — 針對當日 `news` 做極輕量情緒分數（無需外部套件）
- 規則：正向/負向關鍵詞計分，score ∈ [-1, 1]
- 將結果寫入 `sentiments(news_id, score, summary)`；同 news_id 先刪後寫（冪等）
"""
import sqlite3, pathlib, datetime as dt
from textwrap import shorten

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"

POS = ["surge","rally","beat","beats","soar","soars","rise","rises","gain","gains","pop","pops","jump","jumps"]
NEG = ["plunge","plunges","fall","falls","drop","drops","miss","misses","slump","slumps","slide","slides","tumble","tumbles"]

def score_text(text: str) -> float:
    t = (text or "").lower()
    pos = sum(1 for w in POS if w in t)
    neg = sum(1 for w in NEG if w in t)
    if pos == neg == 0:
        return 0.0
    raw = (pos - neg) / max(1, (pos + neg))
    return max(-1.0, min(1.0, raw))

def ensure_tables(con):
    con.execute("""CREATE TABLE IF NOT EXISTS sentiments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      news_id INTEGER, score REAL, summary TEXT,
      FOREIGN KEY (news_id) REFERENCES news(id)
    );""")
    con.commit()

def run(day=None):
    con = sqlite3.connect(DB)
    ensure_tables(con)
    cur = con.cursor()
    if day is None:
        day = dt.date.today().isoformat()
    # 取當日新聞（若 published_at 為 NULL，當天匯入的也抓）
    cur.execute("""
    SELECT id, title, source FROM news
    WHERE
        published_at IS NULL
        OR date(published_at) BETWEEN date(?,'-1 day') AND date(?,'+1 day')
    """, (day, day))
    rows = cur.fetchall()
    upserts = 0
    for nid, title, source in rows:
        s = score_text(title or "")
        summ = shorten((title or ""), width=160, placeholder="…")
        # 冪等：先刪後寫
        cur.execute("DELETE FROM sentiments WHERE news_id=?", (nid,))
        cur.execute("INSERT INTO sentiments(news_id, score, summary) VALUES (?,?,?)", (nid, s, summ))
        upserts += 1
    con.commit()
    con.close()
    print({"sentiments_upserted": upserts, "day": day})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", help="YYYY-MM-DD", default=None)
    args = ap.parse_args()
    run(args.day)
