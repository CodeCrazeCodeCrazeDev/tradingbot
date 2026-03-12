@echo off
title AlphaAlgo Trading Bot - Full System
color 0A

echo ======================================================
echo   ALPHAALGO TRADING BOT - FULL SYSTEM LAUNCHER
echo ======================================================
echo.
echo   [1] Start FULL System (All 4 Layers)
echo   [2] Start Trading Only (Layer 1)
echo   [3] Start Background Services Only (Layer 2)
echo   [4] Start Scheduled Jobs Only (Layer 3)
echo   [5] Run Scheduled Job NOW
echo   [6] Check System Status
echo   [7] Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" (
    echo.
    echo Starting FULL system with all 4 layers...
    echo.
    py master_runner.py --full -- --symbol EURUSD --mode paper
) else if "%choice%"=="2" (
    echo.
    echo Starting Trading Only...
    echo.
    py main.py --symbol EURUSD --mode paper --use-all-systems
) else if "%choice%"=="3" (
    echo.
    echo Starting Background Services...
    echo.
    py background_services.py --start-all
) else if "%choice%"=="4" (
    echo.
    echo Starting Scheduled Jobs...
    echo.
    py scheduled_jobs_runner.py --schedule
) else if "%choice%"=="5" (
    echo.
    echo Available jobs:
    echo   - offline_rl
    echo   - adversarial
    echo   - neural_evolution
    echo   - pattern_discovery
    echo   - performance
    echo   - model_retraining
    echo   - strategy_optimization
    echo   - data_cleanup
    echo.
    set /p job="Enter job name: "
    py scheduled_jobs_runner.py --run-now %job%
) else if "%choice%"=="6" (
    echo.
    echo Checking system status...
    echo.
    py master_runner.py --status
) else if "%choice%"=="7" (
    exit
) else (
    echo Invalid choice
)

echo.
pause
