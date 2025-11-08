#!/usr/bin/env python
"""
Day 6 helper — 將 data/news/YYYY-MM-DD.jsonl 匯入 SQLite 的 `news` 表
- 去重依 `url_hash UNIQUE`
- 缺少 published_at 時允許 NULL
"""
import json, sys, pathlib, sqlite3, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
NEWS_DIR = ROOT / "data" / "news"

def ensure_tables(con):
    con.execute("""CREATE TABLE IF NOT EXISTS news (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT, source TEXT, url TEXT, url_hash TEXT UNIQUE,
      published_at DATETIME
    );""")
    con.commit()

def import_jsonl(day=None):
    if day is None:
        day = dt.date.today().isoformat()
    fp = NEWS_DIR / f"{day}.jsonl"
    if not fp.exists():
        print("[FATAL] JSONL not found:", fp)
        sys.exit(1)
    con = sqlite3.connect(DB)
    ensure_tables(con)
    cur = con.cursor()
    added = 0; skipped = 0
    with open(fp, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            vals = (
                rec.get("title"),
                rec.get("source"),
                rec.get("url"),
                rec.get("url_hash"),
                rec.get("published_at"),
            )
            try:
                cur.execute(
                    "INSERT INTO news(title,source,url,url_hash,published_at) VALUES (?,?,?,?,?)",
                    vals
                )
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1
                continue
    con.commit()
    con.close()
    print({"added": added, "skipped": skipped, "path": str(fp)})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", help="YYYY-MM-DD, default=today", default=None)
    args = ap.parse_args()
    import_jsonl(args.day)
