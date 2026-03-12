@echo off
title Adversarial Curriculum Learning System
color 0A

echo ================================================================================
echo                    ADVERSARIAL CURRICULUM LEARNING SYSTEM
echo ================================================================================
echo.
echo  Train AI trading agents through progressively harder market conditions.
echo.
echo  CORE PRINCIPLES:
echo    - Capital preservation greater than Profit
echo    - Statistical dominance, not perfection
echo    - No shortcuts, no overfitting, no reward hacking
echo.
echo ================================================================================
echo.

:menu
echo  SELECT AN OPTION:
echo.
echo    [1] Run Demo (Recommended for first time)
echo    [2] Run Full Curriculum Training
echo    [3] Run Single Level Test
echo    [4] View Documentation
echo    [5] Exit
echo.
set /p choice="  Enter choice (1-5): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto full_training
if "%choice%"=="3" goto single_level
if "%choice%"=="4" goto docs
if "%choice%"=="5" goto end

echo  Invalid choice. Please try again.
echo.
goto menu

:demo
echo.
echo  Running Adversarial Curriculum Demo...
echo  ================================================================================
echo.
cd /d "%~dp0"
py examples\adversarial_curriculum_demo.py
echo.
echo  Demo complete.
pause
goto menu

:full_training
echo.
echo  Starting Full Curriculum Training...
echo  ================================================================================
echo.
echo  WARNING: Full training can take a long time depending on configuration.
echo.
set /p confirm="  Continue? (y/n): "
if /i "%confirm%"=="y" (
    cd /d "%~dp0"
    py -c "from trading_bot.adversarial_curriculum import quick_start, CurriculumLevel; o = quick_start(); o.run_full_training(CurriculumLevel.LEVEL_5, 20)"
)
echo.
pause
goto menu

:single_level
echo.
echo  Single Level Test
echo  ================================================================================
echo.
echo  Select level (0-10):
set /p level="  Level: "
echo.
echo  Running test at Level %level%...
cd /d "%~dp0"
py -c "from trading_bot.adversarial_curriculum import quick_start, CurriculumLevel; o = quick_start(); o.start_training(CurriculumLevel.LEVEL_%level%); [o.run_episode() for _ in range(10)]; print(o.generate_curriculum_report())"
echo.
pause
goto menu

:docs
echo.
echo  Opening documentation...
start "" "%~dp0ADVERSARIAL_CURRICULUM_COMPLETE.md"
goto menu

:end
echo.
echo  Exiting...
exit
