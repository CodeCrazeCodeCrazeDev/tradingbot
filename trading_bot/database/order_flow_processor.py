"""
Order Flow Processor
Analyzes order flow patterns for alpha generation
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from collections import deque
import asyncio
from scipy.stats import norm
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class OrderFlowSignal:
    """Order flow trading signal"""
    timestamp: datetime
    symbol: str
    signal_type: str  # 'absorption', 'exhaustion', 'momentum'
    direction: str    # 'buy', 'sell'
    strength: float   # 0.0 to 1.0
    price_level: float
    volume: float
    confidence: float
    metadata: Dict[str, Any]

class OrderFlowProcessor:
    """
    Advanced order flow analysis for trading signals
    Features:
    - Volume delta analysis
    - Price absorption detection
    - Institutional order detection
    - Liquidity sweeps identification
    - Order book imbalance analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Analysis windows
        self.short_window = config.get('short_window', 20)
        self.medium_window = config.get('medium_window', 50)
        self.long_window = config.get('long_window', 100)
        
        # Thresholds
        self.volume_threshold = config.get('volume_threshold', 0.8)
        self.delta_threshold = config.get('delta_threshold', 0.6)
        self.absorption_threshold = config.get('absorption_threshold', 0.7)
        
        # Data buffers
        self.price_buffer: Dict[str, deque] = {}
        self.volume_buffer: Dict[str, deque] = {}
        self.delta_buffer: Dict[str, deque] = {}
        self.signals: Dict[str, List[OrderFlowSignal]] = {}
        
        # Statistical measures
        self.volume_stats: Dict[str, Dict[str, float]] = {}
        self.price_stats: Dict[str, Dict[str, float]] = {}
        
        logger.info("Order flow processor initialized")
    
    async def process_tick(self, symbol: str, tick: Dict[str, Any]) -> Optional[OrderFlowSignal]:
        """Process new tick data and generate signals"""
        # Initialize buffers if needed
        if symbol not in self.price_buffer:
            self._initialize_buffers(symbol)
        
        # Update buffers
        self._update_buffers(symbol, tick)
        
        # Update statistics
        self._update_statistics(symbol)
        
        # Generate signals
        signals = await self._generate_signals(symbol)
        
        # Store signals
        if signals:
            if symbol not in self.signals:
                self.signals[symbol] = []
            self.signals[symbol].extend(signals)
        
        # Return most significant signal
        return signals[0] if signals else None
    
    def _initialize_buffers(self, symbol: str):
        """Initialize data buffers for symbol"""
        self.price_buffer[symbol] = deque(maxlen=self.long_window)
        self.volume_buffer[symbol] = deque(maxlen=self.long_window)
        self.delta_buffer[symbol] = deque(maxlen=self.long_window)
        self.volume_stats[symbol] = {'mean': 0, 'std': 0}
        self.price_stats[symbol] = {'mean': 0, 'std': 0}
    
    def _update_buffers(self, symbol: str, tick: Dict[str, Any]):
        """Update data buffers with new tick"""
        self.price_buffer[symbol].append(tick.get('price', 0))
        self.volume_buffer[symbol].append(tick.get('volume', 0))
        
        # Calculate volume delta
        buy_volume = tick.get('buy_volume', tick.get('volume', 0) / 2)
        sell_volume = tick.get('sell_volume', tick.get('volume', 0) / 2)
        delta = buy_volume - sell_volume
        self.delta_buffer[symbol].append(delta)
    
    def _update_statistics(self, symbol: str):
        """Update statistical measures"""
        if len(self.volume_buffer[symbol]) > 0:
            self.volume_stats[symbol] = {
                'mean': np.mean(self.volume_buffer[symbol]),
                'std': np.std(self.volume_buffer[symbol])
            }
        
        if len(self.price_buffer[symbol]) > 0:
            self.price_stats[symbol] = {
                'mean': np.mean(self.price_buffer[symbol]),
                'std': np.std(self.price_buffer[symbol])
            }
    
    async def _generate_signals(self, symbol: str) -> List[OrderFlowSignal]:
        """Generate trading signals from order flow analysis"""
        signals = []
        
        # Check for volume absorption
        absorption = self._detect_absorption(symbol)
        if absorption:
            signals.append(absorption)
        
        # Check for exhaustion
        exhaustion = self._detect_exhaustion(symbol)
        if exhaustion:
            signals.append(exhaustion)
        
        # Check for momentum
        momentum = self._detect_momentum(symbol)
        if momentum:
            signals.append(momentum)
        
        # Sort by confidence
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals
    
    def _detect_absorption(self, symbol: str) -> Optional[OrderFlowSignal]:
        """Detect price absorption patterns"""
        if len(self.price_buffer[symbol]) < self.short_window:
            return None
        
        # Get recent data
        recent_prices = list(self.price_buffer[symbol])[-self.short_window:]
        recent_volumes = list(self.volume_buffer[symbol])[-self.short_window:]
        recent_deltas = list(self.delta_buffer[symbol])[-self.short_window:]
        
        # Calculate price movement
        price_change = recent_prices[-1] - recent_prices[0]
        
        # Calculate volume concentration
        volume_concentration = np.sum(recent_volumes) / (
            self.volume_stats[symbol]['mean'] * self.short_window
        )
        
        # Check for absorption pattern
        if abs(price_change) < self.price_stats[symbol]['std'] * 0.5:
            if volume_concentration > self.absorption_threshold:
                # Determine direction
                net_delta = np.sum(recent_deltas)
                direction = 'buy' if net_delta > 0 else 'sell'
                
                return OrderFlowSignal(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type='absorption',
                    direction=direction,
                    strength=volume_concentration,
                    price_level=recent_prices[-1],
                    volume=np.sum(recent_volumes),
                    confidence=min(volume_concentration / self.absorption_threshold, 1.0),
                    metadata={
                        'price_change': price_change,
                        'volume_concentration': volume_concentration,
                        'net_delta': net_delta
                    }
                )
        
        return None
    
    def _detect_exhaustion(self, symbol: str) -> Optional[OrderFlowSignal]:
        """Detect buying/selling exhaustion"""
        if len(self.delta_buffer[symbol]) < self.medium_window:
            return None
        
        # Get recent deltas
        recent_deltas = list(self.delta_buffer[symbol])[-self.medium_window:]
        
        # Calculate cumulative delta
        cumulative_delta = np.cumsum(recent_deltas)
        
        # Check for exhaustion pattern
        if len(cumulative_delta) > 1:
            # Look for reversal in cumulative delta
            peak_idx = np.argmax(np.abs(cumulative_delta))
            if peak_idx < len(cumulative_delta) - 1:
                peak_value = cumulative_delta[peak_idx]
                current_value = cumulative_delta[-1]
                
                # Calculate reversal strength
                reversal = (peak_value - current_value) / peak_value if peak_value != 0 else 0
                
                if abs(reversal) > self.delta_threshold:
                    direction = 'buy' if current_value < 0 else 'sell'
                    
                    return OrderFlowSignal(
                        timestamp=datetime.now(),
                        symbol=symbol,
                        signal_type='exhaustion',
                        direction=direction,
                        strength=abs(reversal),
                        price_level=self.price_buffer[symbol][-1],
                        volume=self.volume_buffer[symbol][-1],
                        confidence=min(abs(reversal) / self.delta_threshold, 1.0),
                        metadata={
                            'peak_delta': peak_value,
                            'current_delta': current_value,
                            'reversal_strength': reversal
                        }
                    )
        
        return None
    
    def _detect_momentum(self, symbol: str) -> Optional[OrderFlowSignal]:
        """Detect order flow momentum"""
        if len(self.delta_buffer[symbol]) < self.long_window:
            return None
        
        # Get recent data
        recent_deltas = list(self.delta_buffer[symbol])[-self.long_window:]
        recent_prices = list(self.price_buffer[symbol])[-self.long_window:]
        
        # Calculate delta momentum
        delta_momentum = np.mean(recent_deltas[-self.short_window:])
        delta_trend = np.polyfit(range(len(recent_deltas)), recent_deltas, 1)[0]
        
        # Calculate price momentum
        price_momentum = recent_prices[-1] - recent_prices[0]
        
        # Check for momentum signal
        if abs(delta_momentum) > np.std(recent_deltas) * self.volume_threshold:
            direction = 'buy' if delta_momentum > 0 else 'sell'
            
            # Confidence based on alignment of price and delta momentum
            confidence = min(
                abs(delta_momentum) / (np.std(recent_deltas) * self.volume_threshold),
                1.0
            )
            
            # Adjust confidence based on price momentum alignment
            if (direction == 'buy' and price_momentum > 0) or \
               (direction == 'sell' and price_momentum < 0):
                confidence *= 1.2  # Boost confidence when price aligns
            else:
                confidence *= 0.8  # Reduce confidence when price diverges
            
            return OrderFlowSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                signal_type='momentum',
                direction=direction,
                strength=abs(delta_momentum),
                price_level=recent_prices[-1],
                volume=self.volume_buffer[symbol][-1],
                confidence=min(confidence, 1.0),
                metadata={
                    'delta_momentum': delta_momentum,
                    'delta_trend': delta_trend,
                    'price_momentum': price_momentum
                }
            )
        
        return None
    
    def get_order_flow_stats(self, symbol: str) -> Dict[str, Any]:
        """Get order flow statistics for symbol"""
        if symbol not in self.volume_stats:
            return {}
        
        recent_signals = [
            s for s in self.signals.get(symbol, [])
            if (datetime.now() - s.timestamp) < timedelta(minutes=5)
        ]
        
        return {
            'volume_stats': self.volume_stats[symbol],
            'price_stats': self.price_stats[symbol],
            'recent_signals': [
                {
                    'type': s.signal_type,
                    'direction': s.direction,
                    'strength': s.strength,
                    'confidence': s.confidence,
                    'age_seconds': (datetime.now() - s.timestamp).total_seconds()
                }
                for s in recent_signals
            ],
            'signal_distribution': {
                'absorption': len([s for s in recent_signals if s.signal_type == 'absorption']),
                'exhaustion': len([s for s in recent_signals if s.signal_type == 'exhaustion']),
                'momentum': len([s for s in recent_signals if s.signal_type == 'momentum'])
            }
        }
    
    def calculate_signal_probability(self, symbol: str, 
                                  timeframe: int = 300) -> Dict[str, float]:
        """Calculate probability of different signal types"""
        recent_signals = [
            s for s in self.signals.get(symbol, [])
            if (datetime.now() - s.timestamp) < timedelta(seconds=timeframe)
        ]
        
        if not recent_signals:
            return {}
        
        total_signals = len(recent_signals)
        
        # Calculate base probabilities
        probabilities = {
            'absorption': len([s for s in recent_signals if s.signal_type == 'absorption']) / total_signals,
            'exhaustion': len([s for s in recent_signals if s.signal_type == 'exhaustion']) / total_signals,
            'momentum': len([s for s in recent_signals if s.signal_type == 'momentum']) / total_signals
        }
        
        # Adjust based on confidence
        for signal_type in probabilities.keys():
            relevant_signals = [s for s in recent_signals if s.signal_type == signal_type]
            if relevant_signals:
                avg_confidence = np.mean([s.confidence for s in relevant_signals])
                probabilities[signal_type] *= avg_confidence
        
        return probabilities
