import os
import time
import json
import logging
import datetime as dt
import yaml

from .base_agent import BaseAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class MasterAgent(BaseAgent):
    def execute(self, context):
        logging.info("MasterAgent start")
        # TODO: invoke data collectors, analyst, strategist via context router
        return {"status": "ok", "ts": dt.datetime.utcnow().isoformat()}

def main():
    cfg = load_config()
    tz = cfg.get("schedule", {}).get("timezone", "America/New_York")
    logging.info(f"Config loaded. TZ={tz}")
    m = MasterAgent()
    result = m.execute({})
    logging.info("MasterAgent result: %s", json.dumps(result))

if __name__ == "__main__":
    main()
