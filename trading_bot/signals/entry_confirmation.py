"""
ENTRY CONFIRMATION MODULE - PHASE 2 QUICK-WIN #2
============================================================

Implements multi-factor entry confirmation to reduce false signals.

Features:
- Multiple confirmation indicators
- Confluence detection
- Signal strength scoring
- Entry probability calculation

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional

import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ConfirmationType(Enum):
    """Types of entry confirmations."""
    TREND = auto()
    MOMENTUM = auto()
    VOLUME = auto()
    SUPPORT_RESISTANCE = auto()
    PATTERN = auto()
    DIVERGENCE = auto()
    OSCILLATOR = auto()
    VOLATILITY = auto()


@dataclass
class ConfirmationSignal:
    """Single confirmation signal."""
    signal_type: ConfirmationType
    strength: float  # 0-1
    description: str
    timestamp: datetime = None
    
    def __post_init__(self):
        try:
            if self.timestamp is None:
                self.timestamp = datetime.now()
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class EntryConfirmation:
    """Multi-factor entry confirmation system."""
    
    def __init__(self, min_confirmations: int = 2,
                 min_strength: float = 0.6):
        """
        Initialize entry confirmation.
        
        Args:
            min_confirmations: Minimum number of confirmations required
            min_strength: Minimum average strength required (0-1)
        """
        try:
            self.min_confirmations = min_confirmations
            self.min_strength = min_strength
        
            self.signals: Dict[str, List[ConfirmationSignal]] = {}
        
            logger.info(f"Entry confirmation initialized (min: {min_confirmations}, strength: {min_strength})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_signal(self, symbol: str, signal: ConfirmationSignal):
        """Add confirmation signal."""
        try:
            if symbol not in self.signals:
                self.signals[symbol] = []
        
            self.signals[symbol].append(signal)
        
            # Keep only last 100 signals
            if len(self.signals[symbol]) > 100:
                self.signals[symbol].pop(0)
        
            logger.debug(f"{symbol}: {signal.signal_type.name} confirmation added (strength: {signal.strength:.2f})")
        except Exception as e:
            logger.error(f"Error in add_signal: {e}")
            raise
    
    def get_confirmation_score(self, symbol: str) -> Dict[str, any]:
        """
        Calculate confirmation score for entry.
        
        Returns:
            Dict with score, count, strength, and details
        """
        try:
            if symbol not in self.signals or not self.signals[symbol]:
                return {
                    'score': 0,
                    'is_confirmed': False,
                    'confirmation_count': 0,
                    'average_strength': 0,
                    'details': 'No signals'
                }
        
            recent_signals = self.signals[symbol][-10:]  # Last 10 signals
        
            if not recent_signals:
                return {
                    'score': 0,
                    'is_confirmed': False,
                    'confirmation_count': 0,
                    'average_strength': 0,
                    'details': 'No recent signals'
                }
        
            # Count unique confirmation types
            confirmation_types = set(s.signal_type for s in recent_signals)
            confirmation_count = len(confirmation_types)
        
            # Calculate average strength
            average_strength = np.mean([s.strength for s in recent_signals])
        
            # Calculate score (0-1)
            type_score = min(1.0, confirmation_count / self.min_confirmations)
            strength_score = average_strength
            score = (type_score + strength_score) / 2
        
            # Check if confirmed
            is_confirmed = (confirmation_count >= self.min_confirmations and 
                           average_strength >= self.min_strength)
        
            # Build details
            details = f"{confirmation_count} confirmations, {average_strength:.2f} avg strength"
        
            return {
                'score': score,
                'is_confirmed': is_confirmed,
                'confirmation_count': confirmation_count,
                'average_strength': average_strength,
                'details': details,
                'signals': [
                    {
                        'type': s.signal_type.name,
                        'strength': s.strength,
                        'description': s.description
                    }
                    for s in recent_signals[-5:]  # Last 5
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_confirmation_score: {e}")
            raise
    
    def get_confluence_zones(self, symbol: str) -> List[Dict]:
        """
        Get areas of high confirmation confluence.
        
        Returns:
            List of confluence zones with price levels and strength
        """
        try:
            if symbol not in self.signals:
                return []
        
            # Group signals by type
            signals_by_type = {}
            for signal in self.signals[symbol][-20:]:
                if signal.signal_type not in signals_by_type:
                    signals_by_type[signal.signal_type] = []
                signals_by_type[signal.signal_type].append(signal.strength)
        
            # Calculate confluence strength for each type
            confluence = []
            for signal_type, strengths in signals_by_type.items():
                avg_strength = np.mean(strengths)
                confluence.append({
                    'type': signal_type.name,
                    'strength': avg_strength,
                    'count': len(strengths)
                })
        
            return sorted(confluence, key=lambda x: x['strength'], reverse=True)
        except Exception as e:
            logger.error(f"Error in get_confluence_zones: {e}")
            raise
    
    def get_entry_probability(self, symbol: str) -> float:
        """
        Calculate probability of successful entry.
        
        Returns:
            Probability (0-1)
        """
        try:
            score = self.get_confirmation_score(symbol)
        
            if not score['is_confirmed']:
                return 0.0
        
            # Probability based on score and confirmation count
            base_probability = score['score']
            confirmation_bonus = min(0.2, (score['confirmation_count'] - self.min_confirmations) * 0.05)
        
            probability = min(1.0, base_probability + confirmation_bonus)
        
            return probability
        except Exception as e:
            logger.error(f"Error in get_entry_probability: {e}")
            raise
    
    def get_confirmation_summary(self, symbol: str) -> str:
        """Get human-readable confirmation summary."""
        try:
            score = self.get_confirmation_score(symbol)
        
            summary = f"ENTRY CONFIRMATION - {symbol}\n"
            summary += "=" * 50 + "\n"
            summary += f"Score: {score['score']:.2f}\n"
            summary += f"Confirmed: {'✓ YES' if score['is_confirmed'] else '✗ NO'}\n"
            summary += f"Confirmations: {score['confirmation_count']}/{self.min_confirmations}\n"
            summary += f"Average Strength: {score['average_strength']:.2f}/{self.min_strength}\n"
            summary += f"Entry Probability: {self.get_entry_probability(symbol):.1%}\n"
            summary += "=" * 50 + "\n"
        
            if score['signals']:
                summary += "Recent Signals:\n"
                for sig in score['signals']:
                    summary += f"  • {sig['type']}: {sig['strength']:.2f} - {sig['description']}\n"
        
            return summary
        except Exception as e:
            logger.error(f"Error in get_confirmation_summary: {e}")
            raise
    
    def clear_signals(self, symbol: str):
        """Clear signals for symbol."""
        try:
            if symbol in self.signals:
                self.signals[symbol].clear()
            logger.info(f"Signals cleared for {symbol}")
        except Exception as e:
            logger.error(f"Error in clear_signals: {e}")
            raise
    
    def reset(self):
        """Reset all signals."""
        try:
            self.signals.clear()
            logger.info("Entry confirmation reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
