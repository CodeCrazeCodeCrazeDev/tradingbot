#!/usr/bin/env python
"""
Log Rotation Script for Elite Trading Bot

This script rotates log files to prevent them from growing too large.
It should be run periodically (e.g., daily via cron or Task Scheduler).
"""

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
    """Rotate log files"""
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
                f.write(f"Log rotated at {datetime.datetime.now().isoformat()}\n")
            
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
