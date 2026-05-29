"""
Self-Coordinating AI Core - Complete Integration

Integrates all coordination capabilities:
- Task Decomposition
- Agent Negotiation
- Resource Allocation
- Failure Recovery
- Coordination Layer
- Shared Memory
- Governance
- Learning Loop
- Dynamic Sub-Agent Creation

All following DeepMind, OpenAI, and Anthropic patterns.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path

# Import coordination components
from .coordination_core import (
    Task, TaskType, TaskPriority, TaskStatus,
    TaskDecomposer, AgentNegotiator, ResourceAllocator,
    FailureRecoverySystem, FailureType
)
from .coordination_core_part2 import (
    CoordinationLayer, SharedMemory, SharedMemoryScope,
    GovernanceSystem, CoordinationLearningLoop
)
from .dynamic_agent_factory import (
    DynamicAgentFactory, AgentArchetype, SubAgent
)

logger = logging.getLogger(__name__)


@dataclass
class CoordinationMetrics:
    """Metrics for coordination performance"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_tasks: int = 0
    
    total_agents: int = 0
    active_agents: int = 0
    
    avg_task_duration: float = 0.0
    avg_resource_efficiency: float = 0.0
    coordination_success_rate: float = 1.0
    
    governance_violations: int = 0
    safety_checks_passed: int = 0
    
    def update_from_task(self, task: Task, duration: float, efficiency: float):
        """Update metrics from completed task"""
        self.completed_tasks += 1
        
        # Update averages
        n = self.completed_tasks
        self.avg_task_duration = (self.avg_task_duration * (n - 1) + duration) / n
        self.avg_resource_efficiency = (self.avg_resource_efficiency * (n - 1) + efficiency) / n
        
        # Update success rate
        self.coordination_success_rate = self.completed_tasks / max(self.total_tasks, 1)


class SelfCoordinatingCore:
    """
    Self-Coordinating AI Core
    
    The master coordination system that enables the AI to:
    1. Break down complex tasks hierarchically
    2. Negotiate with agents for task allocation
    3. Allocate resources efficiently
    4. Recover from failures gracefully
    5. Coordinate multi-agent communication
    6. Share memory across agents
    7. Enforce governance and safety
    8. Learn from coordination experiences
    9. Create specialized sub-agents dynamically
    
    Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │         SELF-COORDINATING AI CORE                            │
    │                                                              │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  TASK DECOMPOSITION (HTN Planning)                     │ │
    │  │  Complex Task → Subtasks → Atomic Tasks                │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  AGENT NEGOTIATION (Contract Net Protocol)             │ │
    │  │  Announce → Bid → Award → Contract                     │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  RESOURCE ALLOCATION (Priority Scheduling)             │ │
    │  │  CPU, Memory, Network, API Quota                       │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  COORDINATION LAYER (Message Passing)                  │ │
    │  │  Agent A ←→ Message Bus ←→ Agent B                     │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  SHARED MEMORY (Collaborative Workspace)               │ │
    │  │  Global, Team, Private scopes                          │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  GOVERNANCE (Constitutional AI)                        │ │
    │  │  Safety, Compliance, Oversight                         │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  FAILURE RECOVERY (Retry, Reassign, Rollback)          │ │
    │  │  Exponential backoff, Checkpoints                      │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  LEARNING LOOP (Experience → Knowledge)                │ │
    │  │  Pattern recognition, Performance optimization         │ │
    │  └────────────────────────────────────────────────────────┘ │
    │                          ↓                                   │
    │  ┌────────────────────────────────────────────────────────┐ │
    │  │  DYNAMIC SUB-AGENT FACTORY                             │ │
    │  │  Create specialized agents on-demand                   │ │
    │  │  AlphaGo, ReAct, Constitutional patterns               │ │
    │  └────────────────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(
        self,
        policy_network=None,
        value_network=None,
        react_loop=None,
        constitutional_layer=None,
        memory_system=None,
        tool_registry=None,
        agent_registry=None,
        config: Optional[Dict] = None
    ):
        self.config = config or {}
        
        # Core components (injected)
        self.policy_network = policy_network
        self.value_network = value_network
        self.react_loop = react_loop
        self.constitutional_layer = constitutional_layer
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry
        
        # Initialize coordination components
        self.task_decomposer = TaskDecomposer()
        self.agent_negotiator = AgentNegotiator()
        self.resource_allocator = ResourceAllocator(self.config.get('resources', {}))
        self.failure_recovery = FailureRecoverySystem()
        self.coordination_layer = CoordinationLayer()
        self.shared_memory = SharedMemory()
        self.governance = GovernanceSystem(constitutional_layer)
        self.learning_loop = CoordinationLearningLoop(memory_system)
        
        # Dynamic agent factory
        self.agent_factory = DynamicAgentFactory(
            policy_network=policy_network,
            value_network=value_network,
            react_loop=react_loop,
            constitutional_layer=constitutional_layer,
            memory_system=memory_system,
            tool_registry=tool_registry,
            agent_registry=agent_registry
        )
        
        # State
        self.running = False
        self.metrics = CoordinationMetrics()
        
        # Task tracking
        self.active_tasks: Dict[str, Task] = {}
        self.task_start_times: Dict[str, datetime] = {}
        
        logger.info("=" * 60)
        logger.info("SELF-COORDINATING AI CORE")
        logger.info("=" * 60)
        logger.info("Capabilities: Task Decomposition, Agent Negotiation,")
        logger.info("             Resource Allocation, Failure Recovery,")
        logger.info("             Coordination, Shared Memory, Governance,")
        logger.info("             Learning, Dynamic Sub-Agent Creation")
        logger.info("=" * 60)
    
    async def initialize(self):
        """Initialize the coordination core"""
        logger.info("Initializing Self-Coordinating AI Core...")
        
        # Create default teams in shared memory
        self.shared_memory.create_team('trading_team', set())
        self.shared_memory.create_team('research_team', set())
        self.shared_memory.create_team('safety_team', set())
        
        # Create initial sub-agents
        await self._create_initial_agents()
        
        self.running = True
        
        logger.info("Self-Coordinating AI Core initialized")
    
    async def _create_initial_agents(self):
        """Create initial set of sub-agents"""
        initial_agents = [
            ('react_reasoner', 'MainReasoner', 'trading_team'),
            ('constitutional_guardian', 'SafetyGuardian', 'safety_team'),
            ('analyst', 'MarketAnalyst', 'trading_team'),
            ('monitor', 'SystemMonitor', None),
        ]
        
        for template_id, name, team in initial_agents:
            agent = await self.agent_factory.create_agent(
                template_id=template_id,
                name=name
            )
            
            # Add to team if specified
            if team:
                self.shared_memory.add_to_team(team, agent.agent_id)
            
            logger.info(f"Created initial agent: {name}")
    
    async def execute_task(
        self,
        task_name: str,
        task_type: TaskType,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using full coordination capabilities.
        
        This is the main entry point for task execution.
        """
        # Create task
        task = Task(
            task_id=str(asyncio.current_task()),
            name=task_name,
            task_type=task_type,
            priority=priority,
            description=description,
            required_capabilities=required_capabilities or [],
            metadata=metadata or {}
        )
        
        self.metrics.total_tasks += 1
        self.active_tasks[task.task_id] = task
        self.task_start_times[task.task_id] = datetime.now()
        
        logger.info(f"Executing task: {task_name} ({task_type.value}, priority: {priority.value})")
        
        try:
            # Step 1: Task Decomposition
            subtasks = await self.task_decomposer.decompose(task)
            logger.info(f"Decomposed into {len(subtasks)} subtasks")
            
            # Step 2: Process subtasks
            results = []
            for subtask in subtasks:
                if subtask.is_leaf():
                    result = await self._execute_atomic_task(subtask)
                    results.append(result)
            
            # Aggregate results
            success = all(r.get('success', False) for r in results)
            
            # Update metrics
            duration = (datetime.now() - self.task_start_times[task.task_id]).total_seconds()
            efficiency = self._calculate_efficiency(task, results)
            
            self.metrics.update_from_task(task, duration, efficiency)
            
            # Record experience for learning
            await self.learning_loop.record_experience(
                task=task,
                agents_involved=[r.get('agent_id', 'unknown') for r in results],
                coordination_pattern='hierarchical',
                success=success,
                duration=duration,
                resource_efficiency=efficiency,
                quality=sum(r.get('quality', 0.5) for r in results) / max(len(results), 1)
            )
            
            return {
                'success': success,
                'task_id': task.task_id,
                'subtasks_completed': len(results),
                'duration': duration,
                'efficiency': efficiency,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.metrics.failed_tasks += 1
            
            # Handle failure
            recovery_action = await self.failure_recovery.handle_failure(
                task=task,
                failure_type=FailureType.TASK_FAILURE,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'recovery_action': recovery_action
            }
        
        finally:
            # Cleanup
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            if task.task_id in self.task_start_times:
                del self.task_start_times[task.task_id]
    
    async def _execute_atomic_task(self, task: Task) -> Dict[str, Any]:
        """Execute an atomic (leaf) task"""
        logger.info(f"Executing atomic task: {task.name}")
        
        # Step 1: Find or create agent for task
        agent = self.agent_factory.get_best_agent_for_task(task)
        
        if not agent:
            # Create new agent for this task
            logger.info(f"Creating new agent for task {task.name}")
            agent = await self.agent_factory.create_agent_for_task(task)
        
        if not agent:
            return {'success': False, 'error': 'No suitable agent available'}
        
        # Step 2: Governance check
        is_compliant, violations = await self.governance.check_compliance(
            agent_id=agent.agent_id,
            action={'task': task.to_dict()},
            task=task
        )
        
        if not is_compliant:
            logger.warning(f"Governance violations: {violations}")
            self.metrics.governance_violations += len(violations)
            return {'success': False, 'error': 'Governance check failed', 'violations': violations}
        
        self.metrics.safety_checks_passed += 1
        
        # Step 3: Resource allocation
        allocation_id = await self.resource_allocator.allocate(
            task=task,
            agent_id=agent.agent_id,
            required_resources=task.required_resources or {'cpu': 1.0, 'memory': 1.0}
        )
        
        if not allocation_id:
            logger.warning(f"Resource allocation failed for task {task.name}")
            return {'success': False, 'error': 'Insufficient resources'}
        
        try:
            # Step 4: Create checkpoint for recovery
            await self.failure_recovery.create_checkpoint(
                task.task_id,
                {'task': task.to_dict(), 'agent_id': agent.agent_id}
            )
            
            # Step 5: Execute task with agent
            task.status = TaskStatus.IN_PROGRESS
            task.assigned_agent_id = agent.agent_id
            
            result = await agent.execute_task(task)
            
            # Step 6: Mark task complete
            if result.get('success'):
                self.task_decomposer.mark_completed(task.task_id, result)
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.FAILED
            
            # Step 7: Broadcast completion
            await self.coordination_layer.broadcast(
                sender_id=agent.agent_id,
                topic='task_complete',
                content={
                    'task_id': task.task_id,
                    'task_name': task.name,
                    'success': result.get('success'),
                    'agent_id': agent.agent_id
                }
            )
            
            # Step 8: Store result in shared memory
            await self.shared_memory.write(
                key=f"task_result_{task.task_id}",
                value=result,
                agent_id=agent.agent_id,
                scope=SharedMemoryScope.GLOBAL
            )
            
            return {
                **result,
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'quality': 0.8  # Could be computed from result
            }
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            
            # Handle failure
            recovery_action = await self.failure_recovery.handle_failure(
                task=task,
                failure_type=FailureType.TASK_FAILURE,
                error_message=str(e),
                agent_id=agent.agent_id
            )
            
            if recovery_action == 'retry':
                # Retry the task
                return await self._execute_atomic_task(task)
            
            return {'success': False, 'error': str(e), 'recovery_action': recovery_action}
        
        finally:
            # Release resources
            if allocation_id:
                await self.resource_allocator.release(allocation_id)
    
    def _calculate_efficiency(self, task: Task, results: List[Dict]) -> float:
        """Calculate resource efficiency"""
        # Simple efficiency calculation
        # In production, would consider actual resource usage
        successful = sum(1 for r in results if r.get('success', False))
        return successful / max(len(results), 1)
    
    async def create_sub_agent(
        self,
        archetype: AgentArchetype,
        name: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        parent_agent_id: Optional[str] = None
    ) -> SubAgent:
        """
        Create a sub-agent dynamically.
        
        This allows the AI to create specialized agents as needed.
        """
        template_id = archetype.value
        
        agent = await self.agent_factory.create_agent(
            template_id=template_id,
            name=name,
            parent_agent_id=parent_agent_id,
            additional_capabilities=capabilities
        )
        
        self.metrics.total_agents += 1
        self.metrics.active_agents += 1
        
        # Broadcast agent creation
        await self.coordination_layer.broadcast(
            sender_id='coordination_core',
            topic='agent_created',
            content={
                'agent_id': agent.agent_id,
                'agent_name': agent.name,
                'archetype': archetype.value
            }
        )
        
        logger.info(f"Created sub-agent: {agent.name} ({archetype.value})")
        
        return agent
    
    async def coordinate_multi_agent_task(
        self,
        task_name: str,
        subtasks: List[Dict[str, Any]],
        coordination_pattern: str = 'parallel'
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents on a complex task.
        
        Patterns:
        - sequential: Tasks executed in order
        - parallel: Tasks executed simultaneously
        - hierarchical: Tasks organized in tree structure
        """
        logger.info(f"Coordinating multi-agent task: {task_name} ({coordination_pattern})")
        
        start_time = datetime.now()
        results = []
        
        if coordination_pattern == 'parallel':
            # Execute all subtasks in parallel
            tasks = [
                self.execute_task(
                    task_name=st['name'],
                    task_type=TaskType[st.get('type', 'ANALYSIS').upper()],
                    description=st.get('description', ''),
                    required_capabilities=st.get('capabilities', [])
                )
                for st in subtasks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elif coordination_pattern == 'sequential':
            # Execute subtasks in sequence
            for st in subtasks:
                result = await self.execute_task(
                    task_name=st['name'],
                    task_type=TaskType[st.get('type', 'ANALYSIS').upper()],
                    description=st.get('description', ''),
                    required_capabilities=st.get('capabilities', [])
                )
                results.append(result)
        
        duration = (datetime.now() - start_time).total_seconds()
        success = all(
            r.get('success', False) if isinstance(r, dict) else False
            for r in results
        )
        
        return {
            'success': success,
            'task_name': task_name,
            'coordination_pattern': coordination_pattern,
            'subtasks_completed': len(results),
            'duration': duration,
            'results': results
        }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of coordination core"""
        return {
            'running': self.running,
            'metrics': {
                'total_tasks': self.metrics.total_tasks,
                'completed_tasks': self.metrics.completed_tasks,
                'failed_tasks': self.metrics.failed_tasks,
                'active_tasks': len(self.active_tasks),
                'success_rate': self.metrics.coordination_success_rate,
                'avg_task_duration': self.metrics.avg_task_duration,
                'avg_efficiency': self.metrics.avg_resource_efficiency,
                'governance_violations': self.metrics.governance_violations,
                'safety_checks_passed': self.metrics.safety_checks_passed
            },
            'task_decomposer': {
                'total_tasks': len(self.task_decomposer.tasks),
                'ready_tasks': len(self.task_decomposer.get_ready_tasks())
            },
            'resource_allocator': self.resource_allocator.get_status(),
            'coordination_layer': self.coordination_layer.get_status(),
            'shared_memory': self.shared_memory.get_status(),
            'governance': self.governance.get_compliance_report(),
            'learning_loop': self.learning_loop.get_learning_stats(),
            'agent_factory': self.agent_factory.get_status(),
            'failure_recovery': self.failure_recovery.get_failure_stats()
        }
    
    async def shutdown(self):
        """Shutdown coordination core"""
        logger.info("Shutting down Self-Coordinating AI Core...")
        
        self.running = False
        
        # Terminate all sub-agents
        for agent_id in list(self.agent_factory.agents.keys()):
            await self.agent_factory.terminate_agent(agent_id)
        
        logger.info("Self-Coordinating AI Core shutdown complete")


# Export
__all__ = ['SelfCoordinatingCore', 'CoordinationMetrics']
