# src/llm_clients/gemini_client.py
from __future__ import annotations
import os
from typing import Optional

class GeminiClient:
    """
    Minimal, CI-friendly shim.
    - 支援 __init__(api_key: Optional[str])，若未提供則讀環境 GEMINI_API_KEY
    - analyze/summarize 接受 model= 與 timeout= 參數
    - 無金鑰時：回傳可預期的占位摘要字串，避免 E2E/CI 中斷
      （若你要真正打 API，再把占位邏輯換成官方 SDK 呼叫即可）
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()

    def _degraded_summary(self, text: str, model: Optional[str]) -> str:
        head = (text or "").replace("\n", " ").strip()[:200]
        tag = model or "default"
        return f"[gemini:{tag}] {head}"

    def analyze(self, prompt: str, *, model: Optional[str] = None, timeout: Optional[float] = None) -> str:
        # TODO: 若要真連線，改成官方 SDK 並用 self.api_key 建 client
        if not self.api_key:
            return self._degraded_summary(prompt, model)
        # 這裡先回傳 placeholder，保持與上游呼叫相容
        return self._degraded_summary(prompt, model)

    def summarize(self, text: str, *, model: Optional[str] = None, timeout: Optional[float] = None) -> str:
        # 與 analyze 共用邏輯
        return self.analyze(text, model=model, timeout=timeout)
