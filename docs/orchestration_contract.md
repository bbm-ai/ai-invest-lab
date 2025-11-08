# 🔗 Orchestration Contract — Orchestrator ↔ Agents 協議（v2.2, 2025-11-08）
> 本文件定義**每日例行序列**、事件/狀態、資料契約與日誌規範，確保跨 Agent 的可觀測性與可追溯。

---

## 1) Daily Sequence（收盤後）
1. `start`（Master）→ 產生 `run_id`，設定 `trace_id` 种子。
2. `collect_prices` → upsert `prices`。
3. `collect_news` → upsert `news`（去重 by `url_hash`）。
4. `analyze_sentiment`（批次新聞 → `sentiments`）。
5. `analyze_tech`（價量 → `tech_signals`）。
6. `strategy_decision`（整合輸出 → `strategies`）。
6.5 `strategy_metrics_upsert`：將滾動績效（sharpe_7d/sharpe_30d/maxdd_30d/win_rate_30d）寫入 `strategy_metrics`（與 `strategies(date, symbol)` 對齊）。
7. `persist_logs`（結構化日誌與 Router traces）。
8. `reports/alerts`（日報、告警根據 `constants.md` 門檻）。

---

## 2) Event Model（事件與狀態機）
- 事件：`start` → `retry?` → `fallback?` → `success | fail`。
- 狀態轉移規則：
  - `retry`：可重試錯誤；若已達最大重試 → 進入 `fallback` 或 `fail`。
  - `fallback`：Router 改供應商/策略；仍失敗 → `fail`。
  - `success`：回填 `AgentResult`；寫入 DB 與日誌。
- 每個事件都需附：`run_id, trace_id, agent, task_type, ts`。

---

## 3) Router Trace（資料契約）
| 欄位 | 型別 | 說明 |
|---|---|---|
| `task_type` | enum | 任務類型 |
| `vendor` | enum | groq/gemini/gemini_flash/claude/local |
| `fallback_used` | bool | 是否切換 |
| `latency_ms` | int | 延遲 |
| `tokens` | int | token 數（如適用） |
| `cost_usd` | number | 成本 |
| `ts` | ISODate | 時間戳 |
> Trace 落存：建議每日彙總輸出 `logs/api_usage_summary.csv`（欄位：`task_type,vendor,fallback_used,latency_ms,tokens,cost_usd,ts`），供「成本 & Token」與「APIRouter 視圖」直接讀取。

---

## 4) Logging（結構化日誌欄位）
`ts, level, agent, event, run_id, trace_id, message, meta`  
- `meta` 範例：`{"symbol":"SPY","rows":500,"prompt_ver":"v1.3","model":"gemini-flash"}`

---

## 5) Upsert & Idempotency
- `prices(symbol,date)`、`tech_signals(symbol,date)`：主鍵 upsert。
- `news(url_hash)`：唯一鍵去重。
- `strategies(date,symbol)`：日級唯一；多版本策略另存 `id` 與 `version` 欄位（可選）。

---

## 6) Alerting & KPIs（與 constants 對齊）
- 成本（`$0.05/$0.10`）、可用性（99%）、Failover（95%）、LLM/API P50（3s）、Pipeline（<5m）。
- `/health` 連續失敗 2/5 次 → `WARN/CRIT`。

---

## 7) 驗收
- 實際運行時，事件流能完整記錄； `trace_id` 可追到每個 Agent 的 I/O；
- 日報/週報可從 traces 聚合出成本與可靠性指標。
