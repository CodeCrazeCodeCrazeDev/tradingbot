"""
Self-Coordinating AI Core - Part 2
Coordination Layer, Shared Memory, Governance, Learning Loop, Dynamic Sub-Agent Creation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


# ==================== COORDINATION LAYER ====================

class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUERY = "query"
    COMMAND = "command"
    BROADCAST = "broadcast"


@dataclass
class Message:
    """Inter-agent message"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: str  # or "broadcast"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None
    priority: int = 3  # 1-5, 5 is highest


class CoordinationLayer:
    """
    Coordination Layer - Inter-Agent Communication
    
    Manages communication between agents using message passing.
    Implements publish-subscribe pattern for broadcasts.
    
    ┌─────────────────────────────────────────────────────┐
    │         COORDINATION LAYER                           │
    │                                                      │
    │  Agent A ←──────┐                                   │
    │     │           │                                   │
    │     │      Message Bus                              │
    │     │           │                                   │
    │     └──────→ Agent B                                │
    │                  │                                   │
    │              Agent C                                │
    │                                                      │
    │  Subscriptions:                                      │
    │  - Agent A: [task_complete, market_update]          │
    │  - Agent B: [task_complete, risk_alert]             │
    │  - Agent C: [market_update, risk_alert]             │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.message_queue: List[Message] = []
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # topic -> agent_ids
        self.message_handlers: Dict[str, Callable] = {}  # agent_id -> handler
        
        logger.info("Coordination Layer initialized")
    
    async def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: int = 3
    ) -> str:
        """Send a message from one agent to another"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            priority=priority
        )
        
        self.message_queue.append(message)
        self.message_queue.sort(key=lambda m: m.priority, reverse=True)
        
        logger.debug(f"Message sent: {sender_id} -> {receiver_id} ({message_type.value})")
        
        # Deliver immediately if handler registered
        if receiver_id in self.message_handlers:
            await self._deliver_message(message)
        
        return message.message_id
    
    async def broadcast(
        self,
        sender_id: str,
        topic: str,
        content: Dict[str, Any],
        priority: int = 3
    ):
        """Broadcast message to all subscribers of a topic"""
        subscribers = self.subscriptions.get(topic, set())
        
        logger.debug(f"Broadcasting to {len(subscribers)} subscribers on topic '{topic}'")
        
        for receiver_id in subscribers:
            await self.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=MessageType.BROADCAST,
                content={'topic': topic, **content},
                priority=priority
            )
    
    def subscribe(self, agent_id: str, topic: str):
        """Subscribe agent to a topic"""
        self.subscriptions[topic].add(agent_id)
        logger.debug(f"Agent {agent_id} subscribed to '{topic}'")
    
    def unsubscribe(self, agent_id: str, topic: str):
        """Unsubscribe agent from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(agent_id)
            logger.debug(f"Agent {agent_id} unsubscribed from '{topic}'")
    
    def register_handler(self, agent_id: str, handler: Callable):
        """Register message handler for an agent"""
        self.message_handlers[agent_id] = handler
    
    async def _deliver_message(self, message: Message):
        """Deliver message to recipient"""
        handler = self.message_handlers.get(message.receiver_id)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error delivering message to {message.receiver_id}: {e}")
    
    async def process_messages(self):
        """Process pending messages"""
        while self.message_queue:
            message = self.message_queue.pop(0)
            await self._deliver_message(message)
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordination layer status"""
        return {
            'pending_messages': len(self.message_queue),
            'active_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'topics': list(self.subscriptions.keys()),
            'registered_handlers': len(self.message_handlers)
        }


# ==================== SHARED MEMORY ====================

class SharedMemoryScope(Enum):
    """Scope of shared memory"""
    GLOBAL = "global"  # Accessible by all agents
    TEAM = "team"      # Accessible by team members
    PRIVATE = "private"  # Accessible by specific agents


@dataclass
class SharedMemoryEntry:
    """Entry in shared memory"""
    key: str
    value: Any
    scope: SharedMemoryScope
    owner_id: str
    allowed_agents: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedMemory:
    """
    Shared Memory System - Collaborative Workspace
    
    Provides shared memory space for agents to collaborate.
    Supports different access scopes and versioning.
    
    ┌─────────────────────────────────────────────────────┐
    │           SHARED MEMORY                              │
    │                                                      │
    │  Global Scope:                                       │
    │  ├─ market_state: {...}                             │
    │  ├─ system_config: {...}                            │
    │  └─ performance_metrics: {...}                      │
    │                                                      │
    │  Team Scope (Trading Team):                         │
    │  ├─ active_positions: [...]                         │
    │  ├─ risk_limits: {...}                              │
    │  └─ trading_signals: [...]                          │
    │                                                      │
    │  Private Scope:                                      │
    │  └─ agent_A_state: {...}                            │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self):
        self.memory: Dict[str, SharedMemoryEntry] = {}
        self.teams: Dict[str, Set[str]] = defaultdict(set)  # team_name -> agent_ids
        self.locks: Dict[str, asyncio.Lock] = {}
        
        logger.info("Shared Memory initialized")
    
    async def write(
        self,
        key: str,
        value: Any,
        agent_id: str,
        scope: SharedMemoryScope = SharedMemoryScope.GLOBAL,
        allowed_agents: Optional[Set[str]] = None,
        metadata: Optional[Dict] = None
    ):
        """Write to shared memory"""
        # Get lock for this key
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            if key in self.memory:
                # Update existing entry
                entry = self.memory[key]
                entry.value = value
                entry.updated_at = datetime.now()
                entry.version += 1
                if metadata:
                    entry.metadata.update(metadata)
            else:
                # Create new entry
                entry = SharedMemoryEntry(
                    key=key,
                    value=value,
                    scope=scope,
                    owner_id=agent_id,
                    allowed_agents=allowed_agents or set(),
                    metadata=metadata or {}
                )
                self.memory[key] = entry
        
        logger.debug(f"Shared memory write: {key} by {agent_id} (v{entry.version})")
    
    async def read(
        self,
        key: str,
        agent_id: str
    ) -> Optional[Any]:
        """Read from shared memory"""
        if key not in self.memory:
            return None
        
        entry = self.memory[key]
        
        # Check access permissions
        if not self._check_access(entry, agent_id):
            logger.warning(f"Access denied: {agent_id} cannot read {key}")
            return None
        
        return entry.value
    
    def _check_access(self, entry: SharedMemoryEntry, agent_id: str) -> bool:
        """Check if agent has access to entry"""
        if entry.scope == SharedMemoryScope.GLOBAL:
            return True
        
        if entry.scope == SharedMemoryScope.PRIVATE:
            return agent_id == entry.owner_id or agent_id in entry.allowed_agents
        
        if entry.scope == SharedMemoryScope.TEAM:
            # Check if agent is in same team as owner
            for team_agents in self.teams.values():
                if entry.owner_id in team_agents and agent_id in team_agents:
                    return True
            return False
        
        return False
    
    def create_team(self, team_name: str, agent_ids: Set[str]):
        """Create a team for shared memory access"""
        self.teams[team_name] = agent_ids
        logger.info(f"Team '{team_name}' created with {len(agent_ids)} agents")
    
    def add_to_team(self, team_name: str, agent_id: str):
        """Add agent to team"""
        self.teams[team_name].add(agent_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get shared memory status"""
        return {
            'total_entries': len(self.memory),
            'by_scope': {
                'global': sum(1 for e in self.memory.values() if e.scope == SharedMemoryScope.GLOBAL),
                'team': sum(1 for e in self.memory.values() if e.scope == SharedMemoryScope.TEAM),
                'private': sum(1 for e in self.memory.values() if e.scope == SharedMemoryScope.PRIVATE)
            },
            'teams': len(self.teams),
            'keys': list(self.memory.keys())[:20]  # First 20
        }


# ==================== GOVERNANCE ====================

class GovernanceRule(Enum):
    """Governance rules"""
    SAFETY_CHECK = "safety_check"
    RESOURCE_LIMIT = "resource_limit"
    APPROVAL_REQUIRED = "approval_required"
    AUDIT_LOG = "audit_log"
    RATE_LIMIT = "rate_limit"


@dataclass
class GovernancePolicy:
    """Governance policy"""
    policy_id: str
    name: str
    rule: GovernanceRule
    conditions: Dict[str, Any]
    actions: List[str]  # block, warn, log, escalate
    enabled: bool = True


@dataclass
class GovernanceViolation:
    """Governance violation record"""
    violation_id: str
    policy_id: str
    agent_id: str
    task_id: Optional[str]
    description: str
    severity: str  # critical, high, medium, low
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False


class GovernanceSystem:
    """
    Governance System - Agent Oversight and Compliance
    
    Ensures agents follow rules and policies.
    Integrates with Constitutional AI for safety.
    
    ┌─────────────────────────────────────────────────────┐
    │           GOVERNANCE SYSTEM                          │
    │                                                      │
    │  Policies:                                           │
    │  ├─ Safety Check: All actions verified              │
    │  ├─ Resource Limit: Max 4 concurrent tasks          │
    │  ├─ Approval Required: High-risk actions            │
    │  ├─ Audit Log: All decisions logged                 │
    │  └─ Rate Limit: Max 100 actions/hour                │
    │                                                      │
    │  Monitoring:                                         │
    │  ├─ Active Violations: 0                            │
    │  ├─ Warnings Today: 3                               │
    │  └─ Compliance Rate: 99.7%                          │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self, constitutional_layer=None):
        self.constitutional_layer = constitutional_layer
        
        self.policies: Dict[str, GovernancePolicy] = {}
        self.violations: List[GovernanceViolation] = []
        self.action_counts: Dict[str, int] = defaultdict(int)  # agent_id -> count
        self.last_reset: datetime = datetime.now()
        
        # Register default policies
        self._register_default_policies()
        
        logger.info("Governance System initialized")
    
    def _register_default_policies(self):
        """Register default governance policies"""
        self.policies['safety_check'] = GovernancePolicy(
            policy_id='safety_check',
            name='Constitutional Safety Check',
            rule=GovernanceRule.SAFETY_CHECK,
            conditions={'safety_threshold': 0.7},
            actions=['block', 'log']
        )
        
        self.policies['resource_limit'] = GovernancePolicy(
            policy_id='resource_limit',
            name='Resource Usage Limit',
            rule=GovernanceRule.RESOURCE_LIMIT,
            conditions={'max_concurrent_tasks': 4},
            actions=['warn', 'log']
        )
        
        self.policies['rate_limit'] = GovernancePolicy(
            policy_id='rate_limit',
            name='Action Rate Limit',
            rule=GovernanceRule.RATE_LIMIT,
            conditions={'max_actions_per_hour': 100},
            actions=['block', 'log']
        )
    
    async def check_compliance(
        self,
        agent_id: str,
        action: Dict[str, Any],
        task: Optional[Any] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check if action complies with governance policies.
        
        Returns (is_compliant, violations)
        """
        violations = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            if policy.rule == GovernanceRule.SAFETY_CHECK:
                # Use Constitutional AI
                if self.constitutional_layer:
                    critique = await self.constitutional_layer.critique(action)
                    # Support both is_safe and can_proceed attributes
                    is_safe = getattr(critique, 'is_safe', getattr(critique, 'can_proceed', True))
                    if not is_safe:
                        violations.append(f"Safety check failed: {getattr(critique, 'violations', [])}")
            
            elif policy.rule == GovernanceRule.RESOURCE_LIMIT:
                # Check resource limits
                max_tasks = policy.conditions.get('max_concurrent_tasks', 4)
                current_tasks = action.get('current_tasks', 0)
                if current_tasks >= max_tasks:
                    violations.append(f"Resource limit exceeded: {current_tasks}/{max_tasks}")
            
            elif policy.rule == GovernanceRule.RATE_LIMIT:
                # Check rate limits
                max_actions = policy.conditions.get('max_actions_per_hour', 100)
                
                # Reset counter if hour passed
                if datetime.now() - self.last_reset > timedelta(hours=1):
                    self.action_counts.clear()
                    self.last_reset = datetime.now()
                
                if self.action_counts[agent_id] >= max_actions:
                    violations.append(f"Rate limit exceeded: {self.action_counts[agent_id]}/{max_actions}")
        
        # Record violations
        if violations:
            for violation_desc in violations:
                violation = GovernanceViolation(
                    violation_id=str(uuid.uuid4()),
                    policy_id='multiple',
                    agent_id=agent_id,
                    task_id=task.task_id if task else None,
                    description=violation_desc,
                    severity='high'
                )
                self.violations.append(violation)
        
        # Increment action count
        self.action_counts[agent_id] += 1
        
        is_compliant = len(violations) == 0
        
        return is_compliant, violations
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report"""
        total_checks = sum(self.action_counts.values())
        total_violations = len(self.violations)
        
        compliance_rate = (
            (total_checks - total_violations) / total_checks
            if total_checks > 0 else 1.0
        )
        
        return {
            'total_checks': total_checks,
            'total_violations': total_violations,
            'compliance_rate': compliance_rate,
            'active_violations': len([v for v in self.violations if not v.resolved]),
            'violations_by_severity': {
                'critical': sum(1 for v in self.violations if v.severity == 'critical'),
                'high': sum(1 for v in self.violations if v.severity == 'high'),
                'medium': sum(1 for v in self.violations if v.severity == 'medium'),
                'low': sum(1 for v in self.violations if v.severity == 'low')
            },
            'recent_violations': [
                {
                    'agent_id': v.agent_id,
                    'description': v.description,
                    'severity': v.severity,
                    'timestamp': v.timestamp.isoformat()
                }
                for v in self.violations[-10:]
            ]
        }


# ==================== LEARNING LOOP ====================

@dataclass
class CoordinationExperience:
    """Experience from coordination"""
    experience_id: str
    task_id: str
    agents_involved: List[str]
    coordination_pattern: str  # sequential, parallel, hierarchical
    success: bool
    duration: float  # seconds
    resource_efficiency: float  # 0-1
    quality: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    lessons_learned: List[str] = field(default_factory=list)


class CoordinationLearningLoop:
    """
    Learning Loop - Continuous Improvement from Coordination
    
    Learns from coordination experiences to improve future performance.
    
    ┌─────────────────────────────────────────────────────┐
    │         COORDINATION LEARNING LOOP                   │
    │                                                      │
    │  Experience Collection                               │
    │       │                                              │
    │       ├─ Task: Market Analysis                      │
    │       │  Agents: [Planner, Analyzer, Reporter]      │
    │       │  Pattern: Sequential                        │
    │       │  Success: Yes, Duration: 45s                │
    │       │  Efficiency: 0.85, Quality: 0.92            │
    │       │                                              │
    │       ├─ Pattern Analysis                           │
    │       │  → Sequential works well for analysis       │
    │       │  → 3 agents optimal for this task type      │
    │       │  → Reporter should wait for full analysis   │
    │       │                                              │
    │       ├─ Knowledge Update                           │
    │       │  → Store pattern in memory                  │
    │       │  → Update agent selection heuristics        │
    │       │                                              │
    │       └─ Apply Learning                             │
    │          → Use pattern for similar tasks            │
    └─────────────────────────────────────────────────────┘
    """
    
    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        
        self.experiences: List[CoordinationExperience] = []
        self.patterns: Dict[str, Dict[str, Any]] = {}  # pattern_name -> stats
        
        logger.info("Coordination Learning Loop initialized")
    
    async def record_experience(
        self,
        task: Any,
        agents_involved: List[str],
        coordination_pattern: str,
        success: bool,
        duration: float,
        resource_efficiency: float,
        quality: float
    ):
        """Record a coordination experience"""
        experience = CoordinationExperience(
            experience_id=str(uuid.uuid4()),
            task_id=task.task_id,
            agents_involved=agents_involved,
            coordination_pattern=coordination_pattern,
            success=success,
            duration=duration,
            resource_efficiency=resource_efficiency,
            quality=quality
        )
        
        self.experiences.append(experience)
        
        # Analyze and learn
        await self._analyze_experience(experience)
        
        logger.info(f"Recorded coordination experience: {coordination_pattern} "
                   f"({'success' if success else 'failure'})")
    
    async def _analyze_experience(self, experience: CoordinationExperience):
        """Analyze experience and extract lessons"""
        pattern = experience.coordination_pattern
        
        # Update pattern statistics
        if pattern not in self.patterns:
            self.patterns[pattern] = {
                'total_uses': 0,
                'successes': 0,
                'avg_duration': 0.0,
                'avg_efficiency': 0.0,
                'avg_quality': 0.0
            }
        
        stats = self.patterns[pattern]
        stats['total_uses'] += 1
        
        if experience.success:
            stats['successes'] += 1
        
        # Update averages
        n = stats['total_uses']
        stats['avg_duration'] = (stats['avg_duration'] * (n - 1) + experience.duration) / n
        stats['avg_efficiency'] = (stats['avg_efficiency'] * (n - 1) + experience.resource_efficiency) / n
        stats['avg_quality'] = (stats['avg_quality'] * (n - 1) + experience.quality) / n
        
        # Extract lessons
        lessons = []
        
        if experience.success and experience.quality > 0.8:
            lessons.append(f"Pattern '{pattern}' works well for this task type")
        
        if experience.duration < stats['avg_duration'] * 0.8:
            lessons.append(f"This configuration was faster than average")
        
        if experience.resource_efficiency > 0.9:
            lessons.append(f"Excellent resource efficiency achieved")
        
        experience.lessons_learned = lessons
        
        # Store in memory system
        if self.memory_system:
            await self.memory_system.store_knowledge(
                f"coordination_pattern_{pattern}",
                stats,
                related=[f"task_type_{experience.task_id}"]
            )
    
    def recommend_pattern(
        self,
        task_type: str,
        num_agents: int
    ) -> Optional[str]:
        """Recommend coordination pattern based on learned experiences"""
        if not self.patterns:
            return "sequential"  # Default
        
        # Find best performing pattern
        best_pattern = max(
            self.patterns.items(),
            key=lambda x: (
                x[1]['successes'] / max(x[1]['total_uses'], 1) * 0.5 +
                x[1]['avg_quality'] * 0.3 +
                x[1]['avg_efficiency'] * 0.2
            )
        )
        
        return best_pattern[0]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_experiences': len(self.experiences),
            'patterns_learned': len(self.patterns),
            'pattern_stats': self.patterns,
            'recent_lessons': [
                {
                    'pattern': exp.coordination_pattern,
                    'success': exp.success,
                    'lessons': exp.lessons_learned
                }
                for exp in self.experiences[-10:]
            ]
        }


# Export all classes
__all__ = [
    'MessageType', 'Message', 'CoordinationLayer',
    'SharedMemoryScope', 'SharedMemoryEntry', 'SharedMemory',
    'GovernanceRule', 'GovernancePolicy', 'GovernanceViolation', 'GovernanceSystem',
    'CoordinationExperience', 'CoordinationLearningLoop'
]
