"""
Capability Discovery Engine (CDE)

Core loop:
Observe performance → detect limitation → generate capability hypothesis → 
implement prototype → test in sandbox → validate statistically → integrate if superior.

A system that discovers WHICH capabilities it lacks.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import logging

from .core_types import CapabilityHypothesis, FailurePattern
from .memory_system import FailureMemory, OutcomeMemory, DecisionMemory
from .plane_evolution import ControlledEvolutionPlane

logger = logging.getLogger(__name__)


@dataclass
class PerformanceObservation:
    """Observation of system performance"""
    timestamp: datetime
    metric_name: str
    value: float
    threshold: float
    passed: bool
    context: Dict[str, Any]


@dataclass
class Limitation:
    """Detected limitation in system capability"""
    id: str
    description: str
    affected_metrics: List[str]
    frequency: int
    severity: float
    first_observed: datetime
    last_observed: datetime


class CapabilityDiscoveryEngine:
    """
    Continuously detects capability gaps and generates hypotheses to address them.
    """
    
    def __init__(
        self,
        failure_memory: FailureMemory,
        outcome_memory: OutcomeMemory,
        decision_memory: DecisionMemory,
        evolution_plane: ControlledEvolutionPlane
    ):
        self.failure_memory = failure_memory
        self.outcome_memory = outcome_memory
        self.decision_memory = decision_memory
        self.evolution_plane = evolution_plane
        
        # Observation tracking
        self.observations: List[PerformanceObservation] = []
        self.detected_limitations: Dict[str, Limitation] = {}
        
        # Capability gap tracking
        self.known_gaps: List[Dict[str, Any]] = []
        self.addressed_gaps: List[str] = []
        
    async def run_discovery_cycle(self) -> Dict[str, Any]:
        """
        Run a complete capability discovery cycle.
        
        Returns:
            Discovery results
        """
        results = {
            'cycle_timestamp': datetime.utcnow().isoformat(),
            'steps': {}
        }
        
        # Step 1: Observe performance
        results['steps']['observation'] = await self._observe_performance()
        
        # Step 2: Detect limitations
        results['steps']['limitation_detection'] = await self._detect_limitations()
        
        # Step 3: Generate capability hypotheses
        results['steps']['hypothesis_generation'] = await self._generate_hypotheses()
        
        # Step 4: Submit to evolution plane
        results['steps']['submission'] = await self._submit_hypotheses()
        
        logger.info("Completed capability discovery cycle")
        
        return results
    
    async def _observe_performance(self) -> Dict[str, Any]:
        """Observe current system performance"""
        
        observations = []
        
        # Observe calibration quality
        calibration = self.outcome_memory.calculate_calibration_metrics()
        observations.append(PerformanceObservation(
            timestamp=datetime.utcnow(),
            metric_name='calibration_brier_score',
            value=calibration.get('brier_score', 0.25),
            threshold=0.15,
            passed=calibration.get('brier_score', 0.25) < 0.15,
            context={'sample_size': calibration.get('sample_size', 0)}
        ))
        
        # Observe win rate
        since = datetime.utcnow() - timedelta(days=30)
        outcomes = [
            o for o in self.outcome_memory.outcomes.values()
            if o.timestamp >= since
        ]
        
        if outcomes:
            win_rate = sum(1 for o in outcomes if o.realized_pnl > 0) / len(outcomes)
            observations.append(PerformanceObservation(
                timestamp=datetime.utcnow(),
                metric_name='win_rate_30d',
                value=win_rate,
                threshold=0.5,
                passed=win_rate >= 0.5,
                context={'sample_size': len(outcomes)}
            ))
            
        # Observe invalidation detection
        invalidation_hits = sum(1 for o in outcomes if o.invalidation_hit)
        if outcomes:
            invalidation_rate = invalidation_hits / len(outcomes)
            observations.append(PerformanceObservation(
                timestamp=datetime.utcnow(),
                metric_name='invalidation_hit_rate',
                value=invalidation_rate,
                threshold=0.2,
                passed=invalidation_rate < 0.2,
                context={'total_invalidations': invalidation_hits}
            ))
            
        self.observations.extend(observations)
        
        # Keep only recent observations
        cutoff = datetime.utcnow() - timedelta(days=30)
        self.observations = [o for o in self.observations if o.timestamp >= cutoff]
        
        return {
            'observations_count': len(observations),
            'passed': sum(1 for o in observations if o.passed),
            'failed': sum(1 for o in observations if not o.passed),
            'metrics': [o.metric_name for o in observations]
        }
    
    async def _detect_limitations(self) -> Dict[str, Any]:
        """Detect limitations from observations and failures"""
        
        limitations = []
        
        # Check failed observations
        failed_obs = [o for o in self.observations if not o.passed]
        
        for obs in failed_obs:
            # Check if this limitation already exists
            existing = self._find_existing_limitation(obs.metric_name)
            
            if existing:
                # Update existing
                existing.frequency += 1
                existing.last_observed = obs.timestamp
                existing.severity = max(existing.severity, self._calculate_severity(obs))
            else:
                # Create new limitation
                new_limitation = Limitation(
                    id=f"lim_{len(self.detected_limitations)}",
                    description=f"System fails to meet {obs.metric_name} threshold",
                    affected_metrics=[obs.metric_name],
                    frequency=1,
                    severity=self._calculate_severity(obs),
                    first_observed=obs.timestamp,
                    last_observed=obs.timestamp
                )
                self.detected_limitations[new_limitation.id] = new_limitation
                limitations.append(new_limitation)
                
        # Also check failure patterns
        patterns = self.failure_memory.get_patterns(min_frequency=2)
        
        for pattern in patterns:
            # Map pattern to limitation
            limitation_desc = f"Recurring {pattern.pattern_name} failures"
            
            existing = next(
                (l for l in self.detected_limitations.values() if l.description == limitation_desc),
                None
            )
            
            if not existing:
                limitation = Limitation(
                    id=f"lim_pattern_{pattern.id[:8]}",
                    description=limitation_desc,
                    affected_metrics=['failure_rate'],
                    frequency=pattern.frequency,
                    severity=pattern.severity,
                    first_observed=datetime.utcnow(),
                    last_observed=datetime.utcnow()
                )
                self.detected_limitations[limitation.id] = limitation
                limitations.append(limitation)
                
        return {
            'limitations_detected': len(limitations),
            'total_known_limitations': len(self.detected_limitations),
            'high_severity': sum(1 for l in limitations if l.severity > 0.7),
            'limitation_descriptions': [l.description for l in limitations]
        }
    
    def _find_existing_limitation(self, metric_name: str) -> Optional[Limitation]:
        """Find existing limitation by metric name"""
        for lim in self.detected_limitations.values():
            if metric_name in lim.affected_metrics:
                return lim
        return None
    
    def _calculate_severity(self, observation: PerformanceObservation) -> float:
        """Calculate severity of a failed observation"""
        
        deviation = abs(observation.value - observation.threshold)
        relative_deviation = deviation / observation.threshold if observation.threshold > 0 else deviation
        
        return min(1.0, relative_deviation)
    
    async def _generate_hypotheses(self) -> Dict[str, Any]:
        """Generate capability hypotheses to address limitations"""
        
        hypotheses = []
        
        # Generate hypotheses from limitations
        for limitation in self.detected_limitations.values():
            # Skip if already being addressed
            if limitation.id in self.addressed_gaps:
                continue
                
            hypothesis = self._generate_hypothesis_for_limitation(limitation)
            if hypothesis:
                hypotheses.append(hypothesis)
                
        # Generate hypotheses from capability gaps
        gaps = self.failure_memory.generate_capability_gaps()
        
        for gap in gaps:
            if gap['pattern_id'] in self.addressed_gaps:
                continue
                
            hypothesis = CapabilityHypothesis(
                id=f"hyp_gap_{gap['pattern_id'][:8]}",
                gap_description=gap['description'],
                capability_type=gap['required_capability'],
                implementation_sketch=self._sketch_implementation(gap['required_capability']),
                expected_improvement=gap['priority'] * 0.1
            )
            hypotheses.append(hypothesis)
            
        return {
            'hypotheses_generated': len(hypotheses),
            'from_limitations': sum(1 for h in hypotheses if h.id.startswith('hyp_lim')),
            'from_gaps': sum(1 for h in hypotheses if h.id.startswith('hyp_gap')),
            'hypothesis_types': list(set(h.capability_type for h in hypotheses))
        }
    
    def _generate_hypothesis_for_limitation(
        self,
        limitation: Limitation
    ) -> Optional[CapabilityHypothesis]:
        """Generate a hypothesis to address a limitation"""
        
        # Map limitation to capability type
        capability_map = {
            'calibration_brier_score': 'calibration_model',
            'win_rate_30d': 'signal_quality',
            'invalidation_hit_rate': 'risk_management',
            'failure_rate': 'systematic_improvement'
        }
        
        for metric, capability_type in capability_map.items():
            if metric in limitation.affected_metrics:
                return CapabilityHypothesis(
                    id=f"hyp_lim_{limitation.id}",
                    gap_description=limitation.description,
                    capability_type=capability_type,
                    implementation_sketch=self._sketch_implementation(capability_type),
                    expected_improvement=limitation.severity * 0.15
                )
                
        return None
    
    def _sketch_implementation(self, capability_type: str) -> str:
        """Generate implementation sketch for capability type"""
        
        sketches = {
            'calibration_model': 'Implement temperature scaling or isotonic regression',
            'signal_quality': 'Add feature engineering or improve signal aggregation',
            'risk_management': 'Enhance position sizing or add stop-loss logic',
            'systematic_improvement': 'Add new validation layers or improve regime detection',
            'real_time_invalidation_monitoring': 'Add streaming invalidation checks',
            'better_calibration_system': 'Implement Bayesian calibration methods',
            'improved_regime_detection': 'Add HMM or clustering-based regime detection',
            'enhanced_counterfactual_testing': 'Increase scenario coverage',
            'better_execution_modeling': 'Add market impact models',
            'additional_feature_discovery': 'Run automated feature engineering'
        }
        
        return sketches.get(capability_type, f"Research implementation for {capability_type}")
    
    async def _submit_hypotheses(self) -> Dict[str, Any]:
        """Submit hypotheses to evolution plane for validation"""
        
        submitted = []
        
        # Get recently generated hypotheses from registry
        for hypothesis in self.evolution_plane.capability_registry.values():
            if not hypothesis.tested and not hypothesis.promoted:
                submitted.append(hypothesis.id)
                
        return {
            'submitted_to_evolution': len(submitted),
            'awaiting_validation': len(submitted),
            'in_promotion_pipeline': sum(
                1 for h in self.evolution_plane.capability_registry.values()
                if h.tested and not h.promoted
            )
        }
    
    def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get metrics about capability discovery"""
        
        return {
            'observations_tracked': len(self.observations),
            'limitation_count': len(self.detected_limitations),
            'high_severity_limitations': sum(
                1 for l in self.detected_limitations.values() if l.severity > 0.7
            ),
            'addressed_gaps': len(self.addressed_gaps),
            'pending_hypotheses': sum(
                1 for h in self.evolution_plane.capability_registry.values()
                if not h.tested
            )
        }
        
    def generate_discovery_report(self) -> Dict[str, Any]:
        """Generate comprehensive discovery report"""
        
        return {
            'metrics': self.get_discovery_metrics(),
            'active_limitations': [
                {
                    'id': l.id,
                    'description': l.description,
                    'severity': l.severity,
                    'frequency': l.frequency,
                    'days_active': (datetime.utcnow() - l.first_observed).days
                }
                for l in self.detected_limitations.values()
                if l.id not in self.addressed_gaps
            ],
            'recent_observations': [
                {
                    'metric': o.metric_name,
                    'value': o.value,
                    'passed': o.passed,
                    'timestamp': o.timestamp.isoformat()
                }
                for o in self.observations[-10:]
            ],
            'evolution_status': self.evolution_plane.get_evolution_status()
        }


class CapabilityDiscoveryAndIntegrationEngine:
    """
    Capability Discovery and Integration Engine
    
    A system that continuously maps its own capability space, detects missing 
    capabilities, generates targeted innovations, and integrates only those that 
    produce robust, measurable improvements under real-world constraints.
    
    Core Functions:
    1. Capability Space Mapping - Continuous inventory of system capabilities
    2. Gap Detection - Identify missing or weak capabilities
    3. Innovation Generation - Create targeted solutions for detected gaps
    4. Validation & Integration - Test and integrate only proven improvements
    
    Philosophy:
    - Evolution over revolution: Incremental, measurable improvements
    - Constraint-aware: All innovations validated under real trading conditions
    - Evidence-based: Only integrate capabilities with statistical significance
    - Self-monitoring: Track its own effectiveness and adapt
    """
    
    def __init__(self, trading_system: Any):
        self.trading_system = trading_system
        
        # Capability space mapping
        self.capability_registry: Dict[str, Dict[str, Any]] = {}
        self.capability_graph: Dict[str, List[str]] = {}  # dependency graph
        self.performance_baselines: Dict[str, float] = {}
        
        # Gap detection
        self.detected_gaps: List[Dict[str, Any]] = []
        self.gap_severity_scores: Dict[str, float] = {}
        
        # Innovation pipeline
        self.innovation_queue: List[Dict[str, Any]] = []
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.experiment_results: Dict[str, List[Dict[str, Any]]] = {}
        
        # Integration tracking
        self.integrated_innovations: List[Dict[str, Any]] = []
        self.rejected_innovations: List[Dict[str, Any]] = []
        
        # Performance thresholds
        self.min_improvement_threshold = 0.05  # 5% minimum improvement
        self.confidence_threshold = 0.95
        self.max_experiment_duration_days = 30
        
        logger.info("CapabilityDiscoveryAndIntegrationEngine initialized")
    
    def map_capability_space(self) -> Dict[str, Any]:
        """
        Map current capability space by discovering all available capabilities
        in the trading system.
        
        Returns:
            Comprehensive capability map with coverage metrics
        """
        discovered_capabilities = {
            'signal_generation': self._detect_signal_capabilities(),
            'risk_management': self._detect_risk_capabilities(),
            'execution': self._detect_execution_capabilities(),
            'portfolio_management': self._detect_portfolio_capabilities(),
            'market_analysis': self._detect_analysis_capabilities(),
            'decision_governance': self._detect_governance_capabilities()
        }
        
        # Calculate coverage metrics
        total_categories = len(discovered_capabilities)
        populated_categories = sum(
            1 for caps in discovered_capabilities.values() if caps
        )
        
        # Identify capability density
        capability_counts = {
            cat: len(caps) for cat, caps in discovered_capabilities.items()
        }
        
        # Update registry
        self.capability_registry = discovered_capabilities
        
        return {
            'capability_categories': discovered_capabilities,
            'coverage_ratio': populated_categories / total_categories if total_categories > 0 else 0,
            'total_capabilities': sum(capability_counts.values()),
            'capability_density_by_category': capability_counts,
            'sparse_categories': [
                cat for cat, count in capability_counts.items() if count < 3
            ],
            'recommendation': self._generate_capability_recommendation(capability_counts)
        }
    
    def _detect_signal_capabilities(self) -> List[str]:
        """Detect available signal generation capabilities."""
        # Scan orchestrator.py for signal classes
        capabilities = []
        try:
            from trading_bot.signal_discovery.orchestrator import (
                SignalDependencyGraph, StrategyDNAMapper, SystemHealthMonitor,
                DecisionEntropyMonitor, OptionsImpliedEdgeCalculator,
                CrossAssetMomentumLeader, TermStructureRollOptimizer,
                CalendarSpreadSelector, EdgeHalfLifeEngine, SignalFragilityIndex,
                EdgeSaturationDetector, EdgeReinforcementEngine
            )
            capabilities = [
                'SignalDependencyGraph', 'StrategyDNAMapper', 'SystemHealthMonitor',
                'DecisionEntropyMonitor', 'OptionsImpliedEdgeCalculator',
                'CrossAssetMomentumLeader', 'TermStructureRollOptimizer',
                'CalendarSpreadSelector', 'EdgeHalfLifeEngine', 'SignalFragilityIndex',
                'EdgeSaturationDetector', 'EdgeReinforcementEngine'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _detect_risk_capabilities(self) -> List[str]:
        """Detect available risk management capabilities."""
        capabilities = []
        try:
            from trading_bot.risk.drawdown_protector import (
                AdaptiveRiskCompressor, MaximumAdverseExcursionTracker,
                StrategyCapacityLimiter, EarningsEventRiskManager,
                LiquidityAdjustedVaR, CorporateActionAdjustor
            )
            capabilities = [
                'AdaptiveRiskCompressor', 'MaximumAdverseExcursionTracker',
                'StrategyCapacityLimiter', 'EarningsEventRiskManager',
                'LiquidityAdjustedVaR', 'CorporateActionAdjustor'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _detect_execution_capabilities(self) -> List[str]:
        """Detect available execution capabilities."""
        capabilities = []
        try:
            from trading_bot.execution.smart_execution import (
                TradeKillSwitchPredictor, ExecutionAlphaExtractor,
                ExecutionTimingOptimizer, DecisionLatencyOptimizer,
                MarketImpactEstimator, OrderFlowToxicityDetector,
                CrossExchangeLiquidityRouter
            )
            from trading_bot.execution.liquidity_analyzer import (
                LiquidityVacuumDetector, ExecutionStressIndex,
                StructuralLiquidityMap, InventorySkewRiskManager,
                FundingRateArbitrageMonitor, CointegrationBreakdownDetector
            )
            capabilities = [
                'TradeKillSwitchPredictor', 'ExecutionAlphaExtractor',
                'ExecutionTimingOptimizer', 'DecisionLatencyOptimizer',
                'MarketImpactEstimator', 'OrderFlowToxicityDetector',
                'CrossExchangeLiquidityRouter', 'LiquidityVacuumDetector',
                'ExecutionStressIndex', 'StructuralLiquidityMap',
                'InventorySkewRiskManager', 'FundingRateArbitrageMonitor',
                'CointegrationBreakdownDetector'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _detect_portfolio_capabilities(self) -> List[str]:
        """Detect available portfolio management capabilities."""
        capabilities = []
        try:
            from trading_bot.portfolio.portfolio_optimizer import (
                EdgePortfolioManager, EdgeOrthogonalityAnalyzer,
                PositionSizingOptimizer
            )
            capabilities = [
                'EdgePortfolioManager', 'EdgeOrthogonalityAnalyzer',
                'PositionSizingOptimizer'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _detect_analysis_capabilities(self) -> List[str]:
        """Detect available market analysis capabilities."""
        capabilities = []
        try:
            from trading_bot.decision_governance.layer4_regime_engine import (
                VolatilityRegimeDetector, CorrelationStressTester,
                FatTailRiskCalculator, IntradaySeasonalityAnalyzer,
                RegimeTransitionEarlyWarning
            )
            from trading_bot.decision_governance.causal_attribution import (
                CausalDriverIsolationEngine
            )
            capabilities = [
                'VolatilityRegimeDetector', 'CorrelationStressTester',
                'FatTailRiskCalculator', 'IntradaySeasonalityAnalyzer',
                'RegimeTransitionEarlyWarning', 'CausalDriverIsolationEngine'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _detect_governance_capabilities(self) -> List[str]:
        """Detect available governance capabilities."""
        capabilities = []
        try:
            from trading_bot.decision_governance.core_types import (
                OpportunityCostEngine, CapitalSurvivalPriorityEngine
            )
            from trading_bot.decision_governance.layer6_uncertainty import (
                ConfidenceCalibrationEngine, MetaUncertaintyController
            )
            from trading_bot.decision_governance.layer3_adversarial_analyst import (
                CognitiveBiasDetector
            )
            from trading_bot.decision_governance.layer5_counterfactual import (
                MetaStrategySelector, FailureReplayEngine
            )
            from trading_bot.decision_governance.diagnostic_engine import (
                SelfCorrectionEngine
            )
            capabilities = [
                'OpportunityCostEngine', 'CapitalSurvivalPriorityEngine',
                'ConfidenceCalibrationEngine', 'MetaUncertaintyController',
                'CognitiveBiasDetector', 'MetaStrategySelector',
                'FailureReplayEngine', 'SelfCorrectionEngine'
            ]
        except ImportError:
            pass
        return capabilities
    
    def _generate_capability_recommendation(self, counts: Dict[str, int]) -> str:
        """Generate recommendation based on capability coverage."""
        min_count = min(counts.values()) if counts else 0
        min_category = min(counts.items(), key=lambda x: x[1])[0] if counts else 'unknown'
        
        if min_count < 3:
            return f"Priority: Expand {min_category} capabilities"
        elif sum(counts.values()) < 20:
            return "Moderate: Continue capability expansion"
        else:
            return "Good: Capability space well-covered, focus on integration"
    
    def detect_capability_gaps(self) -> List[Dict[str, Any]]:
        """
        Detect gaps in capability space by analyzing:
        - Missing capability categories
        - Underperforming existing capabilities
        - Capability dependencies without implementations
        
        Returns:
            List of detected gaps with severity scores
        """
        gaps = []
        
        # Map current space
        space = self.map_capability_space()
        categories = space.get('capability_categories', {})
        
        # Detect sparse categories
        for category, caps in categories.items():
            if len(caps) < 3:
                gaps.append({
                    'type': 'sparse_category',
                    'category': category,
                    'current_count': len(caps),
                    'target_count': 5,
                    'severity': 0.7 if len(caps) == 0 else 0.4,
                    'rationale': f"Category {category} has insufficient coverage"
                })
        
        # Detect missing cross-cutting concerns
        if categories:
            all_caps = [cap for caps in categories.values() for cap in caps]
            
            # Check for monitoring gaps
            monitoring_caps = [c for c in all_caps if 'Monitor' in c or 'Tracker' in c]
            if len(monitoring_caps) < 3:
                gaps.append({
                    'type': 'missing_monitoring',
                    'current_monitors': monitoring_caps,
                    'severity': 0.6,
                    'rationale': 'Insufficient real-time monitoring capabilities'
                })
            
            # Check for optimization gaps
            opt_caps = [c for c in all_caps if 'Optimizer' in c or 'Optimal' in c]
            if len(opt_caps) < 2:
                gaps.append({
                    'type': 'missing_optimization',
                    'current_optimizers': opt_caps,
                    'severity': 0.5,
                    'rationale': 'Limited optimization capabilities'
                })
        
        # Store detected gaps
        self.detected_gaps = gaps
        self.gap_severity_scores = {f"gap_{i}": g['severity'] for i, g in enumerate(gaps)}
        
        return gaps
    
    def generate_targeted_innovation(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a targeted innovation to address a specific capability gap.
        
        Args:
            gap: Detected gap dictionary
            
        Returns:
            Innovation proposal with implementation plan
        """
        gap_type = gap.get('type', '')
        
        # Innovation templates by gap type
        innovation_templates = {
            'sparse_category': {
                'signal_generation': {
                    'name': 'DynamicSignalWeightOptimizer',
                    'description': 'Automatically optimize signal weights based on real-time performance',
                    'complexity': 'medium',
                    'expected_improvement': 0.08,
                    'test_duration_days': 14
                },
                'risk_management': {
                    'name': 'RealTimeRiskBudgetAllocator',
                    'description': 'Dynamically allocate risk budgets across strategies based on edge detection',
                    'complexity': 'high',
                    'expected_improvement': 0.12,
                    'test_duration_days': 21
                },
                'execution': {
                    'name': 'MicrostructureMomentumDetector',
                    'description': 'Detect microstructure momentum shifts before price moves',
                    'complexity': 'high',
                    'expected_improvement': 0.15,
                    'test_duration_days': 21
                },
                'portfolio_management': {
                    'name': 'AdaptiveCorrelationHedger',
                    'description': 'Dynamically hedge correlation breakdown risks',
                    'complexity': 'high',
                    'expected_improvement': 0.10,
                    'test_duration_days': 28
                },
                'market_analysis': {
                    'name': 'RegimeTransitionPredictor',
                    'description': 'Predict regime transitions 1-3 days in advance',
                    'complexity': 'very_high',
                    'expected_improvement': 0.18,
                    'test_duration_days': 30
                },
                'decision_governance': {
                    'name': 'MultiObjectiveDecisionOptimizer',
                    'description': 'Balance profit, risk, and capacity in multi-objective framework',
                    'complexity': 'high',
                    'expected_improvement': 0.09,
                    'test_duration_days': 21
                }
            },
            'missing_monitoring': {
                'name': 'ComprehensiveSystemMonitor',
                'description': 'Unified monitoring of all system health metrics with predictive alerts',
                'complexity': 'medium',
                'expected_improvement': 0.06,
                'test_duration_days': 14
            },
            'missing_optimization': {
                'name': 'MultiStrategyParameterOptimizer',
                'description': 'Optimize parameters across multiple strategies simultaneously',
                'complexity': 'high',
                'expected_improvement': 0.11,
                'test_duration_days': 21
            }
        }
        
        # Select appropriate innovation
        if gap_type in innovation_templates:
            if gap_type == 'sparse_category':
                category = gap.get('category', '')
                template = innovation_templates[gap_type].get(category, {
                    'name': f"{category}GapFiller",
                    'description': f"Fill capability gap in {category}",
                    'complexity': 'medium',
                    'expected_improvement': 0.05,
                    'test_duration_days': 14
                })
            else:
                template = innovation_templates[gap_type]
        else:
            template = {
                'name': 'GenericGapFiller',
                'description': f"Address gap: {gap.get('rationale', 'Unknown')}",
                'complexity': 'medium',
                'expected_improvement': 0.05,
                'test_duration_days': 14
            }
        
        innovation = {
            'id': f"innov_{datetime.now().strftime('%Y%m%d%H%M%S')}_{gap_type}",
            'target_gap': gap,
            'name': template['name'],
            'description': template['description'],
            'complexity': template['complexity'],
            'expected_improvement': template['expected_improvement'],
            'test_duration_days': template['test_duration_days'],
            'status': 'proposed',
            'created_at': datetime.now()
        }
        
        # Add to queue
        self.innovation_queue.append(innovation)
        
        return innovation
    
    def validate_and_integrate(self, innovation_id: str) -> Dict[str, Any]:
        """
        Validate an innovation through controlled experimentation
        and integrate if it meets performance thresholds.
        
        Args:
            innovation_id: ID of innovation to validate
            
        Returns:
            Integration result with performance metrics
        """
        # Find innovation
        innovation = next(
            (i for i in self.innovation_queue if i['id'] == innovation_id),
            None
        )
        
        if not innovation:
            return {'status': 'not_found', 'innovation_id': innovation_id}
        
        # Start experiment
        experiment_id = f"exp_{innovation_id}"
        
        self.active_experiments[experiment_id] = {
            'innovation': innovation,
            'start_date': datetime.now(),
            'baseline_metrics': self._capture_baseline_metrics(),
            'experiment_metrics': [],
            'status': 'running'
        }
        
        return {
            'status': 'experiment_started',
            'experiment_id': experiment_id,
            'innovation': innovation,
            'expected_completion': datetime.now() + timedelta(days=innovation['test_duration_days']),
            'next_action': f"Run experiment for {innovation['test_duration_days']} days then evaluate"
        }
    
    def _capture_baseline_metrics(self) -> Dict[str, float]:
        """Capture current system performance as baseline."""
        return {
            'sharpe_ratio': 1.5,  # Placeholder - would come from actual system
            'win_rate': 0.55,
            'avg_return_per_trade': 0.001,
            'max_drawdown': 0.10,
            'calmar_ratio': 1.2,
            'capacity_utilization': 0.6
        }
    
    def evaluate_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        Evaluate experiment results and decide on integration.
        
        Args:
            experiment_id: Experiment to evaluate
            
        Returns:
            Evaluation result with integration decision
        """
        experiment = self.active_experiments.get(experiment_id)
        
        if not experiment:
            return {'status': 'experiment_not_found'}
        
        innovation = experiment['innovation']
        baseline = experiment['baseline_metrics']
        
        # Simulate experiment results (in real implementation, would be actual measurements)
        # For now, use expected improvement with some noise
        np.random.seed(hash(experiment_id) % 2**32)
        actual_improvement = innovation['expected_improvement'] * np.random.normal(1.0, 0.3)
        
        # Calculate statistical significance (simplified)
        confidence = 0.95 if actual_improvement > innovation['expected_improvement'] * 0.8 else 0.80
        
        # Decision
        if actual_improvement >= self.min_improvement_threshold and confidence >= self.confidence_threshold:
            decision = 'INTEGRATE'
            self.integrated_innovations.append({
                'experiment_id': experiment_id,
                'innovation': innovation,
                'actual_improvement': actual_improvement,
                'confidence': confidence,
                'integrated_at': datetime.now()
            })
        elif actual_improvement > 0:
            decision = 'EXTEND_TEST'
        else:
            decision = 'REJECT'
            self.rejected_innovations.append({
                'experiment_id': experiment_id,
                'innovation': innovation,
                'actual_improvement': actual_improvement,
                'reason': 'Insufficient improvement or negative results'
            })
        
        # Update experiment status
        experiment['status'] = 'completed'
        experiment['results'] = {
            'actual_improvement': actual_improvement,
            'confidence': confidence,
            'decision': decision
        }
        
        return {
            'experiment_id': experiment_id,
            'innovation_name': innovation['name'],
            'baseline_metrics': baseline,
            'actual_improvement': actual_improvement,
            'expected_improvement': innovation['expected_improvement'],
            'confidence': confidence,
            'decision': decision,
            'reason': 'Meets thresholds' if decision == 'INTEGRATE' else 'Insufficient evidence' if decision == 'EXTEND_TEST' else 'Negative results'
        }
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive status of capability discovery and integration."""
        return {
            'capability_space': self.map_capability_space(),
            'detected_gaps': len(self.detected_gaps),
            'gap_details': self.detected_gaps,
            'innovation_queue': len(self.innovation_queue),
            'active_experiments': len(self.active_experiments),
            'completed_experiments': len([e for e in self.active_experiments.values() if e.get('status') == 'completed']),
            'integrated_innovations': len(self.integrated_innovations),
            'rejected_innovations': len(self.rejected_innovations),
            'integration_rate': (
                len(self.integrated_innovations) / max(1, len(self.integrated_innovations) + len(self.rejected_innovations))
            ),
            'recent_integrations': self.integrated_innovations[-5:],
            'system_health': 'evolving' if len(self.integrated_innovations) > 5 else 'developing'
        }
    
    def run_continuous_discovery_cycle(self) -> Dict[str, Any]:
        """
        Run one full cycle of continuous discovery:
        1. Map capability space
        2. Detect gaps
        3. Generate innovations
        4. Start validations
        
        Returns:
            Cycle summary
        """
        # Step 1: Map space
        space = self.map_capability_space()
        
        # Step 2: Detect gaps
        gaps = self.detect_capability_gaps()
        
        # Step 3: Generate innovations for high-severity gaps
        innovations = []
        for gap in gaps:
            if gap['severity'] > 0.5:
                innovation = self.generate_targeted_innovation(gap)
                innovations.append(innovation)
        
        # Step 4: Start validations for top innovations
        started_experiments = []
        for innovation in innovations[:3]:  # Start top 3
            result = self.validate_and_integrate(innovation['id'])
            if result['status'] == 'experiment_started':
                started_experiments.append(result)
        
        return {
            'cycle_timestamp': datetime.now(),
            'capabilities_mapped': space['total_capabilities'],
            'gaps_detected': len(gaps),
            'innovations_generated': len(innovations),
            'experiments_started': len(started_experiments),
            'cycle_complete': True,
            'next_cycle_recommended': datetime.now() + timedelta(days=7)
        }
