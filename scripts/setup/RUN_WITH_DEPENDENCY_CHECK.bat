@echo off
REM ============================================================================
REM AlphaAlgo Trading Bot - Run with Automatic Dependency Check
REM ============================================================================
REM This script checks dependencies before starting the bot
REM ============================================================================

echo.
echo ========================================================================
echo   ALPHAALGO TRADING BOT - STARTUP WITH DEPENDENCY CHECK
echo ========================================================================
echo.

cd /d "%~dp0"

REM Run startup checks
echo Running startup checks...
py -m trading_bot.core.startup_checks
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   STARTUP CHECKS FAILED
    echo ========================================================================
    echo.
    echo Please fix the issues above before starting the bot.
    echo.
    echo You can run CHECK_AND_INSTALL_DEPENDENCIES.bat to install missing packages.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   STARTUP CHECKS PASSED - STARTING BOT
echo ========================================================================
echo.

REM Start the bot
py trading_bot/main.py %*

pause
