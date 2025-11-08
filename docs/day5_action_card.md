# 🗂 Day 5 行動卡 — T05 Data Collector (II) 新聞 RSS（v2.3）

**Inputs**：`data/news_sources.yaml`、`scripts/collector_news_rss.py`  
**Expected Outputs**：`data/news/2025-11-08.jsonl`（至少 20 則），欄位：`title, source, url, url_hash, published_at, symbols[]`

## 套件
```bash
source .venv/bin/activate
pip install feedparser pyyaml
```

## 執行
```bash
python scripts/collector_news_rss.py
# 看到：{"count": N, "path": "data/news/2025-11-08.jsonl"}
```

## 驗收
```bash
wc -l data/news/2025-11-08.jsonl        # 行數（新聞數量）
head -3 data/news/2025-11-08.jsonl      # 抽查欄位格式
```

## 備註
- 去重以 `url_hash=sha256(url)`；symbols 以簡單關鍵字猜測（可再迭代）。
- 後續 Day 6 才把 JSONL upsert 進 DB 與做情緒摘要。
