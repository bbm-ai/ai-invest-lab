from loguru import logger
from pathlib import Path
import yaml

def run():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    logger.info(f"Loaded timezone: {cfg.get('timezone')} | tickers={cfg.get('tickers')}")
    logger.info("Hello ai-invest-lab v2 👋")

if __name__ == "__main__":
    run()
