import os, pathlib
def load_env():
    envfile = pathlib.Path(__file__).resolve().parents[2] / ".env"
    # 先嘗試標準庫：手動解析簡單 KEY=VALUE 行
    if envfile.exists():
        for line in envfile.read_text(encoding="utf-8").splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    # 若安裝了 python-dotenv 就用它覆蓋（更完整）
    try:
        from dotenv import load_dotenv
        load_dotenv(envfile)
    except Exception:
        pass
