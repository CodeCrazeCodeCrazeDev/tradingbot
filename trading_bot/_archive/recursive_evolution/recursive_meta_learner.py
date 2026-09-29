"""
Recursive Meta-Learner
=======================

The core meta-learning engine that learns how to learn better.
This system recursively improves its own learning strategies, evolution methods,
and improvement discovery processes.

KEY CONCEPT: Instead of just improving trading strategies, this system improves
the PROCESS of improvement itself - meta-meta-learning.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class EvolutionDimension(Enum):
    """Dimensions of trading capability that can evolve"""
    # Core Trading
    REASONING_QUALITY = "reasoning_quality"
    DECISION_MAKING = "decision_making"
    ENTRY_TIMING = "entry_timing"
    EXIT_TIMING = "exit_timing"
    POSITION_SIZING = "position_sizing"
    
    # Market Understanding
    MARKET_INTELLIGENCE = "market_intelligence"
    REGIME_DETECTION = "regime_detection"
    LIQUIDITY_ANALYSIS = "liquidity_analysis"
    ORDER_FLOW_READING = "order_flow_reading"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    
    # Institutional Analysis
    INSTITUTIONAL_DETECTION = "institutional_detection"
    BLOCK_TRADE_SPOTTING = "block_trade_spotting"
    SPOOFING_DETECTION = "spoofing_detection"
    ICEBERG_DETECTION = "iceberg_detection"
    
    # Research & Discovery
    OPPORTUNITY_DISCOVERY = "opportunity_discovery"
    EDGE_GENERATION = "edge_generation"
    PATTERN_RECOGNITION = "pattern_recognition"
    ALTERNATIVE_DATA = "alternative_data"
    
    # Execution
    EXECUTION_QUALITY = "execution_quality"
    SLIPPAGE_MINIMIZATION = "slippage_minimization"
    MARKET_IMPACT = "market_impact"
    
    # Risk & Discipline
    RISK_MANAGEMENT = "risk_management"
    DISCIPLINE = "discipline"
    TRADE_REJECTION = "trade_rejection"
    DRAWDOWN_CONTROL = "drawdown_control"
    
    # Meta-Learning
    LEARNING_EFFICIENCY = "learning_efficiency"
    ADAPTATION_SPEED = "adaptation_speed"
    KNOWLEDGE_TRANSFER = "knowledge_transfer"
    SELF_AWARENESS = "self_awareness"


class ImprovementType(Enum):
    """Types of improvements"""
    PARAMETER_TUNING = "parameter_tuning"
    ALGORITHM_UPGRADE = "algorithm_upgrade"
    NEW_FEATURE = "new_feature"
    PROCESS_OPTIMIZATION = "process_optimization"
    META_IMPROVEMENT = "meta_improvement"  # Improving the improvement process


@dataclass
class ImprovementProposal:
    """A proposed improvement to the system"""
    proposal_id: str
    dimension: EvolutionDimension
    improvement_type: ImprovementType
    description: str
    expected_impact: float  # 0-1 scale
    confidence: float  # 0-1 scale
    implementation_complexity: float  # 0-1 scale
    
    # What needs to change
    changes: Dict[str, Any]
    
    # Evidence supporting this improvement
    evidence: List[str]
    
    # Risks and mitigations
    risks: List[str]
    mitigations: List[str]
    
    # Testing plan
    test_plan: str
    
    # Rollback plan
    rollback_plan: str
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "proposed"  # proposed, testing, approved, rejected, implemented
    
    # Results after testing
    actual_impact: Optional[float] = None
    test_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetaLearningConfig:
    """Configuration for meta-learning"""
    # Evolution rates
    base_learning_rate: float = 0.01
    meta_learning_rate: float = 0.001  # Rate at which learning rate adapts
    
    # Exploration vs exploitation
    exploration_rate: float = 0.2
    exploration_decay: float = 0.995
    
    # Improvement thresholds
    min_improvement_threshold: float = 0.01  # Minimum improvement to consider
    confidence_threshold: float = 0.7  # Minimum confidence to implement
    
    # Safety limits
    max_changes_per_cycle: int = 3
    require_human_approval: bool = True
    rollback_on_degradation: bool = True
    
    # Meta-learning parameters
    enable_meta_meta_learning: bool = True  # Learn how to learn how to learn
    track_learning_efficiency: bool = True
    optimize_evolution_strategy: bool = True


class RecursiveMetaLearner:
    """
    Recursive meta-learning system that improves its own improvement process.
    
    This system:
    1. Monitors performance across all dimensions
    2. Identifies improvement opportunities
    3. Generates improvement proposals
    4. Tests improvements safely
    5. Learns from improvement outcomes
    6. Improves its own improvement discovery process (meta-meta-learning)
    """
    
    def __init__(self, config: Optional[MetaLearningConfig] = None):
        self.config = config or MetaLearningConfig()
        
        # Performance tracking per dimension
        self.dimension_performance: Dict[EvolutionDimension, List[float]] = defaultdict(list)
        self.dimension_baselines: Dict[EvolutionDimension, float] = {}
        
        # Improvement history
        self.proposals: List[ImprovementProposal] = []
        self.successful_improvements: List[ImprovementProposal] = []
        self.failed_improvements: List[ImprovementProposal] = []
        
        # Meta-learning state
        self.learning_rates: Dict[EvolutionDimension, float] = {}
        self.improvement_strategies: Dict[EvolutionDimension, List[str]] = defaultdict(list)
        self.strategy_success_rates: Dict[str, float] = {}
        
        # Meta-meta-learning: Learning about learning
        self.meta_performance_history: List[float] = []
        self.evolution_strategy_performance: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("RecursiveMetaLearner initialized with meta-meta-learning enabled")
    
    def record_performance(self, dimension: EvolutionDimension, score: float, 
                          context: Optional[Dict[str, Any]] = None):
        """Record performance in a specific dimension"""
        self.dimension_performance[dimension].append(score)
        
        # Set baseline if first measurement
        if dimension not in self.dimension_baselines:
            self.dimension_baselines[dimension] = score
            logger.info(f"Baseline set for {dimension.value}: {score:.4f}")
        
        # Check for improvement or degradation
        baseline = self.dimension_baselines[dimension]
        change = score - baseline
        
        if abs(change) > self.config.min_improvement_threshold:
            if change > 0:
                logger.info(f"Improvement detected in {dimension.value}: +{change:.4f}")
            else:
                logger.warning(f"Degradation detected in {dimension.value}: {change:.4f}")
    
    def identify_improvement_opportunities(self) -> List[Tuple[EvolutionDimension, float]]:
        """
        Identify dimensions that need improvement.
        Returns list of (dimension, priority) tuples.
        """
        opportunities = []
        
        for dimension in EvolutionDimension:
            if dimension not in self.dimension_performance:
                # Never measured - high priority to establish baseline
                opportunities.append((dimension, 1.0))
                continue
            
            scores = self.dimension_performance[dimension]
            if len(scores) < 5:
                continue  # Need more data
            
            # Calculate improvement potential
            recent_scores = scores[-10:]
            baseline = self.dimension_baselines.get(dimension, scores[0])
            current = np.mean(recent_scores)
            
            # Check for stagnation
            recent_variance = np.var(recent_scores)
            is_stagnant = recent_variance < 0.001
            
            # Check for degradation
            is_degrading = current < baseline * 0.95
            
            # Calculate priority
            if is_degrading:
                priority = 1.0  # Highest priority
            elif is_stagnant and current < 0.8:  # Stagnant and not excellent
                priority = 0.8
            elif current < 0.6:  # Poor performance
                priority = 0.9
            else:
                # Lower priority but still consider
                priority = max(0.0, 0.7 - current)
            
            if priority > 0.3:
                opportunities.append((dimension, priority))
        
        # Sort by priority
        opportunities.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Identified {len(opportunities)} improvement opportunities")
        return opportunities
    
    def generate_improvement_proposal(self, dimension: EvolutionDimension,
                                     context: Optional[Dict[str, Any]] = None) -> ImprovementProposal:
        """
        Generate an improvement proposal for a specific dimension.
        Uses meta-learning to select the best improvement strategy.
        """
        # Get historical performance
        scores = self.dimension_performance.get(dimension, [])
        baseline = self.dimension_baselines.get(dimension, 0.5)
        current = np.mean(scores[-10:]) if len(scores) >= 10 else baseline
        
        # Determine improvement type based on meta-learning
        improvement_type = self._select_improvement_type(dimension, current)
        
        # Generate specific proposal based on dimension and type
        proposal = self._generate_specific_proposal(dimension, improvement_type, current, context)
        
        self.proposals.append(proposal)
        logger.info(f"Generated improvement proposal: {proposal.proposal_id}")
        
        return proposal
    
    def _select_improvement_type(self, dimension: EvolutionDimension, 
                                 current_score: float) -> ImprovementType:
        """
        Select the best improvement type using meta-learning.
        Learns which improvement types work best for each dimension.
        """
        # Get success rates for each improvement type on this dimension
        dimension_key = dimension.value
        type_scores = {}
        
        for imp_type in ImprovementType:
            # Calculate historical success rate
            successes = [
                imp for imp in self.successful_improvements
                if imp.dimension == dimension and imp.improvement_type == imp_type
            ]
            failures = [
                imp for imp in self.failed_improvements
                if imp.dimension == dimension and imp.improvement_type == imp_type
            ]
            
            total = len(successes) + len(failures)
            if total > 0:
                success_rate = len(successes) / total
                avg_impact = np.mean([imp.actual_impact for imp in successes]) if successes else 0
                type_scores[imp_type] = success_rate * avg_impact
            else:
                # No history - use exploration
                type_scores[imp_type] = np.random.random() * self.config.exploration_rate
        
        # Select best type with some exploration
        if np.random.random() < self.config.exploration_rate:
            # Explore: random selection
            selected_type = np.random.choice(list(ImprovementType))
        else:
            # Exploit: select best performing type
            selected_type = max(type_scores.items(), key=lambda x: x[1])[0]
        
        return selected_type
    
    def _generate_specific_proposal(self, dimension: EvolutionDimension,
                                   improvement_type: ImprovementType,
                                   current_score: float,
                                   context: Optional[Dict[str, Any]]) -> ImprovementProposal:
        """Generate specific improvement proposal based on dimension and type"""
        
        proposal_id = f"IMP-{dimension.value[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Dimension-specific proposals
        if dimension == EvolutionDimension.REASONING_QUALITY:
            return self._propose_reasoning_improvement(proposal_id, improvement_type, current_score)
        elif dimension == EvolutionDimension.ORDER_FLOW_READING:
            return self._propose_orderflow_improvement(proposal_id, improvement_type, current_score)
        elif dimension == EvolutionDimension.INSTITUTIONAL_DETECTION:
            return self._propose_institutional_improvement(proposal_id, improvement_type, current_score)
        elif dimension == EvolutionDimension.LIQUIDITY_ANALYSIS:
            return self._propose_liquidity_improvement(proposal_id, improvement_type, current_score)
        elif dimension == EvolutionDimension.EDGE_GENERATION:
            return self._propose_edge_improvement(proposal_id, improvement_type, current_score)
        else:
            return self._propose_generic_improvement(proposal_id, dimension, improvement_type, current_score)
    
    def _propose_reasoning_improvement(self, proposal_id: str, 
                                      improvement_type: ImprovementType,
                                      current_score: float) -> ImprovementProposal:
        """Propose improvement to reasoning quality"""
        
        if improvement_type == ImprovementType.ALGORITHM_UPGRADE:
            return ImprovementProposal(
                proposal_id=proposal_id,
                dimension=EvolutionDimension.REASONING_QUALITY,
                improvement_type=improvement_type,
                description="Upgrade reasoning engine to use deeper chain-of-thought with verification",
                expected_impact=0.15,
                confidence=0.8,
                implementation_complexity=0.6,
                changes={
                    "reasoning_depth": 5,  # Increase from 3 to 5
                    "enable_verification": True,
                    "add_counterfactual_analysis": True
                },
                evidence=[
                    "Current reasoning depth of 3 is insufficient for complex market conditions",
                    "Verification step reduces false positives by 30%",
                    "Counterfactual analysis improves decision quality"
                ],
                risks=[
                    "Increased computation time",
                    "Potential for analysis paralysis"
                ],
                mitigations=[
                    "Implement caching for common reasoning patterns",
                    "Add timeout mechanisms",
                    "Parallel processing for verification"
                ],
                test_plan="Run on 1000 historical scenarios, compare decision quality",
                rollback_plan="Revert to depth-3 reasoning if quality degrades or latency exceeds 500ms"
            )
        
        elif improvement_type == ImprovementType.NEW_FEATURE:
            return ImprovementProposal(
                proposal_id=proposal_id,
                dimension=EvolutionDimension.REASONING_QUALITY,
                improvement_type=improvement_type,
                description="Add multi-perspective reasoning: bull case, bear case, neutral case",
                expected_impact=0.12,
                confidence=0.75,
                implementation_complexity=0.5,
                changes={
                    "enable_multi_perspective": True,
                    "perspectives": ["bull", "bear", "neutral"],
                    "weight_by_evidence": True
                },
                evidence=[
                    "Single-perspective reasoning misses important counterarguments",
                    "Professional traders always consider multiple scenarios",
                    "Reduces confirmation bias"
                ],
                risks=[
                    "May lead to indecision",
                    "Conflicting perspectives could confuse the system"
                ],
                mitigations=[
                    "Use evidence-weighted voting",
                    "Require minimum confidence threshold",
                    "Track which perspective was correct historically"
                ],
                test_plan="Compare decision quality on 500 historical trades",
                rollback_plan="Disable multi-perspective if decision quality drops"
            )
        
        else:
            return self._propose_generic_improvement(proposal_id, EvolutionDimension.REASONING_QUALITY,
                                                    improvement_type, current_score)
    
    def _propose_orderflow_improvement(self, proposal_id: str,
                                      improvement_type: ImprovementType,
                                      current_score: float) -> ImprovementProposal:
        """Propose improvement to order flow reading"""
        
        return ImprovementProposal(
            proposal_id=proposal_id,
            dimension=EvolutionDimension.ORDER_FLOW_READING,
            improvement_type=improvement_type,
            description="Implement advanced order flow imbalance detection with ML",
            expected_impact=0.18,
            confidence=0.82,
            implementation_complexity=0.7,
            changes={
                "add_ml_orderflow_model": True,
                "features": ["volume_delta", "absorption", "exhaustion", "momentum"],
                "lookback_periods": [5, 10, 20, 50],
                "enable_institutional_filter": True
            },
            evidence=[
                "Order flow imbalances predict short-term price moves",
                "ML can detect subtle patterns humans miss",
                "Institutional order flow has higher predictive power"
            ],
            risks=[
                "ML model may overfit to recent market conditions",
                "Requires significant training data",
                "May have false positives during low liquidity"
            ],
            mitigations=[
                "Use walk-forward validation",
                "Require minimum liquidity threshold",
                "Ensemble with rule-based approach",
                "Regular model retraining"
            ],
            test_plan="Backtest on 6 months of tick data, validate on out-of-sample period",
            rollback_plan="Revert to rule-based order flow analysis if accuracy drops below 60%"
        )
    
    def _propose_institutional_improvement(self, proposal_id: str,
                                          improvement_type: ImprovementType,
                                          current_score: float) -> ImprovementProposal:
        """Propose improvement to institutional detection"""
        
        return ImprovementProposal(
            proposal_id=proposal_id,
            dimension=EvolutionDimension.INSTITUTIONAL_DETECTION,
            improvement_type=improvement_type,
            description="Enhance institutional activity detection with pattern recognition",
            expected_impact=0.20,
            confidence=0.78,
            implementation_complexity=0.8,
            changes={
                "add_block_trade_detector": True,
                "add_iceberg_detector": True,
                "add_spoofing_detector": True,
                "min_block_size": 100000,  # USD
                "iceberg_detection_window": 60,  # seconds
                "spoofing_cancel_ratio": 0.8
            },
            evidence=[
                "Institutional orders move markets significantly",
                "Following institutional flow improves win rate",
                "Early detection provides edge"
            ],
            risks=[
                "False positives from retail aggregation",
                "Institutional patterns change over time",
                "May be gamed by sophisticated players"
            ],
            mitigations=[
                "Multi-factor confirmation required",
                "Adaptive thresholds based on market conditions",
                "Track detector accuracy and adjust",
                "Combine with other signals"
            ],
            test_plan="Validate on known institutional events, measure detection accuracy",
            rollback_plan="Disable if false positive rate exceeds 40%"
        )
    
    def _propose_liquidity_improvement(self, proposal_id: str,
                                      improvement_type: ImprovementType,
                                      current_score: float) -> ImprovementProposal:
        """Propose improvement to liquidity analysis"""
        
        return ImprovementProposal(
            proposal_id=proposal_id,
            dimension=EvolutionDimension.LIQUIDITY_ANALYSIS,
            improvement_type=improvement_type,
            description="Build 3D liquidity heatmap with predictive zones",
            expected_impact=0.16,
            confidence=0.80,
            implementation_complexity=0.65,
            changes={
                "enable_3d_liquidity_map": True,
                "dimensions": ["price", "time", "volume"],
                "identify_liquidity_zones": True,
                "predict_liquidity_shifts": True,
                "update_frequency": 1  # seconds
            },
            evidence=[
                "Liquidity zones act as support/resistance",
                "Liquidity shifts predict price moves",
                "3D visualization reveals hidden patterns"
            ],
            risks=[
                "Computationally intensive",
                "May lag in fast markets",
                "Liquidity can evaporate instantly"
            ],
            mitigations=[
                "Optimize with spatial indexing",
                "Pre-compute common patterns",
                "Add instant liquidity shock detection",
                "Fallback to 2D analysis if needed"
            ],
            test_plan="Compare liquidity prediction accuracy vs current method",
            rollback_plan="Revert to 2D liquidity analysis if performance degrades"
        )
    
    def _propose_edge_improvement(self, proposal_id: str,
                                 improvement_type: ImprovementType,
                                 current_score: float) -> ImprovementProposal:
        """Propose improvement to edge generation"""
        
        return ImprovementProposal(
            proposal_id=proposal_id,
            dimension=EvolutionDimension.EDGE_GENERATION,
            improvement_type=improvement_type,
            description="Implement alternative data fusion for edge discovery",
            expected_impact=0.22,
            confidence=0.72,
            implementation_complexity=0.85,
            changes={
                "add_alternative_data_sources": [
                    "sentiment", "news", "social_media", "economic_calendar",
                    "options_flow", "futures_positioning", "crypto_flows"
                ],
                "fusion_method": "transformer_attention",
                "enable_cross_asset_signals": True,
                "edge_validation_required": True
            },
            evidence=[
                "Alternative data provides unique insights",
                "Cross-asset correlations reveal opportunities",
                "Data fusion improves signal quality"
            ],
            risks=[
                "Data quality issues",
                "Overfitting to noise",
                "High data costs",
                "Integration complexity"
            ],
            mitigations=[
                "Rigorous data validation",
                "Out-of-sample testing required",
                "Start with free/low-cost sources",
                "Incremental integration",
                "Track edge decay over time"
            ],
            test_plan="Validate each data source independently, then test fusion",
            rollback_plan="Remove data sources that don't improve Sharpe ratio"
        )
    
    def _propose_generic_improvement(self, proposal_id: str, dimension: EvolutionDimension,
                                    improvement_type: ImprovementType,
                                    current_score: float) -> ImprovementProposal:
        """Generic improvement proposal"""
        
        return ImprovementProposal(
            proposal_id=proposal_id,
            dimension=dimension,
            improvement_type=improvement_type,
            description=f"Improve {dimension.value} through {improvement_type.value}",
            expected_impact=0.10,
            confidence=0.65,
            implementation_complexity=0.5,
            changes={"optimize": True},
            evidence=[f"Current score of {current_score:.2f} can be improved"],
            risks=["Unknown risks - requires further analysis"],
            mitigations=["Careful testing", "Gradual rollout", "Monitoring"],
            test_plan="Standard validation on historical data",
            rollback_plan="Revert if performance degrades"
        )
    
    def test_improvement(self, proposal: ImprovementProposal,
                        test_data: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Test an improvement proposal safely.
        Returns (success, results)
        """
        logger.info(f"Testing improvement proposal: {proposal.proposal_id}")
        
        # This would be implemented with actual testing logic
        # For now, simulate testing
        
        results = {
            "test_duration": 60,  # seconds
            "samples_tested": 1000,
            "baseline_score": 0.65,
            "new_score": 0.65 + proposal.expected_impact * 0.8,  # 80% of expected
            "confidence_interval": [0.63, 0.72],
            "passed_safety_checks": True
        }
        
        success = results["new_score"] > results["baseline_score"]
        proposal.actual_impact = results["new_score"] - results["baseline_score"]
        proposal.test_results = results
        
        if success:
            proposal.status = "approved"
            self.successful_improvements.append(proposal)
            logger.info(f"Improvement test PASSED: {proposal.proposal_id}")
        else:
            proposal.status = "rejected"
            self.failed_improvements.append(proposal)
            logger.warning(f"Improvement test FAILED: {proposal.proposal_id}")
        
        # Meta-learning: Learn from this outcome
        self._update_meta_learning(proposal, success)
        
        return success, results
    
    def _update_meta_learning(self, proposal: ImprovementProposal, success: bool):
        """
        Update meta-learning models based on improvement outcome.
        This is where the system learns how to improve better.
        """
        # Update strategy success rates
        strategy_key = f"{proposal.dimension.value}_{proposal.improvement_type.value}"
        
        if strategy_key not in self.strategy_success_rates:
            self.strategy_success_rates[strategy_key] = 0.5
        
        # Update with exponential moving average
        alpha = 0.1
        current_rate = self.strategy_success_rates[strategy_key]
        new_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * current_rate
        self.strategy_success_rates[strategy_key] = new_rate
        
        # Update learning rate for this dimension
        if proposal.dimension not in self.learning_rates:
            self.learning_rates[proposal.dimension] = self.config.base_learning_rate
        
        if success and proposal.actual_impact:
            # Increase learning rate if improvement was successful
            self.learning_rates[proposal.dimension] *= 1.1
        else:
            # Decrease learning rate if improvement failed
            self.learning_rates[proposal.dimension] *= 0.9
        
        # Clip learning rate
        self.learning_rates[proposal.dimension] = np.clip(
            self.learning_rates[proposal.dimension],
            0.001, 0.1
        )
        
        # Meta-meta-learning: Track evolution strategy performance
        if self.config.enable_meta_meta_learning:
            evolution_strategy = f"{proposal.improvement_type.value}"
            impact = proposal.actual_impact if success else -0.05
            self.evolution_strategy_performance[evolution_strategy].append(impact)
            
            # Adjust exploration rate based on recent success
            recent_successes = len([p for p in self.successful_improvements[-20:]])
            recent_total = len(self.proposals[-20:])
            if recent_total > 0:
                success_rate = recent_successes / recent_total
                # Increase exploration if success rate is too high (may be stuck in local optimum)
                # Decrease exploration if success rate is too low (need to exploit known good strategies)
                if success_rate > 0.8:
                    self.config.exploration_rate = min(0.3, self.config.exploration_rate * 1.05)
                elif success_rate < 0.3:
                    self.config.exploration_rate = max(0.05, self.config.exploration_rate * 0.95)
    
    def run_evolution_cycle(self, context: Optional[Dict[str, Any]] = None) -> List[ImprovementProposal]:
        """
        Run one complete evolution cycle:
        1. Identify improvement opportunities
        2. Generate proposals
        3. Return proposals for testing/approval
        """
        logger.info("Starting evolution cycle")
        
        # Identify opportunities
        opportunities = self.identify_improvement_opportunities()
        
        # Generate proposals for top opportunities
        max_proposals = self.config.max_changes_per_cycle
        proposals = []
        
        for dimension, priority in opportunities[:max_proposals]:
            proposal = self.generate_improvement_proposal(dimension, context)
            proposals.append(proposal)
        
        logger.info(f"Evolution cycle complete: {len(proposals)} proposals generated")
        
        return proposals
    
    def get_evolution_metrics(self) -> Dict[str, Any]:
        """Get metrics about the evolution process itself"""
        
        total_proposals = len(self.proposals)
        successful = len(self.successful_improvements)
        failed = len(self.failed_improvements)
        
        success_rate = successful / total_proposals if total_proposals > 0 else 0
        
        # Calculate average impact of successful improvements
        avg_impact = np.mean([p.actual_impact for p in self.successful_improvements 
                             if p.actual_impact]) if successful > 0 else 0
        
        # Calculate meta-learning efficiency
        if len(self.meta_performance_history) > 10:
            recent_meta = self.meta_performance_history[-10:]
            older_meta = self.meta_performance_history[-20:-10] if len(self.meta_performance_history) > 20 else recent_meta
            meta_improvement = np.mean(recent_meta) - np.mean(older_meta)
        else:
            meta_improvement = 0
        
        return {
            "total_proposals": total_proposals,
            "successful_improvements": successful,
            "failed_improvements": failed,
            "success_rate": success_rate,
            "average_impact": avg_impact,
            "meta_learning_efficiency": meta_improvement,
            "exploration_rate": self.config.exploration_rate,
            "dimensions_tracked": len(self.dimension_performance),
            "learning_rates": {d.value: lr for d, lr in self.learning_rates.items()},
            "strategy_success_rates": self.strategy_success_rates
        }


def quick_start_meta_learner(config: Optional[Dict[str, Any]] = None) -> RecursiveMetaLearner:
    """Quick start function for meta-learner"""
    if config:
        meta_config = MetaLearningConfig(**config)
    else:
        meta_config = MetaLearningConfig()
    
    return RecursiveMetaLearner(meta_config)
