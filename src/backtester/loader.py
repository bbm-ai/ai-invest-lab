import csv, pathlib, sqlite3, datetime as dt

def load_prices_csv(path: pathlib.Path):
    rows=[]
    with path.open(newline="", encoding="utf-8") as f:
        r=csv.DictReader(f)
        for w in r:
            rows.append({
                "date": w["date"],
                "open": float(w["open"]),
                "high": float(w["high"]),
                "low":  float(w["low"]),
                "close":float(w["close"]),
                "volume": float(w["volume"]),
            })
    return rows

def load_daily_strategies(con: sqlite3.Connection, day: str):
    cur=con.cursor()
    cur.execute("""
      SELECT date, symbol, recommendation, position_size, confidence
      FROM strategies
      WHERE date=date(?) ORDER BY symbol
    """,(day,))
    return cur.fetchall()
