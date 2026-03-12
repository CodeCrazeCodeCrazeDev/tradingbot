"""
AlphaAlgo Status Checker
========================
Quick status check for AlphaAlgo trading bot.
Shows current health, performance, and system metrics.
"""

import json
import psutil
import time
from pathlib import Path
from datetime import datetime
import subprocess

def check_bot_running():
    """Check if Python processes are running (likely the bot)"""
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('main.py' in str(cmd) or 'alphaalgo' in str(cmd).lower() for cmd in cmdline):
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.cpu_percent(interval=0.1),
                        'memory': proc.memory_percent()
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return python_processes

def get_system_health():
    """Get current system health metrics"""
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'memory_available_gb': psutil.virtual_memory().available / (1024**3)
    }

def load_operator_state():
    """Load operator state if it exists"""
    state_file = Path("operator_state.json")
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def get_latest_log_entries(log_dir, count=10):
    """Get latest log entries"""
    log_path = Path(log_dir)
    if not log_path.exists():
        return []
    
    log_files = list(log_path.glob("alphaalgo_operator_*.log"))
    if not log_files:
        return []
    
    latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return lines[-count:]
    except:
        return []

def main():
    """Main status check"""
    print("\n" + "="*70)
    print("           AlphaAlgo Trading Bot - Status Check")
    print("="*70)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if bot is running
    print("BOT STATUS")
    print("-" * 70)
    bot_processes = check_bot_running()
    if bot_processes:
        print(f"Status: RUNNING ({len(bot_processes)} process(es))")
        for proc in bot_processes:
            print(f"  PID {proc['pid']}: CPU {proc['cpu']:.1f}%, Memory {proc['memory']:.1f}%")
    else:
        print("Status: NOT RUNNING")
    
    # System health
    print("\nSYSTEM HEALTH")
    print("-" * 70)
    health = get_system_health()
    print(f"CPU Usage: {health['cpu_percent']:.1f}%")
    print(f"Memory Usage: {health['memory_percent']:.1f}%")
    print(f"Memory Available: {health['memory_available_gb']:.2f} GB")
    print(f"Disk Usage: {health['disk_percent']:.1f}%")
    
    # Operator state
    print("\nOPERATOR STATISTICS")
    print("-" * 70)
    state = load_operator_state()
    if state:
        print(f"Total Runtime: {state.get('total_runtime_hours', 0):.1f} hours")
        print(f"Total Trades: {state.get('total_trades', 0)}")
        print(f"Total P/L: ${state.get('total_profit_loss', 0):.2f}")
        print(f"Restarts: {state.get('restarts', 0)}")
        print(f"Errors Fixed: {state.get('errors_fixed', 0)}")
        if state.get('last_health_check'):
            print(f"Last Health Check: {state['last_health_check']}")
    else:
        print("No operator state file found (operator may not have run yet)")
    
    # Recent log entries
    print("\nRECENT LOG ENTRIES")
    print("-" * 70)
    logs = get_latest_log_entries("logs", count=5)
    if logs:
        for log in logs:
            # Remove emojis and special characters for console compatibility
            clean_log = log.encode('ascii', 'ignore').decode('ascii').strip()
            if clean_log:
                print(clean_log)
    else:
        print("No recent logs found")
    
    print("\n" + "="*70)
    print("\nTo start AlphaAlgo: Run START_ALPHAALGO.bat")
    print("To view full logs: Check logs/alphaalgo_operator_*.log")
    print("To stop AlphaAlgo: Press Ctrl+C in the operator window")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
