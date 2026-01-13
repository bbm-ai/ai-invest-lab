#!/usr/bin/env python3
"""
QQQ 策略回測工具
Version: 2.0

功能：
1. 抓取過去 N 週的歷史數據
2. 模擬策略執行
3. 計算績效指標
4. 參數優化並自動更新 optimized_params.json

使用方式：
    python backtest.py                      # 回測預設 10 週
    python backtest.py --weeks 20           # 回測 20 週
    python backtest.py --optimize           # 參數優化 (自動更新 JSON)
    python backtest.py --strategy ma20      # 指定策略
    python backtest.py --compare            # 比較所有策略
"""

import json
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import itertools

import yfinance as yf
import pandas as pd
import numpy as np


# ============================================
# 設定
# ============================================

PARAMS_FILE = 'optimized_params.json'  # 參數檔案路徑


# ============================================
# 參數管理
# ============================================

class ParamsManager:
    """參數檔案管理器"""
    
    @staticmethod
    def load() -> Dict:
        """讀取參數檔案"""
        if os.path.exists(PARAMS_FILE):
            try:
                with open(PARAMS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 預設參數
        return {
            "meta": {
                "last_updated": None,
                "last_backtest_weeks": None,
                "version": "2.0"
            },
            "ma20": {
                "days_threshold": 2,
                "vix_limit": 35,
                "position_weight": 0.50,
                "trend_weight": 0.30,
                "vix_weight": 0.20,
                "backtest_result": {}
            },
            "default": {
                "weights": {
                    "price_momentum": 0.30,
                    "volume": 0.20,
                    "vix": 0.20,
                    "bond": 0.15,
                    "mag7": 0.15
                },
                "backtest_result": {}
            }
        }
    
    @staticmethod
    def save(params: Dict):
        """儲存參數檔案"""
        params['meta']['last_updated'] = datetime.now().isoformat()
        
        with open(PARAMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(params, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 參數已更新: {PARAMS_FILE}")
    
    @staticmethod
    def update_strategy(strategy_name: str, new_params: Dict, backtest_result: Dict, weeks: int):
        """更新特定策略的參數"""
        params = ParamsManager.load()
        
        # 更新策略參數
        if strategy_name not in params:
            params[strategy_name] = {}
        
        params[strategy_name].update(new_params)
        params[strategy_name]['backtest_result'] = backtest_result
        
        # 更新 meta
        params['meta']['last_backtest_weeks'] = weeks
        
        ParamsManager.save(params)
        
        return params


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
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'total_return': self.total_return,
            'qqq_return': self.qqq_return,
            'alpha': self.alpha,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_loss_ratio': self.profit_loss_ratio,
            'accuracy': self.accuracy,
            'total_trades': self.total_trades
        }


# ============================================
# 數據抓取
# ============================================

class DataFetcher:
    """歷史數據抓取"""
    
    @staticmethod
    def fetch_historical(ticker: str, weeks: int) -> pd.DataFrame:
        """抓取歷史數據"""
        period = f"{weeks * 7 + 30}d"
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
        
        # 只保留最近 N 週 (處理時區問題)
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        # 將 cutoff_date 轉換為與 df.index 相同的時區
        if df.index.tz is not None:
            cutoff_date = pd.Timestamp(cutoff_date).tz_localize(df.index.tz)
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
        raise NotImplementedError
    
    def get_allocation(self, score: float) -> int:
        raise NotImplementedError
    
    def get_params_for_save(self) -> Dict:
        """返回要儲存的參數"""
        return self.params


class DefaultStrategy(BaseStrategy):
    """預設多因子策略"""
    name = "default"
    
    def __init__(self, params: Dict = None):
        super().__init__(params)
        
        # 從參數檔讀取或使用預設
        if params and 'weights' in params:
            self.weights = params['weights']
        else:
            self.weights = {
                "price_momentum": 0.30,
                "volume": 0.20,
                "vix": 0.20,
                "bond": 0.15,
                "mag7": 0.15
            }
    
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
        
        if total >= 6.5: signal = 'BUY'
        elif total <= 3.5: signal = 'SELL'
        else: signal = 'HOLD'
        
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
    
    def get_params_for_save(self) -> Dict:
        return {'weights': self.weights}


class MA20Strategy(BaseStrategy):
    """MA20 策略"""
    name = "ma20"
    
    def __init__(self, params: Dict = None):
        super().__init__(params)
        
        # 從參數讀取或使用預設
        self.days_threshold = params.get('days_threshold', 2) if params else 2
        self.vix_limit = params.get('vix_limit', 35) if params else 35
        self.position_weight = params.get('position_weight', 0.50) if params else 0.50
        self.trend_weight = params.get('trend_weight', 0.30) if params else 0.30
        self.vix_weight = params.get('vix_weight', 0.20) if params else 0.20
    
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
        
        # MA20 Trend
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
    
    def get_params_for_save(self) -> Dict:
        return {
            'days_threshold': self.days_threshold,
            'vix_limit': self.vix_limit,
            'position_weight': self.position_weight,
            'trend_weight': self.trend_weight,
            'vix_weight': self.vix_weight
        }


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
        prev_allocation = 50
        
        correct_predictions = 0
        total_predictions = 0
        
        for i in range(1, len(self.data)):
            row = self.data.iloc[i]
            prev_row = self.data.iloc[i-1]
            
            score, signal, factors = strategy.score(prev_row)
            allocation = strategy.get_allocation(score)
            
            change = row['change_pct']
            pnl = change * (prev_allocation / 100)
            cumulative_pnl += pnl
            
            if signal in ['BUY', 'SELL']:
                total_predictions += 1
                if (signal == 'BUY' and change > 0) or (signal == 'SELL' and change < 0):
                    correct_predictions += 1
            
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
            prev_allocation = allocation
        
        # 計算績效指標
        total_return = cumulative_pnl
        qqq_return = (self.data['close'].iloc[-1] / self.data['close'].iloc[0] - 1) * 100
        alpha = total_return - qqq_return
        
        pnls = [r.pnl_pct for r in results]
        win_days = len([p for p in pnls if p > 0])
        win_rate = win_days / len(pnls) * 100 if pnls else 0
        
        gains = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 1
        pl_ratio = avg_gain / avg_loss if avg_loss > 0 else 0
        
        cumulative = [r.cumulative_pnl for r in results]
        peak = cumulative[0] if cumulative else 0
        max_dd = 0
        for c in cumulative:
            if c > peak:
                peak = c
            dd = peak - c
            if dd > max_dd:
                max_dd = dd
        
        if len(pnls) > 1:
            mean_return = np.mean(pnls) * 252
            std_return = np.std(pnls) * np.sqrt(252)
            sharpe = mean_return / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        accuracy = correct_predictions / total_predictions * 100 if total_predictions > 0 else 0
        
        return BacktestResult(
            strategy=strategy.name,
            params=strategy.get_params_for_save(),
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
    
    def __init__(self, data: pd.DataFrame, weeks: int):
        self.data = data
        self.weeks = weeks
        self.engine = BacktestEngine(data)
    
    def optimize_ma20(self, auto_save: bool = True) -> Tuple[Dict, BacktestResult]:
        """優化 MA20 策略參數"""
        print("\n🔧 優化 MA20 策略參數...")
        
        # 參數搜索空間
        days_thresholds = [1, 2, 3]
        vix_limits = [30, 35, 40, 45]
        position_weights = [0.4, 0.5, 0.6]
        trend_weights = [0.2, 0.3, 0.4]
        
        results = []
        total = len(days_thresholds) * len(vix_limits) * len(position_weights) * len(trend_weights)
        
        print(f"  測試 {total} 種參數組合...")
        
        for days, vix_lim, pos_w, trend_w in itertools.product(
            days_thresholds, vix_limits, position_weights, trend_weights
        ):
            vix_w = round(1 - pos_w - trend_w, 2)
            if vix_w < 0.1 or vix_w > 0.4:
                continue
            
            params = {
                'days_threshold': days,
                'vix_limit': vix_lim,
                'position_weight': pos_w,
                'trend_weight': trend_w,
                'vix_weight': vix_w
            }
            
            strategy = MA20Strategy(params)
            result = self.engine.run(strategy)
            
            # 綜合評分
            composite = (
                result.alpha * 0.30 +
                result.sharpe_ratio * 0.25 +
                result.win_rate * 0.20 +
                result.accuracy * 0.15 -
                result.max_drawdown * 0.10
            )
            
            results.append({
                'params': params,
                'result': result,
                'composite_score': composite
            })
        
        # 排序
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        best = results[0]
        best_params = best['params']
        best_result = best['result']
        
        print(f"\n🏆 最佳參數:")
        print(f"  days_threshold: {best_params['days_threshold']}")
        print(f"  vix_limit: {best_params['vix_limit']}")
        print(f"  position_weight: {best_params['position_weight']}")
        print(f"  trend_weight: {best_params['trend_weight']}")
        print(f"  vix_weight: {best_params['vix_weight']}")
        print(f"\n📈 績效:")
        print(f"  Alpha: {best_result.alpha:+.2f}%")
        print(f"  夏普: {best_result.sharpe_ratio:.2f}")
        print(f"  勝率: {best_result.win_rate:.1f}%")
        print(f"  準確率: {best_result.accuracy:.1f}%")
        
        # 自動儲存
        if auto_save:
            ParamsManager.update_strategy(
                'ma20',
                best_params,
                best_result.to_dict(),
                self.weeks
            )
        
        return best_params, best_result
    
    def optimize_default(self, auto_save: bool = True) -> Tuple[Dict, BacktestResult]:
        """優化 Default 策略權重"""
        print("\n🔧 優化 Default 策略權重...")
        
        # 權重搜索空間
        weight_sets = [
            {"price_momentum": 0.30, "volume": 0.20, "vix": 0.20, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.35, "volume": 0.15, "vix": 0.25, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.25, "volume": 0.25, "vix": 0.25, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.40, "volume": 0.15, "vix": 0.20, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.30, "volume": 0.15, "vix": 0.30, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.25, "volume": 0.20, "vix": 0.25, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.35, "volume": 0.20, "vix": 0.15, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.30, "volume": 0.10, "vix": 0.30, "bond": 0.15, "mag7": 0.15},
            {"price_momentum": 0.35, "volume": 0.10, "vix": 0.30, "bond": 0.10, "mag7": 0.15},
            {"price_momentum": 0.40, "volume": 0.10, "vix": 0.25, "bond": 0.10, "mag7": 0.15},
        ]
        
        results = []
        
        print(f"  測試 {len(weight_sets)} 種權重組合...")
        
        for weights in weight_sets:
            params = {'weights': weights}
            strategy = DefaultStrategy(params)
            result = self.engine.run(strategy)
            # 將所有指標標準化為 0~1 或相似量級
            # win_rate: 60% -> 0.6
            # max_drawdown: 10% -> 0.1
            # sharpe: 除以 3 (假設 3 為極優秀)
            # alpha: 使用小數點 (0.05 代表 5%)
            composite = (
                result.alpha * 0.30 +
                result.sharpe_ratio * 0.25 +
                result.win_rate * 0.20 +
                result.accuracy * 0.15 -
                result.max_drawdown * 0.10
            )
            
            results.append({
                'params': params,
                'result': result,
                'composite_score': composite
            })
        
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        best = results[0]
        best_params = best['params']
        best_result = best['result']
        
        print(f"\n🏆 最佳權重:")
        for k, v in best_params['weights'].items():
            print(f"  {k}: {v}")
        print(f"\n📈 績效:")
        print(f"  Alpha: {best_result.alpha:+.2f}%")
        print(f"  夏普: {best_result.sharpe_ratio:.2f}")
        print(f"  勝率: {best_result.win_rate:.1f}%")
        
        if auto_save:
            ParamsManager.update_strategy(
                'default',
                best_params,
                best_result.to_dict(),
                self.weeks
            )
        
        return best_params, best_result


# ============================================
# 報表
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
    print(f"  • 預測準確率: {result.accuracy:.1f}%")


# ============================================
# 主程式
# ============================================

def main():
    parser = argparse.ArgumentParser(description='QQQ 策略回測工具 v2.0')
    parser.add_argument('--weeks', type=int, default=10, help='回測週數')
    parser.add_argument('--strategy', type=str, default='all', help='策略 (default, ma20, all)')
    parser.add_argument('--optimize', action='store_true', help='執行參數優化並自動儲存')
    parser.add_argument('--compare', action='store_true', help='比較所有策略')
    parser.add_argument('--no-save', action='store_true', help='不自動儲存參數')
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🔬 QQQ 策略回測工具 v2.0")
    print("="*60)
    
    # 抓取數據
    data = DataFetcher.prepare_data(args.weeks)
    if data.empty:
        print("❌ 無法取得數據")
        return
    
    engine = BacktestEngine(data)
    auto_save = not args.no_save
    
    # 參數優化
    if args.optimize:
        optimizer = ParameterOptimizer(data, args.weeks)
        
        print("\n" + "="*60)
        print("🔧 開始參數優化")
        print("="*60)
        
        # 優化 MA20
        ma20_params, ma20_result = optimizer.optimize_ma20(auto_save=auto_save)
        
        # 優化 Default
        default_params, default_result = optimizer.optimize_default(auto_save=auto_save)
        
        # 顯示最終參數檔
        print("\n" + "="*60)
        print("📄 optimized_params.json 內容:")
        print("="*60)
        params = ParamsManager.load()
        print(json.dumps(params, indent=2, ensure_ascii=False))
        
        return
    
    # 比較策略
    if args.compare or args.strategy == 'all':
        # 讀取最佳參數
        saved_params = ParamsManager.load()
        
        print(f"\n📖 載入參數: {PARAMS_FILE}")
        
        strategies = [
            ('default', DefaultStrategy(saved_params.get('default', {}))),
            ('ma20', MA20Strategy(saved_params.get('ma20', {}))),
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
    
    # 單一策略
    saved_params = ParamsManager.load()
    
    if args.strategy == 'ma20':
        strategy = MA20Strategy(saved_params.get('ma20', {}))
    else:
        strategy = DefaultStrategy(saved_params.get('default', {}))
    
    result = engine.run(strategy)
    print_backtest_result(result)


if __name__ == "__main__":
    main()
