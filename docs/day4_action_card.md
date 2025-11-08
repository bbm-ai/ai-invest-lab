# 🗂 Day 4 行動卡 — T04 Data Collector (I) 價量資料（v2.3）

**Inputs**：`data/symbols.yaml`、`scripts/collector_prices.py`  
**Expected Outputs**：
- 產生 `data/prices/{SYMBOL}.csv`（欄位：`date, open, high, low, close, volume`）
- 可離線：若網路或 API 失敗，會回退到合成資料（不中斷）

## 步驟
1) 安裝套件（若尚未安裝）
   ```bash
   source .venv/bin/activate
   pip install yfinance pandas numpy pyyaml
   ```
2) 檢查 symbols
   ```bash
   cat data/symbols.yaml
   # 預設: SPY, QQQ, DIA
   ```
3) 執行收集（優先使用快取，同檔存在則跳過）
   ```bash
   python scripts/collector_prices.py
   # 若要重抓（忽略快取）：
   # python scripts/collector_prices.py --refresh
   ```
4) 驗收
   ```bash
   ls -l data/prices/
   head -5 data/prices/SPY.csv
   ```

## 風險提示
- 若無法連線 yfinance，腳本會自動產生合成資料，先確保管線不中斷；之後再切換為真實資料。
- 僅輸出 CSV，不寫 DB；Day 5 再做 `news` 與之後的 DB upsert。

完成後回覆「完成」，我會勾選 `T04` 並寫入 `progress.md`。
