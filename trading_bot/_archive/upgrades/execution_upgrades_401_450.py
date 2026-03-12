"""
Execution System Upgrades 401-450
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import hashlib
import time

# UPGRADE 401: Order Manager
class OrderManager:
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        self.order_counter = 0
        
    def create_order(self, symbol: str, side: str, quantity: float, order_type: str, price: float = None) -> str:
        self.order_counter += 1
        order_id = f"ORD_{self.order_counter:08d}"
        self.orders[order_id] = {
            'id': order_id, 'symbol': symbol, 'side': side, 'quantity': quantity,
            'type': order_type, 'price': price, 'status': 'pending',
            'created_at': datetime.utcnow().isoformat(), 'filled_qty': 0
        }
        return order_id
    
    def update_status(self, order_id: str, status: str, filled_qty: float = None):
        if order_id in self.orders:
            self.orders[order_id]['status'] = status
            if filled_qty is not None: self.orders[order_id]['filled_qty'] = filled_qty
            
    def get_order(self, order_id: str) -> Dict:
        return self.orders.get(order_id, {})

# UPGRADE 402: Order Validator
class OrderValidator:
    def __init__(self):
        self.rules: List[Callable] = []
        
    def add_rule(self, rule: Callable):
        self.rules.append(rule)
        
    def validate(self, order: Dict) -> Tuple[bool, List[str]]:
        errors = []
        for rule in self.rules:
            try:
                if not rule(order): errors.append(rule.__name__)
            except Exception as e: errors.append(f"{rule.__name__}: {e}")
        return len(errors) == 0, errors

# UPGRADE 403: Order Router
class OrderRouter:
    def __init__(self):
        self.routes: Dict[str, str] = {}
        self.default_route = 'primary'
        
    def add_route(self, symbol: str, venue: str):
        self.routes[symbol] = venue
        
    def get_route(self, symbol: str) -> str:
        return self.routes.get(symbol, self.default_route)
    
    def route_order(self, order: Dict) -> str:
        return self.get_route(order.get('symbol', ''))

# UPGRADE 404: Order Executor
class OrderExecutor:
    def __init__(self):
        self.execution_log: List[Dict] = []
        
    def execute(self, order: Dict) -> Dict:
        execution = {
            'order_id': order.get('id'), 'status': 'executed',
            'executed_at': datetime.utcnow().isoformat(),
            'executed_price': order.get('price', 0),
            'executed_qty': order.get('quantity', 0)
        }
        self.execution_log.append(execution)
        return execution

# UPGRADE 405: Fill Simulator
class FillSimulator:
    def __init__(self, fill_rate: float = 0.95, slippage_bps: float = 2):
        self.fill_rate = fill_rate
        self.slippage_bps = slippage_bps
        
    def simulate_fill(self, order: Dict, market_price: float) -> Dict:
        if np.random.random() > self.fill_rate:
            return {'status': 'rejected', 'reason': 'no_fill'}
        slippage = market_price * self.slippage_bps / 10000
        if order.get('side') == 'buy': fill_price = market_price + slippage
        else: fill_price = market_price - slippage
        return {'status': 'filled', 'fill_price': fill_price, 'fill_qty': order.get('quantity', 0)}

# UPGRADE 406: Partial Fill Handler
class PartialFillHandler:
    def __init__(self):
        self.partial_fills: Dict[str, List[Dict]] = {}
        
    def record_fill(self, order_id: str, qty: float, price: float):
        if order_id not in self.partial_fills: self.partial_fills[order_id] = []
        self.partial_fills[order_id].append({'qty': qty, 'price': price, 'time': datetime.utcnow()})
        
    def get_avg_price(self, order_id: str) -> float:
        fills = self.partial_fills.get(order_id, [])
        if not fills: return 0
        total_qty = sum(f['qty'] for f in fills)
        total_value = sum(f['qty'] * f['price'] for f in fills)
        return total_value / total_qty if total_qty > 0 else 0
    
    def get_filled_qty(self, order_id: str) -> float:
        return sum(f['qty'] for f in self.partial_fills.get(order_id, []))

# UPGRADE 407: Order Amendment Handler
class OrderAmendmentHandler:
    def __init__(self):
        self.amendments: List[Dict] = []
        
    def amend(self, order_id: str, changes: Dict) -> Dict:
        amendment = {
            'order_id': order_id, 'changes': changes,
            'timestamp': datetime.utcnow().isoformat(), 'status': 'pending'
        }
        self.amendments.append(amendment)
        return amendment

# UPGRADE 408: Order Cancellation Handler
class OrderCancellationHandler:
    def __init__(self):
        self.cancellations: List[Dict] = []
        
    def cancel(self, order_id: str, reason: str = '') -> Dict:
        cancellation = {
            'order_id': order_id, 'reason': reason,
            'timestamp': datetime.utcnow().isoformat(), 'status': 'cancelled'
        }
        self.cancellations.append(cancellation)
        return cancellation

# UPGRADE 409: Order Book Tracker
class OrderBookTracker:
    def __init__(self):
        self.bids: Dict[str, List[Tuple[float, float]]] = {}
        self.asks: Dict[str, List[Tuple[float, float]]] = {}
        
    def update(self, symbol: str, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        self.bids[symbol] = sorted(bids, key=lambda x: -x[0])[:20]
        self.asks[symbol] = sorted(asks, key=lambda x: x[0])[:20]
        
    def get_best_bid(self, symbol: str) -> Tuple[float, float]:
        bids = self.bids.get(symbol, [])
        return bids[0] if bids else (0, 0)
    
    def get_best_ask(self, symbol: str) -> Tuple[float, float]:
        asks = self.asks.get(symbol, [])
        return asks[0] if asks else (0, 0)
    
    def get_spread(self, symbol: str) -> float:
        bid = self.get_best_bid(symbol)[0]
        ask = self.get_best_ask(symbol)[0]
        return ask - bid if bid and ask else 0

# UPGRADE 410: Market Depth Analyzer
class MarketDepthAnalyzer:
    def analyze(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]) -> Dict:
        bid_volume = sum(v for _, v in bids)
        ask_volume = sum(v for _, v in asks)
        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if bid_volume + ask_volume > 0 else 0
        return {
            'bid_volume': bid_volume, 'ask_volume': ask_volume,
            'imbalance': imbalance, 'depth_ratio': bid_volume / ask_volume if ask_volume > 0 else 0
        }

# UPGRADE 411: Execution Quality Analyzer
class ExecutionQualityAnalyzer:
    def __init__(self):
        self.executions: List[Dict] = []
        
    def record(self, expected_price: float, actual_price: float, side: str, qty: float):
        slippage = (actual_price - expected_price) / expected_price * 10000
        if side == 'sell': slippage = -slippage
        self.executions.append({'slippage_bps': slippage, 'qty': qty, 'time': datetime.utcnow()})
        
    def get_stats(self) -> Dict:
        if not self.executions: return {}
        slippages = [e['slippage_bps'] for e in self.executions]
        return {
            'avg_slippage': np.mean(slippages), 'max_slippage': max(slippages),
            'min_slippage': min(slippages), 'std_slippage': np.std(slippages)
        }

# UPGRADE 412: Latency Monitor
class LatencyMonitor:
    def __init__(self):
        self.latencies: Dict[str, deque] = {}
        
    def record(self, operation: str, latency_ms: float):
        if operation not in self.latencies: self.latencies[operation] = deque(maxlen=1000)
        self.latencies[operation].append(latency_ms)
        
    def get_stats(self, operation: str) -> Dict:
        if operation not in self.latencies: return {}
        lats = list(self.latencies[operation])
        return {
            'avg': np.mean(lats), 'p50': np.percentile(lats, 50),
            'p95': np.percentile(lats, 95), 'p99': np.percentile(lats, 99)
        }

# UPGRADE 413: Order Flow Tracker
class OrderFlowTracker:
    def __init__(self):
        self.flow: deque = deque(maxlen=10000)
        
    def record(self, symbol: str, side: str, qty: float, price: float):
        self.flow.append({'symbol': symbol, 'side': side, 'qty': qty, 'price': price, 'time': datetime.utcnow()})
        
    def get_net_flow(self, symbol: str, minutes: int = 5) -> float:
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent = [f for f in self.flow if f['symbol'] == symbol and f['time'] > cutoff]
        buy_vol = sum(f['qty'] for f in recent if f['side'] == 'buy')
        sell_vol = sum(f['qty'] for f in recent if f['side'] == 'sell')
        return buy_vol - sell_vol

# UPGRADE 414: Trade Aggregator
class TradeAggregator:
    def aggregate(self, trades: List[Dict], interval_seconds: int = 60) -> List[Dict]:
        if not trades: return []
        aggregated = {}
        for trade in trades:
            bucket = int(trade.get('timestamp', 0) // interval_seconds) * interval_seconds
            if bucket not in aggregated:
                aggregated[bucket] = {'open': trade['price'], 'high': trade['price'], 'low': trade['price'], 'volume': 0}
            agg = aggregated[bucket]
            agg['high'] = max(agg['high'], trade['price'])
            agg['low'] = min(agg['low'], trade['price'])
            agg['close'] = trade['price']
            agg['volume'] += trade.get('qty', 0)
        return [{'timestamp': k, **v} for k, v in sorted(aggregated.items())]

# UPGRADE 415: Position Tracker
class PositionTracker:
    def __init__(self):
        self.positions: Dict[str, Dict] = {}
        
    def update(self, symbol: str, qty_change: float, price: float):
        if symbol not in self.positions:
            self.positions[symbol] = {'qty': 0, 'avg_price': 0, 'realized_pnl': 0}
        pos = self.positions[symbol]
        if pos['qty'] == 0:
            pos['qty'] = qty_change
            pos['avg_price'] = price
        elif (pos['qty'] > 0) == (qty_change > 0):
            total_cost = pos['qty'] * pos['avg_price'] + qty_change * price
            pos['qty'] += qty_change
            pos['avg_price'] = total_cost / pos['qty'] if pos['qty'] != 0 else 0
        else:
            close_qty = min(abs(pos['qty']), abs(qty_change))
            pnl = close_qty * (price - pos['avg_price']) * (1 if pos['qty'] > 0 else -1)
            pos['realized_pnl'] += pnl
            pos['qty'] += qty_change
            
    def get_position(self, symbol: str) -> Dict:
        return self.positions.get(symbol, {'qty': 0, 'avg_price': 0, 'realized_pnl': 0})

# UPGRADE 416: PnL Calculator
class PnLCalculator:
    def calculate_unrealized(self, position: Dict, current_price: float) -> float:
        qty = position.get('qty', 0)
        avg_price = position.get('avg_price', 0)
        return qty * (current_price - avg_price)
    
    def calculate_total(self, position: Dict, current_price: float) -> float:
        unrealized = self.calculate_unrealized(position, current_price)
        realized = position.get('realized_pnl', 0)
        return unrealized + realized

# UPGRADE 417: Execution Benchmark
class ExecutionBenchmark:
    def __init__(self):
        self.benchmarks: Dict[str, float] = {}
        
    def set_benchmark(self, order_id: str, benchmark_price: float):
        self.benchmarks[order_id] = benchmark_price
        
    def calculate_performance(self, order_id: str, execution_price: float, side: str) -> float:
        benchmark = self.benchmarks.get(order_id)
        if benchmark is None: return 0
        if side == 'buy': return (benchmark - execution_price) / benchmark * 10000
        return (execution_price - benchmark) / benchmark * 10000

# UPGRADE 418: Implementation Shortfall Calculator
class ImplementationShortfallCalculator:
    def calculate(self, decision_price: float, execution_price: float, side: str, qty: float) -> Dict:
        if side == 'buy': shortfall = (execution_price - decision_price) * qty
        else: shortfall = (decision_price - execution_price) * qty
        shortfall_bps = shortfall / (decision_price * qty) * 10000 if decision_price * qty > 0 else 0
        return {'shortfall': shortfall, 'shortfall_bps': shortfall_bps}

# UPGRADE 419: Market Impact Estimator
class MarketImpactEstimator:
    def estimate(self, order_size: float, avg_volume: float, volatility: float) -> float:
        participation_rate = order_size / avg_volume if avg_volume > 0 else 0
        impact = volatility * np.sqrt(participation_rate) * 0.5
        return impact

# UPGRADE 420: Optimal Execution Scheduler
class OptimalExecutionScheduler:
    def schedule(self, total_qty: float, duration_mins: int, urgency: float = 0.5) -> List[Dict]:
        n_slices = max(1, duration_mins)
        if urgency > 0.7:
            weights = [urgency ** i for i in range(n_slices)]
        elif urgency < 0.3:
            weights = [(1 - urgency) ** (n_slices - i - 1) for i in range(n_slices)]
        else:
            weights = [1] * n_slices
        total_weight = sum(weights)
        schedule = []
        for i, w in enumerate(weights):
            schedule.append({'slice': i, 'qty': total_qty * w / total_weight, 'delay_mins': i})
        return schedule

# UPGRADE 421: Adaptive Execution Algorithm
class AdaptiveExecutionAlgorithm:
    def __init__(self):
        self.state = {'aggression': 0.5, 'remaining': 0}
        
    def initialize(self, total_qty: float):
        self.state['remaining'] = total_qty
        self.state['aggression'] = 0.5
        
    def get_next_slice(self, market_conditions: Dict) -> float:
        spread = market_conditions.get('spread', 0)
        volume = market_conditions.get('volume', 1)
        if spread < market_conditions.get('avg_spread', spread):
            self.state['aggression'] = min(1, self.state['aggression'] + 0.1)
        else:
            self.state['aggression'] = max(0.1, self.state['aggression'] - 0.1)
        slice_qty = self.state['remaining'] * self.state['aggression'] * 0.1
        self.state['remaining'] -= slice_qty
        return slice_qty

# UPGRADE 422: Participation Rate Algorithm
class ParticipationRateAlgorithm:
    def __init__(self, target_rate: float = 0.1):
        self.target_rate = target_rate
        self.executed = 0
        
    def get_slice(self, market_volume: float) -> float:
        return market_volume * self.target_rate
    
    def update(self, executed_qty: float):
        self.executed += executed_qty

# UPGRADE 423: Arrival Price Algorithm
class ArrivalPriceAlgorithm:
    def __init__(self, arrival_price: float):
        self.arrival_price = arrival_price
        self.executed_qty = 0
        self.executed_value = 0
        
    def should_be_aggressive(self, current_price: float, side: str) -> bool:
        if side == 'buy': return current_price < self.arrival_price
        return current_price > self.arrival_price
    
    def record_execution(self, qty: float, price: float):
        self.executed_qty += qty
        self.executed_value += qty * price
        
    def get_performance(self) -> float:
        if self.executed_qty == 0: return 0
        avg_price = self.executed_value / self.executed_qty
        return (self.arrival_price - avg_price) / self.arrival_price * 10000

# UPGRADE 424: Close Price Algorithm
class ClosePriceAlgorithm:
    def __init__(self, close_time: datetime):
        self.close_time = close_time
        self.total_qty = 0
        self.remaining = 0
        
    def initialize(self, qty: float):
        self.total_qty = qty
        self.remaining = qty
        
    def get_slice(self, current_time: datetime) -> float:
        time_remaining = (self.close_time - current_time).total_seconds()
        if time_remaining <= 0: return self.remaining
        urgency = 1 - (time_remaining / 3600)
        return self.remaining * max(0.1, urgency) * 0.1

# UPGRADE 425: Dark Pool Router
class DarkPoolRouter:
    def __init__(self):
        self.pools: Dict[str, Dict] = {}
        
    def add_pool(self, name: str, min_size: float, fee: float):
        self.pools[name] = {'min_size': min_size, 'fee': fee, 'available': True}
        
    def route(self, order_size: float) -> List[str]:
        eligible = [name for name, pool in self.pools.items() if pool['available'] and order_size >= pool['min_size']]
        return sorted(eligible, key=lambda x: self.pools[x]['fee'])

# UPGRADE 426: Lit Market Router
class LitMarketRouter:
    def __init__(self):
        self.venues: Dict[str, Dict] = {}
        
    def add_venue(self, name: str, latency_ms: float, rebate: float):
        self.venues[name] = {'latency': latency_ms, 'rebate': rebate}
        
    def route(self, order_type: str) -> str:
        if order_type == 'maker':
            return max(self.venues.items(), key=lambda x: x[1]['rebate'])[0]
        return min(self.venues.items(), key=lambda x: x[1]['latency'])[0]

# UPGRADE 427: Smart Order Router
class SmartOrderRouter:
    def __init__(self):
        self.venues: Dict[str, Dict] = {}
        
    def add_venue(self, name: str, liquidity: float, cost: float, latency: float):
        self.venues[name] = {'liquidity': liquidity, 'cost': cost, 'latency': latency}
        
    def route(self, order: Dict, priority: str = 'cost') -> List[Tuple[str, float]]:
        if priority == 'cost':
            sorted_venues = sorted(self.venues.items(), key=lambda x: x[1]['cost'])
        elif priority == 'speed':
            sorted_venues = sorted(self.venues.items(), key=lambda x: x[1]['latency'])
        else:
            sorted_venues = sorted(self.venues.items(), key=lambda x: -x[1]['liquidity'])
        total_qty = order.get('quantity', 0)
        allocation = []
        remaining = total_qty
        for venue, info in sorted_venues:
            alloc = min(remaining, info['liquidity'] * 0.1)
            if alloc > 0:
                allocation.append((venue, alloc))
                remaining -= alloc
            if remaining <= 0: break
        return allocation

# UPGRADE 428: Order Spray Algorithm
class OrderSprayAlgorithm:
    def spray(self, total_qty: float, venues: List[str], weights: List[float] = None) -> Dict[str, float]:
        if weights is None: weights = [1] * len(venues)
        total_weight = sum(weights)
        return {venue: total_qty * w / total_weight for venue, w in zip(venues, weights)}

# UPGRADE 429: Sweep Algorithm
class SweepAlgorithm:
    def sweep(self, order_qty: float, order_book: List[Tuple[float, float]], side: str) -> List[Dict]:
        fills = []
        remaining = order_qty
        for price, qty in order_book:
            fill_qty = min(remaining, qty)
            fills.append({'price': price, 'qty': fill_qty})
            remaining -= fill_qty
            if remaining <= 0: break
        return fills

# UPGRADE 430: Peg Order Manager
class PegOrderManager:
    def __init__(self):
        self.pegged_orders: Dict[str, Dict] = {}
        
    def create_peg(self, order_id: str, peg_type: str, offset: float):
        self.pegged_orders[order_id] = {'peg_type': peg_type, 'offset': offset}
        
    def get_price(self, order_id: str, bid: float, ask: float, mid: float) -> float:
        peg = self.pegged_orders.get(order_id)
        if not peg: return mid
        if peg['peg_type'] == 'bid': return bid + peg['offset']
        if peg['peg_type'] == 'ask': return ask + peg['offset']
        if peg['peg_type'] == 'mid': return mid + peg['offset']
        return mid

# UPGRADE 431: Discretionary Order Handler
class DiscretionaryOrderHandler:
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        
    def create(self, order_id: str, limit_price: float, discretion: float):
        self.orders[order_id] = {'limit': limit_price, 'discretion': discretion}
        
    def get_effective_price(self, order_id: str, side: str, market_price: float) -> float:
        order = self.orders.get(order_id)
        if not order: return market_price
        if side == 'buy':
            return min(order['limit'] + order['discretion'], market_price)
        return max(order['limit'] - order['discretion'], market_price)

# UPGRADE 432: Reserve Order Handler
class ReserveOrderHandler:
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        
    def create(self, order_id: str, total_qty: float, display_qty: float):
        self.orders[order_id] = {'total': total_qty, 'display': display_qty, 'filled': 0}
        
    def get_display_qty(self, order_id: str) -> float:
        order = self.orders.get(order_id)
        if not order: return 0
        remaining = order['total'] - order['filled']
        return min(order['display'], remaining)
    
    def record_fill(self, order_id: str, qty: float):
        if order_id in self.orders:
            self.orders[order_id]['filled'] += qty

# UPGRADE 433: Stop Order Manager
class StopOrderManager:
    def __init__(self):
        self.stops: Dict[str, Dict] = {}
        
    def create_stop(self, order_id: str, trigger_price: float, order_type: str, limit_price: float = None):
        self.stops[order_id] = {
            'trigger': trigger_price, 'type': order_type, 'limit': limit_price, 'triggered': False
        }
        
    def check_trigger(self, order_id: str, current_price: float, side: str) -> bool:
        stop = self.stops.get(order_id)
        if not stop or stop['triggered']: return False
        if side == 'sell' and current_price <= stop['trigger']:
            stop['triggered'] = True
            return True
        if side == 'buy' and current_price >= stop['trigger']:
            stop['triggered'] = True
            return True
        return False

# UPGRADE 434: Trailing Stop Manager
class TrailingStopManager:
    def __init__(self):
        self.stops: Dict[str, Dict] = {}
        
    def create(self, order_id: str, trail_amount: float, side: str, initial_price: float):
        self.stops[order_id] = {
            'trail': trail_amount, 'side': side, 'best_price': initial_price, 'trigger': None
        }
        self._update_trigger(order_id)
        
    def _update_trigger(self, order_id: str):
        stop = self.stops[order_id]
        if stop['side'] == 'sell':
            stop['trigger'] = stop['best_price'] - stop['trail']
        else:
            stop['trigger'] = stop['best_price'] + stop['trail']
            
    def update(self, order_id: str, current_price: float) -> bool:
        stop = self.stops.get(order_id)
        if not stop: return False
        if stop['side'] == 'sell' and current_price > stop['best_price']:
            stop['best_price'] = current_price
            self._update_trigger(order_id)
        elif stop['side'] == 'buy' and current_price < stop['best_price']:
            stop['best_price'] = current_price
            self._update_trigger(order_id)
        if stop['side'] == 'sell' and current_price <= stop['trigger']: return True
        if stop['side'] == 'buy' and current_price >= stop['trigger']: return True
        return False

# UPGRADE 435: Take Profit Manager
class TakeProfitManager:
    def __init__(self):
        self.targets: Dict[str, List[Dict]] = {}
        
    def set_targets(self, position_id: str, targets: List[Tuple[float, float]]):
        self.targets[position_id] = [{'price': p, 'portion': pct, 'hit': False} for p, pct in targets]
        
    def check_targets(self, position_id: str, current_price: float, side: str) -> List[Dict]:
        targets = self.targets.get(position_id, [])
        triggered = []
        for target in targets:
            if target['hit']: continue
            if side == 'long' and current_price >= target['price']:
                target['hit'] = True
                triggered.append(target)
            elif side == 'short' and current_price <= target['price']:
                target['hit'] = True
                triggered.append(target)
        return triggered

# UPGRADE 436: Order Timeout Handler
class OrderTimeoutHandler:
    def __init__(self, default_timeout: int = 60):
        self.default_timeout = default_timeout
        self.orders: Dict[str, Dict] = {}
        
    def set_timeout(self, order_id: str, timeout_seconds: int = None):
        self.orders[order_id] = {
            'created': datetime.utcnow(),
            'timeout': timeout_seconds or self.default_timeout
        }
        
    def is_expired(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if not order: return False
        elapsed = (datetime.utcnow() - order['created']).total_seconds()
        return elapsed > order['timeout']

# UPGRADE 437: Order Priority Manager
class OrderPriorityManager:
    def __init__(self):
        self.priorities: Dict[str, int] = {}
        
    def set_priority(self, order_id: str, priority: int):
        self.priorities[order_id] = priority
        
    def get_sorted_orders(self, order_ids: List[str]) -> List[str]:
        return sorted(order_ids, key=lambda x: self.priorities.get(x, 0), reverse=True)

# UPGRADE 438: Order Dependency Manager
class OrderDependencyManager:
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}
        
    def add_dependency(self, order_id: str, depends_on: str):
        if order_id not in self.dependencies: self.dependencies[order_id] = []
        self.dependencies[order_id].append(depends_on)
        
    def can_execute(self, order_id: str, completed_orders: set) -> bool:
        deps = self.dependencies.get(order_id, [])
        return all(d in completed_orders for d in deps)

# UPGRADE 439: Order State Machine
class OrderStateMachine:
    STATES = ['created', 'validated', 'submitted', 'acknowledged', 'partial', 'filled', 'cancelled', 'rejected']
    TRANSITIONS = {
        'created': ['validated', 'rejected'],
        'validated': ['submitted', 'cancelled'],
        'submitted': ['acknowledged', 'rejected'],
        'acknowledged': ['partial', 'filled', 'cancelled'],
        'partial': ['filled', 'cancelled']
    }
    
    def __init__(self):
        self.states: Dict[str, str] = {}
        
    def create(self, order_id: str):
        self.states[order_id] = 'created'
        
    def transition(self, order_id: str, new_state: str) -> bool:
        current = self.states.get(order_id)
        if current and new_state in self.TRANSITIONS.get(current, []):
            self.states[order_id] = new_state
            return True
        return False

# UPGRADE 440: Execution Report Generator
class ExecutionReportGenerator:
    def generate(self, executions: List[Dict]) -> Dict:
        if not executions: return {}
        total_qty = sum(e.get('qty', 0) for e in executions)
        total_value = sum(e.get('qty', 0) * e.get('price', 0) for e in executions)
        avg_price = total_value / total_qty if total_qty > 0 else 0
        return {
            'total_executions': len(executions),
            'total_quantity': total_qty,
            'total_value': total_value,
            'average_price': avg_price,
            'vwap': avg_price
        }

# UPGRADE 441: Fill Rate Calculator
class FillRateCalculator:
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        
    def record_order(self, order_id: str, requested_qty: float):
        self.orders[order_id] = {'requested': requested_qty, 'filled': 0}
        
    def record_fill(self, order_id: str, filled_qty: float):
        if order_id in self.orders:
            self.orders[order_id]['filled'] += filled_qty
            
    def get_fill_rate(self, order_id: str) -> float:
        order = self.orders.get(order_id)
        if not order or order['requested'] == 0: return 0
        return order['filled'] / order['requested']

# UPGRADE 442: Rejection Handler
class RejectionHandler:
    def __init__(self):
        self.rejections: List[Dict] = []
        
    def record(self, order_id: str, reason: str, details: Dict = None):
        self.rejections.append({
            'order_id': order_id, 'reason': reason, 'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def get_rejection_stats(self) -> Dict:
        if not self.rejections: return {}
        reasons = [r['reason'] for r in self.rejections]
        return {reason: reasons.count(reason) for reason in set(reasons)}

# UPGRADE 443: Execution Cost Analyzer
class ExecutionCostAnalyzer:
    def analyze(self, executions: List[Dict], benchmark_prices: Dict[str, float]) -> Dict:
        total_cost = 0
        for exec in executions:
            order_id = exec.get('order_id')
            benchmark = benchmark_prices.get(order_id, exec.get('price', 0))
            cost = abs(exec.get('price', 0) - benchmark) * exec.get('qty', 0)
            total_cost += cost
        return {'total_execution_cost': total_cost, 'avg_cost_per_share': total_cost / len(executions) if executions else 0}

# UPGRADE 444: Venue Performance Tracker
class VenuePerformanceTracker:
    def __init__(self):
        self.stats: Dict[str, Dict] = {}
        
    def record(self, venue: str, fill_rate: float, latency_ms: float, slippage_bps: float):
        if venue not in self.stats:
            self.stats[venue] = {'fills': [], 'latencies': [], 'slippages': []}
        self.stats[venue]['fills'].append(fill_rate)
        self.stats[venue]['latencies'].append(latency_ms)
        self.stats[venue]['slippages'].append(slippage_bps)
        
    def get_ranking(self) -> List[Tuple[str, float]]:
        scores = {}
        for venue, data in self.stats.items():
            fill_score = np.mean(data['fills']) if data['fills'] else 0
            latency_score = 1 / (np.mean(data['latencies']) + 1) if data['latencies'] else 0
            slippage_score = 1 / (abs(np.mean(data['slippages'])) + 1) if data['slippages'] else 0
            scores[venue] = fill_score * 0.4 + latency_score * 0.3 + slippage_score * 0.3
        return sorted(scores.items(), key=lambda x: -x[1])

# UPGRADE 445: Order Audit Trail
class OrderAuditTrail:
    def __init__(self):
        self.trail: List[Dict] = []
        
    def log(self, order_id: str, event: str, details: Dict = None):
        self.trail.append({
            'order_id': order_id, 'event': event, 'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def get_trail(self, order_id: str) -> List[Dict]:
        return [e for e in self.trail if e['order_id'] == order_id]

# UPGRADE 446: Execution Simulator
class ExecutionSimulator:
    def __init__(self, latency_ms: float = 10, fill_prob: float = 0.95):
        self.latency = latency_ms
        self.fill_prob = fill_prob
        
    def simulate(self, order: Dict, market_state: Dict) -> Dict:
        time.sleep(self.latency / 1000)
        if np.random.random() > self.fill_prob:
            return {'status': 'rejected', 'reason': 'no_liquidity'}
        slippage = np.random.normal(0, 0.0001)
        fill_price = market_state.get('mid', order.get('price', 0)) * (1 + slippage)
        return {'status': 'filled', 'price': fill_price, 'qty': order.get('quantity', 0)}

# UPGRADE 447: Order Replay Engine
class OrderReplayEngine:
    def __init__(self):
        self.history: List[Dict] = []
        
    def record(self, order: Dict, result: Dict):
        self.history.append({'order': order, 'result': result, 'timestamp': datetime.utcnow()})
        
    def replay(self, simulator: ExecutionSimulator, market_states: List[Dict]) -> List[Dict]:
        results = []
        for i, entry in enumerate(self.history):
            if i < len(market_states):
                result = simulator.simulate(entry['order'], market_states[i])
                results.append(result)
        return results

# UPGRADE 448: Order Compression
class OrderCompression:
    def compress(self, orders: List[Dict]) -> List[Dict]:
        compressed = {}
        for order in orders:
            key = (order.get('symbol'), order.get('side'))
            if key not in compressed:
                compressed[key] = order.copy()
            else:
                compressed[key]['quantity'] += order.get('quantity', 0)
        return list(compressed.values())

# UPGRADE 449: Order Netting
class OrderNetting:
    def net(self, orders: List[Dict]) -> List[Dict]:
        netted = {}
        for order in orders:
            symbol = order.get('symbol')
            if symbol not in netted:
                netted[symbol] = {'buy': 0, 'sell': 0}
            netted[symbol][order.get('side', 'buy')] += order.get('quantity', 0)
        result = []
        for symbol, sides in netted.items():
            net_qty = sides['buy'] - sides['sell']
            if net_qty != 0:
                result.append({
                    'symbol': symbol,
                    'side': 'buy' if net_qty > 0 else 'sell',
                    'quantity': abs(net_qty)
                })
        return result

# UPGRADE 450: Execution Analytics Dashboard
class ExecutionAnalyticsDashboard:
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        
    def update(self, executions: List[Dict], orders: List[Dict]):
        total_orders = len(orders)
        filled_orders = len([e for e in executions if e.get('status') == 'filled'])
        self.metrics = {
            'fill_rate': filled_orders / total_orders if total_orders > 0 else 0,
            'total_volume': sum(e.get('qty', 0) for e in executions),
            'avg_slippage': np.mean([e.get('slippage', 0) for e in executions]) if executions else 0,
            'order_count': total_orders,
            'execution_count': len(executions)
        }
        
    def get_dashboard(self) -> Dict:
        return self.metrics
