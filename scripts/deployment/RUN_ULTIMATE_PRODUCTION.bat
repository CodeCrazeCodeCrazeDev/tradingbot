@echo off
title Ultimate Production Trading System
color 0A

echo.
echo ============================================================
echo     ULTIMATE PRODUCTION TRADING SYSTEM
echo     The Absolute Best Trading System
echo ============================================================
echo.

:menu
echo Select Mode:
echo.
echo   [1] Paper Trading (Safe - No Real Money)
echo   [2] Live Trading (REAL MONEY - Use with caution!)
echo   [3] Shadow Mode (Run alongside but don't execute)
echo   [4] Custom Configuration
echo   [5] View Documentation
echo   [6] Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto paper
if "%choice%"=="2" goto live
if "%choice%"=="3" goto shadow
if "%choice%"=="4" goto custom
if "%choice%"=="5" goto docs
if "%choice%"=="6" goto exit

echo Invalid choice. Please try again.
goto menu

:paper
echo.
echo Starting Paper Trading Mode...
echo.
python run_ultimate_production.py --mode paper
pause
goto menu

:live
echo.
echo ============================================================
echo WARNING: LIVE TRADING MODE
echo This will execute REAL trades with REAL money!
echo ============================================================
echo.
set /p confirm="Are you sure? Type YES to confirm: "
if not "%confirm%"=="YES" (
    echo Live trading cancelled.
    pause
    goto menu
)
python run_ultimate_production.py --mode live
pause
goto menu

:shadow
echo.
echo Starting Shadow Mode...
echo (Runs alongside but doesn't execute trades)
echo.
python run_ultimate_production.py --mode shadow
pause
goto menu

:custom
echo.
echo Custom Configuration
echo.
set /p symbols="Enter symbols (space-separated, e.g., EURUSD GBPUSD): "
set /p capital="Enter initial capital (default 10000): "
set /p mode="Enter mode (paper/live/shadow): "

if "%capital%"=="" set capital=10000
if "%mode%"=="" set mode=paper

echo.
echo Running with: symbols=%symbols%, capital=%capital%, mode=%mode%
echo.
python run_ultimate_production.py --mode %mode% --symbols %symbols% --capital %capital%
pause
goto menu

:docs
echo.
echo Opening documentation...
if exist "ULTIMATE_PRODUCTION_COMPLETE.md" (
    start notepad "ULTIMATE_PRODUCTION_COMPLETE.md"
) else (
    echo Documentation not found. Check the docs folder.
)
pause
goto menu

:exit
echo.
echo Thank you for using Ultimate Production Trading System!
echo.
exit /b 0
