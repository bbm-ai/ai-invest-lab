#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 載入環境變數
set -a
[ -f .env ] && . ./.env
set +a

# 設定日子：預設以「美東當日」，也可外部傳入 YYYY-MM-DD
DAY="${1:-$(TZ=America/New_York date +%F)}"

LOG="logs/daily_${DAY}.log"
mkdir -p logs reports

echo "=== [$(date -Is)] run_daily_pipeline start | DAY=${DAY} ===" | tee -a "$LOG"
echo "[INFO] Python=$(python -V 2>&1)" | tee -a "$LOG"

# 1) 新聞→情緒
PYTHONPATH=. ./.venv/bin/python scripts/analyst_news_llm.py --day "$DAY" | tee -a "$LOG" || true

# 2) 技術指標
PYTHONPATH=. ./.venv/bin/python scripts/analyst_tech_llm.py  --day "$DAY" | tee -a "$LOG" || true

# 3) 策略合成（含升級政策）
PYTHONPATH=. ./.venv/bin/python scripts/strategist_daily_llm.py --day "$DAY" | tee -a "$LOG" || true

# 4) 產出預覽報告
PYTHONPATH=. ./.venv/bin/python scripts/strategy_preview_report.py --day "$DAY" | tee -a "$LOG" || true

echo "=== [$(date -Is)] run_daily_pipeline done ===" | tee -a "$LOG"
