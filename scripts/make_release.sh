#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[1/5] Re-generate reports"
python scripts/report_ops_24h.py    || true
python scripts/generate_final_report.py || true
python scripts/backtest_runner.py   || true

echo "[2/5] Build artifact"
OUT="release_$(date +%Y%m%d_%H%M%S).zip"
# 打包關鍵檔案（排除大型動態資料夾）
zip -r "$OUT" \
  README.md config.yaml .env.example \
  docs/ app/ scripts/ src/ migrations/ reports/ \
  -x "data/*" -x "backups/*" -x ".venv/*" -x "__pycache__/*" >/dev/null

echo "[3/5] Git add & commit (optional)"
git add docs/ reports/ scripts/ || true
git commit -m "chore(release): finalize milestone3 reports & artifacts" || true

echo "[4/5] Create tag"
TAG="v0.3-milestone3"
git tag -f -a "$TAG" -m "Milestone 3: 24/7 run + dashboard + reports"
git push origin main --tags

echo "[5/5] Done. Artifact -> $OUT"
