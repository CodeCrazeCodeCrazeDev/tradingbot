"""
Self-Coordinating AI Core - Multi-Agent Coordination System

Implements advanced multi-agent coordination capabilities:
- Task Decomposition (hierarchical task breakdown)
- Agent Negotiation (contract net protocol)
- Resource Allocation (priority scheduling)
- Failure Recovery (rollback and retry)
- Coordination Layer (inter-agent communication)
- Shared Memory (collaborative workspace)
- Governance (oversight and compliance)
- Learning Loop (continuous improvement)
- Dynamic Sub-Agent Creation (on-demand agent spawning)

Patterns:
- DeepMind: Hierarchical RL, multi-agent coordination
- OpenAI: Agent communication protocols
- Anthropic: Safety governance and oversight
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== TASK DECOMPOSITION ====================

class TaskType(Enum):
    """Types of tasks"""
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    RESEARCH = "research"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    COORDINATION = "coordination"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class Task:
    """
    A task in the system.
    
    Follows hierarchical task network (HTN) decomposition pattern.
    """
    task_id: str
    name: str
    task_type: TaskType
    priority: TaskPriority
    description: str
    
    # Hierarchical structure
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    
    # Requirements
    required_capabilities: List[str] = field(default_factory=list)
    required_resources: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    
    # Execution
    assigned_agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf task (no subtasks)"""
        return len(self.subtasks) == 0
    
    def is_ready(self) -> bool:
        """Check if task is ready to execute (all dependencies met)"""
        # A task is ready if it's pending and all its dependencies are COMPLETED
        return self.status == TaskStatus.PENDING and len(self.dependencies) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'progress': self.progress,
            'assigned_agent_id': self.assigned_agent_id
        }


class TaskDecomposer:
    """
    Hierarchical Task Decomposition
    
    Breaks down complex tasks into manageable subtasks.
    Inspired by HTN planning and DeepMind's hierarchical RL.
    
    ┌─────────────────────────────────────────────────────┐
    │              TASK DECOMPOSITION                      │
    │                                                      │
    │  Complex Task                                        │
    │       │                                              │
    │       ├─── Subtask 1                                │
    │       │      ├─── Atomic Task 1.1                   │
    │       │      └─── Atomic Task 1.2                   │
    │       │                                              │
    │       ├─── Subtask 2                                │
    │       │      ├─── Atomic Task 2.1                   │
    │       │      └─── Atomic Task 2.2                   │
    │       │                                              │
    │       └─── Subtask 3                                │
    │              └─── Atomic Task 3.1                   │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.decomposition_rules: Dict[TaskType, Callable] = {}
        
        # Register default decomposition rules
        self._register_default_rules()
        
        logger.info("Task Decomposer initialized")
    
    def _register_default_rules(self):
        """Register default task decomposition rules"""
        self.decomposition_rules[TaskType.ANALYSIS] = self._decompose_analysis
        self.decomposition_rules[TaskType.EXECUTION] = self._decompose_execution
        self.decomposition_rules[TaskType.RESEARCH] = self._decompose_research
        self.decomposition_rules[TaskType.OPTIMIZATION] = self._decompose_optimization
    
    async def decompose(self, task: Task) -> List[Task]:
        """
        Decompose a task into subtasks.
        
        Returns list of subtasks.
        """
        # Store parent task
        self.tasks[task.task_id] = task
        
        # Get decomposition rule
        rule = self.decomposition_rules.get(task.task_type)
        
        if not rule:
            # No decomposition rule - task is atomic
            return [task]
        
        # Apply decomposition rule
        subtasks = await rule(task)
        
        # Link subtasks to parent
        task.subtasks = [st.task_id for st in subtasks]
        for subtask in subtasks:
            subtask.parent_task_id = task.task_id
            self.tasks[subtask.task_id] = subtask
        
        logger.info(f"Decomposed task {task.name} into {len(subtasks)} subtasks")
        
        return subtasks
    
    async def _decompose_analysis(self, task: Task) -> List[Task]:
        """Decompose analysis task"""
        subtasks = [
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Data Collection",
                task_type=TaskType.ANALYSIS,
                priority=task.priority,
                description="Collect required data",
                required_capabilities=['data_access'],
                metadata={'phase': 'collection'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Processing",
                task_type=TaskType.ANALYSIS,
                priority=task.priority,
                description="Process and analyze data",
                required_capabilities=['analysis'],
                dependencies=[],  # Will be set to previous task
                metadata={'phase': 'processing'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Reporting",
                task_type=TaskType.ANALYSIS,
                priority=task.priority,
                description="Generate analysis report",
                required_capabilities=['reporting'],
                dependencies=[],  # Will be set to previous task
                metadata={'phase': 'reporting'}
            )
        ]
        
        # Set dependencies (sequential)
        subtasks[1].dependencies = [subtasks[0].task_id]
        subtasks[2].dependencies = [subtasks[1].task_id]
        
        return subtasks
    
    async def _decompose_execution(self, task: Task) -> List[Task]:
        """Decompose execution task"""
        subtasks = [
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Validation",
                task_type=TaskType.EXECUTION,
                priority=task.priority,
                description="Validate execution parameters",
                required_capabilities=['validation'],
                metadata={'phase': 'validation'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Execution",
                task_type=TaskType.EXECUTION,
                priority=task.priority,
                description="Execute action",
                required_capabilities=['execution'],
                dependencies=[],
                metadata={'phase': 'execution'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Verification",
                task_type=TaskType.EXECUTION,
                priority=task.priority,
                description="Verify execution result",
                required_capabilities=['verification'],
                dependencies=[],
                metadata={'phase': 'verification'}
            )
        ]
        
        subtasks[1].dependencies = [subtasks[0].task_id]
        subtasks[2].dependencies = [subtasks[1].task_id]
        
        return subtasks
    
    async def _decompose_research(self, task: Task) -> List[Task]:
        """Decompose research task"""
        subtasks = [
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Hypothesis",
                task_type=TaskType.RESEARCH,
                priority=task.priority,
                description="Generate research hypothesis",
                required_capabilities=['research'],
                metadata={'phase': 'hypothesis'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Experiment",
                task_type=TaskType.RESEARCH,
                priority=task.priority,
                description="Design and run experiment",
                required_capabilities=['experimentation'],
                dependencies=[],
                metadata={'phase': 'experiment'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Analysis",
                task_type=TaskType.RESEARCH,
                priority=task.priority,
                description="Analyze results",
                required_capabilities=['analysis'],
                dependencies=[],
                metadata={'phase': 'analysis'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Conclusion",
                task_type=TaskType.RESEARCH,
                priority=task.priority,
                description="Draw conclusions",
                required_capabilities=['research'],
                dependencies=[],
                metadata={'phase': 'conclusion'}
            )
        ]
        
        subtasks[1].dependencies = [subtasks[0].task_id]
        subtasks[2].dependencies = [subtasks[1].task_id]
        subtasks[3].dependencies = [subtasks[2].task_id]
        
        return subtasks
    
    async def _decompose_optimization(self, task: Task) -> List[Task]:
        """Decompose optimization task"""
        subtasks = [
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Baseline",
                task_type=TaskType.OPTIMIZATION,
                priority=task.priority,
                description="Establish baseline metrics",
                required_capabilities=['monitoring'],
                metadata={'phase': 'baseline'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Search",
                task_type=TaskType.OPTIMIZATION,
                priority=task.priority,
                description="Search for improvements",
                required_capabilities=['optimization'],
                dependencies=[],
                metadata={'phase': 'search'}
            ),
            Task(
                task_id=str(uuid.uuid4()),
                name=f"{task.name} - Evaluation",
                task_type=TaskType.OPTIMIZATION,
                priority=task.priority,
                description="Evaluate improvements",
                required_capabilities=['evaluation'],
                dependencies=[],
                metadata={'phase': 'evaluation'}
            )
        ]
        
        subtasks[1].dependencies = [subtasks[0].task_id]
        subtasks[2].dependencies = [subtasks[1].task_id]
        
        return subtasks
    
    def get_ready_tasks(self) -> List[Task]:
        """Get all tasks ready for execution"""
        return [
            task for task in self.tasks.values()
            if task.is_ready() and task.is_leaf()
        ]
    
    def mark_completed(self, task_id: str, result: Dict[str, Any]):
        """Mark task as completed and update dependencies"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result
        task.progress = 1.0
        
        # Remove this task from dependencies of other tasks
        for other_task in self.tasks.values():
            if task_id in other_task.dependencies:
                other_task.dependencies.remove(task_id)
        
        # Check if parent task is complete
        if task.parent_task_id:
            self._check_parent_completion(task.parent_task_id)
    
    def _check_parent_completion(self, parent_id: str):
        """Check if parent task is complete (all subtasks done)"""
        parent = self.tasks.get(parent_id)
        if not parent:
            return
        
        # Check all subtasks
        all_complete = all(
            self.tasks[st_id].status == TaskStatus.COMPLETED
            for st_id in parent.subtasks
            if st_id in self.tasks
        )
        
        if all_complete:
            parent.status = TaskStatus.COMPLETED
            parent.completed_at = datetime.now()
            parent.progress = 1.0
            
            # Recursively check parent's parent
            if parent.parent_task_id:
                self._check_parent_completion(parent.parent_task_id)


# ==================== AGENT NEGOTIATION ====================

class NegotiationProtocol(Enum):
    """Negotiation protocols"""
    CONTRACT_NET = "contract_net"  # Contract Net Protocol (CNP)
    AUCTION = "auction"
    CONSENSUS = "consensus"
    VOTING = "voting"


@dataclass
class Bid:
    """Agent bid for a task"""
    bid_id: str
    agent_id: str
    task_id: str
    
    # Bid details
    cost: float  # Resource cost
    time_estimate: float  # Estimated completion time (seconds)
    confidence: float  # Confidence in ability to complete (0-1)
    quality_estimate: float  # Expected quality (0-1)
    
    # Capabilities
    capabilities_match: float  # How well capabilities match (0-1)
    
    # Timestamp
    submitted_at: datetime = field(default_factory=datetime.now)
    
    def score(self) -> float:
        """Calculate bid score (higher is better)"""
        # Weighted combination of factors
        return (
            0.3 * self.confidence +
            0.3 * self.quality_estimate +
            0.2 * self.capabilities_match +
            0.1 * (1.0 / (1.0 + self.cost)) +  # Lower cost is better
            0.1 * (1.0 / (1.0 + self.time_estimate / 3600))  # Faster is better
        )


@dataclass
class Contract:
    """Contract between coordinator and agent"""
    contract_id: str
    task_id: str
    agent_id: str
    
    # Terms
    agreed_cost: float
    agreed_time: float
    agreed_quality: float
    
    # Status
    status: str = "active"  # active, completed, breached
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class AgentNegotiator:
    """
    Agent Negotiation System
    
    Implements Contract Net Protocol (CNP) for task allocation.
    
    Process:
    1. Task Announcement: Coordinator announces task
    2. Bidding: Agents submit bids
    3. Award: Coordinator selects best bid
    4. Contract: Formal agreement created
    5. Execution: Agent executes task
    6. Verification: Coordinator verifies completion
    
    Reference: "The Contract Net Protocol" (Smith, 1980)
    """
    
    def __init__(self):
        self.active_bids: Dict[str, List[Bid]] = defaultdict(list)
        self.contracts: Dict[str, Contract] = {}
        
        logger.info("Agent Negotiator initialized")
    
    async def announce_task(
        self,
        task: Task,
        available_agents: List[Any]
    ) -> Optional[str]:
        """
        Announce task and collect bids (Contract Net Protocol).
        
        Returns selected agent_id or None.
        """
        logger.info(f"Announcing task {task.name} to {len(available_agents)} agents")
        
        # Collect bids from agents
        bids = []
        for agent in available_agents:
            bid = await self._request_bid(agent, task)
            if bid:
                bids.append(bid)
                self.active_bids[task.task_id].append(bid)
        
        if not bids:
            logger.warning(f"No bids received for task {task.task_id}")
            return None
        
        # Select best bid
        best_bid = max(bids, key=lambda b: b.score())
        
        # Create contract
        contract = Contract(
            contract_id=str(uuid.uuid4()),
            task_id=task.task_id,
            agent_id=best_bid.agent_id,
            agreed_cost=best_bid.cost,
            agreed_time=best_bid.time_estimate,
            agreed_quality=best_bid.quality_estimate
        )
        
        self.contracts[contract.contract_id] = contract
        
        logger.info(f"Task {task.name} awarded to agent {best_bid.agent_id} "
                   f"(score: {best_bid.score():.2f})")
        
        return best_bid.agent_id
    
    async def _request_bid(self, agent: Any, task: Task) -> Optional[Bid]:
        """Request bid from an agent"""
        # Check if agent has required capabilities
        agent_capabilities = set(agent.capabilities)
        required_capabilities = set(task.required_capabilities)
        
        if not required_capabilities.issubset(agent_capabilities):
            return None  # Agent cannot handle this task
        
        # Calculate capability match
        capabilities_match = len(required_capabilities & agent_capabilities) / max(len(required_capabilities), 1)
        
        # Estimate cost and time based on agent's current load
        base_cost = 1.0
        base_time = 300  # 5 minutes
        
        # Adjust for agent load
        load_factor = 1.0 + (agent.current_tasks / max(agent.max_concurrent_tasks, 1))
        
        cost = base_cost * load_factor
        time_estimate = base_time * load_factor
        
        # Agent's confidence based on past performance
        confidence = agent.success_rate if hasattr(agent, 'success_rate') else 0.7
        
        # Create bid
        bid = Bid(
            bid_id=str(uuid.uuid4()),
            agent_id=agent.agent_id,
            task_id=task.task_id,
            cost=cost,
            time_estimate=time_estimate,
            confidence=confidence,
            quality_estimate=confidence,
            capabilities_match=capabilities_match
        )
        
        return bid
    
    def complete_contract(self, contract_id: str, success: bool):
        """Mark contract as completed"""
        if contract_id not in self.contracts:
            return
        
        contract = self.contracts[contract_id]
        contract.status = "completed" if success else "breached"
        contract.completed_at = datetime.now()


# ==================== RESOURCE ALLOCATION ====================

@dataclass
class Resource:
    """System resource"""
    resource_id: str
    resource_type: str  # cpu, memory, network, api_quota, etc.
    total_capacity: float
    available_capacity: float
    unit: str  # cores, GB, requests/min, etc.
    
    def allocate(self, amount: float) -> bool:
        """Allocate resource"""
        if amount <= self.available_capacity:
            self.available_capacity -= amount
            return True
        return False
    
    def release(self, amount: float):
        """Release resource"""
        self.available_capacity = min(
            self.available_capacity + amount,
            self.total_capacity
        )


@dataclass
class ResourceAllocation:
    """Resource allocation for a task"""
    allocation_id: str
    task_id: str
    agent_id: str
    resources: Dict[str, float]  # resource_type -> amount
    allocated_at: datetime = field(default_factory=datetime.now)
    released_at: Optional[datetime] = None


class ResourceAllocator:
    """
    Resource Allocation Manager
    
    Manages system resources and allocates them to tasks/agents.
    Uses priority scheduling and fair allocation.
    
    ┌─────────────────────────────────────────────────────┐
    │           RESOURCE ALLOCATION                        │
    │                                                      │
    │  Resources:                                          │
    │  ├─ CPU: 8 cores (6 available)                      │
    │  ├─ Memory: 16 GB (12 GB available)                 │
    │  ├─ Network: 1000 req/min (800 available)           │
    │  └─ API Quota: 10000 calls/day (9500 available)     │
    │                                                      │
    │  Allocations:                                        │
    │  ├─ Task A: 2 cores, 4 GB (HIGH priority)           │
    │  ├─ Task B: 1 core, 2 GB (MEDIUM priority)          │
    │  └─ Task C: Waiting... (LOW priority)               │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        
        # Initialize resources
        self.resources: Dict[str, Resource] = {
            'cpu': Resource('cpu', 'cpu', 8.0, 8.0, 'cores'),
            'memory': Resource('memory', 'memory', 16.0, 16.0, 'GB'),
            'network': Resource('network', 'network', 1000.0, 1000.0, 'req/min'),
            'api_quota': Resource('api_quota', 'api_quota', 10000.0, 10000.0, 'calls/day')
        }
        
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.waiting_queue: List[Tuple[Task, Dict[str, float]]] = []
        
        logger.info("Resource Allocator initialized")
    
    async def allocate(
        self,
        task: Task,
        agent_id: str,
        required_resources: Dict[str, float]
    ) -> Optional[str]:
        """
        Allocate resources for a task.
        
        Returns allocation_id if successful, None otherwise.
        """
        # Check if resources available
        can_allocate = all(
            self.resources[res_type].available_capacity >= amount
            for res_type, amount in required_resources.items()
            if res_type in self.resources
        )
        
        if not can_allocate:
            # Add to waiting queue
            self.waiting_queue.append((task, required_resources))
            self.waiting_queue.sort(key=lambda x: x[0].priority.value, reverse=True)
            logger.info(f"Task {task.name} added to waiting queue")
            return None
        
        # Allocate resources
        for res_type, amount in required_resources.items():
            if res_type in self.resources:
                self.resources[res_type].allocate(amount)
        
        # Create allocation record
        allocation = ResourceAllocation(
            allocation_id=str(uuid.uuid4()),
            task_id=task.task_id,
            agent_id=agent_id,
            resources=required_resources
        )
        
        self.allocations[allocation.allocation_id] = allocation
        
        logger.info(f"Allocated resources for task {task.name}: {required_resources}")
        
        return allocation.allocation_id
    
    async def release(self, allocation_id: str):
        """Release allocated resources"""
        if allocation_id not in self.allocations:
            return
        
        allocation = self.allocations[allocation_id]
        
        # Release resources
        for res_type, amount in allocation.resources.items():
            if res_type in self.resources:
                self.resources[res_type].release(amount)
        
        allocation.released_at = datetime.now()
        
        logger.info(f"Released resources for allocation {allocation_id}")
        
        # Process waiting queue
        await self._process_waiting_queue()
    
    async def _process_waiting_queue(self):
        """Process tasks in waiting queue"""
        processed = []
        
        for task, required_resources in self.waiting_queue:
            # Try to allocate
            allocation_id = await self.allocate(
                task,
                task.assigned_agent_id or "unknown",
                required_resources
            )
            
            if allocation_id:
                processed.append((task, required_resources))
        
        # Remove processed tasks from queue
        for item in processed:
            self.waiting_queue.remove(item)
    
    def get_status(self) -> Dict[str, Any]:
        """Get resource status"""
        return {
            'resources': {
                res_type: {
                    'total': res.total_capacity,
                    'available': res.available_capacity,
                    'used': res.total_capacity - res.available_capacity,
                    'utilization': (res.total_capacity - res.available_capacity) / res.total_capacity,
                    'unit': res.unit
                }
                for res_type, res in self.resources.items()
            },
            'active_allocations': len([a for a in self.allocations.values() if not a.released_at]),
            'waiting_queue': len(self.waiting_queue)
        }


# ==================== FAILURE RECOVERY ====================

class FailureType(Enum):
    """Types of failures"""
    TASK_FAILURE = "task_failure"
    AGENT_FAILURE = "agent_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT = "timeout"
    DEPENDENCY_FAILURE = "dependency_failure"
    VALIDATION_FAILURE = "validation_failure"


@dataclass
class Failure:
    """Failure record"""
    failure_id: str
    failure_type: FailureType
    task_id: str
    agent_id: Optional[str]
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryStrategy:
    """Recovery strategy for a failure"""
    strategy_id: str
    failure_type: FailureType
    actions: List[str]  # retry, reassign, rollback, skip, escalate
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds
    backoff_factor: float = 2.0


class FailureRecoverySystem:
    """
    Failure Recovery System
    
    Handles failures with multiple recovery strategies:
    - Retry with exponential backoff
    - Task reassignment
    - Rollback to checkpoint
    - Graceful degradation
    - Escalation to human
    
    ┌─────────────────────────────────────────────────────┐
    │           FAILURE RECOVERY                           │
    │                                                      │
    │  Failure Detected                                    │
    │       │                                              │
    │       ├─ Classify Failure Type                      │
    │       │                                              │
    │       ├─ Select Recovery Strategy                   │
    │       │    ├─ Retry (with backoff)                  │
    │       │    ├─ Reassign to different agent           │
    │       │    ├─ Rollback to checkpoint                │
    │       │    ├─ Skip and continue                     │
    │       │    └─ Escalate to supervisor                │
    │       │                                              │
    │       ├─ Execute Recovery                           │
    │       │                                              │
    │       └─ Learn from Failure                         │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.failures: List[Failure] = []
        self.recovery_strategies: Dict[FailureType, RecoveryStrategy] = {}
        self.retry_counts: Dict[str, int] = defaultdict(int)
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        
        # Register default strategies
        self._register_default_strategies()
        
        logger.info("Failure Recovery System initialized")
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        self.recovery_strategies[FailureType.TASK_FAILURE] = RecoveryStrategy(
            strategy_id="task_failure_recovery",
            failure_type=FailureType.TASK_FAILURE,
            actions=["retry", "reassign", "escalate"],
            max_retries=3
        )
        
        self.recovery_strategies[FailureType.AGENT_FAILURE] = RecoveryStrategy(
            strategy_id="agent_failure_recovery",
            failure_type=FailureType.AGENT_FAILURE,
            actions=["reassign", "escalate"],
            max_retries=1
        )
        
        self.recovery_strategies[FailureType.TIMEOUT] = RecoveryStrategy(
            strategy_id="timeout_recovery",
            failure_type=FailureType.TIMEOUT,
            actions=["retry", "reassign"],
            max_retries=2
        )
        
        self.recovery_strategies[FailureType.RESOURCE_EXHAUSTION] = RecoveryStrategy(
            strategy_id="resource_recovery",
            failure_type=FailureType.RESOURCE_EXHAUSTION,
            actions=["wait", "retry"],
            max_retries=5,
            retry_delay=10.0
        )
    
    async def handle_failure(
        self,
        task: Task,
        failure_type: FailureType,
        error_message: str,
        agent_id: Optional[str] = None
    ) -> str:
        """
        Handle a failure.
        
        Returns recovery action: retry, reassign, rollback, skip, escalate
        """
        # Record failure
        failure = Failure(
            failure_id=str(uuid.uuid4()),
            failure_type=failure_type,
            task_id=task.task_id,
            agent_id=agent_id,
            error_message=error_message
        )
        self.failures.append(failure)
        
        logger.warning(f"Failure detected: {failure_type.value} for task {task.name}")
        
        # Get recovery strategy
        strategy = self.recovery_strategies.get(failure_type)
        if not strategy:
            return "escalate"
        
        # Check retry count
        retry_count = self.retry_counts[task.task_id]
        
        if retry_count >= strategy.max_retries:
            logger.error(f"Max retries exceeded for task {task.task_id}")
            return "escalate"
        
        # Select recovery action
        action = strategy.actions[min(retry_count, len(strategy.actions) - 1)]
        
        # Execute recovery
        if action == "retry":
            self.retry_counts[task.task_id] += 1
            delay = strategy.retry_delay * (strategy.backoff_factor ** retry_count)
            logger.info(f"Retrying task {task.name} after {delay}s (attempt {retry_count + 1})")
            await asyncio.sleep(delay)
        
        elif action == "reassign":
            logger.info(f"Reassigning task {task.name} to different agent")
            task.assigned_agent_id = None
            task.status = TaskStatus.PENDING
        
        elif action == "rollback":
            logger.info(f"Rolling back task {task.name} to checkpoint")
            await self._rollback_to_checkpoint(task.task_id)
        
        return action
    
    async def create_checkpoint(self, task_id: str, state: Dict[str, Any]):
        """Create a checkpoint for rollback"""
        self.checkpoints[task_id] = {
            'state': state,
            'timestamp': datetime.now()
        }
        logger.debug(f"Checkpoint created for task {task_id}")
    
    async def _rollback_to_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Rollback to checkpoint"""
        if task_id not in self.checkpoints:
            logger.warning(f"No checkpoint found for task {task_id}")
            return None
        
        checkpoint = self.checkpoints[task_id]
        logger.info(f"Rolled back task {task_id} to checkpoint from {checkpoint['timestamp']}")
        
        return checkpoint['state']
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure statistics"""
        total_failures = len(self.failures)
        
        if total_failures == 0:
            return {'total_failures': 0}
        
        failure_by_type = defaultdict(int)
        for failure in self.failures:
            failure_by_type[failure.failure_type.value] += 1
        
        return {
            'total_failures': total_failures,
            'by_type': dict(failure_by_type),
            'recent_failures': [
                {
                    'type': f.failure_type.value,
                    'task_id': f.task_id,
                    'error': f.error_message,
                    'timestamp': f.timestamp.isoformat()
                }
                for f in self.failures[-10:]  # Last 10
            ]
        }


# Continue in next file due to length...
