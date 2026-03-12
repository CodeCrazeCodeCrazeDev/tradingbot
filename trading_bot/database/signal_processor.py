"""
Signal Processor
Processes analytics into actionable trading signals
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
import logging
from collections import deque
import numpy

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
class TradingSignal:
    """Trading signal with execution details"""
    timestamp: datetime
    symbol: str
    direction: str  # 'buy' or 'sell'
    signal_type: str  # 'momentum', 'reversal', 'breakout'
    entry_price: float
    stop_loss: float
    take_profit: float
    size: float
    confidence: float
    timeframe: str
    metadata: Dict[str, Any]

class SignalProcessor:
    """
    Processes analytics into trading signals
    Features:
    - Signal generation
    - Risk calculation
    - Position sizing
    - Entry/exit optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Risk parameters
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.01)
        self.max_position_size = config.get('max_position_size', 1.0)
        self.min_confidence = config.get('min_confidence', 0.7)
        
        # Signal tracking
        self.active_signals: Dict[str, List[TradingSignal]] = {}
        self.signal_history: Dict[str, deque] = {}
        
        # Performance tracking
        self.signal_performance: Dict[str, Dict[str, float]] = {}
        
        logger.info("Signal processor initialized")
    
    async def process_analytics(self,
                              symbol: str,
                              analytics: Dict[str, Any],
                              market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Process analytics into trading signal"""
        try:
            # Initialize tracking if needed
            if symbol not in self.active_signals:
                self.active_signals[symbol] = []
            if symbol not in self.signal_history:
                self.signal_history[symbol] = deque(maxlen=1000)
            
            # Check confidence threshold
            if analytics['confidence'] < self.min_confidence:
                return None
            
            # Generate signal
            signal = await self._generate_signal(symbol, analytics, market_data)
            
            if signal:
                # Validate signal
                if self._validate_signal(signal):
                    # Track signal
                    self.active_signals[symbol].append(signal)
                    self.signal_history[symbol].append(signal)
                    
                    return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing analytics for {symbol}: {e}")
            raise
    
    async def _generate_signal(self,
                             symbol: str,
                             analytics: Dict[str, Any],
                             market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Generate trading signal from analytics"""
        # Get current price
        current_price = market_data.get('price', 0)
        if not current_price:
            return None
        
        # Determine signal direction and type
        direction, signal_type = self._determine_signal_type(analytics)
        if not direction:
            return None
        
        # Calculate entry and exit prices
        entry_price = self._calculate_entry_price(
            direction, current_price, analytics
        )
        
        stop_loss = self._calculate_stop_loss(
            direction, entry_price, analytics
        )
        
        take_profit = self._calculate_take_profit(
            direction, entry_price, stop_loss, analytics
        )
        
        # Calculate position size
        size = self._calculate_position_size(
            entry_price, stop_loss, analytics
        )
        
        return TradingSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            signal_type=signal_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=size,
            confidence=analytics['confidence'],
            timeframe=analytics.get('timeframe', '5m'),
            metadata={
                'analytics': analytics,
                'market_regime': analytics.get('market_regime'),
                'features': analytics.get('features', {})
            }
        )
    
    def _determine_signal_type(self,
                             analytics: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Determine signal direction and type"""
        predictions = analytics.get('predictions', {})
        signals = analytics.get('signals', [])
        
        # Check price direction predictions
        up_prob = predictions.get('price_up_probability', 0)
        down_prob = predictions.get('price_down_probability', 0)
        
        if up_prob > 0.7 and up_prob > down_prob:
            # Look for confirming signals
            confirming_signals = [
                s for s in signals
                if s.get('direction') in ['up', 'with_trend']
            ]
            
            if confirming_signals:
                signal_types = [s.get('type') for s in confirming_signals]
                # Use most common signal type
                signal_type = max(set(signal_types), key=signal_types.count)
                return 'buy', signal_type
                
        elif down_prob > 0.7 and down_prob > up_prob:
            confirming_signals = [
                s for s in signals
                if s.get('direction') in ['down', 'against_trend']
            ]
            
            if confirming_signals:
                signal_types = [s.get('type') for s in confirming_signals]
                signal_type = max(set(signal_types), key=signal_types.count)
                return 'sell', signal_type
        
        return None, None
    
    def _calculate_entry_price(self,
                             direction: str,
                             current_price: float,
                             analytics: Dict[str, Any]) -> float:
        """Calculate optimal entry price"""
        features = analytics.get('features', {})
        
        # Get volatility measure
        volatility = features.get('volatility', 0.001)
        
        # Adjust entry based on volatility and liquidity
        if direction == 'buy':
            # Enter slightly above current price in strong momentum
            if features.get('momentum', 0) > 0.7:
                entry = current_price * (1 + volatility)
            else:
                # Try to get better entry on retracement
                entry = current_price * (1 - volatility * 0.5)
        else:
            if features.get('momentum', 0) < -0.7:
                entry = current_price * (1 - volatility)
            else:
                entry = current_price * (1 + volatility * 0.5)
        
        return entry
    
    def _calculate_stop_loss(self,
                           direction: str,
                           entry_price: float,
                           analytics: Dict[str, Any]) -> float:
        """Calculate stop loss price"""
        features = analytics.get('features', {})
        
        # Get volatility and liquidity measures
        volatility = features.get('volatility', 0.001)
        liquidity = features.get('liquidity', 1.0)
        
        # Base stop distance on volatility
        base_distance = volatility * 2
        
        # Adjust for liquidity
        stop_distance = base_distance * (1 + (1 - liquidity))
        
        # Calculate stop price
        if direction == 'buy':
            stop_loss = entry_price * (1 - stop_distance)
        else:
            stop_loss = entry_price * (1 + stop_distance)
        
        return stop_loss
    
    def _calculate_take_profit(self,
                             direction: str,
                             entry_price: float,
                             stop_loss: float,
                             analytics: Dict[str, Any]) -> float:
        """Calculate take profit price"""
        # Calculate risk in points
        risk = abs(entry_price - stop_loss)
        
        # Get reward multiplier based on confidence
        confidence = analytics['confidence']
        base_reward_ratio = 1.5 + confidence  # 1.5 to 2.5x
        
        # Adjust for market regime
        regime = analytics.get('market_regime', 'ranging')
        if regime == 'trending':
            base_reward_ratio *= 1.5
        elif regime == 'volatile':
            base_reward_ratio *= 0.8
        
        # Calculate take profit
        reward = risk * base_reward_ratio
        
        if direction == 'buy':
            take_profit = entry_price + reward
        else:
            take_profit = entry_price - reward
        
        return take_profit
    
    def _calculate_position_size(self,
                               entry_price: float,
                               stop_loss: float,
                               analytics: Dict[str, Any]) -> float:
        """Calculate position size based on risk"""
        # Calculate risk per point
        risk_points = abs(entry_price - stop_loss)
        if risk_points == 0:
            return 0
        
        # Get account risk amount
        account_size = self.config.get('account_size', 100000)
        risk_amount = account_size * self.max_risk_per_trade
        
        # Calculate base position size
        base_size = risk_amount / risk_points
        
        # Adjust for confidence
        confidence = analytics['confidence']
        size = base_size * confidence
        
        # Apply maximum position size limit
        max_size = account_size * self.max_position_size
        size = min(size, max_size)
        
        return size
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate trading signal"""
        # Check risk-reward ratio
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.entry_price - signal.take_profit)
        
        if risk == 0 or reward / risk < 1.5:
            return False
        
        # Check recent signals
        recent_signals = [
            s for s in self.signal_history.get(signal.symbol, [])
            if (datetime.now() - s.timestamp).total_seconds() < 300  # 5 minutes
        ]
        
        # Avoid signal clustering
        if len(recent_signals) > 2:
            return False
        
        # Check performance of similar signals
        similar_performance = self._get_similar_signal_performance(signal)
        if similar_performance and similar_performance['win_rate'] < 0.4:
            return False
        
        return True
    
    def _get_similar_signal_performance(self,
                                      signal: TradingSignal) -> Optional[Dict[str, float]]:
        """Get performance metrics for similar signals"""
        if signal.symbol not in self.signal_performance:
            return None
        
        performance = self.signal_performance[signal.symbol]
        
        # Get performance for this signal type
        return performance.get(signal.signal_type)
    
    def update_signal_performance(self,
                                signal: TradingSignal,
                                result: Dict[str, Any]):
        """Update signal performance metrics"""
        if signal.symbol not in self.signal_performance:
            self.signal_performance[signal.symbol] = {}
        
        if signal.signal_type not in self.signal_performance[signal.symbol]:
            self.signal_performance[signal.symbol][signal.signal_type] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0
            }
        
        perf = self.signal_performance[signal.symbol][signal.signal_type]
        
        # Update metrics
        perf['trades'] += 1
        if result.get('profit', 0) > 0:
            perf['wins'] += 1
            perf['avg_profit'] = (perf['avg_profit'] * (perf['wins'] - 1) +
                                result['profit']) / perf['wins']
        else:
            perf['losses'] += 1
            perf['avg_loss'] = (perf['avg_loss'] * (perf['losses'] - 1) +
                              result['profit']) / perf['losses']
        
        perf['win_rate'] = perf['wins'] / perf['trades']
    
    def get_signal_metrics(self) -> Dict[str, Any]:
        """Get signal generation metrics"""
        total_signals = sum(
            len(signals) for signals in self.signal_history.values()
        )
        
        return {
            'total_signals': total_signals,
            'active_signals': sum(
                len(signals) for signals in self.active_signals.values()
            ),
            'performance': self.signal_performance
        }
