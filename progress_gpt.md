# 📊 Project Progress — AI Agent Team (v2)

## 🧩 專案簡介
本專案旨在建立一個可模組化、可迭代的 AI Agent 團隊，能執行以下任務：
- 代理程式編寫與除錯  
- 與 LLM 對話與決策輔助  
- 收集外部數據（YouTube / X / Gmail）  
- 自動化工作流程（影片 / Podcast 生成）  
- 資料整合與知識抽取  

初期 POC 階段以 **零成本為優先**，部署於 **本地 Ubuntu + Ollama + Gemini CLI**。

---

## ✅ Checklist — Tasks

| ID | 任務 | 狀態 | 備註 |
|----|------|------|------|
| T01 | 環境設定 | ✅ 已完成規劃 | Ubuntu + VSCode + Python + Ollama + Gemini CLI |
| T02 | 數據庫設計 | ⬜ 未開始 | Postgres (本地) |
| T03 | Agent 抽象類 | ⬜ 規劃中 | BaseAgent + 子類架構 |
| T04 | Data Collector (I) | ⬜ 待開始 | YouTube API 初版 |
| T05 | Data Collector (II) | ⬜ 待開始 | X (Twitter) 抓取 |
| T06 | Master Agent | ⬜ 待開始 | 任務協調與資料整合 |
| T07 | Milestone 1 驗收 | ⬜ 未開始 | — |
| T08 | LLM API 整合 | ⚙️ 進行中 | Gemini CLI 作為核心 API |
| T09 | API 智能路由 (I) | ⬜ 規劃中 | Gemini / Groq / Claude |
| T10 | Analyst (I) | ⬜ 未開始 | — |
| T11 | Analyst (II) | ⬜ 未開始 | — |
| T12 | Strategist (I) | ⬜ 未開始 | — |
| T13 | Strategist (II) | ⬜ 未開始 | — |
| T14 | Milestone 2 驗收 | ⬜ 未開始 | — |
| T15 | 自動部署與排程 | ⬜ 未開始 | Systemd / Cron |
| T16 | 健壯性 (I) | ⬜ 未開始 | Failover |
| T17 | 健壯性 (II) | ⬜ 未開始 | 備份 / 告警 |
| T18 | Milestone 3 驗收 | ⬜ 未開始 | — |
| T19 | 性能與回測 (I) | ⬜ 未開始 | — |
| T20 | 可視化儀表板 (I) | ⬜ 未開始 | Streamlit |
| T21 | 專案結案 | ⬜ 未開始 | — |

---

## 🧭 Milestones

### M1 (Day 7) — MVP 基礎完成
- ✅ BaseAgent 架構確立  
- ⚙️ Gemini CLI 語法檢查完成  
- ⬜ YouTube / X 抓取第一輪成功  
- ⬜ 數據入庫  

### M2 (Day 14) — 智能增強
- ⬜ API 路由與成本日誌  
- ⬜ Analyst 模組完成 (情緒/技術摘要)  
- ⬜ Strategist 模組產生策略與信心分數  

### M3 (Day 21) — 部署與優化
- ⬜ Systemd + Cron 長駐任務  
- ⬜ Failover 測試  
- ⬜ 備份 + 告警 OK  
- ⬜ Streamlit 儀表板上線  

---

## 📝 Daily Log

### 2025-11-08 (Asia/Taipei)
進度：完成 **T01**，確定環境架構與 Agent-1 的角色重定義。  
問題 / 風險：尚未確認 Gemini CLI 安裝與指令參數。  
成本：$0（使用本地 Ollama + 免費 Gemini CLI）  
明日目標：
- 安裝並測試 Gemini CLI  
- 完成 Agent-1 語法檢查功能原型  
- 新增 `agents/agent_1.py`  

---

## 🎯 Next Actions
- [ ] 測試 Gemini CLI 在 Python subprocess 中運行
- [ ] 撰寫 `AgentBase` 抽象類
- [ ] 寫入 `agents/agent_1.py` 模組，完成語法檢查功能

---

## 🧾 Changelog
- **v2.1 (2025-11-08)**：初始化 `progress.md`；新增 Agent-1 任務說明與 Gemini CLI 集成計畫  
- **v2 (2025-11-07)**：新增健康檢查與 API 成本監控模組  
- **v1 (2025-11-02)**：專案藍圖初版  
