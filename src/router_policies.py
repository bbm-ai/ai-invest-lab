import os, sqlite3, pathlib, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"

def count_today_claude_calls() -> int:
    """回傳今天已記錄的 claude 呼叫數（OK/ERROR/SKIP 都算嘗試）。"""
    if not DB.exists():
        return 0
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""
      SELECT COUNT(*) FROM llm_costs
      WHERE date(ts)=date('now','localtime')
        AND provider='claude'
        AND status IN ('OK','ERROR','SKIP')
    """)
    n = cur.fetchone()[0]
    con.close()
    return int(n or 0)

def should_use_claude(*, conf: float, avg_sent: float, trend_label: str,
                      cap_limit: int, enable: bool) -> tuple[bool, str]:
    """
    回傳 (use_claude, reason)

    觸發條件（且 enable=True 且未達今日 cap）：
      - 低置信度（conf < POLICY_MIN_CONF，預設 0.55），或
      - 情緒極端（|avg_sent| >= POLICY_SENTIMENT_EXTREME，預設 0.40）且與趨勢衝突（up↔negative / down↔positive）
    """
    if not enable:
        return False, "Claude disabled"

    used = count_today_claude_calls()
    if used >= cap_limit:
        return False, f"Claude cap reached ({used}/{cap_limit})"

    # 閾值可由環境變數覆蓋
    min_conf = float(os.getenv("POLICY_MIN_CONF", "0.55"))
    sent_ext = float(os.getenv("POLICY_SENTIMENT_EXTREME", "0.40"))

    low_conf = (conf is None) or (conf < min_conf)
    tl = (trend_label or "").lower()
    extreme = abs(avg_sent) >= sent_ext
    conflict = extreme and (
        (avg_sent > 0 and tl == "down") or
        (avg_sent < 0 and tl == "up")
    )

    if low_conf or conflict:
        reason = []
        if low_conf:
            reason.append(f"low_conf({conf})")
        if conflict:
            reason.append("trend_sentiment_conflict")
        return True, ",".join(reason)

    return False, "no_escalation_needed"
