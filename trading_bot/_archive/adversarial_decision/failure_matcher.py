"""
Failure Mode Matching - STEP 6

Compares current conditions against known historical failure modes.
Similarity above threshold → REJECT TRADE
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categories of failure modes"""
    REGIME_TRANSITION = "regime_transition"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    FLASH_CRASH = "flash_crash"
    EXECUTION_FAILURE = "execution_failure"
    MODEL_DEGRADATION = "model_degradation"
    TAIL_EVENT = "tail_event"
    LOSS_CLUSTERING = "loss_clustering"


@dataclass
class FailureMode:
    """A historical failure mode"""
    failure_id: str
    category: FailureCategory
    conditions: Dict[str, Any]
    loss_amount: float
    loss_percentage: float
    timestamp: datetime
    description: str
    lessons_learned: List[str] = field(default_factory=list)
    
    def get_similarity_score(self, current_conditions: Dict[str, Any]) -> float:
        """Calculate similarity to current conditions"""
        similarity_scores = []
        
        # Compare each condition
        for key, historical_value in self.conditions.items():
            current_value = current_conditions.get(key)
            if current_value is None:
                continue
            
            # Calculate similarity based on type
            if isinstance(historical_value, (int, float)) and isinstance(current_value, (int, float)):
                # Numerical similarity
                if historical_value == 0:
                    similarity = 1.0 if current_value == 0 else 0.0
                else:
                    ratio = current_value / historical_value
                    similarity = 1.0 - min(abs(1.0 - ratio), 1.0)
                similarity_scores.append(similarity)
            
            elif isinstance(historical_value, str) and isinstance(current_value, str):
                # String similarity (exact match)
                similarity = 1.0 if historical_value == current_value else 0.0
                similarity_scores.append(similarity)
        
        # Return average similarity
        if similarity_scores:
            return np.mean(similarity_scores)
        return 0.0


class HistoricalFailureDatabase:
    """
    Database of historical failure modes.
    Stores and retrieves failure patterns.
    """
    
    def __init__(self):
        self.failures: List[FailureMode] = []
        self._initialize_known_failures()
        
    def add_failure(self, failure: FailureMode):
        """Add a failure mode to database"""
        self.failures.append(failure)
        logger.info(f"Added failure mode: {failure.failure_id} ({failure.category.value})")
    
    def find_similar_failures(
        self,
        current_conditions: Dict[str, Any],
        min_similarity: float = 0.7
    ) -> List[tuple[FailureMode, float]]:
        """
        Find failures similar to current conditions.
        
        Returns:
            List of (FailureMode, similarity_score) tuples
        """
        similar_failures = []
        
        for failure in self.failures:
            similarity = failure.get_similarity_score(current_conditions)
            if similarity >= min_similarity:
                similar_failures.append((failure, similarity))
        
        # Sort by similarity (highest first)
        similar_failures.sort(key=lambda x: x[1], reverse=True)
        
        return similar_failures
    
    def get_failures_by_category(self, category: FailureCategory) -> List[FailureMode]:
        """Get all failures in a category"""
        return [f for f in self.failures if f.category == category]
    
    def _initialize_known_failures(self):
        """Initialize with known failure patterns"""
        # Regime transition failure
        self.add_failure(FailureMode(
            failure_id="REGIME_TRANS_001",
            category=FailureCategory.REGIME_TRANSITION,
            conditions={
                'regime': 'TRANSITIONING',
                'regime_stability': 0.3,
                'volatility_percentile': 85.0,
            },
            loss_amount=-5000.0,
            loss_percentage=-0.05,
            timestamp=datetime(2024, 1, 15),
            description="Loss during regime transition with low stability",
            lessons_learned=["Avoid trading during regime transitions", "Wait for regime stability > 0.6"]
        ))
        
        # Volatility spike failure
        self.add_failure(FailureMode(
            failure_id="VOL_SPIKE_001",
            category=FailureCategory.VOLATILITY_SPIKE,
            conditions={
                'volatility_percentile': 95.0,
                'volatility_regime': 'EXTREME',
                'vol_of_vol': 0.8,
            },
            loss_amount=-8000.0,
            loss_percentage=-0.08,
            timestamp=datetime(2024, 2, 20),
            description="Extreme volatility spike caused stop-out",
            lessons_learned=["Reduce position size in extreme volatility", "Use wider stops"]
        ))
        
        # Liquidity crisis failure
        self.add_failure(FailureMode(
            failure_id="LIQ_CRISIS_001",
            category=FailureCategory.LIQUIDITY_CRISIS,
            conditions={
                'volume_ratio': 0.3,
                'bid_ask_spread': 0.002,
                'market_depth': 500.0,
            },
            loss_amount=-3000.0,
            loss_percentage=-0.03,
            timestamp=datetime(2024, 3, 10),
            description="Liquidity dried up, wide slippage on exit",
            lessons_learned=["Check volume before entry", "Avoid trading in low liquidity"]
        ))
        
        # Correlation breakdown failure
        self.add_failure(FailureMode(
            failure_id="CORR_BREAK_001",
            category=FailureCategory.CORRELATION_BREAKDOWN,
            conditions={
                'max_correlation': 0.9,
                'portfolio_concentration': 0.4,
            },
            loss_amount=-6000.0,
            loss_percentage=-0.06,
            timestamp=datetime(2024, 4, 5),
            description="Highly correlated positions all moved against us",
            lessons_learned=["Limit correlation exposure", "Diversify positions"]
        ))
        
        # Model degradation failure
        self.add_failure(FailureMode(
            failure_id="MODEL_DEG_001",
            category=FailureCategory.MODEL_DEGRADATION,
            conditions={
                'days_since_update': 120,
                'recent_sharpe': -0.5,
                'out_sample_sharpe': 0.3,
            },
            loss_amount=-4000.0,
            loss_percentage=-0.04,
            timestamp=datetime(2024, 5, 15),
            description="Model performance degraded over time",
            lessons_learned=["Retrain models regularly", "Monitor out-of-sample performance"]
        ))
        
        # Loss clustering failure
        self.add_failure(FailureMode(
            failure_id="LOSS_CLUST_001",
            category=FailureCategory.LOSS_CLUSTERING,
            conditions={
                'recent_losses': 4,
                'current_drawdown': 0.12,
            },
            loss_amount=-2000.0,
            loss_percentage=-0.02,
            timestamp=datetime(2024, 6, 20),
            description="Continued trading during drawdown, losses clustered",
            lessons_learned=["Stop trading after 3 consecutive losses", "Reduce size in drawdown"]
        ))


class FailureMatcher:
    """
    Matches current trade conditions against historical failure modes.
    
    RULE: Similarity above threshold → REJECT TRADE
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.database = HistoricalFailureDatabase()
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
    def check_failure_match(
        self,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if current conditions match historical failure modes.
        
        Returns:
            Dictionary with match results and decision
        """
        # Build current conditions
        current_conditions = self._build_current_conditions(
            market_data, signal_data, portfolio_state, historical_data
        )
        
        # Find similar failures
        similar_failures = self.database.find_similar_failures(
            current_conditions,
            min_similarity=self.similarity_threshold
        )
        
        # Determine if we should reject
        should_reject = len(similar_failures) > 0
        
        # Get rejection reason
        rejection_reason = None
        if should_reject:
            top_failure, similarity = similar_failures[0]
            rejection_reason = (
                f"Similar to historical failure {top_failure.failure_id} "
                f"({top_failure.category.value}) with {similarity:.1%} similarity. "
                f"Previous loss: {top_failure.loss_percentage:.2%}. "
                f"Lesson: {top_failure.lessons_learned[0] if top_failure.lessons_learned else 'N/A'}"
            )
        
        return {
            'should_reject': should_reject,
            'similar_failures': similar_failures,
            'match_count': len(similar_failures),
            'rejection_reason': rejection_reason,
            'current_conditions': current_conditions
        }
    
    def _build_current_conditions(
        self,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build current conditions dictionary"""
        conditions = {}
        
        # Market conditions
        conditions['regime'] = market_data.get('regime', 'UNKNOWN')
        conditions['regime_stability'] = market_data.get('regime_stability', 0.0)
        conditions['volatility_percentile'] = market_data.get('volatility_percentile', 50.0)
        conditions['volatility_regime'] = market_data.get('volatility_regime', 'NORMAL')
        conditions['vol_of_vol'] = market_data.get('vol_of_vol', 0.0)
        
        # Liquidity conditions
        conditions['volume_ratio'] = market_data.get('volume', 0.0) / max(market_data.get('avg_volume', 1.0), 1.0)
        conditions['bid_ask_spread'] = market_data.get('bid_ask_spread', 0.0)
        conditions['market_depth'] = market_data.get('market_depth', 0.0)
        
        # Portfolio conditions
        conditions['max_correlation'] = portfolio_state.get('correlations', {}).get('max', 0.0)
        conditions['portfolio_concentration'] = portfolio_state.get('concentration', 0.0)
        conditions['current_drawdown'] = historical_data.get('current_drawdown', 0.0)
        conditions['recent_losses'] = len(historical_data.get('recent_losses', []))
        
        # Model conditions
        model_last_updated = signal_data.get('model_last_updated')
        if model_last_updated:
            conditions['days_since_update'] = (datetime.utcnow() - model_last_updated).days
        else:
            conditions['days_since_update'] = 999
        
        conditions['recent_sharpe'] = historical_data.get('recent_sharpe', 0.0)
        conditions['out_sample_sharpe'] = signal_data.get('out_sample_sharpe', 0.0)
        
        return conditions
    
    def add_new_failure(
        self,
        category: FailureCategory,
        conditions: Dict[str, Any],
        loss_amount: float,
        loss_percentage: float,
        description: str,
        lessons_learned: List[str] = None
    ):
        """Add a new failure mode from recent experience"""
        failure_id = f"{category.value.upper()}_{len(self.database.failures):03d}"
        
        failure = FailureMode(
            failure_id=failure_id,
            category=category,
            conditions=conditions,
            loss_amount=loss_amount,
            loss_percentage=loss_percentage,
            timestamp=datetime.utcnow(),
            description=description,
            lessons_learned=lessons_learned or []
        )
        
        self.database.add_failure(failure)
        logger.info(f"Learned new failure mode: {failure_id}")
