"""
Goal Manager - Hierarchical Goal System
========================================

Implements hierarchical goal management:
1. Goal Hierarchy: Long-term to immediate goals
2. Goal Decomposition: Break complex goals into subgoals
3. Goal Selection: Choose which goals to pursue
4. Goal Monitoring: Track progress and adapt

Based on the Foundation Agents paper (arXiv:2504.01990) goal systems.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Status of a goal"""
    PENDING = "pending"          # Not yet started
    ACTIVE = "active"            # Currently being pursued
    PAUSED = "paused"            # Temporarily suspended
    COMPLETED = "completed"      # Successfully achieved
    FAILED = "failed"            # Failed to achieve
    ABANDONED = "abandoned"      # Deliberately abandoned


class GoalPriority(Enum):
    """Priority levels for goals"""
    CRITICAL = 5     # Must achieve
    HIGH = 4         # Very important
    MEDIUM = 3       # Standard priority
    LOW = 2          # Nice to have
    BACKGROUND = 1   # Work on when nothing else


class GoalType(Enum):
    """Types of goals"""
    PROFIT = "profit"                    # Financial goals
    RISK = "risk"                        # Risk management goals
    DISCOVERY = "discovery"              # Research/discovery goals
    LEARNING = "learning"                # Learning/improvement goals
    OPERATIONAL = "operational"          # System operation goals
    SAFETY = "safety"                    # Safety/compliance goals
    EXPLORATION = "exploration"          # Exploration goals


@dataclass
class Goal:
    """A goal in the system"""
    goal_id: str
    name: str
    description: str
    goal_type: GoalType
    priority: GoalPriority
    
    # Hierarchy
    parent_id: Optional[str] = None
    subgoal_ids: List[str] = field(default_factory=list)
    
    # Conditions
    success_conditions: List[Dict[str, Any]] = field(default_factory=list)
    failure_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Progress
    progress: float = 0.0  # 0 to 1
    status: GoalStatus = GoalStatus.PENDING
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resources
    estimated_effort: float = 1.0  # Arbitrary units
    actual_effort: float = 0.0
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    # Metrics
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_achievable(self, completed_goals: Set[str]) -> bool:
        """Check if goal can be pursued (dependencies met)"""
        return all(dep in completed_goals for dep in self.depends_on)
    
    def is_overdue(self) -> bool:
        """Check if goal is past deadline"""
        if self.deadline:
            return datetime.utcnow() > self.deadline
        return False
    
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until deadline"""
        if self.deadline:
            return self.deadline - datetime.utcnow()
        return None
    
    def to_dict(self) -> Dict:
        return {
            'goal_id': self.goal_id,
            'name': self.name,
            'description': self.description,
            'goal_type': self.goal_type.value,
            'priority': self.priority.value,
            'parent_id': self.parent_id,
            'subgoal_ids': self.subgoal_ids,
            'progress': self.progress,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'target_value': self.target_value,
            'current_value': self.current_value
        }


@dataclass
class GoalHierarchy:
    """Hierarchical structure of goals"""
    root_goals: List[str] = field(default_factory=list)
    goal_tree: Dict[str, List[str]] = field(default_factory=dict)  # parent -> children
    
    def add_goal(self, goal: Goal):
        """Add goal to hierarchy"""
        if goal.parent_id:
            if goal.parent_id not in self.goal_tree:
                self.goal_tree[goal.parent_id] = []
            self.goal_tree[goal.parent_id].append(goal.goal_id)
        else:
            self.root_goals.append(goal.goal_id)
    
    def get_children(self, goal_id: str) -> List[str]:
        """Get child goals"""
        return self.goal_tree.get(goal_id, [])
    
    def get_depth(self, goal_id: str, goals: Dict[str, Goal]) -> int:
        """Get depth of goal in hierarchy"""
        depth = 0
        current = goal_id
        while current:
            goal = goals.get(current)
            if goal and goal.parent_id:
                current = goal.parent_id
                depth += 1
            else:
                break
        return depth


class GoalDecomposer:
    """
    Goal Decomposition Engine
    
    Breaks complex goals into achievable subgoals.
    """
    
    def __init__(self):
        self.decomposition_rules: Dict[GoalType, List[Callable]] = defaultdict(list)
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize decomposition rules for each goal type"""
        # Profit goal decomposition
        self.decomposition_rules[GoalType.PROFIT].append(self._decompose_profit_goal)
        
        # Discovery goal decomposition
        self.decomposition_rules[GoalType.DISCOVERY].append(self._decompose_discovery_goal)
        
        # Learning goal decomposition
        self.decomposition_rules[GoalType.LEARNING].append(self._decompose_learning_goal)
    
    def decompose(self, goal: Goal) -> List[Goal]:
        """Decompose a goal into subgoals"""
        subgoals = []
        
        rules = self.decomposition_rules.get(goal.goal_type, [])
        for rule in rules:
            subgoals.extend(rule(goal))
        
        # Set parent relationship
        for subgoal in subgoals:
            subgoal.parent_id = goal.goal_id
        
        return subgoals
    
    def _decompose_profit_goal(self, goal: Goal) -> List[Goal]:
        """Decompose profit goal"""
        subgoals = []
        
        if goal.target_value and goal.target_value > 0.1:  # Significant profit target
            # Break into phases
            phases = 3
            phase_target = goal.target_value / phases
            
            for i in range(phases):
                subgoal = Goal(
                    goal_id=f"{goal.goal_id}_phase_{i+1}",
                    name=f"{goal.name} - Phase {i+1}",
                    description=f"Achieve {phase_target:.2%} profit (phase {i+1} of {phases})",
                    goal_type=GoalType.PROFIT,
                    priority=goal.priority,
                    target_value=phase_target,
                    estimated_effort=goal.estimated_effort / phases
                )
                
                if i > 0:
                    subgoal.depends_on.append(f"{goal.goal_id}_phase_{i}")
                
                subgoals.append(subgoal)
        
        return subgoals
    
    def _decompose_discovery_goal(self, goal: Goal) -> List[Goal]:
        """Decompose discovery goal"""
        subgoals = []
        
        # Standard discovery phases
        phases = [
            ("research", "Research existing knowledge", 0.2),
            ("hypothesis", "Generate hypotheses", 0.2),
            ("experiment", "Design and run experiments", 0.3),
            ("validate", "Validate findings", 0.2),
            ("document", "Document and integrate", 0.1)
        ]
        
        prev_id = None
        for phase_id, phase_name, effort_fraction in phases:
            subgoal = Goal(
                goal_id=f"{goal.goal_id}_{phase_id}",
                name=f"{goal.name} - {phase_name}",
                description=phase_name,
                goal_type=GoalType.DISCOVERY,
                priority=goal.priority,
                estimated_effort=goal.estimated_effort * effort_fraction
            )
            
            if prev_id:
                subgoal.depends_on.append(prev_id)
            
            subgoals.append(subgoal)
            prev_id = subgoal.goal_id
        
        return subgoals
    
    def _decompose_learning_goal(self, goal: Goal) -> List[Goal]:
        """Decompose learning goal"""
        subgoals = []
        
        # Learning phases
        phases = [
            ("acquire", "Acquire new knowledge", 0.3),
            ("practice", "Practice and apply", 0.4),
            ("evaluate", "Evaluate understanding", 0.2),
            ("integrate", "Integrate into system", 0.1)
        ]
        
        prev_id = None
        for phase_id, phase_name, effort_fraction in phases:
            subgoal = Goal(
                goal_id=f"{goal.goal_id}_{phase_id}",
                name=f"{goal.name} - {phase_name}",
                description=phase_name,
                goal_type=GoalType.LEARNING,
                priority=goal.priority,
                estimated_effort=goal.estimated_effort * effort_fraction
            )
            
            if prev_id:
                subgoal.depends_on.append(prev_id)
            
            subgoals.append(subgoal)
            prev_id = subgoal.goal_id
        
        return subgoals


class GoalSelector:
    """
    Goal Selection Engine
    
    Selects which goals to pursue based on:
    - Priority
    - Dependencies
    - Resource availability
    - Expected value
    """
    
    def __init__(self):
        self.selection_history: List[str] = []
    
    def select_goals(
        self,
        goals: Dict[str, Goal],
        max_active: int = 3,
        completed_goals: Optional[Set[str]] = None
    ) -> List[Goal]:
        """Select goals to pursue"""
        completed = completed_goals or set()
        
        # Filter to achievable, non-completed goals
        candidates = [
            g for g in goals.values()
            if g.status in [GoalStatus.PENDING, GoalStatus.PAUSED]
            and g.is_achievable(completed)
        ]
        
        # Score each goal
        scored = [(self._score_goal(g), g) for g in candidates]
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Select top goals
        selected = [g for _, g in scored[:max_active]]
        
        # Record selection
        for g in selected:
            self.selection_history.append(g.goal_id)
        
        return selected
    
    def _score_goal(self, goal: Goal) -> float:
        """Score a goal for selection"""
        score = 0.0
        
        # Priority weight
        score += goal.priority.value * 10
        
        # Urgency (deadline proximity)
        if goal.deadline:
            time_left = (goal.deadline - datetime.utcnow()).total_seconds()
            if time_left > 0:
                urgency = 1.0 / (1 + time_left / 86400)  # Days
                score += urgency * 20
            else:
                score -= 10  # Penalty for overdue
        
        # Progress bonus (prefer goals with some progress)
        if 0 < goal.progress < 1:
            score += goal.progress * 5
        
        # Effort efficiency (prefer lower effort)
        if goal.estimated_effort > 0:
            score += 5 / goal.estimated_effort
        
        # Dependency bonus (prefer goals that unblock others)
        score += len(goal.blocks) * 3
        
        return score


class GoalManager:
    """
    Goal Manager
    
    Central system for managing all goals:
    - Goal creation and tracking
    - Hierarchical organization
    - Progress monitoring
    - Adaptive goal adjustment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Goal storage
        self.goals: Dict[str, Goal] = {}
        self.hierarchy = GoalHierarchy()
        
        # Subsystems
        self.decomposer = GoalDecomposer()
        self.selector = GoalSelector()
        
        # Active goals
        self.active_goals: Set[str] = set()
        self.completed_goals: Set[str] = set()
        
        # Statistics
        self.stats = {
            'goals_created': 0,
            'goals_completed': 0,
            'goals_failed': 0,
            'goals_abandoned': 0,
            'avg_completion_time': 0.0
        }
        
        # Initialize default goals
        self._initialize_default_goals()
        
        logger.info("Goal Manager initialized")
    
    def _initialize_default_goals(self):
        """Initialize default system goals"""
        default_goals = [
            Goal(
                goal_id="goal_profit_daily",
                name="Daily Profit Target",
                description="Achieve positive daily returns",
                goal_type=GoalType.PROFIT,
                priority=GoalPriority.HIGH,
                target_value=0.001,  # 0.1% daily
                deadline=datetime.utcnow() + timedelta(days=1)
            ),
            Goal(
                goal_id="goal_risk_management",
                name="Risk Management",
                description="Maintain risk within acceptable bounds",
                goal_type=GoalType.RISK,
                priority=GoalPriority.CRITICAL,
                target_value=0.02  # Max 2% drawdown
            ),
            Goal(
                goal_id="goal_discovery",
                name="Alpha Discovery",
                description="Discover new alpha signals",
                goal_type=GoalType.DISCOVERY,
                priority=GoalPriority.MEDIUM
            ),
            Goal(
                goal_id="goal_learning",
                name="Continuous Learning",
                description="Continuously improve system knowledge",
                goal_type=GoalType.LEARNING,
                priority=GoalPriority.MEDIUM
            ),
            Goal(
                goal_id="goal_safety",
                name="System Safety",
                description="Maintain safe operation",
                goal_type=GoalType.SAFETY,
                priority=GoalPriority.CRITICAL
            )
        ]
        
        for goal in default_goals:
            self.add_goal(goal)
    
    def add_goal(
        self,
        goal: Goal,
        auto_decompose: bool = False
    ) -> str:
        """Add a new goal"""
        self.goals[goal.goal_id] = goal
        self.hierarchy.add_goal(goal)
        self.stats['goals_created'] += 1
        
        # Auto-decompose if requested
        if auto_decompose:
            subgoals = self.decomposer.decompose(goal)
            for subgoal in subgoals:
                self.add_goal(subgoal, auto_decompose=False)
            goal.subgoal_ids = [sg.goal_id for sg in subgoals]
        
        logger.info(f"Added goal: {goal.name}")
        return goal.goal_id
    
    def create_goal(
        self,
        name: str,
        description: str,
        goal_type: GoalType,
        priority: GoalPriority = GoalPriority.MEDIUM,
        target_value: Optional[float] = None,
        deadline: Optional[datetime] = None,
        parent_id: Optional[str] = None,
        auto_decompose: bool = False,
        metadata: Optional[Dict] = None
    ) -> Goal:
        """Create and add a new goal"""
        goal = Goal(
            goal_id=f"goal_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            goal_type=goal_type,
            priority=priority,
            target_value=target_value,
            deadline=deadline,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.add_goal(goal, auto_decompose=auto_decompose)
        return goal
    
    def activate_goal(self, goal_id: str) -> bool:
        """Activate a goal for pursuit"""
        if goal_id not in self.goals:
            return False
        
        goal = self.goals[goal_id]
        
        if not goal.is_achievable(self.completed_goals):
            logger.warning(f"Cannot activate goal {goal_id}: dependencies not met")
            return False
        
        goal.status = GoalStatus.ACTIVE
        goal.started_at = datetime.utcnow()
        self.active_goals.add(goal_id)
        
        logger.info(f"Activated goal: {goal.name}")
        return True
    
    def update_progress(
        self,
        goal_id: str,
        progress: Optional[float] = None,
        current_value: Optional[float] = None,
        effort_spent: float = 0.0
    ):
        """Update goal progress"""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        
        if progress is not None:
            goal.progress = min(1.0, max(0.0, progress))
        
        if current_value is not None:
            goal.current_value = current_value
            
            # Auto-calculate progress if target exists
            if goal.target_value is not None and goal.target_value != 0:
                goal.progress = min(1.0, current_value / goal.target_value)
        
        goal.actual_effort += effort_spent
        
        # Check completion
        if goal.progress >= 1.0:
            self.complete_goal(goal_id, success=True)
        
        # Check failure conditions
        for condition in goal.failure_conditions:
            if self._check_condition(condition, goal):
                self.complete_goal(goal_id, success=False)
                break
    
    def _check_condition(self, condition: Dict[str, Any], goal: Goal) -> bool:
        """Check if a condition is met"""
        condition_type = condition.get('type')
        
        if condition_type == 'value_below':
            threshold = condition.get('threshold', 0)
            return (goal.current_value or 0) < threshold
        
        if condition_type == 'value_above':
            threshold = condition.get('threshold', 0)
            return (goal.current_value or 0) > threshold
        
        if condition_type == 'deadline_passed':
            return goal.is_overdue()
        
        return False
    
    def complete_goal(self, goal_id: str, success: bool = True):
        """Mark a goal as completed"""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        goal.completed_at = datetime.utcnow()
        
        if success:
            goal.status = GoalStatus.COMPLETED
            goal.progress = 1.0
            self.completed_goals.add(goal_id)
            self.stats['goals_completed'] += 1
            logger.info(f"Goal completed: {goal.name}")
        else:
            goal.status = GoalStatus.FAILED
            self.stats['goals_failed'] += 1
            logger.warning(f"Goal failed: {goal.name}")
        
        self.active_goals.discard(goal_id)
        
        # Update completion time stats
        if goal.started_at:
            completion_time = (goal.completed_at - goal.started_at).total_seconds()
            n = self.stats['goals_completed'] + self.stats['goals_failed']
            self.stats['avg_completion_time'] = (
                (self.stats['avg_completion_time'] * (n - 1) + completion_time) / n
            )
        
        # Update parent goal progress
        if goal.parent_id and goal.parent_id in self.goals:
            self._update_parent_progress(goal.parent_id)
    
    def _update_parent_progress(self, parent_id: str):
        """Update parent goal progress based on children"""
        parent = self.goals[parent_id]
        children = self.hierarchy.get_children(parent_id)
        
        if not children:
            return
        
        # Calculate average progress of children
        child_progress = []
        for child_id in children:
            if child_id in self.goals:
                child_progress.append(self.goals[child_id].progress)
        
        if child_progress:
            parent.progress = sum(child_progress) / len(child_progress)
            
            if parent.progress >= 1.0:
                self.complete_goal(parent_id, success=True)
    
    def abandon_goal(self, goal_id: str, reason: str = ""):
        """Abandon a goal"""
        if goal_id not in self.goals:
            return
        
        goal = self.goals[goal_id]
        goal.status = GoalStatus.ABANDONED
        goal.metadata['abandon_reason'] = reason
        
        self.active_goals.discard(goal_id)
        self.stats['goals_abandoned'] += 1
        
        logger.info(f"Goal abandoned: {goal.name} - {reason}")
    
    def select_next_goals(self, max_active: int = 3) -> List[Goal]:
        """Select next goals to pursue"""
        # Deactivate completed/failed goals
        to_deactivate = [
            gid for gid in self.active_goals
            if self.goals[gid].status not in [GoalStatus.ACTIVE, GoalStatus.PENDING]
        ]
        for gid in to_deactivate:
            self.active_goals.discard(gid)
        
        # Select new goals
        selected = self.selector.select_goals(
            self.goals,
            max_active=max_active,
            completed_goals=self.completed_goals
        )
        
        # Activate selected goals
        for goal in selected:
            if goal.goal_id not in self.active_goals:
                self.activate_goal(goal.goal_id)
        
        return selected
    
    def get_active_goals(self) -> List[Goal]:
        """Get currently active goals"""
        return [self.goals[gid] for gid in self.active_goals if gid in self.goals]
    
    def get_goal_tree(self, root_id: Optional[str] = None) -> Dict[str, Any]:
        """Get goal hierarchy as tree structure"""
        def build_tree(goal_id: str) -> Dict[str, Any]:
            goal = self.goals.get(goal_id)
            if not goal:
                return {}
            
            children = self.hierarchy.get_children(goal_id)
            
            return {
                'goal': goal.to_dict(),
                'children': [build_tree(cid) for cid in children]
            }
        
        if root_id:
            return build_tree(root_id)
        
        return {
            'roots': [build_tree(rid) for rid in self.hierarchy.root_goals]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get goal management statistics"""
        active = [self.goals[gid] for gid in self.active_goals if gid in self.goals]
        
        return {
            **self.stats,
            'total_goals': len(self.goals),
            'active_goals': len(self.active_goals),
            'completed_goals': len(self.completed_goals),
            'pending_goals': len([g for g in self.goals.values() if g.status == GoalStatus.PENDING]),
            'overdue_goals': len([g for g in self.goals.values() if g.is_overdue()]),
            'by_type': {
                gt.value: len([g for g in self.goals.values() if g.goal_type == gt])
                for gt in GoalType
            },
            'by_priority': {
                gp.value: len([g for g in self.goals.values() if g.priority == gp])
                for gp in GoalPriority
            },
            'active_goal_names': [g.name for g in active]
        }
