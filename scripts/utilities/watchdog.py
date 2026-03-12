"""
Trading Bot Watchdog - Continuous Monitoring and Auto-Restart
Monitors the bot, auto-restarts on crash, logs incidents and recoveries.
"""

import subprocess
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import psutil

class TradingBotWatchdog:
    """Monitors and manages the trading bot process"""
    
    def __init__(self, bot_script="main.py", restart_delay=10, max_restarts_per_hour=5):
        self.bot_script = bot_script
        self.restart_delay = restart_delay
        self.max_restarts_per_hour = max_restarts_per_hour
        self.restart_history = []
        self.process = None
        self.log_file = Path("logs/watchdog.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def start_bot(self):
        """Start the trading bot process"""
        try:
            self.log("Starting trading bot...")
            
            # Start bot as subprocess
            self.process = subprocess.Popen(
                [sys.executable, self.bot_script, "--mode", "paper", "--symbol", "EURUSD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.log(f"Bot started with PID: {self.process.pid}")
            return True
            
        except Exception as e:
            self.log(f"Failed to start bot: {e}", "ERROR")
            return False
    
    def is_bot_running(self):
        """Check if bot process is still running"""
        if self.process is None:
            return False
        
        # Check if process is still alive
        poll = self.process.poll()
        return poll is None
    
    def check_restart_limit(self):
        """Check if restart limit has been exceeded"""
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        # Remove old restart records
        self.restart_history = [t for t in self.restart_history if t > one_hour_ago]
        
        if len(self.restart_history) >= self.max_restarts_per_hour:
            self.log(
                f"Restart limit exceeded: {len(self.restart_history)} restarts in last hour",
                "ERROR"
            )
            return False
        
        return True
    
    def restart_bot(self):
        """Restart the bot after a crash"""
        if not self.check_restart_limit():
            self.log("Too many restarts. Stopping watchdog.", "ERROR")
            return False
        
        self.log(f"Waiting {self.restart_delay} seconds before restart...")
        time.sleep(self.restart_delay)
        
        # Record restart time
        self.restart_history.append(time.time())
        
        # Start bot
        return self.start_bot()
    
    def get_bot_stats(self):
        """Get bot process statistics"""
        if not self.is_bot_running():
            return None
        
        try:
            proc = psutil.Process(self.process.pid)
            stats = {
                'cpu_percent': proc.cpu_percent(interval=1),
                'memory_mb': proc.memory_info().rss / 1024 / 1024,
                'num_threads': proc.num_threads(),
                'status': proc.status()
            }
            return stats
        except:
            return None
    
    def monitor(self):
        """Main monitoring loop"""
        self.log("="*60)
        self.log("TRADING BOT WATCHDOG STARTED")
        self.log("="*60)
        self.log(f"Bot script: {self.bot_script}")
        self.log(f"Restart delay: {self.restart_delay}s")
        self.log(f"Max restarts/hour: {self.max_restarts_per_hour}")
        self.log("="*60)
        
        # Initial start
        if not self.start_bot():
            self.log("Failed to start bot initially. Exiting.", "ERROR")
            return
        
        check_interval = 5  # Check every 5 seconds
        stats_interval = 60  # Log stats every 60 seconds
        last_stats_time = time.time()
        
        try:
            while True:
                time.sleep(check_interval)
                
                # Check if bot is running
                if not self.is_bot_running():
                    exit_code = self.process.poll()
                    self.log(f"Bot crashed with exit code: {exit_code}", "ERROR")
                    
                    # Attempt restart
                    if not self.restart_bot():
                        self.log("Watchdog stopping due to restart limit.", "ERROR")
                        break
                
                # Log stats periodically
                current_time = time.time()
                if current_time - last_stats_time >= stats_interval:
                    stats = self.get_bot_stats()
                    if stats:
                        self.log(
                            f"Bot stats - CPU: {stats['cpu_percent']:.1f}%, "
                            f"Memory: {stats['memory_mb']:.1f}MB, "
                            f"Threads: {stats['num_threads']}, "
                            f"Status: {stats['status']}"
                        )
                    last_stats_time = current_time
        
        except KeyboardInterrupt:
            self.log("Watchdog stopped by user (Ctrl+C)")
            if self.process and self.is_bot_running():
                self.log("Terminating bot process...")
                self.process.terminate()
                self.process.wait(timeout=10)
        
        except Exception as e:
            self.log(f"Watchdog error: {e}", "ERROR")
        
        finally:
            self.log("Watchdog shutdown complete")

def main():
    """Run the watchdog"""
    watchdog = TradingBotWatchdog(
        bot_script="main.py",
        restart_delay=10,
        max_restarts_per_hour=5
    )
    
    watchdog.monitor()

if __name__ == "__main__":
    main()
