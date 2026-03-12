@echo off
REM ============================================================================
REM AlphaAlgo Trading Bot - Install ALL Dependencies (Required + Optional)
REM ============================================================================
REM This script installs ALL 34 dependencies including optional ones
REM ============================================================================

echo.
echo ========================================================================
echo   ALPHAALGO - INSTALL ALL DEPENDENCIES
echo ========================================================================
echo.
echo This will install ALL 34 dependencies:
echo   - 14 Required packages
echo   - 20 Optional packages
echo.
echo This may take 5-10 minutes depending on your internet speed.
echo.
pause

cd /d "%~dp0"

REM Check Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo [1/3] Upgrading pip...
py -m pip install --upgrade pip

echo.
echo [2/3] Installing ALL dependencies (this may take several minutes)...
py -c "from trading_bot.core.dependency_manager import AutoDependencyManager; import logging; logging.basicConfig(level=logging.INFO, format='%%(message)s'); print('\n'); manager = AutoDependencyManager(auto_install=True, auto_update=False); manager.ensure_dependencies(install_optional=True); print('\n'); manager.print_report(); manager.save_report()"

echo.
echo [3/3] Installation complete!
echo.
echo ========================================================================
echo   INSTALLATION SUMMARY
echo ========================================================================
echo.
echo Check dependency_report.json for detailed status.
echo.
echo Note: Some packages (d3rlpy, prophet) may fail on some systems.
echo This is normal and won't affect the bot's core functionality.
echo.
echo You can now run the bot with:
echo   - RUN_WITH_DEPENDENCY_CHECK.bat
echo   - python trading_bot/main.py
echo.
pause
