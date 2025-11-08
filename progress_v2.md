📊 Project Progress (AI 專業投資團隊) — v2 模板

使用方式：

每完成任務卡就勾選；
每日填寫「Daily Log」與「Next Actions」；
重大變更請在「Changelog」紀錄，並用 Git tag 做節點。


✅ Checklist — Tasks

 T01 環境設定
 T02 數據庫設計
 T03 Agent 抽象類
 T04 Data Collector (I)
 T05 Data Collector (II)
 T06 Master Agent
 T07 Milestone 1 驗收
 T08 LLM API 整合
 T09 API 智能路由 (I)
 T10 Analyst (I)
 T11 Analyst (II)
 T12 Strategist (I)
 T13 Strategist (II)
 T14 Milestone 2 驗收
 T15 自動部署與排程
 T16 健壯性 (I) — Failover
 T17 健壯性 (II) — 備份/告警
 T18 Milestone 3 驗收
 T19 性能與回測 (I)
 T20 可視化儀表板 (I)
 T21 專案結案

🧭 Milestones
M1 (Day 7) — MVP 基礎完成：

 端到端收集一次成功
 SPY 價/量 & 新聞入庫
BaseAgent 介面穩定

M2 (Day 14) — 智能增強：

 APIRouter 分流/成本日誌
 Analyst 情緒 & 技術摘要
 Strategist 策略含倉位/信心
should_use_claude 生效

M3 (Day 21) — 部署與優化：

 Systemd + Cron 24/7 (TZ=America/New_York)
 Failover 測試通過
 備份/告警 OK
 Streamlit 儀表板上線

📝 Daily Log (樣板)
YYYY-MM-DD (Local: Asia/Taipei)

進度：完成 T0x …
問題 / 風險：… (含暫解/待解)
成本：Groq X tokens / Gemini X tokens / Claude X tokens
明日目標：…

🎯 Next Actions (滾動 3 項)

…
…
…

🧪 KPIs

成本/月：$≤2（free tier 優先）
可用性：≥ 99%（以健康檢查結果計算）
延遲：API 回應 P50 < 3s
策略品質：7 日/30 日回測 Sharpe、MaxDD（於 Backtester 報告）

🛡️ Risk & Mitigation

VM 停機 → Systemd 自啟 + 雲備援筆記
API 額度 → 路由優先順序 + qps 限制 + 重試退避
數據品質 → 多源比對/去重/缺值補全

🧾 Reports

reports/backtest_report.md
docs/system_architecture.md
logs/api_usage_summary.csv

🧱 Changelog

v3 (2025-11-08): 更新通知渠道至 Telegram/Slack/Email、新增 GLM LLM、加入初始資本與 VOO benchmark。
v2 (2025-11-07): 新增 Inputs/Outputs、Failover 細節、健康檢查/備份/告警、報告清單；對齊時區與 Cron 指南。
v1 (2025-11-02): 初版 21 天藍圖。