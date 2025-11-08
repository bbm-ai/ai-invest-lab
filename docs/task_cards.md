# 🔖 AI 專業投資團隊 - 21 天任務卡 (v2)

> **新增**：每張任務卡皆含 **Inputs / Expected Outputs** 與更明確的驗收條件。

## Phase 1: MVP 基礎架構 (T01–T07)

| 編號 | 任務名稱 | 核心目標 | Inputs | Expected Outputs | 驗收標準 | 預估時長 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T01** | 環境設定 | 建立穩定的雲端運行環境 | GCP 帳號、SSH 金鑰 | e2-micro VM、Git Repo、Python3.12/uv/venv | SSH 可連；Repo 初始化；`python -V` 正確；`.env.example` 建好 | 8 hr |
| **T02** | 數據庫設計 | 建立結構化數據庫 | Schema 設計清單 | SQLite 檔與初始化腳本 | `strategies` 含 `is_executed`、`confidence` 欄位；`PRAGMA integrity_check`=ok | 8 hr |
| **T03** | Agent 抽象類 | 可擴展 Agent 框架 | Python 腳手架 | `BaseAgent` with `execute(context)` | 子類能成功繼承並呼叫；單元測試通過 | 4 hr |
| **T04** | Data Collector (I) | 取得 SPY 價/量 | yfinance 或替代源 | 歷史/當日價量入庫 | 近 3 年日線可查；重跑具冪等性 | 8 hr |
| **T05** | Data Collector (II) | 市場新聞入庫 | RSS/News API | 當日 Top 市場新聞 | 每日≥20筆；含標題、來源、時間、URL；去重 | 12 hr |
| **T06** | Master Agent | 系統調度/日誌 | `config.yaml` | 可串 T04+T05 | 日誌完整；出錯自動重試一次 | 8 hr |
| **T07** | Milestone 1 驗收 | 基礎穩定運行 | — | Day1–6 功能整合 | README 首次運行文件；端到端成功一次 | 4 hr |

## Phase 2: AI 智能增強 (T08–T14)

| 編號 | 任務名稱 | 核心目標 | Inputs | Expected Outputs | 驗收標準 | 預估時長 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T08** | LLM API 整合 | 準備 LLM 客戶端 | API Keys | Groq/Gemini/Claude 客戶端 | `ping` 測試回 200；憑證加密保存 | 4 hr |
| **T09** | API 智能路由 (I) | 任務分流 | T08 客戶端 | `APIRouter.call()` | news→Groq、ta→Gemini；錯誤日誌記錄 | 8 hr |
| **T10** | Analyst (I) | 新聞情緒/摘要 | T05 新聞 | 情緒分數(−1~1)、摘要 | 入庫成功；樣本抽查合邏輯 | 12 hr |
| **T11** | Analyst (II) | 技術指標分析 | T04 價量 | RSI/MACD 趨勢判斷 | 入庫成功；與 TA-Lib 結果合理接近 | 12 hr |
| **T12** | Strategist (I) | 策略建議 | T10+T11 | Rec/Reason/Size/Conf | `strategies` 寫入且可追溯 | 12 hr |
| **T13** | Strategist (II) | 成本控制 & 高級決策 | VIX/分歧度 | `should_use_claude()` | 低信心或高波動時觸發；成本日誌明確 | 8 hr |
| **T14** | Milestone 2 驗收 | 決策鏈檢驗 | — | 端到端策略輸出 | 成本/品質雙通過；審查報告 | 4 hr |

## Phase 3: 部署、健壯與優化 (T15–T21)

| 編號 | 任務名稱 | 核心目標 | Inputs | Expected Outputs | 驗收標準 | 預估時長 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T15** | 自動部署與排程 | Systemd + Cron | `deploy.sh` | 服務自動啟動；定時運行 | `TZ=America/New_York` 生效；重啟後仍運行 | 12 hr |
| **T16** | 健壯性 (I) | API Failover | T09 路由 | 失敗自動切換 | 模擬逾時/429；成功降級或切換 | 8 hr |
| **T17** | 健壯性 (II) | 備份與告警 | rclone/Telegram | 每日 DB 備份；錯誤告警 | 備份可還原；告警不漏報、不重複 | 8 hr |
| **T18** | Milestone 3 驗收 | 部署穩定 | — | 24 小時自動運行 | 日誌 OK；Cron 時間正確；Failover 測試通過 | 4 hr |
| **T19** | 性能與回測 (I) | 長期運行準備 | 歷史價/策略 | `Backtester` 介面 | 能讀取並產出 P&L 基本指標 | 8 hr |
| **T20** | 儀表板 (I) | Streamlit UI | 內部 API | 歷史/最新策略視圖 | 行動版 OK；延遲<2s；狀態指示燈 | 12 hr |
| **T21** | 專案結案 | 文檔與報告 | Git Logs | 回測報告、KPI、總結 | `reports/` 完整；README 更新至 v2 | 8 hr |
