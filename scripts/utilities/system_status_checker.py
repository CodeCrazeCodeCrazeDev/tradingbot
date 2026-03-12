"""
System Status Checker - Quick system health and readiness check
Provides instant overview of system status
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Minimal logging for status check
logging.basicConfig(level=logging.WARNING)


class SystemStatusChecker:
    """Quick system status checker."""
    
    def __init__(self):
        """Initialize status checker."""
        self.status = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'overall_status': 'UNKNOWN',
            'critical_issues': [],
            'warnings': []
        }
    
    def check_all(self) -> Dict[str, Any]:
        """Run all status checks."""
        print("="*80)
        print("  TRADING BOT - SYSTEM STATUS CHECK")
        print("="*80)
        print()
        
        # 1. Python Environment
        self._check_python()
        
        # 2. Directory Structure
        self._check_directories()
        
        # 3. Core Files
        self._check_core_files()
        
        # 4. Recent Logs
        self._check_recent_logs()
        
        # 5. Saved State
        self._check_saved_state()
        
        # 6. System Resources
        self._check_system_resources()
        
        # Determine overall status
        self._determine_overall_status()
        
        # Display summary
        self._display_summary()
        
        return self.status
    
    def _check_python(self):
        """Check Python environment."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major == 3 and version.minor >= 10:
            self._add_check("Python Version", "OK", f"Python {version_str}")
        else:
            self._add_check("Python Version", "FAIL", f"Python {version_str} (Need 3.10+)", critical=True)
    
    def _check_directories(self):
        """Check required directories."""
        required_dirs = ['logs', 'knowledge', 'data', 'trading_bot', 'learning']
        
        missing = []
        for directory in required_dirs:
            if not os.path.isdir(directory):
                missing.append(directory)
        
        if not missing:
            self._add_check("Directories", "OK", f"All {len(required_dirs)} directories present")
        else:
            self._add_check("Directories", "WARN", f"Missing: {', '.join(missing)}")
    
    def _check_core_files(self):
        """Check core system files."""
        core_files = [
            'integrated_trading_system.py',
            'production_runner.py',
            'system_health_monitor.py',
            'risk_controller.py',
            'data_manager.py',
            'performance_optimizer.py',
            'alphaalgo_2_0.py',
            'learning_bot.py'
        ]
        
        missing = []
        for file in core_files:
            if not os.path.isfile(file):
                missing.append(file)
        
        if not missing:
            self._add_check("Core Files", "OK", f"All {len(core_files)} core files present")
        else:
            self._add_check("Core Files", "FAIL", f"Missing: {', '.join(missing)}", critical=True)
    
    def _check_recent_logs(self):
        """Check for recent log activity."""
        log_dir = Path('logs')
        
        if not log_dir.exists():
            self._add_check("Recent Logs", "WARN", "No logs directory")
            return
        
        log_files = list(log_dir.glob('*.log'))
        
        if not log_files:
            self._add_check("Recent Logs", "INFO", "No log files (fresh system)")
            return
        
        # Check most recent log
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        age_seconds = (datetime.now().timestamp() - latest_log.stat().st_mtime)
        age_hours = age_seconds / 3600
        
        if age_hours < 1:
            self._add_check("Recent Logs", "OK", f"Recent activity ({age_hours:.1f}h ago)")
        elif age_hours < 24:
            self._add_check("Recent Logs", "INFO", f"Last activity {age_hours:.1f}h ago")
        else:
            self._add_check("Recent Logs", "INFO", f"Last activity {age_hours/24:.1f}d ago")
    
    def _check_saved_state(self):
        """Check for saved state files."""
        state_files = [
            'knowledge/distributional_rl.pt',
            'knowledge/optimizer_state.json',
            'knowledge/strategy_params.json'
        ]
        
        found = sum(1 for f in state_files if os.path.isfile(f))
        
        if found > 0:
            self._add_check("Saved State", "OK", f"{found}/{len(state_files)} state files found")
        else:
            self._add_check("Saved State", "INFO", "No saved state (fresh system)")
    
    def _check_system_resources(self):
        """Check system resources."""
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            issues = []
            if cpu > 80:
                issues.append(f"High CPU: {cpu:.1f}%")
            if memory > 85:
                issues.append(f"High Memory: {memory:.1f}%")
            if disk > 90:
                issues.append(f"High Disk: {disk:.1f}%")
            
            if issues:
                self._add_check("System Resources", "WARN", ", ".join(issues))
            else:
                self._add_check("System Resources", "OK", 
                              f"CPU: {cpu:.1f}%, Memory: {memory:.1f}%, Disk: {disk:.1f}%")
        
        except ImportError:
            self._add_check("System Resources", "SKIP", "psutil not available")
    
    def _add_check(self, name: str, status: str, message: str, critical: bool = False):
        """Add a check result."""
        check = {
            'name': name,
            'status': status,
            'message': message
        }
        
        self.status['checks'].append(check)
        
        if critical:
            self.status['critical_issues'].append(f"{name}: {message}")
        elif status == "WARN":
            self.status['warnings'].append(f"{name}: {message}")
        
        # Display check result
        icon = {
            'OK': '✅',
            'WARN': '⚠️',
            'FAIL': '❌',
            'INFO': 'ℹ️',
            'SKIP': '⏭️'
        }.get(status, '❓')
        
        print(f"{icon} {name:.<30} {status:>6} - {message}")
    
    def _determine_overall_status(self):
        """Determine overall system status."""
        if self.status['critical_issues']:
            self.status['overall_status'] = 'CRITICAL'
        elif self.status['warnings']:
            self.status['overall_status'] = 'WARNING'
        else:
            self.status['overall_status'] = 'HEALTHY'
    
    def _display_summary(self):
        """Display status summary."""
        print()
        print("="*80)
        print("  SUMMARY")
        print("="*80)
        
        total_checks = len(self.status['checks'])
        ok_checks = sum(1 for c in self.status['checks'] if c['status'] == 'OK')
        
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {ok_checks}")
        print(f"Warnings: {len(self.status['warnings'])}")
        print(f"Critical Issues: {len(self.status['critical_issues'])}")
        print()
        
        # Overall status
        status_icon = {
            'HEALTHY': '✅',
            'WARNING': '⚠️',
            'CRITICAL': '❌'
        }.get(self.status['overall_status'], '❓')
        
        print(f"Overall Status: {status_icon} {self.status['overall_status']}")
        
        # Critical issues
        if self.status['critical_issues']:
            print()
            print("❌ CRITICAL ISSUES:")
            for issue in self.status['critical_issues']:
                print(f"   - {issue}")
        
        # Warnings
        if self.status['warnings']:
            print()
            print("⚠️ WARNINGS:")
            for warning in self.status['warnings']:
                print(f"   - {warning}")
        
        print("="*80)
        
        # Recommendations
        if self.status['overall_status'] == 'HEALTHY':
            print()
            print("✅ System is ready to run!")
            print("   Use: py production_runner.py")
        elif self.status['overall_status'] == 'WARNING':
            print()
            print("⚠️ System can run but has warnings")
            print("   Review warnings before starting")
        else:
            print()
            print("❌ System has critical issues")
            print("   Fix critical issues before running")
        
        print()
    
    def save_report(self, filename: str = 'logs/status_report.json'):
        """Save status report to file."""
        try:
            os.makedirs('logs', exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(self.status, f, indent=2)
            print(f"📄 Status report saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")


def main():
    """Main entry point."""
    checker = SystemStatusChecker()
    status = checker.check_all()
    checker.save_report()
    
    # Exit code based on status
    if status['overall_status'] == 'CRITICAL':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
