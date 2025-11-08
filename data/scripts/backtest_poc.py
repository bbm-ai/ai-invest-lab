import yfinance as yf
import pandas as pd
from pathlib import Path
import yaml

def sma_cross(prices, fast=5, slow=20):
    df = prices.copy()
    df['fast'] = df['Close'].rolling(fast).mean()
    df['slow'] = df['Close'].rolling(slow).mean()
    df['signal'] = (df['fast'] > df['slow']).astype(int).diff().fillna(0)
    return df

def main():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    data_dir = Path(cfg["data_dir"])
    data_dir.mkdir(parents=True, exist_ok=True)
    ticker = cfg.get("tickers", ["QQQ"])[0]
    print(f"[INFO] Fetching {ticker} data...")
    data = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
    if data.empty:
        raise RuntimeError("No data fetched.")
    data.to_csv(data_dir / f"{ticker}.csv")
    out = sma_cross(data)
    print(out.tail(3))

if __name__ == "__main__":
    main()
    print("Backtest POC ready ✅")
