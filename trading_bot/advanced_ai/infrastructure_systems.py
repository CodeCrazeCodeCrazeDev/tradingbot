"""
Infrastructure Systems
======================

Advanced infrastructure capabilities including:
- Automated Dependency Management
- Self-Healing Infrastructure
- Performance Profiling & Optimization
- Automated Testing Generation
"""

import ast
import asyncio
import hashlib
import importlib
import inspect
import logging
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# AUTOMATED DEPENDENCY MANAGEMENT
# =============================================================================

@dataclass
class Dependency:
    """A package dependency"""
    name: str
    version: str
    required_version: Optional[str] = None
    is_installed: bool = False
    is_compatible: bool = True
    has_security_issue: bool = False
    last_checked: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DependencyUpdate:
    """A pending dependency update"""
    package: str
    current_version: str
    new_version: str
    is_major: bool
    is_security: bool
    changelog_url: Optional[str] = None


class DependencyManager:
    """
    Automated Dependency Management
    
    Automatically manages, updates, and validates
    package dependencies.
    """
    
    def __init__(
        self,
        requirements_file: str = "requirements.txt",
        auto_update: bool = False,
        security_only: bool = True
    ):
        self.requirements_file = requirements_file
        self.auto_update = auto_update
        self.security_only = security_only
        
        self.dependencies: Dict[str, Dependency] = {}
        self.pending_updates: List[DependencyUpdate] = []
        self.update_history: List[Dict[str, Any]] = []
        
        # Packages to never auto-update
        self.protected_packages = {
            'numpy', 'pandas', 'tensorflow', 'torch', 'scikit-learn'
        }
        
        logger.info("DependencyManager initialized")
    
    def scan_dependencies(self) -> Dict[str, Dependency]:
        """Scan and catalog all dependencies"""
        
        self.dependencies = {}
        
        # Read requirements file
        if os.path.exists(self.requirements_file):
            with open(self.requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self._parse_requirement(line)
        
        # Check installed packages
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                import json
                installed = json.loads(result.stdout)
                
                for pkg in installed:
                    name = pkg['name'].lower()
                    version = pkg['version']
                    
                    if name in self.dependencies:
                        self.dependencies[name].version = version
                        self.dependencies[name].is_installed = True
                    else:
                        self.dependencies[name] = Dependency(
                            name=name,
                            version=version,
                            is_installed=True
                        )
        except Exception as e:
            logger.warning(f"Error scanning installed packages: {e}")
        
        logger.info(f"Scanned {len(self.dependencies)} dependencies")
        
        return self.dependencies
    
    def _parse_requirement(self, line: str):
        """Parse a requirement line"""
        
        # Handle various formats: pkg, pkg==1.0, pkg>=1.0, pkg[extra]
        import re
        
        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?(?:([<>=!]+)(.+))?$', line)
        
        if match:
            name = match.group(1).lower()
            operator = match.group(2)
            version = match.group(3)
            
            self.dependencies[name] = Dependency(
                name=name,
                version=version or 'unknown',
                required_version=f"{operator}{version}" if operator else None
            )
    
    def check_for_updates(self) -> List[DependencyUpdate]:
        """Check for available updates"""
        
        self.pending_updates = []
        
        for name, dep in self.dependencies.items():
            if not dep.is_installed:
                continue
            
            try:
                # Check PyPI for latest version (simplified)
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'index', 'versions', name],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    # Parse output for available versions
                    output = result.stdout
                    if 'Available versions:' in output:
                        versions_str = output.split('Available versions:')[1].strip()
                        versions = [v.strip() for v in versions_str.split(',')]
                        
                        if versions and versions[0] != dep.version:
                            is_major = self._is_major_update(dep.version, versions[0])
                            
                            update = DependencyUpdate(
                                package=name,
                                current_version=dep.version,
                                new_version=versions[0],
                                is_major=is_major,
                                is_security=False  # Would need security DB
                            )
                            
                            self.pending_updates.append(update)
            
            except Exception as e:
                logger.debug(f"Error checking updates for {name}: {e}")
        
        logger.info(f"Found {len(self.pending_updates)} available updates")
        
        return self.pending_updates
    
    def _is_major_update(self, current: str, new: str) -> bool:
        """Check if update is a major version change"""
        
        try:
            current_major = int(current.split('.')[0])
            new_major = int(new.split('.')[0])
            return new_major > current_major
        except:
            return False
    
    def apply_update(
        self,
        package: str,
        version: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """Apply a package update"""
        
        if package in self.protected_packages and not force:
            logger.warning(f"Package {package} is protected, use force=True to update")
            return False
        
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
            
            if version:
                cmd.append(f"{package}=={version}")
            else:
                cmd.append(package)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.update_history.append({
                    'package': package,
                    'version': version,
                    'timestamp': datetime.utcnow().isoformat(),
                    'success': True
                })
                logger.info(f"Updated {package} successfully")
                return True
            else:
                logger.error(f"Failed to update {package}: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error updating {package}: {e}")
            return False
    
    def validate_compatibility(self) -> List[str]:
        """Validate dependency compatibility"""
        
        issues = []
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'check'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                issues.extend(result.stdout.strip().split('\n'))
        
        except Exception as e:
            issues.append(f"Error checking compatibility: {e}")
        
        return issues
    
    def get_report(self) -> Dict[str, Any]:
        """Get dependency management report"""
        
        return {
            'total_dependencies': len(self.dependencies),
            'installed': sum(1 for d in self.dependencies.values() if d.is_installed),
            'pending_updates': len(self.pending_updates),
            'recent_updates': self.update_history[-10:],
            'protected_packages': list(self.protected_packages)
        }


# =============================================================================
# SELF-HEALING INFRASTRUCTURE
# =============================================================================

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """A health check definition"""
    name: str
    check_function: Callable[[], bool]
    recovery_function: Optional[Callable[[], bool]] = None
    interval_seconds: int = 60
    timeout_seconds: int = 10
    failure_threshold: int = 3
    
    consecutive_failures: int = 0
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.HEALTHY


@dataclass
class RecoveryAction:
    """A recovery action taken"""
    timestamp: datetime
    health_check: str
    action: str
    success: bool
    details: str


class SelfHealingInfrastructure:
    """
    Self-Healing Infrastructure
    
    Automatically detects and recovers from failures.
    """
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.recovery_history: List[RecoveryAction] = []
        self.overall_status = HealthStatus.HEALTHY
        
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Register default health checks
        self._register_default_checks()
        
        logger.info("SelfHealingInfrastructure initialized")
    
    def _register_default_checks(self):
        """Register default health checks"""
        
        # Memory check
        self.register_health_check(
            "memory",
            self._check_memory,
            self._recover_memory,
            interval_seconds=30
        )
        
        # Disk check
        self.register_health_check(
            "disk",
            self._check_disk,
            None,
            interval_seconds=300
        )
        
        # Process check
        self.register_health_check(
            "process",
            self._check_process,
            self._recover_process,
            interval_seconds=60
        )
    
    def _check_memory(self) -> bool:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent < 90
        except ImportError:
            return True
    
    def _recover_memory(self) -> bool:
        """Attempt memory recovery"""
        import gc
        gc.collect()
        return True
    
    def _check_disk(self) -> bool:
        """Check disk space"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return disk.percent < 95
        except ImportError:
            return True
    
    def _check_process(self) -> bool:
        """Check process health"""
        return True  # Placeholder
    
    def _recover_process(self) -> bool:
        """Attempt process recovery"""
        return True  # Placeholder
    
    def register_health_check(
        self,
        name: str,
        check_function: Callable[[], bool],
        recovery_function: Optional[Callable[[], bool]] = None,
        interval_seconds: int = 60,
        failure_threshold: int = 3
    ):
        """Register a health check"""
        
        self.health_checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            recovery_function=recovery_function,
            interval_seconds=interval_seconds,
            failure_threshold=failure_threshold
        )
        
        logger.info(f"Registered health check: {name}")
    
    async def run_health_check(self, name: str) -> HealthStatus:
        """Run a specific health check"""
        
        if name not in self.health_checks:
            return HealthStatus.UNHEALTHY
        
        check = self.health_checks[name]
        
        try:
            # Run check with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, check.check_function),
                timeout=check.timeout_seconds
            )
            
            check.last_check = datetime.utcnow()
            
            if result:
                check.consecutive_failures = 0
                check.last_status = HealthStatus.HEALTHY
            else:
                check.consecutive_failures += 1
                
                if check.consecutive_failures >= check.failure_threshold:
                    check.last_status = HealthStatus.CRITICAL
                    
                    # Attempt recovery
                    if check.recovery_function:
                        await self._attempt_recovery(check)
                else:
                    check.last_status = HealthStatus.DEGRADED
            
            return check.last_status
        
        except asyncio.TimeoutError:
            check.consecutive_failures += 1
            check.last_status = HealthStatus.UNHEALTHY
            return HealthStatus.UNHEALTHY
        
        except Exception as e:
            logger.error(f"Health check {name} failed: {e}")
            check.consecutive_failures += 1
            check.last_status = HealthStatus.UNHEALTHY
            return HealthStatus.UNHEALTHY
    
    async def _attempt_recovery(self, check: HealthCheck):
        """Attempt recovery for a failed check"""
        
        if not check.recovery_function:
            return
        
        logger.info(f"Attempting recovery for {check.name}")
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, check.recovery_function)
            
            action = RecoveryAction(
                timestamp=datetime.utcnow(),
                health_check=check.name,
                action="auto_recovery",
                success=success,
                details=f"Recovery {'succeeded' if success else 'failed'}"
            )
            
            self.recovery_history.append(action)
            
            if success:
                check.consecutive_failures = 0
                check.last_status = HealthStatus.HEALTHY
                logger.info(f"Recovery successful for {check.name}")
            else:
                logger.warning(f"Recovery failed for {check.name}")
        
        except Exception as e:
            logger.error(f"Recovery error for {check.name}: {e}")
    
    async def run_all_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks"""
        
        results = {}
        
        for name in self.health_checks:
            results[name] = await self.run_health_check(name)
        
        # Update overall status
        statuses = list(results.values())
        
        if HealthStatus.CRITICAL in statuses:
            self.overall_status = HealthStatus.CRITICAL
        elif HealthStatus.UNHEALTHY in statuses:
            self.overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.HEALTHY
        
        return results
    
    async def start_monitoring(self):
        """Start background health monitoring"""
        
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop background health monitoring"""
        
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        
        while self._monitoring:
            try:
                await self.run_all_checks()
                await asyncio.sleep(10)  # Check interval
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        
        return {
            'overall_status': self.overall_status.value,
            'checks': {
                name: {
                    'status': check.last_status.value,
                    'consecutive_failures': check.consecutive_failures,
                    'last_check': check.last_check.isoformat() if check.last_check else None
                }
                for name, check in self.health_checks.items()
            },
            'recent_recoveries': [
                {
                    'timestamp': r.timestamp.isoformat(),
                    'check': r.health_check,
                    'success': r.success
                }
                for r in self.recovery_history[-10:]
            ]
        }


# =============================================================================
# PERFORMANCE PROFILING & OPTIMIZATION
# =============================================================================

@dataclass
class ProfileResult:
    """Result of profiling"""
    function_name: str
    total_time: float
    call_count: int
    avg_time: float
    memory_used: int
    bottleneck_score: float


@dataclass
class OptimizationSuggestion:
    """A suggested optimization"""
    target: str
    suggestion: str
    expected_improvement: float
    priority: int
    code_change: Optional[str] = None


class PerformanceProfiler:
    """
    Performance Profiling & Optimization
    
    Profiles code performance and suggests optimizations.
    """
    
    def __init__(self):
        self.profile_results: Dict[str, ProfileResult] = {}
        self.suggestions: List[OptimizationSuggestion] = []
        self.timing_history: Dict[str, List[float]] = {}
        
        logger.info("PerformanceProfiler initialized")
    
    def profile_function(
        self,
        func: Callable,
        *args,
        num_runs: int = 10,
        **kwargs
    ) -> ProfileResult:
        """Profile a function"""
        
        times = []
        
        for _ in range(num_runs):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        
        total_time = sum(times)
        avg_time = total_time / num_runs
        
        # Estimate memory (simplified)
        import sys
        memory_used = sys.getsizeof(func)
        
        # Calculate bottleneck score
        bottleneck_score = avg_time / 0.001  # Relative to 1ms baseline
        
        result = ProfileResult(
            function_name=func.__name__,
            total_time=total_time,
            call_count=num_runs,
            avg_time=avg_time,
            memory_used=memory_used,
            bottleneck_score=min(1.0, bottleneck_score)
        )
        
        self.profile_results[func.__name__] = result
        
        # Track timing history
        if func.__name__ not in self.timing_history:
            self.timing_history[func.__name__] = []
        self.timing_history[func.__name__].extend(times)
        
        return result
    
    def profile_code_block(
        self,
        code: str,
        globals_dict: Optional[Dict] = None,
        locals_dict: Optional[Dict] = None,
        num_runs: int = 10
    ) -> ProfileResult:
        """Profile a code block"""
        
        globals_dict = globals_dict or {}
        locals_dict = locals_dict or {}
        
        times = []
        
        for _ in range(num_runs):
            start = time.perf_counter()
            exec(code, globals_dict, locals_dict)
            end = time.perf_counter()
            times.append(end - start)
        
        total_time = sum(times)
        avg_time = total_time / num_runs
        
        result = ProfileResult(
            function_name="code_block",
            total_time=total_time,
            call_count=num_runs,
            avg_time=avg_time,
            memory_used=len(code),
            bottleneck_score=min(1.0, avg_time / 0.001)
        )
        
        return result
    
    def analyze_bottlenecks(self) -> List[ProfileResult]:
        """Identify performance bottlenecks"""
        
        bottlenecks = sorted(
            self.profile_results.values(),
            key=lambda x: x.bottleneck_score,
            reverse=True
        )
        
        return bottlenecks[:10]  # Top 10 bottlenecks
    
    def suggest_optimizations(self) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions"""
        
        self.suggestions = []
        
        for name, result in self.profile_results.items():
            if result.avg_time > 0.1:  # > 100ms
                self.suggestions.append(OptimizationSuggestion(
                    target=name,
                    suggestion="Consider caching results or using memoization",
                    expected_improvement=0.5,
                    priority=1
                ))
            
            if result.avg_time > 0.01 and result.call_count > 100:
                self.suggestions.append(OptimizationSuggestion(
                    target=name,
                    suggestion="High call frequency - consider batching operations",
                    expected_improvement=0.3,
                    priority=2
                ))
            
            if result.memory_used > 1000000:  # > 1MB
                self.suggestions.append(OptimizationSuggestion(
                    target=name,
                    suggestion="High memory usage - consider streaming or chunking",
                    expected_improvement=0.4,
                    priority=2
                ))
        
        # Sort by priority
        self.suggestions.sort(key=lambda x: x.priority)
        
        return self.suggestions
    
    def detect_performance_regression(
        self,
        function_name: str,
        threshold: float = 0.2
    ) -> Optional[Dict[str, Any]]:
        """Detect performance regression"""
        
        if function_name not in self.timing_history:
            return None
        
        times = self.timing_history[function_name]
        
        if len(times) < 20:
            return None
        
        # Compare recent vs historical
        recent = np.mean(times[-10:])
        historical = np.mean(times[:-10])
        
        if historical > 0:
            regression = (recent - historical) / historical
            
            if regression > threshold:
                return {
                    'function': function_name,
                    'regression_pct': regression * 100,
                    'recent_avg': recent,
                    'historical_avg': historical
                }
        
        return None
    
    def get_report(self) -> Dict[str, Any]:
        """Get profiling report"""
        
        return {
            'num_profiled': len(self.profile_results),
            'bottlenecks': [
                {
                    'function': r.function_name,
                    'avg_time_ms': r.avg_time * 1000,
                    'bottleneck_score': r.bottleneck_score
                }
                for r in self.analyze_bottlenecks()[:5]
            ],
            'suggestions': [
                {
                    'target': s.target,
                    'suggestion': s.suggestion,
                    'priority': s.priority
                }
                for s in self.suggestions[:5]
            ]
        }


# =============================================================================
# AUTOMATED TESTING GENERATION
# =============================================================================

class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PROPERTY = "property"
    MUTATION = "mutation"
    FUZZ = "fuzz"


@dataclass
class GeneratedTest:
    """A generated test case"""
    test_id: str
    test_type: TestType
    target_function: str
    test_code: str
    inputs: List[Any]
    expected_output: Any
    is_valid: bool = True


class AutomatedTestGenerator:
    """
    Automated Testing Generation
    
    Automatically generates test cases for code.
    """
    
    def __init__(self):
        self.generated_tests: List[GeneratedTest] = []
        self.coverage_data: Dict[str, float] = {}
        
        logger.info("AutomatedTestGenerator initialized")
    
    def generate_unit_tests(
        self,
        func: Callable,
        num_tests: int = 10
    ) -> List[GeneratedTest]:
        """Generate unit tests for a function"""
        
        tests = []
        sig = inspect.signature(func)
        
        for i in range(num_tests):
            # Generate random inputs based on parameter hints
            inputs = []
            
            for param_name, param in sig.parameters.items():
                if param.annotation == int:
                    inputs.append(np.random.randint(-100, 100))
                elif param.annotation == float:
                    inputs.append(np.random.uniform(-100, 100))
                elif param.annotation == str:
                    inputs.append(f"test_string_{i}")
                elif param.annotation == bool:
                    inputs.append(np.random.choice([True, False]))
                elif param.annotation == list:
                    inputs.append([np.random.randint(0, 10) for _ in range(5)])
                else:
                    inputs.append(None)
            
            # Try to get expected output
            try:
                expected = func(*inputs)
                is_valid = True
            except Exception as e:
                expected = f"Exception: {type(e).__name__}"
                is_valid = False
            
            # Generate test code
            test_code = self._generate_test_code(func, inputs, expected, i)
            
            test = GeneratedTest(
                test_id=f"test_{func.__name__}_{i}",
                test_type=TestType.UNIT,
                target_function=func.__name__,
                test_code=test_code,
                inputs=inputs,
                expected_output=expected,
                is_valid=is_valid
            )
            
            tests.append(test)
            self.generated_tests.append(test)
        
        return tests
    
    def _generate_test_code(
        self,
        func: Callable,
        inputs: List[Any],
        expected: Any,
        test_num: int
    ) -> str:
        """Generate test code string"""
        
        inputs_str = ', '.join(repr(i) for i in inputs)
        
        code = f'''
def test_{func.__name__}_{test_num}():
    """Auto-generated test for {func.__name__}"""
    result = {func.__name__}({inputs_str})
    expected = {repr(expected)}
    assert result == expected, f"Expected {{expected}}, got {{result}}"
'''
        return code
    
    def generate_property_tests(
        self,
        func: Callable,
        properties: List[Callable[[Any, Any], bool]]
    ) -> List[GeneratedTest]:
        """Generate property-based tests"""
        
        tests = []
        
        for i, prop in enumerate(properties):
            test_code = f'''
def test_{func.__name__}_property_{i}():
    """Property-based test for {func.__name__}"""
    for _ in range(100):
        # Generate random inputs
        inputs = generate_random_inputs()
        result = {func.__name__}(*inputs)
        assert property_{i}(inputs, result), "Property violation"
'''
            
            test = GeneratedTest(
                test_id=f"test_{func.__name__}_prop_{i}",
                test_type=TestType.PROPERTY,
                target_function=func.__name__,
                test_code=test_code,
                inputs=[],
                expected_output=None
            )
            
            tests.append(test)
            self.generated_tests.append(test)
        
        return tests
    
    def generate_fuzz_tests(
        self,
        func: Callable,
        num_iterations: int = 100
    ) -> List[GeneratedTest]:
        """Generate fuzz tests"""
        
        tests = []
        sig = inspect.signature(func)
        
        # Generate many random inputs to find edge cases
        for i in range(num_iterations):
            inputs = []
            
            for param_name, param in sig.parameters.items():
                # Generate edge case values
                if param.annotation == int:
                    inputs.append(np.random.choice([
                        0, 1, -1, 2**31-1, -2**31,
                        np.random.randint(-1000000, 1000000)
                    ]))
                elif param.annotation == float:
                    inputs.append(np.random.choice([
                        0.0, 1.0, -1.0, float('inf'), float('-inf'),
                        1e-10, 1e10, np.random.uniform(-1e6, 1e6)
                    ]))
                elif param.annotation == str:
                    inputs.append(np.random.choice([
                        "", " ", "a" * 10000, "\n\t\r",
                        "".join(chr(np.random.randint(0, 128)) for _ in range(100))
                    ]))
                else:
                    inputs.append(None)
            
            try:
                expected = func(*inputs)
                is_valid = True
            except Exception as e:
                expected = f"Exception: {type(e).__name__}"
                is_valid = False
            
            if not is_valid:
                # Found a crash - this is valuable
                test = GeneratedTest(
                    test_id=f"fuzz_{func.__name__}_{i}",
                    test_type=TestType.FUZZ,
                    target_function=func.__name__,
                    test_code=self._generate_test_code(func, inputs, expected, i),
                    inputs=inputs,
                    expected_output=expected,
                    is_valid=False
                )
                tests.append(test)
                self.generated_tests.append(test)
        
        return tests
    
    def generate_mutation_tests(
        self,
        func: Callable,
        test_inputs: List[Tuple]
    ) -> List[GeneratedTest]:
        """Generate mutation tests"""
        
        tests = []
        
        # Get original outputs
        original_outputs = []
        for inputs in test_inputs:
            try:
                output = func(*inputs)
                original_outputs.append(output)
            except:
                original_outputs.append(None)
        
        # Generate mutant-killing tests
        for i, (inputs, expected) in enumerate(zip(test_inputs, original_outputs)):
            if expected is None:
                continue
            
            test_code = f'''
def test_{func.__name__}_mutation_{i}():
    """Mutation test for {func.__name__}"""
    result = {func.__name__}(*{repr(inputs)})
    # This test should fail if the function is mutated
    assert result == {repr(expected)}
'''
            
            test = GeneratedTest(
                test_id=f"mutation_{func.__name__}_{i}",
                test_type=TestType.MUTATION,
                target_function=func.__name__,
                test_code=test_code,
                inputs=list(inputs),
                expected_output=expected
            )
            
            tests.append(test)
            self.generated_tests.append(test)
        
        return tests
    
    def export_tests(self, output_file: str):
        """Export generated tests to file"""
        
        with open(output_file, 'w') as f:
            f.write("# Auto-generated tests\n")
            f.write("import pytest\n\n")
            
            for test in self.generated_tests:
                if test.is_valid:
                    f.write(test.test_code)
                    f.write("\n")
        
        logger.info(f"Exported {len(self.generated_tests)} tests to {output_file}")
    
    def get_report(self) -> Dict[str, Any]:
        """Get test generation report"""
        
        return {
            'total_generated': len(self.generated_tests),
            'by_type': {
                t.value: sum(1 for test in self.generated_tests if test.test_type == t)
                for t in TestType
            },
            'valid_tests': sum(1 for t in self.generated_tests if t.is_valid),
            'crash_tests': sum(1 for t in self.generated_tests if not t.is_valid)
        }


# =============================================================================
# INTEGRATED INFRASTRUCTURE SYSTEM
# =============================================================================

class IntegratedInfrastructureSystem:
    """
    Integrated Infrastructure System
    
    Combines all infrastructure components for
    comprehensive system management.
    """
    
    def __init__(self):
        self.dependency_manager = DependencyManager()
        self.self_healing = SelfHealingInfrastructure()
        self.profiler = PerformanceProfiler()
        self.test_generator = AutomatedTestGenerator()
        
        logger.info("IntegratedInfrastructureSystem initialized")
    
    async def full_system_check(self) -> Dict[str, Any]:
        """Run full system check"""
        
        results = {}
        
        # 1. Dependency check
        self.dependency_manager.scan_dependencies()
        compatibility_issues = self.dependency_manager.validate_compatibility()
        results['dependencies'] = {
            'total': len(self.dependency_manager.dependencies),
            'issues': compatibility_issues
        }
        
        # 2. Health check
        health_results = await self.self_healing.run_all_checks()
        results['health'] = {
            'overall': self.self_healing.overall_status.value,
            'checks': {k: v.value for k, v in health_results.items()}
        }
        
        # 3. Performance check
        bottlenecks = self.profiler.analyze_bottlenecks()
        results['performance'] = {
            'bottlenecks': len(bottlenecks),
            'suggestions': len(self.profiler.suggestions)
        }
        
        # 4. Overall status
        is_healthy = (
            len(compatibility_issues) == 0 and
            self.self_healing.overall_status == HealthStatus.HEALTHY
        )
        
        results['overall_healthy'] = is_healthy
        
        return results
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure report"""
        
        return {
            'dependencies': self.dependency_manager.get_report(),
            'health': self.self_healing.get_status(),
            'performance': self.profiler.get_report(),
            'testing': self.test_generator.get_report()
        }


# Convenience functions
def create_infrastructure_system() -> IntegratedInfrastructureSystem:
    """Create integrated infrastructure system"""
    return IntegratedInfrastructureSystem()
