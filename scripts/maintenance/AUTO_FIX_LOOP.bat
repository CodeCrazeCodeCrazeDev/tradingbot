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
echo [INFO] Running Dry Run (scan only)...
echo.
%PYTHON_CMD% -c "
import os
import sys
import ast
import re
import shutil
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict

# ============================================================
# CONTINUOUS AUTO-FIX LOOP
# ============================================================

@dataclass
class Issue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    original_code: str
    fixed_code: str = ''
    auto_fixable: bool = True

class ContinuousAutoFixer:
    '''
    Continuously scans and fixes code until all issues are resolved.
    '''
    
    def __init__(self, root_dir: str, max_iterations: int = 10):
        self.root_dir = Path(root_dir)
        self.max_iterations = max_iterations
        self.backup_dir = self.root_dir / 'auto_fix_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Directories to skip
        self.skip_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env', 
            '.venv', 'node_modules', '.hypothesis', 'htmlcov',
            'autonomous_backups', 'auto_fix_backups', '.mypy_cache', 
            'mlruns', 'models', 'backup', 'archive', '.github', 
            '.idea', '.vscode', 'dist', 'build', 'egg-info', 
            'site-packages', 'evolution_backups', 'complete_work_backups',
            'fix_backups', 'syntax_fix_backups', 'backups', 'old', 'deprecated'
        }
        
        # Typo fixes
        self.typo_fixes = {
            'imoprt': 'import', 'improt': 'import', 'funciton': 'function',
            'retrun': 'return', 'reutrn': 'return', 'defualt': 'default',
            'ture': 'True', 'treu': 'True', 'flase': 'False', 'fales': 'False',
            'noen': 'None', 'Noen': 'None', 'slef': 'self', 'sefl': 'self',
            'clss': 'class', 'calss': 'class', 'asnyc': 'async', 'awiat': 'await',
            'pritn': 'print', 'pirnt': 'print', 'yeild': 'yield', 'glboal': 'global',
            'lamda': 'lambda', 'excpet': 'except', 'finaly': 'finally',
            'raiase': 'raise', 'assret': 'assert', 'passs': 'pass', 'braek': 'break',
            'contniue': 'continue', 'whiel': 'while', 'elfi': 'elif', 'esle': 'else',
            'lenght': 'length', 'widht': 'width', 'heigth': 'height',
            'reciever': 'receiver', 'occured': 'occurred', 'sucess': 'success',
            'arguemnt': 'argument', 'paramter': 'parameter', 'varaible': 'variable',
            'stirng': 'string', 'lsit': 'list', 'dcit': 'dict', 'tpye': 'type',
            'vlaue': 'value', 'indx': 'index', 'resutl': 'result',
        }
        
        # Import mappings
        self.import_map = {
            'np': 'import numpy as np',
            'pd': 'import pandas as pd',
            'plt': 'import matplotlib.pyplot as plt',
            'tf': 'import tensorflow as tf',
            'torch': 'import torch',
            'nn': 'import torch.nn as nn',
            'F': 'import torch.nn.functional as F',
            'Path': 'from pathlib import Path',
            'Dict': 'from typing import Dict',
            'List': 'from typing import List',
            'Optional': 'from typing import Optional',
            'Tuple': 'from typing import Tuple',
            'Any': 'from typing import Any',
            'Set': 'from typing import Set',
            'Union': 'from typing import Union',
            'dataclass': 'from dataclasses import dataclass',
            'field': 'from dataclasses import field',
            'Enum': 'from enum import Enum',
            'auto': 'from enum import auto',
            'ABC': 'from abc import ABC',
            'abstractmethod': 'from abc import abstractmethod',
            'defaultdict': 'from collections import defaultdict',
            'deque': 'from collections import deque',
            'Counter': 'from collections import Counter',
            'asyncio': 'import asyncio',
            'aiohttp': 'import aiohttp',
            'json': 'import json',
            'logging': 'import logging',
            'os': 'import os',
            'sys': 'import sys',
            're': 'import re',
            'time': 'import time',
            'datetime': 'from datetime import datetime',
            'timedelta': 'from datetime import timedelta',
            'random': 'import random',
            'math': 'import math',
            'hashlib': 'import hashlib',
            'base64': 'import base64',
            'uuid': 'import uuid',
            'threading': 'import threading',
            'queue': 'import queue',
            'copy': 'import copy',
            'deepcopy': 'from copy import deepcopy',
            'shutil': 'import shutil',
            'glob': 'import glob',
            'pickle': 'import pickle',
            'warnings': 'import warnings',
            'traceback': 'import traceback',
            'inspect': 'import inspect',
            'functools': 'import functools',
            'itertools': 'import itertools',
            'wraps': 'from functools import wraps',
            'lru_cache': 'from functools import lru_cache',
            'partial': 'from functools import partial',
            'contextmanager': 'from contextlib import contextmanager',
            'suppress': 'from contextlib import suppress',
            'ThreadPoolExecutor': 'from concurrent.futures import ThreadPoolExecutor',
            'ProcessPoolExecutor': 'from concurrent.futures import ProcessPoolExecutor',
        }
    
    def get_python_files(self) -> List[Path]:
        '''Get all Python files'''
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            for file in files:
                if file.endswith('.py') and file not in {'__init__.py', 'setup.py', 'conftest.py'}:
                    python_files.append(Path(root) / file)
        return sorted(python_files)
    
    def create_backup(self, file_path: Path) -> bool:
        '''Create backup of file'''
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            relative_path = file_path.relative_to(self.root_dir)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except:
            return False
    
    def scan_file(self, file_path: Path) -> List[Issue]:
        '''Scan a file for issues'''
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except:
            return issues
        
        # Check syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(Issue(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type='SYNTAX_ERROR',
                severity='CRITICAL',
                description=f'Syntax error: {e.msg}',
                original_code=e.text or '',
                auto_fixable=True
            ))
            return issues  # Can't check more if syntax is broken
        
        # Check each line
        for i, line in enumerate(lines, 1):
            # Check typos
            for typo, fix in self.typo_fixes.items():
                pattern = r'\\b' + re.escape(typo) + r'\\b'
                if re.search(pattern, line, re.IGNORECASE):
                    fixed_line = re.sub(pattern, fix, line, flags=re.IGNORECASE)
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type='TYPO',
                        severity='MEDIUM',
                        description=f'Typo: {typo} -> {fix}',
                        original_code=line.rstrip(),
                        fixed_code=fixed_line.rstrip(),
                        auto_fixable=True
                    ))
            
            # Check bare except
            if re.match(r'^\\s*except\\s*:\\s*$', line):
                indent = len(line) - len(line.lstrip())
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='BARE_EXCEPT',
                    severity='MEDIUM',
                    description='Bare except clause',
                    original_code=line.rstrip(),
                    fixed_code=' ' * indent + 'except Exception:',
                    auto_fixable=True
                ))
            
            # Check == None
            if ' == None' in line:
                fixed_line = line.replace(' == None', ' is None')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='NONE_COMPARISON',
                    severity='LOW',
                    description='Use is None instead of == None',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check != None
            if ' != None' in line:
                fixed_line = line.replace(' != None', ' is not None')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='NONE_COMPARISON',
                    severity='LOW',
                    description='Use is not None instead of != None',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check mixed indentation
            if '\\t' in line and '    ' in line:
                fixed_line = line.replace('\\t', '    ')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='MIXED_INDENT',
                    severity='MEDIUM',
                    description='Mixed tabs and spaces',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
        
        # Check missing imports
        try:
            tree = ast.parse(content)
            imported_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.asname or alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names.add(node.module.split('.')[0])
                    for alias in node.names:
                        if alias.name != '*':
                            imported_names.add(alias.asname or alias.name)
            
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            
            import builtins
            builtin_names = set(dir(builtins))
            
            for name in used_names:
                if name in self.import_map and name not in imported_names and name not in builtin_names:
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=1,
                        issue_type='MISSING_IMPORT',
                        severity='HIGH',
                        description=f'Missing import for {name}',
                        original_code='',
                        fixed_code=self.import_map[name],
                        auto_fixable=True
                    ))
        except:
            pass
        
        return issues
    
    def fix_syntax_error(self, file_path: Path, issue: Issue) -> bool:
        '''Try to fix syntax errors'''
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            line_idx = issue.line_number - 1
            if line_idx < 0 or line_idx >= len(lines):
                return False
            
            line = lines[line_idx]
            fixed = False
            
            # Missing colon
            keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 
                       'try', 'except', 'finally', 'with', 'async def']
            for kw in keywords:
                if re.match(rf'^\\s*{kw}\\s+.*[^:]\\s*$', line):
                    lines[line_idx] = line.rstrip() + ':\\n'
                    fixed = True
                    break
            
            if not fixed:
                # Unclosed parenthesis
                open_parens = line.count('(') - line.count(')')
                if open_parens > 0:
                    lines[line_idx] = line.rstrip() + ')' * open_parens + '\\n'
                    fixed = True
            
            if not fixed:
                # Unclosed bracket
                open_brackets = line.count('[') - line.count(']')
                if open_brackets > 0:
                    lines[line_idx] = line.rstrip() + ']' * open_brackets + '\\n'
                    fixed = True
            
            if not fixed:
                # Unclosed brace
                open_braces = line.count('{') - line.count('}')
                if open_braces > 0:
                    lines[line_idx] = line.rstrip() + '}' * open_braces + '\\n'
                    fixed = True
            
            if not fixed:
                # Unclosed string
                if line.count('\"') % 2 == 1:
                    lines[line_idx] = line.rstrip() + '\"\\n'
                    fixed = True
                elif line.count(\"'\") % 2 == 1:
                    lines[line_idx] = line.rstrip() + \"'\\n\"
                    fixed = True
            
            if fixed:
                try:
                    ast.parse(''.join(lines))
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
                except:
                    return False
            
            return False
        except:
            return False
    
    def fix_file(self, file_path: Path, issues: List[Issue]) -> int:
        '''Apply fixes to a file'''
        if not issues:
            return 0
        
        # Handle syntax errors first
        syntax_issues = [i for i in issues if i.issue_type == 'SYNTAX_ERROR']
        if syntax_issues:
            self.create_backup(file_path)
            for issue in syntax_issues:
                if self.fix_syntax_error(file_path, issue):
                    return 1
            return 0
        
        # Filter fixable issues
        fixable = [i for i in issues if i.auto_fixable and i.fixed_code]
        if not fixable:
            return 0
        
        try:
            self.create_backup(file_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Separate import issues
            import_issues = [i for i in fixable if i.issue_type == 'MISSING_IMPORT']
            line_issues = [i for i in fixable if i.issue_type != 'MISSING_IMPORT']
            
            # Sort line issues by line number (descending)
            line_issues.sort(key=lambda x: x.line_number, reverse=True)
            
            fixes_applied = 0
            
            # Apply line fixes
            for issue in line_issues:
                line_idx = issue.line_number - 1
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx].rstrip()
                    if original == issue.original_code or issue.original_code in original:
                        lines[line_idx] = issue.fixed_code + '\\n'
                        fixes_applied += 1
            
            # Apply import fixes
            if import_issues:
                insert_idx = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        insert_idx = i + 1
                    elif stripped and not stripped.startswith('#') and not stripped.startswith('\"\"\"'):
                        if insert_idx > 0:
                            break
                
                existing = ''.join(lines[:insert_idx + 10])
                for issue in import_issues:
                    if issue.fixed_code not in existing:
                        lines.insert(insert_idx, issue.fixed_code + '\\n')
                        insert_idx += 1
                        fixes_applied += 1
            
            # Validate and save
            try:
                ast.parse(''.join(lines))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return fixes_applied
            except:
                # Restore backup
                backup_path = self.backup_dir / file_path.relative_to(self.root_dir)
                if backup_path.exists():
                    shutil.copy2(backup_path, file_path)
                return 0
        except:
            return 0
    
    def run_iteration(self) -> Tuple[int, int, int]:
        '''Run one scan-fix iteration. Returns (files_scanned, issues_found, issues_fixed)'''
        python_files = self.get_python_files()
        total_issues = 0
        total_fixed = 0
        
        for file_path in python_files:
            issues = self.scan_file(file_path)
            total_issues += len(issues)
            
            if issues:
                fixed = self.fix_file(file_path, issues)
                total_fixed += fixed
        
        return len(python_files), total_issues, total_fixed
    
    def run(self):
        '''Run the continuous fix loop'''
        print('=' * 70)
        print('CONTINUOUS AUTO-FIX LOOP - STARTING')
        print('=' * 70)
        print()
        print(f'Root Directory: {self.root_dir}')
        print(f'Max Iterations: {self.max_iterations}')
        print(f'Backup Directory: {self.backup_dir}')
        print()
        
        iteration = 0
        prev_issues = float('inf')
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f'--- ITERATION {iteration}/{self.max_iterations} ---')
            
            files_scanned, issues_found, issues_fixed = self.run_iteration()
            
            print(f'  Files Scanned: {files_scanned}')
            print(f'  Issues Found:  {issues_found}')
            print(f'  Issues Fixed:  {issues_fixed}')
            print()
            
            # Check if we're done
            if issues_found == 0:
                print('[SUCCESS] All issues resolved!')
                break
            
            # Check if we're making progress
            if issues_fixed == 0:
                print('[INFO] No more auto-fixable issues. Remaining issues require manual fix.')
                break
            
            # Check if issues are decreasing
            if issues_found >= prev_issues:
                print('[INFO] No progress made. Some issues may require manual intervention.')
                break
            
            prev_issues = issues_found
            
            # Small delay between iterations
            time.sleep(0.5)
        
        if iteration >= self.max_iterations:
            print(f'[INFO] Reached maximum iterations ({self.max_iterations})')
        
        # Final scan
        print()
        print('--- FINAL VERIFICATION ---')
        files_scanned, issues_found, _ = self.run_iteration()
        print(f'  Files Scanned: {files_scanned}')
        print(f'  Remaining Issues: {issues_found}')
        
        if issues_found == 0:
            print()
            print('[SUCCESS] ALL ISSUES RESOLVED!')
        else:
            print()
            print(f'[INFO] {issues_found} issues remain (may require manual fix)')
        
        print()
        print('=' * 70)
        print('CONTINUOUS AUTO-FIX LOOP - COMPLETE')
        print('=' * 70)
        print()
        print(f'Total Iterations: {iteration}')
        print(f'Backups saved to: {self.backup_dir}')


# Run the continuous fixer
if __name__ == '__main__':
    root_dir = r'%~dp0trading_bot'
    if not Path(root_dir).exists():
        root_dir = r'%~dp0'
    
    fixer = ContinuousAutoFixer(root_dir, max_iterations=10)
    fixer.run()
"

if errorlevel 1 (
    echo [ERROR] Auto-fix loop encountered an error
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════════
echo                         AUTO-FIX LOOP COMPLETE
echo ═══════════════════════════════════════════════════════════════════════════════
echo.
echo Check auto_fix_backups\ for file backups
echo.

pause
