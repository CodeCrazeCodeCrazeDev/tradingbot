"""
Market Impact Minimization & Predator Detection
================================================
Advanced market microstructure analysis and protection.

Features:
- Market impact estimation and minimization
- Hidden liquidity detection
- Algorithmic predator detection
- Stop-hunt prediction
- Institutional footprint reverse-engineering
- Dark pool activity monitoring
- Spoofing detection
- Front-running protection

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
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
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PredatorType(Enum):
    """Types of algorithmic predators"""
    MOMENTUM_IGNITION = auto()
    SPOOFING = auto()
    LAYERING = auto()
    QUOTE_STUFFING = auto()
    FRONT_RUNNING = auto()
    STOP_HUNTING = auto()
    PINGING = auto()
    ICEBERG_DETECTOR = auto()


class ThreatLevel(Enum):
    """Threat level classifications"""
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class MarketImpactEstimate:
    """Estimated market impact"""
    timestamp: datetime
    symbol: str
    
    # Order details
    order_size: float
    side: str
    
    # Impact estimates
    temporary_impact_bps: float = 0.0
    permanent_impact_bps: float = 0.0
    total_impact_bps: float = 0.0
    
    # Cost breakdown
    spread_cost_bps: float = 0.0
    timing_cost_bps: float = 0.0
    opportunity_cost_bps: float = 0.0
    
    # Recommendations
    optimal_execution_time: int = 0  # minutes
    recommended_algo: str = ""
    slice_size: float = 0.0


@dataclass
class HiddenLiquidity:
    """Hidden liquidity detection result"""
    timestamp: datetime
    symbol: str
    
    # Detection
    detected: bool = False
    confidence: float = 0.0
    
    # Estimates
    estimated_hidden_size: float = 0.0
    price_level: float = 0.0
    side: str = ""
    
    # Source
    source_type: str = ""  # dark_pool, iceberg, reserve
    venue: str = ""


@dataclass
class PredatorAlert:
    """Alert for detected predator activity"""
    alert_id: str
    timestamp: datetime
    symbol: str
    
    # Predator info
    predator_type: PredatorType
    threat_level: ThreatLevel
    confidence: float
    
    # Details
    description: str = ""
    evidence: List[str] = field(default_factory=list)
    
    # Recommendations
    recommended_action: str = ""
    avoid_trading: bool = False


@dataclass
class StopHuntPrediction:
    """Stop-hunt prediction"""
    timestamp: datetime
    symbol: str
    
    # Prediction
    probability: float = 0.0
    direction: str = ""  # up, down
    target_level: float = 0.0
    
    # Evidence
    stop_cluster_detected: bool = False
    unusual_activity: bool = False
    
    # Timing
    expected_timeframe: str = ""  # minutes, hours


@dataclass
class InstitutionalFootprint:
    """Detected institutional activity"""
    timestamp: datetime
    symbol: str
    
    # Detection
    detected: bool = False
    confidence: float = 0.0
    
    # Activity type
    activity_type: str = ""  # accumulation, distribution, rebalancing
    estimated_size: float = 0.0
    
    # Direction
    direction: str = ""  # buy, sell
    
    # Execution pattern
    execution_style: str = ""  # TWAP, VWAP, iceberg, etc.
    estimated_completion: float = 0.0  # percentage


class MarketImpactModel:
    """Market impact estimation model"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Model parameters (Almgren-Chriss style)
        self.temporary_impact_coef = self.config.get('temp_impact_coef', 0.1)
        self.permanent_impact_coef = self.config.get('perm_impact_coef', 0.05)
        self.volatility_impact_coef = self.config.get('vol_impact_coef', 0.5)
        
    def estimate_impact(
        self,
        order_size: float,
        side: str,
        adv: float,  # Average daily volume
        spread: float,
        volatility: float,
        urgency: float = 0.5  # 0 = patient, 1 = urgent
    ) -> MarketImpactEstimate:
        """Estimate market impact for an order"""
        
        # Participation rate
        participation = order_size / adv if adv > 0 else 0.01
        
        # Temporary impact (immediate price move)
        temp_impact = self.temporary_impact_coef * np.sqrt(participation) * volatility * 10000
        
        # Permanent impact (lasting price change)
        perm_impact = self.permanent_impact_coef * participation * volatility * 10000
        
        # Spread cost
        spread_cost = spread * 10000 / 2  # Half spread
        
        # Timing cost (opportunity cost of slow execution)
        timing_cost = volatility * 10000 * (1 - urgency) * np.sqrt(participation)
        
        # Total impact
        total_impact = temp_impact + perm_impact + spread_cost
        
        # Optimal execution time (minutes)
        optimal_time = int(60 * participation / 0.1)  # Target 10% participation
        optimal_time = max(5, min(optimal_time, 480))  # 5 min to 8 hours
        
        # Recommended algo
        if participation < 0.01:
            algo = "LIMIT"
        elif participation < 0.05:
            algo = "TWAP"
        elif participation < 0.1:
            algo = "VWAP"
        else:
            algo = "ICEBERG"
        
        # Slice size
        slice_size = order_size / max(optimal_time / 5, 1)
        
        return MarketImpactEstimate(
            timestamp=datetime.now(),
            symbol="",
            order_size=order_size,
            side=side,
            temporary_impact_bps=temp_impact,
            permanent_impact_bps=perm_impact,
            total_impact_bps=total_impact,
            spread_cost_bps=spread_cost,
            timing_cost_bps=timing_cost,
            opportunity_cost_bps=timing_cost * 0.5,
            optimal_execution_time=optimal_time,
            recommended_algo=algo,
            slice_size=slice_size
        )
    
    def minimize_impact(
        self,
        order_size: float,
        side: str,
        adv: float,
        spread: float,
        volatility: float,
        max_time: int = 60  # minutes
    ) -> Dict[str, Any]:
        """Find optimal execution to minimize impact"""
        
        best_impact = float('inf')
        best_params = {}
        
        # Try different participation rates
        for participation_target in [0.01, 0.02, 0.05, 0.1, 0.15, 0.2]:
            execution_time = order_size / (adv * participation_target / 390)  # 390 min trading day
            
            if execution_time > max_time:
                continue
            
            # Estimate impact
            estimate = self.estimate_impact(
                order_size, side, adv, spread, volatility,
                urgency=1 - execution_time / max_time
            )
            
            if estimate.total_impact_bps < best_impact:
                best_impact = estimate.total_impact_bps
                best_params = {
                    'participation_rate': participation_target,
                    'execution_time': int(execution_time),
                    'slice_size': order_size / max(execution_time / 5, 1),
                    'expected_impact_bps': estimate.total_impact_bps,
                    'algorithm': estimate.recommended_algo
                }
        
        return best_params


class HiddenLiquidityDetector:
    """Detect hidden liquidity in the market"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: deque = deque(maxlen=1000)
        self.quote_history: deque = deque(maxlen=1000)
        
    def add_trade(self, trade: Dict):
        """Add trade to history"""
        self.trade_history.append(trade)
    
    def add_quote(self, quote: Dict):
        """Add quote to history"""
        self.quote_history.append(quote)
    
    def detect(self, symbol: str) -> List[HiddenLiquidity]:
        """Detect hidden liquidity"""
        
        detections = []
        
        if len(self.trade_history) < 50:
            return detections
        
        trades = list(self.trade_history)
        
        # Method 1: Large trades at same price level
        price_volumes = {}
        for trade in trades:
            price = round(trade.get('price', 0), 4)
            size = trade.get('size', 0)
            if price not in price_volumes:
                price_volumes[price] = 0
            price_volumes[price] += size
        
        # Find price levels with unusually high volume
        volumes = list(price_volumes.values())
        if volumes:
            mean_vol = np.mean(volumes)
            std_vol = np.std(volumes)
            
            for price, vol in price_volumes.items():
                if vol > mean_vol + 2 * std_vol:
                    # Likely hidden liquidity
                    detections.append(HiddenLiquidity(
                        timestamp=datetime.now(),
                        symbol=symbol,
                        detected=True,
                        confidence=min((vol - mean_vol) / (std_vol + 1), 1.0),
                        estimated_hidden_size=vol - mean_vol,
                        price_level=price,
                        side='unknown',
                        source_type='iceberg'
                    ))
        
        # Method 2: Trade size patterns (iceberg detection)
        trade_sizes = [t.get('size', 0) for t in trades]
        if trade_sizes:
            # Look for repeated similar sizes
            size_counts = {}
            for size in trade_sizes:
                rounded = round(size, -2)  # Round to nearest 100
                size_counts[rounded] = size_counts.get(rounded, 0) + 1
            
            for size, count in size_counts.items():
                if count > 10 and size > 0:
                    # Repeated size suggests iceberg
                    detections.append(HiddenLiquidity(
                        timestamp=datetime.now(),
                        symbol=symbol,
                        detected=True,
                        confidence=min(count / 20, 1.0),
                        estimated_hidden_size=size * count,
                        price_level=0,
                        side='unknown',
                        source_type='iceberg'
                    ))
        
        return detections


class PredatorDetector:
    """Detect algorithmic predators"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.order_flow: deque = deque(maxlen=5000)
        self.quote_changes: deque = deque(maxlen=5000)
        
        # ML model for anomaly detection
        if SKLEARN_AVAILABLE:
            self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
            self.is_fitted = False
        else:
            self.anomaly_detector = None
            self.is_fitted = False
        
    def add_order_flow(self, order: Dict):
        """Add order flow data"""
        self.order_flow.append(order)
    
    def add_quote_change(self, quote: Dict):
        """Add quote change"""
        self.quote_changes.append(quote)
    
    def detect_spoofing(self, symbol: str) -> Optional[PredatorAlert]:
        """Detect spoofing activity"""
        
        if len(self.order_flow) < 100:
            return None
        
        orders = list(self.order_flow)
        
        # Look for large orders that are quickly cancelled
        cancel_ratio = sum(1 for o in orders if o.get('status') == 'cancelled') / len(orders)
        
        # Look for orders far from market
        far_orders = sum(1 for o in orders if o.get('distance_from_mid', 0) > 0.005)
        far_ratio = far_orders / len(orders)
        
        # Spoofing indicators
        if cancel_ratio > 0.8 and far_ratio > 0.5:
            return PredatorAlert(
                alert_id=str(hash(datetime.now()))[:8],
                timestamp=datetime.now(),
                symbol=symbol,
                predator_type=PredatorType.SPOOFING,
                threat_level=ThreatLevel.HIGH,
                confidence=min(cancel_ratio * far_ratio * 2, 1.0),
                description="High cancel rate with orders far from market",
                evidence=[
                    f"Cancel ratio: {cancel_ratio:.2%}",
                    f"Far order ratio: {far_ratio:.2%}"
                ],
                recommended_action="Avoid aggressive orders, use passive limits",
                avoid_trading=True
            )
        
        return None
    
    def detect_layering(self, symbol: str) -> Optional[PredatorAlert]:
        """Detect layering activity"""
        
        if len(self.quote_changes) < 100:
            return None
        
        quotes = list(self.quote_changes)
        
        # Look for multiple price levels being added/removed together
        bid_changes = [q.get('bid_levels_changed', 0) for q in quotes]
        ask_changes = [q.get('ask_levels_changed', 0) for q in quotes]
        
        # Layering: many levels change simultaneously
        multi_level_changes = sum(1 for b, a in zip(bid_changes, ask_changes) if b > 3 or a > 3)
        
        if multi_level_changes > len(quotes) * 0.3:
            return PredatorAlert(
                alert_id=str(hash(datetime.now()))[:8],
                timestamp=datetime.now(),
                symbol=symbol,
                predator_type=PredatorType.LAYERING,
                threat_level=ThreatLevel.MEDIUM,
                confidence=multi_level_changes / len(quotes),
                description="Multiple price levels changing simultaneously",
                evidence=[f"Multi-level changes: {multi_level_changes}"],
                recommended_action="Be cautious of apparent depth",
                avoid_trading=False
            )
        
        return None
    
    def detect_momentum_ignition(self, symbol: str, trades: List[Dict]) -> Optional[PredatorAlert]:
        """Detect momentum ignition"""
        
        if len(trades) < 50:
            return None
        
        # Look for sudden burst of same-direction trades
        recent = trades[-50:]
        buy_count = sum(1 for t in recent if t.get('side') == 'buy')
        sell_count = len(recent) - buy_count
        
        imbalance = abs(buy_count - sell_count) / len(recent)
        
        # Check for rapid price movement
        prices = [t.get('price', 0) for t in recent]
        if prices:
            price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        else:
            price_change = 0
        
        # Momentum ignition: extreme imbalance + rapid price move
        if imbalance > 0.8 and abs(price_change) > 0.005:
            return PredatorAlert(
                alert_id=str(hash(datetime.now()))[:8],
                timestamp=datetime.now(),
                symbol=symbol,
                predator_type=PredatorType.MOMENTUM_IGNITION,
                threat_level=ThreatLevel.HIGH,
                confidence=imbalance,
                description="Sudden burst of one-sided trades causing rapid price move",
                evidence=[
                    f"Trade imbalance: {imbalance:.2%}",
                    f"Price change: {price_change:.2%}"
                ],
                recommended_action="Wait for momentum to fade before trading",
                avoid_trading=True
            )
        
        return None
    
    def detect_quote_stuffing(self, symbol: str) -> Optional[PredatorAlert]:
        """Detect quote stuffing"""
        
        if len(self.quote_changes) < 100:
            return None
        
        quotes = list(self.quote_changes)
        
        # Calculate quote rate
        if len(quotes) >= 2:
            time_span = (quotes[-1].get('timestamp', datetime.now()) - 
                        quotes[0].get('timestamp', datetime.now()))
            if hasattr(time_span, 'total_seconds'):
                seconds = time_span.total_seconds()
            else:
                seconds = 1
            
            quote_rate = len(quotes) / max(seconds, 1)
            
            # Quote stuffing: extremely high quote rate
            if quote_rate > 100:  # More than 100 quotes per second
                return PredatorAlert(
                    alert_id=str(hash(datetime.now()))[:8],
                    timestamp=datetime.now(),
                    symbol=symbol,
                    predator_type=PredatorType.QUOTE_STUFFING,
                    threat_level=ThreatLevel.MEDIUM,
                    confidence=min(quote_rate / 200, 1.0),
                    description="Extremely high quote update rate",
                    evidence=[f"Quote rate: {quote_rate:.0f}/sec"],
                    recommended_action="Increase latency tolerance, avoid market orders",
                    avoid_trading=False
                )
        
        return None
    
    def detect_all(self, symbol: str, trades: List[Dict] = None) -> List[PredatorAlert]:
        """Run all predator detection"""
        
        alerts = []
        
        # Spoofing
        spoofing = self.detect_spoofing(symbol)
        if spoofing:
            alerts.append(spoofing)
        
        # Layering
        layering = self.detect_layering(symbol)
        if layering:
            alerts.append(layering)
        
        # Momentum ignition
        if trades:
            momentum = self.detect_momentum_ignition(symbol, trades)
            if momentum:
                alerts.append(momentum)
        
        # Quote stuffing
        stuffing = self.detect_quote_stuffing(symbol)
        if stuffing:
            alerts.append(stuffing)
        
        return alerts


class StopHuntPredictor:
    """Predict stop-hunt attempts"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.price_history: deque = deque(maxlen=1000)
        self.volume_history: deque = deque(maxlen=1000)
        
    def add_price(self, price: float, volume: float):
        """Add price and volume data"""
        self.price_history.append(price)
        self.volume_history.append(volume)
    
    def predict(self, symbol: str) -> StopHuntPrediction:
        """Predict stop-hunt probability"""
        
        if len(self.price_history) < 100:
            return StopHuntPrediction(
                timestamp=datetime.now(),
                symbol=symbol,
                probability=0.0
            )
        
        prices = np.array(list(self.price_history))
        volumes = np.array(list(self.volume_history))
        
        # Find potential stop levels (recent highs/lows)
        recent_high = np.max(prices[-50:])
        recent_low = np.min(prices[-50:])
        current_price = prices[-1]
        
        # Distance to potential stop levels
        dist_to_high = (recent_high - current_price) / current_price
        dist_to_low = (current_price - recent_low) / current_price
        
        # Stop cluster detection (prices cluster near round numbers or recent extremes)
        stop_cluster_up = dist_to_high < 0.005  # Within 0.5% of high
        stop_cluster_down = dist_to_low < 0.005  # Within 0.5% of low
        
        # Volume analysis (increasing volume near stops)
        recent_vol = np.mean(volumes[-10:])
        baseline_vol = np.mean(volumes[-50:-10]) if len(volumes) > 50 else recent_vol
        vol_spike = recent_vol > baseline_vol * 1.5
        
        # Price momentum toward stops
        momentum = (prices[-1] - prices[-10]) / prices[-10] if len(prices) > 10 else 0
        
        # Calculate probability
        probability = 0.0
        direction = ""
        target_level = 0.0
        
        if stop_cluster_up and momentum > 0:
            probability = 0.3 + (0.3 if vol_spike else 0) + min(momentum * 10, 0.3)
            direction = "up"
            target_level = recent_high * 1.002  # Just above high
        elif stop_cluster_down and momentum < 0:
            probability = 0.3 + (0.3 if vol_spike else 0) + min(abs(momentum) * 10, 0.3)
            direction = "down"
            target_level = recent_low * 0.998  # Just below low
        
        return StopHuntPrediction(
            timestamp=datetime.now(),
            symbol=symbol,
            probability=min(probability, 1.0),
            direction=direction,
            target_level=target_level,
            stop_cluster_detected=stop_cluster_up or stop_cluster_down,
            unusual_activity=vol_spike,
            expected_timeframe="5-30 minutes" if probability > 0.5 else "unknown"
        )


class InstitutionalFootprintAnalyzer:
    """Reverse-engineer institutional footprints"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: deque = deque(maxlen=10000)
        
    def add_trade(self, trade: Dict):
        """Add trade to history"""
        self.trade_history.append(trade)
    
    def analyze(self, symbol: str) -> InstitutionalFootprint:
        """Analyze for institutional activity"""
        
        if len(self.trade_history) < 500:
            return InstitutionalFootprint(
                timestamp=datetime.now(),
                symbol=symbol,
                detected=False
            )
        
        trades = list(self.trade_history)
        
        # Method 1: VWAP tracking
        # Institutions often execute at VWAP
        prices = np.array([t.get('price', 0) for t in trades])
        volumes = np.array([t.get('size', 0) for t in trades])
        
        if volumes.sum() > 0:
            vwap = np.sum(prices * volumes) / np.sum(volumes)
            
            # Check if trades cluster around VWAP
            vwap_deviation = np.abs(prices - vwap) / vwap
            vwap_trades = np.sum(vwap_deviation < 0.001)  # Within 0.1% of VWAP
            vwap_ratio = vwap_trades / len(trades)
        else:
            vwap_ratio = 0
        
        # Method 2: Time-weighted execution pattern
        # Look for consistent trade sizes over time
        trade_sizes = [t.get('size', 0) for t in trades]
        size_std = np.std(trade_sizes) / (np.mean(trade_sizes) + 1)
        consistent_sizing = size_std < 0.5
        
        # Method 3: Direction consistency
        buy_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'buy')
        sell_volume = sum(t.get('size', 0) for t in trades if t.get('side') == 'sell')
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            direction_bias = abs(buy_volume - sell_volume) / total_volume
            direction = 'buy' if buy_volume > sell_volume else 'sell'
        else:
            direction_bias = 0
            direction = 'unknown'
        
        # Determine if institutional
        institutional_score = (
            0.4 * vwap_ratio +
            0.3 * (1 if consistent_sizing else 0) +
            0.3 * direction_bias
        )
        
        detected = institutional_score > 0.5
        
        # Estimate activity type
        if detected:
            if direction_bias > 0.7:
                activity_type = 'accumulation' if direction == 'buy' else 'distribution'
            else:
                activity_type = 'rebalancing'
            
            # Estimate execution style
            if vwap_ratio > 0.3:
                execution_style = 'VWAP'
            elif consistent_sizing:
                execution_style = 'TWAP'
            else:
                execution_style = 'iceberg'
        else:
            activity_type = 'unknown'
            execution_style = 'unknown'
        
        return InstitutionalFootprint(
            timestamp=datetime.now(),
            symbol=symbol,
            detected=detected,
            confidence=institutional_score,
            activity_type=activity_type,
            estimated_size=total_volume,
            direction=direction,
            execution_style=execution_style,
            estimated_completion=0.5  # Would need more context
        )


class MarketImpactPredatorSystem:
    """
    Complete Market Impact Minimization & Predator Detection System.
    
    Features:
    - Market impact estimation and minimization
    - Hidden liquidity detection
    - Algorithmic predator detection
    - Stop-hunt prediction
    - Institutional footprint analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.impact_model = MarketImpactModel(config)
        self.hidden_liquidity_detector = HiddenLiquidityDetector(config)
        self.predator_detector = PredatorDetector(config)
        self.stop_hunt_predictor = StopHuntPredictor(config)
        self.institutional_analyzer = InstitutionalFootprintAnalyzer(config)
        
        # Alert history
        self.alert_history: List[PredatorAlert] = []
        
        logger.info("MarketImpactPredatorSystem initialized")
    
    def estimate_impact(
        self,
        symbol: str,
        order_size: float,
        side: str,
        adv: float,
        spread: float,
        volatility: float
    ) -> MarketImpactEstimate:
        """Estimate market impact for an order"""
        
        estimate = self.impact_model.estimate_impact(
            order_size, side, adv, spread, volatility
        )
        estimate.symbol = symbol
        
        return estimate
    
    def minimize_impact(
        self,
        symbol: str,
        order_size: float,
        side: str,
        adv: float,
        spread: float,
        volatility: float,
        max_time: int = 60
    ) -> Dict[str, Any]:
        """Find optimal execution to minimize impact"""
        
        return self.impact_model.minimize_impact(
            order_size, side, adv, spread, volatility, max_time
        )
    
    def detect_hidden_liquidity(self, symbol: str) -> List[HiddenLiquidity]:
        """Detect hidden liquidity"""
        return self.hidden_liquidity_detector.detect(symbol)
    
    def detect_predators(
        self,
        symbol: str,
        trades: List[Dict] = None
    ) -> List[PredatorAlert]:
        """Detect algorithmic predators"""
        
        alerts = self.predator_detector.detect_all(symbol, trades)
        self.alert_history.extend(alerts)
        
        return alerts
    
    def predict_stop_hunt(self, symbol: str) -> StopHuntPrediction:
        """Predict stop-hunt probability"""
        return self.stop_hunt_predictor.predict(symbol)
    
    def analyze_institutional_activity(self, symbol: str) -> InstitutionalFootprint:
        """Analyze institutional footprints"""
        return self.institutional_analyzer.analyze(symbol)
    
    def add_trade(self, trade: Dict):
        """Add trade data to all analyzers"""
        self.hidden_liquidity_detector.add_trade(trade)
        self.predator_detector.add_order_flow(trade)
        self.institutional_analyzer.add_trade(trade)
        
        price = trade.get('price', 0)
        volume = trade.get('size', 0)
        self.stop_hunt_predictor.add_price(price, volume)
    
    def add_quote(self, quote: Dict):
        """Add quote data"""
        self.hidden_liquidity_detector.add_quote(quote)
        self.predator_detector.add_quote_change(quote)
    
    def get_market_assessment(self, symbol: str, trades: List[Dict] = None) -> Dict[str, Any]:
        """Get complete market assessment"""
        
        # Detect predators
        predator_alerts = self.detect_predators(symbol, trades)
        
        # Detect hidden liquidity
        hidden_liquidity = self.detect_hidden_liquidity(symbol)
        
        # Predict stop hunts
        stop_hunt = self.predict_stop_hunt(symbol)
        
        # Analyze institutional activity
        institutional = self.analyze_institutional_activity(symbol)
        
        # Overall threat level
        if any(a.threat_level == ThreatLevel.CRITICAL for a in predator_alerts):
            overall_threat = ThreatLevel.CRITICAL
        elif any(a.threat_level == ThreatLevel.HIGH for a in predator_alerts):
            overall_threat = ThreatLevel.HIGH
        elif any(a.threat_level == ThreatLevel.MEDIUM for a in predator_alerts):
            overall_threat = ThreatLevel.MEDIUM
        elif predator_alerts:
            overall_threat = ThreatLevel.LOW
        else:
            overall_threat = ThreatLevel.NONE
        
        # Trading recommendation
        if overall_threat in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            recommendation = "AVOID_TRADING"
        elif stop_hunt.probability > 0.7:
            recommendation = "CAUTION_STOP_HUNT"
        elif institutional.detected:
            recommendation = "FOLLOW_INSTITUTIONAL"
        else:
            recommendation = "NORMAL_TRADING"
        
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'overall_threat_level': overall_threat.name,
            'recommendation': recommendation,
            'predator_alerts': [
                {
                    'type': a.predator_type.name,
                    'threat_level': a.threat_level.name,
                    'confidence': a.confidence,
                    'description': a.description
                }
                for a in predator_alerts
            ],
            'hidden_liquidity': [
                {
                    'detected': h.detected,
                    'estimated_size': h.estimated_hidden_size,
                    'price_level': h.price_level
                }
                for h in hidden_liquidity
            ],
            'stop_hunt_prediction': {
                'probability': stop_hunt.probability,
                'direction': stop_hunt.direction,
                'target_level': stop_hunt.target_level
            },
            'institutional_activity': {
                'detected': institutional.detected,
                'activity_type': institutional.activity_type,
                'direction': institutional.direction,
                'execution_style': institutional.execution_style
            }
        }
    
    def should_trade(self, symbol: str) -> Tuple[bool, str]:
        """Determine if it's safe to trade"""
        
        assessment = self.get_market_assessment(symbol)
        
        if assessment['overall_threat_level'] in ['CRITICAL', 'HIGH']:
            return False, f"High threat level: {assessment['overall_threat_level']}"
        
        if assessment['stop_hunt_prediction']['probability'] > 0.7:
            return False, "High stop-hunt probability"
        
        return True, "Market conditions acceptable"


# Factory function
def create_impact_predator_system(config: Optional[Dict] = None) -> MarketImpactPredatorSystem:
    """Create and return a MarketImpactPredatorSystem instance"""
    return MarketImpactPredatorSystem(config)
