[![release](https://img.shields.io/github/v/release/bbm-ai/ai-invest-lab)](https://github.com/bbm-ai/ai-invest-lab/releases)

# Day 2 Starter Kit — 快速補檔指南（v2.2, 2025-11-08)

將本資料夾內容複製到你的專案根目錄 `ai-invest-lab/`：
```
migrations/001_init.sql
docs/system_architecture.md
docs/constants.md
```
完成後，依 Day 2 行動卡執行：
```bash
sqlite3 data/ai_invest.sqlite3 < migrations/001_init.sql
sqlite3 data/ai_invest.sqlite3 '.tables'
sqlite3 data/ai_invest.sqlite3 'PRAGMA integrity_check;'
```
驗收：看到 5+ 張表、`integrity_check=ok`、`news.url_hash` 為 UNIQUE。

## 🔐 環境變數載入（建議）
- 本地互動：使用 **direnv**（在專案根 `direnv allow` 後，進入資料夾自動載入 `.env`）
- systemd/cron：使用 `EnvironmentFile=.env`（服務與排程不依賴 direnv）
