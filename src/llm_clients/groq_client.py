class GroqClient:
    """Minimal Groq client wrapper.
    缺 GROQ_API_KEY 或未安裝 'groq' 套件時，會回傳 {"status":"SKIP"}。
    """
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def summarize(self, text: str, model: str = "llama3-8b", timeout: float = 15.0) -> dict:
        if not self.api_key:
            return {"status": "SKIP", "reason": "GROQ_API_KEY missing"}
        try:
            import groq  # 官方 SDK
        except Exception:
            return {"status": "SKIP", "reason": "groq SDK not installed"}
        try:
            client = groq.Groq(api_key=self.api_key, timeout=timeout)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content": f"Summarize: {text[:4000]}"}],
                temperature=0.3,
            )
            content = resp.choices[0].message.content if resp.choices else ""
            return {"status": "OK", "provider": "groq", "model": model, "output": content}
        except Exception as e:
            return {"status": "ERROR", "provider": "groq", "model": model, "error": str(e)}
