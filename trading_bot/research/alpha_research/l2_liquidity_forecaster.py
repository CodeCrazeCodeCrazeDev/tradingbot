"""
L2 Liquidity Forecasting Model
==============================
Advanced order book dynamics prediction.

Inputs:
- Order book imbalance
- Queue dynamics
- Hidden iceberg order patterns
- Sweep activity
- Toxic flow indicators
- Cancel/replace frequency
- Surges in passive liquidity

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.signal import find_peaks
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class LiquidityState(Enum):
    """Liquidity state classifications"""
    ABUNDANT = auto()
    NORMAL = auto()
    THIN = auto()
    STRESSED = auto()
    CRISIS = auto()


class FlowType(Enum):
    """Order flow types"""
    PASSIVE = auto()
    AGGRESSIVE = auto()
    TOXIC = auto()
    INFORMED = auto()
    NOISE = auto()


@dataclass
class OrderBookSnapshot:
    """Single order book snapshot"""
    timestamp: datetime
    symbol: str
    
    # Bid side (price, size, order_count)
    bids: List[Tuple[float, float, int]] = field(default_factory=list)
    
    # Ask side
    asks: List[Tuple[float, float, int]] = field(default_factory=list)
    
    # Derived metrics
    mid_price: float = 0.0
    spread: float = 0.0
    imbalance: float = 0.0
    
    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.bids and self.asks:
            self.mid_price = (self.bids[0][0] + self.asks[0][0]) / 2
            self.spread = self.asks[0][0] - self.bids[0][0]
            
            bid_depth = sum(b[1] for b in self.bids[:5])
            ask_depth = sum(a[1] for a in self.asks[:5])
            total = bid_depth + ask_depth
            self.imbalance = (bid_depth - ask_depth) / total if total > 0 else 0


@dataclass
class LiquidityForecast:
    """Liquidity forecast output"""
    timestamp: datetime
    symbol: str
    horizon_ms: int
    
    # Predictions
    predicted_spread_bps: float = 0.0
    predicted_depth_change: float = 0.0
    predicted_imbalance: float = 0.0
    
    # Fill probabilities at price levels
    fill_probabilities: Dict[float, float] = field(default_factory=dict)
    
    # State prediction
    predicted_state: LiquidityState = LiquidityState.NORMAL
    state_confidence: float = 0.5
    
    # Risk metrics
    adverse_selection_risk: float = 0.0
    execution_risk: float = 0.0


@dataclass
class QueueDynamics:
    """Queue position dynamics"""
    price_level: float
    side: str
    
    # Queue metrics
    queue_position: int = 0
    queue_size: float = 0.0
    
    # Dynamics
    arrival_rate: float = 0.0  # Orders per second
    cancel_rate: float = 0.0
    fill_rate: float = 0.0
    
    # Predictions
    expected_wait_time_ms: int = 0
    fill_probability: float = 0.0


class ImbalanceAnalyzer:
    """Analyze order book imbalance"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.imbalance_history: deque = deque(maxlen=1000)
        
    def calculate_imbalance(
        self,
        bids: List[Tuple[float, float, int]],
        asks: List[Tuple[float, float, int]],
        levels: int = 5
    ) -> Dict[str, float]:
        """Calculate various imbalance metrics"""
        
        # Volume imbalance
        bid_volume = sum(b[1] for b in bids[:levels])
        ask_volume = sum(a[1] for a in asks[:levels])
        total_volume = bid_volume + ask_volume
        
        volume_imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        
        # Order count imbalance
        bid_orders = sum(b[2] for b in bids[:levels])
        ask_orders = sum(a[2] for a in asks[:levels])
        total_orders = bid_orders + ask_orders
        
        order_imbalance = (bid_orders - ask_orders) / total_orders if total_orders > 0 else 0
        
        # Weighted imbalance (closer to mid weighted more)
        if bids and asks:
            mid = (bids[0][0] + asks[0][0]) / 2
            
            bid_weighted = sum(b[1] / (1 + abs(b[0] - mid) / mid * 100) for b in bids[:levels])
            ask_weighted = sum(a[1] / (1 + abs(a[0] - mid) / mid * 100) for a in asks[:levels])
            total_weighted = bid_weighted + ask_weighted
            
            weighted_imbalance = (bid_weighted - ask_weighted) / total_weighted if total_weighted > 0 else 0
        else:
            weighted_imbalance = 0
        
        result = {
            'volume_imbalance': volume_imbalance,
            'order_imbalance': order_imbalance,
            'weighted_imbalance': weighted_imbalance,
            'bid_volume': bid_volume,
            'ask_volume': ask_volume
        }
        
        self.imbalance_history.append({
            'timestamp': datetime.now(),
            **result
        })
        
        return result
    
    def get_imbalance_trend(self, lookback: int = 20) -> float:
        """Get trend in imbalance"""
        
        if len(self.imbalance_history) < lookback:
            return 0.0
        
        recent = list(self.imbalance_history)[-lookback:]
        imbalances = [r['volume_imbalance'] for r in recent]
        
        # Linear regression slope
        x = np.arange(len(imbalances))
        slope = np.polyfit(x, imbalances, 1)[0]
        
        return slope


class IcebergDetector:
    """Detect hidden iceberg orders"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: deque = deque(maxlen=5000)
        self.detected_icebergs: List[Dict] = []
        
    def add_trade(self, trade: Dict):
        """Add trade to history"""
        self.trade_history.append(trade)
    
    def detect_icebergs(
        self,
        bids: List[Tuple[float, float, int]],
        asks: List[Tuple[float, float, int]]
    ) -> List[Dict]:
        """Detect potential iceberg orders"""
        
        icebergs = []
        
        if len(self.trade_history) < 50:
            return icebergs
        
        trades = list(self.trade_history)
        
        # Method 1: Repeated fills at same price
        price_fills = {}
        for trade in trades[-100:]:
            price = round(trade.get('price', 0), 4)
            if price not in price_fills:
                price_fills[price] = []
            price_fills[price].append(trade.get('size', 0))
        
        for price, fills in price_fills.items():
            if len(fills) >= 5:
                # Check for similar sizes (iceberg signature)
                sizes = np.array(fills)
                cv = np.std(sizes) / (np.mean(sizes) + 1e-10)
                
                if cv < 0.3:  # Low coefficient of variation
                    icebergs.append({
                        'price': price,
                        'estimated_size': sum(fills) * 2,  # Estimate remaining
                        'confidence': 1 - cv,
                        'side': 'unknown',
                        'detected_at': datetime.now()
                    })
        
        # Method 2: Depth that doesn't deplete
        for side, levels in [('bid', bids), ('ask', asks)]:
            for price, size, count in levels[:5]:
                # Check if this level has been hit multiple times
                hits = sum(1 for t in trades[-50:] if abs(t.get('price', 0) - price) < 0.0001)
                
                if hits >= 3 and size > 0:
                    icebergs.append({
                        'price': price,
                        'visible_size': size,
                        'estimated_hidden': size * hits,
                        'confidence': min(hits / 10, 1.0),
                        'side': side,
                        'detected_at': datetime.now()
                    })
        
        self.detected_icebergs = icebergs
        return icebergs


class SweepDetector:
    """Detect sweep activity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.sweep_history: deque = deque(maxlen=100)
        
    def detect_sweep(
        self,
        trades: List[Dict],
        book_before: OrderBookSnapshot,
        book_after: OrderBookSnapshot
    ) -> Optional[Dict]:
        """Detect if a sweep occurred"""
        
        if not trades:
            return None
        
        # Check for rapid multi-level execution
        recent_trades = trades[-20:]
        
        if len(recent_trades) < 3:
            return None
        
        # Time span
        if 'timestamp' in recent_trades[0]:
            time_span = (recent_trades[-1]['timestamp'] - recent_trades[0]['timestamp']).total_seconds()
        else:
            time_span = 1.0
        
        if time_span > 1.0:  # More than 1 second
            return None
        
        # Check price levels hit
        prices = [t.get('price', 0) for t in recent_trades]
        unique_prices = len(set(round(p, 4) for p in prices))
        
        if unique_prices >= 3:
            # Sweep detected
            total_volume = sum(t.get('size', 0) for t in recent_trades)
            direction = 'buy' if prices[-1] > prices[0] else 'sell'
            
            sweep = {
                'timestamp': datetime.now(),
                'direction': direction,
                'levels_hit': unique_prices,
                'total_volume': total_volume,
                'time_span_ms': time_span * 1000,
                'aggression': unique_prices / time_span if time_span > 0 else 0
            }
            
            self.sweep_history.append(sweep)
            return sweep
        
        return None
    
    def get_sweep_frequency(self, lookback_seconds: int = 60) -> float:
        """Get sweep frequency"""
        
        cutoff = datetime.now() - timedelta(seconds=lookback_seconds)
        recent = [s for s in self.sweep_history if s['timestamp'] > cutoff]
        
        return len(recent) / lookback_seconds


class ToxicFlowAnalyzer:
    """Analyze toxic order flow"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.flow_history: deque = deque(maxlen=1000)
        
    def analyze_flow(
        self,
        trades: List[Dict],
        book: OrderBookSnapshot
    ) -> Dict[str, Any]:
        """Analyze flow toxicity"""
        
        if not trades:
            return {'toxicity': 0.0, 'flow_type': FlowType.NOISE}
        
        # VPIN calculation
        buy_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'buy')
        sell_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'sell')
        total_volume = buy_volume + sell_volume
        
        vpin = abs(buy_volume - sell_volume) / total_volume if total_volume > 0 else 0
        
        # Adverse selection
        # Check if trades moved price unfavorably
        if len(trades) >= 2:
            price_move = trades[-1].get('price', 0) - trades[0].get('price', 0)
            net_direction = 1 if buy_volume > sell_volume else -1
            adverse = (price_move * net_direction) < 0
        else:
            adverse = False
        
        # Spread impact
        spread_bps = book.spread / book.mid_price * 10000 if book.mid_price > 0 else 0
        spread_toxicity = min(spread_bps / 20, 1.0)  # Normalize to 20 bps
        
        # Combined toxicity
        toxicity = 0.4 * vpin + 0.3 * (1 if adverse else 0) + 0.3 * spread_toxicity
        
        # Classify flow type
        if toxicity > 0.7:
            flow_type = FlowType.TOXIC
        elif vpin > 0.6:
            flow_type = FlowType.INFORMED
        elif vpin < 0.3:
            flow_type = FlowType.NOISE
        else:
            flow_type = FlowType.PASSIVE if spread_toxicity < 0.3 else FlowType.AGGRESSIVE
        
        result = {
            'toxicity': toxicity,
            'vpin': vpin,
            'adverse_selection': adverse,
            'spread_toxicity': spread_toxicity,
            'flow_type': flow_type
        }
        
        self.flow_history.append({
            'timestamp': datetime.now(),
            **result
        })
        
        return result


class CancelReplaceAnalyzer:
    """Analyze cancel/replace frequency"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.event_history: deque = deque(maxlen=5000)
        
    def add_event(self, event_type: str, details: Dict):
        """Add order event"""
        self.event_history.append({
            'timestamp': datetime.now(),
            'type': event_type,
            **details
        })
    
    def get_cancel_rate(self, lookback_seconds: int = 60) -> float:
        """Get cancel rate"""
        
        cutoff = datetime.now() - timedelta(seconds=lookback_seconds)
        recent = [e for e in self.event_history if e['timestamp'] > cutoff]
        
        cancels = sum(1 for e in recent if e['type'] == 'cancel')
        total = len(recent)
        
        return cancels / total if total > 0 else 0
    
    def get_replace_rate(self, lookback_seconds: int = 60) -> float:
        """Get replace/modify rate"""
        
        cutoff = datetime.now() - timedelta(seconds=lookback_seconds)
        recent = [e for e in self.event_history if e['timestamp'] > cutoff]
        
        replaces = sum(1 for e in recent if e['type'] == 'replace')
        total = len(recent)
        
        return replaces / total if total > 0 else 0
    
    def detect_quote_stuffing(self) -> bool:
        """Detect quote stuffing behavior"""
        
        if len(self.event_history) < 100:
            return False
        
        recent = list(self.event_history)[-100:]
        
        # Check event rate
        if recent:
            time_span = (recent[-1]['timestamp'] - recent[0]['timestamp']).total_seconds()
            rate = len(recent) / max(time_span, 0.001)
            
            # More than 100 events per second suggests stuffing
            return rate > 100
        
        return False


class LiquiditySurgeDetector:
    """Detect surges in passive liquidity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.depth_history: deque = deque(maxlen=500)
        
    def update(self, book: OrderBookSnapshot):
        """Update with new book snapshot"""
        
        bid_depth = sum(b[1] for b in book.bids[:10])
        ask_depth = sum(a[1] for a in book.asks[:10])
        
        self.depth_history.append({
            'timestamp': book.timestamp,
            'bid_depth': bid_depth,
            'ask_depth': ask_depth,
            'total_depth': bid_depth + ask_depth
        })
    
    def detect_surge(self, threshold_std: float = 2.0) -> Optional[Dict]:
        """Detect liquidity surge"""
        
        if len(self.depth_history) < 50:
            return None
        
        depths = [d['total_depth'] for d in self.depth_history]
        
        mean_depth = np.mean(depths[:-1])
        std_depth = np.std(depths[:-1])
        current_depth = depths[-1]
        
        z_score = (current_depth - mean_depth) / (std_depth + 1e-10)
        
        if abs(z_score) > threshold_std:
            return {
                'timestamp': datetime.now(),
                'direction': 'surge' if z_score > 0 else 'drain',
                'z_score': z_score,
                'current_depth': current_depth,
                'mean_depth': mean_depth
            }
        
        return None


class LOBForecaster(nn.Module):
    """Neural network for LOB forecasting"""
    
    def __init__(self, input_dim: int = 50, hidden_dim: int = 128, output_dim: int = 10):
        super().__init__()
        
        # LSTM for sequence modeling
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.2)
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=4, batch_first=True)
        
        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, output_dim)
        )
        
    def forward(self, x):
        # LSTM encoding
        lstm_out, _ = self.lstm(x)
        
        # Self-attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use last timestep
        out = self.fc(attn_out[:, -1, :])
        
        return out


class L2LiquidityForecaster:
    """
    Complete L2 Liquidity Forecasting Model.
    
    Inputs:
    - Order book imbalance
    - Queue dynamics
    - Hidden iceberg order patterns
    - Sweep activity
    - Toxic flow indicators
    - Cancel/replace frequency
    - Surges in passive liquidity
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analyzers
        self.imbalance_analyzer = ImbalanceAnalyzer(config)
        self.iceberg_detector = IcebergDetector(config)
        self.sweep_detector = SweepDetector(config)
        self.toxic_analyzer = ToxicFlowAnalyzer(config)
        self.cancel_analyzer = CancelReplaceAnalyzer(config)
        self.surge_detector = LiquiditySurgeDetector(config)
        
        # ML model
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        
        if TORCH_AVAILABLE:
            self.model = LOBForecaster()
        
        # History
        self.book_history: deque = deque(maxlen=1000)
        self.forecast_history: List[LiquidityForecast] = []
        
        logger.info("L2LiquidityForecaster initialized")
    
    def update(
        self,
        book: OrderBookSnapshot,
        trades: List[Dict] = None
    ):
        """Update with new data"""
        
        book.calculate_metrics()
        self.book_history.append(book)
        
        # Update analyzers
        self.surge_detector.update(book)
        
        if trades:
            for trade in trades:
                self.iceberg_detector.add_trade(trade)
    
    def forecast(
        self,
        symbol: str,
        horizon_ms: int = 1000
    ) -> LiquidityForecast:
        """Generate liquidity forecast"""
        
        if len(self.book_history) < 10:
            return LiquidityForecast(
                timestamp=datetime.now(),
                symbol=symbol,
                horizon_ms=horizon_ms
            )
        
        # Get current state
        current_book = self.book_history[-1]
        
        # Calculate features
        imbalance = self.imbalance_analyzer.calculate_imbalance(
            current_book.bids, current_book.asks
        )
        
        # Detect patterns
        icebergs = self.iceberg_detector.detect_icebergs(
            current_book.bids, current_book.asks
        )
        
        surge = self.surge_detector.detect_surge()
        
        # Predict spread
        spreads = [b.spread for b in list(self.book_history)[-20:]]
        predicted_spread = np.mean(spreads) * (1 + imbalance['volume_imbalance'] * 0.1)
        predicted_spread_bps = predicted_spread / current_book.mid_price * 10000
        
        # Predict depth change
        depths = [sum(b[1] for b in book.bids[:5]) + sum(a[1] for a in book.asks[:5]) 
                  for book in list(self.book_history)[-20:]]
        depth_trend = np.polyfit(range(len(depths)), depths, 1)[0]
        predicted_depth_change = depth_trend * (horizon_ms / 1000)
        
        # Predict imbalance
        imbalance_trend = self.imbalance_analyzer.get_imbalance_trend()
        predicted_imbalance = imbalance['volume_imbalance'] + imbalance_trend * (horizon_ms / 1000)
        
        # Fill probabilities
        fill_probs = self._calculate_fill_probabilities(current_book, icebergs)
        
        # Predict state
        state, confidence = self._predict_state(
            current_book, imbalance, surge
        )
        
        # Risk metrics
        adverse_risk = abs(imbalance['volume_imbalance']) * 0.5
        execution_risk = predicted_spread_bps / 10 + (0.2 if surge else 0)
        
        forecast = LiquidityForecast(
            timestamp=datetime.now(),
            symbol=symbol,
            horizon_ms=horizon_ms,
            predicted_spread_bps=predicted_spread_bps,
            predicted_depth_change=predicted_depth_change,
            predicted_imbalance=predicted_imbalance,
            fill_probabilities=fill_probs,
            predicted_state=state,
            state_confidence=confidence,
            adverse_selection_risk=adverse_risk,
            execution_risk=execution_risk
        )
        
        self.forecast_history.append(forecast)
        
        return forecast
    
    def _calculate_fill_probabilities(
        self,
        book: OrderBookSnapshot,
        icebergs: List[Dict]
    ) -> Dict[float, float]:
        """Calculate fill probabilities at price levels"""
        
        fill_probs = {}
        
        # Bid side
        for price, size, count in book.bids[:5]:
            # Base probability from queue position
            base_prob = 0.8 - (book.bids.index((price, size, count)) * 0.1)
            
            # Adjust for icebergs
            iceberg_at_level = any(
                abs(i['price'] - price) < 0.0001 
                for i in icebergs if i.get('side') == 'bid'
            )
            if iceberg_at_level:
                base_prob *= 0.7  # Lower probability due to hidden orders
            
            fill_probs[price] = max(0, min(base_prob, 1.0))
        
        # Ask side
        for price, size, count in book.asks[:5]:
            base_prob = 0.8 - (book.asks.index((price, size, count)) * 0.1)
            
            iceberg_at_level = any(
                abs(i['price'] - price) < 0.0001 
                for i in icebergs if i.get('side') == 'ask'
            )
            if iceberg_at_level:
                base_prob *= 0.7
            
            fill_probs[price] = max(0, min(base_prob, 1.0))
        
        return fill_probs
    
    def _predict_state(
        self,
        book: OrderBookSnapshot,
        imbalance: Dict,
        surge: Optional[Dict]
    ) -> Tuple[LiquidityState, float]:
        """Predict liquidity state"""
        
        # Calculate state score
        spread_bps = book.spread / book.mid_price * 10000 if book.mid_price > 0 else 0
        
        if spread_bps > 20 or (surge and surge['direction'] == 'drain'):
            state = LiquidityState.STRESSED
            confidence = 0.8
        elif spread_bps > 10:
            state = LiquidityState.THIN
            confidence = 0.7
        elif spread_bps < 2 and (surge and surge['direction'] == 'surge'):
            state = LiquidityState.ABUNDANT
            confidence = 0.8
        else:
            state = LiquidityState.NORMAL
            confidence = 0.6
        
        return state, confidence
    
    def get_queue_dynamics(
        self,
        price_level: float,
        side: str
    ) -> QueueDynamics:
        """Get queue dynamics for a price level"""
        
        if len(self.book_history) < 20:
            return QueueDynamics(price_level=price_level, side=side)
        
        # Analyze queue at this level over time
        queue_sizes = []
        for book in list(self.book_history)[-20:]:
            levels = book.bids if side == 'bid' else book.asks
            for p, s, c in levels:
                if abs(p - price_level) < 0.0001:
                    queue_sizes.append(s)
                    break
        
        if not queue_sizes:
            return QueueDynamics(price_level=price_level, side=side)
        
        # Calculate dynamics
        avg_size = np.mean(queue_sizes)
        size_changes = np.diff(queue_sizes)
        
        arrivals = sum(1 for c in size_changes if c > 0)
        cancels = sum(1 for c in size_changes if c < 0)
        
        time_span = 20  # Approximate seconds
        
        return QueueDynamics(
            price_level=price_level,
            side=side,
            queue_size=queue_sizes[-1] if queue_sizes else 0,
            arrival_rate=arrivals / time_span,
            cancel_rate=cancels / time_span,
            fill_probability=0.5 + (arrivals - cancels) / (len(size_changes) + 1) * 0.3
        )


# Factory function
def create_l2_forecaster(config: Optional[Dict] = None) -> L2LiquidityForecaster:
    """Create and return a L2LiquidityForecaster instance"""
    return L2LiquidityForecaster(config)
