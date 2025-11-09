# DECISIONS (ADR)

## 2025-11-09 — CI 檔名統一
- 決策：`nightly.yml` → `ci.yml`
- 理由：同檔名便於跨機器與教學對齊
- 影響：所有文件與指令統一指向 `.github/workflows/ci.yml`

## 2025-11-09 — 發佈入口整合
- 決策：用 `scripts/make_release.sh` 取代 `publish_github_release.sh`
- 理由：單一路徑避免分叉；含 Re-tag、打包、GitHub Release 自動上傳
- 影響：任何發佈請只用 `make_release.sh`

## 2025-11-07 — direnv 生效點
- 決策：從 Day 7 起，進專案目錄自動載入 `.envrc`
- 理由：避免每次 `set -a`；秘密保留在 `.env`（不版控）

