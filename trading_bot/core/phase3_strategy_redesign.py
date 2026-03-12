"""
PHASE 3 STRATEGY REDESIGN - INTEGRATION MODULE
============================================================

Integrates Phase 1 (P0), Phase 2 (Quick Wins), and Phase 3 (Strategy) systems.

Objectives:
- Achieve 55%+ win rate
- Achieve 1.5+ Sharpe ratio
- Reduce drawdown to <15%
- Improve risk/reward to 2:1

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Import Phase 1 & 2
from trading_bot.core.phase2_quick_wins import Phase2QuickWinsSystem, Phase2Config

# Import Phase 3 components
from trading_bot.strategy.multi_timeframe_strategy import (
    MultiTimeFrameStrategy, TimeFrame, TimeFrameAnalysis, TrendDirection
)
from trading_bot.analysis.market_regime import MarketRegimeDetector, MarketRegime


@dataclass
class Phase3Config:
    """Configuration for Phase 3 strategy redesign."""
    # Multi-timeframe settings
    primary_timeframe: TimeFrame = TimeFrame.ONE_HOUR
    secondary_timeframe: TimeFrame = TimeFrame.FIFTEEN_MIN
    tertiary_timeframe: TimeFrame = TimeFrame.FIVE_MIN
    
    # Market regime settings
    regime_lookback: int = 50
    
    # Entry settings
    min_entry_confidence: float = 0.65
    
    # Exit settings
    use_trailing_stops: bool = True
    trailing_stop_percent: float = 1.0
    
    # Performance targets
    target_win_rate: float = 0.55
    target_sharpe: float = 1.5
    target_drawdown: float = 0.15
    target_risk_reward: float = 2.0


class Phase3StrategyRedesign:
    """Phase 3 strategy redesign system."""
    
    def __init__(self, phase2_system: Phase2QuickWinsSystem = None,
                 config: Phase3Config = None):
        """Initialize Phase 3 system."""
        try:
            self.config = config or Phase3Config()
        
            # Initialize Phase 2 system if not provided
            if phase2_system is None:
                self.phase2_system = Phase2QuickWinsSystem()
            else:
                self.phase2_system = phase2_system
        
            # Initialize Phase 3 components
            self.multi_timeframe_strategy = MultiTimeFrameStrategy(
                primary_tf=self.config.primary_timeframe,
                secondary_tf=self.config.secondary_timeframe,
                tertiary_tf=self.config.tertiary_timeframe
            )
        
            self.market_regime_detector = MarketRegimeDetector(
                lookback_period=self.config.regime_lookback
            )
        
            # Performance tracking
            self.trades_completed = 0
            self.trades_won = 0
            self.total_profit = 0.0
        
            logger.info("Phase 3 Strategy Redesign System initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_entry(self, symbol: str, 
                     timeframe_analyses: Dict[TimeFrame, TimeFrameAnalysis],
                     current_price: float, account_balance: float) -> Dict[str, Any]:
        """
        Analyze entry opportunity with all Phase 1, 2, and 3 checks.
        
        Returns:
            Dict with entry analysis and recommendation
        """
        # Add timeframe analyses
        try:
            for tf, analysis in timeframe_analyses.items():
                self.multi_timeframe_strategy.add_analysis(symbol, tf, analysis)
        
            # Generate multi-timeframe signal
            signal = self.multi_timeframe_strategy.generate_signal(symbol)
        
            if not signal:
                return {
                    'should_enter': False,
                    'reason': 'No multi-timeframe signal'
                }
        
            # Check confidence
            if signal.confidence < self.config.min_entry_confidence:
                return {
                    'should_enter': False,
                    'reason': f'Low confidence: {signal.confidence:.2f}'
                }
        
            # Validate with Phase 2 system
            phase2_validation = self.phase2_system.validate_entry(
                symbol=symbol,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                position_size=0.25,  # Default
                account_balance=account_balance,
                bid=current_price * 0.9999,
                ask=current_price * 1.0001
            )
        
            if not phase2_validation['valid']:
                return {
                    'should_enter': False,
                    'reason': 'Phase 2 validation failed'
                }
        
            # Detect market regime
            regime_metrics = self.market_regime_detector.detect_regime()
        
            # Adjust position size based on regime
            position_multiplier = self._get_regime_multiplier(regime_metrics)
            adjusted_position = phase2_validation['adjusted_position_size'] * position_multiplier
        
            return {
                'should_enter': True,
                'signal': signal,
                'phase2_validation': phase2_validation,
                'regime': regime_metrics.regime.name if regime_metrics else 'UNKNOWN',
                'position_size': adjusted_position,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit
            }
        except Exception as e:
            logger.error(f"Error in analyze_entry: {e}")
            raise
    
    def _get_regime_multiplier(self, regime_metrics) -> float:
        """Get position size multiplier based on market regime."""
        try:
            if not regime_metrics:
                return 1.0
        
            regime = regime_metrics.regime
        
            multipliers = {
                MarketRegime.STRONG_UPTREND: 1.2,
                MarketRegime.WEAK_UPTREND: 1.0,
                MarketRegime.RANGE_BOUND: 0.8,
                MarketRegime.WEAK_DOWNTREND: 1.0,
                MarketRegime.STRONG_DOWNTREND: 1.2,
                MarketRegime.HIGHLY_VOLATILE: 0.6
            }
        
            return multipliers.get(regime, 1.0)
        except Exception as e:
            logger.error(f"Error in _get_regime_multiplier: {e}")
            raise
    
    def record_trade_result(self, won: bool, profit: float):
        """Record trade result for performance tracking."""
        try:
            self.trades_completed += 1
            if won:
                self.trades_won += 1
            self.total_profit += profit
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        try:
            if self.trades_completed == 0:
                return {
                    'win_rate': 0,
                    'avg_profit': 0,
                    'total_profit': 0,
                    'trades': 0
                }
        
            win_rate = self.trades_won / self.trades_completed
            avg_profit = self.total_profit / self.trades_completed
        
            return {
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'total_profit': self.total_profit,
                'trades': self.trades_completed,
                'wins': self.trades_won
            }
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            raise
    
    def get_system_status(self) -> str:
        """Get comprehensive system status."""
        try:
            status = "PHASE 3 STRATEGY REDESIGN STATUS\n"
            status += "=" * 60 + "\n\n"
        
            # Phase 2 status
            status += self.phase2_system.get_system_status()
            status += "\n"
        
            # Market regime
            regime_metrics = self.market_regime_detector.detect_regime()
            if regime_metrics:
                status += f"Market Regime: {regime_metrics.regime.name}\n"
                status += f"Trend Strength: {regime_metrics.trend_strength:.2f}\n"
                status += f"Volatility: {regime_metrics.volatility:.2f}\n"
                status += "\n"
        
            # Performance
            metrics = self.get_performance_metrics()
            status += f"Trades Completed: {metrics['trades']}\n"
            status += f"Win Rate: {metrics['win_rate']:.1%}\n"
            status += f"Total Profit: {metrics['total_profit']:.2f}\n"
            status += "\n"
        
            # Targets
            status += "PERFORMANCE TARGETS:\n"
            status += f"  Win Rate: {metrics['win_rate']:.1%} / {self.config.target_win_rate:.1%}\n"
            status += f"  Sharpe: TBD / {self.config.target_sharpe}\n"
            status += f"  Drawdown: TBD / {self.config.target_drawdown:.1%}\n"
            status += f"  Risk/Reward: TBD / {self.config.target_risk_reward}:1\n"
        
            return status
        except Exception as e:
            logger.error(f"Error in get_system_status: {e}")
            raise
    
    def reset(self):
        """Reset all systems."""
        try:
            self.phase2_system.reset()
            self.multi_timeframe_strategy.reset()
            self.market_regime_detector.reset()
            self.trades_completed = 0
            self.trades_won = 0
            self.total_profit = 0.0
            logger.info("Phase 3 Strategy Redesign System reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
