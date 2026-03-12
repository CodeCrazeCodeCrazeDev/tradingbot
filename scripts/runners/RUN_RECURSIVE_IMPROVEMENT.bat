@echo off
echo ================================================================================
echo RECURSIVE SELF-IMPROVEMENT SYSTEM
echo ================================================================================
echo.

:menu
echo.
echo Select an option:
echo.
echo 1. Run Recursive Improvement Demo
echo 2. Start Continuous Improvement
echo 3. Run Single Improvement Cycle
echo 4. View System Status
echo 5. Clean and Integrate with DeepSeek
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto continuous
if "%choice%"=="3" goto single_cycle
if "%choice%"=="4" goto status
if "%choice%"=="5" goto deepseek
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running Recursive Improvement Demo...
echo ================================================================================
python examples/recursive_improvement_demo.py
echo.
pause
goto menu

:continuous
echo.
echo Starting Continuous Improvement...
echo ================================================================================
python -c "import asyncio; from trading_bot.recursive_improvement import create_recursive_system; asyncio.run(create_recursive_system(auto_start=True))"
echo.
pause
goto menu

:single_cycle
echo.
echo Running Single Improvement Cycle...
echo ================================================================================
python -c "import asyncio; from trading_bot.recursive_improvement import quick_start; orchestrator = quick_start(); asyncio.run(orchestrator.run_improvement_cycle())"
echo.
pause
goto menu

:status
echo.
echo System Status...
echo ================================================================================
python -c "from trading_bot.recursive_improvement import quick_start; orchestrator = quick_start(); print(orchestrator.get_comprehensive_summary())"
echo.
pause
goto menu

:deepseek
echo.
echo Running DeepSeek Integration and Cleanup...
echo ================================================================================
python run_deepseek_complete_work.py
echo.
pause
goto menu

:end
echo.
echo Exiting...
exit
