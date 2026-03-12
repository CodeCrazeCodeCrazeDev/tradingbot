"""
Adversarial Position Sizing - STEP 8

Sizes positions using:
- Confidence-weighted risk
- Regime multiplier
- Correlation penalty
- Recent loss fatigue adjustment

RULE: Never size aggressively after drawdowns
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
import logging

from .confidence_vector import ConfidenceVector

logger = logging.getLogger(__name__)


@dataclass
class SizingFactors:
    """Factors used in position sizing"""
    base_risk_per_trade: float
    confidence_multiplier: float
    regime_multiplier: float
    correlation_penalty: float
    loss_fatigue_adjustment: float
    final_risk_per_trade: float
    final_position_size: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AdversarialPositionSizer:
    """
    Position sizer using adversarial principles.
    
    RULE: Never size aggressively after drawdowns
    RULE: Confidence-weighted risk allocation
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Base parameters
        self.base_risk_per_trade = self.config.get('base_risk_per_trade', 0.01)  # 1%
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)  # 2%
        self.min_risk_per_trade = self.config.get('min_risk_per_trade', 0.0025)  # 0.25%
        
        # Regime multipliers
        self.regime_multipliers = {
            'TRENDING': 1.2,
            'RANGING': 0.8,
            'VOLATILE': 0.6,
            'TRANSITIONING': 0.4,
            'UNKNOWN': 0.3,
        }
        
        # Drawdown thresholds for fatigue
        self.drawdown_thresholds = [
            (0.05, 0.9),   # 5% drawdown: 90% size
            (0.10, 0.7),   # 10% drawdown: 70% size
            (0.15, 0.5),   # 15% drawdown: 50% size
            (0.20, 0.25),  # 20% drawdown: 25% size
        ]
        
    def calculate_position_size(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        confidence_vector: ConfidenceVector,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> SizingFactors:
        """
        Calculate position size using adversarial factors.
        
        Returns:
            SizingFactors with all sizing components
        """
        # 1. Confidence-weighted risk
        confidence_multiplier = self._calculate_confidence_multiplier(confidence_vector)
        
        # 2. Regime multiplier
        regime_multiplier = self._calculate_regime_multiplier(market_data)
        
        # 3. Correlation penalty
        correlation_penalty = self._calculate_correlation_penalty(
            symbol, portfolio_state
        )
        
        # 4. Recent loss fatigue adjustment
        loss_fatigue = self._calculate_loss_fatigue(
            portfolio_state, historical_data
        )
        
        # Calculate final risk per trade
        final_risk = (
            self.base_risk_per_trade *
            confidence_multiplier *
            regime_multiplier *
            correlation_penalty *
            loss_fatigue
        )
        
        # Clamp to limits
        final_risk = np.clip(final_risk, self.min_risk_per_trade, self.max_risk_per_trade)
        
        # Calculate position size
        account_value = portfolio_state.get('account_value', 100000.0)
        risk_amount = account_value * final_risk
        
        # Calculate position size based on stop distance
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            logger.warning("Stop distance is zero, using minimum position size")
            position_size = account_value * self.min_risk_per_trade / entry_price
        
        return SizingFactors(
            base_risk_per_trade=self.base_risk_per_trade,
            confidence_multiplier=confidence_multiplier,
            regime_multiplier=regime_multiplier,
            correlation_penalty=correlation_penalty,
            loss_fatigue_adjustment=loss_fatigue,
            final_risk_per_trade=final_risk,
            final_position_size=position_size
        )
    
    def _calculate_confidence_multiplier(
        self,
        confidence_vector: ConfidenceVector
    ) -> float:
        """
        Calculate confidence multiplier.
        Uses minimum confidence (not average).
        """
        min_confidence = confidence_vector.get_minimum()
        
        # Linear scaling from min confidence to multiplier
        # min_conf = 0.6 → multiplier = 0.5
        # min_conf = 0.8 → multiplier = 1.0
        # min_conf = 1.0 → multiplier = 1.5
        
        if min_confidence < 0.6:
            return 0.3
        elif min_confidence < 0.8:
            # Linear interpolation between 0.6 and 0.8
            return 0.5 + (min_confidence - 0.6) / 0.2 * 0.5
        else:
            # Linear interpolation between 0.8 and 1.0
            return 1.0 + (min_confidence - 0.8) / 0.2 * 0.5
    
    def _calculate_regime_multiplier(
        self,
        market_data: Dict[str, Any]
    ) -> float:
        """Calculate regime-based multiplier"""
        regime = market_data.get('regime', 'UNKNOWN')
        multiplier = self.regime_multipliers.get(regime, 0.5)
        
        # Additional penalty for low regime stability
        regime_stability = market_data.get('regime_stability', 0.0)
        if regime_stability < 0.5:
            multiplier *= 0.7
        
        return multiplier
    
    def _calculate_correlation_penalty(
        self,
        symbol: str,
        portfolio_state: Dict[str, Any]
    ) -> float:
        """
        Calculate correlation penalty.
        Higher correlation = lower position size.
        """
        correlations = portfolio_state.get('correlations', {})
        
        # Find maximum correlation with existing positions
        max_correlation = 0.0
        for pos_symbol, pos_data in portfolio_state.get('positions', {}).items():
            if pos_symbol == symbol:
                continue
            corr = correlations.get(f"{symbol}_{pos_symbol}", 0.0)
            max_correlation = max(max_correlation, abs(corr))
        
        # Calculate penalty
        if max_correlation < 0.3:
            penalty = 1.0  # No penalty
        elif max_correlation < 0.5:
            penalty = 0.9
        elif max_correlation < 0.7:
            penalty = 0.7
        else:
            penalty = 0.5  # Heavy penalty for high correlation
        
        # Additional penalty for portfolio concentration
        concentration = portfolio_state.get('concentration', 0.0)
        if concentration > 0.3:
            penalty *= 0.8
        
        return penalty
    
    def _calculate_loss_fatigue(
        self,
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> float:
        """
        Calculate loss fatigue adjustment.
        
        RULE: Never size aggressively after drawdowns
        """
        # Check current drawdown
        current_drawdown = portfolio_state.get('current_drawdown', 0.0)
        
        # Apply drawdown-based reduction
        fatigue = 1.0
        for dd_threshold, size_multiplier in self.drawdown_thresholds:
            if current_drawdown >= dd_threshold:
                fatigue = size_multiplier
        
        # Check for recent losses
        recent_losses = historical_data.get('recent_losses', [])
        if len(recent_losses) >= 3:
            # 3+ recent losses: reduce size by 50%
            fatigue *= 0.5
        elif len(recent_losses) >= 2:
            # 2 recent losses: reduce size by 30%
            fatigue *= 0.7
        elif len(recent_losses) >= 1:
            # 1 recent loss: reduce size by 15%
            fatigue *= 0.85
        
        # Check for loss clustering
        if len(recent_losses) >= 2:
            # Check if losses are clustered (within short time)
            loss_times = [loss.get('timestamp', datetime.utcnow()) for loss in recent_losses[-3:]]
            if len(loss_times) >= 2:
                time_span = (max(loss_times) - min(loss_times)).total_seconds() / 3600
                if time_span < 24:  # Losses within 24 hours
                    fatigue *= 0.6
        
        # Check recent performance
        recent_sharpe = historical_data.get('recent_sharpe', 0.0)
        if recent_sharpe < 0:
            # Negative recent Sharpe: reduce size
            fatigue *= 0.7
        elif recent_sharpe < 0.5:
            fatigue *= 0.9
        
        return fatigue
    
    def adjust_for_gate_decision(
        self,
        sizing_factors: SizingFactors,
        gate_reduction_factor: float
    ) -> SizingFactors:
        """
        Adjust position size based on gate decision.
        
        Args:
            sizing_factors: Original sizing factors
            gate_reduction_factor: Reduction factor from decision gate (0.0 to 1.0)
            
        Returns:
            Adjusted SizingFactors
        """
        adjusted_factors = SizingFactors(
            base_risk_per_trade=sizing_factors.base_risk_per_trade,
            confidence_multiplier=sizing_factors.confidence_multiplier,
            regime_multiplier=sizing_factors.regime_multiplier,
            correlation_penalty=sizing_factors.correlation_penalty,
            loss_fatigue_adjustment=sizing_factors.loss_fatigue_adjustment,
            final_risk_per_trade=sizing_factors.final_risk_per_trade * gate_reduction_factor,
            final_position_size=sizing_factors.final_position_size * gate_reduction_factor
        )
        
        return adjusted_factors
    
    def validate_position_size(
        self,
        position_size: float,
        symbol: str,
        entry_price: float,
        portfolio_state: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that position size is within limits.
        
        Returns:
            (is_valid, rejection_reason)
        """
        account_value = portfolio_state.get('account_value', 100000.0)
        position_value = position_size * entry_price
        
        # Check maximum position value
        max_position_pct = 0.2  # 20% of account
        if position_value > account_value * max_position_pct:
            return False, f"Position exceeds {max_position_pct:.0%} of account value"
        
        # Check minimum position value
        min_position_value = 100.0  # $100 minimum
        if position_value < min_position_value:
            return False, f"Position below minimum ${min_position_value:.0f}"
        
        # Check portfolio concentration after adding position
        current_positions = portfolio_state.get('positions', {})
        total_exposure = sum(
            pos.get('value', 0.0) for pos in current_positions.values()
        )
        new_total_exposure = total_exposure + position_value
        
        if new_total_exposure > account_value * 0.95:  # 95% max exposure
            return False, "Adding position would exceed maximum portfolio exposure"
        
        return True, None
