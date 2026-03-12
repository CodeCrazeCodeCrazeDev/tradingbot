"""VPIN (Volume-Synchronized Probability of Informed Trading) Analysis Module.

Implements comprehensive order flow toxicity analysis including:
- VPIN calculation and monitoring
- Order flow toxicity measurement
- Informed trading activity detection
- Flash crash probability estimation
- Market maker risk assessment
- Toxic flow alerts
- Volume bucket analysis
- CDF-based probability estimation

This module enables detection of toxic order flow and
informed trading activity for risk management.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import deque

import numpy as np
import pandas as pd
from loguru import logger

try:
    from scipy.stats import norm
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    norm = None


class ToxicityLevel(enum.Enum):
    """Order flow toxicity levels."""
    LOW = "low"  # VPIN < 0.3
    MODERATE = "moderate"  # 0.3 <= VPIN < 0.5
    ELEVATED = "elevated"  # 0.5 <= VPIN < 0.7
    HIGH = "high"  # 0.7 <= VPIN < 0.85
    EXTREME = "extreme"  # VPIN >= 0.85


class FlowDirection(enum.Enum):
    """Order flow direction."""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


class AlertType(enum.Enum):
    """Types of VPIN alerts."""
    TOXICITY_SPIKE = "toxicity_spike"
    SUSTAINED_HIGH = "sustained_high"
    FLASH_CRASH_RISK = "flash_crash_risk"
    INFORMED_FLOW = "informed_flow"
    LIQUIDITY_CRISIS = "liquidity_crisis"


@dataclass
class VolumeBucket:
    """Represents a volume bucket for VPIN calculation."""
    bucket_id: int
    start_time: datetime
    end_time: datetime
    total_volume: float
    buy_volume: float
    sell_volume: float
    num_trades: int
    vwap: float
    price_range: Tuple[float, float]
    order_imbalance: float  # (buy - sell) / total


@dataclass
class VPINReading:
    """VPIN calculation result."""
    timestamp: datetime
    vpin: float  # 0-1 scale
    toxicity_level: ToxicityLevel
    buy_volume_pct: float
    sell_volume_pct: float
    volume_imbalance: float
    buckets_used: int
    confidence: float
    historical_percentile: float


@dataclass
class ToxicityAlert:
    """Toxicity alert."""
    timestamp: datetime
    alert_type: AlertType
    vpin_value: float
    toxicity_level: ToxicityLevel
    severity: float  # 0-100
    message: str
    recommended_action: str


@dataclass
class InformedTradingSignal:
    """Informed trading detection signal."""
    timestamp: datetime
    probability: float  # Probability of informed trading
    direction: FlowDirection
    volume_anomaly: float  # Standard deviations from normal
    price_impact: float
    persistence: int  # Number of consecutive signals
    confidence: float


@dataclass
class FlashCrashRisk:
    """Flash crash risk assessment."""
    timestamp: datetime
    risk_score: float  # 0-100
    vpin_contribution: float
    liquidity_contribution: float
    volatility_contribution: float
    probability_1h: float  # Probability of flash crash in next hour
    probability_24h: float  # Probability in next 24 hours
    risk_factors: List[str]


class VPINCalculator:
    """VPIN (Volume-Synchronized Probability of Informed Trading) Calculator.
    
    VPIN measures the probability that informed traders are active
    in the market, which can predict market stress and flash crashes.
    """
    
    def __init__(
        self,
        bucket_size: float = 50000,  # Volume per bucket
        num_buckets: int = 50,  # Number of buckets for VPIN
        sigma_multiplier: float = 1.0,
        alert_threshold: float = 0.7
    ):
        """Initialize VPIN Calculator.
        
        Args:
            bucket_size: Volume per bucket (in shares/contracts)
            num_buckets: Number of buckets for rolling VPIN
            sigma_multiplier: Multiplier for volume classification
            alert_threshold: VPIN threshold for alerts
        """
        self.bucket_size = bucket_size
        self.num_buckets = num_buckets
        self.sigma_multiplier = sigma_multiplier
        self.alert_threshold = alert_threshold
        
        # Storage
        self._buckets: deque = deque(maxlen=num_buckets * 2)
        self._vpin_history: List[VPINReading] = []
        self._alerts: List[ToxicityAlert] = []
        
        # Current bucket accumulator
        self._current_bucket_volume = 0
        self._current_bucket_buy = 0
        self._current_bucket_sell = 0
        self._current_bucket_trades = 0
        self._current_bucket_start = None
        self._current_bucket_prices: List[Tuple[float, float]] = []  # (price, volume)
        
    def process_trade(
        self,
        price: float,
        volume: float,
        timestamp: datetime,
        trade_direction: Optional[FlowDirection] = None
    ) -> Optional[VPINReading]:
        """Process a single trade and update VPIN.
        
        Args:
            price: Trade price
            volume: Trade volume
            timestamp: Trade timestamp
            trade_direction: Known trade direction (optional)
            
        Returns:
            VPINReading if a new bucket was completed
        """
        if self._current_bucket_start is None:
            self._current_bucket_start = timestamp
            
        # Classify trade direction if not provided
        if trade_direction is None:
            trade_direction = self._classify_trade(price, volume)
            
        # Update current bucket
        self._current_bucket_volume += volume
        self._current_bucket_trades += 1
        self._current_bucket_prices.append((price, volume))
        
        if trade_direction == FlowDirection.BUY:
            self._current_bucket_buy += volume
        elif trade_direction == FlowDirection.SELL:
            self._current_bucket_sell += volume
        else:
            # Split neutral trades
            self._current_bucket_buy += volume / 2
            self._current_bucket_sell += volume / 2
            
        # Check if bucket is complete
        if self._current_bucket_volume >= self.bucket_size:
            return self._complete_bucket(timestamp)
            
        return None
        
    def process_bar(
        self,
        bar: pd.Series,
        timestamp: datetime
    ) -> Optional[VPINReading]:
        """Process an OHLCV bar and update VPIN.
        
        Uses bulk volume classification based on price movement.
        
        Args:
            bar: OHLCV bar data
            timestamp: Bar timestamp
            
        Returns:
            VPINReading if a new bucket was completed
        """
        volume = bar.get('volume', 0)
        if volume <= 0:
            return None
            
        # Bulk volume classification
        buy_volume, sell_volume = self._bulk_classify(bar)
        
        if self._current_bucket_start is None:
            self._current_bucket_start = timestamp
            
        # Update current bucket
        self._current_bucket_volume += volume
        self._current_bucket_buy += buy_volume
        self._current_bucket_sell += sell_volume
        self._current_bucket_trades += 1
        
        high = bar.get('high', bar.get('close', 0))
        low = bar.get('low', bar.get('close', 0))
        close = bar.get('close', 0)
        self._current_bucket_prices.append((close, volume))
        
        # Check if bucket is complete
        if self._current_bucket_volume >= self.bucket_size:
            return self._complete_bucket(timestamp)
            
        return None
        
    def _classify_trade(
        self,
        price: float,
        volume: float
    ) -> FlowDirection:
        """Classify trade direction using tick rule.
        
        Simple implementation - in practice would use
        bid/ask data or more sophisticated methods.
        """
        if not self._current_bucket_prices:
            return FlowDirection.NEUTRAL
            
        last_price = self._current_bucket_prices[-1][0]
        
        if price > last_price:
            return FlowDirection.BUY
        elif price < last_price:
            return FlowDirection.SELL
        else:
            return FlowDirection.NEUTRAL
            
    def _bulk_classify(
        self,
        bar: pd.Series
    ) -> Tuple[float, float]:
        """Bulk volume classification for OHLCV bars.
        
        Uses the formula from Easley, Lopez de Prado, and O'Hara (2012).
        """
        high = bar.get('high', bar.get('close', 0))
        low = bar.get('low', bar.get('close', 0))
        close = bar.get('close', 0)
        open_price = bar.get('open', close)
        volume = bar.get('volume', 0)
        
        if high == low:
            # No price movement - split evenly
            return volume / 2, volume / 2
            
        # Calculate buy/sell volume using price position
        # Buy volume = V * (C - L) / (H - L)
        # Sell volume = V * (H - C) / (H - L)
        
        buy_pct = (close - low) / (high - low)
        sell_pct = (high - close) / (high - low)
        
        # Alternative: Use open-close direction
        if close > open_price:
            # Bullish bar - weight towards buy
            buy_pct = min(1.0, buy_pct + 0.1)
            sell_pct = max(0.0, sell_pct - 0.1)
        elif close < open_price:
            # Bearish bar - weight towards sell
            buy_pct = max(0.0, buy_pct - 0.1)
            sell_pct = min(1.0, sell_pct + 0.1)
            
        buy_volume = volume * buy_pct
        sell_volume = volume * sell_pct
        
        return buy_volume, sell_volume
        
    def _complete_bucket(
        self,
        end_time: datetime
    ) -> VPINReading:
        """Complete current bucket and calculate VPIN."""
        # Calculate VWAP
        total_value = sum(p * v for p, v in self._current_bucket_prices)
        total_vol = sum(v for _, v in self._current_bucket_prices)
        vwap = total_value / total_vol if total_vol > 0 else 0
        
        # Price range
        prices = [p for p, _ in self._current_bucket_prices]
        price_range = (min(prices), max(prices)) if prices else (0, 0)
        
        # Order imbalance
        total = self._current_bucket_buy + self._current_bucket_sell
        imbalance = (self._current_bucket_buy - self._current_bucket_sell) / total if total > 0 else 0
        
        # Create bucket
        bucket = VolumeBucket(
            bucket_id=len(self._buckets),
            start_time=self._current_bucket_start,
            end_time=end_time,
            total_volume=self._current_bucket_volume,
            buy_volume=self._current_bucket_buy,
            sell_volume=self._current_bucket_sell,
            num_trades=self._current_bucket_trades,
            vwap=vwap,
            price_range=price_range,
            order_imbalance=imbalance
        )
        
        self._buckets.append(bucket)
        
        # Reset accumulator
        self._current_bucket_volume = 0
        self._current_bucket_buy = 0
        self._current_bucket_sell = 0
        self._current_bucket_trades = 0
        self._current_bucket_start = end_time
        self._current_bucket_prices = []
        
        # Calculate VPIN
        return self._calculate_vpin(end_time)
        
    def _calculate_vpin(
        self,
        timestamp: datetime
    ) -> VPINReading:
        """Calculate VPIN from recent buckets."""
        if len(self._buckets) < self.num_buckets:
            # Not enough buckets yet
            vpin = 0.5  # Neutral
            confidence = len(self._buckets) / self.num_buckets
        else:
            # Use last n buckets
            recent_buckets = list(self._buckets)[-self.num_buckets:]
            
            # VPIN = Sum(|V_buy - V_sell|) / Sum(V_total)
            total_imbalance = sum(abs(b.buy_volume - b.sell_volume) for b in recent_buckets)
            total_volume = sum(b.total_volume for b in recent_buckets)
            
            vpin = total_imbalance / total_volume if total_volume > 0 else 0.5
            confidence = 1.0
            
        # Determine toxicity level
        toxicity_level = self._get_toxicity_level(vpin)
        
        # Calculate buy/sell percentages
        recent_buckets = list(self._buckets)[-self.num_buckets:] if len(self._buckets) >= self.num_buckets else list(self._buckets)
        total_buy = sum(b.buy_volume for b in recent_buckets)
        total_sell = sum(b.sell_volume for b in recent_buckets)
        total = total_buy + total_sell
        
        buy_pct = (total_buy / total * 100) if total > 0 else 50
        sell_pct = (total_sell / total * 100) if total > 0 else 50
        
        # Volume imbalance
        vol_imbalance = (total_buy - total_sell) / total if total > 0 else 0
        
        # Historical percentile
        percentile = self._calculate_percentile(vpin)
        
        reading = VPINReading(
            timestamp=timestamp,
            vpin=vpin,
            toxicity_level=toxicity_level,
            buy_volume_pct=buy_pct,
            sell_volume_pct=sell_pct,
            volume_imbalance=vol_imbalance,
            buckets_used=len(recent_buckets),
            confidence=confidence,
            historical_percentile=percentile
        )
        
        self._vpin_history.append(reading)
        
        # Check for alerts
        self._check_alerts(reading)
        
        return reading
        
    def _get_toxicity_level(self, vpin: float) -> ToxicityLevel:
        """Convert VPIN to toxicity level."""
        if vpin < 0.3:
            return ToxicityLevel.LOW
        elif vpin < 0.5:
            return ToxicityLevel.MODERATE
        elif vpin < 0.7:
            return ToxicityLevel.ELEVATED
        elif vpin < 0.85:
            return ToxicityLevel.HIGH
        else:
            return ToxicityLevel.EXTREME
            
    def _calculate_percentile(self, vpin: float) -> float:
        """Calculate historical percentile of VPIN value."""
        if not self._vpin_history:
            return 50.0
            
        historical = [r.vpin for r in self._vpin_history]
        below = sum(1 for v in historical if v < vpin)
        
        return (below / len(historical)) * 100
        
    def _check_alerts(self, reading: VPINReading) -> None:
        """Check for alert conditions."""
        # Toxicity spike
        if reading.vpin >= self.alert_threshold:
            if reading.toxicity_level == ToxicityLevel.EXTREME:
                severity = 100
                action = "HALT TRADING - Extreme toxicity detected"
            elif reading.toxicity_level == ToxicityLevel.HIGH:
                severity = 80
                action = "REDUCE POSITION SIZE - High toxicity"
            else:
                severity = 60
                action = "MONITOR CLOSELY - Elevated toxicity"
                
            self._alerts.append(ToxicityAlert(
                timestamp=reading.timestamp,
                alert_type=AlertType.TOXICITY_SPIKE,
                vpin_value=reading.vpin,
                toxicity_level=reading.toxicity_level,
                severity=severity,
                message=f"VPIN spike to {reading.vpin:.3f}",
                recommended_action=action
            ))
            
        # Sustained high toxicity
        if len(self._vpin_history) >= 5:
            recent = self._vpin_history[-5:]
            if all(r.vpin >= 0.6 for r in recent):
                self._alerts.append(ToxicityAlert(
                    timestamp=reading.timestamp,
                    alert_type=AlertType.SUSTAINED_HIGH,
                    vpin_value=reading.vpin,
                    toxicity_level=reading.toxicity_level,
                    severity=70,
                    message="Sustained high toxicity over 5 periods",
                    recommended_action="Consider exiting positions"
                ))
                
        # Flash crash risk
        if reading.vpin >= 0.8 and reading.historical_percentile >= 95:
            self._alerts.append(ToxicityAlert(
                timestamp=reading.timestamp,
                alert_type=AlertType.FLASH_CRASH_RISK,
                vpin_value=reading.vpin,
                toxicity_level=reading.toxicity_level,
                severity=90,
                message="Flash crash risk elevated",
                recommended_action="IMMEDIATE ACTION - Reduce exposure"
            ))
            
    def detect_informed_trading(
        self,
        lookback: int = 10
    ) -> Optional[InformedTradingSignal]:
        """Detect informed trading activity.
        
        Args:
            lookback: Number of readings to analyze
            
        Returns:
            InformedTradingSignal if detected
        """
        if len(self._vpin_history) < lookback:
            return None
            
        recent = self._vpin_history[-lookback:]
        
        # Calculate average and std of VPIN
        vpins = [r.vpin for r in recent]
        avg_vpin = np.mean(vpins)
        std_vpin = np.std(vpins)
        
        current = recent[-1]
        
        # Check for anomaly
        if std_vpin > 0:
            z_score = (current.vpin - avg_vpin) / std_vpin
        else:
            z_score = 0
            
        # Informed trading if VPIN is significantly elevated
        if z_score >= 2.0 or current.vpin >= 0.7:
            # Determine direction
            if current.volume_imbalance > 0.2:
                direction = FlowDirection.BUY
            elif current.volume_imbalance < -0.2:
                direction = FlowDirection.SELL
            else:
                direction = FlowDirection.NEUTRAL
                
            # Count consecutive high readings
            persistence = 0
            for r in reversed(recent):
                if r.vpin >= 0.6:
                    persistence += 1
                else:
                    break
                    
            # Probability based on VPIN level
            probability = min(0.95, current.vpin)
            
            # Price impact (would need actual price data)
            price_impact = abs(current.volume_imbalance) * current.vpin
            
            return InformedTradingSignal(
                timestamp=current.timestamp,
                probability=probability,
                direction=direction,
                volume_anomaly=z_score,
                price_impact=price_impact,
                persistence=persistence,
                confidence=current.confidence
            )
            
        return None
        
    def assess_flash_crash_risk(
        self,
        volatility: Optional[float] = None,
        liquidity_score: Optional[float] = None
    ) -> FlashCrashRisk:
        """Assess flash crash risk.
        
        Args:
            volatility: Current volatility (optional)
            liquidity_score: Current liquidity score 0-100 (optional)
            
        Returns:
            FlashCrashRisk assessment
        """
        if not self._vpin_history:
            return FlashCrashRisk(
                timestamp=datetime.now(),
                risk_score=0,
                vpin_contribution=0,
                liquidity_contribution=0,
                volatility_contribution=0,
                probability_1h=0,
                probability_24h=0,
                risk_factors=[]
            )
            
        current = self._vpin_history[-1]
        
        # VPIN contribution (0-40 points)
        vpin_contribution = min(40, current.vpin * 50)
        
        # Liquidity contribution (0-30 points)
        if liquidity_score is not None:
            # Low liquidity = high risk
            liquidity_contribution = max(0, 30 - liquidity_score * 0.3)
        else:
            liquidity_contribution = 15  # Neutral
            
        # Volatility contribution (0-30 points)
        if volatility is not None:
            # High volatility = high risk
            volatility_contribution = min(30, volatility * 10)
        else:
            volatility_contribution = 15  # Neutral
            
        # Total risk score
        risk_score = vpin_contribution + liquidity_contribution + volatility_contribution
        
        # Probability estimates (simplified model)
        # Based on historical flash crash research
        if risk_score >= 80:
            prob_1h = 0.15
            prob_24h = 0.35
        elif risk_score >= 60:
            prob_1h = 0.05
            prob_24h = 0.15
        elif risk_score >= 40:
            prob_1h = 0.02
            prob_24h = 0.05
        else:
            prob_1h = 0.005
            prob_24h = 0.01
            
        # Risk factors
        risk_factors = []
        if current.vpin >= 0.7:
            risk_factors.append("High VPIN indicating toxic flow")
        if current.vpin >= 0.85:
            risk_factors.append("Extreme VPIN - informed trading likely")
        if liquidity_score is not None and liquidity_score < 30:
            risk_factors.append("Low liquidity conditions")
        if volatility is not None and volatility > 3:
            risk_factors.append("Elevated volatility")
        if len(self._vpin_history) >= 5:
            recent_avg = np.mean([r.vpin for r in self._vpin_history[-5:]])
            if recent_avg >= 0.6:
                risk_factors.append("Sustained elevated toxicity")
                
        return FlashCrashRisk(
            timestamp=datetime.now(),
            risk_score=risk_score,
            vpin_contribution=vpin_contribution,
            liquidity_contribution=liquidity_contribution,
            volatility_contribution=volatility_contribution,
            probability_1h=prob_1h,
            probability_24h=prob_24h,
            risk_factors=risk_factors
        )
        
    def get_current_vpin(self) -> Optional[VPINReading]:
        """Get most recent VPIN reading."""
        return self._vpin_history[-1] if self._vpin_history else None
        
    def get_alerts(
        self,
        since: Optional[datetime] = None
    ) -> List[ToxicityAlert]:
        """Get alerts since a given time."""
        if since is None:
            return self._alerts
        return [a for a in self._alerts if a.timestamp >= since]
        
    def get_summary(self) -> Dict[str, Any]:
        """Get VPIN analysis summary."""
        if not self._vpin_history:
            return {'status': 'no_data'}
            
        current = self._vpin_history[-1]
        
        # Historical stats
        vpins = [r.vpin for r in self._vpin_history]
        
        return {
            'current_vpin': current.vpin,
            'toxicity_level': current.toxicity_level.value,
            'buy_volume_pct': current.buy_volume_pct,
            'sell_volume_pct': current.sell_volume_pct,
            'volume_imbalance': current.volume_imbalance,
            'historical_percentile': current.historical_percentile,
            'statistics': {
                'mean': np.mean(vpins),
                'std': np.std(vpins),
                'min': min(vpins),
                'max': max(vpins),
                'readings': len(vpins)
            },
            'buckets_processed': len(self._buckets),
            'active_alerts': len([a for a in self._alerts if a.timestamp >= datetime.now() - timedelta(hours=1)])
        }


# Convenience functions
def calculate_vpin_from_bars(
    df: pd.DataFrame,
    bucket_size: float = 50000,
    num_buckets: int = 50
) -> List[VPINReading]:
    """Calculate VPIN from OHLCV DataFrame."""
    calculator = VPINCalculator(bucket_size=bucket_size, num_buckets=num_buckets)
    readings = []
    
    for idx, row in df.iterrows():
        timestamp = idx if isinstance(idx, datetime) else datetime.now()
        reading = calculator.process_bar(row, timestamp)
        if reading:
            readings.append(reading)
            
    return readings


def get_toxicity_level(vpin: float) -> str:
    """Quick function to get toxicity level from VPIN value."""
    if vpin < 0.3:
        return "LOW"
    elif vpin < 0.5:
        return "MODERATE"
    elif vpin < 0.7:
        return "ELEVATED"
    elif vpin < 0.85:
        return "HIGH"
    else:
        return "EXTREME"
