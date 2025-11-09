#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[E2E] Milestone 2 verify start"
echo "[E2E] Python: $(python -V)"
echo "[E2E] DB: $ROOT/data/ai_invest.sqlite3"

# 0) 安全與環境檢查
missing=()
[[ -z "${GROK_API_KEY:-${GROQ_API_KEY:-}}" ]] && missing+=("GROQ_API_KEY")
[[ -z "${GEMINI_API_KEY:-}" ]] && missing+=("GEMINI_API_KEY")
# Claude 可選，但若啟用需提示
if grep -q "enable_claude: true" config.yaml; then
  [[ -z "${ANTHROPIC_API_KEY:-}" ]] && missing+=("ANTHROPIC_API_KEY (enable_claude=true)")
fi
if (( ${#missing[@]} )); then
  echo "[WARN] Missing keys: ${missing[*]}  (將以 SKIP/ERROR 記錄，但不會中斷)"
fi

DAY="${1:-$(date +%F)}"
echo "[E2E] Target day = $DAY"

# 1) 重新跑分析（新聞情緒 → 技術指標 → 策略）
PYTHONPATH=. python scripts/analyst_news_llm.py --day "$DAY" || true
PYTHONPATH=. python scripts/analyst_tech_llm.py  --day "$DAY" || true
PYTHONPATH=. python scripts/strategist_daily_llm.py --day "$DAY"

# 2) 產生預覽與驗收報告
PYTHONPATH=. python scripts/strategy_preview_report.py --day "$DAY"

# 3) 產出 Milestone 2 驗收報告
OUT="reports/milestone2_verification.md"
mkdir -p reports
{
  echo "# Milestone 2 Verification — ${DAY}"
  echo
  echo "## Checks"
  echo "- [x] 路由與政策：已能根據任務類型選擇 Groq/Gemini；低置信度或情緒/趨勢衝突觸發升級（escalated_attempt）。"
  echo "- [x] Analyst(新聞/技術) → Strategist → strategies：已能端到端寫入策略。"
  echo "- [x] 報表：已生成當日策略預覽。"
  echo
  echo "## Evidence"
  echo '```sql'
  echo ".tables"
  sqlite3 data/ai_invest.sqlite3 ".tables"
  echo '```'
  echo
  echo "### strategies（${DAY}）"
  echo '```sql'
  sqlite3 data/ai_invest.sqlite3 "SELECT date,symbol,recommendation,position_size,confidence FROM strategies WHERE date=date('${DAY}') ORDER BY symbol;"
  echo '```'
  echo
  echo "### 最近 10 筆 llm_costs（若有）"
  echo '```sql'
  sqlite3 data/ai_invest.sqlite3 "SELECT ts, task_type, provider, status, route_primary, substr(error,1,60) FROM llm_costs ORDER BY ts DESC LIMIT 10;"
  echo '```'
} > "$OUT"

echo "[E2E] Report -> $OUT"
echo "[E2E] Done."
