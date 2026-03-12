@echo off
REM ============================================================================
REM AlphaAlgo Unified Approval Dashboard - Quick Launcher
REM ============================================================================

title AlphaAlgo Approval Dashboard
color 0A

cd /d "%~dp0"

:MENU
cls
echo.
echo ================================================================================
echo                    ALPHAALGO UNIFIED APPROVAL DASHBOARD
echo ================================================================================
echo.
echo   Modern, centralized approval system for all bot requests
echo.
echo ================================================================================
echo.
echo   [1] Start Web Dashboard (Recommended)
echo       - Modern web interface
echo       - Access from any device
echo       - Real-time updates
echo.
echo   [2] Start CLI Tool
echo       - Quick terminal access
echo       - Fast approve/reject
echo       - Lightweight
echo.
echo   [3] View Pending Approvals (Quick View)
echo       - List all pending requests
echo       - No interaction needed
echo.
echo   [4] View Statistics
echo       - Approval analytics
echo       - Response times
echo       - Category breakdown
echo.
echo   [5] Integrate Existing Systems
echo       - Migrate old approval systems
echo       - One-time setup
echo.
echo   [6] Exit
echo.
echo ================================================================================
echo.

set /p choice="Select option (1-6): "

if "%choice%"=="1" goto WEB_DASHBOARD
if "%choice%"=="2" goto CLI_TOOL
if "%choice%"=="3" goto QUICK_VIEW
if "%choice%"=="4" goto STATS
if "%choice%"=="5" goto INTEGRATE
if "%choice%"=="6" goto EXIT

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:WEB_DASHBOARD
cls
echo.
echo ================================================================================
echo                    STARTING WEB DASHBOARD
echo ================================================================================
echo.
echo Starting web dashboard on http://localhost:8080
echo.
echo The dashboard will open in your browser automatically.
echo Press Ctrl+C to stop the server.
echo.
echo ================================================================================
echo.

py run_approval_dashboard.py

pause
goto MENU

:CLI_TOOL
cls
echo.
echo ================================================================================
echo                    STARTING CLI TOOL
echo ================================================================================
echo.

py approve.py

pause
goto MENU

:QUICK_VIEW
cls
echo.
echo ================================================================================
echo                    PENDING APPROVALS
echo ================================================================================
echo.

py approve.py list

echo.
pause
goto MENU

:STATS
cls
echo.
echo ================================================================================
echo                    APPROVAL STATISTICS
echo ================================================================================
echo.

py approve.py stats

echo.
pause
goto MENU

:INTEGRATE
cls
echo.
echo ================================================================================
echo                    INTEGRATE EXISTING SYSTEMS
echo ================================================================================
echo.
echo This will integrate the 4 existing approval systems into the unified hub:
echo   1. trading_bot/approval/human_in_loop.py
echo   2. trading_bot/human_layer/approval.py
echo   3. trading_bot/alphaalgo_core/central_controller.py
echo   4. trading_bot/autonomous_pipeline/approval_system.py
echo.
echo This is a one-time setup process.
echo.

set /p confirm="Continue with integration? (y/n): "
if /i not "%confirm%"=="y" goto MENU

echo.
echo Running integration...
echo.

py -c "import asyncio; from trading_bot.unified_approval.integrator import integrate_approval_systems; asyncio.run(integrate_approval_systems())"

echo.
echo Integration complete!
echo.
pause
goto MENU

:EXIT
cls
echo.
echo ================================================================================
echo                    ALPHAALGO UNIFIED APPROVAL DASHBOARD
echo ================================================================================
echo.
echo Thank you for using the unified approval system!
echo.
echo Quick Access:
echo   - Web Dashboard: python run_approval_dashboard.py
echo   - CLI Tool: python approve.py
echo.
echo ================================================================================
echo.
timeout /t 3
exit /b 0
