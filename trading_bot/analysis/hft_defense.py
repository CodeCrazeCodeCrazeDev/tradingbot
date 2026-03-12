import logging
logger = logging.getLogger(__name__)
"""HFT Defense Module

This module implements defense mechanisms against high-frequency trading (HFT) predatory strategies
such as latency arbitrage, quote stuffing, momentum ignition, and layering/spoofing.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import time
from collections import deque
from loguru import logger

from trading_bot.analysis.market_microstructure import OrderBookSnapshot, TradeData, MarketRegime
from typing import Set
import numpy
import pandas


class HFTStrategy(Enum):
    """Types of predatory HFT strategies."""
    LATENCY_ARBITRAGE = auto()
    QUOTE_STUFFING = auto()
    MOMENTUM_IGNITION = auto()
    LAYERING = auto()
    SPOOFING = auto()
    PINGING = auto()
    FRONT_RUNNING = auto()
    WASH_TRADING = auto()


@dataclass
class HFTDetection:
    """Detection of HFT activity."""
    timestamp: datetime
    strategy: HFTStrategy
    confidence: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0
    details: Dict[str, Any]


@dataclass
class DefenseRecommendation:
    """Recommendation for defending against HFT."""
    strategy: HFTStrategy
    action: str
    priority: int  # 1 (highest) to 5 (lowest)
    description: str
    params: Dict[str, Any] = field(default_factory=dict)


class HFTDefenseSystem:
    """System for detecting and defending against predatory HFT strategies."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the HFT defense system.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Detection history
            self.detection_history: Dict[str, List[HFTDetection]] = {}
        
            # Order book history for analysis
            self.orderbook_history: Dict[str, deque] = {}
            self.trade_history: Dict[str, deque] = {}
        
            # Detection counters
            self.detection_counters: Dict[str, Dict[HFTStrategy, int]] = {}
        
            logger.info("HFTDefenseSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration."""
        try:
            defaults = {
                "history_size": 1000,
                "detection_window": 60,  # seconds
                "quote_stuff_threshold": 20,  # messages per second
                "layering_levels": 3,  # minimum levels for layering detection
                "momentum_threshold": 0.5,  # percent price move
                "latency_threshold": 0.05,  # seconds
                "confidence_thresholds": {
                    "low": 0.3,
                    "medium": 0.6,
                    "high": 0.8
                }
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def analyze_for_hft(self, 
                      symbol: str,
                      orderbook_data: List[OrderBookSnapshot],
                      trade_data: List[TradeData],
                      market_regime: MarketRegime) -> List[HFTDetection]:
        """Analyze market data for HFT activity.
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book snapshots
            trade_data: Trade data
            market_regime: Current market regime
            
        Returns:
            List of HFT detections
        """
        # Update history
        try:
            self._update_history(symbol, orderbook_data, trade_data)
        
            # Run detection algorithms
            detections = []
        
            # Detect quote stuffing
            quote_stuffing = self._detect_quote_stuffing(symbol, orderbook_data)
            if quote_stuffing:
                detections.append(quote_stuffing)
        
            # Detect layering/spoofing
            layering = self._detect_layering(symbol, orderbook_data)
            if layering:
                detections.append(layering)
        
            # Detect momentum ignition
            momentum_ignition = self._detect_momentum_ignition(symbol, trade_data, market_regime)
            if momentum_ignition:
                detections.append(momentum_ignition)
        
            # Detect latency arbitrage
            latency_arbitrage = self._detect_latency_arbitrage(symbol, orderbook_data, trade_data)
            if latency_arbitrage:
                detections.append(latency_arbitrage)
        
            # Detect pinging
            pinging = self._detect_pinging(symbol, orderbook_data, trade_data)
            if pinging:
                detections.append(pinging)
        
            # Update detection history
            if symbol not in self.detection_history:
                self.detection_history[symbol] = []
        
            self.detection_history[symbol].extend(detections)
        
            # Update detection counters
            if symbol not in self.detection_counters:
                self.detection_counters[symbol] = {strategy: 0 for strategy in HFTStrategy}
        
            for detection in detections:
                self.detection_counters[symbol][detection.strategy] += 1
        
            return detections
        except Exception as e:
            logger.error(f"Error in analyze_for_hft: {e}")
            raise
    
    def get_defense_recommendations(self, 
                                  symbol: str,
                                  detections: List[HFTDetection]) -> List[DefenseRecommendation]:
        """Get recommendations for defending against detected HFT strategies.
        
        Args:
            symbol: Trading symbol
            detections: List of HFT detections
            
        Returns:
            List of defense recommendations
        """
        try:
            recommendations = []
        
            for detection in detections:
                if detection.strategy == HFTStrategy.QUOTE_STUFFING:
                    recommendations.append(self._recommend_quote_stuffing_defense(detection))
                elif detection.strategy == HFTStrategy.LAYERING:
                    recommendations.append(self._recommend_layering_defense(detection))
                elif detection.strategy == HFTStrategy.MOMENTUM_IGNITION:
                    recommendations.append(self._recommend_momentum_ignition_defense(detection))
                elif detection.strategy == HFTStrategy.LATENCY_ARBITRAGE:
                    recommendations.append(self._recommend_latency_arbitrage_defense(detection))
                elif detection.strategy == HFTStrategy.PINGING:
                    recommendations.append(self._recommend_pinging_defense(detection))
        
            # Sort by priority
            recommendations.sort(key=lambda r: r.priority)
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in get_defense_recommendations: {e}")
            raise
    
    def _update_history(self, 
                      symbol: str,
                      orderbook_data: List[OrderBookSnapshot],
                      trade_data: List[TradeData]):
        """Update historical data."""
        try:
            if symbol not in self.orderbook_history:
                self.orderbook_history[symbol] = deque(maxlen=self.config["history_size"])
                self.trade_history[symbol] = deque(maxlen=self.config["history_size"])
        
            # Store recent order book and trade data
            if orderbook_data:
                self.orderbook_history[symbol].extend(orderbook_data)
        
            if trade_data:
                self.trade_history[symbol].extend(trade_data)
        except Exception as e:
            logger.error(f"Error in _update_history: {e}")
            raise
    
    def _detect_quote_stuffing(self, 
                             symbol: str,
                             orderbook_data: List[OrderBookSnapshot]) -> Optional[HFTDetection]:
        """Detect quote stuffing (rapid order submissions and cancellations).
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book snapshots
            
        Returns:
            HFT detection if quote stuffing is detected, None otherwise
        """
        try:
            if not orderbook_data or len(orderbook_data) < 10:
                return None
        
            # Calculate message rate
            time_span = (orderbook_data[-1].timestamp - orderbook_data[0].timestamp).total_seconds()
            if time_span <= 0:
                return None
        
            message_rate = len(orderbook_data) / time_span
        
            if message_rate > self.config["quote_stuff_threshold"]:
                # Check for rapid changes in order book
                bid_changes = 0
                ask_changes = 0
            
                for i in range(1, len(orderbook_data)):
                    prev_ob = orderbook_data[i-1]
                    curr_ob = orderbook_data[i]
                
                    # Count changes in top levels
                    if prev_ob.bids and curr_ob.bids:
                        if prev_ob.bids[0].price != curr_ob.bids[0].price or prev_ob.bids[0].size != curr_ob.bids[0].size:
                            bid_changes += 1
                
                    if prev_ob.asks and curr_ob.asks:
                        if prev_ob.asks[0].price != curr_ob.asks[0].price or prev_ob.asks[0].size != curr_ob.asks[0].size:
                            ask_changes += 1
            
                change_rate = (bid_changes + ask_changes) / time_span
            
                if change_rate > self.config["quote_stuff_threshold"] * 0.5:
                    confidence = min(1.0, change_rate / (self.config["quote_stuff_threshold"] * 2))
                    impact_score = min(1.0, message_rate / (self.config["quote_stuff_threshold"] * 2))
                
                    return HFTDetection(
                        timestamp=datetime.now(),
                        strategy=HFTStrategy.QUOTE_STUFFING,
                        confidence=confidence,
                        impact_score=impact_score,
                        details={
                            "message_rate": message_rate,
                            "change_rate": change_rate,
                            "time_span": time_span,
                            "bid_changes": bid_changes,
                            "ask_changes": ask_changes
                        }
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_quote_stuffing: {e}")
            raise
    
    def _detect_layering(self, 
                       symbol: str,
                       orderbook_data: List[OrderBookSnapshot]) -> Optional[HFTDetection]:
        """Detect layering/spoofing (placing multiple orders to create false impression).
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book snapshots
            
        Returns:
            HFT detection if layering is detected, None otherwise
        """
        try:
            if not orderbook_data:
                return None
        
            latest_ob = orderbook_data[-1]
        
            # Check for layering patterns (multiple orders at different price levels)
            if len(latest_ob.bids) >= self.config["layering_levels"] and len(latest_ob.asks) >= self.config["layering_levels"]:
                # Check for imbalance in order book
                bid_sizes = [level.size for level in latest_ob.bids[:self.config["layering_levels"]]]
                ask_sizes = [level.size for level in latest_ob.asks[:self.config["layering_levels"]]]
            
                total_bid_size = sum(bid_sizes)
                total_ask_size = sum(ask_sizes)
            
                # Check for significant imbalance
                if total_bid_size > 0 and total_ask_size > 0:
                    imbalance_ratio = max(total_bid_size / total_ask_size, total_ask_size / total_bid_size)
                
                    if imbalance_ratio > 3.0:  # Significant imbalance
                        # Check for pattern of similar sized orders
                        if len(orderbook_data) > 10:
                            # Look for pattern of orders appearing and disappearing
                            pattern_detected = False
                        
                            # Check for pattern in historical data
                            if symbol in self.orderbook_history and len(self.orderbook_history[symbol]) > 20:
                                historical_obs = list(self.orderbook_history[symbol])[-20:]
                            
                                # Count appearance/disappearance of orders
                                side = "bids" if total_bid_size > total_ask_size else "asks"
                                level_changes = 0
                            
                                for i in range(1, len(historical_obs)):
                                    prev_ob = historical_obs[i-1]
                                    curr_ob = historical_obs[i]
                                
                                    prev_levels = getattr(prev_ob, side)
                                    curr_levels = getattr(curr_ob, side)
                                
                                    # Check for significant changes in levels
                                    if len(prev_levels) > 0 and len(curr_levels) > 0:
                                        for j in range(min(len(prev_levels), len(curr_levels), 5)):
                                            if abs(prev_levels[j].size - curr_levels[j].size) > 0.2 * prev_levels[j].size:
                                                level_changes += 1
                            
                                pattern_detected = level_changes > 10
                        
                            if pattern_detected:
                                confidence = min(1.0, imbalance_ratio / 10.0)
                                impact_score = min(1.0, (imbalance_ratio - 2.0) / 8.0)
                            
                                return HFTDetection(
                                    timestamp=datetime.now(),
                                    strategy=HFTStrategy.LAYERING,
                                    confidence=confidence,
                                    impact_score=impact_score,
                                    details={
                                        "imbalance_ratio": imbalance_ratio,
                                        "total_bid_size": total_bid_size,
                                        "total_ask_size": total_ask_size,
                                        "dominant_side": "bid" if total_bid_size > total_ask_size else "ask"
                                    }
                                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_layering: {e}")
            raise
    
    def _detect_momentum_ignition(self, 
                                symbol: str,
                                trade_data: List[TradeData],
                                market_regime: MarketRegime) -> Optional[HFTDetection]:
        """Detect momentum ignition (initiating rapid price movement).
        
        Args:
            symbol: Trading symbol
            trade_data: Trade data
            market_regime: Current market regime
            
        Returns:
            HFT detection if momentum ignition is detected, None otherwise
        """
        try:
            if not trade_data or len(trade_data) < 10:
                return None
        
            # Check for rapid price movement
            prices = [t.price for t in trade_data]
            price_change = (prices[-1] - prices[0]) / prices[0] * 100  # percent
        
            time_span = (trade_data[-1].timestamp - trade_data[0].timestamp).total_seconds()
            if time_span <= 0:
                return None
        
            # Calculate rate of change
            rate_of_change = abs(price_change) / time_span
        
            # Higher threshold for volatile regimes
            threshold_multiplier = 1.0
            if market_regime == MarketRegime.VOLATILE:
                threshold_multiplier = 2.0
        
            if rate_of_change > self.config["momentum_threshold"] * threshold_multiplier:
                # Check for large trades initiating the move
                initial_trades = trade_data[:3]  # First few trades
                avg_size = np.mean([t.size for t in trade_data])
            
                large_initiating_trades = [t for t in initial_trades if t.size > 2 * avg_size]
            
                if large_initiating_trades:
                    # Check if trades are in the direction of the move
                    direction = 1 if price_change > 0 else -1
                    aligned_trades = [t for t in large_initiating_trades 
                                    if (t.side == "buy" and direction > 0) or (t.side == "sell" and direction < 0)]
                
                    if aligned_trades:
                        confidence = min(1.0, rate_of_change / (self.config["momentum_threshold"] * 2))
                        impact_score = min(1.0, abs(price_change) / (self.config["momentum_threshold"] * 5))
                    
                        return HFTDetection(
                            timestamp=datetime.now(),
                            strategy=HFTStrategy.MOMENTUM_IGNITION,
                            confidence=confidence,
                            impact_score=impact_score,
                            details={
                                "price_change": price_change,
                                "rate_of_change": rate_of_change,
                                "time_span": time_span,
                                "direction": "up" if price_change > 0 else "down",
                                "large_trades": len(large_initiating_trades)
                            }
                        )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_momentum_ignition: {e}")
            raise
    
    def _detect_latency_arbitrage(self, 
                                symbol: str,
                                orderbook_data: List[OrderBookSnapshot],
                                trade_data: List[TradeData]) -> Optional[HFTDetection]:
        """Detect latency arbitrage (exploiting speed advantages).
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book snapshots
            trade_data: Trade data
            
        Returns:
            HFT detection if latency arbitrage is detected, None otherwise
        """
        try:
            if not orderbook_data or not trade_data or len(orderbook_data) < 5 or len(trade_data) < 5:
                return None
        
            # Look for trades that happen immediately after order book updates
            latency_events = 0
        
            for trade in trade_data:
                # Find closest order book update before trade
                ob_before = None
                for ob in orderbook_data:
                    if ob.timestamp < trade.timestamp:
                        ob_before = ob
                    else:
                        break
            
                if ob_before:
                    # Calculate time difference
                    time_diff = (trade.timestamp - ob_before.timestamp).total_seconds()
                
                    # Check if trade happened very quickly after order book update
                    if time_diff < self.config["latency_threshold"]:
                        latency_events += 1
        
            if latency_events >= 3:  # Multiple instances detected
                confidence = min(1.0, latency_events / 10.0)
                impact_score = min(1.0, latency_events / 20.0)
            
                return HFTDetection(
                    timestamp=datetime.now(),
                    strategy=HFTStrategy.LATENCY_ARBITRAGE,
                    confidence=confidence,
                    impact_score=impact_score,
                    details={
                        "latency_events": latency_events,
                        "threshold": self.config["latency_threshold"]
                    }
                )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_latency_arbitrage: {e}")
            raise
    
    def _detect_pinging(self, 
                      symbol: str,
                      orderbook_data: List[OrderBookSnapshot],
                      trade_data: List[TradeData]) -> Optional[HFTDetection]:
        """Detect pinging (small orders to detect hidden liquidity).
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book snapshots
            trade_data: Trade data
            
        Returns:
            HFT detection if pinging is detected, None otherwise
        """
        try:
            if not trade_data or len(trade_data) < 10:
                return None
        
            # Look for pattern of small trades
            trade_sizes = [t.size for t in trade_data]
            avg_size = np.mean(trade_sizes)
        
            small_trades = [t for t in trade_data if t.size < 0.2 * avg_size]
        
            if len(small_trades) >= 5 and len(small_trades) / len(trade_data) > 0.3:
                # Check for pattern of small trades followed by larger trades
                small_trade_timestamps = [t.timestamp for t in small_trades]
            
                # Look for larger trades following small trades
                pattern_count = 0
            
                for small_ts in small_trade_timestamps:
                    # Find trades that happened shortly after this small trade
                    following_trades = [t for t in trade_data 
                                       if t.timestamp > small_ts 
                                       and (t.timestamp - small_ts).total_seconds() < 1.0
                                       and t.size > avg_size]
                
                    if following_trades:
                        pattern_count += 1
            
                if pattern_count >= 3:
                    confidence = min(1.0, pattern_count / 10.0)
                    impact_score = min(1.0, len(small_trades) / len(trade_data))
                
                    return HFTDetection(
                        timestamp=datetime.now(),
                        strategy=HFTStrategy.PINGING,
                        confidence=confidence,
                        impact_score=impact_score,
                        details={
                            "small_trades": len(small_trades),
                            "total_trades": len(trade_data),
                            "small_trade_ratio": len(small_trades) / len(trade_data),
                            "pattern_count": pattern_count
                        }
                    )
        
            return None
        except Exception as e:
            logger.error(f"Error in _detect_pinging: {e}")
            raise
    
    def _recommend_quote_stuffing_defense(self, detection: HFTDetection) -> DefenseRecommendation:
        """Recommend defense against quote stuffing."""
        try:
            priority = 2 if detection.confidence > 0.7 else 3
        
            return DefenseRecommendation(
                strategy=HFTStrategy.QUOTE_STUFFING,
                action="throttle_orders",
                priority=priority,
                description="Throttle order submission rate to avoid processing excessive messages",
                params={
                    "max_orders_per_second": 5,
                    "cooldown_period": 30  # seconds
                }
            )
        except Exception as e:
            logger.error(f"Error in _recommend_quote_stuffing_defense: {e}")
            raise
    
    def _recommend_layering_defense(self, detection: HFTDetection) -> DefenseRecommendation:
        """Recommend defense against layering."""
        try:
            priority = 1 if detection.confidence > 0.8 else 2
        
            return DefenseRecommendation(
                strategy=HFTStrategy.LAYERING,
                action="ignore_false_liquidity",
                priority=priority,
                description="Ignore suspicious liquidity levels that may disappear",
                params={
                    "side": detection.details.get("dominant_side", "both"),
                    "levels_to_ignore": 3,
                    "duration": 60  # seconds
                }
            )
        except Exception as e:
            logger.error(f"Error in _recommend_layering_defense: {e}")
            raise
    
    def _recommend_momentum_ignition_defense(self, detection: HFTDetection) -> DefenseRecommendation:
        """Recommend defense against momentum ignition."""
        try:
            priority = 1 if detection.impact_score > 0.7 else 2
        
            return DefenseRecommendation(
                strategy=HFTStrategy.MOMENTUM_IGNITION,
                action="pause_trading",
                priority=priority,
                description="Temporarily pause trading during suspicious price movements",
                params={
                    "pause_duration": 30,  # seconds
                    "direction": detection.details.get("direction", "both")
                }
            )
        except Exception as e:
            logger.error(f"Error in _recommend_momentum_ignition_defense: {e}")
            raise
    
    def _recommend_latency_arbitrage_defense(self, detection: HFTDetection) -> DefenseRecommendation:
        """Recommend defense against latency arbitrage."""
        try:
            priority = 2
        
            return DefenseRecommendation(
                strategy=HFTStrategy.LATENCY_ARBITRAGE,
                action="randomize_timing",
                priority=priority,
                description="Randomize order submission timing to avoid predictable patterns",
                params={
                    "max_delay": 0.5,  # seconds
                    "min_delay": 0.1  # seconds
                }
            )
        except Exception as e:
            logger.error(f"Error in _recommend_latency_arbitrage_defense: {e}")
            raise
    
    def _recommend_pinging_defense(self, detection: HFTDetection) -> DefenseRecommendation:
        """Recommend defense against pinging."""
        try:
            priority = 3
        
            return DefenseRecommendation(
                strategy=HFTStrategy.PINGING,
                action="minimum_order_size",
                priority=priority,
                description="Set minimum order size to avoid revealing strategy with small orders",
                params={
                    "min_order_size": detection.details.get("small_trades", 1) * 2
                }
            )
        except Exception as e:
            logger.error(f"Error in _recommend_pinging_defense: {e}")
            raise
    
    def get_hft_activity_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of HFT activity for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with HFT activity summary
        """
        try:
            if symbol not in self.detection_history or not self.detection_history[symbol]:
                return {
                    "symbol": symbol,
                    "hft_activity_detected": False,
                    "message": "No HFT activity detected"
                }
        
            # Get recent detections
            recent_detections = [d for d in self.detection_history[symbol] 
                               if (datetime.now() - d.timestamp).total_seconds() < 3600]  # Last hour
        
            if not recent_detections:
                return {
                    "symbol": symbol,
                    "hft_activity_detected": False,
                    "message": "No recent HFT activity detected"
                }
        
            # Count detections by strategy
            strategy_counts = {}
            for detection in recent_detections:
                strategy_name = detection.strategy.name
                if strategy_name not in strategy_counts:
                    strategy_counts[strategy_name] = 0
                strategy_counts[strategy_name] += 1
        
            # Calculate average confidence and impact
            avg_confidence = np.mean([d.confidence for d in recent_detections])
            avg_impact = np.mean([d.impact_score for d in recent_detections])
        
            # Get most recent detection
            most_recent = max(recent_detections, key=lambda d: d.timestamp)
        
            # Get most common strategy
            most_common_strategy = max(strategy_counts.items(), key=lambda x: x[1])[0]
        
            return {
                "symbol": symbol,
                "hft_activity_detected": True,
                "detection_count": len(recent_detections),
                "most_common_strategy": most_common_strategy,
                "strategy_counts": strategy_counts,
                "avg_confidence": avg_confidence,
                "avg_impact": avg_impact,
                "most_recent_detection": {
                    "strategy": most_recent.strategy.name,
                    "timestamp": most_recent.timestamp.isoformat(),
                    "confidence": most_recent.confidence,
                    "impact_score": most_recent.impact_score
                }
            }
        except Exception as e:
            logger.error(f"Error in get_hft_activity_summary: {e}")
            raise
    
    def get_defense_strategy(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive defense strategy against detected HFT activity.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with defense strategy
        """
        try:
            if symbol not in self.detection_history or not self.detection_history[symbol]:
                return {
                    "symbol": symbol,
                    "defense_needed": False,
                    "message": "No HFT activity detected, standard trading approach recommended"
                }
        
            # Get recent detections
            recent_detections = [d for d in self.detection_history[symbol] 
                               if (datetime.now() - d.timestamp).total_seconds() < 3600]  # Last hour
        
            if not recent_detections:
                return {
                    "symbol": symbol,
                    "defense_needed": False,
                    "message": "No recent HFT activity detected, standard trading approach recommended"
                }
        
            # Get recommendations for all detections
            all_recommendations = []
            for detection in recent_detections:
                if detection.strategy == HFTStrategy.QUOTE_STUFFING:
                    all_recommendations.append(self._recommend_quote_stuffing_defense(detection))
                elif detection.strategy == HFTStrategy.LAYERING:
                    all_recommendations.append(self._recommend_layering_defense(detection))
                elif detection.strategy == HFTStrategy.MOMENTUM_IGNITION:
                    all_recommendations.append(self._recommend_momentum_ignition_defense(detection))
                elif detection.strategy == HFTStrategy.LATENCY_ARBITRAGE:
                    all_recommendations.append(self._recommend_latency_arbitrage_defense(detection))
                elif detection.strategy == HFTStrategy.PINGING:
                    all_recommendations.append(self._recommend_pinging_defense(detection))
        
            # Group by action
            action_groups = {}
            for rec in all_recommendations:
                if rec.action not in action_groups:
                    action_groups[rec.action] = []
                action_groups[rec.action].append(rec)
        
            # Get highest priority recommendation for each action
            prioritized_recommendations = []
            for action, recs in action_groups.items():
                highest_priority = min(recs, key=lambda r: r.priority)
                prioritized_recommendations.append(highest_priority)
        
            # Sort by priority
            prioritized_recommendations.sort(key=lambda r: r.priority)
        
            return {
                "symbol": symbol,
                "defense_needed": True,
                "threat_level": "high" if any(d.impact_score > 0.7 for d in recent_detections) else "medium",
                "recommendations": [
                    {
                        "action": r.action,
                        "priority": r.priority,
                        "description": r.description,
                        "params": r.params,
                        "strategy": r.strategy.name
                    }
                    for r in prioritized_recommendations
                ],
                "general_advice": "Consider using larger order sizes, randomized timing, and avoiding predictable patterns"
            }
        except Exception as e:
            logger.error(f"Error in get_defense_strategy: {e}")
            raise
