import json
#!/usr/bin/env python
"""
Elite Trading Bot - Deployment Script

This script automates the deployment process for the Elite Trading Bot.
It performs system checks, creates necessary directories, and sets up
the required configuration files.
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import logging
import datetime
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment.log")
    ]
)
logger = logging.getLogger("deployment")


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


def create_directories():
    """Create necessary directories"""
    logger.info("Creating necessary directories")
    directories = [
        "logs",
        "data",
        "data/time_series",
        "config",
        "backups"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            logger.info(f"Creating directory: {directory}")
            path.mkdir(parents=True, exist_ok=True)
        else:
            logger.info(f"Directory already exists: {directory}")


def setup_config_files():
    """Set up configuration files"""
    logger.info("Setting up configuration files")
    
    # Check for survival_config.yaml
    config_file = Path("config/survival_config.yaml")
    example_file = Path("config/survival_config.yaml.example")
    
    if not config_file.exists() and example_file.exists():
        logger.info(f"Creating {config_file} from example")
        shutil.copy(example_file, config_file)
    elif not config_file.exists() and not example_file.exists():
        logger.error("No configuration example found")
        return False
    else:
        logger.info(f"Configuration file already exists: {config_file}")
    
    # Check for api_keys.json
    api_keys_file = Path("config/api_keys.json")
    api_keys_example = Path("config/api_keys.json.example")
    
    if not api_keys_file.exists() and api_keys_example.exists():
        logger.info(f"Creating {api_keys_file} from example")
        shutil.copy(api_keys_example, api_keys_file)
    elif not api_keys_file.exists() and not api_keys_example.exists():
        logger.warning("No API keys example found, creating empty file")
        with open(api_keys_file, 'w') as f:
            f.write('{}')
    else:
        logger.info(f"API keys file already exists: {api_keys_file}")
    
    return True


def encrypt_api_keys():
    """Run the API key encryption tool"""
    logger.info("Running API key encryption tool")
    
    # Check if the tool exists
    tool_path = Path("trading_bot/tools/encrypt_api_keys.py")
    if not tool_path.exists():
        logger.error(f"API key encryption tool not found: {tool_path}")
        return False
    
    # Run the tool
    success, output = run_command(f"{sys.executable} -m trading_bot.tools.encrypt_api_keys")
    return success


def run_system_check():
    """Run the system check tool"""
    logger.info("Running system check")
    
    # Check if the tool exists
    tool_path = Path("trading_bot/tools/system_check.py")
    if not tool_path.exists():
        logger.error(f"System check tool not found: {tool_path}")
        return False
    
    # Run the tool
    success, output = run_command(f"{sys.executable} -m trading_bot.tools.system_check")
    return success


def create_backup():
    """Create a backup"""
    logger.info("Creating backup")
    
    # Check if the tool exists
    tool_path = Path("trading_bot/tools/backup.py")
    if not tool_path.exists():
        logger.error(f"Backup tool not found: {tool_path}")
        return False
    
    # Run the tool
    success, output = run_command(f"{sys.executable} -m trading_bot.tools.backup backup")
    return success


def run_tests():
    """Run unit tests"""
    logger.info("Running unit tests")
    
    # Check if tests directory exists
    tests_dir = Path("trading_bot/tests")
    if not tests_dir.exists():
        logger.error(f"Tests directory not found: {tests_dir}")
        return False
    
    # Run the tests
    success, output = run_command(f"{sys.executable} -m unittest discover trading_bot/tests")
    return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Elite Trading Bot - Deployment Script")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-backup", action="store_true", help="Skip creating backup")
    parser.add_argument("--skip-check", action="store_true", help="Skip system check")
    parser.add_argument("--skip-encrypt", action="store_true", help="Skip API key encryption")
    args = parser.parse_args()
    
    logger.info("Starting deployment process")
    logger.info(f"Current time: {datetime.datetime.now()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Create necessary directories
    create_directories()
    
    # Set up configuration files
    if not setup_config_files():
        logger.error("Failed to set up configuration files")
        return 1
    
    # Encrypt API keys
    if not args.skip_encrypt:
        if not encrypt_api_keys():
            logger.error("Failed to encrypt API keys")
            return 1
    else:
        logger.info("Skipping API key encryption")
    
    # Run tests
    if not args.skip_tests:
        if not run_tests():
            logger.error("Tests failed")
            return 1
    else:
        logger.info("Skipping tests")
    
    # Create backup
    if not args.skip_backup:
        if not create_backup():
            logger.error("Failed to create backup")
            return 1
    else:
        logger.info("Skipping backup")
    
    # Run system check
    if not args.skip_check:
        if not run_system_check():
            logger.error("System check failed")
            return 1
    else:
        logger.info("Skipping system check")
    
    logger.info("Deployment completed successfully")
    logger.info("You can now start the trading bot with: python run_survival_system.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
