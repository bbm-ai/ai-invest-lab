#!/usr/bin/env bash
set -Eeuo pipefail

# ------------------------------
# Release builder (tag-safe)
# ------------------------------
# 功能：
# 1) 自動挑選可用 TAG：避免覆蓋遠端既有 tag
# 2) 重新產生報表
# 3) 產出帶 TAG 的 release zip
# 4) 可選：git commit
# 5) 建立並推送 tag
#
# 參數 / 環境變數（可選）：
#   RELEASE_BASE_TAG   預設 v0.3-milestone3
#   RELEASE_NOTE_FILE  預設使用 reports/final_report.md（若存在）
#   INCLUDE_REPORTS    預設 1（將 reports/ 一併打包）；設 0 則不包含
# ------------------------------

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RELEASE_BASE_TAG="${RELEASE_BASE_TAG:-v0.3-milestone3}"
RELEASE_NOTE_FILE="${RELEASE_NOTE_FILE:-reports/final_report.md}"
INCLUDE_REPORTS="${INCLUDE_REPORTS:-1}"

echo "[0/5] Repo: $ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "[ERR] Not a git repository." >&2
  exit 2
}

# ------------------------------
# Step 0: 選出可用 TAG（避免撞名）
# ------------------------------
echo "[0/5] Resolve tag base=${RELEASE_BASE_TAG}"

BASE="$RELEASE_BASE_TAG"
TAG="$BASE"

# 若遠端存在同名，嘗試 v0.3.1-milestone3, v0.3.2-milestone3 ...
if git ls-remote --tags origin | grep -q "refs/tags/${TAG}$"; then
  i=1
  # 從 v0.3.1-milestone3 開始找空位
  while git ls-remote --tags origin | grep -q "refs/tags/v0.3.${i}-milestone3$"; do
    i=$((i+1))
  done
  TAG="v0.3.${i}-milestone3"
fi

# 如果本地也恰好撞名（極小機率），退回帶時間戳
if git show-ref --tags | grep -q "refs/tags/${TAG}$"; then
  TAG="${BASE}-$(date +%Y%m%d-%H%M%S)"
fi

echo "[tag] Selected tag -> ${TAG}"

# 針對 zip 檔名，也帶上 TAG 方便溯源
STAMP="$(date +%Y%m%d_%H%M%S)"
ART="release_${TAG}_${STAMP}.zip"

# ------------------------------
# Step 1: 重新產生報表
# ------------------------------
echo "[1/5] Re-generate reports"
# 允許缺檔不中止；逐一嘗試
if [ -x scripts/report_ops_24h.py ]; then
  python scripts/report_ops_24h.py || true
fi
if [ -x scripts/generate_final_report.py ]; then
  python scripts/generate_final_report.py || true
fi
if [ -x scripts/backtest_runner.py ]; then
  python scripts/backtest_runner.py || true
fi

# ------------------------------
# Step 2: 打包 artifact（排除大型/暫存目錄）
# ------------------------------
echo "[2/5] Build artifact -> ${ART}"

# 準備打包清單
# 注意：
# - 預設包含 reports/；若 .gitignore 忽略也沒關係，zip 不受 git 管控限制
# - 排除 .venv、__pycache__、logs、backups、data/prices 等大資料夾
INCLUDE_PATHS=(
  "README.md"
  "config.yaml"
  "requirements.txt"
  "app/"
  "docs/"
  "migrations/"
  "scripts/"
  "src/"
  "data/symbols.yaml"
  "data/news_sources.yaml"
)

# 可選：包含 reports
if [ "$INCLUDE_REPORTS" = "1" ] && [ -d "reports" ]; then
  INCLUDE_PATHS+=("reports/")
fi

# 建立 zip
# -r 遞迴；-q 安靜，-FS 去除重複；-9 壓縮等級
# -x 為排除清單
zip -r -q -9 -FS "$ART" "${INCLUDE_PATHS[@]}" \
  -x "**/__pycache__/**" \
     "**/.DS_Store" \
     ".git/**" \
     ".venv/**" \
     "logs/**" \
     "backups/**" \
     "data/prices/**" \
     "data/news/**" \
     "reports/*.ipynb_checkpoints/**" \
     "reports/.DS_Store"

echo "[zip] $(ls -lh "$ART" | awk '{print $5, $9}')"

# ------------------------------
# Step 3: 可選 commit（若有變更）
# ------------------------------
echo "[3/5] Git add & commit (optional)"
git add scripts/make_release.sh || true
# 若有想一併提交的其他檔案可加在這裡
if ! git diff --cached --quiet; then
  git commit -m "chore(release): finalize reports & build artifact for ${TAG}" || true
else
  echo "[git] nothing to commit"
fi

# ------------------------------
# Step 4: 建立並推送 TAG（安全）
# ------------------------------
echo "[4/5] Create tag -> ${TAG}"
# 優先以 reports/final_report.md 作為 notes；否則用預設訊息
if [ -f "$RELEASE_NOTE_FILE" ]; then
  NOTE_MSG="(see $RELEASE_NOTE_FILE)"
else
  NOTE_MSG="Release ${TAG}"
fi

# 本地標籤（若存在同名，本地保留；但前面已避開機率小）
git tag -a "${TAG}" -m "${NOTE_MSG}" || true
# 推送新 tag（若已存在，不會出錯，因為我們換了名字）
git push origin "${TAG}" || true

# ------------------------------
# Step 5: 完成
# ------------------------------
echo "[5/5] Done. Artifact -> ${ART}"
echo "[hint] You can manually create a GitHub Release and upload ${ART}."
