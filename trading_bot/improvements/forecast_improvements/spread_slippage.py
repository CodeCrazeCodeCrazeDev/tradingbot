"""
Spread & Slippage Management - Improvement #8 (HIGH PRIORITY)
==============================================================

Full cost awareness to avoid unprofitable trades.

Features:
- Real-time spread monitoring
- Slippage tracking per trade
- Avoid trading during high spread
- Cost-adjusted signal filtering
- Execution quality scoring
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class SpreadCondition(Enum):
    """Spread condition levels"""
    EXCELLENT = "excellent"  # Below typical
    NORMAL = "normal"       # Around typical
    ELEVATED = "elevated"   # Above typical
    HIGH = "high"          # Significantly above
    EXTREME = "extreme"    # Avoid trading


class ExecutionQuality(Enum):
    """Execution quality levels"""
    EXCELLENT = "excellent"  # Better than expected
    GOOD = "good"           # As expected
    ACCEPTABLE = "acceptable"  # Slight slippage
    POOR = "poor"           # Significant slippage
    VERY_POOR = "very_poor"  # Severe slippage


@dataclass
class SpreadData:
    """Spread data point"""
    symbol: str
    bid: float
    ask: float
    spread_pips: float
    spread_percent: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2


@dataclass
class SlippageRecord:
    """Slippage record for a trade"""
    symbol: str
    direction: str
    expected_price: float
    actual_price: float
    slippage_pips: float
    slippage_percent: float
    slippage_cost: float
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionReport:
    """Execution quality report"""
    symbol: str
    quality: ExecutionQuality
    spread_at_entry: float
    slippage: float
    total_cost_percent: float
    score: float  # 0-100
    details: Dict[str, Any] = field(default_factory=dict)


class SpreadMonitor:
    """Real-time spread monitoring"""
    
    # Typical spreads for major pairs (in pips)
    TYPICAL_SPREADS = {
        'EURUSD': 1.0,
        'GBPUSD': 1.5,
        'USDJPY': 1.0,
        'USDCHF': 1.5,
        'AUDUSD': 1.5,
        'NZDUSD': 2.0,
        'USDCAD': 1.5,
        'EURGBP': 1.5,
        'EURJPY': 1.5,
        'GBPJPY': 2.5,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.spread_history: Dict[str, deque] = {}
            self.history_size = self.config.get('history_size', 1000)
            self.pip_size = self.config.get('pip_size', 0.0001)
            self.max_spread_multiplier = self.config.get('max_spread_multiplier', 3.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_spread(self, symbol: str, bid: float, ask: float) -> SpreadData:
        """Update spread data"""
        try:
            spread = ask - bid
        
            # Calculate spread in pips
            if 'JPY' in symbol:
                spread_pips = spread / 0.01
            else:
                spread_pips = spread / self.pip_size
        
            # Calculate spread as percentage
            mid_price = (bid + ask) / 2
            spread_percent = (spread / mid_price) * 100 if mid_price > 0 else 0
        
            data = SpreadData(
                symbol=symbol,
                bid=bid,
                ask=ask,
                spread_pips=spread_pips,
                spread_percent=spread_percent
            )
        
            # Update history
            if symbol not in self.spread_history:
                self.spread_history[symbol] = deque(maxlen=self.history_size)
            self.spread_history[symbol].append(data)
        
            return data
        except Exception as e:
            logger.error(f"Error in update_spread: {e}")
            raise
    
    def get_current_spread(self, symbol: str) -> Optional[SpreadData]:
        """Get current spread"""
        try:
            if symbol not in self.spread_history or not self.spread_history[symbol]:
                return None
            return self.spread_history[symbol][-1]
        except Exception as e:
            logger.error(f"Error in get_current_spread: {e}")
            raise
    
    def get_spread_condition(self, symbol: str) -> Tuple[SpreadCondition, str]:
        """Get current spread condition"""
        try:
            current = self.get_current_spread(symbol)
            if not current:
                return SpreadCondition.NORMAL, "No spread data"
        
            typical = self.TYPICAL_SPREADS.get(symbol, 2.0)
            ratio = current.spread_pips / typical
        
            if ratio <= 0.8:
                return SpreadCondition.EXCELLENT, f"Spread {current.spread_pips:.1f} pips (below typical)"
            elif ratio <= 1.2:
                return SpreadCondition.NORMAL, f"Spread {current.spread_pips:.1f} pips (normal)"
            elif ratio <= 2.0:
                return SpreadCondition.ELEVATED, f"Spread {current.spread_pips:.1f} pips (elevated)"
            elif ratio <= self.max_spread_multiplier:
                return SpreadCondition.HIGH, f"Spread {current.spread_pips:.1f} pips (high)"
            else:
                return SpreadCondition.EXTREME, f"Spread {current.spread_pips:.1f} pips (extreme - avoid)"
        except Exception as e:
            logger.error(f"Error in get_spread_condition: {e}")
            raise
    
    def is_spread_acceptable(self, symbol: str) -> Tuple[bool, str]:
        """Check if spread is acceptable for trading"""
        try:
            condition, reason = self.get_spread_condition(symbol)
        
            if condition in [SpreadCondition.EXCELLENT, SpreadCondition.NORMAL]:
                return True, reason
            elif condition == SpreadCondition.ELEVATED:
                return True, f"Warning: {reason}"
            else:
                return False, f"Spread too high: {reason}"
        except Exception as e:
            logger.error(f"Error in is_spread_acceptable: {e}")
            raise
    
    def get_spread_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get spread statistics"""
        try:
            if symbol not in self.spread_history or len(self.spread_history[symbol]) < 10:
                return {'error': 'Insufficient data'}
        
            spreads = [s.spread_pips for s in self.spread_history[symbol]]
        
            return {
                'current': spreads[-1],
                'average': statistics.mean(spreads),
                'median': statistics.median(spreads),
                'min': min(spreads),
                'max': max(spreads),
                'std_dev': statistics.stdev(spreads) if len(spreads) > 1 else 0,
                'typical': self.TYPICAL_SPREADS.get(symbol, 2.0),
                'samples': len(spreads)
            }
        except Exception as e:
            logger.error(f"Error in get_spread_statistics: {e}")
            raise


class SlippageTracker:
    """Tracks slippage per trade"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.slippage_history: Dict[str, deque] = {}
            self.history_size = self.config.get('history_size', 500)
            self.pip_size = self.config.get('pip_size', 0.0001)
            self.acceptable_slippage_pips = self.config.get('acceptable_slippage_pips', 1.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_slippage(
        self,
        symbol: str,
        direction: str,
        expected_price: float,
        actual_price: float,
        quantity: float,
        execution_time_ms: float = 0
    ) -> SlippageRecord:
        """Record slippage for a trade"""
        # Calculate slippage
        try:
            if direction.lower() == 'buy':
                slippage = actual_price - expected_price  # Positive = worse
            else:
                slippage = expected_price - actual_price  # Positive = worse
        
            # Convert to pips
            if 'JPY' in symbol:
                slippage_pips = slippage / 0.01
            else:
                slippage_pips = slippage / self.pip_size
        
            # Calculate percentage
            slippage_percent = (slippage / expected_price) * 100 if expected_price > 0 else 0
        
            # Calculate cost
            slippage_cost = abs(slippage) * quantity
        
            record = SlippageRecord(
                symbol=symbol,
                direction=direction,
                expected_price=expected_price,
                actual_price=actual_price,
                slippage_pips=slippage_pips,
                slippage_percent=slippage_percent,
                slippage_cost=slippage_cost,
                execution_time_ms=execution_time_ms
            )
        
            # Update history
            if symbol not in self.slippage_history:
                self.slippage_history[symbol] = deque(maxlen=self.history_size)
            self.slippage_history[symbol].append(record)
        
            logger.info(f"Slippage: {symbol} {direction} - {slippage_pips:.2f} pips ({slippage_percent:.4f}%)")
            return record
        except Exception as e:
            logger.error(f"Error in record_slippage: {e}")
            raise
    
    def get_average_slippage(self, symbol: str) -> Tuple[float, float]:
        """Get average slippage in pips and percent"""
        try:
            if symbol not in self.slippage_history or not self.slippage_history[symbol]:
                return 0.0, 0.0
        
            records = list(self.slippage_history[symbol])
            avg_pips = statistics.mean(r.slippage_pips for r in records)
            avg_percent = statistics.mean(r.slippage_percent for r in records)
        
            return avg_pips, avg_percent
        except Exception as e:
            logger.error(f"Error in get_average_slippage: {e}")
            raise
    
    def get_expected_slippage(self, symbol: str) -> float:
        """Get expected slippage for position sizing"""
        try:
            avg_pips, _ = self.get_average_slippage(symbol)
        
            # Add buffer for safety
            return max(avg_pips * 1.5, self.acceptable_slippage_pips)
        except Exception as e:
            logger.error(f"Error in get_expected_slippage: {e}")
            raise
    
    def get_slippage_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get slippage statistics"""
        try:
            if symbol not in self.slippage_history or len(self.slippage_history[symbol]) < 5:
                return {'error': 'Insufficient data'}
        
            records = list(self.slippage_history[symbol])
            slippages = [r.slippage_pips for r in records]
        
            positive_slippage = [s for s in slippages if s > 0]
            negative_slippage = [s for s in slippages if s < 0]
        
            return {
                'average_pips': statistics.mean(slippages),
                'median_pips': statistics.median(slippages),
                'max_pips': max(slippages),
                'min_pips': min(slippages),
                'std_dev': statistics.stdev(slippages) if len(slippages) > 1 else 0,
                'positive_slippage_count': len(positive_slippage),
                'negative_slippage_count': len(negative_slippage),
                'avg_positive': statistics.mean(positive_slippage) if positive_slippage else 0,
                'avg_negative': statistics.mean(negative_slippage) if negative_slippage else 0,
                'total_trades': len(records),
                'avg_execution_time_ms': statistics.mean(r.execution_time_ms for r in records)
            }
        except Exception as e:
            logger.error(f"Error in get_slippage_statistics: {e}")
            raise


class HighSpreadAvoidance:
    """Avoids trading during high spread periods"""
    
    def __init__(self, spread_monitor: SpreadMonitor, config: Optional[Dict] = None):
        try:
            self.spread_monitor = spread_monitor
            self.config = config or {}
            self.max_spread_pips = self.config.get('max_spread_pips', {
                'EURUSD': 2.0,
                'GBPUSD': 3.0,
                'USDJPY': 2.0,
                'DEFAULT': 4.0
            })
            self.high_spread_periods: Dict[str, List[Tuple[int, int]]] = {}  # symbol -> [(hour_start, hour_end)]
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def should_avoid_trading(self, symbol: str) -> Tuple[bool, str]:
        """Check if should avoid trading due to spread"""
        try:
            current = self.spread_monitor.get_current_spread(symbol)
            if not current:
                return False, "No spread data"
        
            max_spread = self.max_spread_pips.get(symbol, self.max_spread_pips.get('DEFAULT', 4.0))
        
            if current.spread_pips > max_spread:
                return True, f"Spread {current.spread_pips:.1f} pips exceeds max {max_spread} pips"
        
            # Check if in known high spread period
            current_hour = datetime.now().hour
            if symbol in self.high_spread_periods:
                for start, end in self.high_spread_periods[symbol]:
                    if start <= current_hour <= end:
                        return True, f"Known high spread period ({start}:00-{end}:00 UTC)"
        
            return False, "Spread acceptable"
        except Exception as e:
            logger.error(f"Error in should_avoid_trading: {e}")
            raise
    
    def learn_high_spread_periods(self, symbol: str):
        """Learn high spread periods from history"""
        try:
            if symbol not in self.spread_monitor.spread_history:
                return
        
            # Group spreads by hour
            hourly_spreads: Dict[int, List[float]] = {}
        
            for data in self.spread_monitor.spread_history[symbol]:
                hour = data.timestamp.hour
                if hour not in hourly_spreads:
                    hourly_spreads[hour] = []
                hourly_spreads[hour].append(data.spread_pips)
        
            # Find hours with consistently high spreads
            typical = self.spread_monitor.TYPICAL_SPREADS.get(symbol, 2.0)
            high_spread_hours = []
        
            for hour, spreads in hourly_spreads.items():
                if len(spreads) >= 10:
                    avg_spread = statistics.mean(spreads)
                    if avg_spread > typical * 2:
                        high_spread_hours.append(hour)
        
            # Convert to periods
            if high_spread_hours:
                high_spread_hours.sort()
                periods = []
                start = high_spread_hours[0]
                end = start
            
                for hour in high_spread_hours[1:]:
                    if hour == end + 1:
                        end = hour
                    else:
                        periods.append((start, end))
                        start = hour
                        end = hour
            
                periods.append((start, end))
                self.high_spread_periods[symbol] = periods
        except Exception as e:
            logger.error(f"Error in learn_high_spread_periods: {e}")
            raise


class CostAdjustedFilter:
    """Filters signals based on trading costs"""
    
    def __init__(
        self,
        spread_monitor: SpreadMonitor,
        slippage_tracker: SlippageTracker,
        config: Optional[Dict] = None
    ):
        try:
            self.spread_monitor = spread_monitor
            self.slippage_tracker = slippage_tracker
            self.config = config or {}
            self.min_profit_to_cost_ratio = self.config.get('min_profit_to_cost_ratio', 3.0)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def estimate_total_cost(self, symbol: str, entry_price: float) -> Tuple[float, Dict[str, float]]:
        """Estimate total trading cost"""
        # Get current spread
        try:
            spread_data = self.spread_monitor.get_current_spread(symbol)
            spread_cost = spread_data.spread_pips if spread_data else 2.0
        
            # Get expected slippage
            expected_slippage = self.slippage_tracker.get_expected_slippage(symbol)
        
            # Total cost in pips (entry + exit)
            total_cost_pips = spread_cost + (expected_slippage * 2)  # Slippage on both entry and exit
        
            # Convert to percentage
            pip_value = 0.0001 if 'JPY' not in symbol else 0.01
            total_cost_percent = (total_cost_pips * pip_value / entry_price) * 100
        
            return total_cost_pips, {
                'spread_pips': spread_cost,
                'slippage_pips': expected_slippage * 2,
                'total_pips': total_cost_pips,
                'total_percent': total_cost_percent
            }
        except Exception as e:
            logger.error(f"Error in estimate_total_cost: {e}")
            raise
    
    def filter_signal(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter signal based on cost analysis"""
        # Calculate expected profit in pips
        try:
            pip_value = 0.0001 if 'JPY' not in symbol else 0.01
        
            profit_pips = abs(take_profit - entry_price) / pip_value
            risk_pips = abs(entry_price - stop_loss) / pip_value
        
            # Get total cost
            total_cost_pips, cost_breakdown = self.estimate_total_cost(symbol, entry_price)
        
            # Calculate profit to cost ratio
            net_profit_pips = profit_pips - total_cost_pips
            profit_to_cost_ratio = net_profit_pips / total_cost_pips if total_cost_pips > 0 else 0
        
            # Calculate cost as percentage of risk
            cost_to_risk_percent = (total_cost_pips / risk_pips) * 100 if risk_pips > 0 else 100
        
            details = {
                'profit_pips': profit_pips,
                'risk_pips': risk_pips,
                'cost_pips': total_cost_pips,
                'net_profit_pips': net_profit_pips,
                'profit_to_cost_ratio': profit_to_cost_ratio,
                'cost_to_risk_percent': cost_to_risk_percent,
                **cost_breakdown
            }
        
            # Filter decision
            if profit_to_cost_ratio < self.min_profit_to_cost_ratio:
                return False, f"Profit/cost ratio {profit_to_cost_ratio:.1f} below minimum {self.min_profit_to_cost_ratio}", details
        
            if cost_to_risk_percent > 30:
                return False, f"Cost {cost_to_risk_percent:.1f}% of risk is too high", details
        
            return True, f"Cost analysis passed (ratio: {profit_to_cost_ratio:.1f})", details
        except Exception as e:
            logger.error(f"Error in filter_signal: {e}")
            raise


class ExecutionQualityScorer:
    """Scores execution quality"""
    
    def __init__(
        self,
        spread_monitor: SpreadMonitor,
        slippage_tracker: SlippageTracker,
        config: Optional[Dict] = None
    ):
        try:
            self.spread_monitor = spread_monitor
            self.slippage_tracker = slippage_tracker
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score_execution(
        self,
        symbol: str,
        direction: str,
        expected_price: float,
        actual_price: float,
        execution_time_ms: float
    ) -> ExecutionReport:
        """Score execution quality"""
        # Get spread at entry
        try:
            spread_data = self.spread_monitor.get_current_spread(symbol)
            spread_pips = spread_data.spread_pips if spread_data else 0
        
            # Calculate slippage
            if direction.lower() == 'buy':
                slippage = actual_price - expected_price
            else:
                slippage = expected_price - actual_price
        
            pip_value = 0.0001 if 'JPY' not in symbol else 0.01
            slippage_pips = slippage / pip_value
        
            # Calculate total cost
            total_cost_pips = spread_pips + abs(slippage_pips)
            total_cost_percent = (total_cost_pips * pip_value / expected_price) * 100
        
            # Score components (0-100 each)
            spread_score = self._score_spread(symbol, spread_pips)
            slippage_score = self._score_slippage(slippage_pips)
            time_score = self._score_execution_time(execution_time_ms)
        
            # Overall score
            overall_score = (spread_score * 0.3 + slippage_score * 0.5 + time_score * 0.2)
        
            # Determine quality level
            if overall_score >= 85:
                quality = ExecutionQuality.EXCELLENT
            elif overall_score >= 70:
                quality = ExecutionQuality.GOOD
            elif overall_score >= 50:
                quality = ExecutionQuality.ACCEPTABLE
            elif overall_score >= 30:
                quality = ExecutionQuality.POOR
            else:
                quality = ExecutionQuality.VERY_POOR
        
            return ExecutionReport(
                symbol=symbol,
                quality=quality,
                spread_at_entry=spread_pips,
                slippage=slippage_pips,
                total_cost_percent=total_cost_percent,
                score=overall_score,
                details={
                    'spread_score': spread_score,
                    'slippage_score': slippage_score,
                    'time_score': time_score,
                    'execution_time_ms': execution_time_ms
                }
            )
        except Exception as e:
            logger.error(f"Error in score_execution: {e}")
            raise
    
    def _score_spread(self, symbol: str, spread_pips: float) -> float:
        """Score spread (0-100)"""
        try:
            typical = self.spread_monitor.TYPICAL_SPREADS.get(symbol, 2.0)
            ratio = spread_pips / typical
        
            if ratio <= 0.8:
                return 100
            elif ratio <= 1.0:
                return 90
            elif ratio <= 1.5:
                return 70
            elif ratio <= 2.0:
                return 50
            elif ratio <= 3.0:
                return 30
            else:
                return 10
        except Exception as e:
            logger.error(f"Error in _score_spread: {e}")
            raise
    
    def _score_slippage(self, slippage_pips: float) -> float:
        """Score slippage (0-100)"""
        try:
            abs_slippage = abs(slippage_pips)
        
            if slippage_pips < 0:  # Positive slippage (better than expected)
                return min(100, 90 + abs_slippage * 5)
            elif abs_slippage <= 0.5:
                return 90
            elif abs_slippage <= 1.0:
                return 75
            elif abs_slippage <= 2.0:
                return 50
            elif abs_slippage <= 3.0:
                return 30
            else:
                return 10
        except Exception as e:
            logger.error(f"Error in _score_slippage: {e}")
            raise
    
    def _score_execution_time(self, time_ms: float) -> float:
        """Score execution time (0-100)"""
        try:
            if time_ms <= 50:
                return 100
            elif time_ms <= 100:
                return 90
            elif time_ms <= 200:
                return 75
            elif time_ms <= 500:
                return 50
            elif time_ms <= 1000:
                return 30
            else:
                return 10
        except Exception as e:
            logger.error(f"Error in _score_execution_time: {e}")
            raise
    
    def get_execution_statistics(self, symbol: str = None) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            slippage_stats = self.slippage_tracker.get_slippage_statistics(symbol) if symbol else {}
            spread_stats = self.spread_monitor.get_spread_statistics(symbol) if symbol else {}
        
            return {
                'slippage': slippage_stats,
                'spread': spread_stats
            }
        except Exception as e:
            logger.error(f"Error in get_execution_statistics: {e}")
            raise


class SpreadSlippageManager:
    """
    Master spread and slippage management system.
    Combines all cost management functionality.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Initialize components
            self.spread_monitor = SpreadMonitor(self.config)
            self.slippage_tracker = SlippageTracker(self.config)
            self.high_spread_avoidance = HighSpreadAvoidance(self.spread_monitor, self.config)
            self.cost_filter = CostAdjustedFilter(self.spread_monitor, self.slippage_tracker, self.config)
            self.quality_scorer = ExecutionQualityScorer(self.spread_monitor, self.slippage_tracker, self.config)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_spread(self, symbol: str, bid: float, ask: float) -> SpreadData:
        """Update spread data"""
        return self.spread_monitor.update_spread(symbol, bid, ask)
    
    def record_execution(
        self,
        symbol: str,
        direction: str,
        expected_price: float,
        actual_price: float,
        quantity: float,
        execution_time_ms: float = 0
    ) -> Tuple[SlippageRecord, ExecutionReport]:
        """Record execution and get quality report"""
        # Record slippage
        try:
            slippage = self.slippage_tracker.record_slippage(
                symbol, direction, expected_price, actual_price, quantity, execution_time_ms
            )
        
            # Score execution
            report = self.quality_scorer.score_execution(
                symbol, direction, expected_price, actual_price, execution_time_ms
            )
        
            return slippage, report
        except Exception as e:
            logger.error(f"Error in record_execution: {e}")
            raise
    
    def should_trade(self, symbol: str) -> Tuple[bool, str]:
        """Check if should trade based on spread"""
        # Check spread condition
        try:
            spread_ok, spread_reason = self.spread_monitor.is_spread_acceptable(symbol)
            if not spread_ok:
                return False, spread_reason
        
            # Check high spread avoidance
            avoid, avoid_reason = self.high_spread_avoidance.should_avoid_trading(symbol)
            if avoid:
                return False, avoid_reason
        
            return True, "Spread conditions acceptable"
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise
    
    def filter_signal(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Filter signal based on costs"""
        return self.cost_filter.filter_signal(symbol, entry_price, stop_loss, take_profit)
    
    def estimate_costs(self, symbol: str, entry_price: float) -> Dict[str, Any]:
        """Estimate trading costs"""
        try:
            total_pips, breakdown = self.cost_filter.estimate_total_cost(symbol, entry_price)
            return {
                'total_cost_pips': total_pips,
                **breakdown
            }
        except Exception as e:
            logger.error(f"Error in estimate_costs: {e}")
            raise
    
    def get_cost_summary(self, symbol: str) -> Dict[str, Any]:
        """Get cost summary for symbol"""
        try:
            spread_stats = self.spread_monitor.get_spread_statistics(symbol)
            slippage_stats = self.slippage_tracker.get_slippage_statistics(symbol)
            condition, _ = self.spread_monitor.get_spread_condition(symbol)
        
            return {
                'symbol': symbol,
                'spread_condition': condition.value,
                'spread_stats': spread_stats,
                'slippage_stats': slippage_stats
            }
        except Exception as e:
            logger.error(f"Error in get_cost_summary: {e}")
            raise
    
    def learn_patterns(self, symbol: str):
        """Learn spread patterns"""
        try:
            self.high_spread_avoidance.learn_high_spread_periods(symbol)
        except Exception as e:
            logger.error(f"Error in learn_patterns: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        try:
            stats = {}
        
            for symbol in self.spread_monitor.spread_history.keys():
                stats[symbol] = self.get_cost_summary(symbol)
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise
