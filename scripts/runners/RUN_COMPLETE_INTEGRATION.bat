@echo off
title AlphaAlgo Complete System Integration
color 0A

:menu
cls
echo ================================================================================
echo                    ALPHAALGO COMPLETE SYSTEM INTEGRATION
echo                         2000+ Modules | 170+ Packages
echo ================================================================================
echo.
echo   IMMUTABLE PRINCIPLES:
echo   1. RISK FIRST: Layer 4 (MSOS) has VETO power over all trades
echo   2. HUMAN CONTROL: Human override ALWAYS works
echo   3. FAIL-SAFE: Default to NO TRADE when uncertain
echo   4. SURVIVAL: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
echo.
echo ================================================================================
echo.
echo   [1] Discover All Modules (Quick scan)
echo   [2] Discover and Export Inventory (JSON)
echo   [3] Load All Modules (Lazy loading)
echo   [4] Load All Modules (Full import)
echo   [5] Initialize All Modules
echo   [6] Start Complete System
echo   [7] View Module Inventory
echo   [8] Exit
echo.
echo ================================================================================
set /p choice="Select option (1-8): "

if "%choice%"=="1" goto discover
if "%choice%"=="2" goto export
if "%choice%"=="3" goto load_lazy
if "%choice%"=="4" goto load_full
if "%choice%"=="5" goto init
if "%choice%"=="6" goto start
if "%choice%"=="7" goto view
if "%choice%"=="8" goto end

echo Invalid option. Please try again.
timeout /t 2 >nul
goto menu

:discover
cls
echo Running module discovery...
echo.
py run_complete_integration.py --mode discover
echo.
pause
goto menu

:export
cls
echo Running module discovery with export...
echo.
py run_complete_integration.py --mode discover --export
echo.
pause
goto menu

:load_lazy
cls
echo Loading all modules (lazy)...
echo.
py run_complete_integration.py --mode load --lazy
echo.
pause
goto menu

:load_full
cls
echo Loading all modules (full import)...
echo.
py run_complete_integration.py --mode load --verbose
echo.
pause
goto menu

:init
cls
echo Initializing all modules...
echo.
py run_complete_integration.py --mode init --lazy
echo.
pause
goto menu

:start
cls
echo Starting complete system...
echo.
py run_complete_integration.py --mode start --lazy
echo.
pause
goto menu

:view
cls
echo.
echo Looking for latest inventory file...
echo.
dir /b /o-d complete_module_inventory_*.json 2>nul | findstr /n "^" | findstr "^1:"
if errorlevel 1 (
    echo No inventory file found. Run option 2 first.
) else (
    for /f "tokens=2 delims=:" %%a in ('dir /b /o-d complete_module_inventory_*.json 2^>nul ^| findstr /n "^" ^| findstr "^1:"') do (
        echo Opening: %%a
        notepad %%a
    )
)
echo.
pause
goto menu

:end
echo.
echo Goodbye!
timeout /t 2 >nul
exit
