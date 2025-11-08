# 確認環境可運行的冒煙測試
from pathlib import Path
import yaml, os
from dotenv import load_dotenv

def main():
    load_dotenv()
    assert os.getenv("LOG_LEVEL", "INFO")
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    print("[OK] config loaded, timezone:", cfg.get("timezone"))
    Path(cfg["data_dir"]).mkdir(parents=True, exist_ok=True)
    print("[OK] data dir ensured:", cfg["data_dir"])

if __name__ == "__main__":
    main()
    print("Smoke test passed ✅")
