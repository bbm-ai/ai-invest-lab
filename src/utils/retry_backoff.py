import time
from typing import Callable, Any, Tuple

def retry_with_backoff(
    fn: Callable[[], Tuple[str, dict]],
    *,
    retries: int = 2,
    backoff_sec: float = 1.0
) -> Tuple[str, dict, int]:
    """
    執行 fn() -> (status, payload)，在 status == "ERROR" 時重試，最多 retries 次。
    傳回 (final_status, final_payload, attempts_used)
    """
    attempt = 0
    status, payload = "ERROR", {}
    while attempt <= retries:
        status, payload = fn()
        if status != "ERROR":
            return status, payload, (attempt + 1)
        time.sleep(backoff_sec * (2 ** attempt))
        attempt += 1
    return status, payload, attempt
