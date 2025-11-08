# 🤖 Agents Spec — BaseAgent 介面規格（v2.2, 2025-11-08）
> 本文件定義所有 AI/非 AI Agent 的**統一契約**：I/O 結構、重試/退避、超時、冪等快取、成本記錄與可觀測性欄位。

---

## 1) Interface（語義契約）
- 入口：`execute(context) -> AgentResult`
- **呼叫語義**：
  - 每次呼叫必帶 `run_id` 與 `trace_id`（由 Orchestrator 下發）。
  - 同一批次輸入（`input_hash`）可回用快取（命中時 `from_cache=true`）。
- **時間限制**：預設 `timeout_ms=3000`，可在 `constants.md` 調整或由 Router 覆寫。
- **冪等等級**：對 `run_id + input_hash` 具有**強冪等**（重跑不產生重覆副作用）。

### 1.1 Input Contract（context）
| 欄位 | 型別 | 必填 | 說明 |
|---|---:|:---:|---|
| `run_id` | string | ✓ | 管線執行批次 ID（同日唯一）。 |
| `trace_id` | string | ✓ | 此任務鏈路追蹤 ID。 |
| `task_type` | enum | ✓ | 如 `news_summary` / `technical_analysis` / `strategy_decision`。 |
| `payload` | object | ✓ | 任務輸入資料（由上游定義）。 |
| `timeout_ms` | int |  | 預設 3000。 |
| `retries` | int |  | 預設 2 次。 |
| `vendor_hint` | enum |  | `groq` / `gemini` / `claude` / `local`。 |
| `input_hash` | string | ✓ | `sha256(payload)` 或標準化後雜湊。

### 1.2 Output Contract（AgentResult）
| 欄位 | 型別 | 必填 | 說明 |
|---|---:|:---:|---|
| `run_id` | string | ✓ | 回填。 |
| `trace_id` | string | ✓ | 回填。 |
| `task_type` | string | ✓ | 回填。 |
| `result_id` | string | ✓ | `uuid` 或主鍵。 |
| `data` | object | ✓ | 任務結果（結構依 Agent）。 |
| `started_at` | ISODate | ✓ | 起始時間（UTC）。 |
| `finished_at` | ISODate | ✓ | 結束時間（UTC）。 |
| `latency_ms` | int | ✓ | 端到端耗時。 |
| `vendor_used` | string |  | 實際供應商（含版本/模型）。 |
| `tokens` | int |  | LLM token 數（若適用）。 |
| `cost_usd` | number |  | 成本估算/實數。 |
| `fallback_used` | boolean |  | 是否發生故障切換。 |
| `from_cache` | boolean |  | 是否由快取命中。 |
| `meta` | object |  | 其他診斷資訊（如 prompt_ver、model_ver）。 |

---

## 2) Retry/Backoff（重試/退避）
- 預設 **最大重試 2 次**；退避：**等比 + 抖動**（例如 300ms、600ms、1200ms ± 隨機 10%）。
- **可重試錯誤**：429/5xx/逾時/可中斷網路錯誤。
- **不可重試**：驗證失敗、參數錯誤、無效輸入、法規/配額永續拒絕。
- 第一次重試失敗 → 啟動 **Failover**（由 Router 決策供應商）。

---

## 3) Timeouts（超時）
- 預設 `3000 ms`；特例可於 context 覆寫。
- 超時必回傳 `status=timeout` 並標 `partial=false`。

---

## 4) Idempotency & Cache（冪等與快取）
- Key：`run_id + input_hash + task_type`。
- 命中快取時：必回 `from_cache=true`，並保留原 `result_id/started_at/finished_at`。

---

## 5) Error Taxonomy（錯誤分類）
- `DATA_ERROR`：上游資料缺漏/格式錯誤。
- `VENDOR_ERROR`：供應商逾時/429/5xx。
- `SYSTEM_ERROR`：OS/磁碟/記憶體/依賴服務不可用。
- `POLICY_ERROR`：內容或合規限制。

---

## 6) Observability（可觀測性）
- 結構化日誌欄位：`ts, level, agent, event, run_id, trace_id, message, meta`。
- 事件：`start`, `retry`, `fallback`, `success`, `fail`。
- Router trace：`vendor`, `latency_ms`, `tokens`, `cost_usd`, `fallback_used`。

---

## 7) 成本記錄
- 計入：Prompt/Completion tokens、供應商單價、固定費用（若有）。
- 產出：逐任務 `cost_usd` 與每日彙總。與 `reporting/templates/*` 指標一致。

---

## 8) Validation（驗收）
- 同一輸入在重跑時 **不產生重覆寫入**（檢查 upsert 鍵）。
- 異常情況能進入 `retry → failover → success/fail` 正確狀態。
- 所有欄位名稱與 `dashboard_ia.md` 與報表模板對齊。

## 9) Versioning
- Strategist 需在 `data` 中包含 `version`（預設 `v1`），與 `strategies.version` 對齊。
- Prompt/模型版本建議記錄於 `meta.prompt_ver`, `meta.model_ver`。
