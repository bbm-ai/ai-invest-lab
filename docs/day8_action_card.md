# 🧠 Day 8 行動卡 — LLM API 整合 + APIRouter (I)（v2.3）

**目標**：建立最小可用的 LLM 客戶端與路由決策，不實際呼叫 API（先 Dry-Run）。

## Inputs
- `.env`：準備（或占位）`GROQ_API_KEY`、`GEMINI_API_KEY`（可先留空）
- `docs/orchestration_contract.md`：任務類型定義（news_summary / tech_summary / strategy_synthesis）

## Expected Outputs
- `src/api_router.py`：根據任務類型回傳「預計使用的模型/供應商」
- `src/llm_clients/`：留空殼檔 `groq_client.py`、`gemini_client.py`（僅定義介面，不發 HTTP）
- `scripts/router_dryrun.py`：示範 3 個任務類型的路由結果（列印到終端）

## 步驟（15–25 分鐘）
1) **檢查 .env**
   ```bash
   grep -E 'GROQ_API_KEY|GEMINI_API_KEY' .env || true
   ```
   如尚未存在，先加入占位：
   ```bash
   cat >> .env << 'EOF'
   GROQ_API_KEY=
   GEMINI_API_KEY=
   EOF
   ```

2) **建立目錄**
   ```bash
   mkdir -p src/llm_clients
   ```

3) **建立 `src/api_router.py`（最小決策邏輯，成本優先 → Groq；複雜任務 → Gemini）**
   ```python
   # src/api_router.py
   from dataclasses import dataclass

   @dataclass
   class RouteDecision:
       provider: str   # 'groq' | 'gemini'
       model: str      # model name
       reason: str     # why

   SIMPLE = {"news_summary"}        # 低成本任務
   COMPLEX = {"tech_summary", "strategy_synthesis"}  # 需要更強推理

   def route(task_type: str) -> RouteDecision:
       t = (task_type or '').strip().lower()
       if t in SIMPLE:
           return RouteDecision(provider="groq", model="llama3-8b", reason="Low-cost summarization")
       if t in COMPLEX:
           return RouteDecision(provider="gemini", model="gemini-1.5-flash", reason="Structured/long-context analysis")
       # 預設
       return RouteDecision(provider="groq", model="llama3-8b", reason="Default fallback")
   ```

4) **建立 LLM 客戶端殼檔（僅介面，尚不發請求）**
   ```python
   # src/llm_clients/groq_client.py
   class GroqClient:
       def __init__(self, api_key: str | None):
           self.api_key = api_key
       def summarize(self, text: str) -> dict:
           raise NotImplementedError("wire later")

   # src/llm_clients/gemini_client.py
   class GeminiClient:
       def __init__(self, api_key: str | None):
           self.api_key = api_key
       def analyze(self, payload: dict) -> dict:
           raise NotImplementedError("wire later")
   ```

5) **建立 Dry-Run 腳本**
   ```python
   # scripts/router_dryrun.py
   from src.api_router import route

   for task in ["news_summary", "tech_summary", "strategy_synthesis", "unknown_task"]:
       d = route(task)
       print({"task": task, "provider": d.provider, "model": d.model, "reason": d.reason})
   ```

6) **執行 Dry-Run**
   ```bash
   python scripts/router_dryrun.py
   ```

## 驗收
- 終端輸出能對應任務類型選擇對應供應商與模型：
  - `news_summary` → groq / llama3-8b
  - `tech_summary`、`strategy_synthesis` → gemini / 1.5-flash
  - 其他 → groq / 預設

## 風險提示
- 尚未發出任何 LLM API 請求；Day 9 再接入環境變數與真實 HTTP（並加入超時與 Failover）。
- 若你當天想直接測真實呼叫，建議使用較短的輸入與限流（避免超額）。
