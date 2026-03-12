"""
from pathlib import Path
Arbitrage Network: Cross-Exchange, Crypto-Fiat, and ETF-Constituent Arbitrage

Implements multi-venue arbitrage detection and execution with real-time monitoring.
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import asyncio
import pathlib
import numpy

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
    ETF_CONSTITUENT = "etf_constituent"
    CRYPTO_FIAT = "crypto_fiat"
    FUTURES_SPOT = "futures_spot"


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity specification"""
    arb_type: ArbitrageType
    timestamp: datetime
    profit_bps: float
    profit_usd: float
    confidence: float
    execution_path: List[Dict]
    required_capital: float
    estimated_duration_ms: float
    risk_score: float


class CrossExchangeArbitrage:
    """
    Cross-Exchange Arbitrage Detector
    
    Finds price discrepancies across multiple exchanges.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Arbitrage parameters
        self.min_profit_bps = self.config.get('min_profit_bps', 10)
        self.max_execution_time_ms = self.config.get('max_execution_time_ms', 500)
        self.transaction_cost_bps = self.config.get('transaction_cost_bps', 5)
        
        # Exchange data
        self.exchange_prices = {}
        self.exchange_fees = {}
        self.exchange_latencies = {}
        
    def update_prices(self, exchange: str, symbol: str, bid: float, ask: float):
        """Update price data for an exchange"""
        if exchange not in self.exchange_prices:
            self.exchange_prices[exchange] = {}
        
        self.exchange_prices[exchange][symbol] = {
            'bid': bid,
            'ask': ask,
            'timestamp': datetime.now()
        }
    
    def detect_opportunities(self, symbol: str) -> List[ArbitrageOpportunity]:
        """
        Detect cross-exchange arbitrage opportunities
        
        Args:
            symbol: Trading symbol
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Find all exchanges with this symbol
        exchanges_with_symbol = [
            ex for ex in self.exchange_prices
            if symbol in self.exchange_prices[ex]
        ]
        
        if len(exchanges_with_symbol) < 2:
            return opportunities
        
        # Check all pairs of exchanges
        for i, buy_exchange in enumerate(exchanges_with_symbol):
            for sell_exchange in exchanges_with_symbol[i+1:]:
                # Buy on one exchange, sell on another
                buy_price = self.exchange_prices[buy_exchange][symbol]['ask']
                sell_price = self.exchange_prices[sell_exchange][symbol]['bid']
                
                # Calculate profit
                gross_profit_bps = (sell_price / buy_price - 1) * 10000
                net_profit_bps = gross_profit_bps - self.transaction_cost_bps * 2
                
                if net_profit_bps > self.min_profit_bps:
                    # Estimate execution time
                    buy_latency = self.exchange_latencies.get(buy_exchange, 50)
                    sell_latency = self.exchange_latencies.get(sell_exchange, 50)
                    execution_time = buy_latency + sell_latency
                    
                    if execution_time < self.max_execution_time_ms:
                        # Calculate required capital (for 1 unit)
                        required_capital = buy_price
                        profit_usd = required_capital * net_profit_bps / 10000
                        
                        # Risk score (higher latency = higher risk)
                        risk_score = min(1.0, execution_time / self.max_execution_time_ms)
                        
                        opportunity = ArbitrageOpportunity(
                            arb_type=ArbitrageType.CROSS_EXCHANGE,
                            timestamp=datetime.now(),
                            profit_bps=net_profit_bps,
                            profit_usd=profit_usd,
                            confidence=1.0 - risk_score,
                            execution_path=[
                                {'action': 'BUY', 'exchange': buy_exchange, 'price': buy_price},
                                {'action': 'SELL', 'exchange': sell_exchange, 'price': sell_price}
                            ],
                            required_capital=required_capital,
                            estimated_duration_ms=execution_time,
                            risk_score=risk_score
                        )
                        
                        opportunities.append(opportunity)
                        
                        logger.info(f"Cross-exchange arbitrage found: {symbol} "
                                  f"Buy@{buy_exchange} ${buy_price:.2f}, "
                                  f"Sell@{sell_exchange} ${sell_price:.2f}, "
                                  f"Profit: {net_profit_bps:.2f} bps")
        
        return opportunities


class TriangularArbitrage:
    """
    Triangular Arbitrage Detector
    
    Finds arbitrage opportunities in currency/crypto triangles.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_profit_bps = self.config.get('min_profit_bps', 5)
        
        # Exchange rates
        self.rates = {}
    
    def update_rate(self, pair: str, rate: float):
        """Update exchange rate"""
        self.rates[pair] = rate
    
    def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Detect triangular arbitrage opportunities
        
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Example: BTC/USD, ETH/USD, BTC/ETH
        # Check if we can profit from: USD -> BTC -> ETH -> USD
        
        if 'BTC/USD' in self.rates and 'ETH/USD' in self.rates and 'BTC/ETH' in self.rates:
            # Path: USD -> BTC -> ETH -> USD
            btc_usd = self.rates['BTC/USD']
            eth_usd = self.rates['ETH/USD']
            btc_eth = self.rates['BTC/ETH']
            
            # Calculate implied ETH/USD from BTC/USD and BTC/ETH
            implied_eth_usd = btc_usd / btc_eth
            
            # Profit opportunity
            profit_bps = (implied_eth_usd / eth_usd - 1) * 10000
            
            if abs(profit_bps) > self.min_profit_bps:
                if profit_bps > 0:
                    # Buy ETH with USD, sell ETH for BTC, sell BTC for USD
                    path = [
                        {'action': 'BUY', 'pair': 'ETH/USD', 'rate': eth_usd},
                        {'action': 'SELL', 'pair': 'BTC/ETH', 'rate': 1/btc_eth},
                        {'action': 'SELL', 'pair': 'BTC/USD', 'rate': btc_usd}
                    ]
                else:
                    # Reverse path
                    path = [
                        {'action': 'BUY', 'pair': 'BTC/USD', 'rate': btc_usd},
                        {'action': 'BUY', 'pair': 'BTC/ETH', 'rate': btc_eth},
                        {'action': 'SELL', 'pair': 'ETH/USD', 'rate': eth_usd}
                    ]
                    profit_bps = abs(profit_bps)
                
                opportunity = ArbitrageOpportunity(
                    arb_type=ArbitrageType.TRIANGULAR,
                    timestamp=datetime.now(),
                    profit_bps=profit_bps,
                    profit_usd=profit_bps / 10000 * 1000,  # For $1000 capital
                    confidence=0.9,
                    execution_path=path,
                    required_capital=1000,
                    estimated_duration_ms=200,
                    risk_score=0.3
                )
                
                opportunities.append(opportunity)
                
                logger.info(f"Triangular arbitrage found: Profit {profit_bps:.2f} bps")
        
        return opportunities


class ETFArbitrage:
    """
    ETF-Constituent Arbitrage Detector
    
    Finds arbitrage between ETF and its underlying constituents.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_profit_bps = self.config.get('min_profit_bps', 20)
        
        # ETF data
        self.etf_prices = {}
        self.etf_constituents = {}
        self.constituent_prices = {}
    
    def set_etf_constituents(self, etf: str, constituents: Dict[str, float]):
        """
        Set ETF constituents and weights
        
        Args:
            etf: ETF symbol
            constituents: {constituent_symbol: weight}
        """
        self.etf_constituents[etf] = constituents
    
    def update_prices(self, symbol: str, price: float, is_etf: bool = False):
        """Update price data"""
        if is_etf:
            self.etf_prices[symbol] = price
        else:
            self.constituent_prices[symbol] = price
    
    def detect_opportunities(self, etf: str) -> List[ArbitrageOpportunity]:
        """
        Detect ETF arbitrage opportunities
        
        Args:
            etf: ETF symbol
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        if etf not in self.etf_prices or etf not in self.etf_constituents:
            return opportunities
        
        etf_price = self.etf_prices[etf]
        constituents = self.etf_constituents[etf]
        
        # Calculate NAV (Net Asset Value) from constituents
        nav = 0
        missing_prices = []
        
        for constituent, weight in constituents.items():
            if constituent in self.constituent_prices:
                nav += self.constituent_prices[constituent] * weight
            else:
                missing_prices.append(constituent)
        
        if missing_prices:
            logger.debug(f"Missing prices for: {missing_prices}")
            return opportunities
        
        # Calculate premium/discount
        premium_bps = (etf_price / nav - 1) * 10000
        
        if abs(premium_bps) > self.min_profit_bps:
            if premium_bps > 0:
                # ETF trading at premium: sell ETF, buy constituents
                action = "SELL_ETF_BUY_BASKET"
            else:
                # ETF trading at discount: buy ETF, sell constituents
                action = "BUY_ETF_SELL_BASKET"
                premium_bps = abs(premium_bps)
            
            opportunity = ArbitrageOpportunity(
                arb_type=ArbitrageType.ETF_CONSTITUENT,
                timestamp=datetime.now(),
                profit_bps=premium_bps,
                profit_usd=premium_bps / 10000 * etf_price,
                confidence=0.85,
                execution_path=[{'action': action, 'etf': etf, 'nav': nav}],
                required_capital=etf_price,
                estimated_duration_ms=1000,
                risk_score=0.4
            )
            
            opportunities.append(opportunity)
            
            logger.info(f"ETF arbitrage found: {etf} premium {premium_bps:.2f} bps")
        
        return opportunities


class ArbitrageNetwork:
    """
    Integrated Arbitrage Network
    
    Monitors and executes arbitrage across multiple strategies.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize arbitrage detectors
        self.cross_exchange = CrossExchangeArbitrage(config)
        self.triangular = TriangularArbitrage(config)
        self.etf_arb = ETFArbitrage(config)
        
        # Opportunity tracking
        self.active_opportunities = []
        self.executed_opportunities = []
        
        # Performance metrics
        self.total_profit = 0.0
        self.total_trades = 0
        self.win_rate = 0.0
        
        logger.info("Arbitrage Network initialized")
    
    def scan_all_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Scan for all arbitrage opportunities
        
        Returns:
            List of all detected opportunities
        """
        all_opportunities = []
        
        # Cross-exchange arbitrage
        # (Would scan all symbols in production)
        
        # Triangular arbitrage
        triangular_opps = self.triangular.detect_opportunities()
        all_opportunities.extend(triangular_opps)
        
        # ETF arbitrage
        # (Would scan all ETFs in production)
        
        # Sort by profit
        all_opportunities.sort(key=lambda x: x.profit_bps, reverse=True)
        
        self.active_opportunities = all_opportunities
        
        return all_opportunities
    
    async def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict:
        """
        Execute arbitrage opportunity
        
        Args:
            opportunity: Arbitrage opportunity to execute
            
        Returns:
            Execution result
        """
        logger.info(f"Executing {opportunity.arb_type.value} arbitrage: "
                   f"{opportunity.profit_bps:.2f} bps profit")
        
        start_time = datetime.now()
        
        try:
            # Execute each step in the path
            for step in opportunity.execution_path:
                # Simulate execution (in production, would call actual exchange APIs)
                await asyncio.sleep(0.05)  # Simulate latency
                
                logger.info(f"  Executed: {step}")
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Calculate actual profit (with slippage)
            slippage_bps = np.random.uniform(0, 2)
            actual_profit_bps = opportunity.profit_bps - slippage_bps
            actual_profit_usd = opportunity.required_capital * actual_profit_bps / 10000
            
            # Update metrics
            self.total_profit += actual_profit_usd
            self.total_trades += 1
            
            result = {
                'success': True,
                'opportunity': opportunity,
                'actual_profit_bps': actual_profit_bps,
                'actual_profit_usd': actual_profit_usd,
                'execution_time_ms': execution_time,
                'slippage_bps': slippage_bps
            }
            
            self.executed_opportunities.append(result)
            
            logger.info(f"Arbitrage executed successfully: ${actual_profit_usd:.2f} profit")
            
            return result
            
        except Exception as e:
            logger.error(f"Arbitrage execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """Get arbitrage network statistics"""
        if self.executed_opportunities:
            successful = [o for o in self.executed_opportunities if o['success']]
            self.win_rate = len(successful) / len(self.executed_opportunities)
            
            avg_profit = np.mean([o['actual_profit_usd'] for o in successful]) if successful else 0
            avg_execution_time = np.mean([o['execution_time_ms'] for o in successful]) if successful else 0
        else:
            avg_profit = 0
            avg_execution_time = 0
        
        return {
            'total_profit_usd': self.total_profit,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'avg_profit_usd': avg_profit,
            'avg_execution_time_ms': avg_execution_time,
            'active_opportunities': len(self.active_opportunities)
        }


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        network = ArbitrageNetwork()
        
        # Update some rates for triangular arbitrage
        network.triangular.update_rate('BTC/USD', 50000)
        network.triangular.update_rate('ETH/USD', 3000)
        network.triangular.update_rate('BTC/ETH', 16.5)  # Slightly off for arbitrage
        
        # Scan for opportunities
        opportunities = network.scan_all_opportunities()
        
        logger.info(f"\nFound {len(opportunities)} arbitrage opportunities:\n")
        
        for opp in opportunities:
            logger.info(f"{opp.arb_type.value}:")
            logger.info(f"  Profit: {opp.profit_bps:.2f} bps (${opp.profit_usd:.2f})")
            logger.info(f"  Confidence: {opp.confidence:.2%}")
            logger.info(f"  Risk Score: {opp.risk_score:.2f}")
            logger.info(f"  Execution Time: {opp.estimated_duration_ms:.0f}ms\n")
            
            # Execute top opportunity
            if opp == opportunities[0]:
                result = await network.execute_opportunity(opp)
                if result['success']:
                    logger.info(f"Execution successful!")
                    logger.info(f"  Actual Profit: ${result['actual_profit_usd']:.2f}")
                    logger.info(f"  Slippage: {result['slippage_bps']:.2f} bps")
        
        # Get statistics
        stats = network.get_statistics()
        logger.info(f"\nArbitrage Network Statistics:")
        logger.info(f"  Total Profit: ${stats['total_profit_usd']:.2f}")
        logger.info(f"  Total Trades: {stats['total_trades']}")
        logger.info(f"  Win Rate: {stats['win_rate']:.1%}")
    
    asyncio.run(main())
