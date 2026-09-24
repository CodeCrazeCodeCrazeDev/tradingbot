"""
Comprehensive Sandbox Controls
================================

All sandbox enforcement mechanisms:
1. Output Gate - Controls what data can leave the sandbox
2. Execution Isolation - Complete process isolation
3. Data Integrity Firewall - Protects data access
4. Resource Control - CPU, memory, disk, network limits
5. Dependency Freezer - Locks dependencies for reproducibility
6. Experiment Registry - Tracks all experiments
7. Scientific Reproducibility - Ensures experiments can be reproduced
8. Network Firewall - Controls network access
9. Experiment Scheduler - Manages experiment execution
10. Result Evaluator - Validates experiment results

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class OutputType(Enum):
    """Types of outputs from sandbox."""
    STDOUT = "stdout"
    STDERR = "stderr"
    FILE = "file"
    NETWORK = "network"
    METRICS = "metrics"
    LOGS = "logs"


class OutputSensitivity(Enum):
    """Sensitivity levels for outputs."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class OutputGateRule:
    """Rule for output gate filtering."""
    rule_id: str
    output_type: OutputType
    pattern: str  # Regex pattern
    action: str  # 'allow', 'block', 'sanitize', 'log'
    sensitivity: OutputSensitivity
    sanitizer: Optional[Callable] = None
    
    def matches(self, content: str) -> bool:
        """Check if content matches this rule."""
        return bool(re.search(self.pattern, content, re.IGNORECASE))


@dataclass
class OutputGateDecision:
    """Decision made by output gate."""
    allowed: bool
    sanitized_content: Optional[str]
    blocked_reason: Optional[str]
    matched_rules: List[str]
    sensitivity: OutputSensitivity


class OutputGate:
    """
    Controls what data can leave the sandbox.
    
    Prevents:
    - Sensitive data leakage
    - API key exposure
    - PII disclosure
    - Proprietary information leakage
    """
    
    # Sensitive patterns to block/sanitize
    SENSITIVE_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'CARD'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]{20,}', 'API_KEY'),
        (r'password["\']?\s*[:=]\s*["\']?[\w-]+', 'PASSWORD'),
        (r'secret["\']?\s*[:=]\s*["\']?[\w-]+', 'SECRET'),
        (r'token["\']?\s*[:=]\s*["\']?[\w-]{20,}', 'TOKEN'),
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
        (r'Bearer\s+[\w-]+\.[\w-]+\.[\w-]+', 'JWT'),
    ]
    
    def __init__(self):
        self._rules: List[OutputGateRule] = []
        self._blocked_outputs: List[Dict] = []
        self._sanitized_outputs: List[Dict] = []
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default output gate rules."""
        # Block API keys
        self.add_rule(OutputGateRule(
            rule_id="block_api_keys",
            output_type=OutputType.STDOUT,
            pattern=r'api[_-]?key',
            action='sanitize',
            sensitivity=OutputSensitivity.RESTRICTED,
        ))
        
        # Block passwords
        self.add_rule(OutputGateRule(
            rule_id="block_passwords",
            output_type=OutputType.STDOUT,
            pattern=r'password',
            action='sanitize',
            sensitivity=OutputSensitivity.RESTRICTED,
        ))
        
        # Log all file outputs
        self.add_rule(OutputGateRule(
            rule_id="log_file_outputs",
            output_type=OutputType.FILE,
            pattern=r'.*',
            action='log',
            sensitivity=OutputSensitivity.INTERNAL,
        ))
    
    def add_rule(self, rule: OutputGateRule):
        """Add an output gate rule."""
        self._rules.append(rule)
    
    def filter_output(
        self,
        content: str,
        output_type: OutputType,
    ) -> OutputGateDecision:
        """
        Filter output through the gate.
        
        Args:
            content: Output content
            output_type: Type of output
        
        Returns:
            OutputGateDecision
        """
        matched_rules = []
        sanitized_content = content
        blocked = False
        blocked_reason = None
        max_sensitivity = OutputSensitivity.PUBLIC
        
        # Check against all rules
        for rule in self._rules:
            if rule.output_type != output_type:
                continue
            
            if rule.matches(content):
                matched_rules.append(rule.rule_id)
                
                if rule.sensitivity.value > max_sensitivity.value:
                    max_sensitivity = rule.sensitivity
                
                if rule.action == 'block':
                    blocked = True
                    blocked_reason = f"Blocked by rule: {rule.rule_id}"
                    break
                
                elif rule.action == 'sanitize':
                    sanitized_content = self._sanitize_content(sanitized_content)
                
                elif rule.action == 'log':
                    self._log_output(content, rule)
        
        # Apply default sanitization for sensitive patterns
        if not blocked:
            sanitized_content = self._sanitize_content(sanitized_content)
        
        decision = OutputGateDecision(
            allowed=not blocked,
            sanitized_content=sanitized_content if not blocked else None,
            blocked_reason=blocked_reason,
            matched_rules=matched_rules,
            sensitivity=max_sensitivity,
        )
        
        if blocked:
            self._blocked_outputs.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'content_hash': hashlib.sha256(content.encode()).hexdigest(),
                'reason': blocked_reason,
            })
        elif sanitized_content != content:
            self._sanitized_outputs.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'original_hash': hashlib.sha256(content.encode()).hexdigest(),
                'sanitized_hash': hashlib.sha256(sanitized_content.encode()).hexdigest(),
            })
        
        return decision
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize sensitive content."""
        sanitized = content
        
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, f'[{replacement}]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _log_output(self, content: str, rule: OutputGateRule):
        """Log output for audit."""
        logger.info(f"Output logged by rule {rule.rule_id}: {len(content)} bytes")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get output gate statistics."""
        return {
            'total_rules': len(self._rules),
            'blocked_outputs': len(self._blocked_outputs),
            'sanitized_outputs': len(self._sanitized_outputs),
        }


@dataclass
class DependencySnapshot:
    """Snapshot of dependencies for reproducibility."""
    snapshot_id: str
    created_at: datetime
    python_version: str
    packages: Dict[str, str]  # package_name: version
    system_info: Dict[str, str]
    hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'snapshot_id': self.snapshot_id,
            'created_at': self.created_at.isoformat(),
            'python_version': self.python_version,
            'packages': self.packages,
            'system_info': self.system_info,
            'hash': self.hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencySnapshot':
        return cls(
            snapshot_id=data['snapshot_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            python_version=data['python_version'],
            packages=data['packages'],
            system_info=data['system_info'],
            hash=data['hash'],
        )


class DependencyFreezer:
    """
    Freezes dependencies for scientific reproducibility.
    
    Ensures experiments can be exactly reproduced by:
    - Capturing exact package versions
    - Recording Python version
    - Storing system information
    - Creating reproducible environments
    """
    
    def __init__(self, storage_path: str = "dependency_snapshots"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        self._snapshots: Dict[str, DependencySnapshot] = {}
    
    async def create_snapshot(
        self,
        experiment_id: str,
        additional_packages: Optional[List[str]] = None,
    ) -> DependencySnapshot:
        """
        Create a dependency snapshot.
        
        Args:
            experiment_id: Experiment ID
            additional_packages: Additional packages to include
        
        Returns:
            DependencySnapshot
        """
        snapshot_id = f"SNAP-{uuid.uuid4().hex[:12]}"
        
        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Get installed packages
        packages = await self._get_installed_packages()
        
        # Add additional packages if specified
        if additional_packages:
            for pkg in additional_packages:
                if pkg not in packages:
                    packages[pkg] = "latest"
        
        # Get system info
        system_info = {
            'platform': sys.platform,
            'architecture': str(sys.maxsize > 2**32),
        }
        
        # Calculate hash
        snapshot_data = {
            'python_version': python_version,
            'packages': packages,
            'system_info': system_info,
        }
        snapshot_hash = hashlib.sha256(
            json.dumps(snapshot_data, sort_keys=True).encode()
        ).hexdigest()
        
        snapshot = DependencySnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(timezone.utc),
            python_version=python_version,
            packages=packages,
            system_info=system_info,
            hash=snapshot_hash,
        )
        
        self._snapshots[snapshot_id] = snapshot
        
        # Persist
        await self._persist_snapshot(snapshot)
        
        logger.info(f"Created dependency snapshot: {snapshot_id}")
        
        return snapshot
    
    async def _get_installed_packages(self) -> Dict[str, str]:
        """Get installed packages and versions."""
        packages = {}
        
        # Core packages we care about
        core_packages = [
            'numpy', 'pandas', 'scipy', 'sklearn', 'statsmodels',
            'ta', 'talib', 'matplotlib', 'seaborn',
        ]
        
        for pkg in core_packages:
            try:
                # Try to import and get version
                mod = __import__(pkg)
                version = getattr(mod, '__version__', 'unknown')
                packages[pkg] = version
            except ImportError:
                pass
        
        return packages
    
    async def restore_snapshot(
        self,
        snapshot_id: str,
    ) -> bool:
        """
        Restore a dependency snapshot.
        
        Args:
            snapshot_id: Snapshot ID
        
        Returns:
            True if restored successfully
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            # Try to load from disk
            snapshot = await self._load_snapshot(snapshot_id)
        
        if not snapshot:
            return False
        
        logger.info(f"Restoring snapshot {snapshot_id} (Python {snapshot.python_version})")
        
        # In production, this would install exact versions
        # For now, just verify compatibility
        current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        if current_python != snapshot.python_version:
            logger.warning(
                f"Python version mismatch: current={current_python}, "
                f"snapshot={snapshot.python_version}"
            )
        
        return True
    
    async def verify_snapshot(
        self,
        snapshot_id: str,
    ) -> Tuple[bool, List[str]]:
        """
        Verify a snapshot matches current environment.
        
        Args:
            snapshot_id: Snapshot ID
        
        Returns:
            Tuple of (matches, list of differences)
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False, ["Snapshot not found"]
        
        differences = []
        
        # Check Python version
        current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if current_python != snapshot.python_version:
            differences.append(f"Python: {current_python} vs {snapshot.python_version}")
        
        # Check packages
        current_packages = await self._get_installed_packages()
        for pkg, version in snapshot.packages.items():
            if pkg not in current_packages:
                differences.append(f"Missing package: {pkg}")
            elif current_packages[pkg] != version:
                differences.append(f"{pkg}: {current_packages[pkg]} vs {version}")
        
        return len(differences) == 0, differences
    
    async def _persist_snapshot(self, snapshot: DependencySnapshot):
        """Persist snapshot to disk."""
        snapshot_file = self._storage_path / f"{snapshot.snapshot_id}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    async def _load_snapshot(self, snapshot_id: str) -> Optional[DependencySnapshot]:
        """Load snapshot from disk."""
        snapshot_file = self._storage_path / f"{snapshot_id}.json"
        if not snapshot_file.exists():
            return None
        
        with open(snapshot_file, 'r') as f:
            data = json.load(f)
        
        snapshot = DependencySnapshot.from_dict(data)
        self._snapshots[snapshot_id] = snapshot
        
        return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[DependencySnapshot]:
        """Get snapshot by ID."""
        return self._snapshots.get(snapshot_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get freezer statistics."""
        return {
            'total_snapshots': len(self._snapshots),
            'unique_python_versions': len(set(
                s.python_version for s in self._snapshots.values()
            )),
        }


class NetworkFirewall:
    """
    Controls network access from sandbox.
    
    Prevents:
    - Unauthorized external connections
    - Data exfiltration
    - Malicious downloads
    - DNS tunneling
    """
    
    def __init__(self):
        self._allowed_hosts: Set[str] = set()
        self._blocked_hosts: Set[str] = set()
        self._connection_log: List[Dict] = []
        self._blocked_attempts: List[Dict] = []
        
        # Default blocked hosts
        self._blocked_hosts.update([
            'pastebin.com',
            'hastebin.com',
            'transfer.sh',
        ])
    
    def allow_host(self, host: str):
        """Allow a host."""
        self._allowed_hosts.add(host)
        self._blocked_hosts.discard(host)
    
    def block_host(self, host: str):
        """Block a host."""
        self._blocked_hosts.add(host)
        self._allowed_hosts.discard(host)
    
    def check_connection(
        self,
        host: str,
        port: int,
        protocol: str = 'tcp',
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if connection is allowed.
        
        Args:
            host: Target host
            port: Target port
            protocol: Protocol (tcp, udp, http, https)
        
        Returns:
            Tuple of (allowed, reason)
        """
        # Check if explicitly blocked
        if host in self._blocked_hosts:
            reason = f"Host {host} is blocked"
            self._log_blocked_attempt(host, port, protocol, reason)
            return False, reason
        
        # Check if explicitly allowed
        if host in self._allowed_hosts:
            self._log_connection(host, port, protocol, True)
            return True, None
        
        # Default: block all external connections
        reason = "External connections not allowed by default"
        self._log_blocked_attempt(host, port, protocol, reason)
        return False, reason
    
    def _log_connection(
        self,
        host: str,
        port: int,
        protocol: str,
        allowed: bool,
    ):
        """Log connection attempt."""
        self._connection_log.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'host': host,
            'port': port,
            'protocol': protocol,
            'allowed': allowed,
        })
    
    def _log_blocked_attempt(
        self,
        host: str,
        port: int,
        protocol: str,
        reason: str,
    ):
        """Log blocked connection attempt."""
        self._blocked_attempts.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'host': host,
            'port': port,
            'protocol': protocol,
            'reason': reason,
        })
        
        logger.warning(f"Blocked connection to {host}:{port} - {reason}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get firewall statistics."""
        return {
            'allowed_hosts': len(self._allowed_hosts),
            'blocked_hosts': len(self._blocked_hosts),
            'total_connections': len(self._connection_log),
            'blocked_attempts': len(self._blocked_attempts),
        }


@dataclass
class ScheduledExperiment:
    """A scheduled experiment."""
    schedule_id: str
    experiment_id: str
    scheduled_at: datetime
    priority: int
    resource_requirements: Dict[str, Any]
    dependencies: List[str]  # Other experiment IDs that must complete first
    status: str  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExperimentScheduler:
    """
    Schedules and manages experiment execution.
    
    Features:
    - Priority-based scheduling
    - Resource-aware scheduling
    - Dependency management
    - Fair resource allocation
    """
    
    def __init__(self, max_concurrent: int = 5):
        self._max_concurrent = max_concurrent
        self._queue: List[ScheduledExperiment] = []
        self._running: Dict[str, ScheduledExperiment] = {}
        self._completed: List[ScheduledExperiment] = []
        
        self._scheduler_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self):
        """Start the scheduler."""
        self._is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduling_loop())
        logger.info("Experiment scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self._is_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Experiment scheduler stopped")
    
    async def schedule_experiment(
        self,
        experiment_id: str,
        priority: int = 5,
        resource_requirements: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        delay_seconds: int = 0,
    ) -> str:
        """
        Schedule an experiment for execution.
        
        Args:
            experiment_id: Experiment ID
            priority: Priority (1=highest, 10=lowest)
            resource_requirements: Required resources
            dependencies: Experiments that must complete first
            delay_seconds: Delay before execution
        
        Returns:
            Schedule ID
        """
        schedule_id = f"SCHED-{uuid.uuid4().hex[:8]}"
        
        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        
        scheduled = ScheduledExperiment(
            schedule_id=schedule_id,
            experiment_id=experiment_id,
            scheduled_at=scheduled_at,
            priority=priority,
            resource_requirements=resource_requirements or {},
            dependencies=dependencies or [],
            status='pending',
        )
        
        self._queue.append(scheduled)
        self._queue.sort(key=lambda x: (x.priority, x.scheduled_at))
        
        logger.info(f"Scheduled experiment {experiment_id} with priority {priority}")
        
        return schedule_id
    
    async def _scheduling_loop(self):
        """Main scheduling loop."""
        while self._is_running:
            try:
                await self._process_queue()
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    async def _process_queue(self):
        """Process the experiment queue."""
        now = datetime.now(timezone.utc)
        
        # Check if we can run more experiments
        if len(self._running) >= self._max_concurrent:
            return
        
        # Find next experiment to run
        for scheduled in list(self._queue):
            # Check if it's time to run
            if scheduled.scheduled_at > now:
                continue
            
            # Check dependencies
            if not self._dependencies_met(scheduled):
                continue
            
            # Check resources (simplified)
            if not self._resources_available(scheduled):
                continue
            
            # Start experiment
            self._queue.remove(scheduled)
            scheduled.status = 'running'
            scheduled.started_at = now
            self._running[scheduled.schedule_id] = scheduled
            
            logger.info(f"Starting experiment {scheduled.experiment_id}")
            
            # Only run one per iteration
            break
    
    def _dependencies_met(self, scheduled: ScheduledExperiment) -> bool:
        """Check if dependencies are met."""
        for dep_id in scheduled.dependencies:
            # Check if dependency is completed
            completed_ids = [s.experiment_id for s in self._completed]
            if dep_id not in completed_ids:
                return False
        return True
    
    def _resources_available(self, scheduled: ScheduledExperiment) -> bool:
        """Check if resources are available."""
        # Simplified resource check
        # In production, would check actual resource availability
        return True
    
    async def mark_completed(
        self,
        schedule_id: str,
        success: bool,
    ):
        """Mark an experiment as completed."""
        if schedule_id not in self._running:
            return
        
        scheduled = self._running.pop(schedule_id)
        scheduled.status = 'completed' if success else 'failed'
        scheduled.completed_at = datetime.now(timezone.utc)
        
        self._completed.append(scheduled)
        
        logger.info(f"Experiment {scheduled.experiment_id} completed: {scheduled.status}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            'queued': len(self._queue),
            'running': len(self._running),
            'completed': len(self._completed),
            'max_concurrent': self._max_concurrent,
        }


@dataclass
class EvaluationResult:
    """Result of experiment evaluation."""
    evaluation_id: str
    experiment_id: str
    evaluated_at: datetime
    
    # Validation
    is_valid: bool
    validation_errors: List[str]
    
    # Reproducibility
    is_reproducible: bool
    reproducibility_score: float
    
    # Statistical Significance
    is_significant: bool
    p_value: Optional[float]
    confidence_interval: Optional[Tuple[float, float]]
    
    # Quality Metrics
    quality_score: float
    completeness_score: float
    
    # Recommendations
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evaluation_id': self.evaluation_id,
            'experiment_id': self.experiment_id,
            'evaluated_at': self.evaluated_at.isoformat(),
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors,
            'is_reproducible': self.is_reproducible,
            'reproducibility_score': self.reproducibility_score,
            'is_significant': self.is_significant,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'quality_score': self.quality_score,
            'completeness_score': self.completeness_score,
            'recommendations': self.recommendations,
        }


class ResultEvaluator:
    """
    Evaluates experiment results for scientific validity.
    
    Checks:
    - Statistical significance
    - Reproducibility
    - Data quality
    - Result completeness
    - Scientific rigor
    """
    
    def __init__(self):
        self._evaluations: Dict[str, EvaluationResult] = {}
    
    async def evaluate(
        self,
        experiment_id: str,
        results: Dict[str, Any],
        expected_metrics: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """
        Evaluate experiment results.
        
        Args:
            experiment_id: Experiment ID
            results: Experiment results
            expected_metrics: Expected metrics to validate
        
        Returns:
            EvaluationResult
        """
        evaluation_id = f"EVAL-{uuid.uuid4().hex[:8]}"
        
        # Validation
        is_valid, validation_errors = self._validate_results(results, expected_metrics)
        
        # Reproducibility
        is_reproducible, reproducibility_score = self._check_reproducibility(results)
        
        # Statistical significance
        is_significant, p_value, ci = self._check_significance(results)
        
        # Quality metrics
        quality_score = self._calculate_quality_score(results)
        completeness_score = self._calculate_completeness(results, expected_metrics)
        
        # Recommendations
        recommendations = self._generate_recommendations(
            results, validation_errors, quality_score, completeness_score
        )
        
        evaluation = EvaluationResult(
            evaluation_id=evaluation_id,
            experiment_id=experiment_id,
            evaluated_at=datetime.now(timezone.utc),
            is_valid=is_valid,
            validation_errors=validation_errors,
            is_reproducible=is_reproducible,
            reproducibility_score=reproducibility_score,
            is_significant=is_significant,
            p_value=p_value,
            confidence_interval=ci,
            quality_score=quality_score,
            completeness_score=completeness_score,
            recommendations=recommendations,
        )
        
        self._evaluations[evaluation_id] = evaluation
        
        logger.info(
            f"Evaluated experiment {experiment_id}: "
            f"valid={is_valid}, reproducible={is_reproducible}, "
            f"significant={is_significant}, quality={quality_score:.2f}"
        )
        
        return evaluation
    
    def _validate_results(
        self,
        results: Dict[str, Any],
        expected_metrics: Optional[List[str]],
    ) -> Tuple[bool, List[str]]:
        """Validate results structure and content."""
        errors = []
        
        # Check for required fields
        if not results:
            errors.append("Results are empty")
            return False, errors
        
        # Check for expected metrics
        if expected_metrics:
            for metric in expected_metrics:
                if metric not in results:
                    errors.append(f"Missing expected metric: {metric}")
        
        # Check for NaN or infinite values
        for key, value in results.items():
            if isinstance(value, (int, float)):
                if value != value:  # NaN check
                    errors.append(f"NaN value in {key}")
                elif abs(value) == float('inf'):
                    errors.append(f"Infinite value in {key}")
        
        return len(errors) == 0, errors
    
    def _check_reproducibility(
        self,
        results: Dict[str, Any],
    ) -> Tuple[bool, float]:
        """Check if results are reproducible."""
        # Check for random seed
        has_seed = 'random_seed' in results or 'seed' in results
        
        # Check for version info
        has_versions = 'python_version' in results or 'package_versions' in results
        
        # Check for timestamp
        has_timestamp = 'timestamp' in results or 'executed_at' in results
        
        # Calculate score
        score = 0.0
        if has_seed:
            score += 0.4
        if has_versions:
            score += 0.3
        if has_timestamp:
            score += 0.3
        
        is_reproducible = score >= 0.7
        
        return is_reproducible, score
    
    def _check_significance(
        self,
        results: Dict[str, Any],
    ) -> Tuple[bool, Optional[float], Optional[Tuple[float, float]]]:
        """Check statistical significance."""
        p_value = results.get('p_value')
        ci = results.get('confidence_interval')
        
        if p_value is not None:
            is_significant = p_value < 0.05
        else:
            is_significant = False
        
        return is_significant, p_value, ci
    
    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall quality score."""
        score = 0.0
        
        # Check for key metrics
        quality_metrics = [
            'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
            'win_rate', 'profit_factor', 'total_return'
        ]
        
        present_metrics = sum(1 for m in quality_metrics if m in results)
        score += (present_metrics / len(quality_metrics)) * 0.5
        
        # Check for statistical tests
        if 'p_value' in results:
            score += 0.2
        if 'confidence_interval' in results:
            score += 0.2
        
        # Check for metadata
        if 'execution_time' in results:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_completeness(
        self,
        results: Dict[str, Any],
        expected_metrics: Optional[List[str]],
    ) -> float:
        """Calculate completeness score."""
        if not expected_metrics:
            return 1.0
        
        present = sum(1 for m in expected_metrics if m in results)
        return present / len(expected_metrics)
    
    def _generate_recommendations(
        self,
        results: Dict[str, Any],
        validation_errors: List[str],
        quality_score: float,
        completeness_score: float,
    ) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        if validation_errors:
            recommendations.append("Fix validation errors before proceeding")
        
        if quality_score < 0.7:
            recommendations.append("Improve result quality by adding more metrics")
        
        if completeness_score < 0.8:
            recommendations.append("Add missing expected metrics")
        
        if 'random_seed' not in results:
            recommendations.append("Add random seed for reproducibility")
        
        if 'p_value' not in results:
            recommendations.append("Add statistical significance tests")
        
        return recommendations
    
    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Get evaluation by ID."""
        return self._evaluations.get(evaluation_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        total = len(self._evaluations)
        if total == 0:
            return {
                'total_evaluations': 0,
                'valid_rate': 0,
                'reproducible_rate': 0,
                'significant_rate': 0,
                'avg_quality_score': 0,
            }
        
        valid = sum(1 for e in self._evaluations.values() if e.is_valid)
        reproducible = sum(1 for e in self._evaluations.values() if e.is_reproducible)
        significant = sum(1 for e in self._evaluations.values() if e.is_significant)
        avg_quality = sum(e.quality_score for e in self._evaluations.values()) / total
        
        return {
            'total_evaluations': total,
            'valid_rate': valid / total,
            'reproducible_rate': reproducible / total,
            'significant_rate': significant / total,
            'avg_quality_score': avg_quality,
        }
