# 🗂 Day 3 行動卡 — T03 BaseAgent 抽象類（v2.2，無程式碼版）

**Inputs**：`docs/system_architecture.md`、`docs/strategy_detail_ui_spec.md`、`docs/constants.md`  
**Expected Outputs**：
- `docs/agents_spec.md`：定義 BaseAgent 介面（I/O 契約、重試/超時/trace_id、快取與冪等規則）
- `docs/orchestration_contract.md`：Orchestrator ↔ Agents 的協議（事件、狀態、日誌欄位）
- `progress.md` 勾選 T03

## 步驟（15–25 分鐘，文件化為主，不寫任何程式碼）
1) **撰寫 BaseAgent 介面規格**（新增 `docs/agents_spec.md`，建議包含）
   - 介面：`execute(context) -> AgentResult`；必要欄位：`run_id, trace_id, started_at, finished_at, retries, vendor_used, cost_usd, latency_ms`。
   - 錯誤處理：等比退避 + 抖動、最大重試 2；可中斷錯誤分類（資料/供應商/系統）。
   - 冪等等級：對同一 `run_id + input_hash`，允許快取命中並回傳同一 `result_id`。
   - 超時：預設 3s（見 `constants.md`）；可覆寫。
2) **撰寫 Orchestrator 協議**（新增 `docs/orchestration_contract.md`）
   - 事件：`start`, `success`, `retry`, `fallback`, `fail`；狀態機與遷移條件。
   - 日誌欄位標準：`ts, level, agent, event, run_id, trace_id, message, meta`。
   - 成本與路由紀錄：`tokens, cost_usd, vendor, fallback_used`，對應儀表板視圖。
3) **校準與簽核**
   - 對照 `dashboard_ia.md` 的 Router/成本面板欄位，確保資料契約一致。
   - 在 `docs/progress.md` 記錄「T03 文件完成」時間。

## 驗收
- `docs/agents_spec.md` 與 `docs/orchestration_contract.md` 兩份文件存在且涵蓋上列欄位。
- 規格中的欄位名稱與 UI/報表模板一致（避免後續對不上）。

完成後回覆「完成」，我會：
- 勾選 `T03`，補上 Daily Log，並送上 **Day 4 行動卡（T04：Data Collector I，不寫 LLM）**。
