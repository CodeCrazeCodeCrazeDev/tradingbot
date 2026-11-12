"""
Compute Budget Controller

Manages and optimizes compute resource allocation for infrastructure evolution.
Ensures efficient use of resources while enabling continuous improvement.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of compute resources."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"
    NETWORK = "network"
    API_CALLS = "api_calls"


class AllocationPriority(Enum):
    """Priority levels for resource allocation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class BudgetStatus(Enum):
    """Status of budget allocation."""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    EXHAUSTED = "exhausted"
    EXCEEDED = "exceeded"


@dataclass
class ResourceQuota:
    """Quota for a specific resource type."""
    resource_type: ResourceType
    total_quota: float
    allocated: float
    consumed: float
    reserved: float
    unit: str
    
    def available(self) -> float:
        """Calculate available resources."""
        return self.total_quota - self.allocated - self.reserved
    
    def utilization(self) -> float:
        """Calculate utilization percentage."""
        return (self.allocated + self.reserved) / self.total_quota if self.total_quota > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'resource_type': self.resource_type.value,
            'total_quota': self.total_quota,
            'allocated': self.allocated,
            'consumed': self.consumed,
            'reserved': self.reserved,
            'available': self.available(),
            'utilization': self.utilization(),
            'unit': self.unit,
        }


@dataclass
class BudgetAllocation:
    """Allocation of compute budget to a task."""
    allocation_id: str
    task_id: str
    task_type: str
    priority: AllocationPriority
    resources: Dict[ResourceType, float]
    allocated_at: datetime
    expires_at: Optional[datetime]
    actual_usage: Dict[ResourceType, float] = field(default_factory=dict)
    is_active: bool = True
    efficiency_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allocation_id': self.allocation_id,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'resources': {rt.value: amount for rt, amount in self.resources.items()},
            'allocated_at': self.allocated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'actual_usage': {rt.value: amount for rt, amount in self.actual_usage.items()},
            'is_active': self.is_active,
            'efficiency_score': self.efficiency_score,
        }


@dataclass
class BudgetOptimization:
    """Optimization recommendation for budget allocation."""
    optimization_id: str
    description: str
    potential_savings: Dict[ResourceType, float]
    estimated_impact: float
    actions: List[Dict[str, Any]]
    priority: AllocationPriority
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'optimization_id': self.optimization_id,
            'description': self.description,
            'potential_savings': {rt.value: amount for rt, amount in self.potential_savings.items()},
            'estimated_impact': self.estimated_impact,
            'actions': self.actions,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
        }


class ComputeBudgetController:
    """
    Manages compute resource budgets for infrastructure evolution.
    
    Provides:
    - Resource quota management
    - Dynamic allocation
    - Usage tracking
    - Optimization recommendations
    - Cost control
    - Priority-based scheduling
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'compute_budget_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._quotas: Dict[ResourceType, ResourceQuota] = {}
        self._allocations: Dict[str, BudgetAllocation] = {}
        self._optimizations: List[BudgetOptimization] = []
        
        self._budget_config = {
            'auto_scale_enabled': True,
            'optimization_interval_hours': 6,
            'efficiency_threshold': 0.7,
            'overallocation_limit': 1.1,
            'reservation_timeout_hours': 24,
        }
        
        self._initialize_quotas()
        
        logger.info("✅ Compute Budget Controller initialized")
    
    def _initialize_quotas(self):
        """Initialize resource quotas."""
        default_quotas = {
            ResourceType.CPU: ResourceQuota(
                resource_type=ResourceType.CPU,
                total_quota=100.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='cores',
            ),
            ResourceType.MEMORY: ResourceQuota(
                resource_type=ResourceType.MEMORY,
                total_quota=256.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='GB',
            ),
            ResourceType.GPU: ResourceQuota(
                resource_type=ResourceType.GPU,
                total_quota=8.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='units',
            ),
            ResourceType.STORAGE: ResourceQuota(
                resource_type=ResourceType.STORAGE,
                total_quota=1000.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='GB',
            ),
            ResourceType.NETWORK: ResourceQuota(
                resource_type=ResourceType.NETWORK,
                total_quota=1000.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='Mbps',
            ),
            ResourceType.API_CALLS: ResourceQuota(
                resource_type=ResourceType.API_CALLS,
                total_quota=1000000.0,
                allocated=0.0,
                consumed=0.0,
                reserved=0.0,
                unit='calls/day',
            ),
        }
        
        self._quotas = default_quotas
    
    async def request_allocation(
        self,
        task_id: str,
        task_type: str,
        resources: Dict[ResourceType, float],
        priority: AllocationPriority = AllocationPriority.MEDIUM,
        duration_hours: Optional[int] = None,
    ) -> Optional[BudgetAllocation]:
        """
        Request resource allocation for a task.
        
        Args:
            task_id: ID of the task
            task_type: Type of task
            resources: Resources requested
            priority: Allocation priority
            duration_hours: Optional duration
        
        Returns:
            BudgetAllocation if successful, None if insufficient resources
        """
        if not await self._check_availability(resources):
            logger.warning(f"Insufficient resources for task {task_id}")
            
            if priority in [AllocationPriority.CRITICAL, AllocationPriority.HIGH]:
                await self._attempt_reallocation(resources, priority)
                
                if await self._check_availability(resources):
                    logger.info(f"Resources freed for high-priority task {task_id}")
                else:
                    return None
            else:
                return None
        
        allocation_id = f"ALLOC-{uuid.uuid4().hex[:12]}"
        
        for resource_type, amount in resources.items():
            if resource_type in self._quotas:
                self._quotas[resource_type].allocated += amount
        
        expires_at = None
        if duration_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        allocation = BudgetAllocation(
            allocation_id=allocation_id,
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            resources=resources,
            allocated_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )
        
        self._allocations[allocation_id] = allocation
        await self._persist_allocation(allocation)
        
        logger.info(f"Allocated resources for task {task_id}: {resources}")
        
        return allocation
    
    async def _check_availability(
        self,
        resources: Dict[ResourceType, float],
    ) -> bool:
        """Check if requested resources are available."""
        for resource_type, amount in resources.items():
            if resource_type not in self._quotas:
                continue
            
            quota = self._quotas[resource_type]
            if quota.available() < amount:
                return False
        
        return True
    
    async def _attempt_reallocation(
        self,
        needed_resources: Dict[ResourceType, float],
        priority: AllocationPriority,
    ):
        """Attempt to free resources by preempting lower-priority tasks."""
        priority_order = {
            AllocationPriority.BACKGROUND: 0,
            AllocationPriority.LOW: 1,
            AllocationPriority.MEDIUM: 2,
            AllocationPriority.HIGH: 3,
            AllocationPriority.CRITICAL: 4,
        }
        
        current_priority_level = priority_order[priority]
        
        for allocation in sorted(
            self._allocations.values(),
            key=lambda a: priority_order[a.priority]
        ):
            if priority_order[allocation.priority] >= current_priority_level:
                break
            
            if allocation.is_active:
                await self.release_allocation(allocation.allocation_id)
                logger.info(f"Preempted allocation {allocation.allocation_id} for higher priority task")
                
                if await self._check_availability(needed_resources):
                    return
    
    async def record_usage(
        self,
        allocation_id: str,
        actual_usage: Dict[ResourceType, float],
    ) -> bool:
        """
        Record actual resource usage for an allocation.
        
        Args:
            allocation_id: ID of the allocation
            actual_usage: Actual resources used
        
        Returns:
            True if recorded successfully
        """
        if allocation_id not in self._allocations:
            return False
        
        allocation = self._allocations[allocation_id]
        allocation.actual_usage = actual_usage
        
        total_allocated = sum(allocation.resources.values())
        total_used = sum(actual_usage.values())
        
        allocation.efficiency_score = total_used / total_allocated if total_allocated > 0 else 0.0
        
        for resource_type, amount in actual_usage.items():
            if resource_type in self._quotas:
                self._quotas[resource_type].consumed += amount
        
        await self._persist_allocation(allocation)
        
        return True
    
    async def release_allocation(
        self,
        allocation_id: str,
    ) -> bool:
        """
        Release an allocation and free resources.
        
        Args:
            allocation_id: ID of the allocation
        
        Returns:
            True if released successfully
        """
        if allocation_id not in self._allocations:
            return False
        
        allocation = self._allocations[allocation_id]
        
        if not allocation.is_active:
            return False
        
        for resource_type, amount in allocation.resources.items():
            if resource_type in self._quotas:
                self._quotas[resource_type].allocated -= amount
        
        allocation.is_active = False
        await self._persist_allocation(allocation)
        
        logger.info(f"Released allocation {allocation_id}")
        
        return True
    
    async def optimize_allocations(self) -> List[BudgetOptimization]:
        """
        Analyze allocations and generate optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        optimizations = []
        
        inefficient_allocations = [
            a for a in self._allocations.values()
            if a.is_active and a.efficiency_score > 0 and 
            a.efficiency_score < self._budget_config['efficiency_threshold']
        ]
        
        if inefficient_allocations:
            total_waste = {}
            for allocation in inefficient_allocations:
                for resource_type, allocated in allocation.resources.items():
                    used = allocation.actual_usage.get(resource_type, 0)
                    waste = allocated - used
                    total_waste[resource_type] = total_waste.get(resource_type, 0) + waste
            
            optimizations.append(BudgetOptimization(
                optimization_id=f"OPT-{uuid.uuid4().hex[:8]}",
                description=f"Reduce over-allocation in {len(inefficient_allocations)} tasks",
                potential_savings=total_waste,
                estimated_impact=0.15,
                actions=[
                    {'action': 'right_size_allocations', 'target_efficiency': 0.85},
                    {'action': 'review_inefficient_tasks', 'count': len(inefficient_allocations)},
                ],
                priority=AllocationPriority.MEDIUM,
                created_at=datetime.now(timezone.utc),
            ))
        
        expired_allocations = [
            a for a in self._allocations.values()
            if a.is_active and a.expires_at and datetime.now(timezone.utc) > a.expires_at
        ]
        
        if expired_allocations:
            freed_resources = {}
            for allocation in expired_allocations:
                for resource_type, amount in allocation.resources.items():
                    freed_resources[resource_type] = freed_resources.get(resource_type, 0) + amount
            
            optimizations.append(BudgetOptimization(
                optimization_id=f"OPT-{uuid.uuid4().hex[:8]}",
                description=f"Release {len(expired_allocations)} expired allocations",
                potential_savings=freed_resources,
                estimated_impact=0.10,
                actions=[
                    {'action': 'release_expired', 'count': len(expired_allocations)},
                ],
                priority=AllocationPriority.HIGH,
                created_at=datetime.now(timezone.utc),
            ))
        
        for resource_type, quota in self._quotas.items():
            if quota.utilization() > 0.9:
                optimizations.append(BudgetOptimization(
                    optimization_id=f"OPT-{uuid.uuid4().hex[:8]}",
                    description=f"{resource_type.value} utilization at {quota.utilization():.1%}",
                    potential_savings={},
                    estimated_impact=0.20,
                    actions=[
                        {'action': 'scale_up_quota', 'resource': resource_type.value, 'increase': 0.2},
                        {'action': 'review_allocations', 'resource': resource_type.value},
                    ],
                    priority=AllocationPriority.HIGH,
                    created_at=datetime.now(timezone.utc),
                ))
        
        self._optimizations.extend(optimizations)
        
        logger.info(f"Generated {len(optimizations)} optimization recommendations")
        
        return optimizations
    
    async def apply_optimization(
        self,
        optimization_id: str,
    ) -> bool:
        """
        Apply an optimization recommendation.
        
        Args:
            optimization_id: ID of the optimization
        
        Returns:
            True if applied successfully
        """
        optimization = next(
            (o for o in self._optimizations if o.optimization_id == optimization_id),
            None
        )
        
        if not optimization:
            return False
        
        for action in optimization.actions:
            action_type = action.get('action')
            
            if action_type == 'release_expired':
                expired = [
                    a for a in self._allocations.values()
                    if a.is_active and a.expires_at and datetime.now(timezone.utc) > a.expires_at
                ]
                for allocation in expired:
                    await self.release_allocation(allocation.allocation_id)
            
            elif action_type == 'right_size_allocations':
                target_efficiency = action.get('target_efficiency', 0.85)
                inefficient = [
                    a for a in self._allocations.values()
                    if a.is_active and a.efficiency_score > 0 and a.efficiency_score < target_efficiency
                ]
                for allocation in inefficient:
                    logger.info(f"Flagged allocation {allocation.allocation_id} for right-sizing")
            
            elif action_type == 'scale_up_quota':
                resource = ResourceType(action.get('resource'))
                increase = action.get('increase', 0.2)
                if resource in self._quotas:
                    self._quotas[resource].total_quota *= (1 + increase)
                    logger.info(f"Scaled up {resource.value} quota by {increase:.1%}")
        
        logger.info(f"Applied optimization {optimization_id}")
        
        return True
    
    async def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        status = {
            'quotas': {rt.value: quota.to_dict() for rt, quota in self._quotas.items()},
            'active_allocations': len([a for a in self._allocations.values() if a.is_active]),
            'total_allocations': len(self._allocations),
            'overall_utilization': sum(q.utilization() for q in self._quotas.values()) / len(self._quotas),
            'pending_optimizations': len(self._optimizations),
        }
        
        for resource_type, quota in self._quotas.items():
            if quota.utilization() > 0.9:
                status.setdefault('warnings', []).append(
                    f"{resource_type.value} utilization critical: {quota.utilization():.1%}"
                )
        
        return status
    
    def get_allocation(self, allocation_id: str) -> Optional[BudgetAllocation]:
        """Get an allocation by ID."""
        return self._allocations.get(allocation_id)
    
    def get_active_allocations(self) -> List[BudgetAllocation]:
        """Get all active allocations."""
        return [a for a in self._allocations.values() if a.is_active]
    
    def get_allocations_by_task_type(self, task_type: str) -> List[BudgetAllocation]:
        """Get allocations for a specific task type."""
        return [a for a in self._allocations.values() if a.task_type == task_type]
    
    async def _persist_allocation(self, allocation: BudgetAllocation):
        """Persist allocation to storage."""
        alloc_file = self.storage_path / 'allocations' / f"{allocation.allocation_id}.json"
        alloc_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alloc_file, 'w') as f:
            json.dump(allocation.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get budget controller statistics."""
        active = [a for a in self._allocations.values() if a.is_active]
        
        avg_efficiency = sum(a.efficiency_score for a in active if a.efficiency_score > 0) / len(active) if active else 0
        
        priority_counts = {}
        for allocation in active:
            priority_counts[allocation.priority.value] = priority_counts.get(allocation.priority.value, 0) + 1
        
        return {
            'total_allocations': len(self._allocations),
            'active_allocations': len(active),
            'average_efficiency': avg_efficiency,
            'allocations_by_priority': priority_counts,
            'resource_utilization': {rt.value: quota.utilization() for rt, quota in self._quotas.items()},
            'pending_optimizations': len(self._optimizations),
        }
