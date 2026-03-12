"""
AlphaAlgo MSOS - Market Tradability Gate (Layer 0)

Before any strategy is evaluated, determine whether the market itself is tradable.

INVALIDATION CONDITIONS:
- Liquidity is unstable
- Spreads are erratic
- Volatility structure is incoherent
- Order flow entropy exceeds stability thresholds
- Event risk dominates signal semantics

If the market is invalid → flat exposure enforced. No exceptions.

Author: AlphaAlgo MSOS
"""

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class MarketValidity(Enum):
    """Market validity states"""
    VALID = auto()           # Market is tradable
    DEGRADED = auto()        # Market is partially tradable with reduced exposure
    INVALID = auto()         # Market is NOT tradable
    UNKNOWN = auto()         # Cannot determine validity


class LiquidityState(Enum):
    """Liquidity states"""
    STABLE = auto()
    UNSTABLE = auto()
    VACUUM = auto()
    UNKNOWN = auto()


class SpreadState(Enum):
    """Spread states"""
    NORMAL = auto()
    ELEVATED = auto()
    ERRATIC = auto()
    UNKNOWN = auto()


class VolatilityStructure(Enum):
    """Volatility structure states"""
    COHERENT = auto()
    TRANSITIONING = auto()
    INCOHERENT = auto()
    EXPLOSIVE = auto()
    UNKNOWN = auto()


class OrderFlowEntropy(Enum):
    """Order flow entropy states"""
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    EXTREME = auto()
    UNKNOWN = auto()


class EventRisk(Enum):
    """Event risk states"""
    NONE = auto()
    LOW = auto()
    MODERATE = auto()
    HIGH = auto()
    DOMINANT = auto()


@dataclass
class LiquidityMetrics:
    """Metrics for liquidity analysis"""
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    depth_imbalance: float = 0.0
    depth_stability: float = 0.0  # Rolling std of depth
    fill_rate: float = 1.0
    slippage_estimate: float = 0.0
    liquidity_score: float = 0.0
    state: LiquidityState = LiquidityState.UNKNOWN
    
    def calculate_score(self) -> float:
        """Calculate overall liquidity score (0-1)"""
        try:
            if self.bid_depth <= 0 or self.ask_depth <= 0:
                return 0.0
        
            # Depth score
            total_depth = self.bid_depth + self.ask_depth
            depth_score = min(1.0, total_depth / 1000000)  # Normalize to $1M
        
            # Imbalance penalty
            imbalance_penalty = abs(self.depth_imbalance)
        
            # Stability score
            stability_score = max(0, 1 - self.depth_stability)
        
            # Fill rate score
            fill_score = self.fill_rate
        
            # Slippage penalty
            slippage_penalty = min(1.0, self.slippage_estimate * 100)  # 1% = full penalty
        
            self.liquidity_score = (
                depth_score * 0.3 +
                (1 - imbalance_penalty) * 0.2 +
                stability_score * 0.2 +
                fill_score * 0.2 +
                (1 - slippage_penalty) * 0.1
            )
        
            return self.liquidity_score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise
    
    def determine_state(self) -> LiquidityState:
        """Determine liquidity state from metrics"""
        try:
            score = self.calculate_score()
        
            if score >= 0.7:
                self.state = LiquidityState.STABLE
            elif score >= 0.4:
                self.state = LiquidityState.UNSTABLE
            elif score > 0:
                self.state = LiquidityState.VACUUM
            else:
                self.state = LiquidityState.UNKNOWN
        
            return self.state
        except Exception as e:
            logger.error(f"Error in determine_state: {e}")
            raise


@dataclass
class SpreadMetrics:
    """Metrics for spread analysis"""
    current_spread: float = 0.0
    average_spread: float = 0.0
    spread_volatility: float = 0.0
    spread_percentile: float = 0.0  # Current spread vs historical
    spread_score: float = 0.0
    state: SpreadState = SpreadState.UNKNOWN
    
    def calculate_score(self, max_spread: float = 0.005) -> float:
        """Calculate spread score (0-1, higher is better)"""
        try:
            if self.current_spread <= 0:
                return 0.0
        
            # Spread level score
            level_score = max(0, 1 - (self.current_spread / max_spread))
        
            # Volatility penalty
            volatility_penalty = min(1.0, self.spread_volatility * 10)
        
            # Percentile score (lower percentile = better)
            percentile_score = max(0, 1 - self.spread_percentile)
        
            self.spread_score = (
                level_score * 0.5 +
                (1 - volatility_penalty) * 0.3 +
                percentile_score * 0.2
            )
        
            return self.spread_score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise
    
    def determine_state(self) -> SpreadState:
        """Determine spread state from metrics"""
        try:
            score = self.calculate_score()
        
            if score >= 0.7:
                self.state = SpreadState.NORMAL
            elif score >= 0.4:
                self.state = SpreadState.ELEVATED
            else:
                self.state = SpreadState.ERRATIC
        
            return self.state
        except Exception as e:
            logger.error(f"Error in determine_state: {e}")
            raise


@dataclass
class VolatilityMetrics:
    """Metrics for volatility structure analysis"""
    realized_volatility: float = 0.0
    implied_volatility: float = 0.0
    volatility_of_volatility: float = 0.0
    volatility_term_structure: List[float] = field(default_factory=list)
    volatility_skew: float = 0.0
    volatility_score: float = 0.0
    state: VolatilityStructure = VolatilityStructure.UNKNOWN
    
    def calculate_score(self, max_volatility: float = 0.10) -> float:
        """Calculate volatility structure score (0-1)"""
        # Level score
        try:
            level_score = max(0, 1 - (self.realized_volatility / max_volatility))
        
            # Vol-of-vol penalty
            vov_penalty = min(1.0, self.volatility_of_volatility * 5)
        
            # Term structure coherence
            if len(self.volatility_term_structure) >= 2:
                term_std = np.std(self.volatility_term_structure)
                term_score = max(0, 1 - term_std * 10)
            else:
                term_score = 0.5
        
            # Skew penalty
            skew_penalty = min(1.0, abs(self.volatility_skew) * 2)
        
            self.volatility_score = (
                level_score * 0.4 +
                (1 - vov_penalty) * 0.3 +
                term_score * 0.2 +
                (1 - skew_penalty) * 0.1
            )
        
            return self.volatility_score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise
    
    def determine_state(self) -> VolatilityStructure:
        """Determine volatility structure state"""
        try:
            score = self.calculate_score()
        
            if self.volatility_of_volatility > 0.5:
                self.state = VolatilityStructure.EXPLOSIVE
            elif score >= 0.7:
                self.state = VolatilityStructure.COHERENT
            elif score >= 0.4:
                self.state = VolatilityStructure.TRANSITIONING
            else:
                self.state = VolatilityStructure.INCOHERENT
        
            return self.state
        except Exception as e:
            logger.error(f"Error in determine_state: {e}")
            raise


@dataclass
class EntropyMetrics:
    """Metrics for order flow entropy analysis"""
    order_flow_entropy: float = 0.0  # Shannon entropy of order flow
    trade_clustering: float = 0.0
    volume_entropy: float = 0.0
    direction_entropy: float = 0.0
    entropy_score: float = 0.0
    state: OrderFlowEntropy = OrderFlowEntropy.UNKNOWN
    
    def calculate_score(self, max_entropy: float = 2.0) -> float:
        """Calculate entropy score (0-1, lower entropy = higher score)"""
        # Normalize entropy
        try:
            normalized_entropy = min(1.0, self.order_flow_entropy / max_entropy)
        
            # Clustering penalty (high clustering = less predictable)
            clustering_penalty = self.trade_clustering
        
            # Volume entropy penalty
            volume_penalty = min(1.0, self.volume_entropy / max_entropy)
        
            # Direction entropy (high = random, low = trending)
            direction_penalty = min(1.0, self.direction_entropy / 1.0)
        
            self.entropy_score = (
                (1 - normalized_entropy) * 0.4 +
                (1 - clustering_penalty) * 0.2 +
                (1 - volume_penalty) * 0.2 +
                (1 - direction_penalty) * 0.2
            )
        
            return self.entropy_score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise
    
    def determine_state(self) -> OrderFlowEntropy:
        """Determine entropy state"""
        try:
            score = self.calculate_score()
        
            if score >= 0.7:
                self.state = OrderFlowEntropy.LOW
            elif score >= 0.5:
                self.state = OrderFlowEntropy.MODERATE
            elif score >= 0.3:
                self.state = OrderFlowEntropy.HIGH
            else:
                self.state = OrderFlowEntropy.EXTREME
        
            return self.state
        except Exception as e:
            logger.error(f"Error in determine_state: {e}")
            raise


@dataclass
class EventRiskMetrics:
    """Metrics for event risk analysis"""
    scheduled_events: List[Dict[str, Any]] = field(default_factory=list)
    event_proximity_hours: float = float('inf')
    event_impact_estimate: float = 0.0
    news_velocity: float = 0.0
    sentiment_volatility: float = 0.0
    event_score: float = 0.0
    state: EventRisk = EventRisk.NONE
    
    def calculate_score(self) -> float:
        """Calculate event risk score (0-1, lower risk = higher score)"""
        # Proximity score (further = better)
        try:
            if self.event_proximity_hours <= 0:
                proximity_score = 0.0
            elif self.event_proximity_hours >= 24:
                proximity_score = 1.0
            else:
                proximity_score = self.event_proximity_hours / 24
        
            # Impact penalty
            impact_penalty = min(1.0, self.event_impact_estimate)
        
            # News velocity penalty
            news_penalty = min(1.0, self.news_velocity / 10)  # 10 news/hour = max
        
            # Sentiment volatility penalty
            sentiment_penalty = min(1.0, self.sentiment_volatility * 2)
        
            self.event_score = (
                proximity_score * 0.4 +
                (1 - impact_penalty) * 0.3 +
                (1 - news_penalty) * 0.15 +
                (1 - sentiment_penalty) * 0.15
            )
        
            return self.event_score
        except Exception as e:
            logger.error(f"Error in calculate_score: {e}")
            raise
    
    def determine_state(self) -> EventRisk:
        """Determine event risk state"""
        try:
            score = self.calculate_score()
        
            if score >= 0.8:
                self.state = EventRisk.NONE
            elif score >= 0.6:
                self.state = EventRisk.LOW
            elif score >= 0.4:
                self.state = EventRisk.MODERATE
            elif score >= 0.2:
                self.state = EventRisk.HIGH
            else:
                self.state = EventRisk.DOMINANT
        
            return self.state
        except Exception as e:
            logger.error(f"Error in determine_state: {e}")
            raise


@dataclass
class TradabilityResult:
    """Result from market tradability gate"""
    validity: MarketValidity
    is_tradable: bool
    exposure_multiplier: float  # 0-1, how much to reduce exposure
    reason: str
    liquidity: LiquidityMetrics
    spread: SpreadMetrics
    volatility: VolatilityMetrics
    entropy: EntropyMetrics
    event_risk: EventRiskMetrics
    overall_score: float
    invalidation_reasons: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'validity': self.validity.name,
            'is_tradable': self.is_tradable,
            'exposure_multiplier': self.exposure_multiplier,
            'reason': self.reason,
            'overall_score': self.overall_score,
            'liquidity_state': self.liquidity.state.name,
            'spread_state': self.spread.state.name,
            'volatility_state': self.volatility.state.name,
            'entropy_state': self.entropy.state.name,
            'event_risk_state': self.event_risk.state.name,
            'invalidation_reasons': self.invalidation_reasons,
            'timestamp': self.timestamp
        }


class MarketTradabilityGate:
    """
    Market Tradability Gate - Layer 0 of MSOS
    
    This gate determines whether the market is structurally tradable
    BEFORE any strategy evaluation occurs.
    
    If market is invalid → flat exposure enforced. No exceptions.
    """
    
    # Thresholds for invalidation
    MIN_LIQUIDITY_SCORE = 0.3
    MIN_SPREAD_SCORE = 0.3
    MIN_VOLATILITY_SCORE = 0.2
    MIN_ENTROPY_SCORE = 0.2
    MIN_EVENT_SCORE = 0.2
    MIN_OVERALL_SCORE = 0.4
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.tradability")
        
            # History for rolling calculations
            self._liquidity_history: Deque[float] = deque(maxlen=100)
            self._spread_history: Deque[float] = deque(maxlen=100)
            self._volatility_history: Deque[float] = deque(maxlen=100)
            self._entropy_history: Deque[float] = deque(maxlen=100)
        
            self.logger.info("Market Tradability Gate initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def evaluate(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> TradabilityResult:
        """
        Evaluate market tradability.
        
        Returns TradabilityResult with validity status and exposure multiplier.
        """
        try:
            invalidation_reasons = []
        
            # Analyze each component
            liquidity = self._analyze_liquidity(market_data)
            spread = self._analyze_spread(market_data)
            volatility = self._analyze_volatility(market_data)
            entropy = self._analyze_entropy(market_data)
            event_risk = self._analyze_event_risk(market_data)
        
            # Check for invalidation conditions
            if liquidity.state == LiquidityState.VACUUM:
                invalidation_reasons.append("Liquidity vacuum detected")
            elif liquidity.state == LiquidityState.UNSTABLE:
                invalidation_reasons.append("Liquidity unstable")
        
            if spread.state == SpreadState.ERRATIC:
                invalidation_reasons.append("Spreads are erratic")
        
            if volatility.state == VolatilityStructure.INCOHERENT:
                invalidation_reasons.append("Volatility structure incoherent")
            elif volatility.state == VolatilityStructure.EXPLOSIVE:
                invalidation_reasons.append("Volatility is explosive")
        
            if entropy.state == OrderFlowEntropy.EXTREME:
                invalidation_reasons.append("Order flow entropy exceeds threshold")
        
            if event_risk.state == EventRisk.DOMINANT:
                invalidation_reasons.append("Event risk dominates signal semantics")
        
            # Calculate overall score
            overall_score = (
                liquidity.liquidity_score * 0.25 +
                spread.spread_score * 0.20 +
                volatility.volatility_score * 0.25 +
                entropy.entropy_score * 0.15 +
                event_risk.event_score * 0.15
            )
        
            # Determine validity
            if len(invalidation_reasons) > 0 or overall_score < self.MIN_OVERALL_SCORE:
                validity = MarketValidity.INVALID
                is_tradable = False
                exposure_multiplier = 0.0
                reason = f"Market invalid: {'; '.join(invalidation_reasons)}" if invalidation_reasons else "Overall score too low"
            elif overall_score < 0.6:
                validity = MarketValidity.DEGRADED
                is_tradable = True
                exposure_multiplier = overall_score  # Reduce exposure proportionally
                reason = f"Market degraded - exposure reduced to {exposure_multiplier:.1%}"
            else:
                validity = MarketValidity.VALID
                is_tradable = True
                exposure_multiplier = 1.0
                reason = "Market is tradable"
        
            result = TradabilityResult(
                validity=validity,
                is_tradable=is_tradable,
                exposure_multiplier=exposure_multiplier,
                reason=reason,
                liquidity=liquidity,
                spread=spread,
                volatility=volatility,
                entropy=entropy,
                event_risk=event_risk,
                overall_score=overall_score,
                invalidation_reasons=invalidation_reasons
            )
        
            self.logger.info(
                f"[{symbol}] Tradability: {validity.name} | Score: {overall_score:.2f} | "
                f"Exposure: {exposure_multiplier:.1%}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def _analyze_liquidity(self, market_data: Dict[str, Any]) -> LiquidityMetrics:
        """Analyze liquidity conditions"""
        try:
            metrics = LiquidityMetrics()
        
            # Extract from market data
            metrics.bid_depth = market_data.get('bid_depth', 0)
            metrics.ask_depth = market_data.get('ask_depth', 0)
        
            if metrics.bid_depth + metrics.ask_depth > 0:
                metrics.depth_imbalance = (
                    (metrics.bid_depth - metrics.ask_depth) /
                    (metrics.bid_depth + metrics.ask_depth)
                )
        
            metrics.fill_rate = market_data.get('fill_rate', 1.0)
            metrics.slippage_estimate = market_data.get('slippage', 0.0)
        
            # Calculate stability from history
            self._liquidity_history.append(metrics.bid_depth + metrics.ask_depth)
            if len(self._liquidity_history) >= 10:
                metrics.depth_stability = np.std(list(self._liquidity_history)) / (np.mean(list(self._liquidity_history)) + 1e-10)
        
            metrics.calculate_score()
            metrics.determine_state()
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _analyze_liquidity: {e}")
            raise
    
    def _analyze_spread(self, market_data: Dict[str, Any]) -> SpreadMetrics:
        """Analyze spread conditions"""
        try:
            metrics = SpreadMetrics()
        
            bid = market_data.get('bid', 0)
            ask = market_data.get('ask', 0)
            mid = (bid + ask) / 2 if bid and ask else 0
        
            if mid > 0:
                metrics.current_spread = (ask - bid) / mid
        
            # Track history
            self._spread_history.append(metrics.current_spread)
            if len(self._spread_history) >= 10:
                metrics.average_spread = np.mean(list(self._spread_history))
                metrics.spread_volatility = np.std(list(self._spread_history))
            
                # Calculate percentile
                sorted_spreads = sorted(self._spread_history)
                idx = sorted_spreads.index(metrics.current_spread) if metrics.current_spread in sorted_spreads else len(sorted_spreads) // 2
                metrics.spread_percentile = idx / len(sorted_spreads)
        
            metrics.calculate_score()
            metrics.determine_state()
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _analyze_spread: {e}")
            raise
    
    def _analyze_volatility(self, market_data: Dict[str, Any]) -> VolatilityMetrics:
        """Analyze volatility structure"""
        try:
            metrics = VolatilityMetrics()
        
            metrics.realized_volatility = market_data.get('realized_volatility', 0.02)
            metrics.implied_volatility = market_data.get('implied_volatility', 0.02)
        
            # Track history for vol-of-vol
            self._volatility_history.append(metrics.realized_volatility)
            if len(self._volatility_history) >= 10:
                metrics.volatility_of_volatility = np.std(list(self._volatility_history))
        
            # Term structure if available
            metrics.volatility_term_structure = market_data.get('vol_term_structure', [])
            metrics.volatility_skew = market_data.get('vol_skew', 0.0)
        
            metrics.calculate_score()
            metrics.determine_state()
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _analyze_volatility: {e}")
            raise
    
    def _analyze_entropy(self, market_data: Dict[str, Any]) -> EntropyMetrics:
        """Analyze order flow entropy"""
        try:
            metrics = EntropyMetrics()
        
            # Calculate entropy from trade data if available
            trades = market_data.get('recent_trades', [])
            if trades:
                # Direction entropy
                directions = [1 if t.get('side') == 'buy' else -1 for t in trades]
                if directions:
                    buy_ratio = sum(1 for d in directions if d > 0) / len(directions)
                    if 0 < buy_ratio < 1:
                        metrics.direction_entropy = -buy_ratio * np.log2(buy_ratio) - (1-buy_ratio) * np.log2(1-buy_ratio)
            
                # Volume entropy
                volumes = [t.get('volume', 0) for t in trades]
                if volumes and sum(volumes) > 0:
                    probs = [v / sum(volumes) for v in volumes if v > 0]
                    metrics.volume_entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        
            metrics.order_flow_entropy = market_data.get('order_flow_entropy', 0.5)
            metrics.trade_clustering = market_data.get('trade_clustering', 0.0)
        
            self._entropy_history.append(metrics.order_flow_entropy)
        
            metrics.calculate_score()
            metrics.determine_state()
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _analyze_entropy: {e}")
            raise
    
    def _analyze_event_risk(self, market_data: Dict[str, Any]) -> EventRiskMetrics:
        """Analyze event risk"""
        try:
            metrics = EventRiskMetrics()
        
            metrics.scheduled_events = market_data.get('scheduled_events', [])
            metrics.event_proximity_hours = market_data.get('event_proximity_hours', float('inf'))
            metrics.event_impact_estimate = market_data.get('event_impact', 0.0)
            metrics.news_velocity = market_data.get('news_velocity', 0.0)
            metrics.sentiment_volatility = market_data.get('sentiment_volatility', 0.0)
        
            metrics.calculate_score()
            metrics.determine_state()
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _analyze_event_risk: {e}")
            raise
    
    def reset_history(self):
        """Reset all history buffers"""
        try:
            self._liquidity_history.clear()
            self._spread_history.clear()
            self._volatility_history.clear()
            self._entropy_history.clear()
        except Exception as e:
            logger.error(f"Error in reset_history: {e}")
            raise
