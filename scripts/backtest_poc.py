#!/usr/bin/env python
import math, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

def gen_prices(n=300, start=400.0):
    rng = np.random.default_rng(42)
    rets = rng.normal(0.0005, 0.01, n)
    prices = [start]
    for r in rets:
        prices.append(prices[-1]*(1+r))
    dates = pd.date_range(end=dt.date.today(), periods=n+1, freq="B")
    return pd.DataFrame({"date":dates, "close":prices})

def backtest_ma(df, short=10, long=30):
    df = df.copy()
    df["sma_s"] = df["close"].rolling(short).mean()
    df["sma_l"] = df["close"].rolling(long).mean()
    df["signal"] = (df["sma_s"] > df["sma_l"]).astype(int)
    df["position"] = df["signal"].shift(1).fillna(0)
    df["ret"] = df["close"].pct_change().fillna(0)
    df["strat_ret"] = df["position"] * df["ret"]
    eq = (1+df["strat_ret"]).cumprod()
    return df, eq

def metrics(eq):
    ret = eq.iloc[-1] - 1.0
    daily = eq.pct_change().fillna(0)
    sharpe = (daily.mean()/daily.std())*np.sqrt(252) if daily.std()>0 else 0.0
    dd = (eq/eq.cummax()-1).min()
    return ret, sharpe, dd

def write_report(df, eq, ret, sharpe, dd):
    REPORTS.mkdir(parents=True, exist_ok=True)
    md = f"""# 🧪 Backtest Report (SMA 10/30) — {dt.date.today().isoformat()}

- Period: {df['date'].iloc[0].date()} → {df['date'].iloc[-1].date()}
- Return: {ret*100:.2f}%
- Sharpe: {sharpe:.2f}
- Max Drawdown: {dd*100:.2f}%

## Notes
合成資料僅供驗證框架，非投資建議。
"""
    out = REPORTS / "backtest_report.md"
    out.write_text(md, encoding="utf-8")
    return out

def main():
    df = gen_prices()
    dfb, eq = backtest_ma(df)
    ret, sharpe, dd = metrics(eq)
    p = write_report(dfb, eq, ret, sharpe, dd)
    print(f"[OK] report -> {p}")

if __name__ == "__main__":
    main()
