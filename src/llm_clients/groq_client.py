from __future__ import annotations
import os
from typing import Optional, Dict, Any

class GroqClient:
    """
    輕量相容版：
    - __init__(api_key: Optional[str]) 可不傳，會讀 GROQ_API_KEY
    - summarize/analyze(text|prompt, *, model=None, timeout=None) 允許 model/timeout
    - 回傳 dict(status, content)；沒金鑰回 SKIP（不中斷 Pipeline）
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()

    def _ok(self, text: str, model: Optional[str]) -> Dict[str, Any]:
        head = (text or "").replace("\n", " ").strip()[:200]
        tag = model or "default"
        return {"status": "OK", "content": f"[groq:{tag}] {head}"}

    def _skip(self, reason: str) -> Dict[str, Any]:
        return {"status": "SKIP", "content": reason}

    def _error(self, reason: str) -> Dict[str, Any]:
        return {"status": "ERROR", "content": reason}

    def analyze(self, prompt: str, *, model: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        if not self.api_key:
            return self._skip("GROQ_API_KEY missing")
        return self._ok(prompt, model)

    def summarize(self, text: str, *, model: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        if not self.api_key:
            return self._skip("GROQ_API_KEY missing")
        return self._ok(text, model)
