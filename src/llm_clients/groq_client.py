import os, time
from src.llm_costs_log import log_call
from src.utils.faults import should_fault

class GroqClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

    def summarize(self, text: str, route_primary: str = "primary", timeout: float | None = None):
        t0 = time.time()
        model = os.getenv("GROQ_MODEL", "gpt-oss:20B")
        provider = "groq"

        if not self.api_key:
            log_call("news_summary", provider, model, "SKIP", route_primary, "GROQ_API_KEY missing")
            return {"status": "SKIP", "reason": "GROQ_API_KEY missing"}

        # Fault injection
        if should_fault(provider, "timeout"):
            time.sleep(1.0 + (timeout or 0)/2)
            log_call("news_summary", provider, model, "ERROR", route_primary, "simulated timeout")
            raise TimeoutError("groq simulated timeout")

        if should_fault(provider, "429"):
            log_call("news_summary", provider, model, "ERROR", route_primary, "simulated 429")
            raise RuntimeError("groq simulated 429")

        # 假輸出
        time.sleep(0.05)
        latency = int((time.time() - t0) * 1000)
        log_call("news_summary", provider, model, "OK", route_primary, None)
        return {"status": "OK", "model": model, "latency_ms": latency, "summary": text[:120]}
