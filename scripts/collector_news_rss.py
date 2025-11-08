#!/usr/bin/env python
"""
Day 5 — Data Collector (II): 新聞 RSS 收集（免金鑰；先產 JSONL，不入庫）

輸出：data/news/YYYY-MM-DD.jsonl
欄位：title, source, url, url_hash, published_at(ISO), symbols[]
"""
import os, sys, datetime as dt, json, hashlib, re
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTDIR = DATA / "news"
OUTDIR.mkdir(parents=True, exist_ok=True)

def load_sources():
    cfg = yaml.safe_load((DATA/"news_sources.yaml").read_text(encoding="utf-8"))
    return cfg.get("feeds", []), cfg.get("symbols_map", {})

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def guess_symbols(text: str, symbols_map: dict) -> list:
    t = text.lower()
    hit = []
    for sym, kws in symbols_map.items():
        for kw in kws:
            if kw.lower() in t:
                hit.append(sym)
                break
    return sorted(set(hit))

def parse_entry(entry, source_name: str, symbols_map: dict) -> dict:
    title = normalize_text(entry.get("title", ""))
    link = entry.get("link") or entry.get("id") or ""
    published = entry.get("published") or entry.get("updated") or ""
    try:
        # feedparser 已解析的日期
        if entry.get("published_parsed"):
            dt_obj = dt.datetime(*entry.published_parsed[:6], tzinfo=dt.timezone.utc)
            published_iso = dt_obj.isoformat()
        elif entry.get("updated_parsed"):
            dt_obj = dt.datetime(*entry.updated_parsed[:6], tzinfo=dt.timezone.utc)
            published_iso = dt_obj.isoformat()
        else:
            published_iso = None
    except Exception:
        published_iso = None

    url_hash = sha256_hex(link) if link else None
    symbols = guess_symbols(f"{title} {link}", symbols_map)
    return {
        "title": title,
        "source": source_name,
        "url": link,
        "url_hash": url_hash,
        "published_at": published_iso,
        "symbols": symbols,
    }

def collect_once():
    feeds, symbols_map = load_sources()
    items = []
    for f in feeds:
        src = f.get("name") or "unknown"
        url = f.get("url")
        if not url:
            continue
        try:
            d = feedparser.parse(url)
            for e in d.entries[:200]:
                rec = parse_entry(e, src, symbols_map)
                if rec["url_hash"]:
                    items.append(rec)
        except Exception as e:
            print("[WARN]", src, "parse failed:", e)
            continue
    # 去重（以 url_hash）
    uniq = {}
    for it in items:
        uniq[it["url_hash"]] = it
    return list(uniq.values())

def write_jsonl(recs):
    day = dt.date.today().isoformat()
    fp = OUTDIR / f"{day}.jsonl"
    with open(fp, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return fp

if __name__ == "__main__":
    recs = collect_once()
    fp = write_jsonl(recs)
    print({"count": len(recs), "path": str(fp)})
