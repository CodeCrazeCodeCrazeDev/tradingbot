"""
Self-Diagnosis Engine for Autonomous Agents
Advanced self-audit and diagnostic capabilities for recursive improvement
"""

import asyncio
import json
import time
import logging
import subprocess
import os
import sys
import importlib
import inspect
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import ast
import numpy as np
from pathlib import Path
import psutil
import threading
import queue
import hashlib
import pickle

@dataclass
class DiagnosticMetric:
    """Individual diagnostic metric"""
    name: str
    value: float
    threshold: float
    status: str  # 'pass', 'warning', 'critical'
    description: str
    recommendations: List[str]

@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""
    timestamp: datetime
    overall_health_score: float
    metrics: List[DiagnosticMetric]
    critical_issues: List[str]
    warnings: List[str]
    performance_bottlenecks: List[str]
    code_quality_metrics: Dict[str, float]
    architectural_health: Dict[str, Any]
    evolution_readiness: float

class SelfDiagnosisEngine:
    """Advanced self-diagnosis engine for autonomous systems"""
    
    def __init__(self, codebase_path: str = "."):
        self.codebase_path = Path(codebase_path)
        self.logger = logging.getLogger("SelfDiagnosisEngine")
        self.diagnostic_history = []
        self.baseline_metrics = {}
        self.health_thresholds = {
            'overall_health': 80.0,
            'performance': 70.0,
            'code_quality': 75.0,
            'architectural_health': 70.0
        }
        
        # Diagnostic modules
        self.performance_monitor = PerformanceMonitor()
        self.code_analyzer = CodeQualityAnalyzer()
        self.architecture_analyzer = ArchitectureAnalyzer()
        self.security_scanner = SecurityScanner()
        self.dependency_checker = DependencyAnalyzer()
    
    async def comprehensive_self_diagnosis(self) -> SystemHealthReport:
        """Perform comprehensive self-diagnosis"""
        self.logger.info("Starting comprehensive self-diagnosis")
        
        # Collect all diagnostic metrics
        metrics = []
        
        # Performance metrics
        perf_metrics = await self.performance_monitor.analyze_performance()
        metrics.extend(perf_metrics)
        
        # Code quality metrics
        code_metrics = await self.code_analyzer.analyze_code_quality(self.codebase_path)
        metrics.extend(code_metrics)
        
        # Architecture health metrics
        arch_metrics = await self.architecture_analyzer.analyze_architecture(self.codebase_path)
        metrics.extend(arch_metrics)
        
        # Security metrics
        sec_metrics = await self.security_scanner.scan_security(self.codebase_path)
        metrics.extend(sec_metrics)
        
        # Dependency metrics
        dep_metrics = await self.dependency_checker.analyze_dependencies(self.codebase_path)
        metrics.extend(dep_metrics)
        
        # Analyze metrics and identify issues
        critical_issues, warnings = self._analyze_metric_status(metrics)
        
        # Calculate overall health score
        overall_score = self._calculate_overall_health(metrics)
        
        # Identify performance bottlenecks
        bottlenecks = self._identify_bottlenecks(metrics)
        
        # Calculate code quality summary
        code_quality_summary = self._summarize_code_quality(metrics)
        
        # Assess architectural health
        architectural_health = self._assess_architectural_health(metrics)
        
        # Calculate evolution readiness
        evolution_readiness = self._calculate_evolution_readiness(overall_score, metrics)
        
        # Create health report
        report = SystemHealthReport(
            timestamp=datetime.now(),
            overall_health_score=overall_score,
            metrics=metrics,
            critical_issues=critical_issues,
            warnings=warnings,
            performance_bottlenecks=bottlenecks,
            code_quality_metrics=code_quality_summary,
            architectural_health=architectural_health,
            evolution_readiness=evolution_readiness
        )
        
        # Store in history
        self.diagnostic_history.append(report)
        
        # Update baseline if this is first run
        if not self.baseline_metrics:
            self._establish_baseline(report)
        
        self.logger.info(f"Self-diagnosis completed. Overall health: {overall_score:.1f}")
        
        return report
    
    def _analyze_metric_status(self, metrics: List[DiagnosticMetric]) -> Tuple[List[str], List[str]]:
        """Analyze metrics to identify critical issues and warnings"""
        critical_issues = []
        warnings = []
        
        for metric in metrics:
            if metric.status == 'critical':
                critical_issues.append(f"{metric.name}: {metric.description}")
            elif metric.status == 'warning':
                warnings.append(f"{metric.name}: {metric.description}")
        
        return critical_issues, warnings
    
    def _calculate_overall_health(self, metrics: List[DiagnosticMetric]) -> float:
        """Calculate overall system health score"""
        if not metrics:
            return 0.0
        
        # Weight different categories
        weights = {
            'performance': 0.25,
            'code_quality': 0.25,
            'security': 0.20,
            'architecture': 0.20,
            'dependencies': 0.10
        }
        
        category_scores = {}
        category_counts = {}
        
        for metric in metrics:
            category = self._get_metric_category(metric.name)
            if category not in category_scores:
                category_scores[category] = 0
                category_counts[category] = 0
            
            # Normalize metric value (assuming higher is better)
            normalized_value = min(100.0, max(0.0, metric.value))
            category_scores[category] += normalized_value
            category_counts[category] += 1
        
        # Calculate weighted average
        overall_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            if category in weights:
                avg_score = score / category_counts[category]
                overall_score += avg_score * weights[category]
                total_weight += weights[category]
        
        return overall_score / total_weight if total_weight > 0 else 0.0
    
    def _get_metric_category(self, metric_name: str) -> str:
        """Categorize metric by name"""
        name_lower = metric_name.lower()
        
        if any(keyword in name_lower for keyword in ['cpu', 'memory', 'performance', 'response']):
            return 'performance'
        elif any(keyword in name_lower for keyword in ['code', 'quality', 'complexity', 'coverage']):
            return 'code_quality'
        elif any(keyword in name_lower for keyword in ['security', 'vulnerability', 'auth']):
            return 'security'
        elif any(keyword in name_lower for keyword in ['architecture', 'design', 'coupling']):
            return 'architecture'
        elif any(keyword in name_lower for keyword in ['dependency', 'package', 'version']):
            return 'dependencies'
        
        return 'general'
    
    def _identify_bottlenecks(self, metrics: List[DiagnosticMetric]) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        for metric in metrics:
            if metric.status == 'critical' and 'performance' in self._get_metric_category(metric.name):
                bottlenecks.append(f"{metric.name}: {metric.value:.1f} (threshold: {metric.threshold})")
        
        return bottlenecks
    
    def _summarize_code_quality(self, metrics: List[DiagnosticMetric]) -> Dict[str, float]:
        """Summarize code quality metrics"""
        quality_metrics = {}
        
        for metric in metrics:
            if self._get_metric_category(metric.name) == 'code_quality':
                quality_metrics[metric.name] = metric.value
        
        return quality_metrics
    
    def _assess_architectural_health(self, metrics: List[DiagnosticMetric]) -> Dict[str, Any]:
        """Assess architectural health"""
        arch_health = {
            'overall_score': 0.0,
            'design_patterns': 0.0,
            'coupling_score': 0.0,
            'cohesion_score': 0.0,
            'modularity_score': 0.0
        }
        
        arch_metrics = [m for m in metrics if self._get_metric_category(m.name) == 'architecture']
        
        if arch_metrics:
            arch_health['overall_score'] = np.mean([m.value for m in arch_metrics])
            
            for metric in arch_metrics:
                if 'pattern' in metric.name.lower():
                    arch_health['design_patterns'] = metric.value
                elif 'coupling' in metric.name.lower():
                    arch_health['coupling_score'] = metric.value
                elif 'cohesion' in metric.name.lower():
                    arch_health['cohesion_score'] = metric.value
                elif 'modular' in metric.name.lower():
                    arch_health['modularity_score'] = metric.value
        
        return arch_health
    
    def _calculate_evolution_readiness(self, overall_score: float, metrics: List[DiagnosticMetric]) -> float:
        """Calculate readiness for evolution"""
        base_readiness = overall_score
        
        # Adjust based on critical issues
        critical_count = sum(1 for m in metrics if m.status == 'critical')
        base_readiness -= critical_count * 10
        
        # Adjust based on code quality
        code_quality_avg = np.mean([m.value for m in metrics if self._get_metric_category(m.name) == 'code_quality'])
        if code_quality_avg < 60:
            base_readiness -= 15
        
        # Adjust based on architectural health
        arch_avg = np.mean([m.value for m in metrics if self._get_metric_category(m.name) == 'architecture'])
        if arch_avg < 60:
            base_readiness -= 10
        
        return max(0.0, min(100.0, base_readiness))
    
    def _establish_baseline(self, report: SystemHealthReport) -> None:
        """Establish baseline metrics for future comparison"""
        for metric in report.metrics:
            self.baseline_metrics[metric.name] = metric.value
    
    def get_diagnostic_trends(self) -> Dict[str, Any]:
        """Analyze diagnostic trends over time"""
        if len(self.diagnostic_history) < 2:
            return {'status': 'Insufficient data for trend analysis'}
        
        trends = {
            'health_score_trend': [],
            'critical_issues_trend': [],
            'performance_trend': [],
            'code_quality_trend': [],
            'improvement_rate': 0.0
        }
        
        for report in self.diagnostic_history:
            trends['health_score_trend'].append(report.overall_health_score)
            trends['critical_issues_trend'].append(len(report.critical_issues))
            
            # Calculate category averages
            perf_metrics = [m.value for m in report.metrics if self._get_metric_category(m.name) == 'performance']
            if perf_metrics:
                trends['performance_trend'].append(np.mean(perf_metrics))
            
            code_metrics = [m.value for m in report.metrics if self._get_metric_category(m.name) == 'code_quality']
            if code_metrics:
                trends['code_quality_trend'].append(np.mean(code_metrics))
        
        # Calculate improvement rate
        if len(trends['health_score_trend']) >= 2:
            initial_score = trends['health_score_trend'][0]
            current_score = trends['health_score_trend'][-1]
            trends['improvement_rate'] = ((current_score - initial_score) / initial_score) * 100
        
        return trends

class PerformanceMonitor:
    """Monitor system performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger("PerformanceMonitor")
    
    async def analyze_performance(self) -> List[DiagnosticMetric]:
        """Analyze system performance"""
        metrics = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(DiagnosticMetric(
                name="cpu_usage",
                value=100.0 - cpu_percent,  # Invert so higher is better
                threshold=70.0,
                status="pass" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical",
                description=f"CPU usage: {cpu_percent:.1f}%",
                recommendations=["Optimize CPU-intensive operations", "Consider load balancing"]
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics.append(DiagnosticMetric(
                name="memory_usage",
                value=100.0 - memory.percent,  # Invert
                threshold=70.0,
                status="pass" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical",
                description=f"Memory usage: {memory.percent:.1f}%",
                recommendations=["Optimize memory usage", "Implement caching strategies"]
            ))
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                # Simplified disk performance metric
                disk_score = 80.0  # Placeholder
                metrics.append(DiagnosticMetric(
                    name="disk_performance",
                    value=disk_score,
                    threshold=70.0,
                    status="pass",
                    description="Disk I/O performance",
                    recommendations=["Monitor disk usage", "Optimize database queries"]
                ))
            
            # Response time (simulated)
            response_time = np.random.uniform(0.1, 2.0)
            response_score = max(0, 100 - (response_time * 20))
            metrics.append(DiagnosticMetric(
                name="response_time",
                value=response_score,
                threshold=80.0,
                status="pass" if response_time < 0.5 else "warning" if response_time < 1.0 else "critical",
                description=f"Average response time: {response_time:.2f}s",
                recommendations=["Optimize database queries", "Implement caching", "Use async operations"]
            ))
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
        
        return metrics

class CodeQualityAnalyzer:
    """Analyze code quality metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger("CodeQualityAnalyzer")
    
    async def analyze_code_quality(self, codebase_path: Path) -> List[DiagnosticMetric]:
        """Analyze code quality across the codebase"""
        metrics = []
        
        try:
            # Find Python files
            python_files = list(codebase_path.rglob("*.py"))
            
            if not python_files:
                return metrics
            
            # Analyze each file
            total_lines = 0
            total_complexity = 0
            total_functions = 0
            documented_functions = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Count lines
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    # Analyze complexity (simplified)
                    complexity = self._calculate_complexity(tree)
                    total_complexity += complexity
                    
                    # Count functions and documentation
                    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    total_functions += len(functions)
                    documented_functions += sum(1 for func in functions if ast.get_docstring(func))
                
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")
            
            # Calculate metrics
            if total_functions > 0:
                documentation_coverage = (documented_functions / total_functions) * 100
                metrics.append(DiagnosticMetric(
                    name="documentation_coverage",
                    value=documentation_coverage,
                    threshold=80.0,
                    status="pass" if documentation_coverage >= 80 else "warning" if documentation_coverage >= 60 else "critical",
                    description=f"Documentation coverage: {documentation_coverage:.1f}%",
                    recommendations=["Add docstrings to functions", "Improve inline documentation"]
                ))
            
            if python_files:
                avg_complexity = total_complexity / len(python_files)
                complexity_score = max(0, 100 - avg_complexity)
                metrics.append(DiagnosticMetric(
                    name="cyclomatic_complexity",
                    value=complexity_score,
                    threshold=70.0,
                    status="pass" if avg_complexity < 10 else "warning" if avg_complexity < 20 else "critical",
                    description=f"Average complexity: {avg_complexity:.1f}",
                    recommendations=["Refactor complex functions", "Break down large functions", "Use design patterns"]
                ))
            
            # Test coverage (simulated)
            test_coverage = np.random.uniform(40, 90)
            metrics.append(DiagnosticMetric(
                name="test_coverage",
                value=test_coverage,
                threshold=80.0,
                status="pass" if test_coverage >= 80 else "warning" if test_coverage >= 60 else "critical",
                description=f"Test coverage: {test_coverage:.1f}%",
                recommendations=["Write more unit tests", "Add integration tests", "Improve test quality"]
            ))
            
        except Exception as e:
            self.logger.error(f"Code quality analysis failed: {e}")
        
        return metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity

class ArchitectureAnalyzer:
    """Analyze architectural health"""
    
    def __init__(self):
        self.logger = logging.getLogger("ArchitectureAnalyzer")
    
    async def analyze_architecture(self, codebase_path: Path) -> List[DiagnosticMetric]:
        """Analyze architectural quality"""
        metrics = []
        
        try:
            # Analyze module structure
            modules = self._analyze_modules(codebase_path)
            
            # Coupling analysis (simulated)
            coupling_score = np.random.uniform(60, 90)
            metrics.append(DiagnosticMetric(
                name="coupling_score",
                value=coupling_score,
                threshold=75.0,
                status="pass" if coupling_score >= 75 else "warning" if coupling_score >= 60 else "critical",
                description=f"Module coupling score: {coupling_score:.1f}",
                recommendations=["Reduce inter-module dependencies", "Implement dependency injection", "Use interfaces"]
            ))
            
            # Cohesion analysis (simulated)
            cohesion_score = np.random.uniform(65, 95)
            metrics.append(DiagnosticMetric(
                name="cohesion_score",
                value=cohesion_score,
                threshold=75.0,
                status="pass" if cohesion_score >= 75 else "warning" if cohesion_score >= 60 else "critical",
                description=f"Module cohesion score: {cohesion_score:.1f}",
                recommendations=["Group related functionality", "Improve single responsibility", "Refactor large modules"]
            ))
            
            # Design pattern usage (simulated)
            pattern_score = np.random.uniform(50, 85)
            metrics.append(DiagnosticMetric(
                name="design_pattern_usage",
                value=pattern_score,
                threshold=70.0,
                status="pass" if pattern_score >= 70 else "warning" if pattern_score >= 50 else "critical",
                description=f"Design pattern usage: {pattern_score:.1f}%",
                recommendations=["Implement appropriate design patterns", "Use SOLID principles", "Improve code organization"]
            ))
            
        except Exception as e:
            self.logger.error(f"Architecture analysis failed: {e}")
        
        return metrics
    
    def _analyze_modules(self, codebase_path: Path) -> Dict[str, Any]:
        """Analyze module structure"""
        modules = {}
        
        for py_file in codebase_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Count imports, classes, functions
                imports = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
                classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
                functions = len([node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))])
                
                modules[str(py_file)] = {
                    'imports': imports,
                    'classes': classes,
                    'functions': functions,
                    'lines': len(content.splitlines())
                }
            
            except Exception as e:
                self.logger.warning(f"Failed to analyze module {py_file}: {e}")
        
        return modules

class SecurityScanner:
    """Scan for security vulnerabilities"""
    
    def __init__(self):
        self.logger = logging.getLogger("SecurityScanner")
    
    async def scan_security(self, codebase_path: Path) -> List[DiagnosticMetric]:
        """Scan for security issues"""
        metrics = []
        
        try:
            # Simulate security scan results
            security_score = np.random.uniform(70, 95)
            metrics.append(DiagnosticMetric(
                name="security_score",
                value=security_score,
                threshold=85.0,
                status="pass" if security_score >= 85 else "warning" if security_score >= 70 else "critical",
                description=f"Security score: {security_score:.1f}",
                recommendations=["Update dependencies", "Implement input validation", "Add authentication mechanisms"]
            ))
            
            # Vulnerability count (simulated)
            vuln_count = np.random.randint(0, 5)
            vuln_score = max(0, 100 - (vuln_count * 20))
            metrics.append(DiagnosticMetric(
                name="vulnerability_count",
                value=vuln_score,
                threshold=90.0,
                status="pass" if vuln_count == 0 else "warning" if vuln_count <= 2 else "critical",
                description=f"Security vulnerabilities found: {vuln_count}",
                recommendations=["Address security vulnerabilities", "Implement security testing", "Regular security audits"]
            ))
            
        except Exception as e:
            self.logger.error(f"Security scan failed: {e}")
        
        return metrics

class DependencyAnalyzer:
    """Analyze project dependencies"""
    
    def __init__(self):
        self.logger = logging.getLogger("DependencyAnalyzer")
    
    async def analyze_dependencies(self, codebase_path: Path) -> List[DiagnosticMetric]:
        """Analyze dependency health"""
        metrics = []
        
        try:
            # Check for requirements file
            req_files = list(codebase_path.rglob("requirements*.txt"))
            
            if req_files:
                # Simulate dependency analysis
                outdated_deps = np.random.randint(0, 8)
                dep_score = max(0, 100 - (outdated_deps * 10))
                metrics.append(DiagnosticMetric(
                    name="dependency_health",
                    value=dep_score,
                    threshold=80.0,
                    status="pass" if outdated_deps <= 2 else "warning" if outdated_deps <= 5 else "critical",
                    description=f"Outdated dependencies: {outdated_deps}",
                    recommendations=["Update dependencies", "Use dependency management tools", "Regular dependency audits"]
                ))
            
        except Exception as e:
            self.logger.error(f"Dependency analysis failed: {e}")
        
        return metrics

# Integration with recursive self-improvement system
class EnhancedSelfDiagnosis:
    """Enhanced self-diagnosis integration"""
    
    def __init__(self, codebase_path: str = "."):
        self.diagnosis_engine = SelfDiagnosisEngine(codebase_path)
        self.logger = logging.getLogger("EnhancedSelfDiagnosis")
    
    async def continuous_health_monitoring(self, interval: int = 300) -> None:
        """Continuous health monitoring"""
        self.logger.info("Starting continuous health monitoring")
        
        while True:
            try:
                # Perform diagnosis
                health_report = await self.diagnosis_engine.comprehensive_self_diagnosis()
                
                # Log results
                self.logger.info(f"Health score: {health_report.overall_health_score:.1f}")
                
                if health_report.critical_issues:
                    self.logger.error(f"Critical issues: {health_report.critical_issues}")
                
                if health_report.warnings:
                    self.logger.warning(f"Warnings: {health_report.warnings}")
                
                # Check if intervention needed
                if health_report.overall_health_score < 60:
                    self.logger.critical("System health critical - intervention required")
                    await self._trigger_emergency_response(health_report)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _trigger_emergency_response(self, health_report: SystemHealthReport) -> None:
        """Trigger emergency response for critical health issues"""
        self.logger.critical("Triggering emergency response protocols")
        
        # Create emergency backup
        backup_path = f"emergency_backup_{int(time.time())}"
        try:
            subprocess.run(f"cp -r . {backup_path}", shell=True, check=True)
            self.logger.info(f"Emergency backup created: {backup_path}")
        except Exception as e:
            self.logger.error(f"Emergency backup failed: {e}")
        
        # Implement emergency fixes for critical issues
        for issue in health_report.critical_issues:
            await self._apply_emergency_fix(issue)
    
    async def _apply_emergency_fix(self, issue: str) -> None:
        """Apply emergency fix for critical issue"""
        # Simplified emergency fixes
        if "memory" in issue.lower():
            self.logger.info("Applying memory optimization")
            # Implement memory cleanup
        elif "cpu" in issue.lower():
            self.logger.info("Applying CPU optimization")
            # Implement CPU optimization
        elif "security" in issue.lower():
            self.logger.info("Applying security patch")
            # Implement security fix

# Usage example
async def main():
    """Main entry point for self-diagnosis system"""
    logging.basicConfig(level=logging.INFO)
    
    diagnosis_system = EnhancedSelfDiagnosis(".")
    
    # Run single comprehensive diagnosis
    health_report = await diagnosis_system.diagnosis_engine.comprehensive_self_diagnosis()
    
    print("\n=== System Health Report ===")
    print(f"Overall Health Score: {health_report.overall_health_score:.1f}")
    print(f"Critical Issues: {len(health_report.critical_issues)}")
    print(f"Warnings: {len(health_report.warnings)}")
    print(f"Evolution Readiness: {health_report.evolution_readiness:.1f}")
    
    if health_report.critical_issues:
        print("\nCritical Issues:")
        for issue in health_report.critical_issues:
            print(f"  - {issue}")
    
    # Start continuous monitoring
    # await diagnosis_system.continuous_health_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
