import logging
logger = logging.getLogger(__name__)
"""Market Context Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
import scipy.stats as stats
import numpy
import pandas


class IntermarketAnalysis:
    """Analyze relationships between different markets."""
    
    def __init__(self):
        try:
            self.correlations = {}
            self.market_data = {}
            logger.info("Initialized IntermarketAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_correlation_matrix(self, data: Dict[str, pd.Series], 
                                   window: int = 30) -> pd.DataFrame:
        """Calculate rolling correlation matrix between markets."""
        try:
            df = pd.DataFrame(data)
            correlations = df.rolling(window=window).corr()
            return correlations
        except Exception as e:
            logger.error(f"Error in calculate_correlation_matrix: {e}")
            raise
    
    def detect_divergences(self, primary_market: pd.Series, 
                          secondary_market: pd.Series, 
                          threshold: float = 0.3) -> List[Dict]:
        """Detect divergences between related markets."""
        # Calculate correlation
        try:
            correlation = primary_market.rolling(30).corr(secondary_market)
        
            # Find periods where correlation breaks down
            divergences = []
            for i, corr in enumerate(correlation):
                if abs(corr) < threshold and not np.isnan(corr):
                    divergences.append({
                        'timestamp': correlation.index[i],
                        'correlation': corr,
                        'primary_value': primary_market.iloc[i],
                        'secondary_value': secondary_market.iloc[i]
                    })
        
            return divergences
        except Exception as e:
            logger.error(f"Error in detect_divergences: {e}")
            raise
    
    def analyze_sector_rotation(self, sector_data: Dict[str, pd.Series]) -> Dict:
        """Analyze sector rotation patterns."""
        # Calculate relative strength
        try:
            relative_strength = {}
            for sector, data in sector_data.items():
                returns = data.pct_change()
                relative_strength[sector] = returns.rolling(20).mean()
        
            # Find leading and lagging sectors
            latest_rs = {sector: rs.iloc[-1] for sector, rs in relative_strength.items()}
            sorted_sectors = sorted(latest_rs.items(), key=lambda x: x[1], reverse=True)
        
            return {
                'leading_sectors': sorted_sectors[:3],
                'lagging_sectors': sorted_sectors[-3:],
                'relative_strength': relative_strength
            }
        except Exception as e:
            logger.error(f"Error in analyze_sector_rotation: {e}")
            raise


class LiquidityAnalysis:
    """Analyze market liquidity conditions."""
    
    def __init__(self):
        try:
            self.liquidity_metrics = {}
            logger.info("Initialized LiquidityAnalysis")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_bid_ask_spread(self, bid_prices: pd.Series, 
                                ask_prices: pd.Series) -> pd.Series:
        """Calculate bid-ask spread as liquidity measure."""
        try:
            spread = ask_prices - bid_prices
            relative_spread = spread / ((bid_prices + ask_prices) / 2)
            return relative_spread
        except Exception as e:
            logger.error(f"Error in calculate_bid_ask_spread: {e}")
            raise
    
    def analyze_volume_profile(self, prices: pd.Series, 
                              volumes: pd.Series, 
                              bins: int = 20) -> Dict:
        """Analyze volume profile to identify liquidity zones."""
        # Create price bins
        try:
            price_min, price_max = prices.min(), prices.max()
            price_bins = np.linspace(price_min, price_max, bins)
        
            # Assign volumes to price bins
            volume_profile = {}
            for i in range(len(price_bins) - 1):
                mask = (prices >= price_bins[i]) & (prices < price_bins[i + 1])
                volume_profile[f"{price_bins[i]:.4f}-{price_bins[i+1]:.4f}"] = volumes[mask].sum()
        
            # Find high volume nodes (liquidity zones)
            sorted_profile = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        
            return {
                'volume_profile': volume_profile,
                'high_volume_nodes': sorted_profile[:5],
                'low_volume_nodes': sorted_profile[-5:]
            }
        except Exception as e:
            logger.error(f"Error in analyze_volume_profile: {e}")
            raise
    
    def detect_liquidity_gaps(self, prices: pd.Series, 
                             volumes: pd.Series, 
                             threshold: float = 0.5) -> List[Dict]:
        """Detect liquidity gaps (areas with low volume)."""
        # Calculate volume-weighted average price
        try:
            vwap = (prices * volumes).cumsum() / volumes.cumsum()
        
            # Find areas where volume is significantly below average
            avg_volume = volumes.rolling(20).mean()
            low_volume_mask = volumes < (avg_volume * threshold)
        
            gaps = []
            for i, is_gap in enumerate(low_volume_mask):
                if is_gap and not pd.isna(is_gap):
                    gaps.append({
                        'timestamp': prices.index[i],
                        'price': prices.iloc[i],
                        'volume': volumes.iloc[i],
                        'avg_volume': avg_volume.iloc[i],
                        'vwap': vwap.iloc[i]
                    })
        
            return gaps
        except Exception as e:
            logger.error(f"Error in detect_liquidity_gaps: {e}")
            raise


class RiskIndicators:
    """Calculate various risk indicators for market context."""
    
    def __init__(self):
        try:
            self.risk_metrics = {}
            logger.info("Initialized RiskIndicators")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.05) -> float:
        """Calculate Value at Risk."""
        return np.percentile(returns.dropna(), confidence * 100)
    
    def calculate_expected_shortfall(self, returns: pd.Series, 
                                   confidence: float = 0.05) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        try:
            var = self.calculate_var(returns, confidence)
            return returns[returns <= var].mean()
        except Exception as e:
            logger.error(f"Error in calculate_expected_shortfall: {e}")
            raise
    
    def calculate_maximum_drawdown(self, prices: pd.Series) -> Dict:
        """Calculate maximum drawdown and related metrics."""
        # Calculate cumulative returns
        try:
            cumulative = (1 + prices.pct_change()).cumprod()
        
            # Calculate running maximum
            running_max = cumulative.expanding().max()
        
            # Calculate drawdown
            drawdown = (cumulative - running_max) / running_max
        
            # Find maximum drawdown
            max_dd = drawdown.min()
            max_dd_date = drawdown.idxmin()
        
            # Find recovery date
            recovery_date = None
            if max_dd_date in drawdown.index:
                post_dd = drawdown[drawdown.index > max_dd_date]
                recovery_mask = post_dd >= 0
                if recovery_mask.any():
                    recovery_date = post_dd[recovery_mask].index[0]
        
            return {
                'max_drawdown': max_dd,
                'max_drawdown_date': max_dd_date,
                'recovery_date': recovery_date,
                'drawdown_series': drawdown
            }
        except Exception as e:
            logger.error(f"Error in calculate_maximum_drawdown: {e}")
            raise
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                              risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        try:
            excess_returns = returns.mean() - risk_free_rate / 252  # Daily risk-free rate
            return excess_returns / returns.std() if returns.std() != 0 else 0
        except Exception as e:
            logger.error(f"Error in calculate_sharpe_ratio: {e}")
            raise
    
    def calculate_sortino_ratio(self, returns: pd.Series, 
                               risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        try:
            excess_returns = returns.mean() - risk_free_rate / 252
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
            return excess_returns / downside_std if downside_std != 0 else 0
        except Exception as e:
            logger.error(f"Error in calculate_sortino_ratio: {e}")
            raise
    
    def calculate_beta(self, asset_returns: pd.Series, 
                      market_returns: pd.Series) -> float:
        """Calculate beta relative to market."""
        try:
            covariance = np.cov(asset_returns.dropna(), market_returns.dropna())[0, 1]
            market_variance = np.var(market_returns.dropna())
            return covariance / market_variance if market_variance != 0 else 0
        except Exception as e:
            logger.error(f"Error in calculate_beta: {e}")
            raise
    
    def calculate_risk_adjusted_returns(self, prices: pd.Series, 
                                      market_prices: pd.Series = None) -> Dict:
        """Calculate comprehensive risk-adjusted return metrics."""
        try:
            returns = prices.pct_change().dropna()
        
            metrics = {
                'total_return': (prices.iloc[-1] / prices.iloc[0]) - 1,
                'annualized_return': returns.mean() * 252,
                'annualized_volatility': returns.std() * np.sqrt(252),
                'sharpe_ratio': self.calculate_sharpe_ratio(returns),
                'sortino_ratio': self.calculate_sortino_ratio(returns),
                'var_5pct': self.calculate_var(returns, 0.05),
                'expected_shortfall': self.calculate_expected_shortfall(returns, 0.05),
                'max_drawdown': self.calculate_maximum_drawdown(prices)['max_drawdown']
            }
        
            if market_prices is not None:
                market_returns = market_prices.pct_change().dropna()
                metrics['beta'] = self.calculate_beta(returns, market_returns)
            
                # Calculate alpha
                risk_free_rate = 0.02 / 252  # Daily risk-free rate
                expected_return = risk_free_rate + metrics['beta'] * (market_returns.mean() - risk_free_rate)
                metrics['alpha'] = returns.mean() - expected_return
        
            return metrics
        except Exception as e:
            logger.error(f"Error in calculate_risk_adjusted_returns: {e}")
            raise
    
    def detect_regime_changes(self, returns: pd.Series, 
                             window: int = 60) -> pd.Series:
        """Detect volatility regime changes."""
        # Calculate rolling volatility
        try:
            rolling_vol = returns.rolling(window=window).std()
        
            # Calculate volatility of volatility
            vol_of_vol = rolling_vol.rolling(window=window).std()
        
            # Detect regime changes using statistical tests
            regime_changes = pd.Series(index=returns.index, dtype=bool)
        
            for i in range(window * 2, len(returns)):
                # Get two windows of volatility data
                vol1 = rolling_vol.iloc[i-window*2:i-window]
                vol2 = rolling_vol.iloc[i-window:i]
            
                # Perform statistical test for difference in means
                if len(vol1) > 0 and len(vol2) > 0:
                    statistic, p_value = stats.ttest_ind(vol1.dropna(), vol2.dropna())
                    regime_changes.iloc[i] = p_value < 0.05
        
            return regime_changes
        except Exception as e:
            logger.error(f"Error in detect_regime_changes: {e}")
            raise
    
    def calculate_market_stress_indicator(self, price_data: Dict[str, pd.Series]) -> pd.Series:
        """Calculate a composite market stress indicator."""
        try:
            stress_components = {}
        
            for symbol, prices in price_data.items():
                returns = prices.pct_change()
            
                # Calculate individual stress components
                volatility = returns.rolling(20).std()
                skewness = returns.rolling(60).skew()
                kurtosis = returns.rolling(60).kurt()
            
                # Normalize components
                vol_norm = (volatility - volatility.rolling(252).mean()) / volatility.rolling(252).std()
                skew_norm = (skewness - skewness.rolling(252).mean()) / skewness.rolling(252).std()
                kurt_norm = (kurtosis - kurtosis.rolling(252).mean()) / kurtosis.rolling(252).std()
            
                # Combine into stress indicator
                stress_components[symbol] = vol_norm + abs(skew_norm) + kurt_norm
        
            # Average across all symbols
            stress_df = pd.DataFrame(stress_components)
            market_stress = stress_df.mean(axis=1)
        
            return market_stress
        except Exception as e:
            logger.error(f"Error in calculate_market_stress_indicator: {e}")
            raise
