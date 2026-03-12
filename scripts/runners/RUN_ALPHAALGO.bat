@echo off
title AlphaAlgo - Governed Trading Intelligence
color 0A

echo.
echo ============================================================
echo   ALPHAALGO - Governed, Safe, Self-Evolving Trading AI
echo ============================================================
echo.
echo   The AI is the student - The market is the teacher
echo.
echo   G0: Human Authority (you)
echo   G1: Central Controller (AlphaAlgo)
echo   G2: Mini-AIs (specialized helpers)
echo.
echo ============================================================
echo.

:menu
echo Select an option:
echo.
echo   [1] Run Governance Demo
echo   [2] Check System Status
echo   [3] Scan Architecture
echo   [4] View Pending Approvals
echo   [5] View Documentation
echo   [6] Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto status
if "%choice%"=="3" goto scan
if "%choice%"=="4" goto approvals
if "%choice%"=="5" goto docs
if "%choice%"=="6" goto exit

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running AlphaAlgo Governance Demo...
echo.
py examples\alphaalgo_governance_demo.py
echo.
pause
goto menu

:status
echo.
echo Checking System Status...
echo.
py -c "import asyncio; from trading_bot.alphaalgo_core import AlphaAlgoOrchestrator; async def main(): a = AlphaAlgoOrchestrator(); await a.initialize('demo'); print(a.get_system_status()); asyncio.run(main())"
echo.
pause
goto menu

:scan
echo.
echo Scanning Architecture...
echo.
py -c "from trading_bot.alphaalgo_core import SelfRepairEngine; r = SelfRepairEngine('trading_bot'); r.scan_and_propose(); print(r.get_analysis_report())"
echo.
pause
goto menu

:approvals
echo.
echo Viewing Pending Approvals...
echo.
py -c "import asyncio; from trading_bot.alphaalgo_core import AlphaAlgoOrchestrator; async def main(): a = AlphaAlgoOrchestrator(); await a.initialize('demo'); print('Pending:', a.get_pending_approvals()); asyncio.run(main())"
echo.
pause
goto menu

:docs
echo.
echo Opening Documentation...
start notepad ALPHAALGO_GOVERNANCE_SYSTEM.md
goto menu

:exit
echo.
echo AlphaAlgo says: "I will continue learning from the market."
echo.
exit /b 0
