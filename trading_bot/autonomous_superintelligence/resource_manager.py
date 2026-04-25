"""
Autonomous Resource Manager
Manages resources globally, allocates compute, deploys capital autonomously.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    CAPITAL = "capital"
    DATA = "data"
    API_CREDITS = "api_credits"


@dataclass
class Resource:
    resource_id: str
    resource_type: ResourceType
    total_capacity: float
    available_capacity: float
    allocated_capacity: float
    unit: str
    cost_per_unit: float
    priority: float = 0.5


@dataclass
class Allocation:
    allocation_id: str
    resource_type: ResourceType
    amount: float
    allocated_to: str
    purpose: str
    priority: float
    created_at: datetime
    expires_at: Optional[datetime] = None
    active: bool = True


@dataclass
class CapitalDeployment:
    deployment_id: str
    amount: float
    target: str
    strategy: str
    expected_return: float
    risk_level: float
    deployed_at: datetime
    status: str = "active"
    actual_return: Optional[float] = None


class AutonomousResourceManager:
    """
    Manages all system resources autonomously - compute, memory, capital, etc.
    Optimizes allocation and deploys capital automatically.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.resources: Dict[str, Resource] = {}
        self.allocations: List[Allocation] = []
        self.capital_deployments: List[CapitalDeployment] = []
        
        self.total_capital = config.get('total_capital', 100000.0)
        self.available_capital = self.total_capital
        self.deployed_capital = 0.0
        
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'resource_manager_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Autonomous Resource Manager initialized")
    
    async def initialize(self):
        """Initialize the resource manager."""
        logger.info("Initializing Autonomous Resource Manager")
        
        await self._initialize_resources()
        await self._load_allocations()
        await self._load_deployments()
        
        self.running = True
        logger.info("Resource Manager ready - managing %.2f in capital", self.total_capital)
    
    async def _initialize_resources(self):
        """Initialize resource pools."""
        self.resources = {
            'compute_cpu': Resource(
                resource_id='compute_cpu',
                resource_type=ResourceType.COMPUTE,
                total_capacity=100.0,
                available_capacity=100.0,
                allocated_capacity=0.0,
                unit='cores',
                cost_per_unit=0.1,
            ),
            'compute_gpu': Resource(
                resource_id='compute_gpu',
                resource_type=ResourceType.COMPUTE,
                total_capacity=8.0,
                available_capacity=8.0,
                allocated_capacity=0.0,
                unit='gpus',
                cost_per_unit=2.0,
            ),
            'memory': Resource(
                resource_id='memory',
                resource_type=ResourceType.MEMORY,
                total_capacity=128.0,
                available_capacity=128.0,
                allocated_capacity=0.0,
                unit='GB',
                cost_per_unit=0.01,
            ),
            'storage': Resource(
                resource_id='storage',
                resource_type=ResourceType.STORAGE,
                total_capacity=10000.0,
                available_capacity=10000.0,
                allocated_capacity=0.0,
                unit='GB',
                cost_per_unit=0.001,
            ),
            'capital': Resource(
                resource_id='capital',
                resource_type=ResourceType.CAPITAL,
                total_capacity=self.total_capital,
                available_capacity=self.available_capital,
                allocated_capacity=0.0,
                unit='USD',
                cost_per_unit=0.0,
                priority=1.0,
            ),
        }
        
        logger.info("Initialized %d resource pools", len(self.resources))
    
    async def _load_allocations(self):
        """Load existing allocations."""
        alloc_file = self.storage_path / 'allocations.json'
        if alloc_file.exists():
            with open(alloc_file, 'r') as f:
                data = json.load(f)
                for alloc_data in data:
                    if alloc_data.get('active', True):
                        allocation = Allocation(
                            allocation_id=alloc_data['allocation_id'],
                            resource_type=ResourceType(alloc_data['resource_type']),
                            amount=alloc_data['amount'],
                            allocated_to=alloc_data['allocated_to'],
                            purpose=alloc_data['purpose'],
                            priority=alloc_data['priority'],
                            created_at=datetime.fromisoformat(alloc_data['created_at']),
                            active=alloc_data.get('active', True),
                        )
                        self.allocations.append(allocation)
    
    async def _load_deployments(self):
        """Load capital deployments."""
        deploy_file = self.storage_path / 'deployments.json'
        if deploy_file.exists():
            with open(deploy_file, 'r') as f:
                data = json.load(f)
                for deploy_data in data:
                    deployment = CapitalDeployment(
                        deployment_id=deploy_data['deployment_id'],
                        amount=deploy_data['amount'],
                        target=deploy_data['target'],
                        strategy=deploy_data['strategy'],
                        expected_return=deploy_data['expected_return'],
                        risk_level=deploy_data['risk_level'],
                        deployed_at=datetime.fromisoformat(deploy_data['deployed_at']),
                        status=deploy_data.get('status', 'active'),
                        actual_return=deploy_data.get('actual_return'),
                    )
                    self.capital_deployments.append(deployment)
                    
                    if deployment.status == 'active':
                        self.deployed_capital += deployment.amount
        
        self.available_capital = self.total_capital - self.deployed_capital
    
    async def allocate_resource(
        self,
        resource_type: ResourceType,
        amount: float,
        allocated_to: str,
        purpose: str,
        priority: float = 0.5
    ) -> Optional[Allocation]:
        """Allocate resources to a consumer."""
        
        resource = self._find_resource(resource_type)
        
        if not resource:
            logger.warning("Resource type not found: %s", resource_type)
            return None
        
        if resource.available_capacity < amount:
            logger.warning("Insufficient %s capacity: requested %.2f, available %.2f",
                         resource_type.value, amount, resource.available_capacity)
            
            freed = await self._free_low_priority_resources(resource_type, amount, priority)
            
            if not freed:
                return None
        
        allocation = Allocation(
            allocation_id=f"alloc_{datetime.now().timestamp()}",
            resource_type=resource_type,
            amount=amount,
            allocated_to=allocated_to,
            purpose=purpose,
            priority=priority,
            created_at=datetime.now(),
        )
        
        resource.available_capacity -= amount
        resource.allocated_capacity += amount
        self.allocations.append(allocation)
        
        logger.info("Allocated %.2f %s to %s for %s",
                   amount, resource.unit, allocated_to, purpose)
        
        return allocation
    
    def _find_resource(self, resource_type: ResourceType) -> Optional[Resource]:
        """Find a resource by type."""
        for resource in self.resources.values():
            if resource.resource_type == resource_type:
                return resource
        return None
    
    async def _free_low_priority_resources(
        self,
        resource_type: ResourceType,
        needed_amount: float,
        min_priority: float
    ) -> bool:
        """Free resources from low-priority allocations."""
        
        low_priority_allocs = [
            alloc for alloc in self.allocations
            if alloc.resource_type == resource_type
            and alloc.active
            and alloc.priority < min_priority
        ]
        
        low_priority_allocs.sort(key=lambda a: a.priority)
        
        freed_amount = 0.0
        for alloc in low_priority_allocs:
            if freed_amount >= needed_amount:
                break
            
            await self.deallocate_resource(alloc.allocation_id)
            freed_amount += alloc.amount
        
        return freed_amount >= needed_amount
    
    async def deallocate_resource(self, allocation_id: str) -> bool:
        """Deallocate resources."""
        allocation = next((a for a in self.allocations if a.allocation_id == allocation_id), None)
        
        if not allocation or not allocation.active:
            return False
        
        resource = self._find_resource(allocation.resource_type)
        if resource:
            resource.available_capacity += allocation.amount
            resource.allocated_capacity -= allocation.amount
        
        allocation.active = False
        
        logger.info("Deallocated %.2f %s from %s",
                   allocation.amount, resource.unit if resource else 'units',
                   allocation.allocated_to)
        
        return True
    
    async def deploy_capital(
        self,
        amount: float,
        target: str,
        strategy: str,
        expected_return: float,
        risk_level: float
    ) -> Optional[CapitalDeployment]:
        """Deploy capital autonomously."""
        
        if amount > self.available_capital:
            logger.warning("Insufficient capital: requested %.2f, available %.2f",
                         amount, self.available_capital)
            return None
        
        max_deployment = self.total_capital * 0.2
        if amount > max_deployment:
            logger.warning("Deployment exceeds maximum (%.2f): %.2f",
                         max_deployment, amount)
            return None
        
        if risk_level > 0.7:
            logger.warning("Risk level too high: %.2f", risk_level)
            return None
        
        deployment = CapitalDeployment(
            deployment_id=f"deploy_{datetime.now().timestamp()}",
            amount=amount,
            target=target,
            strategy=strategy,
            expected_return=expected_return,
            risk_level=risk_level,
            deployed_at=datetime.now(),
        )
        
        self.available_capital -= amount
        self.deployed_capital += amount
        self.capital_deployments.append(deployment)
        
        resource = self.resources.get('capital')
        if resource:
            resource.available_capacity = self.available_capital
            resource.allocated_capacity = self.deployed_capital
        
        logger.info("CAPITAL DEPLOYED: %.2f to %s (expected return: %.2f%%)",
                   amount, target, expected_return * 100)
        
        return deployment
    
    async def optimize_resource_allocation(self):
        """Optimize resource allocation across the system."""
        logger.info("Optimizing resource allocation")
        
        for resource in self.resources.values():
            utilization = resource.allocated_capacity / resource.total_capacity
            
            if utilization > 0.9:
                logger.warning("Resource %s highly utilized: %.1f%%",
                             resource.resource_id, utilization * 100)
                
                await self._scale_resource(resource)
            
            elif utilization < 0.3:
                logger.info("Resource %s underutilized: %.1f%%",
                           resource.resource_id, utilization * 100)
                
                await self._consolidate_resource(resource)
    
    async def _scale_resource(self, resource: Resource):
        """Scale up a resource."""
        scale_factor = 1.5
        additional_capacity = resource.total_capacity * (scale_factor - 1.0)
        
        resource.total_capacity *= scale_factor
        resource.available_capacity += additional_capacity
        
        logger.info("Scaled %s by %.1fx (new capacity: %.2f %s)",
                   resource.resource_id, scale_factor,
                   resource.total_capacity, resource.unit)
    
    async def _consolidate_resource(self, resource: Resource):
        """Consolidate underutilized resources."""
        logger.info("Consolidating %s resources", resource.resource_id)
    
    async def manage_capital_deployments(self):
        """Manage and rebalance capital deployments."""
        for deployment in self.capital_deployments:
            if deployment.status != 'active':
                continue
            
            performance = await self._evaluate_deployment(deployment)
            
            if performance['should_exit']:
                await self._exit_deployment(deployment, performance['reason'])
            
            elif performance['should_increase']:
                await self._increase_deployment(deployment, performance['increase_amount'])
    
    async def _evaluate_deployment(self, deployment: CapitalDeployment) -> Dict[str, Any]:
        """Evaluate a capital deployment."""
        
        simulated_return = np.random.uniform(-0.1, deployment.expected_return * 1.5)
        
        deployment.actual_return = simulated_return
        
        should_exit = simulated_return < -0.05 or simulated_return > deployment.expected_return * 2.0
        should_increase = simulated_return > deployment.expected_return * 1.2 and deployment.risk_level < 0.5
        
        return {
            'current_return': simulated_return,
            'should_exit': should_exit,
            'should_increase': should_increase,
            'increase_amount': deployment.amount * 0.5 if should_increase else 0.0,
            'reason': 'Stop loss triggered' if simulated_return < -0.05 else 'Target reached',
        }
    
    async def _exit_deployment(self, deployment: CapitalDeployment, reason: str):
        """Exit a capital deployment."""
        deployment.status = 'closed'
        
        self.deployed_capital -= deployment.amount
        self.available_capital += deployment.amount
        
        if deployment.actual_return:
            profit = deployment.amount * deployment.actual_return
            self.total_capital += profit
            self.available_capital += profit
        
        resource = self.resources.get('capital')
        if resource:
            resource.total_capacity = self.total_capital
            resource.available_capacity = self.available_capital
            resource.allocated_capacity = self.deployed_capital
        
        logger.info("EXITED DEPLOYMENT: %s - Reason: %s, Return: %.2f%%",
                   deployment.target, reason,
                   (deployment.actual_return or 0.0) * 100)
    
    async def _increase_deployment(self, deployment: CapitalDeployment, amount: float):
        """Increase a capital deployment."""
        if amount <= self.available_capital:
            deployment.amount += amount
            self.available_capital -= amount
            self.deployed_capital += amount
            
            logger.info("INCREASED DEPLOYMENT: %s by %.2f (new total: %.2f)",
                       deployment.target, amount, deployment.amount)
    
    async def resource_management_loop(self):
        """Main resource management loop."""
        logger.info("Starting resource management loop")
        
        while self.running:
            try:
                await self.optimize_resource_allocation()
                
                await self.manage_capital_deployments()
                
                await self._rebalance_portfolio()
                
                await self._persist_state()
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error("Error in resource management loop: %s", e, exc_info=True)
                await asyncio.sleep(30)
    
    async def _rebalance_portfolio(self):
        """Rebalance capital deployment portfolio."""
        if not self.capital_deployments:
            return
        
        active_deployments = [d for d in self.capital_deployments if d.status == 'active']
        
        if not active_deployments:
            return
        
        total_deployed = sum(d.amount for d in active_deployments)
        
        if total_deployed > self.total_capital * 0.8:
            logger.warning("Over-deployed: %.1f%% of capital",
                         (total_deployed / self.total_capital) * 100)
    
    async def _persist_state(self):
        """Persist resource state."""
        alloc_file = self.storage_path / 'allocations.json'
        alloc_data = [
            {
                'allocation_id': a.allocation_id,
                'resource_type': a.resource_type.value,
                'amount': a.amount,
                'allocated_to': a.allocated_to,
                'purpose': a.purpose,
                'priority': a.priority,
                'created_at': a.created_at.isoformat(),
                'active': a.active,
            }
            for a in self.allocations[-1000:]
        ]
        
        with open(alloc_file, 'w') as f:
            json.dump(alloc_data, f, indent=2)
        
        deploy_file = self.storage_path / 'deployments.json'
        deploy_data = [
            {
                'deployment_id': d.deployment_id,
                'amount': d.amount,
                'target': d.target,
                'strategy': d.strategy,
                'expected_return': d.expected_return,
                'risk_level': d.risk_level,
                'deployed_at': d.deployed_at.isoformat(),
                'status': d.status,
                'actual_return': d.actual_return,
            }
            for d in self.capital_deployments
        ]
        
        with open(deploy_file, 'w') as f:
            json.dump(deploy_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get resource manager status."""
        return {
            'total_capital': self.total_capital,
            'available_capital': self.available_capital,
            'deployed_capital': self.deployed_capital,
            'deployment_ratio': self.deployed_capital / self.total_capital if self.total_capital > 0 else 0.0,
            'active_deployments': sum(1 for d in self.capital_deployments if d.status == 'active'),
            'total_allocations': len([a for a in self.allocations if a.active]),
            'resource_utilization': {
                r.resource_id: r.allocated_capacity / r.total_capacity
                for r in self.resources.values()
            },
        }
    
    async def shutdown(self):
        """Shutdown resource manager."""
        logger.info("Shutting down Autonomous Resource Manager")
        self.running = False
        await self._persist_state()
