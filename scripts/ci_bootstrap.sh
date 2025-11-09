#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${DB_PATH:-$ROOT/data/ai_invest.sqlite3}"
DAY="${1:-$(TZ=America/New_York date -d 'yesterday' +%F)}"

mkdir -p "$ROOT/data" "$ROOT/reports" "$ROOT/logs" "$ROOT/backups"

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "[BOOT] installing sqlite3 not supported here; ensure it's preinstalled" >&2
fi

echo "[BOOT] DB -> $DB"
# 依序套用 migrations（001 ~ 999）
for f in $(ls -1 "$ROOT/migrations/"*.sql | sort); do
  echo "[BOOT] apply $(basename "$f")"
  sqlite3 "$DB" < "$f"
done

echo "[BOOT] integrity_check"
sqlite3 "$DB" "PRAGMA integrity_check;"

# 若有本地新聞檔就先匯入，避免 sentiments/strategy 讀不到資料
NEWS_JSON="$ROOT/data/news/${DAY}.jsonl"
if [ -f "$NEWS_JSON" ]; then
  echo "[BOOT] import news from $NEWS_JSON"
  python "$ROOT/scripts/news_to_db.py" --day "$DAY" || true
else
  echo "[BOOT] skip news import (file not found: $NEWS_JSON)"
fi

# 確認基本表存在
echo "[BOOT] tables:"
sqlite3 "$DB" ".tables"
