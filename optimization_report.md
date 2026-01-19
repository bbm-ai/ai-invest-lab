# Optimization Report

**Date:** Mon Jan 19 12:07:58 UTC 2026
**Strategy:** all
**Days:** 60
**Dry Run:** false


## Updated Parameters
```json
{
  "meta": {
    "last_updated": "2026-01-19T12:07:56.389610",
    "last_backtest_weeks": 10,
    "version": "2.0",
    "optimization_days": 60,
    "optimization_results": {
      "ma20": {
        "params": {
          "days_threshold": 1,
          "vix_limit": 30,
          "position_weight": 0.4,
          "trend_weight": 0.35,
          "vix_weight": 0.25
        },
        "metrics": {
          "total_return": 0.82,
          "benchmark_return": 2.74,
          "alpha": -1.92,
          "sharpe_ratio": 0.58,
          "max_drawdown": 3.2,
          "final_nav": 10082111.96,
          "days": 59
        }
      },
      "default": {
        "weights": {
          "price_momentum": 0.1,
          "volume": 0.1,
          "vix": 0.1,
          "bond": 0.35,
          "mag7": 0.3500000000000001
        },
        "metrics": {
          "total_return": 1.01,
          "benchmark_return": 2.74,
          "alpha": -1.72,
          "sharpe_ratio": 0.58,
          "max_drawdown": 3.99,
          "final_nav": 10101190.31,
          "days": 59
        }
      }
    }
  },
  "ma20": {
    "days_threshold": 1,
    "vix_limit": 30,
    "position_weight": 0.4,
    "trend_weight": 0.35,
    "vix_weight": 0.25
  },
  "default": {
    "weights": {
      "price_momentum": 0.1,
      "volume": 0.1,
      "vix": 0.1,
      "bond": 0.35,
      "mag7": 0.3500000000000001
    },
    "backtest_result": {
      "total_return": 2.79,
      "qqq_return": 4.32,
      "alpha": -1.53,
      "sharpe_ratio": 2.41,
      "max_drawdown": 2.47,
      "win_rate": 57.5,
      "profit_loss_ratio": 1.08,
      "accuracy": 88.9,
      "total_trades": 9
    }
  }
}```
