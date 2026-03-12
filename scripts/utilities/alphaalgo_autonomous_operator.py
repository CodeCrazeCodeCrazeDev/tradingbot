"""
AlphaAlgo Autonomous Operator
==============================
Fully autonomous trading bot operator with self-healing, monitoring, and optimization.
Designed for non-coders - runs completely automatically.

Author: AI System Engineer
Version: 1.0.0
"""

import os
import sys
import time
import json
import psutil
import logging
import asyncio
import subprocess
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests
from loguru import logger

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)
logger.add(
    LOG_DIR / "alphaalgo_operator_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG"
)


@dataclass
class SystemHealth:
    """System health metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    internet_latency_ms: Optional[float]
    bot_running: bool
    errors_count: int
    warnings_count: int
    status: str  # "healthy", "degraded", "critical"


@dataclass
class TradingMetrics:
    """Trading performance metrics"""
    timestamp: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    profit_loss: float
    win_rate: float
    current_positions: int
    max_drawdown: float


class AlphaAlgoOperator:
    """Autonomous operator for AlphaAlgo trading bot"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.state_file = self.root_dir / "operator_state.json"
        self.learning_log = LOG_DIR / "learning_history.log"
        self.bot_process = None
        self.state = self._load_state()
        self.safe_mode = False
        self.restart_count = 0
        self.max_restarts = 5
        
    def _load_state(self) -> Dict:
        """Load operator state from disk"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                    return json.load(f)
        return {
            "start_time": datetime.now().isoformat(),
            "total_runtime_hours": 0,
            "total_trades": 0,
            "total_profit_loss": 0.0,
            "restarts": 0,
            "errors_fixed": 0,
            "last_health_check": None,
            "performance_adjustments": []
        }
    
    def _save_state(self):
        """Save operator state to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def check_internet(self) -> Tuple[bool, Optional[float]]:
        """Check internet connectivity and latency"""
        try:
            start = time.time()
            response = requests.get("https://www.google.com", timeout=5)
            latency = (time.time() - start) * 1000
            return response.status_code == 200, latency
        except:
            return False, None
    
    def check_system_resources(self) -> Dict:
        """Check CPU, memory, and disk usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "cpu_count": psutil.cpu_count(),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3)
        }
    
    def check_required_files(self) -> List[str]:
        """Check if all required files exist"""
        required_files = [
            "main.py",
            "requirements.txt",
            ".env",
            "config/testing_config.yaml",
            "trading_bot/__init__.py"
        ]
        
        missing = []
        for file_path in required_files:
            if not (self.root_dir / file_path).exists():
                missing.append(file_path)
        
        return missing
    
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Validate environment variables and configuration"""
        issues = []
        
        # Check .env file
        env_file = self.root_dir / ".env"
        if not env_file.exists():
            issues.append(".env file missing")
            return False, issues
        
        # Check critical env vars
        from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(env_file)
        
critical_vars = ["MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"]
for var in critical_vars:
            if not os.getenv(var):
                issues.append(f"Missing environment variable: {var}")
        
return len(issues) == 0, issues
    
def run_system_diagnostic(self) -> SystemHealth:
        """Run complete system diagnostic"""
        logger.info("🔍 Running system diagnostic...")
        
        # Check internet
        internet_ok, latency = self.check_internet()
        if not internet_ok:
            logger.warning("⚠️ Internet connection issue detected")
        
        # Check resources
        resources = self.check_system_resources()
        
        # Determine status
        status = "healthy"
        errors = 0
        warnings = 0
        
        if resources["cpu_percent"] > 90:
            logger.warning(f"⚠️ High CPU usage: {resources['cpu_percent']}%")
            warnings += 1
            status = "degraded"
        
        if resources["memory_percent"] > 85:
            logger.warning(f"⚠️ High memory usage: {resources['memory_percent']}%")
            warnings += 1
            status = "degraded"
        
        if not internet_ok:
            errors += 1
            status = "critical"
        
        if latency and latency > 200:
            logger.warning(f"⚠️ High latency: {latency:.0f}ms")
            warnings += 1
        
        # Check files
        missing_files = self.check_required_files()
        if missing_files:
            logger.error(f"❌ Missing files: {missing_files}")
            errors += len(missing_files)
            status = "critical"
        
        # Check environment
        env_ok, env_issues = self.validate_environment()
        if not env_ok:
            logger.error(f"❌ Environment issues: {env_issues}")
            errors += len(env_issues)
            status = "critical"
        
        health = SystemHealth(
            timestamp=datetime.now().isoformat(),
            cpu_percent=resources["cpu_percent"],
            memory_percent=resources["memory_percent"],
            disk_percent=resources["disk_percent"],
            internet_latency_ms=latency,
            bot_running=self.is_bot_running(),
            errors_count=errors,
            warnings_count=warnings,
            status=status
        )
        
        logger.info(f"✅ Diagnostic complete: {status.upper()}")
        return health
    
def is_bot_running(self) -> bool:
        """Check if trading bot is running"""
        if self.bot_process and self.bot_process.poll() is None:
            return True
        return False
    
def start_bot(self) -> bool:
        """Start the trading bot"""
        logger.info("🚀 Starting AlphaAlgo trading bot...")
        
        try:
            # Use the main.py file
            bot_script = self.root_dir / "main.py"
            
            if not bot_script.exists():
                logger.error("❌ main.py not found")
                return False
            
            # Start bot process
            self.bot_process = subprocess.Popen(
                [sys.executable, str(bot_script)],
                cwd=str(self.root_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait a bit to see if it starts successfully
            time.sleep(5)
            
            if self.bot_process.poll() is None:
                logger.info("✅ AlphaAlgo started successfully")
                self.restart_count = 0
                return True
            else:
                # Process died immediately
                stdout, stderr = self.bot_process.communicate()
                logger.error(f"❌ Bot failed to start:\n{stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            logger.error(traceback.format_exc())
            return False
    
def stop_bot(self):
        """Stop the trading bot gracefully"""
        if self.bot_process:
            logger.info("🛑 Stopping AlphaAlgo...")
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                logger.info("✅ AlphaAlgo stopped")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Force killing bot process")
                self.bot_process.kill()
            except Exception as e:
                logger.error(f"❌ Error stopping bot: {e}")
    
def restart_bot(self):
        """Restart the trading bot"""
        logger.info("🔄 Restarting AlphaAlgo...")
        self.stop_bot()
        time.sleep(2)
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ Max restarts ({self.max_restarts}) reached. Entering safe mode.")
            self.safe_mode = True
            return False
        
        self.restart_count += 1
        self.state["restarts"] += 1
        return self.start_bot()
    
def monitor_bot_logs(self) -> Tuple[int, int]:
        """Monitor bot logs for errors and warnings"""
        errors = 0
        warnings = 0
        
        try:
            log_files = list(LOG_DIR.glob("*.log"))
            if not log_files:
                return 0, 0
            
            # Check most recent log
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            
            # Read last 100 lines with proper encoding handling
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-100:]
            
            for line in lines:
                if "ERROR" in line or "CRITICAL" in line:
                    errors += 1
                elif "WARNING" in line:
                    warnings += 1
            
        except Exception as e:
            # Silently handle log reading errors
            pass
        
        return errors, warnings
    
def auto_fix_issues(self, health: SystemHealth) -> int:
        """Automatically fix detected issues"""
        fixes_applied = 0
        
        # High CPU - restart bot
        if health.cpu_percent > 95:
            logger.warning("🔧 High CPU detected - restarting bot")
            if self.restart_bot():
                fixes_applied += 1
        
        # High memory - restart bot
        if health.memory_percent > 90:
            logger.warning("🔧 High memory usage - restarting bot")
            if self.restart_bot():
                fixes_applied += 1
        
        # Bot not running - start it
        if not health.bot_running and not self.safe_mode:
            logger.warning("🔧 Bot not running - starting it")
            if self.start_bot():
                fixes_applied += 1
        
        # Internet issues - wait and retry
        if health.internet_latency_ms is None:
            logger.warning("🔧 Internet down - entering safe mode")
            self.safe_mode = True
            self.stop_bot()
        
        self.state["errors_fixed"] += fixes_applied
        return fixes_applied
    
def generate_hourly_report(self) -> str:
        """Generate hourly performance report"""
        health = self.run_system_diagnostic()
        
        latency_str = f"{health.internet_latency_ms:.0f}ms" if health.internet_latency_ms else "N/A"
        bot_status = "Yes" if health.bot_running else "No"
        safe_mode_str = "ACTIVE" if self.safe_mode else "Normal"
        
        report = f"""
==============================================================
           AlphaAlgo Hourly Status Report                     
==============================================================

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SYSTEM HEALTH
  Status: {health.status.upper()}
  CPU: {health.cpu_percent:.1f}%
  Memory: {health.memory_percent:.1f}%
  Disk: {health.disk_percent:.1f}%
  Latency: {latency_str}
  Bot Running: {bot_status}

ISSUES
  Errors: {health.errors_count}
  Warnings: {health.warnings_count}

OPERATOR STATS
  Total Runtime: {self.state['total_runtime_hours']:.1f} hours
  Restarts: {self.state['restarts']}
  Errors Fixed: {self.state['errors_fixed']}
  Safe Mode: {safe_mode_str}

==============================================================
"""
        return report
    
async def run_continuous_operation(self):
        """Main continuous operation loop"""
        logger.info("🤖 AlphaAlgo Autonomous Operator Starting...")
        logger.info("=" * 60)
        
        # Initial diagnostic
        health = self.run_system_diagnostic()
        
        if health.status == "critical":
            logger.error("❌ Critical issues detected. Cannot start bot.")
            logger.error("Please fix the following issues:")
            if health.errors_count > 0:
                logger.error(f"  - {health.errors_count} critical errors")
            return
        
        # Start the bot
        if not self.start_bot():
            logger.error("❌ Failed to start bot. Exiting.")
            return
        
        logger.info("✅ AlphaAlgo is now running autonomously")
        logger.info("=" * 60)
        
        last_hourly_report = datetime.now()
        last_health_check = datetime.now()
        
        try:
            while True:
                # Health check every 5 minutes
                if datetime.now() - last_health_check > timedelta(minutes=5):
                    health = self.run_system_diagnostic()
                    
                    # Auto-fix issues
                    if health.status != "healthy":
                        fixes = self.auto_fix_issues(health)
                        if fixes > 0:
                            logger.info(f"🔧 Applied {fixes} automatic fixes")
                    
                    last_health_check = datetime.now()
                    self.state["last_health_check"] = last_health_check.isoformat()
                    self._save_state()
                
                # Hourly report
                if datetime.now() - last_hourly_report > timedelta(hours=1):
                    report = self.generate_hourly_report()
                    logger.info(report)
                    last_hourly_report = datetime.now()
                    
                    # Update runtime
                    self.state["total_runtime_hours"] += 1
                    self._save_state()
                
                # Check if bot is still running
                if not self.is_bot_running() and not self.safe_mode:
                    logger.warning("⚠️ Bot stopped unexpectedly - restarting")
                    self.restart_bot()
                
                # Monitor logs
                errors, warnings = self.monitor_bot_logs()
                if errors > 10:
                    logger.warning(f"⚠️ High error count ({errors}) - may need intervention")
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested by user")
            self.stop_bot()
            self._save_state()
            logger.info("✅ AlphaAlgo shutdown complete")
        except Exception as e:
            logger.error(f"❌ Operator error: {e}")
            logger.error(traceback.format_exc())
            self.stop_bot()
            self._save_state()


def main():
    """Main entry point"""
    print("""
    ==============================================================
                                                              
              AlphaAlgo Autonomous Operator                   
                                                              
      Fully automated trading bot management system               
      - Automatic startup and monitoring                          
      - Self-healing and error recovery                           
      - Performance optimization                                  
      - Continuous operation                                      
                                                              
    ==============================================================
    """)
    
    operator = AlphaAlgoOperator()
    asyncio.run(operator.run_continuous_operation())


if __name__ == "__main__":
    main()
