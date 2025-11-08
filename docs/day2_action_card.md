# 🗂 Day 2 行動卡 — T02 數據庫設計（v2.2）

**Inputs**：`migrations/001_init.sql` 骨架、`docs/system_architecture.md` 的 schema 與 Data Lineage、`docs/constants.md`  
**Expected Outputs**：SQLite 初始 schema 建立完畢；索引與冪等鍵確認；`progress.md` 打勾 T02

## 步驟（15~25 分鐘）
1) **檢視/微調初始 schema**
   - 開啟 `migrations/001_init.sql`，確認以下表與鍵：
     - `prices (symbol,date)` PK、`news(url_hash UNIQUE)`、`tech_signals(symbol,date)`、`strategies(id, date, symbol, is_executed)`、`logs(...)`。
2) **執行初始遷移**
   ```bash
   sqlite3 data/ai_invest.sqlite3 < migrations/001_init.sql
   sqlite3 data/ai_invest.sqlite3 '.tables'
   sqlite3 data/ai_invest.sqlite3 'PRAGMA integrity_check;'
   ```
3) **驗收索引/鍵**
   - 以 `sqlite3 .schema strategies` 檢查 `is_executed DEFAULT 0` 是否存在。
   - 以 `sqlite3 .schema news` 檢查 `url_hash UNIQUE`。
4) **冪等 upsert 規範（落檔）**
   - 在 `docs/system_architecture.md` 或 `docs/readiness_review.md` 補充：
     - prices/news/tech_signals/strategies 的 upsert key 與去重策略。
5) **提交紀錄（可選）**
   ```bash
   git add migrations/001_init.sql docs/*
   git commit -m "feat(db): init schema & upsert keys (v2.2)"
   ```

## 驗收
- `sqlite3 data/ai_invest.sqlite3 '.tables'` 顯示 5+ 張表。
- `PRAGMA integrity_check=ok`
- `news.url_hash` 有 UNIQUE；`prices(symbol,date)` 與 `tech_signals(symbol,date)` 是主鍵。

## 風險提示
- 小心覆寫既有 DB；如已有資料，先備份 `data/ai_invest.sqlite3`。
- 後續 schema 變更請新增 `002_*.sql`，不要改動 `001_init.sql`。

完成後回覆「完成」，我會打勾 T02，並把驗收結果寫入 `progress.md`。
