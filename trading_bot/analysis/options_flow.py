"""
Options Flow Analysis

Analyzes options market data to generate trading signals:
- Unusual options activity detection
- Put/Call ratio analysis
- Options volume vs open interest
- Smart money flow detection
- Gamma exposure analysis
- Max pain calculation
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class OptionType(Enum):
    """Option type."""
    CALL = "call"
    PUT = "put"


class OrderFlow(Enum):
    """Order flow direction."""
    BUY = "buy"
    SELL = "sell"
    UNKNOWN = "unknown"


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class OptionContract:
    """Represents an option contract."""
    symbol: str
    underlying: str
    option_type: OptionType
    strike: float
    expiration: datetime
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    
    @property
    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_pct(self) -> float:
        try:
            if self.mid_price > 0:
                return self.spread / self.mid_price
            return 0.0
        except Exception as e:
            logger.error(f"Error in spread_pct: {e}")
            raise
    
    @property
    def volume_oi_ratio(self) -> float:
        try:
            if self.open_interest > 0:
                return self.volume / self.open_interest
            return 0.0
        except Exception as e:
            logger.error(f"Error in volume_oi_ratio: {e}")
            raise
    
    @property
    def is_unusual_volume(self) -> bool:
        return self.volume_oi_ratio > 1.0
    
    @property
    def notional_value(self) -> float:
        return self.volume * self.last * 100  # Options are 100 shares
    
    @property
    def days_to_expiry(self) -> int:
        return (self.expiration - datetime.now()).days


@dataclass
class OptionsFlow:
    """Represents an options flow transaction."""
    timestamp: datetime
    contract: OptionContract
    size: int
    price: float
    flow_type: OrderFlow
    is_sweep: bool = False
    is_block: bool = False
    exchange: str = ""
    premium: float = 0.0
    
    @property
    def total_premium(self) -> float:
        return self.size * self.price * 100
    
    @property
    def is_bullish(self) -> bool:
        try:
            if self.contract.option_type == OptionType.CALL:
                return self.flow_type == OrderFlow.BUY
            else:
                return self.flow_type == OrderFlow.SELL
        except Exception as e:
            logger.error(f"Error in is_bullish: {e}")
            raise
    
    @property
    def is_bearish(self) -> bool:
        return not self.is_bullish


@dataclass
class OptionsSignal:
    """Options-based trading signal."""
    symbol: str
    signal_type: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: SignalStrength
    confidence: float
    put_call_ratio: float
    unusual_activity_count: int
    total_call_volume: int
    total_put_volume: int
    net_premium_flow: float  # Positive = bullish, Negative = bearish
    max_pain: float
    gamma_exposure: float
    key_strikes: List[float]
    analysis: str
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'put_call_ratio': self.put_call_ratio,
            'unusual_activity_count': self.unusual_activity_count,
            'total_call_volume': self.total_call_volume,
            'total_put_volume': self.total_put_volume,
            'net_premium_flow': self.net_premium_flow,
            'max_pain': self.max_pain,
            'gamma_exposure': self.gamma_exposure,
            'key_strikes': self.key_strikes,
            'analysis': self.analysis,
            'generated_at': self.generated_at.isoformat()
        }


class PutCallRatioAnalyzer:
    """
    Analyzes put/call ratios for sentiment.
    
    - PCR < 0.7: Bullish sentiment (more calls)
    - PCR 0.7-1.0: Neutral
    - PCR > 1.0: Bearish sentiment (more puts)
    - Extreme readings often signal reversals
    """
    
    def __init__(self):
        try:
            self.history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
            self.lookback_days = 20
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_reading(self, symbol: str, pcr: float, timestamp: Optional[datetime] = None):
        """Add PCR reading to history."""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            self.history[symbol].append((timestamp, pcr))
        
            # Keep only recent history
            cutoff = datetime.now() - timedelta(days=self.lookback_days)
            self.history[symbol] = [(t, p) for t, p in self.history[symbol] if t >= cutoff]
        except Exception as e:
            logger.error(f"Error in add_reading: {e}")
            raise
    
    def analyze(self, symbol: str, current_pcr: float) -> Dict[str, Any]:
        """
        Analyze PCR for a symbol.
        
        Returns:
            Analysis dict with sentiment and signals
        """
        try:
            self.add_reading(symbol, current_pcr)
        
            history = [p for _, p in self.history[symbol]]
        
            if len(history) < 5:
                return {
                    'sentiment': 'NEUTRAL',
                    'signal': None,
                    'pcr': current_pcr,
                    'percentile': 50
                }
        
            # Calculate percentile
            sorted_history = sorted(history)
            percentile = (sorted_history.index(min(sorted_history, key=lambda x: abs(x - current_pcr))) / len(sorted_history)) * 100
        
            # Determine sentiment
            if current_pcr < 0.7:
                sentiment = 'BULLISH'
            elif current_pcr > 1.0:
                sentiment = 'BEARISH'
            else:
                sentiment = 'NEUTRAL'
        
            # Check for extreme readings (contrarian signals)
            signal = None
            if percentile < 10:
                signal = 'EXTREME_BULLISH_CONTRARIAN_BEARISH'  # Too bullish, expect reversal
            elif percentile > 90:
                signal = 'EXTREME_BEARISH_CONTRARIAN_BULLISH'  # Too bearish, expect reversal
        
            return {
                'sentiment': sentiment,
                'signal': signal,
                'pcr': current_pcr,
                'percentile': percentile,
                'avg_pcr': statistics.mean(history),
                'std_pcr': statistics.stdev(history) if len(history) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class UnusualActivityDetector:
    """
    Detects unusual options activity.
    
    Criteria:
    - Volume > 2x average
    - Volume > Open Interest
    - Large premium transactions
    - Sweep orders across exchanges
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.volume_threshold = self.config.get('volume_threshold', 2.0)
            self.premium_threshold = self.config.get('premium_threshold', 100000)
            self.sweep_threshold = self.config.get('sweep_threshold', 3)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect(self, contracts: List[OptionContract], flows: List[OptionsFlow]) -> List[Dict[str, Any]]:
        """
        Detect unusual activity.
        
        Returns:
            List of unusual activity alerts
        """
        try:
            alerts = []
        
            for contract in contracts:
                # Check volume vs OI
                if contract.volume_oi_ratio > self.volume_threshold:
                    alerts.append({
                        'type': 'HIGH_VOLUME_OI',
                        'contract': contract,
                        'ratio': contract.volume_oi_ratio,
                        'description': f"Volume {contract.volume:,} is {contract.volume_oi_ratio:.1f}x OI"
                    })
            
                # Check for unusual volume
                if contract.is_unusual_volume:
                    alerts.append({
                        'type': 'UNUSUAL_VOLUME',
                        'contract': contract,
                        'volume': contract.volume,
                        'description': f"Unusual volume: {contract.volume:,} contracts"
                    })
        
            # Check flows for large premiums
            for flow in flows:
                if flow.total_premium > self.premium_threshold:
                    alerts.append({
                        'type': 'LARGE_PREMIUM',
                        'flow': flow,
                        'premium': flow.total_premium,
                        'description': f"Large premium: ${flow.total_premium:,.0f}"
                    })
            
                if flow.is_sweep:
                    alerts.append({
                        'type': 'SWEEP_ORDER',
                        'flow': flow,
                        'description': f"Sweep order: {flow.size} contracts across exchanges"
                    })
            
                if flow.is_block:
                    alerts.append({
                        'type': 'BLOCK_TRADE',
                        'flow': flow,
                        'description': f"Block trade: {flow.size} contracts"
                    })
        
            return alerts
        except Exception as e:
            logger.error(f"Error in detect: {e}")
            raise


class MaxPainCalculator:
    """
    Calculates options max pain level.
    
    Max pain is the strike price where option holders would
    experience the maximum loss (and option writers maximum gain).
    """
    
    def calculate(self, calls: List[OptionContract], puts: List[OptionContract]) -> Dict[str, Any]:
        """
        Calculate max pain strike.
        
        Returns:
            Dict with max pain strike and analysis
        """
        try:
            if not calls and not puts:
                return {'max_pain': None, 'analysis': 'No options data'}
        
            # Get all unique strikes
            all_strikes = set()
            for c in calls:
                all_strikes.add(c.strike)
            for p in puts:
                all_strikes.add(p.strike)
        
            strikes = sorted(all_strikes)
        
            if not strikes:
                return {'max_pain': None, 'analysis': 'No strikes found'}
        
            # Calculate pain at each strike
            pain_by_strike = {}
        
            for test_strike in strikes:
                total_pain = 0
            
                # Call pain: if price < strike, calls expire worthless (pain for call holders)
                for call in calls:
                    if test_strike < call.strike:
                        # Call is OTM, holder loses premium
                        total_pain += call.open_interest * call.last * 100
                    else:
                        # Call is ITM, holder gains intrinsic value
                        intrinsic = (test_strike - call.strike) * call.open_interest * 100
                        premium_paid = call.open_interest * call.last * 100
                        total_pain += max(0, premium_paid - intrinsic)
            
                # Put pain: if price > strike, puts expire worthless
                for put in puts:
                    if test_strike > put.strike:
                        # Put is OTM, holder loses premium
                        total_pain += put.open_interest * put.last * 100
                    else:
                        # Put is ITM, holder gains intrinsic value
                        intrinsic = (put.strike - test_strike) * put.open_interest * 100
                        premium_paid = put.open_interest * put.last * 100
                        total_pain += max(0, premium_paid - intrinsic)
            
                pain_by_strike[test_strike] = total_pain
        
            # Find max pain (strike with maximum total pain)
            max_pain_strike = min(pain_by_strike, key=pain_by_strike.get)
        
            return {
                'max_pain': max_pain_strike,
                'pain_by_strike': pain_by_strike,
                'analysis': f"Max pain at ${max_pain_strike:.2f}"
            }
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class GammaExposureCalculator:
    """
    Calculates dealer gamma exposure (GEX).
    
    High positive GEX: Dealers are long gamma, will buy dips and sell rallies (stabilizing)
    High negative GEX: Dealers are short gamma, will sell dips and buy rallies (destabilizing)
    """
    
    def calculate(
        self,
        calls: List[OptionContract],
        puts: List[OptionContract],
        spot_price: float
    ) -> Dict[str, Any]:
        """
        Calculate gamma exposure.
        
        Returns:
            Dict with GEX analysis
        """
        try:
            total_call_gex = 0
            total_put_gex = 0
            gex_by_strike = defaultdict(float)
        
            for call in calls:
                # Dealers are typically short calls (sold to retail)
                # So dealer gamma from calls is negative
                gex = -call.gamma * call.open_interest * 100 * spot_price
                total_call_gex += gex
                gex_by_strike[call.strike] += gex
        
            for put in puts:
                # Dealers are typically long puts (bought from retail)
                # So dealer gamma from puts is positive
                gex = put.gamma * put.open_interest * 100 * spot_price
                total_put_gex += gex
                gex_by_strike[put.strike] += gex
        
            total_gex = total_call_gex + total_put_gex
        
            # Find key gamma levels
            sorted_strikes = sorted(gex_by_strike.items(), key=lambda x: abs(x[1]), reverse=True)
            key_levels = [strike for strike, _ in sorted_strikes[:5]]
        
            # Determine market impact
            if total_gex > 0:
                impact = "STABILIZING - Dealers will buy dips and sell rallies"
            else:
                impact = "DESTABILIZING - Dealers will amplify moves"
        
            return {
                'total_gex': total_gex,
                'call_gex': total_call_gex,
                'put_gex': total_put_gex,
                'gex_by_strike': dict(gex_by_strike),
                'key_levels': key_levels,
                'market_impact': impact,
                'spot_price': spot_price
            }
        except Exception as e:
            logger.error(f"Error in calculate: {e}")
            raise


class OptionsFlowAnalyzer:
    """
    Complete options flow analysis system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            self.pcr_analyzer = PutCallRatioAnalyzer()
            self.unusual_detector = UnusualActivityDetector(config)
            self.max_pain_calc = MaxPainCalculator()
            self.gex_calc = GammaExposureCalculator()
        
            # Storage
            self.contracts: Dict[str, List[OptionContract]] = defaultdict(list)
            self.flows: Dict[str, List[OptionsFlow]] = defaultdict(list)
        
            logger.info("OptionsFlowAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_contract(self, contract: OptionContract):
        """Add option contract data."""
        try:
            self.contracts[contract.underlying].append(contract)
        except Exception as e:
            logger.error(f"Error in add_contract: {e}")
            raise
    
    def add_flow(self, flow: OptionsFlow):
        """Add options flow transaction."""
        try:
            self.flows[flow.contract.underlying].append(flow)
        except Exception as e:
            logger.error(f"Error in add_flow: {e}")
            raise
    
    def analyze(self, symbol: str, spot_price: float) -> OptionsSignal:
        """
        Generate comprehensive options signal for a symbol.
        
        Args:
            symbol: Underlying symbol
            spot_price: Current spot price
            
        Returns:
            OptionsSignal with analysis
        """
        try:
            contracts = self.contracts.get(symbol, [])
            flows = self.flows.get(symbol, [])
        
            if not contracts:
                return OptionsSignal(
                    symbol=symbol,
                    signal_type='NEUTRAL',
                    strength=SignalStrength.WEAK,
                    confidence=0.0,
                    put_call_ratio=1.0,
                    unusual_activity_count=0,
                    total_call_volume=0,
                    total_put_volume=0,
                    net_premium_flow=0.0,
                    max_pain=spot_price,
                    gamma_exposure=0.0,
                    key_strikes=[],
                    analysis="No options data available"
                )
        
            # Separate calls and puts
            calls = [c for c in contracts if c.option_type == OptionType.CALL]
            puts = [c for c in contracts if c.option_type == OptionType.PUT]
        
            # Calculate volumes
            total_call_volume = sum(c.volume for c in calls)
            total_put_volume = sum(c.volume for c in puts)
        
            # Put/Call ratio
            pcr = total_put_volume / total_call_volume if total_call_volume > 0 else 1.0
            pcr_analysis = self.pcr_analyzer.analyze(symbol, pcr)
        
            # Unusual activity
            unusual = self.unusual_detector.detect(contracts, flows)
        
            # Max pain
            max_pain_result = self.max_pain_calc.calculate(calls, puts)
            max_pain = max_pain_result.get('max_pain', spot_price)
        
            # Gamma exposure
            gex_result = self.gex_calc.calculate(calls, puts, spot_price)
        
            # Calculate net premium flow
            bullish_premium = sum(f.total_premium for f in flows if f.is_bullish)
            bearish_premium = sum(f.total_premium for f in flows if f.is_bearish)
            net_premium_flow = bullish_premium - bearish_premium
        
            # Determine signal
            signal_type, strength, confidence = self._calculate_signal(
                pcr_analysis,
                unusual,
                net_premium_flow,
                gex_result,
                spot_price,
                max_pain
            )
        
            # Get key strikes
            key_strikes = gex_result.get('key_levels', [])
            if max_pain and max_pain not in key_strikes:
                key_strikes.insert(0, max_pain)
        
            # Generate analysis text
            analysis = self._generate_analysis(
                pcr_analysis,
                unusual,
                net_premium_flow,
                gex_result,
                max_pain,
                spot_price
            )
        
            return OptionsSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                put_call_ratio=pcr,
                unusual_activity_count=len(unusual),
                total_call_volume=total_call_volume,
                total_put_volume=total_put_volume,
                net_premium_flow=net_premium_flow,
                max_pain=max_pain,
                gamma_exposure=gex_result.get('total_gex', 0),
                key_strikes=key_strikes[:5],
                analysis=analysis
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _calculate_signal(
        self,
        pcr_analysis: Dict,
        unusual: List,
        net_premium: float,
        gex_result: Dict,
        spot_price: float,
        max_pain: float
    ) -> Tuple[str, SignalStrength, float]:
        """Calculate signal type, strength, and confidence."""
        try:
            bullish_points = 0
            bearish_points = 0
            total_points = 0
        
            # PCR analysis
            if pcr_analysis['sentiment'] == 'BULLISH':
                bullish_points += 2
            elif pcr_analysis['sentiment'] == 'BEARISH':
                bearish_points += 2
            total_points += 2
        
            # Contrarian signals from extreme PCR
            if pcr_analysis.get('signal') == 'EXTREME_BULLISH_CONTRARIAN_BEARISH':
                bearish_points += 1
            elif pcr_analysis.get('signal') == 'EXTREME_BEARISH_CONTRARIAN_BULLISH':
                bullish_points += 1
        
            # Net premium flow
            if net_premium > 100000:
                bullish_points += 2
            elif net_premium < -100000:
                bearish_points += 2
            elif net_premium > 0:
                bullish_points += 1
            else:
                bearish_points += 1
            total_points += 2
        
            # Max pain analysis
            if max_pain:
                if spot_price < max_pain * 0.98:  # Below max pain
                    bullish_points += 1  # Price may gravitate up
                elif spot_price > max_pain * 1.02:  # Above max pain
                    bearish_points += 1  # Price may gravitate down
            total_points += 1
        
            # GEX analysis
            total_gex = gex_result.get('total_gex', 0)
            if total_gex > 0:
                # Stabilizing - trend continuation
                pass
            else:
                # Destabilizing - expect larger moves
                total_points += 1
        
            # Unusual activity
            bullish_unusual = len([u for u in unusual if 'CALL' in str(u.get('contract', {}))])
            bearish_unusual = len([u for u in unusual if 'PUT' in str(u.get('contract', {}))])
        
            if bullish_unusual > bearish_unusual:
                bullish_points += 1
            elif bearish_unusual > bullish_unusual:
                bearish_points += 1
            total_points += 1
        
            # Calculate final signal
            net_score = bullish_points - bearish_points
            confidence = abs(net_score) / total_points if total_points > 0 else 0
        
            if net_score >= 3:
                signal_type = 'BULLISH'
                strength = SignalStrength.VERY_STRONG if net_score >= 5 else SignalStrength.STRONG
            elif net_score >= 1:
                signal_type = 'BULLISH'
                strength = SignalStrength.MODERATE if net_score >= 2 else SignalStrength.WEAK
            elif net_score <= -3:
                signal_type = 'BEARISH'
                strength = SignalStrength.VERY_STRONG if net_score <= -5 else SignalStrength.STRONG
            elif net_score <= -1:
                signal_type = 'BEARISH'
                strength = SignalStrength.MODERATE if net_score <= -2 else SignalStrength.WEAK
            else:
                signal_type = 'NEUTRAL'
                strength = SignalStrength.WEAK
        
            return signal_type, strength, confidence
        except Exception as e:
            logger.error(f"Error in _calculate_signal: {e}")
            raise
    
    def _generate_analysis(
        self,
        pcr_analysis: Dict,
        unusual: List,
        net_premium: float,
        gex_result: Dict,
        max_pain: float,
        spot_price: float
    ) -> str:
        """Generate human-readable analysis."""
        try:
            parts = []
        
            # PCR
            parts.append(f"P/C Ratio: {pcr_analysis['pcr']:.2f} ({pcr_analysis['sentiment']})")
        
            # Net premium
            if net_premium > 0:
                parts.append(f"Net bullish premium: ${net_premium:,.0f}")
            else:
                parts.append(f"Net bearish premium: ${abs(net_premium):,.0f}")
        
            # Max pain
            if max_pain:
                distance = (max_pain - spot_price) / spot_price * 100
                parts.append(f"Max pain: ${max_pain:.2f} ({distance:+.1f}% from spot)")
        
            # GEX
            total_gex = gex_result.get('total_gex', 0)
            parts.append(f"GEX: {gex_result.get('market_impact', 'Unknown')}")
        
            # Unusual activity
            if unusual:
                parts.append(f"Unusual activity: {len(unusual)} alerts")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        return {
            'symbols_tracked': len(self.contracts),
            'total_contracts': sum(len(c) for c in self.contracts.values()),
            'total_flows': sum(len(f) for f in self.flows.values()),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_options_analyzer(config: Optional[Dict] = None) -> OptionsFlowAnalyzer:
    """Create OptionsFlowAnalyzer instance."""
    return OptionsFlowAnalyzer(config)


# Example usage
if __name__ == "__main__":
    analyzer = create_options_analyzer()
    
    # Create sample data
    spot_price = 150.0
    
    # Add some call contracts
    for strike in [145, 150, 155, 160]:
        analyzer.add_contract(OptionContract(
            symbol=f"AAPL{strike}C",
            underlying="AAPL",
            option_type=OptionType.CALL,
            strike=strike,
            expiration=datetime.now() + timedelta(days=30),
            bid=5.0 if strike < spot_price else 2.0,
            ask=5.5 if strike < spot_price else 2.5,
            last=5.25 if strike < spot_price else 2.25,
            volume=1000 + (160 - strike) * 100,
            open_interest=5000,
            implied_volatility=0.25,
            delta=0.6 if strike < spot_price else 0.4,
            gamma=0.05
        ))
    
    # Add some put contracts
    for strike in [140, 145, 150, 155]:
        analyzer.add_contract(OptionContract(
            symbol=f"AAPL{strike}P",
            underlying="AAPL",
            option_type=OptionType.PUT,
            strike=strike,
            expiration=datetime.now() + timedelta(days=30),
            bid=2.0 if strike < spot_price else 5.0,
            ask=2.5 if strike < spot_price else 5.5,
            last=2.25 if strike < spot_price else 5.25,
            volume=800 + (strike - 140) * 50,
            open_interest=4000,
            implied_volatility=0.28,
            delta=-0.4 if strike < spot_price else -0.6,
            gamma=0.04
        ))
    
    # Analyze
    signal = analyzer.analyze("AAPL", spot_price)
    
    print("=" * 60)
    print("OPTIONS FLOW ANALYSIS")
    print("=" * 60)
    print(f"\nSymbol: {signal.symbol}")
    print(f"Signal: {signal.signal_type} ({signal.strength.name})")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"\nPut/Call Ratio: {signal.put_call_ratio:.2f}")
    print(f"Call Volume: {signal.total_call_volume:,}")
    print(f"Put Volume: {signal.total_put_volume:,}")
    print(f"Net Premium Flow: ${signal.net_premium_flow:,.0f}")
    print(f"Max Pain: ${signal.max_pain:.2f}")
    print(f"Gamma Exposure: {signal.gamma_exposure:,.0f}")
    print(f"\nKey Strikes: {signal.key_strikes}")
    print(f"\nAnalysis: {signal.analysis}")
