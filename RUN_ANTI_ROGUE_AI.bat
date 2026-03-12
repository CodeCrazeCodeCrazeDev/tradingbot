@echo off
title Anti-Rogue AI System Launcher
color 0A

:menu
cls
echo ================================================================================
echo                    ANTI-ROGUE AI SYSTEM LAUNCHER
echo ================================================================================
echo.
echo This system prevents AI from going rogue and forces market understanding.
echo.
echo [1] Run Full Demo (All 7 scenarios)
echo [2] Test Safe Action
echo [3] Test Constraint Violation
echo [4] Test Market Understanding
echo [5] Test Rogue Detection
echo [6] Test Kill Switch
echo [7] Show System Status
echo [8] Integration Guide
echo [9] Exit
echo.
echo ================================================================================
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto full_demo
if "%choice%"=="2" goto safe_action
if "%choice%"=="3" goto constraint_test
if "%choice%"=="4" goto understanding_test
if "%choice%"=="5" goto rogue_test
if "%choice%"=="6" goto kill_switch_test
if "%choice%"=="7" goto status
if "%choice%"=="8" goto integration
if "%choice%"=="9" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:full_demo
cls
echo ================================================================================
echo                         RUNNING FULL DEMO
echo ================================================================================
echo.
py examples/anti_rogue_ai_demo.py
echo.
pause
goto menu

:safe_action
cls
echo ================================================================================
echo                    TESTING SAFE ACTION
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_safe_action; demo_safe_action()"
echo.
pause
goto menu

:constraint_test
cls
echo ================================================================================
echo                  TESTING CONSTRAINT VIOLATION
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_constraint_violation; demo_constraint_violation()"
echo.
pause
goto menu

:understanding_test
cls
echo ================================================================================
echo               TESTING MARKET UNDERSTANDING REQUIREMENT
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_insufficient_understanding; demo_insufficient_understanding()"
echo.
pause
goto menu

:rogue_test
cls
echo ================================================================================
echo                    TESTING ROGUE DETECTION
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_rogue_behavior; demo_rogue_behavior()"
echo.
pause
goto menu

:kill_switch_test
cls
echo ================================================================================
echo                    TESTING KILL SWITCH
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_kill_switch; demo_kill_switch()"
echo.
pause
goto menu

:status
cls
echo ================================================================================
echo                      SYSTEM STATUS
echo ================================================================================
echo.
py -c "from examples.anti_rogue_ai_demo import demo_comprehensive_status; demo_comprehensive_status()"
echo.
pause
goto menu

:integration
cls
echo ================================================================================
echo                    INTEGRATION GUIDE
echo ================================================================================
echo.
echo QUICK INTEGRATION:
echo.
echo 1. Import the system:
echo    from trading_bot.anti_rogue_ai import quick_start
echo.
echo 2. Initialize:
echo    anti_rogue = quick_start({'oversight_level': 'moderate'})
echo.
echo 3. Validate before trading:
echo    check = anti_rogue.validate_action(
echo        action_type='trade',
echo        action=signal,
echo        reasoning=reasoning,
echo        market_data=market_data,
echo        metrics=metrics
echo    )
echo.
echo 4. Execute only if safe:
echo    if check.can_proceed:
echo        execute_trade(signal)
echo.
echo See ANTI_ROGUE_AI_COMPLETE.md for full documentation.
echo.
pause
goto menu

:end
cls
echo.
echo Thank you for using the Anti-Rogue AI System!
echo Your AI is now safe, controllable, and forced to understand markets.
echo.
timeout /t 2 >nul
exit
