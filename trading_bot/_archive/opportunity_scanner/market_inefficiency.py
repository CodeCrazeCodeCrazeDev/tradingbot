"""
Market Inefficiency Scanner
Detects temporary pricing anomalies and market inefficiencies for profit
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import threading
import asyncio
import numpy
import pandas

logger = logging.getLogger(__name__)

class InefficiencyType(Enum):
    """Types of market inefficiencies"""
    PRICE_DISLOCATION = "price_dislocation"
    MEAN_REVERSION = "mean_reversion"
    MICROSTRUCTURE_NOISE = "microstructure_noise"
    LIQUIDITY_GAP = "liquidity_gap"
    TIME_DECAY = "time_decay"
    VOLATILITY_MISPRICING = "volatility_mispricing"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    SENTIMENT_DIVERGENCE = "sentiment_divergence"

@dataclass
class PriceAnomaly:
    """Represents a detected price anomaly"""
    symbol: str
    anomaly_type: InefficiencyType
    current_price: float
    expected_price: float
    deviation_percent: float
    confidence: float
    profit_potential: float
    risk_level: float
    time_to_reversion: float
    entry_zones: List[float]
    exit_targets: List[float]
    metadata: Dict[str, Any]

class MarketInefficiencyScanner:
    """
    Scans markets for inefficiencies and pricing anomalies
    Uses statistical models, ML, and market microstructure analysis
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.anomaly_threshold = self.config.get('anomaly_threshold', 2.5)  # Standard deviations
        self.lookback_period = self.config.get('lookback_period', 100)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        
        # Price history for analysis
        self.price_history = {}
        self.volume_history = {}
        self.spread_history = {}
        
        # Detected anomalies
        self.active_anomalies = []
        self.anomaly_history = deque(maxlen=1000)
        
        # Statistical models
        self.mean_reversion_models = {}
        self.volatility_models = {}
        self.correlation_matrices = {}
        
        # Real-time monitoring
        self.monitoring_active = False
        self.scan_interval = self.config.get('scan_interval', 1.0)
        
    async def scan_all_inefficiencies(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Comprehensive scan for all types of market inefficiencies
        """
        anomalies = []
        
        # Run all detection methods in parallel
        tasks = [
            self._detect_price_dislocations(market_data),
            self._detect_mean_reversion_opportunities(market_data),
            self._detect_microstructure_noise(market_data),
            self._detect_liquidity_gaps(market_data),
            self._detect_volatility_mispricings(market_data),
            self._detect_correlation_breakdowns(market_data),
            self._detect_sentiment_divergences(market_data)
        ]
        
        results = await asyncio.gather(*tasks)
        
        for result in results:
            if result:
                anomalies.extend(result)
        
        # Filter and rank anomalies
        filtered_anomalies = self._filter_anomalies(anomalies)
        ranked_anomalies = self._rank_by_profit_potential(filtered_anomalies)
        
        return ranked_anomalies
    
    async def _detect_price_dislocations(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Detect when price significantly deviates from fair value
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                # Calculate fair value using multiple methods
                fair_value = self._calculate_fair_value(symbol, data)
                current_price = data['price']
                
                # Calculate deviation
                deviation = abs(current_price - fair_value) / fair_value
                
                if deviation > self.anomaly_threshold / 100:
                    # Calculate Z-score
                    z_score = self._calculate_z_score(symbol, current_price)
                    
                    # Determine profit potential
                    profit_potential = self._estimate_profit_potential(
                        current_price, fair_value, data.get('volatility', 0.02)
                    )
                    
                    anomaly = PriceAnomaly(
                        symbol=symbol,
                        anomaly_type=InefficiencyType.PRICE_DISLOCATION,
                        current_price=current_price,
                        expected_price=fair_value,
                        deviation_percent=deviation * 100,
                        confidence=min(0.95, abs(z_score) / 4),
                        profit_potential=profit_potential,
                        risk_level=self._calculate_risk_level(data),
                        time_to_reversion=self._estimate_reversion_time(symbol, z_score),
                        entry_zones=self._calculate_entry_zones(current_price, fair_value),
                        exit_targets=self._calculate_exit_targets(current_price, fair_value),
                        metadata={
                            'z_score': z_score,
                            'volume_ratio': data.get('volume_ratio', 1.0),
                            'spread': data.get('spread', 0)
                        }
                    )
                    
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting price dislocation for {symbol}: {e}")
        
        return anomalies
    
    async def _detect_mean_reversion_opportunities(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Find assets that have deviated from their mean and likely to revert
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                if symbol not in self.price_history:
                    continue
                
                prices = self.price_history[symbol]
                if len(prices) < self.lookback_period:
                    continue
                
                # Calculate various means
                sma = np.mean(prices[-self.lookback_period:])
                ema = self._calculate_ema(prices, self.lookback_period)
                vwap = self._calculate_vwap(symbol)
                
                current_price = data['price']
                
                # Check for mean reversion opportunity
                deviations = [
                    (current_price - sma) / sma,
                    (current_price - ema) / ema,
                    (current_price - vwap) / vwap if vwap else 0
                ]
                
                max_deviation = max(abs(d) for d in deviations)
                
                if max_deviation > self.anomaly_threshold / 100:
                    # Calculate Bollinger Bands
                    bb_upper, bb_lower = self._calculate_bollinger_bands(prices)
                    
                    # Determine if overbought or oversold
                    if current_price > bb_upper:
                        expected_price = sma
                        direction = "SHORT"
                    elif current_price < bb_lower:
                        expected_price = sma
                        direction = "LONG"
                    else:
                        continue
                    
                    anomaly = PriceAnomaly(
                        symbol=symbol,
                        anomaly_type=InefficiencyType.MEAN_REVERSION,
                        current_price=current_price,
                        expected_price=expected_price,
                        deviation_percent=max_deviation * 100,
                        confidence=self._calculate_mean_reversion_confidence(symbol, current_price),
                        profit_potential=(abs(current_price - expected_price) / current_price) * 100,
                        risk_level=self._calculate_risk_level(data),
                        time_to_reversion=self._estimate_mean_reversion_time(symbol),
                        entry_zones=self._calculate_mean_reversion_entries(current_price, expected_price),
                        exit_targets=[expected_price * 0.98, expected_price, expected_price * 1.02],
                        metadata={
                            'direction': direction,
                            'bollinger_position': 'UPPER' if current_price > bb_upper else 'LOWER',
                            'rsi': self._calculate_rsi(prices)
                        }
                    )
                    
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting mean reversion for {symbol}: {e}")
        
        return anomalies
    
    async def _detect_microstructure_noise(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Detect and exploit temporary microstructure noise in pricing
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                # Analyze tick-level data for microstructure patterns
                if 'ticks' not in data:
                    continue
                
                ticks = data['ticks']
                
                # Detect temporary spikes/dips
                noise_level = self._calculate_microstructure_noise(ticks)
                
                if noise_level > self.anomaly_threshold:
                    # Identify the true price through noise filtering
                    true_price = self._filter_microstructure_noise(ticks)
                    current_price = data['price']
                    
                    deviation = abs(current_price - true_price) / true_price
                    
                    if deviation > 0.001:  # 0.1% threshold
                        anomaly = PriceAnomaly(
                            symbol=symbol,
                            anomaly_type=InefficiencyType.MICROSTRUCTURE_NOISE,
                            current_price=current_price,
                            expected_price=true_price,
                            deviation_percent=deviation * 100,
                            confidence=0.85,
                            profit_potential=deviation * 100 * 0.7,  # Conservative estimate
                            risk_level=0.3,  # Low risk for microstructure trades
                            time_to_reversion=0.1,  # Very quick reversion
                            entry_zones=[current_price],
                            exit_targets=[true_price],
                            metadata={
                                'noise_level': noise_level,
                                'tick_count': len(ticks),
                                'spread_volatility': self._calculate_spread_volatility(symbol)
                            }
                        )
                        
                        anomalies.append(anomaly)
                        
            except Exception as e:
                logger.error(f"Error detecting microstructure noise for {symbol}: {e}")
        
        return anomalies
    
    async def _detect_liquidity_gaps(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Find liquidity gaps that can be exploited
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                if 'order_book' not in data:
                    continue
                
                order_book = data['order_book']
                
                # Analyze order book for liquidity gaps
                gaps = self._find_liquidity_gaps(order_book)
                
                for gap in gaps:
                    if gap['size'] > self.anomaly_threshold:
                        current_price = data['price']
                        
                        anomaly = PriceAnomaly(
                            symbol=symbol,
                            anomaly_type=InefficiencyType.LIQUIDITY_GAP,
                            current_price=current_price,
                            expected_price=gap['target_price'],
                            deviation_percent=gap['size'],
                            confidence=0.75,
                            profit_potential=gap['profit_potential'],
                            risk_level=gap['risk'],
                            time_to_reversion=gap['estimated_fill_time'],
                            entry_zones=gap['entry_levels'],
                            exit_targets=gap['exit_levels'],
                            metadata={
                                'gap_volume': gap['volume'],
                                'bid_ask_imbalance': gap['imbalance'],
                                'depth': gap['depth']
                            }
                        )
                        
                        anomalies.append(anomaly)
                        
            except Exception as e:
                logger.error(f"Error detecting liquidity gaps for {symbol}: {e}")
        
        return anomalies
    
    async def _detect_volatility_mispricings(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Detect when volatility is mispriced relative to expected moves
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                if 'implied_volatility' not in data:
                    continue
                
                iv = data['implied_volatility']
                hv = self._calculate_historical_volatility(symbol)
                
                if hv is None:
                    continue
                
                # Check for volatility mispricing
                vol_spread = iv - hv
                
                if abs(vol_spread) > self.anomaly_threshold * 0.01:
                    current_price = data['price']
                    
                    # Calculate expected move based on correct volatility
                    expected_move = current_price * hv * np.sqrt(1/252)
                    
                    anomaly = PriceAnomaly(
                        symbol=symbol,
                        anomaly_type=InefficiencyType.VOLATILITY_MISPRICING,
                        current_price=current_price,
                        expected_price=current_price,  # Price itself isn't wrong, vol is
                        deviation_percent=abs(vol_spread) * 100,
                        confidence=0.8,
                        profit_potential=abs(vol_spread) * 100 * 0.5,
                        risk_level=0.4,
                        time_to_reversion=5.0,  # Volatility convergence takes time
                        entry_zones=[current_price - expected_move, current_price + expected_move],
                        exit_targets=self._calculate_volatility_targets(current_price, hv, iv),
                        metadata={
                            'implied_vol': iv,
                            'historical_vol': hv,
                            'vol_spread': vol_spread,
                            'expected_daily_move': expected_move
                        }
                    )
                    
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting volatility mispricing for {symbol}: {e}")
        
        return anomalies
    
    async def _detect_correlation_breakdowns(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Find when historically correlated assets diverge
        """
        anomalies = []
        
        # Get correlation pairs
        pairs = self._get_correlation_pairs(market_data)
        
        for pair in pairs:
            try:
                symbol1, symbol2 = pair
                
                if symbol1 not in market_data or symbol2 not in market_data:
                    continue
                
                # Calculate historical correlation
                hist_corr = self._calculate_correlation(symbol1, symbol2)
                
                if hist_corr is None or abs(hist_corr) < 0.7:
                    continue
                
                # Check current price relationship
                price1 = market_data[symbol1]['price']
                price2 = market_data[symbol2]['price']
                
                # Calculate expected price based on correlation
                expected_price2 = self._calculate_correlated_price(symbol1, symbol2, price1)
                
                deviation = abs(price2 - expected_price2) / expected_price2
                
                if deviation > self.anomaly_threshold / 100:
                    anomaly = PriceAnomaly(
                        symbol=f"{symbol1}/{symbol2}",
                        anomaly_type=InefficiencyType.CORRELATION_BREAKDOWN,
                        current_price=price2,
                        expected_price=expected_price2,
                        deviation_percent=deviation * 100,
                        confidence=abs(hist_corr),
                        profit_potential=deviation * 100 * abs(hist_corr),
                        risk_level=1 - abs(hist_corr),
                        time_to_reversion=self._estimate_correlation_reversion_time(pair),
                        entry_zones=[price2],
                        exit_targets=[expected_price2],
                        metadata={
                            'correlation': hist_corr,
                            'symbol1': symbol1,
                            'symbol2': symbol2,
                            'price1': price1
                        }
                    )
                    
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting correlation breakdown for {pair}: {e}")
        
        return anomalies
    
    async def _detect_sentiment_divergences(self, market_data: Dict) -> List[PriceAnomaly]:
        """
        Detect when market sentiment diverges from price action
        """
        anomalies = []
        
        for symbol, data in market_data.items():
            try:
                if 'sentiment' not in data:
                    continue
                
                sentiment = data['sentiment']
                current_price = data['price']
                
                # Calculate expected price based on sentiment
                expected_price = self._sentiment_to_price(symbol, sentiment)
                
                if expected_price is None:
                    continue
                
                deviation = abs(current_price - expected_price) / expected_price
                
                if deviation > self.anomaly_threshold / 100:
                    anomaly = PriceAnomaly(
                        symbol=symbol,
                        anomaly_type=InefficiencyType.SENTIMENT_DIVERGENCE,
                        current_price=current_price,
                        expected_price=expected_price,
                        deviation_percent=deviation * 100,
                        confidence=0.7,
                        profit_potential=deviation * 100 * 0.6,
                        risk_level=0.5,
                        time_to_reversion=10.0,  # Sentiment convergence is slow
                        entry_zones=self._calculate_sentiment_entries(current_price, expected_price),
                        exit_targets=[expected_price],
                        metadata={
                            'sentiment_score': sentiment,
                            'sentiment_type': self._classify_sentiment(sentiment),
                            'social_volume': data.get('social_volume', 0)
                        }
                    )
                    
                    anomalies.append(anomaly)
                    
            except Exception as e:
                logger.error(f"Error detecting sentiment divergence for {symbol}: {e}")
        
        return anomalies
    
    def _calculate_fair_value(self, symbol: str, data: Dict) -> float:
        """Calculate fair value using multiple valuation methods"""
        values = []
        
        # DCF valuation if available
        if 'fundamentals' in data:
            dcf_value = self._dcf_valuation(data['fundamentals'])
            if dcf_value:
                values.append(dcf_value)
        
        # Technical fair value
        if symbol in self.price_history:
            tech_value = self._technical_fair_value(self.price_history[symbol])
            if tech_value:
                values.append(tech_value)
        
        # Market-based fair value
        market_value = self._market_fair_value(data)
        if market_value:
            values.append(market_value)
        
        # Return weighted average
        if values:
            return np.average(values, weights=[0.3, 0.4, 0.3][:len(values)])
        
        return data['price']  # Default to current price
    
    def _calculate_z_score(self, symbol: str, price: float) -> float:
        """Calculate Z-score for price deviation"""
        if symbol not in self.price_history:
            return 0
        
        prices = self.price_history[symbol]
        if len(prices) < 20:
            return 0
        
        mean = np.mean(prices)
        std = np.std(prices)
        
        if std == 0:
            return 0
        
        return (price - mean) / std
    
    def _estimate_profit_potential(self, current: float, target: float, volatility: float) -> float:
        """Estimate realistic profit potential"""
        raw_potential = abs(target - current) / current
        
        # Adjust for volatility and slippage
        volatility_adjustment = 1 - (volatility * 2)  # Higher vol = lower realized profit
        slippage_adjustment = 0.95  # 5% slippage assumption
        
        return raw_potential * volatility_adjustment * slippage_adjustment * 100
    
    def _calculate_risk_level(self, data: Dict) -> float:
        """Calculate risk level for the opportunity"""
        risk_factors = []
        
        # Volatility risk
        if 'volatility' in data:
            risk_factors.append(min(1.0, data['volatility'] * 10))
        
        # Liquidity risk
        if 'volume' in data:
            liquidity_score = 1 - min(1.0, data['volume'] / 1000000)
            risk_factors.append(liquidity_score)
        
        # Spread risk
        if 'spread' in data:
            spread_risk = min(1.0, data['spread'] * 100)
            risk_factors.append(spread_risk)
        
        if risk_factors:
            return np.mean(risk_factors)
        
        return 0.5  # Default medium risk
    
    def _estimate_reversion_time(self, symbol: str, z_score: float) -> float:
        """Estimate time to price reversion in hours"""
        base_time = abs(z_score) * 2  # Base estimate
        
        # Adjust based on historical reversion patterns
        if symbol in self.anomaly_history:
            historical_times = [a.time_to_reversion for a in self.anomaly_history if a.symbol == symbol]
            if historical_times:
                base_time = np.mean(historical_times)
        
        return min(24.0, base_time)  # Cap at 24 hours
    
    def _calculate_entry_zones(self, current: float, target: float) -> List[float]:
        """Calculate optimal entry zones"""
        if current > target:
            # Short opportunity
            return [
                current * 1.005,  # Slightly above current
                current * 1.01,   # 1% above
                current * 1.02    # 2% above for aggressive entry
            ]
        else:
            # Long opportunity
            return [
                current * 0.995,  # Slightly below current
                current * 0.99,   # 1% below
                current * 0.98    # 2% below for aggressive entry
            ]
    
    def _calculate_exit_targets(self, current: float, target: float) -> List[float]:
        """Calculate exit targets with scaling"""
        diff = target - current
        
        return [
            current + (diff * 0.5),   # 50% of move
            current + (diff * 0.75),  # 75% of move
            target,                   # Full target
            current + (diff * 1.25)   # Stretch target
        ]
    
    def _filter_anomalies(self, anomalies: List[PriceAnomaly]) -> List[PriceAnomaly]:
        """Filter anomalies based on confidence and risk"""
        filtered = []
        
        for anomaly in anomalies:
            # Apply filters
            if anomaly.confidence < self.min_confidence:
                continue
            
            if anomaly.risk_level > 0.8:  # Too risky
                continue
            
            if anomaly.profit_potential < 0.5:  # Too small
                continue
            
            filtered.append(anomaly)
        
        return filtered
    
    def _rank_by_profit_potential(self, anomalies: List[PriceAnomaly]) -> List[PriceAnomaly]:
        """Rank anomalies by risk-adjusted profit potential"""
        for anomaly in anomalies:
            # Calculate risk-adjusted score
            anomaly.score = (
                anomaly.profit_potential * 
                anomaly.confidence * 
                (1 - anomaly.risk_level) /
                max(0.1, anomaly.time_to_reversion)
            )
        
        # Sort by score
        return sorted(anomalies, key=lambda x: x.score, reverse=True)
    
    # Helper methods
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_vwap(self, symbol: str) -> Optional[float]:
        """Calculate Volume Weighted Average Price"""
        if symbol not in self.price_history or symbol not in self.volume_history:
            return None
        
        prices = self.price_history[symbol][-self.lookback_period:]
        volumes = self.volume_history[symbol][-self.lookback_period:]
        
        if len(prices) != len(volumes):
            return None
        
        return np.sum(np.array(prices) * np.array(volumes)) / np.sum(volumes)
    
    def _calculate_bollinger_bands(self, prices: List[float]) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        mean = np.mean(prices)
        std = np.std(prices)
        
        upper = mean + (2 * std)
        lower = mean - (2 * std)
        
        return upper, lower
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50  # Neutral
        
        deltas = np.diff(prices)
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class MispricingDetector:
    """
    Advanced mispricing detection using multiple techniques
    """
    
    def __init__(self):
        self.detection_methods = [
            self._detect_put_call_parity_violation,
            self._detect_futures_basis_trade,
            self._detect_etf_nav_discount,
            self._detect_cross_asset_mispricing
        ]
    
    def detect_all_mispricings(self, market_data: Dict) -> List[Dict]:
        """Run all mispricing detection methods"""
        mispricings = []
        
        for method in self.detection_methods:
            try:
                results = method(market_data)
                if results:
                    mispricings.extend(results)
            except Exception as e:
                logger.error(f"Error in mispricing detection: {e}")
        
        return mispricings
    
    def _detect_put_call_parity_violation(self, market_data: Dict) -> List[Dict]:
        """Detect put-call parity violations in options"""
        violations = []
        
        # Implementation for put-call parity check
        # C - P = S - K * e^(-r*T)
        
        return violations
    
    def _detect_futures_basis_trade(self, market_data: Dict) -> List[Dict]:
        """Detect futures basis trading opportunities"""
        opportunities = []
        
        # Check futures vs spot prices
        # Look for abnormal basis
        
        return opportunities
    
    def _detect_etf_nav_discount(self, market_data: Dict) -> List[Dict]:
        """Detect ETF trading at discount/premium to NAV"""
        discounts = []
        
        # Compare ETF price to underlying basket value
        
        return discounts
    
    def _detect_cross_asset_mispricing(self, market_data: Dict) -> List[Dict]:
        """Detect cross-asset mispricings"""
        mispricings = []
        
        # Check relationships between related assets
        # E.g., gold vs gold miners, oil vs energy stocks
        
        return mispricings


class EfficiencyRatio:
    """
    Calculate market efficiency ratio to identify trending vs ranging markets
    """
    
    def __init__(self, period: int = 10):
        self.period = period
    
    def calculate(self, prices: List[float]) -> float:
        """
        Calculate Kaufman's Efficiency Ratio
        Values close to 1 indicate trending market (inefficient)
        Values close to 0 indicate ranging market (efficient)
        """
        if len(prices) < self.period:
            return 0.5
        
        # Calculate net change
        net_change = abs(prices[-1] - prices[-self.period])
        
        # Calculate sum of absolute changes
        sum_changes = sum(abs(prices[i] - prices[i-1]) for i in range(-self.period + 1, 0))
        
        if sum_changes == 0:
            return 0
        
        return net_change / sum_changes
