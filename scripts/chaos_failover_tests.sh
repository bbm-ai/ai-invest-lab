#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 先清除注入，跑基線
unset FAULT_MODE FAULT_PROB FAULT_LATENCY_MS
PYTHONPATH=. ./.venv/bin/python scripts/test_failover_matrix.py

OUT="reports/day16_failover_summary.md"
mkdir -p reports
{
  echo "# Day 16 — Failover/Retry Summary"
  echo
  echo "## llm_costs — 最近 200 筆（觀察 OK/ERROR/SKIP 與 route）"
  echo '```sql'
  sqlite3 data/ai_invest.sqlite3 "SELECT ts,task_type,provider,status,route_primary,substr(error,1,50) FROM llm_costs ORDER BY ts DESC LIMIT 200;"
  echo '```'
  echo
  echo "## 測試矩陣彙整（_tmp_summary）"
  echo '```sql'
  sqlite3 data/ai_invest.sqlite3 "SELECT scenario,route,status,SUM(n) AS cnt FROM _tmp_summary GROUP BY scenario,route,status ORDER BY scenario,route,status;"
  echo '```'
} > "$OUT"

echo "[OK] Report -> $OUT"
