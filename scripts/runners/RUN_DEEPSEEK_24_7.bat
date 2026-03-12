@echo off
title DeepSeek Autonomous Engineer - 24/7 Mode
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║     🤖 DEEPSEEK AUTONOMOUS ENGINEER - 24/7 MODE 🤖           ║
echo  ╠══════════════════════════════════════════════════════════════╣
echo  ║  Running continuously until 8 PM                             ║
echo  ║  Auto-fixing issues WITHOUT human approval                   ║
echo  ║  Protected files: risk, security, credentials                ║
echo  ║  All changes backed up and logged                            ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo Starting DeepSeek Autonomous Mode...
echo.

py run_deepseek_autonomous_24_7.py

echo.
echo Session complete. Check autonomous_logs for details.
pause
