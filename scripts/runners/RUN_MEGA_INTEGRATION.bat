@echo off
title MEGA INTEGRATION - Ultimate Trading System
color 0A

echo ========================================================================
echo                    MEGA INTEGRATION SYSTEM
echo                  Ultimate Unified Trading Bot
echo ========================================================================
echo.
echo  150+ Modules | 300+ Features | 100,000+ Lines of Code
echo.
echo ========================================================================
echo.

:menu
echo Select an option:
echo.
echo   [1] Run MEGA System (Paper Mode)
echo   [2] Run MEGA System (Simulation Mode)
echo   [3] Run MEGA System (Backtest Mode)
echo   [4] Run with Quantum Computing
echo   [5] Run with Blockchain/DeFi
echo   [6] Run Full System (All Features)
echo   [7] Check System Status
echo   [8] Run Demo
echo   [9] Exit
echo.

set /p choice="Enter choice (1-9): "

if "%choice%"=="1" goto paper
if "%choice%"=="2" goto simulation
if "%choice%"=="3" goto backtest
if "%choice%"=="4" goto quantum
if "%choice%"=="5" goto blockchain
if "%choice%"=="6" goto full
if "%choice%"=="7" goto status
if "%choice%"=="8" goto demo
if "%choice%"=="9" goto exit

echo Invalid choice. Please try again.
goto menu

:paper
echo.
echo Starting MEGA System in Paper Mode...
echo.
py -m trading_bot.mega_integration --mode paper --symbols BTCUSDT ETHUSDT EURUSD
goto end

:simulation
echo.
echo Starting MEGA System in Simulation Mode...
echo.
py -m trading_bot.mega_integration --mode simulation --symbols BTCUSDT ETHUSDT
goto end

:backtest
echo.
echo Starting MEGA System in Backtest Mode...
echo.
py -m trading_bot.mega_integration --mode backtest --symbols BTCUSDT
goto end

:quantum
echo.
echo Starting MEGA System with Quantum Computing...
echo.
py -m trading_bot.mega_integration --mode paper --quantum --symbols BTCUSDT ETHUSDT
goto end

:blockchain
echo.
echo Starting MEGA System with Blockchain/DeFi...
echo.
py -m trading_bot.mega_integration --mode paper --blockchain --symbols BTCUSDT ETHUSDT
goto end

:full
echo.
echo Starting MEGA System with ALL Features...
echo.
py -m trading_bot.mega_integration --mode paper --quantum --blockchain --symbols BTCUSDT ETHUSDT EURUSD GBPUSD USDJPY
goto end

:status
echo.
echo Checking System Status...
echo.
py -c "from trading_bot.mega_integration import create_mega_system; s = create_mega_system(); print('Modules:', len(s.modules)); print('Active:', len(s.active_modules)); print('Failed:', len(s.failed_modules)); print('Health:', s.health.value)"
echo.
pause
goto menu

:demo
echo.
echo Running MEGA Integration Demo...
echo.
py examples\mega_integration_demo.py
goto end

:exit
echo.
echo Goodbye!
exit /b 0

:end
echo.
echo ========================================================================
echo MEGA Integration System Stopped
echo ========================================================================
pause
