"""
Pre-Trade Checks Engine - Hard pre-trade rule enforcement

Implements comprehensive pre-trade validation before signal processing.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, time
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CheckResult(Enum):
    """Pre-trade check results"""
    APPROVED = 'approved'
    REJECTED = 'rejected'
    WARNING = 'warning'


@dataclass
class PreTradeCheck:
    """Pre-trade check result"""
    check_name: str
    result: CheckResult
    reason: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        try:
            if self.metadata is None:
                self.metadata = {}
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class PreTradeChecksEngine:
    """Comprehensive pre-trade validation engine"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Leverage limits
            self.max_leverage = self.config.get('max_leverage', 10.0)
        
            # Symbol blacklist
            self.blacklisted_symbols = set(self.config.get('blacklisted_symbols', []))
        
            # Trading windows
            self.trading_windows = self.config.get('trading_windows', {})
        
            # Liquidity thresholds
            self.min_liquidity = self.config.get('min_liquidity', {
                'min_volume': 1000,
                'max_spread_bps': 50
            })
        
            # Position limits
            self.max_position_size_pct = self.config.get('max_position_size_pct', 0.20)  # 20% of portfolio
            self.max_positions_per_symbol = self.config.get('max_positions_per_symbol', 1)
            self.max_total_positions = self.config.get('max_total_positions', 5)  # CRITICAL: Max total positions
        
            # TP/SL requirements
            self.require_stop_loss = self.config.get('require_stop_loss', True)
            self.require_take_profit = self.config.get('require_take_profit', True)
            self.min_risk_reward_ratio = self.config.get('min_risk_reward_ratio', 1.0)
        
            # Order frequency limits
            self.max_orders_per_minute = self.config.get('max_orders_per_minute', 10)
            self.order_history = []
        
            # Wash trade prevention
            self.min_time_between_opposite_trades = self.config.get('min_time_between_opposite_trades', 60)  # seconds
            self.recent_trades = []
        
            # News embargo
            self.news_embargo_symbols = set()
            self.embargo_duration = self.config.get('embargo_duration', 300)  # 5 minutes
        
            logger.info("Pre-trade checks engine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def run_all_checks(self, order_params: Dict[str, Any], 
                      portfolio_state: Dict[str, Any]) -> List[PreTradeCheck]:
        """
        Run all pre-trade checks
        
        Args:
            order_params: Order parameters (symbol, side, size, etc.)
            portfolio_state: Current portfolio state
            
        Returns:
            List of check results
        """
        try:
            checks = []
        
            # 1. Blacklist check
            checks.append(self._check_blacklist(order_params))
        
            # 2. Trading window check
            checks.append(self._check_trading_window(order_params))
        
            # 3. Leverage check
            checks.append(self._check_leverage(order_params, portfolio_state))
        
            # 4. Liquidity check
            checks.append(self._check_liquidity(order_params))
        
            # 5. Position size check
            checks.append(self._check_position_size(order_params, portfolio_state))
        
            # 6. Position count check
            checks.append(self._check_position_count(order_params, portfolio_state))
        
            # 7. Order frequency check
            checks.append(self._check_order_frequency(order_params))
        
            # 8. Wash trade check
            checks.append(self._check_wash_trade(order_params))
        
            # 9. News embargo check
            checks.append(self._check_news_embargo(order_params))
        
            # 10. TP/SL required check (CRITICAL)
            checks.append(self._check_tp_sl_required(order_params))
        
            return checks
        except Exception as e:
            logger.error(f"Error in run_all_checks: {e}")
            raise
    
    def is_approved(self, checks: List[PreTradeCheck]) -> bool:
        """Check if all checks are approved"""
        return all(check.result == CheckResult.APPROVED for check in checks)
    
    def get_rejection_reasons(self, checks: List[PreTradeCheck]) -> List[str]:
        """Get all rejection reasons"""
        return [
            check.reason for check in checks 
            if check.result == CheckResult.REJECTED
        ]
    
    def _check_blacklist(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check if symbol is blacklisted"""
        try:
            symbol = order_params.get('symbol', '')
        
            if symbol in self.blacklisted_symbols:
                return PreTradeCheck(
                    check_name='blacklist',
                    result=CheckResult.REJECTED,
                    reason=f"Symbol {symbol} is blacklisted"
                )
        
            return PreTradeCheck(
                check_name='blacklist',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_blacklist: {e}")
            raise
    
    def _check_trading_window(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check if trading is allowed at current time"""
        try:
            symbol = order_params.get('symbol', '')
            now = datetime.now().time()
        
            if symbol in self.trading_windows:
                window = self.trading_windows[symbol]
                start = time.fromisoformat(window['start'])
                end = time.fromisoformat(window['end'])
            
                if not (start <= now <= end):
                    return PreTradeCheck(
                        check_name='trading_window',
                        result=CheckResult.REJECTED,
                        reason=f"Outside trading window for {symbol}: {start}-{end}"
                    )
        
            return PreTradeCheck(
                check_name='trading_window',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_trading_window: {e}")
            raise
    
    def _check_leverage(self, order_params: Dict[str, Any], 
                       portfolio_state: Dict[str, Any]) -> PreTradeCheck:
        """Check leverage limits"""
        try:
            position_value = order_params.get('position_value', 0)
            account_equity = portfolio_state.get('equity', 1)
        
            leverage = position_value / max(account_equity, 1)
        
            if leverage > self.max_leverage:
                return PreTradeCheck(
                    check_name='leverage',
                    result=CheckResult.REJECTED,
                    reason=f"Leverage {leverage:.1f}x exceeds limit {self.max_leverage}x",
                    metadata={'leverage': leverage, 'max_leverage': self.max_leverage}
                )
        
            return PreTradeCheck(
                check_name='leverage',
                result=CheckResult.APPROVED,
                metadata={'leverage': leverage}
            )
        except Exception as e:
            logger.error(f"Error in _check_leverage: {e}")
            raise
    
    def _check_liquidity(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check liquidity thresholds"""
        try:
            volume = order_params.get('volume', 0)
            spread_bps = order_params.get('spread_bps', 0)
        
            if volume < self.min_liquidity['min_volume']:
                return PreTradeCheck(
                    check_name='liquidity',
                    result=CheckResult.REJECTED,
                    reason=f"Volume {volume} below minimum {self.min_liquidity['min_volume']}"
                )
        
            if spread_bps > self.min_liquidity['max_spread_bps']:
                return PreTradeCheck(
                    check_name='liquidity',
                    result=CheckResult.REJECTED,
                    reason=f"Spread {spread_bps} bps exceeds maximum {self.min_liquidity['max_spread_bps']} bps"
                )
        
            return PreTradeCheck(
                check_name='liquidity',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_liquidity: {e}")
            raise
    
    def _check_position_size(self, order_params: Dict[str, Any],
                            portfolio_state: Dict[str, Any]) -> PreTradeCheck:
        """Check position size limits"""
        try:
            position_value = order_params.get('position_value', 0)
            portfolio_value = portfolio_state.get('total_value', 1)
        
            position_pct = position_value / max(portfolio_value, 1)
        
            if position_pct > self.max_position_size_pct:
                return PreTradeCheck(
                    check_name='position_size',
                    result=CheckResult.REJECTED,
                    reason=f"Position size {position_pct:.1%} exceeds limit {self.max_position_size_pct:.1%}"
                )
        
            return PreTradeCheck(
                check_name='position_size',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_position_size: {e}")
            raise
    
    def _check_position_count(self, order_params: Dict[str, Any],
                             portfolio_state: Dict[str, Any]) -> PreTradeCheck:
        """Check position count limits"""
        try:
            symbol = order_params.get('symbol', '')
            positions = portfolio_state.get('positions', {})
        
            # CRITICAL FIX: Check TOTAL positions first
            total_positions = len(positions)
            if total_positions >= self.max_total_positions:
                return PreTradeCheck(
                    check_name='position_count',
                    result=CheckResult.REJECTED,
                    reason=f"Max total positions reached: {total_positions} >= {self.max_total_positions}"
                )
        
            # Then check per-symbol limit
            symbol_positions = sum(1 for p in positions.values() if p.get('symbol') == symbol)
            if symbol_positions >= self.max_positions_per_symbol:
                return PreTradeCheck(
                    check_name='position_count',
                    result=CheckResult.REJECTED,
                    reason=f"Max positions for {symbol} reached: {symbol_positions}/{self.max_positions_per_symbol}"
                )
        
            return PreTradeCheck(
                check_name='position_count',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_position_count: {e}")
            raise
    
    def _check_order_frequency(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check order frequency limits"""
        try:
            now = datetime.now()
        
            # Clean old orders (older than 1 minute)
            self.order_history = [
                t for t in self.order_history 
                if (now - t).total_seconds() < 60
            ]
        
            if len(self.order_history) >= self.max_orders_per_minute:
                return PreTradeCheck(
                    check_name='order_frequency',
                    result=CheckResult.REJECTED,
                    reason=f"Order frequency limit exceeded: {len(self.order_history)}/{self.max_orders_per_minute} per minute"
                )
        
            # Record this order
            self.order_history.append(now)
        
            return PreTradeCheck(
                check_name='order_frequency',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_order_frequency: {e}")
            raise
    
    def _check_wash_trade(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check for potential wash trades"""
        try:
            symbol = order_params.get('symbol', '')
            side = order_params.get('side', '')
            now = datetime.now()
        
            # Clean old trades
            self.recent_trades = [
                t for t in self.recent_trades
                if (now - t['timestamp']).total_seconds() < self.min_time_between_opposite_trades
            ]
        
            # Check for opposite side trade
            for trade in self.recent_trades:
                if (trade['symbol'] == symbol and 
                    trade['side'] != side and
                    (now - trade['timestamp']).total_seconds() < self.min_time_between_opposite_trades):
                
                    return PreTradeCheck(
                        check_name='wash_trade',
                        result=CheckResult.WARNING,
                        reason=f"Opposite trade within {self.min_time_between_opposite_trades}s"
                    )
        
            # Record this trade
            self.recent_trades.append({
                'symbol': symbol,
                'side': side,
                'timestamp': now
            })
        
            return PreTradeCheck(
                check_name='wash_trade',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_wash_trade: {e}")
            raise
    
    def _check_news_embargo(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """Check news embargo"""
        try:
            symbol = order_params.get('symbol', '')
        
            if symbol in self.news_embargo_symbols:
                return PreTradeCheck(
                    check_name='news_embargo',
                    result=CheckResult.REJECTED,
                    reason=f"News embargo active for {symbol}"
                )
        
            return PreTradeCheck(
                check_name='news_embargo',
                result=CheckResult.APPROVED
            )
        except Exception as e:
            logger.error(f"Error in _check_news_embargo: {e}")
            raise
    
    def _check_tp_sl_required(self, order_params: Dict[str, Any]) -> PreTradeCheck:
        """
        CRITICAL: Check if TP and SL are provided and validate risk:reward ratio.
        This prevents trades without stop loss (unlimited risk exposure).
        """
        try:
            stop_loss = order_params.get('stop_loss')
            take_profit = order_params.get('take_profit')
        
            # Check if SL is required and provided
            if self.require_stop_loss and not stop_loss:
                return PreTradeCheck(
                    check_name='tp_sl_required',
                    result=CheckResult.REJECTED,
                    reason="CRITICAL: Stop loss is required but not provided - unlimited risk!"
                )
        
            # Check if TP is required and provided
            if self.require_take_profit and not take_profit:
                return PreTradeCheck(
                    check_name='tp_sl_required',
                    result=CheckResult.REJECTED,
                    reason="Take profit is required but not provided"
                )
        
            # Validate risk:reward ratio if both TP and SL provided
            if stop_loss and take_profit:
                entry_price = order_params.get('price', 0)
                side = order_params.get('side', 'buy')
            
                if entry_price > 0:
                    if side == 'buy':
                        risk = abs(entry_price - stop_loss)
                        reward = abs(take_profit - entry_price)
                    else:  # sell
                        risk = abs(stop_loss - entry_price)
                        reward = abs(entry_price - take_profit)
                
                    if risk > 0:
                        rr_ratio = reward / risk
                    
                        if rr_ratio < self.min_risk_reward_ratio:
                            return PreTradeCheck(
                                check_name='tp_sl_required',
                                result=CheckResult.REJECTED,
                                reason=f"Risk:Reward ratio {rr_ratio:.2f} below minimum {self.min_risk_reward_ratio:.2f}"
                            )
        
            return PreTradeCheck(
                check_name='tp_sl_required',
                result=CheckResult.APPROVED,
                metadata={'stop_loss': stop_loss, 'take_profit': take_profit}
            )
        except Exception as e:
            logger.error(f"Error in _check_tp_sl_required: {e}")
            raise
    
    def add_news_embargo(self, symbol: str):
        """Add symbol to news embargo"""
        try:
            self.news_embargo_symbols.add(symbol)
            logger.info("News embargo added for %s", symbol)
        except Exception as e:
            logger.error(f"Error in add_news_embargo: {e}")
            raise
    
    def remove_news_embargo(self, symbol: str):
        """Remove symbol from news embargo"""
        try:
            self.news_embargo_symbols.discard(symbol)
            logger.info("News embargo removed for %s", symbol)
        except Exception as e:
            logger.error(f"Error in remove_news_embargo: {e}")
            raise
    
    def add_to_blacklist(self, symbol: str):
        """Add symbol to blacklist"""
        try:
            self.blacklisted_symbols.add(symbol)
            logger.info("Symbol %s added to blacklist", symbol)
        except Exception as e:
            logger.error(f"Error in add_to_blacklist: {e}")
            raise
    
    def remove_from_blacklist(self, symbol: str):
        """Remove symbol from blacklist"""
        try:
            self.blacklisted_symbols.discard(symbol)
            logger.info("Symbol %s removed from blacklist", symbol)
        except Exception as e:
            logger.error(f"Error in remove_from_blacklist: {e}")
            raise
