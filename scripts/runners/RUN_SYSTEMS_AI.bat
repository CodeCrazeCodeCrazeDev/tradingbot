@echo off
title AlphaAlgo Systems AI
color 0A

echo.
echo ============================================================
echo        ALPHAALGO SYSTEMS AI LAUNCHER
echo        Intelligence from Architecture, Not Parameters
echo ============================================================
echo.

:menu
echo Select an option:
echo.
echo   [1] Run Systems AI Demo
echo   [2] View Architecture Documentation
echo   [3] Start Interactive Python Shell
echo   [4] Run Quick Status Check
echo   [5] Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto docs
if "%choice%"=="3" goto shell
if "%choice%"=="4" goto status
if "%choice%"=="5" goto end

echo Invalid choice. Please try again.
goto menu

:demo
echo.
echo Running Systems AI Demo...
echo.
python examples/systems_ai_demo.py
echo.
pause
goto menu

:docs
echo.
echo Opening Architecture Documentation...
echo.
if exist "SYSTEMS_AI_ARCHITECTURE.md" (
    type SYSTEMS_AI_ARCHITECTURE.md | more
) else (
    echo Documentation not found.
)
echo.
pause
goto menu

:shell
echo.
echo Starting Interactive Python Shell...
echo.
echo Use the following to get started:
echo   from trading_bot.systems_ai import *
echo   orchestrator = create_systems_ai(mode='paper')
echo.
python -i -c "from trading_bot.systems_ai import *; print('Systems AI loaded. Try: orchestrator = create_systems_ai(mode=\"paper\")')"
goto menu

:status
echo.
echo Running Quick Status Check...
echo.
python -c "from trading_bot.systems_ai import SystemsAIOrchestrator; print('Systems AI module loaded successfully!'); print('Available components:'); from trading_bot.systems_ai import __all__; print('  ' + ', '.join(__all__[:10]) + '...')"
echo.
pause
goto menu

:end
echo.
echo Goodbye!
echo.
exit /b 0
