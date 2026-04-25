"""
Research Agenda - Self-Directed Research Planning
=====================================================

Manages autonomous research planning:
1. Research priority assessment
2. Resource allocation
3. Timeline management
4. Goal decomposition
5. Progress tracking

Enables the AI to plan and manage its own research activities.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class ResearchPriority(Enum):
    """Research priority levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


class ResearchStatus(Enum):
    """Status of research items"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEPRECATED = "deprecated"


class ResearchArea(Enum):
    """Research areas/domains"""
    ALPHA_DISCOVERY = "alpha_discovery"
    RISK_MODELING = "risk_modeling"
    MARKET_MICROSTRUCTURE = "market_microstructure"
    CAUSAL_INFERENCE = "causal_inference"
    CROSS_DOMAIN = "cross_domain"
    BEHAVIORAL_FINANCE = "behavioral_finance"
    ML_METHODS = "ml_methods"
    ECONOMIC_THEORY = "economic_theory"


@dataclass
class ResearchItem:
    """An item in the research agenda"""
    item_id: str
    title: str
    description: str
    
    # Classification
    research_area: ResearchArea
    priority: ResearchPriority
    
    # Requirements
    required_resources: List[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    required_data: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # item_ids
    
    # Status
    status: ResearchStatus = ResearchStatus.PENDING
    progress_percentage: float = 0.0
    
    # Timeline
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    
    # Outcomes
    expected_outcomes: List[str] = field(default_factory=list)
    actual_outcomes: List[str] = field(default_factory=list)
    
    # Attribution
    origin_hypothesis: Optional[str] = None  # hypothesis_id that generated this
    assigned_agents: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def is_overdue(self) -> bool:
        if self.scheduled_end and self.status not in [ResearchStatus.COMPLETED, ResearchStatus.DEPRECATED]:
            return datetime.utcnow() > self.scheduled_end
        return False
    
    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'title': self.title,
            'area': self.research_area.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'progress': self.progress_percentage,
            'overdue': self.is_overdue()
        }


@dataclass
class ResearchMilestone:
    """A milestone in the research agenda"""
    milestone_id: str
    title: str
    description: str
    
    # Target
    target_items: List[str] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    
    # Status
    status: ResearchStatus = ResearchStatus.PENDING
    progress: float = 0.0
    
    # Timeline
    target_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResearchAgenda:
    """
    Research Agenda Manager
    
    Manages the AI's self-directed research planning,
    including prioritization, scheduling, and progress tracking.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Agenda items
        self.items: Dict[str, ResearchItem] = {}
        self.milestones: Dict[str, ResearchMilestone] = {}
        
        # Categorization
        self.items_by_area: Dict[ResearchArea, Set[str]] = defaultdict(set)
        self.items_by_status: Dict[ResearchStatus, Set[str]] = defaultdict(set)
        
        # Resources
        self.available_resources: Dict[str, float] = {
            'compute_hours_per_day': 24.0,
            'data_budget': 1000.0,
            'agent_capacity': 10.0
        }
        self.resource_usage: Dict[str, float] = defaultdict(float)
        
        # Scheduling
        self.schedule_horizon_days = self.config.get('schedule_horizon_days', 30)
        
        # History
        self.completed_items: List[ResearchItem] = []
        
        # Statistics
        self.stats = {
            'items_created': 0,
            'items_completed': 0,
            'total_hours_invested': 0.0
        }
        
        logger.info("Research Agenda initialized")
    
    def add_research_item(
        self,
        title: str,
        description: str,
        research_area: ResearchArea,
        priority: ResearchPriority = ResearchPriority.MEDIUM,
        estimated_effort_hours: float = 0.0,
        expected_outcomes: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        origin_hypothesis: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ResearchItem:
        """Add a new research item to the agenda"""
        item = ResearchItem(
            item_id=f"ri_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            research_area=research_area,
            priority=priority,
            estimated_effort_hours=estimated_effort_hours,
            expected_outcomes=expected_outcomes or [],
            dependencies=dependencies or [],
            origin_hypothesis=origin_hypothesis,
            tags=tags or []
        )
        
        self.items[item.item_id] = item
        self.items_by_area[research_area].add(item.item_id)
        self.items_by_status[ResearchStatus.PENDING].add(item.item_id)
        
        self.stats['items_created'] += 1
        
        logger.info(f"Added research item: {title} ({item.item_id})")
        
        return item
    
    def create_milestone(
        self,
        title: str,
        description: str,
        target_items: List[str],
        target_date: Optional[datetime] = None
    ) -> ResearchMilestone:
        """Create a research milestone"""
        milestone = ResearchMilestone(
            milestone_id=f"ms_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            target_items=target_items,
            target_date=target_date
        )
        
        self.milestones[milestone.milestone_id] = milestone
        
        return milestone
    
    def prioritize_agenda(
        self,
        consider_dependencies: bool = True,
        consider_resources: bool = True
    ) -> List[ResearchItem]:
        """Prioritize all research items"""
        # Get pending and in-progress items
        active_items = [
            item for item in self.items.values()
            if item.status in [ResearchStatus.PENDING, ResearchStatus.SCHEDULED]
        ]
        
        # Calculate priority scores
        scored_items = []
        
        for item in active_items:
            score = self._calculate_priority_score(
                item,
                consider_dependencies=consider_dependencies,
                consider_resources=consider_resources
            )
            scored_items.append((item, score))
        
        # Sort by score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in scored_items]
    
    def _calculate_priority_score(
        self,
        item: ResearchItem,
        consider_dependencies: bool,
        consider_resources: bool
    ) -> float:
        """Calculate priority score for an item"""
        # Base score from priority
        base_score = item.priority.value * 10
        
        # Age factor (older items get slight boost)
        age_days = (datetime.utcnow() - item.created_at).days
        age_factor = min(5, age_days / 7)  # Max 5 points for age
        
        # Strategic importance by area
        area_weights = {
            ResearchArea.ALPHA_DISCOVERY: 2.0,
            ResearchArea.RISK_MODELING: 1.8,
            ResearchArea.CAUSAL_INFERENCE: 1.5,
            ResearchArea.MARKET_MICROSTRUCTURE: 1.3,
            ResearchArea.CROSS_DOMAIN: 1.2,
            ResearchArea.BEHAVIORAL_FINANCE: 1.0,
            ResearchArea.ML_METHODS: 1.0,
            ResearchArea.ECONOMIC_THEORY: 1.1
        }
        area_factor = area_weights.get(item.research_area, 1.0)
        
        # Dependency factor
        dep_factor = 1.0
        if consider_dependencies:
            # Items with unmet dependencies get reduced score
            unmet_deps = [
                dep for dep in item.dependencies
                if dep in self.items and self.items[dep].status != ResearchStatus.COMPLETED
            ]
            dep_factor = 1.0 - (len(unmet_deps) * 0.3)
        
        # Resource fit
        resource_factor = 1.0
        if consider_resources:
            # Check if required resources are available
            for resource in item.required_resources:
                usage = self.resource_usage.get(resource, 0)
                available = self.available_resources.get(resource, 100)
                if usage > available * 0.8:  # Resource is mostly used
                    resource_factor *= 0.8
        
        # Overdue bonus/penalty
        overdue_factor = 1.5 if item.is_overdue() else 1.0
        
        # Calculate final score
        score = (
            base_score * area_factor * dep_factor * resource_factor * overdue_factor + age_factor
        )
        
        return score
    
    def schedule_items(
        self,
        items: Optional[List[ResearchItem]] = None,
        start_date: Optional[datetime] = None
    ) -> Dict[str, Tuple[datetime, datetime]]:
        """Schedule research items"""
        if items is None:
            items = self.prioritize_agenda()
        
        if start_date is None:
            start_date = datetime.utcnow()
        
        schedule = {}
        current_date = start_date
        
        for item in items:
            # Check if item is schedulable
            if not self._is_schedulable(item):
                continue
            
            # Calculate duration
            duration_days = max(1, int(item.estimated_effort_hours / 8))  # 8 hours per day
            
            # Set schedule
            item.scheduled_start = current_date
            item.scheduled_end = current_date + timedelta(days=duration_days)
            item.status = ResearchStatus.SCHEDULED
            
            # Update indices
            self.items_by_status[ResearchStatus.PENDING].discard(item.item_id)
            self.items_by_status[ResearchStatus.SCHEDULED].add(item.item_id)
            
            schedule[item.item_id] = (item.scheduled_start, item.scheduled_end)
            
            # Move current date
            current_date = item.scheduled_end + timedelta(days=1)
            
            # Check horizon
            if (current_date - start_date).days > self.schedule_horizon_days:
                break
        
        return schedule
    
    def _is_schedulable(self, item: ResearchItem) -> bool:
        """Check if item can be scheduled"""
        # Check if dependencies are met
        for dep_id in item.dependencies:
            if dep_id in self.items:
                if self.items[dep_id].status != ResearchStatus.COMPLETED:
                    return False
            else:
                # Dependency doesn't exist
                return False
        
        # Check if already scheduled or in progress
        if item.status in [ResearchStatus.IN_PROGRESS, ResearchStatus.COMPLETED]:
            return False
        
        return True
    
    def start_item(self, item_id: str, agent_ids: Optional[List[str]] = None) -> bool:
        """Start working on a research item"""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        
        if item.status not in [ResearchStatus.PENDING, ResearchStatus.SCHEDULED]:
            return False
        
        item.status = ResearchStatus.IN_PROGRESS
        item.actual_start = datetime.utcnow()
        
        if agent_ids:
            item.assigned_agents.extend(agent_ids)
        
        # Update indices
        self.items_by_status[ResearchStatus.PENDING].discard(item_id)
        self.items_by_status[ResearchStatus.SCHEDULED].discard(item_id)
        self.items_by_status[ResearchStatus.IN_PROGRESS].add(item_id)
        
        # Update resource usage
        for resource in item.required_resources:
            self.resource_usage[resource] += item.estimated_effort_hours
        
        logger.info(f"Started research item: {item.title}")
        
        return True
    
    def update_progress(self, item_id: str, progress: float, notes: Optional[str] = None):
        """Update progress on a research item"""
        if item_id not in self.items:
            return
        
        item = self.items[item_id]
        item.progress_percentage = max(0.0, min(100.0, progress))
        
        if notes:
            item.notes.append(f"[{datetime.utcnow().isoformat()}] {notes}")
        
        # Auto-complete if 100%
        if item.progress_percentage >= 100.0:
            self.complete_item(item_id)
    
    def complete_item(self, item_id: str, outcomes: Optional[List[str]] = None) -> bool:
        """Mark a research item as complete"""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        
        if item.status == ResearchStatus.COMPLETED:
            return True
        
        item.status = ResearchStatus.COMPLETED
        item.progress_percentage = 100.0
        item.actual_end = datetime.utcnow()
        
        if outcomes:
            item.actual_outcomes = outcomes
        
        # Update indices
        for status in [ResearchStatus.PENDING, ResearchStatus.SCHEDULED, ResearchStatus.IN_PROGRESS]:
            self.items_by_status[status].discard(item_id)
        self.items_by_status[ResearchStatus.COMPLETED].add(item_id)
        
        # Move to completed list
        self.completed_items.append(item)
        
        # Update stats
        self.stats['items_completed'] += 1
        if item.actual_start:
            hours = (item.actual_end - item.actual_start).total_seconds() / 3600
            self.stats['total_hours_invested'] += hours
        
        # Update milestones
        self._update_milestones_for_completion(item_id)
        
        logger.info(f"Completed research item: {item.title}")
        
        return True
    
    def _update_milestones_for_completion(self, completed_item_id: str):
        """Update milestones when an item is completed"""
        for milestone in self.milestones.values():
            if completed_item_id in milestone.target_items:
                # Calculate progress
                completed = sum(
                    1 for item_id in milestone.target_items
                    if item_id in self.items and
                    self.items[item_id].status == ResearchStatus.COMPLETED
                )
                total = len(milestone.target_items)
                
                milestone.progress = completed / total if total > 0 else 0.0
                
                if milestone.progress >= 1.0:
                    milestone.status = ResearchStatus.COMPLETED
                    milestone.completed_at = datetime.utcnow()
    
    def generate_research_plan(
        self,
        horizon_days: int = 30,
        focus_areas: Optional[List[ResearchArea]] = None
    ) -> Dict:
        """Generate a comprehensive research plan"""
        # Get prioritized items
        prioritized = self.prioritize_agenda()
        
        # Filter by focus areas if specified
        if focus_areas:
            prioritized = [
                item for item in prioritized
                if item.research_area in focus_areas
            ]
        
        # Schedule items within horizon
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=horizon_days)
        
        scheduled = []
        current_date = start_date
        
        for item in prioritized:
            if current_date > end_date:
                break
            
            if self._is_schedulable(item):
                duration_days = max(1, int(item.estimated_effort_hours / 8))
                scheduled_end = current_date + timedelta(days=duration_days)
                
                scheduled.append({
                    'item_id': item.item_id,
                    'title': item.title,
                    'area': item.research_area.value,
                    'priority': item.priority.value,
                    'start': current_date.isoformat(),
                    'end': scheduled_end.isoformat(),
                    'effort_hours': item.estimated_effort_hours
                })
                
                current_date = scheduled_end + timedelta(days=1)
        
        # Calculate resource allocation
        total_hours = sum(item['effort_hours'] for item in scheduled)
        
        return {
            'plan_period': f"{start_date.date()} to {end_date.date()}",
            'items_scheduled': len(scheduled),
            'total_effort_hours': total_hours,
            'focus_areas': [a.value for a in focus_areas] if focus_areas else 'all',
            'schedule': scheduled,
            'milestones': [
                {
                    'id': m.milestone_id,
                    'title': m.title,
                    'progress': m.progress,
                    'status': m.status.value
                }
                for m in self.milestones.values()
            ]
        }
    
    def get_agenda_summary(self) -> Dict:
        """Get summary of research agenda"""
        return {
            'total_items': len(self.items),
            'by_status': {
                status.value: len(items)
                for status, items in self.items_by_status.items()
            },
            'by_area': {
                area.value: len(items)
                for area, items in self.items_by_area.items()
            },
            'overdue_items': len([
                item for item in self.items.values()
                if item.is_overdue()
            ]),
            'completion_rate': (
                self.stats['items_completed'] / max(1, self.stats['items_created'])
            ),
            'top_priorities': [
                item.to_dict() for item in self.prioritize_agenda()[:5]
            ]
        }
    
    def get_statistics(self) -> Dict:
        """Get agenda statistics"""
        return {
            **self.stats,
            'active_items': len(self.items_by_status[ResearchStatus.IN_PROGRESS]),
            'scheduled_items': len(self.items_by_status[ResearchStatus.SCHEDULED]),
            'pending_items': len(self.items_by_status[ResearchStatus.PENDING]),
            'milestones_total': len(self.milestones),
            'milestones_completed': len([
                m for m in self.milestones.values()
                if m.status == ResearchStatus.COMPLETED
            ])
        }
