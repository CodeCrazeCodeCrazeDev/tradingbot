@echo off
title Unified AI Brain - The ONE Trading System
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    UNIFIED AI BRAIN LAUNCHER                                  ║
echo ║                                                                               ║
echo ║  The ONE system that integrates ALL 2900+ files into a single AI             ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:MENU
echo.
echo  ┌─────────────────────────────────────────────────────────────────┐
echo  │                    SELECT AN OPTION                             │
echo  ├─────────────────────────────────────────────────────────────────┤
echo  │  1. Interactive Mode (Recommended)                              │
echo  │  2. Quick Start - Paper Trading                                 │
echo  │  3. Quick Start - Simulation Mode                               │
echo  │  4. Run with Custom Symbols                                     │
echo  │  5. Debug Mode (Verbose Logging)                                │
echo  │  6. Show Help                                                   │
echo  │  7. Exit                                                        │
echo  └─────────────────────────────────────────────────────────────────┘
echo.

set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto INTERACTIVE
if "%choice%"=="2" goto QUICK_PAPER
if "%choice%"=="3" goto QUICK_SIM
if "%choice%"=="4" goto CUSTOM
if "%choice%"=="5" goto DEBUG
if "%choice%"=="6" goto HELP
if "%choice%"=="7" goto EXIT

echo Invalid choice. Please try again.
goto MENU

:INTERACTIVE
echo.
echo Starting Interactive Mode...
echo.
python run_unified_brain.py --interactive
goto END

:QUICK_PAPER
echo.
echo Starting Quick Paper Trading...
echo Symbols: BTCUSDT, EURUSD
echo Capital: $100,000
echo.
python run_unified_brain.py --quick-start --mode paper
goto END

:QUICK_SIM
echo.
echo Starting Simulation Mode...
echo.
python run_unified_brain.py --quick-start --mode simulation
goto END

:CUSTOM
echo.
set /p symbols="Enter symbols (space-separated, e.g., BTCUSDT ETHUSDT EURUSD): "
set /p capital="Enter initial capital (default 100000): "
if "%capital%"=="" set capital=100000
echo.
echo Starting with symbols: %symbols%
echo Capital: $%capital%
echo.
python run_unified_brain.py --quick-start --mode paper --symbols %symbols% --capital %capital%
goto END

:DEBUG
echo.
echo Starting Debug Mode (Verbose Logging)...
echo.
python run_unified_brain.py --interactive --log-level DEBUG
goto END

:HELP
echo.
python run_unified_brain.py --help
echo.
pause
goto MENU

:EXIT
echo.
echo Goodbye!
exit /b 0

:END
echo.
echo ═══════════════════════════════════════════════════════════════════
echo Session ended.
echo ═══════════════════════════════════════════════════════════════════
pause
goto MENU
