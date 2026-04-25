"""
Agent Lifecycle Manager
Manages agent spawning, lifecycle, and termination.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentLifecycleStage(Enum):
    SPAWNING = "spawning"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    LEARNING = "learning"
    IDLE = "idle"
    DEGRADING = "degrading"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


@dataclass
class AgentLifecycle:
    agent_id: str
    agent_type: str
    stage: AgentLifecycleStage
    spawned_at: datetime
    health: float
    performance: float
    age_hours: float
    tasks_completed: int
    last_activity: datetime


class AgentLifecycleManager:
    """
    Manages the complete lifecycle of agents - spawning, monitoring, and termination.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.agent_lifecycles: Dict[str, AgentLifecycle] = {}
        
        self.max_agents = config.get('max_agents', 100)
        self.min_agents = config.get('min_agents', 5)
        self.health_check_interval = config.get('health_check_interval', 60)
        
        self.running = False
        
        self.storage_path = Path(config.get('storage_path', 'agent_lifecycle_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Agent Lifecycle Manager initialized")
    
    async def initialize(self):
        """Initialize the lifecycle manager."""
        logger.info("Initializing Agent Lifecycle Manager")
        
        await self._load_lifecycles()
        
        self.running = True
        logger.info("Lifecycle Manager ready - managing %d agents", len(self.agent_lifecycles))
    
    async def _load_lifecycles(self):
        """Load agent lifecycle data."""
        lifecycle_file = self.storage_path / 'lifecycles.json'
        if lifecycle_file.exists():
            with open(lifecycle_file, 'r') as f:
                data = json.load(f)
                for lc_data in data:
                    if lc_data['stage'] not in ['terminated', 'terminating']:
                        lifecycle = AgentLifecycle(
                            agent_id=lc_data['agent_id'],
                            agent_type=lc_data['agent_type'],
                            stage=AgentLifecycleStage(lc_data['stage']),
                            spawned_at=datetime.fromisoformat(lc_data['spawned_at']),
                            health=lc_data['health'],
                            performance=lc_data['performance'],
                            age_hours=lc_data['age_hours'],
                            tasks_completed=lc_data['tasks_completed'],
                            last_activity=datetime.fromisoformat(lc_data['last_activity']),
                        )
                        self.agent_lifecycles[lifecycle.agent_id] = lifecycle
    
    async def spawn_agent(self, agent_type: str, capabilities: List[str]) -> str:
        """Spawn a new agent."""
        if len(self.agent_lifecycles) >= self.max_agents:
            logger.warning("Maximum agent count reached: %d", self.max_agents)
            await self._terminate_weakest_agent()
        
        agent_id = f"agent_{agent_type}_{datetime.now().timestamp()}"
        
        lifecycle = AgentLifecycle(
            agent_id=agent_id,
            agent_type=agent_type,
            stage=AgentLifecycleStage.SPAWNING,
            spawned_at=datetime.now(),
            health=1.0,
            performance=0.5,
            age_hours=0.0,
            tasks_completed=0,
            last_activity=datetime.now(),
        )
        
        self.agent_lifecycles[agent_id] = lifecycle
        
        await self._initialize_agent(agent_id)
        
        logger.info("Spawned agent: %s (%s)", agent_id, agent_type)
        
        return agent_id
    
    async def _initialize_agent(self, agent_id: str):
        """Initialize a newly spawned agent."""
        lifecycle = self.agent_lifecycles.get(agent_id)
        if not lifecycle:
            return
        
        lifecycle.stage = AgentLifecycleStage.INITIALIZING
        
        await asyncio.sleep(0.5)
        
        lifecycle.stage = AgentLifecycleStage.ACTIVE
        lifecycle.last_activity = datetime.now()
    
    async def monitor_agent_health(self, agent_id: str):
        """Monitor an agent's health."""
        lifecycle = self.agent_lifecycles.get(agent_id)
        if not lifecycle:
            return
        
        age = (datetime.now() - lifecycle.spawned_at).total_seconds() / 3600
        lifecycle.age_hours = age
        
        time_since_activity = (datetime.now() - lifecycle.last_activity).total_seconds()
        
        if time_since_activity > 3600:
            lifecycle.health -= 0.1
            lifecycle.stage = AgentLifecycleStage.IDLE
        
        if lifecycle.performance < 0.3:
            lifecycle.health -= 0.05
            lifecycle.stage = AgentLifecycleStage.DEGRADING
        
        if age > 168:
            lifecycle.health -= 0.02
        
        lifecycle.health = max(lifecycle.health, 0.0)
        
        if lifecycle.health < 0.3:
            logger.warning("Agent %s health critical: %.2f", agent_id, lifecycle.health)
            await self.terminate_agent(agent_id, "Low health")
    
    async def update_agent_activity(self, agent_id: str, task_completed: bool = False):
        """Update agent activity."""
        lifecycle = self.agent_lifecycles.get(agent_id)
        if not lifecycle:
            return
        
        lifecycle.last_activity = datetime.now()
        lifecycle.stage = AgentLifecycleStage.ACTIVE
        
        if task_completed:
            lifecycle.tasks_completed += 1
            lifecycle.performance = min(lifecycle.performance + 0.01, 1.0)
            lifecycle.health = min(lifecycle.health + 0.05, 1.0)
    
    async def terminate_agent(self, agent_id: str, reason: str):
        """Terminate an agent."""
        lifecycle = self.agent_lifecycles.get(agent_id)
        if not lifecycle:
            return
        
        lifecycle.stage = AgentLifecycleStage.TERMINATING
        
        await asyncio.sleep(0.2)
        
        lifecycle.stage = AgentLifecycleStage.TERMINATED
        
        logger.info("Terminated agent: %s - Reason: %s", agent_id, reason)
        
        del self.agent_lifecycles[agent_id]
    
    async def _terminate_weakest_agent(self):
        """Terminate the weakest performing agent."""
        if not self.agent_lifecycles:
            return
        
        weakest = min(
            self.agent_lifecycles.values(),
            key=lambda lc: lc.performance * lc.health
        )
        
        await self.terminate_agent(weakest.agent_id, "Weakest performer - making room for new agent")
    
    async def lifecycle_management_loop(self):
        """Main lifecycle management loop."""
        logger.info("Starting lifecycle management loop")
        
        while self.running:
            try:
                for agent_id in list(self.agent_lifecycles.keys()):
                    await self.monitor_agent_health(agent_id)
                
                await self._maintain_agent_population()
                
                await self._persist_state()
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error("Error in lifecycle management loop: %s", e, exc_info=True)
                await asyncio.sleep(30)
    
    async def _maintain_agent_population(self):
        """Maintain optimal agent population."""
        active_agents = sum(
            1 for lc in self.agent_lifecycles.values()
            if lc.stage == AgentLifecycleStage.ACTIVE
        )
        
        if active_agents < self.min_agents:
            logger.info("Agent count below minimum - spawning new agents")
            for _ in range(self.min_agents - active_agents):
                await self.spawn_agent("general_purpose", ["general"])
    
    async def _persist_state(self):
        """Persist lifecycle state."""
        lifecycle_file = self.storage_path / 'lifecycles.json'
        lifecycle_data = [
            {
                'agent_id': lc.agent_id,
                'agent_type': lc.agent_type,
                'stage': lc.stage.value,
                'spawned_at': lc.spawned_at.isoformat(),
                'health': lc.health,
                'performance': lc.performance,
                'age_hours': lc.age_hours,
                'tasks_completed': lc.tasks_completed,
                'last_activity': lc.last_activity.isoformat(),
            }
            for lc in self.agent_lifecycles.values()
        ]
        
        with open(lifecycle_file, 'w') as f:
            json.dump(lifecycle_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get lifecycle manager status."""
        stage_counts = {}
        for stage in AgentLifecycleStage:
            count = sum(1 for lc in self.agent_lifecycles.values() if lc.stage == stage)
            if count > 0:
                stage_counts[stage.value] = count
        
        return {
            'total_agents': len(self.agent_lifecycles),
            'stage_distribution': stage_counts,
            'avg_health': sum(lc.health for lc in self.agent_lifecycles.values()) / len(self.agent_lifecycles) if self.agent_lifecycles else 0.0,
            'avg_performance': sum(lc.performance for lc in self.agent_lifecycles.values()) / len(self.agent_lifecycles) if self.agent_lifecycles else 0.0,
            'total_tasks_completed': sum(lc.tasks_completed for lc in self.agent_lifecycles.values()),
        }
    
    async def shutdown(self):
        """Shutdown lifecycle manager."""
        logger.info("Shutting down Agent Lifecycle Manager")
        self.running = False
        await self._persist_state()
