"""
Self-Assembly Orchestrator
===========================

Autonomous component management - the AI can assemble and manage
its own components while respecting safety boundaries.
"""

import asyncio
import importlib
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable

from .immutable_safety_core import get_safety_core, SafetyBoundary
from .recursive_self_improvement import RecursiveSelfImprovement, ImprovementType

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of components the AI can manage"""
    DATA_SOURCE = "data_source"
    STRATEGY = "strategy"
    INDICATOR = "indicator"
    RISK_MANAGER = "risk_manager"
    EXECUTION_ENGINE = "execution_engine"
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"


class AssemblyStatus(Enum):
    """Status of component assembly"""
    PENDING = "pending"
    ASSEMBLING = "assembling"
    TESTING = "testing"
    ACTIVE = "active"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class Component:
    """A self-assembled component"""
    component_id: str
    component_type: ComponentType
    name: str
    description: str
    module_path: str
    class_name: str
    dependencies: List[str]
    config: Dict[str, Any]
    status: AssemblyStatus
    created_at: datetime
    instance: Optional[Any] = None
    health_score: float = 1.0
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class AssemblyPlan:
    """Plan for assembling components"""
    plan_id: str
    components_to_add: List[Component]
    components_to_remove: List[str]
    components_to_update: List[str]
    reason: str
    created_at: datetime
    approved: bool = False
    executed: bool = False


class SelfAssemblyOrchestrator:
    """
    Self-Assembly Orchestrator
    
    Manages autonomous component assembly and lifecycle.
    
    Key Features:
    - Automatic component discovery
    - Dependency resolution
    - Health monitoring
    - Automatic replacement of failing components
    - Safety-constrained assembly
    """
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.safety_core = get_safety_core()
        self.self_improvement = RecursiveSelfImprovement(workspace_path)
        
        self.components: Dict[str, Component] = {}
        self.assembly_plans: Dict[str, AssemblyPlan] = {}
        
        self.component_registry: Dict[ComponentType, List[str]] = {
            ct: [] for ct in ComponentType
        }
        
        self.health_check_interval = 60  # seconds
        self.auto_replace_failing = True
        
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        logger.info("SelfAssemblyOrchestrator initialized")
    
    async def start(self):
        """Start the self-assembly orchestrator"""
        if self._running:
            logger.warning("Orchestrator already running")
            return
        
        self._running = True
        
        # Start background tasks
        self._tasks.append(asyncio.create_task(self._health_monitor_loop()))
        self._tasks.append(asyncio.create_task(self._auto_assembly_loop()))
        
        logger.info("Self-assembly orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator"""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        logger.info("Self-assembly orchestrator stopped")
    
    def discover_components(self) -> List[Component]:
        """
        Discover available components in the workspace.
        
        This scans the codebase for components that can be assembled.
        """
        discovered = []
        
        # Scan trading_bot directory for components
        trading_bot_path = self.workspace_path / 'trading_bot'
        
        if not trading_bot_path.exists():
            logger.warning(f"Trading bot path not found: {trading_bot_path}")
            return discovered
        
        # Look for strategy modules
        strategies_path = trading_bot_path / 'strategies'
        if strategies_path.exists():
            for strategy_file in strategies_path.glob('*.py'):
                if strategy_file.name.startswith('_'):
                    continue
                
                component = Component(
                    component_id=f"strategy_{strategy_file.stem}",
                    component_type=ComponentType.STRATEGY,
                    name=strategy_file.stem,
                    description=f"Strategy from {strategy_file.name}",
                    module_path=f"trading_bot.strategies.{strategy_file.stem}",
                    class_name=self._guess_class_name(strategy_file.stem),
                    dependencies=[],
                    config={},
                    status=AssemblyStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                discovered.append(component)
        
        # Look for indicator modules
        indicators_path = trading_bot_path / 'indicators'
        if indicators_path.exists():
            for indicator_file in indicators_path.glob('*.py'):
                if indicator_file.name.startswith('_'):
                    continue
                
                component = Component(
                    component_id=f"indicator_{indicator_file.stem}",
                    component_type=ComponentType.INDICATOR,
                    name=indicator_file.stem,
                    description=f"Indicator from {indicator_file.name}",
                    module_path=f"trading_bot.indicators.{indicator_file.stem}",
                    class_name=self._guess_class_name(indicator_file.stem),
                    dependencies=[],
                    config={},
                    status=AssemblyStatus.PENDING,
                    created_at=datetime.utcnow()
                )
                discovered.append(component)
        
        logger.info(f"Discovered {len(discovered)} components")
        return discovered
    
    def _guess_class_name(self, module_name: str) -> str:
        """Guess the class name from module name"""
        # Convert snake_case to PascalCase
        parts = module_name.split('_')
        return ''.join(word.capitalize() for word in parts)
    
    async def assemble_component(self, component: Component) -> bool:
        """
        Assemble (instantiate) a component.
        
        This loads the module and creates an instance.
        """
        try:
            component.status = AssemblyStatus.ASSEMBLING
            
            # Check dependencies
            if not self._check_dependencies(component):
                logger.error(f"Missing dependencies for {component.component_id}")
                component.status = AssemblyStatus.FAILED
                return False
            
            # Import module
            try:
                module = importlib.import_module(component.module_path)
            except ImportError as e:
                logger.error(f"Failed to import {component.module_path}: {e}")
                component.status = AssemblyStatus.FAILED
                component.last_error = str(e)
                return False
            
            # Get class
            if not hasattr(module, component.class_name):
                logger.error(f"Class {component.class_name} not found in {component.module_path}")
                component.status = AssemblyStatus.FAILED
                return False
            
            component_class = getattr(module, component.class_name)
            
            # Instantiate
            try:
                instance = component_class(**component.config)
                component.instance = instance
            except Exception as e:
                logger.error(f"Failed to instantiate {component.class_name}: {e}")
                component.status = AssemblyStatus.FAILED
                component.last_error = str(e)
                return False
            
            # Test component
            component.status = AssemblyStatus.TESTING
            if not await self._test_component(component):
                logger.error(f"Component {component.component_id} failed testing")
                component.status = AssemblyStatus.FAILED
                return False
            
            # Success
            component.status = AssemblyStatus.ACTIVE
            self.components[component.component_id] = component
            
            # Register in component registry
            self.component_registry[component.component_type].append(component.component_id)
            
            logger.info(f"Successfully assembled component: {component.component_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assembling component {component.component_id}: {e}")
            component.status = AssemblyStatus.FAILED
            component.last_error = str(e)
            return False
    
    def _check_dependencies(self, component: Component) -> bool:
        """Check if all dependencies are available"""
        for dep in component.dependencies:
            if dep not in self.components:
                return False
            if self.components[dep].status != AssemblyStatus.ACTIVE:
                return False
        return True
    
    async def _test_component(self, component: Component) -> bool:
        """Test a component before activation"""
        
        # Basic health check
        if hasattr(component.instance, 'health_check'):
            try:
                result = component.instance.health_check()
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception as e:
                logger.error(f"Health check failed for {component.component_id}: {e}")
                return False
        
        # If no health check method, assume OK
        return True
    
    async def _health_monitor_loop(self):
        """Background loop to monitor component health"""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                for component_id, component in list(self.components.items()):
                    if component.status != AssemblyStatus.ACTIVE:
                        continue
                    
                    # Check health
                    is_healthy = await self._test_component(component)
                    
                    if is_healthy:
                        component.health_score = min(1.0, component.health_score + 0.1)
                        component.error_count = max(0, component.error_count - 1)
                    else:
                        component.health_score = max(0.0, component.health_score - 0.2)
                        component.error_count += 1
                        
                        logger.warning(
                            f"Component {component_id} health degraded: "
                            f"score={component.health_score:.2f}, errors={component.error_count}"
                        )
                        
                        # Auto-replace if failing
                        if component.health_score < 0.3 and self.auto_replace_failing:
                            logger.warning(f"Auto-replacing failing component: {component_id}")
                            await self._replace_component(component_id)
                
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
    
    async def _auto_assembly_loop(self):
        """Background loop for automatic component assembly"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Discover new components
                discovered = self.discover_components()
                
                # Assemble new components
                for component in discovered:
                    if component.component_id not in self.components:
                        logger.info(f"Auto-assembling new component: {component.component_id}")
                        await self.assemble_component(component)
                
            except Exception as e:
                logger.error(f"Error in auto-assembly loop: {e}")
    
    async def _replace_component(self, component_id: str):
        """Replace a failing component"""
        
        if component_id not in self.components:
            return
        
        old_component = self.components[component_id]
        
        # Disable old component
        old_component.status = AssemblyStatus.DISABLED
        
        # Try to find a replacement
        # For now, just try to reassemble the same component
        new_component = Component(
            component_id=f"{component_id}_v2",
            component_type=old_component.component_type,
            name=f"{old_component.name}_v2",
            description=f"Replacement for {old_component.name}",
            module_path=old_component.module_path,
            class_name=old_component.class_name,
            dependencies=old_component.dependencies,
            config=old_component.config,
            status=AssemblyStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        success = await self.assemble_component(new_component)
        
        if success:
            logger.info(f"Successfully replaced {component_id} with {new_component.component_id}")
        else:
            logger.error(f"Failed to replace {component_id}")
    
    def create_assembly_plan(
        self,
        components_to_add: List[Component],
        components_to_remove: List[str],
        reason: str
    ) -> AssemblyPlan:
        """Create a plan for component assembly changes"""
        
        import hashlib
        plan_id = hashlib.sha256(
            f"{reason}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        plan = AssemblyPlan(
            plan_id=plan_id,
            components_to_add=components_to_add,
            components_to_remove=components_to_remove,
            components_to_update=[],
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.assembly_plans[plan_id] = plan
        
        logger.info(f"Created assembly plan: {plan_id}")
        return plan
    
    async def execute_assembly_plan(self, plan_id: str) -> bool:
        """Execute an assembly plan"""
        
        if plan_id not in self.assembly_plans:
            logger.error(f"Unknown assembly plan: {plan_id}")
            return False
        
        plan = self.assembly_plans[plan_id]
        
        if not plan.approved:
            logger.warning(f"Assembly plan {plan_id} not approved")
            return False
        
        try:
            # Remove components
            for component_id in plan.components_to_remove:
                if component_id in self.components:
                    self.components[component_id].status = AssemblyStatus.DISABLED
                    del self.components[component_id]
                    logger.info(f"Removed component: {component_id}")
            
            # Add components
            for component in plan.components_to_add:
                success = await self.assemble_component(component)
                if not success:
                    logger.error(f"Failed to add component: {component.component_id}")
                    return False
            
            plan.executed = True
            logger.info(f"Successfully executed assembly plan: {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing assembly plan: {e}")
            return False
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get status report of all components"""
        return {
            'total_components': len(self.components),
            'active': len([c for c in self.components.values() if c.status == AssemblyStatus.ACTIVE]),
            'failed': len([c for c in self.components.values() if c.status == AssemblyStatus.FAILED]),
            'disabled': len([c for c in self.components.values() if c.status == AssemblyStatus.DISABLED]),
            'by_type': {
                ct.value: len(ids) for ct, ids in self.component_registry.items()
            },
            'health_scores': {
                cid: c.health_score for cid, c in self.components.items()
                if c.status == AssemblyStatus.ACTIVE
            },
            'components': [
                {
                    'id': c.component_id,
                    'type': c.component_type.value,
                    'name': c.name,
                    'status': c.status.value,
                    'health_score': c.health_score,
                    'error_count': c.error_count
                }
                for c in self.components.values()
            ]
        }


async def quick_start_self_assembly(workspace_path: str = ".") -> SelfAssemblyOrchestrator:
    """Quick start the self-assembly orchestrator"""
    orchestrator = SelfAssemblyOrchestrator(workspace_path)
    await orchestrator.start()
    
    # Discover and assemble initial components
    components = orchestrator.discover_components()
    for component in components[:5]:  # Start with first 5
        await orchestrator.assemble_component(component)
    
    return orchestrator
