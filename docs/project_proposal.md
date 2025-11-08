# 🤖 AI 專業投資團隊 - 完整專案企劃書 (21 天優化版, v2)

## 📋 專案概述

### 專案願景
建立一個完全自主運作的 AI 投資團隊，能夠 24/7 自動收集市場數據、分析趨勢、制定策略，並持續自我優化，最終達到專業投資團隊的決策水平。

### 核心目標 (Optimized)
* **最低成本運行**：**免費層級資源優先** (Google Cloud Free Tier, Groq/Gemini Free Tier)，運行成本控制在 $0–2/月。
* **自主運作**：無需人工干預，自動循環執行。
* **手機友好**：**Web 儀表板 (Streamlit)** 響應式設計，透過 **Telegram/Email** 推送關鍵報告與告警。
* **系統健壯性**：**API 故障切換 (Failover)** 機制，確保決策不中斷。
* **數據驅動**：所有決策可追溯、可回測，保留完整日誌與版本。

---

## 🎯 專案階段規劃

| 階段 (Phase) | 日期 | 重點工作 | 里程碑 (Milestone) |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Day 1–7** | **MVP 基礎架構**：VM、Git、環境、數據庫、數據收集腳本、Agent 框架。 | **Milestone 1**：單次運行成功，數據正確存儲，Agent 框架搭建完成。 |
| **Phase 2** | **Day 8–14** | **AI 智能增強**：Groq/Gemini/Claude API、情感分析、技術分析、策略生成、**API 智能路由**。 | **Milestone 2**：多模態分析策略輸出，含成本日誌。 |
| **Phase 3** | **Day 15–21** | **部署與優化**：Systemd + Cron、Failover、備份/告警、Streamlit、回測框架。 | **Milestone 3**：24/7 自動運行、告警/備份完整、儀表板可視化。 |

---

## 🚀 21 天時間表 (摘要)
> 完整 Task 詳見 `task_cards.md`

| Day | 階段 | 任務卡 | 核心工作內容 | 驗收/成果 |
| :--- | :--- | :--- | :--- | :--- |
| 1–7 | 1 | T01–T07 | VM/Repo/SQLite/BaseAgent/Collector/Master/初驗收 | **Milestone 1** |
| 8–14 | 2 | T08–T14 | API Clients/APIRouter/Analyst/Strategist/成本控制/二次驗收 | **Milestone 2** |
| 15–21 | 3 | T15–T21 | Systemd+Cron/Failover/備份告警/回測/UI/結案報告 | **Milestone 3** |

---

## 🔧 技術架構與關鍵設計

### 1) 數據庫設計 (SQLite, 可升級)
```sql
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    symbol TEXT DEFAULT 'SPY',
    recommendation TEXT,  -- BUY / SELL / HOLD
    reasoning TEXT,
    risk_level TEXT,
    position_size REAL,
    confidence REAL,      -- 0–1, 由 LLM 輸出
    is_executed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2) 調度與時區
使用 `config.yaml` 定義投資標的、時區與 Cron 表達式。策略分析須在 **美股收盤後 (16:00 ET)** 執行。

```yaml
investment:
  symbols: ["SPY"]

schedule:
  timezone: "America/New_York"  # 以美股時間運行
  strategy: "0 17 * * 1-5"       # 週一至週五 17:00 (收盤後 1h)
  data_collection: "0 */4 * * *" # 每 4 小時抓價
  backup: "0 2 * * *"            # 每日 02:00 備份
```

> **落地備註**：VM 系統時區可維持在 Asia/Taipei，Cron Job 以 `TZ=America/New_York` 覆寫；Systemd 服務裡也可注入 `Environment=TZ=America/New_York`，確保時間一致。

### 3) API 智能路由 (成本優先 + Failover)

- **任務分流**：
  - `news_summary` → **Groq (Llama3-8B)**
  - `technical_analysis` → **Gemini Flash**
  - `high_confidence_decision` (低信心/高波動) → **Claude**
- **成本控制**：記錄每次 API token/成本，納入 KPI；僅在 `should_use_claude()` 返回 `True` 時調用 Claude。
- **故障切換**：主要供應商逾時/錯誤 → 自動切換次優（例：Groq → Gemini Flash）。

**參考骨架**：
```python
class APIRouter:
    def __init__(self, clients):
        self.c = clients  # {"groq": g, "gemini": ge, "gemini_flash": gf, "claude": c}

    def call(self, task: str, payload: dict):
        plan = {
            "news_summary": ["groq", "gemini_flash"],
            "technical_analysis": ["gemini_flash", "groq"],
            "high_confidence_decision": ["claude", "gemini"]
        }.get(task, ["groq", "gemini_flash"])  # 預設

        last_err = None
        for key in plan:
            try:
                return self.c[key].run(payload)
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"APIRouter failover exhausted: {last_err}")

    def should_use_claude(self, context) -> bool:
        # 低信心、VIX 高於閾值、或多策略分歧明顯
        return (
            context.get("confidence", 1.0) < 0.6
            or context.get("vix", 0) >= 25
            or context.get("disagreement_score", 0) >= 0.4
        )
```

### 4) 健康檢查、備份與告警
- **健康檢查**：暴露 `/health` (return `{status: 'ok', ts}`)，每日 `curl` 檢查，失敗即告警。
- **備份**：`cron + rclone` → Google Drive/GCS；每日全量 SQLite 備份 + 每週壓縮存檔。
- **告警**：Telegram Bot 統一格式：`[UTC-5 17:00][Master][OK/ERROR][code][hint]`。

### 5) 報告與版本控管
- 自動輸出：
  - `/reports/backtest_report.md`
  - `/docs/system_architecture.md`
  - `/logs/api_usage_summary.csv`
- 以 `jinja2` 模板生成 Markdown 報告，Git 版本標記（tag: `v0.1-m1`, `v0.2-m2` ...）。

---

## 🏁 階段性里程碑 (驗收重點)

### Milestone 1 (Day 7)
- VM/Repo/環境完成；Master 完成一次端到端收集；SPY 歷史價 & 新聞入庫；`BaseAgent` 介面穩定。

### Milestone 2 (Day 14)
- APIRouter 任務分流與成本日誌；Analyst 產出情緒 & 技術摘要；Strategist 輸出含倉位與信心；`should_use_claude` 生效。

### Milestone 3 (Day 21)
- Systemd + Cron 24/7；**America/New_York** 定時正確；Failover 測試通過；備份/告警正常；Streamlit 顯示即時數據與策略。
