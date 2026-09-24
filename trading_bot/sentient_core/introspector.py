"""
Introspector - Self-Analysis and Flaw Detection System

Analyzes the bot's own code, performance, and behavior to:
- Detect bugs and flaws
- Identify performance bottlenecks
- Find improvement opportunities
- Track code quality metrics
- Suggest optimizations
"""

import ast
import asyncio
import inspect
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict
import logging
import importlib
import threading

logger = logging.getLogger(__name__)


class FlawType(Enum):
    """Types of flaws that can be detected"""
    BUG = auto()
    PERFORMANCE = auto()
    SECURITY = auto()
    CODE_SMELL = auto()
    MISSING_FEATURE = auto()
    DEPRECATED = auto()
    INCOMPLETE = auto()
    INEFFICIENT = auto()
    ERROR_PRONE = auto()
    MAINTAINABILITY = auto()


class FlawSeverity(Enum):
    """Severity of detected flaws"""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DetectedFlaw:
    """A detected flaw in the system"""
    id: str
    flaw_type: FlawType
    severity: FlawSeverity
    location: str  # file:line or module.function
    description: str
    suggestion: str
    code_snippet: Optional[str]
    detected_at: datetime
    fixed: bool = False
    fix_applied: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.flaw_type.name,
            'severity': self.severity.name,
            'location': self.location,
            'description': self.description,
            'suggestion': self.suggestion,
            'code_snippet': self.code_snippet,
            'detected_at': self.detected_at.isoformat(),
            'fixed': self.fixed,
            'fix_applied': self.fix_applied,
        }


@dataclass
class PerformanceMetric:
    """Performance metric for a component"""
    name: str
    execution_time_ms: float
    memory_usage_mb: float
    call_count: int
    error_count: int
    last_measured: datetime


@dataclass
class CodeQualityReport:
    """Code quality analysis report"""
    total_files: int
    total_lines: int
    total_functions: int
    total_classes: int
    complexity_score: float
    maintainability_score: float
    test_coverage: float
    documentation_coverage: float
    flaws_by_type: Dict[str, int]
    flaws_by_severity: Dict[str, int]
    top_issues: List[DetectedFlaw]
    generated_at: datetime


class Introspector:
    """
    Self-analysis system that examines the bot's own code and behavior.
    
    Features:
    - Static code analysis
    - Runtime performance monitoring
    - Error pattern detection
    - Code quality metrics
    - Improvement suggestions
    - Automatic flaw detection
    """
    
    # Code patterns that indicate potential issues
    CODE_SMELL_PATTERNS = {
        'bare_except': (r'except\s*:', 'Bare except clause catches all exceptions'),
        'magic_number': (r'(?<!["\'])\b(?<!\.)\d{3,}\b(?!["\'])', 'Magic number in code'),
        'long_function': None,  # Checked programmatically
        'deep_nesting': None,  # Checked programmatically
        'duplicate_code': None,  # Checked programmatically
        'unused_import': None,  # Checked programmatically
        'hardcoded_secret': (r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'function_time_ms': 100,  # Max function execution time
        'memory_mb': 500,  # Max memory usage
        'error_rate': 0.05,  # Max error rate (5%)
    }
    
    def __init__(
        self,
        project_root: str = "trading_bot",
        analysis_interval: int = 3600,  # 1 hour
        report_path: str = "reports/introspection/",
    ):
        self.project_root = Path(project_root)
        self.analysis_interval = analysis_interval
        self.report_path = Path(report_path)
        self.report_path.mkdir(parents=True, exist_ok=True)
        
        # State
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        
        # Detected flaws
        self.flaws: Dict[str, DetectedFlaw] = {}
        self.flaw_history: List[DetectedFlaw] = []
        
        # Performance tracking
        self.performance_metrics: Dict[str, PerformanceMetric] = {}
        self.function_timings: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Code analysis cache
        self._file_hashes: Dict[str, str] = {}
        self._ast_cache: Dict[str, ast.AST] = {}
        
        # Statistics
        self.stats = {
            'files_analyzed': 0,
            'flaws_detected': 0,
            'flaws_fixed': 0,
            'analyses_run': 0,
            'last_analysis': None,
        }
        
        logger.info("Introspector initialized")
    
    async def start(self) -> None:
        """Start the introspection loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._analysis_loop())
        logger.info("Introspector started")
    
    async def stop(self) -> None:
        """Stop the introspection"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Introspector stopped")
    
    async def _analysis_loop(self) -> None:
        """Main analysis loop"""
        while self.is_running:
            try:
                await self.run_full_analysis()
                self.stats['last_analysis'] = datetime.now().isoformat()
                self.stats['analyses_run'] += 1
            except Exception as e:
                logger.error(f"Analysis error: {e}")
            
            await asyncio.sleep(self.analysis_interval)
    
    async def run_full_analysis(self) -> CodeQualityReport:
        """Run a complete code analysis"""
        logger.info("Starting full code analysis...")
        
        # Analyze all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        complexity_scores = []
        
        for file_path in python_files:
            try:
                analysis = await self._analyze_file(file_path)
                total_lines += analysis.get('lines', 0)
                total_functions += analysis.get('functions', 0)
                total_classes += analysis.get('classes', 0)
                if analysis.get('complexity'):
                    complexity_scores.append(analysis['complexity'])
            except Exception as e:
                logger.debug(f"Error analyzing {file_path}: {e}")
        
        self.stats['files_analyzed'] = len(python_files)
        
        # Calculate metrics
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        
        # Count flaws
        flaws_by_type = defaultdict(int)
        flaws_by_severity = defaultdict(int)
        
        for flaw in self.flaws.values():
            flaws_by_type[flaw.flaw_type.name] += 1
            flaws_by_severity[flaw.severity.name] += 1
        
        # Get top issues
        top_issues = sorted(
            self.flaws.values(),
            key=lambda f: f.severity.value,
            reverse=True
        )[:10]
        
        report = CodeQualityReport(
            total_files=len(python_files),
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            complexity_score=avg_complexity,
            maintainability_score=self._calculate_maintainability(),
            test_coverage=self._estimate_test_coverage(),
            documentation_coverage=self._estimate_doc_coverage(),
            flaws_by_type=dict(flaws_by_type),
            flaws_by_severity=dict(flaws_by_severity),
            top_issues=top_issues,
            generated_at=datetime.now(),
        )
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Analysis complete: {len(python_files)} files, {len(self.flaws)} flaws detected")
        
        return report
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            try:
                # Parse AST
                tree = ast.parse(content)
                self._ast_cache[str(file_path)] = tree
            except SyntaxError as e:
                self._record_flaw(
                    FlawType.BUG,
                    FlawSeverity.CRITICAL,
                    f"{file_path}:{e.lineno}",
                    f"Syntax error: {e.msg}",
                    "Fix the syntax error",
                    lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else None
                )
                return {'lines': len(lines), 'functions': 0, 'classes': 0}
            
            # Count elements
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Check for code smells
            self._check_code_smells(file_path, content, lines, tree)
            
            # Calculate complexity
            complexity = self._calculate_complexity(tree)
            
            return {
                'lines': len(lines),
                'functions': len(functions),
                'classes': len(classes),
                'complexity': complexity,
            }
            
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
            return {'lines': 0, 'functions': 0, 'classes': 0}
    
    def _check_code_smells(
        self,
        file_path: Path,
        content: str,
        lines: List[str],
        tree: ast.AST
    ) -> None:
        """Check for code smells in a file"""
        # Check regex patterns
        for smell_name, pattern_info in self.CODE_SMELL_PATTERNS.items():
            if pattern_info is None:
                continue
            
            pattern, description = pattern_info
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    self._record_flaw(
                        FlawType.CODE_SMELL,
                        f"{file_path}:{i}",
                        description,
                        f"Review and fix: {smell_name}",
                        line.strip()
                    )
        
        # Check for long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    self._record_flaw(
                        FlawType.MAINTAINABILITY,
                        FlawSeverity.MEDIUM,
                        f"{file_path}:{node.lineno}",
                        f"Function '{node.name}' is too long ({func_lines} lines)",
                        "Consider breaking into smaller functions",
                        None
                    )
                
                # Check for deep nesting
                max_depth = self._get_max_nesting_depth(node)
                if max_depth > 4:
                    self._record_flaw(
                        FlawType.MAINTAINABILITY,
                        FlawSeverity.MEDIUM,
                        f"{file_path}:{node.lineno}",
                        f"Function '{node.name}' has deep nesting (depth: {max_depth})",
                        "Reduce nesting by extracting logic or using early returns",
                        None
                    )
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self._record_flaw(
                        FlawType.INCOMPLETE,
                        FlawSeverity.INFO,
                        f"{file_path}:{node.lineno}",
                        f"Missing docstring for {type(node).__name__} '{node.name}'",
                        "Add a docstring describing the purpose and parameters",
                        None
                    )
        
        # Check for unused imports
        self._check_unused_imports(file_path, tree, content)
    
    def _get_max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Get maximum nesting depth of a node"""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._get_max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._get_max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _check_unused_imports(
        self,
        file_path: Path,
        tree: ast.AST,
        content: str
    ) -> None:
        """Check for unused imports"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imports.append((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != '*':
                        name = alias.asname or alias.name
                        imports.append((name, node.lineno))
        
        # Check if imports are used
        for name, lineno in imports:
            # Simple check: count occurrences after import
            pattern = rf'\b{re.escape(name)}\b'
            matches = list(re.finditer(pattern, content))
            
            # If only one match (the import itself), it's unused
            if len(matches) <= 1:
                self._record_flaw(
                    FlawType.CODE_SMELL,
                    FlawSeverity.LOW,
                    f"{file_path}:{lineno}",
                    f"Unused import: {name}",
                    f"Remove unused import '{name}'",
                    None
                )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity of code"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_maintainability(self) -> float:
        """Calculate maintainability index"""
        if not self.flaws:
            return 100.0
        
        # Start with 100 and subtract based on flaws
        score = 100.0
        
        for flaw in self.flaws.values():
            if flaw.severity == FlawSeverity.CRITICAL:
                score -= 10
            elif flaw.severity == FlawSeverity.HIGH:
                score -= 5
            elif flaw.severity == FlawSeverity.MEDIUM:
                score -= 2
            elif flaw.severity == FlawSeverity.LOW:
                score -= 1
        
        return max(0, min(100, score))
    
    def _estimate_test_coverage(self) -> float:
        """Estimate test coverage"""
        test_files = list(self.project_root.rglob("test_*.py"))
        test_files.extend(self.project_root.rglob("*_test.py"))
        
        all_files = list(self.project_root.rglob("*.py"))
        
        if not all_files:
            return 0.0
        
        # Rough estimate based on test file ratio
        return min(100, len(test_files) / len(all_files) * 200)
    
    def _estimate_doc_coverage(self) -> float:
        """Estimate documentation coverage"""
        documented = 0
        total = 0
        
        for tree in self._ast_cache.values():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    total += 1
                    if ast.get_docstring(node):
                        documented += 1
        
        if total == 0:
            return 0.0
        
        return (documented / total) * 100
    
    def _record_flaw(
        self,
        flaw_type: FlawType,
        severity: FlawSeverity,
        location: str,
        description: str,
        suggestion: str,
        code_snippet: Optional[str]
    ) -> DetectedFlaw:
        """Record a detected flaw"""
        import hashlib
        flaw_id = hashlib.md5(f"{location}:{description}".encode()).hexdigest()[:12]
        
        # Don't duplicate
        if flaw_id in self.flaws:
            return self.flaws[flaw_id]
        
        flaw = DetectedFlaw(
            id=flaw_id,
            flaw_type=flaw_type,
            severity=severity,
            location=location,
            description=description,
            suggestion=suggestion,
            code_snippet=code_snippet,
            detected_at=datetime.now(),
        )
        
        with self._lock:
            self.flaws[flaw_id] = flaw
            self.flaw_history.append(flaw)
            self.stats['flaws_detected'] += 1
        
        if severity.value >= FlawSeverity.HIGH.value:
            logger.warning(f"Flaw detected: {description} at {location}")
        
        return flaw
    
    def _save_report(self, report: CodeQualityReport) -> None:
        """Save analysis report to file"""
        report_file = self.report_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump({
                    'total_files': report.total_files,
                    'total_lines': report.total_lines,
                    'total_functions': report.total_functions,
                    'total_classes': report.total_classes,
                    'complexity_score': report.complexity_score,
                    'maintainability_score': report.maintainability_score,
                    'test_coverage': report.test_coverage,
                    'documentation_coverage': report.documentation_coverage,
                    'flaws_by_type': report.flaws_by_type,
                    'flaws_by_severity': report.flaws_by_severity,
                    'top_issues': [f.to_dict() for f in report.top_issues],
                    'generated_at': report.generated_at.isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    # Performance monitoring
    
    def track_function_call(
        self,
        function_name: str,
        execution_time_ms: float,
        success: bool = True
    ) -> None:
        """Track a function call for performance analysis"""
        with self._lock:
            self.function_timings[function_name].append(execution_time_ms)
            
            # Keep only last 1000 timings
            if len(self.function_timings[function_name]) > 1000:
                self.function_timings[function_name] = self.function_timings[function_name][-1000:]
            
            if not success:
                self.error_counts[function_name] += 1
            
            # Check for performance issues
            if execution_time_ms > self.PERFORMANCE_THRESHOLDS['function_time_ms']:
                self._record_flaw(
                    FlawType.PERFORMANCE,
                    FlawSeverity.MEDIUM,
                    function_name,
                    f"Slow function execution: {execution_time_ms:.2f}ms",
                    "Optimize the function or add caching",
                    None
                )
    
    def get_performance_report(self) -> Dict[str, PerformanceMetric]:
        """Get performance metrics for all tracked functions"""
        metrics = {}
        
        for func_name, timings in self.function_timings.items():
            if timings:
                metrics[func_name] = PerformanceMetric(
                    name=func_name,
                    execution_time_ms=sum(timings) / len(timings),
                    memory_usage_mb=0,  # Would need memory profiling
                    call_count=len(timings),
                    error_count=self.error_counts.get(func_name, 0),
                    last_measured=datetime.now(),
                )
        
        return metrics
    
    # Public API
    
    def get_flaws(
        self,
        flaw_type: FlawType = None,
        min_severity: FlawSeverity = None
    ) -> List[DetectedFlaw]:
        """Get detected flaws with optional filtering"""
        flaws = list(self.flaws.values())
        
        if flaw_type:
            flaws = [f for f in flaws if f.flaw_type == flaw_type]
        
        if min_severity:
            flaws = [f for f in flaws if f.severity.value >= min_severity.value]
        
        return sorted(flaws, key=lambda f: f.severity.value, reverse=True)
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get prioritized improvement suggestions"""
        suggestions = []
        
        for flaw in self.get_flaws(min_severity=FlawSeverity.MEDIUM):
            if not flaw.fixed:
                suggestions.append({
                    'priority': flaw.severity.value,
                    'type': flaw.flaw_type.name,
                    'location': flaw.location,
                    'issue': flaw.description,
                    'suggestion': flaw.suggestion,
                })
        
        return sorted(suggestions, key=lambda s: s['priority'], reverse=True)
    
    def mark_flaw_fixed(self, flaw_id: str, fix_description: str) -> None:
        """Mark a flaw as fixed"""
        if flaw_id in self.flaws:
            self.flaws[flaw_id].fixed = True
            self.flaws[flaw_id].fix_applied = fix_description
            self.stats['flaws_fixed'] += 1
    
    def get_code_health_score(self) -> float:
        """Get overall code health score (0-100)"""
        maintainability = self._calculate_maintainability()
        test_coverage = self._estimate_test_coverage()
        doc_coverage = self._estimate_doc_coverage()
        
        # Weighted average
        return (
            maintainability * 0.5 +
            test_coverage * 0.3 +
            doc_coverage * 0.2
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get introspector statistics"""
        return {
            **self.stats,
            'active_flaws': len([f for f in self.flaws.values() if not f.fixed]),
            'code_health_score': self.get_code_health_score(),
        }
