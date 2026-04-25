"""
Agent Swarm - Multi-Agent Collaboration System
================================================

Implements a swarm of specialized agents:
1. Agent creation and management
2. Task distribution
3. Communication protocols
4. Collective intelligence

Based on the Foundation Agents paper (arXiv:2504.01990) multi-agent systems.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable, Set
from collections import defaultdict
import uuid
import random

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Roles agents can take"""
    ANALYST = "analyst"             # Analyzes data
    STRATEGIST = "strategist"       # Develops strategies
    RISK_MANAGER = "risk_manager"   # Manages risk
    EXECUTOR = "executor"           # Executes trades
    RESEARCHER = "researcher"       # Conducts research
    CRITIC = "critic"               # Critiques proposals
    SYNTHESIZER = "synthesizer"     # Synthesizes information
    COORDINATOR = "coordinator"     # Coordinates agents


class AgentStatus(Enum):
    """Status of an agent"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    QUERY = "query"
    INFORM = "inform"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    DELEGATE = "delegate"


@dataclass
class AgentMessage:
    """A message between agents"""
    message_id: str
    sender_id: str
    receiver_id: str  # "all" for broadcast
    message_type: MessageType
    
    # Content
    subject: str
    content: Any
    
    # Threading
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    
    # Priority
    priority: int = 0
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.value,
            'subject': self.subject,
            'content': str(self.content)[:200],
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AgentCapability:
    """A capability an agent has"""
    name: str
    description: str
    proficiency: float = 0.5  # 0-1 scale
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'proficiency': self.proficiency
        }


@dataclass
class Agent:
    """A single agent in the swarm"""
    agent_id: str
    name: str
    role: AgentRole
    
    # Capabilities
    capabilities: List[AgentCapability] = field(default_factory=list)
    
    # State
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    
    # Performance
    tasks_completed: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    
    # Communication
    inbox: List[AgentMessage] = field(default_factory=list)
    outbox: List[AgentMessage] = field(default_factory=list)
    
    # Knowledge
    beliefs: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    
    # Relationships
    trust_scores: Dict[str, float] = field(default_factory=dict)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    def has_capability(self, capability_name: str) -> bool:
        return any(c.name == capability_name for c in self.capabilities)
    
    def get_capability_proficiency(self, capability_name: str) -> float:
        for cap in self.capabilities:
            if cap.name == capability_name:
                return cap.proficiency
        return 0.0
    
    def update_trust(self, other_agent_id: str, success: bool):
        """Update trust score for another agent"""
        current = self.trust_scores.get(other_agent_id, 0.5)
        if success:
            self.trust_scores[other_agent_id] = min(1.0, current + 0.05)
        else:
            self.trust_scores[other_agent_id] = max(0.0, current - 0.1)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'role': self.role.value,
            'status': self.status.value,
            'capabilities': [c.to_dict() for c in self.capabilities],
            'tasks_completed': self.tasks_completed,
            'success_rate': self.success_rate
        }


@dataclass
class SwarmTask:
    """A task for the swarm to complete"""
    task_id: str
    description: str
    
    # Requirements
    required_capabilities: List[str] = field(default_factory=list)
    required_roles: List[AgentRole] = field(default_factory=list)
    
    # Assignment
    assigned_agents: List[str] = field(default_factory=list)
    coordinator_id: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, failed
    progress: float = 0.0
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    agent_contributions: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'assigned_agents': self.assigned_agents
        }


class MessageBroker:
    """Handles message routing between agents"""
    
    def __init__(self):
        self.message_queue: List[AgentMessage] = []
        self.message_history: List[AgentMessage] = []
        self.subscribers: Dict[str, List[str]] = defaultdict(list)  # topic -> agent_ids
    
    def send(self, message: AgentMessage):
        """Queue a message for delivery"""
        self.message_queue.append(message)
    
    def broadcast(self, sender_id: str, subject: str, content: Any):
        """Broadcast message to all agents"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id="all",
            message_type=MessageType.BROADCAST,
            subject=subject,
            content=content
        )
        self.message_queue.append(message)
    
    def subscribe(self, agent_id: str, topic: str):
        """Subscribe agent to a topic"""
        if agent_id not in self.subscribers[topic]:
            self.subscribers[topic].append(agent_id)
    
    def deliver(self, agents: Dict[str, Agent]) -> int:
        """Deliver queued messages to agents"""
        delivered = 0
        
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.message_history.append(message)
            
            if message.receiver_id == "all":
                # Broadcast
                for agent in agents.values():
                    if agent.agent_id != message.sender_id:
                        agent.inbox.append(message)
                        delivered += 1
            elif message.receiver_id in agents:
                agents[message.receiver_id].inbox.append(message)
                delivered += 1
        
        return delivered


class TaskAllocator:
    """Allocates tasks to agents"""
    
    def allocate(
        self,
        task: SwarmTask,
        agents: Dict[str, Agent]
    ) -> List[str]:
        """Allocate task to suitable agents"""
        candidates = []
        
        for agent in agents.values():
            if agent.status != AgentStatus.IDLE:
                continue
            
            # Check role match
            if task.required_roles and agent.role not in task.required_roles:
                continue
            
            # Check capability match
            capability_score = 0.0
            for cap_name in task.required_capabilities:
                if agent.has_capability(cap_name):
                    capability_score += agent.get_capability_proficiency(cap_name)
            
            if task.required_capabilities:
                capability_score /= len(task.required_capabilities)
            else:
                capability_score = 0.5
            
            # Consider success rate
            overall_score = 0.5 * capability_score + 0.5 * agent.success_rate
            
            candidates.append((agent.agent_id, overall_score))
        
        # Sort by score and select top agents
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select appropriate number of agents
        n_agents = min(3, len(candidates))
        selected = [c[0] for c in candidates[:n_agents]]
        
        return selected


class AgentSwarm:
    """
    Agent Swarm
    
    Manages a swarm of specialized agents that collaborate
    on trading research and decision-making tasks.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.message_broker = MessageBroker()
        self.task_allocator = TaskAllocator()
        
        # Agents
        self.agents: Dict[str, Agent] = {}
        
        # Tasks
        self.tasks: Dict[str, SwarmTask] = {}
        self.task_history: List[SwarmTask] = []
        
        # Statistics
        self.stats = {
            'agents_created': 0,
            'tasks_completed': 0,
            'messages_sent': 0,
            'collaborations': 0
        }
        
        # Initialize default agents
        self._initialize_default_agents()
        
        logger.info("Agent Swarm initialized")
    
    def _initialize_default_agents(self):
        """Initialize default specialized agents"""
        default_agents = [
            {
                'name': 'Alpha Analyst',
                'role': AgentRole.ANALYST,
                'capabilities': [
                    AgentCapability('technical_analysis', 'Analyze price patterns', 0.8),
                    AgentCapability('fundamental_analysis', 'Analyze fundamentals', 0.7),
                    AgentCapability('data_processing', 'Process market data', 0.9)
                ]
            },
            {
                'name': 'Strategy Designer',
                'role': AgentRole.STRATEGIST,
                'capabilities': [
                    AgentCapability('strategy_design', 'Design trading strategies', 0.85),
                    AgentCapability('optimization', 'Optimize parameters', 0.8),
                    AgentCapability('backtesting', 'Backtest strategies', 0.75)
                ]
            },
            {
                'name': 'Risk Guardian',
                'role': AgentRole.RISK_MANAGER,
                'capabilities': [
                    AgentCapability('risk_assessment', 'Assess trading risks', 0.9),
                    AgentCapability('position_sizing', 'Calculate position sizes', 0.85),
                    AgentCapability('portfolio_analysis', 'Analyze portfolio risk', 0.8)
                ]
            },
            {
                'name': 'Research Explorer',
                'role': AgentRole.RESEARCHER,
                'capabilities': [
                    AgentCapability('literature_review', 'Review research papers', 0.8),
                    AgentCapability('hypothesis_testing', 'Test hypotheses', 0.75),
                    AgentCapability('data_mining', 'Mine data for patterns', 0.7)
                ]
            },
            {
                'name': 'Critical Reviewer',
                'role': AgentRole.CRITIC,
                'capabilities': [
                    AgentCapability('critique', 'Critique proposals', 0.85),
                    AgentCapability('validation', 'Validate findings', 0.8),
                    AgentCapability('devil_advocate', 'Challenge assumptions', 0.9)
                ]
            },
            {
                'name': 'Knowledge Synthesizer',
                'role': AgentRole.SYNTHESIZER,
                'capabilities': [
                    AgentCapability('synthesis', 'Synthesize information', 0.85),
                    AgentCapability('summarization', 'Summarize findings', 0.8),
                    AgentCapability('integration', 'Integrate knowledge', 0.75)
                ]
            }
        ]
        
        for agent_config in default_agents:
            self.create_agent(
                name=agent_config['name'],
                role=agent_config['role'],
                capabilities=agent_config['capabilities']
            )
    
    def create_agent(
        self,
        name: str,
        role: AgentRole,
        capabilities: Optional[List[AgentCapability]] = None
    ) -> Agent:
        """Create a new agent"""
        agent = Agent(
            agent_id=str(uuid.uuid4())[:8],
            name=name,
            role=role,
            capabilities=capabilities or []
        )
        
        self.agents[agent.agent_id] = agent
        self.stats['agents_created'] += 1
        
        logger.info(f"Created agent: {name} ({role.value})")
        
        return agent
    
    def create_task(
        self,
        description: str,
        required_capabilities: Optional[List[str]] = None,
        required_roles: Optional[List[AgentRole]] = None,
        deadline: Optional[datetime] = None
    ) -> SwarmTask:
        """Create a new task for the swarm"""
        task = SwarmTask(
            task_id=str(uuid.uuid4())[:8],
            description=description,
            required_capabilities=required_capabilities or [],
            required_roles=required_roles or [],
            deadline=deadline
        )
        
        # Allocate agents
        assigned = self.task_allocator.allocate(task, self.agents)
        task.assigned_agents = assigned
        
        # Set coordinator (first assigned agent)
        if assigned:
            task.coordinator_id = assigned[0]
        
        # Update agent status
        for agent_id in assigned:
            if agent_id in self.agents:
                self.agents[agent_id].status = AgentStatus.BUSY
                self.agents[agent_id].current_task = task.task_id
        
        self.tasks[task.task_id] = task
        task.status = "in_progress"
        
        logger.info(f"Created task: {task.task_id} with {len(assigned)} agents")
        
        return task
    
    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: MessageType,
        subject: str,
        content: Any,
        reply_to: Optional[str] = None
    ) -> AgentMessage:
        """Send a message between agents"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            subject=subject,
            content=content,
            reply_to=reply_to
        )
        
        self.message_broker.send(message)
        self.stats['messages_sent'] += 1
        
        return message
    
    def broadcast(self, sender_id: str, subject: str, content: Any):
        """Broadcast message to all agents"""
        self.message_broker.broadcast(sender_id, subject, content)
        self.stats['messages_sent'] += 1
    
    def process_messages(self) -> int:
        """Process and deliver queued messages"""
        return self.message_broker.deliver(self.agents)
    
    def submit_contribution(
        self,
        task_id: str,
        agent_id: str,
        contribution: Any
    ):
        """Submit an agent's contribution to a task"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.agent_contributions[agent_id] = {
            'contribution': contribution,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Update progress
        n_contributions = len(task.agent_contributions)
        n_assigned = len(task.assigned_agents)
        task.progress = n_contributions / max(1, n_assigned)
        
        # Check if task is complete
        if n_contributions >= n_assigned:
            self._complete_task(task_id)
    
    def _complete_task(self, task_id: str):
        """Complete a task"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.progress = 1.0
        
        # Synthesize results
        task.results = self._synthesize_contributions(task)
        
        # Free agents
        for agent_id in task.assigned_agents:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.status = AgentStatus.IDLE
                agent.current_task = None
                agent.tasks_completed += 1
                agent.last_active = datetime.utcnow()
        
        self.task_history.append(task)
        self.stats['tasks_completed'] += 1
        self.stats['collaborations'] += len(task.assigned_agents)
        
        logger.info(f"Completed task: {task_id}")
    
    def _synthesize_contributions(self, task: SwarmTask) -> Dict[str, Any]:
        """Synthesize contributions from multiple agents"""
        contributions = task.agent_contributions
        
        # Simple aggregation
        result = {
            'task_id': task.task_id,
            'n_contributors': len(contributions),
            'contributions': contributions,
            'synthesis': None
        }
        
        # If we have a synthesizer agent, use it
        synthesizers = [
            a for a in self.agents.values()
            if a.role == AgentRole.SYNTHESIZER and a.status == AgentStatus.IDLE
        ]
        
        if synthesizers:
            # Simulate synthesis
            result['synthesis'] = {
                'synthesizer': synthesizers[0].agent_id,
                'summary': f"Synthesized {len(contributions)} contributions",
                'confidence': 0.8
            }
        
        return result
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[Agent]:
        """Get agents by role"""
        return [a for a in self.agents.values() if a.role == role]
    
    def get_available_agents(self) -> List[Agent]:
        """Get available (idle) agents"""
        return [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
    
    def get_task(self, task_id: str) -> Optional[SwarmTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_active_tasks(self) -> List[SwarmTask]:
        """Get active tasks"""
        return [t for t in self.tasks.values() if t.status == "in_progress"]
    
    async def run_collaborative_task(
        self,
        description: str,
        required_capabilities: List[str],
        timeout_seconds: int = 60
    ) -> Dict[str, Any]:
        """Run a collaborative task asynchronously"""
        task = self.create_task(
            description=description,
            required_capabilities=required_capabilities
        )
        
        # Simulate agent work
        for agent_id in task.assigned_agents:
            agent = self.agents.get(agent_id)
            if agent:
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Generate contribution
                contribution = {
                    'agent': agent.name,
                    'role': agent.role.value,
                    'analysis': f"Analysis from {agent.name}",
                    'confidence': random.uniform(0.6, 0.95)
                }
                
                self.submit_contribution(task.task_id, agent_id, contribution)
        
        return task.results
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status"""
        return {
            'total_agents': len(self.agents),
            'available_agents': len(self.get_available_agents()),
            'active_tasks': len(self.get_active_tasks()),
            'by_role': {
                role.value: len(self.get_agents_by_role(role))
                for role in AgentRole
            },
            'by_status': {
                status.value: len([a for a in self.agents.values() if a.status == status])
                for status in AgentStatus
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get swarm statistics"""
        return {
            **self.stats,
            'avg_success_rate': sum(a.success_rate for a in self.agents.values()) / max(1, len(self.agents)),
            'total_tasks': len(self.tasks) + len(self.task_history),
            'pending_messages': len(self.message_broker.message_queue)
        }
