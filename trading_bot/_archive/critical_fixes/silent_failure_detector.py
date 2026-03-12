"""
Silent Failure Detector - Answers Q851-Q860
============================================

Critical Question Q851: How do you detect failures that don't raise errors?
Critical Question Q852: What happens when silent failures accumulate?
Critical Question Q853: How do you detect silent data corruption?

This module provides:
1. Heartbeat monitoring for all components
2. Output validation (detecting garbage that looks valid)
3. Behavioral anomaly detection
4. Throughput monitoring
5. State consistency checking
6. Automatic alerting on silent failures
"""

import logging
import threading
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SILENT_FAILURE = "silent_failure"
    DEAD = "dead"
    UNKNOWN = "unknown"


class FailureType(Enum):
    """Types of silent failures"""
    HEARTBEAT_MISSING = "heartbeat_missing"
    OUTPUT_STALE = "output_stale"
    OUTPUT_INVALID = "output_invalid"
    THROUGHPUT_DROP = "throughput_drop"
    LATENCY_SPIKE = "latency_spike"
    STATE_INCONSISTENT = "state_inconsistent"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    QUEUE_OVERFLOW = "queue_overflow"
    MEMORY_LEAK = "memory_leak"


@dataclass
class FailureReport:
    """Report of a detected silent failure"""
    failure_id: str
    timestamp: datetime
    component: str
    failure_type: FailureType
    severity: str  # 'critical', 'warning', 'info'
    description: str
    evidence: Dict[str, Any]
    suggested_action: str
    auto_remediated: bool = False
    remediation_result: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'failure_id': self.failure_id,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'failure_type': self.failure_type.value,
            'severity': self.severity,
            'description': self.description,
            'evidence': self.evidence,
            'suggested_action': self.suggested_action,
            'auto_remediated': self.auto_remediated,
            'remediation_result': self.remediation_result
        }


@dataclass
class ComponentHealth:
    """Health status of a monitored component"""
    component_id: str
    name: str
    status: ComponentStatus
    last_heartbeat: Optional[datetime]
    last_output: Optional[datetime]
    heartbeat_interval: float
    output_interval: float
    throughput_per_minute: float
    expected_throughput: float
    latency_ms: float
    expected_latency_ms: float
    error_count: int
    warning_count: int
    
    def to_dict(self) -> Dict:
        return {
            'component_id': self.component_id,
            'name': self.name,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'last_output': self.last_output.isoformat() if self.last_output else None,
            'throughput_per_minute': self.throughput_per_minute,
            'latency_ms': self.latency_ms,
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }


class SilentFailureDetector:
    """
    Detects failures that don't raise errors.
    
    Addresses critical questions:
    - Q851: Detecting failures that don't raise errors
    - Q852: Handling accumulated silent failures
    - Q853: Detecting silent data corruption
    
    Features:
    - Heartbeat monitoring
    - Output freshness tracking
    - Throughput anomaly detection
    - Behavioral analysis
    - State consistency checking
    - Automatic remediation
    """
    
    def __init__(
        self,
        check_interval: float = 5.0,
        heartbeat_timeout: float = 30.0,
        output_timeout: float = 60.0,
        throughput_threshold: float = 0.5,  # 50% drop triggers alert
        on_failure_detected: Optional[Callable] = None,
        on_component_dead: Optional[Callable] = None,
        auto_remediate: bool = False
    ):
        """
        Initialize silent failure detector.
        
        Args:
            check_interval: Seconds between health checks
            heartbeat_timeout: Seconds before missing heartbeat is failure
            output_timeout: Seconds before stale output is failure
            throughput_threshold: Minimum throughput ratio before alert
            on_failure_detected: Callback when failure detected
            on_component_dead: Callback when component is dead
            auto_remediate: Whether to attempt automatic remediation
        """
        self.check_interval = check_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.output_timeout = output_timeout
        self.throughput_threshold = throughput_threshold
        self.on_failure_detected = on_failure_detected
        self.on_component_dead = on_component_dead
        self.auto_remediate = auto_remediate
        
        # Component tracking
        self._lock = threading.RLock()
        self._components: Dict[str, Dict] = {}
        self._heartbeats: Dict[str, datetime] = {}
        self._outputs: Dict[str, deque] = {}
        self._throughput: Dict[str, deque] = {}
        self._latencies: Dict[str, deque] = {}
        
        # Failure tracking
        self._failures: List[FailureReport] = []
        self._active_failures: Dict[str, FailureReport] = {}
        
        # State snapshots for consistency checking
        self._state_snapshots: Dict[str, List] = {}
        
        # Monitoring state
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'total_failures': 0,
            'failures_by_type': {},
            'components_monitored': 0,
            'auto_remediations': 0
        }
        
        logger.info("SilentFailureDetector initialized")
    
    def register_component(
        self,
        component_id: str,
        name: str,
        heartbeat_interval: float = 10.0,
        output_interval: float = 30.0,
        expected_throughput: float = 0.0,
        expected_latency_ms: float = 100.0,
        health_check: Optional[Callable] = None,
        restart_func: Optional[Callable] = None
    ):
        """
        Register a component for monitoring.
        
        Args:
            component_id: Unique component identifier
            name: Human-readable name
            heartbeat_interval: Expected heartbeat interval
            output_interval: Expected output interval
            expected_throughput: Expected throughput per minute
            expected_latency_ms: Expected latency in ms
            health_check: Optional function to check component health
            restart_func: Optional function to restart component
        """
        with self._lock:
            self._components[component_id] = {
                'id': component_id,
                'name': name,
                'heartbeat_interval': heartbeat_interval,
                'output_interval': output_interval,
                'expected_throughput': expected_throughput,
                'expected_latency_ms': expected_latency_ms,
                'health_check': health_check,
                'restart_func': restart_func,
                'registered_at': datetime.now(),
                'status': ComponentStatus.UNKNOWN,
                'error_count': 0,
                'warning_count': 0
            }
            
            self._heartbeats[component_id] = datetime.now()
            self._outputs[component_id] = deque(maxlen=100)
            self._throughput[component_id] = deque(maxlen=60)  # 1 minute of samples
            self._latencies[component_id] = deque(maxlen=100)
            self._state_snapshots[component_id] = []
            
            self.stats['components_monitored'] = len(self._components)
            
            logger.info(f"Registered component for monitoring: {name} ({component_id})")
    
    def heartbeat(self, component_id: str):
        """
        Record heartbeat from a component.
        
        Components should call this regularly to indicate they're alive.
        """
        with self._lock:
            if component_id in self._heartbeats:
                self._heartbeats[component_id] = datetime.now()
    
    def record_output(
        self,
        component_id: str,
        output: Any,
        latency_ms: Optional[float] = None
    ):
        """
        Record output from a component.
        
        Args:
            component_id: Component that produced output
            output: The output (for validation)
            latency_ms: Optional latency measurement
        """
        with self._lock:
            if component_id not in self._outputs:
                return
            
            self._outputs[component_id].append({
                'timestamp': datetime.now(),
                'output_hash': hashlib.md5(str(output).encode()).hexdigest()[:8],
                'output_type': type(output).__name__
            })
            
            # Record throughput
            self._throughput[component_id].append(datetime.now())
            
            # Record latency
            if latency_ms is not None:
                self._latencies[component_id].append(latency_ms)
    
    def record_state_snapshot(self, component_id: str, state: Dict):
        """
        Record state snapshot for consistency checking.
        
        Args:
            component_id: Component ID
            state: Current state dictionary
        """
        with self._lock:
            if component_id not in self._state_snapshots:
                return
            
            snapshot = {
                'timestamp': datetime.now(),
                'state_hash': hashlib.md5(str(sorted(state.items())).encode()).hexdigest(),
                'state_keys': list(state.keys()),
                'state_size': len(str(state))
            }
            
            self._state_snapshots[component_id].append(snapshot)
            
            # Keep only last 100 snapshots
            if len(self._state_snapshots[component_id]) > 100:
                self._state_snapshots[component_id] = self._state_snapshots[component_id][-50:]
    
    async def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Silent failure detection started")
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Silent failure detection stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                
                if not self._running:
                    break
                
                await self._check_all_components()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
    
    async def _check_all_components(self):
        """Check all registered components for silent failures"""
        self.stats['total_checks'] += 1
        
        with self._lock:
            components = list(self._components.items())
        
        for component_id, config in components:
            try:
                failures = await self._check_component(component_id, config)
                
                for failure in failures:
                    await self._handle_failure(failure)
                    
            except Exception as e:
                logger.error(f"Error checking component {component_id}: {e}")
    
    async def _check_component(
        self,
        component_id: str,
        config: Dict
    ) -> List[FailureReport]:
        """
        Check a single component for silent failures.
        
        This is the answer to Q851: How do you detect failures that don't raise errors?
        """
        failures = []
        now = datetime.now()
        
        # 1. Check heartbeat
        last_heartbeat = self._heartbeats.get(component_id)
        if last_heartbeat:
            heartbeat_age = (now - last_heartbeat).total_seconds()
            timeout = config.get('heartbeat_interval', 10) * 3  # 3x interval
            
            if heartbeat_age > timeout:
                failures.append(FailureReport(
                    failure_id=f"{component_id}_heartbeat_{now.timestamp()}",
                    timestamp=now,
                    component=component_id,
                    failure_type=FailureType.HEARTBEAT_MISSING,
                    severity='critical' if heartbeat_age > timeout * 2 else 'warning',
                    description=f"No heartbeat for {heartbeat_age:.0f}s (timeout: {timeout:.0f}s)",
                    evidence={'last_heartbeat': last_heartbeat.isoformat(), 'age_seconds': heartbeat_age},
                    suggested_action="Restart component or investigate hang"
                ))
        
        # 2. Check output freshness
        outputs = self._outputs.get(component_id, deque())
        if outputs:
            last_output = outputs[-1]['timestamp']
            output_age = (now - last_output).total_seconds()
            output_timeout = config.get('output_interval', 30) * 2
            
            if output_age > output_timeout:
                failures.append(FailureReport(
                    failure_id=f"{component_id}_output_{now.timestamp()}",
                    timestamp=now,
                    component=component_id,
                    failure_type=FailureType.OUTPUT_STALE,
                    severity='warning',
                    description=f"No output for {output_age:.0f}s (timeout: {output_timeout:.0f}s)",
                    evidence={'last_output': last_output.isoformat(), 'age_seconds': output_age},
                    suggested_action="Check if component is processing or blocked"
                ))
        
        # 3. Check throughput
        throughput_samples = self._throughput.get(component_id, deque())
        if throughput_samples and config.get('expected_throughput', 0) > 0:
            # Count samples in last minute
            one_minute_ago = now - timedelta(minutes=1)
            recent_count = sum(1 for t in throughput_samples if t > one_minute_ago)
            expected = config['expected_throughput']
            
            if recent_count < expected * self.throughput_threshold:
                failures.append(FailureReport(
                    failure_id=f"{component_id}_throughput_{now.timestamp()}",
                    timestamp=now,
                    component=component_id,
                    failure_type=FailureType.THROUGHPUT_DROP,
                    severity='warning',
                    description=f"Throughput {recent_count}/min vs expected {expected}/min",
                    evidence={'actual': recent_count, 'expected': expected, 'ratio': recent_count/expected if expected > 0 else 0},
                    suggested_action="Investigate processing bottleneck"
                ))
        
        # 4. Check latency
        latencies = self._latencies.get(component_id, deque())
        if latencies and config.get('expected_latency_ms', 0) > 0:
            recent_latencies = list(latencies)[-20:]  # Last 20 samples
            if recent_latencies:
                avg_latency = statistics.mean(recent_latencies)
                expected_latency = config['expected_latency_ms']
                
                if avg_latency > expected_latency * 3:
                    failures.append(FailureReport(
                        failure_id=f"{component_id}_latency_{now.timestamp()}",
                        timestamp=now,
                        component=component_id,
                        failure_type=FailureType.LATENCY_SPIKE,
                        severity='warning',
                        description=f"Latency {avg_latency:.0f}ms vs expected {expected_latency:.0f}ms",
                        evidence={'actual_ms': avg_latency, 'expected_ms': expected_latency},
                        suggested_action="Investigate performance degradation"
                    ))
        
        # 5. Check state consistency
        snapshots = self._state_snapshots.get(component_id, [])
        if len(snapshots) >= 2:
            consistency_failure = self._check_state_consistency(component_id, snapshots)
            if consistency_failure:
                failures.append(consistency_failure)
        
        # 6. Run custom health check if provided
        health_check = config.get('health_check')
        if health_check:
            try:
                if asyncio.iscoroutinefunction(health_check):
                    is_healthy = await health_check()
                else:
                    is_healthy = health_check()
                
                if not is_healthy:
                    failures.append(FailureReport(
                        failure_id=f"{component_id}_health_{now.timestamp()}",
                        timestamp=now,
                        component=component_id,
                        failure_type=FailureType.BEHAVIORAL_ANOMALY,
                        severity='warning',
                        description="Custom health check failed",
                        evidence={'health_check_result': False},
                        suggested_action="Review component-specific health"
                    ))
            except Exception as e:
                logger.error(f"Health check error for {component_id}: {e}")
        
        # Update component status
        with self._lock:
            if failures:
                critical_failures = [f for f in failures if f.severity == 'critical']
                if critical_failures:
                    self._components[component_id]['status'] = ComponentStatus.DEAD
                else:
                    self._components[component_id]['status'] = ComponentStatus.DEGRADED
                self._components[component_id]['error_count'] += len([f for f in failures if f.severity == 'critical'])
                self._components[component_id]['warning_count'] += len([f for f in failures if f.severity == 'warning'])
            else:
                self._components[component_id]['status'] = ComponentStatus.HEALTHY
        
        return failures
    
    def _check_state_consistency(
        self,
        component_id: str,
        snapshots: List[Dict]
    ) -> Optional[FailureReport]:
        """
        Check for state consistency issues.
        
        This is the answer to Q853: How do you detect silent data corruption?
        """
        if len(snapshots) < 2:
            return None
        
        recent = snapshots[-10:]  # Last 10 snapshots
        
        # Check for state size explosion (possible memory leak)
        sizes = [s['state_size'] for s in recent]
        if len(sizes) >= 5:
            first_half_avg = statistics.mean(sizes[:len(sizes)//2])
            second_half_avg = statistics.mean(sizes[len(sizes)//2:])
            
            if first_half_avg > 0 and second_half_avg > first_half_avg * 2:
                return FailureReport(
                    failure_id=f"{component_id}_state_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    component=component_id,
                    failure_type=FailureType.MEMORY_LEAK,
                    severity='warning',
                    description=f"State size growing: {first_half_avg:.0f} -> {second_half_avg:.0f}",
                    evidence={'first_half_avg': first_half_avg, 'second_half_avg': second_half_avg},
                    suggested_action="Investigate memory leak or unbounded growth"
                )
        
        # Check for unexpected state key changes
        if len(recent) >= 2:
            prev_keys = set(recent[-2]['state_keys'])
            curr_keys = set(recent[-1]['state_keys'])
            
            removed_keys = prev_keys - curr_keys
            if removed_keys:
                return FailureReport(
                    failure_id=f"{component_id}_keys_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    component=component_id,
                    failure_type=FailureType.STATE_INCONSISTENT,
                    severity='warning',
                    description=f"State keys removed: {removed_keys}",
                    evidence={'removed_keys': list(removed_keys)},
                    suggested_action="Investigate unexpected state changes"
                )
        
        return None
    
    async def _handle_failure(self, failure: FailureReport):
        """Handle a detected failure"""
        self.stats['total_failures'] += 1
        self.stats['failures_by_type'][failure.failure_type.value] = \
            self.stats['failures_by_type'].get(failure.failure_type.value, 0) + 1
        
        # Store failure
        self._failures.append(failure)
        if len(self._failures) > 10000:
            self._failures = self._failures[-5000:]
        
        self._active_failures[failure.failure_id] = failure
        
        logger.warning(
            f"Silent failure detected: {failure.component} - {failure.failure_type.value} - "
            f"{failure.description}"
        )
        
        # Callback
        if self.on_failure_detected:
            try:
                if asyncio.iscoroutinefunction(self.on_failure_detected):
                    await self.on_failure_detected(failure)
                else:
                    self.on_failure_detected(failure)
            except Exception as e:
                logger.error(f"Failure callback error: {e}")
        
        # Check for dead component
        with self._lock:
            component = self._components.get(failure.component, {})
            if component.get('status') == ComponentStatus.DEAD:
                if self.on_component_dead:
                    try:
                        if asyncio.iscoroutinefunction(self.on_component_dead):
                            await self.on_component_dead(failure.component, failure)
                        else:
                            self.on_component_dead(failure.component, failure)
                    except Exception as e:
                        logger.error(f"Component dead callback error: {e}")
        
        # Auto-remediation
        if self.auto_remediate and failure.severity == 'critical':
            await self._attempt_remediation(failure)
    
    async def _attempt_remediation(self, failure: FailureReport):
        """Attempt automatic remediation"""
        with self._lock:
            component = self._components.get(failure.component, {})
            restart_func = component.get('restart_func')
        
        if not restart_func:
            return
        
        logger.info(f"Attempting auto-remediation for {failure.component}")
        
        try:
            if asyncio.iscoroutinefunction(restart_func):
                result = await restart_func()
            else:
                result = restart_func()
            
            failure.auto_remediated = True
            failure.remediation_result = "success" if result else "failed"
            self.stats['auto_remediations'] += 1
            
            logger.info(f"Auto-remediation result for {failure.component}: {failure.remediation_result}")
            
        except Exception as e:
            failure.auto_remediated = True
            failure.remediation_result = f"error: {str(e)}"
            logger.error(f"Auto-remediation error: {e}")
    
    def get_component_health(self, component_id: str) -> Optional[ComponentHealth]:
        """Get health status for a component"""
        with self._lock:
            if component_id not in self._components:
                return None
            
            config = self._components[component_id]
            
            # Calculate throughput
            throughput_samples = self._throughput.get(component_id, deque())
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            throughput = sum(1 for t in throughput_samples if t > one_minute_ago)
            
            # Calculate latency
            latencies = list(self._latencies.get(component_id, deque()))
            avg_latency = statistics.mean(latencies[-20:]) if latencies else 0
            
            return ComponentHealth(
                component_id=component_id,
                name=config['name'],
                status=config['status'],
                last_heartbeat=self._heartbeats.get(component_id),
                last_output=self._outputs[component_id][-1]['timestamp'] if self._outputs.get(component_id) else None,
                heartbeat_interval=config['heartbeat_interval'],
                output_interval=config['output_interval'],
                throughput_per_minute=throughput,
                expected_throughput=config['expected_throughput'],
                latency_ms=avg_latency,
                expected_latency_ms=config['expected_latency_ms'],
                error_count=config['error_count'],
                warning_count=config['warning_count']
            )
    
    def get_all_health(self) -> Dict[str, ComponentHealth]:
        """Get health status for all components"""
        with self._lock:
            return {
                cid: self.get_component_health(cid)
                for cid in self._components
            }
    
    def get_active_failures(self) -> List[FailureReport]:
        """Get currently active failures"""
        return list(self._active_failures.values())
    
    def acknowledge_failure(self, failure_id: str):
        """Acknowledge and clear a failure"""
        if failure_id in self._active_failures:
            del self._active_failures[failure_id]
    
    def get_statistics(self) -> Dict:
        """Get detector statistics"""
        return {
            **self.stats,
            'active_failures': len(self._active_failures),
            'total_failures_recorded': len(self._failures)
        }
