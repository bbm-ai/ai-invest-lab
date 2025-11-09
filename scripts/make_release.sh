#!/usr/bin/env bash
set -Eeuo pipefail

# --- [0] Repo / 前置變數 -------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "[0/5] Repo: $ROOT"

# 允許外部覆蓋：BASE_TAG (例如 v0.3-milestone3) 與 TAG_PREFIX
BASE_TAG="${BASE_TAG:-v0.3-milestone3}"
TAG_PREFIX="${TAG_PREFIX:-}"

# --- 小工具：檢查指令存在 --------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

# --- [0.1] 解析最新版本號並決定下一個 tag --------------------------------------
echo "[0/5] Resolve tag base=${BASE_TAG}"

# 找出現有符合 base 的 tags，格式：v<major>.<minor>.<patch>-milestone3 或 v<major>.<minor>-milestone3
# 規則：若已有 vX.Y.Z-milestone3，就取最大 Z + 1；若只有 vX.Y-milestone3，從 Z=1 開始。
existing_tags="$(git tag --list "${TAG_PREFIX}${BASE_TAG}" "${TAG_PREFIX}${BASE_TAG/%.*/.*}-*" 2>/dev/null || true)"

next_tag_calc() {
  local base="$1"
  local tags="$2"
  # 例：base=v0.3-milestone3 -> major_minor="0.3"
  local mm
  mm="$(sed -E 's/^v([0-9]+)\.([0-9]+).*$/\1.\2/' <<<"$base")" || mm="0.0"
  local re1="^${TAG_PREFIX}v${mm}-"
  local re2="^${TAG_PREFIX}v${mm}\.([0-9]+)-"
  local max_patch=0
  local found_patch=false
  while IFS= read -r t; do
    [[ -z "$t" ]] && continue
    if [[ "$t" =~ ${re2} ]]; then
      found_patch=true
      p="${BASH_REMATCH[1]}"
      [[ "$p" =~ ^[0-9]+$ ]] || continue
      (( p > max_patch )) && max_patch="$p"
    fi
  done <<<"$tags"

  if $found_patch; then
    echo "v${mm}.$((max_patch+1))-${base#*-}"
  else
    # 沒有 patch 版本時，從 .1 開始
    echo "v${mm}.1-${base#*-}"
  fi
}

TAG="$(next_tag_calc "$BASE_TAG" "$existing_tags")"
echo "[tag] Selected tag -> ${TAG}"

# --- [1] 重新產出報表 -----------------------------------------------------------
echo "[1/5] Re-generate reports"

# 報表腳本存在才執行（避免中斷）
have python && { 
  if [ -x "scripts/report_ops_24h.py" ]; then
    python scripts/report_ops_24h.py || echo "[WARN] report_ops_24h.py failed (skip)"
  fi
  if [ -x "scripts/generate_final_report.py" ]; then
    python scripts/generate_final_report.py || echo "[WARN] generate_final_report.py failed (skip)"
  fi
  if [ -x "scripts/backtest_runner.py" ]; then
    python scripts/backtest_runner.py || echo "[WARN] backtest_runner.py failed (skip)"
  fi
} || echo "[WARN] Python not available, skip reports."

# --- [2] 打包產物 ---------------------------------------------------------------
STAMP="$(date +%Y%m%d_%H%M%S)"
ART="release_${TAG}_${STAMP}.zip"
OUT="$ROOT/${ART}"

echo "[2/5] Build artifact -> ${ART}"

# 準備臨時清單；只收斂對分享/驗收有價值的檔案
TMP_LIST="$(mktemp)"
cat > "$TMP_LIST" <<'EOF'
README.md
config.yaml
docs/
migrations/
app/streamlit_app.py
scripts/backtest_runner.py
scripts/report_ops_24h.py
scripts/generate_final_report.py
reports/day18_ops_24h.md
reports/final_report.md
reports/backtest_readout.md
EOF

# 過濾不存在的檔案/資料夾
FILES=()
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if [ -e "$path" ]; then
    FILES+=("$path")
  fi
done < "$TMP_LIST"
rm -f "$TMP_LIST"

if ! have zip; then
  echo "[ERR] zip not found. Please install: sudo apt install -y zip" >&2
  exit 2
fi

# 建包
zip -qry "$OUT" "${FILES[@]}" || {
  echo "[ERR] zip failed" >&2
  exit 3
}
SIZE="$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")"
echo "[zip] $((SIZE/1024))K ${ART}"

# 產生 SHA256
SHA="${OUT}.sha256"
sha256sum "$OUT" | tee "$SHA" >/dev/null

# --- [3]（可選）Git add & commit（避免 reports 在 .gitignore 造成 noisy） -------
echo "[3/5] Git add & commit (optional)"
# 預設不強制加入 reports；僅提交腳本自身（若有變更）
git add scripts/make_release.sh 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "chore(release): finalize reports & build artifact for ${TAG}" || true
fi

# --- [4] 建立/推送 tag -----------------------------------------------------------
echo "[4/5] Create tag -> ${TAG}"
# 若 tag 已存在本地，先刪除再重建，避免 annotation 不一致
if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null; then
  git tag -d "${TAG}" >/dev/null
fi
git tag -a "${TAG}" -m "Release ${TAG}"
git push origin "${TAG}" || echo "[WARN] push tag failed (maybe no permission?)"

# --- [5] 自動發布到 GitHub Release（若 gh 可用且已登入） -------------------------
echo "[5/5] Publish to GitHub Release (auto if gh available)"

publish_release() {
  local tag="$1"
  local art="$2"
  local sha="$3"

  # 解析 repo
  local REMOTE_URL OWNER REPO
  REMOTE_URL="$(git remote get-url origin)"
  if [[ "$REMOTE_URL" =~ git@github\.com:(.+)/(.+)\.git ]]; then
    OWNER="${BASH_REMATCH[1]}"; REPO="${BASH_REMATCH[2]}"
  elif [[ "$REMOTE_URL" =~ https://github\.com/(.+)/(.+)\.git ]]; then
    OWNER="${BASH_REMATCH[1]}"; REPO="${BASH_REMATCH[2]}"
  else
    echo "[WARN] Cannot parse origin remote: $REMOTE_URL"
    return 0
  fi
  local REPO_FULL="${OWNER}/${REPO}"

  # 選擇釋出說明
  local NOTE="Release ${tag}"
  local NOTE_FILE=""
  if [ -f "reports/final_report.md" ]; then
    NOTE_FILE="reports/final_report.md"
  elif [ -f "reports/day18_ops_24h.md" ]; then
    NOTE_FILE="reports/day18_ops_24h.md"
  fi

  # 建立或更新 release
  if gh release view "$tag" -R "$REPO_FULL" >/dev/null 2>&1; then
    echo "[rel] Release exists -> $tag (will upload assets with --clobber)"
  else
    echo "[rel] Create release -> $tag"
    if [ -n "$NOTE_FILE" ]; then
      gh release create "$tag" -R "$REPO_FULL" -F "$NOTE_FILE" -t "$tag" || {
        echo "[WARN] create with notes failed; retry without notes"
        gh release create "$tag" -R "$REPO_FULL" -t "$tag"
      }
    else
      gh release create "$tag" -R "$REPO_FULL" -t "$tag"
    fi
  fi

  echo "[rel] Upload assets..."
  gh release upload "$tag" "$art" "$sha" -R "$REPO_FULL" --clobber
  echo "[OK] Published: https://github.com/$REPO_FULL/releases/tag/$tag"
}

if have gh; then
  if gh auth status -h github.com >/dev/null 2>&1; then
    publish_release "$TAG" "$OUT" "$SHA" || echo "[WARN] publish failed (continue)"
  else
    echo "[hint] gh installed but not logged in. Run: gh auth login"
    echo "[hint] You can manually upload: $ART"
  fi
else
  echo "[hint] Install GitHub CLI for auto-publish: sudo apt install -y gh && gh auth login"
  echo "[hint] You can manually create a GitHub Release and upload ${ART}"
fi

echo "[DONE] Artifact -> ${ART}"
