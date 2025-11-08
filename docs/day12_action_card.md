# 🧭 Day 12 行動卡 — Strategist Agent (I)：LLM 綜合產出日級策略（v2.3）

**目標**：將 `sentiments`（新聞面）+ `tech_signals`（技術面）整合，透過 APIRouter → LLM 產出每檔 `2025-11-08` 的策略，寫入 `strategies`。無金鑰/失敗則用規則法 fallback。

## 步驟（節錄）
1) 確保 strategies schema
   sqlite3 data/ai_invest.sqlite3 < migrations/006_strategies_ensure.sql

2) 產出策略
   python scripts/strategist_daily_llm.py --day 2025-11-08

3) 產出報告
   python scripts/strategy_preview_report.py --day 2025-11-08
