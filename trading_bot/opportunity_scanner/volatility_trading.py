import asyncio
"""
Volatility Trading Module
Captures opportunities from volatility dislocations and regime changes
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
try:
    from scipy import stats
except ImportError:
    scipy = None
import numpy
import pandas

logger = logging.getLogger(__name__)

class VolatilityStrategy(Enum):
    """Types of volatility strategies"""
    ARBITRAGE = "arbitrage"
    DISPERSION = "dispersion"
    GAMMA_SCALPING = "gamma_scalping"
    VOL_OF_VOL = "vol_of_vol"
    SKEW_TRADE = "skew_trade"
    TERM_STRUCTURE = "term_structure"

@dataclass
class VolatilityOpportunity:
    """Represents a volatility trading opportunity"""
    opportunity_id: str
    symbol: str
    strategy_type: VolatilityStrategy
    current_vol: float
    fair_vol: float
    vol_spread: float
    expected_profit: float
    holding_period: float
    confidence: float
    greeks: Dict[str, float]
    hedge_ratio: Dict[str, float]
    entry_levels: Dict[str, float]
    metadata: Dict[str, Any]

class VolatilityArbitrage:
    """
    Trades volatility mispricings between implied and realized vol
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_vol_spread = self.config.get('min_vol_spread', 0.02)
        self.lookback_period = self.config.get('lookback_period', 30)
        
        # Volatility models
        self.garch_models = {}
        self.heston_models = {}
        self.vol_surfaces = {}
        
    async def find_vol_arbitrage(self, market_data: Dict) -> List[VolatilityOpportunity]:
        """
        Find volatility arbitrage opportunities
        """
        opportunities = []
        
        for symbol, data in market_data.items():
            if 'options' not in data:
                continue
            
            # Calculate volatility metrics
            vol_analysis = self._analyze_volatility(symbol, data)
            
            # Check for arbitrage opportunity
            if abs(vol_analysis['vol_spread']) > self.min_vol_spread:
                opportunity = self._create_vol_opportunity(symbol, vol_analysis, data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_volatility(self, symbol: str, data: Dict) -> Dict:
        """Comprehensive volatility analysis"""
        # Calculate realized volatility
        realized_vol = self._calculate_realized_vol(data.get('price_history', []))
        
        # Get implied volatility
        implied_vol = self._calculate_implied_vol(data.get('options', {}))
        
        # GARCH forecast
        garch_vol = self._forecast_garch_vol(symbol, data)
        
        # Calculate fair value
        fair_vol = self._calculate_fair_vol(realized_vol, implied_vol, garch_vol)
        
        # Volatility spread
        vol_spread = implied_vol - fair_vol
        
        # Term structure analysis
        term_structure = self._analyze_term_structure(data.get('options', {}))
        
        # Skew analysis
        skew = self._analyze_skew(data.get('options', {}))
        
        return {
            'realized_vol': realized_vol,
            'implied_vol': implied_vol,
            'garch_vol': garch_vol,
            'fair_vol': fair_vol,
            'vol_spread': vol_spread,
            'term_structure': term_structure,
            'skew': skew,
            'vol_regime': self._identify_vol_regime(realized_vol)
        }
    
    def _calculate_realized_vol(self, price_history: List[float]) -> float:
        """Calculate realized volatility"""
        if len(price_history) < 2:
            return 0.2  # Default
        
        # Calculate returns
        returns = np.diff(np.log(price_history))
        
        # Different volatility estimators
        close_to_close = np.std(returns) * np.sqrt(252)
        
        # Parkinson (high-low)
        # Yang-Zhang
        # Rogers-Satchell
        
        # Use close-to-close for simplicity
        return close_to_close
    
    def _calculate_implied_vol(self, options: Dict) -> float:
        """Calculate average implied volatility"""
        if not options:
            return 0.2
        
        # ATM implied vol
        atm_calls = options.get('atm_calls', [])
        atm_puts = options.get('atm_puts', [])
        
        ivs = []
        for option in atm_calls + atm_puts:
            if 'implied_vol' in option:
                ivs.append(option['implied_vol'])
        
        if ivs:
            return np.mean(ivs)
        
        return 0.2
    
    def _forecast_garch_vol(self, symbol: str, data: Dict) -> float:
        """Forecast volatility using GARCH model"""
        # Simplified GARCH(1,1) forecast
        # In production, use arch package
        
        if 'price_history' not in data:
            return 0.2
        
        returns = np.diff(np.log(data['price_history']))
        
        if len(returns) < 100:
            return np.std(returns) * np.sqrt(252)
        
        # GARCH parameters (would be calibrated)
        omega = 0.000001
        alpha = 0.1
        beta = 0.85
        
        # Initialize
        variance = np.var(returns)
        
        # One-step ahead forecast
        variance_forecast = omega + alpha * returns[-1]**2 + beta * variance
        
        return np.sqrt(variance_forecast * 252)
    
    def _calculate_fair_vol(self, realized: float, implied: float, garch: float) -> float:
        """Calculate fair volatility value"""
        # Weighted average of different estimates
        weights = [0.3, 0.4, 0.3]  # realized, implied, garch
        
        return weights[0] * realized + weights[1] * implied + weights[2] * garch
    
    def _analyze_term_structure(self, options: Dict) -> Dict:
        """Analyze volatility term structure"""
        if not options or 'term_structure' not in options:
            return {}
        
        term_data = options['term_structure']
        
        # Calculate slope
        if len(term_data) >= 2:
            short_term = term_data[0]['vol']
            long_term = term_data[-1]['vol']
            slope = (long_term - short_term) / short_term
            
            # Identify structure type
            if slope > 0.1:
                structure = 'CONTANGO'
            elif slope < -0.1:
                structure = 'BACKWARDATION'
            else:
                structure = 'FLAT'
            
            return {
                'slope': slope,
                'structure': structure,
                'short_term_vol': short_term,
                'long_term_vol': long_term
            }
        
        return {}
    
    def _analyze_skew(self, options: Dict) -> Dict:
        """Analyze volatility skew"""
        if not options or 'skew' not in options:
            return {}
        
        skew_data = options['skew']
        
        # 25-delta risk reversal
        if 'rr_25d' in skew_data:
            risk_reversal = skew_data['rr_25d']
            
            # Interpret skew
            if risk_reversal > 0.02:
                skew_type = 'CALL_SKEW'
            elif risk_reversal < -0.02:
                skew_type = 'PUT_SKEW'
            else:
                skew_type = 'NEUTRAL'
            
            return {
                'risk_reversal': risk_reversal,
                'skew_type': skew_type,
                'butterfly_25d': skew_data.get('butterfly_25d', 0)
            }
        
        return {}
    
    def _identify_vol_regime(self, current_vol: float) -> str:
        """Identify volatility regime"""
        if current_vol < 0.10:
            return 'LOW_VOL'
        elif current_vol < 0.20:
            return 'NORMAL_VOL'
        elif current_vol < 0.40:
            return 'HIGH_VOL'
        else:
            return 'EXTREME_VOL'
    
    def _create_vol_opportunity(self, symbol: str, vol_analysis: Dict, 
                               market_data: Dict) -> VolatilityOpportunity:
        """Create volatility trading opportunity"""
        vol_spread = vol_analysis['vol_spread']
        
        # Determine strategy
        if abs(vol_spread) > 0.05:
            strategy = VolatilityStrategy.ARBITRAGE
        elif vol_analysis['skew'].get('risk_reversal', 0) > 0.03:
            strategy = VolatilityStrategy.SKEW_TRADE
        else:
            strategy = VolatilityStrategy.GAMMA_SCALPING
        
        # Calculate Greeks for hedging
        greeks = self._calculate_greeks(market_data)
        
        # Calculate hedge ratios
        hedge_ratio = self._calculate_hedge_ratio(greeks)
        
        return VolatilityOpportunity(
            opportunity_id=f"VOL_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            strategy_type=strategy,
            current_vol=vol_analysis['implied_vol'],
            fair_vol=vol_analysis['fair_vol'],
            vol_spread=vol_spread,
            expected_profit=abs(vol_spread) * 1000,  # Simplified
            holding_period=30.0,  # Days
            confidence=0.7,
            greeks=greeks,
            hedge_ratio=hedge_ratio,
            entry_levels={
                'spot': market_data['price'],
                'vol_entry': vol_analysis['implied_vol']
            },
            metadata=vol_analysis
        )
    
    def _calculate_greeks(self, market_data: Dict) -> Dict[str, float]:
        """Calculate option Greeks"""
        # Simplified Greeks calculation
        # In production, use QuantLib or similar
        
        return {
            'delta': 0.5,
            'gamma': 0.02,
            'vega': 20.0,
            'theta': -5.0,
            'rho': 10.0
        }
    
    def _calculate_hedge_ratio(self, greeks: Dict[str, float]) -> Dict[str, float]:
        """Calculate hedge ratios for delta-neutral position"""
        return {
            'stock_hedge': -greeks['delta'],
            'vol_hedge': -greeks['vega'] / 100,
            'gamma_hedge': -greeks['gamma'] / 0.01
        }


class GammaScalping:
    """
    Gamma scalping strategy for volatility capture
    """
    
    def __init__(self):
        self.rebalance_threshold = 0.01
        self.gamma_target = 0.02
        
    def calculate_gamma_pnl(self, spot_move: float, gamma: float, 
                           position_size: float) -> float:
        """Calculate P&L from gamma scalping"""
        # Gamma P&L = 0.5 * Gamma * (Spot Move)^2 * Position
        return 0.5 * gamma * (spot_move ** 2) * position_size
    
    def optimal_rebalance_frequency(self, volatility: float, 
                                   transaction_cost: float) -> float:
        """Calculate optimal rebalancing frequency"""
        # Merton's optimal rebalancing
        # Frequency increases with vol, decreases with cost
        
        optimal_freq = volatility / (2 * np.sqrt(transaction_cost))
        
        return min(100, max(1, optimal_freq))  # Cap between 1 and 100 times per day
    
    def generate_scalping_signals(self, market_data: Dict) -> List[Dict]:
        """Generate gamma scalping signals"""
        signals = []
        
        for symbol, data in market_data.items():
            if 'options_position' not in data:
                continue
            
            position = data['options_position']
            
            # Check if rebalancing needed
            delta_drift = position.get('delta_drift', 0)
            
            if abs(delta_drift) > self.rebalance_threshold:
                signal = {
                    'symbol': symbol,
                    'action': 'REBALANCE',
                    'hedge_size': -delta_drift * position['size'],
                    'expected_pnl': self.calculate_gamma_pnl(
                        data.get('expected_move', 0.01),
                        position.get('gamma', 0),
                        position['size']
                    )
                }
                signals.append(signal)
        
        return signals


class VolatilitySkewTrader:
    """
    Trades volatility skew mispricings
    """
    
    def __init__(self):
        self.skew_models = {}
        self.min_skew_deviation = 0.02
        
    def find_skew_opportunities(self, options_data: Dict) -> List[VolatilityOpportunity]:
        """Find skew trading opportunities"""
        opportunities = []
        
        for symbol, data in options_data.items():
            # Analyze skew
            skew_analysis = self._analyze_skew_surface(data)
            
            # Check for mispricings
            if skew_analysis['mispriced']:
                opportunity = self._create_skew_trade(symbol, skew_analysis)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _analyze_skew_surface(self, data: Dict) -> Dict:
        """Analyze volatility skew surface"""
        if 'vol_surface' not in data:
            return {'mispriced': False}
        
        surface = data['vol_surface']
        
        # Extract skew metrics
        atm_vol = surface.get('atm', 0.20)
        put_25d = surface.get('25d_put', 0.22)
        call_25d = surface.get('25d_call', 0.18)
        
        # Risk reversal
        risk_reversal = call_25d - put_25d
        
        # Butterfly
        butterfly = (put_25d + call_25d) / 2 - atm_vol
        
        # Check historical norms
        historical_rr = data.get('historical_rr', 0)
        rr_deviation = risk_reversal - historical_rr
        
        return {
            'mispriced': abs(rr_deviation) > self.min_skew_deviation,
            'risk_reversal': risk_reversal,
            'butterfly': butterfly,
            'deviation': rr_deviation,
            'trade_direction': 'SELL_RR' if rr_deviation > 0 else 'BUY_RR'
        }
    
    def _create_skew_trade(self, symbol: str, skew_analysis: Dict) -> VolatilityOpportunity:
        """Create skew trading opportunity"""
        return VolatilityOpportunity(
            opportunity_id=f"SKEW_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            strategy_type=VolatilityStrategy.SKEW_TRADE,
            current_vol=0,  # Not applicable
            fair_vol=0,
            vol_spread=skew_analysis['deviation'],
            expected_profit=abs(skew_analysis['deviation']) * 500,
            holding_period=20.0,
            confidence=0.65,
            greeks={},  # Would calculate for actual position
            hedge_ratio={},
            entry_levels={
                'risk_reversal': skew_analysis['risk_reversal'],
                'butterfly': skew_analysis['butterfly']
            },
            metadata=skew_analysis
        )


class StrangleHarvester:
    """
    Harvests volatility premium through strangle selling
    """
    
    def __init__(self):
        self.min_vol_premium = 0.02
        self.max_loss_multiplier = 3.0
        
    def identify_strangle_opportunities(self, market_data: Dict) -> List[VolatilityOpportunity]:
        """Identify opportunities to harvest volatility premium"""
        opportunities = []
        
        for symbol, data in market_data.items():
            if 'options' not in data:
                continue
            
            # Check if IV > HV (volatility premium exists)
            vol_premium = self._calculate_vol_premium(data)
            
            if vol_premium > self.min_vol_premium:
                opportunity = self._create_strangle_opportunity(symbol, vol_premium, data)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_vol_premium(self, data: Dict) -> float:
        """Calculate volatility risk premium"""
        implied_vol = data.get('implied_vol', 0.20)
        realized_vol = data.get('realized_vol', 0.18)
        
        return implied_vol - realized_vol
    
    def _create_strangle_opportunity(self, symbol: str, vol_premium: float, 
                                    data: Dict) -> VolatilityOpportunity:
        """Create strangle selling opportunity"""
        current_price = data['price']
        
        # Calculate strangle strikes (e.g., 10% OTM)
        put_strike = current_price * 0.9
        call_strike = current_price * 1.1
        
        # Expected profit (premium collected)
        expected_premium = vol_premium * current_price * 0.1
        
        return VolatilityOpportunity(
            opportunity_id=f"STRANGLE_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            strategy_type=VolatilityStrategy.ARBITRAGE,
            current_vol=data.get('implied_vol', 0.20),
            fair_vol=data.get('realized_vol', 0.18),
            vol_spread=vol_premium,
            expected_profit=expected_premium,
            holding_period=30.0,
            confidence=0.6,
            greeks={
                'delta': 0,  # Delta-neutral at inception
                'gamma': -0.02,
                'vega': -50,
                'theta': 10
            },
            hedge_ratio={'delta_hedge': 0},
            entry_levels={
                'put_strike': put_strike,
                'call_strike': call_strike,
                'spot': current_price
            },
            metadata={
                'vol_premium': vol_premium,
                'max_loss': expected_premium * self.max_loss_multiplier
            }
        )
