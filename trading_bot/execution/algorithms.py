import logging
logger = logging.getLogger(__name__)
"""Execution optimization algorithms for trading.

This module implements advanced execution algorithms like TWAP and VWAP
to optimize trade execution and minimize market impact.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from loguru import logger
import numpy
import pandas


class TWAPExecutor:
    """Time-Weighted Average Price execution algorithm.
    
    Splits a large order into smaller chunks distributed evenly over time
    to minimize market impact and achieve a price close to the time-weighted average.
    """
    
    def __init__(self, base_executor=None, config: Optional[Dict] = None):
        """Initialize the TWAP executor.
        
        Args:
            base_executor: Base executor to route orders through
            config: Configuration dictionary with TWAP parameters.
                   If None, default parameters will be used.
        """
        try:
            self.base_executor = base_executor
            self.mt5 = base_executor.mt5 if base_executor else None
            self.risk = base_executor.risk if base_executor else None
        
            self.config = config or {
                'num_chunks': 5,
                'interval_minutes': 2,
                'price_limit_pct': 0.1,  # 0.1% price deviation limit
                'allow_partial': True,
                'max_duration_minutes': 30
            }
            self.active_orders = []
            self.completed_orders = []
            self.start_time = None
            logger.info("TWAPExecutor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_execution_plan(self, symbol: str, direction: str, volume: float, 
                             current_price: float) -> Dict[str, Any]:
        """Create a TWAP execution plan for an order.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            volume: Total volume to execute
            current_price: Current market price
            
        Returns:
            Dictionary with execution plan details
        """
        try:
            num_chunks = self.config.get('num_chunks', 5)
            interval_minutes = self.config.get('interval_minutes', 2)
        
            # Calculate chunk size
            chunk_size = volume / num_chunks
        
            # Create execution schedule
            now = datetime.now()
            self.start_time = now
        
            schedule = []
            for i in range(num_chunks):
                execution_time = now + timedelta(minutes=i * interval_minutes)
                schedule.append({
                    'chunk_id': i + 1,
                    'planned_time': execution_time,
                    'volume': chunk_size,
                    'status': 'pending',
                    'executed_price': None
                })
        
            # Create execution plan
            plan = {
                'symbol': symbol,
                'direction': direction,
                'total_volume': volume,
                'chunk_size': chunk_size,
                'num_chunks': num_chunks,
                'interval_minutes': interval_minutes,
                'price_limit_pct': self.config.get('price_limit_pct', 0.1),
                'schedule': schedule,
                'status': 'active',
                'start_time': now,
                'expected_end_time': now + timedelta(minutes=(num_chunks - 1) * interval_minutes),
                'reference_price': current_price
            }
        
            self.active_orders.append(plan)
            logger.info(f"Created TWAP execution plan for {symbol} {direction} {volume} units")
            return plan
        except Exception as e:
            logger.error(f"Error in create_execution_plan: {e}")
            raise
    
    def execute_next_chunk(self, plan_id: int, current_price: float) -> Dict[str, Any]:
        """Execute the next chunk in the TWAP plan.
        
        Args:
            plan_id: ID of the execution plan
            current_price: Current market price
            
        Returns:
            Dictionary with execution details
        """
        try:
            if plan_id >= len(self.active_orders):
                logger.error(f"Invalid plan ID: {plan_id}")
                return {'success': False, 'error': 'Invalid plan ID'}
            
            plan = self.active_orders[plan_id]
        
            # Find next pending chunk
            next_chunk = None
            for chunk in plan['schedule']:
                if chunk['status'] == 'pending':
                    next_chunk = chunk
                    break
                
            if next_chunk is None:
                logger.info(f"No more pending chunks in plan {plan_id}")
                return {'success': False, 'error': 'No pending chunks'}
            
            # Check price limit
            price_limit_pct = plan.get('price_limit_pct', 0.1) / 100
            reference_price = plan.get('reference_price')
        
            if reference_price:
                price_deviation = abs(current_price - reference_price) / reference_price
                if price_deviation > price_limit_pct:
                    logger.warning(f"Price deviation ({price_deviation:.2%}) exceeds limit ({price_limit_pct:.2%})")
                    return {
                        'success': False, 
                        'error': 'Price deviation exceeds limit',
                        'chunk_id': next_chunk['chunk_id'],
                        'price_deviation': price_deviation
                    }
        
            # Execute chunk
            next_chunk['status'] = 'executed'
            next_chunk['executed_price'] = current_price
            next_chunk['actual_time'] = datetime.now()
        
            logger.info(f"Executed chunk {next_chunk['chunk_id']} of plan {plan_id} at price {current_price}")
        
            # Check if plan is complete
            pending_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'pending')
            if pending_chunks == 0:
                plan['status'] = 'completed'
                plan['end_time'] = datetime.now()
            
                # Calculate average execution price
                executed_prices = [chunk['executed_price'] for chunk in plan['schedule'] 
                                  if chunk['executed_price'] is not None]
                if executed_prices:
                    plan['average_price'] = sum(executed_prices) / len(executed_prices)
            
                # Move to completed orders
                self.completed_orders.append(plan)
                self.active_orders.pop(plan_id)
            
                logger.success(f"Completed TWAP execution plan {plan_id} with average price {plan.get('average_price')}")
        
            return {
                'success': True,
                'chunk_id': next_chunk['chunk_id'],
                'executed_price': current_price,
                'remaining_chunks': pending_chunks
            }
        except Exception as e:
            logger.error(f"Error in execute_next_chunk: {e}")
            raise
    
    def get_execution_status(self, plan_id: Optional[int] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get the status of execution plans.
        
        Args:
            plan_id: Optional ID of a specific plan to check
            
        Returns:
            Dictionary or list of dictionaries with execution status
        """
        try:
            if plan_id is not None:
                if plan_id < len(self.active_orders):
                    return self.active_orders[plan_id]
            
                # Check completed orders
                for plan in self.completed_orders:
                    if plan.get('id') == plan_id:
                        return plan
                    
                return {'error': 'Plan not found'}
        
            # Return all plans
            return {
                'active': self.active_orders,
                'completed': self.completed_orders
            }
        except Exception as e:
            logger.error(f"Error in get_execution_status: {e}")
            raise
    
    def cancel_execution(self, plan_id: int) -> Dict[str, Any]:
        """Cancel an active TWAP execution plan.
        
        Args:
            plan_id: ID of the execution plan to cancel
            
        Returns:
            Dictionary with cancellation details
        """
        try:
            if plan_id >= len(self.active_orders):
                logger.error(f"Invalid plan ID: {plan_id}")
                return {'success': False, 'error': 'Invalid plan ID'}
            
            plan = self.active_orders[plan_id]
        
            # Mark remaining chunks as cancelled
            for chunk in plan['schedule']:
                if chunk['status'] == 'pending':
                    chunk['status'] = 'cancelled'
                
            # Update plan status
            plan['status'] = 'cancelled'
            plan['end_time'] = datetime.now()
        
            # Calculate partial execution
            executed_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'executed')
            cancelled_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'cancelled')
        
            # Calculate average execution price for executed chunks
            executed_prices = [chunk['executed_price'] for chunk in plan['schedule'] 
                              if chunk['executed_price'] is not None]
            if executed_prices:
                plan['average_price'] = sum(executed_prices) / len(executed_prices)
        
            # Move to completed orders
            self.completed_orders.append(plan)
            self.active_orders.pop(plan_id)
        
            logger.info(f"Cancelled TWAP execution plan {plan_id}: {executed_chunks} executed, {cancelled_chunks} cancelled")
        
            return {
                'success': True,
                'plan_id': plan_id,
                'executed_chunks': executed_chunks,
                'cancelled_chunks': cancelled_chunks,
                'average_price': plan.get('average_price')
            }
        except Exception as e:
            logger.error(f"Error in cancel_execution: {e}")
            raise
        
    def process(self, signals: List, current_price: float) -> None:
        """Process signals using TWAP execution.
        
        Args:
            signals: List of trading signals to process
            current_price: Current market price
        """
        try:
            if not signals or not self.base_executor:
                return
            
            # Check if we should use TWAP algorithm
            signals_to_process = []
            for signal in signals:
                if self._should_use_algo(signal):
                    # Create TWAP execution plan
                    volume = self.risk.calculate_position_size(signal.symbol, signal.confidence)
                    plan = self.create_execution_plan(signal.symbol, signal.direction, volume, current_price)
                
                    # Execute first chunk immediately
                    self.execute_next_chunk(len(self.active_orders) - 1, current_price)
                else:
                    # Pass through to base executor
                    signals_to_process.append(signal)
                
            # Process remaining signals with base executor
            if signals_to_process and self.base_executor:
                self.base_executor.process(signals_to_process, current_price)
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise
            
    def _should_use_algo(self, signal) -> bool:
        """Determine if TWAP algorithm should be used for this signal.
        
        Args:
            signal: Trading signal to evaluate
            
        Returns:
            True if TWAP should be used, False otherwise
        """
        # Use TWAP for signals with high confidence and large position size
        try:
            if not self.risk:
                return False
            
            position_size = self.risk.calculate_position_size(signal.symbol, signal.confidence)
            return position_size >= 0.5 and signal.confidence >= 70.0
        except Exception as e:
            logger.error(f"Error in _should_use_algo: {e}")
            raise


class VWAPExecutor:
    """Volume-Weighted Average Price execution algorithm.
    
    Executes orders based on historical volume profiles to achieve
    a price close to the volume-weighted average price.
    """
    
    def __init__(self, base_executor=None, config: Optional[Dict] = None):
        """Initialize the VWAP executor.
        
        Args:
            base_executor: Base executor to route orders through
            config: Configuration dictionary with VWAP parameters.
                   If None, default parameters will be used.
        """
        try:
            self.base_executor = base_executor
            self.mt5 = base_executor.mt5 if base_executor else None
            self.risk = base_executor.risk if base_executor else None
        
            self.config = config or {
                'num_chunks': 5,
                'price_limit_pct': 0.1,  # 0.1% price deviation limit
                'allow_partial': True,
                'max_duration_minutes': 60,
                'historical_volume_periods': 5  # Number of historical periods to analyze
            }
            self.active_orders = []
            self.completed_orders = []
            self.volume_profiles = {}  # Cache for volume profiles
            logger.info("VWAPExecutor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_volume_profile(self, symbol: str, timeframe: str = 'H1', 
                          periods: int = None) -> Dict[str, float]:
        """Get historical volume profile for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for volume analysis
            periods: Number of historical periods to analyze
            
        Returns:
            Dictionary with volume distribution by hour
        """
        # This is a placeholder for actual volume profile retrieval
        # In a real implementation, this would analyze historical volume data
        
        try:
            periods = periods or self.config.get('historical_volume_periods', 5)
        
            # Check if we have cached profile
            cache_key = f"{symbol}_{timeframe}_{periods}"
            if cache_key in self.volume_profiles:
                return self.volume_profiles[cache_key]
            
            logger.info(f"Generating volume profile for {symbol} on {timeframe} timeframe")
        
            # Generate mock volume profile for demonstration
            # In a real implementation, this would analyze actual historical data
        
            # Create hourly distribution (24-hour format)
            hourly_profile = {}
        
            # Typical market hours have higher volume
            for hour in range(24):
                if 8 <= hour < 11:  # Morning session
                    hourly_profile[hour] = 0.15  # 15% per hour
                elif 11 <= hour < 16:  # Mid-day
                    hourly_profile[hour] = 0.1  # 10% per hour
                elif 16 <= hour < 18:  # Closing session
                    hourly_profile[hour] = 0.12  # 12% per hour
                else:  # Off-hours
                    hourly_profile[hour] = 0.02  # 2% per hour
        
            # Normalize to ensure sum is 1.0
            total = sum(hourly_profile.values())
            for hour in hourly_profile:
                hourly_profile[hour] /= total
            
            # Cache the profile
            self.volume_profiles[cache_key] = hourly_profile
        
            return hourly_profile
        except Exception as e:
            logger.error(f"Error in get_volume_profile: {e}")
            raise
    
    def create_execution_plan(self, symbol: str, direction: str, volume: float, 
                             current_price: float, timeframe: str = 'H1') -> Dict[str, Any]:
        """Create a VWAP execution plan for an order.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            volume: Total volume to execute
            current_price: Current market price
            timeframe: Timeframe for volume analysis
            
        Returns:
            Dictionary with execution plan details
        """
        try:
            num_chunks = self.config.get('num_chunks', 5)
        
            # Get volume profile
            volume_profile = self.get_volume_profile(symbol, timeframe)
        
            # Current hour
            current_hour = datetime.now().hour
        
            # Create execution schedule based on volume profile
            now = datetime.now()
            schedule = []
        
            # Determine execution hours
            execution_hours = []
            hour = current_hour
        
            for _ in range(num_chunks):
                execution_hours.append(hour)
                hour = (hour + 1) % 24
            
            # Calculate volume for each hour based on profile
            total_profile_weight = sum(volume_profile.get(h, 0.01) for h in execution_hours)
        
            for i, hour in enumerate(execution_hours):
                # Calculate minutes until this hour
                if hour < current_hour:
                    hours_diff = 24 - current_hour + hour
                else:
                    hours_diff = hour - current_hour
                
                execution_time = now + timedelta(hours=hours_diff)
            
                # Calculate volume based on profile
                weight = volume_profile.get(hour, 0.01) / total_profile_weight
                chunk_volume = volume * weight
            
                schedule.append({
                    'chunk_id': i + 1,
                    'planned_time': execution_time,
                    'hour': hour,
                    'volume': chunk_volume,
                    'volume_weight': weight,
                    'status': 'pending',
                    'executed_price': None
                })
        
            # Create execution plan
            plan = {
                'symbol': symbol,
                'direction': direction,
                'total_volume': volume,
                'num_chunks': num_chunks,
                'price_limit_pct': self.config.get('price_limit_pct', 0.1),
                'schedule': schedule,
                'status': 'active',
                'start_time': now,
                'expected_end_time': max(chunk['planned_time'] for chunk in schedule),
                'reference_price': current_price
            }
        
            self.active_orders.append(plan)
            logger.info(f"Created VWAP execution plan for {symbol} {direction} {volume} units")
            return plan
        except Exception as e:
            logger.error(f"Error in create_execution_plan: {e}")
            raise
    
    def execute_next_chunk(self, plan_id: int, current_price: float) -> Dict[str, Any]:
        """Execute the next chunk in the VWAP plan.
        
        Args:
            plan_id: ID of the execution plan
            current_price: Current market price
            
        Returns:
            Dictionary with execution details
        """
        try:
            if plan_id >= len(self.active_orders):
                logger.error(f"Invalid plan ID: {plan_id}")
                return {'success': False, 'error': 'Invalid plan ID'}
            
            plan = self.active_orders[plan_id]
        
            # Find next pending chunk
            next_chunk = None
            for chunk in plan['schedule']:
                if chunk['status'] == 'pending':
                    next_chunk = chunk
                    break
                
            if next_chunk is None:
                logger.info(f"No more pending chunks in plan {plan_id}")
                return {'success': False, 'error': 'No pending chunks'}
            
            # Check price limit
            price_limit_pct = plan.get('price_limit_pct', 0.1) / 100
            reference_price = plan.get('reference_price')
        
            if reference_price:
                price_deviation = abs(current_price - reference_price) / reference_price
                if price_deviation > price_limit_pct:
                    logger.warning(f"Price deviation ({price_deviation:.2%}) exceeds limit ({price_limit_pct:.2%})")
                    return {
                        'success': False, 
                        'error': 'Price deviation exceeds limit',
                        'chunk_id': next_chunk['chunk_id'],
                        'price_deviation': price_deviation
                    }
        
            # Execute chunk
            next_chunk['status'] = 'executed'
            next_chunk['executed_price'] = current_price
            next_chunk['actual_time'] = datetime.now()
        
            logger.info(f"Executed chunk {next_chunk['chunk_id']} of plan {plan_id} at price {current_price}")
        
            # Check if plan is complete
            pending_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'pending')
            if pending_chunks == 0:
                plan['status'] = 'completed'
                plan['end_time'] = datetime.now()
            
                # Calculate volume-weighted average execution price
                total_volume = 0
                volume_price_sum = 0
            
                for chunk in plan['schedule']:
                    if chunk['executed_price'] is not None:
                        volume = chunk['volume']
                        total_volume += volume
                        volume_price_sum += volume * chunk['executed_price']
            
                if total_volume > 0:
                    plan['average_price'] = volume_price_sum / total_volume
            
                # Move to completed orders
                self.completed_orders.append(plan)
                self.active_orders.pop(plan_id)
            
                logger.success(f"Completed VWAP execution plan {plan_id} with average price {plan.get('average_price')}")
        
            return {
                'success': True,
                'chunk_id': next_chunk['chunk_id'],
                'executed_price': current_price,
                'remaining_chunks': pending_chunks
            }
        except Exception as e:
            logger.error(f"Error in execute_next_chunk: {e}")
            raise
    
    def get_execution_status(self, plan_id: Optional[int] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get the status of execution plans.
        
        Args:
            plan_id: Optional ID of a specific plan to check
            
        Returns:
            Dictionary or list of dictionaries with execution status
        """
        try:
            if plan_id is not None:
                if plan_id < len(self.active_orders):
                    return self.active_orders[plan_id]
            
                # Check completed orders
                for plan in self.completed_orders:
                    if plan.get('id') == plan_id:
                        return plan
                    
                return {'error': 'Plan not found'}
        
            # Return all plans
            return {
                'active': self.active_orders,
                'completed': self.completed_orders
            }
        except Exception as e:
            logger.error(f"Error in get_execution_status: {e}")
            raise
    
    def cancel_execution(self, plan_id: int) -> Dict[str, Any]:
        """Cancel an active VWAP execution plan.
        
        Args:
            plan_id: ID of the execution plan to cancel
            
        Returns:
            Dictionary with cancellation details
        """
        try:
            if plan_id >= len(self.active_orders):
                logger.error(f"Invalid plan ID: {plan_id}")
                return {'success': False, 'error': 'Invalid plan ID'}
            
            plan = self.active_orders[plan_id]
        
            # Mark remaining chunks as cancelled
            for chunk in plan['schedule']:
                if chunk['status'] == 'pending':
                    chunk['status'] = 'cancelled'
                
            # Update plan status
            plan['status'] = 'cancelled'
            plan['end_time'] = datetime.now()
        
            # Calculate partial execution
            executed_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'executed')
            cancelled_chunks = sum(1 for chunk in plan['schedule'] if chunk['status'] == 'cancelled')
        
            # Calculate volume-weighted average execution price for executed chunks
            total_volume = 0
            volume_price_sum = 0
        
            for chunk in plan['schedule']:
                if chunk['status'] == 'executed' and chunk['executed_price'] is not None:
                    volume = chunk['volume']
                    total_volume += volume
                    volume_price_sum += volume * chunk['executed_price']
        
            if total_volume > 0:
                plan['average_price'] = volume_price_sum / total_volume
        
            # Move to completed orders
            self.completed_orders.append(plan)
            self.active_orders.pop(plan_id)
        
            logger.info(f"Cancelled VWAP execution plan {plan_id}: {executed_chunks} executed, {cancelled_chunks} cancelled")
        
            return {
                'success': True,
                'plan_id': plan_id,
                'executed_chunks': executed_chunks,
                'cancelled_chunks': cancelled_chunks,
                'average_price': plan.get('average_price')
            }
        except Exception as e:
            logger.error(f"Error in cancel_execution: {e}")
            raise
        
    def process(self, signals: List, current_price: float) -> None:
        """Process signals using VWAP execution.
        
        Args:
            signals: List of trading signals to process
            current_price: Current market price
        """
        try:
            if not signals or not self.base_executor:
                return
            
            # Check if we should use VWAP algorithm
            signals_to_process = []
            for signal in signals:
                if self._should_use_algo(signal):
                    # Create VWAP execution plan
                    volume = self.risk.calculate_position_size(signal.symbol, signal.confidence)
                    plan = self.create_execution_plan(signal.symbol, signal.direction, volume, current_price)
                
                    # Execute first chunk immediately
                    self.execute_next_chunk(len(self.active_orders) - 1, current_price)
                else:
                    # Pass through to base executor
                    signals_to_process.append(signal)
                
            # Process remaining signals with base executor
            if signals_to_process and self.base_executor:
                self.base_executor.process(signals_to_process, current_price)
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise
            
    def _should_use_algo(self, signal) -> bool:
        """Determine if VWAP algorithm should be used for this signal.
        
        Args:
            signal: Trading signal to evaluate
            
        Returns:
            True if VWAP should be used, False otherwise
        """
        # Use VWAP for signals with high confidence and large position size
        try:
            if not self.risk:
                return False
            
            position_size = self.risk.calculate_position_size(signal.symbol, signal.confidence)
            return position_size >= 1.0 and signal.confidence >= 80.0
        except Exception as e:
            logger.error(f"Error in _should_use_algo: {e}")
            raise


class SmartOrderRouter:
    """Smart order routing system.
    
    Routes orders to optimal execution venues and algorithms
    based on market conditions and order characteristics.
    """
    
    def __init__(self, base_executor=None):
        """Initialize the smart order router.
        
        Args:
            base_executor: Base executor to route orders through
        """
        try:
            self.base_executor = base_executor
            self.mt5 = base_executor.mt5 if base_executor else None
            self.risk = base_executor.risk if base_executor else None
        
            self.twap_executor = TWAPExecutor(base_executor)
            self.vwap_executor = VWAPExecutor(base_executor)
            self.execution_stats = {
                'total_orders': 0,
                'twap_orders': 0,
                'vwap_orders': 0,
                'market_orders': 0
            }
            logger.info("SmartOrderRouter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process(self, signals: List, current_price: float) -> None:
        """Process signals using smart order routing.
        
        Args:
            signals: List of trading signals to process
            current_price: Current market price
        """
        try:
            if not signals or not self.base_executor:
                return
            
            # Simply pass signals to base executor for now
            self.base_executor.process(signals, current_price)
        except Exception as e:
            logger.error(f"Error in process: {e}")
            raise
        
    def route_order(self, symbol: str, direction: str, volume: float, 
                   current_price: float, urgency: str = 'normal') -> Dict[str, Any]:
        """Route an order to the optimal execution algorithm.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            volume: Total volume to execute
            current_price: Current market price
            urgency: Order urgency ('low', 'normal', 'high')
            
        Returns:
            Dictionary with routing details
        """
        try:
            self.execution_stats['total_orders'] += 1
        
            # Determine optimal execution algorithm based on order characteristics
            if volume > 100 and urgency == 'low':
                # Use VWAP for large, non-urgent orders
                logger.info(f"Routing {symbol} order to VWAP executor")
                plan = self.vwap_executor.create_execution_plan(symbol, direction, volume, current_price)
                self.execution_stats['vwap_orders'] += 1
                return {
                    'algorithm': 'vwap',
                    'plan_id': len(self.vwap_executor.active_orders) - 1,
                    'plan': plan
                }
            elif volume > 50 and urgency != 'high':
                # Use TWAP for medium-sized orders with normal urgency
                logger.info(f"Routing {symbol} order to TWAP executor")
                plan = self.twap_executor.create_execution_plan(symbol, direction, volume, current_price)
                self.execution_stats['twap_orders'] += 1
                return {
                    'algorithm': 'twap',
                    'plan_id': len(self.twap_executor.active_orders) - 1,
                    'plan': plan
                }
            else:
                # Use market order for small or urgent orders
                logger.info(f"Routing {symbol} order as market order")
                self.execution_stats['market_orders'] += 1
                return {
                    'algorithm': 'market',
                    'symbol': symbol,
                    'direction': direction,
                    'volume': volume,
                    'price': current_price
                }
        except Exception as e:
            logger.error(f"Error in route_order: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        try:
            stats = self.execution_stats.copy()
        
            # Calculate percentages
            total = stats['total_orders']
            if total > 0:
                stats['twap_pct'] = stats['twap_orders'] / total * 100
                stats['vwap_pct'] = stats['vwap_orders'] / total * 100
                stats['market_pct'] = stats['market_orders'] / total * 100
            
            return stats
        except Exception as e:
            logger.error(f"Error in get_stats: {e}")
            raise
        
    def _execute_with_twap(self, signals: List, current_price: float) -> None:
        """Execute signals using TWAP algorithm."""
        try:
            for signal in signals:
                volume = self.risk.calculate_position_size(signal.symbol, signal.confidence)
                plan = self.twap_executor.create_execution_plan(signal.symbol, signal.direction, volume, current_price)
                self.twap_executor.execute_next_chunk(len(self.twap_executor.active_orders) - 1, current_price)
        except Exception as e:
            logger.error(f"Error in _execute_with_twap: {e}")
            raise
            
    def _execute_with_vwap(self, signals: List, current_price: float) -> None:
        """Execute signals using VWAP algorithm."""
        try:
            for signal in signals:
                volume = self.risk.calculate_position_size(signal.symbol, signal.confidence)
                plan = self.vwap_executor.create_execution_plan(signal.symbol, signal.direction, volume, current_price)
                self.vwap_executor.execute_next_chunk(len(self.vwap_executor.active_orders) - 1, current_price)
        except Exception as e:
            logger.error(f"Error in _execute_with_vwap: {e}")
            raise
            
    def _execute_with_market(self, signals: List, current_price: float) -> None:
        """Execute signals using market orders."""
        try:
            if self.base_executor:
                self.base_executor.process(signals, current_price)
        except Exception as e:
            logger.error(f"Error in _execute_with_market: {e}")
            raise
