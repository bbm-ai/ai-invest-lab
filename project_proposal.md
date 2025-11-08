# 🤖 AI 專業投資團隊 - 完整專案企劃書

## 📋 專案概述

### 專案名稱
**AI Investment Team - 自我迭代智能投資系統**

### 專案願景
建立一個完全自主運作的 AI 投資團隊，能夠 24/7 自動收集市場數據、分析趨勢、制定策略，並持續自我優化，最終達到專業投資團隊的決策水平。

### 核心目標
- **零成本運行**：完全使用免費資源（MVP 階段）
- **自主運作**：無需人工干預，自動循環執行
- **可擴展性**：模塊化設計，易於添加新 Agent
- **手機友好**：隨時隨地監控和管理
- **數據驅動**：所有決策基於數據分析

---

## 🎯 專案階段規劃

### Phase 0: 準備階段（Day 1-2）
**目標：環境準備和資源申請**

#### 交付成果
- [x] GitHub Repository 建立
- [x] 所有免費 API Keys 申請完成
- [x] Google Cloud VM 創建
- [x] 專案結構建立
- [x] 文檔系統建立

#### 驗收標準
- GitHub repo 可正常訪問
- 所有 API keys 已測試可用
- VM 可 SSH 連接
- 基礎目錄結構完整

---

### Phase 1: MVP 基礎架構（Day 3-7）
**目標：建立可運行的最小系統**

#### 1.1 數據收集模塊（Day 3-4）
**負責 Agent：Data Collector**

**功能需求：**
- 從 Yahoo Finance 收集 SPY ETF 價格
- 收集成交量數據
- 存儲到 SQLite
- 錯誤處理和日誌記錄

**技術實現：**
```python
class DataCollector:
    def collect_price_data(symbol: str) -> dict
    def store_to_db(data: dict) -> bool
    def log_execution() -> None
```

**驗收標準：**
- 能成功獲取實時價格
- 數據正確存入 SQLite
- 日誌文件記錄完整
- 錯誤能自動重試

#### 1.2 數據存儲系統（Day 4-5）
**數據庫設計：SQLite**

**表結構：**
```sql
-- 價格數據表
CREATE TABLE prices (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分析結果表
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    signal TEXT,  -- buy/sell/hold
    confidence REAL,
    indicators JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 執行日誌表
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY,
    agent_name TEXT NOT NULL,
    task_name TEXT,
    status TEXT,  -- success/failed/running
    message TEXT,
    execution_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略決策表
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    recommendation TEXT,
    reasoning TEXT,
    risk_level TEXT,
    position_size REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**驗收標準：**
- 所有表創建成功
- 索引優化完成
- 查詢性能測試通過
- 備份機制建立

#### 1.3 Master Agent 調度系統（Day 5-6）
**核心控制器**

**功能需求：**
- 讀取配置文件
- 調度其他 Agents
- 監控執行狀態
- 錯誤恢復機制
- 狀態持久化

**工作流程：**
```
1. 啟動時讀取上次狀態
2. 檢查當前時間和任務計劃
3. 決定下一個要執行的任務
4. 調用相應的 Agent
5. 記錄執行結果
6. 保存狀態
7. 等待下一個週期
```

**配置文件格式：**
```yaml
# config.yaml
project:
  name: "AI Investment Team"
  version: "1.0.0-mvp"
  
investment:
  symbols: ["SPY"]
  risk_level: "moderate"
  strategy: "trend_following"
  
schedule:
  data_collection: "0 */4 * * *"  # 每4小時
  analysis: "0 10,16 * * *"        # 每天2次
  strategy: "0 17 * * 1-5"         # 工作日收盤後
  backup: "0 2 * * *"              # 每天凌晨2點
  
agents:
  data_collector:
    model: "groq"
    priority: 1
  analyst:
    model: "gemini-flash"
    priority: 2
  strategist:
    model: "gemini-pro"
    priority: 3
```

**驗收標準：**
- 能正確解析配置
- 準時執行定時任務
- 狀態保存和恢復正確
- 異常後能自動恢復

#### 1.4 簡單技術分析（Day 6-7）
**Analyst Agent 基礎功能**

**技術指標實現：**
- SMA (簡單移動平均線) 20/50/200
- RSI (相對強弱指標)
- MACD (指數平滑異同移動平均線)
- 成交量分析

**信號生成邏輯：**
```python
def generate_signal(data: pd.DataFrame) -> dict:
    """
    買入信號：
    - SMA20 上穿 SMA50
    - RSI < 30 (超賣)
    - MACD 金叉
    
    賣出信號：
    - SMA20 下穿 SMA50
    - RSI > 70 (超買)
    - MACD 死叉
    """
    signal = analyze_indicators(data)
    confidence = calculate_confidence(signal)
    return {
        'signal': signal,
        'confidence': confidence,
        'indicators': {...}
    }
```

**驗收標準：**
- 指標計算準確
- 信號邏輯正確
- 結果存入數據庫
- 可視化圖表生成

---

### Phase 2: AI 智能增強（Day 8-14）

#### 2.1 Groq API 整合（Day 8-9）
**Data Collector 智能化**

**AI 能力：**
- 新聞摘要和情緒分析
- 異常數據識別
- 自動重試策略優化

**實現方式：**
```python
def analyze_news_sentiment(news_list: list) -> dict:
    prompt = f"""
    分析以下財經新聞，判斷市場情緒：
    {news_list}
    
    返回 JSON 格式：
    {{
        "sentiment": "bullish/bearish/neutral",
        "confidence": 0.0-1.0,
        "key_factors": [...]
    }}
    """
    response = groq_client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_response(response)
```

**驗收標準：**
- Groq API 調用成功
- 響應時間 < 2秒
- 結果格式正確
- 錯誤處理完善

#### 2.2 Gemini API 整合（Day 9-11）
**Analyst Agent 深度分析**

**AI 分析能力：**
- 多維度技術分析
- 形態識別（頭肩頂、雙底等）
- 趨勢預測
- 風險評估

**Prompt 設計：**
```python
ANALYSIS_PROMPT = """
你是一位專業的技術分析師。

當前數據：
- 標的：{symbol}
- 價格：{current_price}
- 技術指標：
  * SMA20: {sma20}
  * RSI: {rsi}
  * MACD: {macd}
- 成交量：{volume}
- 近期走勢：{trend_description}

任務：
1. 分析當前技術形態
2. 識別支撐和阻力位
3. 判斷趨勢方向和強度
4. 給出交易建議

返回 JSON 格式：
{{
    "trend": "上升/下降/橫盤",
    "strength": 0.0-1.0,
    "support_levels": [price1, price2],
    "resistance_levels": [price1, price2],
    "recommendation": "buy/sell/hold",
    "confidence": 0.0-1.0,
    "reasoning": "詳細說明..."
}}
"""
```

**驗收標準：**
- 分析結果合理
- JSON 格式正確
- 推理邏輯清晰
- 存儲到數據庫

#### 2.3 策略生成系統（Day 11-13）
**Strategist Agent**

**策略制定流程：**
```
1. 讀取最新分析結果
2. 評估市場環境
3. 計算風險收益比
4. 確定倉位大小
5. 設定止損止盈
6. 生成執行計劃
```

**Claude API 集成（關鍵決策）：**
```python
def generate_investment_strategy(context: dict) -> dict:
    """
    使用 Claude 做最終決策
    只在關鍵時刻調用（控制成本）
    """
    prompt = f"""
    你是一位資深投資策略師。
    
    當前情況：
    - 技術分析：{context['analysis']}
    - 市場情緒：{context['sentiment']}
    - 風險評估：{context['risk']}
    - 當前持倉：{context['position']}
    
    請制定明日交易策略，包括：
    1. 操作建議（買入/賣出/持有）
    2. 倉位比例
    3. 止損點位
    4. 目標價位
    5. 風險評估
    6. 替代方案
    
    返回詳細的策略報告（Markdown格式）
    """
    
    # 只在必要時調用 Claude
    if should_use_claude(context):
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    else:
        # 使用 Gemini Pro 處理常規決策
        return use_gemini_strategy(context)
```

**驗收標準：**
- 策略邏輯合理
- 風險控制完善
- 報告格式清晰
- 成本控制有效

#### 2.4 報告生成系統（Day 13-14）
**每日投資報告**

**報告內容：**
```markdown
# AI 投資日報 - {date}

## 市場概況
- 標的：{symbol}
- 收盤價：${close_price} ({change}%)
- 成交量：{volume}
- 市場情緒：{sentiment}

## 技術分析
### 趨勢判斷
{trend_analysis}

### 關鍵指標
- RSI: {rsi_value} - {rsi_interpretation}
- MACD: {macd_status}
- 均線系統：{ma_status}

### 支撐/阻力
- 支撐位：${support_levels}
- 阻力位：${resistance_levels}

## 投資建議
### 操作策略
{recommendation}

### 風險提示
{risk_warning}

### 倉位建議
{position_advice}

## 執行計劃
{action_plan}

---
生成時間：{timestamp}
信心水平：{confidence}
```

**自動化流程：**
```python
def generate_daily_report():
    # 1. 收集數據
    data = collect_today_data()
    
    # 2. 運行分析
    analysis = run_analysis(data)
    
    # 3. 生成策略
    strategy = generate_strategy(analysis)
    
    # 4. 使用 Groq 生成報告
    report = groq_generate_report(data, analysis, strategy)
    
    # 5. 保存為 Markdown
    save_report(report, f"reports/daily_{today}.md")
    
    # 6. Push 到 GitHub
    git_push_report()
    
    return report
```

**驗收標準：**
- 報告完整準確
- 格式美觀易讀
- 自動推送 GitHub
- 手機可正常查看

---

### Phase 3: 自動化部署（Day 15-17）

#### 3.1 VM 自動化部署（Day 15）
**一鍵部署腳本**

```bash
#!/bin/bash
# deploy.sh - 完整部署腳本

set -e  # 遇錯即停

echo "🚀 開始部署 AI Investment Team..."

# 1. 系統更新
echo "📦 更新系統套件..."
sudo apt update && sudo apt upgrade -y

# 2. 安裝依賴
echo "📚 安裝依賴..."
sudo apt install -y python3-pip git sqlite3 cron

# 3. Clone 代碼
echo "📥 下載代碼..."
cd ~
git clone https://github.com/YOUR_USERNAME/ai-investment-team.git
cd ai-investment-team

# 4. 安裝 Python 套件
echo "🐍 安裝 Python 套件..."
pip3 install -r requirements.txt

# 5. 創建數據庫
echo "🗄️ 初始化數據庫..."
python3 scripts/init_database.py

# 6. 配置環境變數
echo "🔑 配置 API Keys..."
cp .env.example .env
echo "請編輯 .env 文件填入你的 API Keys"
nano .env

# 7. 測試運行
echo "🧪 測試運行..."
python3 -m pytest tests/

# 8. 設置 systemd 服務
echo "⚙️ 設置系統服務..."
sudo cp deployment/ai-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent

# 9. 設置備份 cron
echo "⏰ 設置定時備份..."
(crontab -l 2>/dev/null; echo "0 2 * * * ~/ai-investment-team/scripts/backup.sh") | crontab -

# 10. 驗證部署
echo "✅ 驗證部署狀態..."
sudo systemctl status ai-agent

echo "🎉 部署完成！"
echo "查看日誌: sudo journalctl -u ai-agent -f"
```

**驗收標準：**
- 腳本無錯誤執行
- 服務正常啟動
- 日誌正確記錄
- 可自動重啟

#### 3.2 GitHub 備份系統（Day 16）
**自動備份腳本**

```bash
#!/bin/bash
# backup.sh - 每日備份腳本

BACKUP_DIR=~/ai-investment-team
DB_FILE=$BACKUP_DIR/data/investment.db
BACKUP_DATE=$(date +%Y%m%d)

cd $BACKUP_DIR

# 1. 備份數據庫
echo "📦 備份數據庫..."
sqlite3 $DB_FILE ".backup backups/investment_${BACKUP_DATE}.db"

# 2. 壓縮舊備份
echo "🗜️ 壓縮備份..."
find backups/ -name "*.db" -mtime +7 -exec gzip {} \;

# 3. 清理超過30天的備份
find backups/ -name "*.gz" -mtime +30 -delete

# 4. Git 提交
echo "📤 推送到 GitHub..."
git add .
git commit -m "Auto backup: ${BACKUP_DATE}" || echo "No changes to commit"
git push origin main

# 5. 記錄日誌
echo "[$(date)] Backup completed" >> logs/backup.log

echo "✅ 備份完成"
```

**驗收標準：**
- 每日自動執行
- GitHub 有備份記錄
- 舊備份正確清理
- 失敗有通知

#### 3.3 監控和告警（Day 17）
**健康檢查系統**

```python
# health_check.py
import sqlite3
import requests
from datetime import datetime, timedelta

def check_system_health():
    """檢查系統健康狀態"""
    
    checks = {
        'database': check_database(),
        'data_freshness': check_data_freshness(),
        'disk_space': check_disk_space(),
        'api_status': check_api_status(),
        'last_backup': check_last_backup()
    }
    
    # 如果有失敗，發送通知
    failed = [k for k, v in checks.items() if not v]
    if failed:
        send_alert(f"Health check failed: {failed}")
    
    return all(checks.values())

def check_data_freshness():
    """檢查數據是否及時更新"""
    conn = sqlite3.connect('data/investment.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT MAX(created_at) 
        FROM prices 
        WHERE date = DATE('now')
    """)
    
    last_update = cursor.fetchone()[0]
    conn.close()
    
    if not last_update:
        return False
    
    # 檢查是否在4小時內更新
    last_time = datetime.fromisoformat(last_update)
    return (datetime.now() - last_time) < timedelta(hours=4)

def send_alert(message: str):
    """發送告警（可擴展為 Email/Telegram）"""
    print(f"⚠️ ALERT: {message}")
    
    # 記錄到日誌
    with open('logs/alerts.log', 'a') as f:
        f.write(f"[{datetime.now()}] {message}\n")
    
    # TODO: 集成 Telegram Bot 或 Email
```

**驗收標準：**
- 每小時自動檢查
- 異常能及時發現
- 告警信息準確
- 日誌記錄完整

---

### Phase 4: 優化和擴展（Day 18-21）

#### 4.1 性能優化（Day 18）
**優化目標：**
- 數據庫查詢速度 < 100ms
- API 調用次數最小化
- 內存使用 < 500MB
- CPU 使用 < 50%

**優化措施：**
```python
# 1. 數據庫索引優化
CREATE INDEX idx_prices_symbol_date ON prices(symbol, date);
CREATE INDEX idx_analysis_date ON analysis(date);

# 2. 查詢結果緩存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_latest_price(symbol: str):
    # 緩存最新價格，避免重複查詢
    pass

# 3. 批量操作
def batch_insert_prices(prices: list):
    # 使用批量插入而不是逐條插入
    conn.executemany("INSERT INTO prices ...", prices)

# 4. API 調用合併
def analyze_batch(symbols: list):
    # 一次 API 調用分析多個標的
    pass
```

#### 4.2 多標的支持（Day 19）
**擴展到多個投資標的**

**支持列表：**
- SPY (S&P 500 ETF)
- QQQ (Nasdaq 100 ETF)
- DIA (Dow Jones ETF)
- IWM (Russell 2000 ETF)

**實現方式：**
```python
# config.yaml 擴展
investment:
  symbols:
    - symbol: "SPY"
      weight: 0.4
      priority: 1
    - symbol: "QQQ"
      weight: 0.3
      priority: 2
    - symbol: "DIA"
      weight: 0.2
      priority: 3
    - symbol: "IWM"
      weight: 0.1
      priority: 4
```

#### 4.3 回測系統（Day 20）
**驗證策略有效性**

```python
class Backtester:
    def __init__(self, strategy, start_date, end_date):
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        
    def run(self):
        """運行回測"""
        results = []
        
        for date in daterange(self.start_date, self.end_date):
            # 獲取歷史數據
            data = get_historical_data(date)
            
            # 運行策略
            signal = self.strategy.generate_signal(data)
            
            # 記錄結果
            results.append({
                'date': date,
                'signal': signal,
                'price': data['close'],
                'return': calculate_return(signal, data)
            })
        
        return self.analyze_results(results)
    
    def analyze_results(self, results):
        """分析回測結果"""
        return {
            'total_return': sum(r['return'] for r in results),
            'win_rate': calculate_win_rate(results),
            'max_drawdown': calculate_max_drawdown(results),
            'sharpe_ratio': calculate_sharpe_ratio(results)
        }
```

#### 4.4 Web 儀表板（Day 21）
**簡單的監控界面**

```python
# dashboard.py - 使用 Streamlit
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.title("🤖 AI Investment Dashboard")

# 1. 實時狀態
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("當前倉位", "持有", delta="SPY")
with col2:
    st.metric("今日收益", "+1.2%", delta="+$120")
with col3:
    st.metric("總收益", "+5.8%", delta="+$580")

# 2. 價格走勢圖
df = load_price_data()
fig = go.Figure(data=[go.Candlestick(
    x=df['date'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close']
)])
st.plotly_chart(fig)

# 3. 最新分析
st.subheader("最新分析")
analysis = load_latest_analysis()
st.json(analysis)

# 4. 歷史報告
st.subheader("歷史報告")
reports = load_reports()
for report in reports:
    with st.expander(report['date']):
        st.markdown(report['content'])
```

---

## 🔧 技術架構詳細設計

### 目錄結構
```
ai-investment-team/
├── agents/
│   ├── __init__.py
│   ├── master.py              # Master Agent
│   ├── data_collector.py      # 數據收集
│   ├── analyst.py             # 技術分析
│   ├── strategist.py          # 策略生成
│   └── reporter.py            # 報告生成
├── api_clients/
│   ├── __init__.py
│   ├── groq_client.py
│   ├── gemini_client.py
│   └── claude_client.py
├── database/
│   ├── __init__.py
│   ├── models.py              # 數據模型
│   ├── schema.sql             # 數據庫結構
│   └── operations.py          # 數據庫操作
├── utils/
│   ├── __init__.py
│   ├── indicators.py          # 技術指標
│   ├── logger.py              # 日誌系統
│   ├── config.py              # 配置管理
│   └── helpers.py             # 輔助函數
├── scripts/
│   ├── init_database.py       # 初始化數據庫
│   ├── backup.sh              # 備份腳本
│   ├── deploy.sh              # 部署腳本
│   └── health_check.py        # 健康檢查
├── tests/
│   ├── test_agents.py
│   ├── test_database.py
│   └── test_indicators.py
├── data/
│   ├── investment.db          # SQLite 數據庫
│   └── cache/                 # 緩存目錄
├── backups/                   # 備份目錄
├── logs/                      # 日誌目錄
├── reports/                   # 報告目錄
├── deployment/
│   ├── ai-agent.service       # systemd 服務
│   └── nginx.conf             # Web 服務器配置
├── docs/
│   ├── API.md                 # API 文檔
│   ├── ARCHITECTURE.md        # 架構文檔
│   └── TASKS.md               # 任務卡
├── config.yaml                # 配置文件
├── .env.example               # 環境變數範例
├── requirements.txt           # Python 依賴
├── README.md                  # 專案說明
└── main.py                    # 主程式入口
```

### 核心模塊說明

#### 1. Master Agent
```python
class MasterAgent:
    """
    職責：
    - 讀取配置和狀態
    - 調度其他 Agents
    - 監控執行狀態
    - 處理異常和恢復
    - 記錄日誌
    """
    
    def __init__(self):
        self.config = load_config()
        self.state = load_state()
        self.scheduler = Scheduler()
        
    def run(self):
        while True:
            task = self.scheduler.get_next_task()
            self.execute_task(task)
            self.save_state()
            time.sleep(60)
```

#### 2. API 智能路由
```python
class APIRouter:
    """
    根據任務類型選擇最合適的 API
    """
    
    def route(self, task_type: str, complexity: str):
        if task_type == "data_collection":
            return self.groq_client  # 免費快速
        elif task_type == "analysis" and complexity == "simple":
            return self.gemini_flash_client  # 便宜
        elif task_type == "analysis" and complexity == "complex":
            return self.gemini_pro_client  # 性價比
        elif task_type == "strategy":
            return self.claude_client  # 最聰明
```

---

## 📊 成本估算

### MVP 階段（Day 1-21）
| 項目 | 費用 |
|------|------|
| Google Cloud VM | $0 (Free Tier) |
| GitHub | $0 (Public Repo) |
| Groq API | $0 (完全免費) |
| Gemini API | $0 (免費額度) |
| Claude API | $0-2 (免費額度內) |
| **總計** | **$0-2/月** |

### 生產階段預估（3個月後）
| 項目 | 費用 |
|------|------|
| Google Cloud VM | $0 (Free Tier) |
| GitHub | $0 |
| API 調用 | $10-30 |
| 數據源 | $0 (免費 APIs) |
| **總計** | **$10-30/月** |

---

## 🎯 關鍵成功指標（KPI）

### 技術指標
- ✅ 系統正常運行時間 > 99%
- ✅ 數據收集成功率 > 95%
- ✅ API 響應時間 < 2秒
- ✅ 日誌完整性 100%

### 業務指標
- ✅ 每日生成分析報告
- ✅ 信號準確率 > 60%（回測驗證）
- ✅ 最大回撤 < 15%
- ✅ 月度報告完整性 100%

### 成本控制指標
- ✅ 月度成本 < $5 (MVP)
- ✅ API 調用成功率 > 98%
- ✅ 免費額度使用率 < 80%

---

## ⚠️ 風險管理

### 技術風險

**1. VM 停機風險**
- **風險等級：中**
- **應對措施：**
  - 每日自動備份到 GitHub
  - 健康檢查和自動重啟
  - 保留本地和雲端雙份數據
  - 文檔化快速恢復流程

**2. API 額度超限**
- **風險等級：低**
- **應對措施：**
  - 智能路由優先使用免費 API
  - 設置每日調用上限
  - 實時監控用量
  - 多 API 備援機制

**3. 數據丟失**
- **風險等級：低**
- **應對措施：**
  - 每日自動備份
  - 保留 30 天歷史備份
  - GitHub 版本控制
  - 可從免費數據源重新獲取

**4. 代碼錯誤**
- **風險等級：中**
- **應對措施：**
  - 完整的單元測試
  - 詳細的錯誤日誌
  - 自動重試機制
  - 異常告警系統

### 投資風險

**1. 策略失效**
- **風險等級：高**
- **應對措施：**
  - 先進行紙上交易測試
  - 持續回測驗證
  - 設置嚴格止損
  - 人工定期審核

**2. 市場黑天鵝事件**
- **風險等級：中**
- **應對措施：**
  - 分散投資多個標的
  - 限制單一倉位比例
  - 設置最大回撤限制
  - 異常波動自動平倉

---

## 🔄 迭代和維護計劃

### 每日維護（自動化）
```
00:00 - 數據庫備份
04:00 - 收集美股數據
08:00 - 收集亞洲市場數據
10:00 - 運行技術分析
16:00 - 美股收盤後分析
17:00 - 生成每日報告
22:00 - 健康檢查
```

### 每週維護（人工）
- 審閱週報告
- 檢查 API 用量
- 查看錯誤日誌
- 調整配置參數

### 每月維護（人工）
- 性能評估
- 策略回測
- 成本分析
- 功能規劃

---

## 📚 文檔和知識管理

### 必要文檔
1. **README.md** - 專案概述和快速開始
2. **ARCHITECTURE.md** - 系統架構詳細說明
3. **API.md** - API 使用指南
4. **DEPLOYMENT.md** - 部署指南
5. **TASKS.md** - 任務卡系統
6. **TROUBLESHOOTING.md** - 常見問題解決

### 代碼規範
```python
# 所有代碼必須包含：
# 1. 函數/類的 docstring
# 2. 類型提示
# 3. 錯誤處理
# 4. 日誌記錄

def example_function(param: str) -> dict:
    """
    函數說明
    
    Args:
        param: 參數說明
        
    Returns:
        返回值說明
        
    Raises:
        ValueError: 錯誤情況說明
    """
    try:
        logger.info(f"執行功能: {param}")
        result = do_something(param)
        return result
    except Exception as e:
        logger.error(f"錯誤: {e}")
        raise
```

---

## 🎓 學習和改進計劃

### Phase 5: 進階功能（Week 4-6）
- [ ] 多時間框架分析（日線、週線、月線）
- [ ] 基本面數據整合（財報、估值）
- [ ] 機器學習預測模型
- [ ] 投資組合優化
- [ ] 實時價格追蹤

### Phase 6: 專業化（Week 7-12）
- [ ] 期權策略
- [ ] 風險平價配置
- [ ] 量化因子模型
- [ ] 高頻數據分析
- [ ] 另類數據源（衛星、社交媒體）

---

## 🤝 協作和溝通

### 狀態報告格式
```markdown
## 日期：2024-XX-XX

### 今日完成
- [x] 任務 1
- [x] 任務 2

### 遇到的問題
- 問題描述
- 解決方案

### 明日計劃
- [ ] 任務 3
- [ ] 任務 4

### 指標
- 系統運行時間：23.5h
- API 調用次數：150
- 今日成本：$0.05
```

### 決策記錄（ADR）
重要技術決策需記錄原因：
```markdown
# ADR-001: 選擇 SQLite 而非 PostgreSQL

## 狀態
已接受

## 背景
需要選擇數據庫系統

## 決策
使用 SQLite

## 原因
1. 完全免費
2. 無需額外服務器
3. 性能足夠（單用戶）
4. 易於備份

## 後果
- 優點：零成本、簡單
- 缺點：不支持高併發

## 替代方案
PostgreSQL（被拒絕，因為成本）
```

---

## 🎯 階段性里程碑

### Milestone 1: 基礎可運行（Day 7）
**驗收標準：**
- [x] 能自動收集 SPY 價格數據
- [x] 數據正確存入 SQLite
- [x] Master Agent 能調度任務
- [x] 基礎日誌系統工作

**演示內容：**
- 展示實時數據收集
- 展示數據庫內容
- 展示日誌記錄

### Milestone 2: AI 分析可用（Day 14）
**驗收標準：**
- [x] Groq API 正常工作
- [x] Gemini 技術分析準確
- [x] 能生成每日報告
- [x] 報告推送到 GitHub

**演示內容：**
- 展示 AI 分析結果
- 展示生成的報告
- 展示 GitHub 上的報告

### Milestone 3: 完整部署（Day 17）
**驗收標準：**
- [x] VM 上 24/7 自動運行
- [x] 每日自動備份
- [x] 健康檢查正常
- [x] 手機可查看報告

**演示內容：**
- 展示系統持續運行
- 展示自動備份流程
- 展示手機查看體驗

### Milestone 4: 優化完成（Day 21）
**驗收標準：**
- [x] 支持多個標的
- [x] 回測系統可用
- [x] 性能達標
- [x] Web 儀表板可訪問

**演示內容：**
- 展示多標的分析
- 展示回測結果
- 展示儀表板界面

---

## 📞 支援和問題解決

### 常見問題快速索引

**Q: VM 突然停止運行？**
```bash
# 1. 檢查服務狀態
sudo systemctl status ai-agent

# 2. 查看日誌
sudo journalctl -u ai-agent -n 50

# 3. 重啟服務
sudo systemctl restart ai-agent
```

**Q: 數據收集失敗？**
```python
# 檢查 API 連接
python3 -c "import yfinance as yf; print(yf.download('SPY', period='1d'))"

# 檢查網路
ping -c 3 finance.yahoo.com
```

**Q: API 超過限制？**
```python
# 查看用量
python3 scripts/check_api_usage.py

# 切換到備用 API
# 編輯 config.yaml，調整 API 優先級
```

**Q: 數據庫損壞？**
```bash
# 從備份恢復
cp backups/investment_YYYYMMDD.db data/investment.db

# 或從 GitHub 拉取
git pull origin main
```

---

## 🔐 安全性考慮

### API Key 管理
```bash
# 永遠不要將 API keys 提交到 GitHub
# 使用 .env 文件（已在 .gitignore）

# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxx
CLAUDE_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxxxxxx

# 確保 .env 權限
chmod 600 .env
```

### GitHub Token 權限
最小權限原則：
- ✅ repo (讀寫代碼)
- ✅ workflow (觸發 Actions)
- ❌ admin (不需要)
- ❌ delete (不需要)

### VM 安全
```bash
# 1. 定期更新系統
sudo apt update && sudo apt upgrade

# 2. 配置防火牆（只允許 SSH）
sudo ufw enable
sudo ufw allow ssh
sudo ufw status

# 3. 禁用不必要的服務
sudo systemctl list-units --type=service
```

---

## 🚀 未來展望

### 短期目標（3個月）
- 穩定運行 MVP 系統
- 積累至少 3 個月的數據
- 驗證策略有效性
- 優化 AI prompts

### 中期目標（6個月）
- 擴展到 10+ 個投資標的
- 實現多策略並行
- 建立完整的回測系統
- 開發移動端 App

### 長期目標（12個月）
- 完整的 AI 投資團隊（15+ Agents）
- 支持全球多個市場
- 實盤小額交易驗證
- 策略商業化可能性

---

## 📊 專案時間表總覽

```
Week 1: 基礎建設
├─ Day 1-2: 環境準備
├─ Day 3-4: 數據收集
├─ Day 5-6: Master Agent
└─ Day 7: Milestone 1 ✓

Week 2: AI 集成
├─ Day 8-9: Groq 整合
├─ Day 10-11: Gemini 整合
├─ Day 12-13: 策略生成
└─ Day 14: Milestone 2 ✓

Week 3: 部署優化
├─ Day 15: 自動部署
├─ Day 16: 備份系統
├─ Day 17: Milestone 3 ✓
├─ Day 18-19: 性能優化
├─ Day 20: 回測系統
└─ Day 21: Milestone 4 ✓

Week 4+: 持續改進
└─ 根據實際情況調整
```

---

## ✅ 專案檢查清單

### 啟動前
- [ ] GitHub Repository 已建立
- [ ] 所有 API Keys 已申請
- [ ] Google Cloud 帳號已設置
- [ ] VM 已創建（免費層）
- [ ] 文檔結構已建立

### 開發中
- [ ] 代碼遵循規範
- [ ] 所有函數有文檔
- [ ] 錯誤處理完善
- [ ] 日誌記錄完整
- [ ] 測試用例通過

### 部署前
- [ ] 所有環境變數已設置
- [ ] 數據庫已初始化
- [ ] 備份系統已測試
- [ ] 健康檢查正常
- [ ] 文檔已更新

### 運行中
- [ ] 每日檢查日誌
- [ ] 每週審閱報告
- [ ] 每月性能評估
- [ ] 持續優化迭代

---

## 📖 總結

這是一個**從零到一**建立 AI 投資團隊的完整企劃。關鍵特點：

1. **零成本啟動** - 完全使用免費資源
2. **模塊化設計** - 易於擴展和維護
3. **自動化運行** - 最小化人工干預
4. **風險可控** - 先驗證再實盤
5. **文檔完整** - 保證可維護性

**成功的關鍵：**
- 嚴格按照任務卡執行
- 每個 Milestone 都要驗收
- 持續記錄和學習
- 保持耐心和紀律

---

## 📝 版本記錄

- v1.0.0 (2024-11-07): 初始版本，完整企劃書
- 後續版本將根據實際執行情況更新

---

**專案負責人：** [你的名字]  
**開始日期：** [填入日期]  
**預計完成：** 21 天後  
**最後更新：** 2024-11-07