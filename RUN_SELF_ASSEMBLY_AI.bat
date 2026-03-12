@echo off
REM Self-Assembly AI System Launcher
REM Starts the autonomous self-managing AI with comprehensive risk mitigation

echo ================================================================================
echo SELF-ASSEMBLY AI SYSTEM
echo Autonomous Self-Managing AI with Comprehensive Risk Mitigation
echo Advanced AI Capability Registry Loaded
echo ================================================================================
echo.

REM Resolve Python launcher
set "PY_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Make sure either "python" or "py" works in this terminal.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
)

echo Select Mode:
echo.
echo [1] Start Self-Assembly AI (Auto-Evolution Enabled)
echo [2] Start Self-Assembly AI (Manual Mode - No Auto-Evolution)
echo [3] View System Status
echo [4] Create Safety Checkpoint
echo [5] Rollback to Last Safe Checkpoint
echo [6] Emergency Shutdown
echo [7] Run Demo
echo [8] Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto auto_mode
if "%choice%"=="2" goto manual_mode
if "%choice%"=="3" goto status
if "%choice%"=="4" goto checkpoint
if "%choice%"=="5" goto rollback
if "%choice%"=="6" goto emergency
if "%choice%"=="7" goto demo
if "%choice%"=="8" goto end

echo Invalid choice. Please try again.
pause
goto :eof

:auto_mode
echo.
echo ================================================================================
echo Starting Self-Assembly AI in AUTO-EVOLUTION mode
echo ================================================================================
echo.
echo WARNING: The AI will autonomously improve itself within safety boundaries.
echo Human override is ALWAYS available.
echo.
echo Press Ctrl+C to stop at any time.
echo.
%PY_CMD% -c "import asyncio; from trading_bot.self_assembly_ai import run_self_assembly_ai; asyncio.run(run_self_assembly_ai(auto_evolution=True, evolution_interval=3600))"
goto end

:manual_mode
echo.
echo ================================================================================
echo Starting Self-Assembly AI in MANUAL mode
echo ================================================================================
echo.
echo The AI will NOT automatically evolve. Manual approval required for changes.
echo.
%PY_CMD% -c "import asyncio; from trading_bot.self_assembly_ai import run_self_assembly_ai; asyncio.run(run_self_assembly_ai(auto_evolution=False))"
goto end

:status
echo.
echo ================================================================================
echo System Status Report
echo ================================================================================
echo.
%PY_CMD% -c "from trading_bot.self_assembly_ai import MasterSelfAssemblyOrchestrator; orch = MasterSelfAssemblyOrchestrator('.'); status = orch.get_system_status(); capability_report = orch.get_advanced_capability_report(); print(f'Safety Core Integrity: {status.safety_core_integrity}'); print(f'Overall Risk Level: {status.overall_risk_level.name}'); print(f'Active Components: {status.active_components}'); print(f'Total Improvements: {status.total_improvements}'); print(f'Recursion Depth: {status.current_recursion_depth}'); print(f'Auto-Evolution: {status.auto_evolution_enabled}'); print('Advanced AI Capabilities: {} across {} categories'.format(capability_report['total_capabilities'], len(capability_report['categories']))); print('Sample Capabilities: ' + ', '.join([c['name'] for c in capability_report['capabilities'][:5]]))"
echo.
pause
goto :eof

:checkpoint
echo.
echo ================================================================================
echo Creating Safety Checkpoint
echo ================================================================================
echo.
%PY_CMD% -c "from trading_bot.self_assembly_ai import EvolutionMonitor; monitor = EvolutionMonitor('.'); checkpoint = monitor.create_checkpoint('Manual checkpoint'); print(f'Checkpoint created: {checkpoint.checkpoint_id}'); print(f'Timestamp: {checkpoint.timestamp}')"
echo.
pause
goto :eof

:rollback
echo.
echo ================================================================================
echo Rolling Back to Last Safe Checkpoint
echo ================================================================================
echo.
echo WARNING: This will restore the system to the last known safe state.
echo.
set /p confirm="Are you sure? (yes/no): "
if not "%confirm%"=="yes" goto :eof
echo.
%PY_CMD% -c "from trading_bot.self_assembly_ai import EvolutionMonitor; monitor = EvolutionMonitor('.'); success = monitor.rollback_to_last_safe_checkpoint(); print('Rollback: {}'.format('SUCCESS' if success else 'FAILED'))"
echo.
pause
goto :eof

:emergency
echo.
echo ================================================================================
echo EMERGENCY SHUTDOWN
echo ================================================================================
echo.
echo WARNING: This will immediately stop all AI operations and rollback to safety.
echo.
set /p confirm="Are you ABSOLUTELY sure? (yes/no): "
if not "%confirm%"=="yes" goto :eof
echo.
%PY_CMD% -c "import asyncio; from trading_bot.self_assembly_ai import MasterSelfAssemblyOrchestrator; orch = MasterSelfAssemblyOrchestrator('.'); asyncio.run(orch.start()); asyncio.run(orch._emergency_shutdown())"
echo.
echo EMERGENCY SHUTDOWN COMPLETE
pause
goto end

:demo
echo.
echo ================================================================================
echo Running Self-Assembly AI Demo
echo ================================================================================
echo.
%PY_CMD% examples/self_assembly_ai_demo.py
goto end

:end
echo.
echo ================================================================================
echo Self-Assembly AI System Stopped
echo ================================================================================
pause
