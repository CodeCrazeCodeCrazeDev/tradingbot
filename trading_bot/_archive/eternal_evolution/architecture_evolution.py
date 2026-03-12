"""
Architecture Evolution Engine - Self-Evolving System Architecture
=================================================================

Continuously evolves and improves system architecture:
- Code structure and organization
- Error handling and recovery
- Performance optimization
- Memory management
- Latency reduction
- Stability improvements
- Fault tolerance

Learns from system behavior to find better architectural patterns.
"""

import asyncio
import logging
import json
import time
import psutil
import gc
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import traceback
import threading

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class StabilityMetric(Enum):
    """Metrics for measuring system stability"""
    UPTIME = "uptime"
    ERROR_RATE = "error_rate"
    LATENCY_P50 = "latency_p50"
    LATENCY_P99 = "latency_p99"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    THROUGHPUT = "throughput"
    RECOVERY_TIME = "recovery_time"
    CRASH_COUNT = "crash_count"
    DEADLOCK_COUNT = "deadlock_count"


class ArchitecturePattern(Enum):
    """Architectural patterns that can be evolved"""
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    BULKHEAD = "bulkhead"
    TIMEOUT = "timeout"
    CACHE = "cache"
    RATE_LIMITER = "rate_limiter"
    HEALTH_CHECK = "health_check"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    LOAD_BALANCER = "load_balancer"
    FAILOVER = "failover"


@dataclass
class ArchitectureEvolutionResult:
    """Result of an architecture evolution"""
    pattern: str
    change_type: str  # enable, disable, tune
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    improvement_expected: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    applied: bool = False


@dataclass
class SystemHealthSnapshot:
    """Snapshot of system health"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    thread_count: int
    open_files: int
    latency_ms: float
    error_count: int
    uptime_seconds: float
    gc_collections: Tuple[int, int, int]


class ArchitectureEvolutionEngine:
    """
    Self-Evolving Architecture Engine
    
    Continuously monitors and improves system architecture by:
    1. Tracking system health metrics
    2. Detecting performance bottlenecks
    3. Automatically tuning architectural patterns
    4. Implementing self-healing mechanisms
    5. Optimizing resource usage
    
    The goal: Maximum stability, minimum latency, optimal resource usage.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.start_time = datetime.now()
        
        # Architectural pattern configurations (evolvable)
        self.patterns = {
            ArchitecturePattern.CIRCUIT_BREAKER: {
                'enabled': True,
                'failure_threshold': 5,
                'recovery_timeout': 30,
                'half_open_requests': 3
            },
            ArchitecturePattern.RETRY_WITH_BACKOFF: {
                'enabled': True,
                'max_retries': 3,
                'initial_delay': 1.0,
                'max_delay': 30.0,
                'exponential_base': 2.0
            },
            ArchitecturePattern.BULKHEAD: {
                'enabled': True,
                'max_concurrent': 10,
                'queue_size': 100,
                'timeout': 30
            },
            ArchitecturePattern.TIMEOUT: {
                'enabled': True,
                'default_timeout': 30,
                'critical_timeout': 5,
                'non_critical_timeout': 60
            },
            ArchitecturePattern.CACHE: {
                'enabled': True,
                'max_size': 10000,
                'ttl_seconds': 300,
                'eviction_policy': 'lru'
            },
            ArchitecturePattern.RATE_LIMITER: {
                'enabled': True,
                'requests_per_second': 100,
                'burst_size': 20,
                'cooldown_seconds': 1
            },
            ArchitecturePattern.HEALTH_CHECK: {
                'enabled': True,
                'interval_seconds': 30,
                'timeout_seconds': 5,
                'unhealthy_threshold': 3
            },
            ArchitecturePattern.GRACEFUL_DEGRADATION: {
                'enabled': True,
                'degradation_threshold': 0.8,  # 80% resource usage
                'features_to_disable': ['non_critical_logging', 'analytics']
            },
            ArchitecturePattern.LOAD_BALANCER: {
                'enabled': False,
                'algorithm': 'round_robin',
                'health_check_interval': 10
            },
            ArchitecturePattern.FAILOVER: {
                'enabled': True,
                'failover_timeout': 10,
                'max_failovers': 3,
                'cooldown_period': 60
            }
        }
        
        # Pattern bounds for evolution
        self.pattern_bounds = {
            'failure_threshold': (2, 20),
            'recovery_timeout': (10, 120),
            'max_retries': (1, 10),
            'initial_delay': (0.1, 5.0),
            'max_delay': (10, 120),
            'max_concurrent': (5, 50),
            'queue_size': (50, 500),
            'default_timeout': (10, 120),
            'max_size': (1000, 100000),
            'ttl_seconds': (60, 3600),
            'requests_per_second': (10, 1000),
            'interval_seconds': (10, 120)
        }
        
        # Health tracking
        self.health_history: List[SystemHealthSnapshot] = []
        self.error_log: List[Dict] = []
        self.latency_samples: List[float] = []
        
        # Evolution tracking
        self.evolution_history: List[ArchitectureEvolutionResult] = []
        
        # Circuit breaker states
        self.circuit_states: Dict[str, Dict] = {}
        
        # Performance baselines
        self.baselines = {
            'latency_p50': None,
            'latency_p99': None,
            'memory_baseline': None,
            'cpu_baseline': None
        }
        
        # Statistics
        self.stats = {
            'evolutions_performed': 0,
            'patterns_tuned': 0,
            'errors_recovered': 0,
            'circuit_breaks': 0,
            'graceful_degradations': 0,
            'health_checks_passed': 0,
            'health_checks_failed': 0
        }
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'architecture_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        # Start background monitoring
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self._monitor_thread.start()
        
        self._load_state()
        logger.info("Architecture Evolution Engine initialized")
    
    def _background_monitor(self):
        """Background monitoring thread"""
        while self._monitoring:
            try:
                self._take_health_snapshot()
                time.sleep(self.patterns[ArchitecturePattern.HEALTH_CHECK]['interval_seconds'])
            except Exception as e:
                logger.error(f"Background monitor error: {e}")
                time.sleep(30)
    
    def _take_health_snapshot(self) -> SystemHealthSnapshot:
        """Take a snapshot of system health"""
        process = psutil.Process()
        
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.now(),
            cpu_percent=process.cpu_percent(),
            memory_percent=process.memory_percent(),
            memory_mb=process.memory_info().rss / (1024 * 1024),
            thread_count=threading.active_count(),
            open_files=len(process.open_files()) if hasattr(process, 'open_files') else 0,
            latency_ms=self._get_average_latency(),
            error_count=len(self.error_log),
            uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
            gc_collections=gc.get_count()
        )
        
        self.health_history.append(snapshot)
        
        # Trim history
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-500:]
        
        # Check for issues
        self._check_health_issues(snapshot)
        
        return snapshot
    
    def _get_average_latency(self) -> float:
        """Get average latency from recent samples"""
        if not self.latency_samples:
            return 0
        return sum(self.latency_samples[-100:]) / len(self.latency_samples[-100:])
    
    def _check_health_issues(self, snapshot: SystemHealthSnapshot):
        """Check for health issues and trigger evolution if needed"""
        issues = []
        
        # High memory usage
        if snapshot.memory_percent > 80:
            issues.append(('memory', snapshot.memory_percent))
            self._trigger_graceful_degradation('high_memory')
        
        # High CPU usage
        if snapshot.cpu_percent > 90:
            issues.append(('cpu', snapshot.cpu_percent))
            self._trigger_graceful_degradation('high_cpu')
        
        # High latency
        if snapshot.latency_ms > 1000:
            issues.append(('latency', snapshot.latency_ms))
        
        # Many errors
        recent_errors = [e for e in self.error_log 
                       if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(minutes=5)]
        if len(recent_errors) > 10:
            issues.append(('errors', len(recent_errors)))
        
        if issues:
            logger.warning(f"Health issues detected: {issues}")
            asyncio.create_task(self._evolve_for_issues(issues))
    
    def _trigger_graceful_degradation(self, reason: str):
        """Trigger graceful degradation"""
        if not self.patterns[ArchitecturePattern.GRACEFUL_DEGRADATION]['enabled']:
            return
        
        self.stats['graceful_degradations'] += 1
        logger.warning(f"Graceful degradation triggered: {reason}")
        
        # Reduce non-critical operations
        features = self.patterns[ArchitecturePattern.GRACEFUL_DEGRADATION]['features_to_disable']
        for feature in features:
            logger.info(f"Disabling feature: {feature}")
    
    def record_latency(self, latency_ms: float):
        """Record a latency sample"""
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > 10000:
            self.latency_samples = self.latency_samples[-5000:]
    
    def record_error(self, error: Exception, context: Dict[str, Any]):
        """Record an error for learning"""
        self.error_log.append({
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context,
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        })
        
        # Trim error log
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-500:]
        
        # Check circuit breaker
        self._check_circuit_breaker(context.get('service', 'default'), error)
    
    def _check_circuit_breaker(self, service: str, error: Exception):
        """Check and update circuit breaker state"""
        if not self.patterns[ArchitecturePattern.CIRCUIT_BREAKER]['enabled']:
            return
        
        if service not in self.circuit_states:
            self.circuit_states[service] = {
                'state': 'closed',
                'failures': 0,
                'last_failure': None,
                'last_success': None
            }
        
        state = self.circuit_states[service]
        state['failures'] += 1
        state['last_failure'] = datetime.now()
        
        threshold = self.patterns[ArchitecturePattern.CIRCUIT_BREAKER]['failure_threshold']
        
        if state['failures'] >= threshold and state['state'] == 'closed':
            state['state'] = 'open'
            self.stats['circuit_breaks'] += 1
            logger.warning(f"Circuit breaker OPEN for service: {service}")
    
    def is_circuit_open(self, service: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if service not in self.circuit_states:
            return False
        
        state = self.circuit_states[service]
        
        if state['state'] == 'open':
            # Check if recovery timeout has passed
            recovery_timeout = self.patterns[ArchitecturePattern.CIRCUIT_BREAKER]['recovery_timeout']
            if state['last_failure']:
                elapsed = (datetime.now() - state['last_failure']).total_seconds()
                if elapsed > recovery_timeout:
                    state['state'] = 'half-open'
                    return False
            return True
        
        return False
    
    def record_success(self, service: str):
        """Record a successful operation"""
        if service in self.circuit_states:
            state = self.circuit_states[service]
            state['last_success'] = datetime.now()
            
            if state['state'] == 'half-open':
                state['state'] = 'closed'
                state['failures'] = 0
                logger.info(f"Circuit breaker CLOSED for service: {service}")
    
    async def evolve(self) -> List[ArchitectureEvolutionResult]:
        """Run architecture evolution cycle"""
        logger.info("Starting architecture evolution cycle...")
        results = []
        
        # Analyze current health
        health_analysis = self._analyze_health()
        
        # Evolve patterns based on analysis
        for pattern, config in self.patterns.items():
            if not config['enabled']:
                continue
            
            result = await self._evolve_pattern(pattern, health_analysis)
            if result:
                results.append(result)
                self.evolution_history.append(result)
        
        self.stats['evolutions_performed'] += 1
        self._save_state()
        
        logger.info(f"Architecture evolution complete: {len(results)} changes")
        return results
    
    async def _evolve_for_issues(self, issues: List[Tuple[str, float]]):
        """Evolve architecture to address specific issues"""
        for issue_type, value in issues:
            if issue_type == 'memory':
                # Reduce cache size
                await self._tune_pattern_param(
                    ArchitecturePattern.CACHE, 'max_size', 'decrease'
                )
                # Force garbage collection
                gc.collect()
            
            elif issue_type == 'cpu':
                # Reduce concurrent operations
                await self._tune_pattern_param(
                    ArchitecturePattern.BULKHEAD, 'max_concurrent', 'decrease'
                )
                # Increase rate limiting
                await self._tune_pattern_param(
                    ArchitecturePattern.RATE_LIMITER, 'requests_per_second', 'decrease'
                )
            
            elif issue_type == 'latency':
                # Reduce timeouts to fail faster
                await self._tune_pattern_param(
                    ArchitecturePattern.TIMEOUT, 'default_timeout', 'decrease'
                )
                # Increase cache TTL
                await self._tune_pattern_param(
                    ArchitecturePattern.CACHE, 'ttl_seconds', 'increase'
                )
            
            elif issue_type == 'errors':
                # Increase retry attempts
                await self._tune_pattern_param(
                    ArchitecturePattern.RETRY_WITH_BACKOFF, 'max_retries', 'increase'
                )
                # Lower circuit breaker threshold
                await self._tune_pattern_param(
                    ArchitecturePattern.CIRCUIT_BREAKER, 'failure_threshold', 'decrease'
                )
    
    async def _tune_pattern_param(
        self,
        pattern: ArchitecturePattern,
        param: str,
        direction: str
    ) -> Optional[ArchitectureEvolutionResult]:
        """Tune a specific pattern parameter"""
        if param not in self.pattern_bounds:
            return None
        
        config = self.patterns[pattern]
        if param not in config:
            return None
        
        current_value = config[param]
        bounds = self.pattern_bounds[param]
        
        # Calculate adjustment
        adjustment = (bounds[1] - bounds[0]) * 0.1
        if direction == 'decrease':
            adjustment = -adjustment
        
        new_value = current_value + adjustment
        new_value = max(bounds[0], min(bounds[1], new_value))
        
        if abs(new_value - current_value) < 0.001:
            return None
        
        # Apply change
        old_config = config.copy()
        config[param] = new_value
        
        self.stats['patterns_tuned'] += 1
        
        return ArchitectureEvolutionResult(
            pattern=pattern.value,
            change_type='tune',
            old_config={param: current_value},
            new_config={param: new_value},
            improvement_expected=0.1,
            reasoning=f"Adjusted {param} {direction} to address system issues",
            applied=True
        )
    
    def _analyze_health(self) -> Dict[str, Any]:
        """Analyze recent health data"""
        if not self.health_history:
            return {}
        
        recent = self.health_history[-100:]
        
        return {
            'avg_cpu': sum(h.cpu_percent for h in recent) / len(recent),
            'avg_memory': sum(h.memory_percent for h in recent) / len(recent),
            'avg_latency': sum(h.latency_ms for h in recent) / len(recent),
            'max_memory': max(h.memory_percent for h in recent),
            'max_cpu': max(h.cpu_percent for h in recent),
            'error_rate': len(self.error_log) / max(len(recent), 1),
            'uptime': recent[-1].uptime_seconds if recent else 0
        }
    
    async def _evolve_pattern(
        self,
        pattern: ArchitecturePattern,
        health: Dict[str, Any]
    ) -> Optional[ArchitectureEvolutionResult]:
        """Evolve a specific pattern based on health analysis"""
        config = self.patterns[pattern]
        
        # Pattern-specific evolution logic
        if pattern == ArchitecturePattern.CIRCUIT_BREAKER:
            # High error rate -> lower threshold
            if health.get('error_rate', 0) > 0.1:
                return await self._tune_pattern_param(pattern, 'failure_threshold', 'decrease')
        
        elif pattern == ArchitecturePattern.CACHE:
            # High memory -> reduce cache
            if health.get('avg_memory', 0) > 70:
                return await self._tune_pattern_param(pattern, 'max_size', 'decrease')
            # Low memory and high latency -> increase cache
            elif health.get('avg_memory', 0) < 50 and health.get('avg_latency', 0) > 500:
                return await self._tune_pattern_param(pattern, 'max_size', 'increase')
        
        elif pattern == ArchitecturePattern.BULKHEAD:
            # High CPU -> reduce concurrency
            if health.get('avg_cpu', 0) > 80:
                return await self._tune_pattern_param(pattern, 'max_concurrent', 'decrease')
        
        elif pattern == ArchitecturePattern.RATE_LIMITER:
            # Stable system -> can increase throughput
            if health.get('avg_cpu', 0) < 50 and health.get('error_rate', 0) < 0.01:
                return await self._tune_pattern_param(pattern, 'requests_per_second', 'increase')
        
        return None
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get current retry configuration"""
        return self.patterns[ArchitecturePattern.RETRY_WITH_BACKOFF].copy()
    
    def get_timeout(self, operation_type: str = 'default') -> float:
        """Get timeout for an operation type"""
        config = self.patterns[ArchitecturePattern.TIMEOUT]
        
        if operation_type == 'critical':
            return config['critical_timeout']
        elif operation_type == 'non_critical':
            return config['non_critical_timeout']
        return config['default_timeout']
    
    def should_cache(self, key: str) -> bool:
        """Check if caching is enabled"""
        return self.patterns[ArchitecturePattern.CACHE]['enabled']
    
    def get_cache_ttl(self) -> int:
        """Get cache TTL"""
        return self.patterns[ArchitecturePattern.CACHE]['ttl_seconds']
    
    def is_rate_limited(self) -> bool:
        """Check if rate limiting should be applied"""
        return self.patterns[ArchitecturePattern.RATE_LIMITER]['enabled']
    
    def get_rate_limit(self) -> float:
        """Get current rate limit"""
        return self.patterns[ArchitecturePattern.RATE_LIMITER]['requests_per_second']
    
    def _save_state(self):
        """Save evolution state"""
        state = {
            'patterns': {k.value: v for k, v in self.patterns.items()},
            'stats': self.stats,
            'baselines': self.baselines,
            'circuit_states': {
                k: {**v, 'last_failure': v['last_failure'].isoformat() if v['last_failure'] else None,
                    'last_success': v['last_success'].isoformat() if v['last_success'] else None}
                for k, v in self.circuit_states.items()
            }
        }
        
        state_file = self.state_path / 'architecture_evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'architecture_evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore patterns
                for k, v in state.get('patterns', {}).items():
                    pattern = ArchitecturePattern(k)
                    self.patterns[pattern] = v
                
                self.stats = state.get('stats', self.stats)
                self.baselines = state.get('baselines', self.baselines)
                
                logger.info("Loaded previous architecture evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load architecture evolution state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        health = self._analyze_health()
        
        return {
            **self.stats,
            'current_health': health,
            'patterns_enabled': sum(1 for p in self.patterns.values() if p.get('enabled')),
            'circuit_breakers_open': sum(1 for s in self.circuit_states.values() if s['state'] == 'open'),
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'evolutions_applied': len(self.evolution_history)
        }
    
    def shutdown(self):
        """Shutdown the engine"""
        self._monitoring = False
        self._save_state()
        logger.info("Architecture Evolution Engine shutdown")
