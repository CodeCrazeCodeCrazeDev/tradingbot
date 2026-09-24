"""
Code Safety Scanner
====================

Scans AI-generated code for security vulnerabilities and safety issues.
All code MUST pass this scanner before sandbox execution.

Security Checks:
1. Static analysis for dangerous patterns
2. Import validation
3. Resource usage estimation
4. Complexity analysis
5. Malicious code detection

Author: AlphaAlgo Trading System
"""

import ast
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for code."""
    SAFE = "safe"              # No issues detected
    LOW_RISK = "low_risk"      # Minor issues
    MEDIUM_RISK = "medium_risk"  # Moderate issues
    HIGH_RISK = "high_risk"    # Serious issues
    CRITICAL = "critical"      # Dangerous code - block execution
    MALICIOUS = "malicious"    # Intentionally harmful - block and alert


class IssueCategory(Enum):
    """Categories of security issues."""
    DANGEROUS_IMPORT = "dangerous_import"
    DANGEROUS_FUNCTION = "dangerous_function"
    FILE_SYSTEM_ACCESS = "file_system_access"
    NETWORK_ACCESS = "network_access"
    CODE_EXECUTION = "code_execution"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATA_EXFILTRATION = "data_exfiltration"
    OBFUSCATION = "obfuscation"
    INFINITE_LOOP = "infinite_loop"
    COMPLEXITY = "complexity"


@dataclass
class SecurityIssue:
    """A security issue found in code."""
    issue_id: str
    category: IssueCategory
    severity: SecurityLevel
    line_number: Optional[int]
    column: Optional[int]
    code_snippet: str
    description: str
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_id': self.issue_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'line_number': self.line_number,
            'column': self.column,
            'code_snippet': self.code_snippet[:200],
            'description': self.description,
            'recommendation': self.recommendation,
        }


@dataclass
class ScanResult:
    """Result of code safety scan."""
    scan_id: str
    code_hash: str
    scanned_at: datetime
    
    # Overall Assessment
    security_level: SecurityLevel
    is_safe: bool
    can_execute: bool
    
    # Issues
    issues: List[SecurityIssue] = field(default_factory=list)
    
    # Metrics
    lines_of_code: int = 0
    complexity_score: float = 0.0
    import_count: int = 0
    function_count: int = 0
    class_count: int = 0
    
    # Blocked Items
    blocked_imports: List[str] = field(default_factory=list)
    blocked_functions: List[str] = field(default_factory=list)
    
    # Scan Details
    scan_duration_ms: float = 0.0
    checks_performed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scan_id': self.scan_id,
            'code_hash': self.code_hash,
            'scanned_at': self.scanned_at.isoformat(),
            'security_level': self.security_level.value,
            'is_safe': self.is_safe,
            'can_execute': self.can_execute,
            'issues': [i.to_dict() for i in self.issues],
            'lines_of_code': self.lines_of_code,
            'complexity_score': self.complexity_score,
            'import_count': self.import_count,
            'function_count': self.function_count,
            'class_count': self.class_count,
            'blocked_imports': self.blocked_imports,
            'blocked_functions': self.blocked_functions,
            'scan_duration_ms': self.scan_duration_ms,
            'checks_performed': self.checks_performed,
        }


@dataclass
class ScannerConfig:
    """Configuration for code safety scanner."""
    # Blocked Imports
    blocked_imports: Set[str] = field(default_factory=lambda: {
        'os', 'sys', 'subprocess', 'shutil', 'pathlib',
        'socket', 'requests', 'urllib', 'http', 'ftplib',
        'smtplib', 'telnetlib', 'paramiko', 'fabric',
        'pickle', 'shelve', 'marshal', 'dill',
        'ctypes', 'cffi', 'multiprocessing',
        'threading', 'concurrent',
        'importlib', 'imp', 'pkgutil',
        'code', 'codeop', 'compile',
        'gc', 'inspect', 'traceback',
        'signal', 'atexit',
        'sqlite3', 'pymysql', 'psycopg2', 'redis',
        'boto3', 'azure', 'google.cloud',
    })
    
    # Allowed Imports (whitelist)
    allowed_imports: Set[str] = field(default_factory=lambda: {
        'math', 'statistics', 'random', 'decimal', 'fractions',
        'datetime', 'time', 'calendar',
        'collections', 'itertools', 'functools', 'operator',
        'copy', 'typing', 'dataclasses', 'enum',
        'json', 'csv', 're', 'string',
        'numpy', 'pandas', 'scipy', 'sklearn', 'statsmodels',
        'ta', 'talib',  # Technical analysis
    })
    
    # Dangerous Functions
    dangerous_functions: Set[str] = field(default_factory=lambda: {
        'eval', 'exec', 'compile', '__import__',
        'open', 'file', 'input', 'raw_input',
        'globals', 'locals', 'vars', 'dir',
        'getattr', 'setattr', 'delattr', 'hasattr',
        'type', 'isinstance', 'issubclass',
        'exit', 'quit', 'help',
    })
    
    # Complexity Limits
    max_lines: int = 1000
    max_complexity: float = 50.0
    max_nesting_depth: int = 6
    max_function_length: int = 100
    
    # Resource Limits
    max_loop_iterations: int = 10000
    max_recursion_depth: int = 100
    
    # Paths
    scan_log_path: str = "code_scan_logs"


class ASTAnalyzer(ast.NodeVisitor):
    """AST-based code analyzer."""
    
    def __init__(self, config: ScannerConfig):
        self.config = config
        self.issues: List[SecurityIssue] = []
        self.imports: List[str] = []
        self.functions: List[str] = []
        self.classes: List[str] = []
        self.dangerous_calls: List[Tuple[str, int]] = []
        self.nesting_depth = 0
        self.max_nesting = 0
        self.loop_count = 0
        self.has_while_true = False
    
    def visit_Import(self, node: ast.Import):
        """Check import statements."""
        for alias in node.names:
            module = alias.name.split('.')[0]
            self.imports.append(module)
            
            if module in self.config.blocked_imports:
                self.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.DANGEROUS_IMPORT,
                    severity=SecurityLevel.CRITICAL,
                    line_number=node.lineno,
                    column=node.col_offset,
                    code_snippet=f"import {alias.name}",
                    description=f"Blocked import: {module}",
                    recommendation=f"Remove import of {module}",
                ))
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Check from...import statements."""
        if node.module:
            module = node.module.split('.')[0]
            self.imports.append(module)
            
            if module in self.config.blocked_imports:
                self.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.DANGEROUS_IMPORT,
                    severity=SecurityLevel.CRITICAL,
                    line_number=node.lineno,
                    column=node.col_offset,
                    code_snippet=f"from {node.module} import ...",
                    description=f"Blocked import: {module}",
                    recommendation=f"Remove import from {module}",
                ))
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Check function calls."""
        func_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name:
            if func_name in self.config.dangerous_functions:
                severity = SecurityLevel.CRITICAL if func_name in ['eval', 'exec'] else SecurityLevel.HIGH_RISK
                
                self.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.DANGEROUS_FUNCTION,
                    severity=severity,
                    line_number=node.lineno,
                    column=node.col_offset,
                    code_snippet=f"{func_name}(...)",
                    description=f"Dangerous function call: {func_name}",
                    recommendation=f"Remove or replace {func_name}() call",
                ))
                
                self.dangerous_calls.append((func_name, node.lineno))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function definitions."""
        self.functions.append(node.name)
        
        # Check function length
        func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
        if func_lines > self.config.max_function_length:
            self.issues.append(SecurityIssue(
                issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                category=IssueCategory.COMPLEXITY,
                severity=SecurityLevel.LOW_RISK,
                line_number=node.lineno,
                column=node.col_offset,
                code_snippet=f"def {node.name}(...)",
                description=f"Function too long: {func_lines} lines",
                recommendation=f"Split function into smaller functions",
            ))
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Analyze class definitions."""
        self.classes.append(node.name)
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While):
        """Check while loops."""
        self.loop_count += 1
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        
        # Check for while True without break
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            has_break = any(
                isinstance(child, ast.Break)
                for child in ast.walk(node)
            )
            
            if not has_break:
                self.has_while_true = True
                self.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.INFINITE_LOOP,
                    severity=SecurityLevel.HIGH_RISK,
                    line_number=node.lineno,
                    column=node.col_offset,
                    code_snippet="while True: ...",
                    description="Potential infinite loop: while True without break",
                    recommendation="Add break condition or use for loop with limit",
                ))
        
        self.generic_visit(node)
        self.nesting_depth -= 1
    
    def visit_For(self, node: ast.For):
        """Check for loops."""
        self.loop_count += 1
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        
        self.generic_visit(node)
        self.nesting_depth -= 1
    
    def visit_If(self, node: ast.If):
        """Track nesting depth."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        
        self.generic_visit(node)
        self.nesting_depth -= 1
    
    def visit_Try(self, node: ast.Try):
        """Check try/except blocks."""
        # Check for bare except
        for handler in node.handlers:
            if handler.type is None:
                self.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.OBFUSCATION,
                    severity=SecurityLevel.LOW_RISK,
                    line_number=handler.lineno,
                    column=handler.col_offset,
                    code_snippet="except:",
                    description="Bare except clause may hide errors",
                    recommendation="Specify exception type",
                ))
        
        self.generic_visit(node)


class PatternScanner:
    """Pattern-based code scanner."""
    
    # Dangerous patterns with severity
    PATTERNS = [
        # Code execution
        (r'\beval\s*\(', IssueCategory.CODE_EXECUTION, SecurityLevel.CRITICAL, "eval() call"),
        (r'\bexec\s*\(', IssueCategory.CODE_EXECUTION, SecurityLevel.CRITICAL, "exec() call"),
        (r'\bcompile\s*\(', IssueCategory.CODE_EXECUTION, SecurityLevel.HIGH_RISK, "compile() call"),
        (r'__import__\s*\(', IssueCategory.CODE_EXECUTION, SecurityLevel.CRITICAL, "__import__() call"),
        
        # File system
        (r'\bopen\s*\(', IssueCategory.FILE_SYSTEM_ACCESS, SecurityLevel.HIGH_RISK, "open() call"),
        (r'\.read\s*\(', IssueCategory.FILE_SYSTEM_ACCESS, SecurityLevel.MEDIUM_RISK, "file read"),
        (r'\.write\s*\(', IssueCategory.FILE_SYSTEM_ACCESS, SecurityLevel.HIGH_RISK, "file write"),
        (r'os\.remove', IssueCategory.FILE_SYSTEM_ACCESS, SecurityLevel.CRITICAL, "file deletion"),
        (r'shutil\.rmtree', IssueCategory.FILE_SYSTEM_ACCESS, SecurityLevel.CRITICAL, "directory deletion"),
        
        # Network
        (r'socket\.', IssueCategory.NETWORK_ACCESS, SecurityLevel.HIGH_RISK, "socket access"),
        (r'requests\.', IssueCategory.NETWORK_ACCESS, SecurityLevel.MEDIUM_RISK, "HTTP request"),
        (r'urllib\.', IssueCategory.NETWORK_ACCESS, SecurityLevel.MEDIUM_RISK, "URL access"),
        (r'http\.client', IssueCategory.NETWORK_ACCESS, SecurityLevel.MEDIUM_RISK, "HTTP client"),
        
        # Data exfiltration
        (r'base64\.b64encode', IssueCategory.DATA_EXFILTRATION, SecurityLevel.MEDIUM_RISK, "base64 encoding"),
        (r'\.encode\([\'"]hex', IssueCategory.DATA_EXFILTRATION, SecurityLevel.MEDIUM_RISK, "hex encoding"),
        
        # Obfuscation
        (r'\\x[0-9a-fA-F]{2}', IssueCategory.OBFUSCATION, SecurityLevel.MEDIUM_RISK, "hex escape sequence"),
        (r'chr\s*\(\s*\d+\s*\)', IssueCategory.OBFUSCATION, SecurityLevel.MEDIUM_RISK, "chr() obfuscation"),
        (r'ord\s*\(', IssueCategory.OBFUSCATION, SecurityLevel.LOW_RISK, "ord() call"),
        
        # Resource exhaustion
        (r'while\s+True\s*:', IssueCategory.INFINITE_LOOP, SecurityLevel.MEDIUM_RISK, "while True loop"),
        (r'for\s+\w+\s+in\s+range\s*\(\s*\d{7,}', IssueCategory.RESOURCE_EXHAUSTION, SecurityLevel.HIGH_RISK, "large range"),
        (r'\*\s*\d{6,}', IssueCategory.RESOURCE_EXHAUSTION, SecurityLevel.MEDIUM_RISK, "large multiplication"),
    ]
    
    def scan(self, code: str) -> List[SecurityIssue]:
        """Scan code for dangerous patterns."""
        issues = []
        lines = code.split('\n')
        
        for pattern, category, severity, description in self.PATTERNS:
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern, line)
                for match in matches:
                    issues.append(SecurityIssue(
                        issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                        category=category,
                        severity=severity,
                        line_number=line_num,
                        column=match.start(),
                        code_snippet=line.strip()[:100],
                        description=f"Pattern detected: {description}",
                        recommendation=f"Review and remove {description}",
                    ))
        
        return issues


class CodeSafetyScanner:
    """
    Comprehensive code safety scanner.
    
    All AI-generated code MUST pass this scanner before execution.
    Uses multiple analysis techniques:
    1. AST analysis for structural issues
    2. Pattern matching for dangerous code
    3. Complexity analysis
    4. Import validation
    """
    
    def __init__(self, config: Optional[ScannerConfig] = None):
        """
        Initialize the code safety scanner.
        
        Args:
            config: Scanner configuration
        """
        self.config = config or ScannerConfig()
        
        self._pattern_scanner = PatternScanner()
        
        # Scan history
        self._scan_history: Dict[str, ScanResult] = {}
        
        # Storage
        self._log_path = Path(self.config.scan_log_path)
        self._log_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("CodeSafetyScanner initialized")
    
    def scan(self, code: str) -> ScanResult:
        """
        Scan code for security issues.
        
        Args:
            code: Python code to scan
        
        Returns:
            ScanResult with findings
        """
        import time
        start_time = time.time()
        
        scan_id = f"SCAN-{uuid.uuid4().hex[:12]}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Check cache
        if code_hash in self._scan_history:
            cached = self._scan_history[code_hash]
            logger.debug(f"Returning cached scan result for {code_hash[:8]}")
            return cached
        
        result = ScanResult(
            scan_id=scan_id,
            code_hash=code_hash,
            scanned_at=datetime.now(timezone.utc),
            security_level=SecurityLevel.SAFE,
            is_safe=True,
            can_execute=True,
        )
        
        # Basic metrics
        lines = code.split('\n')
        result.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        # Check line count
        if result.lines_of_code > self.config.max_lines:
            result.issues.append(SecurityIssue(
                issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                category=IssueCategory.COMPLEXITY,
                severity=SecurityLevel.MEDIUM_RISK,
                line_number=None,
                column=None,
                code_snippet="",
                description=f"Code too long: {result.lines_of_code} lines",
                recommendation=f"Reduce to under {self.config.max_lines} lines",
            ))
        
        result.checks_performed.append('line_count')
        
        # AST Analysis
        try:
            tree = ast.parse(code)
            analyzer = ASTAnalyzer(self.config)
            analyzer.visit(tree)
            
            result.issues.extend(analyzer.issues)
            result.import_count = len(analyzer.imports)
            result.function_count = len(analyzer.functions)
            result.class_count = len(analyzer.classes)
            result.blocked_imports = [
                imp for imp in analyzer.imports
                if imp in self.config.blocked_imports
            ]
            result.blocked_functions = [
                func for func, _ in analyzer.dangerous_calls
            ]
            
            # Check nesting depth
            if analyzer.max_nesting > self.config.max_nesting_depth:
                result.issues.append(SecurityIssue(
                    issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                    category=IssueCategory.COMPLEXITY,
                    severity=SecurityLevel.MEDIUM_RISK,
                    line_number=None,
                    column=None,
                    code_snippet="",
                    description=f"Nesting too deep: {analyzer.max_nesting} levels",
                    recommendation=f"Reduce nesting to {self.config.max_nesting_depth} levels",
                ))
            
            # Calculate complexity score
            result.complexity_score = self._calculate_complexity(
                result.lines_of_code,
                analyzer.max_nesting,
                analyzer.loop_count,
                len(analyzer.functions),
            )
            
            result.checks_performed.append('ast_analysis')
            
        except SyntaxError as e:
            result.issues.append(SecurityIssue(
                issue_id=f"ISS-{uuid.uuid4().hex[:8]}",
                category=IssueCategory.COMPLEXITY,
                severity=SecurityLevel.CRITICAL,
                line_number=e.lineno,
                column=e.offset,
                code_snippet=e.text or "",
                description=f"Syntax error: {e.msg}",
                recommendation="Fix syntax error",
            ))
            result.can_execute = False
        
        # Pattern scanning
        pattern_issues = self._pattern_scanner.scan(code)
        result.issues.extend(pattern_issues)
        result.checks_performed.append('pattern_scan')
        
        # Determine overall security level
        result.security_level = self._determine_security_level(result.issues)
        
        # Determine if safe to execute
        result.is_safe = result.security_level in [SecurityLevel.SAFE, SecurityLevel.LOW_RISK]
        result.can_execute = result.security_level not in [
            SecurityLevel.CRITICAL, SecurityLevel.MALICIOUS
        ]
        
        # Record timing
        result.scan_duration_ms = (time.time() - start_time) * 1000
        
        # Cache result
        self._scan_history[code_hash] = result
        
        # Persist
        self._persist_result(result)
        
        logger.info(
            f"Scan {scan_id}: {result.security_level.value}, "
            f"{len(result.issues)} issues, can_execute={result.can_execute}"
        )
        
        return result
    
    def _calculate_complexity(
        self,
        lines: int,
        max_nesting: int,
        loop_count: int,
        function_count: int
    ) -> float:
        """Calculate code complexity score."""
        # Simple complexity metric
        complexity = 0.0
        
        # Lines contribution
        complexity += lines * 0.1
        
        # Nesting contribution (exponential)
        complexity += (2 ** max_nesting) * 0.5
        
        # Loop contribution
        complexity += loop_count * 2
        
        # Function contribution (more functions = more complex but also better structured)
        if function_count > 0:
            complexity += function_count * 1.5
        
        return min(100.0, complexity)
    
    def _determine_security_level(self, issues: List[SecurityIssue]) -> SecurityLevel:
        """Determine overall security level from issues."""
        if not issues:
            return SecurityLevel.SAFE
        
        # Get highest severity
        severities = [issue.severity for issue in issues]
        
        if SecurityLevel.MALICIOUS in severities:
            return SecurityLevel.MALICIOUS
        if SecurityLevel.CRITICAL in severities:
            return SecurityLevel.CRITICAL
        if SecurityLevel.HIGH_RISK in severities:
            return SecurityLevel.HIGH_RISK
        if SecurityLevel.MEDIUM_RISK in severities:
            return SecurityLevel.MEDIUM_RISK
        if SecurityLevel.LOW_RISK in severities:
            return SecurityLevel.LOW_RISK
        
        return SecurityLevel.SAFE
    
    def quick_check(self, code: str) -> Tuple[bool, List[str]]:
        """
        Quick safety check without full scan.
        
        Args:
            code: Code to check
        
        Returns:
            Tuple of (is_safe, list of issues)
        """
        issues = []
        
        # Check for obviously dangerous patterns
        dangerous = [
            ('eval(', 'eval() is not allowed'),
            ('exec(', 'exec() is not allowed'),
            ('__import__', '__import__ is not allowed'),
            ('os.system', 'os.system is not allowed'),
            ('subprocess', 'subprocess is not allowed'),
            ('open(', 'open() is not allowed'),
        ]
        
        for pattern, message in dangerous:
            if pattern in code:
                issues.append(message)
        
        # Check imports
        for blocked in self.config.blocked_imports:
            if f'import {blocked}' in code or f'from {blocked}' in code:
                issues.append(f'Import of {blocked} is not allowed')
        
        return len(issues) == 0, issues
    
    def _persist_result(self, result: ScanResult):
        """Persist scan result to disk."""
        try:
            result_file = self._log_path / f"{result.scan_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist scan result: {e}")
    
    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Get scan result by ID."""
        for result in self._scan_history.values():
            if result.scan_id == scan_id:
                return result
        return None
    
    def get_scan_by_hash(self, code_hash: str) -> Optional[ScanResult]:
        """Get scan result by code hash."""
        return self._scan_history.get(code_hash)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scanner statistics."""
        total_scans = len(self._scan_history)
        
        level_counts = {}
        for result in self._scan_history.values():
            level = result.security_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        safe_count = sum(1 for r in self._scan_history.values() if r.is_safe)
        executable_count = sum(1 for r in self._scan_history.values() if r.can_execute)
        
        return {
            'total_scans': total_scans,
            'by_security_level': level_counts,
            'safe_rate': safe_count / total_scans if total_scans > 0 else 0,
            'executable_rate': executable_count / total_scans if total_scans > 0 else 0,
            'total_issues_found': sum(len(r.issues) for r in self._scan_history.values()),
            'blocked_imports_count': len(self.config.blocked_imports),
            'allowed_imports_count': len(self.config.allowed_imports),
        }
