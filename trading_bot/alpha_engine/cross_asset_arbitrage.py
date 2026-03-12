"""
Cross-Asset & Multi-Market Strategies Module
=============================================

Comprehensive arbitrage and cross-market strategies:
- Statistical Arbitrage (Pairs Trading with DC Enhancement)
- Basket Trading
- Triangular Arbitrage (Forex)
- Cross-Exchange Arbitrage (Crypto)
- Options Volatility Arbitrage
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import math

logger = logging.getLogger(__name__)

# Try importing statistical libraries
try:
    from statsmodels.tsa.stattools import coint, adfuller
    from statsmodels.regression.linear_model import OLS
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class ArbitrageType(Enum):
    """Types of arbitrage strategies"""
    PAIRS_TRADING = "pairs_trading"
    BASKET = "basket"
    TRIANGULAR = "triangular"
    CROSS_EXCHANGE = "cross_exchange"
    VOLATILITY = "volatility"


class SpreadState(Enum):
    """State of spread for pairs trading"""
    NEUTRAL = "neutral"
    OVERSOLD = "oversold"  # Spread too low, expect increase
    OVERBOUGHT = "overbought"  # Spread too high, expect decrease


@dataclass
class PairRelationship:
    """Relationship between two assets"""
    asset_a: str
    asset_b: str
    correlation: float
    cointegration_pvalue: float
    beta: float  # Hedge ratio
    half_life: float  # Mean reversion half-life in days
    is_cointegrated: bool
    
    @property
    def strength(self) -> float:
        """Relationship strength score"""
        if not self.is_cointegrated:
            return 0
        return (1 - self.cointegration_pvalue) * abs(self.correlation)


@dataclass
class SpreadSignal:
    """Signal from spread analysis"""
    timestamp: datetime
    pair: PairRelationship
    spread_value: float
    z_score: float
    state: SpreadState
    signal_strength: float
    entry_threshold: float
    exit_threshold: float
    
    # Position recommendation
    position_a: str  # 'long', 'short', 'flat'
    position_b: str
    hedge_ratio: float


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity"""
    timestamp: datetime
    arb_type: ArbitrageType
    assets: List[str]
    expected_profit_bps: float
    confidence: float
    execution_risk: float
    time_sensitivity: str  # 'immediate', 'short', 'medium'
    trades: List[Dict[str, Any]]


class PairsTrader:
    """
    Statistical Arbitrage - Pairs Trading with DC Enhancement
    
    Features:
    - Cointegration testing
    - Spread calculation with hedge ratio
    - Z-score based entry/exit
    - DC threshold application to spread
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Parameters
        self.lookback_period = self.config.get('lookback_period', 60)
        self.entry_z_score = self.config.get('entry_z_score', 2.0)
        self.exit_z_score = self.config.get('exit_z_score', 0.5)
        self.cointegration_threshold = self.config.get('cointegration_threshold', 0.05)
        
        # Price history
        self.price_history: Dict[str, deque] = {}
        
        # Pair relationships
        self.pairs: Dict[Tuple[str, str], PairRelationship] = {}
        
        # Active positions
        self.active_positions: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def update_price(self, symbol: str, price: float, timestamp: datetime = None):
        """Update price for symbol"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.lookback_period * 2)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp,
        })
    
    def test_cointegration(self, asset_a: str, asset_b: str) -> PairRelationship:
        """
        Test cointegration between two assets
        
        Args:
            asset_a: First asset
            asset_b: Second asset
            
        Returns:
            PairRelationship
        """
        if asset_a not in self.price_history or asset_b not in self.price_history:
            return PairRelationship(
                asset_a=asset_a,
                asset_b=asset_b,
                correlation=0,
                cointegration_pvalue=1.0,
                beta=1.0,
                half_life=float('inf'),
                is_cointegrated=False,
            )
        
        prices_a = np.array([p['price'] for p in self.price_history[asset_a]])
        prices_b = np.array([p['price'] for p in self.price_history[asset_b]])
        
        # Ensure same length
        min_len = min(len(prices_a), len(prices_b))
        if min_len < 30:
            return PairRelationship(
                asset_a=asset_a,
                asset_b=asset_b,
                correlation=0,
                cointegration_pvalue=1.0,
                beta=1.0,
                half_life=float('inf'),
                is_cointegrated=False,
            )
        
        prices_a = prices_a[-min_len:]
        prices_b = prices_b[-min_len:]
        
        # Calculate correlation
        correlation = np.corrcoef(prices_a, prices_b)[0, 1]
        
        # Test cointegration
        if STATSMODELS_AVAILABLE:
            try:
                # Engle-Granger cointegration test
                score, pvalue, _ = coint(prices_a, prices_b)
                
                # Calculate hedge ratio (beta)
                model = OLS(prices_a, prices_b).fit()
                beta = model.params[0]
                
                # Calculate spread
                spread = prices_a - beta * prices_b
                
                # Calculate half-life
                spread_lag = spread[:-1]
                spread_diff = np.diff(spread)
                model_hl = OLS(spread_diff, spread_lag).fit()
                half_life = -np.log(2) / model_hl.params[0] if model_hl.params[0] < 0 else float('inf')
                
            except Exception as e:
                logger.error(f"Cointegration test failed: {e}")
                pvalue = 1.0
                beta = 1.0
                half_life = float('inf')
        else:
            # Simple fallback
            pvalue = 0.1 if abs(correlation) > 0.8 else 0.5
            beta = np.std(prices_a) / np.std(prices_b) if np.std(prices_b) > 0 else 1.0
            half_life = 10.0
        
        is_cointegrated = pvalue < self.cointegration_threshold
        
        relationship = PairRelationship(
            asset_a=asset_a,
            asset_b=asset_b,
            correlation=correlation,
            cointegration_pvalue=pvalue,
            beta=beta,
            half_life=half_life,
            is_cointegrated=is_cointegrated,
        )
        
        self.pairs[(asset_a, asset_b)] = relationship
        
        return relationship
    
    def calculate_spread_signal(self, asset_a: str, asset_b: str) -> Optional[SpreadSignal]:
        """
        Calculate spread signal for pair
        
        Args:
            asset_a: First asset
            asset_b: Second asset
            
        Returns:
            SpreadSignal or None
        """
        pair_key = (asset_a, asset_b)
        
        if pair_key not in self.pairs:
            self.test_cointegration(asset_a, asset_b)
        
        pair = self.pairs.get(pair_key)
        if not pair or not pair.is_cointegrated:
            return None
        
        # Get current prices
        if asset_a not in self.price_history or asset_b not in self.price_history:
            return None
        
        prices_a = np.array([p['price'] for p in self.price_history[asset_a]])
        prices_b = np.array([p['price'] for p in self.price_history[asset_b]])
        
        min_len = min(len(prices_a), len(prices_b))
        if min_len < 20:
            return None
        
        prices_a = prices_a[-min_len:]
        prices_b = prices_b[-min_len:]
        
        # Calculate spread
        spread = prices_a - pair.beta * prices_b
        
        # Calculate z-score
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        
        if spread_std == 0:
            return None
        
        current_spread = spread[-1]
        z_score = (current_spread - spread_mean) / spread_std
        
        # Determine state and signal
        if z_score > self.entry_z_score:
            state = SpreadState.OVERBOUGHT
            position_a = 'short'
            position_b = 'long'
            signal_strength = min((z_score - self.entry_z_score) / 2, 1.0)
        elif z_score < -self.entry_z_score:
            state = SpreadState.OVERSOLD
            position_a = 'long'
            position_b = 'short'
            signal_strength = min((abs(z_score) - self.entry_z_score) / 2, 1.0)
        else:
            state = SpreadState.NEUTRAL
            position_a = 'flat'
            position_b = 'flat'
            signal_strength = 0
        
        return SpreadSignal(
            timestamp=datetime.now(),
            pair=pair,
            spread_value=current_spread,
            z_score=z_score,
            state=state,
            signal_strength=signal_strength,
            entry_threshold=self.entry_z_score,
            exit_threshold=self.exit_z_score,
            position_a=position_a,
            position_b=position_b,
            hedge_ratio=pair.beta,
        )
    
    def get_dc_enhanced_signal(self, asset_a: str, asset_b: str,
                               dc_threshold: float = 0.02) -> Optional[SpreadSignal]:
        """
        Get DC-enhanced spread signal
        
        Applies DC threshold to the spread itself
        """
        signal = self.calculate_spread_signal(asset_a, asset_b)
        
        if signal is None:
            return None
        
        # Apply DC logic to spread
        pair_key = (asset_a, asset_b)
        
        if pair_key not in self.active_positions:
            self.active_positions[pair_key] = {
                'extreme_spread': signal.spread_value,
                'direction': None,
            }
        
        pos = self.active_positions[pair_key]
        
        # Check for DC reversal in spread
        if pos['direction'] is None:
            # Initialize direction
            if signal.z_score > 0:
                pos['direction'] = 'up'
                pos['extreme_spread'] = signal.spread_value
            else:
                pos['direction'] = 'down'
                pos['extreme_spread'] = signal.spread_value
        else:
            # Update extreme
            if pos['direction'] == 'up' and signal.spread_value > pos['extreme_spread']:
                pos['extreme_spread'] = signal.spread_value
            elif pos['direction'] == 'down' and signal.spread_value < pos['extreme_spread']:
                pos['extreme_spread'] = signal.spread_value
            
            # Check for DC reversal
            if pos['extreme_spread'] != 0:
                change = (signal.spread_value - pos['extreme_spread']) / abs(pos['extreme_spread'])
                
                if pos['direction'] == 'up' and change < -dc_threshold:
                    # DC reversal down - spread was high, now reversing
                    signal.signal_strength *= 1.3  # Boost signal
                    pos['direction'] = 'down'
                    pos['extreme_spread'] = signal.spread_value
                elif pos['direction'] == 'down' and change > dc_threshold:
                    # DC reversal up - spread was low, now reversing
                    signal.signal_strength *= 1.3
                    pos['direction'] = 'up'
                    pos['extreme_spread'] = signal.spread_value
        
        return signal


class BasketTrader:
    """
    Basket Trading Strategy
    
    Creates synthetic instruments from multiple assets
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Predefined baskets
        self.baskets = {
            'TECH': {
                'AAPL': 0.25,
                'MSFT': 0.25,
                'GOOGL': 0.25,
                'AMZN': 0.25,
            },
            'FINANCE': {
                'JPM': 0.25,
                'BAC': 0.25,
                'GS': 0.25,
                'MS': 0.25,
            },
            'ENERGY': {
                'XOM': 0.33,
                'CVX': 0.33,
                'COP': 0.34,
            },
        }
        
        # Price history
        self.price_history: Dict[str, deque] = {}
        
        # Basket values
        self.basket_values: Dict[str, deque] = {}
    
    def update_price(self, symbol: str, price: float):
        """Update price for symbol"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=500)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': datetime.now(),
        })
        
        # Update basket values
        self._update_basket_values()
    
    def _update_basket_values(self):
        """Update all basket values"""
        for basket_name, weights in self.baskets.items():
            value = 0
            complete = True
            
            for symbol, weight in weights.items():
                if symbol in self.price_history and self.price_history[symbol]:
                    value += self.price_history[symbol][-1]['price'] * weight
                else:
                    complete = False
                    break
            
            if complete:
                if basket_name not in self.basket_values:
                    self.basket_values[basket_name] = deque(maxlen=500)
                
                self.basket_values[basket_name].append({
                    'value': value,
                    'timestamp': datetime.now(),
                })
    
    def get_basket_signal(self, basket_name: str) -> Optional[Dict[str, Any]]:
        """
        Get trading signal for basket
        
        Args:
            basket_name: Name of basket
            
        Returns:
            Signal dictionary
        """
        if basket_name not in self.basket_values:
            return None
        
        values = [v['value'] for v in self.basket_values[basket_name]]
        
        if len(values) < 20:
            return None
        
        # Calculate momentum
        current = values[-1]
        ma_short = np.mean(values[-5:])
        ma_long = np.mean(values[-20:])
        
        # Signal based on MA crossover
        if ma_short > ma_long * 1.01:
            direction = 'long'
            strength = (ma_short / ma_long - 1) * 10
        elif ma_short < ma_long * 0.99:
            direction = 'short'
            strength = (1 - ma_short / ma_long) * 10
        else:
            direction = 'neutral'
            strength = 0
        
        return {
            'basket': basket_name,
            'direction': direction,
            'strength': min(strength, 1.0),
            'current_value': current,
            'ma_short': ma_short,
            'ma_long': ma_long,
            'weights': self.baskets[basket_name],
        }


class TriangularArbitrage:
    """
    Triangular Arbitrage for Forex
    
    Exploits pricing inefficiencies across three currencies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Currency pairs
        self.pairs: Dict[str, float] = {}
        
        # Triangles to monitor
        self.triangles = [
            ('EUR/USD', 'GBP/USD', 'EUR/GBP'),
            ('USD/JPY', 'EUR/USD', 'EUR/JPY'),
            ('GBP/USD', 'USD/CHF', 'GBP/CHF'),
            ('AUD/USD', 'USD/JPY', 'AUD/JPY'),
        ]
        
        # Minimum profit threshold (in bps)
        self.min_profit_bps = self.config.get('min_profit_bps', 5)
    
    def update_rate(self, pair: str, rate: float):
        """Update exchange rate"""
        self.pairs[pair] = rate
    
    def check_arbitrage(self, triangle: Tuple[str, str, str]) -> Optional[ArbitrageOpportunity]:
        """
        Check for arbitrage opportunity in triangle
        
        Args:
            triangle: Tuple of three currency pairs
            
        Returns:
            ArbitrageOpportunity if found
        """
        pair1, pair2, pair3 = triangle
        
        if not all(p in self.pairs for p in triangle):
            return None
        
        rate1 = self.pairs[pair1]
        rate2 = self.pairs[pair2]
        rate3 = self.pairs[pair3]
        
        # Calculate synthetic rate
        # Example: EUR/USD and GBP/USD -> synthetic EUR/GBP = EUR/USD / GBP/USD
        base1, quote1 = pair1.split('/')
        base2, quote2 = pair2.split('/')
        base3, quote3 = pair3.split('/')
        
        # Calculate implied rate
        if quote1 == quote2:
            # Both quoted in same currency
            implied_rate = rate1 / rate2
        elif base1 == quote2:
            implied_rate = rate1 * rate2
        else:
            implied_rate = rate1 / rate2
        
        # Compare with actual rate
        actual_rate = rate3
        
        # Calculate profit
        profit_pct = abs(implied_rate - actual_rate) / actual_rate * 10000  # In bps
        
        if profit_pct < self.min_profit_bps:
            return None
        
        # Determine trade direction
        if implied_rate > actual_rate:
            # Synthetic is expensive, sell synthetic, buy actual
            trades = [
                {'pair': pair3, 'action': 'buy', 'reason': 'Actual is cheap'},
                {'pair': pair1, 'action': 'sell', 'reason': 'Part of synthetic'},
                {'pair': pair2, 'action': 'buy', 'reason': 'Part of synthetic'},
            ]
        else:
            trades = [
                {'pair': pair3, 'action': 'sell', 'reason': 'Actual is expensive'},
                {'pair': pair1, 'action': 'buy', 'reason': 'Part of synthetic'},
                {'pair': pair2, 'action': 'sell', 'reason': 'Part of synthetic'},
            ]
        
        return ArbitrageOpportunity(
            timestamp=datetime.now(),
            arb_type=ArbitrageType.TRIANGULAR,
            assets=list(triangle),
            expected_profit_bps=profit_pct,
            confidence=0.9,
            execution_risk=0.3,  # Forex is liquid
            time_sensitivity='immediate',
            trades=trades,
        )
    
    def scan_all_triangles(self) -> List[ArbitrageOpportunity]:
        """Scan all triangles for opportunities"""
        opportunities = []
        
        for triangle in self.triangles:
            opp = self.check_arbitrage(triangle)
            if opp:
                opportunities.append(opp)
        
        return sorted(opportunities, key=lambda x: x.expected_profit_bps, reverse=True)


class CrossExchangeArbitrage:
    """
    Cross-Exchange Arbitrage for Crypto
    
    Same asset trading at different prices across exchanges
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Exchange prices
        self.prices: Dict[str, Dict[str, float]] = {}  # exchange -> symbol -> price
        
        # Exchanges to monitor
        self.exchanges = ['binance', 'coinbase', 'kraken', 'ftx', 'okx']
        
        # Symbols to monitor
        self.symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        
        # Minimum profit threshold
        self.min_profit_bps = self.config.get('min_profit_bps', 10)
        
        # Fee structure
        self.fees = {
            'binance': 0.1,
            'coinbase': 0.5,
            'kraken': 0.26,
            'ftx': 0.07,
            'okx': 0.1,
        }
    
    def update_price(self, exchange: str, symbol: str, price: float):
        """Update price for exchange/symbol"""
        if exchange not in self.prices:
            self.prices[exchange] = {}
        
        self.prices[exchange][symbol] = price
    
    def find_arbitrage(self, symbol: str) -> Optional[ArbitrageOpportunity]:
        """
        Find arbitrage opportunity for symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            ArbitrageOpportunity if found
        """
        # Get prices across exchanges
        exchange_prices = []
        
        for exchange in self.exchanges:
            if exchange in self.prices and symbol in self.prices[exchange]:
                exchange_prices.append({
                    'exchange': exchange,
                    'price': self.prices[exchange][symbol],
                    'fee': self.fees.get(exchange, 0.1),
                })
        
        if len(exchange_prices) < 2:
            return None
        
        # Find best buy and sell
        sorted_prices = sorted(exchange_prices, key=lambda x: x['price'])
        
        buy_exchange = sorted_prices[0]
        sell_exchange = sorted_prices[-1]
        
        # Calculate profit after fees
        buy_price = buy_exchange['price'] * (1 + buy_exchange['fee'] / 100)
        sell_price = sell_exchange['price'] * (1 - sell_exchange['fee'] / 100)
        
        profit_bps = (sell_price - buy_price) / buy_price * 10000
        
        if profit_bps < self.min_profit_bps:
            return None
        
        return ArbitrageOpportunity(
            timestamp=datetime.now(),
            arb_type=ArbitrageType.CROSS_EXCHANGE,
            assets=[symbol],
            expected_profit_bps=profit_bps,
            confidence=0.85,
            execution_risk=0.4,  # Transfer risk
            time_sensitivity='immediate',
            trades=[
                {
                    'exchange': buy_exchange['exchange'],
                    'action': 'buy',
                    'price': buy_exchange['price'],
                },
                {
                    'exchange': sell_exchange['exchange'],
                    'action': 'sell',
                    'price': sell_exchange['price'],
                },
            ],
        )
    
    def scan_all_symbols(self) -> List[ArbitrageOpportunity]:
        """Scan all symbols for opportunities"""
        opportunities = []
        
        for symbol in self.symbols:
            opp = self.find_arbitrage(symbol)
            if opp:
                opportunities.append(opp)
        
        return sorted(opportunities, key=lambda x: x.expected_profit_bps, reverse=True)


class VolatilityArbitrage:
    """
    Options Volatility Arbitrage
    
    Exploits mispricing in volatility surface
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Volatility surface
        self.implied_vols: Dict[str, Dict[float, Dict[float, float]]] = {}  # symbol -> strike -> expiry -> IV
        
        # Historical volatility
        self.realized_vols: Dict[str, float] = {}
        
        # Price history for RV calculation
        self.price_history: Dict[str, deque] = {}
    
    def update_implied_vol(self, symbol: str, strike: float, expiry_days: float, iv: float):
        """Update implied volatility"""
        if symbol not in self.implied_vols:
            self.implied_vols[symbol] = {}
        if strike not in self.implied_vols[symbol]:
            self.implied_vols[symbol][strike] = {}
        
        self.implied_vols[symbol][strike][expiry_days] = iv
    
    def update_price(self, symbol: str, price: float):
        """Update price for realized vol calculation"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=252)
        
        self.price_history[symbol].append(price)
        
        # Calculate realized vol
        if len(self.price_history[symbol]) >= 20:
            prices = list(self.price_history[symbol])
            returns = np.diff(np.log(prices))
            self.realized_vols[symbol] = np.std(returns) * np.sqrt(252)
    
    def find_vol_arbitrage(self, symbol: str) -> Optional[ArbitrageOpportunity]:
        """
        Find volatility arbitrage opportunity
        
        Args:
            symbol: Trading symbol
            
        Returns:
            ArbitrageOpportunity if found
        """
        if symbol not in self.implied_vols or symbol not in self.realized_vols:
            return None
        
        realized_vol = self.realized_vols[symbol]
        
        # Find mispriced options
        opportunities = []
        
        for strike, expiries in self.implied_vols[symbol].items():
            for expiry, iv in expiries.items():
                # Compare IV to RV
                vol_diff = iv - realized_vol
                
                if abs(vol_diff) > 0.05:  # 5% vol difference
                    opportunities.append({
                        'strike': strike,
                        'expiry': expiry,
                        'iv': iv,
                        'rv': realized_vol,
                        'diff': vol_diff,
                    })
        
        if not opportunities:
            return None
        
        # Take best opportunity
        best = max(opportunities, key=lambda x: abs(x['diff']))
        
        if best['diff'] > 0:
            # IV > RV: Sell volatility
            trades = [
                {'action': 'sell_straddle', 'strike': best['strike'], 'expiry': best['expiry']},
                {'action': 'delta_hedge', 'reason': 'Maintain delta neutral'},
            ]
            direction = 'short_vol'
        else:
            # IV < RV: Buy volatility
            trades = [
                {'action': 'buy_straddle', 'strike': best['strike'], 'expiry': best['expiry']},
                {'action': 'delta_hedge', 'reason': 'Maintain delta neutral'},
            ]
            direction = 'long_vol'
        
        return ArbitrageOpportunity(
            timestamp=datetime.now(),
            arb_type=ArbitrageType.VOLATILITY,
            assets=[symbol],
            expected_profit_bps=abs(best['diff']) * 100,  # Rough estimate
            confidence=0.7,
            execution_risk=0.5,
            time_sensitivity='medium',
            trades=trades,
        )


class CrossAssetArbitrageEngine:
    """
    Unified Cross-Asset Arbitrage Engine
    
    Combines all arbitrage strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize strategies
        self.pairs_trader = PairsTrader(config.get('pairs', {}))
        self.basket_trader = BasketTrader(config.get('basket', {}))
        self.triangular_arb = TriangularArbitrage(config.get('triangular', {}))
        self.cross_exchange_arb = CrossExchangeArbitrage(config.get('cross_exchange', {}))
        self.vol_arb = VolatilityArbitrage(config.get('volatility', {}))
        
        # Opportunity history
        self.opportunities: deque = deque(maxlen=1000)
    
    def update_equity_price(self, symbol: str, price: float):
        """Update equity price"""
        self.pairs_trader.update_price(symbol, price)
        self.basket_trader.update_price(symbol, price)
        self.vol_arb.update_price(symbol, price)
    
    def update_forex_rate(self, pair: str, rate: float):
        """Update forex rate"""
        self.triangular_arb.update_rate(pair, rate)
    
    def update_crypto_price(self, exchange: str, symbol: str, price: float):
        """Update crypto price"""
        self.cross_exchange_arb.update_price(exchange, symbol, price)
    
    def scan_all_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Scan all strategies for opportunities
        
        Returns:
            List of opportunities sorted by expected profit
        """
        all_opportunities = []
        
        # Triangular forex
        all_opportunities.extend(self.triangular_arb.scan_all_triangles())
        
        # Cross-exchange crypto
        all_opportunities.extend(self.cross_exchange_arb.scan_all_symbols())
        
        # Sort by expected profit
        all_opportunities.sort(key=lambda x: x.expected_profit_bps, reverse=True)
        
        # Store
        for opp in all_opportunities:
            self.opportunities.append(opp)
        
        return all_opportunities
    
    def get_pairs_signal(self, asset_a: str, asset_b: str) -> Optional[SpreadSignal]:
        """Get pairs trading signal"""
        return self.pairs_trader.get_dc_enhanced_signal(asset_a, asset_b)
    
    def get_basket_signal(self, basket_name: str) -> Optional[Dict[str, Any]]:
        """Get basket trading signal"""
        return self.basket_trader.get_basket_signal(basket_name)
