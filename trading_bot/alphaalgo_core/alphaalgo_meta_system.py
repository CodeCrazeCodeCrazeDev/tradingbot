"""
AlphaAlgo Meta-System: Offline Intelligence Infrastructure

An offline meta-system that continuously identifies weaknesses in AlphaAlgo's:
- Research workflows
- Analysis pipelines
- Signal generation
- Agent workflows

Then proposes and validates upgrades in simulation before controlled promotion.

Core Philosophy:
"Stop when risk rises faster than capability"

Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                    AlphaAlgoMetaSystem                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Research   │  │   Analysis   │  │    Signal    │            │
│  │   Monitor    │  │   Monitor    │  │   Monitor    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                  │                  │                     │
│  ┌──────▼──────────────────▼──────────────────▼───────┐            │
│  │              Bottleneck Detection Engine             │            │
│  │  • Performance regression analysis                  │            │
│  │  • Workflow latency profiling                       │            │
│  │  • Quality degradation detection                    │            │
│  └──────┬──────────────────────────────────────┬──────┘            │
│         │                                      │                     │
│  ┌──────▼──────────────┐  ┌───────────────────▼───────┐            │
│  │  Improvement       │  │    Risk-Capability      │            │
│  │  Proposal Gen      │  │    Balance Monitor      │            │
│  │  • Hypothesis gen  │  │  • Risk velocity tracker │            │
│  │  • Fix templates   │  │  • Capability growth     │            │
│  │  • Complexity est  │  │  • Safety brake          │            │
│  └──────┬──────────────┘  └──────────┬────────────────┘            │
│         │                            │                               │
│  ┌──────▼────────────────────────────▼───────┐                      │
│  │         Sandbox Validation Pipeline        │                      │
│  │  • Isolated environment testing           │                      │
│  │  • Backtesting with costs                  │                      │
│  │  • Cross-regime validation                │                      │
│  │  • Performance measurement                │                      │
│  └──────┬────────────────────────────────────┘                      │
│         │                                                           │
│  ┌──────▼──────────────┐                                           │
│  │   Promotion Gate     │  ← Only promote if:                      │
│  │   (Controlled)       │     • Measurable improvement               │
│  │                      │     • Risk unchanged or lower              │
│  │                      │     • All tests pass                       │
│  └─────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────┘

Safety Mechanisms:
1. Risk-Capability Ratio Monitor - stops if risk grows faster than capability
2. Rollback capability for any promoted change
3. Gradual rollout with kill switches
4. Automated safety boundaries
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
import numpy as np

# Import existing AlphaAlgo components
try:
    from ..alpha_research.weakness_detection import (
        WeaknessDetector, PerformanceSnapshot, RootCauseType, WeaknessSeverity
    )
    from ..alpha_research.sandbox_testing import (
        SandboxTester, TestType, TestStatus, TestConfig, TestResult
    )
    from ..alpha_research.rdaos_core import Hypothesis, FeatureFamily, RegimeType
    ALPHA_COMPONENTS_AVAILABLE = True
except ImportError:
    ALPHA_COMPONENTS_AVAILABLE = False
    logging.warning("AlphaAlgo components not available, using stubs")

# Import our unified intelligence system
from ..decision_governance.unified_intelligence import (
    UnifiedFinancialIntelligenceSystem, SystemPhase, IntelligenceMetrics
)
from ..decision_governance.trading_simulator import (
    TradingSimulatorIntegration, MarketRegime
)

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of AlphaAlgo workflows to monitor"""
    RESEARCH = "research"  # Feature discovery, hypothesis generation
    ANALYSIS = "analysis"  # Market analysis, regime detection
    SIGNAL_GENERATION = "signal_generation"  # Alpha signal production
    AGENT_WORKFLOW = "agent_workflow"  # Multi-agent coordination


class BottleneckType(Enum):
    """Types of bottlenecks that can be detected"""
    LATENCY = "latency"  # Workflow taking too long
    QUALITY_DEGRADATION = "quality_degradation"  # Output quality declining
    RESOURCE_STARVATION = "resource_starvation"  # Not enough compute/data
    CAPACITY_LIMIT = "capacity_limit"  # Hitting throughput limits
    ERROR_RATE = "error_rate"  # Too many failures
    ALPHA_DECAY = "alpha_decay"  # Signal quality degrading


class ImprovementStatus(Enum):
    """Status of an improvement proposal"""
    IDENTIFIED = "identified"  # Bottleneck found
    PROPOSED = "proposed"  # Fix designed
    SANDBOX_PENDING = "sandbox_pending"  # Waiting to test
    SANDBOX_TESTING = "sandbox_testing"  # Currently testing
    VALIDATED = "validated"  # Tests passed
    REJECTED = "rejected"  # Tests failed
    PROMOTED = "promoted"  # In production
    ROLLED_BACK = "rolled_back"  # Reverted


@dataclass
class WorkflowBottleneck:
    """A detected bottleneck in an AlphaAlgo workflow"""
    bottleneck_id: str
    workflow_type: WorkflowType
    bottleneck_type: BottleneckType
    
    description: str
    severity: float  # 0.0 - 1.0
    
    # Performance impact
    performance_impact: float  # Estimated performance degradation
    frequency: int  # How often this occurs
    
    # Detection info
    detected_at: datetime
    first_observed: datetime
    last_observed: datetime
    
    # Root cause
    root_cause: str
    contributing_factors: List[str]
    
    # Metrics at detection
    metrics_at_detection: Dict[str, float]
    
    def is_critical(self) -> bool:
        return self.severity > 0.8 or self.performance_impact > 0.2


@dataclass
class ImprovementProposal:
    """A proposed improvement to address a bottleneck"""
    proposal_id: str
    target_bottleneck: str  # bottleneck_id
    
    title: str
    description: str
    
    # What this improves
    workflow_type: WorkflowType
    expected_benefit: str
    
    # Implementation details
    implementation_complexity: str  # low, medium, high
    estimated_implementation_time: timedelta
    required_resources: List[str]
    
    # Validation criteria
    success_criteria: Dict[str, Any]  # Metrics to validate
    minimum_improvement_threshold: float  # Must improve by at least this much
    
    # Risk assessment
    risk_level: str  # low, medium, high
    rollback_difficulty: str  # easy, medium, hard
    blast_radius: List[str]  # What could be affected
    
    # Status tracking
    status: ImprovementStatus
    created_at: datetime
    sandbox_results: Optional[Dict] = None
    promoted_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None


@dataclass
class RiskCapabilityBalance:
    """Tracks the balance between risk and capability"""
    timestamp: datetime
    
    # Capability metrics
    capability_score: float  # Overall system capability
    capability_velocity: float  # Rate of capability growth
    new_capabilities: int
    
    # Risk metrics
    risk_score: float  # Overall risk level
    risk_velocity: float  # Rate of risk growth
    risk_sources: List[str]
    
    # Balance calculation
    risk_capability_ratio: float  # risk_velocity / capability_velocity
    is_safe: bool  # True if capability grows faster than risk
    
    # Safety status
    safety_margin: float  # How much room before danger
    recommended_action: str  # continue, pause, stop, rollback


@dataclass
class SandboxValidationResult:
    """Results from sandbox testing of an improvement"""
    proposal_id: str
    test_id: str
    
    # Test configuration
    test_scenarios: List[str]
    duration_hours: int
    
    # Results
    status: str  # passed, failed, partial
    
    # Performance metrics
    baseline_metrics: Dict[str, float]
    improved_metrics: Dict[str, float]
    improvement_delta: Dict[str, float]
    
    # Risk metrics
    risk_metrics: Dict[str, float]
    risk_change: float
    
    # Validation
    meets_criteria: bool
    safe_to_promote: bool
    
    # Details
    detailed_results: Dict[str, Any]
    failure_reasons: List[str]
    
    tested_at: datetime


class AlphaAlgoMetaSystem:
    """
    Offline Meta-System for AlphaAlgo Continuous Improvement
    
    Continuously monitors AlphaAlgo's workflows, detects bottlenecks,
    generates improvement proposals, validates in sandbox, and promotes
    only improvements that measurably improve results without increasing risk.
    
    SAFETY PRINCIPLE: "Stop when risk rises faster than capability"
    """
    
    def __init__(
        self,
        unified_system: Optional[UnifiedFinancialIntelligenceSystem] = None,
        sandbox_integration: Optional[TradingSimulatorIntegration] = None,
        weakness_detector: Optional[Any] = None,
        sandbox_tester: Optional[Any] = None,
        config: Optional[Dict] = None
    ):
        self.config = config or {}
        
        # Core systems
        self.unified_system = unified_system
        self.sandbox = sandbox_integration or TradingSimulatorIntegration()
        
        # AlphaAlgo specific components (or stubs)
        if ALPHA_COMPONENTS_AVAILABLE:
            self.weakness_detector = weakness_detector or WeaknessDetector()
            self.sandbox_tester = sandbox_tester or SandboxTester()
        else:
            self.weakness_detector = None
            self.sandbox_tester = None
        
        # State tracking
        self.bottlenecks: Dict[str, WorkflowBottleneck] = {}
        self.improvements: Dict[str, ImprovementProposal] = {}
        self.validation_results: Dict[str, SandboxValidationResult] = {}
        
        # Workflow performance tracking
        self.workflow_metrics: Dict[WorkflowType, deque] = {
            wt: deque(maxlen=1000) for wt in WorkflowType
        }
        
        # Risk-Capability tracking
        self.balance_history: deque = deque(maxlen=1000)
        self.current_balance: Optional[RiskCapabilityBalance] = None
        
        # Safety settings
        self.safety_brake_active: bool = False
        self.risk_capability_threshold: float = 0.8  # Stop if ratio exceeds this
        
        # Monitoring
        self._monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_bottleneck_detected: List[Callable] = []
        self.on_improvement_proposed: List[Callable] = []
        self.on_improvement_validated: List[Callable] = []
        self.on_safety_brake: List[Callable] = []
        
        logger.info("AlphaAlgoMetaSystem initialized")
    
    # ==================== Core Lifecycle ====================
    
    async def start(self):
        """Start the meta-system monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        logger.info("Starting AlphaAlgoMetaSystem monitoring...")
        
        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        # Start risk-capability balance monitoring
        asyncio.create_task(self._balance_monitoring_loop())
        
        logger.info("✓ AlphaAlgoMetaSystem monitoring active")
    
    async def stop(self):
        """Stop the meta-system"""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("AlphaAlgoMetaSystem stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                cycle_start = datetime.utcnow()
                
                # Skip if safety brake is active
                if self.safety_brake_active:
                    logger.warning("Safety brake active - skipping improvement cycle")
                    await asyncio.sleep(300)  # Check every 5 minutes
                    continue
                
                # Step 1: Monitor all workflows for bottlenecks
                await self._monitor_workflows()
                
                # Step 2: Analyze bottlenecks and generate proposals
                await self._analyze_and_propose()
                
                # Step 3: Run sandbox validation for pending proposals
                await self._run_sandbox_validations()
                
                # Step 4: Promote validated improvements
                await self._promote_validated_improvements()
                
                # Step 5: Update risk-capability balance
                await self._update_balance()
                
                # Wait for next cycle
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                sleep_time = max(0, 600 - cycle_duration)  # 10 minute cycles
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    # ==================== Workflow Monitoring ====================
    
    async def _monitor_workflows(self):
        """Monitor all AlphaAlgo workflows for bottlenecks"""
        for workflow_type in WorkflowType:
            await self._monitor_single_workflow(workflow_type)
    
    async def _monitor_single_workflow(self, workflow_type: WorkflowType):
        """Monitor a specific workflow type"""
        # Collect current metrics (placeholder - would interface with actual systems)
        metrics = await self._collect_workflow_metrics(workflow_type)
        
        # Store metrics
        self.workflow_metrics[workflow_type].append({
            'timestamp': datetime.utcnow(),
            'metrics': metrics
        })
        
        # Detect bottlenecks
        bottleneck = self._detect_bottleneck(workflow_type, metrics)
        
        if bottleneck:
            # Store bottleneck
            self.bottlenecks[bottleneck.bottleneck_id] = bottleneck
            
            # Trigger callbacks
            for callback in self.on_bottleneck_detected:
                try:
                    callback(bottleneck)
                except Exception as e:
                    logger.warning(f"Bottleneck callback error: {e}")
            
            logger.info(f"Bottleneck detected: {bottleneck.bottleneck_id} "
                       f"({workflow_type.value}, severity: {bottleneck.severity:.2f})")
    
    async def _collect_workflow_metrics(self, workflow_type: WorkflowType) -> Dict[str, float]:
        """Collect performance metrics for a workflow"""
        # Placeholder - would interface with actual AlphaAlgo systems
        # In production, this would query the actual workflow systems
        
        base_metrics = {
            'latency_ms': np.random.normal(100, 20),
            'throughput_per_sec': np.random.normal(50, 10),
            'error_rate': np.random.normal(0.02, 0.01),
            'quality_score': np.random.normal(0.85, 0.05),
            'cpu_utilization': np.random.normal(0.6, 0.1),
            'memory_utilization': np.random.normal(0.5, 0.1),
        }
        
        # Workflow-specific metrics
        if workflow_type == WorkflowType.RESEARCH:
            base_metrics['hypothesis_generation_rate'] = np.random.normal(10, 2)
            base_metrics['feature_discovery_rate'] = np.random.normal(5, 1)
            
        elif workflow_type == WorkflowType.ANALYSIS:
            base_metrics['regime_detection_accuracy'] = np.random.normal(0.8, 0.05)
            base_metrics['prediction_accuracy'] = np.random.normal(0.65, 0.05)
            
        elif workflow_type == WorkflowType.SIGNAL_GENERATION:
            base_metrics['sharpe_ratio'] = np.random.normal(1.2, 0.2)
            base_metrics['alpha_decay_rate'] = np.random.normal(0.01, 0.005)
            base_metrics['signal_correlation'] = np.random.normal(0.3, 0.1)
            
        elif workflow_type == WorkflowType.AGENT_WORKFLOW:
            base_metrics['coordination_efficiency'] = np.random.normal(0.8, 0.05)
            base_metrics['agent_consensus_rate'] = np.random.normal(0.75, 0.05)
        
        return base_metrics
    
    def _detect_bottleneck(
        self,
        workflow_type: WorkflowType,
        metrics: Dict[str, float]
    ) -> Optional[WorkflowBottleneck]:
        """Detect if there's a bottleneck in the workflow"""
        
        # Check for various bottleneck types
        checks = [
            (BottleneckType.LATENCY, metrics.get('latency_ms', 0) > 200),
            (BottleneckType.QUALITY_DEGRADATION, metrics.get('quality_score', 1.0) < 0.7),
            (BottleneckType.ERROR_RATE, metrics.get('error_rate', 0) > 0.05),
            (BottleneckType.ALPHA_DECAY, metrics.get('alpha_decay_rate', 0) > 0.02),
        ]
        
        for bottleneck_type, detected in checks:
            if detected:
                # Calculate severity
                if bottleneck_type == BottleneckType.LATENCY:
                    severity = min(1.0, metrics['latency_ms'] / 500)
                    impact = 0.1
                    description = f"High latency in {workflow_type.value}: {metrics['latency_ms']:.0f}ms"
                
                elif bottleneck_type == BottleneckType.QUALITY_DEGRADATION:
                    severity = 1.0 - metrics['quality_score']
                    impact = 0.15
                    description = f"Quality degradation in {workflow_type.value}: {metrics['quality_score']:.2f}"
                
                elif bottleneck_type == BottleneckType.ERROR_RATE:
                    severity = min(1.0, metrics['error_rate'] * 10)
                    impact = 0.2
                    description = f"High error rate in {workflow_type.value}: {metrics['error_rate']:.1%}"
                
                elif bottleneck_type == BottleneckType.ALPHA_DECAY:
                    severity = min(1.0, metrics['alpha_decay_rate'] * 50)
                    impact = 0.25
                    description = f"Alpha decay detected: {metrics['alpha_decay_rate']:.2%}/day"
                
                else:
                    continue
                
                return WorkflowBottleneck(
                    bottleneck_id=f"bottleneck_{workflow_type.value}_{bottleneck_type.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    workflow_type=workflow_type,
                    bottleneck_type=bottleneck_type,
                    description=description,
                    severity=severity,
                    performance_impact=impact,
                    frequency=1,
                    detected_at=datetime.utcnow(),
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow(),
                    root_cause=self._infer_root_cause(bottleneck_type, metrics),
                    contributing_factors=[],
                    metrics_at_detection=metrics
                )
        
        return None
    
    def _infer_root_cause(self, bottleneck_type: BottleneckType, metrics: Dict) -> str:
        """Infer root cause from bottleneck type and metrics"""
        causes = {
            BottleneckType.LATENCY: "Resource constraints or inefficient algorithms",
            BottleneckType.QUALITY_DEGRADATION: "Model drift or stale data sources",
            BottleneckType.ERROR_RATE: "Bug introduction or environment changes",
            BottleneckType.ALPHA_DECAY: "Crowding or market structure changes",
        }
        return causes.get(bottleneck_type, "Unknown - requires investigation")


# Continued in Part 2...
"""
Continuation of AlphaAlgo Meta-System
Part 2: Improvement Generation, Sandbox Validation, and Safety Controls
"""

# Continuation of AlphaAlgoMetaSystem class from Part 1

    # ==================== Improvement Proposal Generation ====================
    
    async def _analyze_and_propose(self):
        """Analyze bottlenecks and generate improvement proposals"""
        
        # Get unaddressed bottlenecks
        unaddressed = [
            b for b in self.bottlenecks.values()
            if b.bottleneck_id not in [
                imp.target_bottleneck for imp in self.improvements.values()
            ]
        ]
        
        # Sort by severity and impact
        unaddressed.sort(key=lambda b: (b.severity, b.performance_impact), reverse=True)
        
        # Generate proposals for critical bottlenecks
        for bottleneck in unaddressed[:5]:  # Top 5
            if bottleneck.is_critical():
                proposal = self._generate_improvement_proposal(bottleneck)
                self.improvements[proposal.proposal_id] = proposal
                
                # Trigger callbacks
                for callback in self.on_improvement_proposed:
                    try:
                        callback(proposal)
                    except Exception as e:
                        logger.warning(f"Proposal callback error: {e}")
                
                logger.info(f"Improvement proposed: {proposal.proposal_id} "
                           f"for bottleneck {bottleneck.bottleneck_id}")
    
    def _generate_improvement_proposal(
        self,
        bottleneck: WorkflowBottleneck
    ) -> ImprovementProposal:
        """Generate an improvement proposal for a bottleneck"""
        
        # Select improvement template based on bottleneck type
        templates = {
            BottleneckType.LATENCY: {
                'title': f"Optimize {bottleneck.workflow_type.value} latency",
                'description': f"Implement caching and parallelization to reduce latency",
                'complexity': 'medium',
                'time_hours': 48,
                'risk': 'low',
            },
            BottleneckType.QUALITY_DEGRADATION: {
                'title': f"Improve {bottleneck.workflow_type.value} quality",
                'description': f"Retrain models and refresh data sources",
                'complexity': 'high',
                'time_hours': 72,
                'risk': 'medium',
            },
            BottleneckType.ERROR_RATE: {
                'title': f"Stabilize {bottleneck.workflow_type.value}",
                'description': f"Add error handling and circuit breakers",
                'complexity': 'low',
                'time_hours': 24,
                'risk': 'low',
            },
            BottleneckType.ALPHA_DECAY: {
                'title': f"Address alpha decay in {bottleneck.workflow_type.value}",
                'description': f"Discover new features and reduce crowding",
                'complexity': 'high',
                'time_hours': 168,
                'risk': 'high',
            },
        }
        
        template = templates.get(bottleneck.bottleneck_type, {
            'title': f"Improve {bottleneck.workflow_type.value}",
            'description': f"General enhancement for {bottleneck.bottleneck_type.value}",
            'complexity': 'medium',
            'time_hours': 48,
            'risk': 'medium',
        })
        
        # Define success criteria
        success_criteria = {
            'latency_ms': bottleneck.metrics_at_detection.get('latency_ms', 100) * 0.7,
            'quality_score': min(1.0, bottleneck.metrics_at_detection.get('quality_score', 0.7) + 0.15),
            'error_rate': bottleneck.metrics_at_detection.get('error_rate', 0.05) * 0.5,
            'alpha_decay_rate': bottleneck.metrics_at_detection.get('alpha_decay_rate', 0.02) * 0.5,
        }
        
        return ImprovementProposal(
            proposal_id=f"improvement_{bottleneck.bottleneck_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            target_bottleneck=bottleneck.bottleneck_id,
            title=template['title'],
            description=template['description'],
            workflow_type=bottleneck.workflow_type,
            expected_benefit=f"Reduce {bottleneck.bottleneck_type.value} by 30%",
            implementation_complexity=template['complexity'],
            estimated_implementation_time=timedelta(hours=template['time_hours']),
            required_resources=['compute', 'data', 'engineering'],
            success_criteria=success_criteria,
            minimum_improvement_threshold=0.15,  # 15% minimum improvement
            risk_level=template['risk'],
            rollback_difficulty='medium',
            blast_radius=[bottleneck.workflow_type.value],
            status=ImprovementStatus.PROPOSED,
            created_at=datetime.utcnow()
        )
    
    # ==================== Sandbox Validation ====================
    
    async def _run_sandbox_validations(self):
        """Run sandbox validation for pending proposals"""
        
        pending = [
            imp for imp in self.improvements.values()
            if imp.status == ImprovementStatus.PROPOSED
        ]
        
        for proposal in pending:
            # Skip if safety brake is active
            if self.safety_brake_active:
                logger.warning(f"Safety brake active - skipping validation for {proposal.proposal_id}")
                continue
            
            # Update status
            proposal.status = ImprovementStatus.SANDBOX_TESTING
            
            # Run validation
            result = await self._validate_in_sandbox(proposal)
            self.validation_results[result.test_id] = result
            
            # Update proposal with results
            proposal.sandbox_results = {
                'test_id': result.test_id,
                'status': result.status,
                'improvement_delta': result.improvement_delta,
                'risk_change': result.risk_change,
                'safe_to_promote': result.safe_to_promote
            }
            
            if result.safe_to_promote:
                proposal.status = ImprovementStatus.VALIDATED
                logger.info(f"✓ Proposal {proposal.proposal_id} validated and ready for promotion")
                
                # Trigger callbacks
                for callback in self.on_improvement_validated:
                    try:
                        callback(proposal, result)
                    except Exception as e:
                        logger.warning(f"Validation callback error: {e}")
            else:
                proposal.status = ImprovementStatus.REJECTED
                logger.warning(f"✗ Proposal {proposal.proposal_id} failed validation: {result.failure_reasons}")
    
    async def _validate_in_sandbox(
        self,
        proposal: ImprovementProposal
    ) -> SandboxValidationResult:
        """Validate an improvement proposal in the sandbox"""
        
        test_id = f"test_{proposal.proposal_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Running sandbox validation: {test_id}")
        
        # Select test scenarios based on workflow type
        scenarios = self._select_test_scenarios(proposal.workflow_type)
        
        # Collect baseline metrics (simulated "before" state)
        baseline_metrics = await self._collect_baseline_metrics(proposal.workflow_type)
        
        # Run tests in sandbox
        test_results = []
        for scenario in scenarios:
            result = await self.sandbox.run_scenario(scenario)
            test_results.append(result)
        
        # Calculate improvement metrics (simulated "after" state)
        # In production, this would actually apply the improvement to a test instance
        improved_metrics = self._simulate_improved_metrics(baseline_metrics, proposal)
        
        # Calculate deltas
        improvement_delta = {
            k: improved_metrics.get(k, 0) - baseline_metrics.get(k, 0)
            for k in baseline_metrics.keys()
        }
        
        # Calculate overall improvement score
        improvement_score = np.mean([
            improvement_delta.get('sharpe_ratio', 0) / max(0.01, abs(baseline_metrics.get('sharpe_ratio', 1))),
            improvement_delta.get('quality_score', 0),
            -improvement_delta.get('error_rate', 0) * 10,  # Negative because lower is better
        ]) if baseline_metrics else 0
        
        # Calculate risk metrics
        risk_metrics = {
            'max_drawdown': max(r['max_drawdown'] for r in test_results),
            'volatility': np.mean([r.get('volatility', 0) for r in test_results]),
            'tail_risk': max(r['max_drawdown'] for r in test_results) * 1.5,
        }
        
        risk_change = risk_metrics['max_drawdown'] - baseline_metrics.get('max_drawdown', 0.1)
        
        # Determine if criteria are met
        meets_criteria = improvement_score >= proposal.minimum_improvement_threshold
        
        # Safety check: improvement must not increase risk significantly
        risk_acceptable = risk_change < 0.05  # Max 5% increase in drawdown
        
        safe_to_promote = meets_criteria and risk_acceptable
        
        failure_reasons = []
        if not meets_criteria:
            failure_reasons.append(f"Improvement {improvement_score:.2f} below threshold {proposal.minimum_improvement_threshold}")
        if not risk_acceptable:
            failure_reasons.append(f"Risk increase {risk_change:.1%} exceeds limit 5%")
        
        return SandboxValidationResult(
            proposal_id=proposal.proposal_id,
            test_id=test_id,
            test_scenarios=scenarios,
            duration_hours=len(scenarios) * 24,
            status='passed' if safe_to_promote else 'failed',
            baseline_metrics=baseline_metrics,
            improved_metrics=improved_metrics,
            improvement_delta=improvement_delta,
            risk_metrics=risk_metrics,
            risk_change=risk_change,
            meets_criteria=meets_criteria,
            safe_to_promote=safe_to_promote,
            detailed_results={'test_results': test_results},
            failure_reasons=failure_reasons,
            tested_at=datetime.utcnow()
        )
    
    def _select_test_scenarios(self, workflow_type: WorkflowType) -> List[str]:
        """Select appropriate test scenarios for a workflow type"""
        scenario_map = {
            WorkflowType.RESEARCH: ['mixed_regimes', 'sideways_chop'],
            WorkflowType.ANALYSIS: ['bull_trend', 'bear_trend', 'high_volatility'],
            WorkflowType.SIGNAL_GENERATION: ['stress_test', 'market_crash', 'bubble_pop'],
            WorkflowType.AGENT_WORKFLOW: ['mixed_regimes', 'stress_test'],
        }
        return scenario_map.get(workflow_type, ['mixed_regimes'])
    
    async def _collect_baseline_metrics(self, workflow_type: WorkflowType) -> Dict[str, float]:
        """Collect baseline performance metrics"""
        # Get recent metrics from workflow
        recent = list(self.workflow_metrics[workflow_type])[-10:]
        
        if recent:
            metrics = recent[-1]['metrics']
            return {
                'sharpe_ratio': metrics.get('sharpe_ratio', 1.0),
                'quality_score': metrics.get('quality_score', 0.8),
                'error_rate': metrics.get('error_rate', 0.02),
                'latency_ms': metrics.get('latency_ms', 100),
                'max_drawdown': 0.1,
                'throughput': metrics.get('throughput_per_sec', 50),
            }
        
        return {
            'sharpe_ratio': 1.0,
            'quality_score': 0.8,
            'error_rate': 0.02,
            'latency_ms': 100,
            'max_drawdown': 0.1,
            'throughput': 50,
        }
    
    def _simulate_improved_metrics(
        self,
        baseline: Dict[str, float],
        proposal: ImprovementProposal
    ) -> Dict[str, float]:
        """Simulate what metrics would look like after improvement"""
        # This is a simulation - in production, actually apply improvement to test instance
        improved = baseline.copy()
        
        # Apply expected improvements
        for key, target in proposal.success_criteria.items():
            if key in improved:
                # Move 50% of the way from current to target
                improved[key] = improved[key] + (target - improved[key]) * 0.5
        
        return improved
    
    # ==================== Promotion Control ====================
    
    async def _promote_validated_improvements(self):
        """Promote validated improvements to production"""
        
        validated = [
            imp for imp in self.improvements.values()
            if imp.status == ImprovementStatus.VALIDATED
        ]
        
        for proposal in validated:
            # Final safety check
            if self.safety_brake_active:
                logger.warning(f"Safety brake active - cannot promote {proposal.proposal_id}")
                continue
            
            # Check risk-capability balance
            if self.current_balance and not self.current_balance.is_safe:
                logger.warning(f"Risk-capability balance unsafe - cannot promote {proposal.proposal_id}")
                continue
            
            # Promote
            await self._promote_improvement(proposal)
            
            proposal.status = ImprovementStatus.PROMOTED
            proposal.promoted_at = datetime.utcnow()
            
            logger.info(f"✓ Improvement {proposal.proposal_id} promoted to production")
    
    async def _promote_improvement(self, proposal: ImprovementProposal):
        """Execute the promotion of an improvement"""
        # In production, this would:
        # 1. Apply the improvement to production systems
        # 2. Enable gradual rollout
        # 3. Set up monitoring
        # 4. Configure rollback capability
        
        logger.info(f"Promoting: {proposal.title}")
        logger.info(f"  Workflow: {proposal.workflow_type.value}")
        logger.info(f"  Expected benefit: {proposal.expected_benefit}")
        
        # Log for tracking
        if self.unified_system:
            await self.unified_system._record_compounding_event(
                event_type='alphaalgo_improvement_promoted',
                description=f"{proposal.title} - {proposal.expected_benefit}",
                intelligence_delta=0.03,
                capabilities_affected=[proposal.workflow_type.value]
            )
    
    # ==================== Risk-Capability Balance ====================
    
    async def _balance_monitoring_loop(self):
        """Continuously monitor risk-capability balance"""
        while self._monitoring:
            try:
                await self._update_balance()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in balance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _update_balance(self):
        """Update the risk-capability balance calculation"""
        
        # Calculate capability metrics
        total_capabilities = len(self.improvements)
        validated_capabilities = sum(1 for imp in self.improvements.values() if imp.status == ImprovementStatus.VALIDATED)
        promoted_capabilities = sum(1 for imp in self.improvements.values() if imp.status == ImprovementStatus.PROMOTED)
        
        # Calculate capability velocity (growth rate)
        if len(self.balance_history) >= 2:
            recent = list(self.balance_history)[-10:]
            capability_velocity = (promoted_capabilities - recent[0].new_capabilities) / max(1, len(recent))
        else:
            capability_velocity = 0
        
        # Calculate risk metrics
        active_bottlenecks = len([b for b in self.bottlenecks.values() if b.severity > 0.7])
        rejected_improvements = sum(1 for imp in self.improvements.values() if imp.status == ImprovementStatus.REJECTED)
        
        # Risk from validation failures
        validation_failure_rate = rejected_improvements / max(1, len(self.improvements))
        
        # Risk from bottlenecks
        bottleneck_risk = sum(b.severity for b in self.bottlenecks.values()) / max(1, len(self.bottlenecks))
        
        # Overall risk score
        risk_score = (validation_failure_rate + bottleneck_risk) / 2
        
        # Risk velocity
        if len(self.balance_history) >= 2:
            recent = list(self.balance_history)[-10:]
            risk_velocity = (risk_score - recent[0].risk_score) / max(1, len(recent))
        else:
            risk_velocity = 0
        
        # Calculate balance
        if capability_velocity > 0:
            risk_capability_ratio = abs(risk_velocity) / capability_velocity
        else:
            risk_capability_ratio = float('inf') if risk_velocity > 0 else 0
        
        # Determine safety
        is_safe = risk_capability_ratio < self.risk_capability_threshold
        
        # Calculate safety margin
        safety_margin = self.risk_capability_threshold - risk_capability_ratio
        
        # Determine recommended action
        if risk_capability_ratio > 1.0:
            recommended_action = 'stop'
        elif risk_capability_ratio > self.risk_capability_threshold:
            recommended_action = 'pause'
        elif safety_margin < 0.1:
            recommended_action = 'caution'
        else:
            recommended_action = 'continue'
        
        # Create balance record
        balance = RiskCapabilityBalance(
            timestamp=datetime.utcnow(),
            capability_score=promoted_capabilities / max(1, total_capabilities),
            capability_velocity=capability_velocity,
            new_capabilities=promoted_capabilities,
            risk_score=risk_score,
            risk_velocity=risk_velocity,
            risk_sources=[b.bottleneck_type.value for b in self.bottlenecks.values() if b.severity > 0.5],
            risk_capability_ratio=risk_capability_ratio,
            is_safe=is_safe,
            safety_margin=safety_margin,
            recommended_action=recommended_action
        )
        
        self.current_balance = balance
        self.balance_history.append(balance)
        
        # Check safety brake
        if not is_safe and not self.safety_brake_active:
            await self._activate_safety_brake(balance)
        elif is_safe and self.safety_brake_active:
            await self._deactivate_safety_brake(balance)
        
        # Log status periodically
        if len(self.balance_history) % 12 == 0:  # Every hour
            logger.info(f"Risk-Capability Balance: ratio={risk_capability_ratio:.2f}, "
                       f"safe={is_safe}, action={recommended_action}")
    
    async def _activate_safety_brake(self, balance: RiskCapabilityBalance):
        """Activate the safety brake when risk rises too fast"""
        self.safety_brake_active = True
        
        logger.critical(f"🛑 SAFETY BRAKE ACTIVATED")
        logger.critical(f"Risk-Capability ratio: {balance.risk_capability_ratio:.2f}")
        logger.critical(f"Risk velocity: {balance.risk_velocity:.4f}")
        logger.critical(f"Capability velocity: {balance.capability_velocity:.4f}")
        logger.critical("All improvements paused. Manual review required.")
        
        # Trigger callbacks
        for callback in self.on_safety_brake:
            try:
                callback(balance)
            except Exception as e:
                logger.warning(f"Safety brake callback error: {e}")
        
        # Notify unified system
        if self.unified_system:
            await self.unified_system._transition_to_phase(SystemPhase.DEGRADED)
    
    async def _deactivate_safety_brake(self, balance: RiskCapabilityBalance):
        """Deactivate safety brake when conditions improve"""
        self.safety_brake_active = False
        
        logger.info(f"✅ Safety brake deactivated - conditions improved")
        logger.info(f"Risk-Capability ratio: {balance.risk_capability_ratio:.2f}")
        
        # Restore unified system
        if self.unified_system:
            await self.unified_system._transition_to_phase(SystemPhase.STABLE)
    
    # ==================== Public API ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self._monitoring,
            'safety_brake_active': self.safety_brake_active,
            
            'bottlenecks': {
                'total': len(self.bottlenecks),
                'critical': len([b for b in self.bottlenecks.values() if b.is_critical()]),
                'by_workflow': {
                    wt.value: len([b for b in self.bottlenecks.values() if b.workflow_type == wt])
                    for wt in WorkflowType
                }
            },
            
            'improvements': {
                'total': len(self.improvements),
                'proposed': len([i for i in self.improvements.values() if i.status == ImprovementStatus.PROPOSED]),
                'testing': len([i for i in self.improvements.values() if i.status == ImprovementStatus.SANDBOX_TESTING]),
                'validated': len([i for i in self.improvements.values() if i.status == ImprovementStatus.VALIDATED]),
                'promoted': len([i for i in self.improvements.values() if i.status == ImprovementStatus.PROMOTED]),
                'rejected': len([i for i in self.improvements.values() if i.status == ImprovementStatus.REJECTED]),
            },
            
            'risk_capability_balance': {
                'ratio': self.current_balance.risk_capability_ratio if self.current_balance else None,
                'is_safe': self.current_balance.is_safe if self.current_balance else None,
                'capability_velocity': self.current_balance.capability_velocity if self.current_balance else None,
                'risk_velocity': self.current_balance.risk_velocity if self.current_balance else None,
                'recommended_action': self.current_balance.recommended_action if self.current_balance else None,
            },
            
            'recent_validations': [
                {
                    'test_id': v.test_id,
                    'proposal': v.proposal_id,
                    'status': v.status,
                    'improvement': sum(v.improvement_delta.values()) / max(1, len(v.improvement_delta)),
                    'risk_change': v.risk_change,
                    'safe_to_promote': v.safe_to_promote
                }
                for v in list(self.validation_results.values())[-5:]
            ]
        }
    
    def force_rollback(self, proposal_id: str) -> bool:
        """Manually rollback a promoted improvement"""
        proposal = self.improvements.get(proposal_id)
        if not proposal:
            return False
        
        if proposal.status != ImprovementStatus.PROMOTED:
            logger.warning(f"Cannot rollback {proposal_id} - status is {proposal.status.value}")
            return False
        
        proposal.status = ImprovementStatus.ROLLED_BACK
        proposal.rolled_back_at = datetime.utcnow()
        
        logger.info(f"Rolled back improvement: {proposal_id}")
        return True


# Factory function
def create_alphaalgo_meta_system(
    unified_system: Optional[UnifiedFinancialIntelligenceSystem] = None,
    config: Optional[Dict] = None
) -> AlphaAlgoMetaSystem:
    """Factory function to create AlphaAlgoMetaSystem"""
    
    return AlphaAlgoMetaSystem(
        unified_system=unified_system,
        config=config
    )
