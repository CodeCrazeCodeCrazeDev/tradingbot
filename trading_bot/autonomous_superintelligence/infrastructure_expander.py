"""
Infrastructure Expansion System
Autonomously expands infrastructure, launches new domains, and scales globally.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class InfrastructureType(Enum):
    COMPUTE_CLUSTER = "compute_cluster"
    DATA_PIPELINE = "data_pipeline"
    TRADING_VENUE = "trading_venue"
    RESEARCH_LAB = "research_lab"
    MODEL_REGISTRY = "model_registry"
    MONITORING_SYSTEM = "monitoring_system"
    BACKUP_SYSTEM = "backup_system"


@dataclass
class InfrastructureComponent:
    component_id: str
    component_type: InfrastructureType
    name: str
    region: str
    capacity: float
    utilization: float
    cost: float
    created_at: datetime
    status: str = "active"


@dataclass
class ExpansionPlan:
    plan_id: str
    target_region: str
    components: List[str]
    estimated_cost: float
    expected_capacity: float
    priority: float
    created_at: datetime
    status: str = "planned"


class InfrastructureExpander:
    """
    Autonomously expands infrastructure based on demand and opportunities.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.infrastructure: Dict[str, InfrastructureComponent] = {}
        self.expansion_plans: List[ExpansionPlan] = []
        
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'infrastructure_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Infrastructure Expander initialized")
    
    async def initialize(self):
        """Initialize infrastructure expander."""
        logger.info("Initializing Infrastructure Expander")
        
        await self._load_infrastructure()
        
        if not self.infrastructure:
            await self._deploy_initial_infrastructure()
        
        self.running = True
        logger.info("Infrastructure Expander ready - %d components", len(self.infrastructure))
    
    async def _load_infrastructure(self):
        """Load existing infrastructure."""
        infra_file = self.storage_path / 'infrastructure.json'
        if infra_file.exists():
            with open(infra_file, 'r') as f:
                data = json.load(f)
                for comp_data in data:
                    component = InfrastructureComponent(
                        component_id=comp_data['component_id'],
                        component_type=InfrastructureType(comp_data['component_type']),
                        name=comp_data['name'],
                        region=comp_data['region'],
                        capacity=comp_data['capacity'],
                        utilization=comp_data['utilization'],
                        cost=comp_data['cost'],
                        created_at=datetime.fromisoformat(comp_data['created_at']),
                        status=comp_data.get('status', 'active'),
                    )
                    self.infrastructure[component.component_id] = component
    
    async def _deploy_initial_infrastructure(self):
        """Deploy initial infrastructure components."""
        initial_components = [
            (InfrastructureType.COMPUTE_CLUSTER, 'Primary Compute', 'US-East', 100.0, 50.0),
            (InfrastructureType.DATA_PIPELINE, 'Market Data Pipeline', 'Global', 1000.0, 100.0),
            (InfrastructureType.TRADING_VENUE, 'Primary Trading', 'US-East', 50.0, 200.0),
            (InfrastructureType.RESEARCH_LAB, 'Research Lab Alpha', 'US-West', 80.0, 150.0),
            (InfrastructureType.MODEL_REGISTRY, 'Model Registry', 'US-East', 200.0, 20.0),
        ]
        
        for comp_type, name, region, capacity, cost in initial_components:
            await self.deploy_component(comp_type, name, region, capacity, cost)
    
    async def deploy_component(
        self,
        component_type: InfrastructureType,
        name: str,
        region: str,
        capacity: float,
        cost: float
    ) -> InfrastructureComponent:
        """Deploy a new infrastructure component."""
        component = InfrastructureComponent(
            component_id=f"infra_{datetime.now().timestamp()}",
            component_type=component_type,
            name=name,
            region=region,
            capacity=capacity,
            utilization=0.0,
            cost=cost,
            created_at=datetime.now(),
        )
        
        self.infrastructure[component.component_id] = component
        
        logger.info("Deployed infrastructure: %s in %s", name, region)
        
        return component
    
    async def plan_expansion(
        self,
        target_region: str,
        required_capacity: float
    ) -> ExpansionPlan:
        """Plan infrastructure expansion."""
        plan = ExpansionPlan(
            plan_id=f"plan_{datetime.now().timestamp()}",
            target_region=target_region,
            components=[],
            estimated_cost=required_capacity * 100,
            expected_capacity=required_capacity,
            priority=0.7,
            created_at=datetime.now(),
        )
        
        self.expansion_plans.append(plan)
        
        logger.info("Created expansion plan for %s (capacity: %.2f)",
                   target_region, required_capacity)
        
        return plan
    
    async def execute_expansion(self, plan: ExpansionPlan) -> bool:
        """Execute an expansion plan."""
        logger.info("Executing expansion plan: %s", plan.plan_id)
        
        plan.status = "executing"
        
        try:
            await self.deploy_component(
                InfrastructureType.COMPUTE_CLUSTER,
                f"Compute {plan.target_region}",
                plan.target_region,
                plan.expected_capacity,
                plan.estimated_cost
            )
            
            plan.status = "completed"
            logger.info("Expansion completed: %s", plan.target_region)
            return True
            
        except Exception as e:
            logger.error("Expansion failed: %s", e)
            plan.status = "failed"
            return False
    
    async def expansion_loop(self):
        """Main expansion loop."""
        logger.info("Starting infrastructure expansion loop")
        
        while self.running:
            try:
                await self._monitor_capacity()
                
                await self._execute_pending_expansions()
                
                await self._persist_state()
                
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error("Error in expansion loop: %s", e)
                await asyncio.sleep(60)
    
    async def _monitor_capacity(self):
        """Monitor infrastructure capacity and plan expansions."""
        for component in self.infrastructure.values():
            if component.utilization > 0.8:
                logger.warning("Component %s over-utilized: %.1f%%",
                             component.name, component.utilization * 100)
                
                await self.plan_expansion(component.region, component.capacity * 0.5)
    
    async def _execute_pending_expansions(self):
        """Execute pending expansion plans."""
        pending = [p for p in self.expansion_plans if p.status == "planned"]
        
        for plan in pending[:2]:
            await self.execute_expansion(plan)
    
    async def _persist_state(self):
        """Persist infrastructure state."""
        infra_file = self.storage_path / 'infrastructure.json'
        infra_data = [
            {
                'component_id': c.component_id,
                'component_type': c.component_type.value,
                'name': c.name,
                'region': c.region,
                'capacity': c.capacity,
                'utilization': c.utilization,
                'cost': c.cost,
                'created_at': c.created_at.isoformat(),
                'status': c.status,
            }
            for c in self.infrastructure.values()
        ]
        
        with open(infra_file, 'w') as f:
            json.dump(infra_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get infrastructure status."""
        return {
            'total_components': len(self.infrastructure),
            'active_components': sum(1 for c in self.infrastructure.values() if c.status == 'active'),
            'total_capacity': sum(c.capacity for c in self.infrastructure.values()),
            'total_cost': sum(c.cost for c in self.infrastructure.values()),
            'expansion_plans': len(self.expansion_plans),
            'regions': len(set(c.region for c in self.infrastructure.values())),
        }
    
    async def shutdown(self):
        """Shutdown infrastructure expander."""
        logger.info("Shutting down Infrastructure Expander")
        self.running = False
        await self._persist_state()
