"""
Execution Quality Monitor - Answers Q141-Q150, Q161-Q170
========================================================

Critical Question Q141: How do you measure execution quality, and what metrics do you track?
Critical Question Q142: What is your expected slippage model, and how do you validate it?
Critical Question Q161: How do you model the permanent vs. temporary market impact of your trades?

This module provides:
1. Real-time execution quality tracking
2. Slippage measurement and analysis
3. Market impact modeling
4. Fill rate monitoring
5. Execution cost analysis
6. Latency tracking
"""

import logging
import threading
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class ExecutionQuality(Enum):
    """Execution quality classification"""
    EXCELLENT = "excellent"    # Better than expected
    GOOD = "good"              # Within expectations
    ACCEPTABLE = "acceptable"  # Slightly worse than expected
    POOR = "poor"              # Significantly worse
    UNACCEPTABLE = "unacceptable"  # Requires investigation


class SlippageType(Enum):
    """Types of slippage"""
    POSITIVE = "positive"      # Got better price than expected
    ZERO = "zero"              # Got expected price
    NEGATIVE = "negative"      # Got worse price than expected


@dataclass
class ExecutionRecord:
    """Record of a single execution"""
    execution_id: str
    order_id: str
    symbol: str
    direction: str  # 'buy' or 'sell'
    expected_price: float
    executed_price: float
    quantity: float
    timestamp_sent: datetime
    timestamp_filled: datetime
    venue: str
    order_type: str
    
    # Calculated metrics
    slippage_bps: float = 0.0
    slippage_type: SlippageType = SlippageType.ZERO
    latency_ms: float = 0.0
    market_impact_bps: float = 0.0
    
    def __post_init__(self):
        # Calculate slippage in basis points
        if self.expected_price > 0:
            if self.direction == 'buy':
                self.slippage_bps = ((self.executed_price - self.expected_price) / self.expected_price) * 10000
            else:
                self.slippage_bps = ((self.expected_price - self.executed_price) / self.expected_price) * 10000
        
        # Classify slippage
        if self.slippage_bps < -0.5:
            self.slippage_type = SlippageType.POSITIVE
        elif self.slippage_bps > 0.5:
            self.slippage_type = SlippageType.NEGATIVE
        else:
            self.slippage_type = SlippageType.ZERO
        
        # Calculate latency
        self.latency_ms = (self.timestamp_filled - self.timestamp_sent).total_seconds() * 1000
    
    def to_dict(self) -> Dict:
        return {
            'execution_id': self.execution_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'expected_price': self.expected_price,
            'executed_price': self.executed_price,
            'quantity': self.quantity,
            'slippage_bps': self.slippage_bps,
            'slippage_type': self.slippage_type.value,
            'latency_ms': self.latency_ms,
            'market_impact_bps': self.market_impact_bps,
            'timestamp_filled': self.timestamp_filled.isoformat()
        }


@dataclass
class ExecutionMetrics:
    """Aggregated execution metrics"""
    timestamp: datetime
    period: str  # 'hourly', 'daily', 'weekly'
    
    # Volume metrics
    total_executions: int
    total_volume: float
    total_notional: float
    
    # Slippage metrics
    avg_slippage_bps: float
    median_slippage_bps: float
    max_slippage_bps: float
    slippage_std_bps: float
    positive_slippage_pct: float
    negative_slippage_pct: float
    
    # Fill metrics
    fill_rate: float
    partial_fill_rate: float
    rejection_rate: float
    
    # Latency metrics
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Market impact
    avg_market_impact_bps: float
    permanent_impact_bps: float
    temporary_impact_bps: float
    
    # Cost metrics
    total_slippage_cost: float
    total_commission_cost: float
    total_execution_cost: float
    
    # Quality
    execution_quality: ExecutionQuality
    quality_score: float  # 0-100
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'period': self.period,
            'total_executions': self.total_executions,
            'total_volume': self.total_volume,
            'avg_slippage_bps': self.avg_slippage_bps,
            'median_slippage_bps': self.median_slippage_bps,
            'fill_rate': self.fill_rate,
            'avg_latency_ms': self.avg_latency_ms,
            'p95_latency_ms': self.p95_latency_ms,
            'avg_market_impact_bps': self.avg_market_impact_bps,
            'total_execution_cost': self.total_execution_cost,
            'execution_quality': self.execution_quality.value,
            'quality_score': self.quality_score
        }


class ExecutionQualityMonitor:
    """
    Monitors and analyzes execution quality.
    
    Addresses critical questions:
    - Q141: Execution quality measurement
    - Q142: Slippage model validation
    - Q161: Market impact modeling
    
    Features:
    - Real-time slippage tracking
    - Market impact estimation
    - Fill rate monitoring
    - Latency analysis
    - Cost attribution
    - Quality scoring
    """
    
    # Expected slippage thresholds (basis points)
    EXPECTED_SLIPPAGE_BPS = {
        'market': 5.0,
        'limit': 0.0,
        'stop': 10.0,
        'stop_limit': 5.0
    }
    
    # Quality thresholds
    QUALITY_THRESHOLDS = {
        'excellent': {'slippage': 2.0, 'fill_rate': 0.99, 'latency_p95': 100},
        'good': {'slippage': 5.0, 'fill_rate': 0.95, 'latency_p95': 250},
        'acceptable': {'slippage': 10.0, 'fill_rate': 0.90, 'latency_p95': 500},
        'poor': {'slippage': 20.0, 'fill_rate': 0.80, 'latency_p95': 1000}
    }
    
    def __init__(
        self,
        history_size: int = 10000,
        commission_rate: float = 0.0001,  # 1 bps
        on_quality_degradation: Optional[callable] = None,
        on_slippage_alert: Optional[callable] = None
    ):
        """
        Initialize execution quality monitor.
        
        Args:
            history_size: Number of executions to keep
            commission_rate: Commission rate for cost calculation
            on_quality_degradation: Callback when quality degrades
            on_slippage_alert: Callback for slippage alerts
        """
        self.history_size = history_size
        self.commission_rate = commission_rate
        self.on_quality_degradation = on_quality_degradation
        self.on_slippage_alert = on_slippage_alert
        
        # Execution history
        self._lock = threading.RLock()
        self._executions: deque = deque(maxlen=history_size)
        self._executions_by_symbol: Dict[str, deque] = {}
        
        # Order tracking
        self._pending_orders: Dict[str, Dict] = {}
        self._rejected_orders: List[Dict] = []
        self._partial_fills: Dict[str, List] = {}
        
        # Market impact tracking
        self._pre_trade_prices: Dict[str, float] = {}
        self._post_trade_prices: Dict[str, List] = {}
        
        # Metrics cache
        self._hourly_metrics: Optional[ExecutionMetrics] = None
        self._daily_metrics: Optional[ExecutionMetrics] = None
        self._last_metrics_update = datetime.min
        
        # Slippage model
        self._slippage_model: Dict[str, Dict] = {}
        
        logger.info("ExecutionQualityMonitor initialized")
    
    def record_order_sent(
        self,
        order_id: str,
        symbol: str,
        direction: str,
        quantity: float,
        expected_price: float,
        order_type: str,
        venue: str = "default"
    ):
        """Record when an order is sent"""
        with self._lock:
            self._pending_orders[order_id] = {
                'order_id': order_id,
                'symbol': symbol,
                'direction': direction,
                'quantity': quantity,
                'expected_price': expected_price,
                'order_type': order_type,
                'venue': venue,
                'timestamp_sent': datetime.now()
            }
            
            # Record pre-trade price for market impact
            self._pre_trade_prices[order_id] = expected_price
    
    def record_execution(
        self,
        order_id: str,
        execution_id: str,
        executed_price: float,
        executed_quantity: float,
        timestamp_filled: Optional[datetime] = None
    ) -> Optional[ExecutionRecord]:
        """
        Record an execution.
        
        This is the answer to Q141: How do you measure execution quality?
        
        Args:
            order_id: Original order ID
            execution_id: Unique execution ID
            executed_price: Price at which order was filled
            executed_quantity: Quantity filled
            timestamp_filled: Fill timestamp
            
        Returns:
            ExecutionRecord with calculated metrics
        """
        timestamp_filled = timestamp_filled or datetime.now()
        
        with self._lock:
            if order_id not in self._pending_orders:
                logger.warning(f"Execution for unknown order: {order_id}")
                return None
            
            order = self._pending_orders[order_id]
            
            # Create execution record
            record = ExecutionRecord(
                execution_id=execution_id,
                order_id=order_id,
                symbol=order['symbol'],
                direction=order['direction'],
                expected_price=order['expected_price'],
                executed_price=executed_price,
                quantity=executed_quantity,
                timestamp_sent=order['timestamp_sent'],
                timestamp_filled=timestamp_filled,
                venue=order['venue'],
                order_type=order['order_type']
            )
            
            # Store execution
            self._executions.append(record)
            
            if order['symbol'] not in self._executions_by_symbol:
                self._executions_by_symbol[order['symbol']] = deque(maxlen=1000)
            self._executions_by_symbol[order['symbol']].append(record)
            
            # Check for partial fill
            if executed_quantity < order['quantity']:
                if order_id not in self._partial_fills:
                    self._partial_fills[order_id] = []
                self._partial_fills[order_id].append(record)
            else:
                # Order complete, remove from pending
                del self._pending_orders[order_id]
            
            # Update slippage model
            self._update_slippage_model(record)
            
            # Check for alerts
            self._check_slippage_alert(record)
            
            return record
    
    def record_rejection(self, order_id: str, reason: str):
        """Record an order rejection"""
        with self._lock:
            if order_id in self._pending_orders:
                order = self._pending_orders.pop(order_id)
                order['rejection_reason'] = reason
                order['rejected_at'] = datetime.now()
                self._rejected_orders.append(order)
                
                # Limit rejection history
                if len(self._rejected_orders) > 1000:
                    self._rejected_orders = self._rejected_orders[-500:]
    
    def record_post_trade_price(self, order_id: str, price: float, delay_seconds: float):
        """Record price after trade for market impact calculation"""
        with self._lock:
            if order_id not in self._post_trade_prices:
                self._post_trade_prices[order_id] = []
            self._post_trade_prices[order_id].append({
                'price': price,
                'delay_seconds': delay_seconds,
                'timestamp': datetime.now()
            })
    
    def _update_slippage_model(self, record: ExecutionRecord):
        """
        Update slippage model with new execution.
        
        This is the answer to Q142: What is your expected slippage model?
        """
        key = f"{record.symbol}_{record.order_type}"
        
        if key not in self._slippage_model:
            self._slippage_model[key] = {
                'samples': deque(maxlen=500),
                'mean': 0.0,
                'std': 0.0,
                'last_updated': None
            }
        
        model = self._slippage_model[key]
        model['samples'].append(record.slippage_bps)
        
        if len(model['samples']) >= 10:
            samples = list(model['samples'])
            model['mean'] = statistics.mean(samples)
            model['std'] = statistics.stdev(samples) if len(samples) > 1 else 0
            model['last_updated'] = datetime.now()
    
    def _check_slippage_alert(self, record: ExecutionRecord):
        """Check if slippage warrants an alert"""
        expected = self.EXPECTED_SLIPPAGE_BPS.get(record.order_type, 5.0)
        
        if record.slippage_bps > expected * 3:
            logger.warning(
                f"High slippage alert: {record.symbol} {record.slippage_bps:.1f} bps "
                f"(expected: {expected:.1f} bps)"
            )
            
            if self.on_slippage_alert:
                try:
                    self.on_slippage_alert(record)
                except Exception as e:
                    logger.error(f"Slippage alert callback error: {e}")
    
    def calculate_market_impact(self, order_id: str) -> Dict:
        """
        Calculate market impact for an order.
        
        This is the answer to Q161: How do you model permanent vs. temporary market impact?
        
        Returns:
            Dictionary with impact metrics
        """
        with self._lock:
            if order_id not in self._pre_trade_prices:
                return {'error': 'No pre-trade price recorded'}
            
            pre_price = self._pre_trade_prices[order_id]
            post_prices = self._post_trade_prices.get(order_id, [])
            
            if not post_prices:
                return {'error': 'No post-trade prices recorded'}
            
            # Find execution
            execution = None
            for ex in self._executions:
                if ex.order_id == order_id:
                    execution = ex
                    break
            
            if not execution:
                return {'error': 'Execution not found'}
            
            # Calculate immediate impact (execution price vs pre-trade)
            if execution.direction == 'buy':
                immediate_impact_bps = ((execution.executed_price - pre_price) / pre_price) * 10000
            else:
                immediate_impact_bps = ((pre_price - execution.executed_price) / pre_price) * 10000
            
            # Calculate temporary vs permanent impact
            # Temporary: impact that reverses within 5 minutes
            # Permanent: impact that persists after 5 minutes
            
            short_term_prices = [p for p in post_prices if p['delay_seconds'] <= 60]
            long_term_prices = [p for p in post_prices if p['delay_seconds'] >= 300]
            
            if short_term_prices:
                short_term_avg = statistics.mean([p['price'] for p in short_term_prices])
                if execution.direction == 'buy':
                    short_term_impact = ((short_term_avg - pre_price) / pre_price) * 10000
                else:
                    short_term_impact = ((pre_price - short_term_avg) / pre_price) * 10000
            else:
                short_term_impact = immediate_impact_bps
            
            if long_term_prices:
                long_term_avg = statistics.mean([p['price'] for p in long_term_prices])
                if execution.direction == 'buy':
                    permanent_impact = ((long_term_avg - pre_price) / pre_price) * 10000
                else:
                    permanent_impact = ((pre_price - long_term_avg) / pre_price) * 10000
            else:
                permanent_impact = short_term_impact * 0.5  # Estimate
            
            temporary_impact = immediate_impact_bps - permanent_impact
            
            return {
                'order_id': order_id,
                'immediate_impact_bps': immediate_impact_bps,
                'short_term_impact_bps': short_term_impact,
                'permanent_impact_bps': permanent_impact,
                'temporary_impact_bps': temporary_impact,
                'impact_decay_ratio': temporary_impact / immediate_impact_bps if immediate_impact_bps != 0 else 0
            }
    
    def get_metrics(self, period: str = 'hourly') -> ExecutionMetrics:
        """
        Get aggregated execution metrics.
        
        Args:
            period: 'hourly', 'daily', or 'weekly'
            
        Returns:
            ExecutionMetrics for the period
        """
        with self._lock:
            # Determine time window
            now = datetime.now()
            if period == 'hourly':
                start_time = now - timedelta(hours=1)
            elif period == 'daily':
                start_time = now - timedelta(days=1)
            elif period == 'weekly':
                start_time = now - timedelta(weeks=1)
            else:
                start_time = now - timedelta(hours=1)
            
            # Filter executions
            executions = [
                e for e in self._executions
                if e.timestamp_filled >= start_time
            ]
            
            if not executions:
                return self._empty_metrics(period)
            
            # Calculate metrics
            slippages = [e.slippage_bps for e in executions]
            latencies = [e.latency_ms for e in executions]
            volumes = [e.quantity for e in executions]
            notionals = [e.quantity * e.executed_price for e in executions]
            
            # Slippage metrics
            avg_slippage = statistics.mean(slippages)
            median_slippage = statistics.median(slippages)
            max_slippage = max(slippages)
            slippage_std = statistics.stdev(slippages) if len(slippages) > 1 else 0
            
            positive_count = sum(1 for s in slippages if s < -0.5)
            negative_count = sum(1 for s in slippages if s > 0.5)
            
            # Latency metrics
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            sorted_latencies = sorted(latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            p95_latency = sorted_latencies[p95_idx] if p95_idx < len(sorted_latencies) else max(latencies)
            p99_latency = sorted_latencies[p99_idx] if p99_idx < len(sorted_latencies) else max(latencies)
            
            # Fill rate
            total_orders = len(executions) + len([
                r for r in self._rejected_orders
                if r.get('rejected_at', datetime.min) >= start_time
            ])
            fill_rate = len(executions) / total_orders if total_orders > 0 else 1.0
            
            partial_count = len([
                oid for oid, fills in self._partial_fills.items()
                if fills and fills[0].timestamp_filled >= start_time
            ])
            partial_fill_rate = partial_count / len(executions) if executions else 0
            
            rejection_count = len([
                r for r in self._rejected_orders
                if r.get('rejected_at', datetime.min) >= start_time
            ])
            rejection_rate = rejection_count / total_orders if total_orders > 0 else 0
            
            # Market impact (average)
            impacts = [e.market_impact_bps for e in executions if e.market_impact_bps != 0]
            avg_impact = statistics.mean(impacts) if impacts else 0
            
            # Cost calculation
            total_notional = sum(notionals)
            total_slippage_cost = sum(
                (e.slippage_bps / 10000) * e.quantity * e.executed_price
                for e in executions
            )
            total_commission = total_notional * self.commission_rate
            total_cost = total_slippage_cost + total_commission
            
            # Quality scoring
            quality_score = self._calculate_quality_score(
                avg_slippage, fill_rate, p95_latency
            )
            quality = self._classify_quality(quality_score)
            
            return ExecutionMetrics(
                timestamp=now,
                period=period,
                total_executions=len(executions),
                total_volume=sum(volumes),
                total_notional=total_notional,
                avg_slippage_bps=avg_slippage,
                median_slippage_bps=median_slippage,
                max_slippage_bps=max_slippage,
                slippage_std_bps=slippage_std,
                positive_slippage_pct=positive_count / len(executions) if executions else 0,
                negative_slippage_pct=negative_count / len(executions) if executions else 0,
                fill_rate=fill_rate,
                partial_fill_rate=partial_fill_rate,
                rejection_rate=rejection_rate,
                avg_latency_ms=avg_latency,
                median_latency_ms=median_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                avg_market_impact_bps=avg_impact,
                permanent_impact_bps=avg_impact * 0.5,  # Estimate
                temporary_impact_bps=avg_impact * 0.5,
                total_slippage_cost=total_slippage_cost,
                total_commission_cost=total_commission,
                total_execution_cost=total_cost,
                execution_quality=quality,
                quality_score=quality_score
            )
    
    def _empty_metrics(self, period: str) -> ExecutionMetrics:
        """Return empty metrics when no data"""
        return ExecutionMetrics(
            timestamp=datetime.now(),
            period=period,
            total_executions=0,
            total_volume=0,
            total_notional=0,
            avg_slippage_bps=0,
            median_slippage_bps=0,
            max_slippage_bps=0,
            slippage_std_bps=0,
            positive_slippage_pct=0,
            negative_slippage_pct=0,
            fill_rate=1.0,
            partial_fill_rate=0,
            rejection_rate=0,
            avg_latency_ms=0,
            median_latency_ms=0,
            p95_latency_ms=0,
            p99_latency_ms=0,
            avg_market_impact_bps=0,
            permanent_impact_bps=0,
            temporary_impact_bps=0,
            total_slippage_cost=0,
            total_commission_cost=0,
            total_execution_cost=0,
            execution_quality=ExecutionQuality.GOOD,
            quality_score=100
        )
    
    def _calculate_quality_score(
        self,
        avg_slippage: float,
        fill_rate: float,
        p95_latency: float
    ) -> float:
        """Calculate execution quality score (0-100)"""
        # Slippage score (40% weight)
        if avg_slippage <= 2:
            slippage_score = 100
        elif avg_slippage <= 5:
            slippage_score = 80
        elif avg_slippage <= 10:
            slippage_score = 60
        elif avg_slippage <= 20:
            slippage_score = 40
        else:
            slippage_score = 20
        
        # Fill rate score (40% weight)
        fill_score = fill_rate * 100
        
        # Latency score (20% weight)
        if p95_latency <= 100:
            latency_score = 100
        elif p95_latency <= 250:
            latency_score = 80
        elif p95_latency <= 500:
            latency_score = 60
        elif p95_latency <= 1000:
            latency_score = 40
        else:
            latency_score = 20
        
        return slippage_score * 0.4 + fill_score * 0.4 + latency_score * 0.2
    
    def _classify_quality(self, score: float) -> ExecutionQuality:
        """Classify quality from score"""
        if score >= 90:
            return ExecutionQuality.EXCELLENT
        elif score >= 75:
            return ExecutionQuality.GOOD
        elif score >= 60:
            return ExecutionQuality.ACCEPTABLE
        elif score >= 40:
            return ExecutionQuality.POOR
        else:
            return ExecutionQuality.UNACCEPTABLE
    
    def get_expected_slippage(self, symbol: str, order_type: str) -> Dict:
        """
        Get expected slippage for a symbol/order type.
        
        This validates the slippage model (Q142).
        """
        key = f"{symbol}_{order_type}"
        
        if key in self._slippage_model:
            model = self._slippage_model[key]
            return {
                'symbol': symbol,
                'order_type': order_type,
                'expected_slippage_bps': model['mean'],
                'slippage_std_bps': model['std'],
                'sample_size': len(model['samples']),
                'last_updated': model['last_updated'].isoformat() if model['last_updated'] else None,
                'confidence': 'high' if len(model['samples']) >= 100 else 'medium' if len(model['samples']) >= 30 else 'low'
            }
        else:
            # Return default
            return {
                'symbol': symbol,
                'order_type': order_type,
                'expected_slippage_bps': self.EXPECTED_SLIPPAGE_BPS.get(order_type, 5.0),
                'slippage_std_bps': 2.0,
                'sample_size': 0,
                'last_updated': None,
                'confidence': 'default'
            }
    
    def get_symbol_metrics(self, symbol: str) -> Dict:
        """Get execution metrics for a specific symbol"""
        with self._lock:
            if symbol not in self._executions_by_symbol:
                return {'symbol': symbol, 'executions': 0}
            
            executions = list(self._executions_by_symbol[symbol])
            
            if not executions:
                return {'symbol': symbol, 'executions': 0}
            
            slippages = [e.slippage_bps for e in executions]
            latencies = [e.latency_ms for e in executions]
            
            return {
                'symbol': symbol,
                'executions': len(executions),
                'avg_slippage_bps': statistics.mean(slippages),
                'max_slippage_bps': max(slippages),
                'avg_latency_ms': statistics.mean(latencies),
                'last_execution': executions[-1].timestamp_filled.isoformat()
            }
    
    def get_status(self) -> Dict:
        """Get monitor status"""
        with self._lock:
            return {
                'total_executions': len(self._executions),
                'pending_orders': len(self._pending_orders),
                'rejected_orders': len(self._rejected_orders),
                'partial_fills': len(self._partial_fills),
                'symbols_tracked': len(self._executions_by_symbol),
                'slippage_models': len(self._slippage_model),
                'hourly_metrics': self.get_metrics('hourly').to_dict()
            }
