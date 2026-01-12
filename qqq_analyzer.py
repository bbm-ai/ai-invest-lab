#!/usr/bin/env python3
"""
QQQ Decision System - Multi-Strategy Version
Version: 4.0

策略：
1. default - 原本的多因子策略
2. ma20 - MA20 趨勢策略 (新增)

使用方式：
    python qqq_analyzer.py                    # 使用預設策略
    python qqq_analyzer.py --strategy ma20    # 使用 MA20 策略
    python qqq_analyzer.py --validate
    python qqq_analyzer.py --weekly
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

import yfinance as yf
import pandas as pd
import numpy as np
import requests


# ============================================
# 設定
# ============================================

class Config:
    GAS_URL = os.environ.get('GAS_URL', '')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
    TICKER = "QQQ"
    INITIAL_CAPITAL = 10_000_000
    RISK_PREFERENCE = os.environ.get('RISK_PREFERENCE', 'neutral')
    STRATEGY = os.environ.get('STRATEGY', 'default')  # default 或 ma20
    STOP_LOSS_PCT = 0.02
    VIX_ALERT_THRESHOLD = 40


# ============================================
# 市場數據
# ============================================

class MarketDataFetcher:
    @staticmethod
    def fetch_quote(ticker: str) -> Dict[str, Any]:
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if hist.empty:
                return {"ticker": ticker, "success": False, "error": "No data"}
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            return {
                "ticker": ticker,
                "success": True,
                "close": round(float(latest['Close']), 2),
                "prev_close": round(float(prev['Close']), 2),
                "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                "volume": int(latest['Volume']),
                "high": round(float(latest['High']), 2),
                "low": round(float(latest['Low']), 2)
            }
        except Exception as e:
            return {"ticker": ticker, "success": False, "error": str(e)}
    
    @staticmethod
    def fetch_historical(ticker: str, period: str = "3mo") -> pd.DataFrame:
        try:
            return yf.Ticker(ticker).history(period=period)
        except:
            return pd.DataFrame()
    
    @staticmethod
    def fetch_all() -> Dict[str, Any]:
        print("📊 抓取市場數據...")
        data = {}
        
        data['qqq'] = MarketDataFetcher.fetch_quote("QQQ")
        if data['qqq']['success']:
            print(f"  ✓ QQQ: ${data['qqq']['close']} ({data['qqq']['change_pct']:+.2f}%)")
        
        vix = MarketDataFetcher.fetch_quote("^VIX")
        data['vix'] = {"value": vix.get('close', 20), "change_pct": vix.get('change_pct', 0), "success": vix.get('success', False)}
        print(f"  ✓ VIX: {data['vix']['value']:.2f}")
        
        tnx = MarketDataFetcher.fetch_quote("^TNX")
        data['us10y'] = {"value": tnx.get('close', 4.5), "change": round(tnx.get('close', 4.5) - tnx.get('prev_close', 4.5), 3)}
        
        irx = MarketDataFetcher.fetch_quote("^IRX")
        data['us2y'] = {"value": irx.get('close', 4.3)}
        
        dxy = MarketDataFetcher.fetch_quote("DX-Y.NYB")
        data['dxy'] = {"value": dxy.get('close', 108)}
        
        return data


# ============================================
# 技術分析
# ============================================

class TechnicalAnalyzer:
    @staticmethod
    def analyze(ticker: str, close: float) -> Dict[str, Any]:
        try:
            df = yf.Ticker(ticker).history(period="3mo")
            if df.empty:
                return {}
        except:
            return {}
        
        result = {}
        
        # 移動平均線
        for p in [5, 20, 60]:
            if len(df) >= p:
                result[f'ma{p}'] = round(float(df['Close'].tail(p).mean()), 2)
        
        # RSI
        if len(df) >= 15:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            if not pd.isna(rsi.iloc[-1]):
                result['rsi'] = round(float(rsi.iloc[-1]), 2)
        
        # 成交量比率
        if len(df) >= 20:
            avg_vol = df['Volume'].tail(20).mean()
            result['volume_ratio'] = round(float(df['Volume'].iloc[-1] / avg_vol), 2) if avg_vol > 0 else 1.0
        
        # 支撐壓力
        recent = df.tail(20)
        result['resistance'] = round(float(recent['High'].max()), 2)
        result['support'] = round(float(recent['Low'].min()), 2)
        
        # MA20 相對位置
        ma20 = result.get('ma20')
        if ma20:
            result['above_ma20'] = close > ma20
            result['ma20_diff_pct'] = round((close - ma20) / ma20 * 100, 2)
        
        # ★ 新增：計算連續站上/跌破 MA20 的天數
        if len(df) >= 20 and 'ma20' in result:
            ma20_series = df['Close'].rolling(20).mean()
            closes = df['Close']
            
            # 計算最近幾天的狀態
            days_above = 0
            days_below = 0
            
            for i in range(1, min(6, len(df))):  # 檢查最近 5 天
                idx = -i
                if pd.isna(ma20_series.iloc[idx]):
                    break
                if closes.iloc[idx] > ma20_series.iloc[idx]:
                    if days_below == 0:
                        days_above += 1
                    else:
                        break
                else:
                    if days_above == 0:
                        days_below += 1
                    else:
                        break
            
            result['consecutive_days_above_ma20'] = days_above
            result['consecutive_days_below_ma20'] = days_below
        
        # 均線位置
        ma5, ma20 = result.get('ma5'), result.get('ma20')
        if ma5 and ma20:
            if close > ma5 and close > ma20:
                result['position_vs_ma'] = 'above_both'
            elif close < ma5 and close < ma20:
                result['position_vs_ma'] = 'below_both'
            else:
                result['position_vs_ma'] = 'between'
        
        return result


# ============================================
# 策略基類
# ============================================

class BaseStrategy(ABC):
    """策略基類"""
    
    name: str = "base"
    version: str = "1.0"
    description: str = "Base strategy"
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.capital = self.config.get('capital', Config.INITIAL_CAPITAL)
    
    @abstractmethod
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """計算評分，返回包含 total_score, regime, factor_scores 等"""
        pass
    
    @abstractmethod
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> Dict[str, Any]:
        """根據評分計算配置"""
        pass
    
    def get_regime(self, score: float) -> str:
        """判斷市場狀態"""
        if score <= 3.5:
            return 'defense'
        elif score >= 6.5:
            return 'offense'
        return 'neutral'


# ============================================
# 預設策略（多因子）
# ============================================

class DefaultStrategy(BaseStrategy):
    """原本的多因子策略"""
    
    name = "default"
    version = "1.0"
    description = "多因子動能策略"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.weights = {
            "price_momentum": 0.30,
            "volume": 0.20,
            "vix": 0.20,
            "bond": 0.15,
            "mag7": 0.15
        }
    
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        change = data.get('qqq', {}).get('change_pct', 0)
        vol_ratio = data.get('technicals', {}).get('volume_ratio', 1.0)
        vix = data.get('vix', {}).get('value', 20)
        bond_change = data.get('us10y', {}).get('change', 0)
        
        factor_scores = {}
        
        # Price Momentum
        if change > 2.0: factor_scores['price_momentum'] = {"score": 9, "direction": "bullish"}
        elif change > 1.0: factor_scores['price_momentum'] = {"score": 8, "direction": "bullish"}
        elif change > 0.5: factor_scores['price_momentum'] = {"score": 7, "direction": "bullish"}
        elif change > 0: factor_scores['price_momentum'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5: factor_scores['price_momentum'] = {"score": 5, "direction": "neutral"}
        elif change > -1.0: factor_scores['price_momentum'] = {"score": 4, "direction": "bearish"}
        elif change > -2.0: factor_scores['price_momentum'] = {"score": 3, "direction": "bearish"}
        else: factor_scores['price_momentum'] = {"score": 2, "direction": "bearish"}
        
        # Volume
        if vol_ratio > 1.5 and change > 0: factor_scores['volume'] = {"score": 9, "direction": "confirm"}
        elif vol_ratio > 1.2 and change > 0: factor_scores['volume'] = {"score": 8, "direction": "confirm"}
        elif vol_ratio < 0.7 and change > 0: factor_scores['volume'] = {"score": 4, "direction": "diverge"}
        elif vol_ratio > 1.5 and change < 0: factor_scores['volume'] = {"score": 2, "direction": "confirm"}
        elif vol_ratio > 1.2 and change < 0: factor_scores['volume'] = {"score": 3, "direction": "confirm"}
        elif vol_ratio < 0.7 and change < 0: factor_scores['volume'] = {"score": 6, "direction": "diverge"}
        else: factor_scores['volume'] = {"score": 5, "direction": "neutral"}
        
        # VIX
        if vix < 12: factor_scores['vix'] = {"score": 9, "direction": "favorable"}
        elif vix < 15: factor_scores['vix'] = {"score": 8, "direction": "favorable"}
        elif vix < 18: factor_scores['vix'] = {"score": 7, "direction": "favorable"}
        elif vix < 22: factor_scores['vix'] = {"score": 5, "direction": "neutral"}
        elif vix < 28: factor_scores['vix'] = {"score": 4, "direction": "unfavorable"}
        elif vix < 35: factor_scores['vix'] = {"score": 3, "direction": "unfavorable"}
        else: factor_scores['vix'] = {"score": 1, "direction": "unfavorable"}
        
        # Bond
        if bond_change > 0.08: factor_scores['bond'] = {"score": 2, "direction": "unfavorable"}
        elif bond_change > 0.05: factor_scores['bond'] = {"score": 3, "direction": "unfavorable"}
        elif bond_change > 0.02: factor_scores['bond'] = {"score": 4, "direction": "unfavorable"}
        elif bond_change < -0.08: factor_scores['bond'] = {"score": 8, "direction": "favorable"}
        elif bond_change < -0.05: factor_scores['bond'] = {"score": 7, "direction": "favorable"}
        elif bond_change < -0.02: factor_scores['bond'] = {"score": 6, "direction": "favorable"}
        else: factor_scores['bond'] = {"score": 5, "direction": "neutral"}
        
        # Mag7 (用 QQQ 動能代理)
        if change > 1.5: factor_scores['mag7'] = {"score": 8, "direction": "strong"}
        elif change > 0.5: factor_scores['mag7'] = {"score": 7, "direction": "strong"}
        elif change > 0: factor_scores['mag7'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5: factor_scores['mag7'] = {"score": 5, "direction": "neutral"}
        elif change > -1.5: factor_scores['mag7'] = {"score": 4, "direction": "weak"}
        else: factor_scores['mag7'] = {"score": 3, "direction": "weak"}
        
        # 加權總分
        total = sum(factor_scores[f]['score'] * self.weights[f] for f in self.weights)
        total = round(total, 1)
        
        return {
            "total_score": total,
            "regime": self.get_regime(total),
            "factor_scores": factor_scores,
            "weights": self.weights
        }
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> Dict[str, Any]:
        adj = score
        if risk_pref == 'conservative': adj -= 1
        elif risk_pref == 'aggressive': adj += 1
        adj = max(0, min(10, adj))
        
        if adj <= 2: pct = 10
        elif adj <= 3: pct = 20
        elif adj <= 4: pct = 35
        elif adj <= 5: pct = 50
        elif adj <= 6: pct = 60
        elif adj <= 7: pct = 75
        elif adj <= 8: pct = 85
        else: pct = 90
        
        return {
            "qqq_pct": pct,
            "cash_pct": 100 - pct,
            "qqq_amount": int(self.capital * pct / 100),
            "cash_amount": int(self.capital * (100 - pct) / 100)
        }


# ============================================
# MA20 策略 (新增)
# ============================================

class MA20Strategy(BaseStrategy):
    """
    MA20 趨勢策略
    
    規則：
    - 連續 2 天收盤 > MA20 → 看多 (買進/加碼)
    - 連續 2 天收盤 < MA20 → 看空 (賣出/減碼)
    - 其他 → 中性 (維持)
    """
    
    name = "ma20"
    version = "1.0"
    description = "MA20 趨勢跟隨策略"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.weights = {
            "ma20_position": 0.50,   # MA20 相對位置（主要因子）
            "ma20_trend": 0.30,      # MA20 連續天數
            "vix_filter": 0.20       # VIX 過濾（風控）
        }
    
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        close = data.get('qqq', {}).get('close', 0)
        technicals = data.get('technicals', {})
        vix = data.get('vix', {}).get('value', 20)
        
        ma20 = technicals.get('ma20', close)
        days_above = technicals.get('consecutive_days_above_ma20', 0)
        days_below = technicals.get('consecutive_days_below_ma20', 0)
        ma20_diff_pct = technicals.get('ma20_diff_pct', 0)
        
        factor_scores = {}
        
        # ===== 因子 1: MA20 相對位置 =====
        # 價格距離 MA20 的幅度
        if ma20_diff_pct > 5:
            factor_scores['ma20_position'] = {"score": 9, "direction": "strong_above", "value": ma20_diff_pct}
        elif ma20_diff_pct > 3:
            factor_scores['ma20_position'] = {"score": 8, "direction": "above", "value": ma20_diff_pct}
        elif ma20_diff_pct > 1:
            factor_scores['ma20_position'] = {"score": 7, "direction": "above", "value": ma20_diff_pct}
        elif ma20_diff_pct > 0:
            factor_scores['ma20_position'] = {"score": 6, "direction": "slight_above", "value": ma20_diff_pct}
        elif ma20_diff_pct > -1:
            factor_scores['ma20_position'] = {"score": 5, "direction": "slight_below", "value": ma20_diff_pct}
        elif ma20_diff_pct > -3:
            factor_scores['ma20_position'] = {"score": 4, "direction": "below", "value": ma20_diff_pct}
        elif ma20_diff_pct > -5:
            factor_scores['ma20_position'] = {"score": 3, "direction": "below", "value": ma20_diff_pct}
        else:
            factor_scores['ma20_position'] = {"score": 2, "direction": "strong_below", "value": ma20_diff_pct}
        
        # ===== 因子 2: MA20 連續天數 (核心邏輯) =====
        if days_above >= 3:
            # 連續 3 天以上站上 → 強烈看多
            factor_scores['ma20_trend'] = {"score": 9, "direction": "bullish", "days_above": days_above, "signal": "BUY"}
        elif days_above >= 2:
            # 連續 2 天站上 → 買進訊號
            factor_scores['ma20_trend'] = {"score": 8, "direction": "bullish", "days_above": days_above, "signal": "BUY"}
        elif days_above == 1:
            # 剛站上 1 天 → 觀察
            factor_scores['ma20_trend'] = {"score": 6, "direction": "neutral", "days_above": days_above, "signal": "WATCH"}
        elif days_below == 1:
            # 剛跌破 1 天 → 觀察
            factor_scores['ma20_trend'] = {"score": 5, "direction": "neutral", "days_below": days_below, "signal": "WATCH"}
        elif days_below >= 2:
            # 連續 2 天跌破 → 賣出訊號
            factor_scores['ma20_trend'] = {"score": 3, "direction": "bearish", "days_below": days_below, "signal": "SELL"}
        elif days_below >= 3:
            # 連續 3 天以上跌破 → 強烈看空
            factor_scores['ma20_trend'] = {"score": 2, "direction": "bearish", "days_below": days_below, "signal": "SELL"}
        else:
            # 無明確訊號
            factor_scores['ma20_trend'] = {"score": 5, "direction": "neutral", "signal": "HOLD"}
        
        # ===== 因子 3: VIX 過濾 (風控) =====
        if vix < 15:
            factor_scores['vix_filter'] = {"score": 8, "direction": "low_risk", "value": vix}
        elif vix < 20:
            factor_scores['vix_filter'] = {"score": 7, "direction": "normal", "value": vix}
        elif vix < 25:
            factor_scores['vix_filter'] = {"score": 5, "direction": "elevated", "value": vix}
        elif vix < 30:
            factor_scores['vix_filter'] = {"score": 3, "direction": "high", "value": vix}
        else:
            # VIX > 30，無論 MA20 訊號如何，都要謹慎
            factor_scores['vix_filter'] = {"score": 2, "direction": "extreme", "value": vix}
        
        # ===== 計算加權總分 =====
        total = sum(factor_scores[f]['score'] * self.weights[f] for f in self.weights)
        total = round(total, 1)
        
        # ===== 生成交易訊號 =====
        signal = factor_scores['ma20_trend'].get('signal', 'HOLD')
        
        # VIX 過高時覆蓋訊號
        if vix > 35:
            signal = "RISK_OFF"
            total = min(total, 4)  # 強制降低評分
        
        return {
            "total_score": total,
            "regime": self.get_regime(total),
            "factor_scores": factor_scores,
            "weights": self.weights,
            "signal": signal,
            "ma20": ma20,
            "close": close,
            "days_above_ma20": days_above,
            "days_below_ma20": days_below
        }
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> Dict[str, Any]:
        """
        MA20 策略的配置邏輯 - 更明確的進出場
        """
        adj = score
        if risk_pref == 'conservative': adj -= 1
        elif risk_pref == 'aggressive': adj += 1
        adj = max(0, min(10, adj))
        
        # MA20 策略的配置更極端（趨勢跟隨特性）
        if adj <= 2:
            pct = 0    # 強烈賣出訊號 → 全部出場
        elif adj <= 3:
            pct = 10   # 賣出訊號
        elif adj <= 4:
            pct = 25
        elif adj <= 5:
            pct = 40   # 中性觀望
        elif adj <= 6:
            pct = 55
        elif adj <= 7:
            pct = 70   # 買進訊號
        elif adj <= 8:
            pct = 85   # 強烈買進
        else:
            pct = 95   # 連續多天站上 → 高度持倉
        
        return {
            "qqq_pct": pct,
            "cash_pct": 100 - pct,
            "qqq_amount": int(self.capital * pct / 100),
            "cash_amount": int(self.capital * (100 - pct) / 100)
        }


# ============================================
# 策略註冊表
# ============================================

STRATEGIES = {
    'default': DefaultStrategy,
    'ma20': MA20Strategy,
}


def get_strategy(name: str, config: Dict = None) -> BaseStrategy:
    """取得策略實例"""
    if name not in STRATEGIES:
        available = list(STRATEGIES.keys())
        print(f"⚠️ 未知策略: {name}，可用策略: {available}")
        print(f"  使用預設策略: default")
        name = 'default'
    
    strategy_class = STRATEGIES[name]
    return strategy_class(config)


# ============================================
# GAS 通訊
# ============================================

class GASClient:
    @staticmethod
    def send(action: str, data: Dict) -> Dict:
        if not Config.GAS_URL:
            print(f"  ⚠️ GAS_URL 未設定")
            return {"success": False, "error": "GAS_URL not set"}
        
        try:
            payload = {'action': action, 'data': json.dumps(data, ensure_ascii=False)}
            response = requests.post(Config.GAS_URL, data=payload, timeout=30)
            result = response.json()
            status = "✅" if result.get('success') else "❌"
            print(f"  {status} {action}: {result.get('message', result.get('error', 'Unknown'))}")
            return result
        except Exception as e:
            print(f"  ❌ {action} 錯誤: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get(action: str, params: Dict = None) -> Dict:
        if not Config.GAS_URL:
            return {"error": "GAS_URL not set"}
        
        try:
            url = Config.GAS_URL + f"?action={action}"
            if params:
                for k, v in params.items():
                    url += f"&{k}={v}"
            response = requests.get(url, timeout=30)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# ============================================
# Telegram 通知
# ============================================

class TelegramNotifier:
    @staticmethod
    def send(message: str) -> bool:
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            print("  ⚠️ Telegram 未設定")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': Config.TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            print(f"  {'✅' if result.get('ok') else '❌'} Telegram")
            return result.get('ok', False)
        except Exception as e:
            print(f"  ❌ Telegram 錯誤: {e}")
            return False


# ============================================
# 每日分析
# ============================================

def run_daily_analysis(strategy_name: str = None):
    """每日盤後分析"""
    strategy_name = strategy_name or Config.STRATEGY
    
    print("\n" + "="*60)
    print(f"🚀 QQQ 每日分析 (策略: {strategy_name})")
    print("="*60)
    
    # 1. 抓取數據
    market_data = MarketDataFetcher.fetch_all()
    if not market_data.get('qqq', {}).get('success'):
        print("❌ 無法取得 QQQ 數據")
        sys.exit(1)
    
    # 2. 技術分析
    print("\n📈 技術分析...")
    technicals = TechnicalAnalyzer.analyze("QQQ", market_data['qqq']['close'])
    market_data['technicals'] = technicals
    
    # 顯示 MA20 相關資訊
    if 'ma20' in technicals:
        print(f"  ✓ MA20: ${technicals['ma20']}")
        print(f"  ✓ 價格 vs MA20: {technicals.get('ma20_diff_pct', 0):+.2f}%")
        days_above = technicals.get('consecutive_days_above_ma20', 0)
        days_below = technicals.get('consecutive_days_below_ma20', 0)
        if days_above > 0:
            print(f"  ✓ 連續站上 MA20: {days_above} 天")
        elif days_below > 0:
            print(f"  ✓ 連續跌破 MA20: {days_below} 天")
    
    # 3. 取得策略並評分
    print(f"\n🎯 策略評分 ({strategy_name})...")
    strategy = get_strategy(strategy_name)
    score_result = strategy.score(market_data)
    
    total_score = score_result['total_score']
    regime = score_result['regime']
    factor_scores = score_result['factor_scores']
    
    # 顯示因子評分
    for factor, score_data in factor_scores.items():
        weight = score_result.get('weights', {}).get(factor, 0)
        weighted = score_data['score'] * weight
        print(f"  • {factor}: {score_data['score']}/10 (權重: {weight}) → {weighted:.2f}")
    print(f"  總分: {total_score}/10")
    
    # MA20 策略額外顯示交易訊號
    if strategy_name == 'ma20':
        signal = score_result.get('signal', 'HOLD')
        signal_emoji = {'BUY': '🟢 買進', 'SELL': '🔴 賣出', 'HOLD': '🟡 持有', 'WATCH': '👀 觀察', 'RISK_OFF': '⚠️ 風控'}
        print(f"  訊號: {signal_emoji.get(signal, signal)}")
    
    # 4. 計算配置
    allocation = strategy.get_allocation(total_score, Config.RISK_PREFERENCE)
    
    # 5. 判斷狀態
    regime_text = {'offense': '🟢 進攻', 'neutral': '🟡 中性', 'defense': '🔴 防禦'}
    
    # 6. 生成輸出
    now = datetime.now()
    close = market_data['qqq']['close']
    change = market_data['qqq']['change_pct']
    vix = market_data['vix']['value']
    
    output = {
        "meta": {"version": "4.0", "generated_at": now.isoformat(), "mode": "daily_analysis", "strategy": strategy_name},
        "date": now.strftime("%Y-%m-%d"),
        "weekday": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now.weekday()],
        "ticker": "QQQ",
        "strategy": strategy_name,
        "market_data": {
            "close": close, "change_pct": change,
            "volume_vs_20ma": technicals.get('volume_ratio'),
            "vix": vix, "vix_change_pct": market_data['vix'].get('change_pct'),
            "us10y": market_data['us10y']['value'],
            "us2y": market_data.get('us2y', {}).get('value'),
            "dxy": market_data['dxy']['value'],
            "ma20": technicals.get('ma20'),
            "ma20_diff_pct": technicals.get('ma20_diff_pct'),
            "days_above_ma20": technicals.get('consecutive_days_above_ma20', 0),
            "days_below_ma20": technicals.get('consecutive_days_below_ma20', 0)
        },
        "technicals": technicals,
        "scoring": {
            "weights": score_result.get('weights', {}),
            "factor_scores": factor_scores,
            "total_score": total_score,
            "regime": regime,
            "signal": score_result.get('signal')
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
    
    # 通知文字
    alert_text = "\n\n⚠️ *風控警報！*" if output['risk_management']['triggered'] else ""
    
    # MA20 策略的特別通知格式
    if strategy_name == 'ma20':
        signal = score_result.get('signal', 'HOLD')
        signal_text = {'BUY': '🟢 買進訊號', 'SELL': '🔴 賣出訊號', 'HOLD': '🟡 持有', 'WATCH': '👀 觀察', 'RISK_OFF': '⚠️ 風控減碼'}
        ma20_val = technicals.get('ma20', 0)
        days_above = technicals.get('consecutive_days_above_ma20', 0)
        days_below = technicals.get('consecutive_days_below_ma20', 0)
        
        position_text = f"連續 {days_above} 天站上" if days_above > 0 else f"連續 {days_below} 天跌破" if days_below > 0 else "剛觸及"
        
        output['notification'] = f"""📊 *QQQ MA20策略報告* {output['date']}

*市場* | ${close} ({'+' if change >= 0 else ''}{change:.2f}%)
*MA20* | ${ma20_val:.2f} ({position_text})
*VIX* | {vix:.1f}

*訊號* | {signal_text.get(signal, signal)}
*評分* | {total_score}/10 {regime_text.get(regime)}
*配置* | QQQ {allocation['qqq_pct']}% / 現金 {allocation['cash_pct']}%
*止損* | ${output['risk_management']['stop_loss']['price']}{alert_text}"""
    else:
        output['notification'] = f"""📊 *QQQ 盤後報告* {output['date']}

*市場* | ${close} ({'+' if change >= 0 else ''}{change:.2f}%) | VIX: {vix:.1f}
*評分* | {total_score}/10 {regime_text.get(regime)}
*配置* | QQQ {allocation['qqq_pct']}% / 現金 {allocation['cash_pct']}%
*止損* | ${output['risk_management']['stop_loss']['price']}{alert_text}"""
    
    # 7. 儲存
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 8. 發送到 GAS
    print("\n📤 發送到 Google Sheets...")
    GASClient.send('daily_log', output)
    GASClient.send('factor_scores', {'date': output['date'], 'factor_scores': factor_scores, 'weights': score_result.get('weights', {}), 'strategy': strategy_name})
    
    if output['risk_management']['triggered']:
        GASClient.send('risk_event', {
            'date': output['date'], 'event_type': 'alert_triggered',
            'trigger_value': f"VIX={vix}, Change={change}%",
            'threshold': 'VIX>40 or Drop>4%', 'action_taken': 'notification_sent'
        })
    
    # 9. Telegram
    print("\n📱 發送通知...")
    TelegramNotifier.send(output['notification'])
    
    print("\n✅ 每日分析完成！")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    return output


# ============================================
# 每日驗證
# ============================================

def run_daily_validation():
    """每日驗證 - 每日 09:35 執行"""
    print("\n" + "="*60)
    print("🔍 QQQ 每日驗證 (Daily Validation)")
    print("="*60)
    
    today = datetime.now()
    
    # 1. 從 GAS 取得前日的預測記錄
    print("\n📥 讀取前日預測...")
    history = GASClient.get('history', {'days': 5})
    
    if isinstance(history, dict) and 'error' in history:
        print(f"  ❌ 無法讀取歷史數據: {history['error']}")
        return None
    
    if not history or not isinstance(history, list) or len(history) < 1:
        print("  ⚠️ 無歷史數據可驗證")
        return None
    
    prev_record = history[-1]
    prev_date = prev_record.get('date', 'Unknown')
    prev_prediction = prev_record.get('prediction', prev_record.get('next_day_bias', 'neutral'))
    prev_close = float(prev_record.get('close', 0))
    prev_strategy = prev_record.get('strategy', 'default')
    
    print(f"  前日日期: {prev_date}")
    print(f"  前日策略: {prev_strategy}")
    print(f"  前日預測: {prev_prediction}")
    print(f"  前日收盤: ${prev_close}")
    
    # 2. 取得今日實際數據
    print("\n📊 取得今日數據...")
    qqq = MarketDataFetcher.fetch_quote("QQQ")
    
    if not qqq.get('success'):
        print("  ❌ 無法取得今日數據")
        return None
    
    today_close = qqq['close']
    today_change = qqq['change_pct']
    
    print(f"  今日收盤: ${today_close}")
    print(f"  今日漲跌: {today_change:+.2f}%")
    
    # 3. 判斷預測是否正確
    if today_change > 0.1:
        actual_direction = 'bullish'
    elif today_change < -0.1:
        actual_direction = 'bearish'
    else:
        actual_direction = 'neutral'
    
    is_correct = False
    if prev_prediction == actual_direction:
        is_correct = True
    elif prev_prediction == 'bullish' and today_change > 0:
        is_correct = True
    elif prev_prediction == 'bearish' and today_change < 0:
        is_correct = True
    elif prev_prediction == 'neutral' and abs(today_change) < 0.5:
        is_correct = True
    
    print(f"\n📋 驗證結果:")
    print(f"  預測方向: {prev_prediction}")
    print(f"  實際方向: {actual_direction}")
    print(f"  預測正確: {'✅ 是' if is_correct else '❌ 否'}")
    
    # 4. 計算 PnL
    prev_qqq_pct = float(prev_record.get('qqq_pct', 50))
    pnl_pct = today_change * (prev_qqq_pct / 100)
    pnl_amount = Config.INITIAL_CAPITAL * (pnl_pct / 100)
    
    print(f"  配置 QQQ: {prev_qqq_pct}%")
    print(f"  組合報酬: {pnl_pct:+.2f}%")
    print(f"  損益金額: ${pnl_amount:+,.0f}")
    
    # 5. 生成驗證記錄
    validation_record = {
        "date": today.strftime("%Y-%m-%d"),
        "prediction_date": prev_date,
        "strategy": prev_strategy,
        "predicted_direction": prev_prediction,
        "actual_direction": actual_direction,
        "actual_change_pct": today_change,
        "is_correct": is_correct,
        "pnl_pct": round(pnl_pct, 2),
        "pnl_amount": round(pnl_amount, 0),
        "prev_qqq_pct": prev_qqq_pct,
        "prev_close": prev_close,
        "today_close": today_close
    }
    
    # 6. 發送到 GAS
    print("\n📤 記錄驗證結果...")
    GASClient.send('validation', validation_record)
    
    # 7. 發送 Telegram 通知
    result_emoji = "✅" if is_correct else "❌"
    notification = f"""🔍 *QQQ 預測驗證* {today.strftime("%Y-%m-%d")}

*前日預測* ({prev_date}) [{prev_strategy}]
方向: {prev_prediction}
配置: QQQ {prev_qqq_pct}%

*今日結果*
收盤: ${today_close} ({'+' if today_change >= 0 else ''}{today_change:.2f}%)
實際方向: {actual_direction}

*驗證* {result_emoji}
預測{'正確' if is_correct else '錯誤'}
組合報酬: {pnl_pct:+.2f}%
損益: ${pnl_amount:+,.0f}"""
    
    print("\n📱 發送通知...")
    TelegramNotifier.send(notification)
    
    # 8. 儲存
    with open('validation.json', 'w', encoding='utf-8') as f:
        json.dump(validation_record, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 每日驗證完成！")
    
    return validation_record


# ============================================
# 週末覆盤
# ============================================

def run_weekly_review():
    """週末覆盤"""
    print("\n" + "="*60)
    print("📊 QQQ 週末覆盤 (Weekly Review)")
    print("="*60)
    
    today = datetime.now()
    
    days_since_monday = today.weekday()
    if today.weekday() == 5:
        days_since_monday = 5
    elif today.weekday() == 6:
        days_since_monday = 6
    
    week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")
    week_end = (today - timedelta(days=days_since_monday - 4)).strftime("%Y-%m-%d")
    
    print(f"\n📅 覆盤週期: {week_start} ~ {week_end}")
    
    history = GASClient.get('history', {'days': 7})
    
    if isinstance(history, dict) and 'error' in history:
        print(f"  ❌ 無法讀取數據: {history['error']}")
        return None
    
    if not history or not isinstance(history, list):
        print("  ⚠️ 無數據可覆盤")
        return None
    
    week_data = [r for r in history if week_start <= r.get('date', '') <= week_end]
    
    if len(week_data) < 1:
        print("  ⚠️ 本週無交易數據")
        return None
    
    print(f"  本週交易日: {len(week_data)} 天")
    
    # 計算績效
    daily_pnls = []
    correct_predictions = 0
    total_predictions = 0
    week_returns = []
    
    for record in week_data:
        try:
            change_pct = float(record.get('change_pct', 0))
            qqq_pct = float(record.get('qqq_pct', 50))
            daily_pnl = change_pct * (qqq_pct / 100)
            daily_pnls.append(daily_pnl)
            week_returns.append(change_pct)
            
            prediction = record.get('prediction', record.get('next_day_bias', ''))
            if prediction:
                total_predictions += 1
                if (prediction == 'bullish' and change_pct > 0) or \
                   (prediction == 'bearish' and change_pct < 0) or \
                   (prediction == 'neutral' and abs(change_pct) < 0.5):
                    correct_predictions += 1
        except:
            continue
    
    week_return = sum(daily_pnls)
    win_days = len([p for p in daily_pnls if p > 0])
    lose_days = len([p for p in daily_pnls if p < 0])
    win_rate = (win_days / len(daily_pnls) * 100) if daily_pnls else 0
    
    gains = [p for p in daily_pnls if p > 0]
    losses = [p for p in daily_pnls if p < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 1
    profit_loss_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
    
    cumulative = []
    cum_sum = 0
    for p in daily_pnls:
        cum_sum += p
        cumulative.append(cum_sum)
    
    peak = cumulative[0] if cumulative else 0
    max_drawdown = 0
    for c in cumulative:
        if c > peak:
            peak = c
        drawdown = peak - c
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    prediction_accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    qqq_week_return = sum(week_returns) if week_returns else 0
    alpha = week_return - qqq_week_return
    
    starting_nav = Config.INITIAL_CAPITAL
    ending_nav = starting_nav * (1 + week_return / 100)
    
    weekly_review = {
        "week_start": week_start,
        "week_end": week_end,
        "trading_days": len(week_data),
        "starting_nav": starting_nav,
        "ending_nav": round(ending_nav, 0),
        "week_return": round(week_return, 2),
        "qqq_return": round(qqq_week_return, 2),
        "alpha": round(alpha, 2),
        "win_rate": round(win_rate, 1),
        "win_days": win_days,
        "lose_days": lose_days,
        "profit_loss_ratio": round(profit_loss_ratio, 2),
        "max_drawdown": round(max_drawdown, 2),
        "prediction_accuracy": round(prediction_accuracy, 1),
        "correct_predictions": correct_predictions,
        "total_predictions": total_predictions,
        "generated_at": today.isoformat()
    }
    
    print(f"\n📈 績效指標:")
    print(f"  週報酬: {week_return:+.2f}%")
    print(f"  Alpha: {alpha:+.2f}%")
    print(f"  勝率: {win_rate:.0f}%")
    print(f"  預測準確率: {prediction_accuracy:.0f}%")
    
    # 發送到 GAS
    print("\n📤 記錄週報...")
    GASClient.send('weekly_review', weekly_review)
    
    # Telegram 通知
    perf_emoji = "📈" if week_return > 0 else "📉" if week_return < 0 else "➖"
    alpha_emoji = "🏆" if alpha > 0 else "😔" if alpha < 0 else "➖"
    
    notification = f"""📊 *QQQ 週末覆盤*
{week_start} ~ {week_end}

*績效表現* {perf_emoji}
週報酬: {week_return:+.2f}%
QQQ: {qqq_week_return:+.2f}%
Alpha: {alpha:+.2f}% {alpha_emoji}

*交易統計*
交易日: {len(week_data)} 天
勝率: {win_rate:.0f}% ({win_days}W-{lose_days}L)
盈虧比: {profit_loss_ratio:.2f}
最大回撤: {max_drawdown:.2f}%

*預測表現*
準確率: {prediction_accuracy:.0f}% ({correct_predictions}/{total_predictions})

*淨值*
期末: ${ending_nav:,.0f}
週損益: ${ending_nav - starting_nav:+,.0f}"""
    
    print("\n📱 發送通知...")
    TelegramNotifier.send(notification)
    
    with open('weekly_review.json', 'w', encoding='utf-8') as f:
        json.dump(weekly_review, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 週末覆盤完成！")
    
    return weekly_review


# ============================================
# 主程式
# ============================================

def main():
    parser = argparse.ArgumentParser(description='QQQ Decision System v4.0')
    parser.add_argument('--strategy', type=str, default=None, help='策略名稱 (default, ma20)')
    parser.add_argument('--validate', action='store_true', help='執行每日驗證')
    parser.add_argument('--weekly', action='store_true', help='執行週末覆盤')
    parser.add_argument('--all', action='store_true', help='執行所有功能（測試用）')
    parser.add_argument('--list-strategies', action='store_true', help='列出所有可用策略')
    args = parser.parse_args()
    
    if args.list_strategies:
        print("\n📋 可用策略:")
        for name, cls in STRATEGIES.items():
            print(f"  • {name}: {cls.description}")
        return
    
    print(f"\n⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 GAS: {'✓' if Config.GAS_URL else '✗'}")
    print(f"📱 Telegram: {'✓' if Config.TELEGRAM_BOT_TOKEN else '✗'}")
    print(f"📊 策略: {args.strategy or Config.STRATEGY}")
    
    if args.all:
        run_daily_analysis(args.strategy)
        run_daily_validation()
        run_weekly_review()
    elif args.validate:
        run_daily_validation()
    elif args.weekly:
        run_weekly_review()
    else:
        run_daily_analysis(args.strategy)


if __name__ == "__main__":
    main()
