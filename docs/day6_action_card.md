# 🗂 Day 6 行動卡 — 匯入新聞→DB + 輕量情緒分數（規則法，v2.3）

**Inputs**：`data/news/2025-11-08.jsonl`、`migrations/001_init.sql`（含 `news` / `sentiments`）  
**Expected Outputs**：
- `news` 表新增今日新聞（去重 by `url_hash`）
- `sentiments` 表有今日對應新聞的 `score` 與 `summary`

## 套件
本步驟僅用到 Python 內建 `sqlite3`（無需外部套件）。

## 步驟
1) 匯入 JSONL → DB
   ```bash
   python scripts/news_to_db.py --day 2025-11-08
   ```
2) 產生輕量情緒分數（規則法，無需外部套件）
   ```bash
   python scripts/analyze_sentiment.py --day 2025-11-08
   ```
3) 驗收
   ```bash
   sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM news WHERE date(COALESCE(published_at,'now'))=date('2025-11-08');"
   sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM sentiments;"
   sqlite3 data/ai_invest.sqlite3 ".schema sentiments"
   ```

## 備註
- 這是 MVP 規則法，先建立資料流正確性；之後 Day 8+ 會替換為 Groq/Gemini 分析。
- `sentiments` 採冪等 upsert（同一 `news_id` 先刪後寫）。
