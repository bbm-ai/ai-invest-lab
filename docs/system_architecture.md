# 🧭 System Architecture — 摘要（v2.2, 2025-11-08)

## Data Flow & Storage Map（摘要）
- Collectors → SQLite（`prices`, `news`）→ Analysts（`sentiments`, `tech_signals`）→ `strategies` → Dashboard 只讀。

## Data Lineage（欄位層級）
| 實體 | 欄位 | 來源 | 處理/轉換 | 落地表 | 索引鍵 | 保留策略 |
|---|---|---|---|---|---|---|
| Prices | symbol,date,open,high,low,close,volume | Yahoo/替代 | 正規化→冪等 upsert | `prices` | (symbol,date) | 24 個月 |
| News | title,source,url_hash,published_at | RSS/API | 去重→清洗→截斷 | `news` | url_hash | 12 個月（僅結構化欄位）|
| Sentiments | news_id,score,summary | News→Sentiment | 快取→截斷 | `sentiments` | news_id | 12 個月 |
| TechSignals | date,symbol,rsi,macd,trend | Prices→TA | 視窗化→四捨五入 | `tech_signals` | (symbol,date) | 24 個月 |
| Strategies | date,symbol,recommendation,reasoning,position_size,confidence,is_executed | Sentiment+Tech | 路由決策→審核 | `strategies` | (symbol,date) | 永久（審計） |

## Upsert/去重規範
- `prices`: `INSERT OR REPLACE` 以 `(symbol,date)`。
- `news`: `url_hash` 唯一；同 URL 不重覆寫入。
- `tech_signals`: `(symbol,date)` 主鍵；重算時覆蓋。
- `strategies`: `(date,symbol)` 唯一日級策略；多版本以 `id` 遞增保留。

### v2.3 補充 — 策略版本與績效映射
- `strategies.version`：用於「策略詳情」與「最新策略」頁面過濾與顯示。
- 新增 `strategy_metrics`：存放回測/滾動績效（`sharpe_7d, sharpe_30d, maxdd_30d, win_rate_30d`），與 `strategies(date, symbol)` 一對一映射，提供 Dashboard 快速讀取。
