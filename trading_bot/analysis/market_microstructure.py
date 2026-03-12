"""
Elite Trading Bot - Market Microstructure Analyzer

This module provides advanced market microstructure analysis including
spread analysis, market depth, price discovery, and institutional flow detection.
"""

import enum
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import uuid

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from collections import deque
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class MarketRegime(enum.Enum):
    """Market microstructure regimes."""
    LIQUID = "liquid"                   # High liquidity, tight spreads
    ILLIQUID = "illiquid"              # Low liquidity, wide spreads
    STRESSED = "stressed"               # Market stress conditions
    VOLATILE = "volatile"               # High volatility regime
    TRENDING = "trending"               # Strong directional movement
    RANGING = "ranging"                 # Sideways consolidation


class InstitutionalFlow(enum.Enum):
    """Types of institutional flow."""
    ACCUMULATION = "accumulation"       # Institutional buying
    DISTRIBUTION = "distribution"       # Institutional selling
    NEUTRAL = "neutral"                # Balanced flow
    ROTATION = "rotation"              # Sector/asset rotation


@dataclass
class MicrostructureMetrics:
    """Market microstructure metrics."""
    timestamp: datetime
    
    # Spread metrics
    bid_ask_spread: float = 0.0
    effective_spread: float = 0.0
    realized_spread: float = 0.0
    price_impact: float = 0.0
    
    # Depth metrics
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    total_depth: float = 0.0
    depth_imbalance: float = 0.0
    
    # Flow metrics
    order_flow_imbalance: float = 0.0
    trade_size_ratio: float = 0.0
    institutional_flow_ratio: float = 0.0
    
    # Quality metrics
    market_quality_score: float = 0.0
    liquidity_score: float = 0.0
    efficiency_score: float = 0.0
    
    # Regime classification
    regime: MarketRegime = MarketRegime.LIQUID
    institutional_flow: InstitutionalFlow = InstitutionalFlow.NEUTRAL


@dataclass
class OrderBookLevel:
    """Order book level data."""
    price: float
    size: float
    orders: int = 1
    side: str = "bid"  # "bid" or "ask"


@dataclass
class OrderBookSnapshot:
    """Order book snapshot."""
    timestamp: datetime
    symbol: str
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)
    mid_price: float = 0.0
    spread: float = 0.0
    total_bid_size: float = 0.0
    total_ask_size: float = 0.0


@dataclass
class TradeData:
    """Individual trade data."""
    timestamp: datetime
    price: float
    size: float
    side: str  # "buy" or "sell"
    trade_type: str = "market"  # "market" or "limit"
    institutional: bool = False


class MarketMicrostructureAnalyzer:
    """
    Advanced market microstructure analysis system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize market microstructure analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Microstructure tracking
        self.metrics_history: Dict[str, deque] = {}
        self.orderbook_history: Dict[str, deque] = {}
        self.trade_history: Dict[str, deque] = {}
        
        logger.info("MarketMicrostructureAnalyzer initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "history_size": 1000,           # Maximum history to keep
            "depth_levels": 10,             # Order book levels to analyze
            "large_trade_threshold": 10000, # Threshold for large trades
            "institutional_size_ratio": 5.0, # Multiple of average for institutional
            "spread_percentile": 95,        # Percentile for spread analysis
            "liquidity_window": 20,         # Window for liquidity calculation
            "regime_window": 50,            # Window for regime detection
            "quality_weights": {            # Weights for quality score
                "spread": 0.3,
                "depth": 0.3,
                "impact": 0.2,
                "flow": 0.2
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def analyze_microstructure(self,
                             orderbook_data: List[OrderBookSnapshot],
                             trade_data: List[TradeData],
                             symbol: str) -> MicrostructureMetrics:
        """
        Analyze market microstructure from order book and trade data.
        
        Args:
            orderbook_data: Order book snapshots
            trade_data: Trade data
            symbol: Trading symbol
            
        Returns:
            MicrostructureMetrics with analysis results
        """
        if not orderbook_data and not trade_data:
            return MicrostructureMetrics(datetime.now())
        
        current_time = datetime.now()
        
        # Calculate spread metrics
        spread_metrics = self._calculate_spread_metrics(orderbook_data, trade_data)
        
        # Calculate depth metrics
        depth_metrics = self._calculate_depth_metrics(orderbook_data)
        
        # Calculate flow metrics
        flow_metrics = self._calculate_flow_metrics(trade_data)
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(spread_metrics, depth_metrics, flow_metrics)
        
        # Detect market regime
        regime = self._detect_market_regime(orderbook_data, trade_data)
        
        # Detect institutional flow
        institutional_flow = self._detect_institutional_flow(trade_data)
        
        # Create metrics object
        metrics = MicrostructureMetrics(
            timestamp=current_time,
            **spread_metrics,
            **depth_metrics,
            **flow_metrics,
            **quality_scores,
            regime=regime,
            institutional_flow=institutional_flow
        )
        
        # Update history
        self._update_history(symbol, metrics, orderbook_data, trade_data)
        
        return metrics
    
    def _calculate_spread_metrics(self,
                                orderbook_data: List[OrderBookSnapshot],
                                trade_data: List[TradeData]) -> Dict[str, float]:
        """Calculate spread-related metrics."""
        metrics = {
            "bid_ask_spread": 0.0,
            "effective_spread": 0.0,
            "realized_spread": 0.0,
            "price_impact": 0.0
        }
        
        if not orderbook_data:
            return metrics
        
        # Bid-ask spread
        spreads = []
        for snapshot in orderbook_data:
            if snapshot.bids and snapshot.asks:
                spread = snapshot.asks[0].price - snapshot.bids[0].price
                spreads.append(spread)
        
        if spreads:
            metrics["bid_ask_spread"] = np.mean(spreads)
        
        # Effective spread (from trades)
        if trade_data and orderbook_data:
            effective_spreads = []
            
            for trade in trade_data:
                # Find closest order book snapshot
                closest_ob = min(orderbook_data, 
                               key=lambda x: abs((x.timestamp - trade.timestamp).total_seconds()))
                
                if closest_ob.mid_price > 0:
                    if trade.side == "buy":
                        effective_spread = 2 * (trade.price - closest_ob.mid_price)
                    else:
                        effective_spread = 2 * (closest_ob.mid_price - trade.price)
                    
                    effective_spreads.append(abs(effective_spread))
            
            if effective_spreads:
                metrics["effective_spread"] = np.mean(effective_spreads)
        
        # Price impact (simplified calculation)
        if trade_data:
            large_trades = [t for t in trade_data if t.size >= self.config["large_trade_threshold"]]
            
            if large_trades and len(trade_data) > 1:
                price_impacts = []
                
                for i, trade in enumerate(large_trades):
                    # Find price before and after trade
                    before_trades = [t for t in trade_data if t.timestamp < trade.timestamp]
                    after_trades = [t for t in trade_data if t.timestamp > trade.timestamp]
                    
                    if before_trades and after_trades:
                        before_price = before_trades[-1].price
                        after_price = after_trades[0].price
                        
                        if trade.side == "buy":
                            impact = (after_price - before_price) / before_price
                        else:
                            impact = (before_price - after_price) / before_price
                        
                        price_impacts.append(abs(impact))
                
                if price_impacts:
                    metrics["price_impact"] = np.mean(price_impacts)
        
        return metrics
    
    def _calculate_depth_metrics(self, orderbook_data: List[OrderBookSnapshot]) -> Dict[str, float]:
        """Calculate market depth metrics."""
        metrics = {
            "bid_depth": 0.0,
            "ask_depth": 0.0,
            "total_depth": 0.0,
            "depth_imbalance": 0.0
        }
        
        if not orderbook_data:
            return metrics
        
        bid_depths = []
        ask_depths = []
        imbalances = []
        
        for snapshot in orderbook_data:
            # Calculate depth for configured levels
            bid_depth = sum(level.size for level in snapshot.bids[:self.config["depth_levels"]])
            ask_depth = sum(level.size for level in snapshot.asks[:self.config["depth_levels"]])
            
            bid_depths.append(bid_depth)
            ask_depths.append(ask_depth)
            
            # Depth imbalance
            total_depth = bid_depth + ask_depth
            if total_depth > 0:
                imbalance = (bid_depth - ask_depth) / total_depth
                imbalances.append(imbalance)
        
        if bid_depths:
            metrics["bid_depth"] = np.mean(bid_depths)
            metrics["ask_depth"] = np.mean(ask_depths)
            metrics["total_depth"] = np.mean([b + a for b, a in zip(bid_depths, ask_depths)])
        
        if imbalances:
            metrics["depth_imbalance"] = np.mean(imbalances)
        
        return metrics
    
    def _calculate_flow_metrics(self, trade_data: List[TradeData]) -> Dict[str, float]:
        """Calculate order flow metrics."""
        metrics = {
            "order_flow_imbalance": 0.0,
            "trade_size_ratio": 0.0,
            "institutional_flow_ratio": 0.0
        }
        
        if not trade_data:
            return metrics
        
        # Order flow imbalance
        buy_volume = sum(t.size for t in trade_data if t.side == "buy")
        sell_volume = sum(t.size for t in trade_data if t.side == "sell")
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            metrics["order_flow_imbalance"] = (buy_volume - sell_volume) / total_volume
        
        # Trade size analysis
        trade_sizes = [t.size for t in trade_data]
        if trade_sizes:
            avg_size = np.mean(trade_sizes)
            large_trades = [s for s in trade_sizes if s >= avg_size * self.config["institutional_size_ratio"]]
            
            if trade_sizes:
                metrics["trade_size_ratio"] = len(large_trades) / len(trade_sizes)
        
        # Institutional flow ratio
        institutional_volume = sum(t.size for t in trade_data if t.institutional)
        if total_volume > 0:
            metrics["institutional_flow_ratio"] = institutional_volume / total_volume
        
        return metrics
    
    def _calculate_quality_scores(self,
                                spread_metrics: Dict[str, float],
                                depth_metrics: Dict[str, float],
                                flow_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate market quality scores."""
        weights = self.config["quality_weights"]
        
        # Spread quality (lower spreads = higher quality)
        spread_score = 1.0 / (1.0 + spread_metrics["bid_ask_spread"] * 10000)  # Normalize for typical FX spreads
        
        # Depth quality (higher depth = higher quality)
        depth_score = min(1.0, depth_metrics["total_depth"] / 1000000)  # Normalize for typical depth
        
        # Impact quality (lower impact = higher quality)
        impact_score = 1.0 / (1.0 + spread_metrics["price_impact"] * 1000)
        
        # Flow quality (balanced flow = higher quality)
        flow_balance = 1.0 - abs(flow_metrics["order_flow_imbalance"])
        
        # Combined scores
        market_quality_score = (
            spread_score * weights["spread"] +
            depth_score * weights["depth"] +
            impact_score * weights["impact"] +
            flow_balance * weights["flow"]
        )
        
        liquidity_score = (spread_score + depth_score) / 2
        efficiency_score = (impact_score + flow_balance) / 2
        
        return {
            "market_quality_score": market_quality_score,
            "liquidity_score": liquidity_score,
            "efficiency_score": efficiency_score
        }
    
    def _detect_market_regime(self,
                            orderbook_data: List[OrderBookSnapshot],
                            trade_data: List[TradeData]) -> MarketRegime:
        """Detect current market microstructure regime."""
        if not orderbook_data and not trade_data:
            return MarketRegime.LIQUID
        
        # Calculate regime indicators
        regime_scores = {regime: 0.0 for regime in MarketRegime}
        
        # Spread-based indicators
        if orderbook_data:
            spreads = [ob.spread for ob in orderbook_data if ob.spread > 0]
            if spreads:
                avg_spread = np.mean(spreads)
                spread_volatility = np.std(spreads) / np.mean(spreads) if np.mean(spreads) > 0 else 0
                
                # Wide spreads suggest illiquidity
                if avg_spread > np.percentile(spreads, 80):
                    regime_scores[MarketRegime.ILLIQUID] += 0.3
                    regime_scores[MarketRegime.STRESSED] += 0.2
                
                # High spread volatility suggests stress
                if spread_volatility > 0.5:
                    regime_scores[MarketRegime.STRESSED] += 0.3
                    regime_scores[MarketRegime.VOLATILE] += 0.2
        
        # Volume-based indicators
        if trade_data:
            volumes = [t.size for t in trade_data]
            if volumes:
                volume_volatility = np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
                
                # High volume volatility suggests volatility regime
                if volume_volatility > 1.0:
                    regime_scores[MarketRegime.VOLATILE] += 0.3
                
                # Large trade concentration suggests institutional activity
                large_trades = len([v for v in volumes if v >= np.mean(volumes) * 3])
                if large_trades / len(volumes) > 0.1:
                    regime_scores[MarketRegime.TRENDING] += 0.2
        
        # Price movement indicators
        if trade_data and len(trade_data) > 10:
            prices = [t.price for t in trade_data]
            price_changes = np.diff(prices)
            
            # Directional movement suggests trending
            if len(price_changes) > 0:
                directional_ratio = abs(np.sum(np.sign(price_changes))) / len(price_changes)
                if directional_ratio > 0.6:
                    regime_scores[MarketRegime.TRENDING] += 0.4
                elif directional_ratio < 0.3:
                    regime_scores[MarketRegime.RANGING] += 0.4
        
        # Default to liquid if no strong signals
        if max(regime_scores.values()) < 0.3:
            regime_scores[MarketRegime.LIQUID] = 0.5
        
        return max(regime_scores, key=regime_scores.get)
    
    def _detect_institutional_flow(self, trade_data: List[TradeData]) -> InstitutionalFlow:
        """Detect institutional flow patterns."""
        if not trade_data:
            return InstitutionalFlow.NEUTRAL
        
        # Analyze trade patterns
        avg_size = np.mean([t.size for t in trade_data])
        large_trade_threshold = avg_size * self.config["institutional_size_ratio"]
        
        large_trades = [t for t in trade_data if t.size >= large_trade_threshold]
        
        if not large_trades:
            return InstitutionalFlow.NEUTRAL
        
        # Analyze large trade direction
        large_buy_volume = sum(t.size for t in large_trades if t.side == "buy")
        large_sell_volume = sum(t.size for t in large_trades if t.side == "sell")
        total_large_volume = large_buy_volume + large_sell_volume
        
        if total_large_volume == 0:
            return InstitutionalFlow.NEUTRAL
        
        flow_ratio = (large_buy_volume - large_sell_volume) / total_large_volume
        
        # Classify flow
        if flow_ratio > 0.3:
            return InstitutionalFlow.ACCUMULATION
        elif flow_ratio < -0.3:
            return InstitutionalFlow.DISTRIBUTION
        else:
            # Check for rotation patterns (alternating large trades)
            if len(large_trades) >= 4:
                sides = [t.side for t in large_trades[-4:]]
                if len(set(sides)) == 2 and sides != sorted(sides) and sides != sorted(sides, reverse=True):
                    return InstitutionalFlow.ROTATION
            
            return InstitutionalFlow.NEUTRAL
    
    def _update_history(self,
                       symbol: str,
                       metrics: MicrostructureMetrics,
                       orderbook_data: List[OrderBookSnapshot],
                       trade_data: List[TradeData]):
        """Update historical data."""
        if symbol not in self.metrics_history:
            self.metrics_history[symbol] = deque(maxlen=self.config["history_size"])
            self.orderbook_history[symbol] = deque(maxlen=self.config["history_size"])
            self.trade_history[symbol] = deque(maxlen=self.config["history_size"])
        
        self.metrics_history[symbol].append(metrics)
        
        # Store recent order book and trade data
        if orderbook_data:
            self.orderbook_history[symbol].extend(orderbook_data[-10:])  # Keep last 10 snapshots
        
        if trade_data:
            self.trade_history[symbol].extend(trade_data[-50:])  # Keep last 50 trades
    
    def get_microstructure_summary(self, symbol: str) -> Dict[str, Any]:
        """Get microstructure summary for a symbol."""
        if symbol not in self.metrics_history or not self.metrics_history[symbol]:
            return {"error": "No microstructure data available"}
        
        latest_metrics = self.metrics_history[symbol][-1]
        
        # Calculate historical averages
        recent_metrics = list(self.metrics_history[symbol])[-20:]  # Last 20 observations
        
        avg_spread = np.mean([m.bid_ask_spread for m in recent_metrics])
        avg_depth = np.mean([m.total_depth for m in recent_metrics])
        avg_quality = np.mean([m.market_quality_score for m in recent_metrics])
        
        return {
            "symbol": symbol,
            "timestamp": latest_metrics.timestamp,
            "current_metrics": {
                "bid_ask_spread": latest_metrics.bid_ask_spread,
                "effective_spread": latest_metrics.effective_spread,
                "price_impact": latest_metrics.price_impact,
                "total_depth": latest_metrics.total_depth,
                "depth_imbalance": latest_metrics.depth_imbalance,
                "order_flow_imbalance": latest_metrics.order_flow_imbalance,
                "market_quality_score": latest_metrics.market_quality_score,
                "liquidity_score": latest_metrics.liquidity_score,
                "efficiency_score": latest_metrics.efficiency_score
            },
            "regime": latest_metrics.regime.value,
            "institutional_flow": latest_metrics.institutional_flow.value,
            "historical_averages": {
                "avg_spread": avg_spread,
                "avg_depth": avg_depth,
                "avg_quality": avg_quality
            },
            "regime_stability": self._calculate_regime_stability(symbol),
            "flow_consistency": self._calculate_flow_consistency(symbol)
        }
    
    def _calculate_regime_stability(self, symbol: str) -> float:
        """Calculate regime stability score."""
        if symbol not in self.metrics_history or len(self.metrics_history[symbol]) < 10:
            return 0.0
        
        recent_regimes = [m.regime for m in list(self.metrics_history[symbol])[-10:]]
        most_common_regime = max(set(recent_regimes), key=recent_regimes.count)
        stability = recent_regimes.count(most_common_regime) / len(recent_regimes)
        
        return stability
    
    def _calculate_flow_consistency(self, symbol: str) -> float:
        """Calculate institutional flow consistency."""
        if symbol not in self.metrics_history or len(self.metrics_history[symbol]) < 10:
            return 0.0
        
        recent_flows = [m.institutional_flow for m in list(self.metrics_history[symbol])[-10:]]
        most_common_flow = max(set(recent_flows), key=recent_flows.count)
        consistency = recent_flows.count(most_common_flow) / len(recent_flows)
        
        return consistency
    
    def detect_microstructure_anomalies(self, symbol: str) -> List[Dict[str, Any]]:
        """Detect microstructure anomalies."""
        anomalies = []
        
        if symbol not in self.metrics_history or len(self.metrics_history[symbol]) < 20:
            return anomalies
        
        recent_metrics = list(self.metrics_history[symbol])[-20:]
        latest = recent_metrics[-1]
        
        # Calculate z-scores for key metrics
        spreads = [m.bid_ask_spread for m in recent_metrics[:-1]]
        depths = [m.total_depth for m in recent_metrics[:-1]]
        impacts = [m.price_impact for m in recent_metrics[:-1]]
        
        if spreads:
            spread_zscore = (latest.bid_ask_spread - np.mean(spreads)) / (np.std(spreads) + 1e-6)
            if abs(spread_zscore) > 2.0:
                anomalies.append({
                    "type": "spread_anomaly",
                    "severity": "high" if abs(spread_zscore) > 3.0 else "medium",
                    "description": f"Unusual spread: {spread_zscore:.2f} standard deviations from mean",
                    "current_value": latest.bid_ask_spread,
                    "normal_range": (np.mean(spreads) - 2*np.std(spreads), np.mean(spreads) + 2*np.std(spreads))
                })
        
        if depths:
            depth_zscore = (latest.total_depth - np.mean(depths)) / (np.std(depths) + 1e-6)
            if abs(depth_zscore) > 2.0:
                anomalies.append({
                    "type": "depth_anomaly",
                    "severity": "high" if abs(depth_zscore) > 3.0 else "medium",
                    "description": f"Unusual depth: {depth_zscore:.2f} standard deviations from mean",
                    "current_value": latest.total_depth,
                    "normal_range": (np.mean(depths) - 2*np.std(depths), np.mean(depths) + 2*np.std(depths))
                })
        
        if impacts:
            impact_zscore = (latest.price_impact - np.mean(impacts)) / (np.std(impacts) + 1e-6)
            if abs(impact_zscore) > 2.0:
                anomalies.append({
                    "type": "impact_anomaly",
                    "severity": "high" if abs(impact_zscore) > 3.0 else "medium",
                    "description": f"Unusual price impact: {impact_zscore:.2f} standard deviations from mean",
                    "current_value": latest.price_impact,
                    "normal_range": (np.mean(impacts) - 2*np.std(impacts), np.mean(impacts) + 2*np.std(impacts))
                })
        
        return anomalies
