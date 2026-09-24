"""
Autonomous Research Framework

High-level framework for conducting autonomous trading strategy research.
Coordinates multiple research threads and manages the research lifecycle.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .aletheia_orchestrator import AletheiaOrchestrator, StrategyHypothesis, AutonomyLevel

logger = logging.getLogger(__name__)


class ResearchPriority(Enum):
    """Priority levels for research tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    EXPLORATORY = "exploratory"


@dataclass
class ResearchProject:
    """Represents an autonomous research project"""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    research_prompts: List[str] = field(default_factory=list)
    priority: ResearchPriority = ResearchPriority.MEDIUM
    autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_C
    market_context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    hypotheses: List[StrategyHypothesis] = field(default_factory=list)
    best_hypothesis: Optional[StrategyHypothesis] = None
    
    # Metadata
    target_hypothesis_count: int = 5
    min_confidence_threshold: float = 0.85
    notes: List[str] = field(default_factory=list)


class AutonomousResearchFramework:
    """
    High-level framework for autonomous trading strategy research.
    
    Manages multiple research projects, coordinates research threads,
    and provides interfaces for human-AI collaboration.
    """
    
    def __init__(
        self,
        orchestrator: Optional[AletheiaOrchestrator] = None,
        max_concurrent_projects: int = 3,
        auto_approve_level_a: bool = False
    ):
        self.orchestrator = orchestrator
        self.max_concurrent_projects = max_concurrent_projects
        self.auto_approve_level_a = auto_approve_level_a
        
        self.projects: Dict[str, ResearchProject] = {}
        self.project_queue: List[str] = []
        self.active_projects: List[str] = []
        self.completed_projects: List[str] = []
        
        self.research_callbacks: List[Callable] = []
        self.approval_callbacks: List[Callable] = []
        
        logger.info("AutonomousResearchFramework initialized")
    
    async def create_research_project(
        self,
        title: str,
        description: str,
        research_prompts: List[str],
        priority: ResearchPriority = ResearchPriority.MEDIUM,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_C,
        market_context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        target_hypothesis_count: int = 5
    ) -> ResearchProject:
        """
        Create a new research project
        
        Args:
            title: Project title
            description: Project description
            research_prompts: List of strategy research prompts
            priority: Research priority level
            autonomy_level: Level of autonomy (A, C, or H)
            market_context: Current market conditions
            constraints: Risk and operational constraints
            target_hypothesis_count: Number of strategies to generate
            
        Returns:
            Created ResearchProject
        """
        project = ResearchProject(
            title=title,
            description=description,
            research_prompts=research_prompts,
            priority=priority,
            autonomy_level=autonomy_level,
            market_context=market_context or {},
            constraints=constraints or {},
            target_hypothesis_count=target_hypothesis_count
        )
        
        self.projects[project.project_id] = project
        self.project_queue.append(project.project_id)
        
        # Sort queue by priority
        priority_order = {
            ResearchPriority.CRITICAL: 0,
            ResearchPriority.HIGH: 1,
            ResearchPriority.MEDIUM: 2,
            ResearchPriority.LOW: 3,
            ResearchPriority.EXPLORATORY: 4
        }
        self.project_queue.sort(
            key=lambda pid: priority_order.get(self.projects[pid].priority, 2)
        )
        
        logger.info(f"Created research project: {title} (ID: {project.project_id})")
        return project
    
    async def start_research(self, project_id: Optional[str] = None) -> Optional[ResearchProject]:
        """
        Start research on a project
        
        Args:
            project_id: Specific project to start, or None for next in queue
            
        Returns:
            Started ResearchProject or None if no projects available
        """
        # Check if we can start more projects
        if len(self.active_projects) >= self.max_concurrent_projects:
            logger.warning("Max concurrent projects reached")
            return None
        
        # Get project to start
        if project_id:
            if project_id not in self.projects:
                logger.error(f"Project {project_id} not found")
                return None
            pid = project_id
        elif self.project_queue:
            pid = self.project_queue.pop(0)
        else:
            logger.info("No projects in queue")
            return None
        
        project = self.projects[pid]
        project.status = "in_progress"
        project.started_at = datetime.now()
        self.active_projects.append(pid)
        
        logger.info(f"Starting research project: {project.title}")
        
        # Start research in background
        asyncio.create_task(self._conduct_research(project))
        
        return project
    
    async def _conduct_research(self, project: ResearchProject):
        """Conduct research for a project"""
        try:
            logger.info(f"Conducting research for project: {project.title}")
            
            # Research each prompt
            for i, prompt in enumerate(project.research_prompts):
                logger.info(f"Researching prompt {i+1}/{len(project.research_prompts)}: {prompt[:80]}...")
                
                # Conduct research through orchestrator
                if self.orchestrator:
                    hypothesis = await self.orchestrator.research_strategy(
                        research_prompt=prompt,
                        market_context=project.market_context,
                        constraints=project.constraints
                    )
                    
                    project.hypotheses.append(hypothesis)
                    
                    # Track best hypothesis
                    if (project.best_hypothesis is None or 
                        hypothesis.confidence_score > project.best_hypothesis.confidence_score):
                        project.best_hypothesis = hypothesis
                
                # Check if we have enough high-confidence hypotheses
                verified_count = sum(1 for h in project.hypotheses if h.verification_status == "verified")
                if verified_count >= project.target_hypothesis_count:
                    project.notes.append(f"Reached target of {verified_count} verified hypotheses")
                    break
            
            # Mark as completed
            project.status = "completed"
            project.completed_at = datetime.now()
            
            # Move from active to completed
            if project.project_id in self.active_projects:
                self.active_projects.remove(project.project_id)
            self.completed_projects.append(project.project_id)
            
            # Trigger callbacks
            for callback in self.research_callbacks:
                try:
                    await callback(project)
                except Exception as e:
                    logger.error(f"Research callback error: {e}")
            
            logger.info(f"Research project completed: {project.title}")
            
        except Exception as e:
            logger.error(f"Research failed for project {project.project_id}: {e}")
            project.status = "failed"
            project.notes.append(f"Error: {str(e)}")
            
            if project.project_id in self.active_projects:
                self.active_projects.remove(project.project_id)
    
    async def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research project"""
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        
        return {
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "priority": project.priority.value,
            "autonomy_level": project.autonomy_level.value,
            "hypotheses_count": len(project.hypotheses),
            "verified_count": sum(1 for h in project.hypotheses if h.verification_status == "verified"),
            "best_confidence": project.best_hypothesis.confidence_score if project.best_hypothesis else 0,
            "created_at": project.created_at.isoformat(),
            "started_at": project.started_at.isoformat() if project.started_at else None,
            "completed_at": project.completed_at.isoformat() if project.completed_at else None,
            "notes": project.notes
        }
    
    def get_all_projects_summary(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get summary of all projects"""
        return {
            "queued": [self._project_to_summary(pid) for pid in self.project_queue],
            "active": [self._project_to_summary(pid) for pid in self.active_projects],
            "completed": [self._project_to_summary(pid) for pid in self.completed_projects]
        }
    
    def _project_to_summary(self, project_id: str) -> Dict[str, Any]:
        """Convert project to summary dict"""
        project = self.projects[project_id]
        return {
            "project_id": project_id,
            "title": project.title,
            "status": project.status,
            "priority": project.priority.value,
            "autonomy_level": project.autonomy_level.value,
            "hypotheses_count": len(project.hypotheses),
            "best_confidence": project.best_hypothesis.confidence_score if project.best_hypothesis else 0
        }
    
    async def approve_strategy_for_deployment(
        self,
        project_id: str,
        hypothesis_id: Optional[str] = None,
        approver_name: str = "Human"
    ) -> Dict[str, Any]:
        """
        Approve a strategy for deployment (human approval for Level C)
        
        Args:
            project_id: Research project ID
            hypothesis_id: Specific hypothesis to approve (or best if None)
            approver_name: Name of approving person
            
        Returns:
            Approval result
        """
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        project = self.projects[project_id]
        
        # Get hypothesis to approve
        if hypothesis_id:
            hypothesis = next(
                (h for h in project.hypotheses if h.hypothesis_id == hypothesis_id),
                None
            )
        else:
            hypothesis = project.best_hypothesis
        
        if not hypothesis:
            return {"error": "Hypothesis not found"}
        
        # Check if auto-approval is allowed
        if project.autonomy_level == AutonomyLevel.LEVEL_A and self.auto_approve_level_a:
            approval_type = "auto_approved"
        else:
            approval_type = "human_approved"
        
        result = {
            "project_id": project_id,
            "hypothesis_id": hypothesis.hypothesis_id,
            "strategy_title": hypothesis.title,
            "approval_type": approval_type,
            "approved_by": approver_name if approval_type == "human_approved" else "Aletheia Auto-Approval",
            "approved_at": datetime.now().isoformat(),
            "confidence_score": hypothesis.confidence_score,
            "verification_status": hypothesis.verification_status,
            "ready_for_deployment": hypothesis.verification_status == "verified"
        }
        
        # Trigger callbacks
        for callback in self.approval_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Approval callback error: {e}")
        
        logger.info(f"Strategy approved for deployment: {hypothesis.title}")
        return result
    
    def on_research_complete(self, callback: Callable):
        """Register callback for when research completes"""
        self.research_callbacks.append(callback)
    
    def on_strategy_approved(self, callback: Callable):
        """Register callback for when strategy is approved"""
        self.approval_callbacks.append(callback)
    
    def get_research_statistics(self) -> Dict[str, Any]:
        """Get overall research statistics"""
        all_hypotheses = []
        for project in self.projects.values():
            all_hypotheses.extend(project.hypotheses)
        
        if not all_hypotheses:
            return {"total_hypotheses": 0}
        
        verified = sum(1 for h in all_hypotheses if h.verification_status == "verified")
        partial = sum(1 for h in all_hypotheses if h.verification_status == "partial")
        
        return {
            "total_projects": len(self.projects),
            "queued_projects": len(self.project_queue),
            "active_projects": len(self.active_projects),
            "completed_projects": len(self.completed_projects),
            "total_hypotheses": len(all_hypotheses),
            "verified_hypotheses": verified,
            "partial_hypotheses": partial,
            "verification_rate": verified / len(all_hypotheses),
            "average_confidence": sum(h.confidence_score for h in all_hypotheses) / len(all_hypotheses),
            "average_revisions": sum(h.revision_count for h in all_hypotheses) / len(all_hypotheses)
        }
    
    async def export_research_report(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive research report"""
        if project_id:
            if project_id not in self.projects:
                return {"error": "Project not found"}
            
            project = self.projects[project_id]
            return {
                "project": {
                    "id": project.project_id,
                    "title": project.title,
                    "description": project.description,
                    "status": project.status,
                    "priority": project.priority.value,
                    "autonomy_level": project.autonomy_level.value
                },
                "hypotheses": [
                    {
                        "id": h.hypothesis_id,
                        "title": h.title,
                        "description": h.description,
                        "rationale": h.rationale,
                        "confidence": h.confidence_score,
                        "verification_status": h.verification_status,
                        "revision_count": h.revision_count,
                        "entry_rules": h.entry_rules,
                        "exit_rules": h.exit_rules,
                        "risk_parameters": h.risk_parameters,
                        "expected_performance": h.expected_performance
                    }
                    for h in project.hypotheses
                ],
                "best_strategy": {
                    "id": project.best_hypothesis.hypothesis_id,
                    "title": project.best_hypothesis.title,
                    "confidence": project.best_hypothesis.confidence_score
                } if project.best_hypothesis else None
            }
        
        # Export all projects
        return {
            "projects": [
                await self.export_research_report(pid)
                for pid in self.projects.keys()
            ],
            "statistics": self.get_research_statistics()
        }
