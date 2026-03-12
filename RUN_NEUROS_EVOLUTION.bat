@echo off
REM NEUROS Evolution: Autonomous Financial Intelligence Infrastructure
REM Windows Launcher Script

echo ================================================================================
echo NEUROS EVOLUTION: Autonomous Financial Intelligence Infrastructure
echo ================================================================================
echo.
echo Building on NEUROS-FI brain topology with:
echo   - Autonomous research agents
echo   - Self-rewiring network infrastructure
echo   - Autonomous organization management
echo   - Continuous evolution engine
echo.
echo ================================================================================
echo.

:MENU
echo Please select an option:
echo.
echo 1. Run Full Demo (All Features)
echo 2. Run Research Agents Demo
echo 3. Run Adaptive Network Demo
echo 4. Run Autonomous Organization Demo
echo 5. Run Evolution Engine Demo
echo 6. Start Autonomous System (Background Evolution)
echo 7. View System Documentation
echo 8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto FULL_DEMO
if "%choice%"=="2" goto RESEARCH_DEMO
if "%choice%"=="3" goto NETWORK_DEMO
if "%choice%"=="4" goto ORG_DEMO
if "%choice%"=="5" goto EVOLUTION_DEMO
if "%choice%"=="6" goto START_SYSTEM
if "%choice%"=="7" goto VIEW_DOCS
if "%choice%"=="8" goto EXIT

echo Invalid choice. Please try again.
echo.
goto MENU

:FULL_DEMO
echo.
echo ================================================================================
echo Running Full NEUROS Evolution Demo...
echo ================================================================================
echo.
python examples/neuros_evolution_demo.py
echo.
echo Demo completed!
echo.
pause
goto MENU

:RESEARCH_DEMO
echo.
echo ================================================================================
echo Running Research Agents Demo...
echo ================================================================================
echo.
python -c "import asyncio; from examples.neuros_evolution_demo import demo_research_agents, quick_start; orchestrator = quick_start(); asyncio.run(orchestrator.initialize()); asyncio.run(demo_research_agents(orchestrator))"
echo.
pause
goto MENU

:NETWORK_DEMO
echo.
echo ================================================================================
echo Running Adaptive Network Demo...
echo ================================================================================
echo.
python -c "import asyncio; from examples.neuros_evolution_demo import demo_adaptive_network, quick_start; orchestrator = quick_start(); asyncio.run(orchestrator.initialize()); asyncio.run(demo_adaptive_network(orchestrator))"
echo.
pause
goto MENU

:ORG_DEMO
echo.
echo ================================================================================
echo Running Autonomous Organization Demo...
echo ================================================================================
echo.
python -c "import asyncio; from examples.neuros_evolution_demo import demo_autonomous_organization, quick_start; orchestrator = quick_start(); asyncio.run(orchestrator.initialize()); asyncio.run(demo_autonomous_organization(orchestrator))"
echo.
pause
goto MENU

:EVOLUTION_DEMO
echo.
echo ================================================================================
echo Running Evolution Engine Demo...
echo ================================================================================
echo.
python -c "import asyncio; from examples.neuros_evolution_demo import demo_evolution_engine, quick_start; orchestrator = quick_start(); asyncio.run(orchestrator.initialize()); asyncio.run(demo_evolution_engine(orchestrator))"
echo.
pause
goto MENU

:START_SYSTEM
echo.
echo ================================================================================
echo Starting Autonomous NEUROS Evolution System...
echo ================================================================================
echo.
echo WARNING: This will start background evolution loops that continuously:
echo   - Generate and test hypotheses
echo   - Optimize network topology
echo   - Rebalance capital allocation
echo   - Evolve system architecture
echo   - Improve core capabilities
echo.
set /p confirm="Are you sure you want to start autonomous evolution? (Y/N): "

if /i "%confirm%"=="Y" (
    echo.
    echo Starting autonomous system...
    echo Press Ctrl+C to stop
    echo.
    python -c "import asyncio; from trading_bot.neuros_evolution import quick_start; orchestrator = quick_start({'enable_auto_evolution': True, 'enable_auto_rebalancing': True, 'enable_self_improvement': True}); asyncio.run(orchestrator.initialize()); asyncio.run(orchestrator.start()); import time; time.sleep(3600)"
) else (
    echo.
    echo Autonomous evolution cancelled.
)
echo.
pause
goto MENU

:VIEW_DOCS
echo.
echo ================================================================================
echo Opening Documentation...
echo ================================================================================
echo.
start NEUROS_EVOLUTION_COMPLETE.md
goto MENU

:EXIT
echo.
echo ================================================================================
echo Thank you for using NEUROS Evolution!
echo ================================================================================
echo.
exit /b 0
