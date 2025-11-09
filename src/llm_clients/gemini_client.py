import os, time
from src.llm_costs_log import log_call
from src.utils.faults import should_fault

class GeminiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def analyze(self, payload: dict, route_primary: str = "primary", timeout: float | None = None):
        t0 = time.time()
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        provider = "gemini"

        if not self.api_key:
            log_call(payload.get("task","tech_summary"), provider, model, "SKIP", route_primary, "GEMINI_API_KEY missing")
            return {"status": "SKIP", "reason": "GEMINI_API_KEY missing"}

        # Fault injection
        if should_fault(provider, "timeout"):
            time.sleep(1.0 + (timeout or 0)/2)
            log_call(payload.get("task","tech_summary"), provider, model, "ERROR", route_primary, "simulated timeout")
            raise TimeoutError("gemini simulated timeout")

        if should_fault(provider, "dns"):
            log_call(payload.get("task","tech_summary"), provider, model, "ERROR", route_primary, "simulated dns")
            raise RuntimeError("gemini simulated dns failure")

        time.sleep(0.05)
        latency = int((time.time() - t0) * 1000)
        log_call(payload.get("task","tech_summary"), provider, model, "OK", route_primary, None)
        return {"status": "OK", "model": model, "latency_ms": latency, "result": {"ok": True, "echo": payload}}
