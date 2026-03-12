@echo off
echo ======================================================================
echo DeepSeek Corruption Fixer
echo ======================================================================
echo.
echo This script will fix Python files corrupted by the DeepSeek auto-fixer.
echo Backups will be created before any changes.
echo.
pause

echo.
echo [1/2] Running basic fixer...
py scripts\fixes\fix_corrupted_imports.py
echo.

echo [2/2] Running aggressive fixer...
py scripts\fixes\fix_corrupted_imports_v2.py
echo.

echo ======================================================================
echo Checking remaining errors...
echo ======================================================================
py -c "import os, ast; from pathlib import Path; errors=[(str(fp).split('trading_bot\\')[-1], e.lineno, e.msg) for root, dirs, files in os.walk(r'trading_bot') if not dirs.__setitem__(slice(None), [d for d in dirs if d != '__pycache__']) else True for f in files if f.endswith('.py') for fp in [Path(root)/f] for content in [fp.read_text(encoding='utf-8', errors='ignore')] for e in [None] if (lambda: (ast.parse(content), None)[1])() is None or True]; print(f'Remaining errors: {len([1 for _ in errors if _])}' if errors else 'All files OK!')" 2>nul || echo Error checking files

echo.
echo Done! See DEEPSEEK_CORRUPTION_FIX_REPORT.md for details.
pause
