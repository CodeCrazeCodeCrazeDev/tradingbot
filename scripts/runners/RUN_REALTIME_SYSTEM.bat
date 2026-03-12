@echo off
title AlphaAlgo Real-Time Trading System
color 0A

:MENU
cls
echo ============================================================
echo   ALPHAALGO REAL-TIME TRADING SYSTEM
echo ============================================================
echo.
echo   1. Fix All Dependencies (run first if issues)
echo   2. Validate System
echo   3. Run Real-Time Trading (Paper Mode)
echo   4. Run Real-Time Trading (Simulation)
echo   5. Run System Health Check
echo   6. Run Dependency Manager
echo   7. Exit
echo.
set /p choice="Select option (1-7): "

if "%choice%"=="1" goto FIX_DEPS
if "%choice%"=="2" goto VALIDATE
if "%choice%"=="3" goto RUN_PAPER
if "%choice%"=="4" goto RUN_SIM
if "%choice%"=="5" goto HEALTH
if "%choice%"=="6" goto DEP_MANAGER
if "%choice%"=="7" goto EXIT
goto MENU

:FIX_DEPS
echo.
echo [INFO] Fixing all dependencies...
py "%~dp0FIX_ALL_REALTIME.py"
pause
goto MENU

:VALIDATE
echo.
echo [INFO] Validating system...
py "%~dp0trading_bot\realtime_system_validator.py" --validate
pause
goto MENU

:RUN_PAPER
echo.
echo [INFO] Starting Real-Time Trading (Paper Mode)...
echo [INFO] Press Ctrl+C to stop
echo.
py "%~dp0trading_bot\realtime_trading_core.py" --mode paper --symbols BTCUSDT ETHUSDT
pause
goto MENU

:RUN_SIM
echo.
echo [INFO] Starting Real-Time Trading (Simulation Mode)...
echo [INFO] Press Ctrl+C to stop
echo.
py "%~dp0trading_bot\realtime_trading_core.py" --mode simulation --symbols BTCUSDT ETHUSDT
pause
goto MENU

:HEALTH
echo.
echo [INFO] Running health check...
py -c "import asyncio; from trading_bot.realtime_system_validator import run_health_check; import json; print(json.dumps(asyncio.run(run_health_check()), indent=2))"
pause
goto MENU

:DEP_MANAGER
echo.
echo [INFO] Running dependency manager...
py "%~dp0trading_bot\realtime_dependency_manager.py" --all
pause
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0
