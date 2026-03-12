"""
Regime-Adaptive Trading Strategy Module
Dynamically adjusts trading parameters based on detected market regimes
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
import asyncio
from dataclasses import dataclass
import json

from trading_bot.analysis.market_regime_detector import MarketRegime, MarketRegimeDetector
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

@dataclass
class StrategyParameters:
    """Strategy parameters that adapt to market regimes"""
    # Position sizing
    position_size_multiplier: float = 1.0
    max_position_size: float = 1.0
    
    # Entry parameters
    entry_threshold: float = 0.7
    entry_confirmation_required: bool = True
    
    # Exit parameters
    stop_loss_multiplier: float = 1.0
    take_profit_multiplier: float = 1.0
    trailing_stop_enabled: bool = False
    trailing_stop_distance: float = 0.02
    
    # Time parameters
    holding_period_multiplier: float = 1.0
    
    # Risk parameters
    risk_per_trade: float = 0.01
    max_correlation_allowed: float = 0.7
    
    # Execution parameters
    execution_aggression: float = 0.5  # 0=passive, 1=aggressive
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'position_size_multiplier': self.position_size_multiplier,
            'max_position_size': self.max_position_size,
            'entry_threshold': self.entry_threshold,
            'entry_confirmation_required': self.entry_confirmation_required,
            'stop_loss_multiplier': self.stop_loss_multiplier,
            'take_profit_multiplier': self.take_profit_multiplier,
            'trailing_stop_enabled': self.trailing_stop_enabled,
            'trailing_stop_distance': self.trailing_stop_distance,
            'holding_period_multiplier': self.holding_period_multiplier,
            'risk_per_trade': self.risk_per_trade,
            'max_correlation_allowed': self.max_correlation_allowed,
            'execution_aggression': self.execution_aggression
        }


class RegimeAdaptiveStrategy:
    """
    Adapts trading strategy parameters based on detected market regimes
    
    Features:
    - Dynamic parameter adjustment
    - Regime-specific strategy selection
    - Performance tracking by regime
    - Automatic strategy optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize regime detector
        self.regime_detector = MarketRegimeDetector(self.config.get('regime_detector', {}))
        
        # Base strategy parameters
        self.base_parameters = StrategyParameters(
            position_size_multiplier=1.0,
            max_position_size=1.0,
            entry_threshold=0.7,
            entry_confirmation_required=True,
            stop_loss_multiplier=1.0,
            take_profit_multiplier=1.0,
            trailing_stop_enabled=False,
            trailing_stop_distance=0.02,
            holding_period_multiplier=1.0,
            risk_per_trade=0.01,
            max_correlation_allowed=0.7,
            execution_aggression=0.5
        )
        
        # Regime-specific parameter adjustments
        self.regime_parameters = {
            # Trending Bull
            0: StrategyParameters(
                position_size_multiplier=1.2,
                max_position_size=1.5,
                entry_threshold=0.6,
                entry_confirmation_required=False,
                stop_loss_multiplier=1.0,
                take_profit_multiplier=1.5,
                trailing_stop_enabled=True,
                trailing_stop_distance=0.03,
                holding_period_multiplier=1.5,
                risk_per_trade=0.015,
                max_correlation_allowed=0.8,
                execution_aggression=0.7
            ),
            # Trending Bear
            1: StrategyParameters(
                position_size_multiplier=1.0,
                max_position_size=1.2,
                entry_threshold=0.7,
                entry_confirmation_required=True,
                stop_loss_multiplier=0.8,
                take_profit_multiplier=1.2,
                trailing_stop_enabled=True,
                trailing_stop_distance=0.02,
                holding_period_multiplier=0.8,
                risk_per_trade=0.012,
                max_correlation_allowed=0.7,
                execution_aggression=0.6
            ),
            # Range-Bound Low Vol
            2: StrategyParameters(
                position_size_multiplier=0.8,
                max_position_size=1.0,
                entry_threshold=0.8,
                entry_confirmation_required=True,
                stop_loss_multiplier=1.2,
                take_profit_multiplier=0.8,
                trailing_stop_enabled=False,
                trailing_stop_distance=0.01,
                holding_period_multiplier=0.6,
                risk_per_trade=0.008,
                max_correlation_allowed=0.6,
                execution_aggression=0.3
            ),
            # Volatile Sideways
            3: StrategyParameters(
                position_size_multiplier=0.6,
                max_position_size=0.8,
                entry_threshold=0.85,
                entry_confirmation_required=True,
                stop_loss_multiplier=1.5,
                take_profit_multiplier=1.0,
                trailing_stop_enabled=False,
                trailing_stop_distance=0.04,
                holding_period_multiplier=0.4,
                risk_per_trade=0.006,
                max_correlation_allowed=0.5,
                execution_aggression=0.4
            ),
            # Crisis/Panic
            4: StrategyParameters(
                position_size_multiplier=0.3,
                max_position_size=0.5,
                entry_threshold=0.95,
                entry_confirmation_required=True,
                stop_loss_multiplier=2.0,
                take_profit_multiplier=1.5,
                trailing_stop_enabled=True,
                trailing_stop_distance=0.05,
                holding_period_multiplier=0.2,
                risk_per_trade=0.004,
                max_correlation_allowed=0.4,
                execution_aggression=0.2
            )
        }
        
        # Current parameters
        self.current_parameters = self.base_parameters
        
        # Current regime
        self.current_regime = None
        
        # Performance tracking
        self.performance_by_regime = {}
        
        logger.info("Regime-adaptive strategy initialized")
    
    async def update_regime(self, market_data: Dict[str, pd.DataFrame]) -> MarketRegime:
        """
        Update current market regime
        
        Args:
            market_data: Dictionary of market data frames by symbol
            
        Returns:
            Current market regime
        """
        # Detect regime
        regime = await self.regime_detector.detect_regime(market_data)
        
        # Update current regime
        self.current_regime = regime
        
        # Update strategy parameters
        self._update_parameters(regime)
        
        logger.info(f"Current market regime: {regime.name} (ID: {regime.regime_id})")
        
        return regime
    
    def _update_parameters(self, regime: MarketRegime):
        """Update strategy parameters based on regime"""
        # Get base parameters for this regime
        regime_params = self.regime_parameters.get(
            regime.regime_id, self.base_parameters
        )
        
        # Apply confidence-weighted adjustment
        confidence = regime.confidence
        
        # Create new parameters with weighted values
        self.current_parameters = StrategyParameters(
            position_size_multiplier=self._weighted_param(
                self.base_parameters.position_size_multiplier,
                regime_params.position_size_multiplier,
                confidence
            ),
            max_position_size=self._weighted_param(
                self.base_parameters.max_position_size,
                regime_params.max_position_size,
                confidence
            ),
            entry_threshold=self._weighted_param(
                self.base_parameters.entry_threshold,
                regime_params.entry_threshold,
                confidence
            ),
            entry_confirmation_required=regime_params.entry_confirmation_required if confidence > 0.7 else True,
            stop_loss_multiplier=self._weighted_param(
                self.base_parameters.stop_loss_multiplier,
                regime_params.stop_loss_multiplier,
                confidence
            ),
            take_profit_multiplier=self._weighted_param(
                self.base_parameters.take_profit_multiplier,
                regime_params.take_profit_multiplier,
                confidence
            ),
            trailing_stop_enabled=regime_params.trailing_stop_enabled if confidence > 0.7 else False,
            trailing_stop_distance=self._weighted_param(
                self.base_parameters.trailing_stop_distance,
                regime_params.trailing_stop_distance,
                confidence
            ),
            holding_period_multiplier=self._weighted_param(
                self.base_parameters.holding_period_multiplier,
                regime_params.holding_period_multiplier,
                confidence
            ),
            risk_per_trade=self._weighted_param(
                self.base_parameters.risk_per_trade,
                regime_params.risk_per_trade,
                confidence
            ),
            max_correlation_allowed=self._weighted_param(
                self.base_parameters.max_correlation_allowed,
                regime_params.max_correlation_allowed,
                confidence
            ),
            execution_aggression=self._weighted_param(
                self.base_parameters.execution_aggression,
                regime_params.execution_aggression,
                confidence
            )
        )
        
        logger.debug(f"Updated strategy parameters for regime {regime.name}")
    
    def _weighted_param(self, base_value: float, regime_value: float, confidence: float) -> float:
        """Calculate confidence-weighted parameter value"""
        return base_value * (1 - confidence) + regime_value * confidence
    
    def get_current_parameters(self) -> StrategyParameters:
        """Get current strategy parameters"""
        return self.current_parameters
    
    def update_performance(self, trade_result: Dict[str, Any]):
        """
        Update performance tracking by regime
        
        Args:
            trade_result: Trade result including PnL, regime, etc.
        """
        if not self.current_regime:
            return
        
        regime_id = self.current_regime.regime_id
        
        # Initialize regime performance if needed
        if regime_id not in self.performance_by_regime:
            self.performance_by_regime[regime_id] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'trades_by_strategy': {}
            }
        
        perf = self.performance_by_regime[regime_id]
        
        # Update metrics
        perf['trades'] += 1
        
        pnl = trade_result.get('pnl', 0)
        perf['total_pnl'] += pnl
        
        if pnl > 0:
            perf['wins'] += 1
        else:
            perf['losses'] += 1
        
        # Update averages
        perf['avg_pnl'] = perf['total_pnl'] / perf['trades']
        perf['win_rate'] = perf['wins'] / perf['trades'] if perf['trades'] > 0 else 0
        
        # Update by strategy
        strategy = trade_result.get('strategy', 'default')
        if strategy not in perf['trades_by_strategy']:
            perf['trades_by_strategy'][strategy] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0.0
            }
        
        strat_perf = perf['trades_by_strategy'][strategy]
        strat_perf['trades'] += 1
        strat_perf['total_pnl'] += pnl
        if pnl > 0:
            strat_perf['wins'] += 1
        
        logger.debug(f"Updated performance for regime {regime_id}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary by regime"""
        return {
            'by_regime': self.performance_by_regime,
            'current_regime': self.current_regime.to_dict() if self.current_regime else None,
            'current_parameters': self.current_parameters.to_dict()
        }
    
    def optimize_parameters(self):
        """
        Optimize strategy parameters based on performance
        
        This would typically use more advanced optimization techniques
        like Bayesian optimization, but here we use a simple approach
        """
        if not self.performance_by_regime:
            logger.warning("No performance data for parameter optimization")
            return
        
        # For each regime with enough data
        for regime_id, perf in self.performance_by_regime.items():
            if perf['trades'] < 10:
                continue  # Not enough data
            
            # Get current parameters
            current_params = self.regime_parameters.get(regime_id, self.base_parameters)
            
            # Simple optimization based on win rate
            win_rate = perf['win_rate']
            
            if win_rate > 0.6:
                # Successful regime, increase position size
                new_position_multiplier = min(1.5, current_params.position_size_multiplier * 1.1)
                new_risk = min(0.02, current_params.risk_per_trade * 1.1)
            elif win_rate < 0.4:
                # Unsuccessful regime, decrease position size
                new_position_multiplier = max(0.3, current_params.position_size_multiplier * 0.9)
                new_risk = max(0.003, current_params.risk_per_trade * 0.9)
            else:
                # Neutral, keep same
                new_position_multiplier = current_params.position_size_multiplier
                new_risk = current_params.risk_per_trade
            
            # Update parameters
            self.regime_parameters[regime_id] = StrategyParameters(
                position_size_multiplier=new_position_multiplier,
                max_position_size=current_params.max_position_size,
                entry_threshold=current_params.entry_threshold,
                entry_confirmation_required=current_params.entry_confirmation_required,
                stop_loss_multiplier=current_params.stop_loss_multiplier,
                take_profit_multiplier=current_params.take_profit_multiplier,
                trailing_stop_enabled=current_params.trailing_stop_enabled,
                trailing_stop_distance=current_params.trailing_stop_distance,
                holding_period_multiplier=current_params.holding_period_multiplier,
                risk_per_trade=new_risk,
                max_correlation_allowed=current_params.max_correlation_allowed,
                execution_aggression=current_params.execution_aggression
            )
            
            logger.info(f"Optimized parameters for regime {regime_id}")
    
    def save_state(self, file_path: str):
        """Save strategy state to file"""
        state = {
            'current_regime': self.current_regime.to_dict() if self.current_regime else None,
            'performance_by_regime': self.performance_by_regime,
            'regime_parameters': {k: v.to_dict() for k, v in self.regime_parameters.items()},
            'base_parameters': self.base_parameters.to_dict()
        }
        
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved strategy state to {file_path}")
    
    def load_state(self, file_path: str):
        """Load strategy state from file"""
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            # Load regime parameters
            for regime_id, params_dict in state.get('regime_parameters', {}).items():
                self.regime_parameters[int(regime_id)] = StrategyParameters(**params_dict)
            
            # Load base parameters
            if 'base_parameters' in state:
                self.base_parameters = StrategyParameters(**state['base_parameters'])
            
            # Load performance
            self.performance_by_regime = state.get('performance_by_regime', {})
            
            # Load current regime
            if state.get('current_regime'):
                self.current_regime = MarketRegime.from_dict(state['current_regime'])
                self._update_parameters(self.current_regime)
            
            logger.info(f"Loaded strategy state from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading strategy state: {e}")
            return False
