@echo off
REM Recursive Self-Evolution System Launcher
REM ==========================================

echo.
echo ================================================================================
echo RECURSIVE SELF-EVOLUTION SYSTEM
echo ================================================================================
echo.
echo This system continuously improves ALL aspects of the trading bot:
echo   - Elite trader reasoning and decision-making
echo   - Deep market intelligence and research
echo   - Institutional order flow detection
echo   - Multi-paradigm decision fusion
echo   - Continuous self-improvement across 30+ dimensions
echo.
echo ================================================================================
echo.

:MENU
echo.
echo Select an option:
echo.
echo   1. Run Demo (Comprehensive demonstration)
echo   2. Run Single Evolution Cycle
echo   3. Start Continuous Evolution
echo   4. Generate Trading Signal
echo   5. View Evolution Status
echo   6. Export Evolution Report
echo   7. View Documentation
echo   8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto DEMO
if "%choice%"=="2" goto SINGLE_CYCLE
if "%choice%"=="3" goto CONTINUOUS
if "%choice%"=="4" goto SIGNAL
if "%choice%"=="5" goto STATUS
if "%choice%"=="6" goto REPORT
if "%choice%"=="7" goto DOCS
if "%choice%"=="8" goto EXIT

echo Invalid choice. Please try again.
goto MENU

:DEMO
echo.
echo Running comprehensive demo...
echo.
py examples/recursive_evolution_demo.py
echo.
pause
goto MENU

:SINGLE_CYCLE
echo.
echo Running single evolution cycle...
echo.
py -c "import asyncio; from trading_bot.recursive_evolution import RecursiveEvolutionOrchestrator; asyncio.run(RecursiveEvolutionOrchestrator().run_evolution_cycle())"
echo.
pause
goto MENU

:CONTINUOUS
echo.
echo Starting continuous evolution (press Ctrl+C to stop)...
echo.
py -c "import asyncio; from trading_bot.recursive_evolution import quick_start; orchestrator = asyncio.run(quick_start({'auto_start': True, 'evolution_interval': 3600})); print('Evolution running...'); asyncio.run(asyncio.sleep(3600))"
echo.
pause
goto MENU

:SIGNAL
echo.
echo Generating trading signal...
echo.
py -c "import asyncio; from trading_bot.recursive_evolution import RecursiveEvolutionOrchestrator; import numpy as np; orchestrator = RecursiveEvolutionOrchestrator(); market_data = {'symbol': 'EURUSD', 'price': 1.1000, 'prices': list(np.random.randn(100).cumsum() + 1.1000), 'volumes': list(np.random.randint(1000, 10000, 100))}; signal = asyncio.run(orchestrator.generate_trading_signal('EURUSD', market_data)); print(f'Decision: {signal.final_decision.value}'); print(f'Confidence: {signal.confidence.overall_confidence:.2%%}'); print(f'Recommendation: {signal.recommended_action}')"
echo.
pause
goto MENU

:STATUS
echo.
echo Viewing evolution status...
echo.
py -c "from trading_bot.recursive_evolution import RecursiveEvolutionOrchestrator; orchestrator = RecursiveEvolutionOrchestrator(); status = orchestrator.get_evolution_status(); import json; print(json.dumps(status, indent=2, default=str))"
echo.
pause
goto MENU

:REPORT
echo.
echo Exporting evolution report...
echo.
py -c "from trading_bot.recursive_evolution import RecursiveEvolutionOrchestrator; orchestrator = RecursiveEvolutionOrchestrator(); orchestrator.export_evolution_report('recursive_evolution_report.json'); print('Report exported to: recursive_evolution_report.json')"
echo.
pause
goto MENU

:DOCS
echo.
echo Opening documentation...
echo.
start docs\RECURSIVE_EVOLUTION_COMPLETE.md
goto MENU

:EXIT
echo.
echo Exiting...
echo.
exit /b 0
