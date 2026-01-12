#!/usr/bin/env python3
"""
QQQ 策略回測工具
Version: 1.0

功能：
1. 抓取過去 N 週的歷史數據
2. 模擬策略執行
3. 計算績效指標
4. 參數優化

使用方式：
    python backtest.py                      # 回測預設 10 週
    python backtest.py --weeks 20           # 回測 20 週
    python backtest.py --optimize           # 參數優化
    python backtest.py --strategy ma20      # 指定策略
    python backtest.py --compare            # 比較所有策略
"""

import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import itertools

import yfinance as yf
import pandas as pd
import numpy as np


# ============================================
# 數據類別
# ============================================

@dataclass
class DailyResult:
    """每日回測結果"""
    date: str
    close: float
    change_pct: float
    ma20: float
    above_ma20: bool
    days_above: int
    days_below: int
    vix: float
    score: float
    signal: str
    regime: str
    qqq_pct: int
    pnl_pct: float
    cumulative_pnl: float


@dataclass
class BacktestResult:
    """回測總結果"""
    strategy: str
    params: Dict
    total_return: float
    qqq_return: float
    alpha: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_loss_ratio: float
    total_trades: int
    accuracy: float
    daily_results: List[DailyResult]


# ============================================
# 數據抓取
# ============================================

class DataFetcher:
    """歷史數據抓取"""
    
    @staticmethod
    def fetch_historical(ticker: str, weeks: int) -> pd.DataFrame:
        """抓取歷史數據"""
        period = f"{weeks * 7 + 30}d"  # 多抓一些計算 MA
        try:
            df = yf.Ticker(ticker).history(period=period)
            return df
        except Exception as e:
            print(f"❌ 抓取 {ticker} 失敗: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def prepare_data(weeks: int) -> pd.DataFrame:
        """準備回測數據"""
        print(f"📊 抓取過去 {weeks} 週數據...")
        
        # 抓取 QQQ
        qqq = DataFetcher.fetch_historical("QQQ", weeks)
        if qqq.empty:
            return pd.DataFrame()
        
        # 抓取 VIX
        vix = DataFetcher.fetch_historical("^VIX", weeks)
        
        # 抓取 10Y
        tnx = DataFetcher.fetch_historical("^TNX", weeks)
        
        # 合併數據
        df = pd.DataFrame()
        df['close'] = qqq['Close']
        df['high'] = qqq['High']
        df['low'] = qqq['Low']
        df['volume'] = qqq['Volume']
        df['change_pct'] = qqq['Close'].pct_change() * 100
        
        # 計算技術指標
        df['ma5'] = qqq['Close'].rolling(5).mean()
        df['ma20'] = qqq['Close'].rolling(20).mean()
        df['ma60'] = qqq['Close'].rolling(60).mean()
        
        # RSI
        delta = qqq['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 成交量比
        df['volume_ratio'] = qqq['Volume'] / qqq['Volume'].rolling(20).mean()
        
        # MA20 相對位置
        df['ma20_diff_pct'] = (df['close'] - df['ma20']) / df['ma20'] * 100
        df['above_ma20'] = df['close'] > df['ma20']
        
        # 計算連續站上/跌破天數
        df['days_above_ma20'] = 0
        df['days_below_ma20'] = 0
        
        days_above = 0
        days_below = 0
        for i in range(len(df)):
            if pd.isna(df['above_ma20'].iloc[i]):
                continue
            if df['above_ma20'].iloc[i]:
                days_above += 1
                days_below = 0
            else:
                days_below += 1
                days_above = 0
            df.iloc[i, df.columns.get_loc('days_above_ma20')] = days_above
            df.iloc[i, df.columns.get_loc('days_below_ma20')] = days_below
        
        # 加入 VIX
        if not vix.empty:
            df['vix'] = vix['Close'].reindex(df.index, method='ffill')
            df['vix_change'] = vix['Close'].pct_change().reindex(df.index, method='ffill') * 100
        else:
            df['vix'] = 20
            df['vix_change'] = 0
        
        # 加入 10Y
        if not tnx.empty:
            df['us10y'] = tnx['Close'].reindex(df.index, method='ffill')
            df['us10y_change'] = tnx['Close'].diff().reindex(df.index, method='ffill')
        else:
            df['us10y'] = 4.5
            df['us10y_change'] = 0
        
        # 移除 NaN
        df = df.dropna()
        
        # 只保留最近 N 週
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        df = df[df.index >= cutoff_date]
        
        print(f"  ✓ 共 {len(df)} 個交易日")
        print(f"  ✓ 期間: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
        
        return df


# ============================================
# 策略類別
# ============================================

class BaseStrategy:
    """策略基類"""
    name = "base"
    
    def __init__(self, params: Dict = None):
        self.params = params or {}
    
    def score(self, row: pd.Series) -> Tuple[float, str, Dict]:
        """計算評分，返回 (總分, 訊號, 因子詳情)"""
        raise NotImplementedError
    
    def get_allocation(self, score: float) -> int:
        """根據評分返回 QQQ 配置比例"""
        raise NotImplementedError


class DefaultStrategy(BaseStrategy):
    """預設多因子策略"""
    name = "default"
    
    def __init__(self, params: Dict = None):
        super().__init__(params)
        self.weights = params.get('weights', {
            "price_momentum": 0.30,
            "volume": 0.20,
            "vix": 0.20,
            "bond": 0.15,
            "mag7": 0.15
        })
    
    def score(self, row: pd.Series) -> Tuple[float, str, Dict]:
        change = row['change_pct']
        vol_ratio = row.get('volume_ratio', 1.0)
        vix = row.get('vix', 20)
        bond_change = row.get('us10y_change', 0)
        
        factors = {}
        
        # Price Momentum
        if change > 2.0: factors['price_momentum'] = 9
        elif change > 1.0: factors['price_momentum'] = 8
        elif change > 0.5: factors['price_momentum'] = 7
        elif change > 0: factors['price_momentum'] = 6
        elif change > -0.5: factors['price_momentum'] = 5
        elif change > -1.0: factors['price_momentum'] = 4
        elif change > -2.0: factors['price_momentum'] = 3
        else: factors['price_momentum'] = 2
        
        # Volume
        if vol_ratio > 1.5 and change > 0: factors['volume'] = 9
        elif vol_ratio > 1.2 and change > 0: factors['volume'] = 8
        elif vol_ratio < 0.7 and change > 0: factors['volume'] = 4
        elif vol_ratio > 1.5 and change < 0: factors['volume'] = 2
        elif vol_ratio > 1.2 and change < 0: factors['volume'] = 3
        elif vol_ratio < 0.7 and change < 0: factors['volume'] = 6
        else: factors['volume'] = 5
        
        # VIX
        if vix < 12: factors['vix'] = 9
        elif vix < 15: factors['vix'] = 8
        elif vix < 18: factors['vix'] = 7
        elif vix < 22: factors['vix'] = 5
        elif vix < 28: factors['vix'] = 4
        elif vix < 35: factors['vix'] = 3
        else: factors['vix'] = 1
        
        # Bond
        if bond_change > 0.08: factors['bond'] = 2
        elif bond_change > 0.05: factors['bond'] = 3
        elif bond_change > 0.02: factors['bond'] = 4
        elif bond_change < -0.08: factors['bond'] = 8
        elif bond_change < -0.05: factors['bond'] = 7
        elif bond_change < -0.02: factors['bond'] = 6
        else: factors['bond'] = 5
        
        # Mag7
        if change > 1.5: factors['mag7'] = 8
        elif change > 0.5: factors['mag7'] = 7
        elif change > 0: factors['mag7'] = 6
        elif change > -0.5: factors['mag7'] = 5
        elif change > -1.5: factors['mag7'] = 4
        else: factors['mag7'] = 3
        
        # 加權總分
        total = sum(factors[f] * self.weights[f] for f in self.weights)
        total = round(total, 1)
        
        # 訊號
        if total >= 6.5:
            signal = 'BUY'
        elif total <= 3.5:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return total, signal, factors
    
    def get_allocation(self, score: float) -> int:
        if score <= 2: return 10
        elif score <= 3: return 20
        elif score <= 4: return 35
        elif score <= 5: return 50
        elif score <= 6: return 60
        elif score <= 7: return 75
        elif score <= 8: return 85
        else: return 90


class MA20Strategy(BaseStrategy):
    """MA20 策略"""
    name = "ma20"
    
    def __init__(self, params: Dict = None):
        super().__init__(params)
        # 可調參數
        self.days_threshold = params.get('days_threshold', 2)  # 連續天數閾值
        self.vix_limit = params.get('vix_limit', 35)  # VIX 上限
        self.position_weight = params.get('position_weight', 0.5)
        self.trend_weight = params.get('trend_weight', 0.3)
        self.vix_weight = params.get('vix_weight', 0.2)
    
    def score(self, row: pd.Series) -> Tuple[float, str, Dict]:
        ma20_diff = row.get('ma20_diff_pct', 0)
        days_above = row.get('days_above_ma20', 0)
        days_below = row.get('days_below_ma20', 0)
        vix = row.get('vix', 20)
        
        factors = {}
        
        # MA20 Position
        if ma20_diff > 5: factors['ma20_position'] = 9
        elif ma20_diff > 3: factors['ma20_position'] = 8
        elif ma20_diff > 1: factors['ma20_position'] = 7
        elif ma20_diff > 0: factors['ma20_position'] = 6
        elif ma20_diff > -1: factors['ma20_position'] = 5
        elif ma20_diff > -3: factors['ma20_position'] = 4
        elif ma20_diff > -5: factors['ma20_position'] = 3
        else: factors['ma20_position'] = 2
        
        # MA20 Trend (連續天數)
        if days_above >= self.days_threshold + 1:
            factors['ma20_trend'] = 9
            signal = 'BUY'
        elif days_above >= self.days_threshold:
            factors['ma20_trend'] = 8
            signal = 'BUY'
        elif days_above == 1:
            factors['ma20_trend'] = 6
            signal = 'WATCH'
        elif days_below == 1:
            factors['ma20_trend'] = 5
            signal = 'WATCH'
        elif days_below >= self.days_threshold:
            factors['ma20_trend'] = 3
            signal = 'SELL'
        elif days_below >= self.days_threshold + 1:
            factors['ma20_trend'] = 2
            signal = 'SELL'
        else:
            factors['ma20_trend'] = 5
            signal = 'HOLD'
        
        # VIX Filter
        if vix < 15: factors['vix_filter'] = 8
        elif vix < 20: factors['vix_filter'] = 7
        elif vix < 25: factors['vix_filter'] = 5
        elif vix < 30: factors['vix_filter'] = 3
        else: factors['vix_filter'] = 2
        
        # 加權總分
        total = (
            factors['ma20_position'] * self.position_weight +
            factors['ma20_trend'] * self.trend_weight +
            factors['vix_filter'] * self.vix_weight
        )
        total = round(total, 1)
        
        # VIX 過高時覆蓋訊號
        if vix > self.vix_limit:
            signal = 'RISK_OFF'
            total = min(total, 4)
        
        return total, signal, factors
    
    def get_allocation(self, score: float) -> int:
        if score <= 2: return 0
        elif score <= 3: return 10
        elif score <= 4: return 25
        elif score <= 5: return 40
        elif score <= 6: return 55
        elif score <= 7: return 70
        elif score <= 8: return 85
        else: return 95


# ============================================
# 回測引擎
# ============================================

class BacktestEngine:
    """回測引擎"""
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10_000_000):
        self.data = data
        self.initial_capital = initial_capital
    
    def run(self, strategy: BaseStrategy) -> BacktestResult:
        """執行回測"""
        results = []
        cumulative_pnl = 0
        prev_allocation = 50  # 初始配置
        
        correct_predictions = 0
        total_predictions = 0
        
        for i in range(1, len(self.data)):
            row = self.data.iloc[i]
            prev_row = self.data.iloc[i-1]
            
            # 使用前一天數據計算評分（模擬真實情況）
            score, signal, factors = strategy.score(prev_row)
            allocation = strategy.get_allocation(score)
            
            # 今天的實際漲跌
            change = row['change_pct']
            
            # 計算 PnL（用前一天的配置）
            pnl = change * (prev_allocation / 100)
            cumulative_pnl += pnl
            
            # 驗證預測
            if signal in ['BUY', 'SELL']:
                total_predictions += 1
                if (signal == 'BUY' and change > 0) or (signal == 'SELL' and change < 0):
                    correct_predictions += 1
            
            # 記錄結果
            result = DailyResult(
                date=row.name.strftime('%Y-%m-%d'),
                close=row['close'],
                change_pct=change,
                ma20=row.get('ma20', 0),
                above_ma20=row.get('above_ma20', False),
                days_above=row.get('days_above_ma20', 0),
                days_below=row.get('days_below_ma20', 0),
                vix=row.get('vix', 20),
                score=score,
                signal=signal,
                regime='offense' if score >= 6.5 else 'defense' if score <= 3.5 else 'neutral',
                qqq_pct=allocation,
                pnl_pct=pnl,
                cumulative_pnl=cumulative_pnl
            )
            results.append(result)
            
            # 更新配置供下一天使用
            prev_allocation = allocation
        
        # 計算績效指標
        total_return = cumulative_pnl
        qqq_return = (self.data['close'].iloc[-1] / self.data['close'].iloc[0] - 1) * 100
        alpha = total_return - qqq_return
        
        # 勝率
        pnls = [r.pnl_pct for r in results]
        win_days = len([p for p in pnls if p > 0])
        lose_days = len([p for p in pnls if p < 0])
        win_rate = win_days / len(pnls) * 100 if pnls else 0
        
        # 盈虧比
        gains = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 1
        pl_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
        
        # 最大回撤
        cumulative = [r.cumulative_pnl for r in results]
        peak = cumulative[0]
        max_dd = 0
        for c in cumulative:
            if c > peak:
                peak = c
            dd = peak - c
            if dd > max_dd:
                max_dd = dd
        
        # 夏普比率 (年化)
        if len(pnls) > 1:
            mean_return = np.mean(pnls) * 252
            std_return = np.std(pnls) * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        # 準確率
        accuracy = correct_predictions / total_predictions * 100 if total_predictions > 0 else 0
        
        return BacktestResult(
            strategy=strategy.name,
            params=strategy.params,
            total_return=round(total_return, 2),
            qqq_return=round(qqq_return, 2),
            alpha=round(alpha, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_dd, 2),
            win_rate=round(win_rate, 1),
            profit_loss_ratio=round(pl_ratio, 2),
            total_trades=total_predictions,
            accuracy=round(accuracy, 1),
            daily_results=results
        )


# ============================================
# 參數優化
# ============================================

class ParameterOptimizer:
    """參數優化器"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.engine = BacktestEngine(data)
    
    def optimize_ma20(self) -> List[Dict]:
        """優化 MA20 策略參數"""
        print("\n🔧 優化 MA20 策略參數...")
        
        # 參數搜索空間
        days_thresholds = [1, 2, 3]
        vix_limits = [30, 35, 40]
        position_weights = [0.4, 0.5, 0.6]
        trend_weights = [0.2, 0.3, 0.4]
        
        results = []
        total_combinations = len(days_thresholds) * len(vix_limits) * len(position_weights) * len(trend_weights)
        
        print(f"  測試 {total_combinations} 種參數組合...")
        
        for days, vix_lim, pos_w, trend_w in itertools.product(
            days_thresholds, vix_limits, position_weights, trend_weights
        ):
            vix_w = 1 - pos_w - trend_w
            if vix_w < 0.1 or vix_w > 0.4:
                continue
            
            params = {
                'days_threshold': days,
                'vix_limit': vix_lim,
                'position_weight': pos_w,
                'trend_weight': trend_w,
                'vix_weight': round(vix_w, 2)
            }
            
            strategy = MA20Strategy(params)
            result = self.engine.run(strategy)
            
            results.append({
                'params': params,
                'total_return': result.total_return,
                'alpha': result.alpha,
                'sharpe': result.sharpe_ratio,
                'max_dd': result.max_drawdown,
                'win_rate': result.win_rate,
                'accuracy': result.accuracy,
                # 綜合評分 (可調整權重)
                'composite_score': (
                    result.alpha * 0.3 +
                    result.sharpe_ratio * 0.3 +
                    result.win_rate * 0.2 +
                    result.accuracy * 0.2 -
                    result.max_drawdown * 0.1
                )
            })
        
        # 按綜合評分排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return results
    
    def optimize_default(self) -> List[Dict]:
        """優化 Default 策略權重"""
        print("\n🔧 優化 Default 策略權重...")
        
        # 權重搜索空間 (總和必須為 1)
        weight_sets = [
            {"price_momentum": 0.30, "volume": 0.20, "vix": 0.20, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.35, "volume": 0.15, "vix": 0.25, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.25, "volume": 0.25, "vix": 0.25, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.40, "volume": 0.15, "vix": 0.20, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.30, "volume": 0.15, "vix": 0.30, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.25, "volume": 0.20, "vix": 0.25, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.35, "volume": 0.20, "vix": 0.15, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.30, "volume": 0.10, "vix": 0.30, "bond": 0.15, "mag7": 0.15},
        ]
        
        results = []
        
        for weights in weight_sets:
            params = {'weights': weights}
            strategy = DefaultStrategy(params)
            result = self.engine.run(strategy)
            
            results.append({
                'params': params,
                'total_return': result.total_return,
                'alpha': result.alpha,
                'sharpe': result.sharpe_ratio,
                'max_dd': result.max_drawdown,
                'win_rate': result.win_rate,
                'accuracy': result.accuracy,
                'composite_score': (
                    result.alpha * 0.3 +
                    result.sharpe_ratio * 0.3 +
                    result.win_rate * 0.2 +
                    result.accuracy * 0.2 -
                    result.max_drawdown * 0.1
                )
            })
        
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        return results


# ============================================
# 報表生成
# ============================================

def print_backtest_result(result: BacktestResult):
    """列印回測結果"""
    print(f"\n{'='*60}")
    print(f"📊 {result.strategy.upper()} 策略回測結果")
    print(f"{'='*60}")
    
    print(f"\n📈 績效指標:")
    print(f"  • 總報酬: {result.total_return:+.2f}%")
    print(f"  • QQQ 報酬: {result.qqq_return:+.2f}%")
    print(f"  • Alpha: {result.alpha:+.2f}%")
    print(f"  • 夏普比率: {result.sharpe_ratio:.2f}")
    print(f"  • 最大回撤: {result.max_drawdown:.2f}%")
    
    print(f"\n📋 交易統計:")
    print(f"  • 勝率: {result.win_rate:.1f}%")
    print(f"  • 盈虧比: {result.profit_loss_ratio:.2f}")
    print(f"  • 交易次數: {result.total_trades}")
    print(f"  • 預測準確率: {result.accuracy:.1f}%")


def print_optimization_results(results: List[Dict], top_n: int = 5):
    """列印優化結果"""
    print(f"\n🏆 Top {top_n} 參數組合:")
    print("-" * 80)
    
    for i, r in enumerate(results[:top_n], 1):
        print(f"\n#{i}")
        print(f"  參數: {json.dumps(r['params'], indent=2)}")
        print(f"  報酬: {r['total_return']:+.2f}% | Alpha: {r['alpha']:+.2f}% | 夏普: {r['sharpe']:.2f}")
        print(f"  勝率: {r['win_rate']:.1f}% | 準確率: {r['accuracy']:.1f}% | 最大回撤: {r['max_dd']:.2f}%")
        print(f"  綜合評分: {r['composite_score']:.2f}")


def export_results(result: BacktestResult, filename: str):
    """匯出結果到 JSON"""
    data = {
        'strategy': result.strategy,
        'params': result.params,
        'summary': {
            'total_return': result.total_return,
            'qqq_return': result.qqq_return,
            'alpha': result.alpha,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'win_rate': result.win_rate,
            'profit_loss_ratio': result.profit_loss_ratio,
            'accuracy': result.accuracy
        },
        'daily_results': [
            {
                'date': r.date,
                'close': r.close,
                'change_pct': r.change_pct,
                'ma20': r.ma20,
                'days_above': r.days_above,
                'days_below': r.days_below,
                'vix': r.vix,
                'score': r.score,
                'signal': r.signal,
                'qqq_pct': r.qqq_pct,
                'pnl_pct': r.pnl_pct,
                'cumulative_pnl': r.cumulative_pnl
            }
            for r in result.daily_results
        ]
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果已匯出: {filename}")


# ============================================
# 主程式
# ============================================

def main():
    parser = argparse.ArgumentParser(description='QQQ 策略回測工具')
    parser.add_argument('--weeks', type=int, default=10, help='回測週數 (預設: 10)')
    parser.add_argument('--strategy', type=str, default='all', help='策略 (default, ma20, all)')
    parser.add_argument('--optimize', action='store_true', help='執行參數優化')
    parser.add_argument('--compare', action='store_true', help='比較所有策略')
    parser.add_argument('--export', action='store_true', help='匯出結果到 JSON')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔬 QQQ 策略回測工具")
    print("="*60)
    
    # 抓取數據
    data = DataFetcher.prepare_data(args.weeks)
    if data.empty:
        print("❌ 無法取得數據")
        return
    
    engine = BacktestEngine(data)
    
    # 參數優化
    if args.optimize:
        optimizer = ParameterOptimizer(data)
        
        # 優化 MA20
        ma20_results = optimizer.optimize_ma20()
        print_optimization_results(ma20_results, top_n=5)
        
        # 優化 Default
        default_results = optimizer.optimize_default()
        print_optimization_results(default_results, top_n=3)
        
        # 匯出最佳參數
        best_params = {
            'ma20': ma20_results[0]['params'] if ma20_results else {},
            'default': default_results[0]['params'] if default_results else {}
        }
        
        with open('optimized_params.json', 'w', encoding='utf-8') as f:
            json.dump(best_params, f, ensure_ascii=False, indent=2)
        
        print("\n💾 最佳參數已儲存: optimized_params.json")
        return
    
    # 比較策略
    if args.compare or args.strategy == 'all':
        print("\n📊 策略比較:")
        
        strategies = [
            ('default', DefaultStrategy()),
            ('ma20', MA20Strategy()),
            ('ma20_opt', MA20Strategy({'days_threshold': 2, 'vix_limit': 35})),
        ]
        
        comparison = []
        for name, strategy in strategies:
            result = engine.run(strategy)
            comparison.append(result)
            print_backtest_result(result)
        
        # 比較表
        print(f"\n{'='*60}")
        print("📋 策略比較總表")
        print(f"{'='*60}")
        print(f"{'策略':<12} {'報酬':>10} {'Alpha':>10} {'夏普':>8} {'勝率':>8} {'回撤':>8}")
        print("-" * 60)
        for r in comparison:
            print(f"{r.strategy:<12} {r.total_return:>+9.2f}% {r.alpha:>+9.2f}% {r.sharpe_ratio:>7.2f} {r.win_rate:>7.1f}% {r.max_drawdown:>7.2f}%")
        
        return
    
    # 單一策略回測
    if args.strategy == 'ma20':
        strategy = MA20Strategy()
    else:
        strategy = DefaultStrategy()
    
    result = engine.run(strategy)
    print_backtest_result(result)
    
    # 顯示最近交易
    print(f"\n📅 最近 10 筆交易:")
    print(f"{'日期':<12} {'收盤':>10} {'漲跌':>8} {'MA20':>10} {'訊號':<8} {'配置':>6} {'PnL':>8}")
    print("-" * 70)
    for r in result.daily_results[-10:]:
        print(f"{r.date:<12} ${r.close:>8.2f} {r.change_pct:>+7.2f}% ${r.ma20:>8.2f} {r.signal:<8} {r.qqq_pct:>5}% {r.pnl_pct:>+7.2f}%")
    
    # 匯出
    if args.export:
        export_results(result, f'backtest_{args.strategy}.json')


if __name__ == "__main__":
    main()
