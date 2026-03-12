@echo off
title DeepSeek Autonomous Software Engineer
color 0A

echo ============================================================
echo    DeepSeek Autonomous Software Engineer
echo    Autonomous Codebase Analysis and Improvement
echo ============================================================
echo.

:menu
echo Choose an option:
echo.
echo   1. Run Demo (Recommended for first time)
echo   2. Analyze Codebase
echo   3. Security Audit
echo   4. Architecture Review
echo   5. Interactive Mode
echo   6. View Documentation
echo   7. Exit
echo.
set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto analyze
if "%choice%"=="3" goto security
if "%choice%"=="4" goto architecture
if "%choice%"=="5" goto interactive
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto exit

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running Demo...
echo.
python -m trading_bot.deepseek_engineer.examples.deepseek_engineer_demo
pause
goto menu

:analyze
echo.
echo Analyzing Codebase...
echo.
python -c "import asyncio; from trading_bot.deepseek_engineer import AutonomousEngineer, TaskType; async def main(): e = AutonomousEngineer('.'); await e.initialize(); r = await e.execute_task(TaskType.ANALYZE_CODEBASE); print(f'Files: {r.analysis.total_files}, Issues: {r.analysis.total_issues}'); asyncio.run(main())"
pause
goto menu

:security
echo.
echo Running Security Audit...
echo.
python -c "import asyncio; from trading_bot.deepseek_engineer import AutonomousEngineer, TaskType; async def main(): e = AutonomousEngineer('.'); await e.initialize(); r = await e.execute_task(TaskType.SECURITY_AUDIT); print(r.message); asyncio.run(main())"
pause
goto menu

:architecture
echo.
echo Running Architecture Review...
echo.
python -c "import asyncio; from trading_bot.deepseek_engineer import AutonomousEngineer, TaskType; async def main(): e = AutonomousEngineer('.'); await e.initialize(); r = await e.execute_task(TaskType.ARCHITECTURE_REVIEW); print(r.message); asyncio.run(main())"
pause
goto menu

:interactive
echo.
echo Starting Interactive Mode...
echo.
python -i -c "import asyncio; from trading_bot.deepseek_engineer import *; print('DeepSeek Engineer loaded. Use: engineer = asyncio.run(quick_start(\".\"))')"
goto menu

:docs
echo.
echo Opening Documentation...
echo.
start notepad DEEPSEEK_AUTONOMOUS_ENGINEER.md
goto menu

:exit
echo.
echo Goodbye!
echo.
exit /b 0
