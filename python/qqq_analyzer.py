#!/usr/bin/env python3
"""
QQQ Decision System - Data & Analysis Engine
Version: 2.0

使用方式:
    python qqq_analyzer.py                    # 基本執行
    python qqq_analyzer.py --risk aggressive  # 指定風險偏好
    python qqq_analyzer.py --post             # 執行後自動 POST 到 GAS
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import yfinance as yf
import pandas as pd
import numpy as np
import requests


# ============================================
# 設定類別
# ============================================

class Config:
    """系統設定"""
    
    TICKER = "QQQ"
    INITIAL_CAPITAL = 10_000_000
    
    DEFAULT_WEIGHTS = {
        "price_momentum": 0.30,
        "volume": 0.20,
        "vix": 0.20,
        "bond": 0.15,
        "mag7": 0.15
    }
    
    STOP_LOSS_PCT = 0.02
    VIX_ALERT_THRESHOLD = 40
    MAX_SINGLE_DAY_DROP = 0.04
    
    GAS_URL = None
    
    @classmethod
    def load_from_file(cls, filepath: str = "config.json"):
        """從 JSON 檔案載入設定"""
        if not os.path.exists(filepath):
            print(f"⚠️ 設定檔 {filepath} 不存在，使用預設值", file=sys.stderr)
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'ticker' in config:
            cls.TICKER = config['ticker']
        if 'initial_capital' in config:
            cls.INITIAL_CAPITAL = config['initial_capital']
        if 'weights' in config:
            cls.DEFAULT_WEIGHTS = config['weights']
        if 'gas_url' in config:
            cls.GAS_URL = config['gas_url']
        if 'stop_loss_pct' in config:
            cls.STOP_LOSS_PCT = config['stop_loss_pct']
        if 'vix_alert_threshold' in config:
            cls.VIX_ALERT_THRESHOLD = config['vix_alert_threshold']
        
        print(f"✅ 已載入設定檔: {filepath}", file=sys.stderr)


# ============================================
# 市場數據抓取器
# ============================================

class MarketDataFetcher:
    """市場數據抓取器"""
    
    @staticmethod
    def fetch_quote(ticker: str) -> Dict[str, Any]:
        """抓取即時報價"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if hist.empty:
                raise ValueError(f"無法取得 {ticker} 數據")
            
            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) > 1 else latest
            
            return {
                "ticker": ticker,
                "close": round(float(latest['Close']), 2),
                "prev_close": round(float(prev['Close']), 2),
                "change": round(float(latest['Close'] - prev['Close']), 2),
                "change_pct": round(float((latest['Close'] - prev['Close']) / prev['Close'] * 100), 2),
                "volume": int(latest['Volume']),
                "high": round(float(latest['High']), 2),
                "low": round(float(latest['Low']), 2),
                "open": round(float(latest['Open']), 2),
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
        except Exception as e:
            print(f"⚠️ 無法取得 {ticker} 數據: {e}", file=sys.stderr)
            return {"ticker": ticker, "success": False, "error": str(e)}
    
    @staticmethod
    def fetch_historical(ticker: str, period: str = "3mo") -> pd.DataFrame:
        """抓取歷史數據"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            print(f"⚠️ 無法取得 {ticker} 歷史數據: {e}", file=sys.stderr)
            return pd.DataFrame()
    
    @staticmethod
    def fetch_all_market_data() -> Dict[str, Any]:
        """抓取所有需要的市場數據"""
        print("📊 開始抓取市場數據...", file=sys.stderr)
        data = {}
        
        # QQQ
        print("  → 抓取 QQQ...", file=sys.stderr)
        data['qqq'] = MarketDataFetcher.fetch_quote("QQQ")
        
        # VIX
        print("  → 抓取 VIX...", file=sys.stderr)
        vix_data = MarketDataFetcher.fetch_quote("^VIX")
        if vix_data.get('success'):
            data['vix'] = {
                "value": vix_data['close'],
                "change_pct": vix_data['change_pct'],
                "success": True
            }
        else:
            data['vix'] = {"value": 20.0, "change_pct": 0, "success": False}
        
        # 10Y Treasury Yield
        print("  → 抓取 10Y 殖利率...", file=sys.stderr)
        tnx_data = MarketDataFetcher.fetch_quote("^TNX")
        if tnx_data.get('success'):
            data['us10y'] = {
                "value": tnx_data['close'],
                "change": tnx_data['change'],
                "success": True
            }
        else:
            data['us10y'] = {"value": 4.5, "change": 0, "success": False}
        
        # 2Y Treasury (使用 ^IRX 3個月作為代理，或直接設預設值)
        print("  → 抓取 2Y 殖利率...", file=sys.stderr)
        try:
            twy_data = MarketDataFetcher.fetch_quote("^IRX")
            if twy_data.get('success'):
                data['us2y'] = {"value": twy_data['close'], "success": True}
            else:
                data['us2y'] = {"value": 4.3, "success": False}
        except:
            data['us2y'] = {"value": 4.3, "success": False}
        
        # DXY 美元指數
        print("  → 抓取 DXY...", file=sys.stderr)
        try:
            dxy_data = MarketDataFetcher.fetch_quote("DX-Y.NYB")
            if dxy_data.get('success'):
                data['dxy'] = {"value": dxy_data['close'], "success": True}
            else:
                data['dxy'] = {"value": 108.0, "success": False}
        except:
            data['dxy'] = {"value": 108.0, "success": False}
        
        print("✅ 市場數據抓取完成", file=sys.stderr)
        return data


# ============================================
# 技術分析器
# ============================================

class TechnicalAnalyzer:
    """技術分析器"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = [5, 20, 60]) -> Dict[str, Optional[float]]:
        """計算移動平均線"""
        result = {}
        for period in periods:
            if len(df) >= period:
                result[f"ma{period}"] = round(float(df['Close'].tail(period).mean()), 2)
            else:
                result[f"ma{period}"] = None
        return result
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """計算 RSI"""
        if len(df) < period + 1:
            return None
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """計算 MACD"""
        if len(df) < 26:
            return {"macd": None, "signal": None, "histogram": None}
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        
        return {
            "macd": round(float(macd.iloc[-1]), 4),
            "signal": round(float(signal.iloc[-1]), 4),
            "histogram": round(float(histogram.iloc[-1]), 4)
        }
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, period: int = 20) -> float:
        """計算成交量相對於 20 日均量的比率"""
        if len(df) < period:
            return 1.0
        
        avg_volume = df['Volume'].tail(period).mean()
        current_volume = df['Volume'].iloc[-1]
        
        if avg_volume == 0:
            return 1.0
        
        return round(float(current_volume / avg_volume), 2)
    
    @staticmethod
    def find_support_resistance(df: pd.DataFrame, lookback: int = 20) -> Dict[str, float]:
        """計算支撐與壓力位"""
        if len(df) < lookback:
            lookback = len(df)
        
        recent = df.tail(lookback)
        
        resistance = round(float(recent['High'].max()), 2)
        support = round(float(recent['Low'].min()), 2)
        
        return {
            "resistance": resistance,
            "support": support
        }
    
    @staticmethod
    def get_position_vs_ma(close: float, ma5: Optional[float], ma20: Optional[float]) -> str:
        """判斷價格相對於均線的位置"""
        if ma5 is None or ma20 is None:
            return "unknown"
        
        if close > ma5 and close > ma20:
            return "above_both"
        elif close < ma5 and close < ma20:
            return "below_both"
        else:
            return "between"


# ============================================
# 因子評分器
# ============================================

class FactorScorer:
    """因子評分器"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or Config.DEFAULT_WEIGHTS
    
    def score_price_momentum(self, data: Dict) -> Dict[str, Any]:
        """評分：價格動能"""
        if not data.get('qqq', {}).get('success', False):
            return {"score": 5, "direction": "neutral", "note": "數據缺失"}
        
        change_pct = data['qqq'].get('change_pct', 0)
        position = data.get('technicals', {}).get('position_vs_ma', 'unknown')
        
        # 評分邏輯
        if change_pct > 2.0:
            score, direction = 9, 'bullish'
        elif change_pct > 1.0:
            score, direction = 8, 'bullish'
        elif change_pct > 0.5:
            score, direction = 7, 'bullish'
        elif change_pct > 0:
            score, direction = 6, 'neutral'
        elif change_pct > -0.5:
            score, direction = 5, 'neutral'
        elif change_pct > -1.0:
            score, direction = 4, 'bearish'
        elif change_pct > -2.0:
            score, direction = 3, 'bearish'
        else:
            score, direction = 2, 'bearish'
        
        # 均線位置加成
        if position == 'above_both' and change_pct > 0:
            score = min(10, score + 1)
        elif position == 'below_both' and change_pct < 0:
            score = max(1, score - 1)
        
        return {"score": score, "direction": direction}
    
    def score_volume(self, data: Dict) -> Dict[str, Any]:
        """評分：成交量"""
        volume_ratio = data.get('technicals', {}).get('volume_ratio', 1.0)
        change_pct = data.get('qqq', {}).get('change_pct', 0)
        
        # 量價配合判斷
        if volume_ratio > 1.5 and change_pct > 0:
            score, direction = 9, 'confirm'   # 放量上漲
        elif volume_ratio > 1.2 and change_pct > 0:
            score, direction = 8, 'confirm'   # 量增價漲
        elif volume_ratio < 0.7 and change_pct > 0:
            score, direction = 4, 'diverge'   # 量縮價漲（警訊）
        elif volume_ratio > 1.5 and change_pct < 0:
            score, direction = 2, 'confirm'   # 放量下跌
        elif volume_ratio > 1.2 and change_pct < 0:
            score, direction = 3, 'confirm'   # 量增價跌
        elif volume_ratio < 0.7 and change_pct < 0:
            score, direction = 6, 'diverge'   # 量縮價跌（可能止跌）
        else:
            score, direction = 5, 'neutral'
        
        return {"score": score, "direction": direction}
    
    def score_vix(self, data: Dict) -> Dict[str, Any]:
        """評分：VIX 環境"""
        vix = data.get('vix', {}).get('value', 20)
        vix_change = data.get('vix', {}).get('change_pct', 0)
        
        # VIX 水位評分
        if vix < 12:
            score, direction = 9, 'favorable'
        elif vix < 15:
            score, direction = 8, 'favorable'
        elif vix < 18:
            score, direction = 7, 'favorable'
        elif vix < 22:
            score, direction = 5, 'neutral'
        elif vix < 28:
            score, direction = 4, 'unfavorable'
        elif vix < 35:
            score, direction = 3, 'unfavorable'
        else:
            score, direction = 1, 'unfavorable'
        
        # VIX 變化調整
        if vix_change > 15:
            score = max(1, score - 2)  # VIX 急升
        elif vix_change > 8:
            score = max(1, score - 1)
        elif vix_change < -10:
            score = min(10, score + 1)  # VIX 急降
        
        return {"score": score, "direction": direction}
    
    def score_bond(self, data: Dict) -> Dict[str, Any]:
        """評分：債市訊號"""
        us10y_change = data.get('us10y', {}).get('change', 0)
        
        # 殖利率變化對科技股的影響
        if us10y_change > 0.10:
            score, direction = 2, 'unfavorable'  # 殖利率大漲
        elif us10y_change > 0.05:
            score, direction = 3, 'unfavorable'
        elif us10y_change > 0.02:
            score, direction = 4, 'unfavorable'
        elif us10y_change < -0.10:
            score, direction = 8, 'favorable'   # 殖利率大跌
        elif us10y_change < -0.05:
            score, direction = 7, 'favorable'
        elif us10y_change < -0.02:
            score, direction = 6, 'favorable'
        else:
            score, direction = 5, 'neutral'
        
        return {"score": score, "direction": direction}
    
    def score_mag7(self, data: Dict) -> Dict[str, Any]:
        """評分：權重股表現（簡化版，使用 QQQ 作為代理）"""
        change_pct = data.get('qqq', {}).get('change_pct', 0)
        
        # 簡化版：使用 QQQ 整體表現
        if change_pct > 1.5:
            score, direction = 8, 'strong'
        elif change_pct > 0.5:
            score, direction = 7, 'strong'
        elif change_pct > 0:
            score, direction = 6, 'neutral'
        elif change_pct > -0.5:
            score, direction = 5, 'neutral'
        elif change_pct > -1.5:
            score, direction = 4, 'weak'
        else:
            score, direction = 3, 'weak'
        
        return {"score": score, "direction": direction}
    
    def calculate_all_scores(self, data: Dict) -> Dict[str, Dict]:
        """計算所有因子評分"""
        return {
            "price_momentum": self.score_price_momentum(data),
            "volume": self.score_volume(data),
            "vix": self.score_vix(data),
            "bond": self.score_bond(data),
            "mag7": self.score_mag7(data)
        }
    
    def calculate_total_score(self, factor_scores: Dict) -> float:
        """計算加權總分"""
        total = 0
        for factor, weight in self.weights.items():
            score = factor_scores.get(factor, {}).get('score', 5)
            total += score * weight
        return round(total, 1)
    
    def get_regime(self, score: float) -> str:
        """根據評分判斷市場狀態"""
        if score <= 3.5:
            return 'defense'
        elif score <= 6.5:
            return 'neutral'
        else:
            return 'offense'
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> Dict[str, int]:
        """根據評分計算配置"""
        # 風險偏好調整
        adjusted_score = score
        if risk_pref == 'conservative':
            adjusted_score -= 1
        elif risk_pref == 'aggressive':
            adjusted_score += 1
        
        adjusted_score = max(0, min(10, adjusted_score))
        
        # 配置矩陣
        if adjusted_score <= 2:
            qqq_pct = 10
        elif adjusted_score <= 3:
            qqq_pct = 20
        elif adjusted_score <= 4:
            qqq_pct = 35
        elif adjusted_score <= 5:
            qqq_pct = 50
        elif adjusted_score <= 6:
            qqq_pct = 60
        elif adjusted_score <= 7:
            qqq_pct = 70
        elif adjusted_score <= 8:
            qqq_pct = 80
        else:
            qqq_pct = 90
        
        # 風險偏好微調
        if risk_pref == 'conservative':
            qqq_pct = max(10, qqq_pct - 10)
        elif risk_pref == 'aggressive':
            qqq_pct = min(90, qqq_pct + 10)
        
        cash_pct = 100 - qqq_pct
        qqq_amount = int(Config.INITIAL_CAPITAL * qqq_pct / 100)
        cash_amount = Config.INITIAL_CAPITAL - qqq_amount
        
        return {
            "qqq_pct": qqq_pct,
            "cash_pct": cash_pct,
            "qqq_amount": qqq_amount,
            "cash_amount": cash_amount
        }


# ============================================
# 輸出生成器
# ============================================

class OutputGenerator:
    """輸出生成器"""
    
    @staticmethod
    def generate_json(
        market_data: Dict,
        technicals: Dict,
        factor_scores: Dict,
        total_score: float,
        allocation: Dict,
        weights: Dict,
        risk_pref: str
    ) -> Dict[str, Any]:
        """生成標準化 JSON 輸出"""
        
        now = datetime.now()
        weekday_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        
        scorer = FactorScorer()
        regime = scorer.get_regime(total_score)
        
        # 檢查風控警報
        vix_value = market_data.get('vix', {}).get('value', 0)
        qqq_change = market_data.get('qqq', {}).get('change_pct', 0)
        
        alerts = {
            "vix_above_40": vix_value > Config.VIX_ALERT_THRESHOLD,
            "single_day_drop": qqq_change < -Config.MAX_SINGLE_DAY_DROP * 100
        }
        
        output = {
            "meta": {
                "version": "2.2",
                "generated_at": now.isoformat(),
                "system": "QQQ_Decision_System_Python",
                "risk_preference": risk_pref
            },
            "date": now.strftime("%Y-%m-%d"),
            "weekday": weekday_map[now.weekday()],
            "ticker": Config.TICKER,
            
            "market_data": {
                "close": market_data.get('qqq', {}).get('close'),
                "change_pct": market_data.get('qqq', {}).get('change_pct'),
                "volume_vs_20ma": technicals.get('volume_ratio'),
                "vix": market_data.get('vix', {}).get('value'),
                "vix_change_pct": market_data.get('vix', {}).get('change_pct'),
                "us10y": market_data.get('us10y', {}).get('value'),
                "us2y": market_data.get('us2y', {}).get('value'),
                "dxy": market_data.get('dxy', {}).get('value')
            },
            
            "technicals": {
                "resistance": technicals.get('resistance'),
                "support": technicals.get('support'),
                "ma5": technicals.get('ma5'),
                "ma20": technicals.get('ma20'),
                "ma60": technicals.get('ma60'),
                "rsi": technicals.get('rsi'),
                "macd": technicals.get('macd'),
                "position_vs_ma": technicals.get('position_vs_ma')
            },
            
            "scoring": {
                "weights": weights,
                "factor_scores": factor_scores,
                "total_score": total_score,
                "regime": regime
            },
            
            "allocation": allocation,
            
            "risk_management": {
                "stop_loss": {
                    "price": round(market_data.get('qqq', {}).get('close', 0) * (1 - Config.STOP_LOSS_PCT), 2),
                    "pct": round(-Config.STOP_LOSS_PCT * 100, 1)
                },
                "alerts": alerts,
                "triggered": any(alerts.values())
            },
            
            "prediction": {
                "next_day_bias": "bullish" if total_score >= 6 else "bearish" if total_score <= 4 else "neutral",
                "confidence": "high" if abs(total_score - 5) > 2 else "medium" if abs(total_score - 5) > 1 else "low"
            }
        }
        
        # 生成通知文字
        output['notification'] = OutputGenerator.generate_notification(output)
        
        return output
    
    @staticmethod
    def generate_notification(data: Dict) -> str:
        """生成通知文字"""
        regime_emoji = {
            'offense': '🟢 進攻',
            'neutral': '🟡 中性',
            'defense': '🔴 防禦'
        }
        
        score = data['scoring']['total_score']
        regime = data['scoring']['regime']
        regime_text = regime_emoji.get(regime, regime)
        
        close = data['market_data'].get('close', 0)
        change = data['market_data'].get('change_pct', 0)
        change_sign = '+' if change >= 0 else ''
        
        vix = data['market_data'].get('vix', 0)
        
        qqq_pct = data['allocation']['qqq_pct']
        cash_pct = data['allocation']['cash_pct']
        
        stop_loss = data['risk_management']['stop_loss']['price']
        
        # 風控警報
        alert_text = ""
        if data['risk_management'].get('triggered'):
            alert_text = "\n\n⚠️ *風控警報觸發！*"
            if data['risk_management']['alerts'].get('vix_above_40'):
                alert_text += f"\n• VIX 超過 {Config.VIX_ALERT_THRESHOLD}！"
            if data['risk_management']['alerts'].get('single_day_drop'):
                alert_text += f"\n• 單日跌幅超過 {Config.MAX_SINGLE_DAY_DROP*100}%！"
        
        notification = f"""📊 *QQQ 盤後報告* {data['date']}

*市場數據*
收盤: ${close} ({change_sign}{change:.2f}%)
VIX: {vix:.2f}

*策略評估*
評分: {score}/10
狀態: {regime_text}

*配置建議*
QQQ: {qqq_pct}% / 現金: {cash_pct}%
止損: ${stop_loss}{alert_text}"""
        
        return notification


# ============================================
# GAS 發送器
# ============================================

class GASPoster:
    """Google Apps Script 發送器"""
    
    @staticmethod
    def post_daily_log(data: Dict) -> bool:
        """發送每日日誌到 GAS"""
        if not Config.GAS_URL:
            print("⚠️ GAS_URL 未設定，跳過發送", file=sys.stderr)
            return False
        
        try:
            payload = {
                'action': 'daily_log',
                'data': json.dumps(data, ensure_ascii=False)
            }
            
            response = requests.post(Config.GAS_URL, data=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                print(f"✅ 已發送到 GAS: {result.get('message')}", file=sys.stderr)
                return True
            else:
                print(f"❌ GAS 發送失敗: {result.get('error')}", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"❌ GAS 發送錯誤: {e}", file=sys.stderr)
            return False


# ============================================
# 主分析器
# ============================================

class QQQAnalyzer:
    """主分析器 - 整合所有模組"""
    
    def __init__(self, weights: Dict[str, float] = None, risk_pref: str = 'neutral'):
        self.weights = weights or Config.DEFAULT_WEIGHTS
        self.risk_pref = risk_pref
        self.scorer = FactorScorer(self.weights)
    
    def run(self) -> Dict[str, Any]:
        """執行完整分析流程"""
        
        print("\n" + "="*50, file=sys.stderr)
        print("🚀 QQQ 決策系統 v2.0", file=sys.stderr)
        print("="*50 + "\n", file=sys.stderr)
        
        # Step 1: 抓取市場數據
        market_data = MarketDataFetcher.fetch_all_market_data()
        
        if not market_data.get('qqq', {}).get('success'):
            print("❌ 無法取得 QQQ 數據，中止分析", file=sys.stderr)
            return {"error": "Failed to fetch QQQ data"}
        
        # Step 2: 抓取歷史數據並計算技術指標
        print("\n📈 計算技術指標...", file=sys.stderr)
        hist = MarketDataFetcher.fetch_historical("QQQ")
        
        technicals = {}
        if not hist.empty:
            technicals.update(TechnicalAnalyzer.calculate_ma(hist))
            technicals['rsi'] = TechnicalAnalyzer.calculate_rsi(hist)
            technicals['macd'] = TechnicalAnalyzer.calculate_macd(hist)
            technicals['volume_ratio'] = TechnicalAnalyzer.calculate_volume_ratio(hist)
            technicals.update(TechnicalAnalyzer.find_support_resistance(hist))
            technicals['position_vs_ma'] = TechnicalAnalyzer.get_position_vs_ma(
                market_data['qqq']['close'],
                technicals.get('ma5'),
                technicals.get('ma20')
            )
        
        # 合併 technicals 到 market_data 供評分使用
        market_data['technicals'] = technicals
        
        # Step 3: 計算因子評分
        print("🎯 計算因子評分...", file=sys.stderr)
        factor_scores = self.scorer.calculate_all_scores(market_data)
        total_score = self.scorer.calculate_total_score(factor_scores)
        
        print(f"   → 總評分: {total_score}/10", file=sys.stderr)
        
        # Step 4: 計算配置
        print("💰 計算配置建議...", file=sys.stderr)
        allocation = self.scorer.get_allocation(total_score, self.risk_pref)
        
        print(f"   → QQQ: {allocation['qqq_pct']}% / 現金: {allocation['cash_pct']}%", file=sys.stderr)
        
        # Step 5: 生成輸出
        print("📝 生成輸出...\n", file=sys.stderr)
        output = OutputGenerator.generate_json(
            market_data=market_data,
            technicals=technicals,
            factor_scores=factor_scores,
            total_score=total_score,
            allocation=allocation,
            weights=self.weights,
            risk_pref=self.risk_pref
        )
        
        return output


# ============================================
# 主程式入口
# ============================================

def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description='QQQ Decision System - 美股盤後決策分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python qqq_analyzer.py                    # 基本執行
  python qqq_analyzer.py --risk aggressive  # 積極型
  python qqq_analyzer.py --post             # 執行後發送到 GAS
  python qqq_analyzer.py --output result.json  # 輸出到檔案
        """
    )
    
    parser.add_argument(
        '--risk', 
        choices=['conservative', 'neutral', 'aggressive'],
        default='neutral', 
        help='風險偏好 (預設: neutral)'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        default='config.json',
        help='設定檔路徑 (預設: config.json)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        help='輸出 JSON 檔案路徑'
    )
    
    parser.add_argument(
        '--post', 
        action='store_true',
        help='執行後自動 POST 到 GAS'
    )
    
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help='安靜模式，只輸出 JSON'
    )
    
    args = parser.parse_args()
    
    # 載入設定
    Config.load_from_file(args.config)
    
    # 覆蓋設定檔中的權重（如果有指定）
    weights = Config.DEFAULT_WEIGHTS
    
    # 執行分析
    analyzer = QQQAnalyzer(weights=weights, risk_pref=args.risk)
    result = analyzer.run()
    
    if 'error' in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 輸出 JSON
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"✅ 結果已寫入 {args.output}", file=sys.stderr)
    
    # 發送到 GAS
    if args.post:
        print("\n📤 發送到 Google Apps Script...", file=sys.stderr)
        GASPoster.post_daily_log(result)
    
    # 輸出到 stdout
    print(output_json)
    
    # 顯示摘要
    if not args.quiet:
        print("\n" + "="*50, file=sys.stderr)
        print("📋 分析摘要", file=sys.stderr)
        print("="*50, file=sys.stderr)
        print(f"日期: {result['date']}", file=sys.stderr)
        print(f"收盤: ${result['market_data']['close']}", file=sys.stderr)
        print(f"評分: {result['scoring']['total_score']}/10 ({result['scoring']['regime']})", file=sys.stderr)
        print(f"配置: QQQ {result['allocation']['qqq_pct']}%", file=sys.stderr)
        if result['risk_management'].get('triggered'):
            print("⚠️  風控警報已觸發！", file=sys.stderr)
        print("="*50 + "\n", file=sys.stderr)
    
    return result


if __name__ == "__main__":
    main()
