from dataclasses import dataclass

@dataclass
class RouteDecision:
    provider: str   # 'groq' | 'gemini'
    model: str      # model name
    reason: str     # why

SIMPLE = {"news_summary"}                       # 低成本任務（摘要/重寫）
COMPLEX = {"tech_summary", "strategy_synthesis"}  # 需要較強推理/結構化

def route(task_type: str) -> RouteDecision:
    t = (task_type or '').strip().lower()
    if t in SIMPLE:
        return RouteDecision(provider="groq", model="gpt-oss:20B", reason="Low-cost summarization")
    if t in COMPLEX:
        return RouteDecision(provider="gemini", model="gemini-2.5-flash", reason="Structured/long-context analysis")
    # 預設：省錢路線
    return RouteDecision(provider="groq", model="gpt-oss:20B", reason="Default fallback")

def next_best(decision: RouteDecision) -> RouteDecision:
    """提供固定的備援選擇，用於 Failover。"""
    if decision.provider == "groq":
        return RouteDecision(provider="gemini", model="gemini-2.5-flash", reason="Failover from groq")
    return RouteDecision(provider="groq", model="gpt-oss:20B", reason="Failover from gemini")

def escalate_to_claude(decision: RouteDecision, claude_model: str = "claude-3-5-haiku-latest") -> RouteDecision:
    """將路由升級到 Claude（保留 reason）。"""
    return RouteDecision(provider="claude", model=claude_model, reason=f"Escalate from {decision.provider} due to policy")
