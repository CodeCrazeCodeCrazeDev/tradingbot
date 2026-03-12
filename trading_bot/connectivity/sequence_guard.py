"""
Sequence Guard - Tick Deduplication System
Implements HI-DAT-004: Sequence/duplication guard for ticks

Prevents duplicate ticks and ensures proper temporal ordering.
Critical for data integrity in real-time trading.
"""

import logging
from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import deque
from typing import List
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass
class TickData:
    """Tick data with sequence information"""
    symbol: str
    sequence: int
    timestamp: float
    price: float
    volume: float


class SequenceGuard:
    """
    Prevents duplicate ticks and ensures proper ordering
    
    Features:
    - Duplicate detection by sequence number
    - Temporal ordering validation
    - Gap detection
    - Statistics tracking
    """
    
    def __init__(self, max_history: int = 10000):
        try:
            self.max_history = max_history
        
            # Track seen sequences per symbol
            self.seen_sequences: Dict[str, Set[int]] = {}
            self.last_sequence: Dict[str, int] = {}
            self.last_timestamp: Dict[str, float] = {}
        
            # Gap tracking
            self.sequence_gaps: Dict[str, deque] = {}
        
            # Statistics
            self.stats = {
                'total_ticks': 0,
                'duplicates_blocked': 0,
                'out_of_order_blocked': 0,
                'gaps_detected': 0
            }
        
            logger.info("Sequence Guard initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_tick(self, symbol: str, sequence: int, timestamp: float) -> tuple[bool, str]:
        """
        Validate tick for duplicates and ordering
        
        Args:
            symbol: Trading symbol
            sequence: Sequence number
            timestamp: Tick timestamp
        
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            self.stats['total_ticks'] += 1
        
            # Initialize tracking for new symbol
            if symbol not in self.seen_sequences:
                self.seen_sequences[symbol] = set()
                self.sequence_gaps[symbol] = deque(maxlen=100)
                self.last_sequence[symbol] = sequence - 1
                self.last_timestamp[symbol] = timestamp
        
            # Check for duplicate
            if sequence in self.seen_sequences[symbol]:
                self.stats['duplicates_blocked'] += 1
                logger.warning(f"Duplicate tick: {symbol} seq={sequence}")
                return False, "duplicate_sequence"
        
            # Check temporal ordering
            if timestamp < self.last_timestamp[symbol]:
                self.stats['out_of_order_blocked'] += 1
                logger.warning(f"Out of order: {symbol} seq={sequence} timestamp={timestamp}")
                return False, "out_of_order"
        
            # Check for sequence gap
            expected_seq = self.last_sequence[symbol] + 1
            if sequence > expected_seq:
                gap_size = sequence - expected_seq
                self.stats['gaps_detected'] += 1
                self.sequence_gaps[symbol].append({
                    'gap_start': expected_seq,
                    'gap_end': sequence - 1,
                    'gap_size': gap_size,
                    'timestamp': datetime.now()
                })
                logger.warning(f"Sequence gap: {symbol} expected={expected_seq} got={sequence} (gap={gap_size})")
        
            # Valid tick - update tracking
            self.seen_sequences[symbol].add(sequence)
            self.last_sequence[symbol] = sequence
            self.last_timestamp[symbol] = timestamp
        
            # Cleanup old sequences to prevent memory bloat
            if len(self.seen_sequences[symbol]) > self.max_history:
                # Remove oldest sequences (approximate)
                min_seq = min(self.seen_sequences[symbol])
                self.seen_sequences[symbol] = {s for s in self.seen_sequences[symbol] if s > min_seq + 1000}
        
            return True, "valid"
        except Exception as e:
            logger.error(f"Error in validate_tick: {e}")
            raise
    
    def get_statistics(self) -> dict:
        """Get guard statistics"""
        return {
            **self.stats,
            'symbols_tracked': len(self.seen_sequences),
            'duplicate_rate': (
                self.stats['duplicates_blocked'] / self.stats['total_ticks'] * 100
                if self.stats['total_ticks'] > 0 else 0
            )
        }
    
    def get_gaps(self, symbol: str) -> list:
        """Get detected gaps for symbol"""
        return list(self.sequence_gaps.get(symbol, []))
    
    def validate_sequence(self, sequences: list) -> tuple[bool, list]:
        """
        Validate a sequence of numbers for gaps and out-of-order elements
        
        Args:
            sequences: List of sequence numbers
            
        Returns:
            tuple: (is_valid, gaps) where gaps is list of missing sequences or out-of-order indices
        """
        try:
            if not sequences:
                return True, []
        
            # Check if sequence is in order
            is_ordered = all(sequences[i] <= sequences[i+1] for i in range(len(sequences)-1))
        
            if not is_ordered:
                # Return out-of-order indices
                out_of_order = [i for i in range(len(sequences)-1) if sequences[i] > sequences[i+1]]
                return False, out_of_order
        
            # Check for gaps in ordered sequence
            gaps = []
            for i in range(len(sequences) - 1):
                expected_next = sequences[i] + 1
                actual_next = sequences[i + 1]
            
                if actual_next > expected_next:
                    # Found a gap
                    gap_range = list(range(expected_next, actual_next))
                    gaps.extend(gap_range)
        
            is_valid = len(gaps) == 0
            return is_valid, gaps
        except Exception as e:
            logger.error(f"Error in validate_sequence: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    guard = SequenceGuard()
    
    # Test valid sequence
    valid, reason = guard.validate_tick("EURUSD", 1, 1000.0)
    logger.info(f"Tick 1: {valid} ({reason})")
    
    # Test duplicate
    valid, reason = guard.validate_tick("EURUSD", 1, 1001.0)
    logger.info(f"Duplicate: {valid} ({reason})")
    
    # Test gap
    valid, reason = guard.validate_tick("EURUSD", 5, 1002.0)
    logger.info(f"Gap: {valid} ({reason})")
    
    logger.info(f"\nStats: {guard.get_statistics()}")
    logger.info(f"Gaps: {guard.get_gaps('EURUSD')}")
