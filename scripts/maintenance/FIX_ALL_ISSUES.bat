@echo off
setlocal enabledelayedexpansion
title AlphaAlgo - Autonomous Code Fixer
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                              ║
echo ║     ███████╗██╗██╗  ██╗     █████╗ ██╗     ██╗                              ║
echo ║     ██╔════╝██║╚██╗██╔╝    ██╔══██╗██║     ██║                              ║
echo ║     █████╗  ██║ ╚███╔╝     ███████║██║     ██║                              ║
echo ║     ██╔══╝  ██║ ██╔██╗     ██╔══██║██║     ██║                              ║
echo ║     ██║     ██║██╔╝ ██╗    ██║  ██║███████╗███████╗                         ║
echo ║     ╚═╝     ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝╚══════╝                         ║
echo ║                                                                              ║
echo ║         AUTONOMOUS CODE FIXER v2.0 - FINDS AND FIXES ALL ISSUES             ║
echo ║                                                                              ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Set Python command
set PYTHON_CMD=py
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found! Please install Python 3.8+
        pause
        exit /b 1
    )
)

echo [INFO] Using Python: %PYTHON_CMD%
echo.

:: Create directories
if not exist "autonomous_logs" mkdir autonomous_logs
if not exist "autonomous_backups" mkdir autonomous_backups

echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                              SELECT MODE                                      ║
echo ╠══════════════════════════════════════════════════════════════════════════════╣
echo ║  [1] FULL FIX    - Scan ALL files, find ALL issues, fix AUTOMATICALLY        ║
echo ║  [2] DRY RUN     - Scan only, show issues but don't modify files             ║
echo ║  [3] QUICK FIX   - Fix only critical syntax errors                           ║
echo ║  [4] VERBOSE     - Full fix with detailed output                             ║
echo ║  [5] EXIT                                                                    ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

set /p choice="Enter choice [1-5]: "

if "%choice%"=="1" goto full_fix
if "%choice%"=="2" goto dry_run
if "%choice%"=="3" goto quick_fix
if "%choice%"=="4" goto verbose_fix
if "%choice%"=="5" exit /b 0

echo Invalid choice. Running full fix...
goto full_fix

:full_fix
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                    RUNNING FULL AUTONOMOUS CODE FIXER
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
%PYTHON_CMD% scripts\fixes\autonomous_code_fixer.py --path "%~dp0"
goto post_fix

:dry_run
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                    RUNNING DRY RUN (NO MODIFICATIONS)
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
%PYTHON_CMD% scripts\fixes\autonomous_code_fixer.py --path "%~dp0" --dry-run
goto end

:quick_fix
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                    RUNNING QUICK SYNTAX FIX
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
%PYTHON_CMD% -c "
import os
import ast
import sys
from pathlib import Path

root = Path(r'%~dp0')
skip_dirs = {'__pycache__', '.git', 'venv', 'autonomous_backups', '.hypothesis', 'mlruns'}
fixed = 0
errors = 0

for py_file in root.rglob('*.py'):
    if any(skip in py_file.parts for skip in skip_dirs):
        continue
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ast.parse(content)
    except SyntaxError as e:
        errors += 1
        print(f'[SYNTAX ERROR] {py_file.relative_to(root)}:{e.lineno} - {e.msg}')

print(f'\nFound {errors} syntax errors')
"
goto end

:verbose_fix
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                    RUNNING VERBOSE FULL FIX
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
%PYTHON_CMD% scripts\fixes\autonomous_code_fixer.py --path "%~dp0" --verbose
goto post_fix

:post_fix
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                    POST-FIX VALIDATION
echo ═══════════════════════════════════════════════════════════════════════════════
echo.

echo [Step 1] Validating core modules...
%PYTHON_CMD% -c "
import sys
modules = [
    'trading_bot',
    'trading_bot.trading_engine',
    'trading_bot.master_orchestrator',
]
success = 0
failed = 0
for mod in modules:
    try:
        __import__(mod)
        print(f'  [OK] {mod}')
        success += 1
    except Exception as e:
        print(f'  [FAIL] {mod}: {e}')
        failed += 1
print(f'\nValidation: {success} OK, {failed} FAILED')
"

echo.
echo [Step 2] Checking for remaining syntax errors...
%PYTHON_CMD% -c "
import os
import ast
from pathlib import Path

root = Path(r'%~dp0')
skip_dirs = {'__pycache__', '.git', 'venv', 'autonomous_backups', '.hypothesis', 'mlruns', 'backup', 'archive'}
errors = []

for py_file in root.rglob('*.py'):
    if any(skip in py_file.parts for skip in skip_dirs):
        continue
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append((py_file.relative_to(root), e.lineno, e.msg))

if errors:
    print(f'Found {len(errors)} remaining syntax errors:')
    for path, line, msg in errors[:10]:
        print(f'  - {path}:{line} - {msg}')
    if len(errors) > 10:
        print(f'  ... and {len(errors) - 10} more')
else:
    print('No syntax errors found!')
"

:end
echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                              FIX COMPLETE
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo Check autonomous_logs\ for detailed reports
echo Check autonomous_backups\ for file backups (if any files were modified)
echo.
pause
