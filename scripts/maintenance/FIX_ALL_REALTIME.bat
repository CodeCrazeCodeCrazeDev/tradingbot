@echo off
title AlphaAlgo Real-Time Dependency Fixer
color 0A

echo ============================================================
echo   ALPHAALGO REAL-TIME DEPENDENCY FIXER
echo ============================================================
echo.
echo This will fix ALL dependencies and ensure real-time capability.
echo.

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

echo [INFO] Starting dependency fix...
echo.

REM Run the Python script
python "%~dp0FIX_ALL_REALTIME.py"

echo.
echo ============================================================
if %ERRORLEVEL% EQU 0 (
    echo   SUCCESS! All dependencies fixed.
    color 0A
) else (
    echo   Some issues remain. Check output above.
    color 0C
)
echo ============================================================
echo.

pause
