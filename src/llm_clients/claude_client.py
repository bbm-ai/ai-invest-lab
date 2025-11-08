class ClaudeClient:
    """Minimal Anthropic client wrapper（缺 API 或 SDK → SKIP）"""
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def analyze(self, prompt: str, model: str = "claude-3-5-haiku-latest", timeout: float = 15.0) -> dict:
        if not self.api_key:
            return {"status": "SKIP", "reason": "ANTHROPIC_API_KEY missing"}
        try:
            import anthropic
        except Exception:
            return {"status": "SKIP", "reason": "anthropic SDK not installed"}
        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            msg = client.messages.create(
                model=model, max_tokens=400, temperature=0.2,
                messages=[{"role":"user","content": prompt}],
            )
            text = ""
            if getattr(msg, "content", None):
                for p in msg.content:
                    if getattr(p, "type", "") == "text":
                        text += p.text
            return {"status": "OK", "provider":"claude", "model": model, "output": text}
        except Exception as e:
            return {"status": "ERROR", "provider":"claude", "model": model, "error": str(e)}
