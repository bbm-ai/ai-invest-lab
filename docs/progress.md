# 📈 Project Progress — AI 專業投資團隊（v2.3）

> 目標：21 天完成從 MVP → 智能增強 → 部署優化的自動化投資團隊系統。  
> Repo：`bbm-ai/ai-invest-lab`  
> DB：`data/ai_invest.sqlite3`（SQLite）  
> 時區：分析與排程以 **America/New_York** 為準（Phase 3 套用）。

---

## ✅ 里程碑狀態

- **Milestone 1（Day 1–7）— MVP 基礎架構：Completed**
  - Tag：`v0.1-milestone1`
  - 產出：Collectors（價格/新聞）→ SQLite、情緒（規則）與技術訊號（RSI/MACD）、策略（規則）、操作手冊與進度檔
- **Milestone 2（Day 8–14）— AI 智能增強：Completed**
  - E2E 驗收：`reports/milestone2_verification.md`
  - 7 日路由/成本報表：`reports/m2_costs_last7d.md`
  - 策略合成支援政策升級（`should_use_claude`；`escalated_attempt`）

---

## 🗂 Phase / Task Checklist

### Phase 1: MVP 基礎架構（T01–T07）
- [x] **T01 環境設定**（Day 1）  
  VM/Repo/venv 初始化；Git 遠端（SSH）設好。
- [x] **T02 數據庫設計**（Day 2）  
  `migrations/001_init.sql` → `prices/news/tech_signals/strategies/logs` 等表建立；主鍵／唯一鍵確認。
- [x] **T03 Agent 抽象**（Day 3）  
  `src/base_agent.py`；`src/master_agent.py`；`docs/orchestration_contract.md`。
- [x] **T04 Data Collector (I)**（Day 4–5）  
  `scripts/collector_prices.py`（yfinance）；修正 MultiIndex/多餘 ticker 列。  
  ✅ 產出：`data/prices/SPY.csv, QQQ.csv, DIA.csv`
- [x] **T05 Data Collector (II)**（Day 6）  
  `scripts/collector_news_rss.py` → `data/news/YYYY-MM-DD.jsonl`  
  `scripts/news_to_db.py` 匯入 DB；  
  `scripts/analyze_sentiment.py`（規則法）→ `sentiments`。
- [x] **T06 Master Agent & Logs**（Day 6）  
  `src/master_agent.py` 整合 collector；`logs` 表。  
- [x] **T07 Milestone 1 驗收**（Day 7）  
  DB `.tables`、樣本查詢與 `reports/backtest_report.md`/`reports/daily_smoke_*.md`；Tag `v0.1-milestone1`。

### Phase 2: AI 智能增強（T08–T14）
- [x] **T08 LLM API 客戶端**（Day 8）  
  `src/api_router.py`（`route/next_best`），`scripts/router_dryrun.py`。
- [x] **T09 API 智能路由(I)**（Day 9）  
  路由策略（news→Groq、tech→Gemini、synthesis→Gemini）。
- [x] **T10 Retry/Backoff + Failover + 成本紀錄**（Day 10）  
  `src/utils/retry_backoff.py`, `src/llm_costs.py`, `migrations/003_llm_costs.sql`, `scripts/router_live_retry.py`。  
  ✅ 表：`llm_costs`。
- [x] **T11 分析員(新聞)**（Day 11）  
  `scripts/analyst_news_llm.py`（有金鑰→LLM；否則規則法）；擴大 ±1 天視窗。
- [x] **T12 分析員(技術指標)**（Day 12）  
  `migrations/004_tech_signals_extend.sql`（`rsi_14/macd/macd_signal/macd_hist/trend_label/summary`），  
  `scripts/analyst_tech_llm.py`（規則/LLM 混合）。
- [x] **T13 策略師(升級政策)**（Day 13）  
  `src/router_policies.py` → `should_use_claude(conf, avg_sent, trend_label, cap, enable, min_conf, sent_ext)`  
  `src/api_router.py` → `escalate_to_claude`；  
  `scripts/strategist_daily_llm.py`（完整修正版；`escalated_attempt`/`DEBUG_POLICY`）。
- [x] **T14 Milestone 2 驗收**（Day 14）  
  `scripts/e2e_m2_verify.sh`、`scripts/report_routing_costs.py`、  
  `reports/milestone2_verification.md`、`reports/m2_costs_last7d.md`。

### Phase 3: 部署、健壯與優化（T15–T21）
- [ ] **T15 自動部署與排程（Systemd+Cron，TZ=America/New_York）**
- [ ] **T16 健壯性(I)：APIs Failover 測試與重試策略強化**
- [ ] **T17 健壯性(II)：備份與告警（Telegram/Email）**
- [ ] **T18 Milestone 3 驗收（24/7 測試、日誌與告警核對）**
- [ ] **T19 性能與回測(I)：Backtester 介面與指標**
- [ ] **T20 儀表板(I)：Streamlit IA、頁面與查詢**
- [ ] **T21 結案：回測報告與成本/KPI 總結**

---

## 📅 每日進度（Day 1 → Day 14）

> 記錄格式：日期、完成項目、核心檔案/命令與驗收要點。

### Day 1 — 環境與 Git/SSH
- 完成：venv、Repo 初始化、SSH 金鑰、`origin` 推送
- 產出：`.gitignore`、`.gitattributes`、`README.md`

### Day 2 — DB Schema
- 執行：`sqlite3 data/ai_invest.sqlite3 < migrations/001_init.sql`
- 驗收：`.tables` 出現 `prices, news, tech_signals, strategies, logs`

### Day 3 — Agent 抽象
- 檔案：`src/base_agent.py`, `src/master_agent.py`, `docs/orchestration_contract.md`

### Day 4–5 — 價格 Collector
- 指令：`python scripts/collector_prices.py --refresh`
- 驗收：`data/prices/*.csv` 無多餘 ticker 列；欄位：`date,open,high,low,close,volume`

### Day 6 — 新聞/情緒
- 指令：  
  `python scripts/collector_news_rss.py --day YYYY-MM-DD`  
  `python scripts/news_to_db.py --day YYYY-MM-DD`  
  `python scripts/analyze_sentiment.py --day YYYY-MM-DD`
- 驗收：`news`/`sentiments` 計數符合預期（例：`70/28`）

### Day 7 — Milestone 1 驗收
- Tag：`v0.1-milestone1`
- 產出：`docs/day7_action_card.md`、`reports/backtest_report.md`
- DB：`SELECT COUNT(*) FROM news;`、`sentiments;`、抽查標題/摘要

### Day 8–9 — 路由與 Dryrun
- 指令：`PYTHONPATH=. python scripts/router_dryrun.py`  
- 驗收：任務→模型對映正確（news→groq / tech→gemini / synthesis→gemini）

### Day 10 — Retry/Failover/成本
- DB：`llm_costs` 建立
- 指令：`python scripts/router_live_retry.py`（無金鑰時 SKIP/ERROR 記錄）

### Day 11 — 新聞 LLM（可選）
- 指令：`python scripts/analyst_news_llm.py --day 2025-11-08`
- 驗收：`sentiments_upserted: 28`

### Day 12 — 技術指標擴充
- 指令：  
  `sqlite3 data/ai_invest.sqlite3 < migrations/004_tech_signals_extend.sql`  
  `python scripts/analyst_tech_llm.py --day 2025-11-08`
- 驗收：查詢 `tech_signals` 的 `rsi_14/macd_hist/trend_label`

### Day 13 — 策略師 + 升級政策
- 指令：`python scripts/strategist_daily_llm.py --day 2025-11-08`
- 驗收（樣例）：  
  `{'DEBUG_POLICY': True, 'enable_claude': True, 'min_conf': 0.8, 'sent_ext': 0.1, 'cap': 2}`  
  `{'symbol': 'QQQ', 'rec': 'HOLD', 'pos': 0.0, 'conf': 0.59, 'escalated_attempt': True}`

### Day 14 — Milestone 2 驗收
- 指令：  
  `./scripts/e2e_m2_verify.sh 2025-11-08`  
  `python scripts/report_routing_costs.py`
- 驗收：  
  - `reports/milestone2_verification.md` 產生  
  - `reports/strategy_2025-11-08.md` 產生  
  - `reports/m2_costs_last7d.md`：  
    ```
    | 2025-11-09 | claude | 2 | 0 | 0 | 2 |
    | 2025-11-09 | gemini | 6 | 6 | 0 | 0 |
    | 2025-11-08 | gemini | 5 | 3 | 0 | 2 |
    | 2025-11-08 | groq   | 2 | 0 | 1 | 1 |
    ```

---

## 🔍 運維/KPI（階段性）

- Pipeline 健康：`logs` 表錯誤率、E2E 成功率
- LLM 路由/成本：近 7 日 `llm_costs`（OK/ERROR/SKIP 分佈）
- 策略品質：`strategies.confidence` 分佈、`strategy_metrics`（待 T19）
- 資料品質：`prices/news/sentiments/tech_signals` 缺失率

---

## �� 下一步（Phase 3 起點）

- **Day 15（T15）**：`scripts/deploy.sh` + Systemd 服務（含 `.env`）  
  Cron：`TZ="America/New_York"`，策略在 17:00 ET 之後觸發
- **Day 16（T16）**：Failover 壓測；超時、429、DNS 錯誤模擬
- **Day 17（T17）**：每日備份（DB → GCS/GDrive）與 Telegram/Email 告警
- **Day 18（T18）**：24 小時穩定性測試
- **Day 19（T19）**：`Backtester` 介面與 `strategy_metrics`
- **Day 20（T20）**：Streamlit 儀表板 IA → 頁面/查詢
- **Day 21（T21）**：回測報告、成本/KPI 總結與結案

---

## 變更日誌（摘錄）

- 2025-11-09：完成 Day 14（M2 驗收）與 7 日路由/成本報表。
- 2025-11-08：修復 `strategist_daily_llm.py`（政策參數、`sys.path` bootstrap、情緒日期熱修）。
- 2025-11-08：`analyst_tech_llm.py`、`004_tech_signals_extend.sql` 上線。
- 2025-11-08：`llm_costs` 成本紀錄表與報表腳本建立。
