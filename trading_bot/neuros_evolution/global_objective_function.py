"""
Global Objective Function
========================

Task-conditional utility model per Section 6.

Utility = Benefit - Cost - Risk - Instability - Complexity

Candidate scoring includes:
- task success quality
- factual correctness
- economic usefulness
- calibration quality
- regime robustness
- latency cost
- token cost
- operational fragility
- hallucination severity
- auditability quality
- integration complexity
- rollback risk

For capital-adjacent tasks, hallucination and false-confidence penalties must be dominant.
For offline research tasks, exploration value may receive higher weight.

Weights must be conditional on: capability ID, regime, risk tier, operational environment, review requirements.

Never use one fixed universal weighting scheme for all tasks.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Task categories with different weight priorities"""
    CAPITAL_ADJACENT = "capital_adjacent"  # Trading decisions
    OFFLINE_RESEARCH = "offline_research"  # Analysis, reports
    DATA_PROCESSING = "data_processing"    # ETL, transformations
    COMPLIANCE = "compliance"              # Regulatory checks
    INFRASTRUCTURE = "infrastructure"    # System maintenance


class MarketRegime(Enum):
    """Market regimes for conditional scoring"""
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRENDING = "trending"
    RANGING = "ranging"
    CRISIS = "crisis"
    NORMAL = "normal"


class RiskTier(Enum):
    """Risk tiers for conditional scoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UtilityWeights:
    """Weight configuration for utility calculation"""
    # Benefit components
    task_success_quality: float = 1.0
    factual_correctness: float = 1.0
    economic_usefulness: float = 1.0
    calibration_quality: float = 1.0
    regime_robustness: float = 1.0
    
    # Cost components
    latency_cost: float = 1.0
    token_cost: float = 1.0
    compute_cost: float = 1.0
    
    # Risk components
    hallucination_severity: float = 1.0  # Dominant for capital-adjacent
    false_confidence_risk: float = 1.0  # Dominant for capital-adjacent
    tail_risk: float = 1.0
    execution_realism_risk: float = 1.0
    
    # Instability components
    output_stability: float = 1.0
    regime_stability: float = 1.0
    
    # Complexity components
    integration_complexity: float = 1.0
    operational_fragility: float = 1.0
    auditability_quality: float = 1.0  # Negative weight (higher is better)
    rollback_risk: float = 1.0
    
    # Exploration bonus (for offline research)
    exploration_value: float = 0.0


@dataclass
class CandidateMetrics:
    """Metrics for a candidate capability/object"""
    # Benefit metrics (0-1 scale, higher is better)
    task_success_quality: float = 0.0
    factual_correctness: float = 0.0
    economic_usefulness: float = 0.0
    calibration_quality: float = 0.0
    regime_robustness: float = 0.0
    
    # Cost metrics (absolute values, will be normalized)
    latency_ms: float = 0.0
    token_count: float = 0.0
    compute_hours: float = 0.0
    
    # Risk metrics (0-1 scale, higher is worse)
    hallucination_severity: float = 0.0
    false_confidence_risk: float = 0.0
    tail_risk: float = 0.0
    execution_realism_risk: float = 0.0
    
    # Instability metrics (0-1 scale, higher is worse)
    output_variance: float = 0.0
    regime_performance_std: float = 0.0
    
    # Complexity metrics (0-1 scale, higher is worse)
    integration_burden: float = 0.0
    operational_fragility: float = 0.0
    auditability_score: float = 0.0  # Higher is better
    rollback_difficulty: float = 0.0
    
    # Exploration value (for offline research, 0-1 scale)
    exploration_value: float = 0.0


@dataclass
class UtilityScore:
    """Complete utility score breakdown"""
    total_utility: float
    benefit_component: float
    cost_component: float
    risk_component: float
    instability_component: float
    complexity_component: float
    
    # Individual contributions
    task_success_quality_contrib: float
    factual_correctness_contrib: float
    economic_usefulness_contrib: float
    calibration_quality_contrib: float
    regime_robustness_contrib: float
    latency_cost_contrib: float
    token_cost_contrib: float
    hallucination_severity_contrib: float
    false_confidence_risk_contrib: float
    auditability_contrib: float
    
    # Context
    capability_id: str
    regime: str
    risk_tier: str
    task_category: str
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class WeightConfiguration:
    """
    Task-conditional weight configurations per Section 6.
    Different weights for different task categories and risk tiers.
    """
    
    # Capital-adjacent tasks: hallucination and false-confidence penalties dominant
    CAPITAL_ADJACENT_CRITICAL = UtilityWeights(
        task_success_quality=1.0,
        factual_correctness=2.0,  # High weight on correctness
        economic_usefulness=1.5,
        calibration_quality=2.0,
        regime_robustness=1.5,
        latency_cost=0.5,
        token_cost=0.3,
        compute_cost=0.3,
        hallucination_severity=5.0,  # DOMINANT
        false_confidence_risk=5.0,   # DOMINANT
        tail_risk=3.0,
        execution_realism_risk=2.0,
        output_stability=1.0,
        regime_stability=1.5,
        integration_complexity=0.5,
        operational_fragility=2.0,
        auditability_quality=-2.0,  # Negative because higher auditability is better
        rollback_risk=2.0,
        exploration_value=0.0
    )
    
    CAPITAL_ADJACENT_HIGH = UtilityWeights(
        task_success_quality=1.0,
        factual_correctness=1.5,
        economic_usefulness=1.5,
        calibration_quality=1.5,
        regime_robustness=1.2,
        latency_cost=0.5,
        token_cost=0.5,
        compute_cost=0.5,
        hallucination_severity=3.0,  # DOMINANT
        false_confidence_risk=3.0,   # DOMINANT
        tail_risk=2.0,
        execution_realism_risk=1.5,
        output_stability=0.8,
        regime_stability=1.0,
        integration_complexity=0.5,
        operational_fragility=1.5,
        auditability_quality=-1.5,
        rollback_risk=1.5,
        exploration_value=0.0
    )
    
    # Offline research: exploration value receives higher weight
    OFFLINE_RESEARCH = UtilityWeights(
        task_success_quality=0.8,
        factual_correctness=1.0,
        economic_usefulness=0.5,
        calibration_quality=1.0,
        regime_robustness=0.8,
        latency_cost=0.2,
        token_cost=0.2,
        compute_cost=0.3,
        hallucination_severity=1.0,
        false_confidence_risk=1.0,
        tail_risk=0.5,
        execution_realism_risk=0.5,
        output_stability=0.5,
        regime_stability=0.5,
        integration_complexity=0.3,
        operational_fragility=0.5,
        auditability_quality=-0.5,
        rollback_risk=0.5,
        exploration_value=2.0  # Higher weight on exploration
    )
    
    # Data processing: cost efficiency prioritized
    DATA_PROCESSING = UtilityWeights(
        task_success_quality=1.0,
        factual_correctness=1.0,
        economic_usefulness=0.8,
        calibration_quality=0.8,
        regime_robustness=0.5,
        latency_cost=1.5,  # Higher weight on cost
        token_cost=1.5,
        compute_cost=2.0,
        hallucination_severity=1.0,
        false_confidence_risk=0.8,
        tail_risk=0.5,
        execution_realism_risk=0.5,
        output_stability=0.8,
        regime_stability=0.5,
        integration_complexity=1.0,
        operational_fragility=0.8,
        auditability_quality=-0.5,
        rollback_risk=0.5,
        exploration_value=0.0
    )
    
    # Compliance: correctness and auditability dominant
    COMPLIANCE = UtilityWeights(
        task_success_quality=1.0,
        factual_correctness=2.0,
        economic_usefulness=0.5,
        calibration_quality=1.5,
        regime_robustness=1.0,
        latency_cost=0.8,
        token_cost=0.5,
        compute_cost=0.5,
        hallucination_severity=2.0,
        false_confidence_risk=2.0,
        tail_risk=2.0,
        execution_realism_risk=1.0,
        output_stability=1.0,
        regime_stability=1.0,
        integration_complexity=0.5,
        operational_fragility=1.0,
        auditability_quality=-3.0,  # DOMINANT - high auditability crucial
        rollback_risk=1.0,
        exploration_value=0.0
    )
    
    # Infrastructure: stability and reliability prioritized
    INFRASTRUCTURE = UtilityWeights(
        task_success_quality=1.0,
        factual_correctness=1.0,
        economic_usefulness=0.5,
        calibration_quality=0.8,
        regime_robustness=1.0,
        latency_cost=0.5,
        token_cost=0.3,
        compute_cost=0.5,
        hallucination_severity=0.5,
        false_confidence_risk=0.5,
        tail_risk=1.0,
        execution_realism_risk=0.8,
        output_stability=2.0,  # High stability priority
        regime_stability=1.5,
        integration_complexity=0.5,
        operational_fragility=2.0,
        auditability_quality=-1.0,
        rollback_risk=1.5,
        exploration_value=0.0
    )
    
    @classmethod
    def get_weights(cls, task_category: TaskCategory, risk_tier: RiskTier,
                   regime: Optional[MarketRegime] = None) -> UtilityWeights:
        """Get appropriate weights for task context"""
        
        # Crisis regime increases risk weights
        if regime == MarketRegime.CRISIS:
            base_weights = cls.CAPITAL_ADJACENT_CRITICAL
            return UtilityWeights(
                task_success_quality=base_weights.task_success_quality,
                factual_correctness=base_weights.factual_correctness * 1.5,
                economic_usefulness=base_weights.economic_usefulness,
                calibration_quality=base_weights.calibration_quality * 1.5,
                regime_robustness=base_weights.regime_robustness * 2.0,
                latency_cost=base_weights.latency_cost,
                token_cost=base_weights.token_cost,
                compute_cost=base_weights.compute_cost,
                hallucination_severity=base_weights.hallucination_severity * 1.5,
                false_confidence_risk=base_weights.false_confidence_risk * 1.5,
                tail_risk=base_weights.tail_risk * 2.0,
                execution_realism_risk=base_weights.execution_realism_risk * 1.5,
                output_stability=base_weights.output_stability * 1.5,
                regime_stability=base_weights.regime_stability * 2.0,
                integration_complexity=base_weights.integration_complexity,
                operational_fragility=base_weights.operational_fragility * 1.5,
                auditability_quality=base_weights.auditability_quality,
                rollback_risk=base_weights.rollback_risk * 1.5,
                exploration_value=base_weights.exploration_value
            )
        
        # Select base weights
        if task_category == TaskCategory.CAPITAL_ADJACENT:
            if risk_tier == RiskTier.CRITICAL:
                return cls.CAPITAL_ADJACENT_CRITICAL
            else:
                return cls.CAPITAL_ADJACENT_HIGH
        elif task_category == TaskCategory.OFFLINE_RESEARCH:
            return cls.OFFLINE_RESEARCH
        elif task_category == TaskCategory.DATA_PROCESSING:
            return cls.DATA_PROCESSING
        elif task_category == TaskCategory.COMPLIANCE:
            return cls.COMPLIANCE
        elif task_category == TaskCategory.INFRASTRUCTURE:
            return cls.INFRASTRUCTURE
        
        return cls.CAPITAL_ADJACENT_HIGH  # Default


class GlobalObjectiveFunction:
    """
    Global objective function per Section 6.
    
    Utility = Benefit - Cost - Risk - Instability - Complexity
    """
    
    def __init__(self):
        # Baselines for cost normalization (tunable)
        self.latency_baseline_ms = 1000
        self.token_baseline_1k = 10
        self.compute_baseline_hours = 1.0
        
        logger.info("GlobalObjectiveFunction initialized")
    
    def score_candidate(self, 
                       metrics: CandidateMetrics,
                       capability_id: str,
                       task_category: TaskCategory,
                       risk_tier: RiskTier,
                       regime: Optional[MarketRegime] = None) -> UtilityScore:
        """
        Score a candidate using task-conditional utility model.
        
        Returns detailed breakdown for explainability.
        """
        # Get appropriate weights
        weights = WeightConfiguration.get_weights(task_category, risk_tier, regime)
        
        # Calculate benefit component
        benefit = (
            weights.task_success_quality * metrics.task_success_quality +
            weights.factual_correctness * metrics.factual_correctness +
            weights.economic_usefulness * metrics.economic_usefulness +
            weights.calibration_quality * metrics.calibration_quality +
            weights.regime_robustness * metrics.regime_robustness +
            weights.exploration_value * metrics.exploration_value
        )
        
        # Calculate cost component (normalized)
        normalized_latency = min(1.0, metrics.latency_ms / self.latency_baseline_ms)
        normalized_tokens = min(1.0, metrics.token_count / (self.token_baseline_1k * 1000))
        normalized_compute = min(1.0, metrics.compute_hours / self.compute_baseline_hours)
        
        cost = (
            weights.latency_cost * normalized_latency +
            weights.token_cost * normalized_tokens +
            weights.compute_cost * normalized_compute
        )
        
        # Calculate risk component
        risk = (
            weights.hallucination_severity * metrics.hallucination_severity +
            weights.false_confidence_risk * metrics.false_confidence_risk +
            weights.tail_risk * metrics.tail_risk +
            weights.execution_realism_risk * metrics.execution_realism_risk
        )
        
        # Calculate instability component
        instability = (
            weights.output_stability * metrics.output_variance +
            weights.regime_stability * metrics.regime_performance_std
        )
        
        # Calculate complexity component
        complexity = (
            weights.integration_complexity * metrics.integration_burden +
            weights.operational_fragility * metrics.operational_fragility +
            weights.auditability_quality * (1 - metrics.auditability_score) +  # Invert so higher is worse
            weights.rollback_risk * metrics.rollback_difficulty
        )
        
        # Total utility
        total_utility = benefit - cost - risk - instability - complexity
        
        # Log scoring details for capital-adjacent critical
        if task_category == TaskCategory.CAPITAL_ADJACENT and risk_tier == RiskTier.CRITICAL:
            logger.debug(f"Utility scoring for {capability_id}:")
            logger.debug(f"  Benefit: {benefit:.3f} (correctness={metrics.factual_correctness:.3f})")
            logger.debug(f"  Risk: {risk:.3f} (hallucination={metrics.hallucination_severity:.3f}, false_conf={metrics.false_confidence_risk:.3f})")
            logger.debug(f"  Total: {total_utility:.3f}")
        
        return UtilityScore(
            total_utility=total_utility,
            benefit_component=benefit,
            cost_component=cost,
            risk_component=risk,
            instability_component=instability,
            complexity_component=complexity,
            task_success_quality_contrib=weights.task_success_quality * metrics.task_success_quality,
            factual_correctness_contrib=weights.factual_correctness * metrics.factual_correctness,
            economic_usefulness_contrib=weights.economic_usefulness * metrics.economic_usefulness,
            calibration_quality_contrib=weights.calibration_quality * metrics.calibration_quality,
            regime_robustness_contrib=weights.regime_robustness * metrics.regime_robustness,
            latency_cost_contrib=weights.latency_cost * normalized_latency,
            token_cost_contrib=weights.token_cost * normalized_tokens,
            hallucination_severity_contrib=weights.hallucination_severity * metrics.hallucination_severity,
            false_confidence_risk_contrib=weights.false_confidence_risk * metrics.false_confidence_risk,
            auditability_contrib=weights.auditability_quality * metrics.auditability_score,
            capability_id=capability_id,
            regime=regime.value if regime else "unknown",
            risk_tier=risk_tier.value,
            task_category=task_category.value
        )
    
    def compare_candidates(self, 
                          candidate_scores: List[UtilityScore],
                          current_best: Optional[UtilityScore] = None) -> Dict[str, Any]:
        """
        Compare multiple candidates and select best.
        
        Returns detailed comparison for explainability.
        """
        if not candidate_scores:
            return {"best_candidate": None, "comparison": []}
        
        # Find best candidate
        best_score = max(candidate_scores, key=lambda x: x.total_utility)
        
        # If current best provided, must significantly improve
        if current_best:
            improvement_threshold = 0.05  # 5% improvement required
            relative_improvement = (
                (best_score.total_utility - current_best.total_utility) 
                / abs(current_best.total_utility + 1e-6)
            )
            
            if relative_improvement < improvement_threshold:
                logger.info(f"Best candidate {best_score.capability_id} rejected: "
                          f"improvement {relative_improvement:.3f} < threshold {improvement_threshold:.3f}")
                return {
                    "best_candidate": current_best,
                    "selected_candidate": best_score,
                    "improvement": relative_improvement,
                    "threshold": improvement_threshold,
                    "promoted": False,
                    "reason": "insufficient_improvement"
                }
        
        # Build comparison table
        comparison = []
        for score in candidate_scores:
            comparison.append({
                "capability_id": score.capability_id,
                "total_utility": score.total_utility,
                "benefit": score.benefit_component,
                "cost": score.cost_component,
                "risk": score.risk_component,
                "hallucination_penalty": score.hallucination_severity_contrib,
                "false_conf_penalty": score.false_confidence_risk_contrib,
                "correctness_contrib": score.factual_correctness_contrib
            })
        
        # Sort by total utility
        comparison.sort(key=lambda x: x["total_utility"], reverse=True)
        
        return {
            "best_candidate": best_score,
            "selected_candidate": best_score,
            "comparison": comparison,
            "improvement": relative_improvement if current_best else float('inf'),
            "threshold": improvement_threshold if current_best else 0,
            "promoted": True,
            "reason": "significant_improvement"
        }
    
    def should_promote(self, score: UtilityScore, 
                      minimum_threshold: float = 0.0) -> Dict[str, Any]:
        """
        Determine if a candidate should be promoted.
        
        Returns decision with explanation.
        """
        # Hard constraints
        if score.risk_component > 10:  # Excessive risk
            return {
                "promote": False,
                "reason": "excessive_risk",
                "explanation": f"Risk component {score.risk_component:.3f} exceeds threshold 10"
            }
        
        if score.hallucination_severity_contrib > 2:  # High hallucination for any task
            return {
                "promote": False,
                "reason": "high_hallucination_risk",
                "explanation": f"Hallucination penalty {score.hallucination_severity_contrib:.3f} too high"
            }
        
        # Utility threshold
        if score.total_utility < minimum_threshold:
            return {
                "promote": False,
                "reason": "below_utility_threshold",
                "explanation": f"Utility {score.total_utility:.3f} below threshold {minimum_threshold:.3f}"
            }
        
        return {
            "promote": True,
            "reason": "passes_all_thresholds",
            "explanation": f"Utility {score.total_utility:.3f} acceptable, risk {score.risk_component:.3f} acceptable"
        }


# Factory function
def create_global_objective_function() -> GlobalObjectiveFunction:
    """Factory function to create global objective function"""
    return GlobalObjectiveFunction()
