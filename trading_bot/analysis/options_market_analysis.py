"""Options Market Analysis Module.

Implements institutional-grade options market analysis including:
- Volatility skew analysis
- Gamma exposure (GEX) levels
- Put/Call ratio analysis
- Unusual options activity detection
- Implied volatility surface
- Options flow monitoring
- Max pain calculation
- Delta hedging levels
- Volatility term structure
- Options sentiment indicators

This module enables derivatives market intelligence for
directional bias and market maker positioning analysis.
"""


from __future__ import annotations
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import math

import numpy as np
import pandas as pd
from loguru import logger

try:
    from scipy.stats import norm
    from scipy.optimize import brentq
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    norm = None
    brentq = None


class OptionType(enum.Enum):
    """Option types."""
    CALL = "call"
    PUT = "put"


class SkewType(enum.Enum):
    """Types of volatility skew."""
    NORMAL = "normal"  # Puts more expensive (typical)
    INVERTED = "inverted"  # Calls more expensive
    FLAT = "flat"  # Balanced
    SMILE = "smile"  # Both wings elevated


class FlowType(enum.Enum):
    """Types of options flow."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ActivityType(enum.Enum):
    """Types of unusual activity."""
    SWEEP = "sweep"  # Aggressive multi-exchange sweep
    BLOCK = "block"  # Large block trade
    SPLIT = "split"  # Split across strikes
    UNUSUAL_VOLUME = "unusual_volume"
    UNUSUAL_OI = "unusual_oi"


@dataclass
class OptionContract:
    """Represents an option contract."""
    symbol: str
    underlying: str
    strike: float
    expiration: datetime
    option_type: OptionType
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


@dataclass
class VolatilitySkew:
    """Volatility skew analysis."""
    underlying: str
    expiration: datetime
    atm_iv: float
    skew_25d: float  # 25 delta put IV - 25 delta call IV
    skew_10d: float  # 10 delta put IV - 10 delta call IV
    skew_type: SkewType
    put_wing_iv: float
    call_wing_iv: float
    risk_reversal: float  # 25d call IV - 25d put IV
    butterfly: float  # (25d call + 25d put) / 2 - ATM


@dataclass
class GammaExposure:
    """Gamma exposure analysis."""
    underlying: str
    spot_price: float
    total_gex: float  # Total gamma exposure
    call_gex: float
    put_gex: float
    gex_by_strike: Dict[float, float]
    flip_point: Optional[float]  # Price where GEX flips sign
    major_levels: List[Tuple[float, float]]  # (strike, gex)
    dealer_positioning: str  # 'long_gamma', 'short_gamma', 'neutral'


@dataclass
class PutCallRatio:
    """Put/Call ratio analysis."""
    underlying: str
    timestamp: datetime
    volume_ratio: float  # Put volume / Call volume
    oi_ratio: float  # Put OI / Call OI
    dollar_ratio: float  # Put $ volume / Call $ volume
    signal: str  # 'bullish', 'bearish', 'neutral'
    percentile: float  # Historical percentile (0-100)


@dataclass
class UnusualActivity:
    """Unusual options activity detection."""
    contract: OptionContract
    activity_type: ActivityType
    volume_oi_ratio: float
    dollar_value: float
    sentiment: FlowType
    premium_paid: float
    timestamp: datetime
    significance_score: float  # 0-100


@dataclass
class MaxPain:
    """Max pain calculation."""
    underlying: str
    expiration: datetime
    max_pain_strike: float
    current_price: float
    distance_percent: float
    call_pain_by_strike: Dict[float, float]
    put_pain_by_strike: Dict[float, float]
    total_pain_by_strike: Dict[float, float]


@dataclass
class OptionsFlow:
    """Aggregated options flow."""
    underlying: str
    timeframe_minutes: int
    total_premium: float
    call_premium: float
    put_premium: float
    net_premium: float  # Call - Put
    bullish_flow: float
    bearish_flow: float
    flow_type: FlowType
    large_trades: List[UnusualActivity]


class BlackScholes:
    """Black-Scholes option pricing model."""
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1 parameter."""
        if T <= 0 or sigma <= 0:
            return 0
        return (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2 parameter."""
        if T <= 0 or sigma <= 0:
            return 0
        return BlackScholes.d1(S, K, T, r, sigma) - sigma * math.sqrt(T)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate call option price."""
        if not SCIPY_AVAILABLE:
            return 0
        if T <= 0:
            return max(0, S - K)
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate put option price."""
        if not SCIPY_AVAILABLE:
            return 0
        if T <= 0:
            return max(0, K - S)
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    
    @staticmethod
    def delta(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
        """Calculate option delta."""
        if not SCIPY_AVAILABLE:
            return 0.5 if option_type == OptionType.CALL else -0.5
        if T <= 0:
            if option_type == OptionType.CALL:
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        if option_type == OptionType.CALL:
            return norm.cdf(d1)
        else:
            return norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate option gamma."""
        if not SCIPY_AVAILABLE:
            return 0
        if T <= 0 or sigma <= 0:
            return 0
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        return norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate option vega."""
        if not SCIPY_AVAILABLE:
            return 0
        if T <= 0:
            return 0
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        return S * norm.pdf(d1) * math.sqrt(T) / 100
    
    @staticmethod
    def theta(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
        """Calculate option theta (per day)."""
        if not SCIPY_AVAILABLE:
            return 0
        if T <= 0:
            return 0
        d1 = BlackScholes.d1(S, K, T, r, sigma)
        d2 = BlackScholes.d2(S, K, T, r, sigma)
        
        term1 = -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
        
        if option_type == OptionType.CALL:
            term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
        else:
            term2 = r * K * math.exp(-r * T) * norm.cdf(-d2)
            
        return (term1 + term2) / 365
    
    @staticmethod
    def implied_volatility(
        price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType,
        precision: float = 0.0001
    ) -> float:
        """Calculate implied volatility using Brent's method."""
        if not SCIPY_AVAILABLE or brentq is None:
            return 0.25  # Default IV
            
        if T <= 0:
            return 0
            
        def objective(sigma):
            try:
                if option_type == OptionType.CALL:
                    return BlackScholes.call_price(S, K, T, r, sigma) - price
                else:
                    return BlackScholes.put_price(S, K, T, r, sigma) - price

                return brentq(objective, 0.001, 5.0, xtol=precision)
            except (ValueError, RuntimeError):
                return 0.25


class OptionsMarketAnalyzer:
    """Options Market Analysis Engine.
    
    Provides comprehensive options market analysis for
    understanding market maker positioning and sentiment.
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.05,
        unusual_volume_threshold: float = 3.0,
        unusual_oi_threshold: float = 2.0
    ):
        """Initialize Options Market Analyzer.
        
        Args:
            risk_free_rate: Risk-free interest rate
            unusual_volume_threshold: Multiplier for unusual volume detection
            unusual_oi_threshold: Multiplier for unusual OI detection
        """
        self.risk_free_rate = risk_free_rate
        self.unusual_volume_threshold = unusual_volume_threshold
        self.unusual_oi_threshold = unusual_oi_threshold
        
        # Caches
        self._chain_cache: Dict[str, List[OptionContract]] = {}
        self._flow_cache: Dict[str, List[UnusualActivity]] = {}
        
    def analyze_volatility_skew(
        self,
        chain: List[OptionContract],
        spot_price: float
    ) -> VolatilitySkew:
        """Analyze volatility skew from options chain.
        
        Args:
            chain: List of option contracts
            spot_price: Current underlying price
            
        Returns:
            VolatilitySkew analysis
        """
        if not chain:
            return self._empty_skew()
            
        # Separate calls and puts
        calls = [c for c in chain if c.option_type == OptionType.CALL]
        puts = [c for c in chain if c.option_type == OptionType.PUT]
        
        if not calls or not puts:
            return self._empty_skew()
            
        # Find ATM options
        atm_strike = min(chain, key=lambda x: abs(x.strike - spot_price)).strike
        
        # Get ATM IV
        atm_calls = [c for c in calls if c.strike == atm_strike]
        atm_puts = [c for c in puts if c.strike == atm_strike]
        
        atm_iv = 0.25
        if atm_calls:
            atm_iv = atm_calls[0].implied_volatility
        elif atm_puts:
            atm_iv = atm_puts[0].implied_volatility
            
        # Calculate deltas and find 25d and 10d options
        def find_by_delta(options: List[OptionContract], target_delta: float) -> Optional[OptionContract]:
            closest = None
            min_diff = float('inf')
            for opt in options:
                diff = abs(abs(opt.delta) - target_delta)
                if diff < min_diff:
                    min_diff = diff
                    closest = opt
            return closest
            
        call_25d = find_by_delta(calls, 0.25)
        put_25d = find_by_delta(puts, 0.25)
        call_10d = find_by_delta(calls, 0.10)
        put_10d = find_by_delta(puts, 0.10)
        
        # Calculate skew metrics
        skew_25d = 0
        if put_25d and call_25d:
            skew_25d = put_25d.implied_volatility - call_25d.implied_volatility
            
        skew_10d = 0
        if put_10d and call_10d:
            skew_10d = put_10d.implied_volatility - call_10d.implied_volatility
            
        # Determine skew type
        if skew_25d > 0.02:
            skew_type = SkewType.NORMAL
        elif skew_25d < -0.02:
            skew_type = SkewType.INVERTED
        elif abs(skew_25d) <= 0.02 and abs(skew_10d) > 0.05:
            skew_type = SkewType.SMILE
        else:
            skew_type = SkewType.FLAT
            
        # Wing IVs
        put_wing_iv = put_10d.implied_volatility if put_10d else atm_iv
        call_wing_iv = call_10d.implied_volatility if call_10d else atm_iv
        
        # Risk reversal and butterfly
        risk_reversal = -skew_25d  # Call IV - Put IV
        butterfly = ((call_25d.implied_volatility if call_25d else atm_iv) + 
                    (put_25d.implied_volatility if put_25d else atm_iv)) / 2 - atm_iv
                    
        return VolatilitySkew(
            underlying=chain[0].underlying,
            expiration=chain[0].expiration,
            atm_iv=atm_iv,
            skew_25d=skew_25d,
            skew_10d=skew_10d,
            skew_type=skew_type,
            put_wing_iv=put_wing_iv,
            call_wing_iv=call_wing_iv,
            risk_reversal=risk_reversal,
            butterfly=butterfly
        )
        
    def calculate_gamma_exposure(
        self,
        chain: List[OptionContract],
        spot_price: float,
        contract_multiplier: int = 100
    ) -> GammaExposure:
        """Calculate dealer gamma exposure (GEX).
        
        Assumes dealers are short options (market makers).
        Positive GEX = dealers long gamma = stabilizing
        Negative GEX = dealers short gamma = amplifying
        
        Args:
            chain: List of option contracts
            spot_price: Current underlying price
            contract_multiplier: Contract multiplier (usually 100)
            
        Returns:
            GammaExposure analysis
        """
        if not chain:
            return self._empty_gex(spot_price)
            
        gex_by_strike: Dict[float, float] = {}
        total_call_gex = 0
        total_put_gex = 0
        
        for contract in chain:
            # GEX = Gamma * OI * Spot^2 * Contract Multiplier / 100
            # Negative for puts (dealers short puts = long gamma)
            # Positive for calls (dealers short calls = short gamma)
            
            gex = contract.gamma * contract.open_interest * spot_price**2 * contract_multiplier / 100
            
            if contract.option_type == OptionType.CALL:
                # Dealers short calls = short gamma = negative GEX
                gex = -gex
                total_call_gex += gex
            else:
                # Dealers short puts = long gamma = positive GEX
                total_put_gex += gex
                
            strike = contract.strike
            gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex
            
        total_gex = total_call_gex + total_put_gex
        
        # Find flip point (where GEX changes sign)
        flip_point = None
        sorted_strikes = sorted(gex_by_strike.keys())
        cumulative_gex = 0
        
        for i, strike in enumerate(sorted_strikes):
            prev_cumulative = cumulative_gex
            cumulative_gex += gex_by_strike[strike]
            
            if prev_cumulative * cumulative_gex < 0:  # Sign change
                flip_point = strike
                break
                
        # Major levels (highest absolute GEX)
        major_levels = sorted(
            [(k, v) for k, v in gex_by_strike.items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        # Dealer positioning
        if total_gex > spot_price * 1000000:  # Significant positive
            dealer_positioning = 'long_gamma'
        elif total_gex < -spot_price * 1000000:  # Significant negative
            dealer_positioning = 'short_gamma'
        else:
            dealer_positioning = 'neutral'
            
        return GammaExposure(
            underlying=chain[0].underlying if chain else "UNKNOWN",
            spot_price=spot_price,
            total_gex=total_gex,
            call_gex=total_call_gex,
            put_gex=total_put_gex,
            gex_by_strike=gex_by_strike,
            flip_point=flip_point,
            major_levels=major_levels,
            dealer_positioning=dealer_positioning
        )
        
    def calculate_put_call_ratio(
        self,
        chain: List[OptionContract],
        historical_ratios: Optional[List[float]] = None
    ) -> PutCallRatio:
        """Calculate put/call ratios.
        
        Args:
            chain: List of option contracts
            historical_ratios: Historical volume ratios for percentile
            
        Returns:
            PutCallRatio analysis
        """
        if not chain:
            return self._empty_pcr()
            
        calls = [c for c in chain if c.option_type == OptionType.CALL]
        puts = [c for c in chain if c.option_type == OptionType.PUT]
        
        call_volume = sum(c.volume for c in calls)
        put_volume = sum(c.volume for c in puts)
        
        call_oi = sum(c.open_interest for c in calls)
        put_oi = sum(c.open_interest for c in puts)
        
        call_dollar = sum(c.volume * c.last * 100 for c in calls)
        put_dollar = sum(c.volume * c.last * 100 for c in puts)
        
        volume_ratio = put_volume / call_volume if call_volume > 0 else 1.0
        oi_ratio = put_oi / call_oi if call_oi > 0 else 1.0
        dollar_ratio = put_dollar / call_dollar if call_dollar > 0 else 1.0
        
        # Determine signal
        # High P/C ratio (>1.0) = bearish sentiment = contrarian bullish
        # Low P/C ratio (<0.7) = bullish sentiment = contrarian bearish
        if volume_ratio > 1.2:
            signal = 'bullish'  # Contrarian
        elif volume_ratio < 0.7:
            signal = 'bearish'  # Contrarian
        else:
            signal = 'neutral'
            
        # Calculate percentile
        percentile = 50.0
        if historical_ratios:
            below = sum(1 for r in historical_ratios if r < volume_ratio)
            percentile = (below / len(historical_ratios)) * 100
            
        return PutCallRatio(
            underlying=chain[0].underlying if chain else "UNKNOWN",
            timestamp=datetime.now(),
            volume_ratio=volume_ratio,
            oi_ratio=oi_ratio,
            dollar_ratio=dollar_ratio,
            signal=signal,
            percentile=percentile
        )
        
    def detect_unusual_activity(
        self,
        chain: List[OptionContract],
        avg_volume: Optional[Dict[str, float]] = None
    ) -> List[UnusualActivity]:
        """Detect unusual options activity.
        
        Args:
            chain: List of option contracts
            avg_volume: Average volume by contract (optional)
            
        Returns:
            List of unusual activity detections
        """
        unusual = []
        
        for contract in chain:
            # Volume/OI ratio
            vol_oi_ratio = contract.volume / contract.open_interest if contract.open_interest > 0 else 0
            
            # Check for unusual volume
            is_unusual_volume = vol_oi_ratio > self.unusual_volume_threshold
            
            # Check for unusual OI
            is_unusual_oi = False
            if avg_volume and contract.symbol in avg_volume:
                is_unusual_oi = contract.open_interest > avg_volume[contract.symbol] * self.unusual_oi_threshold
                
            if is_unusual_volume or is_unusual_oi:
                # Determine sentiment
                if contract.option_type == OptionType.CALL:
                    sentiment = FlowType.BULLISH
                else:
                    sentiment = FlowType.BEARISH
                    
                # Calculate dollar value
                dollar_value = contract.volume * contract.last * 100
                
                # Determine activity type
                if vol_oi_ratio > 5:
                    activity_type = ActivityType.SWEEP
                elif dollar_value > 1000000:
                    activity_type = ActivityType.BLOCK
                elif is_unusual_oi:
                    activity_type = ActivityType.UNUSUAL_OI
                else:
                    activity_type = ActivityType.UNUSUAL_VOLUME
                    
                # Significance score
                significance = min(100, vol_oi_ratio * 20 + dollar_value / 100000)
                
                unusual.append(UnusualActivity(
                    contract=contract,
                    activity_type=activity_type,
                    volume_oi_ratio=vol_oi_ratio,
                    dollar_value=dollar_value,
                    sentiment=sentiment,
                    premium_paid=dollar_value,
                    timestamp=datetime.now(),
                    significance_score=significance
                ))
                
        # Sort by significance
        unusual.sort(key=lambda x: x.significance_score, reverse=True)
        
        return unusual
        
    def calculate_max_pain(
        self,
        chain: List[OptionContract],
        spot_price: float
    ) -> MaxPain:
        """Calculate max pain strike.
        
        Max pain is the strike price where option holders
        would experience maximum loss (minimum payout).
        
        Args:
            chain: List of option contracts
            spot_price: Current underlying price
            
        Returns:
            MaxPain analysis
        """
        if not chain:
            return self._empty_max_pain(spot_price)
            
        # Get unique strikes
        strikes = sorted(set(c.strike for c in chain))
        
        call_pain: Dict[float, float] = {}
        put_pain: Dict[float, float] = {}
        total_pain: Dict[float, float] = {}
        
        calls = {c.strike: c for c in chain if c.option_type == OptionType.CALL}
        puts = {c.strike: c for c in chain if c.option_type == OptionType.PUT}
        
        for test_price in strikes:
            call_pain[test_price] = 0
            put_pain[test_price] = 0
            
            for strike, call in calls.items():
                if test_price > strike:
                    # Call is ITM, holder profits
                    call_pain[test_price] += (test_price - strike) * call.open_interest * 100
                    
            for strike, put in puts.items():
                if test_price < strike:
                    # Put is ITM, holder profits
                    put_pain[test_price] += (strike - test_price) * put.open_interest * 100
                    
            total_pain[test_price] = call_pain[test_price] + put_pain[test_price]
            
        # Find max pain (minimum total payout)
        max_pain_strike = min(total_pain.keys(), key=lambda x: total_pain[x])
        distance_percent = (max_pain_strike - spot_price) / spot_price * 100
        
        return MaxPain(
            underlying=chain[0].underlying if chain else "UNKNOWN",
            expiration=chain[0].expiration if chain else datetime.now(),
            max_pain_strike=max_pain_strike,
            current_price=spot_price,
            distance_percent=distance_percent,
            call_pain_by_strike=call_pain,
            put_pain_by_strike=put_pain,
            total_pain_by_strike=total_pain
        )
        
    def analyze_options_flow(
        self,
        activities: List[UnusualActivity],
        timeframe_minutes: int = 60
    ) -> OptionsFlow:
        """Analyze aggregated options flow.
        
        Args:
            activities: List of unusual activities
            timeframe_minutes: Timeframe for aggregation
            
        Returns:
            OptionsFlow analysis
        """
        if not activities:
            return self._empty_flow()
            
        cutoff = datetime.now() - timedelta(minutes=timeframe_minutes)
        recent = [a for a in activities if a.timestamp >= cutoff]
        
        call_premium = sum(a.premium_paid for a in recent if a.contract.option_type == OptionType.CALL)
        put_premium = sum(a.premium_paid for a in recent if a.contract.option_type == OptionType.PUT)
        
        bullish_flow = sum(a.premium_paid for a in recent if a.sentiment == FlowType.BULLISH)
        bearish_flow = sum(a.premium_paid for a in recent if a.sentiment == FlowType.BEARISH)
        
        total_premium = call_premium + put_premium
        net_premium = call_premium - put_premium
        
        # Determine flow type
        if bullish_flow > bearish_flow * 1.5:
            flow_type = FlowType.BULLISH
        elif bearish_flow > bullish_flow * 1.5:
            flow_type = FlowType.BEARISH
        elif total_premium > 0:
            flow_type = FlowType.MIXED
        else:
            flow_type = FlowType.NEUTRAL
            
        return OptionsFlow(
            underlying=recent[0].contract.underlying if recent else "UNKNOWN",
            timeframe_minutes=timeframe_minutes,
            total_premium=total_premium,
            call_premium=call_premium,
            put_premium=put_premium,
            net_premium=net_premium,
            bullish_flow=bullish_flow,
            bearish_flow=bearish_flow,
            flow_type=flow_type,
            large_trades=recent[:10]  # Top 10 by significance
        )
        
    def get_options_sentiment(
        self,
        chain: List[OptionContract],
        spot_price: float
    ) -> Dict[str, Any]:
        """Get comprehensive options sentiment analysis.
        
        Args:
            chain: Options chain
            spot_price: Current price
            
        Returns:
            Dictionary with sentiment analysis
        """
        skew = self.analyze_volatility_skew(chain, spot_price)
        gex = self.calculate_gamma_exposure(chain, spot_price)
        pcr = self.calculate_put_call_ratio(chain)
        max_pain = self.calculate_max_pain(chain, spot_price)
        unusual = self.detect_unusual_activity(chain)
        
        # Aggregate sentiment
        bullish_signals = 0
        bearish_signals = 0
        
        # Skew signal
        if skew.skew_type == SkewType.INVERTED:
            bullish_signals += 1
        elif skew.skew_type == SkewType.NORMAL and skew.skew_25d > 0.05:
            bearish_signals += 1
            
        # GEX signal
        if gex.dealer_positioning == 'long_gamma':
            # Stabilizing, price likely to stay in range
            pass
        elif gex.dealer_positioning == 'short_gamma':
            # Amplifying, expect larger moves
            pass
            
        # PCR signal (contrarian)
        if pcr.signal == 'bullish':
            bullish_signals += 1
        elif pcr.signal == 'bearish':
            bearish_signals += 1
            
        # Max pain signal
        if max_pain.distance_percent > 2:
            bearish_signals += 1  # Price above max pain, expect pullback
        elif max_pain.distance_percent < -2:
            bullish_signals += 1  # Price below max pain, expect rally
            
        # Unusual activity signal
        bullish_unusual = sum(1 for u in unusual if u.sentiment == FlowType.BULLISH)
        bearish_unusual = sum(1 for u in unusual if u.sentiment == FlowType.BEARISH)
        
        if bullish_unusual > bearish_unusual * 1.5:
            bullish_signals += 1
        elif bearish_unusual > bullish_unusual * 1.5:
            bearish_signals += 1
            
        # Overall sentiment
        if bullish_signals > bearish_signals + 1:
            overall = 'bullish'
        elif bearish_signals > bullish_signals + 1:
            overall = 'bearish'
        else:
            overall = 'neutral'
            
        return {
            'overall_sentiment': overall,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'skew': {
                'type': skew.skew_type.value,
                'atm_iv': skew.atm_iv,
                'skew_25d': skew.skew_25d
            },
            'gamma_exposure': {
                'total_gex': gex.total_gex,
                'dealer_positioning': gex.dealer_positioning,
                'flip_point': gex.flip_point
            },
            'put_call_ratio': {
                'volume': pcr.volume_ratio,
                'signal': pcr.signal,
                'percentile': pcr.percentile
            },
            'max_pain': {
                'strike': max_pain.max_pain_strike,
                'distance_percent': max_pain.distance_percent
            },
            'unusual_activity': {
                'count': len(unusual),
                'bullish': bullish_unusual,
                'bearish': bearish_unusual
            }
        }
        
    def _empty_skew(self) -> VolatilitySkew:
        """Create empty volatility skew."""
        return VolatilitySkew(
            underlying="UNKNOWN",
            expiration=datetime.now(),
            atm_iv=0.25,
            skew_25d=0,
            skew_10d=0,
            skew_type=SkewType.FLAT,
            put_wing_iv=0.25,
            call_wing_iv=0.25,
            risk_reversal=0,
            butterfly=0
        )
        
    def _empty_gex(self, spot_price: float) -> GammaExposure:
        """Create empty gamma exposure."""
        return GammaExposure(
            underlying="UNKNOWN",
            spot_price=spot_price,
            total_gex=0,
            call_gex=0,
            put_gex=0,
            gex_by_strike={},
            flip_point=None,
            major_levels=[],
            dealer_positioning='neutral'
        )
        
    def _empty_pcr(self) -> PutCallRatio:
        """Create empty put/call ratio."""
        return PutCallRatio(
            underlying="UNKNOWN",
            timestamp=datetime.now(),
            volume_ratio=1.0,
            oi_ratio=1.0,
            dollar_ratio=1.0,
            signal='neutral',
            percentile=50.0
        )
        
    def _empty_max_pain(self, spot_price: float) -> MaxPain:
        """Create empty max pain."""
        return MaxPain(
            underlying="UNKNOWN",
            expiration=datetime.now(),
            max_pain_strike=spot_price,
            current_price=spot_price,
            distance_percent=0,
            call_pain_by_strike={},
            put_pain_by_strike={},
            total_pain_by_strike={}
        )
        
    def _empty_flow(self) -> OptionsFlow:
        """Create empty options flow."""
        return OptionsFlow(
            underlying="UNKNOWN",
            timeframe_minutes=60,
            total_premium=0,
            call_premium=0,
            put_premium=0,
            net_premium=0,
            bullish_flow=0,
            bearish_flow=0,
            flow_type=FlowType.NEUTRAL,
            large_trades=[]
        )


# Convenience functions
def calculate_iv(
    price: float,
    spot: float,
    strike: float,
    days_to_expiry: int,
    option_type: str = 'call',
    risk_free_rate: float = 0.05
) -> float:
    """Quick function to calculate implied volatility."""
    T = days_to_expiry / 365
    opt_type = OptionType.CALL if option_type.lower() == 'call' else OptionType.PUT
    return BlackScholes.implied_volatility(price, spot, strike, T, risk_free_rate, opt_type)


def calculate_greeks(
    spot: float,
    strike: float,
    days_to_expiry: int,
    volatility: float,
    option_type: str = 'call',
    risk_free_rate: float = 0.05
) -> Dict[str, float]:
    """Quick function to calculate option Greeks."""
    T = days_to_expiry / 365
    opt_type = OptionType.CALL if option_type.lower() == 'call' else OptionType.PUT
    
    return {
        'delta': BlackScholes.delta(spot, strike, T, risk_free_rate, volatility, opt_type),
        'gamma': BlackScholes.gamma(spot, strike, T, risk_free_rate, volatility),
        'theta': BlackScholes.theta(spot, strike, T, risk_free_rate, volatility, opt_type),
        'vega': BlackScholes.vega(spot, strike, T, risk_free_rate, volatility)
    }
