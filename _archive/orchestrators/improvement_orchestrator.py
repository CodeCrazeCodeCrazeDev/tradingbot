"""
Improvement Orchestrator
========================

Master orchestrator that integrates ALL trading improvements:
1. Signal Enhancement
2. Session & Spread Filter
3. Dynamic Position Sizing
4. Market Regime Detection
5. Advanced Exit Strategies
6. News Event Filter
7. Entry Optimization
8. Drawdown Recovery

This is the single entry point for all improvements.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import numpy as np

from .signal_enhancement import SignalEnhancer, SignalEnhancementResult
from .session_spread_filter import TradingTimeFilter, SessionFilter, SpreadFilter
from .position_sizing import DynamicPositionSizer, PositionSizeResult
from .market_regime import MarketRegimeDetector, MarketRegime
from .exit_strategies import AdvancedExitManager, PositionExitPlan
from .news_filter import NewsEventFilter, NewsFilterResult
from .entry_optimizer import EntryOptimizer, EntryOpportunity
from .drawdown_recovery import DrawdownRecoveryManager, RecoveryPlan
import numpy

logger = logging.getLogger(__name__)


@dataclass
class TradeValidationResult:
    """Complete trade validation result"""
    # Overall decision
    should_trade: bool
    confidence: float
    
    # Signal analysis
    signal_result: Optional[SignalEnhancementResult]
    
    # Timing analysis
    session_ok: bool
    spread_ok: bool
    news_ok: bool
    
    # Entry analysis
    entry_quality: str
    optimal_entry: float
    wait_for_pullback: bool
    
    # Position sizing
    position_size: float
    risk_amount: float
    
    # Market context
    market_regime: str
    regime_recommendation: str
    
    # Recovery status
    recovery_mode: str
    position_multiplier: float
    
    # Exit plan
    stop_loss: float
    take_profit_levels: List[float]
    
    # Reasons
    reasons: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'should_trade': self.should_trade,
            'confidence': self.confidence,
            'session_ok': self.session_ok,
            'spread_ok': self.spread_ok,
            'news_ok': self.news_ok,
            'entry_quality': self.entry_quality,
            'optimal_entry': self.optimal_entry,
            'position_size': self.position_size,
            'market_regime': self.market_regime,
            'recovery_mode': self.recovery_mode,
            'stop_loss': self.stop_loss,
            'reasons': self.reasons,
            'warnings': self.warnings,
        }


class ImprovementOrchestrator:
    """
    Master orchestrator for all trading improvements.
    
    USAGE:
        orchestrator = ImprovementOrchestrator()
        
        result = orchestrator.validate_trade_opportunity(
            symbol='EURUSD',
            signal='BUY',
            price=1.0850,
            market_data=data
        )
        
        if result.should_trade:
            size = result.position_size
            entry = result.optimal_entry
            sl = result.stop_loss
            tp = result.take_profit_levels[0]
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize all improvement systems
            self.signal_enhancer = SignalEnhancer(self.config.get('signal', {}))
            self.time_filter = TradingTimeFilter(self.config.get('time', {}))
            self.position_sizer = DynamicPositionSizer(self.config.get('sizing', {}))
            self.regime_detector = MarketRegimeDetector(self.config.get('regime', {}))
            self.exit_manager = AdvancedExitManager(self.config.get('exit', {}))
            self.news_filter = NewsEventFilter(self.config.get('news', {}))
            self.entry_optimizer = EntryOptimizer(self.config.get('entry', {}))
            self.recovery_manager = DrawdownRecoveryManager(self.config.get('recovery', {}))
        
            # Account settings
            self.account_balance = self.config.get('account_balance', 10000)
            self.base_risk_percent = self.config.get('base_risk_percent', 0.02)
        
            # Validation thresholds
            self.min_confidence = self.config.get('min_confidence', 0.6)
            self.min_rr_ratio = self.config.get('min_rr_ratio', 1.5)
        
            logger.info("ImprovementOrchestrator initialized - ALL SYSTEMS ACTIVE")
            logger.info("Systems: Signal, Time, Sizing, Regime, Exit, News, Entry, Recovery")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_trade_opportunity(
        self,
        symbol: str,
        signal: str,
        current_price: float,
        market_data: Dict[str, Any],
        account_balance: Optional[float] = None,
        current_spread: Optional[float] = None
    ) -> TradeValidationResult:
        """
        Comprehensive trade validation using all improvement systems.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            signal: Trade signal ('BUY', 'SELL', 'HOLD')
            current_price: Current market price
            market_data: Dict containing:
                - highs: np.ndarray of high prices
                - lows: np.ndarray of low prices
                - closes: np.ndarray of close prices
                - volumes: np.ndarray of volumes (optional)
                - timeframe_data: Dict of timeframe -> prices (optional)
            account_balance: Current account balance (optional)
            current_spread: Current spread in pips (optional)
        
        Returns:
            TradeValidationResult with complete analysis
        """
        try:
            account_balance = account_balance or self.account_balance
            current_spread = current_spread or 1.5  # Default spread
        
            reasons = []
            warnings = []
            should_trade = True
            confidence = 0.5
        
            # Extract market data
            highs = market_data.get('highs', np.array([current_price]))
            lows = market_data.get('lows', np.array([current_price]))
            closes = market_data.get('closes', np.array([current_price]))
            volumes = market_data.get('volumes')
            timeframe_data = market_data.get('timeframe_data', {'M15': closes})
        
            # 1. CHECK RECOVERY STATUS
            can_trade, recovery_reason = self.recovery_manager.can_trade()
            recovery_plan = self.recovery_manager.assess_state(account_balance)
        
            if not can_trade:
                should_trade = False
                reasons.append(f"Recovery: {recovery_reason}")
            else:
                reasons.append(f"Recovery: {recovery_plan.mode.value} mode")
        
            position_multiplier = recovery_plan.position_multiplier
        
            # 2. CHECK SESSION & SPREAD
            session_ok, time_reasons = self.time_filter.should_trade(
                symbol, current_spread
            )
            reasons.extend(time_reasons)
        
            spread_ok = session_ok  # Combined in time filter
        
            if not session_ok:
                should_trade = False
                warnings.append("Trading conditions not optimal")
        
            # 3. CHECK NEWS EVENTS
            news_result = self.news_filter.check_can_trade(symbol)
            news_ok = news_result.can_trade
        
            if not news_ok:
                should_trade = False
                reasons.append(f"News: {news_result.reason}")
            elif news_result.minutes_to_next_event and news_result.minutes_to_next_event < 60:
                warnings.append(f"News in {news_result.minutes_to_next_event}m")
        
            # 4. DETECT MARKET REGIME
            regime = self.regime_detector.detect(symbol, highs, lows, closes, volumes)
        
            if regime.avoid_trading:
                should_trade = False
                reasons.append(f"Regime: {regime.regime_type.value} - avoid trading")
            else:
                reasons.append(f"Regime: {regime.regime_type.value}")
        
            # Adjust multiplier for regime
            position_multiplier *= regime.position_size_multiplier
        
            # 5. ENHANCE SIGNAL
            signal_result = self.signal_enhancer.enhance_signal(
                signal=signal,
                symbol=symbol,
                timeframe_data=timeframe_data,
                volume_data=volumes,
                current_volume=volumes[-1] if volumes is not None and len(volumes) > 0 else None,
                ohlc_data={'high': highs, 'low': lows, 'close': closes}
            )
        
            if not signal_result.should_take:
                should_trade = False
                reasons.extend(signal_result.reasons)
            else:
                confidence += 0.2
                reasons.extend(signal_result.reasons)
        
            # 6. CALCULATE STOP LOSS AND TAKE PROFIT
            atr = self._calculate_atr(highs, lows, closes)
        
            if signal == 'BUY':
                stop_loss = current_price - (atr * 2)
                take_profit = current_price + (atr * 3)
            else:
                stop_loss = current_price + (atr * 2)
                take_profit = current_price - (atr * 3)
        
            # 7. OPTIMIZE ENTRY
            entry_opportunity = self.entry_optimizer.analyze_entry(
                symbol=symbol,
                direction=signal,
                highs=highs,
                lows=lows,
                closes=closes,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
            if entry_opportunity.entry_quality.value == 'avoid':
                should_trade = False
                reasons.append("Entry quality: AVOID")
            elif entry_opportunity.wait_for_pullback and entry_opportunity.pullback_target:
                warnings.append(f"Consider waiting for pullback to {entry_opportunity.pullback_target:.5f}")
        
            reasons.extend(entry_opportunity.reasons)
        
            # 8. CALCULATE POSITION SIZE
            size_result = self.position_sizer.calculate_size(
                symbol=symbol,
                account_balance=account_balance,
                current_drawdown=self.recovery_manager.tracker.get_snapshot(account_balance).drawdown_pct,
                current_atr=atr,
                average_atr=atr,  # Simplified
            )
        
            # Apply recovery multiplier
            final_size = size_result.recommended_size * position_multiplier
            risk_amount = account_balance * final_size
        
            # 9. CALCULATE FINAL CONFIDENCE
            confidence = (
                signal_result.confidence * 0.3 +
                regime.regime_confidence * 0.2 +
                (1.0 if session_ok else 0.5) * 0.2 +
                (1.0 if news_ok else 0.5) * 0.15 +
                size_result.confidence * 0.15
            )
        
            # Final decision
            if confidence < self.min_confidence:
                should_trade = False
                reasons.append(f"Confidence too low: {confidence:.2f}")
        
            # Calculate take profit levels for partial exits
            risk = abs(current_price - stop_loss)
            tp_levels = [
                current_price + risk * 1.0 * (1 if signal == 'BUY' else -1),
                current_price + risk * 2.0 * (1 if signal == 'BUY' else -1),
                current_price + risk * 3.0 * (1 if signal == 'BUY' else -1),
            ]
        
            return TradeValidationResult(
                should_trade=should_trade,
                confidence=confidence,
                signal_result=signal_result,
                session_ok=session_ok,
                spread_ok=spread_ok,
                news_ok=news_ok,
                entry_quality=entry_opportunity.entry_quality.value,
                optimal_entry=entry_opportunity.optimal_entry,
                wait_for_pullback=entry_opportunity.wait_for_pullback,
                position_size=final_size,
                risk_amount=risk_amount,
                market_regime=regime.regime_type.value,
                regime_recommendation=regime.recommended_strategy,
                recovery_mode=recovery_plan.mode.value,
                position_multiplier=position_multiplier,
                stop_loss=stop_loss,
                take_profit_levels=tp_levels,
                reasons=reasons,
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Error in validate_trade_opportunity: {e}")
            raise
    
    def create_exit_plan(
        self,
        position_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float
    ) -> PositionExitPlan:
        """Create exit plan for a new position"""
        return self.exit_manager.create_exit_plan(
            position_id=position_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss
        )
    
    def update_position(
        self,
        position_id: str,
        current_price: float,
        current_atr: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update exit plan for existing position"""
        return self.exit_manager.update_exit_plan(
            position_id=position_id,
            current_price=current_price,
            current_atr=current_atr
        )
    
    def record_trade_result(
        self,
        pnl: float,
        symbol: str,
        direction: str,
        entry_time: datetime,
        exit_time: datetime
    ):
        """Record trade result for performance tracking"""
        try:
            self.recovery_manager.record_trade(pnl, symbol, direction, entry_time, exit_time)
            self.position_sizer.record_trade(pnl)
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def get_market_analysis(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get comprehensive market analysis without trade validation"""
        try:
            highs = market_data.get('highs', np.array([]))
            lows = market_data.get('lows', np.array([]))
            closes = market_data.get('closes', np.array([]))
            volumes = market_data.get('volumes')
        
            # Detect regime
            regime = self.regime_detector.detect(symbol, highs, lows, closes, volumes)
        
            # Check news
            news = self.news_filter.check_can_trade(symbol)
        
            # Get session info
            session = self.time_filter.session_filter.get_current_session()
        
            return {
                'symbol': symbol,
                'regime': regime.to_dict(),
                'news': {
                    'can_trade': news.can_trade,
                    'reason': news.reason,
                    'risk_level': news.risk_level,
                },
                'session': {
                    'current': session.session.value,
                    'is_optimal': session.is_optimal,
                    'liquidity': session.liquidity_score,
                },
                'recommendations': regime.reasons,
            }
        except Exception as e:
            logger.error(f"Error in get_market_analysis: {e}")
            raise
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        return self.recovery_manager.get_recovery_progress(self.account_balance)
    
    def update_account_balance(self, balance: float):
        """Update account balance"""
        try:
            self.account_balance = balance
        except Exception as e:
            logger.error(f"Error in update_account_balance: {e}")
            raise
    
    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> float:
        """Calculate ATR"""
        try:
            if len(highs) < period + 1:
                return 0.001  # Default for forex
        
            tr = np.zeros(len(highs))
            for i in range(1, len(highs)):
                hl = highs[i] - lows[i]
                hc = abs(highs[i] - closes[i-1])
                lc = abs(lows[i] - closes[i-1])
                tr[i] = max(hl, hc, lc)
        
            return np.mean(tr[-period:])
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise


def create_improvement_system(config: Optional[Dict] = None) -> ImprovementOrchestrator:
    """Factory function to create improvement system"""
    return ImprovementOrchestrator(config)


# Quick usage example
if __name__ == "__main__":
    
    # Create orchestrator
    orchestrator = ImprovementOrchestrator({
        'account_balance': 10000,
        'base_risk_percent': 0.02,
    })
    
    # Sample market data
    np.random.seed(42)
    closes = np.cumsum(np.random.randn(100) * 0.001) + 1.0850
    highs = closes + np.random.rand(100) * 0.001
    lows = closes - np.random.rand(100) * 0.001
    
    market_data = {
        'highs': highs,
        'lows': lows,
        'closes': closes,
        'timeframe_data': {'M15': closes},
    }
    
    # Validate trade
    result = orchestrator.validate_trade_opportunity(
        symbol='EURUSD',
        signal='BUY',
        current_price=closes[-1],
        market_data=market_data,
        current_spread=1.2
    )
    
    print("=" * 60)
    logger.info("TRADE VALIDATION RESULT")
    print("=" * 60)
    logger.info(f"Should Trade: {result.should_trade}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Position Size: {result.position_size:.4f}")
    logger.info(f"Risk Amount: ${result.risk_amount:.2f}")
    logger.info(f"Market Regime: {result.market_regime}")
    logger.info(f"Entry Quality: {result.entry_quality}")
    logger.info(f"Stop Loss: {result.stop_loss:.5f}")
    print()
    logger.info("Reasons:")
    for reason in result.reasons:
        logger.info(f"  - {reason}")
    if result.warnings:
        logger.info("Warnings:")
        for warning in result.warnings:
            logger.info(f"  ! {warning}")
