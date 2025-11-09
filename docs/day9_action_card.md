# ⚙️ Day 9 行動卡 — APIRouter(II)：真實 API + 超時 & Failover（v2.3）

**目標**：以最小實作接上真實 Groq / Gemini；加入超時與簡單 Failover。
> 若無 API Key 或未安裝 SDK，腳本會顯示 SKIP（不報錯）。

## 套件
```bash
source .venv/bin/activate
pip install groq google-generativeai
```

## .env（加入金鑰）
```bash
# 直接追加（若已存在可略過）
cat >> .env << 'EOF'
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
EOF
```

## 驗收 — Live Router（帶 Failover）
```bash
python scripts/router_live.py
```
**預期**：每個任務印出一個 JSON；
- 若缺少金鑰/SDK → `"status": "SKIP"`
- 若呼叫失敗 → `status: ERROR`，並顯示 `backup_result`（備援嘗試）
- 成功 → `status: OK` 與 LLM 輸出

## 風險與注意事項
- 這版只示範單輪 method；未包含重試間隔與指數退避，Day 10 加入。
- 請確保金鑰安全（.env 已在 .gitignore）。
- 成本控管：保持輸入極短、temperature 低；Day 10 會加入 token/成本記錄。
