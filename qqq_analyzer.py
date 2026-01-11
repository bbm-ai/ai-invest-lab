#!/usr/bin/env python3
"""
QQQ Decision System - GitHub Actions 版本
Version: 2.0-github

專為 GitHub Actions 優化：
- 從環境變數讀取敏感設定
- 自動發送到 GAS
- 自動發送 Telegram 通知
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

import yfinance as yf
import pandas as pd
import numpy as np
import requests


# ============================================
# 設定 - 從環境變數讀取
# ============================================

class Config:
    """系統設定"""
    
    # 從環境變數讀取 (GitHub Secrets)
    GAS_URL = os.environ.get('GAS_URL', '')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    # 基本設定
    TICKER = "QQQ"
    INITIAL_CAPITAL = 10_000_000
    RISK_PREFERENCE = os.environ.get('RISK_PREFERENCE', 'neutral')
    
    # 因子權重
    DEFAULT_WEIGHTS = {
        "price_momentum": 0.30,
        "volume": 0.20,
        "vix": 0.20,
        "bond": 0.15,
        "mag7": 0.15
    }
    
    # 風控參數
    STOP_LOSS_PCT = 0.02
    VIX_ALERT_THRESHOLD = 40


# ============================================
# 市場數據抓取
# ============================================

class MarketDataFetcher:
    """市場數據抓取器"""
    
    @staticmethod
    def fetch_quote(ticker: str) -> Dict[str, Any]:
        """抓取報價"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if hist.empty:
                return {"ticker": ticker, "success": False, "error": "No data"}
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            return {
                "ticker": ticker,
                "close": round(float(latest['Close']), 2),
                "prev_close": round(float(prev['Close']), 2),
                "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                "volume": int(latest['Volume']),
                "high": round(float(latest['High']), 2),
                "low": round(float(latest['Low']), 2),
                "success": True
            }
        except Exception as e:
            return {"ticker": ticker, "success": False, "error": str(e)}
    
    @staticmethod
    def fetch_historical(ticker: str, period: str = "3mo") -> pd.DataFrame:
        """抓取歷史數據"""
        try:
            return yf.Ticker(ticker).history(period=period)
        except:
            return pd.DataFrame()
    
    @staticmethod
    def fetch_all() -> Dict[str, Any]:
        """抓取所有市場數據"""
        print("📊 抓取市場數據...")
        
        data = {}
        
        # QQQ
        data['qqq'] = MarketDataFetcher.fetch_quote("QQQ")
        print(f"  ✓ QQQ: ${data['qqq'].get('close', 'N/A')}")
        
        # VIX
        vix = MarketDataFetcher.fetch_quote("^VIX")
        data['vix'] = {
            "value": vix.get('close', 20),
            "change_pct": vix.get('change_pct', 0),
            "success": vix.get('success', False)
        }
        print(f"  ✓ VIX: {data['vix']['value']}")
        
        # 10Y Treasury
        tnx = MarketDataFetcher.fetch_quote("^TNX")
        data['us10y'] = {
            "value": tnx.get('close', 4.5),
            "change": tnx.get('close', 4.5) - tnx.get('prev_close', 4.5),
            "success": tnx.get('success', False)
        }
        print(f"  ✓ 10Y: {data['us10y']['value']}%")
        
        # DXY
        dxy = MarketDataFetcher.fetch_quote("DX-Y.NYB")
        data['dxy'] = {"value": dxy.get('close', 108), "success": dxy.get('success', False)}
        
        return data


# ============================================
# 技術分析
# ============================================

class TechnicalAnalyzer:
    """技術分析器"""
    
    @staticmethod
    def analyze(df: pd.DataFrame, close: float) -> Dict[str, Any]:
        """執行技術分析"""
        if df.empty:
            return {}
        
        result = {}
        
        # 移動平均
        for period in [5, 20, 60]:
            if len(df) >= period:
                result[f'ma{period}'] = round(float(df['Close'].tail(period).mean()), 2)
        
        # RSI
        if len(df) >= 15:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            result['rsi'] = round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None
        
        # 成交量比
        if len(df) >= 20:
            avg_vol = df['Volume'].tail(20).mean()
            result['volume_ratio'] = round(float(df['Volume'].iloc[-1] / avg_vol), 2) if avg_vol > 0 else 1.0
        
        # 支撐壓力
        recent = df.tail(20)
        result['resistance'] = round(float(recent['High'].max()), 2)
        result['support'] = round(float(recent['Low'].min()), 2)
        
        # 均線位置
        ma5 = result.get('ma5')
        ma20 = result.get('ma20')
        if ma5 and ma20:
            if close > ma5 and close > ma20:
                result['position_vs_ma'] = 'above_both'
            elif close < ma5 and close < ma20:
                result['position_vs_ma'] = 'below_both'
            else:
                result['position_vs_ma'] = 'between'
        
        return result


# ============================================
# 因子評分
# ============================================

class FactorScorer:
    """因子評分器"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or Config.DEFAULT_WEIGHTS
    
    def score_all(self, data: Dict) -> Dict[str, Dict]:
        """計算所有因子評分"""
        return {
            "price_momentum": self._score_momentum(data),
            "volume": self._score_volume(data),
            "vix": self._score_vix(data),
            "bond": self._score_bond(data),
            "mag7": self._score_mag7(data)
        }
    
    def _score_momentum(self, data: Dict) -> Dict:
        change = data.get('qqq', {}).get('change_pct', 0)
        if change > 1.5: return {"score": 8, "direction": "bullish"}
        elif change > 0.5: return {"score": 7, "direction": "bullish"}
        elif change > 0: return {"score": 6, "direction": "neutral"}
        elif change > -0.5: return {"score": 5, "direction": "neutral"}
        elif change > -1.5: return {"score": 4, "direction": "bearish"}
        else: return {"score": 2, "direction": "bearish"}
    
    def _score_volume(self, data: Dict) -> Dict:
        vol_ratio = data.get('technicals', {}).get('volume_ratio', 1.0)
        change = data.get('qqq', {}).get('change_pct', 0)
        
        if vol_ratio > 1.2 and change > 0: return {"score": 8, "direction": "confirm"}
        elif vol_ratio < 0.8 and change > 0: return {"score": 4, "direction": "diverge"}
        elif vol_ratio > 1.2 and change < 0: return {"score": 3, "direction": "confirm"}
        else: return {"score": 5, "direction": "neutral"}
    
    def _score_vix(self, data: Dict) -> Dict:
        vix = data.get('vix', {}).get('value', 20)
        if vix < 15: return {"score": 8, "direction": "favorable"}
        elif vix < 20: return {"score": 7, "direction": "favorable"}
        elif vix < 25: return {"score": 5, "direction": "neutral"}
        elif vix < 30: return {"score": 3, "direction": "unfavorable"}
        else: return {"score": 1, "direction": "unfavorable"}
    
    def _score_bond(self, data: Dict) -> Dict:
        change = data.get('us10y', {}).get('change', 0)
        if change > 0.05: return {"score": 3, "direction": "unfavorable"}
        elif change > 0.02: return {"score": 4, "direction": "unfavorable"}
        elif change < -0.05: return {"score": 7, "direction": "favorable"}
        elif change < -0.02: return {"score": 6, "direction": "favorable"}
        else: return {"score": 5, "direction": "neutral"}
    
    def _score_mag7(self, data: Dict) -> Dict:
        change = data.get('qqq', {}).get('change_pct', 0)
        if change > 1: return {"score": 7, "direction": "strong"}
        elif change > 0: return {"score": 6, "direction": "neutral"}
        elif change > -1: return {"score": 4, "direction": "neutral"}
        else: return {"score": 3, "direction": "weak"}
    
    def total_score(self, factor_scores: Dict) -> float:
        """計算加權總分"""
        total = sum(
            factor_scores.get(f, {}).get('score', 5) * w 
            for f, w in self.weights.items()
        )
        return round(total, 1)
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> Dict:
        """計算配置"""
        adj = score + (-1 if risk_pref == 'conservative' else 1 if risk_pref == 'aggressive' else 0)
        adj = max(0, min(10, adj))
        
        if adj <= 3: qqq_pct = 20
        elif adj <= 4: qqq_pct = 35
        elif adj <= 5: qqq_pct = 50
        elif adj <= 6: qqq_pct = 60
        elif adj <= 7: qqq_pct = 75
        else: qqq_pct = 85
        
        return {
            "qqq_pct": qqq_pct,
            "cash_pct": 100 - qqq_pct,
            "qqq_amount": int(Config.INITIAL_CAPITAL * qqq_pct / 100),
            "cash_amount": int(Config.INITIAL_CAPITAL * (100 - qqq_pct) / 100)
        }


# ============================================
# 通知發送
# ============================================

class Notifier:
    """通知發送器"""
    
    @staticmethod
    def send_to_gas(data: Dict) -> bool:
        """發送到 Google Apps Script"""
        if not Config.GAS_URL:
            print("⚠️ GAS_URL 未設定")
            return False
        
        try:
            payload = {'action': 'daily_log', 'data': json.dumps(data, ensure_ascii=False)}
            response = requests.post(Config.GAS_URL, data=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                print(f"✅ GAS: {result.get('message')}")
                return True
            else:
                print(f"❌ GAS 錯誤: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ GAS 發送失敗: {e}")
            return False
    
    @staticmethod
    def send_telegram(message: str) -> bool:
        """發送 Telegram 通知"""
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            print("⚠️ Telegram 未設定")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("✅ Telegram 通知已發送")
                return True
            else:
                print(f"❌ Telegram 錯誤: {result}")
                return False
        except Exception as e:
            print(f"❌ Telegram 發送失敗: {e}")
            return False


# ============================================
# 主程式
# ============================================

def generate_output(market_data: Dict, technicals: Dict, factor_scores: Dict, 
                    total_score: float, allocation: Dict) -> Dict:
    """生成完整輸出"""
    
    now = datetime.now()
    weekday_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    
    regime = 'defense' if total_score <= 3.5 else 'offense' if total_score >= 6.5 else 'neutral'
    
    vix = market_data.get('vix', {}).get('value', 0)
    change = market_data.get('qqq', {}).get('change_pct', 0)
    close = market_data.get('qqq', {}).get('close', 0)
    
    output = {
        "meta": {
            "version": "2.2",
            "generated_at": now.isoformat(),
            "system": "QQQ_Decision_System_GitHub"
        },
        "date": now.strftime("%Y-%m-%d"),
        "weekday": weekday_map[now.weekday()],
        "ticker": "QQQ",
        "market_data": {
            "close": close,
            "change_pct": change,
            "volume_vs_20ma": technicals.get('volume_ratio'),
            "vix": vix,
            "vix_change_pct": market_data.get('vix', {}).get('change_pct'),
            "us10y": market_data.get('us10y', {}).get('value'),
            "dxy": market_data.get('dxy', {}).get('value')
        },
        "technicals": technicals,
        "scoring": {
            "weights": Config.DEFAULT_WEIGHTS,
            "factor_scores": factor_scores,
            "total_score": total_score,
            "regime": regime
        },
        "allocation": allocation,
        "risk_management": {
            "stop_loss": {"price": round(close * (1 - Config.STOP_LOSS_PCT), 2)},
            "alerts": {"vix_above_40": vix > 40, "single_day_drop": change < -4},
            "triggered": vix > 40 or change < -4
        },
        "prediction": {
            "next_day_bias": "bullish" if total_score >= 6 else "bearish" if total_score <= 4 else "neutral",
            "confidence": "high" if abs(total_score - 5) > 2 else "medium"
        }
    }
    
    # 生成通知文字
    regime_text = {'offense': '🟢 進攻', 'neutral': '🟡 中性', 'defense': '🔴 防禦'}
    alert_text = "\n\n⚠️ *風控警報！*" if output['risk_management']['triggered'] else ""
    
    output['notification'] = f"""📊 *QQQ 盤後報告* {output['date']}

*市場數據*
收盤: ${close} ({'+' if change >= 0 else ''}{change:.2f}%)
VIX: {vix:.2f}

*策略評估*
評分: {total_score}/10
狀態: {regime_text.get(regime, regime)}

*配置建議*
QQQ: {allocation['qqq_pct']}% / 現金: {allocation['cash_pct']}%
止損: ${output['risk_management']['stop_loss']['price']}{alert_text}"""
    
    return output


def main():
    """主程式"""
    print("\n" + "="*50)
    print("🚀 QQQ 決策系統 v2.0 (GitHub Actions)")
    print("="*50 + "\n")
    
    # 檢查環境變數
    print("🔧 檢查設定...")
    print(f"  GAS_URL: {'✓ 已設定' if Config.GAS_URL else '✗ 未設定'}")
    print(f"  Telegram: {'✓ 已設定' if Config.TELEGRAM_BOT_TOKEN else '✗ 未設定'}")
    print()
    
    # 1. 抓取數據
    market_data = MarketDataFetcher.fetch_all()
    
    if not market_data.get('qqq', {}).get('success'):
        print("❌ 無法取得 QQQ 數據")
        sys.exit(1)
    
    # 2. 技術分析
    print("\n📈 技術分析...")
    hist = MarketDataFetcher.fetch_historical("QQQ")
    technicals = TechnicalAnalyzer.analyze(hist, market_data['qqq']['close'])
    market_data['technicals'] = technicals
    
    # 3. 因子評分
    print("🎯 因子評分...")
    scorer = FactorScorer()
    factor_scores = scorer.score_all(market_data)
    total_score = scorer.total_score(factor_scores)
    print(f"  總評分: {total_score}/10")
    
    # 4. 配置建議
    allocation = scorer.get_allocation(total_score, Config.RISK_PREFERENCE)
    print(f"  配置: QQQ {allocation['qqq_pct']}%")
    
    # 5. 生成輸出
    output = generate_output(market_data, technicals, factor_scores, total_score, allocation)
    
    # 6. 儲存 JSON
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("\n💾 已儲存 output.json")
    
    # 7. 發送到 GAS
    print("\n📤 發送數據...")
    Notifier.send_to_gas(output)
    
    # 8. 發送 Telegram
    Notifier.send_telegram(output['notification'])
    
    # 9. 輸出摘要
    print("\n" + "="*50)
    print("📋 分析完成")
    print("="*50)
    print(f"日期: {output['date']}")
    print(f"收盤: ${output['market_data']['close']}")
    print(f"評分: {total_score}/10 ({output['scoring']['regime']})")
    print(f"配置: QQQ {allocation['qqq_pct']}%")
    print("="*50 + "\n")
    
    # 輸出 JSON 到 stdout
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
