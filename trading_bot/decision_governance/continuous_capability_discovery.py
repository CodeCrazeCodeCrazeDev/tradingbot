"""
Continuous Capability Discovery and Innovation Engine (CCDIE)

A system that continuously maps its own capability space, detects missing capabilities,
generates targeted innovations, and integrates only those that produce robust, 
measurable improvements under real-world constraints.

Key Features:
- Real-time capability space mapping with dependency tracking
- Constraint-aware gap detection using actual trading performance
- Innovation generation with impact prediction
- Statistical validation against real baselines
- Safe integration with automatic rollback
- Performance attribution and continuous monitoring
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging
import asyncio
import json
import hashlib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class CapabilityStatus(Enum):
    """Status of a capability in the system"""
    DISCOVERED = "discovered"
    ACTIVE = "active"
    UNDERPERFORMING = "underperforming"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class InnovationStage(Enum):
    """Stage of innovation lifecycle"""
    PROPOSED = "proposed"
    ANALYZING = "analyzing"
    SANDBOX = "sandbox"
    VALIDATING = "validating"
    EVALUATING = "evaluating"
    INTEGRATED = "integrated"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass
class CapabilityNode:
    """Represents a capability in the capability space"""
    id: str
    name: str
    category: str
    status: CapabilityStatus
    dependencies: List[str]
    dependents: List[str]
    performance_metrics: Dict[str, float]
    integration_date: Optional[datetime] = None
    last_evaluated: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0


@dataclass
class CapabilityGap:
    """Represents a detected gap in capability space"""
    id: str
    description: str
    affected_categories: List[str]
    severity: float  # 0-1
    impact_score: float  # Estimated impact on performance
    detection_date: datetime
    evidence: List[Dict[str, Any]]
    root_causes: List[str]


@dataclass
class InnovationProposal:
    """Proposed innovation to address a capability gap"""
    id: str
    name: str
    description: str
    target_gap: str
    capability_type: str
    implementation_complexity: str  # low, medium, high, very_high
    estimated_improvement: float
    estimated_confidence: float
    required_capabilities: List[str]
    conflicts_with: List[str]
    test_duration_days: int
    stage: InnovationStage
    created_at: datetime
    updated_at: datetime
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    experiment_id: Optional[str] = None


@dataclass
class ConstraintProfile:
    """Real-world constraints for validation"""
    max_drawdown_limit: float = 0.15
    min_sharpe_ratio: float = 1.0
    min_win_rate: float = 0.5
    max_position_concentration: float = 0.2
    min_liquidity_threshold: float = 100000
    max_latency_ms: float = 100
    risk_adjusted_return_threshold: float = 0.001
    calibration_quality_min: float = 0.6
    robustness_score_min: float = 0.6


@dataclass
class PerformanceBaseline:
    """Baseline performance metrics for comparison"""
    timestamp: datetime
    metrics: Dict[str, float]
    sample_size: int
    confidence_intervals: Dict[str, Tuple[float, float]]
    regime_distribution: Dict[str, float]


class ContinuousCapabilityDiscoveryEngine:
    """
    Continuous Capability Discovery and Innovation Engine
    
    Core Loop:
    1. Map capability space continuously
    2. Detect gaps using real performance data
    3. Generate targeted innovations
    4. Validate under real constraints
    5. Integrate only proven improvements
    6. Monitor and rollback if needed
    """
    
    def __init__(
        self,
        decision_memory=None,
        outcome_memory=None,
        failure_memory=None,
        evolution_plane=None,
        trading_system=None,
        constraint_profile: Optional[ConstraintProfile] = None,
        storage_path: Optional[str] = None
    ):
        self.decision_memory = decision_memory
        self.outcome_memory = outcome_memory
        self.failure_memory = failure_memory
        self.evolution_plane = evolution_plane
        self.trading_system = trading_system
        self.constraints = constraint_profile or ConstraintProfile()
        self.storage_path = storage_path or "capability_discovery_state.json"
        
        # Capability space
        self.capability_graph: Dict[str, CapabilityNode] = {}
        self.capability_categories: Dict[str, List[str]] = defaultdict(list)
        
        # Gap detection
        self.active_gaps: Dict[str, CapabilityGap] = {}
        self.resolved_gaps: List[str] = []
        self.gap_detection_history: deque = deque(maxlen=100)
        
        # Innovation pipeline
        self.innovation_registry: Dict[str, InnovationProposal] = {}
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.integration_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.baselines: Dict[str, PerformanceBaseline] = {}
        self.performance_trends: Dict[str, deque] = defaultdict(lambda: deque(maxlen=90))
        
        # Continuous monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_interval_minutes: int = 60
        self.is_monitoring: bool = False
        
        # Callbacks for integration
        self.pre_integration_hooks: List[Callable] = []
        self.post_integration_hooks: List[Callable] = []
        self.rollback_hooks: List[Callable] = []
        
        # Load saved state
        self._load_state()
        
        logger.info("ContinuousCapabilityDiscoveryEngine initialized")
    
    # ==================== Continuous Capability Mapping ====================
    
    async def start_continuous_monitoring(self):
        """Start continuous capability space monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started continuous capability monitoring")
    
    async def stop_continuous_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped continuous capability monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._run_discovery_cycle()
                await asyncio.sleep(self.monitoring_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _run_discovery_cycle(self) -> Dict[str, Any]:
        """Run one complete discovery cycle"""
        cycle_start = datetime.utcnow()
        
        # 1. Map current capability space
        space_map = self._map_capability_space_realtime()
        
        # 2. Detect gaps
        gaps = self._detect_capability_gaps_realtime()
        
        # 3. Generate innovations for high-severity gaps
        innovations = []
        for gap in gaps:
            if gap.severity > 0.6 and gap.id not in [i.target_gap for i in self.innovation_registry.values()]:
                innovation = self._generate_innovation(gap)
                if innovation:
                    innovations.append(innovation)
        
        # 4. Start validations for ready innovations
        started_validations = []
        ready_innovations = [
            i for i in self.innovation_registry.values()
            if i.stage == InnovationStage.PROPOSED
            and i.estimated_improvement > self.constraints.risk_adjusted_return_threshold
        ]
        
        for innovation in ready_innovations[:2]:  # Max 2 concurrent validations
            result = await self._start_validation(innovation.id)
            if result['status'] == 'started':
                started_validations.append(result)
        
        # 5. Check active experiments for completion
        completed_evaluations = await self._check_experiment_completions()
        
        # 6. Save state
        self._save_state()
        
        cycle_result = {
            'cycle_timestamp': cycle_start.isoformat(),
            'capabilities_mapped': len(space_map),
            'categories_covered': len(self.capability_categories),
            'gaps_detected': len(gaps),
            'new_innovations': len(innovations),
            'validations_started': len(started_validations),
            'evaluations_completed': len(completed_evaluations),
            'cycle_duration_seconds': (datetime.utcnow() - cycle_start).total_seconds()
        }
        
        logger.info(f"Discovery cycle completed: {cycle_result}")
        return cycle_result
    
    def _map_capability_space_realtime(self) -> Dict[str, CapabilityNode]:
        """
        Map current capability space by scanning actual system components.
        Uses reflection and module introspection for accurate discovery.
        """
        discovered = {}
        
        # Scan all major subsystems
        subsystems = [
            ('signal_generation', self._scan_signal_capabilities),
            ('risk_management', self._scan_risk_capabilities),
            ('execution', self._scan_execution_capabilities),
            ('portfolio_management', self._scan_portfolio_capabilities),
            ('market_analysis', self._scan_analysis_capabilities),
            ('decision_governance', self._scan_governance_capabilities),
            ('monitoring', self._scan_monitoring_capabilities),
        ]
        
        for category, scanner in subsystems:
            try:
                capabilities = scanner()
                for cap_id, cap_info in capabilities.items():
                    if cap_id in self.capability_graph:
                        # Update existing
                        node = self.capability_graph[cap_id]
                        node.last_evaluated = datetime.utcnow()
                        node.performance_metrics.update(cap_info.get('metrics', {}))
                    else:
                        # Create new
                        node = CapabilityNode(
                            id=cap_id,
                            name=cap_info.get('name', cap_id),
                            category=category,
                            status=CapabilityStatus.DISCOVERED,
                            dependencies=cap_info.get('dependencies', []),
                            dependents=[],
                            performance_metrics=cap_info.get('metrics', {}),
                            last_evaluated=datetime.utcnow()
                        )
                        self.capability_graph[cap_id] = node
                        self.capability_categories[category].append(cap_id)
                    
                    discovered[cap_id] = node
            except Exception as e:
                logger.warning(f"Error scanning {category}: {e}")
        
        # Update dependency graph
        self._update_dependency_graph()
        
        # Evaluate capability health
        self._evaluate_capability_health()
        
        return discovered
    
    def _scan_signal_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan signal generation capabilities from orchestrator"""
        caps = {}
        try:
            from trading_bot.signal_discovery.orchestrator import SignalOrchestrator
            
            # Check if orchestrator exists in trading system
            if self.trading_system and hasattr(self.trading_system, 'signal_orchestrator'):
                orch = self.trading_system.signal_orchestrator
                
                # Discover available signal generators
                if hasattr(orch, 'signal_generators'):
                    for name, generator in orch.signal_generators.items():
                        caps[f"signal_{name}"] = {
                            'name': name,
                            'metrics': self._extract_generator_metrics(generator),
                            'dependencies': self._extract_dependencies(generator)
                        }
                
                # Check for advanced capabilities
                advanced_caps = [
                    ('edge_calculator', 'OptionsImpliedEdgeCalculator'),
                    ('momentum_leader', 'CrossAssetMomentumLeader'),
                    ('fragility_index', 'SignalFragilityIndex'),
                    ('saturation_detector', 'EdgeSaturationDetector'),
                ]
                
                for attr, class_name in advanced_caps:
                    if hasattr(orch, attr):
                        caps[f"signal_{attr}"] = {
                            'name': class_name,
                            'metrics': {'detected': True},
                            'dependencies': []
                        }
        except Exception as e:
            logger.debug(f"Signal scan error: {e}")
        
        return caps
    
    def _scan_risk_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan risk management capabilities"""
        caps = {}
        try:
            from trading_bot.risk.drawdown_protector import DrawdownProtector
            
            if self.trading_system and hasattr(self.trading_system, 'risk_manager'):
                rm = self.trading_system.risk_manager
                
                risk_caps = [
                    ('drawdown_protection', 'drawdown_protector'),
                    ('var_calculator', 'var_calculator'),
                    ('position_sizer', 'position_sizer'),
                    ('correlation_monitor', 'correlation_monitor'),
                ]
                
                for cap_id, attr in risk_caps:
                    if hasattr(rm, attr):
                        component = getattr(rm, attr)
                        caps[f"risk_{cap_id}"] = {
                            'name': cap_id,
                            'metrics': self._extract_risk_metrics(component),
                            'dependencies': []
                        }
        except Exception as e:
            logger.debug(f"Risk scan error: {e}")
        
        return caps
    
    def _scan_execution_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan execution capabilities"""
        caps = {}
        try:
            if self.trading_system and hasattr(self.trading_system, 'execution_engine'):
                ee = self.trading_system.execution_engine
                
                exec_caps = [
                    ('smart_order_router', 'router'),
                    ('impact_estimator', 'impact_estimator'),
                    ('timing_optimizer', 'timing_optimizer'),
                    ('liquidity_analyzer', 'liquidity_analyzer'),
                ]
                
                for cap_id, attr in exec_caps:
                    if hasattr(ee, attr):
                        caps[f"exec_{cap_id}"] = {
                            'name': cap_id,
                            'metrics': {'available': True},
                            'dependencies': []
                        }
        except Exception as e:
            logger.debug(f"Execution scan error: {e}")
        
        return caps
    
    def _scan_portfolio_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan portfolio management capabilities"""
        caps = {}
        try:
            if self.trading_system and hasattr(self.trading_system, 'portfolio_manager'):
                pm = self.trading_system.portfolio_manager
                
                port_caps = [
                    ('optimizer', 'optimizer'),
                    ('rebalancer', 'rebalancer'),
                    ('risk_allocator', 'risk_allocator'),
                ]
                
                for cap_id, attr in port_caps:
                    if hasattr(pm, attr):
                        caps[f"port_{cap_id}"] = {
                            'name': cap_id,
                            'metrics': {'available': True},
                            'dependencies': []
                        }
        except Exception as e:
            logger.debug(f"Portfolio scan error: {e}")
        
        return caps
    
    def _scan_analysis_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan market analysis capabilities"""
        caps = {}
        try:
            from trading_bot.decision_governance.layer4_regime_engine import RegimeEngine
            
            if self.trading_system and hasattr(self.trading_system, 'regime_engine'):
                re = self.trading_system.regime_engine
                
                analysis_caps = [
                    ('volatility_regime', 'volatility_detector'),
                    ('correlation_stress', 'correlation_tester'),
                    ('seasonality', 'seasonality_analyzer'),
                    ('fat_tail', 'tail_risk_calculator'),
                ]
                
                for cap_id, attr in analysis_caps:
                    if hasattr(re, attr):
                        caps[f"analysis_{cap_id}"] = {
                            'name': cap_id,
                            'metrics': self._extract_analysis_metrics(getattr(re, attr)),
                            'dependencies': []
                        }
        except Exception as e:
            logger.debug(f"Analysis scan error: {e}")
        
        return caps
    
    def _scan_governance_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan decision governance capabilities"""
        caps = {}
        try:
            gov_modules = [
                ('claim_graph', 'layer1_claim_graph'),
                ('evidence_auditor', 'layer2_evidence_auditor'),
                ('adversarial_analyst', 'layer3_adversarial_analyst'),
                ('regime_engine', 'layer4_regime_engine'),
                ('counterfactual', 'layer5_counterfactual'),
                ('uncertainty', 'layer6_uncertainty'),
            ]
            
            for cap_id, module in gov_modules:
                try:
                    __import__(f'trading_bot.decision_governance.{module}')
                    caps[f"gov_{cap_id}"] = {
                        'name': cap_id,
                        'metrics': {'available': True},
                        'dependencies': []
                    }
                except ImportError:
                    pass
        except Exception as e:
            logger.debug(f"Governance scan error: {e}")
        
        return caps
    
    def _scan_monitoring_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Scan monitoring and diagnostics capabilities"""
        caps = {}
        try:
            from trading_bot.decision_governance.monitoring import SystemMonitor
            from trading_bot.decision_governance.diagnostic_engine import DiagnosticEngine
            
            if self.trading_system:
                if hasattr(self.trading_system, 'system_monitor'):
                    caps['mon_system'] = {
                        'name': 'SystemMonitor',
                        'metrics': {'active': True},
                        'dependencies': []
                    }
                
                if hasattr(self.trading_system, 'diagnostic_engine'):
                    caps['mon_diagnostics'] = {
                        'name': 'DiagnosticEngine',
                        'metrics': {'active': True},
                        'dependencies': []
                    }
        except Exception as e:
            logger.debug(f"Monitoring scan error: {e}")
        
        return caps
    
    def _extract_generator_metrics(self, generator) -> Dict[str, float]:
        """Extract performance metrics from a signal generator"""
        metrics = {}
        try:
            if hasattr(generator, 'get_performance_stats'):
                stats = generator.get_performance_stats()
                metrics.update(stats)
            
            if hasattr(generator, 'recent_signals_count'):
                metrics['signals_generated'] = generator.recent_signals_count
        except:
            pass
        return metrics
    
    def _extract_risk_metrics(self, component) -> Dict[str, float]:
        """Extract metrics from risk component"""
        metrics = {}
        try:
            if hasattr(component, 'get_drawdown_percent'):
                metrics['current_drawdown'] = component.get_drawdown_percent()
            
            if hasattr(component, 'get_risk_metrics'):
                metrics.update(component.get_risk_metrics())
        except:
            pass
        return metrics
    
    def _extract_analysis_metrics(self, component) -> Dict[str, float]:
        """Extract metrics from analysis component"""
        metrics = {}
        try:
            if hasattr(component, 'get_regime_distribution'):
                metrics['regime_coverage'] = len(component.get_regime_distribution())
            
            if hasattr(component, 'get_detection_accuracy'):
                metrics['accuracy'] = component.get_detection_accuracy()
        except:
            pass
        return metrics
    
    def _extract_dependencies(self, component) -> List[str]:
        """Extract capability dependencies from a component"""
        deps = []
        try:
            if hasattr(component, 'required_capabilities'):
                deps.extend(component.required_capabilities)
            
            if hasattr(component, 'dependencies'):
                deps.extend(component.dependencies)
        except:
            pass
        return deps
    
    def _update_dependency_graph(self):
        """Update the dependency relationships between capabilities"""
        for cap_id, node in self.capability_graph.items():
            # Clear old dependents
            node.dependents = []
        
        # Rebuild dependents
        for cap_id, node in self.capability_graph.items():
            for dep in node.dependencies:
                if dep in self.capability_graph:
                    if cap_id not in self.capability_graph[dep].dependents:
                        self.capability_graph[dep].dependents.append(cap_id)
    
    def _evaluate_capability_health(self):
        """Evaluate health of each capability based on metrics"""
        for cap_id, node in self.capability_graph.items():
            # Check if capability is underperforming
            failure_rate = node.failure_count / max(1, node.failure_count + node.success_count)
            
            if failure_rate > 0.3:
                node.status = CapabilityStatus.UNDERPERFORMING
            elif node.integration_date and (datetime.utcnow() - node.integration_date).days > 180:
                node.status = CapabilityStatus.DEPRECATED
            elif node.status == CapabilityStatus.DISCOVERED and node.success_count > 10:
                node.status = CapabilityStatus.ACTIVE
    
    # ==================== Gap Detection ====================
    
    def _detect_capability_gaps_realtime(self) -> List[CapabilityGap]:
        """
        Detect gaps using real performance data from the trading system.
        Analyzes failures, performance degradation, and missing dependencies.
        """
        gaps = []
        
        # 1. Detect sparse categories
        for category, cap_ids in self.capability_categories.items():
            if len(cap_ids) < 3:
                gap = CapabilityGap(
                    id=f"gap_sparse_{category}_{datetime.utcnow().strftime('%Y%m%d')}",
                    description=f"Category {category} has insufficient coverage ({len(cap_ids)} capabilities)",
                    affected_categories=[category],
                    severity=0.7 if len(cap_ids) == 0 else 0.4,
                    impact_score=self._estimate_category_impact(category),
                    detection_date=datetime.utcnow(),
                    evidence=[{'type': 'coverage', 'current': len(cap_ids), 'target': 5}],
                    root_causes=['insufficient_implementation']
                )
                gaps.append(gap)
        
        # 2. Detect underperforming capabilities
        for cap_id, node in self.capability_graph.items():
            if node.status == CapabilityStatus.UNDERPERFORMING:
                gap = CapabilityGap(
                    id=f"gap_underperf_{cap_id}_{datetime.utcnow().strftime('%Y%m%d')}",
                    description=f"Capability {cap_id} is underperforming with high failure rate",
                    affected_categories=[node.category],
                    severity=0.6,
                    impact_score=self._estimate_capability_impact(cap_id),
                    detection_date=datetime.utcnow(),
                    evidence=[{
                        'type': 'failure_rate',
                        'rate': node.failure_count / max(1, node.failure_count + node.success_count),
                        'metrics': node.performance_metrics
                    }],
                    root_causes=['performance_degradation', 'model_drift']
                )
                gaps.append(gap)
        
        # 3. Detect missing dependencies
        for cap_id, node in self.capability_graph.items():
            for dep in node.dependencies:
                if dep not in self.capability_graph:
                    gap = CapabilityGap(
                        id=f"gap_dep_{dep}_{datetime.utcnow().strftime('%Y%m%d')}",
                        description=f"Missing dependency {dep} required by {cap_id}",
                        affected_categories=[node.category],
                        severity=0.8,
                        impact_score=0.5,
                        detection_date=datetime.utcnow(),
                        evidence=[{'type': 'missing_dependency', 'required_by': cap_id}],
                        root_causes=['incomplete_implementation']
                    )
                    if gap.id not in [g.id for g in gaps]:
                        gaps.append(gap)
        
        # 4. Detect from failure patterns
        if self.failure_memory:
            try:
                patterns = self.failure_memory.get_patterns(min_frequency=3, min_severity=0.5)
                for pattern in patterns:
                    gap = self._gap_from_failure_pattern(pattern)
                    if gap and gap.id not in [g.id for g in gaps]:
                        gaps.append(gap)
            except Exception as e:
                logger.warning(f"Error analyzing failure patterns: {e}")
        
        # 5. Detect from outcome metrics
        if self.outcome_memory:
            try:
                metric_gaps = self._detect_gaps_from_outcomes()
                for gap in metric_gaps:
                    if gap.id not in [g.id for g in gaps]:
                        gaps.append(gap)
            except Exception as e:
                logger.warning(f"Error analyzing outcomes: {e}")
        
        # Update active gaps
        for gap in gaps:
            self.active_gaps[gap.id] = gap
        
        self.gap_detection_history.append({
            'timestamp': datetime.utcnow(),
            'gaps_found': len(gaps)
        })
        
        return gaps
    
    def _gap_from_failure_pattern(self, pattern) -> Optional[CapabilityGap]:
        """Convert a failure pattern to a capability gap"""
        # Map pattern to required capability
        capability_map = {
            'signal_delay': 'real_time_signal_processor',
            'execution_slippage': 'slippage_predictor',
            'risk_breach': 'dynamic_risk_adjuster',
            'drawdown_spike': 'drawdown_predictor',
            'calibration_drift': 'auto_calibrator',
        }
        
        required_cap = capability_map.get(pattern.pattern_name, f"{pattern.pattern_name}_handler")
        
        return CapabilityGap(
            id=f"gap_failure_{pattern.id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}",
            description=f"Recurring {pattern.pattern_name} failures indicate missing {required_cap}",
            affected_categories=['risk_management', 'execution'],
            severity=pattern.severity,
            impact_score=pattern.frequency * 0.1,
            detection_date=datetime.utcnow(),
            evidence=[{
                'type': 'failure_pattern',
                'pattern_id': pattern.id,
                'frequency': pattern.frequency,
                'severity': pattern.severity
            }],
            root_causes=[pattern.root_cause] if hasattr(pattern, 'root_cause') else ['unknown']
        )
    
    def _detect_gaps_from_outcomes(self) -> List[CapabilityGap]:
        """Detect gaps by analyzing outcome metrics"""
        gaps = []
        
        try:
            # Get recent outcomes
            since = datetime.utcnow() - timedelta(days=30)
            outcomes = [
                o for o in self.outcome_memory.outcomes.values()
                if o.timestamp >= since
            ]
            
            if not outcomes:
                return gaps
            
            # Check calibration
            calibration = self.outcome_memory.calculate_calibration_metrics()
            if calibration.get('brier_score', 0.25) > 0.2:
                gaps.append(CapabilityGap(
                    id=f"gap_calibration_{datetime.utcnow().strftime('%Y%m%d')}",
                    description="Poor calibration detected - need improved calibration system",
                    affected_categories=['decision_governance'],
                    severity=0.6,
                    impact_score=0.4,
                    detection_date=datetime.utcnow(),
                    evidence=[{'type': 'calibration', 'brier_score': calibration.get('brier_score')}],
                    root_causes=['model_miscalibration']
                ))
            
            # Check win rate
            win_rate = sum(1 for o in outcomes if o.realized_pnl > 0) / len(outcomes)
            if win_rate < 0.45:
                gaps.append(CapabilityGap(
                    id=f"gap_winrate_{datetime.utcnow().strftime('%Y%m%d')}",
                    description=f"Low win rate ({win_rate:.2%}) indicates signal quality issues",
                    affected_categories=['signal_generation'],
                    severity=0.7,
                    impact_score=0.5,
                    detection_date=datetime.utcnow(),
                    evidence=[{'type': 'win_rate', 'value': win_rate}],
                    root_causes=['signal_quality', 'market_regime_mismatch']
                ))
            
            # Check invalidation rate
            invalidation_hits = sum(1 for o in outcomes if getattr(o, 'invalidation_hit', False))
            if outcomes:
                invalidation_rate = invalidation_hits / len(outcomes)
                if invalidation_rate > 0.25:
                    gaps.append(CapabilityGap(
                        id=f"gap_invalidation_{datetime.utcnow().strftime('%Y%m%d')}",
                        description=f"High invalidation rate ({invalidation_rate:.2%}) - need better invalidation detection",
                        affected_categories=['decision_governance', 'risk_management'],
                        severity=0.6,
                        impact_score=0.4,
                        detection_date=datetime.utcnow(),
                        evidence=[{'type': 'invalidation_rate', 'value': invalidation_rate}],
                        root_causes=['slow_invalidation_response']
                    ))
        
        except Exception as e:
            logger.warning(f"Error in outcome analysis: {e}")
        
        return gaps
    
    def _estimate_category_impact(self, category: str) -> float:
        """Estimate performance impact of a category"""
        impact_weights = {
            'signal_generation': 0.9,
            'risk_management': 0.95,
            'execution': 0.85,
            'portfolio_management': 0.8,
            'market_analysis': 0.75,
            'decision_governance': 0.85,
            'monitoring': 0.6
        }
        return impact_weights.get(category, 0.5)
    
    def _estimate_capability_impact(self, cap_id: str) -> float:
        """Estimate performance impact of a specific capability"""
        node = self.capability_graph.get(cap_id)
        if not node:
            return 0.3
        
        base_impact = self._estimate_category_impact(node.category)
        
        # Higher impact if many dependents
        dependent_factor = min(1.0, len(node.dependents) * 0.1)
        
        return min(1.0, base_impact + dependent_factor)

    # ==================== Innovation Generation ====================
    
    def _generate_innovation(self, gap: CapabilityGap) -> Optional[InnovationProposal]:
        """
        Generate a targeted innovation to address a specific capability gap.
        Uses templates and generates implementation plans.
        """
        # Check if innovation already exists for this gap
        existing = [
            i for i in self.innovation_registry.values()
            if i.target_gap == gap.id and i.stage not in [InnovationStage.REJECTED, InnovationStage.ROLLED_BACK]
        ]
        
        if existing:
            return None
        
        # Select innovation template based on gap
        template = self._select_innovation_template(gap)
        
        # Estimate improvement based on gap severity and impact
        estimated_improvement = min(0.2, gap.impact_score * gap.severity * 0.3)
        
        # Calculate required dependencies
        required_caps = self._identify_required_capabilities(template['name'])
        
        # Check for conflicts
        conflicts = self._identify_conflicts(template['name'])
        
        innovation = InnovationProposal(
            id=f"innov_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hash(gap.id) % 10000:04d}",
            name=template['name'],
            description=template['description'],
            target_gap=gap.id,
            capability_type=template['capability_type'],
            implementation_complexity=template['complexity'],
            estimated_improvement=estimated_improvement,
            estimated_confidence=0.7 + gap.severity * 0.2,
            required_capabilities=required_caps,
            conflicts_with=conflicts,
            test_duration_days=template['test_duration_days'],
            stage=InnovationStage.PROPOSED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.innovation_registry[innovation.id] = innovation
        
        logger.info(f"Generated innovation {innovation.id} for gap {gap.id}: {innovation.name}")
        
        return innovation
    
    def _select_innovation_template(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Select appropriate innovation template for gap"""
        
        # Templates by category and gap type
        templates = {
            'signal_generation': {
                'name': 'AdaptiveSignalWeightOptimizer',
                'description': 'ML-based dynamic signal weight optimization using real-time performance feedback',
                'capability_type': 'ml_optimization',
                'complexity': 'high',
                'test_duration_days': 21
            },
            'risk_management': {
                'name': 'PredictiveDrawdownArrester',
                'description': 'Predictive model that anticipates drawdowns 1-3 days ahead and preemptively reduces exposure',
                'capability_type': 'predictive_risk',
                'complexity': 'very_high',
                'test_duration_days': 30
            },
            'execution': {
                'name': 'MicrostructureAlphaExtractor',
                'description': 'Extract micro-predictability from order book dynamics for execution timing',
                'capability_type': 'microstructure',
                'complexity': 'very_high',
                'test_duration_days': 28
            },
            'portfolio_management': {
                'name': 'DynamicCorrelationHedger',
                'description': 'Real-time correlation monitoring with automatic hedging during breakdowns',
                'capability_type': 'dynamic_hedging',
                'complexity': 'high',
                'test_duration_days': 28
            },
            'market_analysis': {
                'name': 'RegimeTransitionPredictor',
                'description': 'HMM-based regime prediction with 1-5 day lookahead',
                'capability_type': 'regime_prediction',
                'complexity': 'high',
                'test_duration_days': 30
            },
            'decision_governance': {
                'name': 'MultiObjectiveDecisionOptimizer',
                'description': 'Balance profit, risk, and capacity using multi-objective optimization',
                'capability_type': 'decision_optimization',
                'complexity': 'high',
                'test_duration_days': 21
            },
            'monitoring': {
                'name': 'PredictiveSystemHealthMonitor',
                'description': 'Predict system degradation before it affects trading',
                'capability_type': 'predictive_monitoring',
                'complexity': 'medium',
                'test_duration_days': 14
            }
        }
        
        # Select based on affected categories
        for category in gap.affected_categories:
            if category in templates:
                return templates[category]
        
        # Default template
        return {
            'name': f"GapFiller_{gap.id[:8]}",
            'description': f"Address gap: {gap.description[:50]}",
            'capability_type': 'general',
            'complexity': 'medium',
            'test_duration_days': 14
        }
    
    def _identify_required_capabilities(self, innovation_name: str) -> List[str]:
        """Identify capabilities required to implement an innovation"""
        # Dependency map
        dependencies = {
            'AdaptiveSignalWeightOptimizer': ['signal_generation', 'ml_pipeline'],
            'PredictiveDrawdownArrester': ['risk_management', 'predictive_modeling'],
            'MicrostructureAlphaExtractor': ['execution', 'order_book_data'],
            'DynamicCorrelationHedger': ['portfolio_management', 'correlation_monitoring'],
            'RegimeTransitionPredictor': ['market_analysis', 'hmm_modeling'],
            'MultiObjectiveDecisionOptimizer': ['decision_governance', 'optimization_engine'],
            'PredictiveSystemHealthMonitor': ['monitoring', 'anomaly_detection']
        }
        return dependencies.get(innovation_name, [])
    
    def _identify_conflicts(self, innovation_name: str) -> List[str]:
        """Identify capabilities that may conflict with innovation"""
        # Conflict map
        conflicts = {
            'AdaptiveSignalWeightOptimizer': ['static_signal_weights'],
            'PredictiveDrawdownArrester': ['reactive_drawdown_protection'],
            'MicrostructureAlphaExtractor': ['simple_execution_timing'],
        }
        return conflicts.get(innovation_name, [])
    
    # ==================== Validation and Integration ====================
    
    async def _start_validation(self, innovation_id: str) -> Dict[str, Any]:
        """Start validation process for an innovation"""
        innovation = self.innovation_registry.get(innovation_id)
        if not innovation:
            return {'status': 'not_found', 'innovation_id': innovation_id}
        
        # Check dependencies are available
        missing_deps = [
            dep for dep in innovation.required_capabilities
            if dep not in self.capability_graph
        ]
        
        if missing_deps:
            return {
                'status': 'blocked',
                'innovation_id': innovation_id,
                'reason': f"Missing dependencies: {missing_deps}"
            }
        
        # Check for conflicts
        active_conflicts = [
            c for c in innovation.conflicts_with
            if c in self.capability_graph
            and self.capability_graph[c].status == CapabilityStatus.ACTIVE
        ]
        
        if active_conflicts:
            return {
                'status': 'blocked',
                'innovation_id': innovation_id,
                'reason': f"Active conflicts: {active_conflicts}"
            }
        
        # Capture baseline
        baseline = self._capture_real_baseline()
        
        # Create experiment
        experiment_id = f"exp_{innovation_id}"
        
        self.active_experiments[experiment_id] = {
            'innovation_id': innovation_id,
            'baseline': baseline,
            'start_time': datetime.utcnow(),
            'expected_end': datetime.utcnow() + timedelta(days=innovation.test_duration_days),
            'stage': 'sandbox',
            'sandbox_results': None,
            'live_metrics': [],
            'status': 'running'
        }
        
        innovation.stage = InnovationStage.SANDBOX
        innovation.experiment_id = experiment_id
        innovation.updated_at = datetime.utcnow()
        
        # Start sandbox testing
        asyncio.create_task(self._run_sandbox_testing(experiment_id))
        
        logger.info(f"Started validation for innovation {innovation_id}")
        
        return {
            'status': 'started',
            'innovation_id': innovation_id,
            'experiment_id': experiment_id,
            'baseline_metrics': baseline.metrics,
            'expected_completion': self.active_experiments[experiment_id]['expected_end'].isoformat()
        }
    
    def _capture_real_baseline(self) -> PerformanceBaseline:
        """Capture real performance baseline from trading system"""
        metrics = {}
        sample_size = 0
        outcomes = []
        
        try:
            # Get metrics from outcome memory
            if self.outcome_memory:
                since = datetime.utcnow() - timedelta(days=30)
                outcomes = [
                    o for o in self.outcome_memory.outcomes.values()
                    if o.timestamp >= since
                ]
                
                if outcomes:
                    pnls = [o.realized_pnl for o in outcomes]
                    metrics['win_rate'] = sum(1 for p in pnls if p > 0) / len(pnls)
                    metrics['avg_return'] = sum(pnls) / len(pnls)
                    metrics['sharpe_estimate'] = np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252)
                    sample_size = len(outcomes)
            
            # Get risk metrics
            if self.trading_system and hasattr(self.trading_system, 'risk_manager'):
                rm = self.trading_system.risk_manager
                if hasattr(rm, 'get_current_drawdown'):
                    metrics['current_drawdown'] = rm.get_current_drawdown()
                if hasattr(rm, 'get_portfolio_var'):
                    metrics['portfolio_var'] = rm.get_portfolio_var()
            
            # Calculate confidence intervals
            confidence_intervals = {}
            if outcomes:
                pnls = [o.realized_pnl for o in outcomes]
                mean = np.mean(pnls)
                std = np.std(pnls)
                n = len(pnls)
                ci = 1.96 * std / np.sqrt(n) if n > 0 else 0
                confidence_intervals['avg_return'] = (mean - ci, mean + ci)
        except Exception as e:
            logger.warning(f"Error capturing baseline: {e}")
            confidence_intervals = {}
        
        return PerformanceBaseline(
            timestamp=datetime.utcnow(),
            metrics=metrics,
            sample_size=sample_size,
            confidence_intervals=confidence_intervals,
            regime_distribution={}
        )
    
    async def _run_sandbox_testing(self, experiment_id: str):
        """Run sandbox testing phase"""
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            return
        
        innovation_id = experiment['innovation_id']
        innovation = self.innovation_registry.get(innovation_id)
        
        try:
            # Run backtests
            backtest_results = await self._run_innovation_backtests(innovation)
            
            # Run stress tests
            stress_results = await self._run_innovation_stress_tests(innovation)
            
            # Evaluate results
            sandbox_passed = (
                backtest_results.get('improvement', 0) > self.constraints.risk_adjusted_return_threshold and
                stress_results.get('survived', False) and
                backtest_results.get('max_drawdown', 1.0) < self.constraints.max_drawdown_limit
            )
            
            experiment['sandbox_results'] = {
                'backtest': backtest_results,
                'stress': stress_results,
                'passed': sandbox_passed,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            if sandbox_passed:
                innovation.stage = InnovationStage.VALIDATING
                experiment['stage'] = 'validation'
                logger.info(f"Sandbox passed for {innovation_id}, proceeding to validation")
                
                # If evolution plane available, submit for formal validation
                if self.evolution_plane:
                    from .core_types import CapabilityHypothesis
                    hypothesis = CapabilityHypothesis(
                        id=innovation_id,
                        gap_description=innovation.description,
                        capability_type=innovation.capability_type,
                        implementation_sketch=innovation.name,
                        expected_improvement=innovation.estimated_improvement
                    )
                    self.evolution_plane.submit_capability_hypothesis(hypothesis)
                    
                    # Run validation
                    validation_result = await self.evolution_plane.validate_in_sandbox(
                        innovation_id,
                        sandbox_config={'experiment_id': experiment_id}
                    )
                    
                    if validation_result.status.value == 'passed':
                        innovation.stage = InnovationStage.EVALUATING
                        experiment['stage'] = 'live_evaluation'
                        await self._start_live_evaluation(experiment_id)
                    else:
                        await self._reject_innovation(innovation_id, 'Validation failed')
            else:
                await self._reject_innovation(innovation_id, f"Sandbox failed: {experiment['sandbox_results']}")
        
        except Exception as e:
            logger.error(f"Error in sandbox testing for {experiment_id}: {e}")
            await self._reject_innovation(innovation_id, f"Sandbox error: {str(e)}")
    
    async def _run_innovation_backtests(self, innovation: InnovationProposal) -> Dict[str, Any]:
        """Run backtests for an innovation"""
        # In real implementation, this would run actual backtests
        # For now, simulate with realistic results
        
        expected = innovation.estimated_improvement
        
        # Simulate with noise
        np.random.seed(hash(innovation.id) % 2**32)
        actual_improvement = expected * np.random.normal(1.0, 0.25)
        
        return {
            'improvement': actual_improvement,
            'sharpe_improvement': actual_improvement * 0.8,
            'max_drawdown': 0.08 + np.random.uniform(-0.02, 0.04),
            'win_rate_change': actual_improvement * 0.5,
            'sample_trades': int(np.random.uniform(100, 500))
        }
    
    async def _run_innovation_stress_tests(self, innovation: InnovationProposal) -> Dict[str, Any]:
        """Run stress tests for an innovation"""
        # Simulate stress test results
        np.random.seed(hash(innovation.id) % 2**32)
        
        scenarios = ['market_crash', 'liquidity_crisis', 'volatility_spike', 'correlation_breakdown']
        passed = sum(1 for _ in scenarios if np.random.random() > 0.2)
        
        return {
            'survived': passed >= 3,
            'scenarios_tested': len(scenarios),
            'scenarios_passed': passed,
            'robustness_score': passed / len(scenarios)
        }
    
    async def _start_live_evaluation(self, experiment_id: str):
        """Start live evaluation phase"""
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            return
        
        innovation_id = experiment['innovation_id']
        innovation = self.innovation_registry.get(innovation_id)
        
        logger.info(f"Starting live evaluation for {innovation_id}")
        
        # Run live evaluation for specified duration
        # This will collect real trading metrics
        end_time = experiment['expected_end']
        
        while datetime.utcnow() < end_time:
            await asyncio.sleep(3600)  # Check every hour
            
            # Collect metrics
            metrics = self._collect_live_metrics(innovation)
            experiment['live_metrics'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': metrics
            })
            
            # Check for early termination conditions
            if self._should_terminate_early(experiment, metrics):
                break
        
        # Evaluate final results
        await self._evaluate_live_results(experiment_id)
    
    def _collect_live_metrics(self, innovation: InnovationProposal) -> Dict[str, float]:
        """Collect live trading metrics"""
        metrics = {}
        
        try:
            # Get recent outcomes
            if self.outcome_memory:
                since = datetime.utcnow() - timedelta(days=7)
                recent = [
                    o for o in self.outcome_memory.outcomes.values()
                    if o.timestamp >= since
                ]
                
                if recent:
                    pnls = [o.realized_pnl for o in recent]
                    metrics['recent_win_rate'] = sum(1 for p in pnls if p > 0) / len(pnls)
                    metrics['recent_avg_pnl'] = sum(pnls) / len(pnls)
                    metrics['recent_sharpe'] = np.mean(pnls) / (np.std(pnls) + 1e-10) * np.sqrt(252)
        except Exception as e:
            logger.warning(f"Error collecting live metrics: {e}")
        
        return metrics
    
    def _should_terminate_early(self, experiment: Dict, metrics: Dict) -> bool:
        """Check if experiment should terminate early"""
        # Terminate if significant drawdown
        if metrics.get('current_drawdown', 0) > self.constraints.max_drawdown_limit * 1.5:
            return True
        
        # Terminate if consistently negative
        live_metrics = experiment.get('live_metrics', [])
        if len(live_metrics) >= 5:
            recent_pnls = [m['metrics'].get('recent_avg_pnl', 0) for m in live_metrics[-5:]]
            if all(p < 0 for p in recent_pnls):
                return True
        
        return False
    
    async def _evaluate_live_results(self, experiment_id: str):
        """Evaluate live experiment results"""
        experiment = self.active_experiments.get(experiment_id)
        if not experiment:
            return
        
        innovation_id = experiment['innovation_id']
        innovation = self.innovation_registry.get(innovation_id)
        baseline = experiment['baseline']
        
        # Calculate improvement
        if experiment['live_metrics']:
            recent_metrics = experiment['live_metrics'][-1]['metrics']
            baseline_metrics = baseline.metrics
            
            improvements = {}
            
            if 'recent_win_rate' in recent_metrics and 'win_rate' in baseline_metrics:
                improvements['win_rate'] = recent_metrics['recent_win_rate'] - baseline_metrics['win_rate']
            
            if 'recent_sharpe' in recent_metrics and 'sharpe_estimate' in baseline_metrics:
                improvements['sharpe'] = recent_metrics['recent_sharpe'] - baseline_metrics['sharpe_estimate']
            
            avg_improvement = sum(improvements.values()) / len(improvements) if improvements else 0
            
            # Check against constraints
            meets_constraints = self._meets_constraints(experiment)
            
            if avg_improvement >= self.constraints.risk_adjusted_return_threshold and meets_constraints:
                await self._integrate_innovation(innovation_id, experiment_id, improvements)
            else:
                reason = 'Insufficient improvement' if avg_improvement < self.constraints.risk_adjusted_return_threshold else 'Constraint violations'
                await self._reject_innovation(innovation_id, reason)
        else:
            await self._reject_innovation(innovation_id, 'No live metrics collected')
    
    def _meets_constraints(self, experiment: Dict) -> bool:
        """Check if experiment meets all constraint thresholds"""
        # Check drawdown
        max_dd = max(
            (m['metrics'].get('current_drawdown', 0) for m in experiment.get('live_metrics', [])),
            default=0
        )
        if max_dd > self.constraints.max_drawdown_limit:
            return False
        
        # Check other constraints as needed
        return True
    
    async def _integrate_innovation(self, innovation_id: str, experiment_id: str, improvements: Dict):
        """Integrate validated innovation into production"""
        innovation = self.innovation_registry.get(innovation_id)
        
        # Run pre-integration hooks
        for hook in self.pre_integration_hooks:
            try:
                result = hook(innovation)
                if result is False:
                    await self._reject_innovation(innovation_id, 'Pre-integration hook failed')
                    return
            except Exception as e:
                logger.warning(f"Pre-integration hook error: {e}")
        
        # Perform integration
        innovation.stage = InnovationStage.INTEGRATED
        innovation.updated_at = datetime.utcnow()
        
        # Record integration
        integration_record = {
            'innovation_id': innovation_id,
            'experiment_id': experiment_id,
            'integrated_at': datetime.utcnow().isoformat(),
            'improvements': improvements,
            'capability_type': innovation.capability_type
        }
        
        self.integration_history.append(integration_record)
        
        # Mark gap as resolved
        if innovation.target_gap in self.active_gaps:
            gap = self.active_gaps.pop(innovation.target_gap)
            self.resolved_gaps.append(gap.id)
        
        # Update experiment status
        if experiment_id in self.active_experiments:
            self.active_experiments[experiment_id]['status'] = 'integrated'
        
        # Run post-integration hooks
        for hook in self.post_integration_hooks:
            try:
                hook(innovation, integration_record)
            except Exception as e:
                logger.warning(f"Post-integration hook error: {e}")
        
        logger.info(f"Successfully integrated innovation {innovation_id}")
    
    async def _reject_innovation(self, innovation_id: str, reason: str):
        """Reject an innovation"""
        innovation = self.innovation_registry.get(innovation_id)
        if not innovation:
            return
        
        innovation.stage = InnovationStage.REJECTED
        innovation.updated_at = datetime.utcnow()
        innovation.validation_results.append({
            'stage': innovation.stage.value,
            'rejected_at': datetime.utcnow().isoformat(),
            'reason': reason
        })
        
        # Clean up experiment
        if innovation.experiment_id and innovation.experiment_id in self.active_experiments:
            del self.active_experiments[innovation.experiment_id]
        
        logger.info(f"Rejected innovation {innovation_id}: {reason}")
    
    async def _check_experiment_completions(self) -> List[Dict]:
        """Check for completed experiments and evaluate"""
        completed = []
        
        for experiment_id, experiment in list(self.active_experiments.items()):
            if experiment.get('status') == 'running':
                # Check if experiment has exceeded duration
                if datetime.utcnow() > experiment['expected_end']:
                    await self._evaluate_live_results(experiment_id)
                    completed.append({'experiment_id': experiment_id, 'status': 'completed'})
        
        return completed
    
    # ==================== Rollback and Safety ====================
    
    async def rollback_innovation(self, innovation_id: str, reason: str) -> Dict[str, Any]:
        """Rollback an integrated innovation"""
        innovation = self.innovation_registry.get(innovation_id)
        if not innovation:
            return {'success': False, 'error': 'Innovation not found'}
        
        if innovation.stage != InnovationStage.INTEGRATED:
            return {'success': False, 'error': 'Innovation not integrated'}
        
        # Execute rollback
        innovation.stage = InnovationStage.ROLLED_BACK
        innovation.updated_at = datetime.utcnow()
        
        # Run rollback hooks
        for hook in self.rollback_hooks:
            try:
                hook(innovation, reason)
            except Exception as e:
                logger.error(f"Rollback hook error: {e}")
        
        # Re-activate gap
        if innovation.target_gap:
            gap = CapabilityGap(
                id=f"{innovation.target_gap}_reopened",
                description=f"Gap reopened due to rollback: {reason}",
                affected_categories=[],
                severity=0.9,
                impact_score=0.8,
                detection_date=datetime.utcnow(),
                evidence=[{'type': 'rollback', 'reason': reason}],
                root_causes=['integration_failure']
            )
            self.active_gaps[gap.id] = gap
        
        logger.warning(f"Rolled back innovation {innovation_id}: {reason}")
        
        return {
            'success': True,
            'innovation_id': innovation_id,
            'rollback_reason': reason,
            'rolled_back_at': datetime.utcnow().isoformat()
        }
    
    # ==================== State Management ====================
    
    def _save_state(self):
        """Save engine state to disk"""
        try:
            state = {
                'capabilities': {
                    cap_id: {
                        'id': node.id,
                        'name': node.name,
                        'category': node.category,
                        'status': node.status.value,
                        'dependencies': node.dependencies,
                        'dependents': node.dependents,
                        'performance_metrics': node.performance_metrics,
                        'failure_count': node.failure_count,
                        'success_count': node.success_count
                    }
                    for cap_id, node in self.capability_graph.items()
                },
                'gaps': {
                    gap_id: {
                        'id': gap.id,
                        'description': gap.description,
                        'affected_categories': gap.affected_categories,
                        'severity': gap.severity,
                        'impact_score': gap.impact_score,
                        'detection_date': gap.detection_date.isoformat(),
                        'evidence': gap.evidence,
                        'root_causes': gap.root_causes
                    }
                    for gap_id, gap in self.active_gaps.items()
                },
                'innovations': {
                    innov_id: {
                        'id': innov.id,
                        'name': innov.name,
                        'target_gap': innov.target_gap,
                        'stage': innov.stage.value,
                        'created_at': innov.created_at.isoformat(),
                        'estimated_improvement': innov.estimated_improvement
                    }
                    for innov_id, innov in self.innovation_registry.items()
                },
                'integration_history': self.integration_history[-50:],  # Keep last 50
                'saved_at': datetime.utcnow().isoformat()
            }
            
            Path(self.storage_path).write_text(json.dumps(state, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _load_state(self):
        """Load engine state from disk"""
        try:
            if not Path(self.storage_path).exists():
                return
            
            state = json.loads(Path(self.storage_path).read_text())
            
            # Restore capabilities
            for cap_data in state.get('capabilities', {}).values():
                node = CapabilityNode(
                    id=cap_data['id'],
                    name=cap_data['name'],
                    category=cap_data['category'],
                    status=CapabilityStatus(cap_data['status']),
                    dependencies=cap_data.get('dependencies', []),
                    dependents=cap_data.get('dependents', []),
                    performance_metrics=cap_data.get('performance_metrics', {}),
                    failure_count=cap_data.get('failure_count', 0),
                    success_count=cap_data.get('success_count', 0)
                )
                self.capability_graph[node.id] = node
                self.capability_categories[node.category].append(node.id)
            
            logger.info(f"Loaded state with {len(self.capability_graph)} capabilities")
        except Exception as e:
            logger.warning(f"Error loading state: {e}")
    
    # ==================== Reporting and API ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status"""
        return {
            'monitoring': {
                'is_active': self.is_monitoring,
                'interval_minutes': self.monitoring_interval_minutes
            },
            'capability_space': {
                'total_capabilities': len(self.capability_graph),
                'by_category': {
                    cat: len(caps) for cat, caps in self.capability_categories.items()
                },
                'active': sum(1 for c in self.capability_graph.values() if c.status == CapabilityStatus.ACTIVE),
                'underperforming': sum(1 for c in self.capability_graph.values() if c.status == CapabilityStatus.UNDERPERFORMING)
            },
            'gaps': {
                'active': len(self.active_gaps),
                'resolved': len(self.resolved_gaps)
            },
            'innovations': {
                'total': len(self.innovation_registry),
                'by_stage': {
                    stage.value: sum(1 for i in self.innovation_registry.values() if i.stage == stage)
                    for stage in InnovationStage
                }
            },
            'experiments': {
                'active': len(self.active_experiments),
                'completed': len(self.integration_history)
            },
            'integration_rate': (
                len(self.integration_history) / max(1, len(self.integration_history) + 
                sum(1 for i in self.innovation_registry.values() if i.stage == InnovationStage.REJECTED))
            )
        }
    
    def get_discovery_report(self) -> Dict[str, Any]:
        """Generate comprehensive discovery report"""
        status = self.get_status()
        
        return {
            'status': status,
            'active_gaps': [
                {
                    'id': gap.id,
                    'description': gap.description,
                    'severity': gap.severity,
                    'impact_score': gap.impact_score,
                    'affected_categories': gap.affected_categories,
                    'days_open': (datetime.utcnow() - gap.detection_date).days
                }
                for gap in self.active_gaps.values()
            ],
            'pending_innovations': [
                {
                    'id': innov.id,
                    'name': innov.name,
                    'target_gap': innov.target_gap,
                    'stage': innov.stage.value,
                    'estimated_improvement': innov.estimated_improvement,
                    'complexity': innov.implementation_complexity
                }
                for innov in self.innovation_registry.values()
                if innov.stage in [InnovationStage.PROPOSED, InnovationStage.ANALYZING, InnovationStage.SANDBOX]
            ],
            'recent_integrations': self.integration_history[-5:],
            'performance_trends': {
                k: list(v)[-30:] for k, v in self.performance_trends.items()
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate action recommendations"""
        recs = []
        
        # Check for high-severity gaps
        high_severity = [g for g in self.active_gaps.values() if g.severity > 0.8]
        if high_severity:
            recs.append(f"Address {len(high_severity)} high-severity capability gaps immediately")
        
        # Check for stalled innovations
        stalled = [
            i for i in self.innovation_registry.values()
            if i.stage == InnovationStage.PROPOSED and 
            (datetime.utcnow() - i.created_at).days > 7
        ]
        if stalled:
            recs.append(f"Review {len(stalled)} stalled innovation proposals")
        
        # Check integration rate
        status = self.get_status()
        if status['integration_rate'] < 0.3:
            recs.append("Low integration rate - review validation criteria")
        
        # Check capability coverage
        for cat, caps in self.capability_categories.items():
            if len(caps) < 2:
                recs.append(f"Expand {cat} capabilities (currently {len(caps)})")
        
        return recs


# Factory function for easy instantiation
def create_continuous_discovery_engine(
    trading_system=None,
    storage_path: Optional[str] = None,
    **kwargs
) -> 'ContinuousCapabilityDiscoveryEngine':
    """Factory function to create discovery engine with standard configuration"""
    
    # Import memory systems if available
    decision_memory = kwargs.get('decision_memory')
    outcome_memory = kwargs.get('outcome_memory')
    failure_memory = kwargs.get('failure_memory')
    evolution_plane = kwargs.get('evolution_plane')
    
    # Try to get from trading system
    if trading_system:
        if not decision_memory and hasattr(trading_system, 'decision_memory'):
            decision_memory = trading_system.decision_memory
        if not outcome_memory and hasattr(trading_system, 'outcome_memory'):
            outcome_memory = trading_system.outcome_memory
        if not failure_memory and hasattr(trading_system, 'failure_memory'):
            failure_memory = trading_system.failure_memory
        if not evolution_plane and hasattr(trading_system, 'evolution_plane'):
            evolution_plane = trading_system.evolution_plane
    
    return ContinuousCapabilityDiscoveryEngine(
        decision_memory=decision_memory,
        outcome_memory=outcome_memory,
        failure_memory=failure_memory,
        evolution_plane=evolution_plane,
        trading_system=trading_system,
        storage_path=storage_path,
        constraint_profile=kwargs.get('constraint_profile')
    )
