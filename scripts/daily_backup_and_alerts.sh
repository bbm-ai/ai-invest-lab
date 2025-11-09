#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DAY="${1:-$(TZ=America/New_York date +%F)}"
ALERT_ON_SUCCESS="${ALERT_ON_SUCCESS:-true}"

mkdir -p reports

HC_OUT="$("$ROOT/scripts/healthcheck_probe.sh" "$DAY" || true)"
echo "[HC] $HC_OUT"

BK_OUT=""
BK_STATUS="SKIPPED"
if echo "$HC_OUT" | grep -q '"ok":true'; then
  BK_OUT="$("$ROOT/scripts/db_backup.sh" || true)"
  echo "[BK] $BK_OUT"
  if echo "$BK_OUT" | grep -q '"ok": true'; then
    BK_STATUS="OK"
  else
    BK_STATUS="FAIL"
  fi
else
  BK_STATUS="SKIPPED"
fi

# 通知（不讓它中斷）
if echo "$HC_OUT" | grep -q '"ok":true'; then
  if [ "$BK_STATUS" = "OK" ]; then
    MSG="✅ Day17 OK
• day: $DAY
• healthcheck: ok
• backup: ok"
    [ "$ALERT_ON_SUCCESS" = "true" ] && ./scripts/notify_telegram.py "$MSG" >/dev/null 2>&1 || true
  else
    MSG="🟡 Day17 WARN
• day: $DAY
• healthcheck: ok
• backup: failed"
    ./scripts/notify_telegram.py "$MSG" >/dev/null 2>&1 || true
    ./scripts/notify_email.py "Day17 WARN: backup failed" "$MSG" >/dev/null 2>&1 || true
  fi
else
  MSG="🔴 Day17 FAIL
• day: $DAY
• healthcheck: failed"
  ./scripts/notify_telegram.py "$MSG" >/dev/null 2>&1 || true
  ./scripts/notify_email.py "Day17 FAIL: healthcheck" "$MSG" >/dev/null 2>&1 || true
fi

# ---- 永遠寫報告（即使前面失敗） ----
OUT="reports/day17_ops_summary.md"

# 取出備份檔名（若有）
BK_FILE="$(echo "$BK_OUT" | sed -n 's/.*"zip":"\([^"]*\)".*/\1/p')"

{
  echo "# Day 17 — Ops Summary ($DAY)"
  echo
  echo "## Healthcheck"
  echo '```json'
  echo "${HC_OUT:-{}}"
  echo '```'
  echo
  echo "## Backup"
  echo ""
  echo "- Status: $BK_STATUS"
  if [ -n "$BK_FILE" ]; then
    echo "- File: $BK_FILE"
    if [ -f "$BK_FILE" ]; then
      echo "- Size (bytes): $(stat -c%s "$BK_FILE" 2>/dev/null || stat -f%z "$BK_FILE")"
    fi
  fi
  echo
  echo "## Latest Backups"
  echo '```bash'
  ls -1t backups 2>/dev/null | head -n 10 || echo "(no backups)"
  echo '```'
} > "$OUT"

echo "[OK] Report -> $OUT"
