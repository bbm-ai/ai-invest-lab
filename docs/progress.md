# 📘 Project Progress — AI 投資團隊（v2.3）

## ✅ 任務卡進度 (Phase 1 — T01~T07)
- [ ] **T01** 環境設定（VM / Git / Python）
- [x] **T02** 數據庫設計（SQLite schema + upsert keys）
- [ ] **T03** BaseAgent / Orchestrator 契約（文件）
- [x] **T04** Data Collector (I) 價量資料 — *2025-11-08 完成*
- [x] **T05** Data Collector (II) 新聞 RSS — *2025-11-08 完成*
- [ ] **T06** 匯入新聞→DB + 輕量情緒分數
- [ ] **T07** Milestone 1 驗收

## 📅 Daily Log
### 2025-11-08
- 價量收集：修正 yfinance MultiIndex，輸出純欄名 `date,open,high,low,close,volume`；SPY/QQQ/DIA 重新產出。
- 新聞收集：以 RSS 產生 `data/news/2025-11-08.jsonl`；以 `url_hash=sha256(url)` 去重，初步 `symbols[]` 關鍵字對映。
- 下一步（T06）：將 JSONL 匯入 `news` 表並以規則法產出 `sentiments`（score ∈ [-1,1]）。
