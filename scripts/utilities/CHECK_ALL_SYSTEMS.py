"""
Check All Running Systems Status
Real-time monitoring of all trading bot components
"""

import psutil
import sys
from pathlib import Path
from datetime import datetime

def check_running_processes():
    """Check all Python processes related to trading bot"""
    print("=" * 80)
    print("  TRADING BOT SYSTEMS STATUS CHECK")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    bot_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('trading' in str(cmd).lower() or 'bot' in str(cmd).lower() or 'deepseek' in str(cmd).lower() for cmd in cmdline):
                    bot_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if bot_processes:
        print(f"RUNNING PROCESSES: {len(bot_processes)}")
        print()
        for i, proc in enumerate(bot_processes, 1):
            print(f"{i}. PID: {proc['pid']}")
            if proc['cmdline']:
                script = ' '.join(proc['cmdline'][1:3]) if len(proc['cmdline']) > 2 else ' '.join(proc['cmdline'])
                print(f"   Script: {script}")
            print(f"   CPU: {proc['cpu_percent']:.1f}%")
            print(f"   Memory: {proc['memory_percent']:.1f}%")
            print()
    else:
        print("NO TRADING BOT PROCESSES RUNNING")
        print()
    
    # Check log files
    print("=" * 80)
    print("RECENT LOG FILES:")
    print()
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = sorted(logs_dir.rglob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
        for log_file in log_files:
            size = log_file.stat().st_size / 1024  # KB
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  {log_file.relative_to(logs_dir)} ({size:.1f} KB) - {mtime.strftime('%H:%M:%S')}")
    else:
        print("  No logs directory found")
    
    print()
    print("=" * 80)
    
    # System resources
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print("SYSTEM RESOURCES:")
    print(f"  CPU Usage: {cpu:.1f}%")
    print(f"  Memory Usage: {memory.percent:.1f}% ({memory.used / (1024**3):.1f} GB / {memory.total / (1024**3):.1f} GB)")
    print(f"  Disk Usage: {disk.percent:.1f}% ({disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB)")
    print()
    print("=" * 80)
    
    return len(bot_processes)

if __name__ == "__main__":
    try:
        count = check_running_processes()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
