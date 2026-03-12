"""
Core Trading Engine Upgrades 76-100
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import hashlib
import json

# UPGRADE 076: Smart Order Router
class SmartOrderRouter:
    def __init__(self):
        self.venues: Dict[str, Dict] = {}
        
    def add_venue(self, name: str, latency_ms: float, fee: float, liquidity: float):
        self.venues[name] = {'latency': latency_ms, 'fee': fee, 'liquidity': liquidity}
        
    def route(self, symbol: str, size: float, urgency: str = 'normal') -> str:
        if not self.venues: return 'default'
        if urgency == 'high':
            return min(self.venues.items(), key=lambda x: x[1]['latency'])[0]
        scores = {v: (1/d['latency']) * d['liquidity'] / (1 + d['fee']*100) for v, d in self.venues.items()}
        return max(scores.items(), key=lambda x: x[1])[0]

# UPGRADE 077: Order Splitting Engine
class OrderSplittingEngine:
    def split(self, total_size: float, max_slice: float, strategy: str = 'equal') -> List[float]:
        if total_size <= max_slice: return [total_size]
        n_slices = int(np.ceil(total_size / max_slice))
        if strategy == 'equal': return [total_size / n_slices] * n_slices
        if strategy == 'random':
            weights = np.random.random(n_slices)
            return list(total_size * weights / weights.sum())
        return [max_slice] * (n_slices - 1) + [total_size - max_slice * (n_slices - 1)]

# UPGRADE 078: TWAP Executor
class TWAPExecutor:
    def __init__(self, duration_mins: int = 30):
        self.duration = duration_mins
        
    def get_schedule(self, total_size: float, n_slices: int = None) -> List[Dict]:
        if n_slices is None: n_slices = self.duration
        slice_size = total_size / n_slices
        interval = self.duration * 60 / n_slices
        return [{'size': slice_size, 'delay_secs': i * interval} for i in range(n_slices)]

# UPGRADE 079: VWAP Executor
class VWAPExecutor:
    def get_schedule(self, total_size: float, volume_profile: List[float]) -> List[Dict]:
        if not volume_profile: return [{'size': total_size, 'bucket': 0}]
        total_vol = sum(volume_profile)
        return [{'size': total_size * v / total_vol, 'bucket': i} for i, v in enumerate(volume_profile)]

# UPGRADE 080: Iceberg Order Manager
class IcebergOrderManager:
    def __init__(self, show_ratio: float = 0.1):
        self.show_ratio = show_ratio
        self.orders: Dict[str, Dict] = {}
        
    def create(self, order_id: str, total: float) -> float:
        show_size = total * self.show_ratio
        self.orders[order_id] = {'total': total, 'remaining': total, 'show': show_size}
        return show_size
    
    def on_fill(self, order_id: str, filled: float) -> Optional[float]:
        if order_id not in self.orders: return None
        o = self.orders[order_id]
        o['remaining'] -= filled
        if o['remaining'] <= 0: return None
        return min(o['show'], o['remaining'])

# UPGRADE 081: Bracket Order Manager
class BracketOrderManager:
    def __init__(self):
        self.brackets: Dict[str, Dict] = {}
        
    def create(self, order_id: str, entry: float, stop: float, target: float, size: float):
        self.brackets[order_id] = {'entry': entry, 'stop': stop, 'target': target, 'size': size, 'status': 'pending'}
        
    def on_entry_fill(self, order_id: str) -> Dict[str, Any]:
        if order_id not in self.brackets: return {}
        b = self.brackets[order_id]
        b['status'] = 'active'
        return {'stop_order': {'price': b['stop'], 'size': b['size']}, 'target_order': {'price': b['target'], 'size': b['size']}}

# UPGRADE 082: OCO Order Manager
class OCOOrderManager:
    def __init__(self):
        self.oco_pairs: Dict[str, Tuple[str, str]] = {}
        
    def create(self, oco_id: str, order1_id: str, order2_id: str):
        self.oco_pairs[oco_id] = (order1_id, order2_id)
        
    def on_fill(self, order_id: str) -> Optional[str]:
        for oco_id, (o1, o2) in self.oco_pairs.items():
            if order_id == o1: return o2
            if order_id == o2: return o1
        return None

# UPGRADE 083: Order Queue Manager
class OrderQueueManager:
    def __init__(self, max_pending: int = 10):
        self.max_pending = max_pending
        self.queue: deque = deque()
        self.pending: Dict[str, Dict] = {}
        
    def add(self, order: Dict) -> bool:
        if len(self.pending) >= self.max_pending:
            self.queue.append(order)
            return False
        self.pending[order['id']] = order
        return True
    
    def on_complete(self, order_id: str) -> Optional[Dict]:
        if order_id in self.pending: del self.pending[order_id]
        if self.queue and len(self.pending) < self.max_pending:
            next_order = self.queue.popleft()
            self.pending[next_order['id']] = next_order
            return next_order
        return None

# UPGRADE 084: Order Retry Handler
class OrderRetryHandler:
    def __init__(self, max_retries: int = 3, delay_ms: int = 100):
        self.max_retries = max_retries
        self.delay = delay_ms
        self.attempts: Dict[str, int] = {}
        
    def should_retry(self, order_id: str, error: str) -> Tuple[bool, int]:
        self.attempts[order_id] = self.attempts.get(order_id, 0) + 1
        if self.attempts[order_id] > self.max_retries: return False, 0
        delay = self.delay * (2 ** (self.attempts[order_id] - 1))
        return True, delay

# UPGRADE 085: Position Reconciler
class PositionReconciler:
    def __init__(self):
        self.local: Dict[str, float] = {}
        self.broker: Dict[str, float] = {}
        
    def update_local(self, symbol: str, size: float):
        self.local[symbol] = size
        
    def update_broker(self, symbol: str, size: float):
        self.broker[symbol] = size
        
    def get_discrepancies(self) -> List[Dict]:
        discrepancies = []
        all_symbols = set(self.local.keys()) | set(self.broker.keys())
        for sym in all_symbols:
            local_size = self.local.get(sym, 0)
            broker_size = self.broker.get(sym, 0)
            if abs(local_size - broker_size) > 0.0001:
                discrepancies.append({'symbol': sym, 'local': local_size, 'broker': broker_size})
        return discrepancies

# UPGRADE 086: PnL Calculator
class PnLCalculator:
    def __init__(self):
        self.positions: Dict[str, Dict] = {}
        
    def open_position(self, symbol: str, size: float, price: float, direction: str):
        self.positions[symbol] = {'size': size, 'entry': price, 'direction': direction}
        
    def calculate_unrealized(self, symbol: str, current_price: float) -> float:
        if symbol not in self.positions: return 0
        p = self.positions[symbol]
        if p['direction'] == 'long': return (current_price - p['entry']) * p['size']
        return (p['entry'] - current_price) * p['size']
    
    def close_position(self, symbol: str, exit_price: float) -> float:
        pnl = self.calculate_unrealized(symbol, exit_price)
        if symbol in self.positions: del self.positions[symbol]
        return pnl

# UPGRADE 087: Margin Calculator
class MarginCalculator:
    def __init__(self, leverage: float = 10):
        self.leverage = leverage
        
    def required_margin(self, size: float, price: float) -> float:
        return (size * price) / self.leverage
    
    def available_margin(self, equity: float, used_margin: float) -> float:
        return equity - used_margin
    
    def margin_level(self, equity: float, used_margin: float) -> float:
        return (equity / used_margin * 100) if used_margin > 0 else float('inf')

# UPGRADE 088: Swap Calculator
class SwapCalculator:
    def __init__(self):
        self.rates: Dict[str, Dict] = {}
        
    def set_rate(self, symbol: str, long_rate: float, short_rate: float):
        self.rates[symbol] = {'long': long_rate, 'short': short_rate}
        
    def calculate(self, symbol: str, size: float, direction: str, days: int = 1) -> float:
        if symbol not in self.rates: return 0
        rate = self.rates[symbol]['long' if direction == 'long' else 'short']
        return size * rate * days

# UPGRADE 089: Currency Converter
class CurrencyConverter:
    def __init__(self):
        self.rates: Dict[str, float] = {'EURUSD': 1.08, 'GBPUSD': 1.26, 'USDJPY': 150}
        
    def convert(self, amount: float, from_ccy: str, to_ccy: str) -> float:
        if from_ccy == to_ccy: return amount
        pair = f"{from_ccy}{to_ccy}"
        if pair in self.rates: return amount * self.rates[pair]
        reverse = f"{to_ccy}{from_ccy}"
        if reverse in self.rates: return amount / self.rates[reverse]
        return amount

# UPGRADE 090: Pip Value Calculator
class PipValueCalculator:
    def calculate(self, symbol: str, lot_size: float, account_ccy: str = 'USD') -> float:
        pip_size = 0.0001 if 'JPY' not in symbol else 0.01
        standard_lot = 100000
        return pip_size * standard_lot * lot_size

# UPGRADE 091: Lot Size Calculator
class LotSizeCalculator:
    def calculate(self, risk_amount: float, stop_pips: float, pip_value: float) -> float:
        if stop_pips <= 0 or pip_value <= 0: return 0
        return risk_amount / (stop_pips * pip_value)

# UPGRADE 092: Spread Cost Calculator
class SpreadCostCalculator:
    def calculate(self, spread_pips: float, lot_size: float, pip_value: float) -> float:
        return spread_pips * lot_size * pip_value

# UPGRADE 093: Break-Even Calculator
class BreakEvenCalculator:
    def calculate(self, entry: float, spread: float, commission: float, direction: str) -> float:
        total_cost = spread + commission
        if direction == 'long': return entry + total_cost
        return entry - total_cost

# UPGRADE 094: Risk-Reward Calculator
class RiskRewardCalculator:
    def calculate(self, entry: float, stop: float, target: float) -> float:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return reward / risk if risk > 0 else 0
    
    def target_for_rr(self, entry: float, stop: float, rr: float, direction: str) -> float:
        risk = abs(entry - stop)
        if direction == 'long': return entry + risk * rr
        return entry - risk * rr

# UPGRADE 095: Trade Sizing Validator
class TradeSizingValidator:
    def __init__(self, min_size: float = 0.01, max_size: float = 100):
        self.min_size = min_size
        self.max_size = max_size
        
    def validate(self, size: float) -> Tuple[bool, float]:
        if size < self.min_size: return False, self.min_size
        if size > self.max_size: return False, self.max_size
        return True, size

# UPGRADE 096: Price Precision Handler
class PricePrecisionHandler:
    def __init__(self):
        self.precisions: Dict[str, int] = {}
        
    def set_precision(self, symbol: str, decimals: int):
        self.precisions[symbol] = decimals
        
    def round_price(self, symbol: str, price: float) -> float:
        decimals = self.precisions.get(symbol, 5)
        return round(price, decimals)

# UPGRADE 097: Volume Precision Handler
class VolumePrecisionHandler:
    def __init__(self):
        self.precisions: Dict[str, int] = {}
        
    def set_precision(self, symbol: str, decimals: int):
        self.precisions[symbol] = decimals
        
    def round_volume(self, symbol: str, volume: float) -> float:
        decimals = self.precisions.get(symbol, 2)
        return round(volume, decimals)

# UPGRADE 098: Trading Hours Checker
class TradingHoursChecker:
    def __init__(self):
        self.schedules: Dict[str, List[Tuple[int, int]]] = {}
        
    def set_schedule(self, symbol: str, hours: List[Tuple[int, int]]):
        self.schedules[symbol] = hours
        
    def is_trading_hours(self, symbol: str, hour: int = None) -> bool:
        if hour is None: hour = datetime.utcnow().hour
        if symbol not in self.schedules: return True
        return any(start <= hour < end for start, end in self.schedules[symbol])

# UPGRADE 099: Holiday Calendar
class HolidayCalendar:
    def __init__(self):
        self.holidays: Dict[str, List[str]] = {}
        
    def add_holiday(self, market: str, date: str):
        if market not in self.holidays: self.holidays[market] = []
        self.holidays[market].append(date)
        
    def is_holiday(self, market: str, date: datetime = None) -> bool:
        if date is None: date = datetime.utcnow()
        date_str = date.strftime('%Y-%m-%d')
        return date_str in self.holidays.get(market, [])

# UPGRADE 100: Symbol Info Manager
class SymbolInfoManager:
    def __init__(self):
        self.symbols: Dict[str, Dict] = {}
        
    def add_symbol(self, symbol: str, info: Dict):
        self.symbols[symbol] = info
        
    def get_info(self, symbol: str) -> Dict:
        return self.symbols.get(symbol, {})
    
    def get_min_lot(self, symbol: str) -> float:
        return self.symbols.get(symbol, {}).get('min_lot', 0.01)
    
    def get_max_lot(self, symbol: str) -> float:
        return self.symbols.get(symbol, {}).get('max_lot', 100)
    
    def get_tick_size(self, symbol: str) -> float:
        return self.symbols.get(symbol, {}).get('tick_size', 0.00001)
