@echo off
title Ultimate Integration Trading System
color 0A

:MENU
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                              ║
echo ║     ██╗   ██╗██╗  ████████╗██╗███╗   ███╗ █████╗ ████████╗███████╗          ║
echo ║     ██║   ██║██║  ╚══██╔══╝██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝          ║
echo ║     ██║   ██║██║     ██║   ██║██╔████╔██║███████║   ██║   █████╗            ║
echo ║     ██║   ██║██║     ██║   ██║██║╚██╔╝██║██╔══██║   ██║   ██╔══╝            ║
echo ║     ╚██████╔╝███████╗██║   ██║██║ ╚═╝ ██║██║  ██║   ██║   ███████╗          ║
echo ║      ╚═════╝ ╚══════╝╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝          ║
echo ║                                                                              ║
echo ║           ██╗███╗   ██╗████████╗███████╗ ██████╗ ██████╗  █████╗            ║
echo ║           ██║████╗  ██║╚══██╔══╝██╔════╝██╔════╝ ██╔══██╗██╔══██╗           ║
echo ║           ██║██╔██╗ ██║   ██║   █████╗  ██║  ███╗██████╔╝███████║           ║
echo ║           ██║██║╚██╗██║   ██║   ██╔══╝  ██║   ██║██╔══██╗██╔══██║           ║
echo ║           ██║██║ ╚████║   ██║   ███████╗╚██████╔╝██║  ██║██║  ██║           ║
echo ║           ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝           ║
echo ║                                                                              ║
echo ║                    TRADING SYSTEM v1.0.0                                     ║
echo ║                                                                              ║
echo ║     150+ Modules ^| 300+ Features ^| 50,000+ Lines ^| Production Ready         ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                              MAIN MENU
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo   [1] Run Paper Trading Mode (Safe - No Real Money)
echo   [2] Run Simulation Mode
echo   [3] Run Demo Mode (Quick Test)
echo   [4] Show System Status
echo   [5] List All Modules
echo.
echo   [6] Run with Custom Symbols
echo   [7] Run with AI Disabled
echo   [8] Run with Quantum Computing
echo   [9] Run with Blockchain/DeFi
echo.
echo   [10] Run Full System (All Features)
echo   [11] Run Minimal System (Core Only)
echo.
echo   [12] View Logs
echo   [13] View Documentation
echo.
echo   [0] Exit
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto PAPER
if "%choice%"=="2" goto SIMULATION
if "%choice%"=="3" goto DEMO
if "%choice%"=="4" goto STATUS
if "%choice%"=="5" goto MODULES
if "%choice%"=="6" goto CUSTOM
if "%choice%"=="7" goto NO_AI
if "%choice%"=="8" goto QUANTUM
if "%choice%"=="9" goto BLOCKCHAIN
if "%choice%"=="10" goto FULL
if "%choice%"=="11" goto MINIMAL
if "%choice%"=="12" goto LOGS
if "%choice%"=="13" goto DOCS
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:PAPER
cls
echo.
echo Starting Paper Trading Mode...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode paper --symbols BTCUSDT,EURUSD,ETHUSDT
pause
goto MENU

:SIMULATION
cls
echo.
echo Starting Simulation Mode...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode simulation --symbols BTCUSDT,EURUSD
pause
goto MENU

:DEMO
cls
echo.
echo Running Demo Mode...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --demo
pause
goto MENU

:STATUS
cls
echo.
echo System Status...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --status
pause
goto MENU

:MODULES
cls
echo.
echo Listing All Modules...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --list-modules
pause
goto MENU

:CUSTOM
cls
echo.
echo Custom Symbol Configuration
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
set /p symbols="Enter symbols (comma-separated, e.g., BTCUSDT,ETHUSDT,EURUSD): "
set /p capital="Enter initial capital (default 100000): "
if "%capital%"=="" set capital=100000
echo.
echo Starting with symbols: %symbols%
echo Initial capital: $%capital%
echo.
py run_ultimate_integration.py --mode paper --symbols %symbols% --capital %capital%
pause
goto MENU

:NO_AI
cls
echo.
echo Starting with AI Disabled...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode paper --disable-ai
pause
goto MENU

:QUANTUM
cls
echo.
echo Starting with Quantum Computing Enabled...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode paper --enable-quantum
pause
goto MENU

:BLOCKCHAIN
cls
echo.
echo Starting with Blockchain/DeFi Enabled...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode paper --enable-blockchain
pause
goto MENU

:FULL
cls
echo.
echo Starting Full System (All Features)...
echo ═══════════════════════════════════════════════════════════════════════════════
echo WARNING: This loads ALL modules and may take longer to start.
echo.
py run_ultimate_integration.py --mode full --enable-quantum --enable-blockchain
pause
goto MENU

:MINIMAL
cls
echo.
echo Starting Minimal System (Core Only)...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
py run_ultimate_integration.py --mode minimal --disable-ai
pause
goto MENU

:LOGS
cls
echo.
echo Opening Logs Directory...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
if exist ultimate_logs (
    explorer ultimate_logs
) else (
    echo No logs directory found. Run the system first to generate logs.
)
pause
goto MENU

:DOCS
cls
echo.
echo Opening Documentation...
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
if exist ULTIMATE_INTEGRATION_COMPLETE.md (
    notepad ULTIMATE_INTEGRATION_COMPLETE.md
) else (
    echo Documentation file not found.
)
pause
goto MENU

:EXIT
cls
echo.
echo Thank you for using Ultimate Integration Trading System!
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                           Goodbye!
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
timeout /t 2 >nul
exit /b 0
