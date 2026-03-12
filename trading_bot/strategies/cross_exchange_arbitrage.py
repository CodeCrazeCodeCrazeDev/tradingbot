"""
Cross-Exchange Arbitrage System
================================

Sophisticated arbitrage detection and execution:
- Price discrepancy detection
- Triangular arbitrage
- Statistical arbitrage
- Latency arbitrage
- Risk-adjusted execution
- Fee-aware profit calculation

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum, auto
from collections import defaultdict, deque
import threading
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class ArbitrageType(Enum):
    """Types of arbitrage"""
    SIMPLE = "simple"           # Buy low, sell high across exchanges
    TRIANGULAR = "triangular"   # A->B->C->A currency loop
    STATISTICAL = "statistical" # Mean reversion based
    LATENCY = "latency"         # Speed-based arbitrage
    FUTURES_SPOT = "futures_spot"  # Cash-futures basis


class ArbitrageStatus(Enum):
    """Arbitrage opportunity status"""
    DETECTED = "detected"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class ExchangePrice:
    """Price data from an exchange"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    timestamp: datetime
    latency_ms: float = 0.0
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_pct(self) -> float:
        if self.mid == 0:
            return 0
        return (self.spread / self.mid) * 100


@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage opportunity"""
    opportunity_id: str
    arb_type: ArbitrageType
    detected_at: datetime
    
    # Exchanges involved
    buy_exchange: str
    sell_exchange: str
    
    # Symbol(s)
    symbol: str
    symbols: List[str] = field(default_factory=list)  # For triangular
    
    # Prices
    buy_price: float = 0.0
    sell_price: float = 0.0
    
    # Profit calculation
    gross_profit_pct: float = 0.0
    net_profit_pct: float = 0.0
    estimated_profit: float = 0.0
    
    # Fees
    buy_fee: float = 0.0
    sell_fee: float = 0.0
    transfer_fee: float = 0.0
    total_fees: float = 0.0
    
    # Size
    max_size: float = 0.0
    recommended_size: float = 0.0
    
    # Risk metrics
    execution_risk: float = 0.0  # 0-1
    slippage_risk: float = 0.0   # 0-1
    latency_risk: float = 0.0    # 0-1
    
    # Status
    status: ArbitrageStatus = ArbitrageStatus.DETECTED
    expires_at: Optional[datetime] = None
    
    # Execution
    executed_at: Optional[datetime] = None
    actual_profit: Optional[float] = None
    
    def is_profitable(self, min_profit_pct: float = 0.1) -> bool:
        """Check if opportunity is profitable after fees"""
        return self.net_profit_pct >= min_profit_pct
    
    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    def to_dict(self) -> Dict:
        return {
            'opportunity_id': self.opportunity_id,
            'type': self.arb_type.value,
            'detected_at': self.detected_at.isoformat(),
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'symbol': self.symbol,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'gross_profit_pct': self.gross_profit_pct,
            'net_profit_pct': self.net_profit_pct,
            'estimated_profit': self.estimated_profit,
            'total_fees': self.total_fees,
            'max_size': self.max_size,
            'status': self.status.value,
            'execution_risk': self.execution_risk
        }


@dataclass
class TriangularPath:
    """Triangular arbitrage path"""
    path: List[Tuple[str, str, str]]  # [(symbol, exchange, action), ...]
    profit_pct: float
    limiting_size: float
    fees: float


class ArbitrageDetector:
    """
    Detects arbitrage opportunities across exchanges
    """
    
    def __init__(
        self,
        min_profit_pct: float = 0.1,
        max_latency_ms: float = 100,
        opportunity_ttl_seconds: float = 5.0
    ):
        self.min_profit_pct = min_profit_pct
        self.max_latency_ms = max_latency_ms
        self.opportunity_ttl = opportunity_ttl_seconds
        
        # Price cache
        self.prices: Dict[str, Dict[str, ExchangePrice]] = defaultdict(dict)
        
        # Detected opportunities
        self.opportunities: Dict[str, ArbitrageOpportunity] = {}
        self.opportunity_history: deque = deque(maxlen=1000)
        
        # Fee structures (exchange -> maker/taker fees)
        self.fees: Dict[str, Tuple[float, float]] = {
            'binance': (0.1, 0.1),
            'coinbase': (0.4, 0.6),
            'kraken': (0.16, 0.26),
            'mt5': (0.0, 0.0),  # Spread-based
            'interactive_brokers': (0.0, 0.0)  # Commission-based
        }
        
        # Callbacks
        self.on_opportunity: List[Callable] = []
        
        # Statistics
        self.stats = {
            'opportunities_detected': 0,
            'opportunities_executed': 0,
            'total_profit': 0.0,
            'avg_profit_pct': 0.0
        }
        
        self._lock = threading.RLock()
        self._next_id = 1
        
        logger.info("ArbitrageDetector initialized")
    
    def _generate_id(self) -> str:
        """Generate unique opportunity ID"""
        with self._lock:
            opp_id = f"ARB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._next_id}"
            self._next_id += 1
            return opp_id
    
    def update_price(self, exchange: str, symbol: str, price: ExchangePrice):
        """Update price for a symbol on an exchange"""
        with self._lock:
            self.prices[symbol][exchange] = price
    
    def update_prices_batch(self, prices: List[ExchangePrice]):
        """Update multiple prices at once"""
        with self._lock:
            for price in prices:
                self.prices[price.symbol][price.exchange] = price
    
    def set_fees(self, exchange: str, maker_fee_pct: float, taker_fee_pct: float):
        """Set fee structure for an exchange"""
        self.fees[exchange] = (maker_fee_pct, taker_fee_pct)
    
    def detect_simple_arbitrage(self, symbol: str) -> List[ArbitrageOpportunity]:
        """Detect simple cross-exchange arbitrage"""
        opportunities = []
        
        with self._lock:
            if symbol not in self.prices:
                return opportunities
            
            exchanges = list(self.prices[symbol].keys())
            
            # Compare all exchange pairs
            for i, buy_exchange in enumerate(exchanges):
                for sell_exchange in exchanges[i+1:]:
                    buy_price = self.prices[symbol][buy_exchange]
                    sell_price = self.prices[symbol][sell_exchange]
                    
                    # Check both directions
                    for bp, sp, be, se in [
                        (buy_price, sell_price, buy_exchange, sell_exchange),
                        (sell_price, buy_price, sell_exchange, buy_exchange)
                    ]:
                        # Buy at ask, sell at bid
                        if sp.bid > bp.ask:
                            opp = self._create_simple_opportunity(
                                symbol, be, se, bp, sp
                            )
                            if opp and opp.is_profitable(self.min_profit_pct):
                                opportunities.append(opp)
        
        return opportunities
    
    def _create_simple_opportunity(
        self,
        symbol: str,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: ExchangePrice,
        sell_price: ExchangePrice
    ) -> Optional[ArbitrageOpportunity]:
        """Create a simple arbitrage opportunity"""
        # Calculate gross profit
        gross_profit = sell_price.bid - buy_price.ask
        gross_profit_pct = (gross_profit / buy_price.ask) * 100
        
        if gross_profit_pct <= 0:
            return None
        
        # Calculate fees
        buy_fee_pct = self.fees.get(buy_exchange, (0.1, 0.1))[1]  # Taker
        sell_fee_pct = self.fees.get(sell_exchange, (0.1, 0.1))[1]  # Taker
        total_fee_pct = buy_fee_pct + sell_fee_pct
        
        # Net profit
        net_profit_pct = gross_profit_pct - total_fee_pct
        
        # Calculate max size (limited by order book depth)
        max_size = min(buy_price.ask_size, sell_price.bid_size)
        
        # Recommended size (conservative)
        recommended_size = max_size * 0.5
        
        # Estimated profit
        estimated_profit = recommended_size * buy_price.ask * (net_profit_pct / 100)
        
        # Calculate risks
        avg_latency = (buy_price.latency_ms + sell_price.latency_ms) / 2
        latency_risk = min(1.0, avg_latency / self.max_latency_ms)
        
        execution_risk = 0.1 + latency_risk * 0.3
        slippage_risk = 0.1 if max_size > 1 else 0.3
        
        return ArbitrageOpportunity(
            opportunity_id=self._generate_id(),
            arb_type=ArbitrageType.SIMPLE,
            detected_at=datetime.now(),
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            symbol=symbol,
            buy_price=buy_price.ask,
            sell_price=sell_price.bid,
            gross_profit_pct=gross_profit_pct,
            net_profit_pct=net_profit_pct,
            estimated_profit=estimated_profit,
            buy_fee=buy_fee_pct,
            sell_fee=sell_fee_pct,
            total_fees=total_fee_pct,
            max_size=max_size,
            recommended_size=recommended_size,
            execution_risk=execution_risk,
            slippage_risk=slippage_risk,
            latency_risk=latency_risk,
            expires_at=datetime.now() + timedelta(seconds=self.opportunity_ttl)
        )
    
    def detect_triangular_arbitrage(
        self,
        base_currency: str = "USD",
        exchanges: Optional[List[str]] = None
    ) -> List[ArbitrageOpportunity]:
        """Detect triangular arbitrage opportunities"""
        opportunities = []
        
        with self._lock:
            # Get all available symbols
            all_symbols = set(self.prices.keys())
            
            # Find currency pairs
            currencies = set()
            for symbol in all_symbols:
                # Assume format like "BTC/USD" or "BTCUSD"
                if '/' in symbol:
                    parts = symbol.split('/')
                else:
                    # Try to split 6-char symbols
                    if len(symbol) == 6:
                        parts = [symbol[:3], symbol[3:]]
                    else:
                        continue
                currencies.update(parts)
            
            # Find triangular paths
            currencies = list(currencies)
            for i, c1 in enumerate(currencies):
                for j, c2 in enumerate(currencies):
                    if i == j:
                        continue
                    for k, c3 in enumerate(currencies):
                        if k in [i, j]:
                            continue
                        
                        # Check if we can make a triangle
                        path = self._find_triangular_path(c1, c2, c3, exchanges)
                        if path and path.profit_pct >= self.min_profit_pct:
                            opp = self._create_triangular_opportunity(path, c1, c2, c3)
                            if opp:
                                opportunities.append(opp)
        
        return opportunities
    
    def _find_triangular_path(
        self,
        c1: str,
        c2: str,
        c3: str,
        exchanges: Optional[List[str]] = None
    ) -> Optional[TriangularPath]:
        """Find a profitable triangular path"""
        # This is a simplified implementation
        # In production, you'd need to check actual order books
        
        pairs = [
            (f"{c1}/{c2}", f"{c1}{c2}"),
            (f"{c2}/{c3}", f"{c2}{c3}"),
            (f"{c3}/{c1}", f"{c3}{c1}")
        ]
        
        path = []
        rate = 1.0
        limiting_size = float('inf')
        total_fees = 0.0
        
        for pair_slash, pair_no_slash in pairs:
            # Check if pair exists
            symbol = None
            for s in [pair_slash, pair_no_slash]:
                if s in self.prices:
                    symbol = s
                    break
            
            if not symbol:
                return None
            
            # Get best price across exchanges
            best_price = None
            for exchange, price in self.prices[symbol].items():
                if exchanges and exchange not in exchanges:
                    continue
                if best_price is None or price.ask < best_price.ask:
                    best_price = price
            
            if not best_price:
                return None
            
            path.append((symbol, best_price.exchange, 'buy'))
            rate *= (1 / best_price.ask)  # Simplified
            limiting_size = min(limiting_size, best_price.ask_size)
            total_fees += self.fees.get(best_price.exchange, (0.1, 0.1))[1]
        
        profit_pct = (rate - 1) * 100 - total_fees
        
        if profit_pct > 0:
            return TriangularPath(
                path=path,
                profit_pct=profit_pct,
                limiting_size=limiting_size,
                fees=total_fees
            )
        
        return None
    
    def _create_triangular_opportunity(
        self,
        path: TriangularPath,
        c1: str,
        c2: str,
        c3: str
    ) -> ArbitrageOpportunity:
        """Create a triangular arbitrage opportunity"""
        return ArbitrageOpportunity(
            opportunity_id=self._generate_id(),
            arb_type=ArbitrageType.TRIANGULAR,
            detected_at=datetime.now(),
            buy_exchange=path.path[0][1],
            sell_exchange=path.path[-1][1],
            symbol=f"{c1}->{c2}->{c3}->{c1}",
            symbols=[p[0] for p in path.path],
            gross_profit_pct=path.profit_pct + path.fees,
            net_profit_pct=path.profit_pct,
            total_fees=path.fees,
            max_size=path.limiting_size,
            recommended_size=path.limiting_size * 0.5,
            expires_at=datetime.now() + timedelta(seconds=self.opportunity_ttl)
        )
    
    def detect_all(self, symbols: Optional[List[str]] = None) -> List[ArbitrageOpportunity]:
        """Detect all types of arbitrage opportunities"""
        opportunities = []
        
        with self._lock:
            check_symbols = symbols or list(self.prices.keys())
            
            # Simple arbitrage
            for symbol in check_symbols:
                opps = self.detect_simple_arbitrage(symbol)
                opportunities.extend(opps)
            
            # Triangular arbitrage
            tri_opps = self.detect_triangular_arbitrage()
            opportunities.extend(tri_opps)
        
        # Store and notify
        for opp in opportunities:
            self.opportunities[opp.opportunity_id] = opp
            self.stats['opportunities_detected'] += 1
            
            for callback in self.on_opportunity:
                try:
                    callback(opp)
                except Exception as e:
                    logger.error(f"Opportunity callback error: {e}")
        
        return opportunities
    
    def get_best_opportunity(self) -> Optional[ArbitrageOpportunity]:
        """Get the best current opportunity"""
        with self._lock:
            valid_opps = [
                opp for opp in self.opportunities.values()
                if not opp.is_expired() and opp.status == ArbitrageStatus.DETECTED
            ]
            
            if not valid_opps:
                return None
            
            # Sort by net profit percentage
            valid_opps.sort(key=lambda x: x.net_profit_pct, reverse=True)
            return valid_opps[0]
    
    def cleanup_expired(self):
        """Remove expired opportunities"""
        with self._lock:
            expired = [
                opp_id for opp_id, opp in self.opportunities.items()
                if opp.is_expired()
            ]
            
            for opp_id in expired:
                opp = self.opportunities.pop(opp_id)
                opp.status = ArbitrageStatus.EXPIRED
                self.opportunity_history.append(opp)


class ArbitrageExecutor:
    """
    Executes arbitrage opportunities
    """
    
    def __init__(
        self,
        exchange_adapters: Dict[str, Any],
        max_position_size: float = 10000,
        max_slippage_pct: float = 0.1
    ):
        self.exchanges = exchange_adapters
        self.max_position_size = max_position_size
        self.max_slippage_pct = max_slippage_pct
        
        # Execution tracking
        self.active_executions: Dict[str, ArbitrageOpportunity] = {}
        self.execution_history: deque = deque(maxlen=1000)
        
        # Statistics
        self.stats = {
            'executions_attempted': 0,
            'executions_successful': 0,
            'executions_failed': 0,
            'total_profit': 0.0,
            'total_fees_paid': 0.0
        }
        
        self._lock = threading.RLock()
        
        logger.info("ArbitrageExecutor initialized")
    
    async def execute(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute an arbitrage opportunity"""
        with self._lock:
            pass
        try:
            if opportunity.opportunity_id in self.active_executions:
                logger.warning(f"Opportunity already executing: {opportunity.opportunity_id}")
                return False
            
            opportunity.status = ArbitrageStatus.EXECUTING
            self.active_executions[opportunity.opportunity_id] = opportunity
            self.stats['executions_attempted'] += 1
        
            if opportunity.arb_type == ArbitrageType.SIMPLE:
                success = await self._execute_simple(opportunity)
            elif opportunity.arb_type == ArbitrageType.TRIANGULAR:
                success = await self._execute_triangular(opportunity)
            else:
                logger.error(f"Unsupported arbitrage type: {opportunity.arb_type}")
                success = False
            
            if success:
                opportunity.status = ArbitrageStatus.COMPLETED
                opportunity.executed_at = datetime.now()
                self.stats['executions_successful'] += 1
            else:
                opportunity.status = ArbitrageStatus.FAILED
                self.stats['executions_failed'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Arbitrage execution error: {e}")
            opportunity.status = ArbitrageStatus.FAILED
            self.stats['executions_failed'] += 1
            return False
            
        finally:
            with self._lock:
                if opportunity.opportunity_id in self.active_executions:
                    del self.active_executions[opportunity.opportunity_id]
                self.execution_history.append(opportunity)
    
    async def _execute_simple(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute simple cross-exchange arbitrage"""
        buy_exchange = self.exchanges.get(opportunity.buy_exchange)
        sell_exchange = self.exchanges.get(opportunity.sell_exchange)
        
        if not buy_exchange or not sell_exchange:
            logger.error("Exchange adapter not found")
            return False
        
        # Calculate position size
        size = min(
            opportunity.recommended_size,
            self.max_position_size / opportunity.buy_price
        )
        
        # Verify prices haven't moved too much
        current_buy = await buy_exchange.get_ticker(opportunity.symbol)
        current_sell = await sell_exchange.get_ticker(opportunity.symbol)
        
        if not current_buy or not current_sell:
            logger.error("Failed to get current prices")
            return False
        
        # Check slippage
        buy_slippage = abs(current_buy.ask - opportunity.buy_price) / opportunity.buy_price * 100
        sell_slippage = abs(current_sell.bid - opportunity.sell_price) / opportunity.sell_price * 100
        
        if buy_slippage > self.max_slippage_pct or sell_slippage > self.max_slippage_pct:
            logger.warning(f"Slippage too high: buy={buy_slippage:.2f}%, sell={sell_slippage:.2f}%")
            return False
        try:
        
        # Execute both legs simultaneously
            buy_task = asyncio.create_task(
                buy_exchange.place_order({
                    'symbol': opportunity.symbol,
                    'side': 'BUY',
                    'type': 'MARKET',
                    'quantity': size
                })
            )
            
            sell_task = asyncio.create_task(
                sell_exchange.place_order({
                    'symbol': opportunity.symbol,
                    'side': 'SELL',
                    'type': 'MARKET',
                    'quantity': size
                })
            )
            
            buy_result, sell_result = await asyncio.gather(buy_task, sell_task)
            
            if buy_result and sell_result:
                # Calculate actual profit
                actual_buy_price = buy_result.get('price', opportunity.buy_price)
                actual_sell_price = sell_result.get('price', opportunity.sell_price)
                actual_profit = (actual_sell_price - actual_buy_price) * size
                
                opportunity.actual_profit = actual_profit
                self.stats['total_profit'] += actual_profit
                
                logger.info(f"Arbitrage executed: profit=${actual_profit:.2f}")
                return True
            else:
                # Rollback if one leg failed
                if buy_result and not sell_result:
                    # Close buy position
                    await buy_exchange.place_order({
                        'symbol': opportunity.symbol,
                        'side': 'SELL',
                        'type': 'MARKET',
                        'quantity': size
                    })
                elif sell_result and not buy_result:
                    # Close sell position
                    await sell_exchange.place_order({
                        'symbol': opportunity.symbol,
                        'side': 'BUY',
                        'type': 'MARKET',
                        'quantity': size
                    })
                
                return False
                
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return False
    
    async def _execute_triangular(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute triangular arbitrage"""
        # Triangular arbitrage requires executing all legs in sequence
        # This is more complex and risky
        
        logger.warning("Triangular arbitrage execution not fully implemented")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        with self._lock:
            return dict(self.stats)


class CrossExchangeArbitrageSystem:
    """
    Complete cross-exchange arbitrage system
    """
    
    def __init__(
        self,
        exchange_adapters: Dict[str, Any],
        min_profit_pct: float = 0.1,
        scan_interval_seconds: float = 1.0
    ):
        self.exchanges = exchange_adapters
        self.scan_interval = scan_interval_seconds
        
        # Components
        self.detector = ArbitrageDetector(min_profit_pct=min_profit_pct)
        self.executor = ArbitrageExecutor(exchange_adapters)
        
        # Configuration
        self.auto_execute = False
        self.symbols: List[str] = []
        
        # Background task
        self._running = False
        self._scan_task = None
        
        logger.info("CrossExchangeArbitrageSystem initialized")
    
    def add_symbol(self, symbol: str):
        """Add a symbol to monitor"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from monitoring"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
    
    async def start(self, auto_execute: bool = False):
        """Start the arbitrage system"""
        self.auto_execute = auto_execute
        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info(f"Arbitrage system started (auto_execute={auto_execute})")
    
    async def stop(self):
        """Stop the arbitrage system"""
        self._running = False
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        logger.info("Arbitrage system stopped")
    
    async def _scan_loop(self):
        """Background scanning loop"""
        while self._running:
            try:
                # Update prices from all exchanges
                await self._update_prices()
                
                # Detect opportunities
                opportunities = self.detector.detect_all(self.symbols)
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
                    
                    if self.auto_execute:
                        best = self.detector.get_best_opportunity()
                        if best:
                            await self.executor.execute(best)
                
                # Cleanup expired
                self.detector.cleanup_expired()
                
                await asyncio.sleep(self.scan_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan loop error: {e}")
                await asyncio.sleep(1)
    
    async def _update_prices(self):
        """Update prices from all exchanges"""
        for symbol in self.symbols:
            for exchange_name, adapter in self.exchanges.items():
                try:
                    ticker = await adapter.get_ticker(symbol)
                    if ticker:
                        price = ExchangePrice(
                            exchange=exchange_name,
                            symbol=symbol,
                            bid=ticker.bid,
                            ask=ticker.ask,
                            bid_size=getattr(ticker, 'bid_size', 1.0),
                            ask_size=getattr(ticker, 'ask_size', 1.0),
                            timestamp=datetime.now()
                        )
                        self.detector.update_price(exchange_name, symbol, price)
                except Exception as e:
                    logger.error(f"Failed to get price from {exchange_name}: {e}")
    
    def get_opportunities(self) -> List[ArbitrageOpportunity]:
        """Get current opportunities"""
        return list(self.detector.opportunities.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'detector': self.detector.stats,
            'executor': self.executor.get_stats(),
            'symbols_monitored': len(self.symbols),
            'exchanges_connected': len(self.exchanges),
            'active_opportunities': len(self.detector.opportunities)
        }


# Export
__all__ = [
    'CrossExchangeArbitrageSystem',
    'ArbitrageDetector',
    'ArbitrageExecutor',
    'ArbitrageOpportunity',
    'ArbitrageType',
    'ArbitrageStatus',
    'ExchangePrice',
    'TriangularPath'
]
