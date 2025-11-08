from src.utils.env import load_env
load_env()

def call_provider(dec, text):
    """回傳 (status, payload_dict, latency_ms)；status ∈ {OK, ERROR, SKIP}"""
    start = time.time()
    if dec.provider == "groq":
        out = GroqClient(os.getenv("GROQ_API_KEY")).summarize(text, model=dec.model, timeout=15.0)
    else:
        out = GeminiClient(os.getenv("GEMINI_API_KEY")).analyze(text, model=dec.model, timeout=15.0)
    latency_ms = int((time.time() - start) * 1000)
    status = out.get("status", "ERROR")
    return status, out, latency_ms

def run_task(task_type: str, text: str):
    primary = route(task_type)

    # 定義一次呼叫（供 retry 使用）
    def once():
        status, out, latency = call_provider(primary, text)
        # SKIP/OK 直接結束；ERROR 交給 retry
        return status, {"out": out, "latency_ms": latency}

    status, payload, attempts = retry_with_backoff(once, retries=2, backoff_sec=1.0)
    out = payload["out"]; latency = payload["latency_ms"]

    if status == "ERROR":
        # 執行備援
        backup = next_best(primary)
        b_status, b_out, b_latency = call_provider(backup, text)
        # 成本紀錄（primary 失敗）
        log_cost(task_type=task_type, provider=primary.provider, model=primary.model,
                 status=status, latency_ms=latency, route_primary="primary",
                 error=str(out.get("error") or out.get("reason")))
        # 成本紀錄（backup 結果）
        log_cost(task_type=task_type, provider=backup.provider, model=backup.model,
                 status=b_status, latency_ms=b_latency, route_primary="backup",
                 error=str(b_out.get("error") or b_out.get("reason")))
        return {"primary": primary.__dict__, "result": out,
                "backup": backup.__dict__, "backup_result": b_out}

    else:
        # 成本紀錄（primary 成功或 SKIP）
        log_cost(task_type=task_type, provider=primary.provider, model=primary.model,
                 status=status, latency_ms=latency, route_primary="primary",
                 error=str(out.get("error") or out.get("reason")))
        return {"primary": primary.__dict__, "result": out, "attempts": attempts}

if __name__ == "__main__":
    demo = "Stocks rose after jobs report; tech mixed; yields eased."
    for task in ["news_summary", "tech_summary", "strategy_synthesis"]:
        print(run_task(task, demo))
