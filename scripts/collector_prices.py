#!/usr/bin/env python
"""
Day 4 — Data Collector (I): 價量資料收集（優先本地快取，無網也能跑）

- 讀取 data/symbols.yaml 的 universe
- 先檢查 data/prices/{SYMBOL}.csv 是否存在：存在 → 若 --refresh 才重新抓
- 可上網時使用 yfinance 抓取近 5 年日線；無網或失敗時用合成資料回退
- 產生統一欄位：date, open, high, low, close, volume
"""
import os, sys, argparse, datetime as dt
from pathlib import Path

import pandas as pd
import numpy as np
import yaml

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

def _flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    """將 yfinance 可能產生的 MultiIndex 欄位攤平，並統一為小寫單層欄名。"""
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        flat = []
        for c in df.columns:
            # c 可能像 ('Open','SPY')、('Date','')、('Adj Close','SPY')
            if isinstance(c, tuple):
                # 優先取 level 0（Open/High/Low/Close/Volume/Date）
                name = c[0] if c[0] not in (None, "",) else (c[1] if len(c) > 1 else "")
            else:
                name = c
            flat.append(str(name).strip().lower())
        df.columns = flat
    else:
        df.columns = [str(c).strip().lower() for c in df.columns]

    # 移除欄名/索引名，避免第二行額外 header
    df.columns.name = None
    df.index.name = None
    return df

def fetch_yfinance(symbol: str) -> pd.DataFrame:
    end = dt.date.today()
    start = end - dt.timedelta(days=365*5)
    df = yf.download(symbol, start=start.isoformat(), end=end.isoformat(), progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError("empty from yfinance")

    # reset index 後可能仍是 MultiIndex 欄位
    df = df.reset_index()
    df = _flatten_cols(df)

    # 正規化欄名
    rename_map = {
        "date":"date",
        "open":"open",
        "high":"high",
        "low":"low",
        "close":"close",
        "adj close":"adj_close",
        "volume":"volume",
    }
    df = df.rename(columns=rename_map)

    # 保留必要欄位
    keep = ["date","open","high","low","close","volume"]
    missing = [k for k in keep if k not in df.columns]
    if missing:
        raise RuntimeError(f"missing columns from yfinance after normalize: {missing}")
    df = df[keep]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def gen_synthetic(n=252*3, start=400.0, seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0003, 0.012, n)
    prices = [start]
    for r in rets:
        prices.append(prices[-1]*(1+r))
    dates = pd.bdate_range(end=dt.date.today(), periods=len(prices), freq="B")
    df = pd.DataFrame({"date":dates.date, "close":prices})
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open","close"]].max(axis=1)*(1+rng.normal(0.001,0.002,len(df)))
    df["low"]  = df[["open","close"]].min(axis=1)*(1-abs(rng.normal(0.001,0.002,len(df))))
    df["volume"] = rng.integers(5e6, 1e8, len(df))
    df = df[["date","open","high","low","close","volume"]]
    return _flatten_cols(df)

def save_csv(symbol: str, df: pd.DataFrame) -> Path:
    fp = PRICES_DIR / f"{symbol}.csv"
    df = _flatten_cols(df)
    df.to_csv(fp, index=False)

    # 安全網：若第二行仍像 ",SPY,SPY,..."，刪掉第二行
    try:
        import re
        lines = fp.read_text(encoding="utf-8").splitlines()
        if len(lines) > 1 and re.match(r"^,[A-Za-z]+(,[A-Za-z]+)*$", lines[1]):
            fp.write_text("\n".join([lines[0]] + lines[2:]) + "\n", encoding="utf-8")
    except Exception:
        pass
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
        except Exception:
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