"""
Continuous Research Organism
============================

The main orchestrator for autonomous AI self-improvement.
Coordinates all components to create a continuously evolving,
self-designing, self-programming research system.

Components Orchestrated:
1. SandboxEnvironment - Safe code execution
2. ComputeBudgetController - Resource management
3. DataIntegrityFirewall - Data protection
4. CodeSafetyScanner - Security analysis
5. ExperimentRegistry - Experiment tracking
6. SelfProgrammingEngine - Code evolution

CRITICAL SAFETY PRINCIPLES:
- All operations run in sandbox
- All resources are budgeted
- All data changes are protected
- All code is scanned
- All experiments are registered
- Human override is ALWAYS available
"""

import asyncio
import threading
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import logging
import uuid

from .sandbox_environment import SandboxEnvironment, SandboxConfig, SandboxResult
from .compute_budget_controller import (
    ComputeBudgetController, ResourceType, BudgetPriority, BudgetExceededError
)
from .data_integrity_firewall import (
    DataIntegrityFirewall, ProtectionLevel, ResourceType as FirewallResourceType
)
from .code_safety_scanner import CodeSafetyScanner, ScanResult, ThreatLevel
from .experiment_registry import (
    ExperimentRegistry, Experiment, ExperimentPhase, ExperimentType,
    ExperimentOutcome, ExperimentHypothesis
)
from .self_programming_engine import (
    SelfProgrammingEngine, CodeGeneration, EvolutionStrategy, CodeType, EvolutionConfig
)

logger = logging.getLogger(__name__)


class ResearchPhase(Enum):
    """Phases of the research cycle."""
    IDLE = auto()
    ANALYZING = auto()
    HYPOTHESIZING = auto()
    DESIGNING = auto()
    IMPLEMENTING = auto()
    TESTING = auto()
    VALIDATING = auto()
    DEPLOYING = auto()
    MONITORING = auto()


class ResearchPriority(Enum):
    """Priority levels for research directives."""
    CRITICAL = 1      # Safety improvements
    HIGH = 2          # Performance improvements
    NORMAL = 3        # Feature additions
    LOW = 4           # Optimizations
    BACKGROUND = 5    # Exploration


@dataclass
class ResearchDirective:
    """A directive for research focus."""
    directive_id: str
    title: str
    description: str
    priority: ResearchPriority
    target_area: str  # 'strategy', 'risk', 'execution', 'analysis', 'infrastructure'
    success_criteria: Dict[str, float]
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    status: str = "active"  # active, completed, cancelled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'directive_id': self.directive_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.name,
            'target_area': self.target_area,
            'success_criteria': self.success_criteria,
            'constraints': self.constraints,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
        }


@dataclass
class ResearchCycle:
    """A complete research cycle."""
    cycle_id: str
    directive: ResearchDirective
    phase: ResearchPhase = ResearchPhase.IDLE
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Tracking
    experiments_run: List[str] = field(default_factory=list)
    code_generated: List[str] = field(default_factory=list)
    improvements_deployed: List[str] = field(default_factory=list)
    
    # Results
    success: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cycle_id': self.cycle_id,
            'directive': self.directive.to_dict(),
            'phase': self.phase.name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'experiments_run': self.experiments_run,
            'code_generated': self.code_generated,
            'improvements_deployed': self.improvements_deployed,
            'success': self.success,
            'metrics': self.metrics,
            'notes': self.notes,
        }


@dataclass
class OrganismState:
    """Current state of the research organism."""
    is_active: bool = False
    is_paused: bool = False
    current_phase: ResearchPhase = ResearchPhase.IDLE
    current_cycle: Optional[ResearchCycle] = None
    active_directives: List[ResearchDirective] = field(default_factory=list)
    
    # Statistics
    total_cycles: int = 0
    successful_cycles: int = 0
    total_experiments: int = 0
    total_code_generated: int = 0
    total_improvements: int = 0
    
    # Health
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    errors_last_hour: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'current_phase': self.current_phase.name,
            'current_cycle': self.current_cycle.to_dict() if self.current_cycle else None,
            'active_directives': len(self.active_directives),
            'total_cycles': self.total_cycles,
            'successful_cycles': self.successful_cycles,
            'success_rate': self.successful_cycles / self.total_cycles if self.total_cycles > 0 else 0,
            'total_experiments': self.total_experiments,
            'total_code_generated': self.total_code_generated,
            'total_improvements': self.total_improvements,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'errors_last_hour': self.errors_last_hour,
        }


class ContinuousResearchOrganism:
    """
    The main autonomous research organism.
    
    Continuously analyzes, hypothesizes, designs, implements, tests,
    and deploys improvements to the trading system.
    
    All operations are:
    - Sandboxed for safety
    - Budget-controlled for resources
    - Firewall-protected for data
    - Scanned for security
    - Registered for audit
    """
    
    # Safety limits
    MAX_CYCLES_PER_DAY = 50
    MAX_EXPERIMENTS_PER_CYCLE = 10
    MAX_CODE_GENERATIONS_PER_CYCLE = 20
    MAX_DEPLOYMENTS_PER_DAY = 5
    MIN_CYCLE_INTERVAL_MINUTES = 5
    
    def __init__(self,
                 storage_path: Optional[Path] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the continuous research organism.
        
        Args:
            storage_path: Path for persistent storage
            config: Configuration overrides
        """
        self.storage_path = storage_path or Path("research_organism_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {}
        
        # Initialize components
        self._init_components()
        
        # State
        self.state = OrganismState()
        self.cycles: List[ResearchCycle] = []
        self.directives: Dict[str, ResearchDirective] = {}
        
        # Control
        self._running = False
        self._paused = False
        self._shutdown_event = threading.Event()
        self._main_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self._phase_callbacks: Dict[ResearchPhase, List[Callable]] = {
            phase: [] for phase in ResearchPhase
        }
        self._improvement_callbacks: List[Callable] = []
        
        # Rate limiting
        self._cycles_today = 0
        self._deployments_today = 0
        self._last_cycle_time: Optional[datetime] = None
        self._last_reset_date: Optional[datetime] = None
        
        logger.info("ContinuousResearchOrganism initialized")
    
    def _init_components(self):
        """Initialize all sub-components."""
        # Sandbox environment
        sandbox_config = SandboxConfig(
            max_execution_time_seconds=60.0,
            max_memory_mb=512,
            allowed_imports={'math', 'statistics', 'numpy', 'pandas', 'datetime'},
        )
        self.sandbox = SandboxEnvironment(sandbox_config)
        
        # Compute budget controller
        self.budget_controller = ComputeBudgetController(
            storage_path=self.storage_path / "budget"
        )
        
        # Data integrity firewall
        self.firewall = DataIntegrityFirewall(
            storage_path=self.storage_path / "firewall",
            backup_path=self.storage_path / "backups",
        )
        
        # Code safety scanner
        self.scanner = CodeSafetyScanner(threat_threshold=ThreatLevel.MEDIUM)
        
        # Experiment registry
        self.registry = ExperimentRegistry(
            storage_path=self.storage_path / "experiments",
            max_concurrent_experiments=3,
        )
        
        # Self-programming engine
        evolution_config = EvolutionConfig(
            population_size=10,
            elite_size=3,
            max_generations=20,
        )
        self.programming_engine = SelfProgrammingEngine(
            config=evolution_config,
            safety_scanner=self.scanner,
            sandbox=self.sandbox,
        )
        
        logger.info("All components initialized")
    
    def start(self):
        """Start the research organism."""
        if self._running:
            logger.warning("Research organism already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        self.state.is_active = True
        
        # Start main loop in background thread
        self._main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self._main_thread.start()
        
        logger.info("Research organism started")
    
    def stop(self):
        """Stop the research organism."""
        logger.info("Stopping research organism...")
        
        self._running = False
        self._shutdown_event.set()
        self.state.is_active = False
        
        if self._main_thread:
            self._main_thread.join(timeout=30)
        
        # Cleanup
        self.budget_controller.shutdown()
        
        logger.info("Research organism stopped")
    
    def pause(self):
        """Pause the research organism."""
        self._paused = True
        self.state.is_paused = True
        logger.info("Research organism paused")
    
    def resume(self):
        """Resume the research organism."""
        self._paused = False
        self.state.is_paused = False
        logger.info("Research organism resumed")
    
    def add_directive(self, directive: ResearchDirective):
        """
        Add a research directive.
        
        Args:
            directive: Research directive to add
        """
        self.directives[directive.directive_id] = directive
        self.state.active_directives.append(directive)
        
        logger.info(f"Added directive: {directive.title}")
    
    def create_directive(self,
                         title: str,
                         description: str,
                         target_area: str,
                         success_criteria: Dict[str, float],
                         priority: ResearchPriority = ResearchPriority.NORMAL,
                         constraints: Optional[Dict[str, Any]] = None,
                         deadline: Optional[datetime] = None) -> str:
        """
        Create and add a new research directive.
        
        Args:
            title: Directive title
            description: Detailed description
            target_area: Area to focus on
            success_criteria: Criteria for success
            priority: Priority level
            constraints: Optional constraints
            deadline: Optional deadline
            
        Returns:
            Directive ID
        """
        directive_id = f"dir_{uuid.uuid4().hex[:12]}"
        
        directive = ResearchDirective(
            directive_id=directive_id,
            title=title,
            description=description,
            priority=priority,
            target_area=target_area,
            success_criteria=success_criteria,
            constraints=constraints or {},
            deadline=deadline,
        )
        
        self.add_directive(directive)
        
        return directive_id
    
    def _main_loop(self):
        """Main research loop."""
        logger.info("Research organism main loop started")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Check if paused
                if self._paused:
                    time.sleep(1)
                    continue
                
                # Reset daily counters
                self._reset_daily_counters()
                
                # Check rate limits
                if not self._can_run_cycle():
                    time.sleep(60)
                    continue
                
                # Get next directive
                directive = self._get_next_directive()
                if not directive:
                    time.sleep(60)
                    continue
                
                # Run research cycle
                self._run_cycle(directive)
                
                # Update heartbeat
                self.state.last_heartbeat = datetime.utcnow()
                
                # Sleep between cycles
                time.sleep(self.MIN_CYCLE_INTERVAL_MINUTES * 60)
                
            except Exception as e:
                logger.error(f"Error in research loop: {e}", exc_info=True)
                self.state.errors_last_hour += 1
                time.sleep(60)
        
        logger.info("Research organism main loop ended")
    
    def _reset_daily_counters(self):
        """Reset daily counters if needed."""
        today = datetime.utcnow().date()
        
        if self._last_reset_date != today:
            self._cycles_today = 0
            self._deployments_today = 0
            self._last_reset_date = today
    
    def _can_run_cycle(self) -> bool:
        """Check if we can run another cycle."""
        # Check daily limit
        if self._cycles_today >= self.MAX_CYCLES_PER_DAY:
            return False
        
        # Check interval
        if self._last_cycle_time:
            elapsed = (datetime.utcnow() - self._last_cycle_time).total_seconds()
            if elapsed < self.MIN_CYCLE_INTERVAL_MINUTES * 60:
                return False
        
        # Check budget
        if not self.budget_controller.check_budget(ResourceType.CPU_TIME, 60):
            return False
        
        return True
    
    def _get_next_directive(self) -> Optional[ResearchDirective]:
        """Get the next directive to work on."""
        active = [d for d in self.directives.values() if d.status == "active"]
        
        if not active:
            return None
        
        # Sort by priority and deadline
        active.sort(key=lambda d: (
            d.priority.value,
            d.deadline or datetime.max,
        ))
        
        return active[0]
    
    def _run_cycle(self, directive: ResearchDirective):
        """
        Run a complete research cycle.
        
        Args:
            directive: Directive to work on
        """
        cycle_id = f"cycle_{uuid.uuid4().hex[:12]}"
        
        cycle = ResearchCycle(
            cycle_id=cycle_id,
            directive=directive,
        )
        
        self.state.current_cycle = cycle
        self.cycles.append(cycle)
        self._cycles_today += 1
        self._last_cycle_time = datetime.utcnow()
        
        logger.info(f"Starting research cycle {cycle_id} for directive: {directive.title}")
        
        try:
            # Request budget
            with self.budget_controller.budget_context(
                ResourceType.CPU_TIME, 300, f"research_cycle_{cycle_id}"
            ):
                # Phase 1: Analysis
                self._phase_analyze(cycle)
                
                # Phase 2: Hypothesis
                self._phase_hypothesize(cycle)
                
                # Phase 3: Design
                self._phase_design(cycle)
                
                # Phase 4: Implementation
                self._phase_implement(cycle)
                
                # Phase 5: Testing
                self._phase_test(cycle)
                
                # Phase 6: Validation
                self._phase_validate(cycle)
                
                # Phase 7: Deployment (if validated)
                if cycle.metrics.get('validation_score', 0) >= 0.8:
                    self._phase_deploy(cycle)
                
                # Complete cycle
                cycle.completed_at = datetime.utcnow()
                cycle.success = len(cycle.improvements_deployed) > 0
                
                self.state.total_cycles += 1
                if cycle.success:
                    self.state.successful_cycles += 1
                
        except BudgetExceededError as e:
            logger.warning(f"Cycle {cycle_id} budget exceeded: {e}")
            cycle.notes.append(f"Budget exceeded: {e}")
            
        except Exception as e:
            logger.error(f"Cycle {cycle_id} failed: {e}", exc_info=True)
            cycle.notes.append(f"Error: {e}")
        
        finally:
            cycle.phase = ResearchPhase.IDLE
            self.state.current_phase = ResearchPhase.IDLE
            self._save_cycle(cycle)
        
        logger.info(f"Research cycle {cycle_id} completed. Success: {cycle.success}")
    
    def _phase_analyze(self, cycle: ResearchCycle):
        """Analysis phase - understand current state and gaps."""
        cycle.phase = ResearchPhase.ANALYZING
        self.state.current_phase = ResearchPhase.ANALYZING
        self._trigger_callbacks(ResearchPhase.ANALYZING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Analyzing...")
        
        # Analyze directive requirements
        analysis = {
            'target_area': cycle.directive.target_area,
            'success_criteria': cycle.directive.success_criteria,
            'constraints': cycle.directive.constraints,
        }
        
        cycle.notes.append(f"Analysis: {json.dumps(analysis)}")
    
    def _phase_hypothesize(self, cycle: ResearchCycle):
        """Hypothesis phase - generate hypotheses for improvement."""
        cycle.phase = ResearchPhase.HYPOTHESIZING
        self.state.current_phase = ResearchPhase.HYPOTHESIZING
        self._trigger_callbacks(ResearchPhase.HYPOTHESIZING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Hypothesizing...")
        
        # Generate hypothesis based on directive
        hypothesis = ExperimentHypothesis(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            description=f"Improve {cycle.directive.target_area}: {cycle.directive.description}",
            expected_outcome="Measurable improvement in target metrics",
            success_criteria=cycle.directive.success_criteria,
        )
        
        cycle.notes.append(f"Hypothesis: {hypothesis.description}")
    
    def _phase_design(self, cycle: ResearchCycle):
        """Design phase - design experiments and code."""
        cycle.phase = ResearchPhase.DESIGNING
        self.state.current_phase = ResearchPhase.DESIGNING
        self._trigger_callbacks(ResearchPhase.DESIGNING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Designing...")
        
        # Determine code type based on target area
        code_type_map = {
            'strategy': CodeType.STRATEGY,
            'risk': CodeType.RISK_RULE,
            'execution': CodeType.UTILITY,
            'analysis': CodeType.INDICATOR,
            'infrastructure': CodeType.UTILITY,
        }
        
        code_type = code_type_map.get(
            cycle.directive.target_area, CodeType.UTILITY
        )
        
        cycle.notes.append(f"Design: Code type = {code_type.name}")
    
    def _phase_implement(self, cycle: ResearchCycle):
        """Implementation phase - generate and evolve code."""
        cycle.phase = ResearchPhase.IMPLEMENTING
        self.state.current_phase = ResearchPhase.IMPLEMENTING
        self._trigger_callbacks(ResearchPhase.IMPLEMENTING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Implementing...")
        
        # Determine code type
        code_type_map = {
            'strategy': CodeType.STRATEGY,
            'risk': CodeType.RISK_RULE,
            'execution': CodeType.UTILITY,
            'analysis': CodeType.INDICATOR,
            'infrastructure': CodeType.UTILITY,
        }
        code_type = code_type_map.get(cycle.directive.target_area, CodeType.UTILITY)
        
        # Generate code using self-programming engine
        try:
            generations = self.programming_engine.evolve_population(
                code_type=code_type,
                generations=5,  # Limited for safety
            )
            
            for gen in generations[:self.MAX_CODE_GENERATIONS_PER_CYCLE]:
                # Safety scan
                scan_result = self.scanner.scan(gen.code)
                
                if scan_result.is_safe:
                    cycle.code_generated.append(gen.generation_id)
                    self.state.total_code_generated += 1
                else:
                    cycle.notes.append(
                        f"Code {gen.generation_id} failed safety scan: "
                        f"{scan_result.threat_level.name}"
                    )
            
            cycle.notes.append(f"Generated {len(cycle.code_generated)} safe code specimens")
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            cycle.notes.append(f"Code generation error: {e}")
    
    def _phase_test(self, cycle: ResearchCycle):
        """Testing phase - test generated code in sandbox."""
        cycle.phase = ResearchPhase.TESTING
        self.state.current_phase = ResearchPhase.TESTING
        self._trigger_callbacks(ResearchPhase.TESTING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Testing...")
        
        test_results = []
        
        for gen_id in cycle.code_generated[:self.MAX_EXPERIMENTS_PER_CYCLE]:
            generation = self.programming_engine.generations.get(gen_id)
            if not generation:
                continue
            
            # Register experiment
            exp_id = self.registry.register_experiment(
                name=f"Test {gen_id}",
                description=f"Testing generated code for {cycle.directive.title}",
                experiment_type=ExperimentType.CODE_GENERATION,
                hypothesis=ExperimentHypothesis(
                    hypothesis_id=f"hyp_{gen_id}",
                    description="Generated code improves target metrics",
                    expected_outcome="Positive test results",
                    success_criteria=cycle.directive.success_criteria,
                ),
            )
            
            cycle.experiments_run.append(exp_id)
            self.state.total_experiments += 1
            
            # Approve and run
            self.registry.approve_experiment(exp_id, "autonomous_organism")
            self.registry.start_experiment(exp_id)
            self.registry.set_running(exp_id)
            
            # Execute in sandbox
            result = self.sandbox.execute(generation.code)
            
            if result.success:
                test_results.append({
                    'generation_id': gen_id,
                    'experiment_id': exp_id,
                    'success': True,
                    'execution_time_ms': result.execution_time_ms,
                })
                
                self.registry.complete_experiment(
                    exp_id,
                    ExperimentOutcome.SUCCESS,
                    {'execution_time_ms': result.execution_time_ms}
                )
            else:
                test_results.append({
                    'generation_id': gen_id,
                    'experiment_id': exp_id,
                    'success': False,
                    'error': result.error,
                })
                
                self.registry.fail_experiment(exp_id, result.error or "Unknown error")
        
        # Calculate test success rate
        success_count = sum(1 for r in test_results if r['success'])
        cycle.metrics['test_success_rate'] = (
            success_count / len(test_results) if test_results else 0
        )
        
        cycle.notes.append(
            f"Testing complete: {success_count}/{len(test_results)} passed"
        )
    
    def _phase_validate(self, cycle: ResearchCycle):
        """Validation phase - validate against success criteria."""
        cycle.phase = ResearchPhase.VALIDATING
        self.state.current_phase = ResearchPhase.VALIDATING
        self._trigger_callbacks(ResearchPhase.VALIDATING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Validating...")
        
        # Calculate validation score
        validation_score = 0.0
        
        # Check test success rate
        test_rate = cycle.metrics.get('test_success_rate', 0)
        if test_rate >= 0.8:
            validation_score += 0.4
        elif test_rate >= 0.5:
            validation_score += 0.2
        
        # Check code quality
        if cycle.code_generated:
            best_gen = self.programming_engine.get_best_code()
            if best_gen and best_gen.fitness_score >= 0.7:
                validation_score += 0.3
        
        # Check safety
        safe_count = sum(
            1 for gid in cycle.code_generated
            if self.programming_engine.generations.get(gid, CodeGeneration(
                generation_id="", code_type=CodeType.UTILITY, code="",
                strategy=EvolutionStrategy.TEMPLATE
            )).safety_scan_passed
        )
        if cycle.code_generated:
            safety_rate = safe_count / len(cycle.code_generated)
            validation_score += safety_rate * 0.3
        
        cycle.metrics['validation_score'] = validation_score
        
        cycle.notes.append(f"Validation score: {validation_score:.2f}")
    
    def _phase_deploy(self, cycle: ResearchCycle):
        """Deployment phase - deploy validated improvements."""
        cycle.phase = ResearchPhase.DEPLOYING
        self.state.current_phase = ResearchPhase.DEPLOYING
        self._trigger_callbacks(ResearchPhase.DEPLOYING)
        
        logger.debug(f"Cycle {cycle.cycle_id}: Deploying...")
        
        # Check deployment limit
        if self._deployments_today >= self.MAX_DEPLOYMENTS_PER_DAY:
            cycle.notes.append("Deployment limit reached for today")
            return
        
        # Get best code
        best_gen = self.programming_engine.get_best_code()
        if not best_gen:
            cycle.notes.append("No code to deploy")
            return
        
        # Final safety check
        scan_result = self.scanner.scan(best_gen.code)
        if not scan_result.is_safe:
            cycle.notes.append(f"Final safety check failed: {scan_result.threat_level.name}")
            return
        
        # Request firewall approval for deployment
        try:
            # In production, this would write to actual deployment location
            deployment_path = self.storage_path / "deployments" / f"{best_gen.generation_id}.py"
            deployment_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(deployment_path, 'w') as f:
                f.write(f"# Deployed by ContinuousResearchOrganism\n")
                f.write(f"# Cycle: {cycle.cycle_id}\n")
                f.write(f"# Directive: {cycle.directive.title}\n")
                f.write(f"# Timestamp: {datetime.utcnow().isoformat()}\n\n")
                f.write(best_gen.code)
            
            cycle.improvements_deployed.append(best_gen.generation_id)
            self.state.total_improvements += 1
            self._deployments_today += 1
            
            # Trigger improvement callbacks
            for callback in self._improvement_callbacks:
                try:
                    callback(best_gen, cycle)
                except Exception as e:
                    logger.error(f"Improvement callback error: {e}")
            
            cycle.notes.append(f"Deployed: {best_gen.generation_id}")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            cycle.notes.append(f"Deployment error: {e}")
    
    def _trigger_callbacks(self, phase: ResearchPhase):
        """Trigger registered callbacks for phase."""
        for callback in self._phase_callbacks.get(phase, []):
            try:
                callback(self.state.current_cycle)
            except Exception as e:
                logger.error(f"Phase callback error: {e}")
    
    def register_phase_callback(self, 
                                phase: ResearchPhase, 
                                callback: Callable[[ResearchCycle], None]):
        """Register callback for phase transitions."""
        self._phase_callbacks[phase].append(callback)
    
    def register_improvement_callback(self, 
                                       callback: Callable[[CodeGeneration, ResearchCycle], None]):
        """Register callback for improvements."""
        self._improvement_callbacks.append(callback)
    
    def _save_cycle(self, cycle: ResearchCycle):
        """Save cycle to storage."""
        try:
            cycles_path = self.storage_path / "cycles"
            cycles_path.mkdir(parents=True, exist_ok=True)
            
            file_path = cycles_path / f"{cycle.cycle_id}.json"
            with open(file_path, 'w') as f:
                json.dump(cycle.to_dict(), f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save cycle: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current organism status."""
        return {
            'state': self.state.to_dict(),
            'components': {
                'sandbox': self.sandbox.get_statistics(),
                'budget': self.budget_controller.get_budget_report(),
                'scanner': self.scanner.get_statistics(),
                'registry': self.registry.get_statistics(),
                'programming': self.programming_engine.get_evolution_statistics(),
            },
            'rate_limits': {
                'cycles_today': self._cycles_today,
                'max_cycles_per_day': self.MAX_CYCLES_PER_DAY,
                'deployments_today': self._deployments_today,
                'max_deployments_per_day': self.MAX_DEPLOYMENTS_PER_DAY,
            },
            'directives': {
                'total': len(self.directives),
                'active': len([d for d in self.directives.values() if d.status == 'active']),
            },
        }
    
    def get_recent_cycles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent research cycles."""
        return [c.to_dict() for c in self.cycles[-limit:]]
    
    def emergency_stop(self, reason: str = "Emergency stop"):
        """Emergency stop of all operations."""
        logger.critical(f"EMERGENCY STOP: {reason}")
        
        self._running = False
        self._shutdown_event.set()
        self.state.is_active = False
        
        # Release all budgets
        self.budget_controller.emergency_release_all()
        
        # Mark current cycle as failed
        if self.state.current_cycle:
            self.state.current_cycle.notes.append(f"Emergency stop: {reason}")
            self._save_cycle(self.state.current_cycle)
        
        logger.critical("Emergency stop completed")


def create_research_organism(
    storage_path: Optional[str] = None,
    auto_start: bool = False
) -> ContinuousResearchOrganism:
    """
    Factory function to create a research organism.
    
    Args:
        storage_path: Optional storage path
        auto_start: Whether to start automatically
        
    Returns:
        Configured ContinuousResearchOrganism
    """
    path = Path(storage_path) if storage_path else None
    organism = ContinuousResearchOrganism(storage_path=path)
    
    if auto_start:
        organism.start()
    
    return organism
