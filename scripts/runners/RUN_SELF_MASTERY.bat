@echo off
title Self-Mastery Learning System
color 0A

echo ================================================================================
echo                      SELF-MASTERY LEARNING SYSTEM
echo ================================================================================
echo.
echo  IF I WERE THIS BOT, HERE'S HOW I WOULD LEARN:
echo.
echo    1. EXPERIENCE EVERYTHING - Record every trade and decision
echo    2. REFLECT DEEPLY - Analyze patterns and find insights
echo    3. EVOLVE MY CODE - Turn learning into improvements
echo    4. CONSOLIDATE KNOWLEDGE - Build structured mastery
echo    5. VERIFY MASTERY - Prove competence before advancing
echo.
echo ================================================================================
echo.

:menu
echo  SELECT AN OPTION:
echo.
echo    [1] Run Demo (Recommended)
echo    [2] View Mastery Report
echo    [3] Run Reflection Session
echo    [4] View Documentation
echo    [5] Exit
echo.
set /p choice="  Enter choice (1-5): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto report
if "%choice%"=="3" goto reflect
if "%choice%"=="4" goto docs
if "%choice%"=="5" goto end

echo  Invalid choice. Please try again.
echo.
goto menu

:demo
echo.
echo  Running Self-Mastery Demo...
echo  ================================================================================
echo.
cd /d "%~dp0"
py examples\self_mastery_demo.py
echo.
echo  Demo complete.
pause
goto menu

:report
echo.
echo  Generating Mastery Report...
echo  ================================================================================
echo.
cd /d "%~dp0"
py -c "from trading_bot.self_mastery import quick_start; o = quick_start(); print(o.generate_mastery_report())"
echo.
pause
goto menu

:reflect
echo.
echo  Running Reflection Session...
echo  ================================================================================
echo.
cd /d "%~dp0"
py -c "import asyncio; from trading_bot.self_mastery import quick_start; o = quick_start(); asyncio.run(o.reflect('deep')); print(o.get_learning_recommendations())"
echo.
pause
goto menu

:docs
echo.
echo  Opening documentation...
start "" "%~dp0SELF_MASTERY_SYSTEM_COMPLETE.md"
goto menu

:end
echo.
echo  Remember: The goal is not to win - it's to LEARN and IMPROVE.
echo  Every trade is a lesson. Every mistake is valuable data.
echo.
exit
