"""
Unified Market Hostility Gate - Stage 0 Fix

Addresses violations:
- No unified market hostility gate
- No cross-strategy performance dispersion
- No liquidity stress aggregation
- No edge density calculation

This module provides a SINGLE entry point that blocks ALL trading
when market conditions are hostile.

Author: AlphaAlgo Core
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class HostilityLevel(Enum):
    """Market hostility levels"""
    BENIGN = "benign"
    CAUTIOUS = "cautious"
    HOSTILE = "hostile"
    EXTREME = "extreme"
    LOW_EDGE_DENSITY = "low_edge_density"


@dataclass
class StrategyPerformance:
    """Performance data for a single strategy"""
    strategy_id: str
    recent_returns: List[float]
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    timestamp: datetime


@dataclass
class LiquiditySnapshot:
    """Liquidity data for a symbol"""
    symbol: str
    bid_ask_spread: float
    order_book_depth: float
    volume_24h: float
    slippage_estimate: float
    timestamp: datetime


@dataclass
class HostilityAssessment:
    """Complete hostility assessment"""
    level: HostilityLevel
    can_trade: bool
    cross_strategy_dispersion: float
    liquidity_stress: float
    edge_density: float
    regime_instability: float
    drawdown_clustering: float
    dominant_reason: str
    timestamp: datetime
    details: Dict[str, float]


class CrossStrategyDispersionTracker:
    """
    Tracks performance dispersion across strategies.
    High dispersion = strategies disagree = market hostile.
    """
    
    def __init__(self, window_size: int = 50):
        try:
            self.window_size = window_size
            self.strategy_performances: Dict[str, deque] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, strategy_id: str, return_value: float):
        """Update strategy performance"""
        try:
            if strategy_id not in self.strategy_performances:
                self.strategy_performances[strategy_id] = deque(maxlen=self.window_size)
        
            self.strategy_performances[strategy_id].append(return_value)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_dispersion(self) -> float:
        """
        Calculate cross-strategy dispersion.
        
        Returns:
            0.0 = All strategies agree (low dispersion)
            1.0 = Strategies completely disagree (high dispersion)
        """
        try:
            if len(self.strategy_performances) < 2:
                return 0.0
        
            # Get recent mean returns for each strategy
            strategy_means = []
            for strategy_id, returns in self.strategy_performances.items():
                if len(returns) >= 10:  # Minimum sample size
                    strategy_means.append(np.mean(list(returns)))
        
            if len(strategy_means) < 2:
                return 0.0
        
            # Calculate coefficient of variation (std / mean)
            # High CV = high dispersion
            mean_of_means = np.mean(strategy_means)
            std_of_means = np.std(strategy_means)
        
            if abs(mean_of_means) < 1e-6:
                return 1.0  # Undefined, assume hostile
        
            cv = abs(std_of_means / mean_of_means)
        
            # Normalize to 0-1 range
            # CV > 2.0 is extremely high dispersion
            dispersion = min(cv / 2.0, 1.0)
        
            return dispersion
        except Exception as e:
            logger.error(f"Error in calculate_dispersion: {e}")
            raise


class LiquidityStressAggregator:
    """
    Aggregates liquidity stress across all symbols.
    High stress = illiquid markets = hostile.
    """
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self.liquidity_snapshots: Dict[str, deque] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, symbol: str, snapshot: LiquiditySnapshot):
        """Update liquidity snapshot for symbol"""
        try:
            if symbol not in self.liquidity_snapshots:
                self.liquidity_snapshots[symbol] = deque(maxlen=self.window_size)
        
            self.liquidity_snapshots[symbol].append(snapshot)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_stress(self) -> float:
        """
        Calculate aggregated liquidity stress.
        
        Returns:
            0.0 = Liquid markets
            1.0 = Illiquid/stressed markets
        """
        try:
            if not self.liquidity_snapshots:
                return 1.0  # No data = assume hostile
        
            stress_scores = []
        
            for symbol, snapshots in self.liquidity_snapshots.items():
                if len(snapshots) < 10:
                    continue
            
                recent = list(snapshots)[-10:]
            
                # Calculate stress components
                avg_spread = np.mean([s.bid_ask_spread for s in recent])
                avg_depth = np.mean([s.order_book_depth for s in recent])
                avg_slippage = np.mean([s.slippage_estimate for s in recent])
            
                # Normalize components
                # High spread = high stress
                spread_stress = min(avg_spread / 0.01, 1.0)  # 1% spread = max stress
            
                # Low depth = high stress
                depth_stress = max(0.0, 1.0 - (avg_depth / 1000000.0))  # $1M depth = no stress
            
                # High slippage = high stress
                slippage_stress = min(avg_slippage / 0.005, 1.0)  # 0.5% slippage = max stress
            
                # Combined stress
                symbol_stress = (spread_stress + depth_stress + slippage_stress) / 3.0
                stress_scores.append(symbol_stress)
        
            if not stress_scores:
                return 1.0
        
            # Use 75th percentile (not mean) to be conservative
            return float(np.percentile(stress_scores, 75))
        except Exception as e:
            logger.error(f"Error in calculate_stress: {e}")
            raise


class EdgeDensityCalculator:
    """
    Calculates edge density = recent win rate trends.
    Low edge density = strategies not working = hostile.
    """
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self.trade_outcomes: deque = deque(maxlen=window_size)
            self.strategy_outcomes: Dict[str, deque] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(self, strategy_id: str, won: bool, pnl: float):
        """Record trade outcome"""
        try:
            self.trade_outcomes.append({
                'strategy_id': strategy_id,
                'won': won,
                'pnl': pnl,
                'timestamp': datetime.utcnow()
            })
        
            if strategy_id not in self.strategy_outcomes:
                self.strategy_outcomes[strategy_id] = deque(maxlen=self.window_size)
        
            self.strategy_outcomes[strategy_id].append(won)
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def calculate_edge_density(self) -> float:
        """
        Calculate edge density.
        
        Returns:
            0.0 = No edge (hostile)
            1.0 = Strong edge (benign)
        """
        try:
            if len(self.trade_outcomes) < 20:
                return 0.5  # Insufficient data
        
            recent_trades = list(self.trade_outcomes)[-50:]
        
            # Calculate overall win rate
            wins = sum(1 for t in recent_trades if t['won'])
            win_rate = wins / len(recent_trades)
        
            # Calculate win rate trend (recent vs older)
            if len(recent_trades) >= 40:
                recent_20 = recent_trades[-20:]
                older_20 = recent_trades[-40:-20]
            
                recent_win_rate = sum(1 for t in recent_20 if t['won']) / len(recent_20)
                older_win_rate = sum(1 for t in older_20 if t['won']) / len(older_20)
            
                # Positive trend = edge improving
                trend = recent_win_rate - older_win_rate
            else:
                trend = 0.0
        
            # Calculate average profit per trade
            avg_pnl = np.mean([t['pnl'] for t in recent_trades])
        
            # Edge density components
            # Win rate > 50% is good
            win_rate_component = max(0.0, (win_rate - 0.5) * 2.0)  # 0.5 = 0, 0.75 = 0.5, 1.0 = 1.0
        
            # Positive trend is good
            trend_component = max(0.0, min(1.0, trend * 5.0 + 0.5))  # -0.1 = 0, 0 = 0.5, +0.1 = 1.0
        
            # Positive PnL is good
            pnl_component = 1.0 if avg_pnl > 0 else 0.0
        
            # Combined edge density
            edge_density = (win_rate_component * 0.5 + trend_component * 0.3 + pnl_component * 0.2)
        
            return edge_density
        except Exception as e:
            logger.error(f"Error in calculate_edge_density: {e}")
            raise


class RegimeInstabilityDetector:
    """
    Detects regime instability.
    Frequent regime switches = hostile.
    """
    
    def __init__(self, window_size: int = 50):
        try:
            self.window_size = window_size
            self.regime_history: deque = deque(maxlen=window_size)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, regime: str):
        """Update regime"""
        try:
            self.regime_history.append({
                'regime': regime,
                'timestamp': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_instability(self) -> float:
        """
        Calculate regime instability.
        
        Returns:
            0.0 = Stable regime
            1.0 = Highly unstable
        """
        try:
            if len(self.regime_history) < 10:
                return 0.5  # Insufficient data
        
            regimes = [r['regime'] for r in self.regime_history]
        
            # Count regime switches
            switches = sum(1 for i in range(1, len(regimes)) if regimes[i] != regimes[i-1])
        
            # Normalize by window size
            # More than 10 switches in 50 bars = highly unstable
            instability = min(switches / 10.0, 1.0)
        
            return instability
        except Exception as e:
            logger.error(f"Error in calculate_instability: {e}")
            raise


class DrawdownClusteringDetector:
    """
    Detects drawdown clustering.
    Multiple strategies in drawdown = hostile.
    """
    
    def __init__(self):
        try:
            self.strategy_drawdowns: Dict[str, float] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, strategy_id: str, current_drawdown: float):
        """Update strategy drawdown"""
        try:
            self.strategy_drawdowns[strategy_id] = current_drawdown
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def calculate_clustering(self) -> float:
        """
        Calculate drawdown clustering.
        
        Returns:
            0.0 = No clustering
            1.0 = All strategies in drawdown
        """
        try:
            if not self.strategy_drawdowns:
                return 0.0
        
            # Count strategies in significant drawdown (>5%)
            in_drawdown = sum(1 for dd in self.strategy_drawdowns.values() if dd > 0.05)
        
            # Percentage in drawdown
            clustering = in_drawdown / len(self.strategy_drawdowns)
        
            return clustering
        except Exception as e:
            logger.error(f"Error in calculate_clustering: {e}")
            raise


class UnifiedMarketHostilityGate:
    """
    SINGLE unified gate that blocks ALL trading when hostile.
    
    This is the ONLY market hostility check in the system.
    All other modules must query this gate.
    """
    
    def __init__(
        self,
        dispersion_threshold: float = 0.6,
        liquidity_stress_threshold: float = 0.7,
        edge_density_threshold: float = 0.3,
        regime_instability_threshold: float = 0.6,
        drawdown_clustering_threshold: float = 0.5
    ):
        try:
            self.dispersion_threshold = dispersion_threshold
            self.liquidity_stress_threshold = liquidity_stress_threshold
            self.edge_density_threshold = edge_density_threshold
            self.regime_instability_threshold = regime_instability_threshold
            self.drawdown_clustering_threshold = drawdown_clustering_threshold
        
            # Components
            self.dispersion_tracker = CrossStrategyDispersionTracker()
            self.liquidity_aggregator = LiquidityStressAggregator()
            self.edge_calculator = EdgeDensityCalculator()
            self.regime_detector = RegimeInstabilityDetector()
            self.drawdown_detector = DrawdownClusteringDetector()
        
            # State
            self.last_assessment: Optional[HostilityAssessment] = None
            self.assessment_history: deque = deque(maxlen=100)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_strategy_performance(self, strategy_id: str, return_value: float):
        """Update strategy performance"""
        try:
            self.dispersion_tracker.update(strategy_id, return_value)
        except Exception as e:
            logger.error(f"Error in update_strategy_performance: {e}")
            raise
    
    def update_liquidity(self, symbol: str, snapshot: LiquiditySnapshot):
        """Update liquidity snapshot"""
        try:
            self.liquidity_aggregator.update(symbol, snapshot)
        except Exception as e:
            logger.error(f"Error in update_liquidity: {e}")
            raise
    
    def record_trade(self, strategy_id: str, won: bool, pnl: float):
        """Record trade outcome"""
        try:
            self.edge_calculator.record_trade(strategy_id, won, pnl)
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def update_regime(self, regime: str):
        """Update regime"""
        try:
            self.regime_detector.update(regime)
        except Exception as e:
            logger.error(f"Error in update_regime: {e}")
            raise
    
    def update_drawdown(self, strategy_id: str, drawdown: float):
        """Update strategy drawdown"""
        try:
            self.drawdown_detector.update(strategy_id, drawdown)
        except Exception as e:
            logger.error(f"Error in update_drawdown: {e}")
            raise
    
    def assess_hostility(self) -> HostilityAssessment:
        """
        Assess market hostility.
        
        Returns:
            HostilityAssessment with can_trade flag
        """
        # Calculate all components
        try:
            dispersion = self.dispersion_tracker.calculate_dispersion()
            liquidity_stress = self.liquidity_aggregator.calculate_stress()
            edge_density = self.edge_calculator.calculate_edge_density()
            regime_instability = self.regime_detector.calculate_instability()
            drawdown_clustering = self.drawdown_detector.calculate_clustering()
        
            # Determine hostility level
            hostile_signals = []
        
            if dispersion > self.dispersion_threshold:
                hostile_signals.append(('cross_strategy_dispersion', dispersion))
        
            if liquidity_stress > self.liquidity_stress_threshold:
                hostile_signals.append(('liquidity_stress', liquidity_stress))
        
            if edge_density < self.edge_density_threshold:
                hostile_signals.append(('low_edge_density', edge_density))
        
            if regime_instability > self.regime_instability_threshold:
                hostile_signals.append(('regime_instability', regime_instability))
        
            if drawdown_clustering > self.drawdown_clustering_threshold:
                hostile_signals.append(('drawdown_clustering', drawdown_clustering))
        
            # Determine level
            if len(hostile_signals) >= 3:
                level = HostilityLevel.EXTREME
                can_trade = False
                dominant_reason = f"Multiple hostile signals: {', '.join([s[0] for s in hostile_signals])}"
            elif len(hostile_signals) == 2:
                level = HostilityLevel.HOSTILE
                can_trade = False
                dominant_reason = f"Hostile signals: {', '.join([s[0] for s in hostile_signals])}"
            elif len(hostile_signals) == 1:
                signal_name, signal_value = hostile_signals[0]
                if signal_name == 'low_edge_density':
                    level = HostilityLevel.LOW_EDGE_DENSITY
                    can_trade = False
                    dominant_reason = f"Low edge density: {signal_value:.2%}"
                else:
                    level = HostilityLevel.CAUTIOUS
                    can_trade = True  # Allow trading but with caution
                    dominant_reason = f"Caution: {signal_name} = {signal_value:.2%}"
            else:
                level = HostilityLevel.BENIGN
                can_trade = True
                dominant_reason = "Market conditions benign"
        
            # Create assessment
            assessment = HostilityAssessment(
                level=level,
                can_trade=can_trade,
                cross_strategy_dispersion=dispersion,
                liquidity_stress=liquidity_stress,
                edge_density=edge_density,
                regime_instability=regime_instability,
                drawdown_clustering=drawdown_clustering,
                dominant_reason=dominant_reason,
                timestamp=datetime.utcnow(),
                details={
                    'dispersion': dispersion,
                    'liquidity_stress': liquidity_stress,
                    'edge_density': edge_density,
                    'regime_instability': regime_instability,
                    'drawdown_clustering': drawdown_clustering,
                    'hostile_signal_count': len(hostile_signals)
                }
            )
        
            # Store
            self.last_assessment = assessment
            self.assessment_history.append(assessment)
        
            # Log
            if not can_trade:
                logger.warning(
                    f"MARKET HOSTILE - Trading blocked: {dominant_reason}\n"
                    f"  Dispersion: {dispersion:.2%}\n"
                    f"  Liquidity Stress: {liquidity_stress:.2%}\n"
                    f"  Edge Density: {edge_density:.2%}\n"
                    f"  Regime Instability: {regime_instability:.2%}\n"
                    f"  Drawdown Clustering: {drawdown_clustering:.2%}"
                )
        
            return assessment
        except Exception as e:
            logger.error(f"Error in assess_hostility: {e}")
            raise
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Check if trading is allowed.
        
        Returns:
            (can_trade, reason)
        """
        try:
            assessment = self.assess_hostility()
            return assessment.can_trade, assessment.dominant_reason
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics"""
        try:
            if not self.assessment_history:
                return {}
        
            recent = list(self.assessment_history)[-50:]
        
            hostile_count = sum(1 for a in recent if not a.can_trade)
        
            return {
                'total_assessments': len(self.assessment_history),
                'recent_hostile_rate': hostile_count / len(recent) if recent else 0.0,
                'last_assessment': {
                    'level': self.last_assessment.level.value if self.last_assessment else None,
                    'can_trade': self.last_assessment.can_trade if self.last_assessment else None,
                    'reason': self.last_assessment.dominant_reason if self.last_assessment else None
                },
                'current_metrics': {
                    'dispersion': self.last_assessment.cross_strategy_dispersion if self.last_assessment else None,
                    'liquidity_stress': self.last_assessment.liquidity_stress if self.last_assessment else None,
                    'edge_density': self.last_assessment.edge_density if self.last_assessment else None,
                    'regime_instability': self.last_assessment.regime_instability if self.last_assessment else None,
                    'drawdown_clustering': self.last_assessment.drawdown_clustering if self.last_assessment else None
                }
            }
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


# Global singleton instance
_global_hostility_gate: Optional[UnifiedMarketHostilityGate] = None


def get_global_hostility_gate() -> UnifiedMarketHostilityGate:
    """Get global hostility gate singleton"""
    try:
        global _global_hostility_gate
        if _global_hostility_gate is None:
            _global_hostility_gate = UnifiedMarketHostilityGate()
        return _global_hostility_gate
    except Exception as e:
        logger.error(f"Error in get_global_hostility_gate: {e}")
        raise


def create_hostility_gate(**kwargs) -> UnifiedMarketHostilityGate:
    """Create new hostility gate instance"""
    return UnifiedMarketHostilityGate(**kwargs)
