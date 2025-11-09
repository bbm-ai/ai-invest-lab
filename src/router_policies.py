import sqlite3, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"

def count_today_claude_calls() -> int:
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
                      cap_limit: int, enable: bool,
                      min_conf: float, sent_ext: float) -> tuple[bool, str]:
    """
    回傳 (use_claude, reason)
    觸發條件（且 enable=True 且未達今日 cap）：
      - 低置信度（conf < min_conf），或
      - 情緒極端（|avg_sent| >= sent_ext）且與趨勢衝突（up↔negative / down↔positive）
    """
    if not enable:
        return False, "Claude disabled"

    used = count_today_claude_calls()
    if used >= cap_limit:
        return False, f"Claude cap reached ({used}/{cap_limit})"

    low_conf = (conf is None) or (conf < float(min_conf))
    tl = (trend_label or "").lower()
    extreme = abs(avg_sent) >= float(sent_ext)
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
