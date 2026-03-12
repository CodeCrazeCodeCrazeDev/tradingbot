@echo off
title Autonomous Improvement Agent
color 0A

echo.
echo ========================================================
echo     AUTONOMOUS IMPROVEMENT AGENT
echo     Making Your Trading Bot Better
echo ========================================================
echo.

cd /d "%~dp0"

:MENU
echo.
echo Select an option:
echo.
echo   [1] Run Full Improvement Cycle (Supervised)
echo   [2] Run Analysis Only (Observe Mode)
echo   [3] Interactive Review Session
echo   [4] Generate Report Only
echo   [5] Focus on Security Issues
echo   [6] Focus on Risk Management
echo   [7] Focus on Performance
echo   [8] Quick Analysis (Faster)
echo   [9] Help
echo   [0] Exit
echo.

set /p choice="Enter choice (0-9): "

if "%choice%"=="1" goto FULL
if "%choice%"=="2" goto OBSERVE
if "%choice%"=="3" goto INTERACTIVE
if "%choice%"=="4" goto REPORT
if "%choice%"=="5" goto SECURITY
if "%choice%"=="6" goto RISK
if "%choice%"=="7" goto PERFORMANCE
if "%choice%"=="8" goto QUICK
if "%choice%"=="9" goto HELP
if "%choice%"=="0" goto EXIT

echo Invalid choice. Try again.
goto MENU

:FULL
echo.
echo Starting full improvement cycle...
python -m trading_bot.improvement_agent.run_agent --mode supervised
pause
goto MENU

:OBSERVE
echo.
echo Running analysis only...
python -m trading_bot.improvement_agent.run_agent --mode observe
pause
goto MENU

:INTERACTIVE
echo.
echo Starting interactive review session...
python -m trading_bot.improvement_agent.run_agent --interactive
pause
goto MENU

:REPORT
echo.
echo Generating report...
python -m trading_bot.improvement_agent.run_agent --report-only
pause
goto MENU

:SECURITY
echo.
echo Focusing on security issues...
python -m trading_bot.improvement_agent.run_agent --focus security --interactive
pause
goto MENU

:RISK
echo.
echo Focusing on risk management...
python -m trading_bot.improvement_agent.run_agent --focus risk --interactive
pause
goto MENU

:PERFORMANCE
echo.
echo Focusing on performance...
python -m trading_bot.improvement_agent.run_agent --focus performance --interactive
pause
goto MENU

:QUICK
echo.
echo Running quick analysis...
python -m trading_bot.improvement_agent.run_agent --depth quick --report-only
pause
goto MENU

:HELP
echo.
echo ========================================================
echo IMPROVEMENT AGENT HELP
echo ========================================================
echo.
echo The Improvement Agent analyzes your codebase and proposes
echo improvements for you to review and approve.
echo.
echo MODES:
echo   observe    - Only analyze, no proposals
echo   propose    - Analyze and generate proposals
echo   supervised - Apply only approved changes (DEFAULT)
echo   autonomous - Auto-apply safe changes
echo.
echo WORKFLOW:
echo   1. Agent analyzes codebase
echo   2. Agent detects weaknesses
echo   3. Agent proposes improvements
echo   4. YOU review and approve/reject
echo   5. Agent applies approved changes
echo.
echo See IMPROVEMENT_AGENT_GUIDE.md for full documentation.
echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0
