#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$ROOT/data/ai_invest.sqlite3"
OUT="$ROOT/reports/day18_failures.md"
mkdir -p "$ROOT/reports"

if [ ! -f "$DB" ]; then
  echo "[ERR] DB missing: $DB" >&2
  exit 2
fi

{
  echo "# Day 18 — Failure Summary (last 24h)"
  echo
  echo "## ERROR Types (head)"
  echo '```'
  sqlite3 "$DB" "SELECT substr(COALESCE(error,''),1,120) AS err, COUNT(*)
                 FROM llm_costs
                 WHERE ts >= datetime('now','-1 day','localtime') AND status='ERROR'
                 GROUP BY err ORDER BY COUNT(*) DESC LIMIT 20;"
  echo '```'
  echo
  echo "## By Provider (ERROR)"
  echo '```'
  sqlite3 "$DB" "SELECT provider, COUNT(*)
                 FROM llm_costs
                 WHERE ts >= datetime('now','-1 day','localtime') AND status='ERROR'
                 GROUP BY provider ORDER BY COUNT(*) DESC;"
  echo '```'
  echo
  echo "## Recent ERROR rows (10)"
  echo '```'
  sqlite3 "$DB" "SELECT ts, task_type, provider, route_primary, substr(COALESCE(error,''),1,200)
                 FROM llm_costs
                 WHERE ts >= datetime('now','-1 day','localtime') AND status='ERROR'
                 ORDER BY ts DESC LIMIT 10;"
  echo '```'
} > "$OUT"

echo "[OK] Failure report -> $OUT"
