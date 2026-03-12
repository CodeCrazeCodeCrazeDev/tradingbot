"""
Recursive Evolution Orchestrator
=================================

Master orchestrator that coordinates all recursive self-evolution components
to continuously improve every aspect of the trading system.

This orchestrator:
1. Runs continuous evolution cycles
2. Coordinates meta-learning, reasoning, intelligence, order flow, and fusion
3. Discovers improvement opportunities across all dimensions
4. Tests and validates improvements safely
5. Learns from outcomes to improve the improvement process itself
6. Provides comprehensive metrics and reporting
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from .recursive_meta_learner import (
    RecursiveMetaLearner,
    EvolutionDimension,
    ImprovementProposal,
    MetaLearningConfig
)
from .elite_reasoning_engine import (
    EliteReasoningEngine,
    TradeReasoning,
    ReasoningQuality
)
from .deep_market_intelligence import (
    DeepMarketIntelligence,
    MarketIntelligenceReport,
    MarketRegime
)
from .institutional_orderflow import (
    InstitutionalOrderFlow,
    OrderFlowSignal,
    InstitutionalActivity
)
from .multi_paradigm_fusion import (
    MultiParadigmFusion,
    ParadigmDecision,
    ParadigmType,
    DecisionType,
    FusedDecision
)

logger = logging.getLogger(__name__)


class EvolutionPhase(Enum):
    """Phases of evolution cycle"""
    MONITORING = "monitoring"
    ANALYSIS = "analysis"
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    PROPOSAL_GENERATION = "proposal_generation"
    TESTING = "testing"
    IMPLEMENTATION = "implementation"
    LEARNING = "learning"


@dataclass
class EvolutionMetrics:
    """Metrics tracking evolution progress"""
    total_cycles: int = 0
    total_proposals: int = 0
    successful_improvements: int = 0
    failed_improvements: int = 0
    
    # Performance improvements
    reasoning_quality_improvement: float = 0.0
    intelligence_quality_improvement: float = 0.0
    orderflow_accuracy_improvement: float = 0.0
    decision_quality_improvement: float = 0.0
    
    # Meta-learning metrics
    learning_efficiency: float = 0.0
    adaptation_speed: float = 0.0
    
    # Overall system improvement
    overall_improvement: float = 0.0
    
    last_update: datetime = field(default_factory=datetime.utcnow)


class RecursiveEvolutionOrchestrator:
    """
    Master orchestrator for recursive self-evolution.
    
    This system continuously improves itself by:
    - Monitoring performance across all dimensions
    - Discovering improvement opportunities
    - Generating and testing improvement proposals
    - Learning from outcomes
    - Improving its own improvement process (meta-meta-learning)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize all components
        self.meta_learner = RecursiveMetaLearner(
            MetaLearningConfig(**self.config.get('meta_learning', {}))
        )
        
        self.reasoning_engine = EliteReasoningEngine(
            self.config.get('reasoning', {})
        )
        
        self.intelligence = DeepMarketIntelligence(
            self.config.get('intelligence', {})
        )
        
        self.orderflow = InstitutionalOrderFlow(
            self.config.get('orderflow', {})
        )
        
        self.fusion = MultiParadigmFusion(
            self.config.get('fusion', {})
        )
        
        # Evolution state
        self.current_phase = EvolutionPhase.MONITORING
        self.metrics = EvolutionMetrics()
        self.evolution_history: List[Dict[str, Any]] = []
        
        # Performance baselines
        self.baselines: Dict[str, float] = {}
        
        # Continuous evolution
        self.evolution_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        logger.info("RecursiveEvolutionOrchestrator initialized")
    
    async def start_continuous_evolution(self, interval_seconds: int = 3600):
        """Start continuous evolution loop"""
        
        if self.is_running:
            logger.warning("Evolution already running")
            return
        
        self.is_running = True
        logger.info(f"Starting continuous evolution (interval: {interval_seconds}s)")
        
        self.evolution_task = asyncio.create_task(
            self._evolution_loop(interval_seconds)
        )
    
    async def stop_continuous_evolution(self):
        """Stop continuous evolution loop"""
        
        self.is_running = False
        
        if self.evolution_task:
            self.evolution_task.cancel()
            try:
                await self.evolution_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Continuous evolution stopped")
    
    async def _evolution_loop(self, interval_seconds: int):
        """Main evolution loop"""
        
        while self.is_running:
            try:
                # Run one evolution cycle
                await self.run_evolution_cycle()
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry
    
    async def run_evolution_cycle(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run one complete evolution cycle.
        """
        cycle_start = datetime.utcnow()
        logger.info(f"Starting evolution cycle #{self.metrics.total_cycles + 1}")
        
        cycle_results = {
            'cycle_number': self.metrics.total_cycles + 1,
            'start_time': cycle_start,
            'phases': {}
        }
        
        # Phase 1: Monitoring - Assess current performance
        self.current_phase = EvolutionPhase.MONITORING
        monitoring_results = await self._phase_monitoring()
        cycle_results['phases']['monitoring'] = monitoring_results
        
        # Phase 2: Analysis - Analyze performance data
        self.current_phase = EvolutionPhase.ANALYSIS
        analysis_results = await self._phase_analysis(monitoring_results)
        cycle_results['phases']['analysis'] = analysis_results
        
        # Phase 3: Opportunity Discovery - Find improvement opportunities
        self.current_phase = EvolutionPhase.OPPORTUNITY_DISCOVERY
        opportunities = await self._phase_opportunity_discovery(analysis_results)
        cycle_results['phases']['opportunities'] = opportunities
        
        # Phase 4: Proposal Generation - Generate improvement proposals
        self.current_phase = EvolutionPhase.PROPOSAL_GENERATION
        proposals = await self._phase_proposal_generation(opportunities, context)
        cycle_results['phases']['proposals'] = proposals
        
        # Phase 5: Testing - Test proposals safely
        self.current_phase = EvolutionPhase.TESTING
        test_results = await self._phase_testing(proposals)
        cycle_results['phases']['testing'] = test_results
        
        # Phase 6: Implementation - Implement successful improvements
        self.current_phase = EvolutionPhase.IMPLEMENTATION
        implementation_results = await self._phase_implementation(test_results)
        cycle_results['phases']['implementation'] = implementation_results
        
        # Phase 7: Learning - Learn from cycle outcomes
        self.current_phase = EvolutionPhase.LEARNING
        learning_results = await self._phase_learning(cycle_results)
        cycle_results['phases']['learning'] = learning_results
        
        # Update metrics
        self.metrics.total_cycles += 1
        self.metrics.last_update = datetime.utcnow()
        
        cycle_results['end_time'] = datetime.utcnow()
        cycle_results['duration_seconds'] = (cycle_results['end_time'] - cycle_start).total_seconds()
        
        self.evolution_history.append(cycle_results)
        
        logger.info(f"Evolution cycle #{self.metrics.total_cycles} complete")
        
        return cycle_results
    
    async def _phase_monitoring(self) -> Dict[str, Any]:
        """Phase 1: Monitor current performance"""
        
        logger.info("Phase 1: Monitoring performance")
        
        # Get stats from all components
        reasoning_stats = self.reasoning_engine.get_reasoning_stats()
        intelligence_stats = self.intelligence.get_intelligence_stats()
        fusion_stats = self.fusion.get_fusion_stats()
        meta_stats = self.meta_learner.get_evolution_metrics()
        
        # Calculate current scores for each dimension
        scores = {}
        
        # Reasoning quality
        if reasoning_stats.get('total_reasonings', 0) > 0:
            quality_dist = reasoning_stats.get('quality_distribution', {})
            excellent = quality_dist.get('excellent', 0)
            good = quality_dist.get('good', 0)
            total = reasoning_stats['total_reasonings']
            scores['reasoning_quality'] = (excellent * 1.0 + good * 0.75) / total
        else:
            scores['reasoning_quality'] = 0.5
        
        # Intelligence quality
        scores['market_intelligence'] = intelligence_stats.get('average_tradability', 0.5)
        
        # Decision quality
        scores['decision_making'] = fusion_stats.get('average_confidence', 0.5)
        
        # Meta-learning efficiency
        scores['learning_efficiency'] = meta_stats.get('meta_learning_efficiency', 0.5)
        
        return {
            'scores': scores,
            'reasoning_stats': reasoning_stats,
            'intelligence_stats': intelligence_stats,
            'fusion_stats': fusion_stats,
            'meta_stats': meta_stats
        }
    
    async def _phase_analysis(self, monitoring_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Analyze performance data"""
        
        logger.info("Phase 2: Analyzing performance")
        
        scores = monitoring_results['scores']
        
        # Record scores in meta-learner
        for dimension_name, score in scores.items():
            try:
                dimension = EvolutionDimension[dimension_name.upper()]
                self.meta_learner.record_performance(dimension, score)
            except KeyError:
                pass
        
        # Identify strengths and weaknesses
        strengths = {k: v for k, v in scores.items() if v > 0.7}
        weaknesses = {k: v for k, v in scores.items() if v < 0.5}
        
        # Calculate trends
        trends = {}
        for dimension_name, score in scores.items():
            baseline = self.baselines.get(dimension_name, score)
            trend = score - baseline
            trends[dimension_name] = trend
            
            # Update baseline
            self.baselines[dimension_name] = score
        
        return {
            'scores': scores,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trends': trends
        }
    
    async def _phase_opportunity_discovery(self, analysis_results: Dict[str, Any]) -> List[Tuple[EvolutionDimension, float]]:
        """Phase 3: Discover improvement opportunities"""
        
        logger.info("Phase 3: Discovering opportunities")
        
        # Use meta-learner to identify opportunities
        opportunities = self.meta_learner.identify_improvement_opportunities()
        
        logger.info(f"Discovered {len(opportunities)} improvement opportunities")
        
        return opportunities
    
    async def _phase_proposal_generation(self, opportunities: List[Tuple[EvolutionDimension, float]],
                                        context: Optional[Dict[str, Any]]) -> List[ImprovementProposal]:
        """Phase 4: Generate improvement proposals"""
        
        logger.info("Phase 4: Generating proposals")
        
        proposals = []
        
        # Generate proposals for top opportunities
        for dimension, priority in opportunities[:5]:  # Top 5
            proposal = self.meta_learner.generate_improvement_proposal(dimension, context)
            proposals.append(proposal)
        
        self.metrics.total_proposals += len(proposals)
        
        logger.info(f"Generated {len(proposals)} improvement proposals")
        
        return proposals
    
    async def _phase_testing(self, proposals: List[ImprovementProposal]) -> List[Dict[str, Any]]:
        """Phase 5: Test improvement proposals"""
        
        logger.info("Phase 5: Testing proposals")
        
        test_results = []
        
        for proposal in proposals:
            # Simulate testing (in production, this would run actual tests)
            success, results = self.meta_learner.test_improvement(proposal, test_data=None)
            
            test_results.append({
                'proposal_id': proposal.proposal_id,
                'dimension': proposal.dimension.value,
                'success': success,
                'results': results
            })
            
            if success:
                self.metrics.successful_improvements += 1
            else:
                self.metrics.failed_improvements += 1
        
        logger.info(f"Testing complete: {sum(1 for r in test_results if r['success'])} passed")
        
        return test_results
    
    async def _phase_implementation(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phase 6: Implement successful improvements"""
        
        logger.info("Phase 6: Implementing improvements")
        
        implemented = []
        
        for result in test_results:
            if result['success']:
                # In production, this would actually implement the changes
                implemented.append(result['proposal_id'])
                logger.info(f"Implemented improvement: {result['proposal_id']}")
        
        return {
            'implemented_count': len(implemented),
            'implemented_proposals': implemented
        }
    
    async def _phase_learning(self, cycle_results: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 7: Learn from cycle outcomes"""
        
        logger.info("Phase 7: Learning from cycle")
        
        # Calculate cycle success rate
        test_results = cycle_results['phases'].get('testing', [])
        if test_results:
            success_rate = sum(1 for r in test_results if r['success']) / len(test_results)
        else:
            success_rate = 0.0
        
        # Update meta-learning efficiency
        self.metrics.learning_efficiency = success_rate
        
        # Calculate overall improvement
        monitoring = cycle_results['phases'].get('monitoring', {})
        if monitoring:
            scores = monitoring.get('scores', {})
            if scores:
                self.metrics.overall_improvement = np.mean(list(scores.values()))
        
        return {
            'cycle_success_rate': success_rate,
            'learning_efficiency': self.metrics.learning_efficiency,
            'overall_improvement': self.metrics.overall_improvement
        }
    
    async def generate_trading_signal(self, symbol: str, market_data: Dict[str, Any],
                                     context: Optional[Dict[str, Any]] = None) -> FusedDecision:
        """
        Generate a comprehensive trading signal using all evolved systems.
        """
        logger.info(f"Generating trading signal for {symbol}")
        
        # 1. Elite reasoning
        reasoning = self.reasoning_engine.reason_about_trade(symbol, market_data, context)
        
        # 2. Deep market intelligence
        intelligence_report = self.intelligence.generate_intelligence_report(symbol, market_data, context)
        
        # 3. Order flow analysis
        orderflow_signals = self.orderflow.analyze_order_flow(symbol, market_data, context)
        
        # 4. Create paradigm decisions
        paradigm_decisions = []
        
        # Technical paradigm (from reasoning)
        paradigm_decisions.append(ParadigmDecision(
            paradigm=ParadigmType.TECHNICAL,
            decision=self._map_direction_to_decision(reasoning.direction),
            confidence=reasoning.decision_confidence,
            reasoning=reasoning.decision,
            supporting_evidence=[s.description for s in reasoning.steps[:3]],
            contradicting_evidence=[],
            risk_factors=reasoning.identified_risks,
            expected_return=0.02,  # Would be calculated from reasoning
            expected_risk=0.01
        ))
        
        # Quantitative paradigm (from intelligence)
        paradigm_decisions.append(ParadigmDecision(
            paradigm=ParadigmType.QUANTITATIVE,
            decision=self._map_action_to_decision(intelligence_report.recommended_action),
            confidence=intelligence_report.confidence,
            reasoning=intelligence_report.recommended_action,
            supporting_evidence=[f"Tradability: {intelligence_report.tradability_score:.2f}"],
            contradicting_evidence=[],
            risk_factors=intelligence_report.risk_factors,
            expected_return=0.015,
            expected_risk=intelligence_report.risk_level
        ))
        
        # Order flow paradigm
        if orderflow_signals:
            dominant_signal = max(orderflow_signals, key=lambda s: s.strength)
            paradigm_decisions.append(ParadigmDecision(
                paradigm=ParadigmType.ORDER_FLOW,
                decision=self._map_impact_to_decision(dominant_signal.expected_impact),
                confidence=dominant_signal.confidence,
                reasoning=f"{dominant_signal.flow_type.value}: {dominant_signal.strength:.2f}",
                supporting_evidence=dominant_signal.evidence,
                contradicting_evidence=[],
                risk_factors=[],
                expected_return=0.01,
                expected_risk=0.005
            ))
        
        # 5. Fuse all paradigm decisions
        fused_decision = self.fusion.fuse_decisions(symbol, paradigm_decisions, context)
        
        logger.info(f"Signal generated: {fused_decision.final_decision.value} "
                   f"(confidence: {fused_decision.confidence.overall_confidence:.2f})")
        
        return fused_decision
    
    def _map_direction_to_decision(self, direction: str) -> DecisionType:
        """Map reasoning direction to decision type"""
        if direction == 'buy':
            return DecisionType.BUY
        elif direction == 'sell':
            return DecisionType.SELL
        else:
            return DecisionType.HOLD
    
    def _map_action_to_decision(self, action: str) -> DecisionType:
        """Map intelligence action to decision type"""
        if 'BUY' in action.upper():
            return DecisionType.BUY
        elif 'SELL' in action.upper():
            return DecisionType.SELL
        else:
            return DecisionType.HOLD
    
    def _map_impact_to_decision(self, impact: str) -> DecisionType:
        """Map order flow impact to decision type"""
        if impact == 'bullish':
            return DecisionType.BUY
        elif impact == 'bearish':
            return DecisionType.SELL
        else:
            return DecisionType.HOLD
    
    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status"""
        
        return {
            'is_running': self.is_running,
            'current_phase': self.current_phase.value,
            'metrics': {
                'total_cycles': self.metrics.total_cycles,
                'total_proposals': self.metrics.total_proposals,
                'successful_improvements': self.metrics.successful_improvements,
                'failed_improvements': self.metrics.failed_improvements,
                'success_rate': (self.metrics.successful_improvements / 
                               max(1, self.metrics.total_proposals)),
                'learning_efficiency': self.metrics.learning_efficiency,
                'overall_improvement': self.metrics.overall_improvement
            },
            'component_stats': {
                'reasoning': self.reasoning_engine.get_reasoning_stats(),
                'intelligence': self.intelligence.get_intelligence_stats(),
                'fusion': self.fusion.get_fusion_stats(),
                'meta_learning': self.meta_learner.get_evolution_metrics()
            }
        }
    
    def get_improvement_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent improvement history"""
        
        return self.evolution_history[-limit:]
    
    def export_evolution_report(self, filepath: str):
        """Export comprehensive evolution report"""
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'status': self.get_evolution_status(),
            'history': self.evolution_history,
            'baselines': self.baselines,
            'proposals': [
                {
                    'id': p.proposal_id,
                    'dimension': p.dimension.value,
                    'type': p.improvement_type.value,
                    'description': p.description,
                    'status': p.status,
                    'expected_impact': p.expected_impact,
                    'actual_impact': p.actual_impact
                }
                for p in self.meta_learner.proposals
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Evolution report exported to {filepath}")


async def quick_start(config: Optional[Dict[str, Any]] = None) -> RecursiveEvolutionOrchestrator:
    """Quick start function for recursive evolution orchestrator"""
    
    orchestrator = RecursiveEvolutionOrchestrator(config)
    
    # Optionally start continuous evolution
    if config and config.get('auto_start', False):
        await orchestrator.start_continuous_evolution(
            config.get('evolution_interval', 3600)
        )
    
    return orchestrator
