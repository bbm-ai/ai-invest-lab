#!/usr/bin/env python3
"""
自動化迭代優化腳本
每週自動執行，優化策略參數

使用方式:
    python auto_optimize.py                    # 執行優化
    python auto_optimize.py --dry-run          # 模擬執行，不更新參數
    python auto_optimize.py --strategy ma20    # 只優化特定策略
"""

import json
import argparse
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List

# 假設已經有 qqq_analyzer.py 中的類
from qqq_analyzer import MA20Strategy, DefaultStrategy, GASClient, TelegramNotifier


# ============================================
# 簡化版回測引擎
# ============================================

class SimpleBacktester:
    """簡化版回測引擎"""
    
    @staticmethod
    def backtest(strategy, prices: pd.DataFrame, days: int = 60) -> Dict:
        """
        執行回測
        
        Returns:
            績效指標字典
        """
        if len(prices) < days:
            days = len(prices)
        
        test_prices = prices.tail(days).copy()
        
        nav = 10_000_000
        cash = nav
        shares = 0
        nav_history = [nav]
        
        for i in range(1, len(test_prices)):
            price = test_prices['Close'].iloc[i]
            
            # 簡化的市場數據
            day_data = {
                'qqq': {'close': price},
                'vix': {'value': 20},  # 簡化
                'technicals': {}
            }
            
            # 獲取配置
            score_result = strategy.score(day_data)
            allocation = strategy.get_allocation(score_result['total_score'])
            target_pct = allocation['qqq_pct'] / 100
            
            # 調整持倉
            total_value = cash + shares * price
            target_value = total_value * target_pct
            target_shares = int(target_value / price)
            
            if target_shares > shares:
                shares_to_buy = target_shares - shares
                cost = shares_to_buy * price
                if cost <= cash:
                    shares += shares_to_buy
                    cash -= cost
            elif target_shares < shares:
                shares_to_sell = shares - target_shares
                cash += shares_to_sell * price
                shares -= shares_to_sell
            
            # 記錄 NAV
            nav = cash + shares * price
            nav_history.append(nav)
        
        # 計算指標
        final_return = (nav_history[-1] - nav_history[0]) / nav_history[0] * 100
        benchmark_return = (test_prices['Close'].iloc[-1] - test_prices['Close'].iloc[0]) / test_prices['Close'].iloc[0] * 100
        
        # Sharpe Ratio
        returns = [(nav_history[i] - nav_history[i-1]) / nav_history[i-1] for i in range(1, len(nav_history))]
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
        
        # 最大回撤
        peak = nav_history[0]
        max_dd = 0
        for nav_val in nav_history:
            if nav_val > peak:
                peak = nav_val
            dd = (peak - nav_val) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            'total_return': round(final_return, 2),
            'benchmark_return': round(benchmark_return, 2),
            'alpha': round(final_return - benchmark_return, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_dd, 2)
        }


# ============================================
# 網格搜索優化
# ============================================

def optimize_ma20_params(prices: pd.DataFrame, days: int = 60) -> Dict:
    """優化 MA20 策略參數"""
    
    print("\n🔍 MA20 策略參數優化")
    print(f"   回測天數: {days}")
    
    # 定義參數範圍
    param_grid = {
        'days_threshold': [1, 2, 3],
        'vix_limit': [30, 35, 40],
        'position_weight': [0.4, 0.5, 0.6],
        'trend_weight': [0.25, 0.3, 0.35],
        'vix_weight': [0.15, 0.2, 0.25]
    }
    
    best_sharpe = -999
    best_params = None
    best_metrics = None
    
    total_combinations = (len(param_grid['days_threshold']) * 
                         len(param_grid['vix_limit']) * 
                         len(param_grid['position_weight']) * 
                         len(param_grid['trend_weight']) * 
                         len(param_grid['vix_weight']))
    
    print(f"   參數組合數: {total_combinations}")
    
    count = 0
    for dt in param_grid['days_threshold']:
        for vl in param_grid['vix_limit']:
            for pw in param_grid['position_weight']:
                for tw in param_grid['trend_weight']:
                    for vw in param_grid['vix_weight']:
                        count += 1
                        
                        # 確保權重和為1
                        if abs(pw + tw + vw - 1.0) > 0.01:
                            continue
                        
                        # 創建策略
                        strategy = MA20Strategy()
                        params = {
                            'days_threshold': dt,
                            'vix_limit': vl,
                            'position_weight': pw,
                            'trend_weight': tw,
                            'vix_weight': vw
                        }
                        strategy.load_params(params)
                        
                        # 回測
                        metrics = SimpleBacktester.backtest(strategy, prices, days)
                        
                        # 更新最佳結果
                        if metrics['sharpe_ratio'] > best_sharpe:
                            best_sharpe = metrics['sharpe_ratio']
                            best_params = params
                            best_metrics = metrics
                        
                        if count % 20 == 0:
                            print(f"   進度: {count}/{total_combinations} ({count/total_combinations*100:.1f}%)")
    
    print(f"\n✅ 優化完成")
    print(f"   最佳 Sharpe: {best_sharpe:.2f}")
    print(f"   最佳參數: {best_params}")
    print(f"   績效: Alpha={best_metrics['alpha']:.2f}%, 回撤={best_metrics['max_drawdown']:.2f}%")
    
    return {
        'params': best_params,
        'metrics': best_metrics
    }


def optimize_default_params(prices: pd.DataFrame, days: int = 60) -> Dict:
    """優化 Default 策略參數"""
    
    print("\n🔍 Default 策略權重優化")
    print(f"   回測天數: {days}")
    
    # 定義權重範圍（總和必須為1）
    weight_options = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
    
    best_sharpe = -999
    best_weights = None
    best_metrics = None
    
    count = 0
    total = 0
    
    # 計算總組合數（簡化版，不考慮所有可能）
    for pm in weight_options:
        for vol in weight_options:
            for vix in weight_options:
                for bond in weight_options:
                    mag7 = 1.0 - pm - vol - vix - bond
                    if 0.05 <= mag7 <= 0.40:  # mag7 也要在合理範圍內
                        total += 1
    
    print(f"   權重組合數: {total}")
    
    for pm in weight_options:
        for vol in weight_options:
            for vix in weight_options:
                for bond in weight_options:
                    mag7 = 1.0 - pm - vol - vix - bond
                    
                    # 檢查 mag7 是否在合理範圍
                    if mag7 < 0.05 or mag7 > 0.40:
                        continue
                    
                    count += 1
                    
                    # 創建策略
                    strategy = DefaultStrategy()
                    weights = {
                        'price_momentum': pm,
                        'volume': vol,
                        'vix': vix,
                        'bond': bond,
                        'mag7': mag7
                    }
                    strategy.load_params({'weights': weights})
                    
                    # 回測
                    metrics = SimpleBacktester.backtest(strategy, prices, days)
                    
                    # 更新最佳結果
                    if metrics['sharpe_ratio'] > best_sharpe:
                        best_sharpe = metrics['sharpe_ratio']
                        best_weights = weights
                        best_metrics = metrics
                    
                    if count % 50 == 0:
                        print(f"   進度: {count}/{total} ({count/total*100:.1f}%)")
    
    print(f"\n✅ 優化完成")
    print(f"   最佳 Sharpe: {best_sharpe:.2f}")
    print(f"   最佳權重: {best_weights}")
    print(f"   績效: Alpha={best_metrics['alpha']:.2f}%, 回撤={best_metrics['max_drawdown']:.2f}%")
    
    return {
        'weights': best_weights,
        'metrics': best_metrics
    }


# ============================================
# 主執行函數
# ============================================

def main():
    parser = argparse.ArgumentParser(description='自動化參數優化')
    parser.add_argument('--dry-run', action='store_true', help='模擬執行，不更新參數')
    parser.add_argument('--strategy', type=str, default='all', help='策略名稱 (ma20, default, all)')
    parser.add_argument('--days', type=int, default=60, help='回測天數')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🚀 QQQ 自動化參數優化")
    print("="*60)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 策略: {args.strategy}")
    print(f"📅 回測天數: {args.days}")
    print(f"🔄 模式: {'模擬執行' if args.dry_run else '正式執行'}")
    
    # 下載數據
    print("\n📥 下載歷史數據...")
    qqq = yf.download('QQQ', period='6mo', progress=False)
    print(f"   ✓ 獲取 {len(qqq)} 天數據")
    
    # 載入現有參數
    try:
        with open('optimized_params.json', 'r', encoding='utf-8') as f:
            params_file = json.load(f)
    except:
        params_file = {
            'meta': {},
            'ma20': {},
            'default': {'weights': {}}
        }
    
    optimization_results = {}
    
    # 優化 MA20
    if args.strategy in ['ma20', 'all']:
        ma20_result = optimize_ma20_params(qqq, args.days)
        optimization_results['ma20'] = ma20_result
        
        if not args.dry_run:
            params_file['ma20'] = ma20_result['params']
    
    # 優化 Default
    if args.strategy in ['default', 'all']:
        default_result = optimize_default_params(qqq, args.days)
        optimization_results['default'] = default_result
        
        if not args.dry_run:
            params_file['default']['weights'] = default_result['weights']
    
    # 更新元數據
    params_file['meta']['last_updated'] = datetime.now().isoformat()
    params_file['meta']['optimization_days'] = args.days
    params_file['meta']['optimization_results'] = optimization_results
    
    # 保存參數
    if not args.dry_run:
        with open('optimized_params.json', 'w', encoding='utf-8') as f:
            json.dump(params_file, f, ensure_ascii=False, indent=2)
        print("\n💾 參數已更新到 optimized_params.json")
        
        # 發送通知
        notification = f"""🔄 *參數優化完成*

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 回測天數: {args.days}

"""
        
        if 'ma20' in optimization_results:
            ma20_metrics = optimization_results['ma20']['metrics']
            notification += f"""
*MA20 策略*
Sharpe: {ma20_metrics['sharpe_ratio']:.2f}
Alpha: {ma20_metrics['alpha']:+.2f}%
回撤: {ma20_metrics['max_drawdown']:.2f}%
"""
        
        if 'default' in optimization_results:
            default_metrics = optimization_results['default']['metrics']
            notification += f"""
*Default 策略*
Sharpe: {default_metrics['sharpe_ratio']:.2f}
Alpha: {default_metrics['alpha']:+.2f}%
回撤: {default_metrics['max_drawdown']:.2f}%
"""
        
        TelegramNotifier.send(notification)
        
        # 發送到 Google Sheets（記錄優化歷史）
        optimization_log = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'strategy': args.strategy,
            'days': args.days,
            'results': optimization_results
        }
        GASClient.send('optimization_log', optimization_log)
    
    else:
        print("\n⚠️ 模擬執行模式，未更新參數文件")
    
    print("\n✅ 優化完成！")
    
    # 輸出建議
    print("\n💡 後續步驟：")
    print("   1. 檢查 optimized_params.json 確認新參數")
    print("   2. 執行 python qqq_analyzer.py 測試新參數")
    print("   3. 觀察幾天後再決定是否採用")


if __name__ == "__main__":
    main()
