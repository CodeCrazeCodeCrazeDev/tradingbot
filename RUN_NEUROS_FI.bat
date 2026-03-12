@echo off
REM ============================================================================
REM NEUROS-FI Launcher
REM Neuromorphic Adaptive Financial Intelligence Infrastructure
REM Constitutional Version 5.0
REM ============================================================================

title NEUROS-FI Launcher

:MENU
cls
echo ================================================================================
echo NEUROS-FI: NEUROMORPHIC ADAPTIVE FINANCIAL INTELLIGENCE
echo Brain-Topology Trading System - Constitutional Version 5.0
echo ================================================================================
echo.
echo [1] Run NEUROS-FI Demo (Comprehensive)
echo [2] Initialize System Only
echo [3] Run Market Processing Test
echo [4] Run Offline Consolidation
echo [5] Check System Status
echo [6] View Documentation
echo [7] Run Quick Test
echo [8] Exit
echo.
echo ================================================================================
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto DEMO
if "%choice%"=="2" goto INIT
if "%choice%"=="3" goto MARKET_TEST
if "%choice%"=="4" goto CONSOLIDATION
if "%choice%"=="5" goto STATUS
if "%choice%"=="6" goto DOCS
if "%choice%"=="7" goto QUICK_TEST
if "%choice%"=="8" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:DEMO
cls
echo ================================================================================
echo Running NEUROS-FI Comprehensive Demo
echo ================================================================================
echo.
echo This will demonstrate:
echo - 12-step initialization sequence
echo - All 9 brain regions
echo - 5 neural oscillation bands
echo - Market data processing
echo - Core operating principles
echo - Constitutional constraints
echo - Offline consolidation
echo.
pause
python examples\neuros_fi_demo.py
echo.
echo ================================================================================
echo Demo complete!
echo ================================================================================
pause
goto MENU

:INIT
cls
echo ================================================================================
echo Initializing NEUROS-FI System
echo ================================================================================
echo.
python -c "import asyncio; from trading_bot.neuros_fi import quick_start; asyncio.run(quick_start())"
echo.
echo ================================================================================
echo Initialization complete!
echo ================================================================================
pause
goto MENU

:MARKET_TEST
cls
echo ================================================================================
echo Running Market Processing Test
echo ================================================================================
echo.
python -c "import asyncio; from trading_bot.neuros_fi import quick_start; async def test(): o = await quick_start(); r = await o.process_market_data({'symbol': 'EURUSD', 'price': 1.0850, 'volatility': 0.015, 'signals': {'momentum': 0.6}}); print(f'Result: {r}'); asyncio.run(test())"
echo.
echo ================================================================================
echo Market processing test complete!
echo ================================================================================
pause
goto MENU

:CONSOLIDATION
cls
echo ================================================================================
echo Running Offline Consolidation Cycle
echo ================================================================================
echo.
echo This simulates the overnight "sleeping on a problem" cycle where:
echo - Memories are replayed
echo - Prospective scenarios are generated
echo - Cross-domain hypotheses are created
echo - The system becomes smarter
echo.
pause
python -c "import asyncio; from trading_bot.neuros_fi import quick_start; async def test(): o = await quick_start(); r = await o.run_offline_consolidation(); print(f'Consolidation result: {r}'); asyncio.run(test())"
echo.
echo ================================================================================
echo Consolidation complete!
echo ================================================================================
pause
goto MENU

:STATUS
cls
echo ================================================================================
echo NEUROS-FI System Status
echo ================================================================================
echo.
python -c "import asyncio; from trading_bot.neuros_fi import quick_start; async def test(): o = await quick_start(); s = o.get_status(); print('System State:', s['system_state']); print('Inference Mode:', s['inference_mode']); print('Free Energy:', s['free_energy']); print('Brainstem:', s['brainstem']); asyncio.run(test())"
echo.
echo ================================================================================
pause
goto MENU

:DOCS
cls
echo ================================================================================
echo NEUROS-FI Documentation
echo ================================================================================
echo.
echo Opening documentation file...
start NEUROS_FI_COMPLETE.md
echo.
echo Documentation opened in default markdown viewer.
echo.
pause
goto MENU

:QUICK_TEST
cls
echo ================================================================================
echo NEUROS-FI Quick Test
echo ================================================================================
echo.
echo Testing basic functionality...
echo.
python -c "from trading_bot.neuros_fi import __version__; print(f'NEUROS-FI Version: {__version__}'); print('All imports successful!')"
echo.
echo ================================================================================
echo Quick test complete!
echo ================================================================================
pause
goto MENU

:EXIT
cls
echo ================================================================================
echo Thank you for using NEUROS-FI
echo ================================================================================
echo.
echo "The brain is the most complex object in the known universe."
echo "We've reverse-engineered it for trading."
echo.
echo Constitutional Version 5.0
echo.
timeout /t 3 >nul
exit

REM ============================================================================
REM End of NEUROS-FI Launcher
REM ============================================================================
