"""
Pre-Trade Validation Gateway
============================

The FINAL safety checkpoint before ANY order is submitted to the broker.
This is the last line of defense against catastrophic trading errors.

Features:
- Fat finger protection (unusual size/price detection)
- Slippage protection (max slippage enforcement)
- Market hours validation
- News blackout enforcement
- Margin requirement check
- Position limit enforcement
- Duplicate order prevention
- Risk budget validation
- Correlation exposure check
- Account equity validation

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum, auto
import hashlib
import json
from collections import deque
import numpy as np
# Removed duplicate imports (logging and asyncio already imported above)

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result status"""
    APPROVED = auto()
    REJECTED = auto()
    WARNING = auto()
    PENDING_REVIEW = auto()


class RejectionReason(Enum):
    """Reasons for trade rejection"""
    FAT_FINGER_SIZE = "Position size exceeds normal range"
    FAT_FINGER_PRICE = "Price deviation exceeds threshold"
    MAX_SLIPPAGE = "Expected slippage exceeds limit"
    MARKET_CLOSED = "Market is closed"
    NEWS_BLACKOUT = "High-impact news event imminent"
    INSUFFICIENT_MARGIN = "Insufficient margin available"
    POSITION_LIMIT = "Position limit would be exceeded"
    DUPLICATE_ORDER = "Duplicate order detected"
    RISK_BUDGET_EXCEEDED = "Risk budget exceeded"
    CORRELATION_EXPOSURE = "Correlated exposure too high"
    EQUITY_TOO_LOW = "Account equity below minimum"
    DRAWDOWN_LIMIT = "Drawdown limit reached"
    DAILY_LOSS_LIMIT = "Daily loss limit reached"
    MAX_TRADES_REACHED = "Maximum daily trades reached"
    INVALID_SYMBOL = "Invalid trading symbol"
    INVALID_DIRECTION = "Invalid trade direction"
    INVALID_SIZE = "Invalid position size"
    SPREAD_TOO_WIDE = "Spread exceeds maximum"
    VOLATILITY_TOO_HIGH = "Volatility exceeds threshold"
    LIQUIDITY_TOO_LOW = "Insufficient liquidity"


@dataclass
class ValidationConfig:
    """Configuration for pre-trade validation"""
    max_position_size_pct: float = 5.0
    max_position_size_lots: float = 10.0
    max_price_deviation_pct: float = 1.0
    max_slippage_pips: float = 5.0
    max_spread_pips: float = 3.0
    max_open_positions: int = 10
    max_positions_per_symbol: int = 3
    max_correlated_exposure_pct: float = 30.0
    max_risk_per_trade_pct: float = 2.0
    max_daily_risk_pct: float = 6.0
    max_drawdown_pct: float = 20.0
    min_equity_usd: float = 1000.0
    max_trades_per_day: int = 50
    min_time_between_trades_sec: int = 5
    trading_start_hour: int = 0
    trading_end_hour: int = 24
    news_blackout_minutes: int = 30
    enable_weekend_trading: bool = False
    allowed_symbols: List[str] = field(default_factory=list)
    blocked_symbols: List[str] = field(default_factory=list)


@dataclass
class TradeRequest:
    """Trade request to be validated"""
    symbol: str
    direction: str  # BUY or SELL
    size: float  # Position size in lots
    price: Optional[float] = None  # Limit price (None for market)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    order_type: str = "MARKET"
    magic_number: int = 0
    comment: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_hash(self) -> str:
        """Generate unique hash for duplicate detection"""
        data = f"{self.symbol}:{self.direction}:{self.size}:{self.price}:{self.timestamp.isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()


@dataclass
class ValidationReport:
    """Detailed validation report"""
    result: ValidationResult
    trade_request: TradeRequest
    rejection_reasons: List[RejectionReason] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    estimated_slippage: float = 0.0
    margin_required: float = 0.0
    margin_available: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    validation_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'result': self.result.name,
            'symbol': self.trade_request.symbol,
            'direction': self.trade_request.direction,
            'size': self.trade_request.size,
            'rejection_reasons': [r.value for r in self.rejection_reasons],
            'warnings': self.warnings,
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'risk_score': self.risk_score,
            'estimated_slippage': self.estimated_slippage,
            'margin_required': self.margin_required,
            'margin_available': self.margin_available,
            'timestamp': self.timestamp.isoformat(),
            'validation_time_ms': self.validation_time_ms
        }


class PreTradeValidator:
    """
    Pre-Trade Validation Gateway
    
    The FINAL checkpoint before any order is submitted.
    All trades MUST pass through this validator.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.recent_orders: deque = deque(maxlen=1000)
        self.daily_trades: Dict[str, int] = {}
        self.daily_risk_used: float = 0.0
        self.last_trade_time: Optional[datetime] = None
        self.blocked_until: Optional[datetime] = None
        self.news_events: List[Dict] = []
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # Statistics
        self.stats = {
            'total_validations': 0,
            'approved': 0,
            'rejected': 0,
            'warnings': 0
        }
        
        # Initialize correlation matrix for major pairs
        self._init_correlation_matrix()
        
        logger.info("PreTradeValidator initialized")
    
    def _init_correlation_matrix(self):
        """Initialize default correlation matrix"""
        self.correlation_matrix = {
            'EURUSD': {'GBPUSD': 0.85, 'USDCHF': -0.90, 'USDJPY': -0.30, 'AUDUSD': 0.70},
            'GBPUSD': {'EURUSD': 0.85, 'USDCHF': -0.75, 'USDJPY': -0.25, 'AUDUSD': 0.65},
            'USDCHF': {'EURUSD': -0.90, 'GBPUSD': -0.75, 'USDJPY': 0.60, 'AUDUSD': -0.65},
            'USDJPY': {'EURUSD': -0.30, 'GBPUSD': -0.25, 'USDCHF': 0.60, 'AUDUSD': -0.20},
            'AUDUSD': {'EURUSD': 0.70, 'GBPUSD': 0.65, 'USDCHF': -0.65, 'USDJPY': -0.20}
        }
    
    async def validate(
        self,
        trade: TradeRequest,
        account_info: Dict[str, Any],
        market_data: Dict[str, Any],
        open_positions: List[Dict[str, Any]]
    ) -> ValidationReport:
        """
        Validate a trade request
        
        Args:
            trade: Trade request to validate
            account_info: Current account information
            market_data: Current market data for the symbol
            open_positions: List of currently open positions
            
        Returns:
            ValidationReport with detailed results
        """
        start_time = datetime.now()
        
        report = ValidationReport(
            result=ValidationResult.APPROVED,
            trade_request=trade
        )
        
        self.stats['total_validations'] += 1
        
        # Run all validation checks
        checks = [
            ('basic_validation', self._check_basic_validation),
            ('fat_finger_size', self._check_fat_finger_size),
            ('fat_finger_price', self._check_fat_finger_price),
            ('slippage', self._check_slippage),
            ('spread', self._check_spread),
            ('market_hours', self._check_market_hours),
            ('news_blackout', self._check_news_blackout),
            ('margin', self._check_margin),
            ('position_limits', self._check_position_limits),
            ('duplicate_order', self._check_duplicate_order),
            ('risk_budget', self._check_risk_budget),
            ('correlation_exposure', self._check_correlation_exposure),
            ('equity', self._check_equity),
            ('drawdown', self._check_drawdown),
            ('daily_limits', self._check_daily_limits),
            ('time_between_trades', self._check_time_between_trades),
            ('volatility', self._check_volatility),
            ('liquidity', self._check_liquidity)
        ]
        
        for check_name, check_func in checks:
            try:
                passed, reason, warning = await check_func(
                    trade, account_info, market_data, open_positions
                )
                
                if passed:
                    report.checks_passed.append(check_name)
                else:
                    report.checks_failed.append(check_name)
                    if reason:
                        report.rejection_reasons.append(reason)
                
                if warning:
                    report.warnings.append(warning)
                    
            except Exception as e:
                logger.error(f"Validation check {check_name} failed: {e}")
                report.checks_failed.append(f"{check_name} (error)")
        
        # Determine final result
        if report.rejection_reasons:
            report.result = ValidationResult.REJECTED
            self.stats['rejected'] += 1
        elif report.warnings:
            report.result = ValidationResult.WARNING
            self.stats['warnings'] += 1
            self.stats['approved'] += 1
        else:
            report.result = ValidationResult.APPROVED
            self.stats['approved'] += 1
        
        # Calculate risk score
        report.risk_score = self._calculate_risk_score(trade, account_info, market_data)
        
        # Record validation time
        report.validation_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log result
        if report.result == ValidationResult.REJECTED:
            logger.warning(f"Trade REJECTED: {trade.symbol} {trade.direction} {trade.size} - "
                          f"Reasons: {[r.value for r in report.rejection_reasons]}")
        elif report.result == ValidationResult.WARNING:
            logger.info(f"Trade APPROVED with warnings: {trade.symbol} {trade.direction} {trade.size}")
        else:
            logger.info(f"Trade APPROVED: {trade.symbol} {trade.direction} {trade.size}")
        
        # Record order for duplicate detection
        if report.result in [ValidationResult.APPROVED, ValidationResult.WARNING]:
            self.recent_orders.append({
                'hash': trade.get_hash(),
                'timestamp': datetime.now()
            })
            self.last_trade_time = datetime.now()
        
        return report
    
    async def _check_basic_validation(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Basic validation checks"""
        # Check symbol
        if self.config.blocked_symbols and trade.symbol in self.config.blocked_symbols:
            return False, RejectionReason.INVALID_SYMBOL, None
        
        if self.config.allowed_symbols and trade.symbol not in self.config.allowed_symbols:
            return False, RejectionReason.INVALID_SYMBOL, None
        
        # Check direction
        if trade.direction not in ['BUY', 'SELL']:
            return False, RejectionReason.INVALID_DIRECTION, None
        
        # Check size
        if trade.size <= 0:
            return False, RejectionReason.INVALID_SIZE, None
        
        return True, None, None
    
    async def _check_fat_finger_size(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check for unusually large position sizes"""
        # Check absolute lot limit
        if trade.size > self.config.max_position_size_lots:
            return False, RejectionReason.FAT_FINGER_SIZE, None
        
        # Check percentage of account
        equity = account_info.get('equity', 0)
        if equity > 0:
            # Estimate position value (simplified)
            position_value = trade.size * 100000  # Standard lot = 100,000 units
            position_pct = (position_value / equity) * 100
            
            if position_pct > self.config.max_position_size_pct * 10:  # 10x leverage check
                return False, RejectionReason.FAT_FINGER_SIZE, None
        
        return True, None, None
    
    async def _check_fat_finger_price(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check for price deviation from current market"""
        if trade.price is None:  # Market order
            return True, None, None
        
        current_price = market_data.get('price', market_data.get('bid', 0))
        if current_price <= 0:
            return True, None, "Could not verify price - no market data"
        
        deviation_pct = abs(trade.price - current_price) / current_price * 100
        
        if deviation_pct > self.config.max_price_deviation_pct:
            return False, RejectionReason.FAT_FINGER_PRICE, None
        
        if deviation_pct > self.config.max_price_deviation_pct * 0.5:
            return True, None, f"Price deviation {deviation_pct:.2f}% is elevated"
        
        return True, None, None
    
    async def _check_slippage(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check expected slippage"""
        spread = market_data.get('spread', 0)
        volatility = market_data.get('volatility', 0)
        
        # Estimate slippage based on spread and volatility
        estimated_slippage = spread * 0.5 + volatility * 0.1
        
        if estimated_slippage > self.config.max_slippage_pips:
            return False, RejectionReason.MAX_SLIPPAGE, None
        
        if estimated_slippage > self.config.max_slippage_pips * 0.7:
            return True, None, f"Expected slippage {estimated_slippage:.1f} pips is elevated"
        
        return True, None, None
    
    async def _check_spread(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check if spread is acceptable"""
        spread = market_data.get('spread', 0)
        
        if spread > self.config.max_spread_pips:
            return False, RejectionReason.SPREAD_TOO_WIDE, None
        
        if spread > self.config.max_spread_pips * 0.7:
            return True, None, f"Spread {spread:.1f} pips is elevated"
        
        return True, None, None
    
    async def _check_market_hours(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check if market is open"""
        now = datetime.utcnow()
        
        # Check weekend
        if not self.config.enable_weekend_trading:
            if now.weekday() >= 5:  # Saturday or Sunday
                return False, RejectionReason.MARKET_CLOSED, None
        
        # Check trading hours
        current_hour = now.hour
        if not (self.config.trading_start_hour <= current_hour < self.config.trading_end_hour):
            return False, RejectionReason.MARKET_CLOSED, None
        
        return True, None, None
    
    async def _check_news_blackout(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check for upcoming high-impact news"""
        now = datetime.utcnow()
        blackout_window = timedelta(minutes=self.config.news_blackout_minutes)
        
        for event in self.news_events:
            event_time = event.get('time')
            if event_time and isinstance(event_time, datetime):
                if abs((event_time - now).total_seconds()) < blackout_window.total_seconds():
                    impact = event.get('impact', 'unknown')
                    if impact in ['high', 'critical']:
                        return False, RejectionReason.NEWS_BLACKOUT, None
                    elif impact == 'medium':
                        return True, None, f"Medium impact news in {self.config.news_blackout_minutes} minutes"
        
        return True, None, None
    
    async def _check_margin(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check margin requirements"""
        free_margin = account_info.get('free_margin', 0)
        
        # Estimate required margin (simplified)
        leverage = account_info.get('leverage', 100)
        position_value = trade.size * 100000
        required_margin = position_value / leverage
        
        if required_margin > free_margin:
            return False, RejectionReason.INSUFFICIENT_MARGIN, None
        
        margin_usage_pct = (required_margin / free_margin) * 100 if free_margin > 0 else 100
        if margin_usage_pct > 80:
            return True, None, f"Trade will use {margin_usage_pct:.1f}% of free margin"
        
        return True, None, None
    
    async def _check_position_limits(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check position limits"""
        # Check total open positions
        if len(positions) >= self.config.max_open_positions:
            return False, RejectionReason.POSITION_LIMIT, None
        
        # Check positions per symbol
        symbol_positions = [p for p in positions if p.get('symbol') == trade.symbol]
        if len(symbol_positions) >= self.config.max_positions_per_symbol:
            return False, RejectionReason.POSITION_LIMIT, None
        
        return True, None, None
    
    async def _check_duplicate_order(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check for duplicate orders"""
        trade_hash = trade.get_hash()
        now = datetime.now()
        
        # Check recent orders (within 60 seconds)
        for order in self.recent_orders:
            if order['hash'] == trade_hash:
                age = (now - order['timestamp']).total_seconds()
                if age < 60:
                    return False, RejectionReason.DUPLICATE_ORDER, None
        
        return True, None, None
    
    async def _check_risk_budget(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check risk budget"""
        equity = account_info.get('equity', 0)
        if equity <= 0:
            return True, None, "Could not verify risk budget - no equity data"
        
        # Calculate risk for this trade
        if trade.stop_loss:
            current_price = market_data.get('price', market_data.get('bid', 0))
            if current_price > 0:
                risk_pips = abs(current_price - trade.stop_loss) * 10000
                risk_amount = risk_pips * trade.size * 10  # Simplified pip value
                risk_pct = (risk_amount / equity) * 100
                
                if risk_pct > self.config.max_risk_per_trade_pct:
                    return False, RejectionReason.RISK_BUDGET_EXCEEDED, None
                
                if risk_pct > self.config.max_risk_per_trade_pct * 0.8:
                    return True, None, f"Risk {risk_pct:.2f}% is near limit"
        
        return True, None, None
    
    async def _check_correlation_exposure(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check correlated exposure"""
        symbol = trade.symbol
        
        if symbol not in self.correlation_matrix:
            return True, None, None
        
        # Calculate correlated exposure
        correlated_exposure = 0
        for pos in positions:
            pos_symbol = pos.get('symbol', '')
            if pos_symbol in self.correlation_matrix.get(symbol, {}):
                correlation = self.correlation_matrix[symbol][pos_symbol]
                if abs(correlation) > 0.7:  # High correlation
                    pos_size = pos.get('volume', 0)
                    correlated_exposure += pos_size * abs(correlation)
        
        total_exposure = correlated_exposure + trade.size
        equity = account_info.get('equity', 0)
        
        if equity > 0:
            exposure_pct = (total_exposure * 100000 / equity) * 100
            if exposure_pct > self.config.max_correlated_exposure_pct:
                return False, RejectionReason.CORRELATION_EXPOSURE, None
        
        return True, None, None
    
    async def _check_equity(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check account equity"""
        equity = account_info.get('equity', 0)
        
        if equity < self.config.min_equity_usd:
            return False, RejectionReason.EQUITY_TOO_LOW, None
        
        return True, None, None
    
    async def _check_drawdown(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check current drawdown"""
        equity = account_info.get('equity', 0)
        balance = account_info.get('balance', 0)
        
        if balance > 0:
            drawdown_pct = ((balance - equity) / balance) * 100
            if drawdown_pct > self.config.max_drawdown_pct:
                return False, RejectionReason.DRAWDOWN_LIMIT, None
            
            if drawdown_pct > self.config.max_drawdown_pct * 0.8:
                return True, None, f"Drawdown {drawdown_pct:.2f}% is near limit"
        
        return True, None, None
    
    async def _check_daily_limits(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check daily trading limits"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Check trade count
        daily_count = self.daily_trades.get(today, 0)
        if daily_count >= self.config.max_trades_per_day:
            return False, RejectionReason.MAX_TRADES_REACHED, None
        
        # Check daily risk
        if self.daily_risk_used >= self.config.max_daily_risk_pct:
            return False, RejectionReason.DAILY_LOSS_LIMIT, None
        
        return True, None, None
    
    async def _check_time_between_trades(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check minimum time between trades"""
        if self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time).total_seconds()
            if elapsed < self.config.min_time_between_trades_sec:
                return True, None, f"Only {elapsed:.1f}s since last trade"
        
        return True, None, None
    
    async def _check_volatility(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check market volatility"""
        volatility = market_data.get('volatility', 0)
        avg_volatility = market_data.get('avg_volatility', volatility)
        
        if avg_volatility > 0 and volatility > avg_volatility * 3:
            return False, RejectionReason.VOLATILITY_TOO_HIGH, None
        
        if avg_volatility > 0 and volatility > avg_volatility * 2:
            return True, None, f"Volatility is {volatility/avg_volatility:.1f}x normal"
        
        return True, None, None
    
    async def _check_liquidity(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict, positions: List
    ) -> Tuple[bool, Optional[RejectionReason], Optional[str]]:
        """Check market liquidity"""
        volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume', volume)
        
        if avg_volume > 0 and volume < avg_volume * 0.1:
            return False, RejectionReason.LIQUIDITY_TOO_LOW, None
        
        if avg_volume > 0 and volume < avg_volume * 0.3:
            return True, None, "Liquidity is below average"
        
        return True, None, None
    
    def _calculate_risk_score(
        self, trade: TradeRequest, account_info: Dict, market_data: Dict
    ) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        # Size risk (0-25)
        size_risk = min(trade.size / self.config.max_position_size_lots * 25, 25)
        score += size_risk
        
        # Spread risk (0-25)
        spread = market_data.get('spread', 0)
        spread_risk = min(spread / self.config.max_spread_pips * 25, 25)
        score += spread_risk
        
        # Volatility risk (0-25)
        volatility = market_data.get('volatility', 0)
        avg_volatility = market_data.get('avg_volatility', volatility)
        if avg_volatility > 0:
            vol_risk = min((volatility / avg_volatility) * 12.5, 25)
            score += vol_risk
        
        # Drawdown risk (0-25)
        equity = account_info.get('equity', 0)
        balance = account_info.get('balance', 0)
        if balance > 0:
            drawdown = ((balance - equity) / balance) * 100
            dd_risk = min(drawdown / self.config.max_drawdown_pct * 25, 25)
            score += dd_risk
        
        return min(score, 100)
    
    def add_news_event(self, event: Dict):
        """Add a news event for blackout checking"""
        self.news_events.append(event)
        # Clean old events
        now = datetime.utcnow()
        self.news_events = [
            e for e in self.news_events
            if e.get('time', now) > now - timedelta(hours=1)
        ]
    
    def update_correlation_matrix(self, matrix: Dict[str, Dict[str, float]]):
        """Update correlation matrix"""
        self.correlation_matrix.update(matrix)
    
    def record_trade_result(self, profit_pct: float):
        """Record trade result for daily tracking"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1
        
        if profit_pct < 0:
            self.daily_risk_used += abs(profit_pct)
    
    def reset_daily_counters(self):
        """Reset daily counters (call at start of trading day)"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = 0
        self.daily_risk_used = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = self.stats['total_validations']
        return {
            'total_validations': total,
            'approved': self.stats['approved'],
            'rejected': self.stats['rejected'],
            'warnings': self.stats['warnings'],
            'approval_rate': self.stats['approved'] / total * 100 if total > 0 else 0,
            'rejection_rate': self.stats['rejected'] / total * 100 if total > 0 else 0
        }
    
    def block_trading(self, duration_minutes: int, reason: str):
        """Block all trading for specified duration"""
        self.blocked_until = datetime.now() + timedelta(minutes=duration_minutes)
        logger.warning(f"Trading blocked for {duration_minutes} minutes: {reason}")
    
    def is_trading_blocked(self) -> Tuple[bool, Optional[str]]:
        """Check if trading is currently blocked"""
        if self.blocked_until and datetime.now() < self.blocked_until:
            remaining = (self.blocked_until - datetime.now()).total_seconds() / 60
            return True, f"Trading blocked for {remaining:.1f} more minutes"
        return False, None


# Singleton instance
_validator_instance: Optional[PreTradeValidator] = None


def get_pre_trade_validator(config: Optional[ValidationConfig] = None) -> PreTradeValidator:
    """Get or create the pre-trade validator singleton"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = PreTradeValidator(config)
    return _validator_instance


# Export
__all__ = [
    'PreTradeValidator',
    'ValidationConfig',
    'TradeRequest',
    'ValidationReport',
    'ValidationResult',
    'RejectionReason',
    'get_pre_trade_validator'
]
