@echo off
title AlphaAlgo Unified Trading System - 175+ Modules
color 0A

echo.
echo ===============================================================================
echo                    ALPHAALGO UNIFIED TRADING SYSTEM
echo                         Version 2.0 - 175+ Modules
echo ===============================================================================
echo.
echo IMMUTABLE PRINCIPLES:
echo   1. RISK FIRST: Layer 4 (MSOS) has VETO power over all trades
echo   2. HUMAN CONTROL: Human override ALWAYS works
echo   3. FAIL-SAFE: Default to NO TRADE when uncertain
echo   4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
echo.
echo ===============================================================================
echo.

:MENU
echo Select an option:
echo.
echo   [1] Run in SIMULATION mode (safe testing)
echo   [2] Run in PAPER mode (no real money)
echo   [3] Run in LIVE mode (REAL TRADING - USE WITH CAUTION!)
echo   [4] Dry run (load modules only, no trading)
echo   [5] Show system status
echo   [6] Run with custom symbols
echo   [7] Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto SIMULATION
if "%choice%"=="2" goto PAPER
if "%choice%"=="3" goto LIVE
if "%choice%"=="4" goto DRYRUN
if "%choice%"=="5" goto STATUS
if "%choice%"=="6" goto CUSTOM
if "%choice%"=="7" goto EXIT

echo Invalid choice. Please try again.
goto MENU

:SIMULATION
echo.
echo Starting in SIMULATION mode...
echo.
python run_unified_system.py --mode simulation --verbose
goto END

:PAPER
echo.
echo Starting in PAPER mode...
echo.
python run_unified_system.py --mode paper --verbose
goto END

:LIVE
echo.
echo ===============================================================================
echo                              WARNING - LIVE TRADING
echo ===============================================================================
echo.
echo You are about to start LIVE TRADING with REAL MONEY!
echo.
echo Risk Limits:
echo   - Max Position Size: 10%%
echo   - Max Risk Per Trade: 2%%
echo   - Max Daily Loss: 5%%
echo   - Max Drawdown: 20%%
echo   - Max Leverage: 3x
echo.
set /p confirm="Are you sure you want to continue? (yes/no): "
if /i "%confirm%"=="yes" (
    echo.
    echo Starting in LIVE mode...
    python run_unified_system.py --mode live --verbose
) else (
    echo.
    echo Live trading cancelled.
)
goto END

:DRYRUN
echo.
echo Running dry run (load modules only)...
echo.
python run_unified_system.py --mode paper --dry-run --verbose
goto END

:STATUS
echo.
echo Checking system status...
echo.
python -c "import asyncio; from trading_bot.unified_master_integrator import UnifiedMasterIntegrator; i = UnifiedMasterIntegrator(); i.print_status_report()"
goto END

:CUSTOM
echo.
set /p symbols="Enter symbols (comma-separated, e.g., BTCUSDT,ETHUSD,EURUSD): "
set /p mode="Enter mode (simulation/paper/live): "
set /p capital="Enter initial capital (default 100000): "
if "%capital%"=="" set capital=100000
echo.
echo Starting with custom configuration...
python run_unified_system.py --mode %mode% --symbols %symbols% --capital %capital% --verbose
goto END

:EXIT
echo.
echo Goodbye!
exit /b 0

:END
echo.
echo ===============================================================================
echo System stopped. Press any key to return to menu...
pause >nul
cls
goto MENU
