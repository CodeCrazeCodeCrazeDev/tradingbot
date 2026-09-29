"""
Compute Budget Controller
=========================

Manages and enforces resource limits for autonomous AI operations.
Prevents runaway processes and ensures fair resource allocation.

Resources Controlled:
- CPU time (per operation and daily)
- Memory usage (per operation and total)
- Execution time (wall clock)
- Storage (disk space)
- API calls (rate limiting)
- Concurrent operations

CRITICAL: All autonomous operations MUST request budget allocation.
"""

import os
import time
import threading
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from contextlib import contextmanager
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be budgeted."""
    CPU_TIME = auto()
    MEMORY = auto()
    WALL_TIME = auto()
    STORAGE = auto()
    API_CALLS = auto()
    CONCURRENT_OPS = auto()
    NETWORK_BANDWIDTH = auto()


class BudgetPriority(Enum):
    """Priority levels for budget allocation."""
    CRITICAL = 1      # Safety systems, emergency operations
    HIGH = 2          # Active trading, real-time analysis
    NORMAL = 3        # Research, backtesting
    LOW = 4           # Maintenance, cleanup
    BACKGROUND = 5    # Optional improvements


@dataclass
class ResourceBudget:
    """Budget allocation for a resource."""
    resource_type: ResourceType
    max_per_operation: float
    max_per_hour: float
    max_per_day: float
    current_usage: float = 0.0
    hourly_usage: float = 0.0
    daily_usage: float = 0.0
    last_reset_hour: datetime = field(default_factory=datetime.utcnow)
    last_reset_day: datetime = field(default_factory=datetime.utcnow)
    
    def reset_if_needed(self):
        """Reset counters if time period has passed."""
        now = datetime.utcnow()
        
        # Reset hourly
        if (now - self.last_reset_hour).total_seconds() >= 3600:
            self.hourly_usage = 0.0
            self.last_reset_hour = now
        
        # Reset daily
        if (now - self.last_reset_day).total_seconds() >= 86400:
            self.daily_usage = 0.0
            self.last_reset_day = now
    
    def can_allocate(self, amount: float) -> bool:
        """Check if amount can be allocated."""
        self.reset_if_needed()
        
        if amount > self.max_per_operation:
            return False
        if self.hourly_usage + amount > self.max_per_hour:
            return False
        if self.daily_usage + amount > self.max_per_day:
            return False
        
        return True
    
    def allocate(self, amount: float) -> bool:
        """Allocate resource amount."""
        if not self.can_allocate(amount):
            return False
        
        self.current_usage = amount
        self.hourly_usage += amount
        self.daily_usage += amount
        return True
    
    def release(self, amount: Optional[float] = None):
        """Release allocated resources."""
        if amount is None:
            amount = self.current_usage
        self.current_usage = max(0, self.current_usage - amount)
    
    def get_remaining(self) -> Dict[str, float]:
        """Get remaining budget."""
        self.reset_if_needed()
        return {
            'per_operation': self.max_per_operation,
            'hourly': self.max_per_hour - self.hourly_usage,
            'daily': self.max_per_day - self.daily_usage,
        }


@dataclass
class ResourceUsage:
    """Snapshot of resource usage."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_usage_mb: float
    active_operations: int
    api_calls_hour: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'disk_usage_mb': self.disk_usage_mb,
            'active_operations': self.active_operations,
            'api_calls_hour': self.api_calls_hour,
        }


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded."""
    def __init__(self, resource_type: ResourceType, requested: float, 
                 available: float, message: str = ""):
        self.resource_type = resource_type
        self.requested = requested
        self.available = available
        super().__init__(
            message or f"Budget exceeded for {resource_type.name}: "
                       f"requested {requested}, available {available}"
        )


@dataclass
class BudgetAllocation:
    """Represents an active budget allocation."""
    allocation_id: str
    resource_type: ResourceType
    amount: float
    priority: BudgetPriority
    operation_name: str
    allocated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    released: bool = False
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class ComputeBudgetController:
    """
    Controls and enforces compute resource budgets.
    
    Ensures autonomous AI operations don't consume excessive resources
    and provides fair allocation across different operation types.
    """
    
    # Default budget limits
    DEFAULT_BUDGETS = {
        ResourceType.CPU_TIME: {
            'max_per_operation': 60.0,      # 60 seconds CPU time per op
            'max_per_hour': 1800.0,         # 30 minutes per hour
            'max_per_day': 14400.0,         # 4 hours per day
        },
        ResourceType.MEMORY: {
            'max_per_operation': 512.0,     # 512 MB per operation
            'max_per_hour': 2048.0,         # 2 GB cumulative per hour
            'max_per_day': 8192.0,          # 8 GB cumulative per day
        },
        ResourceType.WALL_TIME: {
            'max_per_operation': 300.0,     # 5 minutes wall time per op
            'max_per_hour': 3600.0,         # 1 hour per hour (100%)
            'max_per_day': 28800.0,         # 8 hours per day
        },
        ResourceType.STORAGE: {
            'max_per_operation': 100.0,     # 100 MB per operation
            'max_per_hour': 500.0,          # 500 MB per hour
            'max_per_day': 2048.0,          # 2 GB per day
        },
        ResourceType.API_CALLS: {
            'max_per_operation': 10.0,      # 10 calls per operation
            'max_per_hour': 100.0,          # 100 calls per hour
            'max_per_day': 1000.0,          # 1000 calls per day
        },
        ResourceType.CONCURRENT_OPS: {
            'max_per_operation': 1.0,       # 1 concurrent op
            'max_per_hour': 10.0,           # 10 concurrent max
            'max_per_day': 10.0,            # Same as hourly
        },
    }
    
    def __init__(self, 
                 custom_budgets: Optional[Dict[ResourceType, Dict[str, float]]] = None,
                 storage_path: Optional[Path] = None):
        """
        Initialize budget controller.
        
        Args:
            custom_budgets: Override default budgets
            storage_path: Path for persisting budget state
        """
        self.budgets: Dict[ResourceType, ResourceBudget] = {}
        self.allocations: Dict[str, BudgetAllocation] = {}
        self.usage_history: List[ResourceUsage] = []
        self.storage_path = storage_path
        
        self._lock = threading.RLock()
        self._allocation_counter = 0
        
        # Initialize budgets
        self._initialize_budgets(custom_budgets)
        
        # Start monitoring thread
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("ComputeBudgetController initialized")
    
    def _initialize_budgets(self, custom_budgets: Optional[Dict] = None):
        """Initialize resource budgets."""
        for resource_type, defaults in self.DEFAULT_BUDGETS.items():
            config = defaults.copy()
            if custom_budgets and resource_type in custom_budgets:
                config.update(custom_budgets[resource_type])
            
            self.budgets[resource_type] = ResourceBudget(
                resource_type=resource_type,
                max_per_operation=config['max_per_operation'],
                max_per_hour=config['max_per_hour'],
                max_per_day=config['max_per_day'],
            )
    
    def request_budget(self, 
                       resource_type: ResourceType,
                       amount: float,
                       operation_name: str,
                       priority: BudgetPriority = BudgetPriority.NORMAL,
                       timeout_seconds: Optional[float] = None) -> str:
        """
        Request budget allocation for an operation.
        
        Args:
            resource_type: Type of resource needed
            amount: Amount of resource needed
            operation_name: Name of the operation
            priority: Priority level
            timeout_seconds: Optional timeout for allocation
            
        Returns:
            Allocation ID
            
        Raises:
            BudgetExceededError: If budget cannot be allocated
        """
        with self._lock:
            budget = self.budgets.get(resource_type)
            if not budget:
                raise ValueError(f"Unknown resource type: {resource_type}")
            
            # Check if allocation is possible
            if not budget.can_allocate(amount):
                remaining = budget.get_remaining()
                raise BudgetExceededError(
                    resource_type=resource_type,
                    requested=amount,
                    available=min(remaining.values()),
                )
            
            # Allocate
            if not budget.allocate(amount):
                raise BudgetExceededError(
                    resource_type=resource_type,
                    requested=amount,
                    available=0,
                )
            
            # Create allocation record
            self._allocation_counter += 1
            allocation_id = f"alloc_{self._allocation_counter:08d}"
            
            expires_at = None
            if timeout_seconds:
                expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            
            allocation = BudgetAllocation(
                allocation_id=allocation_id,
                resource_type=resource_type,
                amount=amount,
                priority=priority,
                operation_name=operation_name,
                expires_at=expires_at,
            )
            
            self.allocations[allocation_id] = allocation
            
            logger.debug(
                f"Budget allocated: {allocation_id} - {resource_type.name} "
                f"{amount} for {operation_name}"
            )
            
            return allocation_id
    
    def release_budget(self, allocation_id: str):
        """
        Release a budget allocation.
        
        Args:
            allocation_id: ID of allocation to release
        """
        with self._lock:
            allocation = self.allocations.get(allocation_id)
            if not allocation:
                logger.warning(f"Unknown allocation: {allocation_id}")
                return
            
            if allocation.released:
                return
            
            budget = self.budgets.get(allocation.resource_type)
            if budget:
                budget.release(allocation.amount)
            
            allocation.released = True
            
            logger.debug(f"Budget released: {allocation_id}")
    
    @contextmanager
    def budget_context(self,
                       resource_type: ResourceType,
                       amount: float,
                       operation_name: str,
                       priority: BudgetPriority = BudgetPriority.NORMAL,
                       timeout_seconds: Optional[float] = None):
        """
        Context manager for budget allocation.
        
        Usage:
            with controller.budget_context(ResourceType.CPU_TIME, 10.0, "my_op"):
                # Do work
        """
        allocation_id = self.request_budget(
            resource_type, amount, operation_name, priority, timeout_seconds
        )
        try:
            yield allocation_id
        finally:
            self.release_budget(allocation_id)
    
    def check_budget(self, resource_type: ResourceType, amount: float) -> bool:
        """
        Check if budget is available without allocating.
        
        Args:
            resource_type: Type of resource
            amount: Amount to check
            
        Returns:
            True if budget is available
        """
        with self._lock:
            budget = self.budgets.get(resource_type)
            if not budget:
                return False
            return budget.can_allocate(amount)
    
    def get_remaining_budget(self, resource_type: ResourceType) -> Dict[str, float]:
        """Get remaining budget for a resource type."""
        with self._lock:
            budget = self.budgets.get(resource_type)
            if not budget:
                return {'per_operation': 0, 'hourly': 0, 'daily': 0}
            return budget.get_remaining()
    
    def get_all_remaining_budgets(self) -> Dict[str, Dict[str, float]]:
        """Get remaining budgets for all resource types."""
        with self._lock:
            return {
                rt.name: self.get_remaining_budget(rt)
                for rt in ResourceType
            }
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current system resource usage."""
        process = psutil.Process()
        
        return ResourceUsage(
            timestamp=datetime.utcnow(),
            cpu_percent=process.cpu_percent(),
            memory_mb=process.memory_info().rss / (1024 * 1024),
            disk_usage_mb=self._get_disk_usage(),
            active_operations=len([a for a in self.allocations.values() if not a.released]),
            api_calls_hour=int(self.budgets[ResourceType.API_CALLS].hourly_usage),
        )
    
    def _get_disk_usage(self) -> float:
        """Get disk usage in MB."""
        try:
            if self.storage_path and self.storage_path.exists():
                total_size = sum(
                    f.stat().st_size for f in self.storage_path.rglob('*') if f.is_file()
                )
                return total_size / (1024 * 1024)
        except Exception:
            pass
        return 0.0
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                # Record usage
                usage = self.get_current_usage()
                self.usage_history.append(usage)
                
                # Keep history bounded
                if len(self.usage_history) > 1000:
                    self.usage_history = self.usage_history[-500:]
                
                # Clean up expired allocations
                self._cleanup_expired_allocations()
                
                # Check for budget overruns
                self._check_budget_health()
                
            except Exception as e:
                logger.error(f"Budget monitor error: {e}")
            
            time.sleep(10)  # Check every 10 seconds
    
    def _cleanup_expired_allocations(self):
        """Clean up expired allocations."""
        with self._lock:
            expired = [
                aid for aid, alloc in self.allocations.items()
                if alloc.is_expired() and not alloc.released
            ]
            
            for allocation_id in expired:
                self.release_budget(allocation_id)
                logger.warning(f"Expired allocation released: {allocation_id}")
    
    def _check_budget_health(self):
        """Check budget health and log warnings."""
        with self._lock:
            for resource_type, budget in self.budgets.items():
                remaining = budget.get_remaining()
                
                # Warn if hourly budget is low
                if remaining['hourly'] < budget.max_per_hour * 0.1:
                    logger.warning(
                        f"Low hourly budget for {resource_type.name}: "
                        f"{remaining['hourly']:.1f} remaining"
                    )
                
                # Warn if daily budget is low
                if remaining['daily'] < budget.max_per_day * 0.1:
                    logger.warning(
                        f"Low daily budget for {resource_type.name}: "
                        f"{remaining['daily']:.1f} remaining"
                    )
    
    def get_budget_report(self) -> Dict[str, Any]:
        """Generate comprehensive budget report."""
        with self._lock:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'budgets': {},
                'active_allocations': len([a for a in self.allocations.values() if not a.released]),
                'total_allocations': len(self.allocations),
            }
            
            for resource_type, budget in self.budgets.items():
                remaining = budget.get_remaining()
                report['budgets'][resource_type.name] = {
                    'max_per_operation': budget.max_per_operation,
                    'max_per_hour': budget.max_per_hour,
                    'max_per_day': budget.max_per_day,
                    'hourly_usage': budget.hourly_usage,
                    'daily_usage': budget.daily_usage,
                    'remaining_hourly': remaining['hourly'],
                    'remaining_daily': remaining['daily'],
                    'utilization_hourly': (
                        budget.hourly_usage / budget.max_per_hour * 100
                        if budget.max_per_hour > 0 else 0
                    ),
                    'utilization_daily': (
                        budget.daily_usage / budget.max_per_day * 100
                        if budget.max_per_day > 0 else 0
                    ),
                }
            
            return report
    
    def set_budget_limit(self, resource_type: ResourceType, 
                         limit_type: str, value: float):
        """
        Dynamically adjust budget limits.
        
        Args:
            resource_type: Resource to adjust
            limit_type: 'per_operation', 'per_hour', or 'per_day'
            value: New limit value
        """
        with self._lock:
            budget = self.budgets.get(resource_type)
            if not budget:
                raise ValueError(f"Unknown resource type: {resource_type}")
            
            if limit_type == 'per_operation':
                budget.max_per_operation = value
            elif limit_type == 'per_hour':
                budget.max_per_hour = value
            elif limit_type == 'per_day':
                budget.max_per_day = value
            else:
                raise ValueError(f"Unknown limit type: {limit_type}")
            
            logger.info(
                f"Budget limit updated: {resource_type.name} "
                f"{limit_type} = {value}"
            )
    
    def emergency_release_all(self):
        """Emergency release of all allocations."""
        with self._lock:
            for allocation_id in list(self.allocations.keys()):
                self.release_budget(allocation_id)
            
            logger.critical("Emergency release of all budget allocations")
    
    def shutdown(self):
        """Shutdown the budget controller."""
        self._monitoring = False
        self.emergency_release_all()
        logger.info("ComputeBudgetController shutdown")


class BudgetAwareExecutor:
    """Executor that automatically manages budget for operations."""
    
    def __init__(self, controller: ComputeBudgetController):
        self.controller = controller
    
    def execute(self, 
                func: Callable,
                operation_name: str,
                cpu_budget: float = 10.0,
                memory_budget: float = 256.0,
                priority: BudgetPriority = BudgetPriority.NORMAL,
                *args, **kwargs) -> Any:
        """
        Execute function with automatic budget management.
        
        Args:
            func: Function to execute
            operation_name: Name for the operation
            cpu_budget: CPU time budget in seconds
            memory_budget: Memory budget in MB
            priority: Operation priority
            *args, **kwargs: Arguments for the function
            
        Returns:
            Function result
        """
        # Request CPU budget
        with self.controller.budget_context(
            ResourceType.CPU_TIME, cpu_budget, operation_name, priority
        ):
            # Request memory budget
            with self.controller.budget_context(
                ResourceType.MEMORY, memory_budget, operation_name, priority
            ):
                return func(*args, **kwargs)
