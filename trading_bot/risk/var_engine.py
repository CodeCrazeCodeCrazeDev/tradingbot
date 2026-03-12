"""
Value at Risk (VaR) Engine
==========================

Comprehensive risk measurement system implementing:
- Historical VaR
- Parametric VaR (Variance-Covariance)
- Monte Carlo VaR
- Expected Shortfall (CVaR)
- Marginal VaR
- Component VaR
- Incremental VaR
- Stressed VaR

Author: Elite Trading Bot
Version: 1.0.0
"""

import numpy as np
import pandas as pd
try:
    from scipy import stats
except ImportError:
    scipy = None
from scipy.optimize import minimize
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import logging
from concurrent.futures import ThreadPoolExecutor
import warnings
import numpy
import pandas

logger = logging.getLogger(__name__)


class VaRMethod(Enum):
    """VaR calculation methods"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"
    EWMA = "ewma"


class DistributionType(Enum):
    """Distribution types for parametric VaR"""
    NORMAL = "normal"
    STUDENT_T = "student_t"
    GENERALIZED_PARETO = "generalized_pareto"


@dataclass
class VaRResult:
    """VaR calculation result"""
    var_value: float
    confidence_level: float
    time_horizon_days: int
    method: VaRMethod
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Additional metrics
    expected_shortfall: Optional[float] = None
    marginal_var: Optional[Dict[str, float]] = None
    component_var: Optional[Dict[str, float]] = None
    
    # Distribution parameters
    mean_return: float = 0.0
    volatility: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    
    # Confidence interval
    var_lower: Optional[float] = None
    var_upper: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'var_value': self.var_value,
            'confidence_level': self.confidence_level,
            'time_horizon_days': self.time_horizon_days,
            'method': self.method.value,
            'currency': self.currency,
            'timestamp': self.timestamp.isoformat(),
            'expected_shortfall': self.expected_shortfall,
            'marginal_var': self.marginal_var,
            'component_var': self.component_var,
            'mean_return': self.mean_return,
            'volatility': self.volatility,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis
        }


@dataclass
class StressTestResult:
    """Stress test result"""
    scenario_name: str
    portfolio_loss: float
    var_breach: bool
    positions_affected: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    """Position for VaR calculation"""
    symbol: str
    quantity: float
    current_price: float
    market_value: float
    weight: float = 0.0
    
    @property
    def notional(self) -> float:
        return self.quantity * self.current_price


class VaREngine:
    """
    Comprehensive Value at Risk calculation engine
    """
    
    def __init__(
        self,
        confidence_levels: List[float] = None,
        time_horizons: List[int] = None,
        lookback_days: int = 252,
        monte_carlo_simulations: int = 10000,
        ewma_lambda: float = 0.94
    ):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.time_horizons = time_horizons or [1, 10]
        self.lookback_days = lookback_days
        self.monte_carlo_simulations = monte_carlo_simulations
        self.ewma_lambda = ewma_lambda
        
        # Cache for returns data
        self.returns_cache: Dict[str, pd.Series] = {}
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.covariance_matrix: Optional[pd.DataFrame] = None
        
        # Historical VaR results
        self.var_history: List[VaRResult] = []
        
        logger.info("VaREngine initialized")
    
    def calculate_var(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series],
        method: VaRMethod = VaRMethod.HISTORICAL,
        confidence_level: float = 0.95,
        time_horizon: int = 1
    ) -> VaRResult:
        """
        Calculate VaR for a portfolio
        
        Args:
            positions: List of positions
            returns_data: Dictionary of symbol -> returns series
            method: VaR calculation method
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            time_horizon: Time horizon in days
            
        Returns:
            VaRResult with calculated VaR
        """
        # Calculate portfolio returns
        portfolio_returns = self._calculate_portfolio_returns(positions, returns_data)
        
        if len(portfolio_returns) < 30:
            logger.warning("Insufficient data for VaR calculation")
            return VaRResult(
                var_value=0.0,
                confidence_level=confidence_level,
                time_horizon_days=time_horizon,
                method=method
            )
        
        # Calculate VaR based on method
        if method == VaRMethod.HISTORICAL:
            var_value = self._historical_var(portfolio_returns, confidence_level, time_horizon)
        elif method == VaRMethod.PARAMETRIC:
            var_value = self._parametric_var(portfolio_returns, confidence_level, time_horizon)
        elif method == VaRMethod.MONTE_CARLO:
            var_value = self._monte_carlo_var(positions, returns_data, confidence_level, time_horizon)
        elif method == VaRMethod.CORNISH_FISHER:
            var_value = self._cornish_fisher_var(portfolio_returns, confidence_level, time_horizon)
        elif method == VaRMethod.EWMA:
            var_value = self._ewma_var(portfolio_returns, confidence_level, time_horizon)
        else:
            var_value = self._historical_var(portfolio_returns, confidence_level, time_horizon)
        
        # Calculate portfolio value
        portfolio_value = sum(p.market_value for p in positions)
        var_amount = var_value * portfolio_value
        
        # Calculate Expected Shortfall (CVaR)
        es = self._calculate_expected_shortfall(portfolio_returns, confidence_level, time_horizon)
        es_amount = es * portfolio_value
        
        # Calculate distribution parameters
        mean_return = portfolio_returns.mean()
        volatility = portfolio_returns.std()
        skewness = portfolio_returns.skew()
        kurtosis = portfolio_returns.kurtosis()
        
        # Calculate marginal and component VaR
        marginal_var = self._calculate_marginal_var(positions, returns_data, confidence_level)
        component_var = self._calculate_component_var(positions, returns_data, confidence_level)
        
        result = VaRResult(
            var_value=var_amount,
            confidence_level=confidence_level,
            time_horizon_days=time_horizon,
            method=method,
            expected_shortfall=es_amount,
            marginal_var=marginal_var,
            component_var=component_var,
            mean_return=mean_return,
            volatility=volatility,
            skewness=skewness,
            kurtosis=kurtosis
        )
        
        self.var_history.append(result)
        
        return result
    
    def _calculate_portfolio_returns(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series]
    ) -> pd.Series:
        """Calculate weighted portfolio returns"""
        # Calculate weights
        total_value = sum(p.market_value for p in positions)
        if total_value == 0:
            return pd.Series()
        
        for p in positions:
            p.weight = p.market_value / total_value
        
        # Align all return series
        symbols = [p.symbol for p in positions if p.symbol in returns_data]
        if not symbols:
            return pd.Series()
        
        returns_df = pd.DataFrame({s: returns_data[s] for s in symbols})
        returns_df = returns_df.dropna()
        
        # Calculate weighted returns
        weights = np.array([p.weight for p in positions if p.symbol in returns_data])
        portfolio_returns = (returns_df * weights).sum(axis=1)
        
        return portfolio_returns
    
    def _historical_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate Historical VaR"""
        # Scale returns for time horizon
        scaled_returns = returns * np.sqrt(time_horizon)
        
        # Calculate VaR as percentile
        var = -np.percentile(scaled_returns, (1 - confidence_level) * 100)
        
        return var
    
    def _parametric_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon: int,
        distribution: DistributionType = DistributionType.NORMAL
    ) -> float:
        """Calculate Parametric (Variance-Covariance) VaR"""
        mean = returns.mean()
        std = returns.std()
        
        # Scale for time horizon
        mean_scaled = mean * time_horizon
        std_scaled = std * np.sqrt(time_horizon)
        
        if distribution == DistributionType.NORMAL:
            z_score = stats.norm.ppf(1 - confidence_level)
        elif distribution == DistributionType.STUDENT_T:
            # Estimate degrees of freedom
            df = self._estimate_t_df(returns)
            z_score = stats.t.ppf(1 - confidence_level, df)
        else:
            z_score = stats.norm.ppf(1 - confidence_level)
        
        var = -(mean_scaled + z_score * std_scaled)
        
        return var
    
    def _monte_carlo_var(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series],
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate Monte Carlo VaR"""
        # Build covariance matrix
        symbols = [p.symbol for p in positions if p.symbol in returns_data]
        returns_df = pd.DataFrame({s: returns_data[s] for s in symbols}).dropna()
        
        if returns_df.empty:
            return 0.0
        
        cov_matrix = returns_df.cov() * time_horizon
        mean_returns = returns_df.mean() * time_horizon
        
        # Cholesky decomposition
        try:
            chol = np.linalg.cholesky(cov_matrix)
        except np.linalg.LinAlgError:
            # Matrix not positive definite, use eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            eigenvalues = np.maximum(eigenvalues, 0)
            chol = eigenvectors @ np.diag(np.sqrt(eigenvalues))
        
        # Generate random scenarios
        n_assets = len(symbols)
        random_returns = np.random.standard_normal((self.monte_carlo_simulations, n_assets))
        simulated_returns = mean_returns.values + random_returns @ chol.T
        
        # Calculate portfolio returns
        weights = np.array([p.weight for p in positions if p.symbol in returns_data])
        portfolio_returns = simulated_returns @ weights
        
        # Calculate VaR
        var = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        
        return var
    
    def _cornish_fisher_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate Cornish-Fisher VaR (adjusts for skewness and kurtosis)"""
        mean = returns.mean() * time_horizon
        std = returns.std() * np.sqrt(time_horizon)
        skew = returns.skew()
        kurt = returns.kurtosis()
        
        z = stats.norm.ppf(1 - confidence_level)
        
        # Cornish-Fisher expansion
        z_cf = (z + 
                (z**2 - 1) * skew / 6 +
                (z**3 - 3*z) * kurt / 24 -
                (2*z**3 - 5*z) * skew**2 / 36)
        
        var = -(mean + z_cf * std)
        
        return var
    
    def _ewma_var(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate EWMA (Exponentially Weighted Moving Average) VaR"""
        # Calculate EWMA variance
        ewma_var = returns.ewm(alpha=1-self.ewma_lambda).var().iloc[-1]
        ewma_std = np.sqrt(ewma_var) * np.sqrt(time_horizon)
        
        mean = returns.mean() * time_horizon
        z_score = stats.norm.ppf(1 - confidence_level)
        
        var = -(mean + z_score * ewma_std)
        
        return var
    
    def _calculate_expected_shortfall(
        self,
        returns: pd.Series,
        confidence_level: float,
        time_horizon: int
    ) -> float:
        """Calculate Expected Shortfall (CVaR)"""
        scaled_returns = returns * np.sqrt(time_horizon)
        var_threshold = np.percentile(scaled_returns, (1 - confidence_level) * 100)
        
        # ES is the average of returns below VaR
        tail_returns = scaled_returns[scaled_returns <= var_threshold]
        
        if len(tail_returns) == 0:
            return -var_threshold
        
        es = -tail_returns.mean()
        
        return es
    
    def _calculate_marginal_var(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series],
        confidence_level: float
    ) -> Dict[str, float]:
        """Calculate Marginal VaR for each position"""
        marginal_var = {}
        
        # Calculate portfolio VaR
        portfolio_returns = self._calculate_portfolio_returns(positions, returns_data)
        portfolio_var = self._historical_var(portfolio_returns, confidence_level, 1)
        portfolio_value = sum(p.market_value for p in positions)
        
        for position in positions:
            if position.symbol not in returns_data:
                continue
            
            # Calculate VaR without this position
            other_positions = [p for p in positions if p.symbol != position.symbol]
            if not other_positions:
                marginal_var[position.symbol] = portfolio_var * portfolio_value
                continue
            
            other_returns = self._calculate_portfolio_returns(other_positions, returns_data)
            other_var = self._historical_var(other_returns, confidence_level, 1)
            other_value = sum(p.market_value for p in other_positions)
            
            # Marginal VaR is the difference
            marginal_var[position.symbol] = (portfolio_var * portfolio_value - 
                                              other_var * other_value)
        
        return marginal_var
    
    def _calculate_component_var(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series],
        confidence_level: float
    ) -> Dict[str, float]:
        """Calculate Component VaR for each position"""
        component_var = {}
        
        # Build covariance matrix
        symbols = [p.symbol for p in positions if p.symbol in returns_data]
        returns_df = pd.DataFrame({s: returns_data[s] for s in symbols}).dropna()
        
        if returns_df.empty:
            return component_var
        
        cov_matrix = returns_df.cov()
        
        # Calculate portfolio variance
        weights = np.array([p.weight for p in positions if p.symbol in returns_data])
        portfolio_var = weights @ cov_matrix.values @ weights
        portfolio_std = np.sqrt(portfolio_var)
        
        # Calculate component VaR
        z_score = stats.norm.ppf(confidence_level)
        portfolio_value = sum(p.market_value for p in positions)
        
        for i, position in enumerate(positions):
            if position.symbol not in returns_data:
                continue
            
            # Beta of position to portfolio
            position_cov = cov_matrix.loc[position.symbol].values @ weights
            beta = position_cov / portfolio_var if portfolio_var > 0 else 0
            
            # Component VaR
            component_var[position.symbol] = (
                position.weight * beta * z_score * portfolio_std * portfolio_value
            )
        
        return component_var
    
    def _estimate_t_df(self, returns: pd.Series) -> float:
        """Estimate degrees of freedom for Student-t distribution"""
        # Method of moments estimator
        kurtosis = returns.kurtosis()
        if kurtosis <= 0:
            return 30  # Default to high df (approaches normal)
        
        # For Student-t, kurtosis = 6/(df-4) for df > 4
        df = 6 / kurtosis + 4
        return max(df, 3)  # Minimum df of 3
    
    def calculate_incremental_var(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series],
        new_position: Position,
        confidence_level: float = 0.95
    ) -> float:
        """Calculate Incremental VaR for adding a new position"""
        # Current portfolio VaR
        current_returns = self._calculate_portfolio_returns(positions, returns_data)
        current_var = self._historical_var(current_returns, confidence_level, 1)
        current_value = sum(p.market_value for p in positions)
        
        # New portfolio VaR
        new_positions = positions + [new_position]
        new_returns = self._calculate_portfolio_returns(new_positions, returns_data)
        new_var = self._historical_var(new_returns, confidence_level, 1)
        new_value = sum(p.market_value for p in new_positions)
        
        # Incremental VaR
        incremental_var = new_var * new_value - current_var * current_value
        
        return incremental_var
    
    def run_stress_test(
        self,
        positions: List[Position],
        scenarios: Dict[str, Dict[str, float]]
    ) -> List[StressTestResult]:
        """
        Run stress tests on portfolio
        
        Args:
            positions: Current positions
            scenarios: Dict of scenario_name -> {symbol: shock_pct}
            
        Returns:
            List of StressTestResult
        """
        results = []
        
        # Get current VaR for comparison
        portfolio_value = sum(p.market_value for p in positions)
        
        for scenario_name, shocks in scenarios.items():
            positions_affected = {}
            total_loss = 0.0
            
            for position in positions:
                shock = shocks.get(position.symbol, 0.0)
                if shock != 0:
                    loss = position.market_value * shock
                    total_loss += loss
                    positions_affected[position.symbol] = loss
            
            result = StressTestResult(
                scenario_name=scenario_name,
                portfolio_loss=total_loss,
                var_breach=abs(total_loss) > portfolio_value * 0.05,  # 5% threshold
                positions_affected=positions_affected
            )
            results.append(result)
        
        return results
    
    def get_predefined_stress_scenarios(self) -> Dict[str, Dict[str, float]]:
        """Get predefined stress test scenarios"""
        return {
            'market_crash': {
                'EURUSD': -0.05, 'GBPUSD': -0.07, 'USDJPY': 0.08,
                'AUDUSD': -0.10, 'USDCAD': 0.05
            },
            'flash_crash': {
                'EURUSD': -0.03, 'GBPUSD': -0.05, 'USDJPY': 0.03,
                'AUDUSD': -0.06, 'USDCAD': 0.02
            },
            'usd_collapse': {
                'EURUSD': 0.10, 'GBPUSD': 0.08, 'USDJPY': -0.15,
                'AUDUSD': 0.12, 'USDCAD': -0.08
            },
            'risk_off': {
                'EURUSD': -0.02, 'GBPUSD': -0.04, 'USDJPY': 0.05,
                'AUDUSD': -0.08, 'USDCAD': 0.03
            },
            'emerging_market_crisis': {
                'EURUSD': 0.01, 'GBPUSD': -0.02, 'USDJPY': 0.06,
                'AUDUSD': -0.12, 'USDCAD': 0.04
            }
        }
    
    def backtest_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        method: VaRMethod = VaRMethod.HISTORICAL,
        window: int = 252
    ) -> Dict[str, Any]:
        """
        Backtest VaR model
        
        Returns metrics on VaR model accuracy
        """
        breaches = 0
        var_values = []
        actual_returns = []
        
        for i in range(window, len(returns)):
            # Calculate VaR using historical window
            historical_returns = returns.iloc[i-window:i]
            var = self._historical_var(historical_returns, confidence_level, 1)
            
            # Check if actual return breached VaR
            actual_return = returns.iloc[i]
            if actual_return < -var:
                breaches += 1
            
            var_values.append(var)
            actual_returns.append(actual_return)
        
        n_observations = len(returns) - window
        expected_breaches = n_observations * (1 - confidence_level)
        breach_rate = breaches / n_observations if n_observations > 0 else 0
        
        # Kupiec test (unconditional coverage)
        if breaches > 0 and breaches < n_observations:
            lr_uc = -2 * (
                breaches * np.log((1 - confidence_level) / breach_rate) +
                (n_observations - breaches) * np.log(confidence_level / (1 - breach_rate))
            )
            p_value_uc = 1 - stats.chi2.cdf(lr_uc, 1)
        else:
            lr_uc = 0
            p_value_uc = 1
        
        return {
            'total_observations': n_observations,
            'breaches': breaches,
            'expected_breaches': expected_breaches,
            'breach_rate': breach_rate,
            'expected_breach_rate': 1 - confidence_level,
            'kupiec_lr': lr_uc,
            'kupiec_p_value': p_value_uc,
            'model_valid': p_value_uc > 0.05
        }
    
    def get_var_summary(
        self,
        positions: List[Position],
        returns_data: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """Get comprehensive VaR summary"""
        results = {}
        
        for method in [VaRMethod.HISTORICAL, VaRMethod.PARAMETRIC, VaRMethod.MONTE_CARLO]:
            for conf in self.confidence_levels:
                for horizon in self.time_horizons:
                    key = f"{method.value}_{int(conf*100)}_{horizon}d"
                    try:
                        result = self.calculate_var(
                            positions, returns_data, method, conf, horizon
                        )
                        results[key] = result.var_value
                    except Exception as e:
                        logger.error(f"VaR calculation failed for {key}: {e}")
                        results[key] = None
        
        return results


# Singleton instance
_var_engine_instance: Optional[VaREngine] = None


def get_var_engine() -> VaREngine:
    """Get or create the VaR engine singleton"""
    global _var_engine_instance
    if _var_engine_instance is None:
        _var_engine_instance = VaREngine()
    return _var_engine_instance


# Export
__all__ = [
    'VaREngine',
    'VaRMethod',
    'VaRResult',
    'Position',
    'StressTestResult',
    'DistributionType',
    'get_var_engine'
]
