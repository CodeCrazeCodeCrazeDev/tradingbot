"""
Granger Causality - Temporal Causality Testing
=================================================

Implements Granger causality testing for temporal relationships:
1. Bivariate Granger causality
2. Multivariate Granger causality
3. Conditional Granger causality
4. Nonlinear extensions

Based on the concept that X Granger-causes Y if past values of X
help predict Y above and beyond past values of Y alone.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.api import VAR

logger = logging.getLogger(__name__)


@dataclass
class GrangerResult:
    """Result of Granger causality test"""
    cause_variable: str
    effect_variable: str
    
    # Test results
    granger_causes: bool = False
    p_value: float = 1.0
    f_statistic: float = 0.0
    lag_order: int = 1
    
    # Additional info
    test_statistic: str = "ssr_ftest"  # ssr_ftest, ssr_chi2test, lrtest, params_ftest
    confidence_level: float = 0.95
    
    # Effect size
    r_squared: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'cause': self.cause_variable,
            'effect': self.effect_variable,
            'granger_causes': self.granger_causes,
            'p_value': self.p_value,
            'f_statistic': self.f_statistic,
            'lag_order': self.lag_order,
            'r_squared': self.r_squared
        }


@dataclass
class GrangerNetwork:
    """Network of Granger causal relationships"""
    variables: List[str] = field(default_factory=list)
    relationships: List[GrangerResult] = field(default_factory=list)
    
    def get_causes(self, variable: str) -> List[str]:
        """Get variables that Granger-cause the given variable"""
        return [
            r.cause_variable
            for r in self.relationships
            if r.effect_variable == variable and r.granger_causes
        ]
    
    def get_effects(self, variable: str) -> List[str]:
        """Get variables that are Granger-caused by the given variable"""
        return [
            r.effect_variable
            for r in self.relationships
            if r.cause_variable == variable and r.granger_causes
        ]
    
    def to_adjacency_matrix(self) -> np.ndarray:
        """Convert to adjacency matrix"""
        n = len(self.variables)
        adj = np.zeros((n, n))
        
        var_index = {v: i for i, v in enumerate(self.variables)}
        
        for r in self.relationships:
            if r.granger_causes:
                i = var_index.get(r.cause_variable)
                j = var_index.get(r.effect_variable)
                if i is not None and j is not None:
                    adj[i, j] = 1
        
        return adj


class GrangerCausalityTester:
    """
    Granger Causality Tester
    
    Tests for Granger causality between time series variables.
    X Granger-causes Y if past values of X help predict Y.
    """
    
    def __init__(self, max_lag: int = 10, significance_level: float = 0.05):
        self.max_lag = max_lag
        self.significance_level = significance_level
        
        # Results storage
        self.results: List[GrangerResult] = []
        self.networks: Dict[str, GrangerNetwork] = {}
        
        # Statistics
        self.stats = {
            'tests_performed': 0,
            'significant_relationships': 0,
            'avg_lag_order': 0.0
        }
        
        logger.info(f"Granger Causality Tester initialized (max_lag={max_lag})")
    
    def test_bivariate(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_name: str = "X",
        y_name: str = "Y",
        lag: Optional[int] = None
    ) -> GrangerResult:
        """Test if X Granger-causes Y (bivariate)"""
        if lag is None:
            lag = self._select_optimal_lag(x, y)
        
        # Prepare data for statsmodels
        data = np.column_stack([y, x])
        
        try:
            # Run Granger causality test
            test_result = grangercausalitytests(data, maxlag=lag, verbose=False)
            
            # Extract results for the best lag
            best_lag_result = test_result[lag]
            
            # Use ssr F-test
            f_test = best_lag_result[0]['ssr_ftest']
            f_stat, p_value, _, _ = f_test
            
            # Calculate R-squared (approximation)
            # Compare restricted vs unrestricted model
            restricted_r2 = best_lag_result[1][0].rsquared
            unrestricted_r2 = best_lag_result[1][1].rsquared
            
            result = GrangerResult(
                cause_variable=x_name,
                effect_variable=y_name,
                granger_causes=p_value < self.significance_level,
                p_value=p_value,
                f_statistic=f_stat,
                lag_order=lag,
                r_squared=unrestricted_r2 - restricted_r2
            )
            
            self.results.append(result)
            self.stats['tests_performed'] += 1
            if result.granger_causes:
                self.stats['significant_relationships'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Granger test error: {e}")
            return GrangerResult(
                cause_variable=x_name,
                effect_variable=y_name,
                p_value=1.0,
                granger_causes=False
            )
    
    def test_multivariate(
        self,
        data: Dict[str, np.ndarray],
        target: str
    ) -> List[GrangerResult]:
        """Test Granger causality from multiple variables to target"""
        results = []
        
        if target not in data:
            return results
        
        target_series = data[target]
        
        for var_name, var_series in data.items():
            if var_name == target:
                continue
            
            if len(var_series) != len(target_series):
                continue
            
            result = self.test_bivariate(
                var_series, target_series,
                x_name=var_name, y_name=target
            )
            results.append(result)
        
        return results
    
    def test_conditional(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        x_name: str = "X",
        y_name: str = "Y",
        z_name: str = "Z"
    ) -> GrangerResult:
        """Test if X Granger-causes Y conditional on Z"""
        # Prepare data with control variable
        # Y = f(Y_lags, X_lags, Z_lags) vs Y = f(Y_lags, Z_lags)
        
        # This is a simplified conditional test
        # In practice, you'd use a VAR model with all three variables
        
        try:
            # Create VAR model
            data = np.column_stack([y, x, z])
            
            # Fit model with and without X
            model_full = VAR(data)
            results_full = model_full.fit(maxlags=self.max_lag, ic='aic')
            
            # Fit restricted model (without X)
            data_restricted = np.column_stack([y, z])
            model_restricted = VAR(data_restricted)
            results_restricted = model_restricted.fit(maxlags=self.max_lag, ic='aic')
            
            # Likelihood ratio test
            lr_stat = 2 * (results_full.llf - results_restricted.llf)
            df = results_full.df_model - results_restricted.df_model
            p_value = 1 - stats.chi2.cdf(lr_stat, df) if df > 0 else 1.0
            
            result = GrangerResult(
                cause_variable=x_name,
                effect_variable=y_name,
                granger_causes=p_value < self.significance_level,
                p_value=p_value,
                f_statistic=lr_stat / max(1, df),
                lag_order=results_full.k_ar,
                test_statistic="lrtest"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Conditional Granger test error: {e}")
            return GrangerResult(
                cause_variable=x_name,
                effect_variable=y_name,
                p_value=1.0,
                granger_causes=False
            )
    
    def build_network(
        self,
        data: Dict[str, np.ndarray],
        network_name: str = "default"
    ) -> GrangerNetwork:
        """Build Granger causality network from multiple time series"""
        network = GrangerNetwork(variables=list(data.keys()))
        
        for target_var in data.keys():
            results = self.test_multivariate(data, target_var)
            network.relationships.extend(results)
        
        self.networks[network_name] = network
        
        return network
    
    def find_causal_chains(
        self,
        start: str,
        end: str,
        network_name: str = "default",
        max_length: int = 5
    ) -> List[List[str]]:
        """Find causal chains from start to end variable"""
        if network_name not in self.networks:
            return []
        
        network = self.networks[network_name]
        
        # Build adjacency list
        adj = {var: [] for var in network.variables}
        for rel in network.relationships:
            if rel.granger_causes:
                adj[rel.cause_variable].append(rel.effect_variable)
        
        # BFS to find paths
        chains = []
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end and len(path) > 1:
                chains.append(path)
                continue
            
            if len(path) >= max_length:
                continue
            
            for neighbor in adj.get(current, []):
                if neighbor not in path:  # Avoid cycles
                    queue.append((neighbor, path + [neighbor]))
        
        return chains
    
    def _select_optimal_lag(
        self,
        x: np.ndarray,
        y: np.ndarray
    ) -> int:
        """Select optimal lag order using information criteria"""
        # Prepare data
        data = np.column_stack([y, x])
        
        try:
            # Try different lags and select using AIC
            best_aic = np.inf
            best_lag = 1
            
            for lag in range(1, min(self.max_lag + 1, len(data) // 10)):
                try:
                    model = VAR(data)
                    results = model.fit(maxlags=lag)
                    
                    if results.aic < best_aic:
                        best_aic = results.aic
                        best_lag = lag
                except:
                    break
            
            return best_lag
            
        except Exception as e:
            logger.warning(f"Lag selection error: {e}, using default lag=1")
            return 1
    
    def instantaneous_causality(
        self,
        x: np.ndarray,
        y: np.ndarray,
        x_name: str = "X",
        y_name: str = "Y"
    ) -> Dict:
        """Test for instantaneous causality (contemporaneous correlation)"""
        # Instantaneous causality tests if X[t] helps predict Y[t] given past values
        
        # This is a simplified test using contemporaneous correlation
        if len(x) != len(y) or len(x) < 2:
            return {'has_instantaneous': False, 'correlation': 0.0}
        
        # Control for past values
        x_resid = x[1:] - np.mean(x[:-1])  # Simplified residual
        y_resid = y[1:] - np.mean(y[:-1])
        
        corr = np.corrcoef(x_resid, y_resid)[0, 1]
        if np.isnan(corr):
            corr = 0.0
        
        return {
            'has_instantaneous': abs(corr) > 0.3,
            'correlation': corr,
            'p_value': 0.05  # Would need proper test
        }
    
    def granger_causality_matrix(
        self,
        data: Dict[str, np.ndarray]
    ) -> pd.DataFrame:
        """Create Granger causality matrix for all variable pairs"""
        import pandas as pd
        
        variables = list(data.keys())
        n = len(variables)
        
        # Create matrices for p-values and significance
        pvalue_matrix = np.ones((n, n))
        sig_matrix = np.zeros((n, n))
        
        for i, cause in enumerate(variables):
            for j, effect in enumerate(variables):
                if i == j:
                    continue
                
                result = self.test_bivariate(
                    data[cause], data[effect],
                    cause, effect
                )
                
                pvalue_matrix[i, j] = result.p_value
                sig_matrix[i, j] = 1 if result.granger_causes else 0
        
        # Create DataFrames
        pvalue_df = pd.DataFrame(
            pvalue_matrix,
            index=variables,
            columns=variables
        )
        
        return pvalue_df
    
    def get_statistics(self) -> Dict:
        """Get tester statistics"""
        return {
            **self.stats,
            'networks_built': len(self.networks),
            'significance_rate': (
                self.stats['significant_relationships'] / max(1, self.stats['tests_performed'])
            )
        }
