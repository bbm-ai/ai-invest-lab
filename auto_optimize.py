#!/usr/bin/env python3
"""
自動化迭代優化腳本
每週自動執行，優化策略參數

使用方式:
    python auto_optimize.py                    # 執行優化
    python auto_optimize.py --dry-run          # 模擬執行，不更新參數
    python auto_optimize.py --strategy ma20    # 只優化特定策略
    python auto_optimize.py --days 60          # 自定義回測天數
"""

import json
import argparse
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict

# 假設已經有 qqq_analyzer.py 中的類
try:
    from qqq_analyzer import MA20Strategy, DefaultStrategy, GASClient, TelegramNotifier
except ImportError:
    print("⚠️ 警告：無法載入 qqq_analyzer 模組，將使用模擬模式")
    MA20Strategy = None
    DefaultStrategy = None
    GASClient = None
    TelegramNotifier = None


# ============================================
# 簡化版回測引擎（修正版）
# ============================================

class SimpleBacktester:
    """簡化版回測引擎 - 修正 Pandas 類型問題"""
    
    @staticmethod
    def backtest(strategy, prices: pd.DataFrame, days: int = 60) -> Dict:
        """
        執行回測
        
        Args:
            strategy: 策略實例
            prices: 價格數據 DataFrame
            days: 回測天數
            
        Returns:
            績效指標字典
        """
        if len(prices) < days:
            days = len(prices)
        
        # 重置索引確保連續
        test_prices = prices.tail(days).copy().reset_index(drop=True)
        
        nav = 10_000_000
        cash = float(nav)
        shares = 0
        nav_history = [float(nav)]
        
        for i in range(1, len(test_prices)):
            # 🔧 修正：明確轉換為 float
            price = float(test_prices.loc[i, 'Close'])
            
            # 簡化的市場數據
            day_data = {
                'qqq': {'close': price},
                'vix': {'value': 20.0},
                'technicals': {}
            }
            
            try:
                # 獲取配置
                score_result = strategy.score(day_data)
                allocation = strategy.get_allocation(score_result['total_score'])
                target_pct = float(allocation['qqq_pct']) / 100.0
                
                # 調整持倉
                total_value = cash + shares * price
                target_value = total_value * target_pct
                target_shares = int(target_value / price) if price > 0 else 0
                
                if target_shares > shares:
                    # 買入
                    shares_to_buy = target_shares - shares
                    cost = float(shares_to_buy * price)
                    
                    if cost <= cash:  # 🔧 修正：現在是 float 比較，不會有問題
                        shares += shares_to_buy
                        cash -= cost
                        
                elif target_shares < shares:
                    # 賣出
                    shares_to_sell = shares - target_shares
                    proceeds = float(shares_to_sell * price)
                    cash += proceeds
                    shares -= shares_to_sell
                
                # 記錄 NAV
                nav = float(cash + shares * price)
                nav_history.append(nav)
                
            except Exception as e:
                print(f"⚠️ 第 {i} 天回測錯誤: {e}")
                # 保持上一個 NAV
                nav_history.append(nav_history[-1])
        
        # 計算指標
        try:
            final_return = (nav_history[-1] - nav_history[0]) / nav_history[0] * 100
            
            # 基準報酬（Buy & Hold）
            first_price = float(test_prices.loc[0, 'Close'])
            last_price = float(test_prices.loc[len(test_prices)-1, 'Close'])
            benchmark_return = (last_price - first_price) / first_price * 100
            
            # Sharpe Ratio
            if len(nav_history) > 1:
                returns = [(nav_history[i] - nav_history[i-1]) / nav_history[i-1] 
                          for i in range(1, len(nav_history))]
                
                if len(returns) > 1:
                    returns_mean = np.mean(returns)
                    returns_std = np.std(returns)
                    sharpe = (returns_mean / returns_std * np.sqrt(252)) if returns_std > 0 else 0
                else:
                    sharpe = 0
            else:
                sharpe = 0
            
            # 最大回撤
            peak = nav_history[0]
            max_dd = 0.0
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
                'max_drawdown': round(max_dd, 2),
                'final_nav': round(nav_history[-1], 2),
                'days': len(nav_history) - 1
            }
            
        except Exception as e:
            print(f"❌ 計算指標錯誤: {e}")
            return {
                'total_return': 0.0,
                'benchmark_return': 0.0,
                'alpha': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'final_nav': nav_history[-1] if nav_history else nav,
                'days': len(nav_history) - 1
            }


# ============================================
# 網格搜索優化
# ============================================

def optimize_ma20_params(prices: pd.DataFrame, days: int = 60) -> Dict:
    """優化 MA20 策略參數"""
    
    if MA20Strategy is None:
        print("❌ 無法載入 MA20Strategy")
        return {'params': {}, 'metrics': {}}
    
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
    valid_count = 0
    
    for dt in param_grid['days_threshold']:
        for vl in param_grid['vix_limit']:
            for pw in param_grid['position_weight']:
                for tw in param_grid['trend_weight']:
                    for vw in param_grid['vix_weight']:
                        count += 1
                        
                        # 確保權重和為1（容許小誤差）
                        weight_sum = pw + tw + vw
                        if abs(weight_sum - 1.0) > 0.01:
                            continue
                        
                        valid_count += 1
                        
                        try:
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
                            
                            if valid_count % 20 == 0:
                                print(f"   進度: {valid_count} 組有效參數已測試 (總計 {count}/{total_combinations})")
                        
                        except Exception as e:
                            print(f"   ⚠️ 參數組合 {count} 測試失敗: {e}")
                            continue
    
    print(f"\n✅ 優化完成")
    print(f"   有效組合數: {valid_count}")
    print(f"   最佳 Sharpe: {best_sharpe:.2f}")
    print(f"   最佳參數: {best_params}")
    print(f"   績效: Alpha={best_metrics['alpha']:.2f}%, 回撤={best_metrics['max_drawdown']:.2f}%")
    
    return {
        'params': best_params if best_params else {},
        'metrics': best_metrics if best_metrics else {}
    }


def optimize_default_params(prices: pd.DataFrame, days: int = 60) -> Dict:
    """優化 Default 策略參數"""
    
    if DefaultStrategy is None:
        print("❌ 無法載入 DefaultStrategy")
        return {'weights': {}, 'metrics': {}}
    
    print("\n🔍 Default 策略權重優化")
    print(f"   回測天數: {days}")
    
    # 定義權重範圍
    weight_options = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
    
    best_sharpe = -999
    best_weights = None
    best_metrics = None
    
    count = 0
    valid_count = 0
    
    for pm in weight_options:
        for vol in weight_options:
            for vix in weight_options:
                for bond in weight_options:
                    mag7 = 1.0 - pm - vol - vix - bond
                    
                    # 檢查 mag7 是否在合理範圍
                    if mag7 < 0.05 or mag7 > 0.40:
                        continue
                    
                    count += 1
                    
                    try:
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
                        
                        valid_count += 1
                        
                        if valid_count % 50 == 0:
                            print(f"   進度: {valid_count} 組權重已測試")
                    
                    except Exception as e:
                        print(f"   ⚠️ 權重組合 {count} 測試失敗: {e}")
                        continue
    
    print(f"\n✅ 優化完成")
    print(f"   測試組合數: {valid_count}")
    print(f"   最佳 Sharpe: {best_sharpe:.2f}")
    print(f"   最佳權重: {best_weights}")
    print(f"   績效: Alpha={best_metrics['alpha']:.2f}%, 回撤={best_metrics['max_drawdown']:.2f}%")
    
    return {
        'weights': best_weights if best_weights else {},
        'metrics': best_metrics if best_metrics else {}
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
    try:
        qqq = yf.download('QQQ', period='6mo', progress=False)
        print(f"   ✓ 獲取 {len(qqq)} 天數據")
    except Exception as e:
        print(f"❌ 下載數據失敗: {e}")
        return
    
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
        
        if not args.dry_run and ma20_result['params']:
            params_file['ma20'] = ma20_result['params']
    
    # 優化 Default
    if args.strategy in ['default', 'all']:
        default_result = optimize_default_params(qqq, args.days)
        optimization_results['default'] = default_result
        
        if not args.dry_run and default_result['weights']:
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
        if TelegramNotifier:
            notification = f"""🔄 *參數優化完成*

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 回測天數: {args.days}

"""
            
            if 'ma20' in optimization_results and optimization_results['ma20']['metrics']:
                ma20_metrics = optimization_results['ma20']['metrics']
                notification += f"""
*MA20 策略*
Sharpe: {ma20_metrics.get('sharpe_ratio', 0):.2f}
Alpha: {ma20_metrics.get('alpha', 0):+.2f}%
回撤: {ma20_metrics.get('max_drawdown', 0):.2f}%
"""
            
            if 'default' in optimization_results and optimization_results['default']['metrics']:
                default_metrics = optimization_results['default']['metrics']
                notification += f"""
*Default 策略*
Sharpe: {default_metrics.get('sharpe_ratio', 0):.2f}
Alpha: {default_metrics.get('alpha', 0):+.2f}%
回撤: {default_metrics.get('max_drawdown', 0):.2f}%
"""
            
            try:
                TelegramNotifier.send(notification)
            except:
                print("⚠️ Telegram 通知發送失敗")
        
        # 發送到 Google Sheets
        if GASClient:
            optimization_log = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'strategy': args.strategy,
                'days': args.days,
                'results': optimization_results
            }
            try:
                GASClient.send('optimization_log', optimization_log)
            except:
                print("⚠️ Google Sheets 記錄失敗")
    
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
