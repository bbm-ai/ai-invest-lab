from typing import Any, Dict

class APIRouter:
    def __init__(self, clients: Dict[str, Any]):
        self.c = clients  # {"groq": g, "gemini": ge, "gemini_flash": gf, "claude": c}

    def call(self, task: str, payload: Dict[str, Any]) -> Any:
        plan = {
            "news_summary": ["groq", "gemini_flash"],
            "technical_analysis": ["gemini_flash", "groq"],
            "high_confidence_decision": ["claude", "gemini"]
        }.get(task, ["groq", "gemini_flash"])

        last_err = None
        for key in plan:
            try:
                return self.c[key].run(payload)
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"APIRouter failover exhausted: {last_err}")

    def should_use_claude(self, context: Dict[str, Any]) -> bool:
        return (
            context.get("confidence", 1.0) < 0.6
            or context.get("vix", 0) >= 25
            or context.get("disagreement_score", 0) >= 0.4
        )
