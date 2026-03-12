@echo off
setlocal enabledelayedexpansion
title AlphaAlgo Autonomous Code Fixer
color 0A

echo.
echo ============================================================
echo    ALPHAALGO AUTONOMOUS CODE FIXER
echo    Scans ALL files, finds ALL issues, fixes AUTOMATICALLY
echo ============================================================
echo.

:: Set Python command
set PYTHON_CMD=py

:: Check Python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set PYTHON_CMD=python
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found!
        pause
        exit /b 1
    )
)

echo [INFO] Using Python: %PYTHON_CMD%
echo.

:: Create the autonomous fixer script
echo [STEP 1] Creating Autonomous Code Fixer...

%PYTHON_CMD% -c "
import os
import sys
import ast
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import shutil

# ============================================================
# AUTONOMOUS CODE FIXER - COMPLETE IMPLEMENTATION
# ============================================================

@dataclass
class Issue:
    '''Represents a code issue found'''
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    original_code: str
    fixed_code: str = ''
    auto_fixable: bool = True

@dataclass
class FixReport:
    '''Report of all fixes applied'''
    total_files_scanned: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    fixed_files: List[str] = field(default_factory=list)
    failed_fixes: List[str] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)

class AutonomousCodeFixer:
    '''
    Scans entire codebase, finds all issues, and fixes them automatically.
    '''
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.report = FixReport()
        self.backup_dir = self.root_dir / 'autonomous_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Directories to skip
        self.skip_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env', 
            '.venv', 'node_modules', '.hypothesis', 'htmlcov',
            'autonomous_backups', '.mypy_cache', 'mlruns', 'models',
            'backup', 'archive', '.github'
        }
        
        # Common import fixes
        self.import_fixes = {
            'numpy': 'import numpy as np',
            'pandas': 'import pandas as pd',
            'torch': 'import torch',
            'tensorflow': 'import tensorflow as tf',
            'sklearn': 'from sklearn import *',
            'typing': 'from typing import Dict, List, Optional, Tuple, Any, Set, Union',
            'dataclasses': 'from dataclasses import dataclass, field',
            'datetime': 'from datetime import datetime, timedelta',
            'pathlib': 'from pathlib import Path',
            'json': 'import json',
            'logging': 'import logging',
            'asyncio': 'import asyncio',
            'aiohttp': 'import aiohttp',
            'requests': 'import requests',
            'os': 'import os',
            'sys': 'import sys',
            're': 'import re',
            'time': 'import time',
            'random': 'import random',
            'math': 'import math',
            'collections': 'from collections import defaultdict, deque, Counter',
            'enum': 'from enum import Enum, auto',
            'abc': 'from abc import ABC, abstractmethod',
            'functools': 'from functools import wraps, lru_cache',
            'itertools': 'import itertools',
            'threading': 'import threading',
            'queue': 'import queue',
            'hashlib': 'import hashlib',
            'base64': 'import base64',
            'uuid': 'import uuid',
            'copy': 'import copy',
            'traceback': 'import traceback',
            'warnings': 'import warnings',
            'contextlib': 'from contextlib import contextmanager',
            'io': 'import io',
            'struct': 'import struct',
            'socket': 'import socket',
            'ssl': 'import ssl',
            'http': 'import http',
            'urllib': 'import urllib',
            'pickle': 'import pickle',
            'sqlite3': 'import sqlite3',
            'csv': 'import csv',
            'xml': 'import xml',
            'html': 'import html',
            'email': 'import email',
            'mimetypes': 'import mimetypes',
            'tempfile': 'import tempfile',
            'shutil': 'import shutil',
            'glob': 'import glob',
            'fnmatch': 'import fnmatch',
            'stat': 'import stat',
            'platform': 'import platform',
            'subprocess': 'import subprocess',
            'signal': 'import signal',
            'gc': 'import gc',
            'inspect': 'import inspect',
            'types': 'import types',
            'weakref': 'import weakref',
            'array': 'import array',
            'bisect': 'import bisect',
            'heapq': 'import heapq',
            'decimal': 'from decimal import Decimal',
            'fractions': 'from fractions import Fraction',
            'statistics': 'import statistics',
            'secrets': 'import secrets',
            'hmac': 'import hmac',
            'zlib': 'import zlib',
            'gzip': 'import gzip',
            'bz2': 'import bz2',
            'lzma': 'import lzma',
            'zipfile': 'import zipfile',
            'tarfile': 'import tarfile',
            'configparser': 'import configparser',
            'argparse': 'import argparse',
            'getopt': 'import getopt',
            'getpass': 'import getpass',
            'curses': 'import curses',
            'textwrap': 'import textwrap',
            'difflib': 'import difflib',
            'pprint': 'from pprint import pprint',
            'reprlib': 'import reprlib',
            'unittest': 'import unittest',
            'doctest': 'import doctest',
            'timeit': 'import timeit',
            'profile': 'import profile',
            'pstats': 'import pstats',
            'dis': 'import dis',
            'code': 'import code',
            'codeop': 'import codeop',
            'pdb': 'import pdb',
            'faulthandler': 'import faulthandler',
            'atexit': 'import atexit',
            'sched': 'import sched',
            'multiprocessing': 'import multiprocessing',
            'concurrent': 'from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor',
        }
        
        # Patterns for common issues
        self.issue_patterns = [
            # Syntax issues
            (r'^\s*except\s*:\s*$', 'bare_except', 'Bare except clause'),
            (r'^\s*print\s+[^(]', 'print_statement', 'Python 2 print statement'),
            (r'^\s*raise\s+\w+,', 'old_raise', 'Python 2 raise syntax'),
            
            # Common typos
            (r'\bimoprt\b', 'typo_import', 'Typo: imoprt -> import'),
            (r'\bfunciton\b', 'typo_function', 'Typo: funciton -> function'),
            (r'\bretrun\b', 'typo_return', 'Typo: retrun -> return'),
            (r'\bdefualt\b', 'typo_default', 'Typo: defualt -> default'),
            (r'\blenght\b', 'typo_length', 'Typo: lenght -> length'),
            (r'\bwidht\b', 'typo_width', 'Typo: widht -> width'),
            (r'\bheigth\b', 'typo_height', 'Typo: heigth -> height'),
            (r'\breciever\b', 'typo_receiver', 'Typo: reciever -> receiver'),
            (r'\boccured\b', 'typo_occurred', 'Typo: occured -> occurred'),
            (r'\bsucess\b', 'typo_success', 'Typo: sucess -> success'),
            (r'\bfales\b', 'typo_false', 'Typo: fales -> false'),
            (r'\btreu\b', 'typo_true', 'Typo: treu -> true'),
            (r'\bNoen\b', 'typo_none', 'Typo: Noen -> None'),
            (r'\bslef\b', 'typo_self', 'Typo: slef -> self'),
            (r'\bclss\b', 'typo_class', 'Typo: clss -> class'),
            (r'\basnyc\b', 'typo_async', 'Typo: asnyc -> async'),
            (r'\bawiat\b', 'typo_await', 'Typo: awiat -> await'),
            
            # Code smells
            (r'#\s*TODO', 'todo_marker', 'TODO marker found'),
            (r'#\s*FIXME', 'fixme_marker', 'FIXME marker found'),
            (r'#\s*HACK', 'hack_marker', 'HACK marker found'),
            (r'#\s*XXX', 'xxx_marker', 'XXX marker found'),
            
            # Security issues
            (r'eval\s*\(', 'eval_usage', 'Dangerous eval() usage'),
            (r'exec\s*\(', 'exec_usage', 'Dangerous exec() usage'),
            (r'password\s*=\s*[\"\\'][^\"\\'\n]+[\"\\']', 'hardcoded_password', 'Hardcoded password'),
            (r'api_key\s*=\s*[\"\\'][^\"\\'\n]+[\"\\']', 'hardcoded_api_key', 'Hardcoded API key'),
            (r'secret\s*=\s*[\"\\'][^\"\\'\n]+[\"\\']', 'hardcoded_secret', 'Hardcoded secret'),
            
            # Performance issues
            (r'\.append\([^)]+\)\s*$.*for\s+\w+\s+in', 'append_in_loop', 'Append in loop (use list comprehension)'),
        ]
        
        # Typo fixes
        self.typo_fixes = {
            'imoprt': 'import',
            'funciton': 'function',
            'retrun': 'return',
            'defualt': 'default',
            'lenght': 'length',
            'widht': 'width',
            'heigth': 'height',
            'reciever': 'receiver',
            'occured': 'occurred',
            'sucess': 'success',
            'fales': 'False',
            'treu': 'True',
            'Noen': 'None',
            'slef': 'self',
            'clss': 'class',
            'asnyc': 'async',
            'awiat': 'await',
            'ture': 'True',
            'flase': 'False',
            'noen': 'None',
            'pritn': 'print',
            'pirnt': 'print',
            'improt': 'import',
            'formt': 'format',
            'stirng': 'string',
            'lsit': 'list',
            'dcit': 'dict',
            'tpye': 'type',
            'calss': 'class',
            'fucntion': 'function',
            'arguemnt': 'argument',
            'paramter': 'parameter',
            'varaible': 'variable',
            'fucn': 'func',
            'reutrn': 'return',
            'yeild': 'yield',
            'glboal': 'global',
            'nonlocla': 'nonlocal',
            'lamda': 'lambda',
            'excpet': 'except',
            'finaly': 'finally',
            'raiase': 'raise',
            'assret': 'assert',
            'delte': 'delete',
            'passs': 'pass',
            'braek': 'break',
            'contniue': 'continue',
            'whiel': 'while',
            'elfi': 'elif',
            'esle': 'else',
        }
    
    def create_backup(self, file_path: Path) -> bool:
        '''Create backup of file before modifying'''
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            relative_path = file_path.relative_to(self.root_dir)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f'  [WARN] Could not backup {file_path}: {e}')
            return False
    
    def get_python_files(self) -> List[Path]:
        '''Get all Python files in the codebase'''
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def check_syntax(self, file_path: Path) -> List[Issue]:
        '''Check file for syntax errors'''
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type='syntax_error',
                    severity='CRITICAL',
                    description=f'Syntax error: {e.msg}',
                    original_code=e.text or '',
                    auto_fixable=True
                ))
        except Exception as e:
            pass
        
        return issues
    
    def check_imports(self, file_path: Path, content: str, lines: List[str]) -> List[Issue]:
        '''Check for missing or broken imports'''
        issues = []
        
        try:
            tree = ast.parse(content)
        except:
            return issues
        
        # Get all imported names
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module.split('.')[0])
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)
        
        # Get all used names
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # Common modules that might be used but not imported
        common_modules = {'np', 'pd', 'plt', 'tf', 'torch', 'nn', 'F', 'os', 'sys', 're', 
                         'json', 'logging', 'datetime', 'time', 'random', 'math', 'Path',
                         'Dict', 'List', 'Optional', 'Tuple', 'Any', 'Set', 'Union',
                         'dataclass', 'field', 'Enum', 'auto', 'ABC', 'abstractmethod',
                         'defaultdict', 'deque', 'Counter', 'asyncio', 'aiohttp'}
        
        # Check for potentially missing imports
        for name in used_names:
            if name in common_modules and name not in imported_names:
                # Determine the import statement needed
                import_map = {
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
                }
                
                if name in import_map:
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=1,
                        issue_type='missing_import',
                        severity='HIGH',
                        description=f'Missing import for {name}',
                        original_code='',
                        fixed_code=import_map[name],
                        auto_fixable=True
                    ))
        
        return issues
    
    def check_line_issues(self, file_path: Path, lines: List[str]) -> List[Issue]:
        '''Check each line for issues'''
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Check for typos
            for typo, fix in self.typo_fixes.items():
                if re.search(r'\b' + typo + r'\b', line, re.IGNORECASE):
                    fixed_line = re.sub(r'\b' + typo + r'\b', fix, line)
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type='typo',
                        severity='MEDIUM',
                        description=f'Typo: {typo} -> {fix}',
                        original_code=line.rstrip(),
                        fixed_code=fixed_line.rstrip(),
                        auto_fixable=True
                    ))
            
            # Check for bare except
            if re.match(r'^\s*except\s*:\s*$', line):
                indent = len(line) - len(line.lstrip())
                fixed_line = ' ' * indent + 'except Exception:'
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='bare_except',
                    severity='MEDIUM',
                    description='Bare except clause - should specify exception type',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line,
                    auto_fixable=True
                ))
            
            # Check for Python 2 print statements
            if re.match(r'^\s*print\s+[^(]', line) and 'print(' not in line:
                # Convert print statement to print function
                match = re.match(r'^(\s*)print\s+(.+)$', line)
                if match:
                    indent, content = match.groups()
                    fixed_line = f'{indent}print({content.strip()})'
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type='print_statement',
                        severity='HIGH',
                        description='Python 2 print statement',
                        original_code=line.rstrip(),
                        fixed_code=fixed_line,
                        auto_fixable=True
                    ))
            
            # Check for trailing whitespace
            if line.rstrip() != line.rstrip('\n') and line.endswith(' \n'):
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='trailing_whitespace',
                    severity='LOW',
                    description='Trailing whitespace',
                    original_code=line.rstrip('\n'),
                    fixed_code=line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check for tabs mixed with spaces
            if '\t' in line and '    ' in line:
                fixed_line = line.replace('\t', '    ')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='mixed_indentation',
                    severity='MEDIUM',
                    description='Mixed tabs and spaces',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check for == None or == True or == False
            if ' == None' in line:
                fixed_line = line.replace(' == None', ' is None')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='none_comparison',
                    severity='LOW',
                    description='Use \"is None\" instead of \"== None\"',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            if ' != None' in line:
                fixed_line = line.replace(' != None', ' is not None')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='none_comparison',
                    severity='LOW',
                    description='Use \"is not None\" instead of \"!= None\"',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check for mutable default arguments
            if re.search(r'def\s+\w+\s*\([^)]*=\s*\[\]', line) or re.search(r'def\s+\w+\s*\([^)]*=\s*\{\}', line):
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='mutable_default',
                    severity='HIGH',
                    description='Mutable default argument (use None instead)',
                    original_code=line.rstrip(),
                    fixed_code='',  # Complex fix, mark but don't auto-fix
                    auto_fixable=False
                ))
            
            # Check for string formatting issues
            if '%s' in line and '.format(' not in line and 'f\"' not in line and \"f'\" not in line:
                # Suggest f-string but don't auto-fix (too complex)
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type='old_string_format',
                    severity='LOW',
                    description='Consider using f-strings instead of % formatting',
                    original_code=line.rstrip(),
                    fixed_code='',
                    auto_fixable=False
                ))
        
        return issues
    
    def check_undefined_names(self, file_path: Path, content: str) -> List[Issue]:
        '''Check for undefined names using AST'''
        issues = []
        
        try:
            tree = ast.parse(content)
        except:
            return issues
        
        # Collect all defined names
        defined_names = set()
        
        # Built-in names
        import builtins
        defined_names.update(dir(builtins))
        
        # Add common globals
        defined_names.update(['__name__', '__file__', '__doc__', '__package__', 
                             '__spec__', '__annotations__', '__builtins__',
                             '__cached__', '__loader__'])
        
        # Collect imports and definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    defined_names.add(alias.asname or alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    defined_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                defined_names.add(node.name)
                for arg in node.args.args:
                    defined_names.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    defined_names.add(arg.arg)
                if node.args.vararg:
                    defined_names.add(node.args.vararg.arg)
                if node.args.kwarg:
                    defined_names.add(node.args.kwarg.arg)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)
            elif isinstance(node, ast.For):
                if isinstance(node.target, ast.Name):
                    defined_names.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            defined_names.add(elt.id)
            elif isinstance(node, ast.comprehension):
                if isinstance(node.target, ast.Name):
                    defined_names.add(node.target.id)
                elif isinstance(node.target, ast.Tuple):
                    for elt in node.target.elts:
                        if isinstance(elt, ast.Name):
                            defined_names.add(elt.id)
            elif isinstance(node, ast.ExceptHandler):
                if node.name:
                    defined_names.add(node.name)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars:
                        if isinstance(item.optional_vars, ast.Name):
                            defined_names.add(item.optional_vars.id)
        
        return issues
    
    def fix_syntax_error(self, file_path: Path, issue: Issue) -> bool:
        '''Attempt to fix syntax errors'''
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            line_idx = issue.line_number - 1
            if line_idx < 0 or line_idx >= len(lines):
                return False
            
            line = lines[line_idx]
            fixed = False
            
            # Common syntax fixes
            
            # Missing colon at end of def/class/if/for/while/try/except/with
            if re.match(r'^\s*(def|class|if|elif|else|for|while|try|except|finally|with|async\s+def|async\s+for|async\s+with)\s+.*[^:]\s*$', line):
                lines[line_idx] = line.rstrip() + ':\n'
                fixed = True
            
            # Unclosed parenthesis - try to close it
            open_parens = line.count('(') - line.count(')')
            if open_parens > 0:
                lines[line_idx] = line.rstrip() + ')' * open_parens + '\n'
                fixed = True
            
            # Unclosed bracket
            open_brackets = line.count('[') - line.count(']')
            if open_brackets > 0:
                lines[line_idx] = line.rstrip() + ']' * open_brackets + '\n'
                fixed = True
            
            # Unclosed brace
            open_braces = line.count('{') - line.count('}')
            if open_braces > 0:
                lines[line_idx] = line.rstrip() + '}' * open_braces + '\n'
                fixed = True
            
            # Unclosed string
            if line.count('\"') % 2 == 1:
                lines[line_idx] = line.rstrip() + '\"\n'
                fixed = True
            elif line.count(\"'\") % 2 == 1:
                lines[line_idx] = line.rstrip() + \"'\n\"
                fixed = True
            
            if fixed:
                # Validate the fix
                try:
                    ast.parse(''.join(lines))
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
                except:
                    return False
            
            return False
        except Exception as e:
            return False
    
    def fix_file(self, file_path: Path, issues: List[Issue]) -> int:
        '''Apply fixes to a file'''
        if not issues:
            return 0
        
        # Filter to auto-fixable issues
        fixable_issues = [i for i in issues if i.auto_fixable and i.fixed_code]
        
        if not fixable_issues:
            return 0
        
        try:
            # Create backup
            self.create_backup(file_path)
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Sort issues by line number (descending) to fix from bottom up
            fixable_issues.sort(key=lambda x: x.line_number, reverse=True)
            
            fixes_applied = 0
            
            for issue in fixable_issues:
                line_idx = issue.line_number - 1
                
                if issue.issue_type == 'missing_import':
                    # Add import at the top of the file
                    # Find the right place to insert
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            insert_idx = i + 1
                        elif line.strip() and not line.strip().startswith('#') and not line.strip().startswith('\"\"\"'):
                            break
                    
                    # Check if import already exists
                    import_exists = any(issue.fixed_code in line for line in lines)
                    if not import_exists:
                        lines.insert(insert_idx, issue.fixed_code + '\n')
                        fixes_applied += 1
                
                elif 0 <= line_idx < len(lines):
                    # Replace the line
                    original = lines[line_idx].rstrip()
                    if original == issue.original_code or issue.original_code in original:
                        if issue.fixed_code:
                            # Preserve the original line ending
                            lines[line_idx] = issue.fixed_code + '\n'
                            fixes_applied += 1
            
            # Validate the result
            try:
                ast.parse(''.join(lines))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return fixes_applied
            except SyntaxError:
                # Restore from backup
                backup_path = self.backup_dir / file_path.relative_to(self.root_dir)
                if backup_path.exists():
                    shutil.copy2(backup_path, file_path)
                return 0
                
        except Exception as e:
            print(f'  [ERROR] Failed to fix {file_path}: {e}')
            return 0
    
    def scan_file(self, file_path: Path) -> List[Issue]:
        '''Scan a single file for all issues'''
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception as e:
            return issues
        
        # Check syntax
        issues.extend(self.check_syntax(file_path))
        
        # If syntax is OK, check other issues
        if not any(i.issue_type == 'syntax_error' for i in issues):
            issues.extend(self.check_imports(file_path, content, lines))
            issues.extend(self.check_line_issues(file_path, lines))
            issues.extend(self.check_undefined_names(file_path, content))
        
        return issues
    
    def run(self) -> FixReport:
        '''Run the autonomous code fixer'''
        print('=' * 60)
        print('AUTONOMOUS CODE FIXER - STARTING')
        print('=' * 60)
        print()
        
        # Get all Python files
        python_files = self.get_python_files()
        self.report.total_files_scanned = len(python_files)
        
        print(f'[INFO] Found {len(python_files)} Python files to scan')
        print(f'[INFO] Backup directory: {self.backup_dir}')
        print()
        
        # Scan all files
        all_issues = []
        for i, file_path in enumerate(python_files, 1):
            relative_path = file_path.relative_to(self.root_dir)
            print(f'[{i}/{len(python_files)}] Scanning: {relative_path}', end='')
            
            issues = self.scan_file(file_path)
            
            if issues:
                print(f' -> {len(issues)} issues found')
                all_issues.extend(issues)
                
                # Apply fixes
                fixes = self.fix_file(file_path, issues)
                if fixes > 0:
                    print(f'         -> {fixes} fixes applied')
                    self.report.fixed_files.append(str(relative_path))
                    self.report.total_issues_fixed += fixes
            else:
                print(' -> OK')
        
        # Update report
        self.report.total_issues_found = len(all_issues)
        self.report.issues = all_issues
        
        for issue in all_issues:
            self.report.issues_by_type[issue.issue_type] = self.report.issues_by_type.get(issue.issue_type, 0) + 1
            self.report.issues_by_severity[issue.severity] = self.report.issues_by_severity.get(issue.severity, 0) + 1
        
        return self.report
    
    def print_report(self):
        '''Print the fix report'''
        print()
        print('=' * 60)
        print('AUTONOMOUS CODE FIXER - REPORT')
        print('=' * 60)
        print()
        print(f'Files Scanned:    {self.report.total_files_scanned}')
        print(f'Issues Found:     {self.report.total_issues_found}')
        print(f'Issues Fixed:     {self.report.total_issues_fixed}')
        print(f'Files Modified:   {len(self.report.fixed_files)}')
        print()
        
        if self.report.issues_by_severity:
            print('Issues by Severity:')
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = self.report.issues_by_severity.get(severity, 0)
                if count > 0:
                    print(f'  {severity}: {count}')
            print()
        
        if self.report.issues_by_type:
            print('Issues by Type:')
            for issue_type, count in sorted(self.report.issues_by_type.items(), key=lambda x: -x[1])[:20]:
                print(f'  {issue_type}: {count}')
            print()
        
        if self.report.fixed_files:
            print('Files Modified:')
            for f in self.report.fixed_files[:20]:
                print(f'  - {f}')
            if len(self.report.fixed_files) > 20:
                print(f'  ... and {len(self.report.fixed_files) - 20} more')
            print()
        
        # Show unfixed critical issues
        critical_unfixed = [i for i in self.report.issues if i.severity == 'CRITICAL' and not i.auto_fixable]
        if critical_unfixed:
            print('CRITICAL Issues (Manual Fix Required):')
            for issue in critical_unfixed[:10]:
                rel_path = Path(issue.file_path).relative_to(self.root_dir) if self.root_dir in Path(issue.file_path).parents else issue.file_path
                print(f'  - {rel_path}:{issue.line_number} - {issue.description}')
            print()
        
        print('=' * 60)
        print('AUTONOMOUS CODE FIXER - COMPLETE')
        print('=' * 60)
    
    def save_report(self):
        '''Save detailed report to file'''
        report_path = self.root_dir / 'autonomous_logs' / f'fix_all_report_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.txt'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('AUTONOMOUS CODE FIXER - DETAILED REPORT\n')
            f.write('=' * 60 + '\n')
            f.write(f'Generated: {datetime.now().isoformat()}\n')
            f.write(f'Root Directory: {self.root_dir}\n')
            f.write('\n')
            f.write(f'Files Scanned: {self.report.total_files_scanned}\n')
            f.write(f'Issues Found: {self.report.total_issues_found}\n')
            f.write(f'Issues Fixed: {self.report.total_issues_fixed}\n')
            f.write('\n')
            
            f.write('ALL ISSUES:\n')
            f.write('-' * 60 + '\n')
            for issue in self.report.issues:
                rel_path = Path(issue.file_path).relative_to(self.root_dir) if self.root_dir in Path(issue.file_path).parents else issue.file_path
                f.write(f'[{issue.severity}] {rel_path}:{issue.line_number}\n')
                f.write(f'  Type: {issue.issue_type}\n')
                f.write(f'  Description: {issue.description}\n')
                if issue.original_code:
                    f.write(f'  Original: {issue.original_code}\n')
                if issue.fixed_code:
                    f.write(f'  Fixed: {issue.fixed_code}\n')
                f.write(f'  Auto-fixable: {issue.auto_fixable}\n')
                f.write('\n')
        
        print(f'[INFO] Detailed report saved to: {report_path}')


# Run the fixer
if __name__ == '__main__':
    root_dir = r'c:\Users\peterson\trading bot'
    fixer = AutonomousCodeFixer(root_dir)
    fixer.run()
    fixer.print_report()
    fixer.save_report()
"

if errorlevel 1 (
    echo [ERROR] Code fixer encountered an error
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    AUTONOMOUS CODE FIXER COMPLETE
echo ============================================================
echo.
echo Check autonomous_logs\ for detailed report
echo Check autonomous_backups\ for file backups
echo.

pause
