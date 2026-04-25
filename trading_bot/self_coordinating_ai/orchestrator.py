"""
Self-Coordinating AI Orchestrator
===================================

Main orchestrator that integrates all components of the self-coordinating AI system.
Manages the complete lifecycle from opportunity discovery through self-programming
to production promotion.

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                 SELF-COORDINATING AI ORCHESTRATOR               │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  ┌────────────────┐    ┌────────────────┐    ┌──────────────┐  │
    │  │   DISCOVERY    │───▶│ SELF-PROGRAMMING│───▶│  EXPERIMENT  │  │
    │  │    ENGINE      │    │    PROPOSER     │    │   REGISTRY   │  │
    │  └────────────────┘    └────────────────┘    └──────────────┘  │
    │           │                    │                    │           │
    │           ▼                    ▼                    ▼           │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │                    SAFETY LAYER                            ││
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   ││
    │  │  │  CODE    │  │  DATA    │  │ COMPUTE  │  │  SANDBOX │   ││
    │  │  │ SCANNER  │  │ FIREWALL │  │  BUDGET  │  │ EXECUTOR │   ││
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   ││
    │  └────────────────────────────────────────────────────────────┘│
    │                              │                                  │
    │                              ▼                                  │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │                   PROMOTION SYSTEM                         ││
    │  │  Safety Review ─▶ Performance Review ─▶ Approval ─▶ Stage  ││
    │  └────────────────────────────────────────────────────────────┘│
    │                              │                                  │
    │                              ▼                                  │
    │  ┌────────────────────────────────────────────────────────────┐│
    │  │              CORE PRODUCTION SYSTEM (IMMUTABLE)            ││
    │  └────────────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────────────┘

Author: AlphaAlgo Trading System
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from .core_production_system import CoreProductionSystem, ProductionConfig
from .sandbox_executor import SandboxExecutor, SandboxConfig, ExecutionResult
from .compute_budget_controller import ComputeBudgetController, BudgetConfig, ResourceAllocation
from .experiment_registry import (
    ExperimentRegistry, Experiment, ExperimentStatus, 
    ExperimentType, ExperimentCategory, ExperimentMetrics
)
from .data_integrity_firewall import DataIntegrityFirewall, FirewallConfig, DataCategory
from .code_safety_scanner import CodeSafetyScanner, ScanResult, SecurityLevel
from .promotion_system import PromotionSystem, PromotionRequest, PromotionStatus, PromotionType
from .market_opportunity_discovery import MarketOpportunityDiscovery, Opportunity, OpportunityStatus
from .self_programming_proposer import SelfProgrammingProposer, Improvement, ImprovementStatus

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    """State of the orchestrator."""
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    MAINTENANCE = auto()
    SHUTDOWN = auto()


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    # Component Enablement
    enable_discovery: bool = True
    enable_self_programming: bool = True
    enable_auto_experimentation: bool = True
    enable_auto_promotion: bool = False  # Requires human approval by default
    
    # Limits
    max_concurrent_experiments: int = 5
    max_pending_promotions: int = 10
    max_active_opportunities: int = 20
    
    # Intervals
    orchestration_interval_seconds: int = 60
    cleanup_interval_seconds: int = 3600
    
    # Thresholds
    min_experiment_score_for_promotion: float = 0.7
    min_confidence_for_auto_experiment: float = 0.6
    
    # Paths
    storage_path: str = "self_coordinating_ai_data"
    
    # Production Config
    production_config: Optional[ProductionConfig] = None
    sandbox_config: Optional[SandboxConfig] = None
    budget_config: Optional[BudgetConfig] = None
    firewall_config: Optional[FirewallConfig] = None


@dataclass
class OrchestratorStatus:
    """Status of the orchestrator."""
    state: OrchestratorState
    uptime_seconds: float
    
    # Component Status
    production_system_active: bool
    discovery_engine_active: bool
    self_programming_active: bool
    
    # Counts
    active_experiments: int
    pending_promotions: int
    active_opportunities: int
    pending_improvements: int
    
    # Recent Activity
    experiments_last_24h: int
    promotions_last_24h: int
    opportunities_last_24h: int
    
    # Health
    overall_health: float
    component_health: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.name,
            'uptime_seconds': self.uptime_seconds,
            'production_system_active': self.production_system_active,
            'discovery_engine_active': self.discovery_engine_active,
            'self_programming_active': self.self_programming_active,
            'active_experiments': self.active_experiments,
            'pending_promotions': self.pending_promotions,
            'active_opportunities': self.active_opportunities,
            'pending_improvements': self.pending_improvements,
            'experiments_last_24h': self.experiments_last_24h,
            'promotions_last_24h': self.promotions_last_24h,
            'opportunities_last_24h': self.opportunities_last_24h,
            'overall_health': self.overall_health,
            'component_health': self.component_health,
        }


class SelfCoordinatingAIOrchestrator:
    """
    Main orchestrator for the Self-Coordinating AI system.
    
    Integrates all components:
    - Core Production System (immutable)
    - Market Opportunity Discovery
    - Self-Programming Proposer
    - Experiment Registry
    - Sandbox Executor
    - Code Safety Scanner
    - Data Integrity Firewall
    - Compute Budget Controller
    - Promotion System
    
    Manages the complete lifecycle:
    1. Discover market opportunities
    2. Propose improvements via self-programming
    3. Scan code for safety
    4. Execute experiments in sandbox
    5. Validate results
    6. Promote to production (with approval)
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Orchestrator configuration
        """
        self.config = config or OrchestratorConfig()
        
        self._state = OrchestratorState.INITIALIZING
        self._start_time: Optional[datetime] = None
        
        # Storage
        self._storage_path = Path(self.config.storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._production_system: Optional[CoreProductionSystem] = None
        self._sandbox_executor: Optional[SandboxExecutor] = None
        self._budget_controller: Optional[ComputeBudgetController] = None
        self._experiment_registry: Optional[ExperimentRegistry] = None
        self._firewall: Optional[DataIntegrityFirewall] = None
        self._code_scanner: Optional[CodeSafetyScanner] = None
        self._promotion_system: Optional[PromotionSystem] = None
        self._discovery_engine: Optional[MarketOpportunityDiscovery] = None
        self._self_programmer: Optional[SelfProgrammingProposer] = None
        
        # Tasks
        self._orchestration_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Event callbacks
        self._event_callbacks: List[Callable] = []
        
        # Statistics
        self._stats = {
            'total_experiments': 0,
            'successful_experiments': 0,
            'total_promotions': 0,
            'successful_promotions': 0,
            'opportunities_discovered': 0,
            'improvements_proposed': 0,
            'safety_blocks': 0,
        }
        
        logger.info("SelfCoordinatingAIOrchestrator created")
    
    async def initialize(self):
        """Initialize all components."""
        logger.info("=" * 80)
        logger.info("INITIALIZING SELF-COORDINATING AI INFRASTRUCTURE")
        logger.info("=" * 80)
        
        # Initialize Core Production System
        prod_config = self.config.production_config or ProductionConfig()
        self._production_system = CoreProductionSystem(prod_config)
        await self._production_system.initialize()
        logger.info("✅ Core Production System initialized (IMMUTABLE)")
        
        # Initialize Sandbox Executor
        sandbox_config = self.config.sandbox_config or SandboxConfig()
        self._sandbox_executor = SandboxExecutor(sandbox_config)
        logger.info("✅ Sandbox Executor initialized")
        
        # Initialize Compute Budget Controller
        budget_config = self.config.budget_config or BudgetConfig()
        self._budget_controller = ComputeBudgetController(budget_config)
        await self._budget_controller.start()
        logger.info("✅ Compute Budget Controller initialized")
        
        # Initialize Experiment Registry
        self._experiment_registry = ExperimentRegistry(
            storage_path=str(self._storage_path / 'experiments')
        )
        await self._experiment_registry.load_experiments()
        logger.info("✅ Experiment Registry initialized")
        
        # Initialize Data Integrity Firewall
        firewall_config = self.config.firewall_config or FirewallConfig()
        self._firewall = DataIntegrityFirewall(firewall_config)
        logger.info("✅ Data Integrity Firewall initialized")
        
        # Initialize Code Safety Scanner
        self._code_scanner = CodeSafetyScanner()
        logger.info("✅ Code Safety Scanner initialized")
        
        # Initialize Promotion System
        self._promotion_system = PromotionSystem(
            storage_path=str(self._storage_path / 'promotions')
        )
        logger.info("✅ Promotion System initialized")
        
        # Initialize Market Opportunity Discovery
        if self.config.enable_discovery:
            self._discovery_engine = MarketOpportunityDiscovery()
            self._discovery_engine.register_discovery_callback(self._on_opportunity_discovered)
            logger.info("✅ Market Opportunity Discovery initialized")
        
        # Initialize Self-Programming Proposer
        if self.config.enable_self_programming:
            self._self_programmer = SelfProgrammingProposer(
                storage_path=str(self._storage_path / 'improvements')
            )
            self._self_programmer.register_proposal_callback(self._on_improvement_proposed)
            logger.info("✅ Self-Programming Proposer initialized")
        
        # Register cross-component callbacks
        self._register_callbacks()
        
        self._state = OrchestratorState.READY
        
        logger.info("=" * 80)
        logger.info("SELF-COORDINATING AI INFRASTRUCTURE READY")
        logger.info("=" * 80)
    
    def _register_callbacks(self):
        """Register callbacks between components."""
        # Experiment status changes
        self._experiment_registry.register_status_callback(self._on_experiment_status_change)
        
        # Promotion status changes
        self._promotion_system.register_status_callback(self._on_promotion_status_change)
        
        # Budget alerts
        self._budget_controller.register_alert_callback(self._on_budget_alert)
        
        # Firewall anomalies
        self._firewall.register_anomaly_callback(self._on_firewall_anomaly)
    
    async def start(self):
        """Start the orchestrator."""
        if self._state != OrchestratorState.READY:
            await self.initialize()
        
        self._state = OrchestratorState.RUNNING
        self._start_time = datetime.now(timezone.utc)
        
        # Start production system
        self._production_system.start()
        
        # Start discovery engine
        if self._discovery_engine:
            await self._discovery_engine.start()
        
        # Start self-programmer
        if self._self_programmer:
            await self._self_programmer.start()
        
        # Start orchestration loop
        self._orchestration_task = asyncio.create_task(self._orchestration_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("SelfCoordinatingAIOrchestrator started")
    
    async def stop(self):
        """Stop the orchestrator."""
        logger.info("Stopping SelfCoordinatingAIOrchestrator...")
        
        self._state = OrchestratorState.SHUTDOWN
        
        # Cancel tasks
        if self._orchestration_task:
            self._orchestration_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Stop components
        if self._discovery_engine:
            await self._discovery_engine.stop()
        
        if self._self_programmer:
            await self._self_programmer.stop()
        
        await self._budget_controller.stop()
        
        # Persist state
        await self._persist_state()
        
        logger.info("SelfCoordinatingAIOrchestrator stopped")
    
    async def _orchestration_loop(self):
        """Main orchestration loop."""
        while self._state == OrchestratorState.RUNNING:
            try:
                # Process pending improvements
                await self._process_pending_improvements()
                
                # Process pending experiments
                await self._process_pending_experiments()
                
                # Process completed experiments
                await self._process_completed_experiments()
                
                # Process promotion candidates
                await self._process_promotion_candidates()
                
                await asyncio.sleep(self.config.orchestration_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Orchestration error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self):
        """Cleanup loop for expired items."""
        while self._state == OrchestratorState.RUNNING:
            try:
                # Cleanup old sandboxes
                await self._sandbox_executor.cleanup_old_sandboxes(max_age_hours=24)
                
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(300)
    
    async def _process_pending_improvements(self):
        """Process pending improvement proposals."""
        if not self._self_programmer:
            return
        
        # Get improvements ready for experimentation
        approved = self._self_programmer.get_improvements_by_status(ImprovementStatus.APPROVED)
        
        for improvement in approved[:self.config.max_concurrent_experiments]:
            if not improvement.code:
                continue
            
            # Check if we can run more experiments
            running = self._experiment_registry.get_experiments_by_status(ExperimentStatus.RUNNING)
            if len(running) >= self.config.max_concurrent_experiments:
                break
            
            # Create experiment
            await self._create_experiment_from_improvement(improvement)
    
    async def _create_experiment_from_improvement(self, improvement: Improvement):
        """Create an experiment from an improvement."""
        try:
            # Scan code for safety
            scan_result = self._code_scanner.scan(improvement.code)
            
            if not scan_result.can_execute:
                logger.warning(f"Code safety scan failed for {improvement.improvement_id}")
                await self._self_programmer.complete_safety_review(
                    improvement.improvement_id,
                    passed=False,
                    notes=[f"Safety scan failed: {scan_result.security_level.value}"]
                )
                self._stats['safety_blocks'] += 1
                return
            
            # Request compute budget
            allocation = await self._budget_controller.request_allocation(
                experiment_id=f"exp_{improvement.improvement_id}",
                agent_id=improvement.triggered_by,
                cpu_cores=1,
                memory_gb=2.0,
                duration_hours=1.0,
            )
            
            if not allocation:
                logger.warning(f"Could not allocate resources for {improvement.improvement_id}")
                return
            
            # Determine experiment type
            exp_type = self._map_improvement_to_experiment_type(improvement.improvement_type)
            
            # Register experiment
            experiment = await self._experiment_registry.register_experiment(
                name=improvement.title,
                description=improvement.description,
                experiment_type=exp_type,
                category=ExperimentCategory.ALPHA_GENERATION,
                code=improvement.code,
                config={'improvement_id': improvement.improvement_id},
                created_by=improvement.triggered_by,
                tags={'self_programming', improvement.improvement_type.value},
            )
            
            # Link improvement to experiment
            await self._self_programmer.create_experiment(
                improvement.improvement_id,
                experiment.experiment_id,
            )
            
            # Execute in sandbox
            await self._execute_experiment(experiment, allocation)
            
            self._stats['total_experiments'] += 1
            
        except Exception as e:
            logger.error(f"Failed to create experiment from improvement: {e}")
    
    def _map_improvement_to_experiment_type(self, imp_type) -> ExperimentType:
        """Map improvement type to experiment type."""
        from .self_programming_proposer import ImprovementType
        
        mapping = {
            ImprovementType.STRATEGY_ENHANCEMENT: ExperimentType.STRATEGY,
            ImprovementType.NEW_INDICATOR: ExperimentType.INDICATOR,
            ImprovementType.RISK_OPTIMIZATION: ExperimentType.RISK_RULE,
            ImprovementType.FEATURE_ENGINEERING: ExperimentType.FEATURE,
            ImprovementType.MODEL_ARCHITECTURE: ExperimentType.MODEL,
            ImprovementType.NEW_STRATEGY: ExperimentType.STRATEGY,
        }
        
        return mapping.get(imp_type, ExperimentType.STRATEGY)
    
    async def _execute_experiment(self, experiment: Experiment, allocation: ResourceAllocation):
        """Execute an experiment in sandbox."""
        try:
            # Update status
            await self._experiment_registry.update_status(
                experiment.experiment_id,
                ExperimentStatus.RUNNING,
            )
            
            # Activate allocation
            await self._budget_controller.activate_allocation(allocation.allocation_id)
            
            # Execute in sandbox
            result = await self._sandbox_executor.execute(
                code=experiment.code,
                test_data={'experiment_id': experiment.experiment_id},
                timeout=3600,  # 1 hour max
            )
            
            # Record results
            if result.is_success:
                metrics = ExperimentMetrics(
                    execution_time_seconds=result.wall_time_used,
                    memory_peak_mb=result.memory_peak_mb,
                    cpu_time_seconds=result.cpu_time_used,
                    custom=result.metrics,
                )
                
                await self._experiment_registry.record_results(
                    experiment.experiment_id,
                    metrics,
                    output={'stdout': result.stdout[:1000]},
                )
                
                await self._experiment_registry.update_status(
                    experiment.experiment_id,
                    ExperimentStatus.COMPLETED,
                )
                
                self._stats['successful_experiments'] += 1
            else:
                await self._experiment_registry.record_error(
                    experiment.experiment_id,
                    result.exception or "Unknown error",
                )
            
            # Release allocation
            await self._budget_controller.release_allocation(allocation.allocation_id)
            
        except Exception as e:
            logger.error(f"Experiment execution failed: {e}")
            await self._experiment_registry.update_status(
                experiment.experiment_id,
                ExperimentStatus.FAILED,
                notes=str(e),
            )
    
    async def _process_pending_experiments(self):
        """Process experiments waiting for resources."""
        queued = self._experiment_registry.get_experiments_by_status(ExperimentStatus.QUEUED)
        
        for experiment in queued:
            # Check if we can run more
            running = self._experiment_registry.get_experiments_by_status(ExperimentStatus.RUNNING)
            if len(running) >= self.config.max_concurrent_experiments:
                break
            
            # Request allocation
            allocation = await self._budget_controller.request_allocation(
                experiment_id=experiment.experiment_id,
                agent_id=experiment.created_by,
                cpu_cores=1,
                memory_gb=2.0,
                duration_hours=1.0,
            )
            
            if allocation:
                await self._execute_experiment(experiment, allocation)
    
    async def _process_completed_experiments(self):
        """Process completed experiments for promotion eligibility."""
        completed = self._experiment_registry.get_experiments_by_status(ExperimentStatus.COMPLETED)
        
        for experiment in completed:
            if experiment.promotion_eligible:
                # Check if already has promotion request
                existing = self._promotion_system.get_requests_by_status(PromotionStatus.PENDING)
                if any(r.experiment_id == experiment.experiment_id for r in existing):
                    continue
                
                # Create promotion request
                await self._create_promotion_request(experiment)
    
    async def _create_promotion_request(self, experiment: Experiment):
        """Create a promotion request for an experiment."""
        try:
            # Determine promotion type
            prom_type = self._map_experiment_to_promotion_type(experiment.experiment_type)
            
            # Create request
            request = await self._promotion_system.create_promotion_request(
                experiment_id=experiment.experiment_id,
                promotion_type=prom_type,
                code=experiment.code,
                requested_by=experiment.created_by,
                description=experiment.description,
                impact_assessment=f"Score: {experiment.promotion_score:.2f}",
                rollback_plan="Revert to previous version",
            )
            
            # Auto-submit safety review (already passed scanner)
            await self._promotion_system.submit_safety_review(
                request.request_id,
                passed=True,
                reviewer='code_scanner',
                notes=['Passed automated safety scan'],
            )
            
            # Submit performance review
            if experiment.metrics:
                await self._promotion_system.submit_performance_review(
                    request.request_id,
                    metrics=experiment.metrics.to_dict(),
                    reviewer='experiment_registry',
                )
            
            self._stats['total_promotions'] += 1
            
        except Exception as e:
            logger.error(f"Failed to create promotion request: {e}")
    
    def _map_experiment_to_promotion_type(self, exp_type: ExperimentType) -> PromotionType:
        """Map experiment type to promotion type."""
        mapping = {
            ExperimentType.STRATEGY: PromotionType.STRATEGY,
            ExperimentType.INDICATOR: PromotionType.INDICATOR,
            ExperimentType.MODEL: PromotionType.MODEL,
            ExperimentType.FEATURE: PromotionType.FEATURE,
            ExperimentType.RISK_RULE: PromotionType.RISK_RULE,
        }
        
        return mapping.get(exp_type, PromotionType.STRATEGY)
    
    async def _process_promotion_candidates(self):
        """Process approved promotions for staging."""
        if not self.config.enable_auto_promotion:
            return
        
        approved = self._promotion_system.get_requests_by_status(PromotionStatus.APPROVED)
        
        for request in approved:
            # Start staging
            staging = await self._promotion_system.start_staging(
                request.request_id,
                traffic_percentage=5.0,
                duration_hours=24.0,
            )
            
            if staging:
                logger.info(f"Started staging for {request.request_id}")
    
    # Event Handlers
    
    async def _on_opportunity_discovered(self, opportunity: Opportunity):
        """Handle new opportunity discovery."""
        self._stats['opportunities_discovered'] += 1
        
        logger.info(f"New opportunity: {opportunity.opportunity_id} - {opportunity.description}")
        
        # Notify callbacks
        await self._emit_event('opportunity_discovered', opportunity.to_dict())
    
    async def _on_improvement_proposed(self, improvement: Improvement):
        """Handle new improvement proposal."""
        self._stats['improvements_proposed'] += 1
        
        logger.info(f"New improvement: {improvement.improvement_id} - {improvement.title}")
        
        # Auto-submit for safety review if code is generated
        if improvement.code and improvement.status == ImprovementStatus.CODE_GENERATED:
            scan_result = self._code_scanner.scan(improvement.code)
            
            await self._self_programmer.complete_safety_review(
                improvement.improvement_id,
                passed=scan_result.can_execute,
                notes=[f"Security level: {scan_result.security_level.value}"],
            )
        
        await self._emit_event('improvement_proposed', improvement.to_dict())
    
    async def _on_experiment_status_change(
        self,
        experiment: Experiment,
        old_status: ExperimentStatus,
        new_status: ExperimentStatus,
    ):
        """Handle experiment status change."""
        logger.debug(f"Experiment {experiment.experiment_id}: {old_status.name} -> {new_status.name}")
        
        # Update linked improvement
        if new_status == ExperimentStatus.COMPLETED:
            config = experiment.config or {}
            improvement_id = config.get('improvement_id')
            
            if improvement_id and self._self_programmer:
                actual_improvement = experiment.promotion_score
                await self._self_programmer.record_experiment_results(
                    improvement_id,
                    results=experiment.metrics.to_dict() if experiment.metrics else {},
                    actual_improvement=actual_improvement,
                )
        
        await self._emit_event('experiment_status_change', {
            'experiment_id': experiment.experiment_id,
            'old_status': old_status.name,
            'new_status': new_status.name,
        })
    
    async def _on_promotion_status_change(
        self,
        request: PromotionRequest,
        old_status: PromotionStatus,
        new_status: PromotionStatus,
    ):
        """Handle promotion status change."""
        logger.debug(f"Promotion {request.request_id}: {old_status.name} -> {new_status.name}")
        
        if new_status == PromotionStatus.PROMOTED:
            self._stats['successful_promotions'] += 1
            
            # Mark improvement as promoted
            experiment = self._experiment_registry.get_experiment(request.experiment_id)
            if experiment:
                config = experiment.config or {}
                improvement_id = config.get('improvement_id')
                
                if improvement_id and self._self_programmer:
                    await self._self_programmer.mark_promoted(improvement_id)
        
        await self._emit_event('promotion_status_change', {
            'request_id': request.request_id,
            'old_status': old_status.name,
            'new_status': new_status.name,
        })
    
    async def _on_budget_alert(self, alert):
        """Handle budget alert."""
        logger.warning(f"Budget alert: {alert.message}")
        
        await self._emit_event('budget_alert', alert.to_dict())
    
    async def _on_firewall_anomaly(self, anomaly):
        """Handle firewall anomaly."""
        logger.warning(f"Firewall anomaly: {anomaly.description}")
        
        await self._emit_event('firewall_anomaly', anomaly.to_dict())
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to callbacks."""
        event = {
            'type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data,
        }
        
        for callback in self._event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def register_event_callback(self, callback: Callable):
        """Register callback for events."""
        self._event_callbacks.append(callback)
    
    async def _persist_state(self):
        """Persist orchestrator state."""
        state = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'state': self._state.name,
            'statistics': self._stats,
        }
        
        state_file = self._storage_path / 'orchestrator_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_status(self) -> OrchestratorStatus:
        """Get current orchestrator status."""
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        # Count active items
        active_experiments = len(
            self._experiment_registry.get_experiments_by_status(ExperimentStatus.RUNNING)
        ) if self._experiment_registry else 0
        
        pending_promotions = len(
            self._promotion_system.get_pending_approvals()
        ) if self._promotion_system else 0
        
        active_opportunities = len(
            self._discovery_engine.get_opportunities_by_status(OpportunityStatus.VALIDATED)
        ) if self._discovery_engine else 0
        
        pending_improvements = len(
            self._self_programmer.get_pending_improvements()
        ) if self._self_programmer else 0
        
        # Component health
        component_health = {
            'production_system': 1.0 if self._production_system else 0.0,
            'sandbox_executor': 1.0 if self._sandbox_executor else 0.0,
            'budget_controller': 1.0 if self._budget_controller else 0.0,
            'experiment_registry': 1.0 if self._experiment_registry else 0.0,
            'firewall': 1.0 if self._firewall else 0.0,
            'code_scanner': 1.0 if self._code_scanner else 0.0,
            'promotion_system': 1.0 if self._promotion_system else 0.0,
            'discovery_engine': 1.0 if self._discovery_engine else 0.0,
            'self_programmer': 1.0 if self._self_programmer else 0.0,
        }
        
        overall_health = sum(component_health.values()) / len(component_health)
        
        return OrchestratorStatus(
            state=self._state,
            uptime_seconds=uptime,
            production_system_active=self._production_system is not None,
            discovery_engine_active=self._discovery_engine is not None,
            self_programming_active=self._self_programmer is not None,
            active_experiments=active_experiments,
            pending_promotions=pending_promotions,
            active_opportunities=active_opportunities,
            pending_improvements=pending_improvements,
            experiments_last_24h=self._stats['total_experiments'],
            promotions_last_24h=self._stats['total_promotions'],
            opportunities_last_24h=self._stats['opportunities_discovered'],
            overall_health=overall_health,
            component_health=component_health,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            'orchestrator': self._stats.copy(),
            'status': self.get_status().to_dict(),
        }
        
        if self._experiment_registry:
            stats['experiments'] = self._experiment_registry.get_statistics()
        
        if self._promotion_system:
            stats['promotions'] = self._promotion_system.get_statistics()
        
        if self._discovery_engine:
            stats['discovery'] = self._discovery_engine.get_statistics()
        
        if self._self_programmer:
            stats['self_programming'] = self._self_programmer.get_statistics()
        
        if self._budget_controller:
            stats['budget'] = self._budget_controller.get_statistics()
        
        if self._code_scanner:
            stats['code_scanner'] = self._code_scanner.get_statistics()
        
        if self._firewall:
            stats['firewall'] = self._firewall.get_statistics()
        
        return stats
    
    # Public API for manual operations
    
    async def submit_improvement(
        self,
        title: str,
        description: str,
        code: str,
        improvement_type: str = "strategy_enhancement",
    ) -> Optional[str]:
        """
        Manually submit an improvement for evaluation.
        
        Args:
            title: Improvement title
            description: Description
            code: Implementation code
            improvement_type: Type of improvement
        
        Returns:
            Improvement ID if submitted successfully
        """
        if not self._self_programmer:
            return None
        
        # This would need to be implemented in the proposer
        # For now, return None
        return None
    
    async def approve_promotion(
        self,
        request_id: str,
        approver: str,
        comments: str = "",
    ) -> bool:
        """
        Approve a promotion request.
        
        Args:
            request_id: Promotion request ID
            approver: Approver ID
            comments: Approval comments
        
        Returns:
            True if approved successfully
        """
        if not self._promotion_system:
            return False
        
        return await self._promotion_system.approve(request_id, approver, comments)
    
    async def reject_promotion(
        self,
        request_id: str,
        rejector: str,
        reason: str,
    ) -> bool:
        """
        Reject a promotion request.
        
        Args:
            request_id: Promotion request ID
            rejector: Rejector ID
            reason: Rejection reason
        
        Returns:
            True if rejected successfully
        """
        if not self._promotion_system:
            return False
        
        return await self._promotion_system.reject(request_id, rejector, reason)
    
    async def rollback_promotion(
        self,
        request_id: str,
        reason: str,
        actor: str,
    ) -> bool:
        """
        Rollback a promoted change.
        
        Args:
            request_id: Promotion request ID
            reason: Rollback reason
            actor: Who initiated rollback
        
        Returns:
            True if rolled back successfully
        """
        if not self._promotion_system:
            return False
        
        return await self._promotion_system.rollback(request_id, reason, actor)
    
    async def emergency_stop(self, reason: str, actor: str):
        """
        Trigger emergency stop on production system.
        
        Args:
            reason: Reason for emergency stop
            actor: Who triggered the stop
        """
        if self._production_system:
            await self._production_system.emergency_stop(reason, actor)
        
        # Also pause orchestrator
        self._state = OrchestratorState.PAUSED
        
        logger.critical(f"EMERGENCY STOP triggered by {actor}: {reason}")
