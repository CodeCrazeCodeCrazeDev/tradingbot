"""
Feature Ranking & Pruning Module
================================
Rank features by:
- Risk-adjusted return after costs
- Stability across regimes
- Low correlation with existing features
- Capacity potential
- Robustness score

Only promote top features into production models.

Author: AlphaAlgo Research Team
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    FeatureFamily,
    FeatureRanking,
    HARD_LIMITS,
    ProductionStatus,
    TestingResult,
    generate_id
)

logger = logging.getLogger(__name__)


class RankingCriteria(Enum):
    """Criteria for ranking features"""
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"
    STABILITY = "stability"
    CORRELATION = "correlation"
    CAPACITY = "capacity"
    ROBUSTNESS = "robustness"


@dataclass
class RankingWeights:
    """Weights for ranking criteria"""
    risk_adjusted_return: float = 0.35
    stability: float = 0.20
    correlation: float = 0.15
    capacity: float = 0.15
    robustness: float = 0.15
    
    def validate(self) -> bool:
        """Validate weights sum to 1"""
        try:
            total = (
                self.risk_adjusted_return +
                self.stability +
                self.correlation +
                self.capacity +
                self.robustness
            )
            return abs(total - 1.0) < 0.01
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


@dataclass
class CorrelationMatrix:
    """Correlation matrix for features"""
    feature_ids: List[str]
    matrix: np.ndarray
    
    def get_correlation(self, id1: str, id2: str) -> float:
        """Get correlation between two features"""
        try:
            if id1 not in self.feature_ids or id2 not in self.feature_ids:
                return 0.0
        
            idx1 = self.feature_ids.index(id1)
            idx2 = self.feature_ids.index(id2)
            return self.matrix[idx1, idx2]
        except Exception as e:
            logger.error(f"Error in get_correlation: {e}")
            raise
    
    def get_max_correlation_with_existing(
        self,
        new_id: str,
        existing_ids: List[str]
    ) -> float:
        """Get maximum correlation of new feature with existing features"""
        try:
            if new_id not in self.feature_ids:
                return 0.0
        
            max_corr = 0.0
            for existing_id in existing_ids:
                corr = abs(self.get_correlation(new_id, existing_id))
                max_corr = max(max_corr, corr)
        
            return max_corr
        except Exception as e:
            logger.error(f"Error in get_max_correlation_with_existing: {e}")
            raise


@dataclass
class RankedFeature:
    """A feature with its ranking information"""
    family_id: str
    family_name: str
    
    # Individual scores (0-1, higher is better)
    risk_adjusted_score: float = 0.0
    stability_score: float = 0.0
    correlation_score: float = 0.0  # Lower correlation = higher score
    capacity_score: float = 0.0
    robustness_score: float = 0.0
    
    # Composite
    composite_score: float = 0.0
    rank: int = 0
    
    # Metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    capacity_usd: float = 0.0
    
    # Decision
    promoted: bool = False
    promotion_reason: str = ""
    rejection_reason: str = ""


class RiskAdjustedScorer:
    """Score features by risk-adjusted returns"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_sharpe = self.config.get("min_sharpe", 0.5)
            self.max_sharpe = self.config.get("max_sharpe", 3.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score(self, testing_result: TestingResult) -> float:
        """Score based on risk-adjusted returns"""
        # Use cost-adjusted Sharpe as primary metric
        try:
            sharpe = testing_result.cost_adjusted_metrics.sharpe_ratio
        
            # Normalize to 0-1 scale
            if sharpe <= self.min_sharpe:
                return 0.0
            elif sharpe >= self.max_sharpe:
                return 1.0
            else:
                return (sharpe - self.min_sharpe) / (self.max_sharpe - self.min_sharpe)
        except Exception as e:
            logger.error(f"Error in score: {e}")
            raise
    
    def get_sharpe(self, testing_result: TestingResult) -> float:
        """Get the Sharpe ratio"""
        return testing_result.cost_adjusted_metrics.sharpe_ratio


class StabilityScorer:
    """Score features by stability across regimes"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_regimes_positive = self.config.get("min_regimes_positive", 3)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score(self, testing_result: TestingResult) -> float:
        """Score based on stability across regimes"""
        try:
            regime_metrics = testing_result.regime_metrics
        
            if not regime_metrics:
                return 0.0
        
            # Count regimes with positive Sharpe
            positive_regimes = sum(
                1 for metrics in regime_metrics.values()
                if metrics.sharpe_ratio > 0
            )
        
            total_regimes = len(regime_metrics)
        
            if total_regimes == 0:
                return 0.0
        
            # Score based on proportion of positive regimes
            base_score = positive_regimes / total_regimes
        
            # Bonus for consistency (low variance in Sharpe across regimes)
            sharpe_values = [m.sharpe_ratio for m in regime_metrics.values()]
            if len(sharpe_values) > 1:
                sharpe_std = np.std(sharpe_values)
                sharpe_mean = np.mean(sharpe_values)
            
                if sharpe_mean > 0:
                    cv = sharpe_std / sharpe_mean  # Coefficient of variation
                    consistency_bonus = max(0, 1 - cv) * 0.2
                    base_score = min(1.0, base_score + consistency_bonus)
        
            return base_score
        except Exception as e:
            logger.error(f"Error in score: {e}")
            raise


class CorrelationScorer:
    """Score features by correlation with existing features"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.max_correlation = self.config.get("max_correlation", HARD_LIMITS.MAX_CORRELATION_WITH_EXISTING)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score(
        self,
        family_id: str,
        correlation_matrix: Optional[CorrelationMatrix],
        existing_family_ids: List[str]
    ) -> float:
        """Score based on correlation with existing features"""
        try:
            if not correlation_matrix or not existing_family_ids:
                return 1.0  # No existing features, perfect score
        
            max_corr = correlation_matrix.get_max_correlation_with_existing(
                family_id,
                existing_family_ids
            )
        
            # Lower correlation = higher score
            if max_corr >= self.max_correlation:
                return 0.0
            else:
                return 1.0 - (max_corr / self.max_correlation)
        except Exception as e:
            logger.error(f"Error in score: {e}")
            raise


class CapacityScorer:
    """Score features by capacity potential"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.min_capacity = self.config.get("min_capacity", HARD_LIMITS.MIN_CAPACITY_USD)
            self.target_capacity = self.config.get("target_capacity", 100_000_000)  # $100M
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score(self, family: FeatureFamily) -> float:
        """Score based on capacity"""
        try:
            capacity = family.capacity_limit_usd
        
            if capacity < self.min_capacity:
                return 0.0
            elif capacity >= self.target_capacity:
                return 1.0
            else:
                # Log scale for capacity
                log_min = np.log10(self.min_capacity)
                log_target = np.log10(self.target_capacity)
                log_capacity = np.log10(capacity)
            
                return (log_capacity - log_min) / (log_target - log_min)
        except Exception as e:
            logger.error(f"Error in score: {e}")
            raise


class RobustnessScorer:
    """Score features by robustness"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score(self, testing_result: TestingResult) -> float:
        """Score based on robustness"""
        # Combine parameter stability and data robustness
        try:
            param_score = testing_result.parameter_stability_score
            data_score = testing_result.data_robustness_score
        
            # Weight equally
            return (param_score + data_score) / 2
        except Exception as e:
            logger.error(f"Error in score: {e}")
            raise


class FeatureRanker:
    """
    Rank and prune feature families.
    
    Uses multiple criteria:
    - Risk-adjusted return after costs
    - Stability across regimes
    - Low correlation with existing features
    - Capacity potential
    - Robustness score
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize weights
            self.weights = RankingWeights(
                risk_adjusted_return=self.config.get("weight_risk_adjusted", 0.35),
                stability=self.config.get("weight_stability", 0.20),
                correlation=self.config.get("weight_correlation", 0.15),
                capacity=self.config.get("weight_capacity", 0.15),
                robustness=self.config.get("weight_robustness", 0.15)
            )
        
            # Initialize scorers
            self.risk_scorer = RiskAdjustedScorer(config)
            self.stability_scorer = StabilityScorer(config)
            self.correlation_scorer = CorrelationScorer(config)
            self.capacity_scorer = CapacityScorer(config)
            self.robustness_scorer = RobustnessScorer(config)
        
            # Promotion thresholds
            self.min_composite_score = self.config.get("min_composite_score", 0.5)
            self.max_promoted = self.config.get("max_promoted", 10)
        
            logger.info("Feature Ranker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def rank_families(
        self,
        families: List[FeatureFamily],
        testing_results: Dict[str, TestingResult],
        existing_family_ids: Optional[List[str]] = None,
        correlation_matrix: Optional[CorrelationMatrix] = None
    ) -> List[RankedFeature]:
        """Rank all feature families"""
        try:
            existing_family_ids = existing_family_ids or []
            ranked_features = []
        
            for family in families:
                testing_result = testing_results.get(family.family_id)
            
                if not testing_result:
                    logger.warning(f"No testing results for family {family.family_id}")
                    continue
            
                # Skip if failed all tests
                if not testing_result.all_tests_passed:
                    logger.info(f"Family {family.family_id} failed tests, skipping")
                    continue
            
                # Score each criterion
                risk_score = self.risk_scorer.score(testing_result)
                stability_score = self.stability_scorer.score(testing_result)
                correlation_score = self.correlation_scorer.score(
                    family.family_id,
                    correlation_matrix,
                    existing_family_ids
                )
                capacity_score = self.capacity_scorer.score(family)
                robustness_score = self.robustness_scorer.score(testing_result)
            
                # Compute composite score
                composite_score = (
                    self.weights.risk_adjusted_return * risk_score +
                    self.weights.stability * stability_score +
                    self.weights.correlation * correlation_score +
                    self.weights.capacity * capacity_score +
                    self.weights.robustness * robustness_score
                )
            
                ranked_feature = RankedFeature(
                    family_id=family.family_id,
                    family_name=family.name,
                    risk_adjusted_score=risk_score,
                    stability_score=stability_score,
                    correlation_score=correlation_score,
                    capacity_score=capacity_score,
                    robustness_score=robustness_score,
                    composite_score=composite_score,
                    sharpe_ratio=self.risk_scorer.get_sharpe(testing_result),
                    max_drawdown=testing_result.cost_adjusted_metrics.max_drawdown,
                    capacity_usd=family.capacity_limit_usd
                )
            
                ranked_features.append(ranked_feature)
        
            # Sort by composite score (descending)
            ranked_features.sort(key=lambda x: x.composite_score, reverse=True)
        
            # Assign ranks
            for i, rf in enumerate(ranked_features):
                rf.rank = i + 1
        
            return ranked_features
        except Exception as e:
            logger.error(f"Error in rank_families: {e}")
            raise
    
    def select_for_promotion(
        self,
        ranked_features: List[RankedFeature],
        existing_family_ids: Optional[List[str]] = None
    ) -> Tuple[List[RankedFeature], List[RankedFeature]]:
        """Select features for promotion to production"""
        try:
            existing_family_ids = existing_family_ids or []
        
            promoted = []
            rejected = []
        
            for rf in ranked_features:
                # Check minimum score
                if rf.composite_score < self.min_composite_score:
                    rf.promoted = False
                    rf.rejection_reason = f"Composite score {rf.composite_score:.2f} < {self.min_composite_score}"
                    rejected.append(rf)
                    continue
            
                # Check correlation with already promoted
                if rf.correlation_score < 0.3:  # High correlation with existing
                    rf.promoted = False
                    rf.rejection_reason = "Too correlated with existing features"
                    rejected.append(rf)
                    continue
            
                # Check max promoted limit
                if len(promoted) >= self.max_promoted:
                    rf.promoted = False
                    rf.rejection_reason = f"Max promoted limit ({self.max_promoted}) reached"
                    rejected.append(rf)
                    continue
            
                # Promote
                rf.promoted = True
                rf.promotion_reason = self._generate_promotion_reason(rf)
                promoted.append(rf)
        
            logger.info(f"Promoted {len(promoted)} features, rejected {len(rejected)}")
        
            return promoted, rejected
        except Exception as e:
            logger.error(f"Error in select_for_promotion: {e}")
            raise
    
    def _generate_promotion_reason(self, rf: RankedFeature) -> str:
        """Generate promotion reason"""
        try:
            reasons = []
        
            if rf.risk_adjusted_score >= 0.7:
                reasons.append(f"Strong risk-adjusted returns (Sharpe: {rf.sharpe_ratio:.2f})")
        
            if rf.stability_score >= 0.7:
                reasons.append("Stable across regimes")
        
            if rf.correlation_score >= 0.7:
                reasons.append("Low correlation with existing features")
        
            if rf.capacity_score >= 0.7:
                reasons.append(f"Good capacity (${rf.capacity_usd/1e6:.1f}M)")
        
            if rf.robustness_score >= 0.7:
                reasons.append("Robust to parameter changes and data errors")
        
            return "; ".join(reasons) if reasons else "Met all minimum criteria"
        except Exception as e:
            logger.error(f"Error in _generate_promotion_reason: {e}")
            raise


class FeaturePruner:
    """
    Prune features that no longer meet criteria.
    
    Removes features that:
    - Have decayed below threshold
    - Are too correlated with better features
    - Have insufficient capacity
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            self.min_sharpe = self.config.get("min_sharpe_for_retention", 0.3)
            self.max_correlation = self.config.get("max_correlation", 0.7)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def prune(
        self,
        families: List[FeatureFamily],
        current_metrics: Dict[str, TestingResult],
        correlation_matrix: Optional[CorrelationMatrix] = None
    ) -> Tuple[List[FeatureFamily], List[Tuple[FeatureFamily, str]]]:
        """Prune underperforming features"""
        try:
            retained = []
            pruned = []
        
            # Sort by current Sharpe (best first)
            sorted_families = sorted(
                families,
                key=lambda f: current_metrics.get(f.family_id, TestingResult("", "")).cost_adjusted_metrics.sharpe_ratio,
                reverse=True
            )
        
            retained_ids = []
        
            for family in sorted_families:
                metrics = current_metrics.get(family.family_id)
            
                if not metrics:
                    pruned.append((family, "No current metrics available"))
                    continue
            
                sharpe = metrics.cost_adjusted_metrics.sharpe_ratio
            
                # Check Sharpe threshold
                if sharpe < self.min_sharpe:
                    pruned.append((family, f"Sharpe {sharpe:.2f} below threshold {self.min_sharpe}"))
                    continue
            
                # Check correlation with retained features
                if correlation_matrix and retained_ids:
                    max_corr = correlation_matrix.get_max_correlation_with_existing(
                        family.family_id,
                        retained_ids
                    )
                
                    if max_corr > self.max_correlation:
                        pruned.append((family, f"Correlation {max_corr:.2f} too high with retained features"))
                        continue
            
                retained.append(family)
                retained_ids.append(family.family_id)
        
            logger.info(f"Retained {len(retained)} features, pruned {len(pruned)}")
        
            return retained, pruned
        except Exception as e:
            logger.error(f"Error in prune: {e}")
            raise


class FeatureRankingEngine:
    """
    Main engine for feature ranking and pruning.
    
    Coordinates:
    - Ranking by multiple criteria
    - Selection for promotion
    - Pruning of underperformers
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            self.ranker = FeatureRanker(config)
            self.pruner = FeaturePruner(config)
        
            # Track promoted features
            self.promoted_family_ids: List[str] = []
        
            logger.info("Feature Ranking Engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def rank_and_promote(
        self,
        families: List[FeatureFamily],
        testing_results: Dict[str, TestingResult],
        correlation_matrix: Optional[CorrelationMatrix] = None
    ) -> Tuple[List[FeatureFamily], List[FeatureRanking]]:
        """Rank families and promote top performers"""
        
        # Rank all families
        try:
            ranked_features = self.ranker.rank_families(
                families,
                testing_results,
                self.promoted_family_ids,
                correlation_matrix
            )
        
            # Select for promotion
            promoted, rejected = self.ranker.select_for_promotion(
                ranked_features,
                self.promoted_family_ids
            )
        
            # Update promoted list
            for rf in promoted:
                if rf.family_id not in self.promoted_family_ids:
                    self.promoted_family_ids.append(rf.family_id)
        
            # Create FeatureRanking objects
            rankings = []
            for rf in ranked_features:
                ranking = FeatureRanking(
                    family_id=rf.family_id,
                    risk_adjusted_return_rank=self._get_rank_for_score(ranked_features, rf, "risk_adjusted_score"),
                    stability_rank=self._get_rank_for_score(ranked_features, rf, "stability_score"),
                    correlation_rank=self._get_rank_for_score(ranked_features, rf, "correlation_score"),
                    capacity_rank=self._get_rank_for_score(ranked_features, rf, "capacity_score"),
                    robustness_rank=self._get_rank_for_score(ranked_features, rf, "robustness_score"),
                    composite_score=rf.composite_score,
                    composite_rank=rf.rank,
                    promoted=rf.promoted,
                    promotion_reason=rf.promotion_reason if rf.promoted else rf.rejection_reason
                )
                rankings.append(ranking)
        
            # Get promoted families
            promoted_families = [
                f for f in families
                if f.family_id in [rf.family_id for rf in promoted]
            ]
        
            # Update status
            for family in promoted_families:
                family.status = ProductionStatus.PROMOTED
        
            return promoted_families, rankings
        except Exception as e:
            logger.error(f"Error in rank_and_promote: {e}")
            raise
    
    def _get_rank_for_score(
        self,
        ranked_features: List[RankedFeature],
        target: RankedFeature,
        score_attr: str
    ) -> int:
        """Get rank for a specific score attribute"""
        try:
            sorted_by_score = sorted(
                ranked_features,
                key=lambda x: getattr(x, score_attr),
                reverse=True
            )
        
            for i, rf in enumerate(sorted_by_score):
                if rf.family_id == target.family_id:
                    return i + 1
        
            return len(ranked_features)
        except Exception as e:
            logger.error(f"Error in _get_rank_for_score: {e}")
            raise
    
    def prune_underperformers(
        self,
        families: List[FeatureFamily],
        current_metrics: Dict[str, TestingResult],
        correlation_matrix: Optional[CorrelationMatrix] = None
    ) -> Tuple[List[FeatureFamily], List[Tuple[FeatureFamily, str]]]:
        """Prune underperforming features"""
        try:
            retained, pruned = self.pruner.prune(
                families,
                current_metrics,
                correlation_matrix
            )
        
            # Update promoted list
            pruned_ids = [f.family_id for f, _ in pruned]
            self.promoted_family_ids = [
                fid for fid in self.promoted_family_ids
                if fid not in pruned_ids
            ]
        
            # Update status
            for family, _ in pruned:
                family.status = ProductionStatus.RETIRED
        
            return retained, pruned
        except Exception as e:
            logger.error(f"Error in prune_underperformers: {e}")
            raise
    
    def get_promoted_count(self) -> int:
        """Get count of promoted features"""
        return len(self.promoted_family_ids)


def create_ranking_engine(config: Optional[Dict] = None) -> FeatureRankingEngine:
    """Factory function to create ranking engine"""
    return FeatureRankingEngine(config)
