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
