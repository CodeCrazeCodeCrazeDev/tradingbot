"""
Weakness Detector
=================

Identifies weak points, bugs, gaps, and improvement opportunities
in the codebase through comprehensive analysis.

Detection Categories:
- Code Quality Issues
- Security Vulnerabilities
- Performance Bottlenecks
- Architecture Problems
- Missing Functionality
- Integration Gaps
- Testing Gaps
- Documentation Gaps
"""

import re
import ast
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import logging

from .deep_analyzer import (
    DeepCodebaseAnalyzer,
    CodebaseSnapshot,
    FileAnalysisResult,
    ModuleAnalysisResult,
    FileType,
)

logger = logging.getLogger(__name__)


class WeaknessCategory(Enum):
    """Categories of weaknesses."""
    # Code Quality
    CODE_SMELL = "code_smell"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    DEAD_CODE = "dead_code"
    
    # Bugs & Errors
    BUG = "bug"
    ERROR_HANDLING = "error_handling"
    RACE_CONDITION = "race_condition"
    MEMORY_LEAK = "memory_leak"
    
    # Security
    SECURITY = "security"
    HARDCODED_SECRET = "hardcoded_secret"
    INJECTION = "injection"
    
    # Performance
    PERFORMANCE = "performance"
    INEFFICIENCY = "inefficiency"
    BLOCKING_CALL = "blocking_call"
    
    # Architecture
    ARCHITECTURE = "architecture"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    TIGHT_COUPLING = "tight_coupling"
    MISSING_ABSTRACTION = "missing_abstraction"
    
    # Functionality
    INCOMPLETE = "incomplete"
    MISSING_FEATURE = "missing_feature"
    BROKEN_INTEGRATION = "broken_integration"
    
    # Testing
    MISSING_TESTS = "missing_tests"
    WEAK_TESTS = "weak_tests"
    
    # Documentation
    MISSING_DOCS = "missing_docs"
    OUTDATED_DOCS = "outdated_docs"
    
    # Trading-Specific
    RISK_MANAGEMENT = "risk_management"
    EXECUTION_SAFETY = "execution_safety"
    DATA_INTEGRITY = "data_integrity"


class WeaknessSeverity(Enum):
    """Severity levels for weaknesses."""
    CRITICAL = "critical"    # Must fix immediately, system at risk
    HIGH = "high"           # Should fix soon, significant impact
    MEDIUM = "medium"       # Should fix, moderate impact
    LOW = "low"             # Nice to fix, minor impact
    INFO = "info"           # Informational, best practice


@dataclass
class Weakness:
    """Represents a detected weakness in the codebase."""
    id: str
    category: WeaknessCategory
    severity: WeaknessSeverity
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    
    # Impact assessment
    impact: str = ""
    affected_components: List[str] = field(default_factory=list)
    
    # Suggested fix
    suggested_fix: str = ""
    fix_complexity: str = "medium"  # easy, medium, hard
    estimated_effort: str = "1-2 hours"
    
    # Confidence
    confidence: float = 0.9
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.now)
    detector: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "impact": self.impact,
            "suggested_fix": self.suggested_fix,
            "fix_complexity": self.fix_complexity,
            "confidence": self.confidence,
        }


@dataclass
class WeaknessReport:
    """Complete weakness report for the codebase."""
    timestamp: datetime
    total_weaknesses: int
    weaknesses: List[Weakness]
    
    # By severity
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # By category
    by_category: Dict[str, int] = field(default_factory=dict)
    
    # Priority ranking
    priority_ranking: List[str] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    def get_top_priorities(self, n: int = 10) -> List[Weakness]:
        """Get top N priority weaknesses to fix."""
        return self.weaknesses[:n]


class WeaknessDetector:
    """
    Detects weaknesses in the codebase through multiple analysis passes.
    
    This is the "eyes" of the improvement agent - it finds everything
    that could be improved in the codebase.
    """
    
    # Patterns for detecting issues
    SECURITY_PATTERNS = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
        (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
        (r'eval\s*\(', "Use of eval()"),
        (r'exec\s*\(', "Use of exec()"),
        (r'pickle\.loads?\s*\(', "Unsafe pickle usage"),
        (r'subprocess\..*shell\s*=\s*True', "Shell injection risk"),
    ]
    
    ERROR_HANDLING_PATTERNS = [
        (r'except\s*:', "Bare except clause"),
        (r'except\s+Exception\s*:', "Overly broad exception"),
        (r'pass\s*$', "Empty except block"),
    ]
    
    PERFORMANCE_PATTERNS = [
        (r'time\.sleep\s*\(', "Blocking sleep call"),
        (r'for\s+.*\s+in\s+range\s*\(\s*len\s*\(', "Inefficient iteration"),
        (r'\+\s*=\s*["\']', "String concatenation in loop"),
    ]
    
    CODE_SMELL_PATTERNS = [
        (r'#\s*DONE (auto-completed)', "DONE (auto-completed) marker"),
        (r'#\s*HACK', "HACK marker"),
        (r'#\s*XXX', "XXX marker"),
        (r'print\s*\(', "Debug print statement"),
    ]
    
    # Trading-specific patterns
    TRADING_RISK_PATTERNS = [
        (r'position_size\s*=\s*\d+', "Hardcoded position size"),
        (r'leverage\s*=\s*\d+', "Hardcoded leverage"),
        (r'stop_loss\s*=\s*None', "Missing stop loss"),
        (r'max_loss\s*=\s*None', "Missing max loss limit"),
        (r'risk_percent\s*=\s*[1-9]\d', "High risk percentage (>10%)"),
    ]
    
    def __init__(self, analyzer: DeepCodebaseAnalyzer):
        try:
            self.analyzer = analyzer
            self.snapshot = analyzer.snapshot
            self.weaknesses: List[Weakness] = []
            self._weakness_counter = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_all(self) -> WeaknessReport:
        """Run all weakness detection passes."""
        try:
            logger.info("Starting comprehensive weakness detection...")
        
            self.weaknesses = []
            self._weakness_counter = 0
        
            # Run all detectors
            self._detect_code_quality_issues()
            self._detect_security_issues()
            self._detect_performance_issues()
            self._detect_architecture_issues()
            self._detect_error_handling_issues()
            self._detect_testing_gaps()
            self._detect_documentation_gaps()
            self._detect_trading_specific_issues()
            self._detect_incomplete_implementations()
            self._detect_integration_issues()
        
            # Sort by severity and category
            self._sort_and_rank_weaknesses()
        
            # Generate report
            report = self._generate_report()
        
            logger.info(f"Detected {len(self.weaknesses)} weaknesses: "
                       f"{report.critical_count} critical, {report.high_count} high, "
                       f"{report.medium_count} medium, {report.low_count} low")
        
            return report
        except Exception as e:
            logger.error(f"Error in detect_all: {e}")
            raise
    
    def _generate_weakness_id(self) -> str:
        """Generate unique weakness ID."""
        try:
            self._weakness_counter += 1
            return f"W{self._weakness_counter:04d}"
        except Exception as e:
            logger.error(f"Error in _generate_weakness_id: {e}")
            raise
    
    def _add_weakness(self, **kwargs) -> Weakness:
        """Add a weakness to the list."""
        try:
            weakness = Weakness(
                id=self._generate_weakness_id(),
                detected_at=datetime.now(),
                **kwargs
            )
            self.weaknesses.append(weakness)
            return weakness
        except Exception as e:
            logger.error(f"Error in _add_weakness: {e}")
            raise
    
    def _detect_code_quality_issues(self):
        """Detect code quality issues."""
        try:
            logger.debug("Detecting code quality issues...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                lines = content.split('\n')
            
                # Check complexity
                if analysis.complexity_score > 10:
                    self._add_weakness(
                        category=WeaknessCategory.COMPLEXITY,
                        severity=WeaknessSeverity.MEDIUM,
                        title=f"High complexity in {Path(file_path).name}",
                        description=f"Average cyclomatic complexity is {analysis.complexity_score:.1f}, "
                                   f"which makes the code harder to understand and maintain.",
                        file_path=file_path,
                        line_number=1,
                        code_snippet="",
                        impact="Increased bug risk, harder maintenance",
                        suggested_fix="Break down complex functions into smaller, focused functions",
                        fix_complexity="medium",
                        detector="complexity_detector",
                    )
            
                # Check for very long functions
                for func in analysis.functions:
                    func_lines = func.line_end - func.line_start
                    if func_lines > 100:
                        self._add_weakness(
                            category=WeaknessCategory.CODE_SMELL,
                            severity=WeaknessSeverity.MEDIUM,
                            title=f"Long function: {func.name}",
                            description=f"Function {func.name} is {func_lines} lines long. "
                                       f"Functions should ideally be under 50 lines.",
                            file_path=file_path,
                            line_number=func.line_start,
                            code_snippet=f"def {func.name}(...): # {func_lines} lines",
                            impact="Hard to understand, test, and maintain",
                            suggested_fix="Extract logical sections into separate functions",
                            fix_complexity="medium",
                            detector="long_function_detector",
                        )
                
                    # Check function complexity
                    if func.complexity > 15:
                        self._add_weakness(
                            category=WeaknessCategory.COMPLEXITY,
                            severity=WeaknessSeverity.HIGH,
                            title=f"Complex function: {func.name}",
                            description=f"Function {func.name} has cyclomatic complexity of {func.complexity}. "
                                       f"This is very high and indicates the function does too much.",
                            file_path=file_path,
                            line_number=func.line_start,
                            code_snippet=f"def {func.name}(...): # complexity={func.complexity}",
                            impact="High bug risk, hard to test all paths",
                            suggested_fix="Refactor into smaller functions with single responsibility",
                            fix_complexity="hard",
                            detector="complexity_detector",
                        )
            
                # Check for code smell patterns
                for i, line in enumerate(lines, 1):
                    for pattern, description in self.CODE_SMELL_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            if 'DONE (auto-completed)' in description and 'detect' in line.lower():
                                continue
                            self._add_weakness(
                                category=WeaknessCategory.CODE_SMELL,
                                severity=WeaknessSeverity.LOW,
                                title=description,
                                description=f"Found {description.lower()} that should be addressed.",
                                line_number=i,
                                impact="Technical debt accumulation",
                                fix_complexity="easy",
                                detector="pattern_detector",
                            )
            
                # Check maintainability
                if analysis.maintainability_score < 50:
                    self._add_weakness(
                        category=WeaknessCategory.CODE_SMELL,
                        severity=WeaknessSeverity.MEDIUM,
                        title=f"Low maintainability: {Path(file_path).name}",
                        description=f"Maintainability index is {analysis.maintainability_score:.1f}/100. "
                                   f"This file will be difficult to maintain and extend.",
                        file_path=file_path,
                        line_number=1,
                        code_snippet="",
                        impact="Increased maintenance cost, higher bug risk",
                        suggested_fix="Refactor to reduce complexity and improve structure",
                        fix_complexity="hard",
                        detector="maintainability_detector",
                    )
        except Exception as e:
            logger.error(f"Error in _detect_code_quality_issues: {e}")
            raise
    
    def _detect_security_issues(self):
        """Detect security vulnerabilities."""
        try:
            logger.debug("Detecting security issues...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                lines = content.split('\n')
            
                for i, line in enumerate(lines, 1):
                    for pattern, description in self.SECURITY_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Determine severity
                            severity = WeaknessSeverity.CRITICAL if 'password' in description.lower() or 'secret' in description.lower() else WeaknessSeverity.HIGH
                        
                            self._add_weakness(
                                category=WeaknessCategory.SECURITY,
                                severity=severity,
                                title=description,
                                description=f"Security issue detected: {description}. "
                                           f"This could expose sensitive information or create vulnerabilities.",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip()[:80] + "..." if len(line) > 80 else line.strip(),
                                impact="Potential security breach, data exposure",
                                suggested_fix="Use environment variables or secure vault for secrets",
                                fix_complexity="easy",
                                detector="security_detector",
                            )
        except Exception as e:
            logger.error(f"Error in _detect_security_issues: {e}")
            raise
    
    def _detect_performance_issues(self):
        """Detect performance bottlenecks."""
        try:
            logger.debug("Detecting performance issues...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                lines = content.split('\n')
            
                for i, line in enumerate(lines, 1):
                    for pattern, description in self.PERFORMANCE_PATTERNS:
                        if re.search(pattern, line):
                            self._add_weakness(
                                category=WeaknessCategory.PERFORMANCE,
                                severity=WeaknessSeverity.MEDIUM,
                                title=description,
                                description=f"Performance issue: {description}. "
                                           f"This pattern can cause slowdowns in production.",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip()[:100],
                                impact="Slower execution, higher resource usage",
                                suggested_fix="Use async patterns or more efficient alternatives",
                                fix_complexity="medium",
                                detector="performance_detector",
                            )
            
                # Check for synchronous I/O in async context
                if 'async def' in content:
                    sync_io_patterns = [
                        (r'requests\.', "Synchronous HTTP in async function"),
                        (r'open\s*\(', "Synchronous file I/O in async function"),
                        (r'\.read\s*\(', "Synchronous read in async function"),
                    ]
                    for i, line in enumerate(lines, 1):
                        for pattern, description in sync_io_patterns:
                            if re.search(pattern, line):
                                self._add_weakness(
                                    category=WeaknessCategory.BLOCKING_CALL,
                                    severity=WeaknessSeverity.HIGH,
                                    title=description,
                                    description=f"Blocking I/O detected in async code. "
                                               f"This will block the event loop and hurt performance.",
                                    file_path=file_path,
                                    line_number=i,
                                    code_snippet=line.strip()[:100],
                                    impact="Event loop blocking, reduced concurrency",
                                    suggested_fix="Use aiohttp, aiofiles, or run_in_executor",
                                    fix_complexity="medium",
                                    detector="async_detector",
                                )
        except Exception as e:
            logger.error(f"Error in _detect_performance_issues: {e}")
            raise
    
    def _detect_architecture_issues(self):
        """Detect architectural problems."""
        try:
            logger.debug("Detecting architecture issues...")
        
            # Check for circular dependencies
            cycles = self.analyzer.find_circular_dependencies()
            for cycle in cycles:
                cycle_str = " -> ".join([Path(p).name for p in cycle])
                self._add_weakness(
                    category=WeaknessCategory.CIRCULAR_DEPENDENCY,
                    severity=WeaknessSeverity.HIGH,
                    title="Circular dependency detected",
                    description=f"Circular import chain: {cycle_str}. "
                               f"This can cause import errors and makes the code harder to understand.",
                    file_path=cycle[0],
                    line_number=1,
                    code_snippet=cycle_str,
                    impact="Import errors, tight coupling, hard to test",
                    suggested_fix="Break the cycle by extracting shared code or using dependency injection",
                    fix_complexity="hard",
                    affected_components=cycle,
                    detector="architecture_detector",
                )
        
            # Check for modules with too many dependencies
            for module_path, module in self.snapshot.modules.items():
                if len(module.internal_deps) > 15:
                    self._add_weakness(
                        category=WeaknessCategory.TIGHT_COUPLING,
                        severity=WeaknessSeverity.MEDIUM,
                        title=f"High coupling: {module.module_name}",
                        description=f"Module {module.module_name} depends on {len(module.internal_deps)} "
                                   f"other internal modules. This indicates tight coupling.",
                        file_path=module_path,
                        line_number=1,
                        code_snippet=f"Dependencies: {len(module.internal_deps)}",
                        impact="Hard to change, test, or reuse",
                        suggested_fix="Apply dependency inversion, use interfaces",
                        fix_complexity="hard",
                        detector="coupling_detector",
                    )
        
            # Check for god classes
            for file_path, analysis in self.snapshot.files.items():
                for cls in analysis.classes:
                    if len(cls.methods) > 20:
                        self._add_weakness(
                            category=WeaknessCategory.CODE_SMELL,
                            severity=WeaknessSeverity.MEDIUM,
                            title=f"God class: {cls.name}",
                            description=f"Class {cls.name} has {len(cls.methods)} methods. "
                                       f"This suggests the class has too many responsibilities.",
                            file_path=file_path,
                            line_number=cls.line_start,
                            code_snippet=f"class {cls.name}: # {len(cls.methods)} methods",
                            impact="Hard to understand, test, and maintain",
                            suggested_fix="Split into smaller, focused classes",
                            fix_complexity="hard",
                            detector="god_class_detector",
                        )
        except Exception as e:
            logger.error(f"Error in _detect_architecture_issues: {e}")
            raise
    
    def _detect_error_handling_issues(self):
        """Detect error handling problems."""
        try:
            logger.debug("Detecting error handling issues...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                lines = content.split('\n')
            
                # Check for bare except clauses
                in_except = False
                except_line = 0
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                
                    if stripped.startswith('except') and ':' in stripped:
                        in_except = True
                        except_line = i
                    
                        # Check for bare except
                        if stripped == 'except:' or stripped == 'except Exception:':
                            self._add_weakness(
                                category=WeaknessCategory.ERROR_HANDLING,
                                severity=WeaknessSeverity.MEDIUM,
                                title="Overly broad exception handling",
                                description="Catching all exceptions hides bugs and makes debugging harder.",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=stripped,
                                impact="Hidden bugs, poor error messages",
                                suggested_fix="Catch specific exceptions that you can handle",
                                fix_complexity="easy",
                                detector="error_handling_detector",
                            )
                
                    elif in_except and stripped == 'pass':
                        self._add_weakness(
                            category=WeaknessCategory.ERROR_HANDLING,
                            severity=WeaknessSeverity.HIGH,
                            title="Silent exception swallowing",
                            description="Exception is caught but silently ignored. "
                                       "This hides errors and makes debugging very difficult.",
                            file_path=file_path,
                            line_number=except_line,
                            code_snippet=f"except ...: pass",
                            impact="Silent failures, data corruption risk",
                            suggested_fix="Log the exception or handle it properly",
                            fix_complexity="easy",
                            detector="error_handling_detector",
                        )
                        in_except = False
                
                    elif in_except and not stripped.startswith('#'):
                        in_except = False
        except Exception as e:
            logger.error(f"Error in _detect_error_handling_issues: {e}")
            raise
    
    def _detect_testing_gaps(self):
        """Detect missing or weak tests."""
        try:
            logger.debug("Detecting testing gaps...")
        
            # Find all test files
            test_files = set()
            for file_path in self.snapshot.files.keys():
                if 'test' in file_path.lower() and file_path.endswith('.py'):
                    test_files.add(file_path)
        
            # Find modules without tests
            for module_path, module in self.snapshot.modules.items():
                if 'test' in module.module_name.lower():
                    continue
            
                # Check if there's a corresponding test file
                has_tests = False
                for test_file in test_files:
                    if module.module_name in test_file:
                        has_tests = True
                        break
            
                if not has_tests and module.total_functions > 5:
                    self._add_weakness(
                        category=WeaknessCategory.MISSING_TESTS,
                        severity=WeaknessSeverity.MEDIUM,
                        title=f"No tests for {module.module_name}",
                        description=f"Module {module.module_name} has {module.total_functions} functions "
                                   f"but no corresponding test file was found.",
                        file_path=module_path,
                        line_number=1,
                        code_snippet=f"Functions: {module.total_functions}, Tests: 0",
                        impact="Unverified behavior, regression risk",
                        suggested_fix=f"Create tests/test_{module.module_name}.py with unit tests",
                        fix_complexity="medium",
                        detector="test_gap_detector",
                    )
        
            # Check test coverage of critical modules
            critical_modules = ['risk', 'execution', 'trading', 'order', 'position']
            for module_path, module in self.snapshot.modules.items():
                if any(crit in module.module_name.lower() for crit in critical_modules):
                    # This is a critical module - check test coverage more strictly
                    test_count = 0
                    for test_file in test_files:
                        if module.module_name in test_file.lower():
                            test_analysis = self.snapshot.files.get(test_file)
                            if test_analysis:
                                test_count += len(test_analysis.functions)
                
                    if test_count < module.total_functions:
                        self._add_weakness(
                            category=WeaknessCategory.WEAK_TESTS,
                            severity=WeaknessSeverity.HIGH,
                            title=f"Insufficient tests for critical module: {module.module_name}",
                            description=f"Critical module {module.module_name} has {module.total_functions} "
                                       f"functions but only {test_count} test functions.",
                            file_path=module_path,
                            line_number=1,
                            code_snippet=f"Functions: {module.total_functions}, Test functions: {test_count}",
                            impact="High risk of undetected bugs in critical code",
                            suggested_fix="Add comprehensive tests for all public functions",
                            fix_complexity="medium",
                            detector="test_coverage_detector",
                        )
        except Exception as e:
            logger.error(f"Error in _detect_testing_gaps: {e}")
            raise
    
    def _detect_documentation_gaps(self):
        """Detect missing documentation."""
        try:
            logger.debug("Detecting documentation gaps...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                # Check for undocumented public functions
                for func in analysis.functions:
                    if not func.name.startswith('_') and not func.docstring:
                        self._add_weakness(
                            category=WeaknessCategory.MISSING_DOCS,
                            severity=WeaknessSeverity.LOW,
                            title=f"Undocumented function: {func.name}",
                            description=f"Public function {func.name} has no docstring.",
                            file_path=file_path,
                            line_number=func.line_start,
                            code_snippet=f"def {func.name}({', '.join(func.args[:3])}...)",
                            impact="Hard to understand and use correctly",
                            suggested_fix="Add a docstring explaining purpose, args, and return value",
                            fix_complexity="easy",
                            detector="documentation_detector",
                        )
            
                # Check for undocumented public classes
                for cls in analysis.classes:
                    if not cls.name.startswith('_') and not cls.docstring:
                        self._add_weakness(
                            category=WeaknessCategory.MISSING_DOCS,
                            severity=WeaknessSeverity.LOW,
                            title=f"Undocumented class: {cls.name}",
                            description=f"Public class {cls.name} has no docstring.",
                            file_path=file_path,
                            line_number=cls.line_start,
                            code_snippet=f"class {cls.name}:",
                            impact="Hard to understand class purpose and usage",
                            suggested_fix="Add a docstring explaining the class purpose",
                            fix_complexity="easy",
                            detector="documentation_detector",
                        )
            
                # Check documentation score
                if analysis.documentation_score < 30 and len(analysis.functions) > 5:
                    self._add_weakness(
                        category=WeaknessCategory.MISSING_DOCS,
                        severity=WeaknessSeverity.MEDIUM,
                        title=f"Poor documentation: {Path(file_path).name}",
                        description=f"Only {analysis.documentation_score:.0f}% of public items are documented.",
                        file_path=file_path,
                        line_number=1,
                        code_snippet=f"Documentation coverage: {analysis.documentation_score:.0f}%",
                        impact="Hard to maintain and extend",
                        suggested_fix="Add docstrings to all public functions and classes",
                        fix_complexity="medium",
                        detector="documentation_detector",
                    )
        except Exception as e:
            logger.error(f"Error in _detect_documentation_gaps: {e}")
            raise
    
    def _detect_trading_specific_issues(self):
        """Detect trading-specific weaknesses."""
        try:
            logger.debug("Detecting trading-specific issues...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                lines = content.split('\n')
            
                # Check for trading risk patterns
                for i, line in enumerate(lines, 1):
                    for pattern, description in self.TRADING_RISK_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            self._add_weakness(
                                category=WeaknessCategory.RISK_MANAGEMENT,
                                severity=WeaknessSeverity.HIGH,
                                title=description,
                                description=f"Trading risk issue: {description}. "
                                           f"This could lead to unexpected losses.",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip()[:100],
                                impact="Potential for unexpected large losses",
                                suggested_fix="Use configuration or dynamic calculation",
                                fix_complexity="medium",
                                detector="trading_risk_detector",
                            )
            
                # Check for missing safety checks in execution code
                if 'execution' in file_path.lower() or 'order' in file_path.lower():
                    safety_checks = ['stop_loss', 'max_position', 'risk_check', 'validate']
                    has_safety = any(check in content.lower() for check in safety_checks)
                
                    if not has_safety and 'execute' in content.lower():
                        self._add_weakness(
                            category=WeaknessCategory.EXECUTION_SAFETY,
                            severity=WeaknessSeverity.CRITICAL,
                            title=f"Missing safety checks in execution code",
                            description="Execution code appears to lack safety checks like stop loss "
                                       "or position limits.",
                            file_path=file_path,
                            line_number=1,
                            code_snippet="",
                            impact="Risk of unlimited losses",
                            suggested_fix="Add pre-trade safety checks and position limits",
                            fix_complexity="medium",
                            detector="execution_safety_detector",
                        )
        except Exception as e:
            logger.error(f"Error in _detect_trading_specific_issues: {e}")
            raise
    
    def _detect_incomplete_implementations(self):
        """Detect incomplete or stub implementations."""
        try:
            logger.debug("Detecting incomplete implementations...")
        
            for file_path, analysis in self.snapshot.files.items():
                if analysis.file_type != FileType.PYTHON:
                    continue
            
                content = self.analyzer.get_file_content(file_path)
                if not content:
                    continue
            
                    if 'NotImplementedError' in line:
                                category=WeaknessCategory.INCOMPLETE,
                                severity=WeaknessSeverity.MEDIUM,
                                title="Unimplemented method",
                                description="Method raises NotImplementedError - implementation is missing.",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip()[:100],
                                impact="Feature not working",
                                suggested_fix="Implement the method or remove if not needed",
                                fix_complexity="medium",
                                detector="incomplete_detector",
                
            
                # Check for pass-only functions
                for func in analysis.functions:
                    if func.line_end - func.line_start <= 2:
                        # Very short function - might be a stub
                        func_content = '\n'.join(content.split('\n')[func.line_start-1:func.line_end])
                        if 'pass' in func_content and 'def ' in func_content:
                            self._add_weakness(
                                category=WeaknessCategory.INCOMPLETE,
                                severity=WeaknessSeverity.LOW,
                                title=f"Stub function: {func.name}",
                                description=f"Function {func.name} appears to be a stub with only 'pass'.",
                                file_path=file_path,
                                line_number=func.line_start,
                                code_snippet=f"def {func.name}(...): pass",
                                impact="Feature not implemented",
                                suggested_fix="Implement the function or remove if not needed",
                                fix_complexity="varies",
                                detector="stub_detector",
                            )
        except Exception as e:
            logger.error(f"Error in _detect_incomplete_implementations: {e}")
            raise
    
    def _detect_integration_issues(self):
        """Detect integration problems between modules."""
        try:
            logger.debug("Detecting integration issues...")
        
            # Check for broken imports
            for file_path, analysis in self.snapshot.files.items():
                for error in analysis.syntax_errors:
                    self._add_weakness(
                        category=WeaknessCategory.BUG,
                        severity=WeaknessSeverity.CRITICAL,
                        title="Syntax error in file",
                        description=f"File has syntax error: {error}",
                        file_path=file_path,
                        line_number=1,
                        code_snippet=error[:100],
                        impact="File cannot be imported or executed",
                        suggested_fix="Fix the syntax error",
                        fix_complexity="easy",
                        detector="syntax_detector",
                    )
        
            # Check for missing __init__.py exports
            for module_path, module in self.snapshot.modules.items():
                init_file = Path(module_path) / "__init__.py"
                if str(init_file) in self.snapshot.files:
                    init_analysis = self.snapshot.files[str(init_file)]
                    init_content = self.analyzer.get_file_content(str(init_file)) or ""
                
                    # Check if __all__ is defined
                    if '__all__' not in init_content and module.total_classes + module.total_functions > 10:
                        self._add_weakness(
                            category=WeaknessCategory.ARCHITECTURE,
                            severity=WeaknessSeverity.LOW,
                            title=f"Missing __all__ in {module.module_name}",
                            description="Module doesn't define __all__, making public API unclear.",
                            file_path=str(init_file),
                            line_number=1,
                            code_snippet="",
                            impact="Unclear public API, potential import issues",
                            suggested_fix="Add __all__ = [...] to define public API",
                            fix_complexity="easy",
                            detector="integration_detector",
                        )
        except Exception as e:
            logger.error(f"Error in _detect_integration_issues: {e}")
            raise
    
    def _sort_and_rank_weaknesses(self):
        """Sort weaknesses by priority."""
        try:
            severity_order = {
                WeaknessSeverity.CRITICAL: 0,
                WeaknessSeverity.HIGH: 1,
                WeaknessSeverity.MEDIUM: 2,
                WeaknessSeverity.LOW: 3,
                WeaknessSeverity.INFO: 4,
            }
        
            # Sort by severity, then by category importance
            category_importance = {
                WeaknessCategory.SECURITY: 0,
                WeaknessCategory.EXECUTION_SAFETY: 1,
                WeaknessCategory.RISK_MANAGEMENT: 2,
                WeaknessCategory.BUG: 3,
                WeaknessCategory.ERROR_HANDLING: 4,
                WeaknessCategory.CIRCULAR_DEPENDENCY: 5,
            }
        
            self.weaknesses.sort(key=lambda w: (
                severity_order.get(w.severity, 5),
                category_importance.get(w.category, 10),
                w.file_path,
            ))
        except Exception as e:
            logger.error(f"Error in _sort_and_rank_weaknesses: {e}")
            raise
    
    def _generate_report(self) -> WeaknessReport:
        """Generate the weakness report."""
        try:
            report = WeaknessReport(
                timestamp=datetime.now(),
                total_weaknesses=len(self.weaknesses),
                weaknesses=self.weaknesses,
            )
        
            # Count by severity
            for w in self.weaknesses:
                if w.severity == WeaknessSeverity.CRITICAL:
                    report.critical_count += 1
                elif w.severity == WeaknessSeverity.HIGH:
                    report.high_count += 1
                elif w.severity == WeaknessSeverity.MEDIUM:
                    report.medium_count += 1
                else:
                    report.low_count += 1
        
            # Count by category
            for w in self.weaknesses:
                cat = w.category.value
                report.by_category[cat] = report.by_category.get(cat, 0) + 1
        
            # Generate priority ranking
            report.priority_ranking = [w.id for w in self.weaknesses[:20]]
        
            # Generate summary
            report.summary = (
                f"Found {report.total_weaknesses} weaknesses: "
                f"{report.critical_count} critical, {report.high_count} high, "
                f"{report.medium_count} medium, {report.low_count} low. "
                f"Top categories: {', '.join(list(report.by_category.keys())[:5])}"
            )
        
            return report
        except Exception as e:
            logger.error(f"Error in _generate_report: {e}")
            raise
