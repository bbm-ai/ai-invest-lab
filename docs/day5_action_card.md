# 🗂 Day 5 行動卡 — T05 Data Collector (II) 新聞資料源（v2.3，先 RSS 無金鑰）

**Inputs**：免費 RSS 來源清單（例如：CNBC / Reuters / WSJ Markets 的 RSS）、`news` 表結構（url_hash 唯一）  
**Expected Outputs**：
- 產出 `data/news/YYYY-MM-DD.jsonl`（每列一則標準化新聞）
- 欄位：`title, source, url, url_hash, published_at, symbols[]`（先以關鍵字或簡短規則判斷對應標的）

## 步驟
1) 準備 RSS 清單（可先 3~5 個）
   - 例如：Reuters Business、CNBC Markets、Yahoo Finance Tickers（若可用）。
2) 標準化欄位與去重規則
   - `url_hash = sha256(url)`；同一天同一 `url_hash` 不重覆。
   - 限制欄長（如 title ≤ 200 chars）；`published_at` 轉 ISO（UTC）。
3) 先寫入 JSONL（不入庫）
   - 路徑：`data/news/YYYY-MM-DD.jsonl`；方便調試/去重與追蹤。
4) 驗收
   - 檔案存在且至少 20 則；抽查無重覆 URL。

## 風險提示
- RSS 穩定度不一，先少量來源試跑；News API/GNews 等需金鑰的方案留 Day 6+。
- 先不做 LLM，純結構化收集；Day 6 才做情緒/技術分析串接。

完成後回覆「完成」，我會勾選 `T05` 並更新 `progress.md`，再發後續行動卡。
