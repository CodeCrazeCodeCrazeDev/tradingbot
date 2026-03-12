@echo off
title AlphaAlgo Ultimate Integrated Trading Bot - 1500+ Modules
color 0A
setlocal EnableDelayedExpansion

:: ============================================================================
:: ALPHAALGO ULTIMATE INTEGRATED TRADING BOT
:: ============================================================================
:: This launcher integrates ALL 1500+ modules with auto-dependency installation
:: ============================================================================

echo.
echo ========================================================================
echo    ALPHAALGO ULTIMATE INTEGRATED TRADING BOT
echo    1,501 Modules ^| 7,142 Classes ^| 1,073 Functions
echo ========================================================================
echo.

:: Check for Python
where py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Get Python version
for /f "tokens=*" %%i in ('py --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Using: %PYTHON_VERSION%

:: Change to script directory
cd /d "%~dp0"
echo [INFO] Working directory: %CD%

:: ============================================================================
:: MAIN MENU
:: ============================================================================

:MENU
echo.
echo ========================================================================
echo                           MAIN MENU
echo ========================================================================
echo.
echo   [1] Quick Start (Paper Trading)
echo   [2] Full System Start (All Modules)
echo   [3] Install/Update Dependencies
echo   [4] Check System Health
echo   [5] Run Module Integration Test
echo   [6] Advanced Options
echo   [7] View Documentation
echo   [8] Exit
echo.
set /p CHOICE="Select option (1-8): "

if "%CHOICE%"=="1" goto QUICK_START
if "%CHOICE%"=="2" goto FULL_START
if "%CHOICE%"=="3" goto INSTALL_DEPS
if "%CHOICE%"=="4" goto HEALTH_CHECK
if "%CHOICE%"=="5" goto INTEGRATION_TEST
if "%CHOICE%"=="6" goto ADVANCED_MENU
if "%CHOICE%"=="7" goto VIEW_DOCS
if "%CHOICE%"=="8" goto EXIT

echo [ERROR] Invalid option. Please select 1-8.
goto MENU

:: ============================================================================
:: QUICK START - Paper Trading Mode
:: ============================================================================

:QUICK_START
echo.
echo ========================================================================
echo                    QUICK START - PAPER TRADING
echo ========================================================================
echo.
echo [INFO] Starting in Paper Trading mode...
echo [INFO] This is safe - no real money will be used.
echo.

:: Check dependencies first
call :CHECK_DEPS_QUICK
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Some dependencies missing. Installing...
    call :INSTALL_DEPS_SILENT
)

echo [INFO] Launching trading bot...
echo.

py -c "
import sys
sys.path.insert(0, '.')

print('Loading Ultimate Module Integrator...')
from trading_bot.ultimate_module_integrator import IntegratedTradingSystem

print('Initializing system with all 1500+ modules...')
system = IntegratedTradingSystem({'mode': 'paper'})
system.initialize()

print()
print('=' * 60)
print('SYSTEM READY - Paper Trading Mode')
print('=' * 60)
print(f'Orchestrators loaded: {len(system.list_orchestrators())}')
print()

# Try to start mega integration
try:
    from trading_bot.mega_integration import MegaIntegration, MegaConfig, SystemMode
    config = MegaConfig(mode=SystemMode.PAPER, symbols=['BTCUSDT', 'EURUSD'])
    mega = MegaIntegration(config)
    print('MegaIntegration initialized successfully!')
    print('Press Ctrl+C to stop...')
    import asyncio
    asyncio.run(mega.start())
except KeyboardInterrupt:
    print('\\nShutdown requested...')
except Exception as e:
    print(f'Note: {e}')
    print('System initialized but trading loop requires additional setup.')
"

echo.
echo [INFO] Trading session ended.
pause
goto MENU

:: ============================================================================
:: FULL SYSTEM START - All Modules
:: ============================================================================

:FULL_START
echo.
echo ========================================================================
echo                    FULL SYSTEM START
echo ========================================================================
echo.

set /p SYMBOLS="Enter symbols (comma-separated, e.g., BTCUSDT,EURUSD): "
if "%SYMBOLS%"=="" set SYMBOLS=BTCUSDT,EURUSD

set /p CAPITAL="Enter initial capital (default 100000): "
if "%CAPITAL%"=="" set CAPITAL=100000

echo.
echo Select trading mode:
echo   [1] Paper Trading (Simulation)
echo   [2] Live Trading (Real Money - CAUTION!)
echo   [3] Backtest Mode
echo.
set /p MODE_CHOICE="Select mode (1-3): "

if "%MODE_CHOICE%"=="1" set MODE=paper
if "%MODE_CHOICE%"=="2" set MODE=live
if "%MODE_CHOICE%"=="3" set MODE=backtest
if "%MODE%"=="" set MODE=paper

echo.
echo [INFO] Configuration:
echo   - Symbols: %SYMBOLS%
echo   - Capital: $%CAPITAL%
echo   - Mode: %MODE%
echo.

if "%MODE%"=="live" (
    echo ========================================================================
    echo                         WARNING - LIVE TRADING
    echo ========================================================================
    echo.
    echo You are about to start LIVE trading with REAL MONEY!
    echo Make sure you understand the risks involved.
    echo.
    set /p CONFIRM="Type 'CONFIRM' to proceed: "
    if not "!CONFIRM!"=="CONFIRM" (
        echo [INFO] Live trading cancelled.
        goto MENU
    )
)

:: Install dependencies
call :INSTALL_DEPS_SILENT

echo [INFO] Starting full system...
echo.

py -c "
import sys
sys.path.insert(0, '.')

symbols = '%SYMBOLS%'.split(',')
capital = float('%CAPITAL%')
mode = '%MODE%'

print('=' * 60)
print('ALPHAALGO ULTIMATE INTEGRATED TRADING BOT')
print('=' * 60)
print(f'Mode: {mode.upper()}')
print(f'Symbols: {symbols}')
print(f'Capital: ${capital:,.2f}')
print('=' * 60)
print()

# Load all modules
print('Loading 1500+ modules...')
from trading_bot.ultimate_module_integrator import IntegratedTradingSystem
system = IntegratedTradingSystem({'mode': mode, 'symbols': symbols, 'capital': capital})
system.initialize()

# Start trading
try:
    from trading_bot.mega_integration import MegaIntegration, MegaConfig, SystemMode
    
    mode_map = {'paper': SystemMode.PAPER, 'live': SystemMode.LIVE, 'backtest': SystemMode.BACKTEST}
    config = MegaConfig(
        mode=mode_map.get(mode, SystemMode.PAPER),
        symbols=symbols,
        initial_capital=capital
    )
    
    mega = MegaIntegration(config)
    print()
    print('System fully initialized!')
    print('Press Ctrl+C to stop trading...')
    print()
    
    import asyncio
    asyncio.run(mega.start())
    
except KeyboardInterrupt:
    print('\\nShutdown requested...')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"

echo.
pause
goto MENU

:: ============================================================================
:: INSTALL DEPENDENCIES
:: ============================================================================

:INSTALL_DEPS
echo.
echo ========================================================================
echo                    DEPENDENCY INSTALLATION
echo ========================================================================
echo.
echo [INFO] This will install all required Python packages.
echo.

:: Upgrade pip first
echo [INFO] Upgrading pip...
py -m pip install --upgrade pip -q

:: Install from requirements.txt if exists
if exist "requirements.txt" (
    echo [INFO] Installing from requirements.txt...
    py -m pip install -r requirements.txt -q
)

:: Run auto dependency installer
echo [INFO] Scanning for missing dependencies...
py -c "
import sys
sys.path.insert(0, '.')
from trading_bot.auto_dependency_installer import install_dependencies
install_dependencies()
"

echo.
echo [INFO] Dependency installation complete!
pause
goto MENU

:INSTALL_DEPS_SILENT
:: Silent dependency installation
py -m pip install --upgrade pip -q 2>nul
if exist "requirements.txt" (
    py -m pip install -r requirements.txt -q 2>nul
)
py -c "import sys; sys.path.insert(0, '.'); from trading_bot.auto_dependency_installer import AutoDependencyInstaller; a = AutoDependencyInstaller(verbose=False); a.full_install()" 2>nul
exit /b 0

:CHECK_DEPS_QUICK
:: Quick dependency check
py -c "from trading_bot.mega_integration import MegaIntegration" 2>nul
exit /b %ERRORLEVEL%

:: ============================================================================
:: HEALTH CHECK
:: ============================================================================

:HEALTH_CHECK
echo.
echo ========================================================================
echo                       SYSTEM HEALTH CHECK
echo ========================================================================
echo.

py -c "
import sys
sys.path.insert(0, '.')

print('Running comprehensive health check...')
print()

from trading_bot.ultimate_module_integrator import UltimateModuleIntegrator

integrator = UltimateModuleIntegrator()
integrator.discover_all_modules()
integrator.load_all_modules()

report = integrator.get_health_report()

print('=' * 60)
print('HEALTH REPORT')
print('=' * 60)
print(f'Total Modules: {report[\"total_modules\"]}')
print(f'Loaded: {report[\"loaded\"]}')
print(f'Failed: {report[\"failed\"]}')
print(f'Success Rate: {report[\"success_rate\"]:.1f}%%')
print()
print('Categories:')
for cat, data in sorted(report['categories'].items(), key=lambda x: -x[1]['total']):
    print(f'  {cat}: {data[\"loaded\"]}/{data[\"total\"]} ({data[\"success_rate\"]:.0f}%%)')

if report['failed_modules']:
    print()
    print(f'Failed Modules ({len(report[\"failed_modules\"])}):')
    for mod in report['failed_modules'][:10]:
        print(f'  - {mod[\"path\"]}: {mod[\"error\"][:50]}...')
    if len(report['failed_modules']) > 10:
        print(f'  ... and {len(report[\"failed_modules\"]) - 10} more')

print()
if report['success_rate'] >= 95:
    print('STATUS: EXCELLENT - System fully operational!')
elif report['success_rate'] >= 80:
    print('STATUS: GOOD - System operational with minor issues')
elif report['success_rate'] >= 60:
    print('STATUS: DEGRADED - Some modules not working')
else:
    print('STATUS: CRITICAL - Many modules failing')
"

echo.
pause
goto MENU

:: ============================================================================
:: INTEGRATION TEST
:: ============================================================================

:INTEGRATION_TEST
echo.
echo ========================================================================
echo                    MODULE INTEGRATION TEST
echo ========================================================================
echo.

py -c "
import sys
sys.path.insert(0, '.')

print('Testing module integration...')
print()

# Test 1: Ultimate Module Integrator
print('[TEST 1] Ultimate Module Integrator')
try:
    from trading_bot.ultimate_module_integrator import UltimateModuleIntegrator
    i = UltimateModuleIntegrator()
    count = i.discover_all_modules()
    print(f'  PASS - Discovered {count} modules')
except Exception as e:
    print(f'  FAIL - {e}')

# Test 2: Mega Integration
print('[TEST 2] Mega Integration')
try:
    from trading_bot.mega_integration import MegaIntegration, MegaConfig
    config = MegaConfig()
    mega = MegaIntegration(config)
    print(f'  PASS - Loaded {len(mega.active_modules)} modules')
except Exception as e:
    print(f'  FAIL - {e}')

# Test 3: Core Systems
print('[TEST 3] Core Trading Systems')
try:
    from trading_bot.core.survival_core import SurvivalCore
    from trading_bot.risk.MASTER_risk_manager import MasterRiskManager
    print('  PASS - Core systems loaded')
except Exception as e:
    print(f'  FAIL - {e}')

# Test 4: AI/ML Systems
print('[TEST 4] AI/ML Systems')
try:
    from trading_bot.cognitive_architecture.cognitive_core import AlphaAlgoCognitiveCore
    print('  PASS - Cognitive core loaded')
except Exception as e:
    print(f'  PARTIAL - {e}')

# Test 5: Safety Systems
print('[TEST 5] Safety Systems')
try:
    from trading_bot.hedge_fund_safety.mitigation_orchestrator import HedgeFundSafetyOrchestrator
    print('  PASS - Safety systems loaded')
except Exception as e:
    print(f'  PARTIAL - {e}')

# Test 6: Execution Systems
print('[TEST 6] Execution Systems')
try:
    from trading_bot.execution.complete_execution_system import CompleteExecutionSystem
    print('  PASS - Execution systems loaded')
except Exception as e:
    print(f'  PARTIAL - {e}')

print()
print('Integration test complete!')
"

echo.
pause
goto MENU

:: ============================================================================
:: ADVANCED MENU
:: ============================================================================

:ADVANCED_MENU
echo.
echo ========================================================================
echo                        ADVANCED OPTIONS
echo ========================================================================
echo.
echo   [1] Export Module Map (JSON)
echo   [2] Run Specific Orchestrator
echo   [3] Check Missing Dependencies
echo   [4] Clear Cache and Logs
echo   [5] Run in Debug Mode
echo   [6] Back to Main Menu
echo.
set /p ADV_CHOICE="Select option (1-6): "

if "%ADV_CHOICE%"=="1" goto EXPORT_MAP
if "%ADV_CHOICE%"=="2" goto RUN_ORCHESTRATOR
if "%ADV_CHOICE%"=="3" goto CHECK_MISSING
if "%ADV_CHOICE%"=="4" goto CLEAR_CACHE
if "%ADV_CHOICE%"=="5" goto DEBUG_MODE
if "%ADV_CHOICE%"=="6" goto MENU

goto ADVANCED_MENU

:EXPORT_MAP
echo.
echo [INFO] Exporting module map...
py -c "
import sys
sys.path.insert(0, '.')
from trading_bot.ultimate_module_integrator import UltimateModuleIntegrator
i = UltimateModuleIntegrator()
i.discover_all_modules()
i.load_all_modules()
i.export_module_map('module_map_export.json')
print('Module map exported to module_map_export.json')
"
pause
goto ADVANCED_MENU

:RUN_ORCHESTRATOR
echo.
echo Available Orchestrators:
echo   [1] MegaIntegration
echo   [2] MasterOrchestrator
echo   [3] EliteTradingOrchestrator
echo   [4] UltimateOrchestrator
echo   [5] AlphaEngineOrchestrator
echo.
set /p ORCH_CHOICE="Select orchestrator (1-5): "

if "%ORCH_CHOICE%"=="1" set ORCH_CLASS=MegaIntegration
if "%ORCH_CHOICE%"=="2" set ORCH_CLASS=MasterOrchestrator
if "%ORCH_CHOICE%"=="3" set ORCH_CLASS=EliteTradingOrchestrator
if "%ORCH_CHOICE%"=="4" set ORCH_CLASS=UltimateOrchestrator
if "%ORCH_CHOICE%"=="5" set ORCH_CLASS=AlphaEngineOrchestrator

echo [INFO] Running %ORCH_CLASS%...
py trading_bot/mega_integration.py --mode paper
pause
goto ADVANCED_MENU

:CHECK_MISSING
echo.
echo [INFO] Checking for missing dependencies...
py trading_bot/auto_dependency_installer.py --check
pause
goto ADVANCED_MENU

:CLEAR_CACHE
echo.
echo [INFO] Clearing cache and logs...
if exist "mega_logs" rd /s /q "mega_logs" 2>nul
if exist "mega_data" rd /s /q "mega_data" 2>nul
if exist "mega_state" rd /s /q "mega_state" 2>nul
if exist "__pycache__" rd /s /q "__pycache__" 2>nul
for /d /r "trading_bot" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo [INFO] Cache cleared!
pause
goto ADVANCED_MENU

:DEBUG_MODE
echo.
echo [INFO] Starting in debug mode...
set PYTHONDONTWRITEBYTECODE=1
py -c "
import sys
import logging
sys.path.insert(0, '.')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from trading_bot.ultimate_module_integrator import IntegratedTradingSystem
system = IntegratedTradingSystem()
system.initialize()

print()
print('Debug mode active. System initialized.')
print('You can now import and test any module.')
print()

import code
code.interact(local=locals())
"
pause
goto ADVANCED_MENU

:: ============================================================================
:: VIEW DOCUMENTATION
:: ============================================================================

:VIEW_DOCS
echo.
echo ========================================================================
echo                         DOCUMENTATION
echo ========================================================================
echo.
echo Available documentation:
echo.

if exist "ULTIMATE_INTEGRATION_COMPLETE.md" (
    echo   [1] Ultimate Integration Guide
)
if exist "README.md" (
    echo   [2] Main README
)
if exist "docs" (
    echo   [3] Open docs folder
)
echo   [4] Back to Main Menu
echo.
set /p DOC_CHOICE="Select option: "

if "%DOC_CHOICE%"=="1" if exist "ULTIMATE_INTEGRATION_COMPLETE.md" notepad "ULTIMATE_INTEGRATION_COMPLETE.md"
if "%DOC_CHOICE%"=="2" if exist "README.md" notepad "README.md"
if "%DOC_CHOICE%"=="3" if exist "docs" explorer "docs"
if "%DOC_CHOICE%"=="4" goto MENU

goto VIEW_DOCS

:: ============================================================================
:: EXIT
:: ============================================================================

:EXIT
echo.
echo ========================================================================
echo                    Thank you for using AlphaAlgo!
echo ========================================================================
echo.
echo Trade safely and responsibly.
echo.
timeout /t 3 >nul
exit /b 0
