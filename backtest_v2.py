#!/usr/bin/env python3
"""
QQQ Backtest & Optimization System
Version: 1.0

功能：
- 歷史數據回測
- 參數網格搜索
- 策略績效評估
- 自動參數更新
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from itertools import product
import yfinance as yf


# ============================================
# 回測引擎
# ============================================

class Backtester:
    """回測引擎"""
    
    def __init__(self, initial_capital: float = 10_000_000):
        self.initial_capital = initial_capital
        self.reset()
    
    def reset(self):
        """重置回測狀態"""
        self.cash = self.initial_capital
        self.shares = 0
        self.nav_history = []
        self.trades = []
        self.daily_returns = []
    
    def run(self, prices: pd.DataFrame, signals: pd.Series) -> Dict:
        """
        執行回測
        
        Args:
            prices: DataFrame with 'Close' column
            signals: Series with allocation percentages (0-100)
        
        Returns:
            績效統計字典
        """
        self.reset()
        
        for i in range(len(prices)):
            date = prices.index[i]
            price = prices['Close'].iloc[i]
            target_pct = signals.iloc[i] / 100
            
            # 計算目標持倉
            total_value = self.cash + self.shares * price
            target_value = total_value * target_pct
            target_shares = int(target_value / price)
            
            # 交易
            if target_shares > self.shares:
                # 買入
                shares_to_buy = target_shares - self.shares
                cost = shares_to_buy * price
                if cost <= self.cash:
                    self.shares += shares_to_buy
                    self.cash -= cost
                    self.trades.append({
                        'date': date,
                        'action': 'BUY',
                        'shares': shares_to_buy,
                        'price': price,
                        'value': cost
                    })
            elif target_shares < self.shares:
                # 賣出
                shares_to_sell = self.shares - target_shares
                proceeds = shares_to_sell * price
                self.shares -= shares_to_sell
                self.cash += proceeds
                self.trades.append({
                    'date': date,
                    'action': 'SELL',
                    'shares': shares_to_sell,
                    'price': price,
                    'value': proceeds
                })
            
            # 記錄 NAV
            nav = self.cash + self.shares * price
            self.nav_history.append({
                'date': date,
                'nav': nav,
                'cash': self.cash,
                'shares': self.shares,
                'price': price
            })
            
            # 記錄每日報酬
            if i > 0:
                prev_nav = self.nav_history[i-1]['nav']
                daily_return = (nav - prev_nav) / prev_nav
                self.daily_returns.append(daily_return)
        
        return self.calculate_metrics(prices)
    
    def calculate_metrics(self, prices: pd.DataFrame) -> Dict:
        """計算績效指標"""
        if not self.nav_history:
            return {}
        
        nav_df = pd.DataFrame(self.nav_history)
        nav_df.set_index('date', inplace=True)
        
        final_nav = nav_df['nav'].iloc[-1]
        total_return = (final_nav - self.initial_capital) / self.initial_capital * 100
        
        # 基準報酬（Buy & Hold）
        benchmark_return = (prices['Close'].iloc[-1] - prices['Close'].iloc[0]) / prices['Close'].iloc[0] * 100
        
        # Alpha
        alpha = total_return - benchmark_return
        
        # 最大回撤
        nav_series = nav_df['nav']
        cummax = nav_series.cummax()
        drawdown = (nav_series - cummax) / cummax * 100
        max_drawdown = drawdown.min()
        
        # Sharpe Ratio (假設無風險利率 = 0)
        if self.daily_returns:
            returns_std = np.std(self.daily_returns)
            sharpe = (np.mean(self.daily_returns) / returns_std * np.sqrt(252)) if returns_std > 0 else 0
        else:
            sharpe = 0
        
        # 勝率
        wins = sum(1 for r in self.daily_returns if r > 0)
        win_rate = wins / len(self.daily_returns) * 100 if self.daily_returns else 0
        
        # 盈虧比
        profits = [r for r in self.daily_returns if r > 0]
        losses = [abs(r) for r in self.daily_returns if r < 0]
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 1
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0
        
        return {
            'total_return': round(total_return, 2),
            'benchmark_return': round(benchmark_return, 2),
            'alpha': round(alpha, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'win_rate': round(win_rate, 1),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'total_trades': len(self.trades),
            'final_nav': round(final_nav, 2),
            'days': len(self.nav_history)
        }


# ============================================
# 參數優化器
# ============================================

class ParameterOptimizer:
    """參數網格搜索優化器"""
    
    def __init__(self, strategy_class, initial_capital: float = 10_000_000):
        self.strategy_class = strategy_class
        self.initial_capital = initial_capital
        self.results = []
    
    def generate_param_grid(self, param_ranges: Dict) -> List[Dict]:
        """生成參數網格"""
        keys = param_ranges.keys()
        values = param_ranges.values()
        
        grid = []
        for combination in product(*values):
            grid.append(dict(zip(keys, combination)))
        
        return grid
    
    def optimize(self, prices: pd.DataFrame, market_data: pd.DataFrame, 
                 param_ranges: Dict, metric: str = 'sharpe_ratio') -> Tuple[Dict, List]:
        """
        執行參數優化
        
        Args:
            prices: 價格數據
            market_data: 市場數據（包含 VIX, 技術指標等）
            param_ranges: 參數範圍，例如 {'days_threshold': [1, 2, 3], 'vix_limit': [30, 35, 40]}
            metric: 優化目標指標
        
        Returns:
            (最佳參數, 所有結果)
        """
        param_grid = self.generate_param_grid(param_ranges)
        
        print(f"\n🔍 開始參數優化")
        print(f"   參數組合數: {len(param_grid)}")
        print(f"   優化指標: {metric}")
        
        self.results = []
        
        for i, params in enumerate(param_grid, 1):
            # 創建策略實例
            strategy = self.strategy_class(config={'capital': self.initial_capital})
            strategy.load_params(params)
            
            # 生成信號
            signals = []
            for idx in range(len(prices)):
                # 構建當日市場數據
                day_data = {
                    'qqq': {'close': prices['Close'].iloc[idx]},
                    'vix': {'value': market_data['VIX'].iloc[idx] if 'VIX' in market_data.columns else 20},
                    'technicals': {}
                }
                
                # 計算評分
                score_result = strategy.score(day_data)
                allocation = strategy.get_allocation(score_result['total_score'])
                signals.append(allocation['qqq_pct'])
            
            # 回測
            backtester = Backtester(self.initial_capital)
            metrics = backtester.run(prices, pd.Series(signals, index=prices.index))
            
            result = {
                'params': params,
                'metrics': metrics,
                'score': metrics.get(metric, 0)
            }
            self.results.append(result)
            
            if i % 10 == 0 or i == len(param_grid):
                print(f"   進度: {i}/{len(param_grid)} ({i/len(param_grid)*100:.1f}%)")
        
        # 找出最佳參數
        self.results.sort(key=lambda x: x['score'], reverse=True)
        best_result = self.results[0]
        
        print(f"\n✅ 優化完成")
        print(f"   最佳 {metric}: {best_result['score']}")
        print(f"   最佳參數: {best_result['params']}")
        
        return best_result['params'], self.results
    
    def save_results(self, filename: str = 'optimization_results.json'):
        """保存優化結果"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_combinations': len(self.results),
            'best_params': self.results[0]['params'] if self.results else {},
            'best_metrics': self.results[0]['metrics'] if self.results else {},
            'all_results': self.results[:20]  # 只保存前20名
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果已保存: {filename}")


# ============================================
# 策略比較器
# ============================================

class StrategyComparator:
    """多策略比較"""
    
    def __init__(self, strategies: Dict[str, Any], initial_capital: float = 10_000_000):
        self.strategies = strategies
        self.initial_capital = initial_capital
        self.comparison_results = {}
    
    def compare(self, prices: pd.DataFrame, market_data: pd.DataFrame) -> Dict:
        """比較多個策略"""
        print(f"\n📊 策略比較")
        print(f"   策略數量: {len(self.strategies)}")
        print(f"   回測天數: {len(prices)}")
        
        for name, strategy in self.strategies.items():
            print(f"\n   測試策略: {name}")
            
            # 生成信號
            signals = []
            for idx in range(len(prices)):
                day_data = {
                    'qqq': {'close': prices['Close'].iloc[idx]},
                    'vix': {'value': market_data['VIX'].iloc[idx] if 'VIX' in market_data.columns else 20},
                    'technicals': {}
                }
                
                score_result = strategy.score(day_data)
                allocation = strategy.get_allocation(score_result['total_score'])
                signals.append(allocation['qqq_pct'])
            
            # 回測
            backtester = Backtester(self.initial_capital)
            metrics = backtester.run(prices, pd.Series(signals, index=prices.index))
            
            self.comparison_results[name] = metrics
        
        return self.comparison_results
    
    def print_comparison(self):
        """打印比較結果"""
        print("\n" + "="*80)
        print("📊 策略比較結果")
        print("="*80)
        
        # 表頭
        print(f"{'策略':<15} {'總報酬':<10} {'Alpha':<10} {'Sharpe':<10} {'勝率':<10} {'最大回撤':<10}")
        print("-"*80)
        
        # 各策略結果
        for name, metrics in self.comparison_results.items():
            print(f"{name:<15} "
                  f"{metrics['total_return']:>8.2f}% "
                  f"{metrics['alpha']:>8.2f}% "
                  f"{metrics['sharpe_ratio']:>8.2f}  "
                  f"{metrics['win_rate']:>8.1f}% "
                  f"{metrics['max_drawdown']:>8.2f}%")
        
        print("="*80)


# ============================================
# 主執行函數
# ============================================

def run_optimization_example():
    """執行優化示例"""
    from qqq_analyzer import MA20Strategy, DefaultStrategy
    
    print("\n" + "="*60)
    print("🚀 QQQ 參數優化系統")
    print("="*60)
    
    # 1. 下載歷史數據
    print("\n📥 下載歷史數據...")
    qqq = yf.download('QQQ', period='6mo', progress=False)
    vix = yf.download('^VIX', period='6mo', progress=False)
    
    market_data = pd.DataFrame({
        'VIX': vix['Close']
    }, index=qqq.index)
    
    print(f"   ✓ 獲取 {len(qqq)} 天數據")
    
    # 2. MA20 策略優化
    print("\n🎯 MA20 策略參數優化")
    
    param_ranges = {
        'days_threshold': [1, 2, 3],
        'vix_limit': [30, 35, 40],
        'position_weight': [0.4, 0.5, 0.6],
        'trend_weight': [0.3, 0.35, 0.4],
        'vix_weight': [0.15, 0.2, 0.25]
    }
    
    optimizer = ParameterOptimizer(MA20Strategy)
    best_params, all_results = optimizer.optimize(
        qqq, 
        market_data, 
        param_ranges, 
        metric='sharpe_ratio'
    )
    
    optimizer.save_results('ma20_optimization.json')
    
    # 3. 策略比較
    print("\n📊 策略比較")
    
    # 使用優化後的參數創建策略
    ma20_optimized = MA20Strategy()
    ma20_optimized.load_params(best_params)
    
    strategies = {
        'MA20 (優化後)': ma20_optimized,
        'MA20 (預設)': MA20Strategy(),
        'Default': DefaultStrategy()
    }
    
    comparator = StrategyComparator(strategies)
    comparator.compare(qqq, market_data)
    comparator.print_comparison()
    
    # 4. 更新參數文件
    print("\n💾 更新參數文件")
    
    try:
        with open('optimized_params.json', 'r', encoding='utf-8') as f:
            params_file = json.load(f)
    except:
        params_file = {'meta': {}, 'ma20': {}, 'default': {}}
    
    params_file['ma20'] = best_params
    params_file['meta']['last_updated'] = datetime.now().isoformat()
    params_file['meta']['optimization_metrics'] = all_results[0]['metrics']
    
    with open('optimized_params.json', 'w', encoding='utf-8') as f:
        json.dump(params_file, f, ensure_ascii=False, indent=2)
    
    print("   ✓ 參數已更新到 optimized_params.json")
    
    print("\n✅ 優化完成！")


if __name__ == "__main__":
    run_optimization_example()
