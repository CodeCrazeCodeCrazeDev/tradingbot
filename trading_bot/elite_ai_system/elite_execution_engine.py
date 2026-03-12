"""
Elite Execution Engine - Precision Entry and Exit Optimization

Implements institutional-grade execution:
- Entry timing optimization
- Exit optimization
- Order flow analysis
- Smart order routing
- Execution quality monitoring
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np
from collections import deque
import asyncio
import numpy

logger = logging.getLogger(__name__)


class ExecutionType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


class ExecutionQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class EntryOptimization:
    """Entry optimization results"""
    optimal_entry_price: float
    entry_zone_low: float
    entry_zone_high: float
    entry_timing_score: float
    order_flow_confirmation: bool
    recommended_execution_type: ExecutionType
    limit_price: Optional[float]
    urgency_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExitOptimization:
    """Exit optimization results"""
    optimal_exit_price: float
    take_profit_levels: List[float]
    stop_loss_level: float
    trailing_stop_distance: float
    exit_timing_score: float
    partial_exit_levels: List[Dict[str, float]]
    recommended_execution_type: ExecutionType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Execution result"""
    order_id: str
    symbol: str
    action: str
    requested_price: float
    executed_price: float
    slippage: float
    execution_time_ms: float
    execution_quality: ExecutionQuality
    fill_rate: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'action': self.action,
            'requested_price': self.requested_price,
            'executed_price': self.executed_price,
            'slippage': self.slippage,
            'execution_time_ms': self.execution_time_ms,
            'execution_quality': self.execution_quality.value,
            'fill_rate': self.fill_rate,
            'timestamp': self.timestamp.isoformat()
        }


class EliteExecutionEngine:
    """
    Elite Execution Engine
    
    Optimizes trade execution through:
    - Entry timing optimization
    - Exit strategy optimization
    - Order flow analysis
    - Smart order routing
    - Execution quality monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Execution parameters
            self.max_slippage = self.config.get('max_slippage', 0.001)  # 0.1%
            self.default_execution_type = ExecutionType(self.config.get('default_execution', 'limit'))
        
            # Partial exit configuration
            self.partial_exit_levels = self.config.get('partial_exit_levels', [0.33, 0.33, 0.34])
            self.partial_exit_targets = self.config.get('partial_exit_targets', [1.0, 2.0, 3.0])  # R multiples
        
            # History
            self.execution_history: deque = deque(maxlen=1000)
            self.execution_stats = {
                'total_executions': 0,
                'avg_slippage': 0,
                'fill_rate': 0,
                'excellent_count': 0,
                'poor_count': 0
            }
        
            logger.info("EliteExecutionEngine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def optimize_entry(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> EntryOptimization:
        """
        Optimize entry timing and price
        
        Args:
            signal: Trading signal
            market_data: Current market data
            
        Returns:
            EntryOptimization with optimal entry parameters
        """
        try:
            prices = market_data.get('prices', [])
            volumes = market_data.get('volumes', [])
            current_price = prices[-1] if prices else 0
            action = signal.get('action', 'HOLD')
        
            if len(prices) < 10 or action == 'HOLD':
                return EntryOptimization(
                    optimal_entry_price=current_price,
                    entry_zone_low=current_price,
                    entry_zone_high=current_price,
                    entry_timing_score=0.5,
                    order_flow_confirmation=False,
                    recommended_execution_type=ExecutionType.MARKET,
                    limit_price=None,
                    urgency_score=0.5
                )
        
            price_array = np.array(prices)
        
            # Calculate entry zone
            atr = self._calculate_atr(price_array)
        
            if action == 'BUY':
                # Look for pullback entry
                optimal_entry = current_price - (atr * 0.5)
                entry_zone_low = current_price - atr
                entry_zone_high = current_price + (atr * 0.25)
            else:  # SELL
                optimal_entry = current_price + (atr * 0.5)
                entry_zone_low = current_price - (atr * 0.25)
                entry_zone_high = current_price + atr
        
            # Entry timing score
            timing_score = self._calculate_entry_timing_score(price_array, action)
        
            # Order flow confirmation
            order_flow_confirmed = self._check_order_flow_confirmation(prices, volumes, action)
        
            # Urgency score
            urgency = self._calculate_urgency(price_array, action)
        
            # Determine execution type
            if urgency > 0.8:
                exec_type = ExecutionType.MARKET
                limit_price = None
            elif urgency > 0.5:
                exec_type = ExecutionType.LIMIT
                limit_price = optimal_entry
            else:
                exec_type = ExecutionType.LIMIT
                limit_price = optimal_entry
        
            return EntryOptimization(
                optimal_entry_price=optimal_entry,
                entry_zone_low=entry_zone_low,
                entry_zone_high=entry_zone_high,
                entry_timing_score=timing_score,
                order_flow_confirmation=order_flow_confirmed,
                recommended_execution_type=exec_type,
                limit_price=limit_price,
                urgency_score=urgency
            )
        except Exception as e:
            logger.error(f"Error in optimize_entry: {e}")
            raise
    
    async def optimize_exit(
        self,
        position: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> ExitOptimization:
        """
        Optimize exit strategy
        
        Args:
            position: Current position details
            market_data: Current market data
            
        Returns:
            ExitOptimization with optimal exit parameters
        """
        try:
            prices = market_data.get('prices', [])
            current_price = prices[-1] if prices else 0
            entry_price = position.get('entry_price', current_price)
            direction = position.get('direction', 'LONG')
        
            if len(prices) < 10:
                return ExitOptimization(
                    optimal_exit_price=current_price,
                    take_profit_levels=[current_price],
                    stop_loss_level=entry_price,
                    trailing_stop_distance=0,
                    exit_timing_score=0.5,
                    partial_exit_levels=[],
                    recommended_execution_type=ExecutionType.MARKET
                )
        
            price_array = np.array(prices)
            atr = self._calculate_atr(price_array)
        
            # Calculate stop loss
            if direction == 'LONG':
                stop_loss = entry_price - (atr * 2)
                risk = entry_price - stop_loss
            
                # Take profit levels (1R, 2R, 3R)
                take_profit_levels = [
                    entry_price + risk * self.partial_exit_targets[0],
                    entry_price + risk * self.partial_exit_targets[1],
                    entry_price + risk * self.partial_exit_targets[2]
                ]
            
                optimal_exit = take_profit_levels[1]  # Target 2R
                trailing_distance = atr * 1.5
            else:  # SHORT
                stop_loss = entry_price + (atr * 2)
                risk = stop_loss - entry_price
            
                take_profit_levels = [
                    entry_price - risk * self.partial_exit_targets[0],
                    entry_price - risk * self.partial_exit_targets[1],
                    entry_price - risk * self.partial_exit_targets[2]
                ]
            
                optimal_exit = take_profit_levels[1]
                trailing_distance = atr * 1.5
        
            # Partial exit levels
            partial_exits = []
            for i, (level, pct) in enumerate(zip(take_profit_levels, self.partial_exit_levels)):
                partial_exits.append({
                    'level': level,
                    'percentage': pct,
                    'r_multiple': self.partial_exit_targets[i]
                })
        
            # Exit timing score
            timing_score = self._calculate_exit_timing_score(price_array, direction, entry_price)
        
            return ExitOptimization(
                optimal_exit_price=optimal_exit,
                take_profit_levels=take_profit_levels,
                stop_loss_level=stop_loss,
                trailing_stop_distance=trailing_distance,
                exit_timing_score=timing_score,
                partial_exit_levels=partial_exits,
                recommended_execution_type=ExecutionType.LIMIT
            )
        except Exception as e:
            logger.error(f"Error in optimize_exit: {e}")
            raise
    
    def record_execution(
        self,
        order_id: str,
        symbol: str,
        action: str,
        requested_price: float,
        executed_price: float,
        execution_time_ms: float,
        fill_rate: float = 1.0
    ) -> ExecutionResult:
        """Record execution and calculate quality"""
        # Calculate slippage
        try:
            slippage = abs(executed_price - requested_price) / requested_price if requested_price > 0 else 0
        
            # Determine quality
            if slippage < 0.0001 and fill_rate == 1.0:
                quality = ExecutionQuality.EXCELLENT
            elif slippage < 0.0005 and fill_rate >= 0.95:
                quality = ExecutionQuality.GOOD
            elif slippage < 0.001 and fill_rate >= 0.8:
                quality = ExecutionQuality.FAIR
            else:
                quality = ExecutionQuality.POOR
        
            result = ExecutionResult(
                order_id=order_id,
                symbol=symbol,
                action=action,
                requested_price=requested_price,
                executed_price=executed_price,
                slippage=slippage,
                execution_time_ms=execution_time_ms,
                execution_quality=quality,
                fill_rate=fill_rate
            )
        
            # Update stats
            self.execution_history.append(result)
            self._update_execution_stats(result)
        
            logger.info(f"Execution recorded: {symbol} {action} - Quality: {quality.value}, Slippage: {slippage:.4%}")
        
            return result
        except Exception as e:
            logger.error(f"Error in record_execution: {e}")
            raise
    
    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(prices) < period + 1:
                return np.std(prices) * 2
        
            # Simplified ATR using price changes
            changes = np.abs(np.diff(prices))
            atr = np.mean(changes[-period:])
        
            return atr
        except Exception as e:
            logger.error(f"Error in _calculate_atr: {e}")
            raise
    
    def _calculate_entry_timing_score(self, prices: np.ndarray, action: str) -> float:
        """Calculate entry timing score (0-1)"""
        try:
            if len(prices) < 20:
                return 0.5
        
            current_price = prices[-1]
            sma_short = np.mean(prices[-5:])
            sma_long = np.mean(prices[-20:])
        
            # Score based on price position relative to MAs
            if action == 'BUY':
                # Good entry if price is near support
                if current_price < sma_short < sma_long:
                    return 0.8
                elif current_price < sma_short:
                    return 0.7
                elif current_price > sma_short * 1.02:
                    return 0.3  # Chasing
                else:
                    return 0.5
            else:  # SELL
                if current_price > sma_short > sma_long:
                    return 0.8
                elif current_price > sma_short:
                    return 0.7
                elif current_price < sma_short * 0.98:
                    return 0.3
                else:
                    return 0.5
        except Exception as e:
            logger.error(f"Error in _calculate_entry_timing_score: {e}")
            raise
    
    def _calculate_exit_timing_score(self, prices: np.ndarray, direction: str, entry_price: float) -> float:
        """Calculate exit timing score"""
        try:
            if len(prices) < 10:
                return 0.5
        
            current_price = prices[-1]
        
            # Calculate momentum
            momentum = (prices[-1] - prices[-5]) / prices[-5]
        
            if direction == 'LONG':
                # Good exit if momentum fading after profit
                if current_price > entry_price and momentum < 0:
                    return 0.8
                elif current_price > entry_price:
                    return 0.6
                else:
                    return 0.4
            else:  # SHORT
                if current_price < entry_price and momentum > 0:
                    return 0.8
                elif current_price < entry_price:
                    return 0.6
                else:
                    return 0.4
        except Exception as e:
            logger.error(f"Error in _calculate_exit_timing_score: {e}")
            raise
    
    def _check_order_flow_confirmation(self, prices: List[float], volumes: List[float], action: str) -> bool:
        """Check if order flow confirms the trade direction"""
        try:
            if not volumes or len(volumes) < 5:
                return False
        
            price_array = np.array(prices[-5:])
            volume_array = np.array(volumes[-5:])
        
            # Calculate volume-weighted direction
            price_changes = np.diff(price_array)
            weighted_direction = np.sum(price_changes * volume_array[1:])
        
            if action == 'BUY' and weighted_direction > 0:
                return True
            elif action == 'SELL' and weighted_direction < 0:
                return True
        
            return False
        except Exception as e:
            logger.error(f"Error in _check_order_flow_confirmation: {e}")
            raise
    
    def _calculate_urgency(self, prices: np.ndarray, action: str) -> float:
        """Calculate entry urgency score"""
        try:
            if len(prices) < 10:
                return 0.5
        
            # Calculate momentum
            momentum = (prices[-1] - prices[-5]) / prices[-5]
        
            if action == 'BUY':
                # High urgency if price moving up quickly
                if momentum > 0.01:
                    return 0.9
                elif momentum > 0.005:
                    return 0.7
                else:
                    return 0.4
            else:  # SELL
                if momentum < -0.01:
                    return 0.9
                elif momentum < -0.005:
                    return 0.7
                else:
                    return 0.4
        except Exception as e:
            logger.error(f"Error in _calculate_urgency: {e}")
            raise
    
    def _update_execution_stats(self, result: ExecutionResult):
        """Update execution statistics"""
        try:
            self.execution_stats['total_executions'] += 1
        
            # Update average slippage
            n = self.execution_stats['total_executions']
            old_avg = self.execution_stats['avg_slippage']
            self.execution_stats['avg_slippage'] = old_avg + (result.slippage - old_avg) / n
        
            # Update fill rate
            old_fill = self.execution_stats['fill_rate']
            self.execution_stats['fill_rate'] = old_fill + (result.fill_rate - old_fill) / n
        
            # Update quality counts
            if result.execution_quality == ExecutionQuality.EXCELLENT:
                self.execution_stats['excellent_count'] += 1
            elif result.execution_quality == ExecutionQuality.POOR:
                self.execution_stats['poor_count'] += 1
        except Exception as e:
            logger.error(f"Error in _update_execution_stats: {e}")
            raise
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        try:
            total = self.execution_stats['total_executions']
            return {
                'total_executions': total,
                'avg_slippage': self.execution_stats['avg_slippage'],
                'avg_fill_rate': self.execution_stats['fill_rate'],
                'excellent_rate': self.execution_stats['excellent_count'] / total if total > 0 else 0,
                'poor_rate': self.execution_stats['poor_count'] / total if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error in get_execution_stats: {e}")
            raise
