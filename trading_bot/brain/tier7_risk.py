"""
Tier 7: Risk & Portfolio Optimization
Manages risk and optimizes portfolio allocation
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from scipy import stats
from scipy.optimize import minimize

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector, SentimentVector, 
    MacroContext, RiskParameters
)

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for a position or portfolio"""
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float


class HierarchicalRiskParity:
    """
    Hierarchical Risk Parity (HRP) portfolio optimization
    Based on Lopez de Prado's algorithm
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def optimize(self, returns: pd.DataFrame) -> Dict[str, float]:
        """
        Optimize portfolio weights using HRP
        
        Args:
            returns: DataFrame of asset returns
            
        Returns:
            Dictionary of asset weights
        """
        try:
            # Calculate correlation matrix
            corr = returns.corr()
            
            # Calculate distance matrix
            dist = np.sqrt(0.5 * (1 - corr))
            
            # Hierarchical clustering
            links = self._get_clusters(dist)
            
            # Get quasi-diagonal matrix
            sorted_assets = self._get_quasi_diagonal(links)
            
            # Calculate inverse variance weights
            inv_var = 1 / returns.var()
            
            # Calculate cluster variances
            cluster_var = self._get_cluster_var(returns[sorted_assets])
            
            # Calculate final weights
            weights = self._get_recursive_bisection(cluster_var, inv_var[sorted_assets])
            
            # Return as dictionary
            return {asset: weight for asset, weight in zip(sorted_assets, weights)}
            
        except Exception as e:
            logger.error(f"Error in HRP optimization: {str(e)}")
            # Return equal weights as fallback
            return {col: 1.0/len(returns.columns) for col in returns.columns}
    
    def _get_clusters(self, dist: pd.DataFrame) -> np.ndarray:
        """Perform hierarchical clustering"""
        from scipy.cluster.hierarchy import linkage
        links = linkage(dist, 'single')
        return links
    
    def _get_quasi_diagonal(self, links: np.ndarray) -> pd.Index:
        """Get quasi-diagonal matrix from clusters"""
        from scipy.cluster.hierarchy import leaves_list
        return leaves_list(links)
    
    def _get_cluster_var(self, returns: pd.DataFrame) -> pd.Series:
        """Calculate cluster variances"""
        return returns.var()
    
    def _get_recursive_bisection(self, cluster_var: pd.Series, 
                               inv_var: pd.Series) -> np.ndarray:
        """Calculate weights using recursive bisection"""
        w = pd.Series(1, index=cluster_var.index)
        c_items = [cluster_var.index.tolist()]
        
        while len(c_items) > 0:
            c_items = [i[j:k] for i in c_items for j, k in ((0, len(i)//2), 
                      (len(i)//2, len(i))) if len(i) > 1]
            
            for i in range(0, len(c_items), 2):
                if len(c_items) > i + 1:
                    left = c_items[i]
                    right = c_items[i + 1]
                    left_var = cluster_var[left].sum()
                    right_var = cluster_var[right].sum()
                    alpha = 1 - left_var/(left_var + right_var)
                    w[left] *= alpha
                    w[right] *= (1 - alpha)
        
        return w * inv_var/sum(w * inv_var)


class DynamicPositionSizing:
    """Dynamic position sizing based on confidence and volatility"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_position_size = self.config.get('max_position_size', 0.2)
        self.min_position_size = self.config.get('min_position_size', 0.01)
        self.kelly_fraction = self.config.get('kelly_fraction', 0.5)
    
    def calculate_size(self, confidence: float, volatility: float, 
                      win_rate: float, profit_factor: float) -> Dict[str, float]:
        """
        Calculate optimal position size
        
        Args:
            confidence: Signal confidence (0-1)
            volatility: Current volatility
            win_rate: Historical win rate
            profit_factor: Profit factor
            
        Returns:
            Dictionary with position size and metrics
        """
        try:
            # Calculate Kelly criterion
            avg_win = profit_factor / win_rate if win_rate > 0 else 1.0
            avg_loss = 1.0
            kelly = win_rate - ((1 - win_rate) / (avg_win/avg_loss))
            
            # Apply fraction and confidence
            kelly *= self.kelly_fraction * confidence
            
            # Adjust for volatility
            vol_factor = np.exp(-volatility)  # Reduce size in high volatility
            
            # Calculate final size
            position_size = kelly * vol_factor
            
            # Apply limits
            position_size = max(min(position_size, self.max_position_size), 
                              self.min_position_size)
            
            return {
                'position_size': position_size,
                'kelly_percentage': kelly * 100,
                'volatility_factor': vol_factor,
                'confidence_factor': confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return {
                'position_size': self.min_position_size,
                'kelly_percentage': 0.0,
                'volatility_factor': 1.0,
                'confidence_factor': 0.0
            }


class AdaptiveStopLoss:
    """Adaptive stop-loss placement engine"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.atr_multiplier = self.config.get('atr_multiplier', 2.0)
        self.min_stop_distance = self.config.get('min_stop_distance', 0.001)
    
    def calculate_stops(self, df: pd.DataFrame, position_type: str,
                       liquidity_zones: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate adaptive stop-loss levels
        
        Args:
            df: OHLCV DataFrame
            position_type: 'long' or 'short'
            liquidity_zones: Dictionary of liquidity zones
            
        Returns:
            Dictionary with stop levels
        """
        try:
            # Calculate ATR
            atr = self._calculate_atr(df)
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Base stop distance on ATR
            base_stop = atr * self.atr_multiplier
            
            # Adjust for liquidity zones
            if liquidity_zones and 'zones' in liquidity_zones:
                nearest_zone = self._find_nearest_zone(current_price, 
                                                     liquidity_zones['zones'],
                                                     position_type)
                if nearest_zone:
                    # Use liquidity zone if it's closer than ATR-based stop
                    if position_type == 'long':
                        zone_stop = nearest_zone['low']
                        base_stop = min(base_stop, current_price - zone_stop)
                    else:
                        zone_stop = nearest_zone['high']
                        base_stop = min(base_stop, zone_stop - current_price)
            
            # Calculate stop levels
            if position_type == 'long':
                initial_stop = current_price - base_stop
                breakeven_stop = current_price
                trailing_stop = current_price - (base_stop * 0.8)
            else:
                initial_stop = current_price + base_stop
                breakeven_stop = current_price
                trailing_stop = current_price + (base_stop * 0.8)
            
            # Ensure minimum distance
            min_distance = current_price * self.min_stop_distance
            if position_type == 'long':
                initial_stop = min(initial_stop, current_price - min_distance)
            else:
                initial_stop = max(initial_stop, current_price + min_distance)
            
            return {
                'initial_stop': initial_stop,
                'breakeven_stop': breakeven_stop,
                'trailing_stop': trailing_stop,
                'atr_value': atr,
                'stop_distance': base_stop
            }
            
        except Exception as e:
            logger.error(f"Error calculating stops: {str(e)}")
            return {
                'initial_stop': 0.0,
                'breakeven_stop': 0.0,
                'trailing_stop': 0.0,
                'atr_value': 0.0,
                'stop_distance': 0.0
            }
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.iloc[-1]
    
    def _find_nearest_zone(self, price: float, zones: List[Dict], 
                          position_type: str) -> Optional[Dict]:
        """Find nearest liquidity zone"""
        nearest_zone = None
        min_distance = float('inf')
        
        for zone in zones:
            if position_type == 'long' and zone['high'] < price:
                distance = price - zone['high']
                if distance < min_distance:
                    min_distance = distance
                    nearest_zone = zone
            elif position_type == 'short' and zone['low'] > price:
                distance = zone['low'] - price
                if distance < min_distance:
                    min_distance = distance
                    nearest_zone = zone
        
        return nearest_zone


class MonteCarloAnalysis:
    """Monte Carlo portfolio stress testing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.num_simulations = self.config.get('num_simulations', 1000)
        self.confidence_level = self.config.get('confidence_level', 0.95)
    
    def run_simulation(self, returns: pd.Series, position_size: float,
                      holding_period: int) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation
        
        Args:
            returns: Historical returns series
            position_size: Current position size
            holding_period: Expected holding period in bars
            
        Returns:
            Dictionary with simulation results
        """
        try:
            # Calculate parameters
            mu = returns.mean()
            sigma = returns.std()
            
            # Generate simulations
            simulations = np.random.normal(
                mu * holding_period,
                sigma * np.sqrt(holding_period),
                self.num_simulations
            )
            
            # Calculate portfolio values
            portfolio_values = 1 + (simulations * position_size)
            
            # Calculate risk metrics
            var_95 = np.percentile(portfolio_values, 5) - 1
            cvar_95 = portfolio_values[portfolio_values <= var_95].mean() - 1
            
            # Calculate probabilities
            prob_profit = (portfolio_values > 1).mean()
            prob_loss = 1 - prob_profit
            
            # Calculate expected values
            expected_return = portfolio_values.mean() - 1
            expected_shortfall = (portfolio_values[portfolio_values < 1] - 1).mean()
            
            return {
                'var_95': var_95,
                'cvar_95': cvar_95,
                'probability_profit': prob_profit,
                'probability_loss': prob_loss,
                'expected_return': expected_return,
                'expected_shortfall': expected_shortfall,
                'simulated_values': portfolio_values.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {str(e)}")
            return {
                'var_95': -position_size,
                'cvar_95': -position_size,
                'probability_profit': 0.5,
                'probability_loss': 0.5,
                'expected_return': 0.0,
                'expected_shortfall': -position_size,
                'simulated_values': []
            }


class Tier7RiskManagement(TierBase):
    """
    Tier 7: Risk & Portfolio Optimization
    
    Manages risk and optimizes portfolio:
    - Hierarchical Risk Parity (HRP)
    - Dynamic Position Sizing
    - Adaptive Stop-Loss Engine
    - Monte Carlo Stress Testing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 7: Risk Management", config)
        self.hrp = None
        self.position_sizer = None
        self.stop_loss = None
        self.monte_carlo = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.hrp = HierarchicalRiskParity(self.config.get('hrp', {}))
        self.position_sizer = DynamicPositionSizing(self.config.get('position', {}))
        self.stop_loss = AdaptiveStopLoss(self.config.get('stops', {}))
        self.monte_carlo = MonteCarloAnalysis(self.config.get('simulation', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[MacroContext] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> RiskParameters:
        """
        Process market data and generate risk parameters
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 6 (MacroContext)
            additional_inputs: Dictionary with portfolio data and performance metrics
            
        Returns:
            RiskParameters with risk management decisions
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 7")
            return None
        try:
        
            # Get additional data
            portfolio_data = additional_inputs.get('portfolio_data', {})
            performance = additional_inputs.get('performance_metrics', {})
            liquidity_zones = additional_inputs.get('liquidity_zones', {})
            
            # Get signal direction and confidence
            signal_value = previous_tier_output.signal_value if previous_tier_output else 0.0
            confidence = previous_tier_output.confidence if previous_tier_output else 0.5
            
            # Determine position type
            position_type = 'long' if signal_value > 0 else 'short'
            
            # Calculate portfolio optimization if we have portfolio data
            if portfolio_data:
                returns = pd.DataFrame(portfolio_data['returns'])
                weights = self.hrp.optimize(returns)
            else:
                weights = {'current': 1.0}
            
            # Calculate position size
            volatility = market_data['close'].pct_change().std() * np.sqrt(252)
            win_rate = performance.get('win_rate', 0.5)
            profit_factor = performance.get('profit_factor', 1.0)
            
            size_result = self.position_sizer.calculate_size(
                confidence, volatility, win_rate, profit_factor
            )
            
            # Calculate stop levels
            stops = self.stop_loss.calculate_stops(
                market_data, position_type, liquidity_zones
            )
            
            # Run Monte Carlo simulation
            returns = market_data['close'].pct_change()
            simulation = self.monte_carlo.run_simulation(
                returns, size_result['position_size'], holding_period=20
            )
            
            # Calculate risk-reward ratio
            if position_type == 'long':
                risk = (market_data['close'].iloc[-1] - stops['initial_stop']) / market_data['close'].iloc[-1]
                reward = simulation['expected_return']
            else:
                risk = (stops['initial_stop'] - market_data['close'].iloc[-1]) / market_data['close'].iloc[-1]
                reward = -simulation['expected_return']
            
            risk_reward_ratio = abs(reward / risk) if risk != 0 else 0.0
            
            # Calculate signal value (-1 to 1)
            # Based on risk-adjusted expected return
            signal_value = np.sign(reward) * min(abs(reward / volatility), 1.0)
            
            # Calculate confidence (0 to 1)
            confidence_factors = [
                simulation['probability_profit'],
                min(risk_reward_ratio / 3, 1.0),
                1.0 - abs(simulation['var_95'])
            ]
            confidence = np.mean(confidence_factors)
            
            # Create metadata
            metadata = {
                'portfolio_weights': weights,
                'position_sizing': size_result,
                'stop_levels': stops,
                'simulation': simulation
            }
            
            # Create risk parameters
            risk_params = RiskParameters(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                position_size=size_result['position_size'],
                stop_loss_level=stops['initial_stop'],
                take_profit_level=market_data['close'].iloc[-1] * (1 + reward),
                max_drawdown_limit=abs(simulation['var_95']),
                portfolio_var=abs(simulation['var_95']),
                risk_reward_ratio=risk_reward_ratio,
                metadata=metadata
            )
            
            self.last_output = risk_params
            return risk_params
            
        except Exception as e:
            logger.error(f"Error processing Tier 7: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample additional inputs
    additional_inputs = {
        'portfolio_data': {
            'returns': {
                'asset1': np.random.randn(100) * 0.02,
                'asset2': np.random.randn(100) * 0.03,
                'asset3': np.random.randn(100) * 0.01
            }
        },
        'performance_metrics': {
            'win_rate': 0.55,
            'profit_factor': 1.2
        },
        'liquidity_zones': {
            'zones': [
                {'high': 99.5, 'low': 99.0},
                {'high': 101.0, 'low': 100.5}
            ]
        }
    }
    
    # Initialize and process
    tier7 = Tier7RiskManagement()
    tier7.initialize()
    result = tier7.process(df, additional_inputs=additional_inputs)
    
    # Print results
    logger.info("\n=== Tier 7: Risk Management Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Position Size: {result.position_size:.2%}")
    logger.info(f"Stop Loss: {result.stop_loss_level:.2f}")
    logger.info(f"Take Profit: {result.take_profit_level:.2f}")
    logger.info(f"Risk-Reward Ratio: {result.risk_reward_ratio:.2f}")
    logger.info(f"Portfolio VaR: {result.portfolio_var:.2%}")
    logger.info(f"Max Drawdown Limit: {result.max_drawdown_limit:.2%}")
