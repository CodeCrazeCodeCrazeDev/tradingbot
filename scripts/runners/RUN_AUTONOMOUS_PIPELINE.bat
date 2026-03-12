@echo off
title AlphaAlgo - Autonomous Pipeline System
color 0A

:MENU
cls
echo ================================================================================
echo                    AUTONOMOUS PIPELINE SYSTEM
echo ================================================================================
echo.
echo  Discover -^> Sandbox -^> Test -^> Approve -^> Deploy
echo.
echo  Automatically finds, tests, and deploys new data sources and models
echo.
echo ================================================================================
echo.
echo  [1] Run Full Pipeline (Discover + Test + Approve + Deploy)
echo  [2] Discovery Only (Find new data sources and models)
echo  [3] Testing Only (Test discovered items)
echo  [4] Interactive Mode (Manual control)
echo  [5] View Pending Approvals
echo  [6] View Statistics
echo  [7] Help / Documentation
echo  [Q] Quit
echo.
echo ================================================================================
echo.

set /p choice="Select option: "

if "%choice%"=="1" goto FULL_PIPELINE
if "%choice%"=="2" goto DISCOVERY_ONLY
if "%choice%"=="3" goto TESTING_ONLY
if "%choice%"=="4" goto INTERACTIVE
if "%choice%"=="5" goto VIEW_APPROVALS
if "%choice%"=="6" goto VIEW_STATS
if "%choice%"=="7" goto HELP
if /i "%choice%"=="Q" goto QUIT

echo Invalid option. Press any key to continue...
pause >nul
goto MENU

:FULL_PIPELINE
cls
echo ================================================================================
echo                    RUNNING FULL PIPELINE
echo ================================================================================
echo.
echo This will:
echo  1. Discover new data sources (stock, forex, crypto, sentiment, satellite, etc.)
echo  2. Discover new models and trading modules
echo  3. Sandbox and test each item
echo  4. Request human approval for deployment
echo  5. Deploy approved items to live production
echo.
echo Press Ctrl+C to cancel...
echo.
py run_autonomous_pipeline.py
echo.
echo Pipeline complete. Press any key to continue...
pause >nul
goto MENU

:DISCOVERY_ONLY
cls
echo ================================================================================
echo                    DISCOVERY PHASE ONLY
echo ================================================================================
echo.
echo Discovering new data sources and models...
echo.
py run_autonomous_pipeline.py --discover-only
echo.
echo Discovery complete. Press any key to continue...
pause >nul
goto MENU

:TESTING_ONLY
cls
echo ================================================================================
echo                    TESTING PHASE ONLY
echo ================================================================================
echo.
echo Testing discovered items...
echo.
py run_autonomous_pipeline.py --test-only
echo.
echo Testing complete. Press any key to continue...
pause >nul
goto MENU

:INTERACTIVE
cls
echo ================================================================================
echo                    INTERACTIVE MODE
echo ================================================================================
echo.
py run_autonomous_pipeline.py --interactive
goto MENU

:VIEW_APPROVALS
cls
echo ================================================================================
echo                    PENDING APPROVALS
echo ================================================================================
echo.
if exist approvals\*.txt (
    echo Approval requests found:
    echo.
    dir /b approvals\*_REVIEW.txt
    echo.
    echo To review, open files in: approvals\
) else (
    echo No pending approvals found.
)
echo.
echo Press any key to continue...
pause >nul
goto MENU

:VIEW_STATS
cls
echo ================================================================================
echo                    PIPELINE STATISTICS
echo ================================================================================
echo.
if exist autonomous_pipeline_data\*.json (
    echo Pipeline runs found. Viewing latest...
    echo.
    py -c "import json; from pathlib import Path; files = list(Path('autonomous_pipeline_data').glob('*.json')); latest = max(files, key=lambda p: p.stat().st_mtime) if files else None; data = json.load(open(latest)) if latest else {}; print(f'Run ID: {data.get(\"run_id\", \"N/A\")}'); print(f'Status: {data.get(\"status\", \"N/A\")}'); print(f'Discovered: {data.get(\"items_discovered\", 0)}'); print(f'Tested: {data.get(\"items_tested\", 0)}'); print(f'Approved: {data.get(\"items_approved\", 0)}'); print(f'Deployed: {data.get(\"items_deployed\", 0)}');"
) else (
    echo No pipeline runs found. Run the pipeline first.
)
echo.
echo Press any key to continue...
pause >nul
goto MENU

:HELP
cls
echo ================================================================================
echo                    AUTONOMOUS PIPELINE - HELP
echo ================================================================================
echo.
echo OVERVIEW:
echo   The Autonomous Pipeline automatically discovers, tests, and deploys new
echo   data sources and trading models with human approval.
echo.
echo WORKFLOW:
echo   1. DISCOVERY - Finds new high-quality data sources:
echo      - Stock data (Yahoo, Alpha Vantage, IEX, Polygon, etc.)
echo      - Forex data (OANDA, Dukascopy, FXCM, etc.)
echo      - Crypto data (Binance, Coinbase, Kraken, etc.)
echo      - Alternative data (satellite imagery, sentiment, social media, etc.)
echo      - ML models and trading modules
echo.
echo   2. SANDBOX - Isolates items for safe testing:
echo      - Resource limits (CPU, memory, network)
echo      - Security restrictions
echo      - Performance monitoring
echo.
echo   3. TESTING - Runs comprehensive automated tests:
echo      - Data quality tests
echo      - Performance tests
echo      - Risk assessment
echo      - Integration tests
echo.
echo   4. APPROVAL - Requests human approval:
echo      - Generates human-readable summaries
echo      - Risk assessment
echo      - Benefit analysis
echo      - Approval tracking
echo.
echo   5. DEPLOYMENT - Safely deploys to production:
echo      - Staged deployment (sandbox -^> staging -^> production)
echo      - Gradual rollout
echo      - Health monitoring
echo      - Automatic rollback on failure
echo.
echo APPROVAL PROCESS:
echo   1. Review approval requests in: approvals\
echo   2. Each request has a *_REVIEW.txt file with details
echo   3. Use Interactive Mode to approve/reject items
echo.
echo SAFETY:
echo   - All items are sandboxed before testing
echo   - Human approval required before deployment
echo   - Automatic rollback on deployment failure
echo   - Resource limits prevent system overload
echo.
echo For more information, see: AUTONOMOUS_PIPELINE_COMPLETE.md
echo.
echo Press any key to continue...
pause >nul
goto MENU

:QUIT
cls
echo.
echo Shutting down Autonomous Pipeline System...
echo.
timeout /t 2 >nul
exit

:ERROR
echo.
echo ERROR: An error occurred. Check autonomous_pipeline.log for details.
echo.
pause
goto MENU
