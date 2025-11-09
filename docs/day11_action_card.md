# 🧩 Day 11 行動卡 — Analyst 接點導入（LLM 產出 sentiments/tech_summary → DB）（v2.3）

**目標**：
1) 以 LLM 生成新聞情緒（fallback 規則法），寫入 `sentiments`；
2) 計算 RSI/MACD 與技術摘要（可選 LLM 強化），寫入 `tech_signals`。

## Inputs
- DB：`data/ai_invest.sqlite3`（`news`, `sentiments`, `tech_signals`）
- 價格檔：`data/prices/*.csv`；標的清單：`data/symbols.yaml`
- API：GROQ / GEMINI（已於 Day 9 設定）

## Expected Outputs
- `scripts/analyst_news_llm.py`、`scripts/analyst_tech_llm.py`
- 當日（±1 天）之 `sentiments` 有 LLM 評分/摘要（失敗時規則法）
- 當日之 `tech_signals` 有 RSI/MACD 與 trend_label，並可帶 `summary`

## 步驟
1) 套用 tech_signals 擴充 schema（一次性）
```bash
sqlite3 data/ai_invest.sqlite3 < migrations/004_tech_signals_extend.sql
sqlite3 data/ai_invest.sqlite3 ".schema tech_signals"
```

2) 產生 LLM 新聞情緒（±1 天；有鍵→用 LLM，否則 fallback 規則法）
```bash
python scripts/analyst_news_llm.py --day 2025-11-08
sqlite3 data/ai_invest.sqlite3 "SELECT COUNT(*) FROM sentiments;"
```

3) 計算 RSI/MACD + 技術摘要（可選用 LLM 補充文字）
```bash
python scripts/analyst_tech_llm.py --day 2025-11-08
sqlite3 data/ai_invest.sqlite3 "SELECT symbol, date, rsi_14, macd_hist, trend_label FROM tech_signals ORDER BY date DESC, symbol LIMIT 9;"
```

## 驗收
- `sentiments` 有今日（±1 天）對應新聞的 LLM/規則分數與短摘要；
- `tech_signals` 有每檔標的的 RSI(14)、MACD(12,26,9) 與 `trend_label`；`summary` 不為空（若 LLM SKIP 則為規則摘要）。

## 提交
```bash
git add scripts/analyst_news_llm.py scripts/analyst_tech_llm.py migrations/004_tech_signals_extend.sql docs/day11_action_card.md docs/progress.md
git commit -m "feat(day11): analyst LLM for news + RSI/MACD tech signals to DB"
git push
```
