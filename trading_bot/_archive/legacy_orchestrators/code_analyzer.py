"""
Code Analyzer
Scans the codebase to find issues, code smells, missing features, and improvement opportunities.
"""

import os
import ast
import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    """Categories of code issues."""
    BUG = "bug"
    CODE_SMELL = "code_smell"
    MISSING_FEATURE = "missing_feature"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    INCOMPLETE = "incomplete"
    DEPRECATED = "deprecated"
    DUPLICATE = "duplicate"
    ARCHITECTURE = "architecture"


class IssueSeverity(Enum):
    """Severity levels."""
    CRITICAL = "critical"  # Must fix immediately
    HIGH = "high"  # Should fix soon
    MEDIUM = "medium"  # Fix when possible
    LOW = "low"  # Nice to fix
    INFO = "info"  # Informational


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    issue_id: str
    file_path: str
    line_number: int
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    current_code: str
    suggested_fix: str
    risk_of_change: str
    effort_estimate: str  # low, medium, high
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'issue_id': self.issue_id,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'current_code': self.current_code,
            'suggested_fix': self.suggested_fix,
            'risk_of_change': self.risk_of_change,
            'effort_estimate': self.effort_estimate,
            'detected_at': self.detected_at.isoformat()
        }


class CodeAnalyzer:
    """
    Analyzes the trading bot codebase to find:
    - Bugs and potential issues
    - Code smells and anti-patterns
    - Missing features and incomplete implementations
    - Security vulnerabilities
    - Performance issues
    - Maintainability problems
    """
    
    def __init__(self, base_path: str):
        """
        Initialize code analyzer.
        
        Args:
            base_path: Root path of the trading bot codebase
        """
        self.base_path = Path(base_path)
        self.issues: List[CodeIssue] = []
        self.issue_counter = 0
        
        # Patterns to detect
        self.hack_pattern = re.compile(r'#\s*HACK[:\s]*(.*)', re.IGNORECASE)
        self.pass_pattern = re.compile(r'^\s*pass\s*$')
        self.bare_except_pattern = re.compile(r'except\s*:')
        self.hardcoded_pattern = re.compile(r'(api_key|password|secret|token)\s*=\s*["\'][^"\']+["\']', re.IGNORECASE)
        self.magic_number_pattern = re.compile(r'(?<![a-zA-Z_])(\d+\.?\d*)\s*[<>=!]+')
        
        logger.info(f"CodeAnalyzer initialized for {base_path}")
    
    def _generate_issue_id(self) -> str:
        """Generate unique issue ID."""
        self.issue_counter += 1
        return f"ISSUE-{datetime.now().strftime('%Y%m%d')}-{self.issue_counter:04d}"
    
    def analyze_codebase(self, max_files: int = 100) -> List[CodeIssue]:
        """
        Analyze the entire codebase for issues.
        
        Args:
            max_files: Maximum number of files to analyze
            
        Returns:
            List of code issues found
        """
        logger.info("Starting codebase analysis...")
        self.issues = []
        files_analyzed = 0
        
        # Get all Python files
        python_files = list(self.base_path.rglob("*.py"))
        
        # Exclude certain directories
        exclude_dirs = {'__pycache__', '.git', 'venv', 'env', '.hypothesis', 'htmlcov', 'mlruns'}
        python_files = [
            f for f in python_files 
            if not any(ex in str(f) for ex in exclude_dirs)
        ]
        
        for file_path in python_files[:max_files]:
            try:
                self._analyze_file(file_path)
                files_analyzed += 1
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
        
        logger.info(f"Analyzed {files_analyzed} files, found {len(self.issues)} issues")
        return self.issues
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for issues."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return

        rel_path = str(file_path.relative_to(self.base_path))

        try:
            # Run all analyzers
            self._check_empty_functions(rel_path, content, lines)
            self._check_bare_excepts(rel_path, lines)
            self._check_hardcoded_secrets(rel_path, lines)
            self._check_long_functions(rel_path, content)
            self._check_missing_docstrings(rel_path, content)
            self._check_unused_imports(rel_path, content)
            self._check_complex_conditions(rel_path, lines)
            self._check_deprecated_patterns(rel_path, content)

        except Exception as e:
            logger.error(f'Error running analyzers on {rel_path}: {e}')

    def _check_todo_markers(self, file_path: str, lines: list) -> None:
        """Check for TODO/FIXME/HACK markers."""
        for i, line in enumerate(lines, 1):
            # TODO markers
            if hasattr(self, 'todo_pattern'):
                match = self.todo_pattern.search(line)
                if match:
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=i,
                        category=IssueCategory.INCOMPLETE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"TODO marker found: {match.group(1) if match.lastindex else line.strip()[:80]}",
                        current_code=line.strip(),
                        suggested_fix="Implement the TODO or remove if no longer needed",
                        risk_of_change="low",
                    ))
            
            # HACK markers
            if hasattr(self, 'hack_pattern'):
                match = self.hack_pattern.search(line)
                if match:
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=i,
                        category=IssueCategory.CODE_SMELL,
                        severity=IssueSeverity.MEDIUM,
                        title=f"HACK: {match.group(1)[:50] if match.lastindex else 'unknown'}",
                        description=f"Hacky code that needs proper implementation",
                        current_code=line.strip(),
                        suggested_fix="Refactor to use proper implementation",
                        risk_of_change="medium",
                        effort_estimate="high"
                    ))
    
    def _check_empty_functions(self, file_path: str, content: str, lines: List[str]) -> None:
        """Check for empty functions with just 'pass'."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function body is just 'pass' or docstring + pass
                body = node.body
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=node.lineno,
                        category=IssueCategory.INCOMPLETE,
                        severity=IssueSeverity.MEDIUM,
                        title=f"Empty function: {node.name}",
                        description=f"Function '{node.name}' has no implementation (just 'pass')",
                        current_code=f"def {node.name}(...): pass",
                        risk_of_change="low",
                        effort_estimate="medium"
                    ))
                elif len(body) == 2 and isinstance(body[0], ast.Expr) and isinstance(body[1], ast.Pass):
                    # Docstring + pass
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=node.lineno,
                        category=IssueCategory.INCOMPLETE,
                        severity=IssueSeverity.MEDIUM,
                        title=f"Stub function: {node.name}",
                        current_code=f"def {node.name}(...): '''...''' pass",
                        risk_of_change="low",
                        effort_estimate="medium"
                    ))
    
    def _check_bare_excepts(self, file_path: str, lines: List[str]) -> None:
        """Check for bare except clauses."""
        for i, line in enumerate(lines, 1):
            if self.bare_except_pattern.search(line):
                self.issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    file_path=file_path,
                    line_number=i,
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.MEDIUM,
                    title="Bare except clause",
                    description="Bare 'except Exception:' catches all exceptions including KeyboardInterrupt and SystemExit",
                    current_code=line.strip(),
                    suggested_fix="except Exception as e:",
                    risk_of_change="low",
                    effort_estimate="low"
                ))
    
    def _check_hardcoded_secrets(self, file_path: str, lines: List[str]) -> None:
        """Check for hardcoded secrets."""
        for i, line in enumerate(lines, 1):
            if self.hardcoded_pattern.search(line):
                self.issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    file_path=file_path,
                    line_number=i,
                    category=IssueCategory.SECURITY,
                    severity=IssueSeverity.CRITICAL,
                    title="Hardcoded secret detected",
                    description="Potential hardcoded API key, password, or secret found",
                    current_code="[REDACTED]",
                    suggested_fix="Use environment variables or secure vault",
                    risk_of_change="medium",
                    effort_estimate="low"
                ))
    
    def _check_long_functions(self, file_path: str, content: str) -> None:
        """Check for functions that are too long."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 100:
                        self.issues.append(CodeIssue(
                            issue_id=self._generate_issue_id(),
                            file_path=file_path,
                            line_number=node.lineno,
                            category=IssueCategory.MAINTAINABILITY,
                            severity=IssueSeverity.MEDIUM,
                            title=f"Long function: {node.name} ({length} lines)",
                            description=f"Function '{node.name}' is {length} lines long. Consider breaking it up.",
                            current_code=f"def {node.name}(...): # {length} lines",
                            suggested_fix="Break into smaller, focused functions",
                            risk_of_change="high",
                            effort_estimate="high"
                        ))
    
    def _check_missing_docstrings(self, file_path: str, content: str) -> None:
        """Check for functions and classes missing docstrings."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private/dunder methods
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                
                # Check for docstring
                if not (node.body and isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                    kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=node.lineno,
                        category=IssueCategory.MAINTAINABILITY,
                        severity=IssueSeverity.LOW,
                        title=f"Missing docstring: {node.name}",
                        description=f"{kind} '{node.name}' is missing a docstring",
                        current_code=f"def {node.name}(...):",
                        suggested_fix=f'Add docstring: """Description of {node.name}."""',
                        risk_of_change="low",
                        effort_estimate="low"
                    ))
    
    def _check_unused_imports(self, file_path: str, content: str) -> None:
        """Check for potentially unused imports."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    imports.add((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':
                        name = alias.asname if alias.asname else alias.name
                        imports.add((name, node.lineno))
        
        # Check if imports are used (simple check)
        for name, lineno in imports:
            # Count occurrences (excluding the import line itself)
            pattern = re.compile(r'\b' + re.escape(name) + r'\b')
            matches = pattern.findall(content)
            if len(matches) <= 1:  # Only the import itself
                self.issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    file_path=file_path,
                    line_number=lineno,
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.LOW,
                    title=f"Potentially unused import: {name}",
                    description=f"Import '{name}' appears to be unused",
                    current_code=f"import {name}",
                    suggested_fix=f"Remove unused import or use it",
                    risk_of_change="low",
                    effort_estimate="low"
                ))
    
    def _check_complex_conditions(self, file_path: str, lines: List[str]) -> None:
        """Check for overly complex conditions."""
        for i, line in enumerate(lines, 1):
            # Count logical operators
            and_count = line.count(' and ')
            or_count = line.count(' or ')
            if and_count + or_count >= 4:
                self.issues.append(CodeIssue(
                    issue_id=self._generate_issue_id(),
                    file_path=file_path,
                    line_number=i,
                    category=IssueCategory.MAINTAINABILITY,
                    severity=IssueSeverity.MEDIUM,
                    title="Complex condition",
                    description=f"Condition has {and_count + or_count} logical operators. Consider simplifying.",
                    current_code=line.strip()[:100],
                    suggested_fix="Break into smaller conditions or use helper functions",
                    risk_of_change="medium",
                    effort_estimate="medium"
                ))
    
    def _check_missing_error_handling(self, file_path: str, content: str) -> None:
        """Check for risky operations without error handling."""
        risky_patterns = [
            (r'open\([^)]+\)(?!.*with)', "File open without context manager"),
            (r'\.connect\(', "Connection without error handling"),
            (r'requests\.(get|post|put|delete)\(', "HTTP request without error handling"),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, description in risky_patterns:
                if re.search(pattern, line):
                    # Check if there's a try block nearby
                    context_start = max(0, i - 5)
                    context = '\n'.join(lines[context_start:i])
                    if 'try:' not in context:
                        self.issues.append(CodeIssue(
                            issue_id=self._generate_issue_id(),
                            file_path=file_path,
                            line_number=i,
                            category=IssueCategory.BUG,
                            severity=IssueSeverity.MEDIUM,
                            title=description,
                            description=f"{description} - may cause unhandled exceptions",
                            current_code=line.strip()[:100],
                            suggested_fix="Wrap in try-except block",
                            risk_of_change="medium",
                            effort_estimate="low"
                        ))
                        break
    
    def _check_deprecated_patterns(self, file_path: str, content: str) -> None:
        """Check for deprecated patterns."""
        deprecated = [
            (r'from typing import Optional', 'Use X | None instead of Optional[X] (Python 3.10+)'),
            (r'\.format\(', 'Consider using f-strings instead of .format()'),
            (r'%\s*\(', 'Consider using f-strings instead of % formatting'),
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, suggestion in deprecated:
                if re.search(pattern, line):
                    self.issues.append(CodeIssue(
                        issue_id=self._generate_issue_id(),
                        file_path=file_path,
                        line_number=i,
                        category=IssueCategory.DEPRECATED,
                        severity=IssueSeverity.INFO,
                        title="Deprecated pattern",
                        description=suggestion,
                        current_code=line.strip()[:100],
                        suggested_fix=suggestion,
                        risk_of_change="low",
                        effort_estimate="low"
                    ))
                    break
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results."""
        by_category = {}
        by_severity = {}
        by_file = {}
        
        for issue in self.issues:
            # By category
            cat = issue.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # By severity
            sev = issue.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            # By file
            by_file[issue.file_path] = by_file.get(issue.file_path, 0) + 1
        
        # Top 10 files with most issues
        top_files = sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_issues': len(self.issues),
            'by_category': by_category,
            'by_severity': by_severity,
            'top_problem_files': top_files,
            'critical_count': by_severity.get('critical', 0),
            'high_count': by_severity.get('high', 0)
        }
    
    def get_issues_for_file(self, file_path: str) -> List[CodeIssue]:
        """Get all issues for a specific file."""
        return [i for i in self.issues if i.file_path == file_path]
    
    def get_critical_issues(self) -> List[CodeIssue]:
        """Get only critical and high severity issues."""
        return [i for i in self.issues if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.HIGH)]
    
    def save_report(self, output_path: str) -> None:
        """Save analysis report to JSON file."""
        report = {
            'analysis_time': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'summary': self.get_summary(),
            'issues': [i.to_dict() for i in self.issues]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")
