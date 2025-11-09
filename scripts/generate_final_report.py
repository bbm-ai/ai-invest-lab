#!/usr/bin/env python3
import os, sqlite3, pathlib, datetime as dt, textwrap, json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "ai_invest.sqlite3"
REP = ROOT / "reports"
REP.mkdir(parents=True, exist_ok=True)

def q(con, sql, params=()):
    cur = con.cursor(); cur.execute(sql, params); return cur.fetchall()

def read_last7_llm(con):
    sql = """
    SELECT date(ts) AS d, provider,
           COUNT(*) AS calls,
           SUM(status='OK') AS ok,
           SUM(status='ERROR') AS err,
           SUM(status='SKIP') AS skip
    FROM llm_costs
    WHERE ts >= datetime('now','-7 day')
    GROUP BY d, provider
    ORDER BY d DESC, provider;
    """
    return q(con, sql)

def read_route_mix_24h(con):
    sql = """
    SELECT route_primary AS route, COUNT(*)
    FROM llm_costs
    WHERE ts >= datetime('now','-1 day')
    GROUP BY route ORDER BY COUNT(*) DESC;
    """
    return q(con, sql)

def read_error_heads_24h(con):
    sql = """
    SELECT substr(COALESCE(error,''),1,60) AS head, COUNT(*)
    FROM llm_costs
    WHERE ts >= datetime('now','-1 day') AND status='ERROR'
    GROUP BY head ORDER BY COUNT(*) DESC LIMIT 12;
    """
    return q(con, sql)

def read_strategies_last(con, days=7):
    sql = """
    SELECT date, symbol, recommendation, position_size, confidence
    FROM strategies
    WHERE date >= date('now', ?)
    ORDER BY date DESC, symbol;
    """
    return q(con, (f'-{days} day',))

def load_config():
    p = ROOT / "config.yaml"
    try:
        return p.read_text(encoding="utf-8")
    except:
        return "(config.yaml not found)"

def main():
    if not DB.exists():
        print(json.dumps({"error": f"DB not found: {DB}"})); return
    con = sqlite3.connect(DB)

    now = dt.datetime.now().isoformat(timespec="seconds")
    out = REP / "final_report.md"

    llm7 = read_last7_llm(con)
    mix = read_route_mix_24h(con)
    errs = read_error_heads_24h(con)
    strat = read_strategies_last(con, 7)

    # 回測彙整（若有）
    bt = []
    bt_path = REP / "backtest_readout.md"
    if bt_path.exists():
        bt.append(bt_path.name)
    # 成本報表（若有）
    cost7 = []
    cost7_path = REP / "m2_costs_last7d.md"
    if cost7_path.exists():
        cost7.append(cost7_path.name)

    md = []
    md.append(f"# Final Project Report\n\n_Generated at: {now}_\n")
    md.append("## 1. 總覽\n- 自動化：Systemd + Cron（ET 17:05）\n- DB：SQLite（prices/news/sentiments/tech_signals/strategies/llm_costs）\n- 路由：Groq/Gemini + Claude（策略性升級）\n- 儀表板：Streamlit（Mobile-friendly）\n")

    md.append("## 2. LLM Routing & Cost（近 7 天）\n")
    if llm7:
        md.append("| Day | Provider | Calls | OK | ERROR | SKIP |")
        md.append("|---|---|---:|---:|---:|---:|")
        for d,p,c,ok,er,sk in llm7:
            md.append(f"| {d} | {p} | {c} | {ok} | {er} | {sk} |")
    else:
        md.append("_No records in last 7 days._")

    md.append("\n### 24h Route mix\n")
    if mix:
        md.append("| Route | Count |"); md.append("|---|---:|")
        for r, n in mix:
            md.append(f"| {r} | {n} |")
    else:
        md.append("_No records in 24h._")

    md.append("\n### 24h Error samples\n")
    if errs:
        md.append("| Error(head) | Count |"); md.append("|---|---:|")
        for h, n in errs:
            md.append(f"| {h} | {n} |")
    else:
        md.append("_No errors in 24h._")

    md.append("\n## 3. Strategies（近 7 天）\n")
    if strat:
        md.append("| Date | Symbol | Rec | Size | Conf |"); md.append("|---|---|---|---:|---:|")
        for d,s,rec,pos,conf in strat:
            md.append(f"| {d} | {s} | {rec} | {pos:.2f} | {conf:.2f} |")
    else:
        md.append("_No strategies in last 7 days._")

    md.append("\n## 4. 回測/報表附件\n")
    attaches = []
    attaches += bt
    attaches += cost7
    if attaches:
        for a in attaches: md.append(f"- {a}")
    else:
        md.append("- (無)")

    md.append("\n## 5. 設定快照（config.yaml）\n```yaml\n")
    md.append(load_config())
    md.append("\n```\n")

    md.append("## 6. 既知事項與後續 Roadmap\n- （示例）完善策略版本管理與滾動回測\n- （示例）Streamlit 登入與角色分權\n- （示例）引入雲端冷備份（GCS/S3）\n- （示例）任務級重試與可觀測性（OpenTelemetry / traces）\n")

    out.write_text("\n".join(md), encoding="utf-8")
    print({"report": str(out)})

if __name__ == "__main__":
    main()
