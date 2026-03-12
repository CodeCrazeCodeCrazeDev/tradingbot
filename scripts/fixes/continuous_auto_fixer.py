"""
CONTINUOUS AUTO-FIX LOOP
========================
Scans codebase, fixes issues, verifies fixes, repeats until clean.

Cycle:
1. SCAN - Find all issues in codebase
2. FIX - Automatically fix all fixable issues
3. VERIFY - Re-scan to check if issues are fixed
4. REPEAT - If issues remain, go back to step 1

Usage:
    python continuous_auto_fixer.py [--path PATH] [--max-iterations N]
"""

import os
import sys
import ast
import re
import shutil
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum, auto


class Severity(Enum):
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()


class IssueType(Enum):
    SYNTAX_ERROR = auto()
    MISSING_IMPORT = auto()
    TYPO = auto()
    BARE_EXCEPT = auto()
    NONE_COMPARISON = auto()
    MIXED_INDENT = auto()
    TRAILING_WHITESPACE = auto()
    MUTABLE_DEFAULT = auto()
    UNDEFINED_NAME = auto()


@dataclass
class Issue:
    """Represents a code issue"""
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: Severity
    description: str
    original_code: str
    fixed_code: str = ''
    auto_fixable: bool = True


@dataclass
class IterationResult:
    """Result of one fix iteration"""
    iteration: int
    files_scanned: int
    issues_found: int
    issues_fixed: int
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    fixed_files: List[str] = field(default_factory=list)


class ContinuousAutoFixer:
    """
    Continuously scans and fixes code until all issues are resolved.
    """
    
    def __init__(self, root_dir: str, max_iterations: int = 10, verbose: bool = False):
        self.root_dir = Path(root_dir).resolve()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.backup_dir = self.root_dir / 'auto_fix_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        self.iteration_results: List[IterationResult] = []
        
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
            # Python keywords
            'imoprt': 'import', 'improt': 'import', 'imoport': 'import',
            'funciton': 'function', 'fucntion': 'function', 'funtion': 'function',
            'retrun': 'return', 'reutrn': 'return', 'retrn': 'return',
            'defualt': 'default', 'deafult': 'default',
            'ture': 'True', 'treu': 'True',
            'flase': 'False', 'fales': 'False', 'fasle': 'False',
            'noen': 'None', 'Noen': 'None', 'NOen': 'None',
            'slef': 'self', 'sefl': 'self', 'selff': 'self',
            'clss': 'class', 'calss': 'class', 'classs': 'class',
            'asnyc': 'async', 'asyc': 'async', 'asnc': 'async',
            'awiat': 'await', 'awit': 'await', 'awaitt': 'await',
            'pritn': 'print', 'pirnt': 'print', 'prnit': 'print',
            'yeild': 'yield', 'yiled': 'yield',
            'glboal': 'global', 'gloabl': 'global',
            'lamda': 'lambda', 'labmda': 'lambda',
            'excpet': 'except', 'exept': 'except', 'ecxept': 'except',
            'finaly': 'finally', 'finlly': 'finally',
            'raiase': 'raise', 'rasie': 'raise',
            'assret': 'assert', 'asert': 'assert',
            'delte': 'delete', 'deleet': 'delete',
            'passs': 'pass', 'pss': 'pass',
            'braek': 'break', 'brak': 'break',
            'contniue': 'continue', 'contineu': 'continue', 'coninue': 'continue',
            'whiel': 'while', 'whle': 'while',
            'elfi': 'elif', 'elseif': 'elif',
            'esle': 'else', 'els': 'else',
            # Common words
            'lenght': 'length', 'legnth': 'length',
            'widht': 'width',
            'heigth': 'height', 'hieght': 'height',
            'reciever': 'receiver', 'recieve': 'receive',
            'occured': 'occurred', 'occurence': 'occurrence',
            'sucess': 'success', 'succes': 'success', 'sucessful': 'successful',
            'faield': 'failed', 'faled': 'failed',
            'arguemnt': 'argument', 'arguement': 'argument',
            'paramter': 'parameter', 'paramater': 'parameter',
            'varaible': 'variable', 'varialbe': 'variable',
            'initalize': 'initialize', 'initialze': 'initialize',
            'configuraiton': 'configuration', 'configration': 'configuration',
            'responce': 'response', 'reponse': 'response',
            'requets': 'request', 'reqeust': 'request',
            'messge': 'message', 'mesage': 'message',
            'conneciton': 'connection', 'connectoin': 'connection',
            'excpetion': 'exception', 'excepton': 'exception',
            'attribtue': 'attribute', 'atribute': 'attribute',
            'stirng': 'string', 'strng': 'string',
            'lsit': 'list', 'lst': 'list',
            'dcit': 'dict', 'dct': 'dict',
            'tpye': 'type', 'tyep': 'type',
            'vlaue': 'value', 'valu': 'value',
            'indx': 'index', 'idnex': 'index',
            'coutner': 'counter', 'couner': 'counter',
            'resutl': 'result', 'reuslt': 'result',
            'outptu': 'output', 'ouput': 'output',
            'inptu': 'input', 'inut': 'input',
        }
        
        # Import mappings
        self.import_map = {
            # Data science
            'np': 'import numpy as np',
            'pd': 'import pandas as pd',
            'plt': 'import matplotlib.pyplot as plt',
            'sns': 'import seaborn as sns',
            # ML/DL
            'tf': 'import tensorflow as tf',
            'torch': 'import torch',
            'nn': 'import torch.nn as nn',
            'F': 'import torch.nn.functional as F',
            # Typing
            'Dict': 'from typing import Dict',
            'List': 'from typing import List',
            'Set': 'from typing import Set',
            'Tuple': 'from typing import Tuple',
            'Optional': 'from typing import Optional',
            'Union': 'from typing import Union',
            'Any': 'from typing import Any',
            'Callable': 'from typing import Callable',
            'TypeVar': 'from typing import TypeVar',
            'Generic': 'from typing import Generic',
            # Dataclasses
            'dataclass': 'from dataclasses import dataclass',
            'field': 'from dataclasses import field',
            'asdict': 'from dataclasses import asdict',
            # Collections
            'defaultdict': 'from collections import defaultdict',
            'deque': 'from collections import deque',
            'Counter': 'from collections import Counter',
            'OrderedDict': 'from collections import OrderedDict',
            # Enum
            'Enum': 'from enum import Enum',
            'auto': 'from enum import auto',
            # ABC
            'ABC': 'from abc import ABC',
            'abstractmethod': 'from abc import abstractmethod',
            # Pathlib
            'Path': 'from pathlib import Path',
            # Datetime
            'datetime': 'from datetime import datetime',
            'timedelta': 'from datetime import timedelta',
            # Async
            'asyncio': 'import asyncio',
            'aiohttp': 'import aiohttp',
            # Standard library
            'json': 'import json',
            'logging': 'import logging',
            'os': 'import os',
            'sys': 'import sys',
            're': 'import re',
            'time': 'import time',
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
    
    def log(self, message: str, level: str = 'INFO'):
        """Log a message"""
        if self.verbose or level in ('ERROR', 'WARNING', 'SUCCESS'):
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{level}] {message}")
    
    def get_python_files(self) -> List[Path]:
        """Get all Python files"""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            for file in files:
                if file.endswith('.py') and file not in {'__init__.py', 'setup.py', 'conftest.py'}:
                    python_files.append(Path(root) / file)
        return sorted(python_files)
    
    def create_backup(self, file_path: Path) -> bool:
        """Create backup of file"""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            relative_path = file_path.relative_to(self.root_dir)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            self.log(f"Backup failed for {file_path}: {e}", 'WARNING')
            return False
    
    def scan_file(self, file_path: Path) -> List[Issue]:
        """Scan a file for issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception as e:
            self.log(f"Could not read {file_path}: {e}", 'WARNING')
            return issues
        
        # Check syntax first
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(Issue(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type=IssueType.SYNTAX_ERROR,
                severity=Severity.CRITICAL,
                description=f'Syntax error: {e.msg}',
                original_code=e.text or '',
                auto_fixable=True
            ))
            return issues  # Can't check more if syntax is broken
        
        # Check each line
        for i, line in enumerate(lines, 1):
            # Check typos
            for typo, fix in self.typo_fixes.items():
                pattern = r'\b' + re.escape(typo) + r'\b'
                if re.search(pattern, line, re.IGNORECASE):
                    fixed_line = re.sub(pattern, fix, line, flags=re.IGNORECASE)
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type=IssueType.TYPO,
                        severity=Severity.MEDIUM,
                        description=f'Typo: {typo} -> {fix}',
                        original_code=line.rstrip(),
                        fixed_code=fixed_line.rstrip(),
                        auto_fixable=True
                    ))
            
            # Check bare except
            if re.match(r'^\s*except\s*:\s*$', line):
                indent = len(line) - len(line.lstrip())
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type=IssueType.BARE_EXCEPT,
                    severity=Severity.MEDIUM,
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
                    issue_type=IssueType.NONE_COMPARISON,
                    severity=Severity.LOW,
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
                    issue_type=IssueType.NONE_COMPARISON,
                    severity=Severity.LOW,
                    description='Use is not None instead of != None',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
            
            # Check mixed indentation
            if '\t' in line and '    ' in line:
                fixed_line = line.replace('\t', '    ')
                issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type=IssueType.MIXED_INDENT,
                    severity=Severity.MEDIUM,
                    description='Mixed tabs and spaces',
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
        
        # Check missing imports
        try:
            tree = ast.parse(content)
            
            # Collect imported names
            imported_names = set()
            defined_names = set()
            
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
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_names.add(node.name)
                    for arg in node.args.args + node.args.kwonlyargs:
                        defined_names.add(arg.arg)
                elif isinstance(node, ast.ClassDef):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    defined_names.add(node.id)
            
            # Collect used names
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
            
            # Get builtins
            import builtins
            builtin_names = set(dir(builtins))
            
            # Find missing imports
            all_known = imported_names | defined_names | builtin_names
            for name in used_names:
                if name in self.import_map and name not in all_known:
                    issues.append(Issue(
                        file_path=str(file_path),
                        line_number=1,
                        issue_type=IssueType.MISSING_IMPORT,
                        severity=Severity.HIGH,
                        description=f'Missing import for {name}',
                        original_code='',
                        fixed_code=self.import_map[name],
                        auto_fixable=True
                    ))
        except Exception as e:
            self.log(f"Import check failed for {file_path}: {e}", 'WARNING')
        
        return issues
    
    def fix_syntax_error(self, file_path: Path, issue: Issue) -> bool:
        """Try to fix syntax errors"""
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
                       'try', 'except', 'finally', 'with', 'async def', 'async for', 'async with']
            for kw in keywords:
                if re.match(rf'^\s*{kw}\s+.*[^:]\s*$', line):
                    lines[line_idx] = line.rstrip() + ':\n'
                    fixed = True
                    break
            
            if not fixed:
                # Unclosed parenthesis
                open_parens = line.count('(') - line.count(')')
                if open_parens > 0:
                    lines[line_idx] = line.rstrip() + ')' * open_parens + '\n'
                    fixed = True
            
            if not fixed:
                # Unclosed bracket
                open_brackets = line.count('[') - line.count(']')
                if open_brackets > 0:
                    lines[line_idx] = line.rstrip() + ']' * open_brackets + '\n'
                    fixed = True
            
            if not fixed:
                # Unclosed brace
                open_braces = line.count('{') - line.count('}')
                if open_braces > 0:
                    lines[line_idx] = line.rstrip() + '}' * open_braces + '\n'
                    fixed = True
            
            if not fixed:
                # Unclosed string
                if line.count('"') % 2 == 1:
                    lines[line_idx] = line.rstrip() + '"\n'
                    fixed = True
                elif line.count("'") % 2 == 1:
                    lines[line_idx] = line.rstrip() + "'\n"
                    fixed = True
            
            if fixed:
                try:
                    ast.parse(''.join(lines))
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    return True
                except SyntaxError:
                    return False
            
            return False
        except Exception as e:
            self.log(f"Syntax fix failed for {file_path}: {e}", 'WARNING')
            return False
    
    def fix_file(self, file_path: Path, issues: List[Issue]) -> int:
        """Apply fixes to a file"""
        if not issues:
            return 0
        
        # Handle syntax errors first
        syntax_issues = [i for i in issues if i.issue_type == IssueType.SYNTAX_ERROR]
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
            import_issues = [i for i in fixable if i.issue_type == IssueType.MISSING_IMPORT]
            line_issues = [i for i in fixable if i.issue_type != IssueType.MISSING_IMPORT]
            
            # Sort line issues by line number (descending)
            line_issues.sort(key=lambda x: x.line_number, reverse=True)
            
            fixes_applied = 0
            
            # Apply line fixes
            for issue in line_issues:
                line_idx = issue.line_number - 1
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx].rstrip()
                    if original == issue.original_code or issue.original_code in original:
                        lines[line_idx] = issue.fixed_code + '\n'
                        fixes_applied += 1
            
            # Apply import fixes
            if import_issues:
                # Find import section
                insert_idx = 0
                in_docstring = False
                docstring_char = None
                
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Track docstrings
                    if not in_docstring:
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            docstring_char = stripped[:3]
                            if stripped.count(docstring_char) == 1:
                                in_docstring = True
                            continue
                    else:
                        if docstring_char in stripped:
                            in_docstring = False
                        continue
                    
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        insert_idx = i + 1
                    elif stripped and not stripped.startswith('#'):
                        if insert_idx > 0:
                            break
                
                existing = ''.join(lines[:insert_idx + 10])
                for issue in import_issues:
                    if issue.fixed_code not in existing:
                        lines.insert(insert_idx, issue.fixed_code + '\n')
                        insert_idx += 1
                        fixes_applied += 1
            
            # Validate and save
            try:
                ast.parse(''.join(lines))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return fixes_applied
            except SyntaxError:
                # Restore backup
                backup_path = self.backup_dir / file_path.relative_to(self.root_dir)
                if backup_path.exists():
                    shutil.copy2(backup_path, file_path)
                self.log(f"Fix validation failed for {file_path}, restored backup", 'WARNING')
                return 0
        except Exception as e:
            self.log(f"Fix failed for {file_path}: {e}", 'WARNING')
            return 0
    
    def run_iteration(self, iteration: int) -> IterationResult:
        """Run one scan-fix iteration"""
        result = IterationResult(
            iteration=iteration,
            files_scanned=0,
            issues_found=0,
            issues_fixed=0
        )
        
        python_files = self.get_python_files()
        result.files_scanned = len(python_files)
        
        all_issues = []
        
        for file_path in python_files:
            issues = self.scan_file(file_path)
            all_issues.extend(issues)
            
            if issues:
                fixed = self.fix_file(file_path, issues)
                result.issues_fixed += fixed
                if fixed > 0:
                    result.fixed_files.append(str(file_path.relative_to(self.root_dir)))
        
        result.issues_found = len(all_issues)
        
        # Count by type
        for issue in all_issues:
            type_name = issue.issue_type.name
            result.issues_by_type[type_name] = result.issues_by_type.get(type_name, 0) + 1
        
        return result
    
    def run(self) -> bool:
        """Run the continuous fix loop. Returns True if all issues resolved."""
        print("=" * 70)
        print("CONTINUOUS AUTO-FIX LOOP - STARTING")
        print("=" * 70)
        print()
        print(f"Root Directory:   {self.root_dir}")
        print(f"Max Iterations:   {self.max_iterations}")
        print(f"Backup Directory: {self.backup_dir}")
        print()
        
        iteration = 0
        prev_issues = float('inf')
        all_resolved = False
        
        while iteration < self.max_iterations:
            iteration += 1
            print(f"{'='*20} ITERATION {iteration}/{self.max_iterations} {'='*20}")
            
            result = self.run_iteration(iteration)
            self.iteration_results.append(result)
            
            print(f"  Files Scanned:  {result.files_scanned}")
            print(f"  Issues Found:   {result.issues_found}")
            print(f"  Issues Fixed:   {result.issues_fixed}")
            
            if result.issues_by_type:
                print(f"  Issues by Type:")
                for issue_type, count in sorted(result.issues_by_type.items(), key=lambda x: -x[1])[:5]:
                    print(f"    - {issue_type}: {count}")
            
            if result.fixed_files:
                print(f"  Files Modified: {len(result.fixed_files)}")
                for f in result.fixed_files[:5]:
                    print(f"    - {f}")
                if len(result.fixed_files) > 5:
                    print(f"    ... and {len(result.fixed_files) - 5} more")
            
            print()
            
            # Check if we're done
            if result.issues_found == 0:
                print("[SUCCESS] All issues resolved!")
                all_resolved = True
                break
            
            # Check if we're making progress
            if result.issues_fixed == 0:
                print("[INFO] No more auto-fixable issues.")
                print("[INFO] Remaining issues may require manual intervention.")
                break
            
            # Check if issues are decreasing
            if result.issues_found >= prev_issues:
                print("[INFO] No progress made in this iteration.")
                print("[INFO] Some issues may require manual intervention.")
                break
            
            prev_issues = result.issues_found
            
            # Small delay between iterations
            time.sleep(0.5)
        
        if iteration >= self.max_iterations and not all_resolved:
            print(f"[INFO] Reached maximum iterations ({self.max_iterations})")
        
        # Final verification scan
        print()
        print("=" * 20 + " FINAL VERIFICATION " + "=" * 20)
        final_result = self.run_iteration(iteration + 1)
        
        print(f"  Files Scanned:     {final_result.files_scanned}")
        print(f"  Remaining Issues:  {final_result.issues_found}")
        
        if final_result.issues_found == 0:
            print()
            print("[SUCCESS] ALL ISSUES RESOLVED!")
            all_resolved = True
        else:
            print()
            print(f"[INFO] {final_result.issues_found} issues remain")
            if final_result.issues_by_type:
                print("  Remaining by Type:")
                for issue_type, count in sorted(final_result.issues_by_type.items(), key=lambda x: -x[1]):
                    print(f"    - {issue_type}: {count}")
        
        # Summary
        print()
        print("=" * 70)
        print("CONTINUOUS AUTO-FIX LOOP - SUMMARY")
        print("=" * 70)
        print()
        print(f"Total Iterations:    {iteration}")
        print(f"Total Files Scanned: {final_result.files_scanned}")
        
        total_fixed = sum(r.issues_fixed for r in self.iteration_results)
        print(f"Total Issues Fixed:  {total_fixed}")
        print(f"Remaining Issues:    {final_result.issues_found}")
        print(f"Backups saved to:    {self.backup_dir}")
        print()
        print("=" * 70)
        print("CONTINUOUS AUTO-FIX LOOP - COMPLETE")
        print("=" * 70)
        
        return all_resolved
    
    def save_report(self):
        """Save detailed report"""
        logs_dir = self.root_dir / 'auto_fix_logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = logs_dir / f'auto_fix_report_{timestamp}.json'
        
        report = {
            'timestamp': timestamp,
            'root_directory': str(self.root_dir),
            'max_iterations': self.max_iterations,
            'backup_directory': str(self.backup_dir),
            'iterations': [
                {
                    'iteration': r.iteration,
                    'files_scanned': r.files_scanned,
                    'issues_found': r.issues_found,
                    'issues_fixed': r.issues_fixed,
                    'issues_by_type': r.issues_by_type,
                    'fixed_files': r.fixed_files
                }
                for r in self.iteration_results
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"[INFO] Report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Continuous Auto-Fix Loop - Scan, Fix, Verify, Repeat'
    )
    parser.add_argument(
        '--path', '-p',
        default=os.getcwd(),
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--max-iterations', '-m',
        type=int,
        default=10,
        help='Maximum number of fix iterations (default: 10)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    fixer = ContinuousAutoFixer(
        root_dir=args.path,
        max_iterations=args.max_iterations,
        verbose=args.verbose
    )
    
    success = fixer.run()
    fixer.save_report()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
