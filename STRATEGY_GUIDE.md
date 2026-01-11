# 📈 交易策略標準化指南

> 本文件說明如何標準化新增交易策略，以及 Prompt 迭代的最佳實踐。

---

## 目錄

1. [策略模組化架構](#1-策略模組化架構)
2. [新增策略 SOP](#2-新增策略-sop)
3. [策略模板](#3-策略模板)
4. [Prompt 設計指南](#4-prompt-設計指南)
5. [策略評估與優化](#5-策略評估與優化)
6. [範例：新增 RSI 策略](#6-範例新增-rsi-策略)

---

## 1. 策略模組化架構

### 1.1 目錄結構

```
ai-invest-lab/
├── qqq_analyzer.py              # 主程式（使用策略）
├── strategies/
│   ├── __init__.py
│   ├── base.py                  # 策略基類
│   ├── registry.py              # 策略註冊表
│   ├── default_strategy.py      # 預設策略
│   ├── momentum_strategy.py     # 動能策略
│   └── rsi_strategy.py          # RSI 策略
├── prompts/
│   ├── v1.0/
│   │   ├── daily_analysis.md
│   │   └── metadata.json
│   └── current -> v1.0/
└── tests/
    └── test_strategies.py
```

### 1.2 設計原則

| 原則 | 說明 |
|------|------|
| 單一職責 | 每個策略只負責一種交易邏輯 |
| 開放封閉 | 新增策略不需修改現有程式碼 |
| 可測試性 | 策略可獨立測試與回測 |
| 可配置性 | 參數可從外部注入 |

---

## 2. 新增策略 SOP

### Step 1: 定義策略規格

```yaml
# 策略規格模板
strategy:
  name: "my_new_strategy"
  version: "1.0"
  description: "策略描述"
  
  # 所需數據
  required_data:
    - close_price
    - volume
    - vix
    
  # 因子定義
  factors:
    - name: factor_1
      weight: 0.4
      description: "因子描述"
    - name: factor_2
      weight: 0.6
      description: "因子描述"
      
  # 評分邏輯
  scoring:
    range: [1, 10]
    regime_thresholds:
      defense: 3.5
      offense: 6.5
      
  # 配置邏輯
  allocation:
    min_qqq: 10
    max_qqq: 90
```

### Step 2: 建立策略類別

### Step 3: 撰寫測試

### Step 4: 註冊策略

### Step 5: 部署與監控

---

## 3. 策略模板

### 3.1 基類 (base.py)

```python
"""
strategies/base.py
策略基類 - 所有策略必須繼承此類別
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ScoreResult:
    """評分結果"""
    total_score: float          # 1-10
    regime: str                 # offense/neutral/defense
    factor_scores: Dict         # 各因子評分
    confidence: str             # high/medium/low
    reasoning: str              # 評分理由


@dataclass
class AllocationResult:
    """配置結果"""
    qqq_pct: int
    cash_pct: int
    qqq_amount: int
    cash_amount: int
    stop_loss_price: float


class BaseStrategy(ABC):
    """
    策略基類
    
    所有自訂策略必須：
    1. 繼承此類別
    2. 實作 score() 方法
    3. 實作 get_allocation() 方法
    """
    
    # 策略元數據（子類別必須覆寫）
    name: str = "base"
    version: str = "1.0"
    description: str = "Base strategy"
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化策略
        
        Args:
            config: 策略配置
                - weights: 因子權重
                - params: 其他參數
                - capital: 初始資金
        """
        self.config = config or {}
        self.weights = self.config.get('weights', self.default_weights())
        self.params = self.config.get('params', {})
        self.capital = self.config.get('capital', 10_000_000)
    
    @abstractmethod
    def default_weights(self) -> Dict[str, float]:
        """
        返回預設權重
        
        Returns:
            Dict[str, float]: 因子名稱 -> 權重
        """
        pass
    
    @abstractmethod
    def score(self, data: Dict[str, Any]) -> ScoreResult:
        """
        計算評分
        
        Args:
            data: 市場數據
                - qqq: QQQ 報價
                - vix: VIX 數據
                - us10y: 10年期殖利率
                - technicals: 技術指標
        
        Returns:
            ScoreResult: 評分結果
        """
        pass
    
    @abstractmethod
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> AllocationResult:
        """
        根據評分計算配置
        
        Args:
            score: 總評分 (1-10)
            risk_pref: 風險偏好 (conservative/neutral/aggressive)
        
        Returns:
            AllocationResult: 配置結果
        """
        pass
    
    def get_regime(self, score: float) -> str:
        """判斷市場狀態"""
        if score <= 3.5:
            return 'defense'
        elif score >= 6.5:
            return 'offense'
        return 'neutral'
    
    def validate_weights(self) -> bool:
        """驗證權重總和為 1"""
        total = sum(self.weights.values())
        return abs(total - 1.0) < 0.01
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'name': self.name,
            'version': self.version,
            'weights': self.weights,
            'params': self.params
        }
```

### 3.2 策略實作模板

```python
"""
strategies/my_strategy.py
自訂策略模板
"""

from typing import Dict, Any
from .base import BaseStrategy, ScoreResult, AllocationResult


class MyStrategy(BaseStrategy):
    """
    策略名稱
    
    策略說明：
    - 核心邏輯
    - 適用場景
    - 注意事項
    """
    
    name = "my_strategy"
    version = "1.0"
    description = "我的自訂策略"
    
    def default_weights(self) -> Dict[str, float]:
        """預設權重"""
        return {
            "factor_1": 0.40,
            "factor_2": 0.30,
            "factor_3": 0.30,
        }
    
    def score(self, data: Dict[str, Any]) -> ScoreResult:
        """
        計算評分
        """
        # 1. 取得數據
        close = data.get('qqq', {}).get('close', 0)
        change = data.get('qqq', {}).get('change_pct', 0)
        vix = data.get('vix', {}).get('value', 20)
        
        # 2. 計算各因子評分
        factor_scores = {}
        
        # 因子 1 評分
        factor_scores['factor_1'] = self._score_factor_1(data)
        
        # 因子 2 評分
        factor_scores['factor_2'] = self._score_factor_2(data)
        
        # 因子 3 評分
        factor_scores['factor_3'] = self._score_factor_3(data)
        
        # 3. 計算加權總分
        total = sum(
            factor_scores[f]['score'] * self.weights[f]
            for f in self.weights
        )
        total = round(total, 1)
        
        # 4. 判斷狀態
        regime = self.get_regime(total)
        
        # 5. 信心度
        confidence = 'high' if abs(total - 5) > 2 else 'medium'
        
        # 6. 生成理由
        reasoning = self._generate_reasoning(factor_scores, total, regime)
        
        return ScoreResult(
            total_score=total,
            regime=regime,
            factor_scores=factor_scores,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _score_factor_1(self, data: Dict) -> Dict:
        """因子 1 評分邏輯"""
        value = data.get('some_value', 0)
        
        if value > 10:
            score, direction = 8, 'bullish'
        elif value > 5:
            score, direction = 6, 'neutral'
        else:
            score, direction = 4, 'bearish'
        
        return {'score': score, 'direction': direction, 'value': value}
    
    def _score_factor_2(self, data: Dict) -> Dict:
        """因子 2 評分邏輯"""
        # 實作評分邏輯
        return {'score': 5, 'direction': 'neutral'}
    
    def _score_factor_3(self, data: Dict) -> Dict:
        """因子 3 評分邏輯"""
        # 實作評分邏輯
        return {'score': 5, 'direction': 'neutral'}
    
    def _generate_reasoning(self, factors: Dict, total: float, regime: str) -> str:
        """生成評分理由"""
        return f"總評分 {total}/10，狀態 {regime}"
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> AllocationResult:
        """
        根據評分計算配置
        """
        # 風險調整
        adj = score
        if risk_pref == 'conservative':
            adj -= 1
        elif risk_pref == 'aggressive':
            adj += 1
        adj = max(1, min(10, adj))
        
        # 評分 -> 配置對照
        allocation_map = {
            (0, 2): 10,
            (2, 3): 20,
            (3, 4): 35,
            (4, 5): 50,
            (5, 6): 60,
            (6, 7): 75,
            (7, 8): 85,
            (8, 11): 90,
        }
        
        qqq_pct = 50  # 預設
        for (low, high), pct in allocation_map.items():
            if low <= adj < high:
                qqq_pct = pct
                break
        
        # 計算金額
        qqq_amount = int(self.capital * qqq_pct / 100)
        cash_amount = self.capital - qqq_amount
        
        # 止損價位
        close = self.params.get('current_close', 500)
        stop_loss = round(close * 0.98, 2)
        
        return AllocationResult(
            qqq_pct=qqq_pct,
            cash_pct=100 - qqq_pct,
            qqq_amount=qqq_amount,
            cash_amount=cash_amount,
            stop_loss_price=stop_loss
        )
```

### 3.3 策略註冊表 (registry.py)

```python
"""
strategies/registry.py
策略註冊表
"""

from typing import Dict, Type
from .base import BaseStrategy
from .default_strategy import DefaultStrategy
# from .momentum_strategy import MomentumStrategy
# from .rsi_strategy import RSIStrategy


# 策略註冊表
STRATEGIES: Dict[str, Type[BaseStrategy]] = {
    'default': DefaultStrategy,
    # 'momentum': MomentumStrategy,
    # 'rsi': RSIStrategy,
}


def get_strategy(name: str, config: Dict = None) -> BaseStrategy:
    """
    取得策略實例
    
    Args:
        name: 策略名稱
        config: 策略配置
    
    Returns:
        BaseStrategy: 策略實例
    
    Raises:
        ValueError: 策略不存在
    """
    if name not in STRATEGIES:
        available = list(STRATEGIES.keys())
        raise ValueError(f"Unknown strategy: {name}. Available: {available}")
    
    strategy_class = STRATEGIES[name]
    return strategy_class(config)


def list_strategies() -> Dict[str, str]:
    """列出所有可用策略"""
    return {
        name: cls.description
        for name, cls in STRATEGIES.items()
    }


def register_strategy(name: str, strategy_class: Type[BaseStrategy]):
    """動態註冊策略"""
    if not issubclass(strategy_class, BaseStrategy):
        raise TypeError("Strategy must inherit from BaseStrategy")
    STRATEGIES[name] = strategy_class
```

---

## 4. Prompt 設計指南

### 4.1 Prompt 結構

```markdown
# [策略名稱] 分析 Prompt

## 系統角色
你是一個專業的量化交易分析師，專精於 {專業領域}。
你的分析風格是 {風格描述}。

## 背景知識
- {相關知識 1}
- {相關知識 2}

## 輸入數據
```json
{
  "date": "{date}",
  "ticker": "QQQ",
  "market_data": {
    "close": {close},
    "change_pct": {change_pct},
    "volume_ratio": {volume_ratio}
  },
  "vix": {vix},
  "us10y": {us10y}
}
```

## 分析任務
1. 分析市場狀態
2. 評估各因子
3. 給出評分 (1-10)
4. 建議配置

## 輸出格式
必須使用以下 JSON 格式回應：
```json
{
  "score": 7.5,
  "regime": "offense",
  "allocation": {"qqq_pct": 70, "cash_pct": 30},
  "factor_analysis": {...},
  "reasoning": "..."
}
```

## 評分指南
- 1-3: 強烈看空（防禦模式）
- 4-5: 中性觀望
- 6-7: 溫和看多
- 8-10: 強烈看多（進攻模式）

## 限制條件
- 評分必須在 1-10 之間
- 配置總和必須為 100%
- 必須提供明確理由
- 不可建議衍生性商品

## 範例
[提供 2-3 個不同情況的範例]
```

### 4.2 Prompt 版本控制

```
prompts/
├── v1.0/
│   ├── daily_analysis.md
│   ├── validation.md
│   ├── weekly_review.md
│   └── metadata.json
├── v1.1/
│   ├── daily_analysis.md
│   ├── CHANGELOG.md
│   └── metadata.json
└── current -> v1.1/
```

**metadata.json**
```json
{
  "version": "1.1",
  "created_at": "2025-01-11",
  "author": "team",
  "changes": [
    "優化評分邏輯",
    "新增 VIX 權重"
  ],
  "metrics": {
    "accuracy": 0.72,
    "test_period": "2024-12-01 to 2025-01-10"
  }
}
```

### 4.3 Prompt 迭代流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Prompt 迭代流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 收集回饋                                                     │
│     ├── 驗證記錄 (Validations)                                   │
│     ├── 錯誤案例分析                                              │
│     └── 使用者回饋                                                │
│                          ↓                                      │
│  2. 識別問題                                                     │
│     ├── 準確率下降？                                              │
│     ├── 某情境表現差？                                            │
│     └── 邏輯不一致？                                              │
│                          ↓                                      │
│  3. 設計改進                                                     │
│     ├── 調整角色設定                                              │
│     ├── 優化輸入格式                                              │
│     ├── 增加範例                                                 │
│     └── 加入限制條件                                              │
│                          ↓                                      │
│  4. A/B 測試                                                    │
│     ├── 新舊 Prompt 並行                                         │
│     ├── 相同輸入比較輸出                                          │
│     └── 統計顯著性檢驗                                            │
│                          ↓                                      │
│  5. 部署                                                        │
│     ├── 更新 current 連結                                        │
│     ├── 記錄變更                                                 │
│     └── 監控效果                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Prompt 最佳實踐

| ✅ DO | ❌ DON'T |
|-------|----------|
| 明確定義角色 | 模糊的指令 |
| 結構化輸入 | 省略上下文 |
| 指定輸出格式 | 開放式輸出 |
| 提供範例 | 只有文字說明 |
| 設定限制條件 | 允許任意回答 |
| 要求解釋理由 | 只要求結論 |
| 版本控制 | 直接覆蓋修改 |

---

## 5. 策略評估與優化

### 5.1 評估指標

```python
# 策略評估指標
class StrategyMetrics:
    """策略績效指標"""
    
    def __init__(self, validations: List[Dict]):
        self.validations = validations
    
    def accuracy(self) -> float:
        """預測準確率"""
        correct = sum(1 for v in self.validations if v['is_correct'])
        return correct / len(self.validations) if self.validations else 0
    
    def win_rate(self) -> float:
        """勝率（獲利天數比例）"""
        wins = sum(1 for v in self.validations if v['pnl_pct'] > 0)
        return wins / len(self.validations) if self.validations else 0
    
    def profit_loss_ratio(self) -> float:
        """盈虧比"""
        gains = [v['pnl_pct'] for v in self.validations if v['pnl_pct'] > 0]
        losses = [abs(v['pnl_pct']) for v in self.validations if v['pnl_pct'] < 0]
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 1
        
        return avg_gain / avg_loss if avg_loss > 0 else 0
    
    def sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """夏普比率（年化）"""
        returns = [v['pnl_pct'] for v in self.validations]
        if not returns:
            return 0
        
        import numpy as np
        mean_return = np.mean(returns) * 252  # 年化
        std_return = np.std(returns) * np.sqrt(252)
        
        return (mean_return - risk_free_rate) / std_return if std_return > 0 else 0
    
    def max_drawdown(self) -> float:
        """最大回撤"""
        cumulative = []
        total = 0
        for v in self.validations:
            total += v['pnl_pct']
            cumulative.append(total)
        
        if not cumulative:
            return 0
        
        peak = cumulative[0]
        max_dd = 0
        for c in cumulative:
            if c > peak:
                peak = c
            dd = peak - c
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def report(self) -> Dict:
        """完整報告"""
        return {
            'accuracy': f"{self.accuracy():.1%}",
            'win_rate': f"{self.win_rate():.1%}",
            'profit_loss_ratio': f"{self.profit_loss_ratio():.2f}",
            'sharpe_ratio': f"{self.sharpe_ratio():.2f}",
            'max_drawdown': f"{self.max_drawdown():.2%}",
            'sample_size': len(self.validations)
        }
```

### 5.2 回測框架

```python
# 簡易回測框架
class Backtester:
    """策略回測器"""
    
    def __init__(self, strategy: BaseStrategy, historical_data: List[Dict]):
        self.strategy = strategy
        self.data = historical_data
    
    def run(self) -> Dict:
        """執行回測"""
        results = []
        
        for i in range(1, len(self.data)):
            # 前一天的數據用於評分
            prev_data = self.data[i-1]
            today_data = self.data[i]
            
            # 計算評分和配置
            score_result = self.strategy.score(prev_data)
            allocation = self.strategy.get_allocation(score_result.total_score)
            
            # 計算實際損益
            actual_change = today_data.get('change_pct', 0)
            pnl = actual_change * (allocation.qqq_pct / 100)
            
            # 驗證預測
            predicted = 'bullish' if score_result.total_score >= 6 else 'bearish' if score_result.total_score <= 4 else 'neutral'
            actual = 'bullish' if actual_change > 0.1 else 'bearish' if actual_change < -0.1 else 'neutral'
            
            results.append({
                'date': today_data.get('date'),
                'score': score_result.total_score,
                'predicted': predicted,
                'actual': actual,
                'is_correct': (predicted == actual) or (predicted == 'bullish' and actual_change > 0) or (predicted == 'bearish' and actual_change < 0),
                'qqq_pct': allocation.qqq_pct,
                'actual_change': actual_change,
                'pnl_pct': pnl
            })
        
        # 計算績效指標
        metrics = StrategyMetrics(results)
        
        return {
            'results': results,
            'metrics': metrics.report(),
            'total_return': sum(r['pnl_pct'] for r in results)
        }
```

### 5.3 優化流程

```
1. 設定基準
   - 使用預設策略建立基準績效
   - 記錄: 準確率、勝率、夏普比率

2. 參數優化
   - 調整因子權重
   - 調整評分閾值
   - 調整配置對照表

3. 驗證改進
   - 回測驗證
   - 樣本外測試
   - 統計顯著性

4. 部署監控
   - 小規模上線
   - 追蹤績效
   - 定期覆盤
```

---

## 6. 範例：新增 RSI 策略

### 6.1 策略定義

```yaml
strategy:
  name: rsi_strategy
  version: "1.0"
  description: "基於 RSI 的均值回歸策略"
  
  logic: |
    當 RSI 過低（超賣）時看多
    當 RSI 過高（超買）時看空
    結合 VIX 作為風險調整
  
  factors:
    - name: rsi
      weight: 0.50
      description: "RSI(14) 指標"
    - name: vix
      weight: 0.30
      description: "VIX 恐慌指數"
    - name: trend
      weight: 0.20
      description: "均線趨勢"
```

### 6.2 策略實作

```python
"""
strategies/rsi_strategy.py
RSI 均值回歸策略
"""

from typing import Dict, Any
from .base import BaseStrategy, ScoreResult, AllocationResult


class RSIStrategy(BaseStrategy):
    """
    RSI 均值回歸策略
    
    邏輯：
    - RSI < 30: 超賣，看多
    - RSI > 70: 超買，看空
    - 結合 VIX 調整風險
    """
    
    name = "rsi_strategy"
    version = "1.0"
    description = "基於 RSI 的均值回歸策略"
    
    def default_weights(self) -> Dict[str, float]:
        return {
            "rsi": 0.50,
            "vix": 0.30,
            "trend": 0.20,
        }
    
    def score(self, data: Dict[str, Any]) -> ScoreResult:
        factor_scores = {}
        
        # 1. RSI 評分（反向邏輯 - 均值回歸）
        rsi = data.get('technicals', {}).get('rsi', 50)
        factor_scores['rsi'] = self._score_rsi(rsi)
        
        # 2. VIX 評分
        vix = data.get('vix', {}).get('value', 20)
        factor_scores['vix'] = self._score_vix(vix)
        
        # 3. 趨勢評分
        factor_scores['trend'] = self._score_trend(data)
        
        # 計算總分
        total = sum(
            factor_scores[f]['score'] * self.weights[f]
            for f in self.weights
        )
        total = round(total, 1)
        
        regime = self.get_regime(total)
        confidence = 'high' if rsi < 25 or rsi > 75 else 'medium'
        
        reasoning = f"RSI={rsi:.0f}, VIX={vix:.1f}, 總分={total}"
        
        return ScoreResult(
            total_score=total,
            regime=regime,
            factor_scores=factor_scores,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _score_rsi(self, rsi: float) -> Dict:
        """RSI 評分 - 均值回歸邏輯"""
        if rsi < 20:
            return {'score': 9, 'direction': 'oversold', 'value': rsi}
        elif rsi < 30:
            return {'score': 8, 'direction': 'oversold', 'value': rsi}
        elif rsi < 40:
            return {'score': 7, 'direction': 'neutral', 'value': rsi}
        elif rsi < 60:
            return {'score': 5, 'direction': 'neutral', 'value': rsi}
        elif rsi < 70:
            return {'score': 4, 'direction': 'neutral', 'value': rsi}
        elif rsi < 80:
            return {'score': 3, 'direction': 'overbought', 'value': rsi}
        else:
            return {'score': 2, 'direction': 'overbought', 'value': rsi}
    
    def _score_vix(self, vix: float) -> Dict:
        """VIX 評分"""
        if vix < 15:
            return {'score': 8, 'direction': 'low_fear'}
        elif vix < 20:
            return {'score': 6, 'direction': 'normal'}
        elif vix < 25:
            return {'score': 5, 'direction': 'elevated'}
        elif vix < 30:
            return {'score': 3, 'direction': 'high'}
        else:
            return {'score': 2, 'direction': 'extreme'}
    
    def _score_trend(self, data: Dict) -> Dict:
        """趨勢評分"""
        close = data.get('qqq', {}).get('close', 0)
        ma20 = data.get('technicals', {}).get('ma20', close)
        
        if close > ma20 * 1.02:
            return {'score': 7, 'direction': 'uptrend'}
        elif close > ma20:
            return {'score': 6, 'direction': 'uptrend'}
        elif close > ma20 * 0.98:
            return {'score': 5, 'direction': 'sideways'}
        else:
            return {'score': 4, 'direction': 'downtrend'}
    
    def get_allocation(self, score: float, risk_pref: str = 'neutral') -> AllocationResult:
        """配置計算"""
        adj = score
        if risk_pref == 'conservative':
            adj -= 1
        elif risk_pref == 'aggressive':
            adj += 1
        adj = max(1, min(10, adj))
        
        # RSI 策略配置較保守
        if adj <= 3:
            qqq_pct = 20
        elif adj <= 4:
            qqq_pct = 35
        elif adj <= 5:
            qqq_pct = 45
        elif adj <= 6:
            qqq_pct = 55
        elif adj <= 7:
            qqq_pct = 65
        else:
            qqq_pct = 75
        
        return AllocationResult(
            qqq_pct=qqq_pct,
            cash_pct=100 - qqq_pct,
            qqq_amount=int(self.capital * qqq_pct / 100),
            cash_amount=int(self.capital * (100 - qqq_pct) / 100),
            stop_loss_price=self.params.get('current_close', 500) * 0.97
        )
```

### 6.3 註冊策略

```python
# 在 registry.py 中加入
from .rsi_strategy import RSIStrategy

STRATEGIES = {
    'default': DefaultStrategy,
    'rsi': RSIStrategy,  # 新增
}
```

### 6.4 使用策略

```python
# 在主程式中使用
from strategies import get_strategy

# 取得策略
strategy = get_strategy('rsi', config={
    'capital': 10_000_000,
    'params': {'current_close': 520}
})

# 計算評分
result = strategy.score(market_data)
print(f"評分: {result.total_score}/10")
print(f"狀態: {result.regime}")

# 計算配置
allocation = strategy.get_allocation(result.total_score, 'neutral')
print(f"配置: QQQ {allocation.qqq_pct}%")
```

---

## 附錄：檢查清單

### 新增策略檢查清單

```markdown
## 策略開發檢查清單

### 設計階段
- [ ] 策略邏輯已定義
- [ ] 因子已識別
- [ ] 權重已設定
- [ ] 評分邏輯已設計

### 開發階段
- [ ] 繼承 BaseStrategy
- [ ] 實作 default_weights()
- [ ] 實作 score()
- [ ] 實作 get_allocation()
- [ ] 錯誤處理完整

### 測試階段
- [ ] 單元測試通過
- [ ] 邊界測試通過
- [ ] 回測完成
- [ ] 績效符合預期

### 部署階段
- [ ] 加入 registry
- [ ] 文件已更新
- [ ] 手動測試成功
```

### Prompt 迭代檢查清單

```markdown
## Prompt 迭代檢查清單

- [ ] 問題已識別
- [ ] 改進方案已設計
- [ ] 新版本已建立
- [ ] 範例已更新
- [ ] A/B 測試完成
- [ ] metadata.json 已更新
- [ ] current 連結已更新
```

---

**文件結束**
