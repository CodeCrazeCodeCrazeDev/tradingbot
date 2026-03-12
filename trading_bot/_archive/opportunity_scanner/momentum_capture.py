import asyncio
"""
Momentum Capture Module
Identifies and captures momentum bursts and trend accelerations
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import numpy
import pandas

logger = logging.getLogger(__name__)

class MomentumType(Enum):
    """Types of momentum patterns"""
    BREAKOUT = "breakout"
    ACCELERATION = "acceleration"
    EXHAUSTION = "exhaustion"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"
    SQUEEZE = "squeeze"

@dataclass
class MomentumOpportunity:
    """Represents a momentum trading opportunity"""
    opportunity_id: str
    symbol: str
    momentum_type: MomentumType
    direction: str  # LONG/SHORT
    strength: float
    velocity: float
    acceleration: float
    confidence: float
    entry_price: float
    stop_loss: float
    targets: List[float]
    optimal_holding: float  # Hours
    metadata: Dict[str, Any]

class MomentumBurstDetector:
    """
    Detects sudden momentum bursts that lead to explosive moves
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_velocity = self.config.get('min_velocity', 0.02)
        self.acceleration_threshold = self.config.get('acceleration_threshold', 0.001)
        
        # Momentum tracking
        self.momentum_history = {}
        self.velocity_history = {}
        self.burst_patterns = []
        
    async def detect_momentum_bursts(self, market_data: Dict) -> List[MomentumOpportunity]:
        """
        Detect momentum bursts across multiple timeframes
        """
        opportunities = []
        
        for symbol, data in market_data.items():
            # Multi-timeframe momentum analysis
            momentum_analysis = self._analyze_momentum(symbol, data)
            
            # Check for burst conditions
            if self._is_momentum_burst(momentum_analysis):
                opportunity = self._create_momentum_opportunity(symbol, momentum_analysis, data)
                opportunities.append(opportunity)
        
        return self._filter_opportunities(opportunities)
    
    def _analyze_momentum(self, symbol: str, data: Dict) -> Dict:
        """Comprehensive momentum analysis"""
        if 'price_history' not in data:
            return {}
        
        prices = np.array(data['price_history'])
        
        if len(prices) < 50:
            return {}
        
        # Calculate momentum indicators
        momentum_1 = self._calculate_momentum(prices, 10)
        momentum_2 = self._calculate_momentum(prices, 20)
        momentum_3 = self._calculate_momentum(prices, 30)
        
        # Calculate velocity (rate of change of momentum)
        velocity = self._calculate_velocity(prices)
        
        # Calculate acceleration (rate of change of velocity)
        acceleration = self._calculate_acceleration(prices)
        
        # RSI for overbought/oversold
        rsi = self._calculate_rsi(prices)
        
        # ADX for trend strength
        adx = self._calculate_adx(data)
        
        # Volume momentum
        volume_momentum = self._calculate_volume_momentum(data)
        
        # Identify pattern
        pattern = self._identify_momentum_pattern(momentum_1, velocity, acceleration, rsi)
        
        return {
            'momentum_short': momentum_1,
            'momentum_medium': momentum_2,
            'momentum_long': momentum_3,
            'velocity': velocity,
            'acceleration': acceleration,
            'rsi': rsi,
            'adx': adx,
            'volume_momentum': volume_momentum,
            'pattern': pattern,
            'strength': self._calculate_strength(momentum_1, velocity, acceleration)
        }
    
    def _calculate_momentum(self, prices: np.ndarray, period: int) -> float:
        """Calculate price momentum"""
        if len(prices) < period:
            return 0
        
        return (prices[-1] - prices[-period]) / prices[-period]
    
    def _calculate_velocity(self, prices: np.ndarray) -> float:
        """Calculate velocity of price movement"""
        if len(prices) < 20:
            return 0
        
        # Rate of change of momentum
        momentum_series = []
        for i in range(10, len(prices)):
            mom = (prices[i] - prices[i-10]) / prices[i-10]
            momentum_series.append(mom)
        
        if len(momentum_series) < 2:
            return 0
        
        # Velocity is the change in momentum
        return momentum_series[-1] - momentum_series[-2]
    
    def _calculate_acceleration(self, prices: np.ndarray) -> float:
        """Calculate acceleration of price movement"""
        if len(prices) < 30:
            return 0
        
        # Calculate velocity series
        velocity_series = []
        for i in range(20, len(prices)):
            # Simplified velocity calculation
            v = (prices[i] - prices[i-1]) / prices[i-1]
            velocity_series.append(v)
        
        if len(velocity_series) < 2:
            return 0
        
        # Acceleration is the change in velocity
        return velocity_series[-1] - velocity_series[-2]
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_adx(self, data: Dict) -> float:
        """Calculate Average Directional Index"""
        # Simplified ADX calculation
        # In production, use TA-Lib or similar
        
        if 'high' not in data or 'low' not in data:
            return 25  # Default neutral
        
        # Placeholder for full ADX calculation
        return 30
    
    def _calculate_volume_momentum(self, data: Dict) -> float:
        """Calculate volume momentum"""
        if 'volume_history' not in data:
            return 0
        
        volumes = data['volume_history']
        
        if len(volumes) < 20:
            return 0
        
        # Volume rate of change
        recent_avg = np.mean(volumes[-5:])
        historical_avg = np.mean(volumes[-20:])
        
        if historical_avg == 0:
            return 0
        
        return (recent_avg - historical_avg) / historical_avg
    
    def _identify_momentum_pattern(self, momentum: float, velocity: float, 
                                  acceleration: float, rsi: float) -> MomentumType:
        """Identify the type of momentum pattern"""
        # Breakout pattern
        if momentum > 0.03 and velocity > 0 and acceleration > 0:
            return MomentumType.BREAKOUT
        
        # Acceleration pattern
        if acceleration > self.acceleration_threshold:
            return MomentumType.ACCELERATION
        
        # Exhaustion pattern
        if (rsi > 80 or rsi < 20) and acceleration < 0:
            return MomentumType.EXHAUSTION
        
        # Reversal pattern
        if momentum * velocity < 0:  # Opposite signs
            return MomentumType.REVERSAL
        
        # Continuation pattern
        if abs(momentum) > 0.01 and velocity > 0:
            return MomentumType.CONTINUATION
        
        # Squeeze pattern (low volatility before expansion)
        if abs(momentum) < 0.005 and abs(velocity) < 0.001:
            return MomentumType.SQUEEZE
        
        return MomentumType.CONTINUATION
    
    def _calculate_strength(self, momentum: float, velocity: float, 
                          acceleration: float) -> float:
        """Calculate overall momentum strength"""
        # Composite score
        mom_score = min(1.0, abs(momentum) * 20)
        vel_score = min(1.0, abs(velocity) * 100)
        acc_score = min(1.0, abs(acceleration) * 1000)
        
        # Weighted average
        return 0.5 * mom_score + 0.3 * vel_score + 0.2 * acc_score
    
    def _is_momentum_burst(self, analysis: Dict) -> bool:
        """Check if conditions indicate a momentum burst"""
        if not analysis:
            return False
        
        # Check velocity threshold
        if abs(analysis.get('velocity', 0)) < self.min_velocity:
            return False
        
        # Check pattern
        pattern = analysis.get('pattern')
        burst_patterns = [MomentumType.BREAKOUT, MomentumType.ACCELERATION]
        
        if pattern not in burst_patterns:
            return False
        
        # Check strength
        if analysis.get('strength', 0) < 0.5:
            return False
        
        return True
    
    def _create_momentum_opportunity(self, symbol: str, analysis: Dict, 
                                    market_data: Dict) -> MomentumOpportunity:
        """Create momentum trading opportunity"""
        current_price = market_data['price']
        momentum = analysis['momentum_short']
        
        # Determine direction
        direction = 'LONG' if momentum > 0 else 'SHORT'
        
        # Calculate entry and exits
        if direction == 'LONG':
            entry = current_price * 1.001
            stop = current_price * 0.97
            targets = [
                current_price * 1.02,
                current_price * 1.03,
                current_price * 1.05
            ]
        else:
            entry = current_price * 0.999
            stop = current_price * 1.03
            targets = [
                current_price * 0.98,
                current_price * 0.97,
                current_price * 0.95
            ]
        
        # Estimate holding period based on momentum decay
        holding_period = self._estimate_holding_period(analysis)
        
        return MomentumOpportunity(
            opportunity_id=f"MOM_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            momentum_type=analysis['pattern'],
            direction=direction,
            strength=analysis['strength'],
            velocity=analysis['velocity'],
            acceleration=analysis['acceleration'],
            confidence=min(0.9, analysis['strength']),
            entry_price=entry,
            stop_loss=stop,
            targets=targets,
            optimal_holding=holding_period,
            metadata=analysis
        )
    
    def _estimate_holding_period(self, analysis: Dict) -> float:
        """Estimate optimal holding period for momentum trade"""
        pattern = analysis.get('pattern')
        
        # Different patterns have different decay rates
        if pattern == MomentumType.BREAKOUT:
            return 24.0  # 24 hours
        elif pattern == MomentumType.ACCELERATION:
            return 4.0  # 4 hours
        elif pattern == MomentumType.SQUEEZE:
            return 48.0  # 48 hours
        else:
            return 8.0  # Default 8 hours
    
    def _filter_opportunities(self, opportunities: List[MomentumOpportunity]) -> List[MomentumOpportunity]:
        """Filter and rank momentum opportunities"""
        filtered = []
        
        for opp in opportunities:
            if opp.confidence < 0.6:
                continue
            
            if opp.strength < 0.5:
                continue
            
            filtered.append(opp)
        
        # Sort by strength * confidence
        return sorted(filtered, 
                     key=lambda x: x.strength * x.confidence, 
                     reverse=True)


class BreakoutScanner:
    """
    Scans for breakout patterns with high probability of continuation
    """
    
    def __init__(self):
        self.min_consolidation = 20  # Minimum bars in consolidation
        self.breakout_threshold = 0.02  # 2% breakout
        self.volume_surge = 1.5  # 50% volume increase
        
    def scan_breakouts(self, market_data: Dict) -> List[MomentumOpportunity]:
        """Scan for breakout opportunities"""
        opportunities = []
        
        for symbol, data in market_data.items():
            # Check for consolidation breakout
            if self._is_breaking_out(data):
                opportunity = self._create_breakout_opportunity(symbol, data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _is_breaking_out(self, data: Dict) -> bool:
        """Check if price is breaking out of consolidation"""
        if 'price_history' not in data:
            return False
        
        prices = data['price_history']
        
        if len(prices) < self.min_consolidation:
            return False
        
        # Check for recent consolidation
        recent_prices = prices[-self.min_consolidation:]
        price_range = max(recent_prices) - min(recent_prices)
        avg_price = np.mean(recent_prices)
        
        # Tight consolidation
        if price_range / avg_price > 0.05:  # More than 5% range
            return False
        
        # Current price breaking out
        current = data['price']
        if current > max(recent_prices) * (1 + self.breakout_threshold):
            # Check volume confirmation
            if 'volume' in data and 'avg_volume' in data:
                if data['volume'] > data['avg_volume'] * self.volume_surge:
                    return True
        
        return False
    
    def _create_breakout_opportunity(self, symbol: str, data: Dict) -> MomentumOpportunity:
        """Create breakout opportunity"""
        current_price = data['price']
        
        return MomentumOpportunity(
            opportunity_id=f"BREAK_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            momentum_type=MomentumType.BREAKOUT,
            direction='LONG',
            strength=0.8,
            velocity=0.03,
            acceleration=0.001,
            confidence=0.75,
            entry_price=current_price,
            stop_loss=current_price * 0.97,
            targets=[
                current_price * 1.03,
                current_price * 1.05,
                current_price * 1.08
            ],
            optimal_holding=24.0,
            metadata={
                'breakout_level': max(data['price_history'][-20:]),
                'volume_surge': data.get('volume', 0) / data.get('avg_volume', 1)
            }
        )


class TrendAccelerationFinder:
    """
    Finds trends that are accelerating
    """
    
    def __init__(self):
        self.min_trend_strength = 0.6
        self.acceleration_factor = 1.5
        
    def find_accelerating_trends(self, market_data: Dict) -> List[MomentumOpportunity]:
        """Find trends that are accelerating"""
        opportunities = []
        
        for symbol, data in market_data.items():
            trend_analysis = self._analyze_trend(data)
            
            if trend_analysis['is_accelerating']:
                opportunity = self._create_acceleration_opportunity(symbol, trend_analysis, data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_trend(self, data: Dict) -> Dict:
        """Analyze trend characteristics"""
        if 'price_history' not in data:
            return {'is_accelerating': False}
        
        prices = np.array(data['price_history'])
        
        if len(prices) < 50:
            return {'is_accelerating': False}
        
        # Calculate trend slope over different periods
        slope_10 = self._calculate_slope(prices[-10:])
        slope_20 = self._calculate_slope(prices[-20:])
        slope_50 = self._calculate_slope(prices[-50:])
        
        # Check if trend is accelerating
        is_accelerating = (
            slope_10 > slope_20 * self.acceleration_factor and
            slope_20 > slope_50 * self.acceleration_factor
        )
        
        return {
            'is_accelerating': is_accelerating,
            'slope_short': slope_10,
            'slope_medium': slope_20,
            'slope_long': slope_50,
            'trend_strength': self._calculate_trend_strength(prices)
        }
    
    def _calculate_slope(self, prices: np.ndarray) -> float:
        """Calculate price slope using linear regression"""
        if len(prices) < 2:
            return 0
        
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)
        
        # Normalize by price level
        return slope / np.mean(prices)
    
    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """Calculate trend strength (R-squared of linear fit)"""
        if len(prices) < 10:
            return 0
        
        x = np.arange(len(prices))
        
        # Linear fit
        coeffs = np.polyfit(x, prices, 1)
        fitted = np.polyval(coeffs, x)
        
        # R-squared
        ss_res = np.sum((prices - fitted) ** 2)
        ss_tot = np.sum((prices - np.mean(prices)) ** 2)
        
        if ss_tot == 0:
            return 0
        
        r_squared = 1 - (ss_res / ss_tot)
        
        return max(0, r_squared)
    
    def _create_acceleration_opportunity(self, symbol: str, trend_analysis: Dict, 
                                        data: Dict) -> MomentumOpportunity:
        """Create trend acceleration opportunity"""
        current_price = data['price']
        direction = 'LONG' if trend_analysis['slope_short'] > 0 else 'SHORT'
        
        if direction == 'LONG':
            entry = current_price
            stop = current_price * 0.95
            targets = [
                current_price * 1.03,
                current_price * 1.06,
                current_price * 1.10
            ]
        else:
            entry = current_price
            stop = current_price * 1.05
            targets = [
                current_price * 0.97,
                current_price * 0.94,
                current_price * 0.90
            ]
        
        return MomentumOpportunity(
            opportunity_id=f"ACCEL_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            momentum_type=MomentumType.ACCELERATION,
            direction=direction,
            strength=trend_analysis['trend_strength'],
            velocity=trend_analysis['slope_short'],
            acceleration=trend_analysis['slope_short'] - trend_analysis['slope_medium'],
            confidence=trend_analysis['trend_strength'],
            entry_price=entry,
            stop_loss=stop,
            targets=targets,
            optimal_holding=12.0,
            metadata=trend_analysis
        )


class VelocityTracker:
    """
    Tracks velocity of price movements across timeframes
    """
    
    def __init__(self):
        self.velocity_windows = [5, 10, 20, 50]
        self.velocity_history = {}
        
    def track_velocity(self, symbol: str, prices: List[float]) -> Dict:
        """Track velocity across multiple timeframes"""
        velocities = {}
        
        for window in self.velocity_windows:
            if len(prices) >= window:
                velocity = self._calculate_window_velocity(prices, window)
                velocities[f'velocity_{window}'] = velocity
        
        # Store in history
        if symbol not in self.velocity_history:
            self.velocity_history[symbol] = deque(maxlen=100)
        
        self.velocity_history[symbol].append({
            'timestamp': datetime.now(),
            'velocities': velocities
        })
        
        # Analyze velocity patterns
        analysis = self._analyze_velocity_patterns(symbol)
        
        return {
            'current_velocities': velocities,
            'analysis': analysis
        }
    
    def _calculate_window_velocity(self, prices: List[float], window: int) -> float:
        """Calculate velocity over specified window"""
        if len(prices) < window:
            return 0
        
        # Simple velocity: percentage change over window
        return (prices[-1] - prices[-window]) / prices[-window] / window
    
    def _analyze_velocity_patterns(self, symbol: str) -> Dict:
        """Analyze velocity patterns for trading signals"""
        if symbol not in self.velocity_history:
            return {}
        
        history = list(self.velocity_history[symbol])
        
        if len(history) < 10:
            return {}
        
        # Check for velocity divergence
        short_velocities = [h['velocities'].get('velocity_5', 0) for h in history[-10:]]
        long_velocities = [h['velocities'].get('velocity_50', 0) for h in history[-10:] 
                          if 'velocity_50' in h['velocities']]
        
        divergence = False
        if short_velocities and long_velocities:
            # Check if short-term and long-term velocities diverge
            if np.mean(short_velocities) * np.mean(long_velocities) < 0:
                divergence = True
        
        return {
            'divergence': divergence,
            'acceleration': short_velocities[-1] - short_velocities[0] if short_velocities else 0,
            'consistency': np.std(short_velocities) if short_velocities else 0
        }
