@echo off
title AlphaAlgo MSOS - Market Survival Operating System
color 0A

echo.
echo ============================================================
echo   ALPHAALGO MSOS - MARKET SURVIVAL OPERATING SYSTEM
echo   Capital Preservation First - Returns Are A Side Effect
echo ============================================================
echo.
echo   PRIMARY DIRECTIVE: Preserve capital across regime shifts.
echo   Returns are a side effect of survival - never the goal.
echo.
echo ============================================================
echo.

:menu
echo   Select an option:
echo.
echo   [1] Run MSOS Demo
echo   [2] Run MSOS Tests
echo   [3] View Documentation
echo   [4] Check System Status
echo   [5] Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto tests
if "%choice%"=="3" goto docs
if "%choice%"=="4" goto status
if "%choice%"=="5" goto exit

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running MSOS Demo...
echo.
python examples\msos_demo.py
echo.
pause
goto menu

:tests
echo.
echo Running MSOS Tests...
echo.
python -m pytest tests\test_msos*.py -v
echo.
pause
goto menu

:docs
echo.
echo Opening Documentation...
echo.
start "" "MSOS_IMPLEMENTATION_COMPLETE.md"
goto menu

:status
echo.
echo ============================================================
echo   MSOS SYSTEM STATUS
echo ============================================================
echo.
python -c "from trading_bot.msos import MSOSCore, ABSOLUTE_AXIOMS; print('Axioms:', len(ABSOLUTE_AXIOMS)); core = MSOSCore(); print('Constraints:', len(list(core.constraints.all_constraints))); print('Status: OPERATIONAL')"
echo.
pause
goto menu

:exit
echo.
echo   "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
echo.
echo Goodbye.
exit /b 0
