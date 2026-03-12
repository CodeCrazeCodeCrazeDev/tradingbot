"""
Confidence-Weighted Position Sizing - Stage 6 Fix

Addresses violations:
- Signal strength may dominate
- Not confidence-vector weighted
- Regime adjustment basic
- Correlation penalty weak

Position sizing MUST use confidence vectors with HEAVY correlation penalties.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PositionSizingResult:
    """Result of position sizing calculation"""
    signal_id: str
    symbol: str
    
    # Inputs
    base_quantity: float
    base_risk_pct: float
    
    # Adjustments
    confidence_multiplier: float
    regime_multiplier: float
    correlation_penalty: float
    volatility_adjustment: float
    drawdown_cap: float
    
    # Final output
    final_quantity: float
    final_risk_pct: float
    
    # Explanation
    sizing_breakdown: Dict[str, float]
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.utcnow()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class ConfidenceWeightedPositionSizer:
    """
    Position sizer that uses confidence VECTORS (not single scores).
    
    Formula:
    size = base × min_confidence × regime_conf × (1 - correlation)^2 × vol_adj × dd_cap
    
    Key principles:
    - Use MINIMUM confidence (not average)
    - HEAVY correlation penalty (squared)
    - Regime confidence weighting
    - Volatility adjustment
    - Drawdown cap
    """
    
    def __init__(
        self,
        base_risk_pct: float = 0.02,  # 2% base risk
        max_risk_pct: float = 0.05,   # 5% max risk
        correlation_penalty_power: float = 2.0  # Squared penalty
    ):
        try:
            self.base_risk_pct = base_risk_pct
            self.max_risk_pct = max_risk_pct
            self.correlation_penalty_power = correlation_penalty_power
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_position_size(
        self,
        signal: Dict,
        confidence_vector: Any,
        market_context: Dict,
        portfolio_state: Dict
    ) -> PositionSizingResult:
        """
        Calculate position size using confidence vector.
        
        Args:
            signal: Signal data
            confidence_vector: Multi-dimensional confidence vector
            market_context: Market conditions
            portfolio_state: Portfolio state
            
        Returns:
            PositionSizingResult with final size
        """
        try:
            signal_id = signal.get('signal_id', 'unknown')
            symbol = signal['symbol']
            base_quantity = signal.get('quantity', 1.0)
        
            # Step 1: Confidence multiplier (use MINIMUM, not average)
            min_confidence = confidence_vector.penalized_minimum_confidence
            confidence_multiplier = min_confidence
        
            # Step 2: Regime confidence multiplier
            regime_confidence = confidence_vector.regime_confidence
            regime_multiplier = regime_confidence
        
            # Step 3: Correlation penalty (HEAVY - squared)
            correlation = market_context.get('correlation_exposure', 0.0)
            # (1 - correlation)^2 means:
            # correlation=0.0 → penalty=1.0 (no penalty)
            # correlation=0.5 → penalty=0.25 (75% reduction)
            # correlation=0.7 → penalty=0.09 (91% reduction)
            # correlation=0.9 → penalty=0.01 (99% reduction)
            correlation_penalty = (1.0 - correlation) ** self.correlation_penalty_power
        
            # Step 4: Volatility adjustment
            current_volatility = market_context.get('volatility', 0.15)
            target_volatility = 0.15  # Target volatility
            # If volatility is high, reduce size
            volatility_adjustment = min(target_volatility / current_volatility, 1.0) if current_volatility > 0 else 1.0
        
            # Step 5: Drawdown cap
            current_drawdown = portfolio_state.get('drawdown', 0.0)
            max_drawdown = 0.15  # 15% max drawdown
        
            if current_drawdown >= max_drawdown:
                drawdown_cap = 0.0  # No trading at max drawdown
            elif current_drawdown >= max_drawdown * 0.8:  # 12%+
                drawdown_cap = 0.2  # Reduce to 20%
            elif current_drawdown >= max_drawdown * 0.6:  # 9%+
                drawdown_cap = 0.5  # Reduce to 50%
            elif current_drawdown >= max_drawdown * 0.4:  # 6%+
                drawdown_cap = 0.75  # Reduce to 75%
            else:
                drawdown_cap = 1.0  # No reduction
        
            # Calculate final multiplier
            total_multiplier = (
                confidence_multiplier *
                regime_multiplier *
                correlation_penalty *
                volatility_adjustment *
                drawdown_cap
            )
        
            # Apply to base quantity
            final_quantity = base_quantity * total_multiplier
        
            # Calculate risk percentages
            entry_price = signal['price']
            stop_loss = signal.get('stop_loss', entry_price * 0.95)
            risk_per_unit = abs(entry_price - stop_loss)
        
            portfolio_value = portfolio_state.get('value', 100000.0)
            base_risk_dollars = portfolio_value * self.base_risk_pct
            final_risk_dollars = final_quantity * risk_per_unit
            final_risk_pct = final_risk_dollars / portfolio_value if portfolio_value > 0 else 0.0
        
            # Cap at max risk
            if final_risk_pct > self.max_risk_pct:
                final_quantity = (portfolio_value * self.max_risk_pct) / risk_per_unit if risk_per_unit > 0 else 0.0
                final_risk_pct = self.max_risk_pct
        
            # Create result
            result = PositionSizingResult(
                signal_id=signal_id,
                symbol=symbol,
                base_quantity=base_quantity,
                base_risk_pct=self.base_risk_pct,
                confidence_multiplier=confidence_multiplier,
                regime_multiplier=regime_multiplier,
                correlation_penalty=correlation_penalty,
                volatility_adjustment=volatility_adjustment,
                drawdown_cap=drawdown_cap,
                final_quantity=final_quantity,
                final_risk_pct=final_risk_pct,
                sizing_breakdown={
                    'base_quantity': base_quantity,
                    'confidence_multiplier': confidence_multiplier,
                    'regime_multiplier': regime_multiplier,
                    'correlation_penalty': correlation_penalty,
                    'volatility_adjustment': volatility_adjustment,
                    'drawdown_cap': drawdown_cap,
                    'total_multiplier': total_multiplier,
                    'final_quantity': final_quantity,
                    'final_risk_pct': final_risk_pct
                }
            )
        
            logger.info(
                f"Position sizing for {symbol}:\n"
                f"  Base quantity: {base_quantity:.4f}\n"
                f"  Confidence multiplier: {confidence_multiplier:.2%} (min confidence)\n"
                f"  Regime multiplier: {regime_multiplier:.2%}\n"
                f"  Correlation penalty: {correlation_penalty:.2%} (correlation={correlation:.2%})\n"
                f"  Volatility adjustment: {volatility_adjustment:.2%}\n"
                f"  Drawdown cap: {drawdown_cap:.2%} (drawdown={current_drawdown:.2%})\n"
                f"  Total multiplier: {total_multiplier:.2%}\n"
                f"  FINAL QUANTITY: {final_quantity:.4f}\n"
                f"  Final risk: {final_risk_pct:.2%}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in calculate_position_size: {e}")
            raise
    
    def validate_position_size(
        self,
        result: PositionSizingResult,
        portfolio_state: Dict
    ) -> bool:
        """
        Validate position size is acceptable.
        
        Returns:
            True if valid
        """
        # Check 1: Risk within limits
        try:
            if result.final_risk_pct > self.max_risk_pct:
                logger.warning(f"Position risk {result.final_risk_pct:.2%} exceeds max {self.max_risk_pct:.2%}")
                return False
        
            # Check 2: Quantity is positive
            if result.final_quantity <= 0:
                logger.warning(f"Position quantity {result.final_quantity} is not positive")
                return False
        
            # Check 3: Not too small (minimum $100 position)
            portfolio_value = portfolio_state.get('value', 100000.0)
            min_position_value = 100.0
        
            # Assuming we have price in the result
            # This is a simplified check
            if result.final_quantity < 0.001:  # Very small quantity
                logger.warning(f"Position quantity {result.final_quantity} too small")
                return False
        
            return True
        except Exception as e:
            logger.error(f"Error in validate_position_size: {e}")
            raise


class CorrelationPenaltyCalculator:
    """
    Calculates HEAVY correlation penalties.
    
    Correlation is DANGEROUS and must be heavily penalized.
    """
    
    @staticmethod
    def calculate_penalty(
        correlation: float,
        penalty_power: float = 2.0
    ) -> float:
        """
        Calculate correlation penalty.
        
        Args:
            correlation: Current correlation (0.0 to 1.0)
            penalty_power: Power to raise penalty (default 2.0 = squared)
            
        Returns:
            Penalty multiplier (0.0 to 1.0)
        """
        # (1 - correlation)^power
        try:
            penalty = (1.0 - correlation) ** penalty_power
        
            return penalty
        except Exception as e:
            logger.error(f"Error in calculate_penalty: {e}")
            raise
    
    @staticmethod
    def get_penalty_table() -> Dict[float, float]:
        """Get penalty table for reference"""
        try:
            correlations = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
            table = {}
            for corr in correlations:
                penalty = CorrelationPenaltyCalculator.calculate_penalty(corr, penalty_power=2.0)
                table[corr] = penalty
        
            return table
        except Exception as e:
            logger.error(f"Error in get_penalty_table: {e}")
            raise


class DrawdownCapCalculator:
    """
    Calculates drawdown cap.
    
    As drawdown increases, reduce position sizes aggressively.
    """
    
    @staticmethod
    def calculate_cap(
        current_drawdown: float,
        max_drawdown: float = 0.15
    ) -> float:
        """
        Calculate drawdown cap.
        
        Args:
            current_drawdown: Current drawdown (0.0 to 1.0)
            max_drawdown: Maximum acceptable drawdown
            
        Returns:
            Cap multiplier (0.0 to 1.0)
        """
        try:
            if current_drawdown >= max_drawdown:
                return 0.0  # No trading at max drawdown
            elif current_drawdown >= max_drawdown * 0.8:  # 80% of max
                return 0.2  # Reduce to 20%
            elif current_drawdown >= max_drawdown * 0.6:  # 60% of max
                return 0.5  # Reduce to 50%
            elif current_drawdown >= max_drawdown * 0.4:  # 40% of max
                return 0.75  # Reduce to 75%
            else:
                return 1.0  # No reduction
        except Exception as e:
            logger.error(f"Error in calculate_cap: {e}")
            raise
    
    @staticmethod
    def get_cap_table(max_drawdown: float = 0.15) -> Dict[float, float]:
        """Get cap table for reference"""
        try:
            drawdowns = [0.0, 0.03, 0.06, 0.09, 0.12, 0.15]
        
            table = {}
            for dd in drawdowns:
                cap = DrawdownCapCalculator.calculate_cap(dd, max_drawdown)
                table[dd] = cap
        
            return table
        except Exception as e:
            logger.error(f"Error in get_cap_table: {e}")
            raise


# Global singleton
_global_sizer: Optional[ConfidenceWeightedPositionSizer] = None


def get_global_sizer() -> ConfidenceWeightedPositionSizer:
    """Get global sizer singleton"""
    try:
        global _global_sizer
        if _global_sizer is None:
            _global_sizer = ConfidenceWeightedPositionSizer()
        return _global_sizer
    except Exception as e:
        logger.error(f"Error in get_global_sizer: {e}")
        raise


def calculate_position_size(
    signal: Dict,
    confidence_vector: Any,
    market_context: Dict,
    portfolio_state: Dict
) -> PositionSizingResult:
    """Calculate position size using global sizer"""
    return get_global_sizer().calculate_position_size(
        signal,
        confidence_vector,
        market_context,
        portfolio_state
    )


def validate_position_size(
    result: PositionSizingResult,
    portfolio_state: Dict
) -> bool:
    """Validate position size"""
    return get_global_sizer().validate_position_size(result, portfolio_state)
