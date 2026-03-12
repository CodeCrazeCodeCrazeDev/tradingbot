@echo off
title DeepSeek AI Engineer - 24/7 Autonomous System
color 0A

echo.
echo ========================================================================
echo                    DEEPSEEK AI ENGINEER SYSTEM
echo                    24/7 Autonomous Operation
echo ========================================================================
echo.
echo  Roles:
echo    - Chief AI Engineer
echo    - Architect
echo    - Quant Researcher
echo    - Security Officer
echo    - Self-Evolution Engine
echo    - Performance Optimizer
echo.
echo  IMMUTABLE RULES:
echo    [X] Bot is ALWAYS and ONLY a trading bot
echo    [X] Reward system CANNOT be changed
echo    [X] Bot's fundamental purpose CANNOT be changed
echo.
echo ========================================================================
echo.

:menu
echo Select an option:
echo.
echo   1. Start 24/7 Full Autonomous Mode
echo   2. Start Supervised Mode (with reports)
echo   3. Run Single Maintenance Cycle
echo   4. Run Single Evolution Cycle
echo   5. Run Security Scan Only
echo   6. View System Status
echo   7. Exit
echo.
set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto full_auto
if "%choice%"=="2" goto supervised
if "%choice%"=="3" goto single_maintenance
if "%choice%"=="4" goto single_evolution
if "%choice%"=="5" goto security_scan
if "%choice%"=="6" goto status
if "%choice%"=="7" goto exit

echo Invalid choice. Please try again.
goto menu

:full_auto
echo.
echo Starting 24/7 Full Autonomous Mode...
echo Press Ctrl+C to stop.
echo.
py run_deepseek_24_7.py --mode full_autonomous
goto menu

:supervised
echo.
echo Starting Supervised Mode...
echo Press Ctrl+C to stop.
echo.
py run_deepseek_24_7.py --mode supervised
goto menu

:single_maintenance
echo.
echo Running Single Maintenance Cycle...
echo.
py run_deepseek_24_7.py --mode maintenance_only --single-cycle
pause
goto menu

:single_evolution
echo.
echo Running Single Evolution Cycle...
echo.
py run_deepseek_24_7.py --mode evolution_only --single-cycle
pause
goto menu

:security_scan
echo.
echo Running Security Scan...
echo.
py -c "import asyncio; from pathlib import Path; from trading_bot.deepseek_ai_engineer import SecurityHardening; asyncio.run(SecurityHardening(Path('.')).full_security_scan())"
pause
goto menu

:status
echo.
echo Checking System Status...
echo.
py -c "from pathlib import Path; from trading_bot.deepseek_ai_engineer import verify_purpose_integrity; valid, msg = verify_purpose_integrity(); print(f'Purpose Integrity: {\"VALID\" if valid else \"COMPROMISED\"}')"
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0
