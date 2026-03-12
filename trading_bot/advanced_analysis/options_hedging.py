"""
Options Hedging Execution - Automated Delta Hedging

Implements automated options hedging strategies:
- Delta hedging automation
- Gamma scalping integration
- Volatility surface trading
- Portfolio Greeks management
- Dynamic hedge adjustment

Features:
- Real-time Greeks calculation
- Automated hedge execution
- Volatility surface analysis
- Risk-neutral portfolio construction
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque
import math

logger = logging.getLogger(__name__)


class OptionType(Enum):
    """Option types"""
    CALL = "call"
    PUT = "put"


class HedgeAction(Enum):
    """Hedging actions"""
    BUY_UNDERLYING = "buy_underlying"
    SELL_UNDERLYING = "sell_underlying"
    BUY_CALL = "buy_call"
    SELL_CALL = "sell_call"
    BUY_PUT = "buy_put"
    SELL_PUT = "sell_put"
    NO_ACTION = "no_action"


class HedgeStrategy(Enum):
    """Hedging strategies"""
    DELTA_NEUTRAL = "delta_neutral"
    DELTA_GAMMA_NEUTRAL = "delta_gamma_neutral"
    VEGA_NEUTRAL = "vega_neutral"
    COLLAR = "collar"
    PROTECTIVE_PUT = "protective_put"
    COVERED_CALL = "covered_call"


@dataclass
class Greeks:
    """Option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    
    def to_dict(self) -> Dict[str, float]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'delta': self.delta,
            'gamma': self.gamma,
            'theta': self.theta,
            'vega': self.vega,
            'rho': self.rho
        }


@dataclass
class OptionPosition:
    """Single option position"""
    symbol: str
    option_type: OptionType
    strike: float
    expiry: datetime
    quantity: int  # Positive for long, negative for short
    premium: float
    underlying_price: float
    implied_vol: float
    greeks: Greeks
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'symbol': self.symbol,
            'option_type': self.option_type.value,
            'strike': self.strike,
            'expiry': self.expiry.isoformat(),
            'quantity': self.quantity,
            'premium': self.premium,
            'underlying_price': self.underlying_price,
            'implied_vol': self.implied_vol,
            'greeks': self.greeks.to_dict()
        }


@dataclass
class HedgeOrder:
    """Hedge order to execute"""
    action: HedgeAction
    symbol: str
    quantity: float
    price: Optional[float]
    reason: str
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'action': self.action.value,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'reason': self.reason,
            'urgency': self.urgency
        }


@dataclass
class PortfolioGreeks:
    """Aggregate portfolio Greeks"""
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    total_rho: float
    delta_dollars: float  # Dollar delta exposure
    gamma_dollars: float  # Dollar gamma exposure
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'total_delta': self.total_delta,
            'total_gamma': self.total_gamma,
            'total_theta': self.total_theta,
            'total_vega': self.total_vega,
            'total_rho': self.total_rho,
            'delta_dollars': self.delta_dollars,
            'gamma_dollars': self.gamma_dollars
        }


@dataclass
class HedgeResult:
    """Result of hedging operation"""
    timestamp: datetime
    strategy: HedgeStrategy
    orders: List[HedgeOrder]
    portfolio_greeks_before: PortfolioGreeks
    portfolio_greeks_after: PortfolioGreeks
    hedge_cost: float
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'strategy': self.strategy.value,
            'orders': [o.to_dict() for o in self.orders],
            'portfolio_greeks_before': self.portfolio_greeks_before.to_dict(),
            'portfolio_greeks_after': self.portfolio_greeks_after.to_dict(),
            'hedge_cost': self.hedge_cost,
            'reasoning': self.reasoning
        }


class BlackScholes:
    """
    Black-Scholes option pricing model
    
    Calculates option prices and Greeks
    """
    
    @staticmethod
    def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d1"""
        try:
            if T <= 0 or sigma <= 0:
                return 0.0
            return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        except Exception as e:
            logger.error(f"Error in d1: {e}")
            raise
    
    @staticmethod
    def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate d2"""
        try:
            if T <= 0 or sigma <= 0:
                return 0.0
            return BlackScholes.d1(S, K, T, r, sigma) - sigma * np.sqrt(T)
        except Exception as e:
            logger.error(f"Error in d2: {e}")
            raise
    
    @staticmethod
    def norm_cdf(x: float) -> float:
        """Standard normal CDF"""
        return 0.5 * (1 + math.erf(x / np.sqrt(2)))
    
    @staticmethod
    def norm_pdf(x: float) -> float:
        """Standard normal PDF"""
        return np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi)
    
    @staticmethod
    def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate call option price"""
        try:
            if T <= 0:
                return max(0, S - K)
        
            d1 = BlackScholes.d1(S, K, T, r, sigma)
            d2 = BlackScholes.d2(S, K, T, r, sigma)
        
            return S * BlackScholes.norm_cdf(d1) - K * np.exp(-r * T) * BlackScholes.norm_cdf(d2)
        except Exception as e:
            logger.error(f"Error in call_price: {e}")
            raise
    
    @staticmethod
    def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Calculate put option price"""
        try:
            if T <= 0:
                return max(0, K - S)
        
            d1 = BlackScholes.d1(S, K, T, r, sigma)
            d2 = BlackScholes.d2(S, K, T, r, sigma)
        
            return K * np.exp(-r * T) * BlackScholes.norm_cdf(-d2) - S * BlackScholes.norm_cdf(-d1)
        except Exception as e:
            logger.error(f"Error in put_price: {e}")
            raise
    
    @staticmethod
    def calculate_greeks(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: OptionType
    ) -> Greeks:
        """Calculate all Greeks for an option"""
        try:
            if T <= 0:
                # At expiry
                if option_type == OptionType.CALL:
                    delta = 1.0 if S > K else 0.0
                else:
                    delta = -1.0 if S < K else 0.0
                return Greeks(delta=delta, gamma=0, theta=0, vega=0, rho=0)
        
            d1 = BlackScholes.d1(S, K, T, r, sigma)
            d2 = BlackScholes.d2(S, K, T, r, sigma)
        
            # Delta
            if option_type == OptionType.CALL:
                delta = BlackScholes.norm_cdf(d1)
            else:
                delta = BlackScholes.norm_cdf(d1) - 1
        
            # Gamma (same for calls and puts)
            gamma = BlackScholes.norm_pdf(d1) / (S * sigma * np.sqrt(T))
        
            # Theta
            term1 = -S * BlackScholes.norm_pdf(d1) * sigma / (2 * np.sqrt(T))
            if option_type == OptionType.CALL:
                term2 = -r * K * np.exp(-r * T) * BlackScholes.norm_cdf(d2)
            else:
                term2 = r * K * np.exp(-r * T) * BlackScholes.norm_cdf(-d2)
            theta = (term1 + term2) / 365  # Daily theta
        
            # Vega (same for calls and puts)
            vega = S * np.sqrt(T) * BlackScholes.norm_pdf(d1) / 100  # Per 1% vol change
        
            # Rho
            if option_type == OptionType.CALL:
                rho = K * T * np.exp(-r * T) * BlackScholes.norm_cdf(d2) / 100
            else:
                rho = -K * T * np.exp(-r * T) * BlackScholes.norm_cdf(-d2) / 100
        
            return Greeks(
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=rho
            )
        except Exception as e:
            logger.error(f"Error in calculate_greeks: {e}")
            raise
    
    @staticmethod
    def implied_volatility(
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: OptionType,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> float:
        """Calculate implied volatility using Newton-Raphson"""
        try:
            sigma = 0.2  # Initial guess
        
            for _ in range(max_iterations):
                if option_type == OptionType.CALL:
                    price = BlackScholes.call_price(S, K, T, r, sigma)
                else:
                    price = BlackScholes.put_price(S, K, T, r, sigma)
            
                diff = price - market_price
            
                if abs(diff) < tolerance:
                    return sigma
            
                # Vega for Newton-Raphson
                d1 = BlackScholes.d1(S, K, T, r, sigma)
                vega = S * np.sqrt(T) * BlackScholes.norm_pdf(d1)
            
                if vega < 1e-10:
                    break
            
                sigma = sigma - diff / vega
                sigma = max(0.01, min(5.0, sigma))  # Bound sigma
        
            return sigma
        except Exception as e:
            logger.error(f"Error in implied_volatility: {e}")
            raise


class OptionsHedgingEngine:
    """
    Options Hedging Engine
    
    Provides automated delta hedging and portfolio Greeks management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Risk-free rate
            self.risk_free_rate = self.config.get('risk_free_rate', 0.05)
        
            # Hedging thresholds
            self.delta_threshold = self.config.get('delta_threshold', 0.1)  # Hedge when delta exceeds
            self.gamma_threshold = self.config.get('gamma_threshold', 0.05)
            self.rebalance_interval = self.config.get('rebalance_interval', 3600)  # Seconds
        
            # Positions
            self.option_positions: List[OptionPosition] = []
            self.underlying_position: float = 0  # Shares of underlying
        
            # History
            self.hedge_history: deque = deque(maxlen=1000)
            self.last_rebalance: Optional[datetime] = None
        
            # Black-Scholes calculator
            self.bs = BlackScholes()
        
            logger.info("OptionsHedgingEngine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_option_position(
        self,
        symbol: str,
        option_type: OptionType,
        strike: float,
        expiry: datetime,
        quantity: int,
        premium: float,
        underlying_price: float,
        implied_vol: Optional[float] = None
    ) -> OptionPosition:
        """Add option position to portfolio"""
        # Calculate time to expiry
        try:
            T = max(0, (expiry - datetime.now()).days / 365)
        
            # Calculate or use implied vol
            if implied_vol is None:
                implied_vol = self.bs.implied_volatility(
                    premium, underlying_price, strike, T,
                    self.risk_free_rate, option_type
                )
        
            # Calculate Greeks
            greeks = self.bs.calculate_greeks(
                underlying_price, strike, T,
                self.risk_free_rate, implied_vol, option_type
            )
        
            position = OptionPosition(
                symbol=symbol,
                option_type=option_type,
                strike=strike,
                expiry=expiry,
                quantity=quantity,
                premium=premium,
                underlying_price=underlying_price,
                implied_vol=implied_vol,
                greeks=greeks
            )
        
            self.option_positions.append(position)
        
            logger.info(
                f"Added {option_type.value} position: {symbol} "
                f"Strike={strike}, Qty={quantity}, Delta={greeks.delta:.3f}"
            )
        
            return position
        except Exception as e:
            logger.error(f"Error in add_option_position: {e}")
            raise
    
    def update_underlying_position(self, quantity: float):
        """Update underlying position"""
        try:
            self.underlying_position = quantity
        except Exception as e:
            logger.error(f"Error in update_underlying_position: {e}")
            raise
    
    def calculate_portfolio_greeks(
        self,
        underlying_price: float
    ) -> PortfolioGreeks:
        """Calculate aggregate portfolio Greeks"""
        try:
            total_delta = self.underlying_position  # Underlying has delta of 1
            total_gamma = 0.0
            total_theta = 0.0
            total_vega = 0.0
            total_rho = 0.0
        
            for pos in self.option_positions:
                # Update Greeks with current price
                T = max(0, (pos.expiry - datetime.now()).days / 365)
                greeks = self.bs.calculate_greeks(
                    underlying_price, pos.strike, T,
                    self.risk_free_rate, pos.implied_vol, pos.option_type
                )
            
                # Aggregate (multiply by quantity and contract multiplier)
                multiplier = pos.quantity * 100  # Standard option = 100 shares
            
                total_delta += greeks.delta * multiplier
                total_gamma += greeks.gamma * multiplier
                total_theta += greeks.theta * multiplier
                total_vega += greeks.vega * multiplier
                total_rho += greeks.rho * multiplier
        
            # Dollar Greeks
            delta_dollars = total_delta * underlying_price
            gamma_dollars = total_gamma * underlying_price ** 2 / 100
        
            return PortfolioGreeks(
                total_delta=total_delta,
                total_gamma=total_gamma,
                total_theta=total_theta,
                total_vega=total_vega,
                total_rho=total_rho,
                delta_dollars=delta_dollars,
                gamma_dollars=gamma_dollars
            )
        except Exception as e:
            logger.error(f"Error in calculate_portfolio_greeks: {e}")
            raise
    
    def calculate_hedge(
        self,
        underlying_price: float,
        strategy: HedgeStrategy = HedgeStrategy.DELTA_NEUTRAL
    ) -> HedgeResult:
        """
        Calculate required hedge
        
        Returns hedge orders needed to achieve target exposure
        """
        # Current portfolio Greeks
        try:
            greeks_before = self.calculate_portfolio_greeks(underlying_price)
        
            orders = []
            reasoning_parts = []
        
            if strategy == HedgeStrategy.DELTA_NEUTRAL:
                # Simple delta hedging
                if abs(greeks_before.total_delta) > self.delta_threshold:
                    # Need to hedge delta
                    hedge_quantity = -greeks_before.total_delta
                
                    if hedge_quantity > 0:
                        action = HedgeAction.BUY_UNDERLYING
                    else:
                        action = HedgeAction.SELL_UNDERLYING
                
                    urgency = "HIGH" if abs(greeks_before.total_delta) > self.delta_threshold * 2 else "MEDIUM"
                
                    orders.append(HedgeOrder(
                        action=action,
                        symbol="UNDERLYING",
                        quantity=abs(hedge_quantity),
                        price=underlying_price,
                        reason=f"Delta hedge: current delta={greeks_before.total_delta:.2f}",
                        urgency=urgency
                    ))
                
                    reasoning_parts.append(
                        f"Delta hedging: {action.value} {abs(hedge_quantity):.0f} shares"
                    )
        
            elif strategy == HedgeStrategy.DELTA_GAMMA_NEUTRAL:
                # Delta-gamma hedging requires options
                if abs(greeks_before.total_gamma) > self.gamma_threshold:
                    # Need to hedge gamma first (requires options)
                    # Simplified: suggest buying/selling ATM options
                
                    if greeks_before.total_gamma > 0:
                        # Long gamma, sell options to reduce
                        action = HedgeAction.SELL_CALL
                    else:
                        # Short gamma, buy options to increase
                        action = HedgeAction.BUY_CALL
                
                    # Approximate quantity needed
                    atm_gamma = 0.05  # Approximate ATM gamma
                    gamma_hedge_qty = abs(greeks_before.total_gamma / atm_gamma)
                
                    orders.append(HedgeOrder(
                        action=action,
                        symbol="ATM_OPTION",
                        quantity=gamma_hedge_qty,
                        price=None,
                        reason=f"Gamma hedge: current gamma={greeks_before.total_gamma:.4f}",
                        urgency="MEDIUM"
                    ))
                
                    reasoning_parts.append(
                        f"Gamma hedging: {action.value} ~{gamma_hedge_qty:.0f} contracts"
                    )
            
                # Then delta hedge
                if abs(greeks_before.total_delta) > self.delta_threshold:
                    hedge_quantity = -greeks_before.total_delta
                    action = HedgeAction.BUY_UNDERLYING if hedge_quantity > 0 else HedgeAction.SELL_UNDERLYING
                
                    orders.append(HedgeOrder(
                        action=action,
                        symbol="UNDERLYING",
                        quantity=abs(hedge_quantity),
                        price=underlying_price,
                        reason=f"Delta hedge after gamma adjustment",
                        urgency="MEDIUM"
                    ))
        
            elif strategy == HedgeStrategy.PROTECTIVE_PUT:
                # Buy puts to protect long position
                if self.underlying_position > 0:
                    # Calculate puts needed
                    puts_needed = self.underlying_position / 100  # 1 put per 100 shares
                
                    orders.append(HedgeOrder(
                        action=HedgeAction.BUY_PUT,
                        symbol="OTM_PUT",
                        quantity=puts_needed,
                        price=None,
                        reason=f"Protective put for {self.underlying_position} shares",
                        urgency="LOW"
                    ))
                
                    reasoning_parts.append(
                        f"Protective put: buy {puts_needed:.0f} puts"
                    )
        
            elif strategy == HedgeStrategy.COVERED_CALL:
                # Sell calls against long position
                if self.underlying_position > 0:
                    calls_to_sell = self.underlying_position / 100
                
                    orders.append(HedgeOrder(
                        action=HedgeAction.SELL_CALL,
                        symbol="OTM_CALL",
                        quantity=calls_to_sell,
                        price=None,
                        reason=f"Covered call for {self.underlying_position} shares",
                        urgency="LOW"
                    ))
                
                    reasoning_parts.append(
                        f"Covered call: sell {calls_to_sell:.0f} calls"
                    )
        
            # Calculate Greeks after hedge (simulated)
            greeks_after = PortfolioGreeks(
                total_delta=0 if strategy == HedgeStrategy.DELTA_NEUTRAL else greeks_before.total_delta,
                total_gamma=greeks_before.total_gamma,
                total_theta=greeks_before.total_theta,
                total_vega=greeks_before.total_vega,
                total_rho=greeks_before.total_rho,
                delta_dollars=0 if strategy == HedgeStrategy.DELTA_NEUTRAL else greeks_before.delta_dollars,
                gamma_dollars=greeks_before.gamma_dollars
            )
        
            # Estimate hedge cost
            hedge_cost = sum(
                o.quantity * (o.price or underlying_price * 0.01)
                for o in orders
            )
        
            reasoning = ". ".join(reasoning_parts) if reasoning_parts else "No hedge required"
        
            result = HedgeResult(
                timestamp=datetime.now(),
                strategy=strategy,
                orders=orders,
                portfolio_greeks_before=greeks_before,
                portfolio_greeks_after=greeks_after,
                hedge_cost=hedge_cost,
                reasoning=reasoning
            )
        
            self.hedge_history.append(result)
            self.last_rebalance = datetime.now()
        
            return result
        except Exception as e:
            logger.error(f"Error in calculate_hedge: {e}")
            raise
    
    def should_rebalance(self, underlying_price: float) -> Tuple[bool, str]:
        """Check if rebalancing is needed"""
        # Time-based check
        try:
            if self.last_rebalance:
                time_since = (datetime.now() - self.last_rebalance).seconds
                if time_since < self.rebalance_interval:
                    return False, f"Last rebalance {time_since}s ago"
        
            # Delta-based check
            greeks = self.calculate_portfolio_greeks(underlying_price)
        
            if abs(greeks.total_delta) > self.delta_threshold:
                return True, f"Delta threshold exceeded: {greeks.total_delta:.2f}"
        
            if abs(greeks.total_gamma) > self.gamma_threshold:
                return True, f"Gamma threshold exceeded: {greeks.total_gamma:.4f}"
        
            return False, "Portfolio within thresholds"
        except Exception as e:
            logger.error(f"Error in should_rebalance: {e}")
            raise
    
    def get_portfolio_summary(self, underlying_price: float) -> Dict[str, Any]:
        """Get portfolio summary"""
        try:
            greeks = self.calculate_portfolio_greeks(underlying_price)
        
            return {
                'underlying_position': self.underlying_position,
                'option_positions': len(self.option_positions),
                'portfolio_greeks': greeks.to_dict(),
                'positions': [p.to_dict() for p in self.option_positions],
                'last_rebalance': self.last_rebalance.isoformat() if self.last_rebalance else None,
                'hedge_count': len(self.hedge_history)
            }
        except Exception as e:
            logger.error(f"Error in get_portfolio_summary: {e}")
            raise
    
    def gamma_scalp_opportunity(
        self,
        underlying_price: float,
        price_move: float
    ) -> Optional[Dict[str, Any]]:
        """
        Identify gamma scalping opportunity
        
        When long gamma, profit from price moves by delta hedging
        """
        try:
            greeks = self.calculate_portfolio_greeks(underlying_price)
        
            if greeks.total_gamma <= 0:
                return None  # Need long gamma for scalping
        
            # Calculate P&L from price move
            delta_pnl = greeks.total_delta * price_move
            gamma_pnl = 0.5 * greeks.total_gamma * price_move ** 2
            theta_cost = greeks.total_theta  # Daily cost
        
            net_pnl = delta_pnl + gamma_pnl - abs(theta_cost)
        
            if net_pnl > 0:
                return {
                    'opportunity': True,
                    'price_move': price_move,
                    'delta_pnl': delta_pnl,
                    'gamma_pnl': gamma_pnl,
                    'theta_cost': theta_cost,
                    'net_pnl': net_pnl,
                    'action': 'HEDGE_DELTA' if abs(greeks.total_delta) > self.delta_threshold else 'HOLD'
                }
        
            return None
        except Exception as e:
            logger.error(f"Error in gamma_scalp_opportunity: {e}")
            raise


# Factory function
def create_options_hedging_engine(config: Optional[Dict[str, Any]] = None) -> OptionsHedgingEngine:
    """Create options hedging engine"""
    return OptionsHedgingEngine(config)
