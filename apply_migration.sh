#!/usr/bin/env bash
set -euo pipefail
DB="data/ai_invest.sqlite3"
SQL="migrations/001_init.sql"
mkdir -p data
sqlite3 "$DB" < "$SQL"
sqlite3 "$DB" '.tables'
sqlite3 "$DB" 'PRAGMA integrity_check;'
echo "[OK] migration applied"
