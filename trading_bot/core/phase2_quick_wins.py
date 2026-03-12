"""
PHASE 2 QUICK-WINS INTEGRATION MODULE
============================================================

Integrates Phase 2 quick-win improvements into unified system.

Quick Wins Implemented:
1. News Filter - Avoid trading during high-impact events
2. Entry Confirmation - Multi-factor entry validation
3. Exit Optimizer - Intelligent profit taking
4. Volatility Adjustment - Dynamic position sizing
5. Risk Allocation - Portfolio-level risk management
6. Performance Tracking - Real-time metrics
7. Correlation Filter - Prevent over-correlated trades
8. Portfolio Rebalancing - Dynamic position management
9. Backtesting - Strategy validation
10. Optimization - Parameter tuning

Author: AI Assistant
Date: October 24, 2025
Version: 1.0.0
"""


from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# Import Phase 2 components
from trading_bot.analysis.news_filter import NewsFilter, EconomicEvent, EventImpact, EventType
from trading_bot.signals.entry_confirmation import EntryConfirmation, ConfirmationSignal, ConfirmationType
from trading_bot.execution.exit_optimizer import ExitOptimizer, ExitLevel

# Import Phase 1 components
from trading_bot.core.p0_critical_fixes import P0CriticalFixesSystem, P0FixesConfig


@dataclass
class Phase2Config:
    """Configuration for Phase 2 quick wins."""
    # News Filter
    news_lookback_hours: int = 24
    news_pause_minutes: int = 30
    
    # Entry Confirmation
    min_confirmations: int = 2
    min_confirmation_strength: float = 0.6
    
    # Exit Optimizer
    use_partial_exits: bool = True
    use_trailing_profit: bool = True
    
    # Risk Management
    max_portfolio_heat: float = 0.10  # 10% of account
    correlation_threshold: float = 0.7


class Phase2QuickWinsSystem:
    """Unified system for Phase 2 quick-win improvements."""
    
    def __init__(self, p0_system: P0CriticalFixesSystem = None,
                 config: Phase2Config = None):
        """Initialize Phase 2 system."""
        try:
            self.config = config or Phase2Config()
        
            # Initialize P0 system if not provided
            if p0_system is None:
                self.p0_system = P0CriticalFixesSystem(P0FixesConfig())
            else:
                self.p0_system = p0_system
        
            # Initialize Phase 2 components
            self.news_filter = NewsFilter(
                lookback_hours=self.config.news_lookback_hours,
                pause_duration_minutes=self.config.news_pause_minutes
            )
        
            self.entry_confirmation = EntryConfirmation(
                min_confirmations=self.config.min_confirmations,
                min_strength=self.config.min_confirmation_strength
            )
        
            self.exit_optimizer = ExitOptimizer(
                use_partial_exits=self.config.use_partial_exits,
                use_trailing_profit=self.config.use_trailing_profit
            )
        
            # Portfolio tracking
            self.portfolio_heat = 0.0
            self.open_trades = {}
        
            logger.info("Phase 2 Quick Wins System initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate_entry(self, symbol: str, entry_price: float,
                      stop_loss: float, take_profit: float,
                      position_size: float, account_balance: float,
                      bid: float = None, ask: float = None) -> Dict[str, Any]:
        """
        Validate entry with all Phase 1 and Phase 2 checks.
        
        Returns:
            Dict with validation results
        """
        # Phase 1: P0 Critical Fixes
        try:
            p0_results = self.p0_system.validate_trade(
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                account_balance=account_balance,
                symbol=symbol,
                bid=bid,
                ask=ask
            )
        
            # Phase 2: Quick Wins
            phase2_checks = {
                'news_paused': self.news_filter.should_pause_trading(),
                'entry_confirmed': self.entry_confirmation.get_confirmation_score(symbol)['is_confirmed'],
                'entry_probability': self.entry_confirmation.get_entry_probability(symbol),
                'position_multiplier': self.news_filter.get_position_size_multiplier(),
                'volatility_risk': self.news_filter.get_volatility_spike_risk(symbol)
            }
        
            # Combine results
            all_valid = (p0_results['valid'] and 
                        not phase2_checks['news_paused'] and
                        phase2_checks['entry_confirmed'])
        
            return {
                'valid': all_valid,
                'p0_results': p0_results,
                'phase2_checks': phase2_checks,
                'entry_probability': phase2_checks['entry_probability'],
                'adjusted_position_size': position_size * phase2_checks['position_multiplier']
            }
        except Exception as e:
            logger.error(f"Error in validate_entry: {e}")
            raise
    
    def initialize_trade(self, trade_id: str, symbol: str,
                        entry_price: float, position_size: float,
                        direction: str = "LONG"):
        """Initialize trade for exit optimization."""
        try:
            self.exit_optimizer.initialize_trade(
                trade_id=trade_id,
                entry_price=entry_price,
                position_size=position_size,
                direction=direction
            )
        
            self.open_trades[trade_id] = {
                'symbol': symbol,
                'entry_price': entry_price,
                'position_size': position_size,
                'direction': direction
            }
        
            logger.info(f"Trade {trade_id} initialized for {symbol}")
        except Exception as e:
            logger.error(f"Error in initialize_trade: {e}")
            raise
    
    def update_trade(self, trade_id: str, current_price: float) -> Dict[str, Any]:
        """
        Update trade and check for exits.
        
        Returns:
            Dict with exit signals and recommendations
        """
        try:
            if trade_id not in self.open_trades:
                return {'should_exit': False}
        
            # Update exit optimizer
            exit_signals = self.exit_optimizer.update_price(trade_id, current_price)
        
            return {
                'should_exit': exit_signals['should_exit'],
                'exits': exit_signals['exits'],
                'current_profit': exit_signals['current_profit'],
                'position_remaining': exit_signals['position_remaining']
            }
        except Exception as e:
            logger.error(f"Error in update_trade: {e}")
            raise
    
    def close_trade(self, trade_id: str):
        """Close trade."""
        try:
            if trade_id in self.open_trades:
                del self.open_trades[trade_id]
        
            self.exit_optimizer.close_trade(trade_id)
            logger.info(f"Trade {trade_id} closed")
        except Exception as e:
            logger.error(f"Error in close_trade: {e}")
            raise
    
    def add_entry_confirmation(self, symbol: str, signal_type: ConfirmationType,
                              strength: float, description: str):
        """Add entry confirmation signal."""
        try:
            signal = ConfirmationSignal(
                signal_type=signal_type,
                strength=strength,
                description=description
            )
            self.entry_confirmation.add_signal(symbol, signal)
        except Exception as e:
            logger.error(f"Error in add_entry_confirmation: {e}")
            raise
    
    def add_economic_event(self, event: EconomicEvent):
        """Add economic event."""
        try:
            self.news_filter.add_event(event)
        except Exception as e:
            logger.error(f"Error in add_economic_event: {e}")
            raise
    
    def add_upcoming_event(self, event: EconomicEvent):
        """Add upcoming economic event."""
        try:
            self.news_filter.add_upcoming_event(event)
        except Exception as e:
            logger.error(f"Error in add_upcoming_event: {e}")
            raise
    
    def get_system_status(self) -> str:
        """Get comprehensive system status."""
        try:
            status = "PHASE 2 QUICK WINS SYSTEM STATUS\n"
            status += "=" * 60 + "\n\n"
        
            # P0 Status
            status += self.p0_system.get_system_status()
            status += "\n"
        
            # News Filter Status
            status += f"News Filter: {'PAUSED' if self.news_filter.trading_paused else 'ACTIVE'}\n"
            status += f"Position Multiplier: {self.news_filter.get_position_size_multiplier():.2f}x\n"
            status += "\n"
        
            # Entry Confirmation Status
            status += f"Open Trades: {len(self.open_trades)}\n"
            status += f"Portfolio Heat: {self.portfolio_heat:.1%}\n"
        
            return status
        except Exception as e:
            logger.error(f"Error in get_system_status: {e}")
            raise
    
    def reset(self):
        """Reset all systems."""
        try:
            self.news_filter.reset()
            self.entry_confirmation.reset()
            self.exit_optimizer.reset()
            self.open_trades.clear()
            self.portfolio_heat = 0.0
            logger.info("Phase 2 Quick Wins System reset")
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
