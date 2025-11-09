# app/streamlit_app.py
import os
import pathlib
import sqlite3
import datetime as dt
import pandas as pd
import streamlit as st

# --- Paths & constants ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
DB_PATH = os.environ.get("AI_INVEST_DB", str(ROOT / "data" / "ai_invest.sqlite3"))

st.set_page_config(
    page_title="AI Invest Lab — Dashboard",
    page_icon="📈",
    layout="wide",
)

# --- Small helpers ---
def get_conn():
    return sqlite3.connect(DB_PATH)

@st.cache_data(show_spinner=False, ttl=60)
def read_sql(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Read SQL safely with optional date parsing heuristic."""
    with get_conn() as con:
        try:
            df = pd.read_sql_query(query, con, params=params)
        except Exception as e:
            st.warning(f"SQL error: {e}")
            df = pd.DataFrame()
    return df

def latest_strategy_date() -> str | None:
    df = read_sql("SELECT MAX(date) AS d FROM strategies")
    if df.empty or pd.isna(df.loc[0, "d"]):
        return None
    return str(df.loc[0, "d"])

# sentiments 沒有 date 欄，改以 news.published_at 或 sentiments.created_at 做聚合
@st.cache_data(show_spinner=False, ttl=60)
def sentiments_timeseries_last30() -> pd.DataFrame:
    q = """
    SELECT date(COALESCE(n.published_at, s.created_at, 'now')) AS d,
           AVG(s.score) AS avg_sent
    FROM sentiments s
    LEFT JOIN news n ON n.id = s.news_id
    GROUP BY date(COALESCE(n.published_at, s.created_at, 'now'))
    ORDER BY d DESC
    LIMIT 30
    """
    df = read_sql(q).rename(columns={"d": "date"})
    if df.empty:
        # 兜底（有些環境沒有 sentiments.created_at）
        q2 = """
        SELECT date(COALESCE(n.published_at, 'now')) AS d,
               AVG(s.score) AS avg_sent
        FROM sentiments s
        JOIN news n ON n.id = s.news_id
        GROUP BY date(COALESCE(n.published_at, 'now'))
        ORDER BY d DESC
        LIMIT 30
        """
        df = read_sql(q2).rename(columns={"d": "date"})
    return df

@st.cache_data(show_spinner=False, ttl=60)
def strategies_of(day: str) -> pd.DataFrame:
    q = """
    SELECT date, symbol, recommendation, position_size, confidence, reasoning
    FROM strategies
    WHERE date = date(?)
    ORDER BY symbol
    """
    return read_sql(q, (day,))

@st.cache_data(show_spinner=False, ttl=60)
def tech_signals_of(day: str) -> pd.DataFrame:
    # 這個 schema 來自 Day10 之後的擴充：rsi_14 / macd / macd_signal / macd_hist / trend_label / summary
    q = """
    SELECT symbol, date, rsi_14, macd, macd_signal, macd_hist, trend_label, summary
    FROM tech_signals
    WHERE date = date(?)
    ORDER BY symbol
    """
    return read_sql(q, (day,))

@st.cache_data(show_spinner=False, ttl=60)
def llm_cost_24h() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """三個表：provider彙總、route彙總、錯誤樣本"""
    q1 = """
    WITH last24 AS (
        SELECT * FROM llm_costs
        WHERE ts >= datetime('now','-24 hours')
    )
    SELECT provider,
           COUNT(*) AS calls,
           SUM(CASE WHEN status='OK' THEN 1 ELSE 0 END) AS ok,
           SUM(CASE WHEN status='ERROR' THEN 1 ELSE 0 END) AS err,
           SUM(CASE WHEN status='SKIP' THEN 1 ELSE 0 END) AS skip
    FROM last24
    GROUP BY provider
    ORDER BY calls DESC;
    """
    q2 = """
    WITH last24 AS (
        SELECT * FROM llm_costs
        WHERE ts >= datetime('now','-24 hours')
    )
    SELECT route_primary AS route, COUNT(*) AS n
    FROM last24
    GROUP BY route
    ORDER BY n DESC;
    """
    q3 = """
    WITH last24 AS (
        SELECT * FROM llm_costs
        WHERE ts >= datetime('now','-24 hours') AND status='ERROR'
    )
    SELECT substr(COALESCE(error,''),1,70) AS error_head, COUNT(*) AS n
    FROM last24
    GROUP BY error_head
    ORDER BY n DESC
    LIMIT 12;
    """
    return read_sql(q1), read_sql(q2), read_sql(q3)

@st.cache_data(show_spinner=False, ttl=60)
def backtest_readout(day: str) -> pd.DataFrame:
    q = """
    SELECT symbol AS Symbol,
           ROUND(position_size, 2) AS Pos
    FROM strategies
    WHERE date = date(?)
    ORDER BY symbol
    """
    pos = read_sql(q, (day,))
    # 嘗試載入回測報告（若已由 scripts/backtest_runner.py 產生）
    report_path = ROOT / "reports" / f"backtest_readout.md"
    if report_path.exists():
        # 簡單回讀報表中的表格（可視化我們仍顯示當日的倉位）
        pass
    return pos

def kpi_box(label: str, value: str | float, help_: str | None = None):
    st.metric(label, value, help=help_)

# --- UI ---
def main():
    st.title("🤖 AI Invest Lab — Dashboard")
    st.caption(f"DB: `{DB_PATH}`")

    # 取得當日（或最新）策略日期
    latest_day = latest_strategy_date()
    day = st.sidebar.date_input(
        "Strategy Day",
        value=dt.date.fromisoformat(latest_day) if latest_day else dt.date.today(),
        min_value=dt.date(2020, 1, 1),
        max_value=dt.date.today(),
        format="YYYY-MM-DD",
    )
    day_str = day.strftime("%Y-%m-%d")

    tab_overview, tab_strategy, tab_backtest = st.tabs(["Overview", "Strategies", "Backtest"])

    # --- Overview ---
    with tab_overview:
        st.subheader("LLM Routing & Ops (last 24h)")

        # KPI
        df_p, df_r, df_e = llm_cost_24h()
        col1, col2, col3, col4 = st.columns(4)
        total_calls = int(df_p["calls"].sum()) if not df_p.empty else 0
        total_ok = int(df_p["ok"].sum()) if not df_p.empty else 0
        total_err = int(df_p["err"].sum()) if not df_p.empty else 0
        total_skip = int(df_p["skip"].sum()) if not df_p.empty else 0
        with col1: kpi_box("Calls(24h)", total_calls)
        with col2: kpi_box("OK(24h)", total_ok)
        with col3: kpi_box("ERROR(24h)", total_err)
        with col4: kpi_box("SKIP(24h)", total_skip)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**By Provider**")
            if df_p.empty:
                st.info("No data in last 24h.")
            else:
                st.dataframe(df_p, width="stretch")
        with c2:
            st.markdown("**Route Mix**")
            if df_r.empty:
                st.info("No route data.")
            else:
                st.dataframe(df_r, width="stretch")

        st.markdown("**Error Samples (head)**")
        if df_e.empty:
            st.success("No errors in last 24h. 🎉")
        else:
            st.dataframe(df_e, width="stretch")

        st.divider()
        st.subheader("Sentiment (avg by published date) — last 30 days")
        sent = sentiments_timeseries_last30()
        if not sent.empty:
            # 轉成時間序列圖
            sent_sorted = sent.sort_values("date")
            sent_sorted["date"] = pd.to_datetime(sent_sorted["date"])
            st.line_chart(
                sent_sorted.set_index("date")["avg_sent"],
                x=None,
                y=None,
                height=240,
            )
            st.dataframe(sent, width="stretch")
        else:
            st.info("No sentiments data yet.")

    # --- Strategies ---
    with tab_strategy:
        st.subheader(f"Daily Strategies — {day_str}")
        df_s = strategies_of(day_str)
        if df_s.empty:
            st.info("No strategies for this day.")
        else:
            # 主表
            st.dataframe(df_s, width="stretch")

            # 技術指標
            st.markdown("**Technical Signals**")
            df_t = tech_signals_of(day_str)
            if df_t.empty:
                st.info("No tech signals for this day.")
            else:
                st.dataframe(df_t, width="stretch")

    # --- Backtest ---
    with tab_backtest:
        st.subheader("Backtest Preview (positions of selected day)")
        df_pos = backtest_readout(day_str)
        if df_pos.empty:
            st.info("No strategy positions for backtest preview.")
        else:
            st.dataframe(df_pos, width="stretch")
            st.caption("完整回測與績效圖請使用 `scripts/backtest_runner.py` 產生 Markdown 報告。")

    st.divider()
    with st.expander("About this dashboard"):
        st.markdown(
            """
**Notes**
- 情緒時間序列改以 `news.published_at` 聚合，不再依賴 `sentiments.date` 欄位。
- `st.dataframe(..., use_container_width=True)` 已改為 `width="stretch"`，避免 2025-12-31 後的退場警告。
- 24h LLM Routing 取自 `llm_costs`，若資料不足會顯示空表或提示。
            """
        )

if __name__ == "__main__":
    # 明確列出 Python 環境資訊於 logs（可視需要加上）
    st.sidebar.caption(f"Python: {os.environ.get('VIRTUAL_ENV','system')} / DB: {DB_PATH}")
    main()
