# 📘 Project Progress — AI 投資團隊（v2.2）

> 本檔作為唯一真實來源（Living Doc）。當你在聊天中回「完成」，我會在這裡打勾與記錄日誌。

## ✅ 任務卡進度 (Phase 1 — T01~T07)
- [x] **T01** 環境設定（Day 1） — *2025-11-08 完成*
- [x] **T02** 數據庫設計（Day 2） — *2025-11-08 完成*
- [ ] **T03** Agent 抽象類（Day 3）
- [ ] **T04** Data Collector (I) — 價量（Day 4）
- [ ] **T05** Data Collector (II) — 新聞（Day 5）
- [ ] **T06** Master Agent（Day 6）
- [ ] **T07** Milestone 1 驗收（Day 7）

## 📅 Daily Log
### 2025-11-08
- 成功執行 `python scripts/smoke_test.py`：建立 `data/ai_invest.sqlite3`，`smoke` 表寫入 1 筆；產生 `reports/daily_smoke_2025-11-08.md`。
- 成功執行 `python scripts/backtest_poc.py`：產生 `reports/backtest_report.md`（合成資料 SMA 10/30）。
- 備註：看到 `DeprecationWarning: datetime.datetime.utcnow()`，後續改為 `datetime.datetime.now(datetime.UTC)`。

## 🔧 開放議題 / TODO
- [ ] 將 `utcnow()` 改為 timezone-aware：`datetime.datetime.now(datetime.UTC)`（或 `pytz.UTC`）。
- [ ] T02 開始補上 `migrations/` 與索引、冪等 upsert 規範。
