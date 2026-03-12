@echo off
setlocal enabledelayedexpansion
title AlphaAlgo - Continuous Auto-Fix Loop
color 0B

echo.
echo ===============================================================================
echo     CONTINUOUS AUTO-FIX LOOP v2.0
echo     Scan - Fix - Verify - Repeat Until All Issues Resolved
echo ===============================================================================
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
if not exist "auto_fix_backups" mkdir auto_fix_backups
if not exist "auto_fix_logs" mkdir auto_fix_logs

echo ===============================================================================
echo                              SELECT MODE
echo ===============================================================================
echo   [1] FIX TRADING_BOT  - Fix only trading_bot folder (recommended)
echo   [2] FIX ALL          - Fix entire project
echo   [3] FIX WITH VERBOSE - Fix with detailed output
echo   [4] DRY RUN          - Scan only, show what would be fixed
echo   [5] EXIT
echo ===============================================================================
echo.

set /p choice="Enter choice [1-5]: "

if "%choice%"=="1" goto fix_trading_bot
if "%choice%"=="2" goto fix_all
if "%choice%"=="3" goto fix_verbose
if "%choice%"=="4" goto dry_run
if "%choice%"=="5" exit /b 0

echo Invalid choice. Running fix on trading_bot...
goto fix_trading_bot

:fix_trading_bot
echo.
echo [INFO] Starting Continuous Auto-Fix Loop on trading_bot folder...
echo.
%PYTHON_CMD% scripts\fixes\continuous_auto_fixer.py --path "%~dp0trading_bot" --max-iterations 10
goto end

:fix_all
echo.
echo [INFO] Starting Continuous Auto-Fix Loop on entire project...
echo.
%PYTHON_CMD% scripts\fixes\continuous_auto_fixer.py --path "%~dp0" --max-iterations 10
goto end

:fix_verbose
echo.
echo [INFO] Starting Continuous Auto-Fix Loop with verbose output...
echo.
%PYTHON_CMD% scripts\fixes\continuous_auto_fixer.py --path "%~dp0trading_bot" --max-iterations 10 --verbose
goto end

:dry_run
echo.
echo [INFO] Running Dry Run (scan only, no fixes applied)...
echo.
%PYTHON_CMD% -c "
import os
import ast
from pathlib import Path
from collections import defaultdict

root = Path(r'%~dp0trading_bot')
skip_dirs = {'__pycache__', '.git', 'venv', 'auto_fix_backups', 'autonomous_backups', 
             'evolution_backups', 'complete_work_backups', 'fix_backups', 'backup', 'archive'}

typos = {'imoprt': 'import', 'retrun': 'return', 'slef': 'self', 'ture': 'True', 
         'flase': 'False', 'noen': 'None', 'clss': 'class', 'asnyc': 'async'}

issues_by_type = defaultdict(int)
files_with_issues = 0
total_issues = 0

print('Scanning files...')
print()

for py_file in root.rglob('*.py'):
    if any(skip in py_file.parts for skip in skip_dirs):
        continue
    if py_file.name in {'__init__.py', 'setup.py', 'conftest.py'}:
        continue
    
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
        
        file_issues = 0
        
        # Check syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues_by_type['SYNTAX_ERROR'] += 1
            file_issues += 1
            print(f'  [SYNTAX] {py_file.relative_to(root)}:{e.lineno} - {e.msg}')
        
        # Check bare except
        for i, line in enumerate(lines, 1):
            if line.strip() == 'except:':
                issues_by_type['BARE_EXCEPT'] += 1
                file_issues += 1
            if ' == None' in line or ' != None' in line:
                issues_by_type['NONE_COMPARISON'] += 1
                file_issues += 1
        
        if file_issues > 0:
            files_with_issues += 1
            total_issues += file_issues
            
    except Exception as e:
        pass

print()
print('=' * 60)
print('DRY RUN SUMMARY')
print('=' * 60)
print(f'Files with issues: {files_with_issues}')
print(f'Total issues found: {total_issues}')
print()
if issues_by_type:
    print('Issues by type:')
    for issue_type, count in sorted(issues_by_type.items(), key=lambda x: -x[1]):
        print(f'  - {issue_type}: {count}')
print()
print('Run with option [1] to fix these issues automatically.')
"
goto end

:end
echo.
echo ===============================================================================
echo                         AUTO-FIX LOOP COMPLETE
echo ===============================================================================
echo.
echo Check auto_fix_backups\ for file backups
echo Check auto_fix_logs\ for detailed reports
echo.

pause
