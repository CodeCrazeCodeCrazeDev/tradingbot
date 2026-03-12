@echo off
setlocal enabledelayedexpansion

:: Integrated Trading Bot Launcher
echo ========================================
echo   Integrated Trading Bot System
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

:: Show menu
:menu
echo.
echo Please select an option:
echo.
echo 1. Run Demo (Shows module integration)
echo 2. Quick Start (Paper mode, EURUSD only)
echo 3. Full System (Paper mode, AI+ML enabled)
echo 4. Interactive Mode
echo 5. Custom Configuration
echo 6. View System Status
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto demo
if "%choice%"=="2" goto quick
if "%choice%"=="3" goto full
if "%choice%"=="4" goto interactive
if "%choice%"=="5" goto custom
if "%choice%"=="6" goto status
if "%choice%"=="7" goto exit
echo Invalid choice, please try again
goto menu

:demo
echo.
echo 🎬 Running Module Integration Demo...
echo.
python run_integrated_system.py --demo
pause
goto menu

:quick
echo.
echo 🚀 Quick Start - Paper Trading Mode
echo.
python run_integrated_system.py --mode paper --symbols EURUSD --auto-start
pause
goto menu

:full
echo.
echo 🔧 Full System - Paper Mode with AI/ML
echo.
python run_integrated_system.py --mode paper --symbols EURUSD,GBPUSD --enable-ai --enable-ml --auto-start
pause
goto menu

:interactive
echo.
echo 🎮 Interactive Mode
echo.
python run_integrated_system.py --mode paper --interactive
pause
goto menu

:custom
echo.
echo ⚙️  Custom Configuration
echo.
set /p symbols="Trading symbols (comma-separated, default: EURUSD): "
if "!symbols!"=="" set symbols=EURUSD

set /p ai="Enable AI features? (y/n, default: y): "
if "!ai!"=="" set ai=y
if /i "!ai!"=="y" (
    set ai_flag=--enable-ai
) else (
    set ai_flag=
)

set /p ml="Enable ML features? (y/n, default: y): "
if "!ml!"=="" set ml=y
if /i "!ml!"=="y" (
    set ml_flag=--enable-ml
) else (
    set ml_flag=
)

set /p start="Auto-start trading? (y/n, default: n): "
if "!start!"=="" set start=n
if /i "!start!"=="y" (
    set start_flag=--auto-start
) else (
    set start_flag=
)

echo.
python run_integrated_system.py --mode paper --symbols !symbols! !ai_flag! !ml_flag! !start_flag!
pause
goto menu

:status
echo.
echo 📊 Checking System Status...
echo.
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from trading_bot import get_registry

async def check_status():
    registry = get_registry()
    registry.discover_modules()
    stats = registry.get_statistics()
    
    print(f'Total modules: {stats[\"total_modules\"]}')
    print(f'Enabled modules: {stats[\"enabled_modules\"]}')
    print()
    print('Modules by category:')
    for cat, info in stats['categories'].items():
        if info['total'] > 0:
            print(f'  {cat}: {info[\"total\"]} modules')

asyncio.run(check_status())
"
pause
goto menu

:exit
echo.
echo 👋 Goodbye!
exit /b 0
