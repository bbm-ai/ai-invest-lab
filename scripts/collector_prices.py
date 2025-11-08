#!/usr/bin/env python
"""
scripts/collector_prices.py
Day 4 — Data Collector (I): 價量資料收集（優先本地快取，無網也能跑）

- 讀取 data/symbols.yaml 的 universe
- 先檢查 data/prices/{SYMBOL}.csv 是否存在：存在 → 若 --refresh 才重新抓
- 可上網時使用 yfinance 抓取近 5 年日線；無網或失敗時用合成資料回退
- 產生統一欄位：date, open, high, low, close, volume
"""
import os, sys, argparse, datetime as dt, pathlib
from pathlib import Path

try:
    import yaml, pandas as pd, numpy as np
except Exception as e:
    print("[FATAL] missing packages:", e)
    sys.exit(1)

try:
    import yfinance as yf
    HAS_YF = True
except Exception:
    HAS_YF = False

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PRICES_DIR = DATA / "prices"
PRICES_DIR.mkdir(parents=True, exist_ok=True)

def load_symbols():
    cfg = yaml.safe_load((DATA/"symbols.yaml").read_text(encoding="utf-8"))
    return [s.strip().upper() for s in cfg.get("universe", []) if s]

def fetch_yfinance(symbol):
    end = dt.date.today()
    start = end - dt.timedelta(days=365*5)
    df = yf.download(symbol, start=start.isoformat(), end=end.isoformat(), progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError("empty from yfinance")
    df = df.reset_index()
    df.rename(columns={"Date":"date", "Open":"open", "High":"high", "Low":"low", "Close":"close", "Adj Close":"adj_close", "Volume":"volume"}, inplace=True)
    df = df[["date","open","high","low","close","volume"]]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def gen_synthetic(n=252*3, start=400.0, seed=42):
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0003, 0.012, n)
    prices = [start]
    for r in rets:
        prices.append(prices[-1]*(1+r))
    dates = pd.bdate_range(end=dt.date.today(), periods=len(prices), freq="B")
    df = pd.DataFrame({"date":dates.date, "close":prices})
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open","close"]].max(axis=1)*(1+rng.normal(0.001,0.002,len(df)))
    df["low"]  = df[["open","close"]].min(axis=1)*(1-rng.normal(0.001,0.002,len(df)).abs())
    df["volume"] = rng.integers(5e6, 1e8, len(df))
    df = df[["date","open","high","low","close","volume"]]
    return df

def save_csv(symbol, df):
    fp = PRICES_DIR / f"{symbol}.csv"
    df.to_csv(fp, index=False)
    return fp

def run(symbols, refresh=False):
    results = []
    for sym in symbols:
        fp = PRICES_DIR / f"{sym}.csv"
        if fp.exists() and not refresh:
            results.append({"symbol":sym, "path":str(fp), "source":"cache"})
            continue
        try:
            if HAS_YF:
                df = fetch_yfinance(sym)
                src = "yfinance"
            else:
                raise RuntimeError("no yfinance")
        except Exception as e:
            df = gen_synthetic(seed=hash(sym)%10000)
            src = "synthetic"
        out = save_csv(sym, df)
        results.append({"symbol":sym, "path":str(out), "source":src, "rows":len(df)})
    return results

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="忽略快取，重新抓取")
    args = ap.parse_args()
    syms = load_symbols()
    res = run(syms, refresh=args.refresh)
    for r in res:
        print(r)
