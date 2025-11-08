#!/usr/bin/env python
import os, sys, sqlite3, textwrap, datetime as dt
from pathlib import Path
import yaml, jinja2, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
CFG = ROOT / "config.yaml"
DB_PATH = ROOT / "data" / "ai_invest.sqlite3"
REPORTS = ROOT / "reports"

def ensure_dirs():
    for p in ["data","logs","reports"]:
        d = ROOT / p
        d.mkdir(parents=True, exist_ok=True)
        (d/".touch").write_text("ok", encoding="utf-8")
        (d/".touch").unlink()

def check_env_cfg():
    assert ENV.exists(), ".env missing; run: cp .env.example .env"
    assert CFG.exists(), "config.yaml missing"
    yaml.safe_load(CFG.read_text(encoding="utf-8"))

def check_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS smoke (ts TEXT, note TEXT)")
    cur.execute("INSERT INTO smoke VALUES (?,?)", (dt.datetime.utcnow().isoformat(), "hi"))
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM smoke")
    n = cur.fetchone()[0]
    conn.close()
    return n

def write_report():
    tpl = """# 📅 Daily Report — {{ date }}
- Pipeline: OK | Last Run: {{ ts }}
- Costs: 0.00

| date | symbol | rec | pos_size | confidence |
|-----:|:------:|:---:|---------:|-----------:|
| {{ date }} | SPY | HOLD | 0.20 | 0.65 |
"""
    env = jinja2.Environment()
    md = env.from_string(tpl).render(date=dt.date.today().isoformat(), ts=dt.datetime.utcnow().isoformat())
    out = REPORTS / f"daily_smoke_{dt.date.today().isoformat()}.md"
    out.write_text(md, encoding="utf-8")
    return out

def main():
    print(f"[SMOKE] root={ROOT}")
    ensure_dirs()
    check_env_cfg()
    n = check_db()
    out = write_report()
    print(f"[OK] sqlite rows={n}; report -> {out}")

if __name__ == "__main__":
    main()
