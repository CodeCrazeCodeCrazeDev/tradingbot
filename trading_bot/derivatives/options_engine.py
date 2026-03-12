"""
Options Pricing and Derivatives Engine
=======================================

Comprehensive options and derivatives:
- Black-Scholes pricing
- Binomial tree pricing
- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Options strategy builder
- Volatility surface modeling
- Options scanner
- Futures roll manager
- Basis trading
- Options P&L attribution
- Expiration manager

Author: Elite Trading Bot
Version: 1.0.0
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum, auto
from collections import defaultdict
import threading
import numpy as np
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import brentq
import numpy

logger = logging.getLogger(__name__)


class OptionType(Enum):
    """Option type"""
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    """Option style"""
    EUROPEAN = "european"
    AMERICAN = "american"


class StrategyType(Enum):
    """Options strategy types"""
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    CALENDAR_SPREAD = "calendar_spread"
    COLLAR = "collar"


@dataclass
class Greeks:
    """Option Greeks"""
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    
    # Second-order Greeks
    vanna: float = 0.0      # d(delta)/d(vol)
    charm: float = 0.0      # d(delta)/d(time)
    vomma: float = 0.0      # d(vega)/d(vol)
    
    def to_dict(self) -> Dict:
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho,
            'vanna': self.vanna,
            'charm': self.charm,
            'vomma': self.vomma
        }


@dataclass
class OptionContract:
    """Option contract"""
    symbol: str
    underlying: str
    option_type: OptionType
    strike: float
    expiration: date
    style: OptionStyle = OptionStyle.EUROPEAN
    
    # Pricing
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    
    # Underlying
    underlying_price: float = 0.0
    
    # Greeks
    greeks: Greeks = field(default_factory=Greeks)
    
    # Implied volatility
    implied_vol: float = 0.0
    
    # Volume and OI
    volume: int = 0
    open_interest: int = 0
    
    @property
    def days_to_expiry(self) -> int:
        return (self.expiration - date.today()).days
    
    @property
    def time_to_expiry(self) -> float:
        """Time to expiry in years"""
        return self.days_to_expiry / 365.0
    
    @property
    def is_itm(self) -> bool:
        """Is in the money"""
        if self.option_type == OptionType.CALL:
            return self.underlying_price > self.strike
        else:
            return self.underlying_price < self.strike
    
    @property
    def intrinsic_value(self) -> float:
        """Intrinsic value"""
        if self.option_type == OptionType.CALL:
            return max(0, self.underlying_price - self.strike)
        else:
            return max(0, self.strike - self.underlying_price)
    
    @property
    def time_value(self) -> float:
        """Time value"""
        return self.price - self.intrinsic_value
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'underlying': self.underlying,
            'type': self.option_type.value,
            'strike': self.strike,
            'expiration': self.expiration.isoformat(),
            'price': self.price,
            'bid': self.bid,
            'ask': self.ask,
            'underlying_price': self.underlying_price,
            'greeks': self.greeks.to_dict(),
            'implied_vol': self.implied_vol,
            'days_to_expiry': self.days_to_expiry,
            'is_itm': self.is_itm,
            'intrinsic_value': self.intrinsic_value,
            'time_value': self.time_value
        }


@dataclass
class FuturesContract:
    """Futures contract"""
    symbol: str
    underlying: str
    expiration: date
    
    # Pricing
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    
    # Underlying
    spot_price: float = 0.0
    
    # Basis
    basis: float = 0.0
    basis_pct: float = 0.0
    
    # Contract specs
    multiplier: float = 1.0
    tick_size: float = 0.01
    
    # Volume
    volume: int = 0
    open_interest: int = 0
    
    @property
    def days_to_expiry(self) -> int:
        return (self.expiration - date.today()).days
    
    def calculate_basis(self):
        """Calculate basis"""
        self.basis = self.price - self.spot_price
        if self.spot_price > 0:
            self.basis_pct = (self.basis / self.spot_price) * 100
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'underlying': self.underlying,
            'expiration': self.expiration.isoformat(),
            'price': self.price,
            'spot_price': self.spot_price,
            'basis': self.basis,
            'basis_pct': self.basis_pct,
            'days_to_expiry': self.days_to_expiry
        }


class BlackScholesModel:
    """
    Black-Scholes option pricing model
    """
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2"""
        if T <= 0 or sigma <= 0:
            return 0.0
        return BlackScholesModel.d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate call option price"""
        if T <= 0:
            return max(0, S - K)
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        d2 = BlackScholesModel.d2(S, K, T, r, sigma)
        
        return S * stats.norm.cdf(d1) - K * np.exp(-r * T) * stats.norm.cdf(d2)
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate put option price"""
        if T <= 0:
            return max(0, K - S)
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        d2 = BlackScholesModel.d2(S, K, T, r, sigma)
        
        return K * np.exp(-r * T) * stats.norm.cdf(-d2) - S * stats.norm.cdf(-d1)
    
    @staticmethod
    def price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """Calculate option price"""
        if option_type == OptionType.CALL:
            return BlackScholesModel.call_price(S, K, T, r, sigma)
        else:
            return BlackScholesModel.put_price(S, K, T, r, sigma)


class GreeksCalculator:
    """
    Calculates option Greeks
    """
    
    @staticmethod
    def delta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """Calculate delta"""
        if T <= 0:
            if option_type == OptionType.CALL:
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        
        if option_type == OptionType.CALL:
            return stats.norm.cdf(d1)
        else:
            return stats.norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate gamma"""
        if T <= 0 or sigma <= 0:
            return 0.0
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        return stats.norm.pdf(d1) / (S * sigma * np.sqrt(T))
    
    @staticmethod
    def theta(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """Calculate theta (per day)"""
        if T <= 0:
            return 0.0
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        d2 = BlackScholesModel.d2(S, K, T, r, sigma)
        
        term1 = -(S * stats.norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == OptionType.CALL:
            term2 = -r * K * np.exp(-r * T) * stats.norm.cdf(d2)
        else:
            term2 = r * K * np.exp(-r * T) * stats.norm.cdf(-d2)
        
        return (term1 + term2) / 365  # Per day
    
    @staticmethod
    def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate vega (per 1% vol change)"""
        if T <= 0:
            return 0.0
        
        d1 = BlackScholesModel.d1(S, K, T, r, sigma)
        return S * stats.norm.pdf(d1) * np.sqrt(T) / 100
    
    @staticmethod
    def rho(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> float:
        """Calculate rho (per 1% rate change)"""
        if T <= 0:
            return 0.0
        
        d2 = BlackScholesModel.d2(S, K, T, r, sigma)
        
        if option_type == OptionType.CALL:
            return K * T * np.exp(-r * T) * stats.norm.cdf(d2) / 100
        else:
            return -K * T * np.exp(-r * T) * stats.norm.cdf(-d2) / 100
    
    @staticmethod
    def calculate_all(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> Greeks:
        """Calculate all Greeks"""
        return Greeks(
            delta=GreeksCalculator.delta(S, K, T, r, sigma, option_type),
            gamma=GreeksCalculator.gamma(S, K, T, r, sigma),
            theta=GreeksCalculator.theta(S, K, T, r, sigma, option_type),
            vega=GreeksCalculator.vega(S, K, T, r, sigma),
            rho=GreeksCalculator.rho(S, K, T, r, sigma, option_type)
        )


class ImpliedVolatilityCalculator:
    """
    Calculates implied volatility
    """
    
    @staticmethod
    def calculate(
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType,
        initial_guess: float = 0.2
    ) -> float:
        """Calculate implied volatility using Newton-Raphson"""
        if T <= 0 or market_price <= 0:
            return 0.0
        
        def objective(sigma):
            try:
                price = BlackScholesModel.price(S, K, T, r, sigma, option_type)
                return price - market_price

                iv = brentq(objective, 0.001, 5.0)
                return iv
            except ValueError:
                # Fallback to Newton-Raphson
                sigma = initial_guess
                for _ in range(100):
                    price = BlackScholesModel.price(S, K, T, r, sigma, option_type)
                    vega = GreeksCalculator.vega(S, K, T, r, sigma) * 100

                    if abs(vega) < 1e-10:
                        break

                    sigma = sigma - (price - market_price) / vega
                    sigma = max(0.001, min(5.0, sigma))

                    if abs(price - market_price) < 0.001:
                        break

                return sigma


class BinomialTreeModel:
    """
    Binomial tree option pricing (for American options)
    """
    
    @staticmethod
    def price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        steps: int = 100
    ) -> float:
        """Price option using binomial tree"""
        if T <= 0:
            if option_type == OptionType.CALL:
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        
        # Build price tree
        prices = np.zeros(steps + 1)
        for i in range(steps + 1):
            prices[i] = S * (u ** (steps - i)) * (d ** i)
        
        # Calculate option values at expiry
        if option_type == OptionType.CALL:
            values = np.maximum(prices - K, 0)
        else:
            values = np.maximum(K - prices, 0)
        
        # Work backwards through tree
        for step in range(steps - 1, -1, -1):
            for i in range(step + 1):
                # Continuation value
                cont_value = np.exp(-r * dt) * (p * values[i] + (1 - p) * values[i + 1])
                
                # Early exercise value
                price_at_node = S * (u ** (step - i)) * (d ** i)
                if option_type == OptionType.CALL:
                    exercise_value = max(0, price_at_node - K)
                else:
                    exercise_value = max(0, K - price_at_node)
                
                # American option: take max
                values[i] = max(cont_value, exercise_value)
        
        return values[0]


class OptionsStrategyBuilder:
    """
    Builds and analyzes options strategies
    """
    
    def __init__(self):
        self.strategies: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
        logger.info("OptionsStrategyBuilder initialized")
    
    def build_strategy(
        self,
        strategy_type: StrategyType,
        underlying: str,
        underlying_price: float,
        options: List[OptionContract],
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Build an options strategy"""
        strategy = {
            'type': strategy_type.value,
            'underlying': underlying,
            'underlying_price': underlying_price,
            'legs': [],
            'max_profit': 0.0,
            'max_loss': 0.0,
            'breakeven': [],
            'net_premium': 0.0,
            'net_delta': 0.0,
            'net_gamma': 0.0,
            'net_theta': 0.0,
            'net_vega': 0.0
        }
        
        for option in options:
            leg = {
                'option': option.to_dict(),
                'quantity': quantity,
                'side': 'long'  # Will be adjusted per strategy
            }
            strategy['legs'].append(leg)
            
            # Aggregate Greeks
            strategy['net_delta'] += option.greeks.delta * quantity
            strategy['net_gamma'] += option.greeks.gamma * quantity
            strategy['net_theta'] += option.greeks.theta * quantity
            strategy['net_vega'] += option.greeks.vega * quantity
            strategy['net_premium'] += option.price * quantity
        
        # Calculate P&L profile
        strategy['pnl_profile'] = self._calculate_pnl_profile(
            strategy, underlying_price
        )
        
        return strategy
    
    def _calculate_pnl_profile(
        self,
        strategy: Dict,
        current_price: float
    ) -> List[Dict]:
        """Calculate P&L profile at various prices"""
        profile = []
        
        # Price range: +/- 20% from current
        prices = np.linspace(current_price * 0.8, current_price * 1.2, 50)
        
        for price in prices:
            pnl = 0.0
            
            for leg in strategy['legs']:
                option = leg['option']
                qty = leg['quantity']
                side_mult = 1 if leg['side'] == 'long' else -1
                
                # Calculate value at expiry
                if option['type'] == 'call':
                    value = max(0, price - option['strike'])
                else:
                    value = max(0, option['strike'] - price)
                
                # P&L = (value - premium) * quantity * side
                leg_pnl = (value - option['price']) * qty * side_mult
                pnl += leg_pnl
            
            profile.append({
                'price': price,
                'pnl': pnl
            })
        
        return profile
    
    def create_straddle(
        self,
        underlying: str,
        strike: float,
        expiration: date,
        call_price: float,
        put_price: float,
        underlying_price: float
    ) -> Dict:
        """Create a straddle strategy"""
        call = OptionContract(
            symbol=f"{underlying}_{strike}C_{expiration}",
            underlying=underlying,
            option_type=OptionType.CALL,
            strike=strike,
            expiration=expiration,
            price=call_price,
            underlying_price=underlying_price
        )
        
        put = OptionContract(
            symbol=f"{underlying}_{strike}P_{expiration}",
            underlying=underlying,
            option_type=OptionType.PUT,
            strike=strike,
            expiration=expiration,
            price=put_price,
            underlying_price=underlying_price
        )
        
        total_premium = call_price + put_price
        
        return {
            'type': 'straddle',
            'underlying': underlying,
            'strike': strike,
            'expiration': expiration.isoformat(),
            'call': call.to_dict(),
            'put': put.to_dict(),
            'total_premium': total_premium,
            'upper_breakeven': strike + total_premium,
            'lower_breakeven': strike - total_premium,
            'max_loss': total_premium,
            'max_profit': 'unlimited'
        }
    
    def create_iron_condor(
        self,
        underlying: str,
        put_buy_strike: float,
        put_sell_strike: float,
        call_sell_strike: float,
        call_buy_strike: float,
        expiration: date,
        prices: Dict[float, float],
        underlying_price: float
    ) -> Dict:
        """Create an iron condor strategy"""
        net_credit = (
            prices.get(put_sell_strike, 0) - prices.get(put_buy_strike, 0) +
            prices.get(call_sell_strike, 0) - prices.get(call_buy_strike, 0)
        )
        
        put_spread_width = put_sell_strike - put_buy_strike
        call_spread_width = call_buy_strike - call_sell_strike
        max_loss = max(put_spread_width, call_spread_width) - net_credit
        
        return {
            'type': 'iron_condor',
            'underlying': underlying,
            'expiration': expiration.isoformat(),
            'put_buy_strike': put_buy_strike,
            'put_sell_strike': put_sell_strike,
            'call_sell_strike': call_sell_strike,
            'call_buy_strike': call_buy_strike,
            'net_credit': net_credit,
            'max_profit': net_credit,
            'max_loss': max_loss,
            'lower_breakeven': put_sell_strike - net_credit,
            'upper_breakeven': call_sell_strike + net_credit
        }


class VolatilitySurface:
    """
    Models implied volatility surface
    """
    
    def __init__(self):
        # IV data: {expiration: {strike: iv}}
        self.iv_data: Dict[date, Dict[float, float]] = defaultdict(dict)
        
        # ATM term structure
        self.atm_term_structure: Dict[date, float] = {}
        
        # Skew parameters
        self.skew: Dict[date, float] = {}
        
        self._lock = threading.RLock()
        
        logger.info("VolatilitySurface initialized")
    
    def update_iv(self, expiration: date, strike: float, iv: float):
        """Update IV point"""
        with self._lock:
            self.iv_data[expiration][strike] = iv
    
    def get_iv(self, expiration: date, strike: float) -> Optional[float]:
        """Get IV for a specific point"""
        with self._lock:
            return self.iv_data.get(expiration, {}).get(strike)
    
    def interpolate_iv(
        self,
        expiration: date,
        strike: float,
        underlying_price: float
    ) -> float:
        """Interpolate IV for a strike"""
        with self._lock:
            strikes_ivs = self.iv_data.get(expiration, {})
            
            if not strikes_ivs:
                return 0.2  # Default
            
            strikes = sorted(strikes_ivs.keys())
            
            # Find surrounding strikes
            lower = None
            upper = None
            
            for s in strikes:
                if s <= strike:
                    lower = s
                if s >= strike and upper is None:
                    upper = s
            
            if lower is None:
                return strikes_ivs[strikes[0]]
            if upper is None:
                return strikes_ivs[strikes[-1]]
            if lower == upper:
                return strikes_ivs[lower]
            
            # Linear interpolation
            iv_lower = strikes_ivs[lower]
            iv_upper = strikes_ivs[upper]
            
            weight = (strike - lower) / (upper - lower)
            return iv_lower + weight * (iv_upper - iv_lower)
    
    def calculate_skew(self, expiration: date, underlying_price: float) -> float:
        """Calculate volatility skew"""
        with self._lock:
            strikes_ivs = self.iv_data.get(expiration, {})
            
            if len(strikes_ivs) < 3:
                return 0.0
            
            # Find ATM and OTM puts
            atm_strike = min(strikes_ivs.keys(), key=lambda x: abs(x - underlying_price))
            otm_put_strike = atm_strike * 0.9
            
            atm_iv = self.interpolate_iv(expiration, atm_strike, underlying_price)
            otm_iv = self.interpolate_iv(expiration, otm_put_strike, underlying_price)
            
            return otm_iv - atm_iv
    
    def get_term_structure(self, strike: float) -> Dict[date, float]:
        """Get IV term structure for a strike"""
        with self._lock:
            term_structure = {}
            
            for exp, strikes_ivs in sorted(self.iv_data.items()):
                if strike in strikes_ivs:
                    term_structure[exp] = strikes_ivs[strike]
            
            return term_structure


class OptionsScanner:
    """
    Scans for unusual options activity
    """
    
    def __init__(
        self,
        volume_threshold: float = 2.0,
        oi_threshold: float = 1.5
    ):
        self.volume_threshold = volume_threshold
        self.oi_threshold = oi_threshold
        
        # Historical data
        self.avg_volume: Dict[str, float] = {}
        self.avg_oi: Dict[str, float] = {}
        
        # Alerts
        self.alerts: List[Dict] = []
        
        # Callbacks
        self.on_alert: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("OptionsScanner initialized")
    
    def scan(self, options: List[OptionContract]) -> List[Dict]:
        """Scan options for unusual activity"""
        alerts = []
        
        for option in options:
            symbol = option.symbol
            
            # Check volume spike
            avg_vol = self.avg_volume.get(symbol, option.volume)
            if avg_vol > 0 and option.volume > avg_vol * self.volume_threshold:
                alert = {
                    'type': 'volume_spike',
                    'symbol': symbol,
                    'underlying': option.underlying,
                    'strike': option.strike,
                    'option_type': option.option_type.value,
                    'expiration': option.expiration.isoformat(),
                    'volume': option.volume,
                    'avg_volume': avg_vol,
                    'ratio': option.volume / avg_vol,
                    'timestamp': datetime.now()
                }
                alerts.append(alert)
            
            # Check OI change
            avg_oi = self.avg_oi.get(symbol, option.open_interest)
            if avg_oi > 0 and option.open_interest > avg_oi * self.oi_threshold:
                alert = {
                    'type': 'oi_spike',
                    'symbol': symbol,
                    'underlying': option.underlying,
                    'strike': option.strike,
                    'option_type': option.option_type.value,
                    'expiration': option.expiration.isoformat(),
                    'open_interest': option.open_interest,
                    'avg_oi': avg_oi,
                    'ratio': option.open_interest / avg_oi,
                    'timestamp': datetime.now()
                }
                alerts.append(alert)
            
            # Update averages
            self.avg_volume[symbol] = (avg_vol * 0.9 + option.volume * 0.1)
            self.avg_oi[symbol] = (avg_oi * 0.9 + option.open_interest * 0.1)
        
        # Store and notify
        with self._lock:
            self.alerts.extend(alerts)
        
        for alert in alerts:
            for callback in self.on_alert:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")
        
        return alerts
    
    def get_recent_alerts(self, count: int = 50) -> List[Dict]:
        """Get recent alerts"""
        with self._lock:
            return self.alerts[-count:]


class FuturesRollManager:
    """
    Manages futures contract rolls
    """
    
    def __init__(self, roll_days_before_expiry: int = 5):
        self.roll_days = roll_days_before_expiry
        
        # Active contracts
        self.contracts: Dict[str, FuturesContract] = {}
        
        # Roll schedule
        self.roll_schedule: List[Dict] = []
        
        # Roll history
        self.roll_history: List[Dict] = []
        
        self._lock = threading.RLock()
        
        logger.info("FuturesRollManager initialized")
    
    def add_contract(self, contract: FuturesContract):
        """Add a futures contract"""
        with self._lock:
            self.contracts[contract.symbol] = contract
            self._update_roll_schedule()
    
    def _update_roll_schedule(self):
        """Update roll schedule"""
        schedule = []
        
        for symbol, contract in self.contracts.items():
            roll_date = contract.expiration - timedelta(days=self.roll_days)
            
            schedule.append({
                'symbol': symbol,
                'expiration': contract.expiration,
                'roll_date': roll_date,
                'days_to_roll': (roll_date - date.today()).days
            })
        
        schedule.sort(key=lambda x: x['roll_date'])
        self.roll_schedule = schedule
    
    def get_contracts_to_roll(self) -> List[Dict]:
        """Get contracts that need to be rolled"""
        today = date.today()
        
        return [
            item for item in self.roll_schedule
            if item['roll_date'] <= today
        ]
    
    def calculate_roll_cost(
        self,
        front_contract: FuturesContract,
        back_contract: FuturesContract
    ) -> Dict[str, float]:
        """Calculate roll cost"""
        # Calendar spread
        spread = back_contract.price - front_contract.price
        spread_pct = (spread / front_contract.price) * 100 if front_contract.price > 0 else 0
        
        # Annualized roll yield
        days_between = (back_contract.expiration - front_contract.expiration).days
        annualized = (spread_pct / days_between) * 365 if days_between > 0 else 0
        
        return {
            'spread': spread,
            'spread_pct': spread_pct,
            'annualized_yield': annualized,
            'front_price': front_contract.price,
            'back_price': back_contract.price
        }
    
    def record_roll(
        self,
        front_symbol: str,
        back_symbol: str,
        quantity: float,
        front_price: float,
        back_price: float
    ):
        """Record a roll transaction"""
        roll = {
            'timestamp': datetime.now(),
            'front_symbol': front_symbol,
            'back_symbol': back_symbol,
            'quantity': quantity,
            'front_price': front_price,
            'back_price': back_price,
            'spread': back_price - front_price,
            'cost': (back_price - front_price) * quantity
        }
        
        with self._lock:
            self.roll_history.append(roll)
            
            # Remove front contract
            if front_symbol in self.contracts:
                del self.contracts[front_symbol]
            
            self._update_roll_schedule()
        
        return roll


class OptionsPnLAttribution:
    """
    Attributes options P&L to Greeks
    """
    
    def __init__(self):
        self.positions: Dict[str, Dict] = {}
        self.pnl_history: List[Dict] = []
        
        self._lock = threading.RLock()
        
        logger.info("OptionsPnLAttribution initialized")
    
    def add_position(
        self,
        symbol: str,
        option: OptionContract,
        quantity: int,
        entry_price: float
    ):
        """Add an options position"""
        with self._lock:
            self.positions[symbol] = {
                'option': option,
                'quantity': quantity,
                'entry_price': entry_price,
                'entry_underlying': option.underlying_price,
                'entry_iv': option.implied_vol,
                'entry_greeks': option.greeks,
                'entry_time': datetime.now()
            }
    
    def calculate_attribution(
        self,
        symbol: str,
        current_option: OptionContract
    ) -> Dict[str, float]:
        """Calculate P&L attribution"""
        with self._lock:
            position = self.positions.get(symbol)
            
            if not position:
                return {}
            
            entry = position
            qty = entry['quantity']
            
            # Total P&L
            total_pnl = (current_option.price - entry['entry_price']) * qty
            
            # Delta P&L
            underlying_move = current_option.underlying_price - entry['entry_underlying']
            delta_pnl = entry['entry_greeks'].delta * underlying_move * qty
            
            # Gamma P&L
            gamma_pnl = 0.5 * entry['entry_greeks'].gamma * (underlying_move ** 2) * qty
            
            # Theta P&L
            days_held = (datetime.now() - entry['entry_time']).days
            theta_pnl = entry['entry_greeks'].theta * days_held * qty
            
            # Vega P&L
            iv_change = (current_option.implied_vol - entry['entry_iv']) * 100
            vega_pnl = entry['entry_greeks'].vega * iv_change * qty
            
            # Unexplained
            explained = delta_pnl + gamma_pnl + theta_pnl + vega_pnl
            unexplained = total_pnl - explained
            
            attribution = {
                'total_pnl': total_pnl,
                'delta_pnl': delta_pnl,
                'gamma_pnl': gamma_pnl,
                'theta_pnl': theta_pnl,
                'vega_pnl': vega_pnl,
                'unexplained': unexplained,
                'underlying_move': underlying_move,
                'iv_change': iv_change,
                'days_held': days_held
            }
            
            self.pnl_history.append({
                'symbol': symbol,
                'timestamp': datetime.now(),
                **attribution
            })
            
            return attribution


class ExpirationManager:
    """
    Manages options expiration
    """
    
    def __init__(self, warning_days: int = 3):
        self.warning_days = warning_days
        
        # Positions
        self.positions: Dict[str, OptionContract] = {}
        
        # Expiration schedule
        self.expiration_schedule: List[Dict] = []
        
        # Callbacks
        self.on_expiration_warning: List[Callable] = []
        self.on_expiration: List[Callable] = []
        
        self._lock = threading.RLock()
        
        logger.info("ExpirationManager initialized")
    
    def add_position(self, option: OptionContract):
        """Add an options position"""
        with self._lock:
            self.positions[option.symbol] = option
            self._update_schedule()
    
    def remove_position(self, symbol: str):
        """Remove an options position"""
        with self._lock:
            if symbol in self.positions:
                del self.positions[symbol]
                self._update_schedule()
    
    def _update_schedule(self):
        """Update expiration schedule"""
        schedule = []
        today = date.today()
        
        for symbol, option in self.positions.items():
            days_to_expiry = (option.expiration - today).days
            
            schedule.append({
                'symbol': symbol,
                'underlying': option.underlying,
                'option_type': option.option_type.value,
                'strike': option.strike,
                'expiration': option.expiration,
                'days_to_expiry': days_to_expiry,
                'is_itm': option.is_itm,
                'intrinsic_value': option.intrinsic_value
            })
        
        schedule.sort(key=lambda x: x['days_to_expiry'])
        self.expiration_schedule = schedule
    
    def check_expirations(self) -> Dict[str, List[Dict]]:
        """Check for upcoming expirations"""
        warnings = []
        expiring_today = []
        
        for item in self.expiration_schedule:
            if item['days_to_expiry'] <= 0:
                expiring_today.append(item)
            elif item['days_to_expiry'] <= self.warning_days:
                warnings.append(item)
        
        # Fire callbacks
        for item in warnings:
            for callback in self.on_expiration_warning:
                try:
                    callback(item)
                except Exception as e:
                    logger.error(f"Expiration warning callback error: {e}")
        
        for item in expiring_today:
            for callback in self.on_expiration:
                try:
                    callback(item)
                except Exception as e:
                    logger.error(f"Expiration callback error: {e}")
        
        return {
            'warnings': warnings,
            'expiring_today': expiring_today
        }
    
    def get_schedule(self) -> List[Dict]:
        """Get expiration schedule"""
        return self.expiration_schedule


class OptionsEngine:
    """
    Complete options and derivatives engine
    """
    
    def __init__(self):
        self.bs_model = BlackScholesModel()
        self.greeks_calculator = GreeksCalculator()
        self.iv_calculator = ImpliedVolatilityCalculator()
        self.binomial_model = BinomialTreeModel()
        self.strategy_builder = OptionsStrategyBuilder()
        self.vol_surface = VolatilitySurface()
        self.scanner = OptionsScanner()
        self.roll_manager = FuturesRollManager()
        self.pnl_attribution = OptionsPnLAttribution()
        self.expiration_manager = ExpirationManager()
        
        logger.info("OptionsEngine initialized")
    
    def price_option(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType,
        style: OptionStyle = OptionStyle.EUROPEAN
    ) -> float:
        """Price an option"""
        if style == OptionStyle.EUROPEAN:
            return self.bs_model.price(S, K, T, r, sigma, option_type)
        else:
            return self.binomial_model.price(S, K, T, r, sigma, option_type)
    
    def calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> Greeks:
        """Calculate all Greeks"""
        return self.greeks_calculator.calculate_all(S, K, T, r, sigma, option_type)
    
    def calculate_iv(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType
    ) -> float:
        """Calculate implied volatility"""
        return self.iv_calculator.calculate(market_price, S, K, T, r, option_type)
    
    def create_option_contract(
        self,
        symbol: str,
        underlying: str,
        option_type: OptionType,
        strike: float,
        expiration: date,
        underlying_price: float,
        market_price: float,
        r: float = 0.05
    ) -> OptionContract:
        """Create a fully priced option contract"""
        T = (expiration - date.today()).days / 365.0
        
        # Calculate IV
        iv = self.calculate_iv(market_price, underlying_price, strike, T, r, option_type)
        
        # Calculate Greeks
        greeks = self.calculate_greeks(underlying_price, strike, T, r, iv, option_type)
        
        return OptionContract(
            symbol=symbol,
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            expiration=expiration,
            price=market_price,
            underlying_price=underlying_price,
            greeks=greeks,
            implied_vol=iv
        )


# Singleton instance
_options_engine: Optional[OptionsEngine] = None


def get_options_engine() -> OptionsEngine:
    """Get or create options engine singleton"""
    global _options_engine
    if _options_engine is None:
        _options_engine = OptionsEngine()
    return _options_engine


# Export
__all__ = [
    'OptionsEngine',
    'BlackScholesModel',
    'GreeksCalculator',
    'ImpliedVolatilityCalculator',
    'BinomialTreeModel',
    'OptionsStrategyBuilder',
    'VolatilitySurface',
    'OptionsScanner',
    'FuturesRollManager',
    'OptionsPnLAttribution',
    'ExpirationManager',
    'OptionContract',
    'FuturesContract',
    'Greeks',
    'OptionType',
    'OptionStyle',
    'StrategyType',
    'get_options_engine'
]
