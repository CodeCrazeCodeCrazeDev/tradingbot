@echo off
REM Comprehensive Recursive Evolution System Launcher
REM ================================================

echo.
echo ================================================================================
echo   COMPREHENSIVE RECURSIVE EVOLUTION SYSTEM
echo ================================================================================
echo.
echo This system enables the trading bot to recursively evolve ALL areas:
echo - Strategies, Risk Management, Execution, Data Processing, ML Models
echo.
echo WHAT AI CAN EVOLVE:
echo   [+] Strategy parameters and combinations
echo   [+] ML models and hyperparameters
echo   [+] Data processing methods
echo   [+] Execution algorithms
echo   [+] Analysis techniques
echo.
echo WHAT AI CANNOT EVOLVE:
echo   [-] Risk limits (max 2%% per trade, 5%% daily, 20%% drawdown)
echo   [-] Safety systems (emergency stop, circuit breakers)
echo   [-] Governance rules (human approval requirements)
echo   [-] Evolution boundaries themselves
echo.
echo ================================================================================
echo.

:MENU
echo.
echo Select an option:
echo.
echo   1. Run Comprehensive Evolution Demo
echo   2. Start Continuous Evolution (Background)
echo   3. Check Pending Approvals
echo   4. View Evolution Summary
echo   5. Verify Boundary Integrity
echo   6. View Evolution Guide
echo   7. Exit
echo.

set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto DEMO
if "%choice%"=="2" goto START
if "%choice%"=="3" goto APPROVALS
if "%choice%"=="4" goto SUMMARY
if "%choice%"=="5" goto VERIFY
if "%choice%"=="6" goto GUIDE
if "%choice%"=="7" goto END

echo Invalid choice. Please try again.
goto MENU

:DEMO
echo.
echo Running Comprehensive Evolution Demo...
echo.
py examples/comprehensive_recursive_evolution_demo.py
pause
goto MENU

:START
echo.
echo Starting Continuous Evolution...
echo.
echo WARNING: This will start the evolution loop in the background.
echo The system will continuously monitor and propose improvements.
echo.
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" goto MENU

py -c "from trading_bot.recursive_evolution import quick_start; import asyncio; o = quick_start(); asyncio.run(o.start()); print('Evolution started. Press Ctrl+C to stop.'); import time; time.sleep(999999)"
goto MENU

:APPROVALS
echo.
echo Checking Pending Approvals...
echo.
py -c "from trading_bot.recursive_evolution import quick_start; o = quick_start(); pending = o.get_pending_approvals(); print(f'Pending approvals: {len(pending)}'); [print(f'\nProposal: {p[\"proposal_id\"]}\nArea: {p[\"area\"]}\nRationale: {p[\"rationale\"]}') for p in pending]"
pause
goto MENU

:SUMMARY
echo.
echo Evolution Summary...
echo.
py -c "from trading_bot.recursive_evolution import quick_start; import json; o = quick_start(); summary = o.get_evolution_summary(); print(json.dumps(summary, indent=2))"
pause
goto MENU

:VERIFY
echo.
echo Verifying Boundary Integrity...
echo.
py -c "from trading_bot.recursive_evolution import verify_boundary_integrity, EvolutionBoundaries; verified = verify_boundary_integrity(); print(f'Boundary Integrity: {\"VERIFIED\" if verified else \"COMPROMISED\"}'); print(f'Boundary Hash: {EvolutionBoundaries.get_boundary_hash()}')"
pause
goto MENU

:GUIDE
echo.
echo Evolution Guide...
echo.
py -c "from trading_bot.recursive_evolution import get_evolution_guide; import json; guide = get_evolution_guide(); print(json.dumps(guide, indent=2))"
pause
goto MENU

:END
echo.
echo Exiting...
echo.
exit /b 0
