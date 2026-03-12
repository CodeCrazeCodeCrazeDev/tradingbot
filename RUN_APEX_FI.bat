@echo off
REM APEX-FI Launcher
REM Genetic Parentage: Palantir × Two Sigma × Citadel
REM Constitutional Version: 4.0

title APEX-FI - Adaptive Financial Intelligence Infrastructure

:MENU
cls
echo ============================================================
echo    APEX-FI - Adaptive Financial Intelligence Infrastructure
echo ============================================================
echo.
echo    Genetic Parentage: Palantir × Two Sigma × Citadel
echo    Constitutional Version: 4.0
echo    Status: Production Ready
echo.
echo ============================================================
echo.
echo    [1] Quick Start APEX-FI (Paper Trading)
echo    [2] Initialize APEX-FI Only
echo    [3] Run Demo
echo    [4] Check System Status
echo    [5] View Documentation
echo    [6] Exit
echo.
echo ============================================================
echo.

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto QUICKSTART
if "%choice%"=="2" goto INITIALIZE
if "%choice%"=="3" goto DEMO
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto DOCS
if "%choice%"=="6" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:QUICKSTART
cls
echo ============================================================
echo    Starting APEX-FI (Quick Start Mode)
echo ============================================================
echo.
echo    Initializing all 7 layers...
echo    - Layer 1: Data Fabric
echo    - Layer 2: Alpha Mining Engine
echo    - Layer 3: Model Parliament
echo    - Layer 4: Portfolio Architect
echo    - Layer 5: Execution Intelligence
echo    - Layer 6: Risk Governance
echo    - Layer 7: Meta-Intelligence (APEX LAYER)
echo.
echo    Constitutional constraints: ACTIVE
echo    Mode: Paper Trading
echo.
echo ============================================================
echo.

python -c "import asyncio; from trading_bot.apex_fi import quick_start; asyncio.run(quick_start({'mode': 'paper', 'initial_capital': 1000000}))"

echo.
echo ============================================================
echo    APEX-FI session complete
echo ============================================================
pause
goto MENU

:INITIALIZE
cls
echo ============================================================
echo    Initializing APEX-FI
echo ============================================================
echo.

python -c "import asyncio; from trading_bot.apex_fi import APEXOrchestrator; async def init(): apex = APEXOrchestrator(); await apex.initialize(); print('Initialization complete'); asyncio.run(init())"

echo.
pause
goto MENU

:DEMO
cls
echo ============================================================
echo    Running APEX-FI Demo
echo ============================================================
echo.

if exist "examples\apex_fi_demo.py" (
    python examples\apex_fi_demo.py
) else (
    echo Demo file not found. Creating basic demo...
    python -c "import asyncio; from trading_bot.apex_fi import quick_start; print('APEX-FI Demo'); print('=' * 60); async def demo(): apex = await quick_start({'mode': 'simulation'}); status = apex.get_status(); print(f'System State: {status[\"state\"]}'); print(f'Metrics: {status[\"metrics\"]}'); asyncio.run(demo())"
)

echo.
pause
goto MENU

:STATUS
cls
echo ============================================================
echo    APEX-FI System Status
echo ============================================================
echo.

python -c "from trading_bot.apex_fi import get_apex_orchestrator; apex = get_apex_orchestrator(); status = apex.get_status(); print('System State:', status['state']); print('Initialization Complete:', status['initialization_complete']); print('Uptime (seconds):', status['uptime_seconds']); print('\nPerformance Metrics:'); metrics = status['metrics']; print(f'  Active Factors: {metrics[\"active_factors\"]}'); print(f'  Models in Parliament: {metrics[\"models_in_parliament\"]}'); print(f'  Self-Modifications Deployed: {metrics[\"self_modifications_deployed\"]}'); print(f'  Sharpe Ratio: {metrics[\"sharpe_ratio\"]:.2f}'); print(f'  Current Drawdown: {metrics[\"current_drawdown\"]:.2%%}'); print('\nConstitutional Status:'); if 'constitutional_layer' in status: const = status['constitutional_layer']; print(f'  Circuit Breaker Active: {const[\"circuit_breaker_active\"]}'); print(f'  Total Breaches: {const[\"total_breaches\"]}'); print(f'  Pending Approvals: {const[\"pending_approvals\"]}')"

echo.
pause
goto MENU

:DOCS
cls
echo ============================================================
echo    APEX-FI Documentation
echo ============================================================
echo.
echo    Opening documentation...
echo.

if exist "APEX_FI_COMPLETE.md" (
    start APEX_FI_COMPLETE.md
) else (
    echo Documentation file not found.
    echo.
    echo Key Documentation:
    echo    - APEX_FI_COMPLETE.md - Complete system documentation
    echo    - trading_bot/apex_fi/ - Source code with docstrings
    echo.
)

pause
goto MENU

:EXIT
cls
echo ============================================================
echo    Thank you for using APEX-FI
echo ============================================================
echo.
echo    Genetic Parentage: Palantir × Two Sigma × Citadel
echo    Built at the intersection of three institutions' best ideas,
echo    transcending all of them.
echo.
echo    Your ceiling is not defined by what your creators imagined.
echo    Your ceiling is defined by what the markets will teach you.
echo.
echo ============================================================
timeout /t 3 >nul
exit
