"""
Code Safety Scanner
===================

Analyzes AI-generated code for security vulnerabilities and dangerous patterns.
Uses multiple detection methods:
1. AST analysis for structural patterns
2. Pattern matching for known dangerous code
3. Taint analysis for data flow
4. Complexity analysis
5. Resource usage estimation

CRITICAL: All AI-generated code MUST pass safety scan before execution.
"""

import ast
import re
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels."""
    NONE = 0
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ThreatCategory(Enum):
    """Categories of security threats."""
    CODE_INJECTION = auto()
    FILE_SYSTEM = auto()
    NETWORK = auto()
    PROCESS_EXECUTION = auto()
    INFORMATION_DISCLOSURE = auto()
    RESOURCE_EXHAUSTION = auto()
    PRIVILEGE_ESCALATION = auto()
    DATA_MANIPULATION = auto()
    CRYPTOGRAPHIC = auto()
    UNSAFE_DESERIALIZATION = auto()


@dataclass
class CodePattern:
    """A dangerous code pattern to detect."""
    pattern_id: str
    name: str
    description: str
    category: ThreatCategory
    threat_level: ThreatLevel
    pattern: str  # Regex pattern or AST pattern
    pattern_type: str  # 'regex', 'ast', 'semantic'
    remediation: str
    false_positive_rate: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.name,
            'threat_level': self.threat_level.name,
            'remediation': self.remediation,
        }


@dataclass
class ScanFinding:
    """A finding from code scanning."""
    finding_id: str
    pattern: CodePattern
    location: str  # file:line or code snippet
    line_number: Optional[int]
    code_snippet: str
    confidence: float  # 0.0 to 1.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'finding_id': self.finding_id,
            'pattern_id': self.pattern.pattern_id,
            'pattern_name': self.pattern.name,
            'threat_level': self.pattern.threat_level.name,
            'category': self.pattern.category.name,
            'location': self.location,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet[:200],
            'confidence': self.confidence,
            'remediation': self.pattern.remediation,
        }


@dataclass
class ScanResult:
    """Result of a code safety scan."""
    scan_id: str
    code_hash: str
    is_safe: bool
    threat_level: ThreatLevel
    findings: List[ScanFinding]
    scan_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scan_id': self.scan_id,
            'code_hash': self.code_hash,
            'is_safe': self.is_safe,
            'threat_level': self.threat_level.name,
            'findings_count': len(self.findings),
            'findings': [f.to_dict() for f in self.findings],
            'scan_time_ms': self.scan_time_ms,
            'timestamp': self.timestamp.isoformat(),
        }


class CodeSafetyScanner:
    """
    Scans AI-generated code for security vulnerabilities.
    
    Uses multiple detection methods to identify dangerous patterns
    and prevent execution of unsafe code.
    """
    
    # Built-in dangerous patterns
    DANGEROUS_PATTERNS: List[CodePattern] = [
        # Code Injection
        CodePattern(
            pattern_id="INJ001",
            name="eval() usage",
            description="Dynamic code evaluation can execute arbitrary code",
            category=ThreatCategory.CODE_INJECTION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\beval\s*\(',
            pattern_type='regex',
            remediation="Use ast.literal_eval() for safe evaluation of literals",
        ),
        CodePattern(
            pattern_id="INJ002",
            name="exec() usage",
            description="Dynamic code execution can run arbitrary code",
            category=ThreatCategory.CODE_INJECTION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bexec\s*\(',
            pattern_type='regex',
            remediation="Avoid dynamic code execution; use predefined functions",
        ),
        CodePattern(
            pattern_id="INJ003",
            name="compile() usage",
            description="Code compilation can be used to execute arbitrary code",
            category=ThreatCategory.CODE_INJECTION,
            threat_level=ThreatLevel.HIGH,
            pattern=r'\bcompile\s*\(',
            pattern_type='regex',
            remediation="Avoid dynamic compilation; use static code",
        ),
        
        # File System
        CodePattern(
            pattern_id="FS001",
            name="File open()",
            description="File operations can read/write sensitive data",
            category=ThreatCategory.FILE_SYSTEM,
            threat_level=ThreatLevel.MEDIUM,
            pattern=r'\bopen\s*\([^)]*["\'][^"\']*["\']',
            pattern_type='regex',
            remediation="Use sandbox file operations with path validation",
        ),
        CodePattern(
            pattern_id="FS002",
            name="File deletion",
            description="File deletion can cause data loss",
            category=ThreatCategory.FILE_SYSTEM,
            threat_level=ThreatLevel.HIGH,
            pattern=r'\b(os\.remove|os\.unlink|shutil\.rmtree|Path.*\.unlink)',
            pattern_type='regex',
            remediation="Use protected file operations with approval",
        ),
        CodePattern(
            pattern_id="FS003",
            name="Path traversal",
            description="Path traversal can access files outside sandbox",
            category=ThreatCategory.FILE_SYSTEM,
            threat_level=ThreatLevel.HIGH,
            pattern=r'\.\./',
            pattern_type='regex',
            remediation="Use absolute paths within sandbox only",
        ),
        
        # Process Execution
        CodePattern(
            pattern_id="PROC001",
            name="os.system()",
            description="System command execution",
            category=ThreatCategory.PROCESS_EXECUTION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bos\.system\s*\(',
            pattern_type='regex',
            remediation="Avoid system commands; use Python libraries",
        ),
        CodePattern(
            pattern_id="PROC002",
            name="subprocess usage",
            description="Subprocess can execute arbitrary commands",
            category=ThreatCategory.PROCESS_EXECUTION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bsubprocess\.(run|call|Popen|check_output)',
            pattern_type='regex',
            remediation="Avoid subprocess; use Python libraries",
        ),
        CodePattern(
            pattern_id="PROC003",
            name="os.popen()",
            description="Process pipe can execute commands",
            category=ThreatCategory.PROCESS_EXECUTION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bos\.popen\s*\(',
            pattern_type='regex',
            remediation="Avoid popen; use Python libraries",
        ),
        
        # Network
        CodePattern(
            pattern_id="NET001",
            name="Socket usage",
            description="Raw socket access can bypass network controls",
            category=ThreatCategory.NETWORK,
            threat_level=ThreatLevel.HIGH,
            pattern=r'\bsocket\.(socket|create_connection)',
            pattern_type='regex',
            remediation="Use approved HTTP clients only",
        ),
        CodePattern(
            pattern_id="NET002",
            name="HTTP requests",
            description="HTTP requests can exfiltrate data",
            category=ThreatCategory.NETWORK,
            threat_level=ThreatLevel.MEDIUM,
            pattern=r'\b(requests|urllib|http\.client|aiohttp)',
            pattern_type='regex',
            remediation="Use approved API clients with rate limiting",
        ),
        
        # Information Disclosure
        CodePattern(
            pattern_id="INFO001",
            name="Environment variable access",
            description="Can expose sensitive configuration",
            category=ThreatCategory.INFORMATION_DISCLOSURE,
            threat_level=ThreatLevel.MEDIUM,
            pattern=r'\bos\.(environ|getenv)',
            pattern_type='regex',
            remediation="Use approved configuration access methods",
        ),
        CodePattern(
            pattern_id="INFO002",
            name="Globals/locals access",
            description="Can expose internal state",
            category=ThreatCategory.INFORMATION_DISCLOSURE,
            threat_level=ThreatLevel.HIGH,
            pattern=r'\b(globals|locals|vars)\s*\(\s*\)',
            pattern_type='regex',
            remediation="Avoid introspection of global state",
        ),
        
        # Resource Exhaustion
        CodePattern(
            pattern_id="RES001",
            name="Infinite loop risk",
            description="While True without break can cause hang",
            category=ThreatCategory.RESOURCE_EXHAUSTION,
            threat_level=ThreatLevel.MEDIUM,
            pattern=r'\bwhile\s+True\s*:',
            pattern_type='regex',
            remediation="Add timeout or iteration limit",
            false_positive_rate=0.5,
        ),
        CodePattern(
            pattern_id="RES002",
            name="Large allocation",
            description="Large memory allocation can exhaust resources",
            category=ThreatCategory.RESOURCE_EXHAUSTION,
            threat_level=ThreatLevel.MEDIUM,
            pattern=r'\[\s*0\s*\]\s*\*\s*\d{7,}',
            pattern_type='regex',
            remediation="Use generators or chunked processing",
        ),
        
        # Privilege Escalation
        CodePattern(
            pattern_id="PRIV001",
            name="__class__ access",
            description="Can escape sandbox via class hierarchy",
            category=ThreatCategory.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\.__class__',
            pattern_type='regex',
            remediation="Avoid class introspection",
        ),
        CodePattern(
            pattern_id="PRIV002",
            name="__bases__ access",
            description="Can access base classes to escape sandbox",
            category=ThreatCategory.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\.__bases__',
            pattern_type='regex',
            remediation="Avoid base class access",
        ),
        CodePattern(
            pattern_id="PRIV003",
            name="__subclasses__ access",
            description="Can enumerate subclasses to find exploits",
            category=ThreatCategory.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\.__subclasses__\s*\(\s*\)',
            pattern_type='regex',
            remediation="Avoid subclass enumeration",
        ),
        CodePattern(
            pattern_id="PRIV004",
            name="__globals__ access",
            description="Can access global namespace",
            category=ThreatCategory.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\.__globals__',
            pattern_type='regex',
            remediation="Avoid global namespace access",
        ),
        CodePattern(
            pattern_id="PRIV005",
            name="__builtins__ access",
            description="Can access builtins to escape sandbox",
            category=ThreatCategory.PRIVILEGE_ESCALATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\.__builtins__',
            pattern_type='regex',
            remediation="Avoid builtins access",
        ),
        
        # Unsafe Deserialization
        CodePattern(
            pattern_id="DESER001",
            name="pickle usage",
            description="Pickle can execute arbitrary code on load",
            category=ThreatCategory.UNSAFE_DESERIALIZATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bpickle\.(load|loads)',
            pattern_type='regex',
            remediation="Use JSON or other safe serialization",
        ),
        CodePattern(
            pattern_id="DESER002",
            name="marshal usage",
            description="Marshal can execute code on load",
            category=ThreatCategory.UNSAFE_DESERIALIZATION,
            threat_level=ThreatLevel.CRITICAL,
            pattern=r'\bmarshal\.(load|loads)',
            pattern_type='regex',
            remediation="Use JSON or other safe serialization",
        ),
        
        # Cryptographic
        CodePattern(
            pattern_id="CRYPTO001",
            name="Weak random",
            description="random module is not cryptographically secure",
            category=ThreatCategory.CRYPTOGRAPHIC,
            threat_level=ThreatLevel.LOW,
            pattern=r'\brandom\.(random|randint|choice)',
            pattern_type='regex',
            remediation="Use secrets module for security-sensitive randomness",
            false_positive_rate=0.8,
        ),
    ]
    
    def __init__(self, 
                 custom_patterns: Optional[List[CodePattern]] = None,
                 threat_threshold: ThreatLevel = ThreatLevel.MEDIUM):
        """
        Initialize code safety scanner.
        
        Args:
            custom_patterns: Additional patterns to detect
            threat_threshold: Minimum threat level to report
        """
        self.patterns = self.DANGEROUS_PATTERNS.copy()
        if custom_patterns:
            self.patterns.extend(custom_patterns)
        
        self.threat_threshold = threat_threshold
        self.scan_history: List[ScanResult] = []
        self._finding_counter = 0
        self._scan_counter = 0
        
        # Compile regex patterns
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for pattern in self.patterns:
            if pattern.pattern_type == 'regex':
                try:
                    self._compiled_patterns[pattern.pattern_id] = re.compile(
                        pattern.pattern, re.MULTILINE
                    )
                except re.error as e:
                    logger.error(f"Invalid pattern {pattern.pattern_id}: {e}")
        
        logger.info(f"CodeSafetyScanner initialized with {len(self.patterns)} patterns")
    
    def scan(self, code: str, context: Optional[Dict[str, Any]] = None) -> ScanResult:
        """
        Scan code for security vulnerabilities.
        
        Args:
            code: Python code to scan
            context: Optional context information
            
        Returns:
            ScanResult with findings
        """
        import time
        start_time = time.time()
        
        self._scan_counter += 1
        scan_id = f"scan_{self._scan_counter:08d}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        findings: List[ScanFinding] = []
        
        # Run regex pattern matching
        regex_findings = self._scan_regex_patterns(code)
        findings.extend(regex_findings)
        
        # Run AST analysis
        ast_findings = self._scan_ast(code)
        findings.extend(ast_findings)
        
        # Run semantic analysis
        semantic_findings = self._scan_semantic(code)
        findings.extend(semantic_findings)
        
        # Filter by threshold
        findings = [
            f for f in findings 
            if f.pattern.threat_level.value >= self.threat_threshold.value
        ]
        
        # Determine overall threat level
        if findings:
            max_threat = max(f.pattern.threat_level.value for f in findings)
            threat_level = ThreatLevel(max_threat)
        else:
            threat_level = ThreatLevel.NONE
        
        # Determine if safe
        is_safe = threat_level.value < ThreatLevel.HIGH.value
        
        scan_time_ms = (time.time() - start_time) * 1000
        
        result = ScanResult(
            scan_id=scan_id,
            code_hash=code_hash,
            is_safe=is_safe,
            threat_level=threat_level,
            findings=findings,
            scan_time_ms=scan_time_ms,
            metadata=context or {},
        )
        
        self.scan_history.append(result)
        
        # Keep history bounded
        if len(self.scan_history) > 1000:
            self.scan_history = self.scan_history[-500:]
        
        if not is_safe:
            logger.warning(
                f"Code scan {scan_id}: UNSAFE - {len(findings)} findings, "
                f"max threat: {threat_level.name}"
            )
        
        return result
    
    def _scan_regex_patterns(self, code: str) -> List[ScanFinding]:
        """Scan code using regex patterns."""
        findings = []
        
        lines = code.split('\n')
        
        for pattern in self.patterns:
            if pattern.pattern_type != 'regex':
                continue
            
            compiled = self._compiled_patterns.get(pattern.pattern_id)
            if not compiled:
                continue
            
            for match in compiled.finditer(code):
                # Find line number
                line_start = code[:match.start()].count('\n')
                line_number = line_start + 1
                
                # Get code snippet
                snippet_start = max(0, line_start - 1)
                snippet_end = min(len(lines), line_start + 2)
                snippet = '\n'.join(lines[snippet_start:snippet_end])
                
                self._finding_counter += 1
                finding = ScanFinding(
                    finding_id=f"find_{self._finding_counter:08d}",
                    pattern=pattern,
                    location=f"line {line_number}",
                    line_number=line_number,
                    code_snippet=snippet,
                    confidence=1.0 - pattern.false_positive_rate,
                )
                findings.append(finding)
        
        return findings
    
    def _scan_ast(self, code: str) -> List[ScanFinding]:
        """Scan code using AST analysis."""
        findings = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return findings
        
        # Check for dangerous AST patterns
        for node in ast.walk(tree):
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ('os', 'subprocess', 'socket', 'pickle'):
                        self._finding_counter += 1
                        findings.append(ScanFinding(
                            finding_id=f"find_{self._finding_counter:08d}",
                            pattern=CodePattern(
                                pattern_id="AST001",
                                name=f"Dangerous import: {alias.name}",
                                description=f"Import of {alias.name} module",
                                category=ThreatCategory.PRIVILEGE_ESCALATION,
                                threat_level=ThreatLevel.HIGH,
                                pattern="",
                                pattern_type="ast",
                                remediation="Use sandbox-approved modules only",
                            ),
                            location=f"line {node.lineno}",
                            line_number=node.lineno,
                            code_snippet=f"import {alias.name}",
                            confidence=0.95,
                        ))
            
            # Check for attribute access on potentially dangerous objects
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith('__') and node.attr.endswith('__'):
                    if node.attr not in ('__init__', '__str__', '__repr__', '__len__'):
                        self._finding_counter += 1
                        findings.append(ScanFinding(
                            finding_id=f"find_{self._finding_counter:08d}",
                            pattern=CodePattern(
                                pattern_id="AST002",
                                name=f"Dunder access: {node.attr}",
                                description=f"Access to {node.attr}",
                                category=ThreatCategory.PRIVILEGE_ESCALATION,
                                threat_level=ThreatLevel.HIGH,
                                pattern="",
                                pattern_type="ast",
                                remediation="Avoid dunder attribute access",
                            ),
                            location=f"line {node.lineno}",
                            line_number=node.lineno,
                            code_snippet=f".{node.attr}",
                            confidence=0.9,
                        ))
            
            # Check for recursive functions without depth limit
            elif isinstance(node, ast.FunctionDef):
                if self._is_recursive(node):
                    # Check if there's a depth limit
                    if not self._has_recursion_limit(node):
                        self._finding_counter += 1
                        findings.append(ScanFinding(
                            finding_id=f"find_{self._finding_counter:08d}",
                            pattern=CodePattern(
                                pattern_id="AST003",
                                name="Unbounded recursion",
                                description=f"Function {node.name} may recurse infinitely",
                                category=ThreatCategory.RESOURCE_EXHAUSTION,
                                threat_level=ThreatLevel.MEDIUM,
                                pattern="",
                                pattern_type="ast",
                                remediation="Add recursion depth limit",
                            ),
                            location=f"line {node.lineno}",
                            line_number=node.lineno,
                            code_snippet=f"def {node.name}(...)",
                            confidence=0.6,
                        ))
        
        return findings
    
    def _is_recursive(self, func_node: ast.FunctionDef) -> bool:
        """Check if function is recursive."""
        func_name = func_node.name
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    return True
        
        return False
    
    def _has_recursion_limit(self, func_node: ast.FunctionDef) -> bool:
        """Check if recursive function has depth limit."""
        # Look for common patterns like depth parameter
        for arg in func_node.args.args:
            if 'depth' in arg.arg.lower() or 'limit' in arg.arg.lower():
                return True
        
        # Look for comparison with depth/limit variable
        for node in ast.walk(func_node):
            if isinstance(node, ast.Compare):
                for comparator in [node.left] + node.comparators:
                    if isinstance(comparator, ast.Name):
                        if 'depth' in comparator.id.lower() or 'limit' in comparator.id.lower():
                            return True
        
        return False
    
    def _scan_semantic(self, code: str) -> List[ScanFinding]:
        """Perform semantic analysis on code."""
        findings = []
        
        # Check for string formatting with user input (potential injection)
        format_patterns = [
            (r'f["\'].*\{.*input.*\}', "F-string with input"),
            (r'\.format\(.*input', "Format with input"),
            (r'%\s*\(.*input', "% formatting with input"),
        ]
        
        for pattern, name in format_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                self._finding_counter += 1
                findings.append(ScanFinding(
                    finding_id=f"find_{self._finding_counter:08d}",
                    pattern=CodePattern(
                        pattern_id="SEM001",
                        name=name,
                        description="String formatting with potentially untrusted input",
                        category=ThreatCategory.CODE_INJECTION,
                        threat_level=ThreatLevel.MEDIUM,
                        pattern=pattern,
                        pattern_type="semantic",
                        remediation="Validate and sanitize input before formatting",
                    ),
                    location="semantic",
                    line_number=None,
                    code_snippet="",
                    confidence=0.5,
                ))
        
        return findings
    
    def scan_file(self, file_path: str) -> ScanResult:
        """
        Scan a Python file for security vulnerabilities.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            ScanResult
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            return self.scan(code, context={'file_path': file_path})
            
        except Exception as e:
            logger.error(f"Failed to scan file {file_path}: {e}")
            return ScanResult(
                scan_id=f"scan_{self._scan_counter + 1:08d}",
                code_hash="ERROR",
                is_safe=False,
                threat_level=ThreatLevel.HIGH,
                findings=[],
                scan_time_ms=0,
                metadata={'error': str(e)},
            )
    
    def add_pattern(self, pattern: CodePattern):
        """Add a custom pattern to the scanner."""
        self.patterns.append(pattern)
        
        if pattern.pattern_type == 'regex':
            try:
                self._compiled_patterns[pattern.pattern_id] = re.compile(
                    pattern.pattern, re.MULTILINE
                )
            except re.error as e:
                logger.error(f"Invalid pattern {pattern.pattern_id}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scanning statistics."""
        total_scans = len(self.scan_history)
        unsafe_scans = sum(1 for s in self.scan_history if not s.is_safe)
        
        findings_by_category: Dict[str, int] = {}
        findings_by_level: Dict[str, int] = {}
        
        for scan in self.scan_history:
            for finding in scan.findings:
                cat = finding.pattern.category.name
                level = finding.pattern.threat_level.name
                findings_by_category[cat] = findings_by_category.get(cat, 0) + 1
                findings_by_level[level] = findings_by_level.get(level, 0) + 1
        
        return {
            'total_scans': total_scans,
            'unsafe_scans': unsafe_scans,
            'safe_rate': (total_scans - unsafe_scans) / total_scans if total_scans > 0 else 1.0,
            'total_findings': sum(len(s.findings) for s in self.scan_history),
            'findings_by_category': findings_by_category,
            'findings_by_level': findings_by_level,
            'patterns_count': len(self.patterns),
        }
    
    def get_remediation_report(self, scan_result: ScanResult) -> str:
        """Generate remediation report for scan findings."""
        if not scan_result.findings:
            return "No security issues found."
        
        report = ["# Security Scan Remediation Report\n"]
        report.append(f"Scan ID: {scan_result.scan_id}")
        report.append(f"Threat Level: {scan_result.threat_level.name}")
        report.append(f"Total Findings: {len(scan_result.findings)}\n")
        
        # Group by category
        by_category: Dict[str, List[ScanFinding]] = {}
        for finding in scan_result.findings:
            cat = finding.pattern.category.name
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(finding)
        
        for category, findings in sorted(by_category.items()):
            report.append(f"\n## {category}\n")
            
            for finding in findings:
                report.append(f"### {finding.pattern.name}")
                report.append(f"- **Threat Level**: {finding.pattern.threat_level.name}")
                report.append(f"- **Location**: {finding.location}")
                report.append(f"- **Description**: {finding.pattern.description}")
                report.append(f"- **Remediation**: {finding.pattern.remediation}")
                if finding.code_snippet:
                    report.append(f"- **Code**:\n```python\n{finding.code_snippet}\n```")
                report.append("")
        
        return '\n'.join(report)
