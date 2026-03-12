@echo off
title MOSEFS - Meta-Orchestrated Self-Evolving Financial Superintelligence
color 0A

echo ========================================================================
echo  MOSEFS - Meta-Orchestrated Self-Evolving Financial Superintelligence
echo  The Ultimate Ceiling Architecture for Adaptive Financial AI
echo ========================================================================
echo.
echo  7-Layer Architecture:
echo    Layer 7: CONSCIOUSNESS - Self-Aware Market Intelligence
echo    Layer 6: EVOLUTION - Autonomous Self-Improvement Engine
echo    Layer 5: INTELLIGENCE - Cross-Domain Knowledge Synthesis
echo    Layer 4: LEARNING - Meta-Learning ^& Adaptation
echo    Layer 3: DISCOVERY - Autonomous Strategy Generation
echo    Layer 2: EXECUTION - Ultra-Fast Trading Operations
echo    Layer 1: INFRASTRUCTURE - Quantum-Neural Computing Foundation
echo.
echo ========================================================================
echo.
echo  Select an option:
echo.
echo    1. Run MOSEFS Demo (showcase all 7 layers)
echo    2. Run MOSEFS in Paper Mode
echo    3. Run MOSEFS in Research Mode
echo    4. Check System Status
echo    5. Exit
echo.
echo ========================================================================
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto paper
if "%choice%"=="3" goto research
if "%choice%"=="4" goto status
if "%choice%"=="5" goto exit

echo Invalid choice. Please try again.
pause
goto :eof

:demo
echo.
echo Starting MOSEFS Demo...
echo.
py examples/mosefs_demo.py
pause
goto :eof

:paper
echo.
echo Starting MOSEFS in Paper Mode...
echo.
py -c "import asyncio; from trading_bot.mosefs import quick_start; asyncio.run(quick_start({'mode': 'paper'}))"
pause
goto :eof

:research
echo.
echo Starting MOSEFS in Research Mode...
echo.
py -c "import asyncio; from trading_bot.mosefs import quick_start; asyncio.run(quick_start({'mode': 'research'}))"
pause
goto :eof

:status
echo.
echo Checking MOSEFS Status...
echo.
py -c "from trading_bot.mosefs import create_mosefs; m = create_mosefs(); print(f'State: {m.get_state().name}'); print(f'Mode: {m.get_mode().name}')"
pause
goto :eof

:exit
echo.
echo Goodbye!
exit /b 0
