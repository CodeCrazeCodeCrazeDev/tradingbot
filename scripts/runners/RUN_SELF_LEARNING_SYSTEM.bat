@echo off
REM Self-Learning Trading System Launcher
REM Comprehensive self-learning, self-evolving, and self-optimizing system

color 0A
title Self-Learning Trading System

:MENU
cls
echo ================================================================================
echo                    SELF-LEARNING TRADING SYSTEM
echo ================================================================================
echo.
echo   A comprehensive AI-driven system for market analysis and profit generation
echo.
echo   Features:
echo   - Real-time learning from every trade
echo   - Evolutionary strategy optimization
echo   - Reinforcement learning execution
echo   - Autonomous self-healing
echo   - Distributed knowledge sharing
echo   - Collective intelligence
echo.
echo ================================================================================
echo.
echo   [1] Run Complete Demo (All Features)
echo   [2] Run Basic Usage Demo
echo   [3] Run Continuous Learning Demo (100 trades)
echo   [4] Run System Modes Demo
echo   [5] Run Distributed Learning Demo
echo   [6] Run Self-Healing Demo
echo   [7] Start Live Trading (Paper Mode)
echo   [8] View System Status
echo   [9] View Documentation
echo   [0] Exit
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto DEMO_ALL
if "%choice%"=="2" goto DEMO_BASIC
if "%choice%"=="3" goto DEMO_CONTINUOUS
if "%choice%"=="4" goto DEMO_MODES
if "%choice%"=="5" goto DEMO_DISTRIBUTED
if "%choice%"=="6" goto DEMO_HEALING
if "%choice%"=="7" goto LIVE_TRADING
if "%choice%"=="8" goto STATUS
if "%choice%"=="9" goto DOCS
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:DEMO_ALL
cls
echo ================================================================================
echo                    RUNNING COMPLETE DEMO
echo ================================================================================
echo.
py examples\self_learning_demo.py
echo.
echo ================================================================================
echo                    DEMO COMPLETE
echo ================================================================================
pause
goto MENU

:DEMO_BASIC
cls
echo ================================================================================
echo                    BASIC USAGE DEMO
echo ================================================================================
echo.
py -c "import asyncio; from examples.self_learning_demo import demo_basic_usage; asyncio.run(demo_basic_usage())"
echo.
pause
goto MENU

:DEMO_CONTINUOUS
cls
echo ================================================================================
echo                    CONTINUOUS LEARNING DEMO (100 trades)
echo ================================================================================
echo.
py -c "import asyncio; from examples.self_learning_demo import demo_continuous_learning; asyncio.run(demo_continuous_learning())"
echo.
pause
goto MENU

:DEMO_MODES
cls
echo ================================================================================
echo                    SYSTEM MODES DEMO
echo ================================================================================
echo.
py -c "import asyncio; from examples.self_learning_demo import demo_system_modes; asyncio.run(demo_system_modes())"
echo.
pause
goto MENU

:DEMO_DISTRIBUTED
cls
echo ================================================================================
echo                    DISTRIBUTED LEARNING DEMO
echo ================================================================================
echo.
py -c "import asyncio; from examples.self_learning_demo import demo_distributed_learning; asyncio.run(demo_distributed_learning())"
echo.
pause
goto MENU

:DEMO_HEALING
cls
echo ================================================================================
echo                    SELF-HEALING DEMO
echo ================================================================================
echo.
py -c "import asyncio; from examples.self_learning_demo import demo_self_healing; asyncio.run(demo_self_healing())"
echo.
pause
goto MENU

:LIVE_TRADING
cls
echo ================================================================================
echo                    LIVE TRADING (PAPER MODE)
echo ================================================================================
echo.
echo WARNING: This will start the self-learning system in paper trading mode.
echo Press Ctrl+C to stop at any time.
echo.
pause
echo.
echo Starting system...
py -c "import asyncio; from trading_bot.self_learning import quick_start; asyncio.run(quick_start())"
echo.
pause
goto MENU

:STATUS
cls
echo ================================================================================
echo                    SYSTEM STATUS
echo ================================================================================
echo.
py -c "import asyncio; from trading_bot.self_learning import quick_start; async def show_status(): orch = await quick_start(); status = orch.get_comprehensive_status(); print('System Mode:', status['system_mode']); print('Total Trades:', status['performance']['total_trades']); print('Win Rate:', f\"{status['performance']['win_rate']:.2%%}\"); print('Total Profit:', f\"${status['performance']['total_profit']:.4f}\"); asyncio.run(show_status())"
echo.
pause
goto MENU

:DOCS
cls
echo ================================================================================
echo                    DOCUMENTATION
echo ================================================================================
echo.
echo Opening documentation...
start SELF_LEARNING_SYSTEM_COMPLETE.md
echo.
echo Documentation opened in your default markdown viewer.
echo.
pause
goto MENU

:EXIT
cls
echo ================================================================================
echo                    THANK YOU FOR USING
echo                    SELF-LEARNING TRADING SYSTEM
echo ================================================================================
echo.
echo The system is ready for production use!
echo.
echo Key Features:
echo   - Continuous learning from every trade
echo   - Evolutionary strategy optimization  
echo   - Reinforcement learning execution
echo   - Autonomous self-healing
echo   - Distributed knowledge sharing
echo.
echo For integration help, see: SELF_LEARNING_SYSTEM_COMPLETE.md
echo.
timeout /t 3 >nul
exit
