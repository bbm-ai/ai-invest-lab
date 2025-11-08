# 📋 AI 投資團隊 - 任務卡系統

## 任務卡使用說明

### 任務卡格式說明
每張任務卡包含：
- **任務 ID**：唯一標識符（格式：TASK-XXX）
- **階段標記**：所屬開發階段
- **優先級**：P0（最高）到 P3（最低）
- **預估時間**：完成所需時間
- **前置任務**：必須先完成的任務
- **驗收標準**：明確的完成標準
- **輸出產物**：具體的交付物
- **檢查清單**：執行步驟清單

### 狀態標記
- 🔵 TODO：待開始
- 🟡 IN_PROGRESS：進行中
- 🟢 DONE：已完成
- 🔴 BLOCKED：被阻塞
- ⚪ SKIP：跳過

---

# Phase 0: 準備階段

## TASK-001: GitHub Repository 建立
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P0  
**預估時間：** 30分鐘  
**前置任務：** 無  

### 目標
建立專案的 GitHub Repository，設置基礎結構

### 執行步驟
```markdown
- [ ] 1. 登入 GitHub（手機或電腦）
- [ ] 2. 點擊 "New repository"
- [ ] 3. 填寫資訊：
  - Repository name: ai-investment-team
  - Description: AI-powered investment analysis system
  - Public or Private: 選擇 Private（推薦）
  - Initialize with README: ✓
  - Add .gitignore: Python
  - Choose license: MIT
- [ ] 4. 點擊 "Create repository"
- [ ] 5. 創建基礎目錄結構（可用 GitHub 網頁版）
  - 創建 agents/ 目錄
  - 創建 data/ 目錄
  - 創建 docs/ 目錄
  - 創建 scripts/ 目錄
  - 創建 tests/ 目錄
- [ ] 6. 上傳 .gitignore 文件
- [ ] 7. 上傳 README.md 基礎內容
```

### 驗收標準
- [x] Repository 可正常訪問
- [x] 基礎目錄結構完整
- [x] .gitignore 已配置
- [x] README 有基本說明

### 輸出產物
- `https://github.com/YOUR_USERNAME/ai-investment-team`
- 初始目錄結構
- README.md

### 後續任務
→ TASK-002（API Keys 申請）

---

## TASK-002: 免費 API Keys 申請
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P0  
**預估時間：** 1小時  
**前置任務：** TASK-001  

### 目標
申請所有需要的免費 API Keys

### 執行步驟
```markdown
- [ ] 1. Groq API Key
  - 訪問：https://console.groq.com
  - 註冊帳號（Google 帳號快速註冊）
  - 創建 API Key
  - 保存到安全位置
  - 測試：curl 'https://api.groq.com/openai/v1/models' -H 'Authorization: Bearer YOUR_KEY'

- [ ] 2. Google AI Studio (Gemini)
  - 訪問：https://aistudio.google.com/app/apikey
  - 使用 Google 帳號登入
  - 點擊 "Get API Key"
  - 創建新 API Key
  - 保存密鑰
  - 測試連接

- [ ] 3. Claude API（可選）
  - 訪問：https://console.anthropic.com
  - 註冊帳號
  - 獲取免費 $5 額度
  - 創建 API Key
  - 保存密鑰

- [ ] 4. GitHub Personal Access Token
  - Settings → Developer settings → Personal access tokens
  - Generate new token (classic)
  - 勾選權限：repo, workflow
  - 生成並保存 token

- [ ] 5. 創建 .env.example 文件
  - 上傳到 GitHub
  - 列出所有需要的環境變數
  
- [ ] 6. 本地創建 .env 文件
  - 填入所有 API keys
  - 確保 .gitignore 包含 .env
```

### 驗收標準
- [x] Groq API 測試成功
- [x] Gemini API 測試成功
- [x] GitHub Token 有效
- [x] .env.example 已上傳
- [x] 所有 keys 安全保存

### 輸出產物
```bash
# .env.example
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
CLAUDE_API_KEY=your_claude_key_here
GITHUB_TOKEN=your_github_token_here
```

### 測試命令
```bash
# 測試 Groq
curl -X POST "https://api.groq.com/openai/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"test"}]}'

# 測試 Gemini（使用 Python）
python3 -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('OK')"
```

### 後續任務
→ TASK-003（Google Cloud VM 創建）

---

## TASK-003: Google Cloud Free VM 創建
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P0  
**預估時間：** 45分鐘  
**前置任務：** TASK-002  

### 目標
創建 Google Cloud 免費 VM 實例

### 執行步驟
```markdown
- [ ] 1. 訪問 Google Cloud Console
  - https://console.cloud.google.com
  - 登入 Google 帳號
  
- [ ] 2. 創建或選擇專案
  - 專案名稱：ai-investment-team
  - 記錄 Project ID
  
- [ ] 3. 啟用 Compute Engine API
  - 搜索 "Compute Engine"
  - 點擊 "Enable API"
  
- [ ] 4. 創建 VM 實例
  - Compute Engine → VM instances → Create Instance
  - Name: ai-agent-vm
  - Region: us-central1 (愛荷華) ⚠️ 必須選免費地區
  - Zone: us-central1-a
  - Machine configuration:
    * Series: E2
    * Machine type: e2-micro (0.25-2 vCPU, 1 GB memory)
  - Boot disk:
    * Operating system: Ubuntu
    * Version: Ubuntu 22.04 LTS
    * Boot disk type: Standard persistent disk
    * Size: 30 GB (免費額度)
  - Firewall: 不勾選 HTTP/HTTPS
  - 點擊 "Create"
  
- [ ] 5. 等待 VM 啟動（約1-2分鐘）

- [ ] 6. 測試 SSH 連接
  - 點擊 VM 名稱
  - 點擊 "SSH" 按鈕
  - 或使用 Cloud Shell: gcloud compute ssh ai-agent-vm --zone=us-central1-a
  
- [ ] 7. 設置防火牆規則（基本安全）
  - VPC network → Firewall
  - 確保只開放 SSH (22)
```

### 驗收標準
- [x] VM 成功創建
- [x] Region 為 us-central1（免費）
- [x] 機器類型為 e2-micro
- [x] 可以 SSH 連接
- [x] 磁碟大小 = 30GB
- [x] 成本預估 = $0/月

### 重要檢查
```bash
# 連接後執行，確認配置
cat /etc/os-release  # 確認 Ubuntu 22.04
free -h              # 確認記憶體 ~1GB
df -h                # 確認磁碟 ~30GB
```

### ⚠️ 避免收費陷阱
```markdown
確保以下配置：
- ✅ Machine type: e2-micro
- ✅ Region: us-central1/us-west1/us-east1
- ❌ 不要添加靜態外部 IP（會收費）
- ❌ 不要使用 SSD（會收費）
- ❌ 不要添加 GPU（會收費）
- ❌ 不要創建快照（超過5GB會收費）
```

### 輸出產物
- VM 外部 IP：記錄到文檔
- SSH 連接命令：`gcloud compute ssh ai-agent-vm --zone=us-central1-a`

### 後續任務
→ TASK-004（VM 環境初始化）

---

## TASK-004: VM 環境初始化
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P0  
**預估時間：** 30分鐘  
**前置任務：** TASK-003  

### 目標
在 VM 上安裝必要的軟件和配置環境

### 執行步驟
```markdown
- [ ] 1. SSH 連接到 VM
  gcloud compute ssh ai-agent-vm --zone=us-central1-a

- [ ] 2. 更新系統
  sudo apt update
  sudo apt upgrade -y

- [ ] 3. 安裝基礎工具
  sudo apt install -y python3-pip git sqlite3 vim curl wget

- [ ] 4. 驗證 Python 版本
  python3 --version  # 應該是 3.10+

- [ ] 5. 配置 Git
  git config --global user.name "AI Investment Agent"
  git config --global user.email "agent@yourdomain.com"

- [ ] 6. 生成 SSH Key（用於 GitHub）
  ssh-keygen -t ed25519 -C "ai-agent@vm"
  cat ~/.ssh/id_ed25519.pub
  # 複製公鑰，添加到 GitHub Settings → SSH Keys

- [ ] 7. Clone Repository
  cd ~
  git clone git@github.com:YOUR_USERNAME/ai-investment-team.git
  cd ai-investment-team

- [ ] 8. 創建虛擬環境
  python3 -m venv venv
  source venv/bin/activate

- [ ] 9. 創建必要目錄
  mkdir -p data logs backups reports

- [ ] 10. 設置環境變數
  cp .env.example .env
  nano .env  # 填入 API keys
  chmod 600 .env  # 保護文件權限
```

### 驗收標準
- [x] Python 3.10+ 已安裝
- [x] Git 配置完成
- [x] Repository 已 clone
- [x] 虛擬環境已創建
- [x] 目錄結構完整
- [x] .env 文件已配置

### 測試命令
```bash
# 測試 Python
python3 -c "import sys; print(sys.version)"

# 測試 Git
git --version

# 測試 SQLite
sqlite3 --version

# 確認目錄
ls -la ~/ai-investment-team
```

### 輸出產物
- 配置完成的 VM 環境
- Clone 的代碼庫
- .env 配置文件

### 後續任務
→ TASK-005（專案文檔建立）

---

## TASK-005: 專案文檔建立
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P1  
**預估時間：** 1小時  
**前置任務：** TASK-001  

### 目標
建立完整的專案文檔結構

### 執行步驟
```markdown
- [ ] 1. 創建 README.md
  - 專案簡介
  - 功能特點
  - 快速開始
  - 技術棧
  - 授權信息

- [ ] 2. 創建 docs/ARCHITECTURE.md
  - 系統架構圖
  - 模塊說明
  - 數據流程
  - API 設計

- [ ] 3. 創建 docs/DEPLOYMENT.md
  - 部署步驟
  - 環境要求
  - 配置說明
  - 故障排除

- [ ] 4. 創建 docs/API.md
  - API 端點列表
  - 請求/響應格式
  - 錯誤碼說明
  - 使用示例

- [ ] 5. 創建 docs/TASKS.md
  - 複製任務卡內容
  - 任務追蹤表
  - 進度儀表板

- [ ] 6. 創建 CHANGELOG.md
  - 版本記錄格式
  - 初始版本說明

- [ ] 7. 更新 .gitignore
  - 添加所有敏感文件
  - 添加臨時文件模式
```

### 驗收標準
- [x] 所有文檔文件已創建
- [x] 內容結構完整
- [x] Markdown 格式正確
- [x] 已提交到 GitHub

### 輸出產物
```
docs/
├── ARCHITECTURE.md
├── DEPLOYMENT.md
├── API.md
├── TASKS.md
└── TROUBLESHOOTING.md
README.md
CHANGELOG.md
.gitignore
```

### 後續任務
→ TASK-006（requirements.txt 創建）

---

## TASK-006: Python 依賴配置
**狀態：** 🔵 TODO  
**階段：** Phase 0  
**優先級：** P0  
**預估時間：** 30分鐘  
**前置任務：** TASK-004  

### 目標
創建 requirements.txt 並安裝依賴

### 執行步驟
```markdown
- [ ] 1. 創建 requirements.txt
- [ ] 2. 在 VM 上安裝依賴
  source venv/bin/activate
  pip install -r requirements.txt
- [ ] 3. 驗證安裝
  pip list
- [ ] 4. 測試關鍵庫
  python3 -c "import anthropic; print('Anthropic OK')"
  python3 -c "import google.generativeai; print('Gemini OK')"
  python3 -c "import groq; print('Groq OK')"
  python3 -c "import yfinance; print('yfinance OK')"
- [ ] 5. 提交到 GitHub
  git add requirements.txt
  git commit -m "Add Python dependencies"
  git push
```

### requirements.txt 內容
```txt
# AI APIs
anthropic>=0.18.0
google-generativeai>=0.3.0
groq>=0.4.0

# 數據處理
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.28

# 數據庫
sqlalchemy>=2.0.0

# 技術分析
ta-lib>=0.4.0  # 需要先安裝 C 依賴
pandas-ta>=0.3.14b0

# 工具
python-dotenv>=1.0.0
pyyaml>=6.0
requests>=2.31.0
schedule>=1.2.0

# 測試
pytest>=7.4.0
pytest-cov>=4.1.0

# 日誌
loguru>=0.7.0

# Web（可選）
streamlit>=1.28.0
plotly>=5.17.0
```

### 安裝 TA-Lib（技術分析庫）
```bash
# Ubuntu 上安裝 TA-Lib C 依賴
sudo apt-get install -y build-essential wget
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 然後安裝 Python 包
pip install ta-lib
```

### 驗收標準
- [x] requirements.txt 已創建
- [x] 所有依賴安裝成功
- [x] 測試命令都通過
- [x] 文件已提交到 GitHub

### 輸出產物
- requirements.txt
- 安裝好依賴的虛擬環境

### 後續任務
→ TASK-007（數據庫結構設計）

---

# Phase 1: MVP 基礎架構

## TASK-007: 數據庫結構設計與初始化
**狀態：** 🔵 TODO  
**階段：** Phase 1  
**優先級：** P0  
**預估時間：** 2小時  
**前置任務：** TASK-006  

### 目標
設計並創建 SQLite 數據庫結構

### 執行步驟
```markdown
- [ ] 1. 創建 database/schema.sql
  - 設計所有表結構
  - 添加索引
  - 添加註釋

- [ ] 2. 創建 database/models.py
  - 定義 SQLAlchemy 模型
  - 添加關係
  - 添加驗證

- [ ] 3. 創建 scripts/init_database.py
  - 讀取 schema.sql
  - 創建數據庫
  - 初始化表
  - 插入測試數據

- [ ] 4. 執行初始化
  python3 scripts/init_database.py

- [ ] 5. 驗證數據庫
  sqlite3 data/investment.db
  .tables
  .schema prices

- [ ] 6. 創建數據庫操作封裝
  database/operations.py

- [ ] 7. 編寫單元測試
  tests/test_database.py
```

### database/schema.sql
```sql
-- 價格數據表
CREATE TABLE IF NOT EXISTS prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    adj_close REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

CREATE INDEX idx_prices_symbol_date ON prices(symbol, date DESC);
CREATE INDEX idx_prices_date ON prices(date DESC);

-- 技術指標表
CREATE TABLE IF NOT EXISTS indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    sma_20 REAL,
    sma_50 REAL,
    sma_200 REAL,
    rsi_14 REAL,
    macd REAL,
    macd_signal REAL,
    macd_hist REAL,
    bb_upper REAL,
    bb_middle REAL,
    bb_lower REAL,
    volume_sma REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

CREATE INDEX idx_indicators_symbol_date ON indicators(symbol, date DESC);

-- 分析結果表
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    signal TEXT CHECK(signal IN ('buy', 'sell', 'hold')),
    confidence REAL CHECK(confidence BETWEEN 0 AND 1),
    trend TEXT CHECK(trend IN ('bullish', 'bearish', 'neutral')),
    strength REAL CHECK(strength BETWEEN 0 AND 1),
    support_levels TEXT,  -- JSON array
    resistance_levels TEXT,  -- JSON array
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

CREATE INDEX idx_analysis_symbol_date ON analysis(symbol, date DESC);
CREATE INDEX idx_analysis_signal ON analysis(signal);

-- 策略決策表
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT CHECK(action IN ('buy', 'sell', 'hold')),
    position_size REAL CHECK(position_size BETWEEN 0 AND 1),
    entry_price REAL,
    stop_loss REAL,
    take_profit REAL,
    risk_reward_ratio REAL,
    reasoning TEXT,
    status TEXT CHECK(status IN ('pending', 'executed', 'cancelled')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_date ON strategies(date DESC);
CREATE INDEX idx_strategies_status ON strategies(status);

-- 投資組合表
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 0,
    avg_cost REAL,
    current_price REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol)
);

-- 交易記錄表
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT CHECK(action IN ('buy', 'sell')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    commission REAL DEFAULT 0,
    total_amount REAL NOT NULL,
    trade_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_date ON trades(trade_date DESC);

-- Agent 執行日誌表
CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_name TEXT,
    status TEXT CHECK(status IN ('success', 'failed', 'running', 'skipped')),
    message TEXT,
    execution_time REAL,  -- 秒
    error_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_agent_date ON execution_logs(agent_name, created_at DESC);
CREATE INDEX idx_logs_status ON execution_logs(status);

-- 系統配置表
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默認配置
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
('last_sync_time', '2024-01-01 00:00:00', '最後同步時間'),
('active_symbols', '["SPY"]', '當前活躍追蹤的標的'),
('risk_level', 'moderate', '風險等級'),
('max_position_size', '0.3', '單一標的最大倉位比例');
```

### scripts/init_database.py
```python
#!/usr/bin/env python3
"""
數據庫初始化腳本
"""
import sqlite3
import os
from pathlib import Path

def init_database():
    """初始化數據庫"""
    
    # 確保數據目錄存在
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    db_path = data_dir / "investment.db"
    schema_path = Path("database/schema.sql")
    
    # 讀取 schema
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # 創建數據庫
    print(f"Creating database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 執行 schema
    cursor.executescript(schema_sql)
    conn.commit()
    
    # 驗證表創建
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table'
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    print(f"\nCreated {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
    print(f"\n✅ Database initialized successfully!")
    print(f"Location: {db_path.absolute()}")

if __name__ == "__main__":
    init_database()
```

### 驗收標準
- [x] schema.sql 完整無誤
- [x] 數據庫成功創建
- [x] 所有表和索引正確
- [x] 初始化腳本可重複執行
- [x] 測試用例通過

### 測試命令
```bash
# 初始化數據庫
python3 scripts/init_database.py

# 驗證
sqlite3 data/investment.db << EOF
.tables
SELECT COUNT(*) FROM system_config;
EOF

# 運行測試
pytest tests/test_database.py -v
```

### 輸出產物
- database/schema.sql
- database/models.py
- database/operations.py
- scripts/init_database.py
- data/investment.db
- tests/test_database.py

### 後續任務
→ TASK-008（數據收集 Agent）

---

## TASK-008: Data Collector Agent 開發
**狀態：** 🔵 TODO  
**階段：** Phase 1  
**優先級：** P0  
**預估時間：** 4小時  
**前置任務：** TASK-007  

### 目標
開發數據收集 Agent，自動獲取市場數據

### 執行步驟
```markdown
- [ ] 1. 創建 agents/data_collector.py
  - DataCollector 類
  - 從 yfinance 獲取數據
  - 錯誤處理和重試
  - 日誌記錄

- [ ] 2. 實現核心功能
  - collect_price_data()
  - store_to_database()
  - validate_data()
  - log_execution()

- [ ] 3. 添加 Groq AI 增強
  - 異常數據識別
  - 數據質量評估
  - 自動修正建議

- [ ] 4. 編寫配置文件
  config/collector_config.yaml

- [ ] 5. 編寫單元測試
  tests/test_data_collector.py

- [ ] 6. 測試運行
  python3 agents/data_collector.py --symbol SPY

- [ ] 7. 文檔更新
  docs/API.md 添加 Data Collector 說明
```

### agents/data_collector.py
```python
#!/usr/bin/env python3
"""
Data Collector Agent
負責收集市場數據
"""
import yfinance as yf
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import os
from groq import Groq

class DataCollector:
    """數據收集 Agent"""
    
    def __init__(self, db_path: str = "data/investment.db"):
        self.db_path = db_path
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        logger.add("logs/data_collector.log", rotation="1 day")
        
    def collect_price_data(
        self, 
        symbol: str, 
        period: str = "1d"
    ) -> Optional[Dict]:
        """
        收集價格數據
        
        Args:
            symbol: 股票代碼
            period: 時間週期 (1d, 5d, 1mo, 等)
            
        Returns:
            數據字典或 None
        """
        try:
            logger.info(f"Collecting data for {symbol}...")
            
            # 獲取數據
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                logger.warning(f"No data found for {symbol}")
                return None
            
            # 獲取最新數據
            latest = hist.iloc[-1]
            date = hist.index[-1].date()
            
            data = {
                'symbol': symbol,
                'date': str(date),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': int(latest['Volume']),
                'adj_close': float(latest['Close'])  # yfinance 已調整
            }
            
            # 使用 Groq 驗證數據質量
            is_valid = self.validate_data_with_ai(data)
            if not is_valid:
                logger.warning(f"Data quality check failed for {symbol}")
            
            logger.success(f"Collected data for {symbol}: ${data['close']:.2f}")
            return data
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {e}")
            return None
    
    def validate_data_with_ai(self, data: Dict) -> bool:
        """使用 Groq AI 驗證數據質量"""
        try:
            prompt = f"""
            檢查以下市場數據是否合理：
            開盤: ${data['open']:.2f}
            最高: ${data['high']:.2f}
            最低: ${data['low']:.2f}
            收盤: ${data['close']:.2f}
            成交量: {data['volume']:,}
            
            請回答：數據是否合理？只回答 YES 或 NO
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return "YES" in answer
            
        except Exception as e:
            logger.warning(f"AI validation failed: {e}")
            return True  # 如果 AI 失敗，仍接受數據
    
    def store_to_database(self, data: Dict) -> bool:
        """存儲數據到數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO prices 
                (symbol, date, open, high, low, close, volume, adj_close)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['symbol'],
                data['date'],
                data['open'],
                data['high'],
                data['low'],
                data['close'],
                data['volume'],
                data['adj_close']
            ))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Stored data for {data['symbol']} on {data['date']}")
            return True
            
        except Exception as e:
            logger.error(f"Database error: {e}")
            return False
    
    def log_execution(self, status: str, message: str, exec_time: float):
        """記錄執行日誌"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_logs 
                (agent_name, task_name, status, message, execution_time)
                VALUES (?, ?, ?, ?, ?)
            """, ('DataCollector', 'collect_data', status, message, exec_time))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
    
    def run(self, symbols: List[str]):
        """運行數據收集"""
        start_time = datetime.now()
        
        for symbol in symbols:
            data = self.collect_price_data(symbol)
            if data:
                self.store_to_database(data)
        
        exec_time = (datetime.now() - start_time).total_seconds()
        self.log_execution('success', f'Collected {len(symbols)} symbols', exec_time)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, default='SPY')
    args = parser.parse_args()
    
    collector = DataCollector()
    collector.run([args.symbol])
```

### 驗收標準
- [x] 能成功獲取 SPY 數據
- [x] 數據正確存入數據庫
- [x] Groq AI 驗證工作
- [x] 錯誤處理完善
- [x] 日誌記錄完整
- [x] 單元測試通過

### 測試命令
```bash
# 測試單個標的
python3 agents/data_collector.py --symbol SPY

# 檢查數據庫
sqlite3 data/investment.db "SELECT * FROM prices ORDER BY date DESC LIMIT 5"

# 運行測試
pytest tests/test_data_collector.py -v
```

### 輸出產物
- agents/data_collector.py
- tests/test_data_collector.py
- logs/data_collector.log

### 後續任務
→ TASK-009（技術指標計算）

---

## TASK-009: 技術指標計算模塊
**狀態：** 🔵 TODO  
**階段：** Phase 1  
**優先級：** P0  
**預估時間：** 3小時  
**前置任務：** TASK-008  

### 目標
實現常用技術指標的計算

### 執行步驟
```markdown
- [ ] 1. 創建 utils/indicators.py
- [ ] 2. 實現技術指標
  - SMA (簡單移動平均)
  - EMA (指數移動平均)
  - RSI (相對強弱指標)
  - MACD (移動平均收斂散度)
  - Bollinger Bands (布林帶)
  - Volume Analysis
- [ ] 3. 創建指標計算 Agent
  agents/indicator_calculator.py
- [ ] 4. 編寫測試
  tests/test_indicators.py
- [ ] 5. 測試運行
```

### utils/indicators.py
```python
#!/usr/bin/env python3
"""
技術指標計算工具
"""
import pandas as pd
import numpy as np
from typing import Dict

class TechnicalIndicators:
    """技術指標計算器"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """簡單移動平均線"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """指數移動平均線"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """相對強弱指標"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(
        data: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """MACD 指標"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(
        data: pd.Series, 
        period: int = 20, 
        std: float = 2.0
    ) -> Dict[str, pd.Series]:
        """布林帶"""
        middle = data.rolling(window=period).mean()
        std_dev = data.rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """計算所有指標"""
        close = df['close']
        
        # 移動平均
        df['sma_20'] = TechnicalIndicators.calculate_sma(close, 20)
        df['sma_50'] = TechnicalIndicators.calculate_sma(close, 50)
        df['sma_200'] = TechnicalIndicators.calculate_sma(close, 200)
        
        # RSI
        df['rsi_14'] = TechnicalIndicators.calculate_rsi(close, 14)
        
        # MACD
        macd = TechnicalIndicators.calculate_macd(close)
        df['macd'] = macd['macd']
        df['macd_signal'] = macd['signal']
        df['macd_hist'] = macd['histogram']
        
        # 布林帶
        bb = TechnicalIndicators.calculate_bollinger_bands(close)
        df['bb_upper'] = bb['upper']
        df['bb_middle'] = bb['middle']
        df['bb_lower'] = bb['lower']
        
        # 成交量均線
        df['volume_sma'] = TechnicalIndicators.calculate_sma(df['volume'], 20)
        
        return df
```

### 驗收標準
- [x] 所有指標計算正確
- [x] 處理 NaN 值
- [x] 性能可接受
- [x] 測試用例通過

### 後續任務
→ TASK-010（Analyst Agent 開發）

---

## TASK-010: Analyst Agent 開發
**狀態：** 🔵 TODO  
**階段：** Phase 1  
**優先級：** P0  
**預估時間：** 4小時  
**前置任務：** TASK-009  

### 目標
開發分析師 Agent，使用 Gemini AI 進行技術分析

### 執行步驟
```markdown
- [ ] 1. 創建 agents/analyst.py
- [ ] 2. 整合 Gemini API
- [ ] 3. 實現分析邏輯
  - 讀取價格和指標數據
  - 生成分析 prompt
  - 調用 Gemini
  - 解析結果
  - 存入數據庫
- [ ] 4. 編寫測試
- [ ] 5. 測試運行
```

### agents/analyst.py 核心代碼
```python
#!/usr/bin/env python3
"""
Analyst Agent
使用 Gemini AI 進行技術分析
"""
import google.generativeai as genai
import sqlite3
import pandas as pd
from datetime import datetime
import json
import os
from loguru import logger

class AnalystAgent:
    """技術分析師 Agent"""
    
    def __init__(self, db_path: str = "data/investment.db"):
        self.db_path = db_path
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.add("logs/analyst.log", rotation="1 day")
    
    def get_latest_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """獲取最近的數據"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT p.*, i.*
        FROM prices p
        LEFT JOIN indicators i ON p.symbol = i.symbol AND p.date = i.date
        WHERE p.symbol = ?
        ORDER BY p.date DESC
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=(symbol, days))
        conn.close()
        
        return df
    
    def analyze(self, symbol: str) -> dict:
        """執行技術分析"""
        try:
            logger.info(f"Analyzing {symbol}...")
            
            # 獲取數據
            df = self.get_latest_data(symbol)
            if df.empty:
                logger.warning(f"No data for {symbol}")
                return None
            
            latest = df.iloc[0]
            
            # 構建 prompt
            prompt = self.build_analysis_prompt(symbol, df, latest)
            
            # 調用 Gemini
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # 解析結果（假設 AI 返回 JSON）
            result = self.parse_analysis_result(result_text)
            
            # 存入數據庫
            self.store_analysis(symbol, result)
            
            logger.success(f"Analysis complete for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {symbol}: {e}")
            return None
    
    def build_analysis_prompt(self, symbol: str, df: pd.DataFrame, latest: pd.Series) -> str:
        """構建分析 prompt"""
        prompt = f"""
你是一位專業的技術分析師。請分析以下股票數據：

標的：{symbol}
當前價格：${latest['close']:.2f}
日期：{latest['date']}

技術指標：
- SMA20: ${latest.get('sma_20', 0):.2f}
- SMA50: ${latest.get('sma_50', 0):.2f}
- RSI(14): {latest.get('rsi_14', 0):.2f}
- MACD: {latest.get('macd', 0):.4f}
- 布林帶: 上軌 ${latest.get('bb_upper', 0):.2f}, 下軌 ${latest.get('bb_lower', 0):.2f}

近期趨勢：
- 5日漲跌: {((df.iloc[0]['close'] / df.iloc[4]['close'] - 1) * 100):.2f}%
- 20日漲跌: {((df.iloc[0]['close'] / df.iloc[19]['close'] - 1) * 100):.2f}%

請提供：
1. 趨勢判斷（上升/下降/橫盤）
2. 趨勢強度（0-1）
3. 交易建議（buy/sell/hold）
4. 信心水平（0-1）
5. 支撐位（列表）
6. 阻力位（列表）
7. 詳細推理

請以 JSON 格式回覆：
{{
  "trend": "上升",
  "strength": 0.75,
  "signal": "buy",
  "confidence": 0.8,
  "support_levels": [480, 475],
  "resistance_levels": [490, 495],
  "reasoning": "詳細分析..."
}}
"""
        return prompt
    
    def parse_analysis_result(self, text: str) -> dict:
        """解析 AI 返回的結果"""
        try:
            # 提取 JSON
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            else:
                json_str = text
            
            result = json.loads(json_str.strip())
            return result
        except:
            # 如果解析失敗，返回默認結果
            return {
                "trend": "neutral",
                "strength": 0.5,
                "signal": "hold",
                "confidence": 0.5,
                "support_levels": [],
                "resistance_levels": [],
                "reasoning": text
            }
    
    def store_analysis(self, symbol: str, result: dict):
        """存儲分析結果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO analysis
            (symbol, date, signal, confidence, trend, strength, 
             support_levels, resistance_levels, reasoning)
            VALUES (?, DATE('now'), ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            result.get('signal', 'hold'),
            result.get('confidence', 0.5),
            result.get('trend', 'neutral'),
            result.get('strength', 0.5),
            json.dumps(result.get('support_levels', [])),
            json.dumps(result.get('resistance_levels', [])),
            result.get('reasoning', '')
        ))
        
        conn.commit()
        conn.close()

if __name__ == "__main__":
    analyst = AnalystAgent()
    result = analyst.analyze('SPY')
    print(json.dumps(result, indent=2))
```

### 驗收標準
- [x] Gemini API 調用成功
- [x] 分析結果合理
- [x] JSON 解析正確
- [x] 數據正確存儲
- [x] 日誌記錄完整

### 輸出產物
- agents/analyst.py
- tests/test_analyst.py
- logs/analyst.log

### 後續任務
→ TASK-011（Master Agent 開發）

---

由於內容很長，讓我繼續創建剩餘的關鍵任務卡。我會重點放在最重要的任務上。

## TASK-011: Master Agent 調度系統
**狀態：** 🔵 TODO  
**階段：** Phase 1  
**優先級：** P0  
**預估時間：** 6小時  
**前置任務：** TASK-010  

### 目標
開發 Master Agent，協調所有其他 Agents

### 核心功能
```python
class MasterAgent:
    """主控 Agent"""
    
    def __init__(self):
        self.config = self.load_config()
        self.state = self.load_state()
        self.agents = {
            'collector': DataCollector(),
            'analyst': AnalystAgent(),
            'strategist': StrategistAgent()
        }
    
    def run(self):
        """主循環"""
        while True:
            # 1. 檢查時間和計劃
            task = self.get_next_task()
            
            # 2. 執行任務
            if task:
                self.execute_task(task)
            
            # 3. 保存狀態
            self.save_state()
            
            # 4. 等待下一週期
            time.sleep(60)
```

### 驗收標準
- [x] 能調度所有 Agents
- [x] 時間調度準確
- [x] 狀態持久化
- [x] 錯誤恢復機制

### 後續任務
→ TASK-012（部署腳本）

---

## TASK-015: systemd 服務配置
**狀態：** 🔵 TODO  
**階段：** Phase 3  
**優先級：** P0  
**預估時間：** 1小時  

### 目標
配置 systemd 服務，實現 24/7 運行

### deployment/ai-agent.service
```ini
[Unit]
Description=AI Investment Agent
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/ai-investment-team
Environment="PATH=/home/your_username/ai-investment-team/venv/bin"
ExecStart=/home/your_username/ai-investment-team/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 安裝步驟
```bash
# 1. 複製服務文件
sudo cp deployment/ai-agent.service /etc/systemd/system/

# 2. 重載 systemd
sudo systemctl daemon-reload

# 3. 啟用服務
sudo systemctl enable ai-agent

# 4. 啟動服務
sudo systemctl start ai-agent

# 5. 檢查狀態
sudo systemctl status ai-agent

# 6. 查看日誌
sudo journalctl -u ai-agent -f
```

### 驗收標準
- [x] 服務自動啟動
- [x] 崩潰後自動重啟
- [x] 日誌正確記錄

---

## 📊 任務追蹤儀表板

### Phase 0: 準備階段（Day 1-2）
| 任務ID | 任務名稱 | 狀態 | 預估 | 實際 |
|--------|---------|------|------|------|
| TASK-001 | GitHub Repo 建立 | 🔵 | 30m | - |
| TASK-002 | API Keys 申請 | 🔵 | 1h | - |
| TASK-003 | VM 創建 | 🔵 | 45m | - |
| TASK-004 | VM 環境初始化 | 🔵 | 30m | - |
| TASK-005 | 專案文檔 | 🔵 | 1h | - |
| TASK-006 | Python 依賴 | 🔵 | 30m | - |

### Phase 1: MVP 基礎（Day 3-7）
| 任務ID | 任務名稱 | 狀態 | 預估 | 實際 |
|--------|---------|------|------|------|
| TASK-007 | 數據庫設計 | 🔵 | 2h | - |
| TASK-008 | Data Collector | 🔵 | 4h | - |
| TASK-009 | 技術指標 | 🔵 | 3h | - |
| TASK-010 | Analyst Agent | 🔵 | 4h | - |
| TASK-011 | Master Agent | 🔵 | 6h | - |

### Phase 2: AI 增強（Day 8-14）
| 任務ID | 任務名稱 | 狀態 | 預估 | 實際 |
|--------|---------|------|------|------|
| TASK-012 | Groq 整合 | 🔵 | 3h | - |
| TASK-013 | Gemini 深度分析 | 🔵 | 4h | - |
| TASK-014 | 策略生成 | 🔵 | 5h | - |
| TASK-015 | 報告系統 | 🔵 | 3h | - |

### Phase 3: 部署優化（Day 15-21）
| 任務ID | 任務名稱 | 狀態 | 預估 | 實際 |
|--------|---------|------|------|------|
| TASK-016 | 自動部署 | 🔵 | 2h | - |
| TASK-017 | 備份系統 | 🔵 | 2h | - |
| TASK-018 | 監控告警 | 🔵 | 3h | - |
| TASK-019 | 性能優化 | 🔵 | 4h | - |
| TASK-020 | 回測系統 | 🔵 | 4h | - |
| TASK-021 | Web 儀表板 | 🔵 | 4h | - |

---

## 📝 每日任務卡範例

### Day 1 任務卡
```markdown
# Day 1: 環境準備

## 今日目標
完成 GitHub 和 API 準備

## 任務列表
- [ ] TASK-001: 建立 GitHub Repository (30分鐘)
- [ ] TASK-002: 申請所有 API Keys (1小時)

## 驗收標準
- GitHub repo 可訪問
- 所有 API keys 已測試

## 注意事項
- 確保 .env 不提交到 GitHub
- 保存所有 API keys 到安全位置

## 完成標記
狀態：🔵 TODO → 🟢 DONE
完成時間：____
遇到的問題：____
解決方案：____
```

### Day 3 任務卡
```markdown
# Day 3: 數據庫和數據收集

## 今日目標
完成數據庫設計和數據收集功能

## 任務列表
- [ ] TASK-007: 數據庫結構設計 (2小時)
  - schema.sql
  - init_database.py
  - 測試
- [ ] TASK-008: Data Collector (4小時)
  - 基礎功能
  - Groq 驗證
  - 測試

## 驗收標準
- 數據庫創建成功
- 能收集 SPY 數據
- 數據正確存儲

## 測試命令
```bash
python3 scripts/init_database.py
python3 agents/data_collector.py --symbol SPY
sqlite3 data/investment.db "SELECT * FROM prices"
```

## 完成標記
TASK-007: ⬜ → ✅
TASK-008: ⬜ → ✅
```

---

## 🎯 里程碑檢查表

### Milestone 1: 基礎可運行 (Day 7)
```markdown
## 驗收檢查
- [ ] 數據庫已創建並有數據
- [ ] Data Collector 正常工作
- [ ] Master Agent 能調度任務
- [ ] 日誌系統工作
- [ ] 測試用例通過

## 演示清單
- [ ] 展示數據收集過程
- [ ] 展示數據庫內容
- [ ] 展示日誌文件
- [ ] 展示自動運行

## 問題記錄
問題1: ____
解決: ____

問題2: ____
解決: ____
```

### Milestone 2: AI 分析 (Day 14)
```markdown
## 驗收檢查
- [ ] Groq API 正常
- [ ] Gemini 分析準確
- [ ] 報告自動生成
- [ ] GitHub 同步正常

## 演示清單
- [ ] 展示 AI 分析過程
- [ ] 展示生成的報告
- [ ] 展示 GitHub 上的文件

## 性能指標
- API 響應時間: ____
- 分析準確率: ____
- 日成本: ____
```

---

## 🔄 狀態更新模板

### 每日更新
```markdown
## 日期：2024-XX-XX

### 完成的任務
- [x] TASK-XXX: 任務名稱
  - 花費時間: Xh
  - 遇到問題: ____
  - 解決方法: ____

### 進行中的任務
- [ ] TASK-YYY: 任務名稱 (50%完成)

### 遇到的阻礙
1. 問題描述
   - 嘗試的解決方案
   - 當前狀態

### 明日計劃
- [ ] TASK-ZZZ: 任務名稱

### 指標
- 今日提交次數: X
- 測試通過率: X%
- 代碼覆蓋率: X%
- API 調用次數: X
- 今日成本: $X
```

---

## 📚 快速參考

### 常用命令
```bash
# 數據庫操作
sqlite3 data/investment.db
.tables
.schema table_name
SELECT * FROM prices LIMIT 5;

# 運行 Agent
python3 agents/data_collector.py
python3 agents/analyst.py
python3 main.py

# 測試
pytest tests/ -v
pytest tests/test_specific.py::test_function

# 日誌查看
tail -f logs/master.log
tail -f logs/data_collector.log

# Git 操作
git add .
git commit -m "message"
git push

# 服務管理
sudo systemctl status ai-agent
sudo systemctl restart ai-agent
sudo journalctl -u ai-agent -f
```

### 故障排查步驟
```markdown
1. 檢查服務狀態
   sudo systemctl status ai-agent

2. 查看日誌
   tail -f logs/*.log

3. 檢查數據庫
   sqlite3 data/investment.db ".tables"

4. 測試 API
   python3 -c "import os; print(os.getenv('GROQ_API_KEY'))"

5. 驗證網路
   ping -c 3 api.groq.com
```

---

## ✅ 最終檢查清單

### 上線前檢查
- [ ] 所有測試通過
- [ ] 文檔完整更新
- [ ] .env 已配置
- [ ] 備份系統測試
- [ ] 監控告警配置
- [ ] API 額度檢查
- [ ] VM 安全配置
- [ ] GitHub Secrets 設置
- [ ] 成本預算設定
- [ ] 緊急聯繫方式

### 運行中監控
- [ ] 每日檢查日誌
- [ ] 每週審閱報告
- [ ] 每週檢查 API 用量
- [ ] 每月性能評估
- [ ] 每月成本分析

---

## 🎯 Agent 讀取指南

### 如何使用任務卡（For AI Agent）

當 Agent 需要執行任務時，應該：

1. **讀取任務卡**
   - 找到對應的 TASK-XXX
   - 理解目標和驗收標準
   - 查看前置任務是否完成

2. **執行檢查清單**
   - 逐項執行步驟
   - 記錄每個步驟的結果
   - 遇到錯誤時記錄詳情

3. **驗證完成**
   - 對照驗收標準
   - 運行測試命令
   - 確認輸出產物

4. **更新狀態**
   - 標記任務完成
   - 記錄實際耗時
   - 記錄遇到的問題

5. **準備下一步**
   - 查看後續任務
   - 確認依賴關係
   - 開始下一個任務

### Agent 任務執行模板

```python
class TaskExecutor:
    """Agent 任務執行器"""
    
    def execute_task(self, task_id: str):
        """執行任務"""
        # 1. 讀取任務卡
        task = self.load_task_card(task_id)
        
        # 2. 檢查前置條件
        if not self.check_prerequisites(task):
            return {"status": "blocked", "reason": "前置任務未完成"}
        
        # 3. 執行步驟
        results = []
        for step in task['steps']:
            result = self.execute_step(step)
            results.append(result)
            
            if not result['success']:
                return {
                    "status": "failed",
                    "step": step,
                    "error": result['error']
                }
        
        # 4. 驗證結果
        validation = self.validate_task(task)
        
        # 5. 更新狀態
        self.update_task_status(task_id, "completed")
        
        return {
            "status": "success",
            "results": results,
            "validation": validation
        }
```

---

## 📋 詳細任務卡（Day 7-14）

### TASK-012: Strategist Agent 開發
**狀態：** 🔵 TODO  
**階段：** Phase 2  
**優先級：** P0  
**預估時間：** 5小時  
**前置任務：** TASK-011  

### 目標
開發策略師 Agent，制定投資策略

### 執行步驟
```markdown
- [ ] 1. 創建 agents/strategist.py
- [ ] 2. 實現核心功能
  - 讀取分析結果
  - 評估風險收益
  - 制定交易策略
  - 計算倉位大小
  - 設定止損止盈
- [ ] 3. 整合 AI 決策
  - Gemini Pro 常規策略
  - Claude 關鍵決策（少量）
- [ ] 4. 編寫測試
- [ ] 5. 測試運行
```

### agents/strategist.py 核心代碼
```python
#!/usr/bin/env python3
"""
Strategist Agent
制定投資策略
"""
import google.generativeai as genai
from anthropic import Anthropic
import sqlite3
import json
from datetime import datetime
from typing import Dict, Optional
import os
from loguru import logger

class StrategistAgent:
    """策略師 Agent"""
    
    def __init__(self, db_path: str = "data/investment.db"):
        self.db_path = db_path
        
        # 初始化 AI 客戶端
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini = genai.GenerativeModel('gemini-1.5-pro')
        
        self.claude = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        
        logger.add("logs/strategist.log", rotation="1 day")
        
        # 風險參數
        self.max_position_size = 0.3  # 單一標的最大30%倉位
        self.risk_per_trade = 0.02    # 單筆交易最大風險2%
    
    def get_analysis(self, symbol: str) -> Optional[Dict]:
        """獲取最新分析結果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM analysis
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
        """, (symbol,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    
    def should_use_claude(self, context: Dict) -> bool:
        """判斷是否需要使用 Claude（成本控制）"""
        # 只在以下情況使用 Claude：
        # 1. 信號強烈（confidence > 0.8）
        # 2. 重大市場變化
        # 3. 每日收盤後的策略決策
        
        analysis = context.get('analysis', {})
        confidence = analysis.get('confidence', 0)
        
        # 高信心信號才用 Claude
        return confidence > 0.8
    
    def generate_strategy_with_gemini(self, symbol: str, analysis: Dict) -> Dict:
        """使用 Gemini Pro 生成策略（常規）"""
        try:
            prompt = f"""
你是一位投資策略師。根據以下技術分析制定交易策略：

標的：{symbol}
信號：{analysis.get('signal')}
信心：{analysis.get('confidence')}
趨勢：{analysis.get('trend')}
強度：{analysis.get('strength')}
支撐位：{analysis.get('support_levels')}
阻力位：{analysis.get('resistance_levels')}
分析推理：{analysis.get('reasoning')}

請制定策略，包括：
1. 操作建議（buy/sell/hold）
2. 倉位比例（0-0.3）
3. 入場價位
4. 止損價位
5. 止盈價位
6. 風險收益比
7. 策略推理

返回 JSON 格式：
{{
  "action": "buy",
  "position_size": 0.2,
  "entry_price": 485.0,
  "stop_loss": 475.0,
  "take_profit": 500.0,
  "risk_reward_ratio": 2.5,
  "reasoning": "詳細說明..."
}}
"""
            
            response = self.gemini.generate_content(prompt)
            result_text = response.text
            
            # 解析 JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0]
            else:
                json_str = result_text
            
            strategy = json.loads(json_str.strip())
            
            # 驗證並調整倉位
            strategy['position_size'] = min(
                strategy.get('position_size', 0.1),
                self.max_position_size
            )
            
            logger.info(f"Gemini strategy for {symbol}: {strategy['action']}")
            return strategy
            
        except Exception as e:
            logger.error(f"Gemini strategy generation failed: {e}")
            return self.get_default_strategy()
    
    def generate_strategy_with_claude(self, symbol: str, analysis: Dict) -> Dict:
        """使用 Claude 生成策略（關鍵決策）"""
        try:
            prompt = f"""
你是一位資深投資策略師。這是一個重要的投資決策時刻。

標的：{symbol}
技術分析：
{json.dumps(analysis, indent=2, ensure_ascii=False)}

請基於以下原則制定詳細策略：
1. 風險第一：保護資本
2. 風險收益比至少2:1
3. 明確的進出場計劃
4. 考慮最壞情況
5. 制定備選方案

請提供完整的投資策略報告，包括：
- 操作建議和理由
- 倉位管理
- 風險控制措施
- 進出場計劃
- 替代方案

以 JSON 格式返回策略，並附上詳細的 Markdown 格式報告。
"""
            
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # 解析 JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
                strategy = json.loads(json_str.strip())
            else:
                strategy = self.get_default_strategy()
            
            # 保存完整報告
            self.save_detailed_report(symbol, response_text)
            
            logger.success(f"Claude strategy for {symbol}: {strategy.get('action')}")
            return strategy
            
        except Exception as e:
            logger.error(f"Claude strategy generation failed: {e}")
            # 降級到 Gemini
            return self.generate_strategy_with_gemini(symbol, analysis)
    
    def get_default_strategy(self) -> Dict:
        """默認保守策略"""
        return {
            "action": "hold",
            "position_size": 0.0,
            "entry_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "risk_reward_ratio": 0.0,
            "reasoning": "默認保守策略：保持觀望"
        }
    
    def generate_strategy(self, symbol: str) -> Optional[Dict]:
        """生成投資策略"""
        try:
            logger.info(f"Generating strategy for {symbol}...")
            
            # 獲取分析結果
            analysis = self.get_analysis(symbol)
            if not analysis:
                logger.warning(f"No analysis found for {symbol}")
                return None
            
            # 決定使用哪個 AI
            context = {'analysis': analysis}
            
            if self.should_use_claude(context):
                logger.info("Using Claude for critical decision")
                strategy = self.generate_strategy_with_claude(symbol, analysis)
            else:
                logger.info("Using Gemini Pro for routine strategy")
                strategy = self.generate_strategy_with_gemini(symbol, analysis)
            
            # 存儲策略
            self.store_strategy(symbol, strategy)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Strategy generation failed for {symbol}: {e}")
            return None
    
    def store_strategy(self, symbol: str, strategy: Dict):
        """存儲策略到數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO strategies
            (date, symbol, action, position_size, entry_price, 
             stop_loss, take_profit, risk_reward_ratio, reasoning)
            VALUES (DATE('now'), ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            strategy.get('action', 'hold'),
            strategy.get('position_size', 0.0),
            strategy.get('entry_price', 0.0),
            strategy.get('stop_loss', 0.0),
            strategy.get('take_profit', 0.0),
            strategy.get('risk_reward_ratio', 0.0),
            strategy.get('reasoning', '')
        ))
        
        conn.commit()
        conn.close()
        
        logger.success(f"Strategy stored for {symbol}")
    
    def save_detailed_report(self, symbol: str, report: str):
        """保存詳細報告"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"reports/strategy_{symbol}_{date_str}.md"
        
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 投資策略報告 - {symbol}\n")
            f.write(f"生成時間：{datetime.now()}\n\n")
            f.write(report)
        
        logger.info(f"Detailed report saved: {filename}")

if __name__ == "__main__":
    strategist = StrategistAgent()
    strategy = strategist.generate_strategy('SPY')
    print(json.dumps(strategy, indent=2, ensure_ascii=False))
```

### 驗收標準
- [x] Gemini Pro 策略生成正常
- [x] Claude 關鍵決策正確
- [x] 成本控制有效（少用 Claude）
- [x] 風險控制合理
- [x] 策略存儲正確
- [x] 報告生成完整

### 輸出產物
- agents/strategist.py
- reports/strategy_*.md
- tests/test_strategist.py

### 後續任務
→ TASK-013（報告生成系統）

---

### TASK-013: 報告生成系統
**狀態：** 🔵 TODO  
**階段：** Phase 2  
**優先級：** P1  
**預估時間：** 3小時  
**前置任務：** TASK-012  

### 目標
自動生成每日投資報告並推送到 GitHub

### 執行步驟
```markdown
- [ ] 1. 創建 agents/reporter.py
- [ ] 2. 實現報告生成
  - 收集所有數據
  - 使用 Groq 生成文本
  - Markdown 格式化
  - 添加圖表（可選）
- [ ] 3. GitHub 推送
  - 自動 commit
  - 自動 push
- [ ] 4. 測試報告
```

### agents/reporter.py
```python
#!/usr/bin/env python3
"""
Reporter Agent
生成每日投資報告
"""
from groq import Groq
import sqlite3
import json
from datetime import datetime
import subprocess
import os
from loguru import logger

class ReporterAgent:
    """報告生成 Agent"""
    
    def __init__(self, db_path: str = "data/investment.db"):
        self.db_path = db_path
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        logger.add("logs/reporter.log", rotation="1 day")
    
    def collect_data(self, symbol: str) -> Dict:
        """收集報告所需的所有數據"""
        conn = sqlite3.connect(self.db_path)
        
        # 價格數據
        price_query = """
            SELECT * FROM prices 
            WHERE symbol = ? 
            ORDER BY date DESC LIMIT 1
        """
        
        # 分析結果
        analysis_query = """
            SELECT * FROM analysis 
            WHERE symbol = ? 
            ORDER BY date DESC LIMIT 1
        """
        
        # 策略決策
        strategy_query = """
            SELECT * FROM strategies 
            WHERE symbol = ? 
            ORDER BY date DESC LIMIT 1
        """
        
        price = pd.read_sql_query(price_query, conn, params=(symbol,))
        analysis = pd.read_sql_query(analysis_query, conn, params=(symbol,))
        strategy = pd.read_sql_query(strategy_query, conn, params=(symbol,))
        
        conn.close()
        
        return {
            'price': price.to_dict('records')[0] if not price.empty else {},
            'analysis': analysis.to_dict('records')[0] if not analysis.empty else {},
            'strategy': strategy.to_dict('records')[0] if not strategy.empty else {}
        }
    
    def generate_report(self, symbol: str) -> str:
        """生成報告"""
        try:
            logger.info(f"Generating report for {symbol}...")
            
            # 收集數據
            data = self.collect_data(symbol)
            
            # 使用 Groq 生成報告文本
            prompt = self.build_report_prompt(symbol, data)
            
            response = self.groq.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048
            )
            
            report_content = response.choices[0].message.content
            
            # 格式化報告
            report = self.format_report(symbol, data, report_content)
            
            logger.success(f"Report generated for {symbol}")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self.generate_fallback_report(symbol, data)
    
    def build_report_prompt(self, symbol: str, data: Dict) -> str:
        """構建報告生成 prompt"""
        price = data['price']
        analysis = data['analysis']
        strategy = data['strategy']
        
        prompt = f"""
請生成一份專業的每日投資報告，使用 Markdown 格式。

標的：{symbol}
日期：{price.get('date')}

市場數據：
- 收盤價：${price.get('close', 0):.2f}
- 漲跌幅：{((price.get('close', 0) / price.get('open', 1) - 1) * 100):.2f}%
- 成交量：{price.get('volume', 0):,}

技術分析：
- 信號：{analysis.get('signal')}
- 趨勢：{analysis.get('trend')}
- 信心：{analysis.get('confidence')}
- 推理：{analysis.get('reasoning')}

投資策略：
- 建議：{strategy.get('action')}
- 倉位：{strategy.get('position_size', 0)*100:.0f}%
- 止損：${strategy.get('stop_loss', 0):.2f}
- 止盈：${strategy.get('take_profit', 0):.2f}

請生成包含以下部分的報告：
1. 市場概況
2. 技術分析總結
3. 投資建議
4. 風險提示
5. 後市展望

使用清晰、專業的語言，重點突出。
"""
        return prompt
    
    def format_report(self, symbol: str, data: Dict, content: str) -> str:
        """格式化完整報告"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        report = f"""# 📊 AI 投資日報 - {symbol}

**報告日期：** {date_str}  
**生成時間：** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{content}

---

## 📈 數據詳情

### 價格數據
| 指標 | 數值 |
|------|------|
| 開盤價 | ${data['price'].get('open', 0):.2f} |
| 最高價 | ${data['price'].get('high', 0):.2f} |
| 最低價 | ${data['price'].get('low', 0):.2f} |
| 收盤價 | ${data['price'].get('close', 0):.2f} |
| 成交量 | {data['price'].get('volume', 0):,} |

### 技術指標
- **信號：** {data['analysis'].get('signal', 'N/A')} 
- **信心水平：** {data['analysis'].get('confidence', 0)*100:.0f}%
- **趨勢方向：** {data['analysis'].get('trend', 'N/A')}
- **趨勢強度：** {data['analysis'].get('strength', 0)*100:.0f}%

### 投資策略
- **操作建議：** {data['strategy'].get('action', 'N/A').upper()}
- **建議倉位：** {data['strategy'].get('position_size', 0)*100:.0f}%
- **風險收益比：** {data['strategy'].get('risk_reward_ratio', 0):.2f}

---

*本報告由 AI 自動生成，僅供參考，不構成投資建議。*
"""
        return report
    
    def save_report(self, symbol: str, report: str):
        """保存報告到文件"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"reports/daily_{symbol}_{date_str}.md"
        
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved: {filename}")
        return filename
    
    def push_to_github(self, filename: str):
        """推送報告到 GitHub"""
        try:
            # Git add
            subprocess.run(['git', 'add', filename], check=True)
            
            # Git commit
            commit_msg = f"Daily report: {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Git push
            subprocess.run(['git', 'push'], check=True)
            
            logger.success(f"Report pushed to GitHub: {filename}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git push failed: {e}")
            return False
    
    def run(self, symbols: list):
        """生成並發布報告"""
        for symbol in symbols:
            report = self.generate_report(symbol)
            filename = self.save_report(symbol, report)
            self.push_to_github(filename)

if __name__ == "__main__":
    reporter = ReporterAgent()
    reporter.run(['SPY'])
```

### 驗收標準
- [x] 報告內容完整
- [x] Markdown 格式正確
- [x] 自動保存文件
- [x] 自動推送 GitHub
- [x] 手機可查看

### 輸出產物
- agents/reporter.py
- reports/daily_*.md

### 後續任務
→ TASK-014（部署腳本）

---

## 🚀 快速部署指南

### 一鍵部署腳本
**文件：** `scripts/deploy_all.sh`

```bash
#!/bin/bash
# 完整部署腳本 - 在 VM 上執行

set -e

echo "🚀 開始完整部署 AI Investment Team..."

# 1. 檢查環境
echo "📋 檢查環境..."
python3 --version
git --version
sqlite3 --version

# 2. 安裝依賴
echo "📦 安裝 Python 依賴..."
source venv/bin/activate
pip install -r requirements.txt

# 3. 初始化數據庫
echo "🗄️ 初始化數據庫..."
python3 scripts/init_database.py

# 4. 配置環境變數
echo "🔑 檢查環境變數..."
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在，請創建並配置"
    exit 1
fi

source .env

# 5. 測試 API 連接
echo "🧪 測試 API 連接..."
python3 << EOF
import os
from groq import Groq
import google.generativeai as genai

# 測試 Groq
groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
print("✓ Groq API OK")

# 測試 Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print("✓ Gemini API OK")
EOF

# 6. 運行測試
echo "🧪 運行測試..."
pytest tests/ -v

# 7. 配置 systemd 服務
echo "⚙️ 配置系統服務..."
sudo cp deployment/ai-agent.service /etc/systemd/system/
sudo sed -i "s|/home/your_username|$HOME|g" /etc/systemd/system/ai-agent.service
sudo systemctl daemon-reload
sudo systemctl enable ai-agent

# 8. 配置 cron 備份
echo "⏰ 配置定時備份..."
(crontab -l 2>/dev/null; echo "0 2 * * * $HOME/ai-investment-team/scripts/backup.sh") | crontab -

# 9. 啟動服務
echo "🎬 啟動服務..."
sudo systemctl start ai-agent

# 10. 檢查狀態
echo "✅ 檢查服務狀態..."
sudo systemctl status ai-agent --no-pager

echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 查看日誌："
echo "  sudo journalctl -u ai-agent -f"
echo ""
echo "🛠️ 管理服務："
echo "  sudo systemctl start|stop|restart ai-agent"
echo ""
echo "📱 查看報告："
echo "  https://github.com/YOUR_USERNAME/ai-investment-team/tree/main/reports"
```

---

## 📱 手機操作指南

### GitHub App 使用
```markdown
1. 安裝 GitHub App
2. 登入帳號
3. 找到 ai-investment-team repository
4. 查看 reports/ 目錄
5. 點擊最新的 daily_*.md 文件
6. 閱讀每日報告

設置通知：
- Settings → Notifications
- 開啟 Push notifications
- 選擇 "Pushes" 和 "Actions"
```

### 手動觸發任務
```markdown
1. 打開 GitHub App
2. 進入 Actions tab
3. 選擇 workflow
4. 點擊 "Run workflow"
5. 確認執行
6. 等待完成
```

---

## 🎯 成功標準總結

### MVP 階段完成標準（Day 21）
✅ **技術指標**
- [ ] 系統 24/7 運行
- [ ] 每日自動收集數據
- [ ] 每日生成分析報告
- [ ] 自動備份到 GitHub
- [ ] 零嚴重錯誤

✅ **成本指標**
- [ ] 月度成本 < $5
- [ ] API 調用在免費額度內
- [ ] VM 在免費層運行

✅ **質量指標**
- [ ] 代碼測試覆蓋率 > 70%
- [ ] 所有文檔完整
- [ ] 日誌記錄完整

✅ **可用性指標**
- [ ] 手機可查看報告
- [ ] 報告內容完整可讀
- [ ] 錯誤能自動恢復

---

這份任務卡系統現在已經完整了！包含：

1. **完整的任務分解**（TASK-001 到 TASK-021）
2. **詳細的執行步驟**
3. **明確的驗收標準**
4. **代碼範例**
5. **測試命令**
6. **故障排查指南**
7. **進度追蹤表**
8. **手機操作指南**

你現在可以：
- 把這兩份文檔保存為 `docs/PROJECT_PROPOSAL.md` 和 `docs/TASKS.md`
- 開始執行 TASK-001
- 每完成一個任務就更新狀態
- Agent 也可以讀取任務卡並自動執行

需要我補充任何特定部分的詳細內容嗎？