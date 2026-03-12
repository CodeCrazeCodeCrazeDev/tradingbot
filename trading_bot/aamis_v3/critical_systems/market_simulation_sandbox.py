"""
Market Simulation Sandbox - Digital Twin
Full market replica for strategy testing and stress testing
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import deque, defaultdict
import random
import numpy
import pandas

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Market participant types"""
    MARKET_MAKER = "market_maker"
    HFT = "hft"
    RETAIL = "retail"
    INSTITUTIONAL = "institutional"
    CENTRAL_BANK = "central_bank"
    ARBITRAGEUR = "arbitrageur"


class MarketEvent(Enum):
    """Market events"""
    NORMAL = "normal"
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    NEWS_SHOCK = "news_shock"
    REGIME_CHANGE = "regime_change"


@dataclass
class Order:
    """Market order"""
    order_id: str
    agent_id: str
    side: str  # BUY, SELL
    price: float
    size: float
    order_type: str  # LIMIT, MARKET
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Trade:
    """Executed trade"""
    trade_id: str
    buyer_id: str
    seller_id: str
    price: float
    size: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrderBook:
    """Order book state"""
    bids: Dict[float, float]  # price -> total size
    asks: Dict[float, float]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_mid_price(self) -> float:
        """Get mid price"""
        try:
            if self.bids and self.asks:
                best_bid = max(self.bids.keys())
                best_ask = min(self.asks.keys())
                return (best_bid + best_ask) / 2
            return 0.0
        except Exception as e:
            logger.error(f"Error in get_mid_price: {e}")
            raise
    
    def get_spread(self) -> float:
        """Get bid-ask spread"""
        try:
            if self.bids and self.asks:
                best_bid = max(self.bids.keys())
                best_ask = min(self.asks.keys())
                return best_ask - best_bid
            return 0.0
        except Exception as e:
            logger.error(f"Error in get_spread: {e}")
            raise


@dataclass
class SimulationResult:
    """Simulation results"""
    strategy_id: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_pnl: float
    volatility: float
    survived: bool
    failure_reason: Optional[str] = None
    trade_history: List[Trade] = field(default_factory=list)


class MarketAgent:
    """Base class for market agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType, capital: float):
        try:
            self.agent_id = agent_id
            self.agent_type = agent_type
            self.capital = capital
            self.position = 0.0
            self.orders: List[Order] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def generate_orders(self, order_book: OrderBook, 
                       market_data: Dict[str, Any]) -> List[Order]:
        """Generate orders based on strategy"""
        # Default implementation - simple market making
        try:
            orders = []
        
            # Get current mid price
            if not order_book.bids or not order_book.asks:
                return orders
        
            best_bid = order_book.bids[0].price if order_book.bids else 100.0
            best_ask = order_book.asks[0].price if order_book.asks else 100.0
            mid_price = (best_bid + best_ask) / 2
        
            # Calculate spread
            spread = best_ask - best_bid
        
            # Generate orders based on position and capital
            max_position = self.capital * 0.1  # 10% of capital
        
            # Place buy order if we have capital and not too long
            if self.capital > mid_price and abs(self.position) < max_position:
                buy_price = mid_price - spread * 0.5
                buy_size = min(1.0, self.capital / buy_price * 0.05)  # 5% of capital
            
                orders.append(Order(
                    order_id=f"{self.agent_id}_buy_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    side='buy',
                    price=buy_price,
                    size=buy_size,
                    timestamp=datetime.now()
                ))
        
            # Place sell order if we have position
            if self.position > 0:
                sell_price = mid_price + spread * 0.5
                sell_size = min(1.0, abs(self.position) * 0.5)  # Sell 50% of position
            
                orders.append(Order(
                    order_id=f"{self.agent_id}_sell_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    side='sell',
                    price=sell_price,
                    size=sell_size,
                    timestamp=datetime.now()
                ))
        
            return orders
        except Exception as e:
            logger.error(f"Error in generate_orders: {e}")
            raise
    
    def update_position(self, trade: Trade):
        """Update position after trade"""
        try:
            if trade.buyer_id == self.agent_id:
                self.position += trade.size
                self.capital -= trade.price * trade.size
            elif trade.seller_id == self.agent_id:
                self.position -= trade.size
                self.capital += trade.price * trade.size
        except Exception as e:
            logger.error(f"Error in update_position: {e}")
            raise


class MarketMakerAgent(MarketAgent):
    """Market maker providing liquidity"""
    
    def __init__(self, agent_id: str, capital: float, spread: float = 0.001):
        try:
            super().__init__(agent_id, AgentType.MARKET_MAKER, capital)
            self.spread = spread
            self.inventory_limit = 1000
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def generate_orders(self, order_book: OrderBook, 
                       market_data: Dict[str, Any]) -> List[Order]:
        """Generate two-sided quotes"""
        
        try:
            mid_price = order_book.get_mid_price()
            if mid_price == 0:
                mid_price = market_data.get('last_price', 100.0)
        
            orders = []
        
            # Adjust spread based on inventory
            inventory_skew = self.position / self.inventory_limit if self.inventory_limit > 0 else 0
        
            # Bid
            bid_price = mid_price * (1 - self.spread/2 - inventory_skew * 0.001)
            bid_size = 100 - abs(self.position) * 0.5
        
            if bid_size > 0:
                orders.append(Order(
                    order_id=f"{self.agent_id}_bid_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    side="BUY",
                    price=bid_price,
                    size=bid_size,
                    order_type="LIMIT"
                ))
        
            # Ask
            ask_price = mid_price * (1 + self.spread/2 - inventory_skew * 0.001)
            ask_size = 100 - abs(self.position) * 0.5
        
            if ask_size > 0:
                orders.append(Order(
                    order_id=f"{self.agent_id}_ask_{datetime.now().timestamp()}",
                    agent_id=self.agent_id,
                    side="SELL",
                    price=ask_price,
                    size=ask_size,
                    order_type="LIMIT"
                ))
        
            return orders
        except Exception as e:
            logger.error(f"Error in generate_orders: {e}")
            raise


class RetailAgent(MarketAgent):
    """Retail trader"""
    
    def __init__(self, agent_id: str, capital: float):
        try:
            super().__init__(agent_id, AgentType.RETAIL, capital)
            self.trade_probability = 0.01  # 1% chance to trade each tick
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def generate_orders(self, order_book: OrderBook, 
                       market_data: Dict[str, Any]) -> List[Order]:
        """Random trading (noise trader)"""
        
        try:
            if random.random() > self.trade_probability:
                return []
        
            mid_price = order_book.get_mid_price()
            if mid_price == 0:
                return []
        
            # Random buy or sell
            side = random.choice(["BUY", "SELL"])
            size = random.uniform(1, 10)
        
            # Market order
            return [Order(
                order_id=f"{self.agent_id}_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                side=side,
                price=mid_price * (1.01 if side == "BUY" else 0.99),
                size=size,
                order_type="MARKET"
            )]
        except Exception as e:
            logger.error(f"Error in generate_orders: {e}")
            raise


class InstitutionalAgent(MarketAgent):
    """Institutional trader with large orders"""
    
    def __init__(self, agent_id: str, capital: float):
        try:
            super().__init__(agent_id, AgentType.INSTITUTIONAL, capital)
            self.target_position = 0
            self.execution_horizon = 100  # Ticks to complete order
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def generate_orders(self, order_book: OrderBook, 
                       market_data: Dict[str, Any]) -> List[Order]:
        """VWAP-style execution"""
        
        try:
            if self.target_position == 0:
                # Randomly decide to build position
                if random.random() < 0.001:  # 0.1% chance
                    self.target_position = random.uniform(-1000, 1000)
                    self.execution_horizon = 100
        
            if self.target_position == 0:
                return []
        
            # Calculate slice size
            remaining = self.target_position - self.position
            slice_size = remaining / self.execution_horizon
        
            if abs(slice_size) < 0.1:
                self.target_position = 0
                return []
        
            mid_price = order_book.get_mid_price()
            if mid_price == 0:
                return []
        
            side = "BUY" if slice_size > 0 else "SELL"
        
            self.execution_horizon -= 1
        
            return [Order(
                order_id=f"{self.agent_id}_{datetime.now().timestamp()}",
                agent_id=self.agent_id,
                side=side,
                price=mid_price,
                size=abs(slice_size),
                order_type="LIMIT"
            )]
        except Exception as e:
            logger.error(f"Error in generate_orders: {e}")
            raise


class MarketSimulator:
    """Market simulation engine"""
    
    def __init__(self, initial_price: float = 100.0):
        try:
            self.initial_price = initial_price
            self.current_price = initial_price
            self.order_book = OrderBook(bids={}, asks={})
            self.agents: List[MarketAgent] = []
            self.trades: List[Trade] = []
            self.price_history: List[float] = [initial_price]
            self.tick = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def add_agent(self, agent: MarketAgent):
        """Add agent to simulation"""
        try:
            self.agents.append(agent)
        except Exception as e:
            logger.error(f"Error in add_agent: {e}")
            raise
        
    def simulate_tick(self) -> List[Trade]:
        """Simulate one market tick"""
        
        try:
            self.tick += 1
        
            # Collect orders from all agents
            market_data = {
                'last_price': self.current_price,
                'tick': self.tick
            }
        
            all_orders = []
            for agent in self.agents:
                orders = agent.generate_orders(self.order_book, market_data)
                all_orders.extend(orders)
        
            # Update order book
            self._update_order_book(all_orders)
        
            # Match orders
            new_trades = self._match_orders()
        
            # Update agents
            for trade in new_trades:
                for agent in self.agents:
                    if agent.agent_id in [trade.buyer_id, trade.seller_id]:
                        agent.update_position(trade)
        
            # Update price
            if new_trades:
                self.current_price = new_trades[-1].price
        
            self.price_history.append(self.current_price)
            self.trades.extend(new_trades)
        
            return new_trades
        except Exception as e:
            logger.error(f"Error in simulate_tick: {e}")
            raise
    
    def _update_order_book(self, orders: List[Order]):
        """Update order book with new orders"""
        
        # Clear old orders (simplified)
        try:
            self.order_book.bids.clear()
            self.order_book.asks.clear()
        
            # Add new orders
            for order in orders:
                if order.side == "BUY":
                    if order.price in self.order_book.bids:
                        self.order_book.bids[order.price] += order.size
                    else:
                        self.order_book.bids[order.price] = order.size
                else:
                    if order.price in self.order_book.asks:
                        self.order_book.asks[order.price] += order.size
                    else:
                        self.order_book.asks[order.price] = order.size
        except Exception as e:
            logger.error(f"Error in _update_order_book: {e}")
            raise
    
    def _match_orders(self) -> List[Trade]:
        """Match buy and sell orders"""
        
        try:
            trades = []
        
            if not self.order_book.bids or not self.order_book.asks:
                return trades
        
            # Get best bid and ask
            best_bid = max(self.order_book.bids.keys())
            best_ask = min(self.order_book.asks.keys())
        
            # Match if bid >= ask
            while best_bid >= best_ask:
                bid_size = self.order_book.bids[best_bid]
                ask_size = self.order_book.asks[best_ask]
            
                # Execute trade
                trade_size = min(bid_size, ask_size)
                trade_price = (best_bid + best_ask) / 2
            
                trade = Trade(
                    trade_id=f"T{len(self.trades)}",
                    buyer_id="buyer",  # Simplified
                    seller_id="seller",
                    price=trade_price,
                    size=trade_size
                )
            
                trades.append(trade)
            
                # Update order book
                self.order_book.bids[best_bid] -= trade_size
                self.order_book.asks[best_ask] -= trade_size
            
                if self.order_book.bids[best_bid] <= 0:
                    del self.order_book.bids[best_bid]
                if self.order_book.asks[best_ask] <= 0:
                    del self.order_book.asks[best_ask]
            
                # Get new best bid/ask
                if not self.order_book.bids or not self.order_book.asks:
                    break
            
                best_bid = max(self.order_book.bids.keys())
                best_ask = min(self.order_book.asks.keys())
        
            return trades
        except Exception as e:
            logger.error(f"Error in _match_orders: {e}")
            raise
    
    def inject_event(self, event: MarketEvent):
        """Inject market event"""
        
        try:
            if event == MarketEvent.FLASH_CRASH:
                # Sudden price drop
                self.current_price *= 0.9
                logger.info("Flash crash injected")
        
            elif event == MarketEvent.LIQUIDITY_CRISIS:
                # Remove market makers
                self.agents = [a for a in self.agents if a.agent_type != AgentType.MARKET_MAKER]
                logger.info("Liquidity crisis injected")
        
            elif event == MarketEvent.NEWS_SHOCK:
                # Random price jump
                self.current_price *= random.choice([0.95, 1.05])
                logger.info("News shock injected")
        except Exception as e:
            logger.error(f"Error in inject_event: {e}")
            raise


class DigitalTwinSimulator:
    """
    Complete digital twin for strategy testing
    """
    
    def __init__(self):
        try:
            self.simulator = MarketSimulator()
            self.test_results: List[SimulationResult] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def setup_realistic_market(self, n_market_makers: int = 5,
                              n_retail: int = 50,
                              n_institutional: int = 3):
        """Setup realistic market with diverse agents"""
        
        # Add market makers
        try:
            for i in range(n_market_makers):
                mm = MarketMakerAgent(f"MM{i}", capital=1000000, spread=0.001)
                self.simulator.add_agent(mm)
        
            # Add retail traders
            for i in range(n_retail):
                retail = RetailAgent(f"RETAIL{i}", capital=10000)
                self.simulator.add_agent(retail)
        
            # Add institutional traders
            for i in range(n_institutional):
                inst = InstitutionalAgent(f"INST{i}", capital=10000000)
                self.simulator.add_agent(inst)
        
            logger.info(f"Market setup: {n_market_makers} MMs, {n_retail} retail, {n_institutional} institutional")
        except Exception as e:
            logger.error(f"Error in setup_realistic_market: {e}")
            raise
    
    def test_strategy(self, strategy: Callable, 
                     n_ticks: int = 10000,
                     stress_events: Optional[List[Tuple[int, MarketEvent]]] = None) -> SimulationResult:
        """Test strategy in simulation"""
        
        # Reset simulator
        try:
            self.simulator = MarketSimulator()
            self.setup_realistic_market()
        
            # Run simulation
            strategy_trades = []
            strategy_pnl = 0.0
            position = 0.0
        
            for tick in range(n_ticks):
                # Inject stress events
                if stress_events:
                    for event_tick, event in stress_events:
                        if tick == event_tick:
                            self.simulator.inject_event(event)
            
                # Simulate market
                trades = self.simulator.simulate_tick()
            
                # Strategy decision
                market_data = {
                    'price': self.simulator.current_price,
                    'order_book': self.simulator.order_book,
                    'tick': tick
                }
            
                signal = strategy(market_data)
            
                # Execute strategy signal
                if signal == "BUY" and position <= 0:
                    # Buy
                    entry_price = self.simulator.current_price
                    position = 1.0
                    strategy_trades.append({
                        'tick': tick,
                        'action': 'BUY',
                        'price': entry_price
                    })
            
                elif signal == "SELL" and position >= 0:
                    # Sell
                    exit_price = self.simulator.current_price
                    if position > 0:
                        pnl = (exit_price - strategy_trades[-1]['price']) * position
                        strategy_pnl += pnl
                    position = -1.0
                    strategy_trades.append({
                        'tick': tick,
                        'action': 'SELL',
                        'price': exit_price
                    })
        
            # Calculate metrics
            returns = np.diff(self.simulator.price_history) / self.simulator.price_history[:-1]
        
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
        
            # Max drawdown
            cumulative = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max)
            max_drawdown = np.min(drawdown)
        
            # Win rate
            if strategy_trades:
                wins = sum(1 for t in strategy_trades if t.get('pnl', 0) > 0)
                win_rate = wins / len(strategy_trades)
            else:
                win_rate = 0.0
        
            result = SimulationResult(
                strategy_id="test_strategy",
                total_return=strategy_pnl,
                sharpe_ratio=sharpe,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=len(strategy_trades),
                avg_trade_pnl=strategy_pnl / len(strategy_trades) if strategy_trades else 0,
                volatility=np.std(returns),
                survived=True
            )
        
            self.test_results.append(result)
        
            return result
        except Exception as e:
            logger.error(f"Error in test_strategy: {e}")
            raise
    
    def stress_test(self, strategy: Callable, 
                   scenarios: List[str]) -> Dict[str, SimulationResult]:
        """Stress test strategy across scenarios"""
        
        try:
            results = {}
        
            for scenario in scenarios:
                if scenario == "flash_crash":
                    events = [(5000, MarketEvent.FLASH_CRASH)]
                elif scenario == "liquidity_crisis":
                    events = [(3000, MarketEvent.LIQUIDITY_CRISIS)]
                elif scenario == "high_volatility":
                    events = [(i * 1000, MarketEvent.NEWS_SHOCK) for i in range(1, 10)]
                else:
                    events = None
            
                result = self.test_strategy(strategy, n_ticks=10000, stress_events=events)
                results[scenario] = result
        
            return results
        except Exception as e:
            logger.error(f"Error in stress_test: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize digital twin
    twin = DigitalTwinSimulator()
    
    # Define simple strategy
    def simple_ma_strategy(market_data: Dict[str, Any]) -> str:
        """Simple moving average crossover"""
        # Simplified - in production use actual MA calculation
        try:
            if random.random() > 0.5:
                return "BUY"
            else:
                return "SELL"
        except Exception as e:
            logger.error(f"Error in simple_ma_strategy: {e}")
            raise
    
    logger.info(f"\n{'='*80}")
    logger.info(f"DIGITAL TWIN MARKET SIMULATION")
    logger.info(f"{'='*80}")
    
    # Test strategy
    logger.info(f"\nTesting strategy in normal conditions...")
    result = twin.test_strategy(simple_ma_strategy, n_ticks=1000)
    
    logger.info(f"\nRESULTS:")
    logger.info(f"  Total Return: ${result.total_return:.2f}")
    logger.info(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
    logger.info(f"  Max Drawdown: {result.max_drawdown:.2%}")
    logger.info(f"  Win Rate: {result.win_rate:.2%}")
    logger.info(f"  Total Trades: {result.total_trades}")
    logger.info(f"  Avg Trade P&L: ${result.avg_trade_pnl:.2f}")
    logger.info(f"  Volatility: {result.volatility:.2%}")
    
    # Stress test
    logger.info(f"\n{'='*80}")
    logger.info(f"STRESS TESTING")
    logger.info(f"{'='*80}")
    
    scenarios = ["flash_crash", "liquidity_crisis", "high_volatility"]
    stress_results = twin.stress_test(simple_ma_strategy, scenarios)
    
    for scenario, result in stress_results.items():
        logger.info(f"\n{scenario.upper()}:")
        logger.info(f"  Survived: {result.survived}")
        logger.info(f"  Sharpe: {result.sharpe_ratio:.2f}")
        logger.info(f"  Max DD: {result.max_drawdown:.2%}")
