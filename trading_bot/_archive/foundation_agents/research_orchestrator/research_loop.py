"""
Research Loop - Autonomous Research Orchestration
===================================================

Implements the autonomous research loop:
1. Hypothesis prioritization
2. Experiment execution
3. Result analysis
4. Knowledge integration
5. New hypothesis generation

Based on the Foundation Agents paper (arXiv:2504.01990) research systems.
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    """Phases of the research loop"""
    IDLE = "idle"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    HYPOTHESIS_PRIORITIZATION = "hypothesis_prioritization"
    EXPERIMENT_DESIGN = "experiment_design"
    EXPERIMENT_EXECUTION = "experiment_execution"
    RESULT_ANALYSIS = "result_analysis"
    KNOWLEDGE_INTEGRATION = "knowledge_integration"
    METHODOLOGY_EVOLUTION = "methodology_evolution"


class ResearchPriority(Enum):
    """Priority levels for research tasks"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    BACKGROUND = 1


@dataclass
class ResearchTask:
    """A task in the research loop"""
    task_id: str
    task_type: str
    priority: ResearchPriority
    
    # Content
    description: str
    hypothesis_id: Optional[str] = None
    experiment_id: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    progress: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ResearchCycle:
    """A complete research cycle"""
    cycle_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Phases completed
    phases_completed: List[ResearchPhase] = field(default_factory=list)
    current_phase: ResearchPhase = ResearchPhase.IDLE
    
    # Metrics
    hypotheses_generated: int = 0
    experiments_run: int = 0
    hypotheses_supported: int = 0
    hypotheses_rejected: int = 0
    knowledge_items_created: int = 0
    
    # Insights
    key_findings: List[str] = field(default_factory=list)
    
    def duration(self) -> Optional[timedelta]:
        if self.completed_at:
            return self.completed_at - self.started_at
        return datetime.utcnow() - self.started_at
    
    def to_dict(self) -> Dict:
        return {
            'cycle_id': self.cycle_id,
            'started_at': self.started_at.isoformat(),
            'current_phase': self.current_phase.value,
            'phases_completed': [p.value for p in self.phases_completed],
            'hypotheses_generated': self.hypotheses_generated,
            'experiments_run': self.experiments_run,
            'key_findings': self.key_findings
        }


class ResearchScheduler:
    """Schedules and prioritizes research tasks"""
    
    def __init__(self):
        self.task_queue: List[ResearchTask] = []
        self.running_tasks: Dict[str, ResearchTask] = {}
        self.completed_tasks: deque = deque(maxlen=1000)
        self.max_concurrent = 3
    
    def add_task(self, task: ResearchTask):
        """Add a task to the queue"""
        self.task_queue.append(task)
        self._sort_queue()
    
    def _sort_queue(self):
        """Sort queue by priority and dependencies"""
        # First by priority (descending), then by creation time
        self.task_queue.sort(
            key=lambda t: (-t.priority.value, t.created_at)
        )
    
    def get_next_task(self) -> Optional[ResearchTask]:
        """Get next task to execute"""
        if len(self.running_tasks) >= self.max_concurrent:
            return None
        
        for task in self.task_queue:
            # Check dependencies
            deps_met = all(
                dep in [t.task_id for t in self.completed_tasks]
                for dep in task.depends_on
            )
            
            if deps_met and task.status == "pending":
                return task
        
        return None
    
    def start_task(self, task_id: str):
        """Mark task as started"""
        for task in self.task_queue:
            if task.task_id == task_id:
                task.status = "running"
                task.started_at = datetime.utcnow()
                self.running_tasks[task_id] = task
                self.task_queue.remove(task)
                break
    
    def complete_task(self, task_id: str, results: Dict, success: bool = True):
        """Mark task as completed"""
        if task_id in self.running_tasks:
            task = self.running_tasks.pop(task_id)
            task.status = "completed" if success else "failed"
            task.completed_at = datetime.utcnow()
            task.results = results
            task.progress = 1.0
            self.completed_tasks.append(task)
    
    def get_queue_status(self) -> Dict:
        return {
            'pending': len(self.task_queue),
            'running': len(self.running_tasks),
            'completed': len(self.completed_tasks)
        }


class ResultAnalyzer:
    """Analyzes experiment results"""
    
    def analyze(
        self,
        experiment_results: Dict,
        hypothesis_statement: str,
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """Analyze experiment results"""
        analysis = {
            'hypothesis': hypothesis_statement,
            'conclusion': 'inconclusive',
            'confidence': 0.5,
            'effect_size': 0.0,
            'p_value': None,
            'insights': [],
            'recommendations': []
        }
        
        # Extract metrics
        p_value = experiment_results.get('p_value')
        effect_size = experiment_results.get('effect_size', 0.0)
        primary_metric = experiment_results.get('primary_metric_value')
        
        if p_value is not None:
            analysis['p_value'] = p_value
            
            if p_value < significance_level:
                if effect_size > 0:
                    analysis['conclusion'] = 'supported'
                    analysis['confidence'] = 1 - p_value
                    analysis['insights'].append(
                        f"Hypothesis supported with p={p_value:.4f}"
                    )
                else:
                    analysis['conclusion'] = 'rejected'
                    analysis['confidence'] = 1 - p_value
                    analysis['insights'].append(
                        f"Effect in opposite direction, p={p_value:.4f}"
                    )
            else:
                analysis['conclusion'] = 'inconclusive'
                analysis['confidence'] = 0.5
                analysis['insights'].append(
                    f"Insufficient evidence, p={p_value:.4f}"
                )
        
        analysis['effect_size'] = effect_size
        
        # Generate recommendations
        if analysis['conclusion'] == 'supported':
            analysis['recommendations'].append(
                "Consider implementing findings in trading strategy"
            )
            analysis['recommendations'].append(
                "Design follow-up experiments to validate robustness"
            )
        elif analysis['conclusion'] == 'rejected':
            analysis['recommendations'].append(
                "Investigate why hypothesis was rejected"
            )
            analysis['recommendations'].append(
                "Consider alternative hypotheses"
            )
        else:
            analysis['recommendations'].append(
                "Collect more data or increase sample size"
            )
            analysis['recommendations'].append(
                "Review experimental design for improvements"
            )
        
        return analysis


class ResearchLoop:
    """
    Research Loop
    
    Orchestrates the autonomous research process:
    - Generates and prioritizes hypotheses
    - Designs and runs experiments
    - Analyzes results
    - Integrates knowledge
    - Evolves methodologies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.scheduler = ResearchScheduler()
        self.analyzer = ResultAnalyzer()
        
        # State
        self.current_cycle: Optional[ResearchCycle] = None
        self.cycle_history: List[ResearchCycle] = []
        self.current_phase = ResearchPhase.IDLE
        
        # Callbacks for integration with other modules
        self.callbacks: Dict[str, Callable] = {}
        
        # Configuration
        self.auto_evolve = self.config.get('auto_evolve', True)
        self.max_hypotheses_per_cycle = self.config.get('max_hypotheses', 5)
        self.min_experiments_before_evolve = self.config.get('min_experiments', 10)
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'total_hypotheses': 0,
            'total_experiments': 0,
            'supported_hypotheses': 0,
            'rejected_hypotheses': 0,
            'inconclusive': 0
        }
        
        # Running state
        self.is_running = False
        self.pause_requested = False
        
        logger.info("Research Loop initialized")
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for research events"""
        self.callbacks[event] = callback
    
    def _trigger_callback(self, event: str, data: Any = None):
        """Trigger a registered callback"""
        if event in self.callbacks:
            try:
                self.callbacks[event](data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
    
    def start_cycle(self) -> ResearchCycle:
        """Start a new research cycle"""
        cycle = ResearchCycle(
            cycle_id=f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        self.current_cycle = cycle
        self.current_phase = ResearchPhase.HYPOTHESIS_GENERATION
        cycle.current_phase = self.current_phase
        
        logger.info(f"Started research cycle: {cycle.cycle_id}")
        self._trigger_callback('cycle_started', cycle)
        
        return cycle
    
    def complete_cycle(self):
        """Complete the current research cycle"""
        if self.current_cycle:
            self.current_cycle.completed_at = datetime.utcnow()
            self.cycle_history.append(self.current_cycle)
            self.stats['cycles_completed'] += 1
            
            logger.info(f"Completed research cycle: {self.current_cycle.cycle_id}")
            self._trigger_callback('cycle_completed', self.current_cycle)
            
            self.current_cycle = None
            self.current_phase = ResearchPhase.IDLE
    
    def advance_phase(self):
        """Advance to next phase"""
        phase_order = [
            ResearchPhase.HYPOTHESIS_GENERATION,
            ResearchPhase.HYPOTHESIS_PRIORITIZATION,
            ResearchPhase.EXPERIMENT_DESIGN,
            ResearchPhase.EXPERIMENT_EXECUTION,
            ResearchPhase.RESULT_ANALYSIS,
            ResearchPhase.KNOWLEDGE_INTEGRATION,
            ResearchPhase.METHODOLOGY_EVOLUTION
        ]
        
        if self.current_phase in phase_order:
            idx = phase_order.index(self.current_phase)
            if idx < len(phase_order) - 1:
                self.current_phase = phase_order[idx + 1]
            else:
                # Cycle complete
                self.complete_cycle()
                return
        
        if self.current_cycle:
            self.current_cycle.phases_completed.append(self.current_phase)
            self.current_cycle.current_phase = self.current_phase
        
        logger.info(f"Advanced to phase: {self.current_phase.value}")
        self._trigger_callback('phase_changed', self.current_phase)
    
    def add_hypothesis_task(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        priority: ResearchPriority = ResearchPriority.MEDIUM
    ):
        """Add a hypothesis testing task"""
        task = ResearchTask(
            task_id=f"hyp_{hypothesis_id}",
            task_type="hypothesis_test",
            priority=priority,
            description=f"Test hypothesis: {hypothesis_statement[:100]}",
            hypothesis_id=hypothesis_id
        )
        
        self.scheduler.add_task(task)
        self.stats['total_hypotheses'] += 1
        
        if self.current_cycle:
            self.current_cycle.hypotheses_generated += 1
    
    def add_experiment_task(
        self,
        experiment_id: str,
        experiment_name: str,
        hypothesis_id: str,
        priority: ResearchPriority = ResearchPriority.MEDIUM
    ):
        """Add an experiment execution task"""
        task = ResearchTask(
            task_id=f"exp_{experiment_id}",
            task_type="experiment",
            priority=priority,
            description=f"Run experiment: {experiment_name}",
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            depends_on=[f"hyp_{hypothesis_id}"]
        )
        
        self.scheduler.add_task(task)
        self.stats['total_experiments'] += 1
    
    def process_experiment_result(
        self,
        experiment_id: str,
        hypothesis_id: str,
        results: Dict
    ) -> Dict[str, Any]:
        """Process experiment results"""
        # Analyze results
        hypothesis_statement = results.get('hypothesis_statement', '')
        analysis = self.analyzer.analyze(
            experiment_results=results,
            hypothesis_statement=hypothesis_statement
        )
        
        # Update statistics
        if analysis['conclusion'] == 'supported':
            self.stats['supported_hypotheses'] += 1
            if self.current_cycle:
                self.current_cycle.hypotheses_supported += 1
        elif analysis['conclusion'] == 'rejected':
            self.stats['rejected_hypotheses'] += 1
            if self.current_cycle:
                self.current_cycle.hypotheses_rejected += 1
        else:
            self.stats['inconclusive'] += 1
        
        if self.current_cycle:
            self.current_cycle.experiments_run += 1
            if analysis['insights']:
                self.current_cycle.key_findings.extend(analysis['insights'])
        
        # Complete task
        self.scheduler.complete_task(
            f"exp_{experiment_id}",
            results={'analysis': analysis},
            success=True
        )
        
        # Trigger callbacks
        self._trigger_callback('experiment_completed', {
            'experiment_id': experiment_id,
            'hypothesis_id': hypothesis_id,
            'analysis': analysis
        })
        
        return analysis
    
    async def run_cycle_async(self):
        """Run a complete research cycle asynchronously"""
        self.is_running = True
        self.pause_requested = False
        
        try:
            # Start cycle
            self.start_cycle()
            
            # Phase 1: Hypothesis Generation
            self.current_phase = ResearchPhase.HYPOTHESIS_GENERATION
            self._trigger_callback('generate_hypotheses', {
                'max_count': self.max_hypotheses_per_cycle
            })
            await asyncio.sleep(0.1)  # Allow callbacks to process
            
            # Phase 2: Prioritization
            self.advance_phase()
            self._trigger_callback('prioritize_hypotheses', None)
            await asyncio.sleep(0.1)
            
            # Phase 3: Experiment Design
            self.advance_phase()
            self._trigger_callback('design_experiments', None)
            await asyncio.sleep(0.1)
            
            # Phase 4: Experiment Execution
            self.advance_phase()
            while self.scheduler.task_queue or self.scheduler.running_tasks:
                if self.pause_requested:
                    break
                
                task = self.scheduler.get_next_task()
                if task:
                    self.scheduler.start_task(task.task_id)
                    self._trigger_callback('execute_task', task)
                
                await asyncio.sleep(0.1)
            
            # Phase 5: Result Analysis
            self.advance_phase()
            self._trigger_callback('analyze_results', None)
            await asyncio.sleep(0.1)
            
            # Phase 6: Knowledge Integration
            self.advance_phase()
            self._trigger_callback('integrate_knowledge', {
                'cycle': self.current_cycle
            })
            await asyncio.sleep(0.1)
            
            # Phase 7: Methodology Evolution
            if self.auto_evolve and self.stats['total_experiments'] >= self.min_experiments_before_evolve:
                self.advance_phase()
                self._trigger_callback('evolve_methodology', None)
                await asyncio.sleep(0.1)
            
            # Complete cycle
            self.complete_cycle()
            
        except Exception as e:
            logger.error(f"Research cycle error: {e}")
            if self.current_cycle:
                self.current_cycle.key_findings.append(f"Error: {str(e)}")
        
        finally:
            self.is_running = False
    
    def run_cycle_sync(self):
        """Run a complete research cycle synchronously"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_cycle_async())
        finally:
            loop.close()
    
    def pause(self):
        """Pause the research loop"""
        self.pause_requested = True
        logger.info("Research loop pause requested")
    
    def resume(self):
        """Resume the research loop"""
        self.pause_requested = False
        logger.info("Research loop resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the research loop"""
        return {
            'is_running': self.is_running,
            'current_phase': self.current_phase.value,
            'current_cycle': self.current_cycle.to_dict() if self.current_cycle else None,
            'queue_status': self.scheduler.get_queue_status(),
            'stats': self.stats
        }
    
    def get_cycle_summary(self, cycle_id: Optional[str] = None) -> Optional[Dict]:
        """Get summary of a research cycle"""
        if cycle_id:
            for cycle in self.cycle_history:
                if cycle.cycle_id == cycle_id:
                    return cycle.to_dict()
            return None
        elif self.current_cycle:
            return self.current_cycle.to_dict()
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get research loop statistics"""
        success_rate = 0.0
        total = self.stats['supported_hypotheses'] + self.stats['rejected_hypotheses'] + self.stats['inconclusive']
        if total > 0:
            success_rate = self.stats['supported_hypotheses'] / total
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'cycles_in_history': len(self.cycle_history),
            'avg_experiments_per_cycle': (
                self.stats['total_experiments'] / max(1, self.stats['cycles_completed'])
            ),
            'avg_hypotheses_per_cycle': (
                self.stats['total_hypotheses'] / max(1, self.stats['cycles_completed'])
            )
        }
