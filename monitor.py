#!/usr/bin/env python3
"""
自動化監控腳本
定期檢查系統狀態並發送告警

使用方式:
    python monitor.py              # 執行一次檢查
    python monitor.py --daemon     # 持續監控模式
"""

import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List
import requests


# ============================================
# 配置
# ============================================

class MonitorConfig:
    GAS_URL = 'YOUR_GAS_URL_HERE'
    TELEGRAM_BOT_TOKEN = 'YOUR_TOKEN_HERE'
    TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID_HERE'
    
    # 告警閾值
    THRESHOLDS = {
        'vix_high': 30,
        'vix_critical': 40,
        'score_low': 3.5,
        'score_critical': 2.5,
        'drawdown_warning': -5.0,
        'drawdown_critical': -8.0,
        'accuracy_low': 45.0,
        'consecutive_losses': 3
    }
    
    # 監控間隔（秒）
    CHECK_INTERVAL = 3600  # 1小時


# ============================================
# 監控器
# ============================================

class SystemMonitor:
    def __init__(self):
        self.alerts = []
        self.last_check = None
        self.status_history = []
    
    def check_system_health(self) -> Dict:
        """檢查系統健康狀況"""
        print(f"\n{'='*60}")
        print(f"🔍 系統健康檢查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        try:
            # 1. API 連接測試
            health['checks']['api'] = self._check_api_connection()
            
            # 2. 數據更新檢查
            health['checks']['data_freshness'] = self._check_data_freshness()
            
            # 3. 市場指標檢查
            health['checks']['market_metrics'] = self._check_market_metrics()
            
            # 4. 策略性能檢查
            health['checks']['strategy_performance'] = self._check_strategy_performance()
            
            # 5. 預測準確率檢查
            health['checks']['prediction_accuracy'] = self._check_prediction_accuracy()
            
            # 總體狀態
            if any(c.get('status') == 'critical' for c in health['checks'].values()):
                health['status'] = 'critical'
            elif any(c.get('status') == 'warning' for c in health['checks'].values()):
                health['status'] = 'warning'
            
            self.last_check = datetime.now()
            self.status_history.append(health)
            
            return health
            
        except Exception as e:
            print(f"❌ 健康檢查失敗: {e}")
            health['status'] = 'error'
            health['error'] = str(e)
            return health
    
    def _check_api_connection(self) -> Dict:
        """檢查 API 連接"""
        try:
            url = f"{MonitorConfig.GAS_URL}?action=health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print("  ✅ API 連接正常")
                    return {'status': 'ok', 'message': 'API 連接正常'}
            
            print("  ⚠️ API 回應異常")
            return {'status': 'warning', 'message': 'API 回應異常'}
            
        except requests.Timeout:
            print("  ❌ API 連接超時")
            return {'status': 'critical', 'message': 'API 連接超時'}
        except Exception as e:
            print(f"  ❌ API 連接失敗: {e}")
            return {'status': 'critical', 'message': f'API 連接失敗: {e}'}
    
    def _check_data_freshness(self) -> Dict:
        """檢查數據新鮮度"""
        try:
            url = f"{MonitorConfig.GAS_URL}?action=latest"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            # 檢查最後更新時間
            if 'date' in data:
                last_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                age = datetime.now() - last_date.replace(tzinfo=None)
                
                if age.days == 0:
                    print(f"  ✅ 數據更新正常 (今日)")
                    return {'status': 'ok', 'message': '數據為最新', 'age_hours': age.seconds // 3600}
                elif age.days == 1:
                    print(f"  ⚠️ 數據稍舊 (昨日)")
                    return {'status': 'warning', 'message': '數據為昨日', 'age_days': age.days}
                else:
                    print(f"  ❌ 數據過舊 ({age.days}天)")
                    return {'status': 'critical', 'message': f'數據已 {age.days} 天未更新', 'age_days': age.days}
            
            return {'status': 'warning', 'message': '無法確定數據時間'}
            
        except Exception as e:
            print(f"  ❌ 數據檢查失敗: {e}")
            return {'status': 'critical', 'message': str(e)}
    
    def _check_market_metrics(self) -> Dict:
        """檢查市場指標"""
        try:
            url = f"{MonitorConfig.GAS_URL}?action=latest"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            issues = []
            vix = float(data.get('vix', 0))
            score = float(data.get('total_score', 5))
            
            # VIX 檢查
            if vix > MonitorConfig.THRESHOLDS['vix_critical']:
                issues.append(f"VIX 極高: {vix:.1f}")
                status = 'critical'
            elif vix > MonitorConfig.THRESHOLDS['vix_high']:
                issues.append(f"VIX 偏高: {vix:.1f}")
                status = 'warning'
            else:
                status = 'ok'
            
            # 評分檢查
            if score < MonitorConfig.THRESHOLDS['score_critical']:
                issues.append(f"評分極低: {score:.1f}/10")
                status = 'critical'
            elif score < MonitorConfig.THRESHOLDS['score_low']:
                issues.append(f"評分偏低: {score:.1f}/10")
                if status == 'ok':
                    status = 'warning'
            
            if issues:
                print(f"  ⚠️ 市場指標異常: {', '.join(issues)}")
            else:
                print(f"  ✅ 市場指標正常 (VIX: {vix:.1f}, 評分: {score:.1f})")
            
            return {
                'status': status,
                'vix': vix,
                'score': score,
                'issues': issues
            }
            
        except Exception as e:
            print(f"  ❌ 市場指標檢查失敗: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _check_strategy_performance(self) -> Dict:
        """檢查策略性能"""
        try:
            url = f"{MonitorConfig.GAS_URL}?action=weekly_reviews&count=1"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if not data or len(data) == 0:
                return {'status': 'warning', 'message': '無週報數據'}
            
            latest = data[-1] if isinstance(data, list) else data
            
            alpha = float(latest.get('alpha', 0))
            max_dd = float(latest.get('max_drawdown', 0))
            
            issues = []
            status = 'ok'
            
            # Alpha 檢查
            if alpha < -2:
                issues.append(f"Alpha 較差: {alpha:.2f}%")
                status = 'warning'
            
            # 回撤檢查
            if max_dd < MonitorConfig.THRESHOLDS['drawdown_critical']:
                issues.append(f"回撤過大: {max_dd:.2f}%")
                status = 'critical'
            elif max_dd < MonitorConfig.THRESHOLDS['drawdown_warning']:
                issues.append(f"回撤較大: {max_dd:.2f}%")
                if status == 'ok':
                    status = 'warning'
            
            if issues:
                print(f"  ⚠️ 策略性能: {', '.join(issues)}")
            else:
                print(f"  ✅ 策略性能正常 (Alpha: {alpha:.2f}%, 回撤: {max_dd:.2f}%)")
            
            return {
                'status': status,
                'alpha': alpha,
                'max_drawdown': max_dd,
                'issues': issues
            }
            
        except Exception as e:
            print(f"  ⚠️ 策略性能檢查失敗: {e}")
            return {'status': 'warning', 'message': str(e)}
    
    def _check_prediction_accuracy(self) -> Dict:
        """檢查預測準確率"""
        try:
            url = f"{MonitorConfig.GAS_URL}?action=validations&days=30"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if not data or len(data) == 0:
                return {'status': 'warning', 'message': '無驗證數據'}
            
            correct = sum(1 for v in data if v.get('is_correct') in [True, 'TRUE'])
            total = len(data)
            accuracy = (correct / total * 100) if total > 0 else 0
            
            if accuracy < MonitorConfig.THRESHOLDS['accuracy_low']:
                print(f"  ⚠️ 準確率偏低: {accuracy:.1f}%")
                return {
                    'status': 'warning',
                    'accuracy': accuracy,
                    'correct': correct,
                    'total': total
                }
            else:
                print(f"  ✅ 準確率正常: {accuracy:.1f}% ({correct}/{total})")
                return {
                    'status': 'ok',
                    'accuracy': accuracy,
                    'correct': correct,
                    'total': total
                }
            
        except Exception as e:
            print(f"  ⚠️ 準確率檢查失敗: {e}")
            return {'status': 'warning', 'message': str(e)}
    
    def send_alert(self, health: Dict):
        """發送告警"""
        if health['status'] in ['warning', 'critical']:
            message = self._format_alert_message(health)
            self._send_telegram(message)
    
    def _format_alert_message(self, health: Dict) -> str:
        """格式化告警訊息"""
        emoji = '🚨' if health['status'] == 'critical' else '⚠️'
        title = '嚴重告警' if health['status'] == 'critical' else '系統警告'
        
        message = f"{emoji} *{title}*\n\n"
        message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 各項檢查結果
        for check_name, check_result in health['checks'].items():
            if check_result.get('status') in ['warning', 'critical']:
                name = check_name.replace('_', ' ').title()
                message += f"• {name}: "
                
                if 'issues' in check_result and check_result['issues']:
                    message += '\n  - ' + '\n  - '.join(check_result['issues'])
                elif 'message' in check_result:
                    message += check_result['message']
                
                message += "\n"
        
        return message
    
    def _send_telegram(self, message: str):
        """發送 Telegram 通知"""
        try:
            url = f"https://api.telegram.org/bot{MonitorConfig.TELEGRAM_BOT_TOKEN}/sendMessage"
            response = requests.post(url, json={
                'chat_id': MonitorConfig.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=10)
            
            if response.json().get('ok'):
                print("\n📱 Telegram 告警已發送")
            else:
                print("\n❌ Telegram 發送失敗")
                
        except Exception as e:
            print(f"\n❌ Telegram 發送錯誤: {e}")
    
    def generate_report(self) -> str:
        """生成監控報告"""
        if not self.status_history:
            return "無監控記錄"
        
        latest = self.status_history[-1]
        
        report = f"\n{'='*60}\n"
        report += f"📊 系統監控報告\n"
        report += f"{'='*60}\n\n"
        
        report += f"⏰ 檢查時間: {latest['timestamp']}\n"
        report += f"📊 系統狀態: {latest['status'].upper()}\n\n"
        
        for check_name, check_result in latest['checks'].items():
            name = check_name.replace('_', ' ').title()
            status = check_result.get('status', 'unknown')
            emoji = '✅' if status == 'ok' else '⚠️' if status == 'warning' else '❌'
            
            report += f"{emoji} {name}: {status}\n"
        
        return report


# ============================================
# 主程式
# ============================================

def main():
    parser = argparse.ArgumentParser(description='QQQ 系統監控')
    parser.add_argument('--daemon', action='store_true', help='持續監控模式')
    parser.add_argument('--interval', type=int, default=3600, help='檢查間隔（秒）')
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.daemon:
        print("🔄 啟動持續監控模式...")
        print(f"   檢查間隔: {args.interval} 秒")
        print("   按 Ctrl+C 停止\n")
        
        try:
            while True:
                health = monitor.check_system_health()
                monitor.send_alert(health)
                print(monitor.generate_report())
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ 監控已停止")
            print(f"   總檢查次數: {len(monitor.status_history)}")
    else:
        # 單次檢查
        health = monitor.check_system_health()
        monitor.send_alert(health)
        print(monitor.generate_report())


if __name__ == "__main__":
    main()
