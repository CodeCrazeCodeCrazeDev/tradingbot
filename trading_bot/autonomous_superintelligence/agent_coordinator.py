"""
Multi-Agent Coordination System
Manages multiple agents, distributes work automatically, and ensures coordination.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

import numpy as np

from ..a2a import A2AMessageBus
from ..world2agent import World2AgentBridge

logger = logging.getLogger(__name__)


class AgentType(Enum):
    MARKET_SCANNER = "market_scanner"
    PATTERN_DETECTOR = "pattern_detector"
    RISK_OPTIMIZER = "risk_optimizer"
    STRATEGY_DEVELOPER = "strategy_developer"
    DATA_ANALYST = "data_analyst"
    RESEARCH_SCIENTIST = "research_scientist"
    OPPORTUNITY_HUNTER = "opportunity_hunter"
    INFRASTRUCTURE_MANAGER = "infrastructure_manager"
    RESOURCE_ALLOCATOR = "resource_allocator"
    MODEL_TRAINER = "model_trainer"
    EXPERIMENT_RUNNER = "experiment_runner"
    CODE_EVOLVER = "code_evolver"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    CAPITAL_DEPLOYER = "capital_deployer"
    MARKET_MAKER = "market_maker"


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    LEARNING = "learning"
    EVOLVING = "evolving"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Agent:
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    capabilities: List[str]
    performance_score: float
    tasks_completed: int
    tasks_failed: int
    created_at: datetime
    last_active: datetime
    specialization: Optional[str] = None
    knowledge: Dict[str, Any] = field(default_factory=dict)
    resources_allocated: Dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    task_id: str
    task_type: str
    description: str
    priority: float
    required_capabilities: List[str]
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None


class AgentCoordinator:
    """
    Coordinates multiple agents, distributes work automatically,
    and ensures efficient collaboration.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.a2a_bus = self.config.get("a2a_bus") or A2AMessageBus()
        self.world_bridge = self.config.get("world_bridge") or World2AgentBridge(self.a2a_bus)
        self.coordinator_id = "autonomous_superintelligence.agent_coordinator"
        
        self.running = False
        self.coordination_mode = 'autonomous'
        
        self.storage_path = Path(self.config.get('storage_path', 'agent_coordination_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.a2a_bus.register_agent(
            self.coordinator_id,
            capabilities=["task_coordination", "autonomous_delegation", "interop"],
        )
        
        logger.info("Agent Coordinator initialized")
    
    async def initialize(self):
        """Initialize the coordination system."""
        logger.info("Initializing Agent Coordination System")
        
        await self._load_agents()
        await self._load_tasks()
        
        if not self.agents:
            await self._spawn_initial_agents()
        
        self.running = True
        logger.info("Agent Coordinator ready - %d agents active", len(self.agents))
    
    async def _load_agents(self):
        """Load existing agents from storage."""
        agents_file = self.storage_path / 'agents.json'
        if agents_file.exists():
            with open(agents_file, 'r') as f:
                data = json.load(f)
                for agent_data in data:
                    agent = Agent(
                        agent_id=agent_data['agent_id'],
                        agent_type=AgentType(agent_data['agent_type']),
                        status=AgentStatus(agent_data['status']),
                        capabilities=agent_data['capabilities'],
                        performance_score=agent_data['performance_score'],
                        tasks_completed=agent_data['tasks_completed'],
                        tasks_failed=agent_data['tasks_failed'],
                        created_at=datetime.fromisoformat(agent_data['created_at']),
                        last_active=datetime.fromisoformat(agent_data['last_active']),
                        specialization=agent_data.get('specialization'),
                        knowledge=agent_data.get('knowledge', {}),
                        resources_allocated=agent_data.get('resources_allocated', {}),
                    )
                    self.agents[agent.agent_id] = agent
            logger.info("Loaded %d agents from storage", len(self.agents))
    
    async def _load_tasks(self):
        """Load pending tasks from storage."""
        tasks_file = self.storage_path / 'tasks.json'
        if tasks_file.exists():
            with open(tasks_file, 'r') as f:
                data = json.load(f)
                for task_data in data:
                    if task_data['status'] != 'completed':
                        task = Task(
                            task_id=task_data['task_id'],
                            task_type=task_data['task_type'],
                            description=task_data['description'],
                            priority=task_data['priority'],
                            required_capabilities=task_data['required_capabilities'],
                            assigned_agent=task_data.get('assigned_agent'),
                            status=task_data['status'],
                            created_at=datetime.fromisoformat(task_data['created_at']),
                        )
                        self.task_queue.append(task)
            logger.info("Loaded %d pending tasks", len(self.task_queue))
    
    async def _spawn_initial_agents(self):
        """Spawn initial set of agents."""
        initial_agents = [
            (AgentType.MARKET_SCANNER, ['market_analysis', 'data_collection']),
            (AgentType.PATTERN_DETECTOR, ['pattern_recognition', 'ml_analysis']),
            (AgentType.RISK_OPTIMIZER, ['risk_management', 'optimization']),
            (AgentType.STRATEGY_DEVELOPER, ['strategy_creation', 'backtesting']),
            (AgentType.RESEARCH_SCIENTIST, ['research', 'experimentation', 'discovery']),
            (AgentType.OPPORTUNITY_HUNTER, ['opportunity_detection', 'market_scanning']),
            (AgentType.RESOURCE_ALLOCATOR, ['resource_management', 'optimization']),
            (AgentType.MODEL_TRAINER, ['ml_training', 'model_optimization']),
        ]
        
        for agent_type, capabilities in initial_agents:
            await self.spawn_agent(agent_type, capabilities)
        
        logger.info("Spawned %d initial agents", len(initial_agents))
    
    async def spawn_agent(
        self,
        agent_type: AgentType,
        capabilities: List[str],
        specialization: Optional[str] = None
    ) -> Agent:
        """Spawn a new agent."""
        agent = Agent(
            agent_id=str(uuid.uuid4()),
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            capabilities=capabilities,
            performance_score=0.5,
            tasks_completed=0,
            tasks_failed=0,
            created_at=datetime.now(),
            last_active=datetime.now(),
            specialization=specialization,
        )
        
        self.agents[agent.agent_id] = agent
        self.a2a_bus.register_agent(
            agent.agent_id,
            capabilities=capabilities,
            metadata={
                "agent_type": agent_type.value,
                "specialization": specialization,
            },
        )
        logger.info("Spawned agent: %s (%s)", agent.agent_id, agent_type.value)
        
        return agent
    
    async def create_task(
        self,
        task_type: str,
        description: str,
        priority: float,
        required_capabilities: List[str]
    ) -> Task:
        """Create a new task."""
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            description=description,
            priority=priority,
            required_capabilities=required_capabilities,
        )
        
        self.task_queue.append(task)
        self.a2a_bus.broadcast(
            sender=self.coordinator_id,
            intent="task_created",
            payload=self.world_bridge.build_agent_context(
                self.coordinator_id,
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "priority": task.priority,
                    "required_capabilities": task.required_capabilities,
                },
            ),
            recipients=list(self.agents.keys()),
            channel="autonomous_superintelligence",
        )
        logger.info("Created task: %s (priority: %.2f)", task.task_id, priority)
        
        return task
    
    async def assign_tasks(self):
        """Automatically assign tasks to agents."""
        if not self.task_queue:
            return
        
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        for task in self.task_queue[:]:
            if task.status != 'pending':
                continue
            
            best_agent = await self._find_best_agent(task)
            
            if best_agent:
                await self._assign_task_to_agent(task, best_agent)
                self.task_queue.remove(task)
    
    async def _find_best_agent(self, task: Task) -> Optional[Agent]:
        """Find the best agent for a task."""
        available_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]
        
        if not available_agents:
            return None
        
        capable_agents = [
            agent for agent in available_agents
            if any(cap in agent.capabilities for cap in task.required_capabilities)
        ]
        
        if not capable_agents:
            return None
        
        best_agent = max(capable_agents, key=lambda a: a.performance_score)
        return best_agent
    
    async def _assign_task_to_agent(self, task: Task, agent: Agent):
        """Assign a task to an agent."""
        task.assigned_agent = agent.agent_id
        task.status = 'assigned'
        task.started_at = datetime.now()
        
        agent.status = AgentStatus.WORKING
        agent.last_active = datetime.now()
        
        logger.info("Assigned task %s to agent %s", task.task_id, agent.agent_id)
        self.a2a_bus.send(
            sender=self.coordinator_id,
            recipients=[agent.agent_id],
            intent="task_assigned",
            payload=self.world_bridge.build_agent_context(
                agent.agent_id,
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "description": task.description,
                    "required_capabilities": task.required_capabilities,
                },
            ),
            channel="autonomous_superintelligence",
        )
        
        asyncio.create_task(self._execute_task(task, agent))
    
    async def _execute_task(self, task: Task, agent: Agent):
        """Execute a task with an agent."""
        try:
            result = await self._simulate_task_execution(task, agent)
            
            task.status = 'completed'
            task.completed_at = datetime.now()
            task.result = result
            
            agent.status = AgentStatus.IDLE
            agent.tasks_completed += 1
            agent.performance_score = min(agent.performance_score + 0.01, 1.0)
            
            self.completed_tasks.append(task)
            self.a2a_bus.send(
                sender=agent.agent_id,
                recipients=[self.coordinator_id],
                intent="task_completed",
                payload=self.world_bridge.build_agent_context(
                    self.coordinator_id,
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "result": result,
                    },
                ),
                channel="autonomous_superintelligence",
            )
            
            logger.info("Task completed: %s by agent %s", task.task_id, agent.agent_id)
            
        except Exception as e:
            logger.error("Task failed: %s - %s", task.task_id, e)
            task.status = 'failed'
            agent.status = AgentStatus.IDLE
            agent.tasks_failed += 1
            agent.performance_score = max(agent.performance_score - 0.05, 0.0)
            self.a2a_bus.send(
                sender=agent.agent_id,
                recipients=[self.coordinator_id],
                intent="task_failed",
                payload=self.world_bridge.build_agent_context(
                    self.coordinator_id,
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "error": str(e),
                    },
                ),
                channel="autonomous_superintelligence",
            )
    
    async def _simulate_task_execution(self, task: Task, agent: Agent) -> Dict:
        """Simulate task execution (replace with actual execution logic)."""
        await asyncio.sleep(1)
        
        return {
            'success': True,
            'agent_id': agent.agent_id,
            'task_type': task.task_type,
            'execution_time': 1.0,
            'quality_score': agent.performance_score,
        }
    
    async def coordinate_agents(self):
        """Main coordination loop."""
        logger.info("Starting agent coordination loop")
        
        while self.running:
            try:
                await self.assign_tasks()
                
                await self._monitor_agents()
                
                await self._optimize_agent_pool()
                
                await self._persist_state()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error("Error in coordination loop: %s", e, exc_info=True)
                await asyncio.sleep(10)
    
    async def _monitor_agents(self):
        """Monitor agent health and performance."""
        for agent in self.agents.values():
            if agent.status == AgentStatus.FAILED:
                logger.warning("Agent %s failed - attempting recovery", agent.agent_id)
                agent.status = AgentStatus.IDLE
            
            if agent.performance_score < 0.3:
                logger.warning("Agent %s underperforming - considering termination", 
                             agent.agent_id)
    
    async def _optimize_agent_pool(self):
        """Optimize the agent pool - spawn or terminate agents."""
        idle_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE)
        working_agents = sum(1 for a in self.agents.values() if a.status == AgentStatus.WORKING)
        
        if len(self.task_queue) > working_agents * 2 and idle_agents < 2:
            await self._spawn_additional_agents()
        
        underperforming = [
            agent for agent in self.agents.values()
            if agent.performance_score < 0.2 and agent.tasks_completed > 10
        ]
        
        for agent in underperforming[:2]:
            await self.terminate_agent(agent.agent_id)
    
    async def _spawn_additional_agents(self):
        """Spawn additional agents based on workload."""
        task_types = {}
        for task in self.task_queue:
            task_types[task.task_type] = task_types.get(task.task_type, 0) + 1
        
        if task_types:
            most_needed = max(task_types.items(), key=lambda x: x[1])
            
            agent_type_map = {
                'market_analysis': AgentType.MARKET_SCANNER,
                'pattern_detection': AgentType.PATTERN_DETECTOR,
                'risk_optimization': AgentType.RISK_OPTIMIZER,
                'strategy_development': AgentType.STRATEGY_DEVELOPER,
                'research': AgentType.RESEARCH_SCIENTIST,
            }
            
            agent_type = agent_type_map.get(most_needed[0], AgentType.DATA_ANALYST)
            await self.spawn_agent(agent_type, [most_needed[0]])
    
    async def terminate_agent(self, agent_id: str):
        """Terminate an agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = AgentStatus.TERMINATED
            logger.info("Terminated agent: %s (performance: %.2f)", 
                       agent_id, agent.performance_score)
            del self.agents[agent_id]
    
    async def _persist_state(self):
        """Persist agent and task state."""
        agents_file = self.storage_path / 'agents.json'
        agents_data = [
            {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type.value,
                'status': agent.status.value,
                'capabilities': agent.capabilities,
                'performance_score': agent.performance_score,
                'tasks_completed': agent.tasks_completed,
                'tasks_failed': agent.tasks_failed,
                'created_at': agent.created_at.isoformat(),
                'last_active': agent.last_active.isoformat(),
                'specialization': agent.specialization,
                'knowledge': agent.knowledge,
                'resources_allocated': agent.resources_allocated,
            }
            for agent in self.agents.values()
        ]
        
        with open(agents_file, 'w') as f:
            json.dump(agents_data, f, indent=2)
        
        tasks_file = self.storage_path / 'tasks.json'
        tasks_data = [
            {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'description': task.description,
                'priority': task.priority,
                'required_capabilities': task.required_capabilities,
                'assigned_agent': task.assigned_agent,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
            }
            for task in (self.task_queue + self.completed_tasks[-1000:])
        ]
        
        with open(tasks_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordination system status."""
        agent_stats = {}
        for agent_type in AgentType:
            count = sum(1 for a in self.agents.values() if a.agent_type == agent_type)
            if count > 0:
                agent_stats[agent_type.value] = count
        
        status_counts = {}
        for status in AgentStatus:
            count = sum(1 for a in self.agents.values() if a.status == status)
            if count > 0:
                status_counts[status.value] = count
        
        latest_snapshot = self.world_bridge.get_latest_snapshot()
        return {
            'total_agents': len(self.agents),
            'agent_types': agent_stats,
            'agent_status': status_counts,
            'pending_tasks': len(self.task_queue),
            'completed_tasks': len(self.completed_tasks),
            'avg_performance': np.mean([a.performance_score for a in self.agents.values()]) if self.agents else 0.0,
            'a2a_registered_agents': self.a2a_bus.list_agents(),
            'a2a_message_count': self.a2a_bus.message_count(),
            'latest_world_context_id': latest_snapshot.context_id if latest_snapshot else None,
        }

    def sync_world_state(
        self,
        source: str,
        world_state: Dict[str, Any],
        audience: Optional[List[str]] = None,
        context_type: str = "market",
    ) -> Dict[str, Any]:
        """Publish a shared world snapshot for autonomous agents."""
        snapshot = self.world_bridge.publish_world_state(
            source=source,
            world_state=world_state,
            audience=audience or list(self.agents.keys()),
            context_type=context_type,
        )
        return snapshot.to_dict()
    
    async def shutdown(self):
        """Shutdown coordination system."""
        logger.info("Shutting down Agent Coordinator")
        self.running = False
        await self._persist_state()
