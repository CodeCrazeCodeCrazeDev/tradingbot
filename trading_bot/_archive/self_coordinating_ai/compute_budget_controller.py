"""
Compute Budget Controller
==========================

Controls and allocates compute resources for AI experiments and self-programming.
Prevents resource exhaustion and ensures fair allocation.

Features:
1. Budget allocation per experiment/agent
2. Real-time resource monitoring
3. Automatic throttling when limits approached
4. Priority-based scheduling
5. Cost tracking and reporting

Author: AlphaAlgo Trading System
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of compute resources."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"
    API_CALLS = "api_calls"


class AllocationStatus(Enum):
    """Status of resource allocation."""
    PENDING = auto()
    ACTIVE = auto()
    EXHAUSTED = auto()
    EXPIRED = auto()
    REVOKED = auto()


class Priority(Enum):
    """Priority levels for resource allocation."""
    CRITICAL = 1      # Production system needs
    HIGH = 2          # Important experiments
    NORMAL = 3        # Standard experiments
    LOW = 4           # Background tasks
    IDLE = 5          # Only when resources available


@dataclass
class BudgetConfig:
    """Configuration for compute budget controller."""
    # Global Limits
    total_cpu_cores: int = 8
    total_memory_gb: float = 32.0
    total_gpu_memory_gb: float = 16.0
    total_disk_gb: float = 100.0
    total_api_calls_per_hour: int = 10000
    
    # Per-Experiment Limits
    max_cpu_per_experiment: int = 2
    max_memory_per_experiment_gb: float = 4.0
    max_gpu_per_experiment_gb: float = 4.0
    max_disk_per_experiment_gb: float = 10.0
    max_api_calls_per_experiment: int = 1000
    max_runtime_hours: float = 24.0
    
    # Reservation Settings
    production_reserved_cpu: int = 2        # Always reserved for production
    production_reserved_memory_gb: float = 8.0
    emergency_buffer_pct: float = 0.1       # 10% emergency buffer
    
    # Throttling
    throttle_threshold_pct: float = 0.8     # Start throttling at 80%
    hard_limit_pct: float = 0.95            # Hard stop at 95%
    
    # Paths
    budget_log_path: str = "compute_budget_logs"
    
    def get_available_cpu(self) -> int:
        """Get CPU cores available for experiments."""
        return self.total_cpu_cores - self.production_reserved_cpu
    
    def get_available_memory(self) -> float:
        """Get memory available for experiments."""
        return self.total_memory_gb - self.production_reserved_memory_gb


@dataclass
class ResourceAllocation:
    """A resource allocation for an experiment."""
    allocation_id: str
    experiment_id: str
    agent_id: str
    priority: Priority
    
    # Allocated Resources
    cpu_cores: int
    memory_gb: float
    gpu_memory_gb: float
    disk_gb: float
    api_calls: int
    
    # Timing
    created_at: datetime
    expires_at: datetime
    started_at: Optional[datetime] = None
    
    # Status
    status: AllocationStatus = AllocationStatus.PENDING
    
    # Usage Tracking
    cpu_used_seconds: float = 0.0
    memory_peak_gb: float = 0.0
    gpu_used_seconds: float = 0.0
    disk_used_gb: float = 0.0
    api_calls_used: int = 0
    
    # Cost (in compute units)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allocation_id': self.allocation_id,
            'experiment_id': self.experiment_id,
            'agent_id': self.agent_id,
            'priority': self.priority.name,
            'cpu_cores': self.cpu_cores,
            'memory_gb': self.memory_gb,
            'gpu_memory_gb': self.gpu_memory_gb,
            'disk_gb': self.disk_gb,
            'api_calls': self.api_calls,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'status': self.status.name,
            'cpu_used_seconds': self.cpu_used_seconds,
            'memory_peak_gb': self.memory_peak_gb,
            'api_calls_used': self.api_calls_used,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
        }
    
    def is_valid(self) -> bool:
        """Check if allocation is still valid."""
        if self.status not in [AllocationStatus.PENDING, AllocationStatus.ACTIVE]:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True
    
    def get_remaining_api_calls(self) -> int:
        """Get remaining API calls."""
        return max(0, self.api_calls - self.api_calls_used)


@dataclass
class ResourceUsage:
    """Current resource usage snapshot."""
    timestamp: datetime
    cpu_used_cores: float
    memory_used_gb: float
    gpu_used_gb: float
    disk_used_gb: float
    api_calls_last_hour: int
    active_allocations: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_used_cores': self.cpu_used_cores,
            'memory_used_gb': self.memory_used_gb,
            'gpu_used_gb': self.gpu_used_gb,
            'disk_used_gb': self.disk_used_gb,
            'api_calls_last_hour': self.api_calls_last_hour,
            'active_allocations': self.active_allocations,
        }


@dataclass
class BudgetAlert:
    """Alert for budget-related events."""
    alert_id: str
    timestamp: datetime
    resource_type: ResourceType
    severity: str  # 'warning', 'critical', 'resolved'
    message: str
    current_usage_pct: float
    threshold_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'resource_type': self.resource_type.value,
            'severity': self.severity,
            'message': self.message,
            'current_usage_pct': self.current_usage_pct,
            'threshold_pct': self.threshold_pct,
        }


class ComputeBudgetController:
    """
    Controls compute resource allocation for AI experiments.
    
    Ensures that:
    1. Production system always has reserved resources
    2. Experiments don't exceed their allocated budgets
    3. Total resource usage stays within limits
    4. Resources are fairly allocated based on priority
    """
    
    def __init__(self, config: Optional[BudgetConfig] = None):
        """
        Initialize the compute budget controller.
        
        Args:
            config: Budget configuration
        """
        self.config = config or BudgetConfig()
        
        self._lock = threading.RLock()
        
        # Allocations
        self._allocations: Dict[str, ResourceAllocation] = {}
        self._allocation_queue: List[str] = []  # Priority queue
        
        # Usage tracking
        self._api_call_history: List[datetime] = []
        self._usage_history: List[ResourceUsage] = []
        
        # Alerts
        self._alerts: List[BudgetAlert] = []
        self._alert_callbacks: List[Callable] = []
        
        # Monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # Storage
        self._log_path = Path(self.config.budget_log_path)
        self._log_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("ComputeBudgetController initialized")
    
    async def start(self):
        """Start the budget controller monitoring."""
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ComputeBudgetController started")
    
    async def stop(self):
        """Stop the budget controller."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("ComputeBudgetController stopped")
    
    async def request_allocation(
        self,
        experiment_id: str,
        agent_id: str,
        cpu_cores: int = 1,
        memory_gb: float = 1.0,
        gpu_memory_gb: float = 0.0,
        disk_gb: float = 1.0,
        api_calls: int = 100,
        priority: Priority = Priority.NORMAL,
        duration_hours: float = 1.0,
    ) -> Optional[ResourceAllocation]:
        """
        Request a resource allocation for an experiment.
        
        Args:
            experiment_id: ID of the experiment
            agent_id: ID of the requesting agent
            cpu_cores: Number of CPU cores needed
            memory_gb: Memory needed in GB
            gpu_memory_gb: GPU memory needed in GB
            disk_gb: Disk space needed in GB
            api_calls: Number of API calls needed
            priority: Priority level
            duration_hours: Expected duration in hours
        
        Returns:
            ResourceAllocation if approved, None if rejected
        """
        with self._lock:
            # Validate request against per-experiment limits
            if cpu_cores > self.config.max_cpu_per_experiment:
                logger.warning(f"CPU request {cpu_cores} exceeds limit {self.config.max_cpu_per_experiment}")
                return None
            
            if memory_gb > self.config.max_memory_per_experiment_gb:
                logger.warning(f"Memory request {memory_gb}GB exceeds limit")
                return None
            
            if duration_hours > self.config.max_runtime_hours:
                logger.warning(f"Duration {duration_hours}h exceeds limit")
                return None
            
            # Check available resources
            current_usage = self._get_current_usage()
            
            available_cpu = self.config.get_available_cpu() - current_usage.cpu_used_cores
            available_memory = self.config.get_available_memory() - current_usage.memory_used_gb
            
            if cpu_cores > available_cpu:
                logger.warning(f"Insufficient CPU: requested {cpu_cores}, available {available_cpu}")
                return None
            
            if memory_gb > available_memory:
                logger.warning(f"Insufficient memory: requested {memory_gb}GB, available {available_memory}GB")
                return None
            
            # Create allocation
            allocation_id = f"ALLOC-{uuid.uuid4().hex[:12]}"
            now = datetime.now(timezone.utc)
            
            allocation = ResourceAllocation(
                allocation_id=allocation_id,
                experiment_id=experiment_id,
                agent_id=agent_id,
                priority=priority,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                gpu_memory_gb=gpu_memory_gb,
                disk_gb=disk_gb,
                api_calls=api_calls,
                created_at=now,
                expires_at=now + timedelta(hours=duration_hours),
                estimated_cost=self._calculate_cost(cpu_cores, memory_gb, gpu_memory_gb, duration_hours),
            )
            
            self._allocations[allocation_id] = allocation
            
            # Add to priority queue
            self._insert_by_priority(allocation_id, priority)
            
            logger.info(f"Allocation approved: {allocation_id} for experiment {experiment_id}")
            
            return allocation
    
    def _insert_by_priority(self, allocation_id: str, priority: Priority):
        """Insert allocation into priority queue."""
        # Find position based on priority
        insert_pos = len(self._allocation_queue)
        for i, existing_id in enumerate(self._allocation_queue):
            existing = self._allocations.get(existing_id)
            if existing and existing.priority.value > priority.value:
                insert_pos = i
                break
        
        self._allocation_queue.insert(insert_pos, allocation_id)
    
    def _calculate_cost(
        self,
        cpu_cores: int,
        memory_gb: float,
        gpu_memory_gb: float,
        duration_hours: float
    ) -> float:
        """Calculate estimated cost in compute units."""
        # Simple cost model
        cpu_cost = cpu_cores * duration_hours * 1.0
        memory_cost = memory_gb * duration_hours * 0.5
        gpu_cost = gpu_memory_gb * duration_hours * 2.0
        
        return cpu_cost + memory_cost + gpu_cost
    
    async def activate_allocation(self, allocation_id: str) -> bool:
        """
        Activate a pending allocation.
        
        Args:
            allocation_id: ID of the allocation to activate
        
        Returns:
            True if activated successfully
        """
        with self._lock:
            allocation = self._allocations.get(allocation_id)
            if not allocation:
                return False
            
            if allocation.status != AllocationStatus.PENDING:
                return False
            
            allocation.status = AllocationStatus.ACTIVE
            allocation.started_at = datetime.now(timezone.utc)
            
            logger.info(f"Allocation activated: {allocation_id}")
            
            return True
    
    async def release_allocation(self, allocation_id: str):
        """
        Release an allocation.
        
        Args:
            allocation_id: ID of the allocation to release
        """
        with self._lock:
            allocation = self._allocations.get(allocation_id)
            if not allocation:
                return
            
            # Calculate actual cost
            if allocation.started_at:
                duration = (datetime.now(timezone.utc) - allocation.started_at).total_seconds() / 3600
                allocation.actual_cost = self._calculate_cost(
                    allocation.cpu_cores,
                    allocation.memory_peak_gb,
                    allocation.gpu_memory_gb,
                    duration
                )
            
            allocation.status = AllocationStatus.EXPIRED
            
            # Remove from queue
            if allocation_id in self._allocation_queue:
                self._allocation_queue.remove(allocation_id)
            
            logger.info(f"Allocation released: {allocation_id}")
    
    async def record_api_call(self, allocation_id: str) -> bool:
        """
        Record an API call against an allocation.
        
        Args:
            allocation_id: ID of the allocation
        
        Returns:
            True if call allowed, False if limit exceeded
        """
        with self._lock:
            allocation = self._allocations.get(allocation_id)
            if not allocation or not allocation.is_valid():
                return False
            
            if allocation.api_calls_used >= allocation.api_calls:
                logger.warning(f"API call limit exceeded for {allocation_id}")
                return False
            
            allocation.api_calls_used += 1
            self._api_call_history.append(datetime.now(timezone.utc))
            
            return True
    
    async def update_usage(
        self,
        allocation_id: str,
        cpu_seconds: float = 0,
        memory_gb: float = 0,
        disk_gb: float = 0,
    ):
        """
        Update resource usage for an allocation.
        
        Args:
            allocation_id: ID of the allocation
            cpu_seconds: CPU seconds used
            memory_gb: Current memory usage
            disk_gb: Current disk usage
        """
        with self._lock:
            allocation = self._allocations.get(allocation_id)
            if not allocation:
                return
            
            allocation.cpu_used_seconds += cpu_seconds
            allocation.memory_peak_gb = max(allocation.memory_peak_gb, memory_gb)
            allocation.disk_used_gb = max(allocation.disk_used_gb, disk_gb)
    
    def _get_current_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        cpu_used = 0.0
        memory_used = 0.0
        gpu_used = 0.0
        disk_used = 0.0
        active_count = 0
        
        for allocation in self._allocations.values():
            if allocation.status == AllocationStatus.ACTIVE:
                cpu_used += allocation.cpu_cores
                memory_used += allocation.memory_gb
                gpu_used += allocation.gpu_memory_gb
                disk_used += allocation.disk_used_gb
                active_count += 1
        
        # Count API calls in last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        api_calls = sum(1 for t in self._api_call_history if t > one_hour_ago)
        
        return ResourceUsage(
            timestamp=datetime.now(timezone.utc),
            cpu_used_cores=cpu_used,
            memory_used_gb=memory_used,
            gpu_used_gb=gpu_used,
            disk_used_gb=disk_used,
            api_calls_last_hour=api_calls,
            active_allocations=active_count,
        )
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._is_running:
            try:
                # Get current usage
                usage = self._get_current_usage()
                self._usage_history.append(usage)
                
                # Keep only last 24 hours
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                self._usage_history = [u for u in self._usage_history if u.timestamp > cutoff]
                
                # Check thresholds
                await self._check_thresholds(usage)
                
                # Clean up expired allocations
                await self._cleanup_expired()
                
                # Clean up old API call history
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
                self._api_call_history = [t for t in self._api_call_history if t > one_hour_ago]
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_thresholds(self, usage: ResourceUsage):
        """Check resource thresholds and generate alerts."""
        available_cpu = self.config.get_available_cpu()
        available_memory = self.config.get_available_memory()
        
        # CPU threshold
        cpu_pct = usage.cpu_used_cores / available_cpu if available_cpu > 0 else 0
        if cpu_pct >= self.config.hard_limit_pct:
            await self._create_alert(
                ResourceType.CPU,
                'critical',
                f'CPU usage critical: {cpu_pct:.1%}',
                cpu_pct,
                self.config.hard_limit_pct
            )
        elif cpu_pct >= self.config.throttle_threshold_pct:
            await self._create_alert(
                ResourceType.CPU,
                'warning',
                f'CPU usage high: {cpu_pct:.1%}',
                cpu_pct,
                self.config.throttle_threshold_pct
            )
        
        # Memory threshold
        memory_pct = usage.memory_used_gb / available_memory if available_memory > 0 else 0
        if memory_pct >= self.config.hard_limit_pct:
            await self._create_alert(
                ResourceType.MEMORY,
                'critical',
                f'Memory usage critical: {memory_pct:.1%}',
                memory_pct,
                self.config.hard_limit_pct
            )
        elif memory_pct >= self.config.throttle_threshold_pct:
            await self._create_alert(
                ResourceType.MEMORY,
                'warning',
                f'Memory usage high: {memory_pct:.1%}',
                memory_pct,
                self.config.throttle_threshold_pct
            )
        
        # API calls threshold
        api_pct = usage.api_calls_last_hour / self.config.total_api_calls_per_hour
        if api_pct >= self.config.hard_limit_pct:
            await self._create_alert(
                ResourceType.API_CALLS,
                'critical',
                f'API calls critical: {api_pct:.1%}',
                api_pct,
                self.config.hard_limit_pct
            )
    
    async def _create_alert(
        self,
        resource_type: ResourceType,
        severity: str,
        message: str,
        current_pct: float,
        threshold_pct: float
    ):
        """Create and dispatch an alert."""
        alert = BudgetAlert(
            alert_id=f"ALERT-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            resource_type=resource_type,
            severity=severity,
            message=message,
            current_usage_pct=current_pct,
            threshold_pct=threshold_pct,
        )
        
        self._alerts.append(alert)
        
        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.warning(f"Budget alert: {message}")
    
    async def _cleanup_expired(self):
        """Clean up expired allocations."""
        now = datetime.now(timezone.utc)
        
        for allocation_id, allocation in list(self._allocations.items()):
            if allocation.status == AllocationStatus.ACTIVE:
                if now > allocation.expires_at:
                    allocation.status = AllocationStatus.EXPIRED
                    if allocation_id in self._allocation_queue:
                        self._allocation_queue.remove(allocation_id)
                    logger.info(f"Allocation expired: {allocation_id}")
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for budget alerts."""
        self._alert_callbacks.append(callback)
    
    def get_allocation(self, allocation_id: str) -> Optional[ResourceAllocation]:
        """Get allocation by ID."""
        return self._allocations.get(allocation_id)
    
    def get_allocations_for_experiment(self, experiment_id: str) -> List[ResourceAllocation]:
        """Get all allocations for an experiment."""
        return [a for a in self._allocations.values() if a.experiment_id == experiment_id]
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self._get_current_usage()
    
    def get_usage_history(self, hours: int = 24) -> List[ResourceUsage]:
        """Get usage history for the specified hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [u for u in self._usage_history if u.timestamp > cutoff]
    
    def get_alerts(self, hours: int = 24) -> List[BudgetAlert]:
        """Get alerts from the specified hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [a for a in self._alerts if a.timestamp > cutoff]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get budget controller statistics."""
        usage = self._get_current_usage()
        
        total_cost = sum(a.actual_cost for a in self._allocations.values())
        
        return {
            'total_allocations': len(self._allocations),
            'active_allocations': usage.active_allocations,
            'pending_allocations': sum(
                1 for a in self._allocations.values() 
                if a.status == AllocationStatus.PENDING
            ),
            'current_cpu_usage': usage.cpu_used_cores,
            'current_memory_usage_gb': usage.memory_used_gb,
            'api_calls_last_hour': usage.api_calls_last_hour,
            'total_compute_cost': total_cost,
            'alerts_last_24h': len(self.get_alerts(24)),
            'available_cpu': self.config.get_available_cpu() - usage.cpu_used_cores,
            'available_memory_gb': self.config.get_available_memory() - usage.memory_used_gb,
        }
    
    async def persist_state(self):
        """Persist current state to disk."""
        state = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'allocations': {k: v.to_dict() for k, v in self._allocations.items()},
            'statistics': self.get_statistics(),
        }
        
        state_file = self._log_path / 'budget_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
