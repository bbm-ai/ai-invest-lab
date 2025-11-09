#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DAY="$(TZ=America/New_York date +%F)"

# 1) 健檢
HC_OUT="$("$ROOT/scripts/healthcheck_probe.sh" "$DAY" || true)"
echo "[HC] $HC_OUT"

# 2) 24h KPI 報告
python scripts/report_ops_24h.py || true

# 3) 若有錯誤：整理失敗並告警（不讓其阻斷）
HAS_ERR="$(sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM llm_costs WHERE ts >= datetime('now','-1 day','localtime') AND status='ERROR';" || echo 0)"
if [ "${HAS_ERR:-0}" -gt 0 ]; then
  scripts/summarize_failures_24h.sh || true
  MSG="🟠 Watchdog: errors in last 24h
• day: $DAY
• errors: $HAS_ERR
• see: reports/day18_failures.md"
  ./scripts/notify_telegram.py "$MSG" >/dev/null 2>&1 || true
  ./scripts/notify_email.py "Watchdog: last 24h errors=$HAS_ERR" "$MSG" >/dev/null 2>&1 || true
else
  MSG="✅ Watchdog OK — last 24h no errors
• day: $DAY"
  # 若不想成功時刷訊息，設 ALERT_ON_SUCCESS=false
  if [ "${ALERT_ON_SUCCESS:-true}" = "true" ]; then
    ./scripts/notify_telegram.py "$MSG" >/dev/null 2>&1 || true
  fi
fi

echo "[OK] Watchdog round finished"
