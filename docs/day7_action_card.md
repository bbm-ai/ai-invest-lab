# 🏁 Day 7 行動卡 — Milestone 1 驗收（v2.3）

**目標**：完成 Phase 1（T01–T06）的端到端驗收與文件校對。

## 驗收清單
- [ ] `prices`：`SPY/QQQ/DIA` CSV 欄位正確（`date,open,high,low,close,volume`），無多餘 header。
- [ ] `news`：`data/news/2025-11-08.jsonl` 產出；DB 中筆數 > 0（允許部分重複被跳過）。
- [ ] `sentiments`：已以 ±1 天視窗寫入，`COUNT(*) >= 20`。
- [ ] 文件一致性：`docs/constants.md`、`docs/orchestration_contract.md`、`docs/dashboard_ia.md` 欄位與實作一致。
- [ ] Git：`main` 已推送，標記 tag `v0.1-milestone1`（可選）。

## 驗收指令（逐行可貼）
```bash
# CSV
head -2 data/prices/SPY.csv

# DB 基本檢查
sqlite3 data/ai_invest.sqlite3 ".tables"
sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM news;"
sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM sentiments;"

# 抽查內容
sqlite3 data/ai_invest.sqlite3 "SELECT id, substr(title,1,60), published_at FROM news ORDER BY id DESC LIMIT 5;"
sqlite3 data/ai_invest.sqlite3 "SELECT news_id, score, substr(summary,1,60) FROM sentiments ORDER BY id DESC LIMIT 5;"

# （可選）打 tag
git tag v0.1-milestone1 -m "Phase 1 MVP pipeline verified"
git push origin v0.1-milestone1
```

## 檔案校對建議
- `migrations/001_init.sql`：確認 `news(url_hash UNIQUE)`、`strategies(is_executed DEFAULT 0)` 存在。
- `docs/dashboard_ia.md`：Strategy Metrics 區塊包含 `sharpe_7d, sharpe_30d, maxdd_30d, win_rate_30d`。
- `docs/system_architecture.md`：`strategies` 欄位名稱（`recommendation, reasoning, position_size, confidence`）與實作一致。

**完成後回覆「完成」**，我會：
1) 將 **T07 勾起來**並寫入進度；
2) 發佈 Phase 2 起手式（Day 8）：**LLM API 整合 + APIRouter(I)** 的行動卡。
