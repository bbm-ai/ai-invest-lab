# src/llm_clients/gemini_client.py
import os, time

class GeminiClient:
    def __init__(self):
        self.key = os.getenv("GEMINI_API_KEY")

    def analyze(self, prompt: str, model: str | None = None, timeout: float = 10.0, **kwargs):
        """
        接受 model 參數以相容呼叫端；若沒有 API Key，回傳可預期的 placeholder。
        """
        if not self.key:
            # CI / 本機無金鑰時用 placeholder，不要丟錯
            return {
                "status": "SKIP",
                "provider": "gemini",
                "model": model or "gemini-2.5-flash",
                "summary": "(gemini:skip) placeholder summary",
                "latency_ms": 0,
            }
        # 真實 API 呼叫（留白或以你現有的 SDK 包裝）
        t0 = time.time()
        # TODO: 實作真正的 Gemini 呼叫；此處以假輸出佔位
        out_text = "(gemini:ok) analyzed"
        return {
            "status": "OK",
            "provider": "gemini",
            "model": model or "gemini-2.5-flash",
            "summary": out_text,
            "latency_ms": int((time.time() - t0) * 1000),
        }

# 讓呼叫端使用單例風格
gemi = GeminiClient()
