class GeminiClient:
    """Minimal Gemini client wrapper.
    缺 GEMINI_API_KEY 或未安裝 'google-generativeai' 套件時，會回傳 {"status":"SKIP"}。
    """
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    def analyze(self, text: str, model: str = "gemini-1.5-flash", timeout: float = 15.0) -> dict:
        if not self.api_key:
            return {"status": "SKIP", "reason": "GEMINI_API_KEY missing"}
        try:
            import google.generativeai as genai
        except Exception:
            return {"status": "SKIP", "reason": "google-generativeai SDK not installed"}
        try:
            genai.configure(api_key=self.api_key)
            m = genai.GenerativeModel(model)
            resp = m.generate_content(f"Analyze: {text[:4000]}")
            output = getattr(resp, "text", None) or (
                resp.candidates[0].content.parts[0].text
                if getattr(resp, "candidates", None) else ""
            )
            return {"status": "OK", "provider": "gemini", "model": model, "output": output}
        except Exception as e:
            return {"status": "ERROR", "provider": "gemini", "model": model, "error": str(e)}
