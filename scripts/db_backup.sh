#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${DB_PATH:-$ROOT/data/ai_invest.sqlite3}"
OUTDIR="$ROOT/backups"
LOGDIR="$ROOT/logs"
mkdir -p "$OUTDIR" "$LOGDIR"

DATE_LOCAL="$(TZ=America/New_York date +%F_%H%M%S)"
DOW="$(TZ=America/New_York date +%u)"  # 1..7, 7=Sun
KIND="daily"
[ "$DOW" = "7" ] && KIND="weekly"

BASENAME="${KIND}_${DATE_LOCAL}"
TMP="$OUTDIR/${BASENAME}.sqlite3"
ZIP="$OUTDIR/${BASENAME}.sqlite3.gz"
SUM="$OUTDIR/${BASENAME}.sha256"

if [ ! -f "$DB" ]; then
  echo "[ERR] DB not found: $DB" >&2
  exit 2
fi

echo "[INFO] backup -> $TMP"
sqlite3 "$DB" "PRAGMA wal_checkpoint(FULL);"
sqlite3 "$DB" "VACUUM;"
sqlite3 "$DB" ".backup '$TMP'"

echo "[INFO] compress -> $ZIP"
gzip -9 "$TMP"

echo "[INFO] sha256 -> $SUM"
sha256sum "$ZIP" > "$SUM"

# 保留策略：daily 保留 14 份；weekly 保留 8 份
echo "[INFO] retention: daily=14 weekly=8"
(ls -1t "$OUTDIR"/daily_*.sqlite3.gz 2>/dev/null | tail -n +15 | xargs -r rm -f)
(ls -1t "$OUTDIR"/daily_*.sha256      2>/dev/null | tail -n +15 | xargs -r rm -f)
(ls -1t "$OUTDIR"/weekly_*.sqlite3.gz 2>/dev/null | tail -n +9  | xargs -r rm -f)
(ls -1t "$OUTDIR"/weekly_*.sha256     2>/dev/null | tail -n +9  | xargs -r rm -f)

# 產出簡要摘要（供通知/報告用）
SIZE="$(stat -c%s "$ZIP" 2>/dev/null || stat -f%z "$ZIP")"
echo "{\"ok\": true, \"kind\":\"$KIND\", \"zip\":\"$ZIP\", \"bytes\": $SIZE }"
