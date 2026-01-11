#!/usr/bin/env python3
"""
QQQ Decision System - Complete Version
Version: 3.0

功能：
1. 每日分析 (Daily Analysis) - 每日 22:30
2. 每日驗證 (Daily Validation) - 每日 09:35 驗證前日預測
3. 週末覆盤 (Weekly Review) - 每週六 10:00

使用方式：
    python qqq_analyzer.py                # 每日分析
    python qqq_analyzer.py --validate     # 每日驗證
    python qqq_analyzer.py --weekly       # 週末覆盤
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

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
    def fetch_historical(ticker: str, period: str = "1mo") -> pd.DataFrame:
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
        
        for p in [5, 20, 60]:
            if len(df) >= p:
                result[f'ma{p}'] = round(float(df['Close'].tail(p).mean()), 2)
        
        if len(df) >= 15:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            if not pd.isna(rsi.iloc[-1]):
                result['rsi'] = round(float(rsi.iloc[-1]), 2)
        
        if len(df) >= 20:
            avg_vol = df['Volume'].tail(20).mean()
            result['volume_ratio'] = round(float(df['Volume'].iloc[-1] / avg_vol), 2) if avg_vol > 0 else 1.0
        
        recent = df.tail(20)
        result['resistance'] = round(float(recent['High'].max()), 2)
        result['support'] = round(float(recent['Low'].min()), 2)
        
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
        
        # Price Momentum
        if change > 2.0: scores['price_momentum'] = {"score": 9, "direction": "bullish"}
        elif change > 1.0: scores['price_momentum'] = {"score": 8, "direction": "bullish"}
        elif change > 0.5: scores['price_momentum'] = {"score": 7, "direction": "bullish"}
        elif change > 0: scores['price_momentum'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5: scores['price_momentum'] = {"score": 5, "direction": "neutral"}
        elif change > -1.0: scores['price_momentum'] = {"score": 4, "direction": "bearish"}
        elif change > -2.0: scores['price_momentum'] = {"score": 3, "direction": "bearish"}
        else: scores['price_momentum'] = {"score": 2, "direction": "bearish"}
        
        # Volume
        if vol_ratio > 1.5 and change > 0: scores['volume'] = {"score": 9, "direction": "confirm"}
        elif vol_ratio > 1.2 and change > 0: scores['volume'] = {"score": 8, "direction": "confirm"}
        elif vol_ratio < 0.7 and change > 0: scores['volume'] = {"score": 4, "direction": "diverge"}
        elif vol_ratio > 1.5 and change < 0: scores['volume'] = {"score": 2, "direction": "confirm"}
        elif vol_ratio > 1.2 and change < 0: scores['volume'] = {"score": 3, "direction": "confirm"}
        elif vol_ratio < 0.7 and change < 0: scores['volume'] = {"score": 6, "direction": "diverge"}
        else: scores['volume'] = {"score": 5, "direction": "neutral"}
        
        # VIX
        if vix < 12: scores['vix'] = {"score": 9, "direction": "favorable"}
        elif vix < 15: scores['vix'] = {"score": 8, "direction": "favorable"}
        elif vix < 18: scores['vix'] = {"score": 7, "direction": "favorable"}
        elif vix < 22: scores['vix'] = {"score": 5, "direction": "neutral"}
        elif vix < 28: scores['vix'] = {"score": 4, "direction": "unfavorable"}
        elif vix < 35: scores['vix'] = {"score": 3, "direction": "unfavorable"}
        else: scores['vix'] = {"score": 1, "direction": "unfavorable"}
        
        # Bond
        if bond_change > 0.08: scores['bond'] = {"score": 2, "direction": "unfavorable"}
        elif bond_change > 0.05: scores['bond'] = {"score": 3, "direction": "unfavorable"}
        elif bond_change > 0.02: scores['bond'] = {"score": 4, "direction": "unfavorable"}
        elif bond_change < -0.08: scores['bond'] = {"score": 8, "direction": "favorable"}
        elif bond_change < -0.05: scores['bond'] = {"score": 7, "direction": "favorable"}
        elif bond_change < -0.02: scores['bond'] = {"score": 6, "direction": "favorable"}
        else: scores['bond'] = {"score": 5, "direction": "neutral"}
        
        # Mag7
        if change > 1.5: scores['mag7'] = {"score": 8, "direction": "strong"}
        elif change > 0.5: scores['mag7'] = {"score": 7, "direction": "strong"}
        elif change > 0: scores['mag7'] = {"score": 6, "direction": "neutral"}
        elif change > -0.5: scores['mag7'] = {"score": 5, "direction": "neutral"}
        elif change > -1.5: scores['mag7'] = {"score": 4, "direction": "weak"}
        else: scores['mag7'] = {"score": 3, "direction": "weak"}
        
        return scores
    
    def total_score(self, scores: Dict) -> float:
        total = sum(scores.get(f, {}).get('score', 5) * w for f, w in self.weights.items())
        return round(total, 1)
    
    def get_allocation(self, score: float) -> Dict:
        adj = score
        if Config.RISK_PREFERENCE == 'conservative': adj -= 1
        elif Config.RISK_PREFERENCE == 'aggressive': adj += 1
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
            "qqq_pct": pct, "cash_pct": 100 - pct,
            "qqq_amount": int(Config.INITIAL_CAPITAL * pct / 100),
            "cash_amount": int(Config.INITIAL_CAPITAL * (100 - pct) / 100)
        }


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
# 每日分析 (Daily Analysis)
# ============================================

def run_daily_analysis():
    """每日盤後分析 - 每日 22:30 執行"""
    print("\n" + "="*60)
    print("🚀 QQQ 每日分析 (Daily Analysis)")
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
    
    # 3. 因子評分
    print("\n🎯 因子評分...")
    scorer = FactorScorer()
    factor_scores = scorer.score_all(market_data)
    total_score = scorer.total_score(factor_scores)
    allocation = scorer.get_allocation(total_score)
    
    for factor, score_data in factor_scores.items():
        weighted = score_data['score'] * Config.DEFAULT_WEIGHTS[factor]
        print(f"  • {factor}: {score_data['score']}/10 → {weighted:.2f}")
    print(f"  總分: {total_score}/10")
    
    # 4. 判斷狀態
    regime = 'defense' if total_score <= 3.5 else 'offense' if total_score >= 6.5 else 'neutral'
    regime_text = {'offense': '🟢 進攻', 'neutral': '🟡 中性', 'defense': '🔴 防禦'}
    
    # 5. 生成輸出
    now = datetime.now()
    close = market_data['qqq']['close']
    change = market_data['qqq']['change_pct']
    vix = market_data['vix']['value']
    
    output = {
        "meta": {"version": "3.0", "generated_at": now.isoformat(), "mode": "daily_analysis"},
        "date": now.strftime("%Y-%m-%d"),
        "weekday": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now.weekday()],
        "ticker": "QQQ",
        "market_data": {
            "close": close, "change_pct": change,
            "volume_vs_20ma": technicals.get('volume_ratio'),
            "vix": vix, "vix_change_pct": market_data['vix'].get('change_pct'),
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
    output['notification'] = f"""📊 *QQQ 盤後報告* {output['date']}

*市場* | ${close} ({'+' if change >= 0 else ''}{change:.2f}%) | VIX: {vix:.1f}
*評分* | {total_score}/10 {regime_text.get(regime)}
*配置* | QQQ {allocation['qqq_pct']}% / 現金 {allocation['cash_pct']}%
*止損* | ${output['risk_management']['stop_loss']['price']}{alert_text}"""
    
    # 6. 儲存
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 7. 發送到 GAS
    print("\n📤 發送到 Google Sheets...")
    GASClient.send('daily_log', output)
    GASClient.send('factor_scores', {'date': output['date'], 'factor_scores': factor_scores, 'weights': Config.DEFAULT_WEIGHTS})
    
    if output['risk_management']['triggered']:
        GASClient.send('risk_event', {
            'date': output['date'], 'event_type': 'alert_triggered',
            'trigger_value': f"VIX={vix}, Change={change}%",
            'threshold': 'VIX>40 or Drop>4%', 'action_taken': 'notification_sent'
        })
    
    # 8. Telegram
    print("\n📱 發送通知...")
    TelegramNotifier.send(output['notification'])
    
    print("\n✅ 每日分析完成！")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    return output


# ============================================
# 每日驗證 (Daily Validation)
# ============================================

def run_daily_validation():
    """每日驗證 - 每日 09:35 執行，驗證前日預測"""
    print("\n" + "="*60)
    print("🔍 QQQ 每日驗證 (Daily Validation)")
    print("="*60)
    
    today = datetime.now()
    
    # 1. 從 GAS 取得前日的預測記錄
    print("\n📥 讀取前日預測...")
    history = GASClient.get('history', {'days': 5})
    
    if isinstance(history, dict) and 'error' in history:
        print(f"  ❌ 無法讀取歷史數據: {history['error']}")
        # 嘗試使用本地備份或跳過
        return None
    
    if not history or len(history) < 1:
        print("  ⚠️ 無歷史數據可驗證")
        return None
    
    # 找到最近一筆記錄（前日預測）
    # 注意：history 可能是 list 或有 error
    if isinstance(history, list) and len(history) > 0:
        prev_record = history[-1]  # 最後一筆是最新的
    else:
        print("  ⚠️ 歷史數據格式不正確")
        return None
    
    prev_date = prev_record.get('date', 'Unknown')
    prev_prediction = prev_record.get('prediction', prev_record.get('next_day_bias', 'neutral'))
    prev_close = float(prev_record.get('close', 0))
    
    print(f"  前日日期: {prev_date}")
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
    
    # 預測正確的判斷邏輯
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
    
    # 4. 計算 PnL（假設按配置持有）
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

*前日預測* ({prev_date})
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
    print(json.dumps(validation_record, ensure_ascii=False, indent=2))
    
    return validation_record


# ============================================
# 週末覆盤 (Weekly Review)
# ============================================

def run_weekly_review():
    """週末覆盤 - 每週六 10:00 執行"""
    print("\n" + "="*60)
    print("📊 QQQ 週末覆盤 (Weekly Review)")
    print("="*60)
    
    today = datetime.now()
    
    # 計算本週範圍（週一到週五）
    # 找到本週六，往前推到週一
    days_since_monday = today.weekday()
    if today.weekday() == 5:  # 週六
        days_since_monday = 5
    elif today.weekday() == 6:  # 週日
        days_since_monday = 6
    
    week_start = (today - timedelta(days=days_since_monday)).strftime("%Y-%m-%d")
    week_end = (today - timedelta(days=days_since_monday - 4)).strftime("%Y-%m-%d")
    
    print(f"\n📅 覆盤週期: {week_start} ~ {week_end}")
    
    # 1. 從 GAS 取得本週數據
    print("\n📥 讀取本週數據...")
    history = GASClient.get('history', {'days': 7})
    
    if isinstance(history, dict) and 'error' in history:
        print(f"  ❌ 無法讀取數據: {history['error']}")
        return None
    
    if not history or not isinstance(history, list):
        print("  ⚠️ 無數據可覆盤")
        return None
    
    # 過濾本週數據
    week_data = [r for r in history if week_start <= r.get('date', '') <= week_end]
    
    if len(week_data) < 1:
        print("  ⚠️ 本週無交易數據")
        return None
    
    print(f"  本週交易日: {len(week_data)} 天")
    
    # 2. 計算績效指標
    print("\n📈 計算績效指標...")
    
    # 取得本週價格變化
    qqq_hist = MarketDataFetcher.fetch_historical("QQQ", "1mo")
    if qqq_hist.empty:
        print("  ❌ 無法取得價格歷史")
        return None
    
    # 本週收益率
    week_returns = []
    daily_pnls = []
    correct_predictions = 0
    total_predictions = 0
    
    for i, record in enumerate(week_data):
        try:
            change_pct = float(record.get('change_pct', 0))
            qqq_pct = float(record.get('qqq_pct', 50))
            daily_pnl = change_pct * (qqq_pct / 100)
            daily_pnls.append(daily_pnl)
            week_returns.append(change_pct)
            
            # 檢查預測準確度
            prediction = record.get('prediction', record.get('next_day_bias', ''))
            if prediction:
                total_predictions += 1
                if (prediction == 'bullish' and change_pct > 0) or \
                   (prediction == 'bearish' and change_pct < 0) or \
                   (prediction == 'neutral' and abs(change_pct) < 0.5):
                    correct_predictions += 1
        except:
            continue
    
    # 週報酬
    week_return = sum(daily_pnls)
    
    # 勝率
    win_days = len([p for p in daily_pnls if p > 0])
    lose_days = len([p for p in daily_pnls if p < 0])
    win_rate = (win_days / len(daily_pnls) * 100) if daily_pnls else 0
    
    # 盈虧比
    gains = [p for p in daily_pnls if p > 0]
    losses = [p for p in daily_pnls if p < 0]
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 1
    profit_loss_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
    
    # 最大回撤
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
    
    # 預測準確率
    prediction_accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    # QQQ 本週表現（用於計算 Alpha）
    qqq_week_return = sum(week_returns) if week_returns else 0
    alpha = week_return - qqq_week_return
    
    print(f"  週報酬: {week_return:+.2f}%")
    print(f"  勝率: {win_rate:.1f}% ({win_days}勝 {lose_days}敗)")
    print(f"  盈虧比: {profit_loss_ratio:.2f}")
    print(f"  最大回撤: {max_drawdown:.2f}%")
    print(f"  預測準確率: {prediction_accuracy:.1f}%")
    print(f"  Alpha: {alpha:+.2f}%")
    
    # 3. 計算起始/結束淨值
    starting_nav = Config.INITIAL_CAPITAL
    ending_nav = starting_nav * (1 + week_return / 100)
    
    # 4. 權重變動分析
    weight_changes = {}
    if len(week_data) >= 2:
        first_scores = week_data[0].get('factor_scores', {})
        last_scores = week_data[-1].get('factor_scores', {})
        
        if isinstance(first_scores, str):
            try: first_scores = json.loads(first_scores)
            except: first_scores = {}
        if isinstance(last_scores, str):
            try: last_scores = json.loads(last_scores)
            except: last_scores = {}
        
        for factor in Config.DEFAULT_WEIGHTS.keys():
            first_score = first_scores.get(factor, {}).get('score', 5)
            last_score = last_scores.get(factor, {}).get('score', 5)
            if first_score != last_score:
                weight_changes[factor] = {"from": first_score, "to": last_score, "change": last_score - first_score}
    
    # 5. 生成週報
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
        "weight_changes": weight_changes,
        "review_notes": "",
        "generated_at": today.isoformat()
    }
    
    # 6. 發送到 GAS
    print("\n📤 記錄週報...")
    GASClient.send('weekly_review', weekly_review)
    
    # 7. 發送 Telegram 通知
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
    
    # 8. 儲存
    with open('weekly_review.json', 'w', encoding='utf-8') as f:
        json.dump(weekly_review, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 週末覆盤完成！")
    print(json.dumps(weekly_review, ensure_ascii=False, indent=2))
    
    return weekly_review


# ============================================
# 主程式
# ============================================

def main():
    parser = argparse.ArgumentParser(description='QQQ Decision System v3.0')
    parser.add_argument('--validate', action='store_true', help='執行每日驗證')
    parser.add_argument('--weekly', action='store_true', help='執行週末覆盤')
    parser.add_argument('--all', action='store_true', help='執行所有功能（測試用）')
    args = parser.parse_args()
    
    print(f"\n⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 GAS: {'✓' if Config.GAS_URL else '✗'}")
    print(f"📱 Telegram: {'✓' if Config.TELEGRAM_BOT_TOKEN else '✗'}")
    
    if args.all:
        # 測試模式：執行所有功能
        run_daily_analysis()
        run_daily_validation()
        run_weekly_review()
    elif args.validate:
        run_daily_validation()
    elif args.weekly:
        run_weekly_review()
    else:
        # 預設：每日分析
        run_daily_analysis()


if __name__ == "__main__":
    main()
