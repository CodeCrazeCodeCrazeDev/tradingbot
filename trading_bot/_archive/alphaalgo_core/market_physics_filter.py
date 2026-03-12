"""
AlphaAlgo Core - Market Physics Filter (Layer 0)

Before any strategy or signal is evaluated, determines whether the market is structurally tradable.

Evaluates:
- Liquidity depth consistency
- Volatility expansion/compression state
- Order-flow entropy stability
- Time-of-day structural reliability
- Spread integrity vs historical baseline

If market structure is degraded or undefined:
- Mute all strategies
- Set exposure = 0
- Log reason
- Do not override
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .capital_governance import (
    GovernanceLayer,
    MarketPhysicsResult,
    MarketStructureState,
    MarketPhysicsError
)

logger = logging.getLogger(__name__)


class MarketPhysicsFilter(GovernanceLayer):
    """
    Layer 0 - Market Physics Filter
    
    Determines if a market is structurally tradable based on fundamental market physics.
    This layer operates before any AI or strategy evaluation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("market_physics_filter")
        self.config = config or {}
        
        # Default thresholds
        self.thresholds = {
            "liquidity_depth_min": self.config.get("liquidity_depth_min", 0.7),  # Minimum acceptable liquidity depth ratio
            "volatility_max": self.config.get("volatility_max", 3.0),  # Maximum acceptable volatility ratio
            "entropy_min": self.config.get("entropy_min", 0.6),  # Minimum acceptable entropy ratio
            "spread_max": self.config.get("spread_max", 2.0),  # Maximum acceptable spread ratio
            "time_reliability_min": self.config.get("time_reliability_min", 0.5),  # Minimum time-of-day reliability
        }
        
        # Historical baselines cache
        self.baselines = {}
        
        logger.info(f"Market Physics Filter initialized with thresholds: {self.thresholds}")
    
    async def process(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> MarketPhysicsResult:
        """
        Process market data to determine if the market is structurally tradable.
        
        Args:
            symbol: The market symbol
            market_data: Dictionary containing market data including:
                - ohlcv: OHLCV data
                - orderbook: Order book data
                - trades: Recent trades
                - liquidity: Liquidity metrics
                - volatility: Volatility metrics
                - microstructure: Market microstructure data
        
        Returns:
            MarketPhysicsResult with tradability determination
        """
        try:
            # Extract required data
            ohlcv = market_data.get("ohlcv")
            orderbook = market_data.get("orderbook")
            trades = market_data.get("trades")
            liquidity = market_data.get("liquidity")
            volatility = market_data.get("volatility")
            microstructure = market_data.get("microstructure")
            
            # Check if we have the minimum required data
            if not all([ohlcv is not None, orderbook is not None]):
                return MarketPhysicsResult(
                    state=MarketStructureState.UNDEFINED,
                    is_tradable=False,
                    reason="Insufficient market data for physics evaluation"
                )
            
            # 1. Evaluate liquidity depth consistency
            liquidity_score = await self._evaluate_liquidity_depth(symbol, orderbook, liquidity)
            
            # 2. Evaluate volatility state
            volatility_score = await self._evaluate_volatility_state(symbol, ohlcv, volatility)
            
            # 3. Evaluate order-flow entropy
            entropy_score = await self._evaluate_orderflow_entropy(symbol, trades, microstructure)
            
            # 4. Evaluate time-of-day reliability
            time_reliability = await self._evaluate_time_reliability(symbol, ohlcv)
            
            # 5. Evaluate spread integrity
            spread_score = await self._evaluate_spread_integrity(symbol, orderbook)
            
            # Compile metrics
            metrics = {
                "liquidity_depth_score": liquidity_score,
                "volatility_score": volatility_score,
                "entropy_score": entropy_score,
                "time_reliability": time_reliability,
                "spread_score": spread_score
            }
            
            # Determine overall market state
            is_tradable, state, reason = self._determine_market_state(metrics)
            
            # Create result
            result = MarketPhysicsResult(
                state=state,
                is_tradable=is_tradable,
                reason=reason,
                metrics=metrics
            )
            
            # Log decision
            level = "info" if is_tradable else "warning"
            self.log_decision(is_tradable, reason, level)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in market physics filter: {e}")
            return MarketPhysicsResult(
                state=MarketStructureState.UNDEFINED,
                is_tradable=False,
                reason=f"Error in market physics evaluation: {str(e)}"
            )
    
    async def _evaluate_liquidity_depth(
        self,
        symbol: str,
        orderbook: Dict[str, Any],
        liquidity: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Evaluate liquidity depth consistency.
        
        Returns a score between 0 and 1, where 1 is excellent liquidity.
        """
        try:
            # Get baseline if available
            baseline = self.baselines.get(f"{symbol}_liquidity", None)
            
            # Extract bid/ask volumes at different price levels
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            
            if not bids or not asks:
                return 0.0
            
            # Calculate total volume within 5 levels
            bid_volume = sum(bid[1] for bid in bids[:5]) if len(bids) >= 5 else 0
            ask_volume = sum(ask[1] for ask in asks[:5]) if len(asks) >= 5 else 0
            
            # If we have liquidity metrics, use them
            if liquidity and "depth" in liquidity:
                current_depth = liquidity["depth"]
            else:
                # Simple depth calculation
                current_depth = (bid_volume + ask_volume) / 2
            
            # If no baseline, use current as baseline
            if baseline is None:
                self.baselines[f"{symbol}_liquidity"] = current_depth
                return 0.8  # Default to slightly below excellent for first measurement
            
            # Calculate ratio to baseline
            depth_ratio = current_depth / baseline
            
            # Normalize to 0-1 score
            if depth_ratio >= 1.0:
                return 1.0
            elif depth_ratio <= 0.2:
                return 0.0
            else:
                return depth_ratio
                
        except Exception as e:
            logger.warning(f"Error evaluating liquidity depth: {e}")
            return 0.5  # Default to neutral on error
    
    async def _evaluate_volatility_state(
        self,
        symbol: str,
        ohlcv: Dict[str, Any],
        volatility: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Evaluate volatility expansion/compression state.
        
        Returns a score between 0 and 1, where 1 is normal volatility.
        """
        try:
            # Get baseline if available
            baseline = self.baselines.get(f"{symbol}_volatility", None)
            
            # If we have volatility metrics, use them
            if volatility and "current" in volatility:
                current_volatility = volatility["current"]
            else:
                # Calculate simple volatility from OHLCV
                closes = ohlcv.get("close", [])
                if len(closes) < 20:
                    return 0.5  # Not enough data
                
                # Calculate rolling standard deviation
                returns = np.diff(closes) / closes[:-1]
                current_volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # If no baseline, use current as baseline
            if baseline is None:
                self.baselines[f"{symbol}_volatility"] = current_volatility
                return 0.8  # Default to slightly below excellent for first measurement
            
            # Calculate ratio to baseline
            volatility_ratio = current_volatility / baseline
            
            # Normalize to 0-1 score (inverse - higher volatility = lower score)
            if volatility_ratio <= 1.0:
                return 1.0
            elif volatility_ratio >= 3.0:
                return 0.0
            else:
                return max(0, 1.0 - (volatility_ratio - 1.0) / 2.0)
                
        except Exception as e:
            logger.warning(f"Error evaluating volatility state: {e}")
            return 0.5  # Default to neutral on error
    
    async def _evaluate_orderflow_entropy(
        self,
        symbol: str,
        trades: Optional[List[Dict[str, Any]]],
        microstructure: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Evaluate order-flow entropy stability.
        
        Returns a score between 0 and 1, where 1 is stable, high-entropy order flow.
        """
        try:
            # Get baseline if available
            baseline = self.baselines.get(f"{symbol}_entropy", None)
            
            # If we have microstructure data with entropy, use it
            if microstructure and "order_flow_entropy" in microstructure:
                current_entropy = microstructure["order_flow_entropy"]
            elif trades and len(trades) >= 50:
                # Calculate simple entropy from trade sizes
                trade_sizes = [trade.get("size", 0) for trade in trades]
                
                # Bin the trade sizes
                hist, _ = np.histogram(trade_sizes, bins=10)
                
                # Calculate probability distribution
                probs = hist / len(trade_sizes)
                
                # Remove zeros
                probs = probs[probs > 0]
                
                # Calculate entropy
                entropy = -np.sum(probs * np.log2(probs))
                
                # Normalize by maximum possible entropy (log2(n))
                max_entropy = np.log2(len(probs)) if len(probs) > 0 else 1
                current_entropy = entropy / max_entropy if max_entropy > 0 else 0
            else:
                return 0.5  # Not enough data
            
            # If no baseline, use current as baseline
            if baseline is None:
                self.baselines[f"{symbol}_entropy"] = current_entropy
                return 0.8  # Default to slightly below excellent for first measurement
            
            # Calculate ratio to baseline
            entropy_ratio = current_entropy / baseline
            
            # Normalize to 0-1 score
            if entropy_ratio >= 1.0:
                return 1.0
            elif entropy_ratio <= 0.3:
                return 0.0
            else:
                return entropy_ratio
                
        except Exception as e:
            logger.warning(f"Error evaluating orderflow entropy: {e}")
            return 0.5  # Default to neutral on error
    
    async def _evaluate_time_reliability(
        self,
        symbol: str,
        ohlcv: Dict[str, Any]
    ) -> float:
        """
        Evaluate time-of-day structural reliability.
        
        Returns a score between 0 and 1, where 1 is highly reliable for current time.
        """
        try:
            # Get current hour
            current_hour = datetime.now().hour
            
            # Check if we have historical reliability data for this hour
            hour_key = f"{symbol}_hour_{current_hour}"
            if hour_key in self.baselines:
                return self.baselines[hour_key]
            
            # If we don't have historical data, use a time-of-day heuristic
            # This is a simplified approach - in production, this would use historical data
            
            # For forex: most liquid during London/NY overlap (13-16 UTC)
            if "USD" in symbol or "EUR" in symbol or "GBP" in symbol:
                if 13 <= current_hour <= 16:
                    reliability = 0.9  # London/NY overlap
                elif 8 <= current_hour <= 16:
                    reliability = 0.8  # European or US hours
                elif 0 <= current_hour <= 7:
                    reliability = 0.7  # Asian hours
                else:
                    reliability = 0.6  # Other hours
            # For crypto: generally 24/7 but can vary
            elif "BTC" in symbol or "ETH" in symbol:
                reliability = 0.8  # Generally reliable
            # For stocks: most liquid during market hours
            elif "US" in symbol:
                if 14 <= current_hour <= 21:  # 9:30 AM - 4:00 PM ET in UTC
                    reliability = 0.9
                else:
                    reliability = 0.3  # Outside market hours
            else:
                reliability = 0.7  # Default
            
            # Store for future use
            self.baselines[hour_key] = reliability
            
            return reliability
                
        except Exception as e:
            logger.warning(f"Error evaluating time reliability: {e}")
            return 0.5  # Default to neutral on error
    
    async def _evaluate_spread_integrity(
        self,
        symbol: str,
        orderbook: Dict[str, Any]
    ) -> float:
        """
        Evaluate spread integrity vs historical baseline.
        
        Returns a score between 0 and 1, where 1 is excellent spread integrity.
        """
        try:
            # Get baseline if available
            baseline = self.baselines.get(f"{symbol}_spread", None)
            
            # Extract best bid/ask
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            
            if not bids or not asks:
                return 0.0
            
            best_bid = bids[0][0]
            best_ask = asks[0][0]
            
            # Calculate current spread
            current_spread = (best_ask - best_bid) / ((best_ask + best_bid) / 2) * 10000  # In basis points
            
            # If no baseline, use current as baseline
            if baseline is None:
                self.baselines[f"{symbol}_spread"] = current_spread
                return 0.8  # Default to slightly below excellent for first measurement
            
            # Calculate ratio to baseline
            spread_ratio = current_spread / baseline
            
            # Normalize to 0-1 score (inverse - wider spread = lower score)
            if spread_ratio <= 1.0:
                return 1.0
            elif spread_ratio >= 3.0:
                return 0.0
            else:
                return max(0, 1.0 - (spread_ratio - 1.0) / 2.0)
                
        except Exception as e:
            logger.warning(f"Error evaluating spread integrity: {e}")
            return 0.5  # Default to neutral on error
    
    def _determine_market_state(self, metrics: Dict[str, float]) -> Tuple[bool, MarketStructureState, str]:
        """
        Determine overall market state based on metrics.
        
        Returns:
            Tuple of (is_tradable, state, reason)
        """
        # Extract metrics
        liquidity_score = metrics["liquidity_depth_score"]
        volatility_score = metrics["volatility_score"]
        entropy_score = metrics["entropy_score"]
        time_reliability = metrics["time_reliability"]
        spread_score = metrics["spread_score"]
        
        # Check against thresholds
        issues = []
        
        if liquidity_score < self.thresholds["liquidity_depth_min"]:
            issues.append(f"Liquidity depth below threshold ({liquidity_score:.2f} < {self.thresholds['liquidity_depth_min']:.2f})")
        
        if volatility_score < 1.0 / self.thresholds["volatility_max"]:
            issues.append(f"Volatility above threshold ({1.0/volatility_score:.2f}x normal)")
        
        if entropy_score < self.thresholds["entropy_min"]:
            issues.append(f"Order flow entropy below threshold ({entropy_score:.2f} < {self.thresholds['entropy_min']:.2f})")
        
        if time_reliability < self.thresholds["time_reliability_min"]:
            issues.append(f"Time-of-day reliability below threshold ({time_reliability:.2f} < {self.thresholds['time_reliability_min']:.2f})")
        
        if spread_score < 1.0 / self.thresholds["spread_max"]:
            issues.append(f"Spread above threshold ({1.0/spread_score:.2f}x normal)")
        
        # Calculate overall score (weighted average)
        weights = {
            "liquidity_depth_score": 0.25,
            "volatility_score": 0.20,
            "entropy_score": 0.20,
            "time_reliability": 0.15,
            "spread_score": 0.20
        }
        
        overall_score = sum(metrics[k] * weights[k] for k in weights)
        
        # Determine state
        if overall_score >= 0.8 and not issues:
            return True, MarketStructureState.NORMAL, "Market structure normal"
        elif overall_score >= 0.5 or (issues and len(issues) <= 2):
            return False, MarketStructureState.DEGRADED, f"Market structure degraded: {'; '.join(issues)}"
        else:
            return False, MarketStructureState.UNDEFINED, f"Market structure undefined: {'; '.join(issues)}"
