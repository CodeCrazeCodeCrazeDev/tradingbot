@echo off
title AlphaAlgo Event Pipeline
color 0A

echo.
echo ============================================================
echo     AlphaAlgo Real-Time Event Pipeline
echo ============================================================
echo.
echo     Consistent - Replayable - Fault-Tolerant - Scalable
echo.
echo ============================================================
echo.

:menu
echo Select an option:
echo.
echo   1. Run Event Pipeline Demo
echo   2. Run Quick Start Example
echo   3. View Documentation
echo   4. Exit
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto quickstart
if "%choice%"=="3" goto docs
if "%choice%"=="4" goto exit

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running Event Pipeline Demo...
echo.
py examples\event_pipeline_demo.py
echo.
pause
goto menu

:quickstart
echo.
echo Running Quick Start Example...
echo.
py -c "import asyncio; from trading_bot.event_pipeline import quick_start, create_event, EventType; asyncio.run((lambda: __import__('asyncio').get_event_loop().run_until_complete(quick_start()))())"
echo.
pause
goto menu

:docs
echo.
echo Opening documentation...
start "" "EVENT_PIPELINE_COMPLETE.md"
goto menu

:exit
echo.
echo Goodbye!
exit /b 0
