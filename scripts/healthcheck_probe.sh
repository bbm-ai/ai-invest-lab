#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${DB_PATH:-$ROOT/data/ai_invest.sqlite3}"
DAY="${1:-$(TZ=America/New_York date +%F)}"

fail() { echo "$1"; exit 1; }

[ -f "$DB" ] || fail '{"ok":false,"err":"db_missing"}'

INTEG="$(sqlite3 "$DB" "PRAGMA integrity_check;")"
[ "$INTEG" = "ok" ] || fail "{\"ok\":false,\"err\":\"integrity:$INTEG\"}"

TABLES="$(sqlite3 "$DB" ".tables")"
echo "$TABLES" | grep -q '\bnews\b'       || fail '{"ok":false,"err":"table_news_missing"}'
echo "$TABLES" | grep -q '\bsentiments\b' || fail '{"ok":false,"err":"table_sentiments_missing"}'
echo "$TABLES" | grep -q '\btech_signals\b' || fail '{"ok":false,"err":"table_tech_signals_missing"}'
echo "$TABLES" | grep -q '\bstrategies\b' || fail '{"ok":false,"err":"table_strategies_missing"}'

N_STRAT="$(sqlite3 "$DB" "SELECT COUNT(*) FROM strategies WHERE date=date('$DAY');")"
[ "$N_STRAT" -ge 1 ] || fail "{\"ok\":false,\"err\":\"no_strategy_for_$DAY\"}"

REP="$ROOT/reports/strategy_${DAY}.md"
[ -f "$REP" ] || fail "{\"ok\":false,\"err\":\"report_missing_$REP\"}"

LOG="$ROOT/logs/daily_${DAY}.log"
[ -f "$LOG" ] || fail "{\"ok\":false,\"err\":\"log_missing_$LOG\"}"

echo "{\"ok\":true,\"day\":\"$DAY\",\"strategies\":$N_STRAT,\"report\":\"$REP\",\"log\":\"$LOG\"}"
