"""
Arbitrage Detection Module
Identifies risk-free profit opportunities across markets and exchanges
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
from collections import deque
import networkx as nx
import json
import numpy
import pandas

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

class ArbitrageType(Enum):
    """Types of arbitrage opportunities"""
    CROSS_EXCHANGE = "cross_exchange"
    TRIANGULAR = "triangular"
    STATISTICAL = "statistical"
    LATENCY = "latency"
    CALENDAR = "calendar"
    MERGER = "merger"
    REGULATORY = "regulatory"

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    opportunity_id: str
    arbitrage_type: ArbitrageType
    symbols: List[str]
    exchanges: List[str]
    buy_price: float
    sell_price: float
    spread: float
    profit_potential: float
    required_capital: float
    execution_time: float
    confidence: float
    risk_score: float
    execution_steps: List[Dict]
    metadata: Dict[str, Any]

class CrossExchangeArbitrage:
    """
    Detects price differences for same asset across different exchanges
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_spread = self.config.get('min_spread', 0.001)  # 0.1%
        self.max_latency = self.config.get('max_latency', 1000)  # 1 second
        self.exchanges = {}
        self.price_feeds = {}
        self.execution_costs = {}
        self.active_opportunities = []
        
    async def scan_exchanges(self, symbol: str) -> List[ArbitrageOpportunity]:
        """
        Scan all connected exchanges for arbitrage opportunities
        """
        opportunities = []
        
        # Get prices from all exchanges
        prices = await self._fetch_prices_async(symbol)
        
        if len(prices) < 2:
            return opportunities
        
        # Find arbitrage opportunities
        for ex1, price1 in prices.items():
            for ex2, price2 in prices.items():
                if ex1 == ex2:
                    continue
                
                # Calculate spread accounting for fees
                buy_cost = price1['ask'] * (1 + self.execution_costs.get(ex1, 0.001))
                sell_revenue = price2['bid'] * (1 - self.execution_costs.get(ex2, 0.001))
                
                spread = (sell_revenue - buy_cost) / buy_cost
                
                if spread > self.min_spread:
                    opportunity = ArbitrageOpportunity(
                        opportunity_id=f"CEA_{symbol}_{ex1}_{ex2}_{datetime.now().timestamp()}",
                        arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
                        symbols=[symbol],
                        exchanges=[ex1, ex2],
                        buy_price=price1['ask'],
                        sell_price=price2['bid'],
                        spread=spread,
                        profit_potential=self._calculate_profit(buy_cost, sell_revenue, price1['volume']),
                        required_capital=buy_cost * price1['volume'],
                        execution_time=self._estimate_execution_time(ex1, ex2),
                        confidence=self._calculate_confidence(price1, price2),
                        risk_score=self._calculate_risk(ex1, ex2, spread),
                        execution_steps=self._create_execution_plan(symbol, ex1, ex2, price1, price2),
                        metadata={
                            'volume_available': min(price1['volume'], price2['volume']),
                            'latency': self._get_latency(ex1, ex2),
                            'historical_success_rate': self._get_success_rate(ex1, ex2)
                        }
                    )
                    
                    opportunities.append(opportunity)
        
        return self._filter_opportunities(opportunities)
    
    async def _fetch_prices_async(self, symbol: str) -> Dict:
        """Fetch prices from multiple exchanges asynchronously"""
        prices = {}
        
        async def fetch_from_exchange(exchange: str):
            try:
                # Simulated API call - replace with actual exchange APIs
                url = f"https://api.{exchange}.com/ticker/{symbol}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        return exchange, {
                            'bid': data.get('bid', 0),
                            'ask': data.get('ask', 0),
                            'volume': data.get('volume', 0),
                            'timestamp': datetime.now()
                        }
            except Exception as e:
                logger.error(f"Error fetching from {exchange}: {e}")
                return exchange, None
        
        # Fetch from all exchanges in parallel
        tasks = [fetch_from_exchange(ex) for ex in self.exchanges.keys()]
        results = await asyncio.gather(*tasks)
        
        for exchange, price_data in results:
            if price_data:
                prices[exchange] = price_data
        
        return prices
    
    def _calculate_profit(self, buy_cost: float, sell_revenue: float, volume: float) -> float:
        """Calculate actual profit after all costs"""
        gross_profit = (sell_revenue - buy_cost) * volume
        
        # Deduct additional costs
        transfer_fee = volume * 0.0001  # Network transfer fee
        slippage = gross_profit * 0.02  # 2% slippage estimate
        
        return gross_profit - transfer_fee - slippage
    
    def _calculate_confidence(self, price1: Dict, price2: Dict) -> float:
        """Calculate confidence in the arbitrage opportunity"""
        factors = []
        
        # Volume confidence
        volume_score = min(1.0, min(price1['volume'], price2['volume']) / 10000)
        factors.append(volume_score)
        
        # Time synchronization confidence
        time_diff = abs((price1['timestamp'] - price2['timestamp']).total_seconds())
        time_score = max(0, 1 - time_diff / 10)
        factors.append(time_score)
        
        # Spread stability confidence
        spread_score = 0.8  # Based on historical volatility
        factors.append(spread_score)
        
        return np.mean(factors)
    
    def _calculate_risk(self, ex1: str, ex2: str, spread: float) -> float:
        """Calculate risk score for the arbitrage"""
        risks = []
        
        # Execution risk
        exec_risk = 0.2  # Base execution risk
        risks.append(exec_risk)
        
        # Regulatory risk
        reg_risk = self._get_regulatory_risk(ex1, ex2)
        risks.append(reg_risk)
        
        # Counterparty risk
        counter_risk = 0.1
        risks.append(counter_risk)
        
        # Spread risk (opportunity might close)
        spread_risk = max(0, 1 - spread * 100)
        risks.append(spread_risk)
        
        return np.mean(risks)
    
    def _create_execution_plan(self, symbol: str, ex1: str, ex2: str, 
                               price1: Dict, price2: Dict) -> List[Dict]:
        """Create step-by-step execution plan"""
        return [
            {
                'step': 1,
                'action': 'BUY',
                'exchange': ex1,
                'symbol': symbol,
                'price': price1['ask'],
                'volume': price1['volume'],
                'order_type': 'MARKET'
            },
            {
                'step': 2,
                'action': 'TRANSFER',
                'from': ex1,
                'to': ex2,
                'symbol': symbol,
                'volume': price1['volume'],
                'estimated_time': '60s'
            },
            {
                'step': 3,
                'action': 'SELL',
                'exchange': ex2,
                'symbol': symbol,
                'price': price2['bid'],
                'volume': price1['volume'],
                'order_type': 'MARKET'
            }
        ]
    
    def _filter_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Filter and rank opportunities"""
        filtered = []
        
        for opp in opportunities:
            # Apply filters
            if opp.profit_potential < 10:  # Minimum $10 profit
                continue
            
            if opp.confidence < 0.7:
                continue
            
            if opp.risk_score > 0.5:
                continue
            
            filtered.append(opp)
        
        # Sort by profit/risk ratio
        return sorted(filtered, 
                     key=lambda x: x.profit_potential / max(0.1, x.risk_score), 
                     reverse=True)
    
    def _estimate_execution_time(self, ex1: str, ex2: str) -> float:
        """Estimate total execution time in seconds"""
        # Order execution time
        exec_time = 0.5
        
        # Transfer time (if different chains)
        transfer_time = 60 if ex1 != ex2 else 0
        
        # Settlement time
        settle_time = 1
        
        return exec_time + transfer_time + settle_time
    
    def _get_latency(self, ex1: str, ex2: str) -> float:
        """Get network latency between exchanges"""
        # Implement actual latency measurement
        return 50  # ms
    
    def _get_success_rate(self, ex1: str, ex2: str) -> float:
        """Get historical success rate for this exchange pair"""
        # Implement historical tracking
        return 0.85
    
    def _get_regulatory_risk(self, ex1: str, ex2: str) -> float:
        """Assess regulatory risk for cross-exchange transfers"""
        # Implement regulatory risk assessment
        return 0.1


class TriangularArbitrage:
    """
    Detects triangular arbitrage opportunities in currency/crypto markets
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_profit = self.config.get('min_profit', 0.002)  # 0.2%
        self.currency_pairs = {}
        self.graph = nx.DiGraph()
        
    async def find_triangular_opportunities(self, exchange_data: Dict) -> List[ArbitrageOpportunity]:
        """
        Find triangular arbitrage opportunities
        Example: USD -> EUR -> GBP -> USD
        """
        opportunities = []
        
        # Build currency graph
        self._build_currency_graph(exchange_data)
        
        # Find all cycles in the graph
        cycles = self._find_profitable_cycles()
        
        for cycle in cycles:
            profit = self._calculate_cycle_profit(cycle, exchange_data)
            
            if profit > self.min_profit:
                opportunity = self._create_triangular_opportunity(cycle, profit, exchange_data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _build_currency_graph(self, exchange_data: Dict):
        """Build directed graph of currency pairs"""
        self.graph.clear()
        
        for pair, data in exchange_data.items():
            if '/' in pair:
                base, quote = pair.split('/')
                
                # Add forward edge (buy quote with base)
                self.graph.add_edge(base, quote, 
                                   rate=data['ask'],
                                   pair=pair,
                                   direction='BUY')
                
                # Add reverse edge (sell quote for base)
                self.graph.add_edge(quote, base,
                                   rate=1/data['bid'],
                                   pair=pair,
                                   direction='SELL')
    
    def _find_profitable_cycles(self) -> List[List[str]]:
        """Find all profitable cycles in currency graph"""
        profitable_cycles = []
        
        # Find all simple cycles
        cycles = list(nx.simple_cycles(self.graph))
        
        for cycle in cycles:
            if len(cycle) == 3:  # Triangular arbitrage
                # Check if cycle is profitable
                product = 1.0
                for i in range(len(cycle)):
                    j = (i + 1) % len(cycle)
                    if self.graph.has_edge(cycle[i], cycle[j]):
                        product *= self.graph[cycle[i]][cycle[j]]['rate']
                
                if product > 1.0 + self.min_profit:
                    profitable_cycles.append(cycle)
        
        return profitable_cycles
    
    def _calculate_cycle_profit(self, cycle: List[str], exchange_data: Dict) -> float:
        """Calculate profit for a triangular arbitrage cycle"""
        initial_amount = 1000  # Start with $1000
        amount = initial_amount
        
        for i in range(len(cycle)):
            j = (i + 1) % len(cycle)
            edge_data = self.graph[cycle[i]][cycle[j]]
            
            # Apply exchange rate and fees
            amount *= edge_data['rate']
            amount *= 0.999  # 0.1% fee per trade
        
        return (amount - initial_amount) / initial_amount
    
    def _create_triangular_opportunity(self, cycle: List[str], profit: float, 
                                      exchange_data: Dict) -> ArbitrageOpportunity:
        """Create arbitrage opportunity from profitable cycle"""
        execution_steps = []
        symbols = []
        
        for i in range(len(cycle)):
            j = (i + 1) % len(cycle)
            edge_data = self.graph[cycle[i]][cycle[j]]
            
            execution_steps.append({
                'step': i + 1,
                'action': edge_data['direction'],
                'pair': edge_data['pair'],
                'rate': edge_data['rate']
            })
            
            symbols.append(edge_data['pair'])
        
        return ArbitrageOpportunity(
            opportunity_id=f"TRI_{'_'.join(cycle)}_{datetime.now().timestamp()}",
            arbitrage_type=ArbitrageType.TRIANGULAR,
            symbols=symbols,
            exchanges=['single_exchange'],
            buy_price=0,  # Complex calculation
            sell_price=0,  # Complex calculation
            spread=profit,
            profit_potential=profit * 1000,  # Based on $1000 initial
            required_capital=1000,
            execution_time=3.0,  # 3 trades, 1 second each
            confidence=0.85,
            risk_score=0.2,
            execution_steps=execution_steps,
            metadata={
                'cycle': ' -> '.join(cycle + [cycle[0]]),
                'number_of_trades': len(cycle)
            }
        )


class StatisticalArbitrage:
    """
    Statistical arbitrage using mean reversion and cointegration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.lookback_period = self.config.get('lookback_period', 60)
        self.z_score_threshold = self.config.get('z_score_threshold', 2.0)
        self.cointegrated_pairs = []
        self.spread_models = {}
        
    async def find_statistical_arbitrage(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """
        Find statistical arbitrage opportunities using pair trading
        """
        opportunities = []
        
        # Find cointegrated pairs
        pairs = await self._find_cointegrated_pairs(market_data)
        
        for pair in pairs:
            # Calculate spread and z-score
            spread_data = self._calculate_spread(pair, market_data)
            
            if abs(spread_data['z_score']) > self.z_score_threshold:
                opportunity = self._create_stat_arb_opportunity(pair, spread_data, market_data)
                opportunities.append(opportunity)
        
        return opportunities
    
    async def _find_cointegrated_pairs(self, market_data: Dict) -> List[Tuple[str, str]]:
        """Find pairs of assets that are cointegrated"""
        cointegrated = []
        symbols = list(market_data.keys())
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                if self._test_cointegration(symbols[i], symbols[j], market_data):
                    cointegrated.append((symbols[i], symbols[j]))
        
        return cointegrated
    
    def _test_cointegration(self, symbol1: str, symbol2: str, market_data: Dict) -> bool:
        """Test if two assets are cointegrated using Engle-Granger test"""
        # Simplified cointegration test
        # In production, use statsmodels.tsa.stattools.coint
        
        if 'price_history' not in market_data[symbol1]:
            return False
        
        prices1 = market_data[symbol1]['price_history']
        prices2 = market_data[symbol2]['price_history']
        
        if len(prices1) < self.lookback_period or len(prices2) < self.lookback_period:
            return False
        
        # Calculate correlation
        correlation = np.corrcoef(prices1[-self.lookback_period:], 
                                 prices2[-self.lookback_period:])[0, 1]
        
        # Simple threshold (should use proper statistical test)
        return abs(correlation) > 0.8
    
    def _calculate_spread(self, pair: Tuple[str, str], market_data: Dict) -> Dict:
        """Calculate spread and z-score for a pair"""
        symbol1, symbol2 = pair
        
        price1 = market_data[symbol1]['price']
        price2 = market_data[symbol2]['price']
        
        # Get historical spread
        if pair not in self.spread_models:
            self._fit_spread_model(pair, market_data)
        
        model = self.spread_models[pair]
        
        # Calculate current spread
        spread = price1 - model['hedge_ratio'] * price2
        
        # Calculate z-score
        z_score = (spread - model['mean']) / model['std']
        
        return {
            'spread': spread,
            'z_score': z_score,
            'mean': model['mean'],
            'std': model['std'],
            'hedge_ratio': model['hedge_ratio']
        }
    
    def _fit_spread_model(self, pair: Tuple[str, str], market_data: Dict):
        """Fit spread model for a pair"""
        symbol1, symbol2 = pair
        
        prices1 = market_data[symbol1]['price_history'][-self.lookback_period:]
        prices2 = market_data[symbol2]['price_history'][-self.lookback_period:]
        
        # Calculate hedge ratio (simplified - use OLS in production)
        hedge_ratio = np.cov(prices1, prices2)[0, 1] / np.var(prices2)
        
        # Calculate historical spread
        spreads = np.array(prices1) - hedge_ratio * np.array(prices2)
        
        self.spread_models[pair] = {
            'hedge_ratio': hedge_ratio,
            'mean': np.mean(spreads),
            'std': np.std(spreads)
        }
    
    def _create_stat_arb_opportunity(self, pair: Tuple[str, str], 
                                    spread_data: Dict, market_data: Dict) -> ArbitrageOpportunity:
        """Create statistical arbitrage opportunity"""
        symbol1, symbol2 = pair
        
        # Determine trade direction
        if spread_data['z_score'] > 0:
            # Spread is too high - short symbol1, long symbol2
            action1 = 'SHORT'
            action2 = 'LONG'
        else:
            # Spread is too low - long symbol1, short symbol2
            action1 = 'LONG'
            action2 = 'SHORT'
        
        # Calculate profit potential
        expected_reversion = abs(spread_data['spread'] - spread_data['mean'])
        profit_potential = expected_reversion / market_data[symbol1]['price'] * 100
        
        return ArbitrageOpportunity(
            opportunity_id=f"STAT_{symbol1}_{symbol2}_{datetime.now().timestamp()}",
            arbitrage_type=ArbitrageType.STATISTICAL,
            symbols=[symbol1, symbol2],
            exchanges=['single_exchange'],
            buy_price=market_data[symbol1]['price'],
            sell_price=market_data[symbol2]['price'],
            spread=spread_data['spread'],
            profit_potential=profit_potential,
            required_capital=10000,  # Standard position size
            execution_time=60.0,  # Stat arb takes time
            confidence=min(0.95, abs(spread_data['z_score']) / 4),
            risk_score=0.3,
            execution_steps=[
                {
                    'step': 1,
                    'action': action1,
                    'symbol': symbol1,
                    'size': 1.0
                },
                {
                    'step': 2,
                    'action': action2,
                    'symbol': symbol2,
                    'size': spread_data['hedge_ratio']
                }
            ],
            metadata={
                'z_score': spread_data['z_score'],
                'hedge_ratio': spread_data['hedge_ratio'],
                'spread_mean': spread_data['mean'],
                'spread_std': spread_data['std']
            }
        )


class LatencyArbitrage:
    """
    High-frequency latency arbitrage
    Exploits speed advantages to capture price discrepancies
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.latency_advantage = self.config.get('latency_advantage', 10)  # ms
        self.min_edge = self.config.get('min_edge', 0.0001)  # 0.01%
        
    async def detect_latency_opportunities(self, market_data: Dict) -> List[ArbitrageOpportunity]:
        """
        Detect opportunities where speed advantage can be monetized
        """
        opportunities = []
        
        # Detect slow market participants
        slow_venues = self._identify_slow_venues(market_data)
        
        # Find predictive signals
        signals = self._find_predictive_signals(market_data)
        
        for signal in signals:
            if signal['edge'] > self.min_edge:
                opportunity = self._create_latency_opportunity(signal, slow_venues)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _identify_slow_venues(self, market_data: Dict) -> List[str]:
        """Identify venues with slower price updates"""
        slow_venues = []
        
        # Analyze update frequencies and latencies
        for venue, data in market_data.items():
            if 'latency' in data and data['latency'] > 100:  # 100ms threshold
                slow_venues.append(venue)
        
        return slow_venues
    
    def _find_predictive_signals(self, market_data: Dict) -> List[Dict]:
        """Find signals that predict price movements"""
        signals = []
        
        # Look for order flow imbalances
        # Large trades on fast exchanges that haven't propagated
        # News events that haven't been priced in
        
        return signals
    
    def _create_latency_opportunity(self, signal: Dict, slow_venues: List[str]) -> ArbitrageOpportunity:
        """Create latency arbitrage opportunity"""
        return ArbitrageOpportunity(
            opportunity_id=f"LAT_{signal['symbol']}_{datetime.now().timestamp()}",
            arbitrage_type=ArbitrageType.LATENCY,
            symbols=[signal['symbol']],
            exchanges=slow_venues,
            buy_price=signal['current_price'],
            sell_price=signal['predicted_price'],
            spread=signal['edge'],
            profit_potential=signal['edge'] * 100,
            required_capital=100000,  # HFT requires capital
            execution_time=0.01,  # 10ms execution
            confidence=signal['confidence'],
            risk_score=0.4,  # Latency arb has execution risk
            execution_steps=[
                {
                    'step': 1,
                    'action': 'DETECT_SIGNAL',
                    'latency': '1ms'
                },
                {
                    'step': 2,
                    'action': 'EXECUTE_FAST',
                    'latency': '5ms'
                },
                {
                    'step': 3,
                    'action': 'CAPTURE_SPREAD',
                    'latency': '10ms'
                }
            ],
            metadata={
                'signal_type': signal['type'],
                'latency_advantage': f"{self.latency_advantage}ms"
            }
        )
