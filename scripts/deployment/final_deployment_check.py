#!/usr/bin/env python
"""
Elite Trading Bot - Final Deployment Check

This script performs a final check to ensure the trading bot is ready for deployment.
It checks for the existence of critical files and directories without importing modules.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import yaml
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment_check.log")
    ]
)
logger = logging.getLogger("deployment_check")

# Critical files to check
CRITICAL_FILES = [
    "config/survival_config.yaml",
    "config/survival_config.yaml.example",
    "config/api_keys.json.example",
    "run_survival_system.py",
    "deploy.py",
    "start_trading_bot.bat",
    "start_trading_bot.sh",
    "DEPLOYMENT_GUIDE.md",
    "PRE_DEPLOYMENT_CHECKLIST.md",
    "trading_bot/core/__init__.py",
    "trading_bot/core/survival_core.py",
    "trading_bot/core/analysis_orchestrator.py",
    "trading_bot/core/execution_manager.py",
    "trading_bot/core/monitoring_system.py",
    "trading_bot/data/__init__.py",
    "trading_bot/data/market_data_stream.py",
    "trading_bot/data/time_series_db.py",
    "trading_bot/tools/__init__.py",
    "trading_bot/tools/encrypt_api_keys.py",
    "trading_bot/tools/system_check.py",
    "trading_bot/tools/backup.py",
    "trading_bot/tests/test_survival_core.py"
]

# Critical directories to check
CRITICAL_DIRS = [
    "logs",
    "data/time_series",
    "config",
    "trading_bot/core",
    "trading_bot/data",
    "trading_bot/tools",
    "trading_bot/tests",
    "trading_bot/analysis",
    "examples"
]

def check_critical_files():
    """Check if critical files exist"""
    logger.info("Checking critical files...")
    
    all_files_ok = True
    missing_files = []
    
    for file_path in CRITICAL_FILES:
        path = Path(file_path)
        if path.exists():
            logger.info(f"[PASS] File {file_path} exists")
            
            # Check if it's a YAML or JSON file
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                try:
                    with open(path, 'r') as f:
                        yaml.safe_load(f)
                    logger.info(f"  [PASS] {file_path} is valid YAML")
                except Exception as e:
                    logger.error(f"  [FAIL] {file_path} is NOT valid YAML: {e}")
                    all_files_ok = False
            
            elif file_path.endswith('.json'):
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    logger.info(f"  [PASS] {file_path} is valid JSON")
                except Exception as e:
                    logger.error(f"  [FAIL] {file_path} is NOT valid JSON: {e}")
                    all_files_ok = False
        else:
            logger.error(f"[FAIL] File {file_path} does NOT exist")
            missing_files.append(file_path)
            all_files_ok = False
    
    return all_files_ok, missing_files


def check_critical_dirs():
    """Check if critical directories exist"""
    logger.info("Checking critical directories...")
    
    all_dirs_ok = True
    missing_dirs = []
    
    for dir_path in CRITICAL_DIRS:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            logger.info(f"[PASS] Directory {dir_path} exists")
        else:
            logger.error(f"[FAIL] Directory {dir_path} does NOT exist")
            missing_dirs.append(dir_path)
            all_dirs_ok = False
    
    return all_dirs_ok, missing_dirs


def check_config_structure():
    """Check if configuration structure is valid"""
    logger.info("Checking configuration structure...")
    
    config_path = Path("config/survival_config.yaml")
    if not config_path.exists():
        config_path = Path("config/survival_config.yaml.example")
        if not config_path.exists():
            logger.error("[FAIL] No configuration file found")
            return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for required sections
        required_sections = [
            "symbols",
            "timeframes",
            "risk_limits",
            "security",
            "monitoring"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in config:
                logger.warning(f"[WARN] Configuration is missing section: {section}")
                missing_sections.append(section)
        
        if not missing_sections:
            logger.info("[PASS] Configuration contains all required sections")
        
        # Check security section specifically
        if "security" in config:
            security = config["security"]
            if "key_rotation_days" in security:
                logger.info(f"[PASS] Key rotation is configured ({security['key_rotation_days']} days)")
            else:
                logger.warning("[WARN] Key rotation is not configured")
        
        return True, missing_sections
        
    except Exception as e:
        logger.error(f"[FAIL] Error checking configuration: {e}")
        return False, ["configuration_error"]


def check_deployment_guide():
    """Check if deployment guide is comprehensive"""
    logger.info("Checking deployment guide...")
    
    guide_path = Path("DEPLOYMENT_GUIDE.md")
    if not guide_path.exists():
        logger.error(f"[FAIL] Deployment guide does not exist at {guide_path}")
        return False
    
    with open(guide_path, 'r') as f:
        content = f.read()
    
    # Check for key sections
    required_sections = [
        "Prerequisites",
        "Installation",
        "Configuration",
        "Security",
        "Running",
        "Monitoring",
        "Troubleshooting"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section.lower() not in content.lower():
            logger.warning(f"[WARN] Deployment guide is missing section: {section}")
            missing_sections.append(section)
    
    if not missing_sections:
        logger.info("[PASS] Deployment guide contains all required sections")
    
    return True, missing_sections


def main():
    """Main function"""
    print("Elite Trading Bot - Final Deployment Check")
    print("=========================================")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Run checks
    files_ok, missing_files = check_critical_files()
    dirs_ok, missing_dirs = check_critical_dirs()
    config_ok, missing_sections = check_config_structure()
    guide_ok, missing_guide_sections = check_deployment_guide()
    
    # Print summary
    print("\nDeployment Check Summary:")
    print("=======================")
    
    print(f"Critical Files: {'PASS' if files_ok else 'FAIL'}")
    if not files_ok:
        print(f"  Missing files: {', '.join(missing_files)}")
    
    print(f"Critical Directories: {'PASS' if dirs_ok else 'FAIL'}")
    if not dirs_ok:
        print(f"  Missing directories: {', '.join(missing_dirs)}")
    
    print(f"Configuration Structure: {'PASS' if config_ok else 'FAIL'}")
    if missing_sections:
        print(f"  Missing sections: {', '.join(missing_sections)}")
    
    print(f"Deployment Guide: {'PASS' if guide_ok else 'FAIL'}")
    if missing_guide_sections:
        print(f"  Missing sections: {', '.join(missing_guide_sections)}")
    
    # Final result
    all_checks_passed = files_ok and dirs_ok and config_ok and guide_ok
    print("\nFinal Result:", "PASS" if all_checks_passed else "FAIL")
    
    if all_checks_passed:
        print("\nThe Elite Trading Bot is ready for deployment!")
        print("Please follow the instructions in DEPLOYMENT_GUIDE.md to deploy the system.")
    else:
        print("\nThe Elite Trading Bot is NOT ready for deployment.")
        print("Please fix the issues above before proceeding with deployment.")
    
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    sys.exit(main())
