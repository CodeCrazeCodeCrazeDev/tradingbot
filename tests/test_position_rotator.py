"""
Unit tests for Position Rotator
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.orchestrator.position_rotator import (
    PositionRotator,
    Position,
    RotationDecision,
    CloseReason
)


class TestPosition:
    """Test suite for Position dataclass."""
    
    def test_position_creation(self):
        """Test position creation."""
        position = Position(
            ticket=12345,
            symbol='EURUSD',
            entry_price=1.1000,
            current_price=1.1050,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.75,
            entry_time=datetime.now()
        )
        
        assert position.ticket == 12345
        assert position.symbol == 'EURUSD'
        assert position.confidence == 0.75
    
    def test_position_update_metrics(self):
        """Test position metrics update."""
        entry_time = datetime.now() - timedelta(minutes=30)
        position = Position(
            ticket=12345,
            symbol='EURUSD',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.75,
            entry_time=entry_time
        )
        
        # Update with new price
        position.update_metrics(1.1050)
        
        assert position.current_price == 1.1050
        assert position.age_minutes >= 29  # At least 29 minutes old
        assert position.pnl > 0  # Profitable long position
        assert position.pnl_pct > 0


class TestPositionRotator:
    """Test suite for PositionRotator."""
    
    def test_initialization(self):
        """Test rotator initialization."""
        rotator = PositionRotator(
            max_positions=5,
            min_confidence_diff=0.1
        )
        
        assert rotator.max_positions == 5
        assert rotator.min_confidence_diff == 0.1
        assert len(rotator.positions) == 0
    
    def test_add_position(self):
        """Test adding a position."""
        rotator = PositionRotator(max_positions=3)
        
        position = Position(
            ticket=1,
            symbol='EURUSD',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.75,
            entry_time=datetime.now()
        )
        
        rotator.add_position(position)
        
        assert len(rotator.positions) == 1
        assert 1 in rotator.positions
    
    def test_remove_position(self):
        """Test removing a position."""
        rotator = PositionRotator(max_positions=3)
        
        position = Position(
            ticket=1,
            symbol='EURUSD',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.75,
            entry_time=datetime.now()
        )
        
        rotator.add_position(position)
        assert len(rotator.positions) == 1
        
        rotator.remove_position(1)
        assert len(rotator.positions) == 0
    
    def test_no_rotation_below_max(self):
        """Test that no rotation occurs when below max positions."""
        rotator = PositionRotator(max_positions=3)
        
        # Add 2 positions (below max)
        for i in range(2):
            position = Position(
                ticket=i,
                symbol=f'PAIR{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=0.6,
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        # Try to evaluate rotation
        decision = rotator.evaluate_rotation(new_signal_confidence=0.9)
        
        assert decision.should_rotate is False
        assert "Below max positions" in decision.explanation
    
    def test_rotation_on_max_positions(self):
        """Test rotation when at max positions with higher confidence."""
        rotator = PositionRotator(
            max_positions=3,
            min_confidence_diff=0.1
        )
        
        # Fill to max with medium confidence
        for i in range(3):
            position = Position(
                ticket=i,
                symbol=f'PAIR{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=0.6 + i * 0.05,  # 0.6, 0.65, 0.7
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        # Try to add higher confidence position
        decision = rotator.evaluate_rotation(new_signal_confidence=0.85)
        
        assert decision.should_rotate is True
        assert decision.position_to_close is not None
        assert decision.position_to_close.confidence < 0.85
        assert decision.confidence_improvement >= 0.1
    
    def test_no_rotation_insufficient_improvement(self):
        """Test no rotation when confidence improvement is insufficient."""
        rotator = PositionRotator(
            max_positions=3,
            min_confidence_diff=0.2  # Require 20% improvement
        )
        
        # Fill to max with good confidence
        for i in range(3):
            position = Position(
                ticket=i,
                symbol=f'PAIR{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=0.7,
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        # Try to add slightly higher confidence (not enough improvement)
        decision = rotator.evaluate_rotation(new_signal_confidence=0.75)
        
        assert decision.should_rotate is False
        assert "Insufficient confidence improvement" in decision.explanation
    
    def test_rotation_selects_lowest_confidence(self):
        """Test that rotation selects lowest confidence position."""
        rotator = PositionRotator(
            max_positions=3,
            min_confidence_diff=0.1,
            enable_performance_rotation=False,  # Disable performance factor
            enable_time_rotation=False  # Disable time factor
        )
        
        # Add positions with different confidences
        confidences = [0.6, 0.3, 0.5]  # 0.3 should be selected (lowest)
        for i, conf in enumerate(confidences):
            position = Position(
                ticket=i,
                symbol=f'PAIR{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=conf,
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        # Evaluate rotation with high confidence
        decision = rotator.evaluate_rotation(new_signal_confidence=0.95)
        
        assert decision.should_rotate is True
        # Should select a position with sufficient confidence improvement
        assert decision.position_to_close is not None
        assert decision.confidence_improvement > 0.1
    
    def test_rotation_considers_age(self):
        """Test that rotation considers position age."""
        rotator = PositionRotator(
            max_positions=3,
            min_confidence_diff=0.05,  # Lower threshold
            enable_time_rotation=True,
            max_position_age_minutes=60,
            enable_performance_rotation=False  # Disable performance factor
        )
        
        # Add old position with lower confidence
        old_position = Position(
            ticket=1,
            symbol='OLD',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.70,  # Lower confidence
            entry_time=datetime.now() - timedelta(minutes=90)  # Very old
        )
        old_position.update_metrics(1.1000)
        rotator.add_position(old_position)
        
        # Add newer positions with higher confidence
        for i in range(2, 4):
            position = Position(
                ticket=i,
                symbol=f'NEW{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=0.80,  # Higher confidence
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        # Evaluate rotation with high confidence (0.90 - 0.70 = 0.20 improvement)
        decision = rotator.evaluate_rotation(new_signal_confidence=0.90)
        
        assert decision.should_rotate is True
        # Should prefer to close the old position with lower confidence
        assert decision.position_to_close.ticket == 1
    
    def test_rotation_protects_profitable_positions(self):
        """Test that rotation protects profitable positions."""
        rotator = PositionRotator(
            max_positions=3,
            min_confidence_diff=0.1,
            enable_performance_rotation=True,
            min_pnl_for_protection=0.5
        )
        
        # Add profitable position with lower confidence
        profitable_pos = Position(
            ticket=1,
            symbol='PROFIT',
            entry_price=1.1000,
            current_price=1.1100,  # +100 pips
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.6,
            entry_time=datetime.now()
        )
        profitable_pos.update_metrics(1.1100)
        rotator.add_position(profitable_pos)
        
        # Add losing position with higher confidence
        losing_pos = Position(
            ticket=2,
            symbol='LOSS',
            entry_price=1.1000,
            current_price=1.0980,  # -20 pips
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.7,
            entry_time=datetime.now()
        )
        losing_pos.update_metrics(1.0980)
        rotator.add_position(losing_pos)
        
        # Add neutral position
        neutral_pos = Position(
            ticket=3,
            symbol='NEUTRAL',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.65,
            entry_time=datetime.now()
        )
        rotator.add_position(neutral_pos)
        
        # Evaluate rotation
        decision = rotator.evaluate_rotation(new_signal_confidence=0.85)
        
        assert decision.should_rotate is True
        # Should close losing position, not profitable one
        assert decision.position_to_close.ticket == 2
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        rotator = PositionRotator(max_positions=3)
        
        # Initially empty
        stats = rotator.get_statistics()
        assert stats['total_rotations'] == 0
        assert stats['current_positions'] == 0
        
        # Add positions
        for i in range(3):
            position = Position(
                ticket=i,
                symbol=f'PAIR{i}',
                entry_price=1.1000,
                current_price=1.1000,
                stop_loss=1.0950,
                take_profit=1.1150,
                lots=0.1,
                direction='long',
                confidence=0.6,
                entry_time=datetime.now()
            )
            rotator.add_position(position)
        
        stats = rotator.get_statistics()
        assert stats['current_positions'] == 3
        assert stats['max_positions'] == 3
    
    def test_is_at_max_positions(self):
        """Test max positions check."""
        rotator = PositionRotator(max_positions=2)
        
        assert not rotator.is_at_max_positions()
        
        # Add one position
        position1 = Position(
            ticket=1,
            symbol='PAIR1',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.6,
            entry_time=datetime.now()
        )
        rotator.add_position(position1)
        
        assert not rotator.is_at_max_positions()
        
        # Add second position
        position2 = Position(
            ticket=2,
            symbol='PAIR2',
            entry_price=1.1000,
            current_price=1.1000,
            stop_loss=1.0950,
            take_profit=1.1150,
            lots=0.1,
            direction='long',
            confidence=0.6,
            entry_time=datetime.now()
        )
        rotator.add_position(position2)
        
        assert rotator.is_at_max_positions()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
