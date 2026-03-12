@echo off
title AlphaAlgo Real-Time Trading System
color 0A

echo ============================================================
echo     ALPHAALGO REAL-TIME TRADING SYSTEM
echo     Version 3.0.0 - Full Real-Time Architecture
echo ============================================================
echo.

:MENU
echo Select an option:
echo.
echo   [1] Run Real-Time Trading (Paper Mode)
echo   [2] Run Real-Time Trading (Simulation Mode)
echo   [3] Run Real-Time Trading (Live Mode - CAUTION!)
echo   [4] Run Demo (30 seconds)
echo   [5] Validate System
echo   [6] Check Dependencies
echo   [7] View Documentation
echo   [8] Exit
echo.

set /p choice="Enter choice (1-8): "

if "%choice%"=="1" goto PAPER
if "%choice%"=="2" goto SIMULATION
if "%choice%"=="3" goto LIVE
if "%choice%"=="4" goto DEMO
if "%choice%"=="5" goto VALIDATE
if "%choice%"=="6" goto DEPS
if "%choice%"=="7" goto DOCS
if "%choice%"=="8" goto EXIT

echo Invalid choice. Please try again.
goto MENU

:PAPER
echo.
echo Starting Real-Time Trading in PAPER mode...
echo.
python -m trading_bot.realtime.realtime_orchestrator --mode paper --symbols BTCUSDT ETHUSDT
goto END

:SIMULATION
echo.
echo Starting Real-Time Trading in SIMULATION mode...
echo.
python -m trading_bot.realtime.realtime_orchestrator --mode simulation --symbols BTCUSDT ETHUSDT
goto END

:LIVE
echo.
echo ============================================================
echo     WARNING: LIVE TRADING MODE
echo     Real money will be at risk!
echo ============================================================
echo.
set /p confirm="Type 'YES' to confirm live trading: "
if not "%confirm%"=="YES" (
    echo Live trading cancelled.
    goto MENU
)
echo.
echo Starting Real-Time Trading in LIVE mode...
python -m trading_bot.realtime.realtime_orchestrator --mode live --symbols BTCUSDT ETHUSDT
goto END

:DEMO
echo.
echo Running 30-second demo...
echo.
python -m trading_bot.realtime.realtime_orchestrator --mode simulation --symbols BTCUSDT --duration 30
echo.
echo Demo complete!
goto MENU

:VALIDATE
echo.
echo Validating Real-Time System...
echo.
python -c "import asyncio; from trading_bot.realtime import create_realtime_system; s = create_realtime_system(); asyncio.run(s.initialize()); print('Validation PASSED - All components initialized successfully')"
echo.
pause
goto MENU

:DEPS
echo.
echo Checking dependencies...
echo.
python -c "import websockets; print('websockets:', websockets.__version__)"
python -c "import aiohttp; print('aiohttp:', aiohttp.__version__)"
python -c "import numpy; print('numpy:', numpy.__version__)"
python -c "import asyncio; print('asyncio: OK')"
echo.
pause
goto MENU

:DOCS
echo.
echo Opening documentation...
start "" "REALTIME_TRADING_COMPLETE.md"
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0

:END
echo.
echo Real-Time Trading System stopped.
pause
goto MENU
