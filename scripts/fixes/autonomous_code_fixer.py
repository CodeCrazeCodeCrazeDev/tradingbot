"""
AUTONOMOUS CODE FIXER
=====================
Scans ALL files in the codebase, finds ALL issues line-by-line,
and automatically fixes them.

Features:
- Syntax error detection and fixing
- Missing import detection and auto-adding
- Typo detection and correction
- Code smell detection
- Undefined name detection
- Style issue fixing
- Security issue detection
- Performance issue detection

Usage:
    python autonomous_code_fixer.py [--dry-run] [--verbose] [--path PATH]
"""

import os
import sys
import ast
import re
import traceback
import argparse
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum, auto
import difflib


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = auto()  # Breaks execution
    HIGH = auto()      # Major bug or security issue
    MEDIUM = auto()    # Code smell or potential bug
    LOW = auto()       # Style or minor issue
    INFO = auto()      # Informational


class IssueType(Enum):
    """Types of issues that can be detected"""
    SYNTAX_ERROR = auto()
    MISSING_IMPORT = auto()
    UNDEFINED_NAME = auto()
    TYPO = auto()
    BARE_EXCEPT = auto()
    MUTABLE_DEFAULT = auto()
    NONE_COMPARISON = auto()
    MIXED_INDENTATION = auto()
    TRAILING_WHITESPACE = auto()
    UNUSED_IMPORT = auto()
    UNUSED_VARIABLE = auto()
    DUPLICATE_IMPORT = auto()
    CIRCULAR_IMPORT = auto()
    HARDCODED_SECRET = auto()
    EVAL_USAGE = auto()
    EXEC_USAGE = auto()
    PRINT_STATEMENT = auto()
    OLD_STRING_FORMAT = auto()
    MISSING_DOCSTRING = auto()
    LONG_LINE = auto()
    COMPLEX_FUNCTION = auto()
    TODO_MARKER = auto()
    FIXME_MARKER = auto()
    DEPRECATED_USAGE = auto()
    ENCODING_ISSUE = auto()
    INDENTATION_ERROR = auto()
    MISSING_COLON = auto()
    UNCLOSED_BRACKET = auto()
    UNCLOSED_STRING = auto()
    INVALID_ESCAPE = auto()


@dataclass
class Issue:
    """Represents a code issue found"""
    file_path: str
    line_number: int
    column: int
    issue_type: IssueType
    severity: Severity
    description: str
    original_code: str
    fixed_code: str = ''
    auto_fixable: bool = True
    context: str = ''  # Surrounding code for context
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column': self.column,
            'issue_type': self.issue_type.name,
            'severity': self.severity.name,
            'description': self.description,
            'original_code': self.original_code,
            'fixed_code': self.fixed_code,
            'auto_fixable': self.auto_fixable,
            'context': self.context
        }


@dataclass
class FixReport:
    """Report of all fixes applied"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    root_directory: str = ''
    total_files_scanned: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    fixed_files: List[str] = field(default_factory=list)
    failed_fixes: List[str] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'root_directory': self.root_directory,
            'total_files_scanned': self.total_files_scanned,
            'total_issues_found': self.total_issues_found,
            'total_issues_fixed': self.total_issues_fixed,
            'issues_by_type': self.issues_by_type,
            'issues_by_severity': self.issues_by_severity,
            'fixed_files': self.fixed_files,
            'failed_fixes': self.failed_fixes,
            'issues': [i.to_dict() for i in self.issues]
        }


class ImportFixer:
    """Handles import-related fixes"""
    
    # Common import mappings
    IMPORT_MAP = {
        # Standard library
        'os': 'import os',
        'sys': 'import sys',
        're': 'import re',
        'json': 'import json',
        'time': 'import time',
        'random': 'import random',
        'math': 'import math',
        'logging': 'import logging',
        'datetime': 'from datetime import datetime, timedelta',
        'timedelta': 'from datetime import timedelta',
        'Path': 'from pathlib import Path',
        'pathlib': 'from pathlib import Path',
        'asyncio': 'import asyncio',
        'threading': 'import threading',
        'multiprocessing': 'import multiprocessing',
        'subprocess': 'import subprocess',
        'shutil': 'import shutil',
        'glob': 'import glob',
        'tempfile': 'import tempfile',
        'pickle': 'import pickle',
        'copy': 'import copy',
        'deepcopy': 'from copy import deepcopy',
        'hashlib': 'import hashlib',
        'base64': 'import base64',
        'uuid': 'import uuid',
        'secrets': 'import secrets',
        'hmac': 'import hmac',
        'socket': 'import socket',
        'ssl': 'import ssl',
        'http': 'import http',
        'urllib': 'import urllib',
        'sqlite3': 'import sqlite3',
        'csv': 'import csv',
        'io': 'import io',
        'struct': 'import struct',
        'warnings': 'import warnings',
        'traceback': 'import traceback',
        'inspect': 'import inspect',
        'functools': 'import functools',
        'itertools': 'import itertools',
        'operator': 'import operator',
        'contextlib': 'import contextlib',
        'abc': 'from abc import ABC, abstractmethod',
        'ABC': 'from abc import ABC',
        'abstractmethod': 'from abc import abstractmethod',
        'argparse': 'import argparse',
        'configparser': 'import configparser',
        'textwrap': 'import textwrap',
        'difflib': 'import difflib',
        'pprint': 'from pprint import pprint',
        'unittest': 'import unittest',
        'doctest': 'import doctest',
        'gc': 'import gc',
        'weakref': 'import weakref',
        'array': 'import array',
        'bisect': 'import bisect',
        'heapq': 'import heapq',
        'statistics': 'import statistics',
        'decimal': 'from decimal import Decimal',
        'Decimal': 'from decimal import Decimal',
        'fractions': 'from fractions import Fraction',
        'Fraction': 'from fractions import Fraction',
        'zlib': 'import zlib',
        'gzip': 'import gzip',
        'zipfile': 'import zipfile',
        'tarfile': 'import tarfile',
        'platform': 'import platform',
        'signal': 'import signal',
        'atexit': 'import atexit',
        'queue': 'import queue',
        'Queue': 'from queue import Queue',
        'sched': 'import sched',
        
        # Typing
        'Dict': 'from typing import Dict',
        'List': 'from typing import List',
        'Set': 'from typing import Set',
        'Tuple': 'from typing import Tuple',
        'Optional': 'from typing import Optional',
        'Union': 'from typing import Union',
        'Any': 'from typing import Any',
        'Callable': 'from typing import Callable',
        'Iterable': 'from typing import Iterable',
        'Iterator': 'from typing import Iterator',
        'Generator': 'from typing import Generator',
        'Sequence': 'from typing import Sequence',
        'Mapping': 'from typing import Mapping',
        'MutableMapping': 'from typing import MutableMapping',
        'TypeVar': 'from typing import TypeVar',
        'Generic': 'from typing import Generic',
        'Protocol': 'from typing import Protocol',
        'Final': 'from typing import Final',
        'Literal': 'from typing import Literal',
        'ClassVar': 'from typing import ClassVar',
        'TYPE_CHECKING': 'from typing import TYPE_CHECKING',
        
        # Collections
        'defaultdict': 'from collections import defaultdict',
        'deque': 'from collections import deque',
        'Counter': 'from collections import Counter',
        'OrderedDict': 'from collections import OrderedDict',
        'namedtuple': 'from collections import namedtuple',
        'ChainMap': 'from collections import ChainMap',
        
        # Dataclasses
        'dataclass': 'from dataclasses import dataclass',
        'field': 'from dataclasses import field',
        'asdict': 'from dataclasses import asdict',
        'astuple': 'from dataclasses import astuple',
        
        # Enum
        'Enum': 'from enum import Enum',
        'auto': 'from enum import auto',
        'IntEnum': 'from enum import IntEnum',
        'Flag': 'from enum import Flag',
        
        # Concurrent
        'ThreadPoolExecutor': 'from concurrent.futures import ThreadPoolExecutor',
        'ProcessPoolExecutor': 'from concurrent.futures import ProcessPoolExecutor',
        'Future': 'from concurrent.futures import Future',
        'as_completed': 'from concurrent.futures import as_completed',
        
        # Functools
        'wraps': 'from functools import wraps',
        'lru_cache': 'from functools import lru_cache',
        'partial': 'from functools import partial',
        'reduce': 'from functools import reduce',
        'cache': 'from functools import cache',
        'cached_property': 'from functools import cached_property',
        
        # Contextlib
        'contextmanager': 'from contextlib import contextmanager',
        'asynccontextmanager': 'from contextlib import asynccontextmanager',
        'suppress': 'from contextlib import suppress',
        'nullcontext': 'from contextlib import nullcontext',
        
        # Third-party - Data Science
        'np': 'import numpy as np',
        'numpy': 'import numpy as np',
        'pd': 'import pandas as pd',
        'pandas': 'import pandas as pd',
        'plt': 'import matplotlib.pyplot as plt',
        'matplotlib': 'import matplotlib.pyplot as plt',
        'sns': 'import seaborn as sns',
        'seaborn': 'import seaborn as sns',
        'scipy': 'import scipy',
        'sklearn': 'import sklearn',
        
        # Third-party - ML/DL
        'torch': 'import torch',
        'nn': 'import torch.nn as nn',
        'F': 'import torch.nn.functional as F',
        'tf': 'import tensorflow as tf',
        'tensorflow': 'import tensorflow as tf',
        'keras': 'from tensorflow import keras',
        
        # Third-party - Web
        'requests': 'import requests',
        'aiohttp': 'import aiohttp',
        'flask': 'from flask import Flask',
        'Flask': 'from flask import Flask',
        'fastapi': 'from fastapi import FastAPI',
        'FastAPI': 'from fastapi import FastAPI',
        
        # Third-party - Other
        'yaml': 'import yaml',
        'toml': 'import toml',
        'redis': 'import redis',
        'sqlalchemy': 'import sqlalchemy',
        'pydantic': 'from pydantic import BaseModel',
        'BaseModel': 'from pydantic import BaseModel',
        'pytest': 'import pytest',
        'click': 'import click',
        'rich': 'from rich import print',
        'tqdm': 'from tqdm import tqdm',
    }
    
    @classmethod
    def get_import_statement(cls, name: str) -> Optional[str]:
        """Get the import statement for a name"""
        return cls.IMPORT_MAP.get(name)
    
    @classmethod
    def find_missing_imports(cls, content: str, file_path: str) -> List[Issue]:
        """Find names that are used but not imported"""
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues
        
        # Collect imported names
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
        
        # Collect defined names (functions, classes, variables)
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
                for arg in node.args.args + node.args.kwonlyargs:
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
            elif isinstance(node, ast.ExceptHandler) and node.name:
                defined_names.add(node.name)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        defined_names.add(item.optional_vars.id)
            elif isinstance(node, ast.comprehension):
                if isinstance(node.target, ast.Name):
                    defined_names.add(node.target.id)
        
        # Add builtins
        import builtins
        builtin_names = set(dir(builtins))
        
        # Collect used names
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        # Find potentially missing imports
        all_known = imported_names | defined_names | builtin_names
        for name in used_names:
            if name not in all_known and name in cls.IMPORT_MAP:
                import_stmt = cls.IMPORT_MAP[name]
                issues.append(Issue(
                    file_path=file_path,
                    line_number=1,
                    column=0,
                    issue_type=IssueType.MISSING_IMPORT,
                    severity=Severity.HIGH,
                    description=f"Missing import for '{name}'",
                    original_code='',
                    fixed_code=import_stmt,
                    auto_fixable=True
                ))
        
        return issues


class TypoFixer:
    """Handles typo detection and fixing"""
    
    TYPOS = {
        # Python keywords
        'imoprt': 'import',
        'improt': 'import',
        'imoport': 'import',
        'funciton': 'function',
        'fucntion': 'function',
        'funtion': 'function',
        'retrun': 'return',
        'reutrn': 'return',
        'retrn': 'return',
        'defualt': 'default',
        'deafult': 'default',
        'ture': 'True',
        'treu': 'True',
        'flase': 'False',
        'fales': 'False',
        'fasle': 'False',
        'noen': 'None',
        'Noen': 'None',
        'NOen': 'None',
        'slef': 'self',
        'sefl': 'self',
        'selff': 'self',
        'clss': 'class',
        'calss': 'class',
        'classs': 'class',
        'asnyc': 'async',
        'asyc': 'async',
        'asnc': 'async',
        'awiat': 'await',
        'awit': 'await',
        'awaitt': 'await',
        'pritn': 'print',
        'pirnt': 'print',
        'prnit': 'print',
        'yeild': 'yield',
        'yiled': 'yield',
        'glboal': 'global',
        'gloabl': 'global',
        'lamda': 'lambda',
        'labmda': 'lambda',
        'excpet': 'except',
        'exept': 'except',
        'ecxept': 'except',
        'finaly': 'finally',
        'finlly': 'finally',
        'raiase': 'raise',
        'rasie': 'raise',
        'assret': 'assert',
        'asert': 'assert',
        'delte': 'delete',
        'deleet': 'delete',
        'passs': 'pass',
        'pss': 'pass',
        'braek': 'break',
        'brak': 'break',
        'contniue': 'continue',
        'contineu': 'continue',
        'coninue': 'continue',
        'whiel': 'while',
        'whle': 'while',
        'elfi': 'elif',
        'elseif': 'elif',
        'esle': 'else',
        'els': 'else',
        
        # Common words
        'lenght': 'length',
        'legnth': 'length',
        'widht': 'width',
        'heigth': 'height',
        'hieght': 'height',
        'reciever': 'receiver',
        'recieve': 'receive',
        'occured': 'occurred',
        'occurence': 'occurrence',
        'sucess': 'success',
        'succes': 'success',
        'sucessful': 'successful',
        'faield': 'failed',
        'faled': 'failed',
        'arguemnt': 'argument',
        'arguement': 'argument',
        'paramter': 'parameter',
        'paramater': 'parameter',
        'varaible': 'variable',
        'varialbe': 'variable',
        'initalize': 'initialize',
        'initialze': 'initialize',
        'configuraiton': 'configuration',
        'configration': 'configuration',
        'responce': 'response',
        'reponse': 'response',
        'requets': 'request',
        'reqeust': 'request',
        'messge': 'message',
        'mesage': 'message',
        'conneciton': 'connection',
        'connectoin': 'connection',
        'excpetion': 'exception',
        'excepton': 'exception',
        'attribtue': 'attribute',
        'atribute': 'attribute',
        'fucn': 'func',
        'fnuc': 'func',
        'stirng': 'string',
        'strng': 'string',
        'lsit': 'list',
        'lst': 'list',
        'dcit': 'dict',
        'dct': 'dict',
        'tpye': 'type',
        'tyep': 'type',
        'vlaue': 'value',
        'valu': 'value',
        'indx': 'index',
        'idnex': 'index',
        'coutner': 'counter',
        'couner': 'counter',
        'resutl': 'result',
        'reuslt': 'result',
        'outptu': 'output',
        'ouput': 'output',
        'inptu': 'input',
        'inut': 'input',
    }
    
    @classmethod
    def find_typos(cls, line: str, line_number: int, file_path: str) -> List[Issue]:
        """Find typos in a line"""
        issues = []
        
        for typo, fix in cls.TYPOS.items():
            pattern = r'\b' + re.escape(typo) + r'\b'
            if re.search(pattern, line, re.IGNORECASE):
                fixed_line = re.sub(pattern, fix, line, flags=re.IGNORECASE)
                issues.append(Issue(
                    file_path=file_path,
                    line_number=line_number,
                    column=line.lower().find(typo.lower()),
                    issue_type=IssueType.TYPO,
                    severity=Severity.MEDIUM,
                    description=f"Typo: '{typo}' should be '{fix}'",
                    original_code=line.rstrip(),
                    fixed_code=fixed_line.rstrip(),
                    auto_fixable=True
                ))
        
        return issues


class SyntaxFixer:
    """Handles syntax error detection and fixing"""
    
    @staticmethod
    def check_syntax(content: str, file_path: str) -> List[Issue]:
        """Check for syntax errors"""
        issues = []
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(Issue(
                file_path=file_path,
                line_number=e.lineno or 0,
                column=e.offset or 0,
                issue_type=IssueType.SYNTAX_ERROR,
                severity=Severity.CRITICAL,
                description=f"Syntax error: {e.msg}",
                original_code=e.text or '',
                fixed_code='',
                auto_fixable=True
            ))
        
        return issues
    
    @staticmethod
    def fix_syntax_error(lines: List[str], issue: Issue) -> Tuple[List[str], bool]:
        """Attempt to fix a syntax error"""
        line_idx = issue.line_number - 1
        if line_idx < 0 or line_idx >= len(lines):
            return lines, False
        
        line = lines[line_idx]
        fixed = False
        
        # Missing colon at end of def/class/if/for/while/try/except/with
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
        
        return lines, fixed


class CodeSmellFixer:
    """Handles code smell detection and fixing"""
    
    @staticmethod
    def check_bare_except(line: str, line_number: int, file_path: str) -> Optional[Issue]:
        """Check for bare except clause"""
        if re.match(r'^\s*except\s*:\s*$', line):
            indent = len(line) - len(line.lstrip())
            return Issue(
                file_path=file_path,
                line_number=line_number,
                column=indent,
                issue_type=IssueType.BARE_EXCEPT,
                severity=Severity.MEDIUM,
                description="Bare except clause - should specify exception type",
                original_code=line.rstrip(),
                fixed_code=' ' * indent + 'except Exception:',
                auto_fixable=True
            )
        return None
    
    @staticmethod
    def check_none_comparison(line: str, line_number: int, file_path: str) -> List[Issue]:
        """Check for == None or != None"""
        issues = []
        
        if ' == None' in line:
            fixed_line = line.replace(' == None', ' is None')
            issues.append(Issue(
                file_path=file_path,
                line_number=line_number,
                column=line.find(' == None'),
                issue_type=IssueType.NONE_COMPARISON,
                severity=Severity.LOW,
                description='Use "is None" instead of "== None"',
                original_code=line.rstrip(),
                fixed_code=fixed_line.rstrip(),
                auto_fixable=True
            ))
        
        if ' != None' in line:
            fixed_line = line.replace(' != None', ' is not None')
            issues.append(Issue(
                file_path=file_path,
                line_number=line_number,
                column=line.find(' != None'),
                issue_type=IssueType.NONE_COMPARISON,
                severity=Severity.LOW,
                description='Use "is not None" instead of "!= None"',
                original_code=line.rstrip(),
                fixed_code=fixed_line.rstrip(),
                auto_fixable=True
            ))
        
        return issues
    
    @staticmethod
    def check_mixed_indentation(line: str, line_number: int, file_path: str) -> Optional[Issue]:
        """Check for mixed tabs and spaces"""
        if '\t' in line and '    ' in line:
            fixed_line = line.replace('\t', '    ')
            return Issue(
                file_path=file_path,
                line_number=line_number,
                column=0,
                issue_type=IssueType.MIXED_INDENTATION,
                severity=Severity.MEDIUM,
                description="Mixed tabs and spaces in indentation",
                original_code=line.rstrip(),
                fixed_code=fixed_line.rstrip(),
                auto_fixable=True
            )
        return None
    
    @staticmethod
    def check_trailing_whitespace(line: str, line_number: int, file_path: str) -> Optional[Issue]:
        """Check for trailing whitespace"""
        if line.rstrip() != line.rstrip('\n\r') and line.endswith((' \n', ' \r\n', '\t\n')):
            return Issue(
                file_path=file_path,
                line_number=line_number,
                column=len(line.rstrip()),
                issue_type=IssueType.TRAILING_WHITESPACE,
                severity=Severity.LOW,
                description="Trailing whitespace",
                original_code=line.rstrip('\n\r'),
                fixed_code=line.rstrip(),
                auto_fixable=True
            )
        return None
    
    @staticmethod
    def check_mutable_default(line: str, line_number: int, file_path: str) -> Optional[Issue]:
        """Check for mutable default arguments"""
        if re.search(r'def\s+\w+\s*\([^)]*=\s*\[\]', line) or \
           re.search(r'def\s+\w+\s*\([^)]*=\s*\{\}', line):
            return Issue(
                file_path=file_path,
                line_number=line_number,
                column=0,
                issue_type=IssueType.MUTABLE_DEFAULT,
                severity=Severity.HIGH,
                description="Mutable default argument (use None and initialize inside function)",
                original_code=line.rstrip(),
                fixed_code='',
                auto_fixable=False  # Too complex to auto-fix safely
            )
        return None


class SecurityChecker:
    """Handles security issue detection"""
    
    @staticmethod
    def check_eval_exec(line: str, line_number: int, file_path: str) -> List[Issue]:
        """Check for dangerous eval/exec usage"""
        issues = []
        
        if re.search(r'\beval\s*\(', line):
            issues.append(Issue(
                file_path=file_path,
                line_number=line_number,
                column=line.find('eval'),
                issue_type=IssueType.EVAL_USAGE,
                severity=Severity.HIGH,
                description="Dangerous eval() usage - potential code injection",
                original_code=line.rstrip(),
                fixed_code='',
                auto_fixable=False
            ))
        
        if re.search(r'\bexec\s*\(', line):
            issues.append(Issue(
                file_path=file_path,
                line_number=line_number,
                column=line.find('exec'),
                issue_type=IssueType.EXEC_USAGE,
                severity=Severity.HIGH,
                description="Dangerous exec() usage - potential code injection",
                original_code=line.rstrip(),
                fixed_code='',
                auto_fixable=False
            ))
        
        return issues
    
    @staticmethod
    def check_hardcoded_secrets(line: str, line_number: int, file_path: str) -> List[Issue]:
        """Check for hardcoded secrets"""
        issues = []
        
        patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'token'),
            (r'private_key\s*=\s*["\'][^"\']+["\']', 'private key'),
        ]
        
        for pattern, secret_type in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Skip if it's clearly a placeholder or environment variable
                if any(x in line.lower() for x in ['os.environ', 'getenv', 'your_', 'xxx', 'placeholder', '...']):
                    continue
                issues.append(Issue(
                    file_path=file_path,
                    line_number=line_number,
                    column=0,
                    issue_type=IssueType.HARDCODED_SECRET,
                    severity=Severity.CRITICAL,
                    description=f"Potential hardcoded {secret_type}",
                    original_code=line.rstrip(),
                    fixed_code='',
                    auto_fixable=False
                ))
        
        return issues


class AutonomousCodeFixer:
    """
    Main class that orchestrates all code fixing operations.
    Scans entire codebase, finds all issues, and fixes them automatically.
    """
    
    def __init__(self, root_dir: str, dry_run: bool = False, verbose: bool = False):
        self.root_dir = Path(root_dir).resolve()
        self.dry_run = dry_run
        self.verbose = verbose
        self.report = FixReport(root_directory=str(self.root_dir))
        self.backup_dir = self.root_dir / 'autonomous_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Directories to skip
        self.skip_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env', 
            '.venv', 'node_modules', '.hypothesis', 'htmlcov',
            'autonomous_backups', '.mypy_cache', 'mlruns', 'models',
            'backup', 'archive', '.github', '.idea', '.vscode',
            'dist', 'build', 'egg-info', 'site-packages',
            'evolution_backups', 'complete_work_backups', 'fix_backups',
            'syntax_fix_backups', 'backups', 'old', 'deprecated'
        }
        
        # Files to skip
        self.skip_files = {
            'setup.py', 'conftest.py', '__init__.py'
        }
    
    def log(self, message: str, level: str = 'INFO'):
        """Log a message"""
        if self.verbose or level in ('ERROR', 'WARNING'):
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{level}] {message}")
    
    def create_backup(self, file_path: Path) -> bool:
        """Create backup of file before modifying"""
        if self.dry_run:
            return True
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            relative_path = file_path.relative_to(self.root_dir)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            self.log(f"Could not backup {file_path}: {e}", 'WARNING')
            return False
    
    def get_python_files(self) -> List[Path]:
        """Get all Python files in the codebase"""
        python_files = []
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if file.endswith('.py') and file not in self.skip_files:
                    python_files.append(Path(root) / file)
        
        return sorted(python_files)
    
    def scan_file(self, file_path: Path) -> List[Issue]:
        """Scan a single file for all issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines(keepends=True)
        except Exception as e:
            self.log(f"Could not read {file_path}: {e}", 'ERROR')
            return issues
        
        # Check syntax first
        syntax_issues = SyntaxFixer.check_syntax(content, str(file_path))
        issues.extend(syntax_issues)
        
        # If syntax is OK, check other issues
        if not syntax_issues:
            # Check imports
            issues.extend(ImportFixer.find_missing_imports(content, str(file_path)))
            
            # Check each line
            for i, line in enumerate(lines, 1):
                # Typos
                issues.extend(TypoFixer.find_typos(line, i, str(file_path)))
                
                # Code smells
                bare_except = CodeSmellFixer.check_bare_except(line, i, str(file_path))
                if bare_except:
                    issues.append(bare_except)
                
                issues.extend(CodeSmellFixer.check_none_comparison(line, i, str(file_path)))
                
                mixed_indent = CodeSmellFixer.check_mixed_indentation(line, i, str(file_path))
                if mixed_indent:
                    issues.append(mixed_indent)
                
                trailing_ws = CodeSmellFixer.check_trailing_whitespace(line, i, str(file_path))
                if trailing_ws:
                    issues.append(trailing_ws)
                
                mutable_default = CodeSmellFixer.check_mutable_default(line, i, str(file_path))
                if mutable_default:
                    issues.append(mutable_default)
                
                # Security
                issues.extend(SecurityChecker.check_eval_exec(line, i, str(file_path)))
                issues.extend(SecurityChecker.check_hardcoded_secrets(line, i, str(file_path)))
        
        return issues
    
    def fix_file(self, file_path: Path, issues: List[Issue]) -> int:
        """Apply fixes to a file"""
        if not issues or self.dry_run:
            return 0
        
        # Filter to auto-fixable issues with fixes
        fixable_issues = [i for i in issues if i.auto_fixable and i.fixed_code]
        
        if not fixable_issues:
            return 0
        
        try:
            # Create backup
            if not self.create_backup(file_path):
                return 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Separate import issues from line issues
            import_issues = [i for i in fixable_issues if i.issue_type == IssueType.MISSING_IMPORT]
            line_issues = [i for i in fixable_issues if i.issue_type != IssueType.MISSING_IMPORT]
            
            # Sort line issues by line number (descending) to fix from bottom up
            line_issues.sort(key=lambda x: x.line_number, reverse=True)
            
            fixes_applied = 0
            
            # Apply line fixes first (from bottom to top)
            for issue in line_issues:
                line_idx = issue.line_number - 1
                if 0 <= line_idx < len(lines):
                    original = lines[line_idx].rstrip()
                    if original == issue.original_code or issue.original_code in original:
                        lines[line_idx] = issue.fixed_code + '\n'
                        fixes_applied += 1
            
            # Apply import fixes
            if import_issues:
                # Find the right place to insert imports
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
                    
                    # Skip comments and empty lines at the top
                    if not stripped or stripped.startswith('#'):
                        continue
                    
                    # Track import section
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        insert_idx = i + 1
                    elif insert_idx > 0:
                        # We've passed the import section
                        break
                
                # Add imports
                existing_imports = set(''.join(lines[:insert_idx + 10]))
                for issue in import_issues:
                    if issue.fixed_code not in existing_imports:
                        lines.insert(insert_idx, issue.fixed_code + '\n')
                        insert_idx += 1
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
                self.log(f"Fix validation failed for {file_path}, restored backup", 'WARNING')
                return 0
                
        except Exception as e:
            self.log(f"Failed to fix {file_path}: {e}", 'ERROR')
            return 0
    
    def run(self) -> FixReport:
        """Run the autonomous code fixer"""
        print("=" * 70)
        print("AUTONOMOUS CODE FIXER - STARTING")
        print("=" * 70)
        print()
        
        if self.dry_run:
            print("[MODE] DRY RUN - No files will be modified")
            print()
        
        # Get all Python files
        python_files = self.get_python_files()
        self.report.total_files_scanned = len(python_files)
        
        print(f"[INFO] Root directory: {self.root_dir}")
        print(f"[INFO] Found {len(python_files)} Python files to scan")
        print(f"[INFO] Backup directory: {self.backup_dir}")
        print()
        
        # Scan all files
        for i, file_path in enumerate(python_files, 1):
            relative_path = file_path.relative_to(self.root_dir)
            
            # Progress indicator
            progress = f"[{i}/{len(python_files)}]"
            print(f"{progress} Scanning: {relative_path}", end='')
            
            issues = self.scan_file(file_path)
            
            if issues:
                print(f" -> {len(issues)} issues found")
                self.report.issues.extend(issues)
                
                # Apply fixes
                fixes = self.fix_file(file_path, issues)
                if fixes > 0:
                    print(f"         -> {fixes} fixes applied")
                    self.report.fixed_files.append(str(relative_path))
                    self.report.total_issues_fixed += fixes
            else:
                print(" -> OK")
        
        # Update report statistics
        self.report.total_issues_found = len(self.report.issues)
        
        for issue in self.report.issues:
            type_name = issue.issue_type.name
            severity_name = issue.severity.name
            self.report.issues_by_type[type_name] = self.report.issues_by_type.get(type_name, 0) + 1
            self.report.issues_by_severity[severity_name] = self.report.issues_by_severity.get(severity_name, 0) + 1
        
        return self.report
    
    def print_report(self):
        """Print the fix report"""
        print()
        print("=" * 70)
        print("AUTONOMOUS CODE FIXER - REPORT")
        print("=" * 70)
        print()
        print(f"Files Scanned:    {self.report.total_files_scanned}")
        print(f"Issues Found:     {self.report.total_issues_found}")
        print(f"Issues Fixed:     {self.report.total_issues_fixed}")
        print(f"Files Modified:   {len(self.report.fixed_files)}")
        print()
        
        if self.report.issues_by_severity:
            print("Issues by Severity:")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                count = self.report.issues_by_severity.get(severity, 0)
                if count > 0:
                    marker = "[!]" if severity == 'CRITICAL' else "[H]" if severity == 'HIGH' else "[M]" if severity == 'MEDIUM' else "[L]"
                    print(f"  {marker} {severity}: {count}")
            print()
        
        if self.report.issues_by_type:
            print("Issues by Type (top 15):")
            sorted_types = sorted(self.report.issues_by_type.items(), key=lambda x: -x[1])[:15]
            for issue_type, count in sorted_types:
                print(f"  - {issue_type}: {count}")
            print()
        
        if self.report.fixed_files:
            print(f"Files Modified ({len(self.report.fixed_files)}):")
            for f in self.report.fixed_files[:20]:
                print(f"  [OK] {f}")
            if len(self.report.fixed_files) > 20:
                print(f"  ... and {len(self.report.fixed_files) - 20} more")
            print()
        
        # Show unfixed critical issues
        critical_unfixed = [i for i in self.report.issues 
                          if i.severity == Severity.CRITICAL and not i.auto_fixable]
        if critical_unfixed:
            print("[!] CRITICAL Issues (Manual Fix Required):")
            for issue in critical_unfixed[:10]:
                try:
                    rel_path = Path(issue.file_path).relative_to(self.root_dir)
                except ValueError:
                    rel_path = issue.file_path
                print(f"  - {rel_path}:{issue.line_number} - {issue.description}")
            if len(critical_unfixed) > 10:
                print(f"  ... and {len(critical_unfixed) - 10} more")
            print()
        
        print("=" * 70)
        print("AUTONOMOUS CODE FIXER - COMPLETE")
        print("=" * 70)
    
    def save_report(self):
        """Save detailed report to files"""
        # Create logs directory
        logs_dir = self.root_dir / 'autonomous_logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save text report
        text_report_path = logs_dir / f'fix_report_{timestamp}.txt'
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write("AUTONOMOUS CODE FIXER - DETAILED REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {self.report.timestamp}\n")
            f.write(f"Root Directory: {self.report.root_directory}\n")
            f.write("\n")
            f.write(f"Files Scanned: {self.report.total_files_scanned}\n")
            f.write(f"Issues Found: {self.report.total_issues_found}\n")
            f.write(f"Issues Fixed: {self.report.total_issues_fixed}\n")
            f.write("\n")
            
            f.write("ALL ISSUES:\n")
            f.write("-" * 70 + "\n")
            for issue in self.report.issues:
                try:
                    rel_path = Path(issue.file_path).relative_to(self.root_dir)
                except ValueError:
                    rel_path = issue.file_path
                f.write(f"[{issue.severity.name}] {rel_path}:{issue.line_number}\n")
                f.write(f"  Type: {issue.issue_type.name}\n")
                f.write(f"  Description: {issue.description}\n")
                if issue.original_code:
                    f.write(f"  Original: {issue.original_code}\n")
                if issue.fixed_code:
                    f.write(f"  Fixed: {issue.fixed_code}\n")
                f.write(f"  Auto-fixable: {issue.auto_fixable}\n")
                f.write("\n")
        
        # Save JSON report
        json_report_path = logs_dir / f'fix_report_{timestamp}.json'
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report.to_dict(), f, indent=2, default=str)
        
        print(f"[INFO] Text report saved to: {text_report_path}")
        print(f"[INFO] JSON report saved to: {json_report_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Autonomous Code Fixer - Scans and fixes all code issues'
    )
    parser.add_argument(
        '--path', '-p',
        default=os.getcwd(),
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Scan only, do not modify files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Run the fixer
    fixer = AutonomousCodeFixer(
        root_dir=args.path,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    fixer.run()
    fixer.print_report()
    fixer.save_report()


if __name__ == '__main__':
    main()
