@echo off
title AlphaAlgo Self-Improvement System
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                                                                      ║
echo ║                    ALPHAALGO SELF-IMPROVEMENT                        ║
echo ║                                                                      ║
echo ║    Find Issues → Propose Fixes → Approve → Apply Changes             ║
echo ║                                                                      ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

:menu
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo                           SELECT AN OPTION
echo ═══════════════════════════════════════════════════════════════════════
echo.
echo   1. Interactive Mode (Full Menu)
echo   2. Quick Scan (Find Issues)
echo   3. Generate Proposals
echo   4. Review Proposals
echo   5. Apply Changes (Dry Run)
echo   6. Full Cycle (Scan → Propose → Review → Apply)
echo   7. Show Status
echo   0. Exit
echo.
echo ═══════════════════════════════════════════════════════════════════════
echo.

set /p choice="Enter your choice (0-7): "

if "%choice%"=="1" goto interactive
if "%choice%"=="2" goto scan
if "%choice%"=="3" goto propose
if "%choice%"=="4" goto review
if "%choice%"=="5" goto apply
if "%choice%"=="6" goto full
if "%choice%"=="7" goto status
if "%choice%"=="0" goto exit

echo Invalid choice. Please try again.
goto menu

:interactive
echo.
echo Starting Interactive Mode...
echo.
py run_self_improvement.py
goto end

:scan
echo.
echo Scanning codebase for issues...
echo.
py run_self_improvement.py scan
pause
goto menu

:propose
echo.
echo Generating fix proposals...
echo.
py run_self_improvement.py propose
pause
goto menu

:review
echo.
echo Starting proposal review...
echo.
py run_self_improvement.py review
goto menu

:apply
echo.
echo Applying changes (DRY RUN - no actual changes)...
echo.
py run_self_improvement.py apply --dry-run
pause
goto menu

:full
echo.
echo Running full improvement cycle...
echo.
py run_self_improvement.py full --auto-approve-safe
pause
goto menu

:status
echo.
echo Showing current status...
echo.
py run_self_improvement.py status
pause
goto menu

:exit
echo.
echo Goodbye!
echo.
exit /b 0

:end
pause
