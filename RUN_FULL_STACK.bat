@echo off
title Full Stack Trading Bot
color 0A

echo.
echo ========================================================================
echo                    FULL STACK TRADING BOT
echo                  All Systems Contributing
echo ========================================================================
echo.
echo   This will start ALL 4 layers:
echo.
echo   LAYER 1: Core Systems (Elite AI, Market Intelligence, etc.)
echo   LAYER 2: Background Services (Learning, Evolution, Sentiment)
echo   LAYER 3: Scheduled Jobs (Nightly training, Weekly testing)
echo   LAYER 4: Coordination (Multi-agent delegation)
echo.
echo ========================================================================
echo.
pause

echo.
echo [1/5] Checking Redis...
where redis-server >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Redis not found. Please run: choco install redis-64
    pause
    exit /b 1
)

echo [2/5] Starting Redis Server...
start "Redis Server" /MIN redis-server
timeout /t 3 /nobreak >nul

echo [3/5] Starting Master Orchestrator (Background Services)...
start "Master Orchestrator" /MIN py master_orchestrator.py
timeout /t 5 /nobreak >nul

echo [4/5] Verifying services...
py -c "import redis; r=redis.Redis(); r.ping(); print('Redis: OK')"
if %ERRORLEVEL% NEQ 0 (
    echo Redis connection failed!
    pause
    exit /b 1
)

echo [5/5] Starting Main Trading Bot (Layer 1)...
echo.
echo ========================================================================
echo   FULL STACK IS NOW RUNNING
echo ========================================================================
echo.
echo   Redis Server: Running (minimized)
echo   Background Services: Running (minimized)
echo   Main Trading Bot: Starting now...
echo.
echo   To view status: py master_orchestrator.py --status
echo   To stop all: Close this window or press Ctrl+C
echo.
echo ========================================================================
echo.

REM Start main.py with all systems enabled
py main.py --symbol EURUSD --use-all-systems --analysis-depth standard

echo.
echo Main trading bot stopped. Cleaning up...
taskkill /FI "WINDOWTITLE eq Redis Server" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Master Orchestrator" /F >nul 2>&1
echo.
echo Full stack shutdown complete.
pause
