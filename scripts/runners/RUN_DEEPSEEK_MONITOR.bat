@echo off
REM DeepSeek Daily Monitoring Script
REM Run this every day to check system health and track progress

echo ========================================
echo DeepSeek Daily Monitoring
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run monitoring script
python DEEPSEEK_MONITORING_SCRIPT.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Monitoring completed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo WARNING: Monitoring detected issues!
    echo Check the logs for details.
    echo ========================================
)

echo.
echo Press any key to exit...
pause >nul
