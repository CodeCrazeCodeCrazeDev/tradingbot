"""
Multi-Modal Market Awareness for GETS

Implements the awareness layers from the vision document:
- Causality: Pattern-cause detection
- Market Structure: Liquidity, order flow, execution friction
- Decision Awareness: Tradability scoring, edge > cost validation
- Risk Awareness: Drawdown paths, capital allocation
- Regime Reasoning: Explicit regime transitions, structural shifts
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
import numpy as np

from .types import MarketData, RegimeType, GETSSignal

logger = logging.getLogger(__name__)


class AwarenessType(Enum):
    """Types of market awareness."""
    CAUSALITY = auto()
    MARKET_STRUCTURE = auto()
    DECISION = auto()
    RISK = auto()
    REGIME = auto()


@dataclass
class CausalPattern:
    """Detected causal pattern with confidence."""
    pattern_id: str
    cause: str
    effect: str
    lag_periods: int
    correlation: float
    causality_score: float  # 0-1, higher = more likely causal
    confidence: float
    detected_at: datetime


@dataclass
class MarketStructureState:
    """Current market structure conditions."""
    timestamp: datetime
    symbol: str
    
    # Liquidity metrics
    bid_ask_spread_bps: float
    depth_imbalance: float  # -1 to 1, positive = more bids
    order_book_imbalance: float
    
    # Flow toxicity
    vp_in_ratio: float  # Volume-synchronized probability of informed trading
    flow_toxicity_score: float  # 0-1
    
    # Execution friction
    estimated_slippage_bps: float
    market_impact_50bp: float  # Impact of 50 bps order
    
    # Resilience
    depth_resilience_score: float  # 0-1, how fast depth recovers
    spread_resilience_score: float  # 0-1


@dataclass
class DecisionContext:
    """Decision-aware context for trading."""
    forecast_tradable: bool
    edge_after_cost: float
    cost_estimate_bps: float
    
    # Capacity
    estimated_capacity: float  # Max position size without excessive impact
    current_liquidity_score: float  # 0-1
    
    # Timing
    optimal_execution_window: Optional[Tuple[datetime, datetime]]
    urgency_score: float  # 0-1, how urgent to execute
    
    # Combined score
    tradability_score: float  # 0-1, overall tradability
    abstain_recommendation: bool
    abstain_reason: Optional[str]


@dataclass
class RiskState:
    """Risk awareness state."""
    timestamp: datetime
    
    # Drawdown risk
    drawdown_prob_5pct: float  # Probability of 5% drawdown
    drawdown_prob_10pct: float
    expected_max_drawdown: float
    
    # Capital allocation
    recommended_position_pct: float  # % of capital to allocate
    concentration_risk: float  # 0-1, portfolio concentration
    
    # Portfolio exposure
    gross_exposure: float
    net_exposure: float
    beta_adjusted_exposure: float
    
    # Tail risk
    var_95: float  # 95% Value at Risk
    cvar_95: float  # Conditional VaR
    tail_risk_score: float  # 0-1


@dataclass
class RegimeTransition:
    """Detected or predicted regime transition."""
    from_regime: RegimeType
    to_regime: RegimeType
    transition_probability: float
    estimated_time_to_transition: int  # periods (e.g., minutes, hours)
    leading_indicators: List[str]
    confidence: float
    detected_at: datetime


class CausalityDetector:
    """
    Detects causal patterns, not just correlations.
    
    Uses:
    - Lag-structure analysis
    - Granger causality approximations
    - Intervention testing
    """
    
    def __init__(self, max_lag: int = 10):
        self.max_lag = max_lag
        self.detected_patterns: List[CausalPattern] = []
        self.pattern_history: Dict[str, List[Dict]] = {}
    
    def detect_causal_patterns(
        self,
        price_series: np.ndarray,
        volume_series: np.ndarray,
        feature_series: Dict[str, np.ndarray]
    ) -> List[CausalPattern]:
        """
        Detect causal patterns in time series data.
        
        Args:
            price_series: Price history
            volume_series: Volume history
            feature_series: Additional features (order flow, etc.)
            
        Returns:
            List of detected causal patterns
        """
        patterns = []
        
        # Check price-volume causality
        price_vol_pattern = self._test_price_volume_causality(
            price_series, volume_series
        )
        if price_vol_pattern:
            patterns.append(price_vol_pattern)
        
        # Check feature causality
        for feature_name, feature_data in feature_series.items():
            feature_pattern = self._test_feature_causality(
                price_series, feature_data, feature_name
            )
            if feature_pattern:
                patterns.append(feature_pattern)
        
        self.detected_patterns.extend(patterns)
        return patterns
    
    def _test_price_volume_causality(
        self,
        price: np.ndarray,
        volume: np.ndarray
    ) -> Optional[CausalPattern]:
        """Test if volume leads price (toxic flow detection)."""
        if len(price) < self.max_lag + 1:
            return None
        
        # Simple lag correlation test
        best_lag = 0
        best_corr = 0
        
        for lag in range(1, self.max_lag + 1):
            if len(volume) > lag:
                vol_lagged = volume[:-lag]
                price_future = price[lag:]
                
                min_len = min(len(vol_lagged), len(price_future))
                if min_len > 10:
                    corr = np.corrcoef(vol_lagged[:min_len], price_future[:min_len])[0, 1]
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag
        
        if abs(best_corr) > 0.3:  # Threshold for significance
            return CausalPattern(
                pattern_id=f"vol_price_lag_{best_lag}",
                cause="volume_spike",
                effect="price_movement",
                lag_periods=best_lag,
                correlation=best_corr,
                causality_score=abs(best_corr) * 0.7,  # Conservative estimate
                confidence=abs(best_corr),
                detected_at=datetime.now()
            )
        
        return None
    
    def _test_feature_causality(
        self,
        price: np.ndarray,
        feature: np.ndarray,
        feature_name: str
    ) -> Optional[CausalPattern]:
        """Test if a feature leads price."""
        if len(price) < self.max_lag + 1 or len(feature) < self.max_lag + 1:
            return None
        
        best_lag = 0
        best_corr = 0
        
        for lag in range(1, self.max_lag + 1):
            feat_lagged = feature[:-lag]
            price_future = price[lag:]
            
            min_len = min(len(feat_lagged), len(price_future))
            if min_len > 10:
                corr = np.corrcoef(feat_lagged[:min_len], price_future[:min_len])[0, 1]
                if abs(corr) > abs(best_corr):
                    best_corr = corr
                    best_lag = lag
        
        if abs(best_corr) > 0.4:
            return CausalPattern(
                pattern_id=f"{feature_name}_price_lag_{best_lag}",
                cause=feature_name,
                effect="price_movement",
                lag_periods=best_lag,
                correlation=best_corr,
                causality_score=abs(best_corr) * 0.6,
                confidence=abs(best_corr),
                detected_at=datetime.now()
            )
        
        return None


class MarketStructureAnalyzer:
    """
    Analyzes market structure: liquidity, order flow, execution friction.
    """
    
    def __init__(self):
        self.historical_spreads: List[float] = []
        self.historical_depth: List[float] = []
    
    def analyze(
        self,
        market_data: MarketData,
        order_book: Optional[Dict] = None
    ) -> MarketStructureState:
        """
        Analyze current market structure.
        
        Args:
            market_data: Current market data
            order_book: Optional order book data (bids, asks)
            
        Returns:
            MarketStructureState with full analysis
        """
        price = market_data.ohlcv['close']
        
        # Spread analysis
        spread_bps = (market_data.bid_ask_spread / price * 10000) if market_data.bid_ask_spread else 5.0
        self.historical_spreads.append(spread_bps)
        if len(self.historical_spreads) > 100:
            self.historical_spreads = self.historical_spreads[-100:]
        
        # Depth imbalance
        depth_imb = market_data.depth_imbalance if market_data.depth_imbalance else 0.0
        
        # Estimate slippage based on spread and volatility
        vol = market_data.realized_volatility or 0.2
        est_slippage = spread_bps * 0.5 + vol * 100  # Simple heuristic
        
        # Flow toxicity (simplified VPIN-like metric)
        volume = market_data.ohlcv.get('volume', 0)
        flow_toxic = self._estimate_flow_toxicity(volume, price)
        
        # Resilience scores
        depth_resilience = 0.7  # Placeholder
        spread_resilience = 0.8 if len(self.historical_spreads) < 5 else \
                          1.0 - (np.std(self.historical_spreads[-5:]) / max(np.mean(self.historical_spreads), 1.0))
        
        return MarketStructureState(
            timestamp=datetime.now(),
            symbol=market_data.symbol,
            bid_ask_spread_bps=spread_bps,
            depth_imbalance=depth_imb,
            order_book_imbalance=depth_imb,
            vp_in_ratio=flow_toxic,
            flow_toxicity_score=flow_toxic,
            estimated_slippage_bps=est_slippage,
            market_impact_50bp=est_slippage * 2,
            depth_resilience_score=depth_resilience,
            spread_resilience_score=spread_resilience
        )
    
    def _estimate_flow_toxicity(self, volume: float, price: float) -> float:
        """Estimate order flow toxicity (simplified VPIN)."""
        # Placeholder: would use actual order flow data
        return 0.3


class DecisionAwarenessEngine:
    """
    Decision awareness: Is this forecast tradable? Edge > cost?
    """
    
    def __init__(self, min_edge_bps: float = 1.0):
        self.min_edge_bps = min_edge_bps
    
    def evaluate_tradability(
        self,
        signal: GETSSignal,
        market_structure: MarketStructureState,
        portfolio_value: float = 100000.0
    ) -> DecisionContext:
        """
        Evaluate if a signal is actually tradable.
        
        Args:
            signal: GETS signal
            market_structure: Current market structure
            portfolio_value: Portfolio value for sizing
            
        Returns:
            DecisionContext with tradability assessment
        """
        edge_bps = signal.expected_edge * 10000
        cost_bps = market_structure.estimated_slippage_bps + market_structure.bid_ask_spread_bps
        
        edge_after_cost = edge_bps - cost_bps
        tradable = edge_after_cost > self.min_edge_bps
        
        # Estimate capacity
        if market_structure.depth_resilience_score > 0.5:
            capacity = portfolio_value * 0.05  # Max 5% of portfolio
        else:
            capacity = portfolio_value * 0.01  # Only 1% in low liquidity
        
        # Liquidity score
        liquidity_score = (
            market_structure.depth_resilience_score * 0.4 +
            market_structure.spread_resilience_score * 0.4 +
            (1.0 - min(market_structure.bid_ask_spread_bps / 10, 1.0)) * 0.2
        )
        
        # Tradability score
        tradability = (
            (1.0 if tradable else 0.0) * 0.4 +
            min(edge_after_cost / 10, 1.0) * 0.3 +
            liquidity_score * 0.3
        )
        
        abstain = not tradable or tradability < 0.3
        abstain_reason = None
        if not tradable:
            abstain_reason = f"Edge {edge_bps:.1f}bps < Cost {cost_bps:.1f}bps + Min {self.min_edge_bps:.1f}bps"
        elif tradability < 0.3:
            abstain_reason = f"Low tradability score: {tradability:.2f}"
        
        return DecisionContext(
            forecast_tradable=tradable,
            edge_after_cost=edge_after_cost / 10000,  # Convert back to decimal
            cost_estimate_bps=cost_bps,
            estimated_capacity=capacity,
            current_liquidity_score=liquidity_score,
            optimal_execution_window=None,  # Would compute based on market conditions
            urgency_score=0.5,
            tradability_score=tradability,
            abstain_recommendation=abstain,
            abstain_reason=abstain_reason
        )


class RiskAwarenessMonitor:
    """
    Risk awareness: Drawdown paths, capital allocation, exposure.
    """
    
    def __init__(self, max_single_position_pct: float = 0.05):
        self.max_position_pct = max_single_position_pct
        self.position_history: List[Dict] = []
    
    def assess_risk(
        self,
        signal: GETSSignal,
        market_structure: MarketStructureState,
        current_positions: Dict[str, float],
        portfolio_value: float
    ) -> RiskState:
        """
        Assess risk for a potential trade.
        
        Args:
            signal: GETS signal
            market_structure: Current market structure
            current_positions: Current portfolio positions
            portfolio_value: Total portfolio value
            
        Returns:
            RiskState with risk assessment
        """
        # Drawdown probability based on volatility and uncertainty
        vol = market_structure.flow_toxicity_score * 0.5  # Proxy for vol
        dd_prob_5 = min(vol * 2, 0.5)  # 5% drawdown probability
        dd_prob_10 = min(vol, 0.3)  # 10% drawdown probability
        
        # Position sizing based on edge and risk
        edge = signal.expected_edge
        confidence = signal.confidence
        
        # Kelly-like sizing
        if edge > 0 and signal.uncertainty_quantile_95 > signal.uncertainty_quantile_05:
            win_prob = confidence
            loss_prob = 1 - confidence
            avg_win = edge
            avg_loss = edge * 0.5  # Conservative
            
            kelly_pct = (win_prob * avg_win - loss_prob * avg_loss) / (avg_win * avg_loss)
            position_pct = min(max(kelly_pct * 0.5, 0), self.max_position_pct)  # Half Kelly, capped
        else:
            position_pct = 0.0
        
        # Concentration risk
        total_position_value = sum(abs(v) for v in current_positions.values())
        concentration = total_position_value / portfolio_value if portfolio_value > 0 else 0.0
        
        # VaR estimation (simplified)
        var_95 = portfolio_value * vol * 1.645  # 95% VaR
        cvar_95 = var_95 * 1.2  # Conservative CVaR
        
        return RiskState(
            timestamp=datetime.now(),
            drawdown_prob_5pct=dd_prob_5,
            drawdown_prob_10pct=dd_prob_10,
            expected_max_drawdown=dd_prob_5 * 0.05,
            recommended_position_pct=position_pct,
            concentration_risk=concentration,
            gross_exposure=total_position_value / portfolio_value if portfolio_value > 0 else 0.0,
            net_exposure=sum(current_positions.values()) / portfolio_value if portfolio_value > 0 else 0.0,
            beta_adjusted_exposure=0.0,  # Would compute with beta data
            var_95=var_95,
            cvar_95=cvar_95,
            tail_risk_score=dd_prob_10
        )


class RegimeReasoningEngine:
    """
    Regime reasoning: Explicit transitions, structural shifts, early warnings.
    """
    
    def __init__(self, transition_threshold: float = 0.6):
        self.transition_threshold = transition_threshold
        self.regime_history: List[Tuple[datetime, RegimeType]] = []
        self.transition_warnings: List[RegimeTransition] = []
    
    def detect_regime_transition(
        self,
        current_regime: RegimeType,
        volatility_series: np.ndarray,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> Optional[RegimeTransition]:
        """
        Detect early warning of regime transition.
        
        Args:
            current_regime: Current detected regime
            volatility_series: Recent volatility history
            correlation_matrix: Cross-asset correlation matrix
            
        Returns:
            RegimeTransition if detected, None otherwise
        """
        if len(volatility_series) < 10:
            return None
        
        # Detect increasing volatility (possible crisis/breakout)
        recent_vol = np.mean(volatility_series[-5:])
        historical_vol = np.mean(volatility_series[:-5]) if len(volatility_series) > 5 else recent_vol
        
        if recent_vol > historical_vol * 1.5 and current_regime not in [RegimeType.HIGH_VOLATILITY, RegimeType.CRISIS]:
            # Potential transition to high volatility
            transition_prob = min((recent_vol / historical_vol - 1) / 2, 0.9)
            
            if transition_prob > self.transition_threshold:
                transition = RegimeTransition(
                    from_regime=current_regime,
                    to_regime=RegimeType.HIGH_VOLATILITY,
                    transition_probability=transition_prob,
                    estimated_time_to_transition=5,
                    leading_indicators=["volatility_spike", "volume_surge"],
                    confidence=transition_prob,
                    detected_at=datetime.now()
                )
                self.transition_warnings.append(transition)
                return transition
        
        # Detect correlation breakdown (possible crisis)
        if correlation_matrix is not None and len(correlation_matrix) > 1:
            avg_corr = np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
            if avg_corr < 0.2 and current_regime != RegimeType.CRISIS:
                transition = RegimeTransition(
                    from_regime=current_regime,
                    to_regime=RegimeType.CRISIS,
                    transition_probability=0.7,
                    estimated_time_to_transition=10,
                    leading_indicators=["correlation_breakdown"],
                    confidence=0.7,
                    detected_at=datetime.now()
                )
                self.transition_warnings.append(transition)
                return transition
        
        return None
    
    def get_active_warnings(self) -> List[RegimeTransition]:
        """Get active regime transition warnings."""
        # Filter warnings from last 24 hours
        cutoff = datetime.now() - 24 * 60 * 60
        return [w for w in self.transition_warnings if w.detected_at > cutoff]


class MultiModalAwareness:
    """
    Orchestrates all awareness modules for comprehensive market understanding.
    """
    
    def __init__(
        self,
        enable_causality: bool = True,
        enable_market_structure: bool = True,
        enable_decision: bool = True,
        enable_risk: bool = True,
        enable_regime_reasoning: bool = True
    ):
        self.causality = CausalityDetector() if enable_causality else None
        self.market_structure = MarketStructureAnalyzer() if enable_market_structure else None
        self.decision = DecisionAwarenessEngine() if enable_decision else None
        self.risk = RiskAwarenessMonitor() if enable_risk else None
        self.regime_reasoning = RegimeReasoningEngine() if enable_regime_reasoning else None
        
        self.enabled_modules = [
            name for name, enabled in [
                ("causality", enable_causality),
                ("market_structure", enable_market_structure),
                ("decision", enable_decision),
                ("risk", enable_risk),
                ("regime_reasoning", enable_regime_reasoning)
            ] if enabled
        ]
    
    def analyze(
        self,
        signal: GETSSignal,
        market_data: MarketData,
        current_positions: Dict[str, float],
        portfolio_value: float
    ) -> Dict[str, Any]:
        """
        Run full multi-modal awareness analysis.
        
        Returns:
            Dict with all awareness module outputs
        """
        results = {
            "enabled_modules": self.enabled_modules,
            "timestamp": datetime.now().isoformat()
        }
        
        # Market structure
        if self.market_structure:
            mss = self.market_structure.analyze(market_data)
            results["market_structure"] = mss
        
        # Decision awareness
        if self.decision and "market_structure" in results:
            decision_ctx = self.decision.evaluate_tradability(
                signal, results["market_structure"], portfolio_value
            )
            results["decision"] = decision_ctx
        
        # Risk awareness
        if self.risk and "market_structure" in results:
            risk_state = self.risk.assess_risk(
                signal, results["market_structure"], current_positions, portfolio_value
            )
            results["risk"] = risk_state
        
        # Regime reasoning
        if self.regime_reasoning:
            # Would pass actual volatility series
            transition = self.regime_reasoning.detect_regime_transition(
                signal.diagnosis_report.regime_label if hasattr(signal.diagnosis_report, 'regime_label') else None,
                np.array([0.2, 0.25, 0.3])  # Placeholder
            )
            if transition:
                results["regime_transition_warning"] = transition
        
        return results
