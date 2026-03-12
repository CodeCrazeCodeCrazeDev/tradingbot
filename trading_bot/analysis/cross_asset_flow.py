"""
Cross-Asset Information Flow Analysis

Correlates order flow events across key correlated assets to detect
when liquidity in one market is being pulled, predicting moves in another.

Features:
- Cross-asset correlation tracking
- Lead-lag relationship detection
- Liquidity flow mapping
- Predictive signal generation
- Multi-market regime detection
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AssetClass(Enum):
    """Asset classes."""
    FOREX = "forex"
    EQUITY_INDEX = "equity_index"
    COMMODITY = "commodity"
    BOND = "bond"
    CRYPTO = "crypto"


class FlowDirection(Enum):
    """Direction of capital flow."""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    ROTATION = "rotation"
    NEUTRAL = "neutral"


class LeadLagRelation(Enum):
    """Lead-lag relationship."""
    LEADING = "leading"
    LAGGING = "lagging"
    COINCIDENT = "coincident"
    INDEPENDENT = "independent"


@dataclass
class AssetData:
    """Data for a single asset."""
    symbol: str
    asset_class: AssetClass
    price: float
    volume: float
    bid_volume: float
    ask_volume: float
    timestamp: datetime
    
    @property
    def order_flow_imbalance(self) -> float:
        """Calculate order flow imbalance."""
        total = self.bid_volume + self.ask_volume
        if total > 0:
            return (self.bid_volume - self.ask_volume) / total
        return 0.0


@dataclass
class CorrelationPair:
    """Correlation between two assets."""
    asset1: str
    asset2: str
    correlation: float
    lead_lag: LeadLagRelation
    lead_bars: int  # Positive = asset1 leads, negative = asset2 leads
    strength: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset1': self.asset1,
            'asset2': self.asset2,
            'correlation': self.correlation,
            'lead_lag': self.lead_lag.value,
            'lead_bars': self.lead_bars,
            'strength': self.strength
        }


@dataclass
class LiquidityFlow:
    """Detected liquidity flow between assets."""
    timestamp: datetime
    source_asset: str
    target_asset: str
    flow_direction: FlowDirection
    magnitude: float
    confidence: float
    trigger_event: str
    expected_impact: Dict[str, float]  # asset -> expected move
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'source_asset': self.source_asset,
            'target_asset': self.target_asset,
            'flow_direction': self.flow_direction.value,
            'magnitude': self.magnitude,
            'confidence': self.confidence,
            'trigger_event': self.trigger_event,
            'expected_impact': self.expected_impact
        }


@dataclass
class CrossAssetSignal:
    """Trading signal from cross-asset analysis."""
    timestamp: datetime
    target_symbol: str
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float
    source_assets: List[str]
    flow_direction: FlowDirection
    correlation_support: float
    lead_lag_support: float
    expected_move_pct: float
    time_horizon_minutes: int
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'target_symbol': self.target_symbol,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'source_assets': self.source_assets,
            'flow_direction': self.flow_direction.value,
            'correlation_support': self.correlation_support,
            'lead_lag_support': self.lead_lag_support,
            'expected_move_pct': self.expected_move_pct,
            'time_horizon_minutes': self.time_horizon_minutes,
            'analysis': self.analysis
        }


# Default correlation groups
CORRELATION_GROUPS = {
    'USD_STRENGTH': {
        'positive': ['DXY', 'USDJPY'],
        'negative': ['EURUSD', 'GBPUSD', 'AUDUSD', 'GOLD', 'BTCUSD']
    },
    'RISK_SENTIMENT': {
        'risk_on': ['SPX', 'NDX', 'AUDJPY', 'BTCUSD'],
        'risk_off': ['GOLD', 'USDJPY', 'VIX', 'BONDS']
    },
    'COMMODITY_CURRENCIES': {
        'oil': ['USDCAD', 'CRUDE'],
        'gold': ['AUDUSD', 'GOLD'],
        'copper': ['AUDUSD', 'COPPER']
    }
}


class CorrelationTracker:
    """
    Tracks rolling correlations between assets.
    """
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=lookback))
        self.return_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=lookback))
    
    def add_price(self, symbol: str, price: float):
        """Add price for an asset."""
        history = self.price_history[symbol]
        
        # Calculate return
        if history:
            prev_price = history[-1]
            if prev_price > 0:
                ret = (price - prev_price) / prev_price
                self.return_history[symbol].append(ret)
        
        history.append(price)
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate correlation between two assets."""
        returns1 = list(self.return_history[symbol1])
        returns2 = list(self.return_history[symbol2])
        
        if len(returns1) < 10 or len(returns2) < 10:
            return None
        
        # Align lengths
        min_len = min(len(returns1), len(returns2))
        returns1 = returns1[-min_len:]
        returns2 = returns2[-min_len:]
        
        # Calculate correlation
        mean1 = statistics.mean(returns1)
        mean2 = statistics.mean(returns2)
        
        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2))
        
        std1 = statistics.stdev(returns1) if len(returns1) > 1 else 0
        std2 = statistics.stdev(returns2) if len(returns2) > 1 else 0
        
        if std1 > 0 and std2 > 0:
            correlation = numerator / (len(returns1) * std1 * std2)
            return max(-1, min(1, correlation))
        
        return 0.0


class LeadLagDetector:
    """
    Detects lead-lag relationships between assets.
    """
    
    def __init__(self, max_lag: int = 10):
        self.max_lag = max_lag
        self.return_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def add_return(self, symbol: str, ret: float):
        """Add return for an asset."""
        self.return_history[symbol].append(ret)
    
    def detect_lead_lag(self, symbol1: str, symbol2: str) -> Tuple[LeadLagRelation, int, float]:
        """
        Detect lead-lag relationship.
        
        Returns:
            Tuple of (relation, lag_bars, strength)
        """
        returns1 = list(self.return_history[symbol1])
        returns2 = list(self.return_history[symbol2])
        
        if len(returns1) < 20 or len(returns2) < 20:
            return LeadLagRelation.INDEPENDENT, 0, 0.0
        
        # Calculate cross-correlation at different lags
        best_corr = 0
        best_lag = 0
        
        for lag in range(-self.max_lag, self.max_lag + 1):
            corr = self._cross_correlation(returns1, returns2, lag)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
        
        # Determine relationship
        if abs(best_lag) <= 1:
            relation = LeadLagRelation.COINCIDENT
        elif best_lag > 0:
            relation = LeadLagRelation.LEADING  # symbol1 leads
        else:
            relation = LeadLagRelation.LAGGING  # symbol1 lags
        
        strength = abs(best_corr)
        
        return relation, best_lag, strength
    
    def _cross_correlation(self, series1: List[float], series2: List[float], lag: int) -> float:
        """Calculate cross-correlation at specific lag."""
        if lag >= 0:
            s1 = series1[lag:]
            s2 = series2[:len(series1) - lag]
        else:
            s1 = series1[:len(series1) + lag]
            s2 = series2[-lag:]
        
        if len(s1) < 5 or len(s2) < 5:
            return 0.0
        
        min_len = min(len(s1), len(s2))
        s1 = s1[:min_len]
        s2 = s2[:min_len]
        
        mean1 = statistics.mean(s1)
        mean2 = statistics.mean(s2)
        
        numerator = sum((a - mean1) * (b - mean2) for a, b in zip(s1, s2))
        
        std1 = statistics.stdev(s1) if len(s1) > 1 else 0
        std2 = statistics.stdev(s2) if len(s2) > 1 else 0
        
        if std1 > 0 and std2 > 0:
            return numerator / (len(s1) * std1 * std2)
        
        return 0.0


class FlowDetector:
    """
    Detects capital flows between assets.
    """
    
    def __init__(self):
        self.flow_history: deque = deque(maxlen=100)
        self.imbalance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
    
    def add_imbalance(self, symbol: str, imbalance: float):
        """Add order flow imbalance."""
        self.imbalance_history[symbol].append(imbalance)
    
    def detect_flow(
        self,
        source: str,
        target: str,
        source_imbalance: float,
        target_imbalance: float
    ) -> Optional[LiquidityFlow]:
        """Detect liquidity flow between assets."""
        # Check for divergent imbalances (flow from source to target)
        if source_imbalance < -0.3 and target_imbalance > 0.3:
            # Selling source, buying target
            return LiquidityFlow(
                timestamp=datetime.now(),
                source_asset=source,
                target_asset=target,
                flow_direction=FlowDirection.ROTATION,
                magnitude=abs(source_imbalance) + abs(target_imbalance),
                confidence=min(0.9, (abs(source_imbalance) + abs(target_imbalance)) / 2),
                trigger_event=f"Rotation from {source} to {target}",
                expected_impact={
                    source: -abs(source_imbalance) * 0.5,
                    target: abs(target_imbalance) * 0.5
                }
            )
        
        return None


class CrossAssetFlowAnalyzer:
    """
    Main cross-asset information flow analyzer.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.correlation_tracker = CorrelationTracker(
            lookback=self.config.get('correlation_lookback', 50)
        )
        self.lead_lag_detector = LeadLagDetector(
            max_lag=self.config.get('max_lag', 10)
        )
        self.flow_detector = FlowDetector()
        
        # Asset registry
        self.assets: Dict[str, AssetClass] = {}
        self.correlation_groups = CORRELATION_GROUPS
        
        # Data storage
        self.latest_data: Dict[str, AssetData] = {}
        self.correlations: Dict[Tuple[str, str], CorrelationPair] = {}
        self.flows: deque = deque(maxlen=100)
        self.signals: deque = deque(maxlen=100)
        
        logger.info("CrossAssetFlowAnalyzer initialized")
    
    def register_asset(self, symbol: str, asset_class: AssetClass):
        """Register an asset for tracking."""
        self.assets[symbol] = asset_class
    
    def update(self, data: AssetData):
        """
        Update with new asset data.
        
        Args:
            data: AssetData for an asset
        """
        symbol = data.symbol
        
        # Register if new
        if symbol not in self.assets:
            self.assets[symbol] = data.asset_class
        
        # Update trackers
        self.correlation_tracker.add_price(symbol, data.price)
        
        # Calculate return for lead-lag
        if symbol in self.latest_data:
            prev_price = self.latest_data[symbol].price
            if prev_price > 0:
                ret = (data.price - prev_price) / prev_price
                self.lead_lag_detector.add_return(symbol, ret)
        
        # Update flow detector
        self.flow_detector.add_imbalance(symbol, data.order_flow_imbalance)
        
        # Store latest
        self.latest_data[symbol] = data
    
    def update_correlations(self):
        """Update all correlation pairs."""
        symbols = list(self.assets.keys())
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self.correlation_tracker.get_correlation(sym1, sym2)
                
                if corr is not None:
                    # Get lead-lag
                    relation, lag, strength = self.lead_lag_detector.detect_lead_lag(sym1, sym2)
                    
                    pair = CorrelationPair(
                        asset1=sym1,
                        asset2=sym2,
                        correlation=corr,
                        lead_lag=relation,
                        lead_bars=lag,
                        strength=strength
                    )
                    
                    self.correlations[(sym1, sym2)] = pair
    
    def detect_flows(self) -> List[LiquidityFlow]:
        """Detect liquidity flows between assets."""
        detected_flows = []
        
        symbols = list(self.latest_data.keys())
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                data1 = self.latest_data[sym1]
                data2 = self.latest_data[sym2]
                
                flow = self.flow_detector.detect_flow(
                    sym1, sym2,
                    data1.order_flow_imbalance,
                    data2.order_flow_imbalance
                )
                
                if flow:
                    detected_flows.append(flow)
                    self.flows.append(flow)
        
        return detected_flows
    
    def generate_signal(self, target_symbol: str) -> Optional[CrossAssetSignal]:
        """
        Generate trading signal for target asset based on cross-asset analysis.
        
        Args:
            target_symbol: Symbol to generate signal for
            
        Returns:
            CrossAssetSignal if conditions met
        """
        if target_symbol not in self.latest_data:
            return None
        
        # Find correlated assets
        correlated = self._find_correlated_assets(target_symbol)
        
        if not correlated:
            return None
        
        # Analyze leading indicators
        leading_signals = []
        
        for sym, pair in correlated:
            if pair.lead_lag == LeadLagRelation.LEADING and pair.lead_bars > 0:
                # This asset leads our target
                if sym in self.latest_data:
                    data = self.latest_data[sym]
                    
                    # Check order flow
                    if data.order_flow_imbalance > 0.3:
                        if pair.correlation > 0:
                            leading_signals.append(('BUY', pair.strength, sym))
                        else:
                            leading_signals.append(('SELL', pair.strength, sym))
                    elif data.order_flow_imbalance < -0.3:
                        if pair.correlation > 0:
                            leading_signals.append(('SELL', pair.strength, sym))
                        else:
                            leading_signals.append(('BUY', pair.strength, sym))
        
        if not leading_signals:
            return None
        
        # Aggregate signals
        buy_strength = sum(s[1] for s in leading_signals if s[0] == 'BUY')
        sell_strength = sum(s[1] for s in leading_signals if s[0] == 'SELL')
        
        if buy_strength > sell_strength and buy_strength > 0.5:
            signal_type = 'BUY'
            confidence = min(0.9, buy_strength / (buy_strength + sell_strength + 0.1))
        elif sell_strength > buy_strength and sell_strength > 0.5:
            signal_type = 'SELL'
            confidence = min(0.9, sell_strength / (buy_strength + sell_strength + 0.1))
        else:
            return None
        
        # Determine flow direction
        flow_direction = self._determine_flow_direction()
        
        # Calculate expected move
        avg_correlation = statistics.mean(abs(p.correlation) for _, p in correlated)
        expected_move = avg_correlation * 0.5  # Percentage
        
        # Time horizon based on lead-lag
        avg_lag = statistics.mean(abs(p.lead_bars) for _, p in correlated if p.lead_bars != 0) if correlated else 5
        time_horizon = int(avg_lag * 5)  # 5 minutes per bar
        
        # Generate analysis
        analysis = self._generate_analysis(
            target_symbol, signal_type, leading_signals, correlated
        )
        
        signal = CrossAssetSignal(
            timestamp=datetime.now(),
            target_symbol=target_symbol,
            signal_type=signal_type,
            confidence=confidence,
            source_assets=[s[2] for s in leading_signals],
            flow_direction=flow_direction,
            correlation_support=avg_correlation,
            lead_lag_support=len(leading_signals) / len(correlated) if correlated else 0,
            expected_move_pct=expected_move,
            time_horizon_minutes=time_horizon,
            analysis=analysis
        )
        
        self.signals.append(signal)
        return signal
    
    def _find_correlated_assets(
        self,
        symbol: str,
        min_correlation: float = 0.3
    ) -> List[Tuple[str, CorrelationPair]]:
        """Find assets correlated with target."""
        correlated = []
        
        for (sym1, sym2), pair in self.correlations.items():
            if sym1 == symbol:
                if abs(pair.correlation) >= min_correlation:
                    correlated.append((sym2, pair))
            elif sym2 == symbol:
                if abs(pair.correlation) >= min_correlation:
                    # Flip the pair perspective
                    flipped = CorrelationPair(
                        asset1=sym2,
                        asset2=sym1,
                        correlation=pair.correlation,
                        lead_lag=LeadLagRelation.LAGGING if pair.lead_lag == LeadLagRelation.LEADING else LeadLagRelation.LEADING,
                        lead_bars=-pair.lead_bars,
                        strength=pair.strength
                    )
                    correlated.append((sym1, flipped))
        
        return correlated
    
    def _determine_flow_direction(self) -> FlowDirection:
        """Determine overall market flow direction."""
        if not self.latest_data:
            return FlowDirection.NEUTRAL
        
        # Check risk assets
        risk_on_imbalance = 0
        risk_off_imbalance = 0
        
        for symbol, data in self.latest_data.items():
            if symbol in ['SPX', 'NDX', 'BTCUSD']:
                risk_on_imbalance += data.order_flow_imbalance
            elif symbol in ['GOLD', 'VIX', 'BONDS']:
                risk_off_imbalance += data.order_flow_imbalance
        
        if risk_on_imbalance > 0.5 and risk_off_imbalance < -0.3:
            return FlowDirection.RISK_ON
        elif risk_off_imbalance > 0.5 and risk_on_imbalance < -0.3:
            return FlowDirection.RISK_OFF
        elif abs(risk_on_imbalance - risk_off_imbalance) > 0.5:
            return FlowDirection.ROTATION
        
        return FlowDirection.NEUTRAL
    
    def _generate_analysis(
        self,
        target: str,
        signal_type: str,
        leading_signals: List[Tuple[str, float, str]],
        correlated: List[Tuple[str, CorrelationPair]]
    ) -> str:
        """Generate analysis text."""
        parts = []
        
        parts.append(f"{signal_type} signal for {target}")
        parts.append(f"Based on {len(leading_signals)} leading indicators")
        
        # Top contributors
        top_sources = sorted(leading_signals, key=lambda x: x[1], reverse=True)[:3]
        sources_str = ", ".join(s[2] for s in top_sources)
        parts.append(f"Key sources: {sources_str}")
        
        # Correlation context
        avg_corr = statistics.mean(abs(p.correlation) for _, p in correlated)
        parts.append(f"Avg correlation: {avg_corr:.2f}")
        
        return " | ".join(parts)
    
    def get_market_regime(self) -> Dict[str, Any]:
        """Get current market regime from cross-asset analysis."""
        flow_direction = self._determine_flow_direction()
        
        # Calculate regime metrics
        correlations_list = list(self.correlations.values())
        
        if correlations_list:
            avg_correlation = statistics.mean(abs(p.correlation) for p in correlations_list)
            correlation_dispersion = statistics.stdev([p.correlation for p in correlations_list]) if len(correlations_list) > 1 else 0
        else:
            avg_correlation = 0
            correlation_dispersion = 0
        
        return {
            'flow_direction': flow_direction.value,
            'avg_correlation': avg_correlation,
            'correlation_dispersion': correlation_dispersion,
            'regime': 'HIGH_CORRELATION' if avg_correlation > 0.6 else 'LOW_CORRELATION',
            'assets_tracked': len(self.assets),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        return {
            'assets_tracked': len(self.assets),
            'correlation_pairs': len(self.correlations),
            'recent_flows': len(self.flows),
            'recent_signals': len(self.signals),
            'market_regime': self.get_market_regime(),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_cross_asset_analyzer(config: Optional[Dict] = None) -> CrossAssetFlowAnalyzer:
    """Create CrossAssetFlowAnalyzer instance."""
    return CrossAssetFlowAnalyzer(config)


# Example usage
if __name__ == "__main__":
    import random
    
    analyzer = create_cross_asset_analyzer()
    
    # Register assets
    assets = [
        ('EURUSD', AssetClass.FOREX),
        ('DXY', AssetClass.FOREX),
        ('SPX', AssetClass.EQUITY_INDEX),
        ('GOLD', AssetClass.COMMODITY),
        ('BTCUSD', AssetClass.CRYPTO),
    ]
    
    for symbol, asset_class in assets:
        analyzer.register_asset(symbol, asset_class)
    
    print("=" * 60)
    print("CROSS-ASSET INFORMATION FLOW ANALYSIS")
    print("=" * 60)
    
    # Simulate data
    print("\nSimulating cross-asset data...")
    
    base_prices = {
        'EURUSD': 1.1000,
        'DXY': 103.0,
        'SPX': 4500.0,
        'GOLD': 1950.0,
        'BTCUSD': 42000.0
    }
    
    for i in range(50):
        # Simulate correlated moves
        # DXY up -> EURUSD down, GOLD down
        dxy_move = random.uniform(-0.002, 0.002)
        
        for symbol, asset_class in assets:
            base = base_prices[symbol]
            
            # Apply correlation
            if symbol == 'DXY':
                price = base * (1 + dxy_move * (i + 1))
            elif symbol == 'EURUSD':
                price = base * (1 - dxy_move * 0.8 * (i + 1))  # Negative correlation
            elif symbol == 'GOLD':
                price = base * (1 - dxy_move * 0.5 * (i + 1))  # Negative correlation
            elif symbol == 'SPX':
                price = base * (1 + random.uniform(-0.001, 0.002) * (i + 1))
            else:
                price = base * (1 + random.uniform(-0.003, 0.003) * (i + 1))
            
            # Random imbalance (with some correlation to price move)
            imbalance = dxy_move * 100 + random.uniform(-0.3, 0.3)
            
            data = AssetData(
                symbol=symbol,
                asset_class=asset_class,
                price=price,
                volume=random.randint(10000, 100000),
                bid_volume=random.randint(5000, 50000) * (1 + imbalance),
                ask_volume=random.randint(5000, 50000) * (1 - imbalance),
                timestamp=datetime.now()
            )
            
            analyzer.update(data)
    
    # Update correlations
    analyzer.update_correlations()
    
    # Show correlations
    print("\n" + "=" * 60)
    print("CORRELATIONS")
    print("=" * 60)
    
    for (sym1, sym2), pair in analyzer.correlations.items():
        print(f"\n{sym1} vs {sym2}:")
        print(f"  Correlation: {pair.correlation:.3f}")
        print(f"  Lead-Lag: {pair.lead_lag.value} ({pair.lead_bars} bars)")
        print(f"  Strength: {pair.strength:.2f}")
    
    # Detect flows
    print("\n" + "=" * 60)
    print("LIQUIDITY FLOWS")
    print("=" * 60)
    
    flows = analyzer.detect_flows()
    for flow in flows:
        print(f"\n{flow.source_asset} -> {flow.target_asset}")
        print(f"  Direction: {flow.flow_direction.value}")
        print(f"  Magnitude: {flow.magnitude:.2f}")
        print(f"  Confidence: {flow.confidence:.0%}")
    
    # Generate signal
    print("\n" + "=" * 60)
    print("TRADING SIGNAL")
    print("=" * 60)
    
    signal = analyzer.generate_signal('EURUSD')
    
    if signal:
        print(f"\nTarget: {signal.target_symbol}")
        print(f"Signal: {signal.signal_type}")
        print(f"Confidence: {signal.confidence:.0%}")
        print(f"Source Assets: {', '.join(signal.source_assets)}")
        print(f"Flow Direction: {signal.flow_direction.value}")
        print(f"Expected Move: {signal.expected_move_pct:.2f}%")
        print(f"Time Horizon: {signal.time_horizon_minutes} minutes")
        print(f"\nAnalysis: {signal.analysis}")
    else:
        print("\nNo signal generated")
    
    # Market regime
    print("\n" + "=" * 60)
    print("MARKET REGIME")
    print("=" * 60)
    
    regime = analyzer.get_market_regime()
    for key, value in regime.items():
        print(f"{key}: {value}")
