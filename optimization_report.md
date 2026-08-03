# Optimization Report

**Date:** Mon Aug  3 12:54:28 UTC 2026
**Strategy:** all
**Days:** 60
**Dry Run:** false


## Updated Parameters
```json
{
  "meta": {
    "last_updated": "2026-08-03T12:54:26.612930",
    "environment": "production",
    "last_backtest_weeks": 10,
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
          "total_return": 0.0,
          "benchmark_return": 0.0,
          "alpha": 0.0,
          "sharpe_ratio": 0.0,
          "max_drawdown": 0.0,
          "final_nav": 10000000.0,
          "days": 0
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
          "total_return": 0.0,
          "benchmark_return": 0.0,
          "alpha": 0.0,
          "sharpe_ratio": 0.0,
          "max_drawdown": 0.0,
          "final_nav": 10000000.0,
          "days": 0
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
      "total_return": -6.96,
      "qqq_return": -7.45,
      "alpha": 0.5,
      "sharpe_ratio": -2.49,
      "max_drawdown": 8.79,
      "win_rate": 42.5,
      "profit_loss_ratio": 0.91,
      "accuracy": 66.7,
      "total_trades": 6
    }
  }
}```
