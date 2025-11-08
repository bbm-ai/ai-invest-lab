# ⚙️ Constants & Thresholds（v2.2, 2025-11-08）
## 成本/路由
- LLM 月成本上限：`$2`
- 日成本告警門檻：`$0.05` (`WARN`), `0.10` (`CRIT`)
- Claude 觸發（高成本路由條件）：`confidence < 0.6` 或 `VIX ≥ 25` 或 `disagreement_score ≥ 0.4`
- 策略低信心告警（Dashboard 用）：`confidence < 0.5`
- 供應商逾時門檻：`3s`；最大重試：`2 次`；退避：`等比 + 抖動`


## 可靠性/SLO
- 可用性：`≥ 99%`
- Cron 準點率：`≥ 99%`
- Failover 成功率：`≥ 95%`
- Pipeline 完成時間：`< 5 分鐘`
- **LLM/LLM/API P50**：`< 3s`

## 風險/策略
- MaxDD 目標：`≤ 20%`
- 單日風險（1d VaR@95%）：`≤ 1.5% NAV`
- 單日虧損硬上限：`1% NAV`
- 單一標的曝險：`≤ 30% NAV`；行業：`≤ 50% NAV`
