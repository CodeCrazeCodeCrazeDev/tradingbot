"""
Position Rotator - Automatic position management when max_positions limit is reached

This module implements intelligent position rotation logic that automatically closes
lower-confidence or underperforming positions to make room for higher-confidence trades.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CloseReason(Enum):
    """Reasons for closing a position."""
    CONFIDENCE_ROTATION = "confidence_rotation"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    STOP_LOSS_HIT = "stop_loss_hit"
    TAKE_PROFIT_HIT = "take_profit_hit"
    CONFIDENCE_DROP = "confidence_drop"
    MANUAL = "manual"


@dataclass
class Position:
    """Represents an open trading position."""
    ticket: int
    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    lots: float
    direction: str  # 'long' or 'short'
    confidence: float  # 0.0 to 1.0
    entry_time: datetime
    pnl: float = 0.0
    pnl_pct: float = 0.0
    age_minutes: int = 0
    
    def update_metrics(self, current_price: float):
        """Update position metrics."""
        try:
            self.current_price = current_price
            self.age_minutes = int((datetime.now() - self.entry_time).total_seconds() / 60)
        
            # Calculate P&L
            if self.direction == 'long':
                self.pnl = (current_price - self.entry_price) * self.lots * 100000  # Simplified
                self.pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
            else:  # short
                self.pnl = (self.entry_price - current_price) * self.lots * 100000
                self.pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        except Exception as e:
            logger.error(f"Error in update_metrics: {e}")
            raise


@dataclass
class RotationDecision:
    """Decision about position rotation."""
    should_rotate: bool
    position_to_close: Optional[Position] = None
    reason: Optional[CloseReason] = None
    explanation: str = ""
    confidence_improvement: float = 0.0


class PositionRotator:
    """
    Intelligent position rotation manager.
    
    Features:
    - Confidence-based rotation
    - Time-based rotation (TTL)
    - Performance-based rotation
    - Configurable rotation strategies
    
    Usage:
        rotator = PositionRotator(max_positions=5)
        rotator.add_position(position)
        
        # When new signal arrives
        decision = rotator.evaluate_rotation(new_signal_confidence=0.85)
        if decision.should_rotate:
            close_position(decision.position_to_close)
            open_position(new_signal)
    """
    
    def __init__(
        self,
        max_positions: int = 5,
        min_confidence_diff: float = 0.1,
        max_position_age_minutes: int = 1440,  # 24 hours
        enable_time_rotation: bool = True,
        enable_performance_rotation: bool = True,
        min_pnl_for_protection: float = 0.5  # Protect positions with >0.5% profit
    ):
        """
        Initialize Position Rotator.
        
        Args:
            max_positions: Maximum number of open positions
            min_confidence_diff: Minimum confidence improvement required for rotation
            max_position_age_minutes: Maximum age before considering rotation
            enable_time_rotation: Enable time-based rotation
            enable_performance_rotation: Enable performance-based rotation
            min_pnl_for_protection: Minimum P&L% to protect position from rotation
        """
        try:
            self.max_positions = max_positions
            self.min_confidence_diff = min_confidence_diff
            self.max_position_age_minutes = max_position_age_minutes
            self.enable_time_rotation = enable_time_rotation
            self.enable_performance_rotation = enable_performance_rotation
            self.min_pnl_for_protection = min_pnl_for_protection
        
            self.positions: Dict[int, Position] = {}
            self.rotation_history: List[Dict] = []
        
            logger.info(
                f"PositionRotator initialized: max_positions={max_positions}, "
                f"min_confidence_diff={min_confidence_diff}"
            )
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_position(self, position: Position):
        """Add a new position to tracking."""
        try:
            self.positions[position.ticket] = position
            logger.info(
                f"Position added: {position.symbol} ticket={position.ticket} "
                f"confidence={position.confidence:.2f}"
            )
        except Exception as e:
            logger.error(f"Error in add_position: {e}")
            raise
    
    def remove_position(self, ticket: int):
        """Remove a position from tracking."""
        try:
            if ticket in self.positions:
                position = self.positions.pop(ticket)
                logger.info(f"Position removed: {position.symbol} ticket={ticket}")
        except Exception as e:
            logger.error(f"Error in remove_position: {e}")
            raise
    
    def update_position_metrics(self, ticket: int, current_price: float):
        """Update metrics for a position."""
        try:
            if ticket in self.positions:
                self.positions[ticket].update_metrics(current_price)
        except Exception as e:
            logger.error(f"Error in update_position_metrics: {e}")
            raise
    
    def evaluate_rotation(
        self,
        new_signal_confidence: float,
        new_signal_symbol: str = ""
    ) -> RotationDecision:
        """
        Evaluate whether to rotate positions for a new signal.
        
        Args:
            new_signal_confidence: Confidence of the new trading signal
            new_signal_symbol: Symbol of the new signal (optional)
        
        Returns:
            RotationDecision with recommendation
        """
        # Check if we're at max positions
        try:
            if len(self.positions) < self.max_positions:
                return RotationDecision(
                    should_rotate=False,
                    explanation="Below max positions, no rotation needed"
                )
        
            # Find candidate for rotation
            candidate = self._find_rotation_candidate(new_signal_confidence)
        
            if candidate is None:
                return RotationDecision(
                    should_rotate=False,
                    explanation="No suitable position found for rotation"
                )
        
            # Calculate confidence improvement
            confidence_improvement = new_signal_confidence - candidate.confidence
        
            # Check if improvement is sufficient
            if confidence_improvement < self.min_confidence_diff:
                return RotationDecision(
                    should_rotate=False,
                    explanation=f"Insufficient confidence improvement: {confidence_improvement:.2f}"
                )
        
            # Determine close reason
            reason = self._determine_close_reason(candidate, new_signal_confidence)
        
            # Create rotation decision
            decision = RotationDecision(
                should_rotate=True,
                position_to_close=candidate,
                reason=reason,
                explanation=f"Rotating {candidate.symbol} (conf={candidate.confidence:.2f}) "
                           f"for new signal (conf={new_signal_confidence:.2f})",
                confidence_improvement=confidence_improvement
            )
        
            # Log rotation decision
            logger.info(
                f"Rotation recommended: Close {candidate.symbol} "
                f"(ticket={candidate.ticket}, conf={candidate.confidence:.2f}, "
                f"age={candidate.age_minutes}min, pnl={candidate.pnl_pct:.2f}%) "
                f"for new signal (conf={new_signal_confidence:.2f})"
            )
        
            # Record in history
            self._record_rotation(decision)
        
            return decision
        except Exception as e:
            logger.error(f"Error in evaluate_rotation: {e}")
            raise
    
    def _find_rotation_candidate(self, new_confidence: float) -> Optional[Position]:
        """
        Find the best candidate for rotation.
        
        Priority:
        1. Positions with confidence drop
        2. Oldest positions (if time rotation enabled)
        3. Underperforming positions (if performance rotation enabled)
        4. Lowest confidence positions
        
        Args:
            new_confidence: Confidence of new signal
        
        Returns:
            Position to close, or None if no suitable candidate
        """
        try:
            if not self.positions:
                return None
        
            candidates = []
        
            for position in self.positions.values():
                # Calculate rotation score (lower is better for rotation)
                score = self._calculate_rotation_score(position, new_confidence)
                candidates.append((score, position))
        
            # Sort by score (lowest first)
            candidates.sort(key=lambda x: x[0])
        
            # Return best candidate
            if candidates:
                score, position = candidates[0]
                logger.debug(
                    f"Rotation candidate: {position.symbol} "
                    f"(score={score:.2f}, conf={position.confidence:.2f})"
                )
                return position
        
            return None
        except Exception as e:
            logger.error(f"Error in _find_rotation_candidate: {e}")
            raise
    
    def _calculate_rotation_score(self, position: Position, new_confidence: float) -> float:
        """
        Calculate rotation score for a position.
        
        Lower score = higher priority for rotation
        
        Args:
            position: Position to evaluate
            new_confidence: Confidence of new signal
        
        Returns:
            Rotation score
        """
        try:
            score = 0.0
        
            # Base score: inverse of confidence (lower confidence = lower score)
            score += (1.0 - position.confidence) * 100
        
            # Age factor (if time rotation enabled)
            if self.enable_time_rotation:
                age_factor = min(position.age_minutes / self.max_position_age_minutes, 1.0)
                score -= age_factor * 20  # Older positions get lower score
        
            # Performance factor (if performance rotation enabled)
            if self.enable_performance_rotation:
                # Protect profitable positions
                if position.pnl_pct > self.min_pnl_for_protection:
                    score += position.pnl_pct * 10  # Higher profit = higher score (less likely to close)
                elif position.pnl_pct < -1.0:
                    # Losing positions get lower score (more likely to close)
                    score += position.pnl_pct * 5
        
            # Confidence improvement factor
            confidence_improvement = new_confidence - position.confidence
            if confidence_improvement > 0:
                score -= confidence_improvement * 50  # Bigger improvement = lower score
        
            return score
        except Exception as e:
            logger.error(f"Error in _calculate_rotation_score: {e}")
            raise
    
    def _determine_close_reason(
        self,
        position: Position,
        new_confidence: float
    ) -> CloseReason:
        """Determine the reason for closing a position."""
        
        # Check time limit
        try:
            if self.enable_time_rotation and position.age_minutes >= self.max_position_age_minutes:
                return CloseReason.TIME_LIMIT_EXCEEDED
        
            # Check confidence drop
            if position.confidence < 0.5:
                return CloseReason.CONFIDENCE_DROP
        
            # Check stop loss
            if position.direction == 'long' and position.current_price <= position.stop_loss:
                return CloseReason.STOP_LOSS_HIT
            elif position.direction == 'short' and position.current_price >= position.stop_loss:
                return CloseReason.STOP_LOSS_HIT
        
            # Check take profit
            if position.direction == 'long' and position.current_price >= position.take_profit:
                return CloseReason.TAKE_PROFIT_HIT
            elif position.direction == 'short' and position.current_price <= position.take_profit:
                return CloseReason.TAKE_PROFIT_HIT
        
            # Default: confidence rotation
            return CloseReason.CONFIDENCE_ROTATION
        except Exception as e:
            logger.error(f"Error in _determine_close_reason: {e}")
            raise
    
    def _record_rotation(self, decision: RotationDecision):
        """Record rotation decision in history."""
        try:
            if decision.position_to_close:
                record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': decision.position_to_close.symbol,
                    'ticket': decision.position_to_close.ticket,
                    'confidence': decision.position_to_close.confidence,
                    'age_minutes': decision.position_to_close.age_minutes,
                    'pnl_pct': decision.position_to_close.pnl_pct,
                    'reason': decision.reason.value if decision.reason else 'unknown',
                    'confidence_improvement': decision.confidence_improvement
                }
                self.rotation_history.append(record)
            
                # Keep only last 100 rotations
                if len(self.rotation_history) > 100:
                    self.rotation_history = self.rotation_history[-100:]
        except Exception as e:
            logger.error(f"Error in _record_rotation: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rotation statistics."""
        try:
            if not self.rotation_history:
                return {
                    'total_rotations': 0,
                    'avg_confidence_improvement': 0.0,
                    'rotation_reasons': {},
                    'current_positions': len(self.positions),
                    'max_positions': self.max_positions
                }
        
            # Calculate statistics
            total_rotations = len(self.rotation_history)
            avg_confidence_improvement = sum(
                r['confidence_improvement'] for r in self.rotation_history
            ) / total_rotations
        
            # Count rotation reasons
            rotation_reasons = {}
            for record in self.rotation_history:
                reason = record['reason']
                rotation_reasons[reason] = rotation_reasons.get(reason, 0) + 1
        
            return {
                'total_rotations': total_rotations,
                'avg_confidence_improvement': avg_confidence_improvement,
                'rotation_reasons': rotation_reasons,
                'current_positions': len(self.positions),
                'max_positions': self.max_positions
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
    
    def get_current_positions(self) -> List[Position]:
        """Get list of current positions."""
        return list(self.positions.values())
    
    def is_at_max_positions(self) -> bool:
        """Check if at maximum positions."""
        return len(self.positions) >= self.max_positions
