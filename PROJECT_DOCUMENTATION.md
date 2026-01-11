# 📊 QQQ 決策系統 - 完整專案文件

> **版本**: 3.0  
> **最後更新**: 2025-01-11  
> **維護者**: AI Investment Team

---

## 📋 目錄

1. [系統概覽](#1-系統概覽)
2. [架構設計](#2-架構設計)
3. [模組說明](#3-模組說明)
4. [資料流程](#4-資料流程)
5. [部署指南](#5-部署指南)
6. [日常操作 SOP](#6-日常操作-sop)
7. [除錯指南](#7-除錯指南)
8. [擴展指南](#8-擴展指南)
9. [交易策略模組化](#9-交易策略模組化)
10. [Prompt 工程指南](#10-prompt-工程指南)
11. [版本迭代流程](#11-版本迭代流程)
12. [附錄](#12-附錄)

---

## 1. 系統概覽

### 1.1 系統目標

提供一個**自動化、可量化、可驗證**的 QQQ ETF 投資決策系統。

### 1.2 核心功能

| 功能 | 說明 | 執行頻率 |
|------|------|----------|
| 每日分析 | 盤後抓取數據、計算評分、產生配置建議 | 每日 22:30 |
| 每日驗證 | 驗證前日預測是否正確 | 每日 09:35 |
| 週末覆盤 | 統計週績效、計算 Alpha | 每週六 10:00 |
| 風控監控 | 監控 VIX > 40 或單日跌幅 > 4% | 即時 |

### 1.3 技術棧

```
┌─────────────────────────────────────────────────────────────┐
│                        QQQ 決策系統 v3.0                      │
├─────────────────────────────────────────────────────────────┤
│  自動化層     │  GitHub Actions (Cron Scheduler)            │
│  運算層       │  Python 3.11 (yfinance, pandas, numpy)      │
│  儲存層       │  Google Sheets (8 工作表)                    │
│  API 層       │  Google Apps Script (REST API)              │
│  通知層       │  Telegram Bot API                           │
│  展示層       │  HTML/JS Dashboard (GitHub Pages)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 架構設計

### 2.1 系統架構圖

```
                          ┌─────────────────┐
                          │   使用者/投資人   │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
             ┌──────────┐  ┌──────────┐  ┌──────────┐
             │ Telegram │  │Dashboard │  │  Sheets  │
             │   通知    │  │  儀表板   │  │  原始數據 │
             └──────────┘  └────┬─────┘  └──────────┘
                                │              ▲
                                │              │
                          ┌─────┴─────┐       │
                          │  GAS API  │───────┘
                          └─────┬─────┘
                                │
                    ┌───────────┴───────────┐
                    │    Google Sheets      │
                    │  ┌─────────────────┐  │
                    │  │ Daily_Logs      │  │
                    │  │ Factor_Scores   │  │
                    │  │ Validations     │  │
                    │  │ Weekly_Reviews  │  │
                    │  │ Risk_Events     │  │
                    │  │ Notifications   │  │
                    │  │ Config          │  │
                    │  │ Weights         │  │
                    │  └─────────────────┘  │
                    └───────────┬───────────┘
                                ▲
                                │
                    ┌───────────┴───────────┐
                    │    GitHub Actions     │
                    │  ┌─────────────────┐  │
                    │  │ daily_analysis  │  │
                    │  │ daily_validation│  │
                    │  │ weekly_review   │  │
                    │  └─────────────────┘  │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │  Python Analyzer      │
                    │  ┌─────────────────┐  │
                    │  │ MarketDataFetch │  │
                    │  │ TechnicalAnalyz │  │
                    │  │ FactorScorer    │  │
                    │  │ Notifier        │  │
                    │  └─────────────────┘  │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │   外部數據源           │
                    │  ┌─────────────────┐  │
                    │  │ Yahoo Finance   │  │
                    │  │ (QQQ, VIX, TNX) │  │
                    │  └─────────────────┘  │
                    └───────────────────────┘
```

### 2.2 模組分離原則

```
┌────────────────────────────────────────────────────────────────┐
│                         分層架構                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐    單一職責原則 (SRP)                        │
│  │  數據抓取     │    • 每個類別只負責一件事                     │
│  │  MarketData  │    • 修改一個功能不影響其他功能                │
│  └──────┬───────┘                                              │
│         │                                                      │
│  ┌──────▼───────┐    開放封閉原則 (OCP)                        │
│  │  技術分析     │    • 對擴展開放（新增因子）                    │
│  │  Technical   │    • 對修改封閉（不改核心邏輯）                 │
│  └──────┬───────┘                                              │
│         │                                                      │
│  ┌──────▼───────┐    依賴注入 (DI)                             │
│  │  因子評分     │    • 權重從外部注入                           │
│  │  FactorScore │    • 策略可替換                               │
│  └──────┬───────┘                                              │
│         │                                                      │
│  ┌──────▼───────┐    介面隔離 (ISP)                            │
│  │  輸出/通知    │    • GAS 和 Telegram 獨立                    │
│  │  Notifier    │    • 可單獨啟用/停用                          │
│  └──────────────┘                                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. 模組說明

### 3.1 Python 模組 (`qqq_analyzer.py`)

```python
# 模組結構
qqq_analyzer.py
├── Config              # 設定類別（從環境變數讀取）
├── MarketDataFetcher   # 市場數據抓取
├── TechnicalAnalyzer   # 技術指標計算
├── FactorScorer        # 因子評分引擎
├── GASClient           # Google Sheets API 通訊
├── TelegramNotifier    # Telegram 通知
├── run_daily_analysis()    # 每日分析主函數
├── run_daily_validation()  # 每日驗證主函數
└── run_weekly_review()     # 週末覆盤主函數
```

#### 3.1.1 MarketDataFetcher

```python
class MarketDataFetcher:
    """
    職責: 抓取市場數據
    數據源: Yahoo Finance (yfinance)
    
    方法:
    - fetch_quote(ticker) -> Dict    # 單一標的報價
    - fetch_historical(ticker, period) -> DataFrame  # 歷史數據
    - fetch_all() -> Dict            # 所有需要的數據
    
    支援標的:
    - QQQ: Nasdaq 100 ETF
    - ^VIX: 恐慌指數
    - ^TNX: 10年期美債殖利率
    - ^IRX: 3個月美債殖利率
    - DX-Y.NYB: 美元指數
    """
```

#### 3.1.2 TechnicalAnalyzer

```python
class TechnicalAnalyzer:
    """
    職責: 計算技術指標
    
    指標:
    - MA5, MA20, MA60: 移動平均線
    - RSI(14): 相對強弱指標
    - Volume Ratio: 成交量比率 (vs 20日均量)
    - Support/Resistance: 20日支撐/壓力位
    - Position vs MA: 價格相對均線位置
    """
```

#### 3.1.3 FactorScorer

```python
class FactorScorer:
    """
    職責: 計算因子評分
    
    因子 (5個):
    ┌─────────────────┬────────┬─────────────────────┐
    │ 因子            │ 權重   │ 評分邏輯            │
    ├─────────────────┼────────┼─────────────────────┤
    │ price_momentum  │ 30%    │ 漲跌幅 + 均線位置   │
    │ volume          │ 20%    │ 量價配合判斷        │
    │ vix             │ 20%    │ VIX 水位 + 變化     │
    │ bond            │ 15%    │ 10Y殖利率變化       │
    │ mag7            │ 15%    │ 權重股表現(用QQQ代理)│
    └─────────────────┴────────┴─────────────────────┘
    
    評分範圍: 1-10 分
    
    狀態判斷:
    - score <= 3.5: defense (防禦)
    - score <= 6.5: neutral (中性)
    - score > 6.5: offense (進攻)
    """
```

### 3.2 Google Apps Script 模組 (`Code.gs`)

```javascript
// GAS 模組結構
Code.gs
├── doPost(e)           // POST 請求處理
│   ├── daily_log       // 寫入每日日誌
│   ├── factor_scores   // 寫入因子評分
│   ├── validation      // 寫入驗證記錄
│   ├── weekly_review   // 寫入週報
│   ├── risk_event      // 寫入風控事件
│   └── notification    // 寫入通知記錄
│
├── doGet(e)            // GET 請求處理
│   ├── latest          // 取得最新數據
│   ├── history         // 取得歷史數據
│   ├── weights         // 取得當前權重
│   ├── validations     // 取得驗證記錄
│   ├── weekly_reviews  // 取得週報
│   └── health          // 健康檢查
│
└── Utilities           // 工具函數
    ├── sendTelegram()  // 發送 Telegram
    └── onOpen()        // 選單建立
```

### 3.3 GitHub Actions Workflows

```yaml
# Workflow 結構
.github/workflows/
├── daily_analysis.yml      # 每日分析 (22:30 週一至週五)
├── daily_validation.yml    # 每日驗證 (09:35 週二至週六)
└── weekly_review.yml       # 週末覆盤 (10:00 週六)
```

---

## 4. 資料流程

### 4.1 每日分析流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     每日分析流程 (22:30)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 觸發                                                        │
│     GitHub Actions Cron: '30 14 * * 1-5' (UTC)                 │
│                          ↓                                      │
│  2. 環境準備                                                     │
│     Setup Python → Install Dependencies                        │
│                          ↓                                      │
│  3. 數據抓取                                                     │
│     MarketDataFetcher.fetch_all()                              │
│     • QQQ 價格、成交量                                           │
│     • VIX 數值                                                  │
│     • 10Y 殖利率                                                │
│     • DXY 美元指數                                              │
│                          ↓                                      │
│  4. 技術分析                                                     │
│     TechnicalAnalyzer.analyze()                                │
│     • MA5, MA20, MA60                                          │
│     • RSI(14)                                                  │
│     • Volume Ratio                                             │
│     • Support/Resistance                                       │
│                          ↓                                      │
│  5. 因子評分                                                     │
│     FactorScorer.score_all()                                   │
│     • 5 個因子獨立評分                                           │
│     • 加權計算總分                                               │
│     • 判斷 regime (offense/neutral/defense)                    │
│                          ↓                                      │
│  6. 配置計算                                                     │
│     FactorScorer.get_allocation()                              │
│     • 根據評分決定 QQQ%                                          │
│     • 計算止損價位                                               │
│                          ↓                                      │
│  7. 輸出生成                                                     │
│     生成標準化 JSON + 通知文字                                    │
│                          ↓                                      │
│  8. 數據發送                                                     │
│     GASClient.send('daily_log', data)                          │
│     GASClient.send('factor_scores', data)                      │
│                          ↓                                      │
│  9. 通知發送                                                     │
│     TelegramNotifier.send(notification)                        │
│                          ↓                                      │
│  10. 完成                                                       │
│      保存 output.json 為 Artifact                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 每日驗證流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     每日驗證流程 (09:35)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 讀取前日預測                                                 │
│     GASClient.get('history', days=5)                           │
│     • 取得 predicted_direction                                  │
│     • 取得 qqq_pct 配置                                         │
│                          ↓                                      │
│  2. 取得今日實際數據                                              │
│     MarketDataFetcher.fetch_quote('QQQ')                       │
│     • 今日收盤價                                                 │
│     • 今日漲跌幅                                                 │
│                          ↓                                      │
│  3. 比對結果                                                     │
│     • 預測方向 vs 實際方向                                        │
│     • 判斷預測是否正確                                            │
│                          ↓                                      │
│  4. 計算損益                                                     │
│     PnL = 漲跌% × QQQ配置%                                      │
│     PnL金額 = 本金 × PnL%                                       │
│                          ↓                                      │
│  5. 記錄驗證結果                                                  │
│     GASClient.send('validation', data)                         │
│                          ↓                                      │
│  6. 發送通知                                                     │
│     TelegramNotifier.send(validation_report)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 週末覆盤流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     週末覆盤流程 (週六 10:00)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 取得本週數據                                                 │
│     GASClient.get('history', days=7)                           │
│     過濾本週一至週五的記錄                                        │
│                          ↓                                      │
│  2. 計算績效指標                                                 │
│     • 週報酬 (組合加權)                                          │
│     • QQQ 原始報酬                                              │
│     • Alpha = 週報酬 - QQQ報酬                                  │
│     • 勝率 = 獲利天數 / 總天數                                   │
│     • 盈虧比 = 平均獲利 / 平均虧損                                │
│     • 最大回撤                                                   │
│                          ↓                                      │
│  3. 計算預測準確率                                                │
│     準確率 = 正確預測數 / 總預測數                                │
│                          ↓                                      │
│  4. 權重變動分析                                                 │
│     比較週初 vs 週末的因子評分變化                                │
│                          ↓                                      │
│  5. 記錄週報                                                     │
│     GASClient.send('weekly_review', data)                      │
│                          ↓                                      │
│  6. 發送週報通知                                                 │
│     TelegramNotifier.send(weekly_report)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 部署指南

### 5.1 前置需求

- GitHub 帳號
- Google 帳號
- Telegram 帳號

### 5.2 部署清單

```
□ Step 1: Google Sheets
  □ 建立新試算表
  □ 建立 8 個工作表 (見 5.3)
  □ 記下 Sheet ID

□ Step 2: Google Apps Script
  □ 擴充功能 → Apps Script
  □ 貼上 GAS 程式碼
  □ 部署為網頁應用程式
  □ 記下部署 URL

□ Step 3: Telegram Bot
  □ 與 @BotFather 對話
  □ /newbot 建立 Bot
  □ 記下 Bot Token
  □ 取得 Chat ID

□ Step 4: GitHub Repository
  □ 建立 Repository
  □ 上傳 qqq_analyzer.py
  □ 上傳 requirements.txt
  □ 建立 .github/workflows/
  □ 設定 Secrets (GAS_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

□ Step 5: Dashboard (可選)
  □ 上傳 index.html
  □ 啟用 GitHub Pages

□ Step 6: 測試
  □ 手動執行 Daily Analysis
  □ 手動執行 Daily Validation
  □ 手動執行 Weekly Review
  □ 確認所有數據正確
```

### 5.3 Google Sheets 工作表結構

```
┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Daily_Logs                                              │
├─────────────────────────────────────────────────────────────────┤
│ date | weekday | close | change_pct | volume_vs_20ma | vix |   │
│ vix_change_pct | us10y | us2y | dxy | resistance | support |   │
│ total_score | regime | qqq_pct | cash_pct | qqq_amount |       │
│ cash_amount | prediction | confidence | stop_loss |             │
│ factor_scores | full_json | created_at                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Factor_Scores                                           │
├─────────────────────────────────────────────────────────────────┤
│ date | factor | score | direction | weight | weighted_score    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Validations                                             │
├─────────────────────────────────────────────────────────────────┤
│ date | prediction_date | predicted_direction | actual_direction │
│ actual_change_pct | is_correct | pnl_pct | pnl_amount |        │
│ prev_qqq_pct | prev_close | today_close | created_at           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Weekly_Reviews                                          │
├─────────────────────────────────────────────────────────────────┤
│ week_start | week_end | trading_days | starting_nav |          │
│ ending_nav | week_return | qqq_return | alpha | win_rate |     │
│ win_days | lose_days | profit_loss_ratio | max_drawdown |      │
│ prediction_accuracy | correct_predictions | total_predictions | │
│ weight_changes | review_notes | created_at                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Risk_Events                                             │
├─────────────────────────────────────────────────────────────────┤
│ date | event_type | trigger_value | threshold | action_taken | │
│ avoided_loss | missed_gain | net_benefit                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Notifications                                           │
├─────────────────────────────────────────────────────────────────┤
│ timestamp | type | channel | message | status                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Config                                                  │
├─────────────────────────────────────────────────────────────────┤
│ key                  | value                                    │
│ ─────────────────────┼────────────────────────                  │
│ system_version       | 3.0                                      │
│ initial_capital      | 10000000                                 │
│ ticker               | QQQ                                      │
│ risk_preference      | neutral                                  │
│ auto_mode            | TRUE                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 工作表: Weights                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Factor         | Current | Min  | Max  | Last_Updated | By     │
│ ───────────────┼─────────┼──────┼──────┼──────────────┼─────── │
│ price_momentum | 0.30    | 0.10 | 0.40 | 2025-01-11   | manual │
│ volume         | 0.20    | 0.10 | 0.40 | 2025-01-11   | manual │
│ vix            | 0.20    | 0.10 | 0.40 | 2025-01-11   | manual │
│ bond           | 0.15    | 0.10 | 0.40 | 2025-01-11   | manual │
│ mag7           | 0.15    | 0.10 | 0.40 | 2025-01-11   | manual │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 日常操作 SOP

### 6.1 每日檢查 (建議 23:00)

```
□ 1. 確認 Telegram 收到盤後報告
□ 2. 查看評分和配置建議
□ 3. 如有風控警報，立即處理
□ 4. 記錄個人決策（是否跟隨系統）
```

### 6.2 每週覆盤 (週六)

```
□ 1. 確認收到週報通知
□ 2. 檢視 Dashboard 績效圖表
□ 3. 分析預測準確率
□ 4. 評估是否需要調整權重
□ 5. 更新 review_notes
```

### 6.3 每月維護 (每月 1 日)

```
□ 1. 備份 Google Sheets
□ 2. 匯出歷史數據 (JSON)
□ 3. 檢查 GitHub Actions 執行記錄
□ 4. 更新系統版本（如有）
□ 5. 評估策略效果
```

### 6.4 異常處理 SOP

#### 6.4.1 Workflow 執行失敗

```
1. 檢查 GitHub Actions 錯誤日誌
2. 常見原因:
   - Yahoo Finance API 暫時無法連線 → 重新執行
   - Secrets 過期 → 更新 Secrets
   - 程式碼錯誤 → 檢查最近的修改
3. 修復後手動觸發 Workflow
```

#### 6.4.2 Telegram 沒收到通知

```
1. 檢查 Workflow 是否成功
2. 確認 TELEGRAM_BOT_TOKEN 正確
3. 確認 TELEGRAM_CHAT_ID 正確
4. 測試: GAS → 選單 → 測試 Telegram
```

#### 6.4.3 Google Sheets 沒有數據

```
1. 檢查 GAS_URL 是否正確
2. 測試: 瀏覽器開啟 GAS_URL?action=health
3. 確認 GAS 已部署為「所有人」可存取
4. 確認 GAS 程式碼是最新版本
```

---

## 7. 除錯指南

### 7.1 日誌查看

```
# GitHub Actions 日誌
Repository → Actions → 選擇 Workflow → 選擇 Run → 查看 Logs

# GAS 日誌
Apps Script → 執行項目 → 查看執行記錄
```

### 7.2 常見錯誤對照表

| 錯誤訊息 | 原因 | 解決方法 |
|----------|------|----------|
| `No file matched to [requirements.txt]` | 檔案路徑錯誤 | 確認檔案在根目錄 |
| `GAS_URL not set` | 環境變數未設定 | 設定 GitHub Secrets |
| `No data` | Yahoo Finance 無回應 | 重新執行或檢查標的代碼 |
| `Sheet not found` | 工作表名稱錯誤 | 確認工作表名稱正確 |
| `Telegram error` | Bot Token 錯誤 | 重新取得 Token |

### 7.3 本地測試

```bash
# 設定環境變數
export GAS_URL="your_gas_url"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 執行測試
python qqq_analyzer.py           # 每日分析
python qqq_analyzer.py --validate  # 每日驗證
python qqq_analyzer.py --weekly    # 週末覆盤
python qqq_analyzer.py --all       # 全部執行
```

---

## 8. 擴展指南

### 8.1 新增數據源

```python
# 在 MarketDataFetcher 新增方法
class MarketDataFetcher:
    @staticmethod
    def fetch_new_source():
        """
        新增數據源範例
        """
        # 1. 呼叫 API
        # 2. 解析數據
        # 3. 返回標準格式
        pass
```

### 8.2 新增因子

```python
# 在 FactorScorer 新增評分方法
class FactorScorer:
    def score_new_factor(self, data: Dict) -> Dict:
        """
        新增因子範例
        
        Returns:
            {"score": 1-10, "direction": "bullish/bearish/neutral"}
        """
        # 1. 取得相關數據
        # 2. 評分邏輯
        # 3. 返回結果
        pass
```

### 8.3 新增通知管道

```python
# 新增 LINE 通知
class LINENotifier:
    @staticmethod
    def send(message: str) -> bool:
        # LINE Notify 實作
        pass

# 新增 Slack 通知
class SlackNotifier:
    @staticmethod
    def send(message: str) -> bool:
        # Slack Webhook 實作
        pass
```

### 8.4 新增標的

```python
# 複製並修改設定
Config.TICKER = "SPY"  # 或 "TQQQ", "SQQQ"

# 可能需要調整的部分:
# 1. 因子權重
# 2. 評分閾值
# 3. 風控參數
```

---

## 9. 交易策略模組化

### 9.1 策略結構

```python
# strategies/base.py
class BaseStrategy:
    """策略基類"""
    
    name: str = "base"
    version: str = "1.0"
    
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights
    
    def score(self, data: Dict) -> Dict:
        """計算評分 - 子類別必須實作"""
        raise NotImplementedError
    
    def get_allocation(self, score: float) -> Dict:
        """計算配置 - 子類別必須實作"""
        raise NotImplementedError
```

```python
# strategies/momentum.py
class MomentumStrategy(BaseStrategy):
    """動能策略"""
    
    name = "momentum"
    version = "1.0"
    
    def score(self, data: Dict) -> Dict:
        # 動能策略評分邏輯
        pass
```

```python
# strategies/mean_reversion.py
class MeanReversionStrategy(BaseStrategy):
    """均值回歸策略"""
    
    name = "mean_reversion"
    version = "1.0"
    
    def score(self, data: Dict) -> Dict:
        # 均值回歸評分邏輯
        pass
```

### 9.2 策略註冊

```python
# strategies/registry.py
STRATEGIES = {
    "default": DefaultStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}

def get_strategy(name: str) -> BaseStrategy:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")
    return STRATEGIES[name]
```

### 9.3 新增策略 SOP

```
1. 建立策略類別
   - 繼承 BaseStrategy
   - 實作 score() 方法
   - 實作 get_allocation() 方法

2. 註冊策略
   - 在 STRATEGIES 字典新增

3. 測試策略
   - 使用歷史數據回測
   - 驗證評分邏輯

4. 部署策略
   - 更新 Config.STRATEGY
   - 或透過環境變數切換
```

---

## 10. Prompt 工程指南

### 10.1 Prompt 模板結構

```markdown
# [策略名稱] Prompt Template

## 角色設定
你是一個專業的量化交易分析師，專精於...

## 輸入數據
- QQQ 收盤價: {close}
- 漲跌幅: {change_pct}%
- VIX: {vix}
- ...

## 分析任務
1. 分析當前市場狀態
2. 評估各因子表現
3. 給出多空評分 (1-10)
4. 建議配置比例

## 輸出格式
```json
{
  "score": 7.5,
  "regime": "offense",
  "allocation": {"qqq": 70, "cash": 30},
  "reasoning": "..."
}
```

## 限制條件
- 評分必須在 1-10 之間
- 配置總和必須為 100%
- 必須提供理由
```

### 10.2 Prompt 版本控制

```
prompts/
├── v1.0/
│   ├── daily_analysis.md
│   ├── validation.md
│   └── weekly_review.md
├── v1.1/
│   ├── daily_analysis.md
│   └── CHANGELOG.md
└── current -> v1.1
```

### 10.3 Prompt 迭代流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Prompt 迭代流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 識別問題                                                     │
│     • 預測準確率下降                                              │
│     • 評分不穩定                                                  │
│     • 邏輯不一致                                                  │
│                          ↓                                      │
│  2. 分析原因                                                     │
│     • 檢視錯誤案例                                                │
│     • 比較預測 vs 實際                                            │
│     • 識別模式                                                   │
│                          ↓                                      │
│  3. 修改 Prompt                                                 │
│     • 調整角色設定                                                │
│     • 優化輸入格式                                                │
│     • 增加限制條件                                                │
│     • 提供更多範例                                                │
│                          ↓                                      │
│  4. A/B 測試                                                    │
│     • 新舊 Prompt 並行                                           │
│     • 比較輸出品質                                                │
│     • 統計準確率                                                  │
│                          ↓                                      │
│  5. 部署 & 監控                                                  │
│     • 更新版本號                                                  │
│     • 記錄變更                                                   │
│     • 持續監控效果                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.4 Prompt 最佳實踐

```
✅ DO:
  • 明確定義角色和專業領域
  • 提供結構化的輸入數據
  • 指定明確的輸出格式
  • 包含具體的範例
  • 設定合理的限制條件
  • 要求解釋理由

❌ DON'T:
  • 使用模糊的指令
  • 省略重要的上下文
  • 忽略邊界情況
  • 過於複雜的單一 Prompt
  • 缺乏版本控制
```

---

## 11. 版本迭代流程

### 11.1 版本號規則

```
版本格式: MAJOR.MINOR.PATCH

MAJOR: 重大架構變更，不向後相容
MINOR: 新功能，向後相容
PATCH: Bug 修復，向後相容

範例:
- 3.0.0: 新增驗證和週報功能
- 3.1.0: 新增 LINE 通知
- 3.1.1: 修復 VIX 評分 bug
```

### 11.2 發布流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        發布流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 開發分支                                                     │
│     git checkout -b feature/new-feature                        │
│                          ↓                                      │
│  2. 開發 & 測試                                                  │
│     • 本地測試                                                   │
│     • 更新文件                                                   │
│     • 更新版本號                                                  │
│                          ↓                                      │
│  3. Code Review                                                 │
│     • 自我審查                                                   │
│     • 檢查邊界情況                                                │
│                          ↓                                      │
│  4. 合併到 main                                                 │
│     git checkout main                                          │
│     git merge feature/new-feature                              │
│                          ↓                                      │
│  5. 部署                                                        │
│     • 更新 GAS（如有）                                           │
│     • 推送到 GitHub                                              │
│     • 手動測試一次                                                │
│                          ↓                                      │
│  6. 監控                                                        │
│     • 觀察首次自動執行                                            │
│     • 確認無錯誤                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.3 回滾流程

```bash
# 如果新版本有問題

# 1. 找到上一個正常的 commit
git log --oneline

# 2. 回滾
git revert HEAD

# 3. 推送
git push

# 4. 更新 GAS（如有變更）
```

---

## 12. 附錄

### 12.1 檔案清單

```
ai-invest-lab/
├── qqq_analyzer.py          # 主程式
├── requirements.txt         # Python 依賴
├── .github/
│   └── workflows/
│       ├── daily_analysis.yml
│       ├── daily_validation.yml
│       └── weekly_review.yml
├── docs/
│   └── PROJECT.md           # 本文件
├── prompts/                 # Prompt 模板 (可選)
│   └── v1.0/
└── strategies/              # 策略模組 (可選)
    └── base.py
```

### 12.2 重要連結

| 項目 | 連結 |
|------|------|
| GitHub Repository | `https://github.com/你的用戶名/ai-invest-lab` |
| Google Sheets | `https://docs.google.com/spreadsheets/d/SHEET_ID/edit` |
| GAS URL | `https://script.google.com/macros/s/.../exec` |
| Dashboard | `https://你的用戶名.github.io/ai-invest-lab/` |

### 12.3 聯絡與支援

```
問題回報: GitHub Issues
文件更新: Pull Request
緊急問題: Telegram @你的用戶名
```

---

## 📝 變更日誌

### v3.0.0 (2025-01-11)
- ✨ 新增每日驗證功能
- ✨ 新增週末覆盤功能
- ✨ 新增 Dashboard
- 📝 新增完整專案文件

### v2.0.0 (2025-01-10)
- 🚀 初始版本
- ✨ 每日分析功能
- ✨ 因子評分系統
- ✨ Telegram 通知

---

**文件結束**
