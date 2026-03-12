#!/usr/bin/env python
"""
Elite Trading Bot - Production Deployment Script

This script automates the production deployment process for the Elite Trading Bot.
It performs final checks, creates backups, and sets up the system for production use.
"""

import os
import sys
import shutil
import argparse
import logging
import datetime
import subprocess
import time
from pathlib import Path
import yaml
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("production_deployment.log")
    ]
)
logger = logging.getLogger("production_deployment")


def run_command(command, cwd=None):
    """Run a command and return the output"""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False, e.stderr


def run_deployment_check():
    """Run the deployment check script"""
    logger.info("Running deployment check...")
    success, output = run_command(f"{sys.executable} final_deployment_check.py")
    if not success:
        logger.error("Deployment check failed")
        return False
    
    if "Final Result: PASS" not in output:
        logger.error("Deployment check did not pass")
        return False
    
    logger.info("Deployment check passed")
    return True


def create_backup():
    """Create a backup of the current state"""
    logger.info("Creating backup...")
    
    # Create backup directory if it doesn't exist
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamp for backup name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"elite_trading_bot_backup_{timestamp}"
    backup_path = backup_dir / backup_name
    
    # Create backup directory
    backup_path.mkdir()
    
    # Copy critical files and directories
    critical_dirs = [
        "config",
        "trading_bot",
        "examples"
    ]
    
    critical_files = [
        "requirements.txt",
        "run_survival_system.py",
        "deploy.py",
        "start_trading_bot.bat",
        "start_trading_bot.sh",
        "DEPLOYMENT_GUIDE.md",
        "PRE_DEPLOYMENT_CHECKLIST.md",
        "README.md"
    ]
    
    # Copy directories
    for dir_name in critical_dirs:
        src_dir = Path(dir_name)
        dst_dir = backup_path / dir_name
        if src_dir.exists():
            shutil.copytree(src_dir, dst_dir)
            logger.info(f"Copied directory {dir_name} to backup")
    
    # Copy files
    for file_name in critical_files:
        src_file = Path(file_name)
        dst_file = backup_path / file_name
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            logger.info(f"Copied file {file_name} to backup")
    
    # Create backup info file
    info_file = backup_path / "backup_info.txt"
    with open(info_file, 'w') as f:
        f.write(f"Elite Trading Bot Backup\n")
        f.write(f"Created: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Python version: {sys.version}\n")
        f.write(f"Platform: {sys.platform}\n")
    
    logger.info(f"Backup created at {backup_path}")
    return str(backup_path)


def setup_production_config():
    """Set up production configuration"""
    logger.info("Setting up production configuration...")
    
    # Load example config
    config_example = Path("config/survival_config.yaml.example")
    config_prod = Path("config/survival_config_production.yaml")
    
    if not config_example.exists():
        logger.error("Example configuration file not found")
        return False
    
    # Load example config
    with open(config_example, 'r') as f:
        config = yaml.safe_load(f)
    
    # Add features section if it doesn't exist
    if 'features' not in config:
        config['features'] = {}
    
    # Modify for production
    config['features']['use_ai_predictions'] = True
    config['features']['use_sentiment_analysis'] = True
    config['features']['use_advanced_execution'] = True
    config['features']['use_multi_timeframe'] = True
    config['features']['use_correlation_protection'] = True
    config['features']['use_adaptive_position_sizing'] = True
    
    # Set conservative risk limits for production
    config['risk_limits']['max_position_size'] = 0.01  # 1% of account
    config['risk_limits']['max_daily_loss'] = 0.03  # 3% max daily loss
    config['risk_limits']['max_drawdown'] = 0.10  # 10% maximum drawdown
    config['risk_limits']['max_open_positions'] = 3  # Maximum 3 open positions
    
    # Add emergency section if it doesn't exist
    if 'emergency' not in config:
        config['emergency'] = {}
    
    # Enable emergency controls
    config['emergency']['pause_on_high_spread'] = True
    config['emergency']['pause_on_high_volatility'] = True
    config['emergency']['pause_on_news'] = True
    config['emergency']['pause_on_critical_error'] = True
    
    # Save production config
    with open(config_prod, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Production configuration saved to {config_prod}")
    return True


def create_production_launcher():
    """Create production launcher script"""
    logger.info("Creating production launcher script...")
    
    # Windows batch file
    win_launcher = Path("start_production.bat")
    with open(win_launcher, 'w') as f:
        f.write("@echo off\n")
        f.write("echo Elite Trading Bot - Production Launcher\n")
        f.write("echo ===================================\n")
        f.write("echo.\n")
        f.write("python run_survival_system.py --config config/survival_config_production.yaml --risk-level conservative\n")
        f.write("pause\n")
    
    # Linux/Mac shell script
    unix_launcher = Path("start_production.sh")
    with open(unix_launcher, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("echo \"Elite Trading Bot - Production Launcher\"\n")
        f.write("echo \"===================================\"\n")
        f.write("echo\n")
        f.write("python run_survival_system.py --config config/survival_config_production.yaml --risk-level conservative\n")
    
    # Make shell script executable on Unix-like systems
    if os.name != 'nt':
        os.chmod(unix_launcher, 0o755)
    
    logger.info("Production launcher scripts created")
    return True


def setup_logging_rotation():
    """Set up log rotation for production"""
    logger.info("Setting up log rotation...")
    
    # Create log directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create tools directory if it doesn't exist
    tools_dir = Path("tools")
    tools_dir.mkdir(exist_ok=True)
    
    # Create log rotation script
    log_script = Path("tools/rotate_logs.py")
    
    with open(log_script, 'w') as f:
        f.write("""#!/usr/bin/env python
\"\"\"
Log Rotation Script for Elite Trading Bot

This script rotates log files to prevent them from growing too large.
It should be run periodically (e.g., daily via cron or Task Scheduler).
\"\"\"

import os
import sys
import glob
import time
import shutil
from pathlib import Path
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/log_rotation.log")
    ]
)
logger = logging.getLogger("log_rotation")

# Configuration
MAX_LOG_SIZE_MB = 10
MAX_LOG_AGE_DAYS = 30
MAX_LOGS_PER_TYPE = 10
LOG_DIR = "logs"


def rotate_logs():
    \"\"\"Rotate log files\"\"\"
    log_dir = Path(LOG_DIR)
    if not log_dir.exists():
        logger.error(f"Log directory {log_dir} does not exist")
        return False
    
    # Get all log files
    log_files = list(log_dir.glob("*.log"))
    
    # Process each log file
    for log_file in log_files:
        # Skip the rotation log itself
        if log_file.name == "log_rotation.log":
            continue
        
        # Check file size
        size_mb = log_file.stat().st_size / (1024 * 1024)
        if size_mb > MAX_LOG_SIZE_MB:
            # Rotate the log
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = log_file.with_name(f"{log_file.stem}_{timestamp}{log_file.suffix}")
            shutil.copy2(log_file, new_name)
            
            # Truncate the original log
            with open(log_file, 'w') as f:
                f.write(f"Log rotated at {datetime.datetime.now().isoformat()}\\n")
            
            logger.info(f"Rotated {log_file} to {new_name}")
    
    # Clean up old log files
    for log_pattern in ["*_*.log"]:
        pattern_files = sorted(
            log_dir.glob(log_pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Keep only the most recent files
        if len(pattern_files) > MAX_LOGS_PER_TYPE:
            for old_file in pattern_files[MAX_LOGS_PER_TYPE:]:
                # Check file age
                file_age_days = (time.time() - old_file.stat().st_mtime) / (86400)
                if file_age_days > MAX_LOG_AGE_DAYS:
                    old_file.unlink()
                    logger.info(f"Deleted old log file {old_file}")
    
    logger.info("Log rotation completed")
    return True


if __name__ == "__main__":
    rotate_logs()
""")
    
    # Make script executable on Unix-like systems
    if os.name != 'nt':
        os.chmod(log_script, 0o755)
    
    logger.info("Log rotation script created")
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Elite Trading Bot - Production Deployment")
    parser.add_argument("--skip-check", action="store_true", help="Skip deployment check")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--force", action="store_true", help="Force deployment even if checks fail")
    args = parser.parse_args()
    
    print("Elite Trading Bot - Production Deployment")
    print("=======================================")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run deployment check
    if not args.skip_check:
        check_passed = run_deployment_check()
        if not check_passed and not args.force:
            logger.error("Deployment check failed. Use --force to deploy anyway.")
            return 1
    
    # Create backup
    if not args.skip_backup:
        backup_path = create_backup()
        logger.info(f"Backup created at {backup_path}")
    
    # Set up production configuration
    if not setup_production_config():
        logger.error("Failed to set up production configuration")
        return 1
    
    # Create production launcher
    if not create_production_launcher():
        logger.error("Failed to create production launcher")
        return 1
    
    # Set up log rotation
    if not setup_logging_rotation():
        logger.error("Failed to set up log rotation")
        return 1
    
    print("\nProduction Deployment Summary:")
    print("============================")
    print("✓ Deployment check completed")
    if not args.skip_backup:
        print("✓ Backup created")
    print("✓ Production configuration created")
    print("✓ Production launcher scripts created")
    print("✓ Log rotation set up")
    
    print("\nThe Elite Trading Bot is now ready for production use!")
    print("To start the bot in production mode, run:")
    print("  Windows: start_production.bat")
    print("  Linux/Mac: ./start_production.sh")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
