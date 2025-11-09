import os, random, time

"""
Fault injection helper.
環境變數控制：
  FAULT_MODE: none | groq_timeout | groq_429 | gemini_timeout | gemini_dns | all_random
  FAULT_PROB: 0.0~1.0 (default 0.8)
  FAULT_LATENCY_MS:  模擬延遲（毫秒），預設 0
"""

def _prob() -> float:
    try:
        return max(0.0, min(1.0, float(os.getenv("FAULT_PROB", "0.8"))))
    except Exception:
        return 0.8

def _sleep_ms():
    ms = int(os.getenv("FAULT_LATENCY_MS", "0"))
    if ms > 0:
        time.sleep(ms / 1000.0)

def should_fault(provider: str, fault_type: str) -> bool:
    mode = os.getenv("FAULT_MODE", "none").strip().lower()
    if mode in ("", "none"): 
        return False
    _sleep_ms()
    p = _prob()
    if mode == "all_random":
        return random.random() < p
    # 精準模式
    if provider == "groq" and mode == f"groq_{fault_type}":
        return random.random() < p
    if provider == "gemini" and mode == f"gemini_{fault_type}":
        return random.random() < p
    return False
