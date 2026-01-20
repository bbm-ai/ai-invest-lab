# QQQ Decision System - Technical Skill Documentation

## System Overview

**Name**: QQQ Automated Trading Decision System  
**Version**: 5.0  
**Purpose**: Automated quantitative trading system for QQQ (Nasdaq-100 ETF) with multi-strategy support, parameter optimization, and comprehensive monitoring  
**Architecture**: Python backend + Google Apps Script + Web Dashboard + GitHub Actions CI/CD

---

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (CI/CD)                    │
│  • Daily Analysis (Mon-Fri 21:30 UTC)                       │
│  • Weekly Review (Fri 22:00 UTC)                            │
│  • Parameter Optimization (1st Sat 10:00 UTC)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Python Analysis Engine (qqq_analyzer.py)        │
│  • Strategy: MA20, Default (multi-factor)                   │
│  • Data: yfinance (QQQ, VIX, Bonds, etc.)                   │
│  • Output: JSON results + Optimized parameters              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Google Apps Script (Data Storage & API)              │
│  • Spreadsheet: Daily_Logs, Weekly_Reviews, Validations     │
│  • API: RESTful endpoints for data retrieval                │
│  • URL: https://script.google.com/macros/s/.../exec         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Web Dashboard (GCP VM)                      │
│  • Main: index.html                                          │
│  • Weekly: enhanced_weekly_dashboard.html                   │
│  • Monitor: monitoring_dashboard.html                        │
│  • Host: https://www.bbm-ai.filegear-sg.me/                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Notification System                             │
│  • Telegram: Real-time alerts                               │
│  • Email: Optional alerts (can be added)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
ai-invest-lab/
├── .github/workflows/
│   ├── daily-analysis.yml          # Daily trading analysis
│   ├── weekly-review.yml           # Weekly performance review
│   ├── optimization.yml            # Parameter optimization
│   └── test.yml                    # System testing
│
├── qqq_analyzer.py                 # Main analysis engine (v5.0)
├── auto_optimize.py                # Parameter optimization
├── optimized_params.json           # Current optimal parameters
├── requirements.txt                # Python dependencies
├── .gitattributes                  # Line ending normalization
│
├── website/ (on GCP VM)
│   ├── index.html                  # Main dashboard
│   ├── enhanced_weekly_dashboard.html  # Weekly report
│   └── monitoring_dashboard.html   # System monitoring
│
└── docs/
    └── SKILL.md                    # This file
```

---

## 🔑 Key Technologies

### Backend
- **Python 3.11**: Core analysis engine
- **yfinance**: Market data retrieval
- **pandas/numpy**: Data processing
- **requests**: API communication

### Data Storage
- **Google Sheets**: Persistent data storage
- **Google Apps Script**: RESTful API layer
- **JSON**: Parameter and configuration storage

### Frontend
- **HTML/CSS/JavaScript**: Dashboard interfaces
- **Chart.js**: Data visualization
- **Nginx**: Web server (Docker on GCP VM)

### CI/CD
- **GitHub Actions**: Automated workflows
- **Cron Jobs**: Scheduled execution
- **Artifacts**: Result storage

---

## 🎯 Trading Strategies

### 1. MA20 Strategy (Trend Following)

**Concept**: Follow price trends relative to 20-day moving average

**Parameters** (`optimized_params.json`):
```json
{
  "ma20": {
    "days_threshold": 2,        // Consecutive days for signal
    "vix_limit": 35,            // VIX threshold for risk-off
    "position_weight": 0.50,    // Weight for MA20 position factor
    "trend_weight": 0.30,       // Weight for trend direction
    "vix_weight": 0.20          // Weight for VIX filter
  }
}
```

**Scoring Logic**:
```python
# MA20 Position Score (0-10)
if price > MA20:
    score = 6-9 (based on distance from MA20)
else:
    score = 2-5 (based on distance below MA20)

# Trend Score (0-10)
if consecutive_days_above >= days_threshold:
    score = 8-9, signal = "BUY"
elif consecutive_days_below >= days_threshold:
    score = 2-3, signal = "SELL"

# VIX Filter Score (0-10)
if VIX < 15: score = 8
elif VIX > 30: score = 2-3

# Final Score = weighted sum of factors
total_score = (position * 0.5) + (trend * 0.3) + (vix * 0.2)
```

**Allocation**:
```python
if score <= 3: allocation = 10% QQQ
if score <= 4: allocation = 25% QQQ
if score <= 5: allocation = 40% QQQ
if score <= 6: allocation = 55% QQQ
if score <= 7: allocation = 70% QQQ
if score <= 8: allocation = 85% QQQ
if score > 8:  allocation = 95% QQQ
```

### 2. Default Strategy (Multi-Factor)

**Concept**: Combine multiple market factors with weighted scoring

**Parameters**:
```json
{
  "default": {
    "weights": {
      "price_momentum": 0.30,   // Price trend strength
      "volume": 0.10,           // Volume confirmation
      "vix": 0.30,              // Volatility/risk
      "bond": 0.15,             // Interest rate environment
      "mag7": 0.15              // Big tech performance
    }
  }
}
```

**Factors**:
1. **Price Momentum**: Daily price change (-2% to +2%)
2. **Volume**: Volume vs 20-day average
3. **VIX**: Market fear index
4. **Bonds**: 10Y Treasury yield change
5. **MAG7**: Proxy for large-cap tech

**Scoring**: Each factor scores 0-10, final = weighted average

---

## 🔄 Automation Workflows

### Daily Analysis (Mon-Fri 21:30 UTC)

**Trigger**: `cron: '30 21 * * 1-5'`

**Process**:
1. Fetch market data (QQQ, VIX, Bonds)
2. Calculate technical indicators (MA20, RSI, etc.)
3. Run strategy scoring
4. Generate allocation recommendation
5. Send to Google Sheets
6. Send Telegram notification

**Output**: `output.json`, Google Sheets row, Telegram message

### Weekly Review (Fri 22:00 UTC)

**Trigger**: `cron: '0 22 * * 5'`

**Process**:
1. Fetch past 7 days data from Google Sheets
2. Calculate weekly metrics:
   - Week return, Alpha, Win rate
   - Profit/Loss ratio, Max drawdown
   - Average allocation, Average VIX
3. Generate recommendations
4. Send to Google Sheets & Telegram

**Output**: Weekly report in Google Sheets

### Parameter Optimization (1st Sat 10:00 UTC)

**Trigger**: `cron: '0 10 1-7 * 6'` (First Saturday)

**Process**:
1. Download 6 months historical data
2. Grid search parameter combinations
3. Backtest each combination
4. Select best parameters (maximize Sharpe ratio)
5. Create Pull Request for review
6. Update `optimized_params.json` upon merge

**Output**: Pull Request with new parameters

---

## 📊 Data Schema

### Google Sheets Structure

#### Daily_Logs
| Column | Type | Description |
|--------|------|-------------|
| date | Date | Trading date |
| weekday | String | Day of week |
| close | Float | QQQ close price |
| change_pct | Float | Daily % change |
| vix | Float | VIX value |
| total_score | Float | Strategy score (0-10) |
| regime | String | offense/neutral/defense |
| qqq_pct | Integer | QQQ allocation % |
| cash_pct | Integer | Cash allocation % |
| factor_scores | JSON | Individual factor scores |
| full_json | JSON | Complete analysis result |

#### Weekly_Reviews
| Column | Type | Description |
|--------|------|-------------|
| week_start | Date | Week start date |
| week_end | Date | Week end date |
| week_return | Float | Weekly return % |
| alpha | Float | Alpha vs benchmark |
| win_rate | Float | Prediction accuracy % |
| profit_loss_ratio | Float | Avg profit / Avg loss |
| max_drawdown | Float | Max drawdown % |
| avg_vix | Float | Average VIX |

#### Validations
| Column | Type | Description |
|--------|------|-------------|
| date | Date | Validation date |
| prediction_date | Date | When prediction was made |
| predicted_direction | String | bullish/neutral/bearish |
| actual_direction | String | Actual result |
| is_correct | Boolean | Prediction accuracy |
| pnl_pct | Float | P&L % |

---

## 🛠️ Configuration Files

### optimized_params.json
```json
{
  "meta": {
    "last_updated": "ISO timestamp",
    "version": "5.0",
    "optimization_days": 60,
    "optimization_results": {}
  },
  "ma20": {
    "days_threshold": 2,
    "vix_limit": 35,
    "position_weight": 0.50,
    "trend_weight": 0.30,
    "vix_weight": 0.20
  },
  "default": {
    "weights": {
      "price_momentum": 0.30,
      "volume": 0.10,
      "vix": 0.30,
      "bond": 0.15,
      "mag7": 0.15
    }
  }
}
```

### Environment Variables (GitHub Secrets)
```bash
GAS_URL=https://script.google.com/macros/s/.../exec
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
RISK_PREFERENCE=neutral  # conservative/neutral/aggressive
STRATEGY=default         # default/ma20
```

---

## 🔌 API Endpoints

### Google Apps Script API

**Base URL**: `https://script.google.com/macros/s/{DEPLOYMENT_ID}/exec`

#### GET Endpoints

**Health Check**
```
GET /?action=health
Response: {"status": "ok", "timestamp": "...", "version": "3.0"}
```

**Latest Data**
```
GET /?action=latest
Response: {date, close, change_pct, vix, total_score, regime, ...}
```

**Historical Data**
```
GET /?action=history&days=30
Response: [{date, close, score, ...}, ...]
```

**Weekly Reviews**
```
GET /?action=weekly_reviews&count=10
Response: [{week_start, week_end, week_return, alpha, ...}, ...]
```

**Validations**
```
GET /?action=validations&days=30
Response: [{date, is_correct, pnl_pct, ...}, ...]
```

#### POST Endpoints

**Daily Log**
```
POST /
Body: {action: "daily_log", data: {...}}
Response: {"success": true, "message": "..."}
```

**Weekly Review**
```
POST /
Body: {action: "weekly_review", data: {...}}
```

---

## 🎛️ Tuning Parameters

### Risk Profiles

**Conservative**
```json
{
  "ma20": {
    "days_threshold": 3,
    "vix_limit": 30,
    "position_weight": 0.40,
    "trend_weight": 0.30,
    "vix_weight": 0.30
  },
  "default": {
    "weights": {
      "price_momentum": 0.20,
      "volume": 0.15,
      "vix": 0.35,
      "bond": 0.20,
      "mag7": 0.10
    }
  }
}
```

**Aggressive**
```json
{
  "ma20": {
    "days_threshold": 1,
    "vix_limit": 40,
    "position_weight": 0.60,
    "trend_weight": 0.35,
    "vix_weight": 0.05
  },
  "default": {
    "weights": {
      "price_momentum": 0.40,
      "volume": 0.25,
      "vix": 0.15,
      "bond": 0.10,
      "mag7": 0.10
    }
  }
}
```

### Optimization Ranges

**MA20 Strategy**
```python
param_ranges = {
    'days_threshold': [1, 2, 3],
    'vix_limit': [30, 35, 40],
    'position_weight': [0.4, 0.5, 0.6],
    'trend_weight': [0.25, 0.3, 0.35],
    'vix_weight': [0.15, 0.2, 0.25]
}
```

**Default Strategy**
```python
weight_options = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
# All weights must sum to 1.0
```

---

## 📈 Performance Metrics

### Key Metrics Tracked

| Metric | Calculation | Target |
|--------|-------------|--------|
| **Total Return** | (End NAV - Start NAV) / Start NAV | >0% |
| **Alpha** | Strategy Return - Benchmark Return | >0% |
| **Sharpe Ratio** | (Mean Return / Std Return) × √252 | >1.0 |
| **Max Drawdown** | Max(Peak - Trough) / Peak | <-10% |
| **Win Rate** | Correct Predictions / Total | >55% |
| **Profit/Loss Ratio** | Avg Win / Avg Loss | >1.5 |

### Backtesting Process

1. **Data**: Download 6 months QQQ history
2. **Loop**: For each day:
   - Apply strategy scoring
   - Calculate allocation
   - Simulate trading (buy/sell)
   - Track NAV
3. **Metrics**: Calculate all performance metrics
4. **Optimization**: Find parameters maximizing Sharpe ratio

---

## 🚨 Alert Thresholds

### System Health Alerts

```python
THRESHOLDS = {
    'vix_high': 30,              # Warning
    'vix_critical': 40,          # Critical
    'score_low': 3.5,            # Warning
    'score_critical': 2.5,       # Critical
    'drawdown_warning': -5.0,    # Warning
    'drawdown_critical': -8.0,   # Critical
    'accuracy_low': 45.0,        # Warning
    'consecutive_losses': 3      # Warning
}
```

### Notification Triggers

- VIX > 30: ⚠️ Warning
- VIX > 40: 🚨 Critical
- Score < 3.5: ⚠️ Warning
- Score < 2.5: 🚨 Critical
- Drawdown < -5%: ⚠️ Warning
- Drawdown < -8%: 🚨 Critical
- Accuracy < 45%: ⚠️ Warning

---

## 🐛 Common Issues & Solutions

### Issue 1: Line Ending Conflicts
**Symptom**: Git errors in GitHub Actions about CRLF/LF
**Solution**: 
- Add `.gitattributes` file
- Configure `git config core.autocrlf false`
- Normalize existing files: `dos2unix` or `sed -i 's/\r$//'`

### Issue 2: Pandas Type Errors
**Symptom**: `ValueError: The truth value of a Series is ambiguous`
**Solution**: 
- Explicitly convert to float: `float(df['Column'].iloc[i])`
- Use `.loc` instead of `.iloc` for clarity
- Reset index after slicing

### Issue 3: Empty Factor Scores in Dashboard
**Symptom**: Dashboard shows "--" for all values
**Solution**:
- Verify GAS_URL is set correctly
- Check Google Sheets has data in factor_scores column
- Ensure JSON is properly stringified before sending
- Use browser DevTools Console to debug

### Issue 4: Optimization Workflow Fails
**Symptom**: Pull Request creation fails with Git errors
**Solution**:
- Clean working directory before checkout
- Use `add-paths` to limit committed files
- Ensure `.gitignore` excludes temp files

---

## 🔐 Security Best Practices

### Secrets Management
- **Never** commit API keys to repository
- Use GitHub Secrets for sensitive data
- Rotate tokens periodically
- Use environment-specific configurations

### API Security
- Google Apps Script URL is public but read-only
- Implement rate limiting if needed
- Validate all inputs server-side
- Use HTTPS for all communications

---

## 🚀 Deployment Checklist

### Initial Setup
- [ ] Clone repository
- [ ] Set up GitHub Secrets (GAS_URL, Telegram tokens)
- [ ] Configure Google Sheets with correct sheet names
- [ ] Deploy Google Apps Script and get deployment URL
- [ ] Test API endpoints
- [ ] Set up GCP VM and Nginx
- [ ] Deploy dashboard files
- [ ] Test all dashboards can load data
- [ ] Trigger test workflow in GitHub Actions

### Ongoing Maintenance
- [ ] Daily: Check dashboard for alerts
- [ ] Weekly: Review weekly report
- [ ] Monthly: Review optimization PR and merge if beneficial
- [ ] Quarterly: Review overall strategy performance
- [ ] As needed: Adjust parameters based on market conditions

---

## 📚 Extension Points

### Adding New Strategies

1. **Create Strategy Class** in `qqq_analyzer.py`:
```python
class MyNewStrategy(BaseStrategy):
    name = "my_strategy"
    version = "1.0"
    description = "Description"
    
    def load_params(self, params: Dict):
        self.my_param = params.get('my_param', default_value)
    
    def score(self, data: Dict) -> Dict:
        # Scoring logic
        return {"total_score": score, "regime": regime}
    
    def get_allocation(self, score: float, risk_pref: str) -> Dict:
        # Allocation logic
        return {"qqq_pct": pct, "cash_pct": 100-pct}
```

2. **Register Strategy**:
```python
STRATEGIES = {
    'default': DefaultStrategy,
    'ma20': MA20Strategy,
    'my_strategy': MyNewStrategy  # Add here
}
```

3. **Add Parameters** to `optimized_params.json`

4. **Update Workflows** to support new strategy

### Adding New Data Sources

1. **Create Fetcher Function**:
```python
def fetch_new_data_source():
    # API call or web scraping
    return data
```

2. **Integrate into MarketDataFetcher.fetch_all()**

3. **Update Strategy Scoring** to use new data

### Adding New Metrics

1. **Add Calculation** in backtester:
```python
def calculate_new_metric(self, nav_history):
    # Calculation logic
    return metric_value
```

2. **Include in Results** dictionary

3. **Display in Dashboard**

---

## 🎓 Learning Resources

### Understanding the Code
- **qqq_analyzer.py**: Start here, main entry point
- **auto_optimize.py**: Parameter optimization logic
- **GitHub Actions**: Workflow automation
- **Google Apps Script**: Data API layer

### Key Concepts
- **Moving Averages**: Trend-following indicators
- **VIX**: Volatility index (fear gauge)
- **Backtesting**: Testing strategies on historical data
- **Sharpe Ratio**: Risk-adjusted return metric
- **Alpha**: Excess return vs benchmark

### External Documentation
- [yfinance docs](https://pypi.org/project/yfinance/)
- [pandas docs](https://pandas.pydata.org/docs/)
- [Chart.js docs](https://www.chartjs.org/docs/)
- [GitHub Actions docs](https://docs.github.com/en/actions)

---

## 🔄 Version History

### v5.0 (Current)
- Auto-load optimized parameters from JSON
- Multi-strategy support (MA20, Default)
- GitHub Actions automation
- Comprehensive dashboard system
- Parameter optimization with PR workflow

### v4.0
- Added weekly review functionality
- Improved validation system
- Enhanced Google Sheets integration

### v3.0
- Initial automation with GitHub Actions
- Google Apps Script API
- Basic dashboard

---

## 💡 Future Enhancements

### Planned Features
- [ ] Machine learning model integration (LSTM, RandomForest)
- [ ] Multi-timeframe analysis (daily + weekly)
- [ ] Portfolio optimization (multiple tickers)
- [ ] Real-time trading integration (Alpaca, Interactive Brokers)
- [ ] Advanced visualization (3D charts, heatmaps)
- [ ] Sentiment analysis (news, social media)
- [ ] Options strategy support
- [ ] Tax-loss harvesting automation

### Potential Optimizations
- [ ] Parallel backtesting (multiprocessing)
- [ ] Bayesian optimization (Optuna)
- [ ] Reinforcement learning for parameter tuning
- [ ] Database migration (SQLite → PostgreSQL)
- [ ] Caching layer (Redis)
- [ ] Microservices architecture

---

## 📞 Support & Contribution

### Getting Help
1. Check this SKILL.md documentation
2. Review code comments in source files
3. Check GitHub Issues for similar problems
4. Use diagnostic tools (weekly-debug.html, monitor.py)

### Contributing
1. Fork repository
2. Create feature branch
3. Make changes with clear commit messages
4. Test thoroughly (including backtests)
5. Submit Pull Request with description

---

## 📄 License & Disclaimer

**License**: MIT (or specify your license)

**Disclaimer**: 
- This system is for educational and research purposes
- Not financial advice
- Past performance does not guarantee future results
- Trading involves risk of loss
- Always do your own research (DYOR)
- Consider consulting a financial advisor

---

**Last Updated**: 2026-01-18  
**Maintained By**: bbm-ai  
**Repository**: https://github.com/bbm-ai/ai-invest-lab

---

## Quick Reference Commands

```bash
# Daily analysis
python qqq_analyzer.py --strategy ma20

# Weekly review
python qqq_analyzer.py --weekly

# Parameter optimization
python auto_optimize.py --strategy all --days 60

# Monitoring
python monitor.py --daemon --interval 3600

# Show current parameters
python qqq_analyzer.py --show-params

# List available strategies
python qqq_analyzer.py --list-strategies

# Run all (daily + validate + weekly)
python qqq_analyzer.py --all
```

---

**End of Documentation**

*This skill document enables Claude to understand, maintain, optimize, and extend the QQQ Decision System.*
