"""
Code Analyzer - AST-based code analysis and smell detection

Provides static analysis capabilities for the trading bot codebase,
detecting code smells, complexity issues, and potential bugs.
"""

import ast
import os
import logging
import py_compile
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for code issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeSmell:
    """Represents a detected code issue"""
    file_path: str
    line_number: int
    severity: SeverityLevel
    category: str
    message: str
    suggestion: Optional[str] = None

    def __str__(self):
        return f"[{self.severity.value.upper()}] {self.file_path}:{self.line_number} - {self.message}"


@dataclass
class AnalysisReport:
    """Complete analysis report for a codebase scan"""
    timestamp: datetime = field(default_factory=datetime.now)
    files_scanned: int = 0
    syntax_errors: List[Dict[str, Any]] = field(default_factory=list)
    code_smells: List[CodeSmell] = field(default_factory=list)
    duplicate_methods: List[Dict[str, Any]] = field(default_factory=list)
    complexity_issues: List[Dict[str, Any]] = field(default_factory=list)
    import_issues: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        return (
            len(self.syntax_errors) + len(self.code_smells) +
            len(self.duplicate_methods) + len(self.complexity_issues) +
            len(self.import_issues)
        )

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0


class CodeAnalyzer:
    """AST-based code analyzer for the trading bot codebase"""

    EXCLUDE_DIRS = {
        'autonomous_backups', 'auto_fix_backups', '.improvement_backups',
        'code_backups', '__pycache__', '.hypothesis', '.pytest_cache',
        'htmlcov', 'node_modules', '.git', '.venv', 'venv',
    }

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)

    def full_scan(self) -> AnalysisReport:
        """Run a complete codebase analysis"""
        report = AnalysisReport()
        python_files = self._find_python_files()
        report.files_scanned = len(python_files)

        for file_path in python_files:
            self._check_syntax(file_path, report)
            self._check_duplicates(file_path, report)
            self._check_broken_guards(file_path, report)
            self._check_future_imports(file_path, report)
            self._check_complexity(file_path, report)

        report.summary = {
            "files_scanned": report.files_scanned,
            "syntax_errors": len(report.syntax_errors),
            "code_smells": len(report.code_smells),
            "duplicate_methods": len(report.duplicate_methods),
            "complexity_issues": len(report.complexity_issues),
            "import_issues": len(report.import_issues),
            "total_issues": report.total_issues,
        }

        logger.info(
            f"Code analysis complete: {report.files_scanned} files, "
            f"{report.total_issues} issues found"
        )
        return report

    def _find_python_files(self) -> List[str]:
        """Find all Python files in the codebase"""
        files = []
        for root, dirs, filenames in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            for f in filenames:
                if f.endswith('.py'):
                    files.append(os.path.join(root, f))
        return files

    def _check_syntax(self, file_path: str, report: AnalysisReport):
        """Check for syntax errors using py_compile"""
        try:
            py_compile.compile(file_path, doraise=True)
        except py_compile.PyCompileError as e:
            report.syntax_errors.append({
                "file": file_path,
                "error": str(e),
            })

    def _check_duplicates(self, file_path: str, report: AnalysisReport):
        """Check for duplicate method definitions in classes"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods: Dict[str, int] = {}
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name in methods:
                                report.duplicate_methods.append({
                                    "file": file_path,
                                    "class": node.name,
                                    "method": item.name,
                                    "first_line": methods[item.name],
                                    "duplicate_line": item.lineno,
                                })
                            methods[item.name] = item.lineno
        except Exception:
            pass

    def _check_broken_guards(self, file_path: str, report: AnalysisReport):
        """Check for broken guard clauses (if cond: pass; try:)"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for i in range(len(lines) - 1):
                if lines[i].strip() == 'pass' and i > 0:
                    prev = lines[i - 1].strip()
                    if prev.startswith('if ') and prev.endswith(':'):
                        next_l = lines[i + 1].strip() if i + 1 < len(lines) else ''
                        if next_l == 'try:':
                            report.code_smells.append(CodeSmell(
                                file_path=file_path,
                                line_number=i + 1,
                                severity=SeverityLevel.ERROR,
                                category="broken_guard",
                                message=f"Broken guard clause: '{prev}' followed by pass+try",
                                suggestion="Move try block body into the if block",
                            ))
        except Exception:
            pass

    def _check_future_imports(self, file_path: str, report: AnalysisReport):
        """Check for misplaced __future__ imports"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)

            future_lines = []
            regular_import_lines = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == '__future__':
                    future_lines.append(node.lineno)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if not (isinstance(node, ast.ImportFrom) and node.module == '__future__'):
                        regular_import_lines.append(node.lineno)

            for fl in future_lines:
                for rl in regular_import_lines:
                    if rl < fl:
                        report.import_issues.append({
                            "file": file_path,
                            "line": fl,
                            "issue": "__future__ import after regular import",
                        })
                        break
        except Exception:
            pass

    def _check_complexity(self, file_path: str, report: AnalysisReport):
        """Check for overly complex functions"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)
                    if complexity > 15:
                        report.complexity_issues.append({
                            "file": file_path,
                            "function": node.name,
                            "line": node.lineno,
                            "complexity": complexity,
                        })
        except Exception:
            pass

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Assert, ast.Raise)):
                complexity += 1
        return complexity
