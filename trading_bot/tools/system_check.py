#!/usr/bin/env python
"""
from typing import Optional
System Check Tool

This tool performs diagnostic checks on the Elite Trading Bot system
to ensure it's properly configured and ready for deployment.
"""

import os
import sys
import importlib
import platform
import socket
import json
import yaml
from pathlib import Path
import time

# Add parent directory to path to allow importing from trading_bot
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Required packages for the trading bot
REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "pyyaml",
    "loguru",
    "requests",
    "aiohttp",
    "websockets",
    "python-dotenv",
    "click",
    "tabulate",
    "pytrends",
    "MetaTrader5",
    "ta-lib",
    "sqlalchemy",
    "aiosqlite",
    "pydantic",
    "psutil",
    "python-telegram-bot",
    "cryptography"
]

# Optional packages that enhance functionality
OPTIONAL_PACKAGES = [
    "scikit-learn",
    "scipy",
    "statsmodels",
    "matplotlib",
    "seaborn",
    "tensorflow",
    "torch",
    "transformers",
    "dash",
    "plotly",
    "redis",
    "pymongo",
    "qiskit"
]

# Required configuration files
REQUIRED_CONFIG_FILES = [
    "config/survival_config.yaml",
    "config/api_keys.json",
    "config/encryption.key"
]

# Required directories
REQUIRED_DIRECTORIES = [
    "logs",
    "data",
    "data/time_series"
]


def check_python_version():
    """Check Python version"""
    print("\n=== Python Version ===")
    version = platform.python_version()
    print(f"Python version: {version}")
    
    major, minor, _ = map(int, version.split('.'))
    if major < 3 or (major == 3 and minor < 9):
        print("❌ Python 3.9+ is recommended")
        return False
    else:
        print("[+] Python version is compatible")
        return True


def check_packages():
    """Check required packages"""
    print("\n=== Package Check ===")
    
    all_required_installed = True
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"[+] {package} is installed")
        except ImportError:
            print(f"[-] {package} is NOT installed")
            all_required_installed = False
    
    print("\n=== Optional Packages ===")
    for package in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"[+] {package} is installed")
        except ImportError:
            print(f"[!] {package} is NOT installed (optional)")
    
    return all_required_installed


def check_config_files():
    """Check configuration files"""
    print("\n=== Configuration Files ===")
    
    all_configs_exist = True
    for config_file in REQUIRED_CONFIG_FILES:
        path = Path(config_file)
        if path.exists():
            print(f"[+] {config_file} exists")
            
            # Check if it's a valid YAML or JSON file
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                try:
                    with open(path, 'r') as f:
                        yaml.safe_load(f)
                    print(f"  [+] {config_file} is valid YAML")
                except Exception as e:
                    print(f"  [-] {config_file} is NOT valid YAML: {e}")
                    all_configs_exist = False
            
            elif config_file.endswith('.json'):
                try:
                    with open(path, 'r') as f:
                        json.load(f)
                    print(f"  [+] {config_file} is valid JSON")
                except Exception as e:
                    print(f"  [-] {config_file} is NOT valid JSON: {e}")
                    all_configs_exist = False
        else:
            print(f"[-] {config_file} does NOT exist")
            all_configs_exist = False
    
    return all_configs_exist


def check_directories():
    """Check required directories"""
    print("\n=== Directories ===")
    
    all_dirs_exist = True
    for directory in REQUIRED_DIRECTORIES:
        path = Path(directory)
        if path.exists() and path.is_dir():
            print(f"[+] {directory} exists")
        else:
            print(f"[-] {directory} does NOT exist")
            all_dirs_exist = False
    
    return all_dirs_exist


def check_network():
    """Check network connectivity"""
    print("\n=== Network Connectivity ===")
    
    # Check internet connectivity
    hosts = [
        ("google.com", 80),
        ("api.binance.com", 443),
        ("api.alpaca.markets", 443)
    ]
    
    all_connections_ok = True
    for host, port in hosts:
        try:
            socket.create_connection((host, port), timeout=5)
            print(f"[+] Connection to {host}:{port} successful")
        except Exception as e:
            print(f"[-] Connection to {host}:{port} failed: {e}")
            all_connections_ok = False
    
    return all_connections_ok


def check_mt5():
    """Check MetaTrader 5 connectivity"""
    print("\n=== MetaTrader 5 Check ===")
    
    try:
        import MetaTrader5 as mt5
        
        # Initialize MT5
        if not mt5.initialize():
            print(f"[-] MetaTrader 5 initialization failed: {mt5.last_error()}")
            return False
        
        print("[+] MetaTrader 5 initialized successfully")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            print("[-] Failed to get terminal info")
            mt5.shutdown()
            return False
        
        print(f"[+] Connected to MetaTrader 5 terminal (build {terminal_info.build})")
        print(f"  Path: {terminal_info.path}")
        print(f"  Connected: {'Yes' if terminal_info.connected else 'No'}")
        
        # Shutdown MT5
        mt5.shutdown()
        return True
        
    except ImportError:
        print("[!] MetaTrader 5 package not installed")
        return False
    except Exception as e:
        print(f"[-] MetaTrader 5 check failed: {e}")
        return False


def check_system_resources():
    """Check system resources"""
    print("\n=== System Resources ===")
    
    try:
        import psutil
        
        # CPU info
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"CPU: {cpu_physical} physical cores, {cpu_count} logical cores")
        print(f"CPU Usage: {cpu_percent}%")
        
        # Memory info
        memory = psutil.virtual_memory()
        print(f"Memory: {memory.total / (1024**3):.2f} GB total")
        print(f"Memory Usage: {memory.percent}%")
        
        # Disk info
        disk = psutil.disk_usage('/')
        print(f"Disk: {disk.total / (1024**3):.2f} GB total")
        print(f"Disk Usage: {disk.percent}%")
        
        # Check if resources are sufficient
        all_resources_ok = True
        
        if cpu_count < 2:
            print("[!] Recommended at least 2 CPU cores")
            all_resources_ok = False
        
        if memory.total < 4 * (1024**3):  # 4 GB
            print("[!] Recommended at least 4 GB of RAM")
            all_resources_ok = False
        
        if disk.free < 5 * (1024**3):  # 5 GB
            print("[!] Less than 5 GB of free disk space")
            all_resources_ok = False
        
        return all_resources_ok
        
    except ImportError:
        print("[!] psutil package not installed, skipping system resource check")
        return True
    except Exception as e:
        print(f"[-] System resource check failed: {e}")
        return False


def main():
    """Main function"""
    print("Elite Trading Bot - System Check Tool")
    print("=====================================")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"System: {platform.system()} {platform.release()}")
    
    # Run checks
    python_ok = check_python_version()
    packages_ok = check_packages()
    config_ok = check_config_files()
    dirs_ok = check_directories()
    network_ok = check_network()
    mt5_ok = check_mt5()
    resources_ok = check_system_resources()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Python Version: {'[+]' if python_ok else '[-]'}")
    print(f"Required Packages: {'[+]' if packages_ok else '[-]'}")
    print(f"Configuration Files: {'[+]' if config_ok else '[-]'}")
    print(f"Directories: {'[+]' if dirs_ok else '[-]'}")
    print(f"Network Connectivity: {'[+]' if network_ok else '[-]'}")
    print(f"MetaTrader 5: {'[+]' if mt5_ok else '[!]'}")
    print(f"System Resources: {'[+]' if resources_ok else '[!]'}")
    
    # Overall status
    critical_checks = [python_ok, packages_ok, config_ok, dirs_ok]
    if all(critical_checks):
        print("\n[+] System is ready for deployment!")
        if not all([network_ok, mt5_ok, resources_ok]):
            print("[!] Some non-critical checks failed, review warnings above")
    else:
        print("\n[-] System is NOT ready for deployment")
        print("Please fix the issues marked with [-] above")


if __name__ == "__main__":
    main()
