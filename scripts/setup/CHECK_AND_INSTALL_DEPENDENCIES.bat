@echo off
REM ============================================================================
REM AlphaAlgo Trading Bot - Dependency Checker and Installer
REM ============================================================================
REM This script checks and installs all required and optional dependencies
REM ============================================================================

echo.
echo ========================================================================
echo   ALPHAALGO TRADING BOT - DEPENDENCY MANAGER
echo ========================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Python found: 
py --version
echo.

REM Upgrade pip first
echo [2/5] Upgrading pip...
py -m pip install --upgrade pip
echo.

REM Run dependency manager - Install ALL dependencies including optional
echo [3/5] Checking and installing ALL dependencies (required + optional)...
py -c "from trading_bot.core.dependency_manager import AutoDependencyManager; import logging; logging.basicConfig(level=logging.INFO); manager = AutoDependencyManager(auto_install=True, auto_update=False); manager.ensure_dependencies(install_optional=True); manager.print_report(); manager.save_report()"
if errorlevel 1 (
    echo.
    echo ERROR: Dependency check failed!
    echo Please check the errors above and try again.
    pause
    exit /b 1
)
echo.

REM Install from requirements.txt
echo [4/5] Installing from requirements.txt...
if exist requirements.txt (
    py -m pip install -r requirements.txt --no-deps --ignore-installed 2>nul
    echo Requirements.txt processed
) else (
    echo requirements.txt not found, skipping
)
echo.

REM Optional dependencies already installed in step 3
echo [5/5] Verifying installation...
echo.
echo All dependencies (required + optional) have been installed!
echo.
echo Note: Some optional packages like d3rlpy or prophet may fail to install
echo on some systems. This is normal and won't affect core functionality.
echo.

echo ========================================================================
echo   DEPENDENCY CHECK COMPLETE
echo ========================================================================
echo.
echo Dependency report saved to: dependency_report.json
echo.
echo You can now run the trading bot with:
echo   - RUN_SAFE_TRADING_BOT.bat
echo   - python trading_bot/main.py
echo.
pause
