#!/usr/bin/env python3
"""
QQQ Decision System - GitHub Actions 版本 (Enhanced)
Version: 2.1

更新內容：
- 同時寫入 Daily_Logs, Factor_Scores, Risk_Events
- 改進錯誤處理
- 更詳細的日誌輸出
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

import yfinance as yf
import pandas as pd
import numpy as np
import requests


# ============================================
# 設定
# ============================================

class Config:
    GAS_URL = os.environ.get('GAS_URL', '')
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKENV', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
    TICKER = "QQQ"
    INITIAL_CAPITAL = 10_000_000
    RISK_PREFERENCE = os.environ.get('RISK_PREFERENCE', 'neutral')
    DEFAULT_WEIGHTS = {
        "price_momentum": 0.30,
        "volume": 0.20,
        "vix": 0.20,
        "bond": 0.15,
        "mag7": 0.15
    }
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
    def fetch_all() -> Dict[str, Any]:
        print("📊 抓取市場數據...")
        data = {}
        
        # QQQ
        data['qqq'] = MarketDataFetcher.fetch_quote("QQQ")
        if data['qqq']['success']:
            print(f"  ✓ QQQ: ${data['qqq']['close']} ({data['qqq']['change_pct']:+.2f}%)")
        else:
            print(f"  ✗ QQQ: {data['qqq'].get('error')}")
        
        # VIX
        vix = MarketDataFetcher.fetch_quote("^VIX")
        data['vix'] = {
            "value": vix.get('close', 20),
            "change_pct": vix.get('change_pct', 0),
            "success": vix.get('success', False)
        }
        print(f"  ✓ VIX: {data['vix']['value']:.2f}")
        
        # 10Y Treasury
        tnx = MarketDataFetcher.fetch_quote("^TNX")
        data['us10y'] = {
            "value": tnx.get('close', 4.5),
            "change": round(tnx.get('close', 4.5) - tnx.get('prev_close', 4.5), 3),
            "success": tnx.get('success', False)
        }
        print(f"  ✓ 10Y: {data['us10y']['value']:.2f}%")
        
        # 2Y Treasury
        irx = MarketDataFetcher.fetch_quote("^IRX")
        data['us2y'] = {"value": irx.get('close', 4.3), "success": irx.get('success', False)}
        
        # DXY
        dxy = MarketDataFetcher.fetch_quote("DX-Y.NYB")
        data['dxy'] = {"value": dxy.get('close', 108), "success": dxy.get('success', False)}
        print(f"  ✓ DXY: {data['dxy']['value']:.2f}")
        
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
        
        # 移動平均
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
        
        # 成交量比
        if len(df) >= 20:
            avg_vol = df['Volume'].tail(20).mean()
            result['volume_ratio'] = round(float(df['Volume'].iloc[-1] / avg_vol), 2) if avg_vol > 0 else 1.0
        
        # 支撐壓力
        recent = df.tail(20)
        result['resistance'] = round(float(recent['High'].max()), 2)
        result['support'] = round(float(recent['Low'].min()), 2)
        
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
# 因子評分
# ============================================

class FactorScorer:
    def __init__(self):
        self.weights = Config.DEFAULT_WEIGHTS
    
    def score_all(self, data: Dict) -> Dict[str, Dict]:
        change = data.get('qqq', {}).get('change_pct', 0)
        vol_ratio = data.get('technicals', {}).get('volume_ratio', 1.0)
        vix = data.get('vix', {}).get('value', 20)
        bond_change = data.get('us10y', {}).get('change', 0)
        
        scores = {}
        
        # 1. Price Momentum
        if change > 2.0:
            scores['price_momentum'] = {"score": 9, "direction": "bullish"}
        elif change > 1.0:
            scores['price_momentum'] = {"score": 8, "direction": "bullish"}
        elif change > 0.5:
            scores['price_momentum'] = {"score": 7, "direction": "bullish"}
        elif change > 0:
            scores['price_momentum'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5:
            scores['price_momentum'] = {"score": 5, "direction": "neutral"}
        elif change > -1.0:
            scores['price_momentum'] = {"score": 4, "direction": "bearish"}
        elif change > -2.0:
            scores['price_momentum'] = {"score": 3, "direction": "bearish"}
        else:
            scores['price_momentum'] = {"score": 2, "direction": "bearish"}
        
        # 2. Volume
        if vol_ratio > 1.5 and change > 0:
            scores['volume'] = {"score": 9, "direction": "confirm"}
        elif vol_ratio > 1.2 and change > 0:
            scores['volume'] = {"score": 8, "direction": "confirm"}
        elif vol_ratio < 0.7 and change > 0:
            scores['volume'] = {"score": 4, "direction": "diverge"}
        elif vol_ratio > 1.5 and change < 0:
            scores['volume'] = {"score": 2, "direction": "confirm"}
        elif vol_ratio > 1.2 and change < 0:
            scores['volume'] = {"score": 3, "direction": "confirm"}
        elif vol_ratio < 0.7 and change < 0:
            scores['volume'] = {"score": 6, "direction": "diverge"}
        else:
            scores['volume'] = {"score": 5, "direction": "neutral"}
        
        # 3. VIX
        if vix < 12:
            scores['vix'] = {"score": 9, "direction": "favorable"}
        elif vix < 15:
            scores['vix'] = {"score": 8, "direction": "favorable"}
        elif vix < 18:
            scores['vix'] = {"score": 7, "direction": "favorable"}
        elif vix < 22:
            scores['vix'] = {"score": 5, "direction": "neutral"}
        elif vix < 28:
            scores['vix'] = {"score": 4, "direction": "unfavorable"}
        elif vix < 35:
            scores['vix'] = {"score": 3, "direction": "unfavorable"}
        else:
            scores['vix'] = {"score": 1, "direction": "unfavorable"}
        
        # 4. Bond
        if bond_change > 0.08:
            scores['bond'] = {"score": 2, "direction": "unfavorable"}
        elif bond_change > 0.05:
            scores['bond'] = {"score": 3, "direction": "unfavorable"}
        elif bond_change > 0.02:
            scores['bond'] = {"score": 4, "direction": "unfavorable"}
        elif bond_change < -0.08:
            scores['bond'] = {"score": 8, "direction": "favorable"}
        elif bond_change < -0.05:
            scores['bond'] = {"score": 7, "direction": "favorable"}
        elif bond_change < -0.02:
            scores['bond'] = {"score": 6, "direction": "favorable"}
        else:
            scores['bond'] = {"score": 5, "direction": "neutral"}
        
        # 5. Mag7 (用 QQQ 作為代理)
        if change > 1.5:
            scores['mag7'] = {"score": 8, "direction": "strong"}
        elif change > 0.5:
            scores['mag7'] = {"score": 7, "direction": "strong"}
        elif change > 0:
            scores['mag7'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5:
            scores['mag7'] = {"score": 5, "direction": "neutral"}
        elif change > -1.5:
            scores['mag7'] = {"score": 4, "direction": "weak"}
        else:
            scores['mag7'] = {"score": 3, "direction": "weak"}
        
        return scores
    
    def total_score(self, scores: Dict) -> float:
        total = sum(scores.get(f, {}).get('score', 5) * w for f, w in self.weights.items())
        return round(total, 1)
    
    def get_allocation(self, score: float) -> Dict:
        adj = score
        if Config.RISK_PREFERENCE == 'conservative':
            adj -= 1
        elif Config.RISK_PREFERENCE == 'aggressive':
            adj += 1
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
            "qqq_amount": int(Config.INITIAL_CAPITAL * pct / 100),
            "cash_amount": int(Config.INITIAL_CAPITAL * (100 - pct) / 100)
        }


# ============================================
# GAS 發送器 (Enhanced)
# ============================================

class GASNotifier:
    @staticmethod
    def send(action: str, data: Dict) -> bool:
        """發送數據到 GAS"""
        if not Config.GAS_URL:
            print(f"  ⚠️ GAS_URL 未設定，跳過 {action}")
            return False
        
        try:
            payload = {
                'action': action,
                'data': json.dumps(data, ensure_ascii=False)
            }
            response = requests.post(Config.GAS_URL, data=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                print(f"  ✅ {action}: {result.get('message', 'OK')}")
                return True
            else:
                print(f"  ❌ {action}: {result.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"  ❌ {action} 錯誤: {e}")
            return False
    
    @staticmethod
    def send_daily_log(data: Dict) -> bool:
        """發送每日日誌"""
        return GASNotifier.send('daily_log', data)
    
    @staticmethod
    def send_factor_scores(date: str, factor_scores: Dict, weights: Dict) -> bool:
        """發送因子評分"""
        payload = {
            'date': date,
            'factor_scores': factor_scores,
            'weights': weights
        }
        return GASNotifier.send('factor_scores', payload)
    
    @staticmethod
    def send_risk_event(event_data: Dict) -> bool:
        """發送風控事件"""
        return GASNotifier.send('risk_event', event_data)
    
    @staticmethod
    def send_notification_log(notif_data: Dict) -> bool:
        """記錄通知"""
        return GASNotifier.send('notification', notif_data)


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
            payload = {
                'chat_id': Config.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("  ✅ Telegram 通知已發送")
                return True
            else:
                print(f"  ❌ Telegram 錯誤: {result.get('description', 'Unknown')}")
                return False
        except Exception as e:
            print(f"  ❌ Telegram 錯誤: {e}")
            return False


# ============================================
# 主程式
# ============================================

def main():
    print("\n" + "="*60)
    print("🚀 QQQ 決策系統 v2.1 (GitHub Actions - Enhanced)")
    print("="*60)
    
    # 檢查設定
    print("\n🔧 檢查設定...")
    print(f"  GAS_URL: {'✓' if Config.GAS_URL else '✗'}")
    print(f"  Telegram: {'✓' if Config.TELEGRAM_BOT_TOKEN else '✗'}")
    print(f"  風險偏好: {Config.RISK_PREFERENCE}")
    
    # 1. 抓取數據
    print("\n" + "-"*60)
    market_data = MarketDataFetcher.fetch_all()
    
    if not market_data.get('qqq', {}).get('success'):
        print("\n❌ 無法取得 QQQ 數據，終止執行")
        sys.exit(1)
    
    # 2. 技術分析
    print("\n📈 執行技術分析...")
    technicals = TechnicalAnalyzer.analyze("QQQ", market_data['qqq']['close'])
    market_data['technicals'] = technicals
    print(f"  ✓ MA5: {technicals.get('ma5')}, MA20: {technicals.get('ma20')}")
    print(f"  ✓ RSI: {technicals.get('rsi')}, Vol Ratio: {technicals.get('volume_ratio')}")
    print(f"  ✓ Support: {technicals.get('support')}, Resistance: {technicals.get('resistance')}")
    
    # 3. 因子評分
    print("\n🎯 計算因子評分...")
    scorer = FactorScorer()
    factor_scores = scorer.score_all(market_data)
    total_score = scorer.total_score(factor_scores)
    allocation = scorer.get_allocation(total_score)
    
    for factor, score_data in factor_scores.items():
        weighted = score_data['score'] * Config.DEFAULT_WEIGHTS[factor]
        print(f"  • {factor}: {score_data['score']}/10 ({score_data['direction']}) → {weighted:.2f}")
    print(f"  ─────────────────")
    print(f"  總分: {total_score}/10")
    
    # 4. 判斷狀態
    regime = 'defense' if total_score <= 3.5 else 'offense' if total_score >= 6.5 else 'neutral'
    regime_text = {'offense': '🟢 進攻', 'neutral': '🟡 中性', 'defense': '🔴 防禦'}
    print(f"  狀態: {regime_text.get(regime)}")
    print(f"  配置: QQQ {allocation['qqq_pct']}% / 現金 {allocation['cash_pct']}%")
    
    # 5. 生成輸出
    now = datetime.now()
    close = market_data['qqq']['close']
    change = market_data['qqq']['change_pct']
    vix = market_data['vix']['value']
    
    output = {
        "meta": {
            "version": "2.1",
            "generated_at": now.isoformat(),
            "system": "GitHub_Actions_Enhanced"
        },
        "date": now.strftime("%Y-%m-%d"),
        "weekday": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now.weekday()],
        "ticker": "QQQ",
        "market_data": {
            "close": close,
            "change_pct": change,
            "volume_vs_20ma": technicals.get('volume_ratio'),
            "vix": vix,
            "vix_change_pct": market_data['vix'].get('change_pct'),
            "us10y": market_data['us10y']['value'],
            "us2y": market_data.get('us2y', {}).get('value'),
            "dxy": market_data['dxy']['value']
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
            "alerts": {
                "vix_above_40": vix > Config.VIX_ALERT_THRESHOLD,
                "single_day_drop": change < -4
            },
            "triggered": vix > Config.VIX_ALERT_THRESHOLD or change < -4
        },
        "prediction": {
            "next_day_bias": "bullish" if total_score >= 6 else "bearish" if total_score <= 4 else "neutral",
            "confidence": "high" if abs(total_score - 5) > 2 else "medium" if abs(total_score - 5) > 1 else "low"
        }
    }
    
    # 生成通知文字
    alert_text = ""
    if output['risk_management']['triggered']:
        alert_text = "\n\n⚠️ *風控警報觸發！*"
        if output['risk_management']['alerts']['vix_above_40']:
            alert_text += f"\n• VIX 超過 {Config.VIX_ALERT_THRESHOLD}！"
        if output['risk_management']['alerts']['single_day_drop']:
            alert_text += "\n• 單日跌幅超過 4%！"
    
    output['notification'] = f"""📊 *QQQ 盤後報告* {output['date']}

*市場數據*
收盤: ${close} ({'+' if change >= 0 else ''}{change:.2f}%)
VIX: {vix:.2f}
10Y: {market_data['us10y']['value']:.2f}%

*因子評分*
動能: {factor_scores['price_momentum']['score']} | 量能: {factor_scores['volume']['score']}
VIX: {factor_scores['vix']['score']} | 債市: {factor_scores['bond']['score']} | 權重股: {factor_scores['mag7']['score']}

*策略結論*
總分: {total_score}/10
狀態: {regime_text.get(regime)}

*配置建議*
QQQ: {allocation['qqq_pct']}% (${allocation['qqq_amount']:,})
現金: {allocation['cash_pct']}% (${allocation['cash_amount']:,})
止損: ${output['risk_management']['stop_loss']['price']}{alert_text}"""
    
    # 6. 儲存 JSON
    print("\n💾 儲存結果...")
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("  ✓ output.json")
    
    # 7. 發送到 GAS
    print("\n📤 發送到 Google Sheets...")
    
    # 7.1 發送每日日誌
    GASNotifier.send_daily_log(output)
    
    # 7.2 發送因子評分
    GASNotifier.send_factor_scores(
        output['date'],
        factor_scores,
        Config.DEFAULT_WEIGHTS
    )
    
    # 7.3 如果有風控事件，發送風控記錄
    if output['risk_management']['triggered']:
        risk_event = {
            'date': output['date'],
            'event_type': 'alert_triggered',
            'trigger_value': f"VIX={vix}, Change={change}%",
            'threshold': f"VIX>{Config.VIX_ALERT_THRESHOLD} or Drop>4%",
            'action_taken': 'notification_sent',
            'avoided_loss': '',
            'missed_gain': '',
            'net_benefit': ''
        }
        GASNotifier.send_risk_event(risk_event)
    
    # 8. 發送 Telegram
    print("\n📱 發送 Telegram 通知...")
    telegram_sent = TelegramNotifier.send(output['notification'])
    
    # 8.1 記錄通知
    GASNotifier.send_notification_log({
        'type': 'daily_report',
        'channel': 'telegram',
        'message': f"Daily report for {output['date']}",
        'status': 'sent' if telegram_sent else 'failed'
    })
    
    # 9. 輸出摘要
    print("\n" + "="*60)
    print("📋 執行摘要")
    print("="*60)
    print(f"  日期: {output['date']} ({output['weekday']})")
    print(f"  收盤: ${close} ({'+' if change >= 0 else ''}{change:.2f}%)")
    print(f"  評分: {total_score}/10 → {regime_text.get(regime)}")
    print(f"  配置: QQQ {allocation['qqq_pct']}% / 現金 {allocation['cash_pct']}%")
    if output['risk_management']['triggered']:
        print(f"  ⚠️ 風控警報已觸發！")
    print("="*60)
    
    # 10. 輸出完整 JSON
    print("\n📄 完整輸出:")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    print("\n✅ 執行完成！")


if __name__ == "__main__":
    main()
