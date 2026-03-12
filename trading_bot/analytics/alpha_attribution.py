"""
Alpha Generation Attribution Module.

This module implements:
- Alpha source identification
- Strategy contribution analysis
- Factor attribution
- Skill vs luck decomposition
- Alpha decay analysis
- Performance attribution
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class AlphaSource(Enum):
    """Sources of alpha generation."""
    TIMING = "timing"  # Entry/exit timing
    SELECTION = "selection"  # Asset selection
    SIZING = "sizing"  # Position sizing
    RISK_MANAGEMENT = "risk_management"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    VOLATILITY = "volatility"
    CARRY = "carry"
    VALUE = "value"
    QUALITY = "quality"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"


class AttributionMethod(Enum):
    """Attribution methods."""
    BRINSON = "brinson"
    FACTOR = "factor"
    RETURNS_BASED = "returns_based"
    HOLDINGS_BASED = "holdings_based"


@dataclass
class AlphaContribution:
    """Contribution from an alpha source."""
    source: AlphaSource
    contribution: float  # In basis points or percent
    percentage_of_total: float
    consistency: float  # 0-1
    statistical_significance: float  # t-stat or p-value
    is_decaying: bool
    decay_rate: float  # If decaying


@dataclass
class StrategyAttribution:
    """Attribution for a strategy."""
    strategy_name: str
    total_return: float
    alpha: float
    beta: float
    benchmark_contribution: float
    active_return: float
    information_ratio: float
    tracking_error: float
    contributions: List[AlphaContribution]


@dataclass
class FactorExposure:
    """Exposure to a factor."""
    factor_name: str
    exposure: float  # Beta to factor
    contribution: float
    t_statistic: float
    r_squared: float


@dataclass
class SkillLuckDecomposition:
    """Decomposition of returns into skill and luck."""
    total_return: float
    skill_component: float
    luck_component: float
    skill_ratio: float  # Skill / Total
    confidence_interval: Tuple[float, float]
    sample_size: int
    is_statistically_significant: bool


@dataclass
class AlphaDecayAnalysis:
    """Analysis of alpha decay over time."""
    initial_alpha: float
    current_alpha: float
    decay_rate: float  # Per period
    half_life: float  # Periods until alpha halves
    is_significant_decay: bool
    projected_alpha: float  # Future projection
    recommendation: str


class AlphaCalculator:
    """
    Calculates alpha and related metrics.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        try:
            self.risk_free_rate = risk_free_rate
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_alpha_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """Calculate alpha and beta using regression."""
        # Align series
        try:
            common_idx = returns.index.intersection(benchmark_returns.index)
            r = returns.loc[common_idx].values
            b = benchmark_returns.loc[common_idx].values
        
            if len(r) < 10:
                return 0.0, 1.0
        
            # Simple linear regression
            cov = np.cov(r, b)
            beta = cov[0, 1] / (cov[1, 1] + 1e-10)
            alpha = np.mean(r) - beta * np.mean(b)
        
            # Annualize
            alpha_annual = alpha * 252
        
            return alpha_annual, beta
        except Exception as e:
            logger.error(f"Error in calculate_alpha_beta: {e}")
            raise
    
    def calculate_information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """Calculate Information Ratio."""
        try:
            active_returns = returns - benchmark_returns
        
            if active_returns.std() == 0:
                return 0.0
        
            return (active_returns.mean() / active_returns.std()) * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error in calculate_information_ratio: {e}")
            raise
    
    def calculate_tracking_error(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """Calculate Tracking Error."""
        try:
            active_returns = returns - benchmark_returns
            return active_returns.std() * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error in calculate_tracking_error: {e}")
            raise
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series
    ) -> float:
        """Calculate Sharpe Ratio."""
        try:
            excess_returns = returns - self.risk_free_rate / 252
        
            if returns.std() == 0:
                return 0.0
        
            return (excess_returns.mean() / returns.std()) * np.sqrt(252)
        except Exception as e:
            logger.error(f"Error in calculate_sharpe_ratio: {e}")
            raise


class BrinsonAttribution:
    """
    Brinson-Fachler attribution model.
    """
    
    def __init__(self):
        try:
            self.alpha_calc = AlphaCalculator()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_allocation_effect(
        self,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        sector_returns: Dict[str, float]
    ) -> float:
        """Calculate allocation effect (over/underweight sectors)."""
        try:
            allocation = 0.0
        
            for sector in portfolio_weights:
                port_weight = portfolio_weights.get(sector, 0)
                bench_weight = benchmark_weights.get(sector, 0)
                sector_return = sector_returns.get(sector, 0)
            
                allocation += (port_weight - bench_weight) * sector_return
        
            return allocation
        except Exception as e:
            logger.error(f"Error in calculate_allocation_effect: {e}")
            raise
    
    def calculate_selection_effect(
        self,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_returns: Dict[str, float]
    ) -> float:
        """Calculate selection effect (stock picking within sectors)."""
        try:
            selection = 0.0
        
            for sector in portfolio_weights:
                bench_weight = benchmark_weights.get(sector, 0)
                port_return = portfolio_returns.get(sector, 0)
                bench_return = benchmark_returns.get(sector, 0)
            
                selection += bench_weight * (port_return - bench_return)
        
            return selection
        except Exception as e:
            logger.error(f"Error in calculate_selection_effect: {e}")
            raise
    
    def calculate_interaction_effect(
        self,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_returns: Dict[str, float]
    ) -> float:
        """Calculate interaction effect."""
        try:
            interaction = 0.0
        
            for sector in portfolio_weights:
                port_weight = portfolio_weights.get(sector, 0)
                bench_weight = benchmark_weights.get(sector, 0)
                port_return = portfolio_returns.get(sector, 0)
                bench_return = benchmark_returns.get(sector, 0)
            
                interaction += (port_weight - bench_weight) * (port_return - bench_return)
        
            return interaction
        except Exception as e:
            logger.error(f"Error in calculate_interaction_effect: {e}")
            raise
    
    def full_attribution(
        self,
        portfolio_weights: Dict[str, float],
        benchmark_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_returns: Dict[str, float],
        sector_returns: Dict[str, float]
    ) -> Dict[str, float]:
        """Perform full Brinson attribution."""
        try:
            allocation = self.calculate_allocation_effect(
                portfolio_weights, benchmark_weights, sector_returns
            )
        
            selection = self.calculate_selection_effect(
                portfolio_weights, benchmark_weights,
                portfolio_returns, benchmark_returns
            )
        
            interaction = self.calculate_interaction_effect(
                portfolio_weights, benchmark_weights,
                portfolio_returns, benchmark_returns
            )
        
            total_active = allocation + selection + interaction
        
            return {
                'allocation_effect': allocation,
                'selection_effect': selection,
                'interaction_effect': interaction,
                'total_active_return': total_active
            }
        except Exception as e:
            logger.error(f"Error in full_attribution: {e}")
            raise


class FactorAttributor:
    """
    Factor-based attribution.
    """
    
    def __init__(self):
        try:
            self.alpha_calc = AlphaCalculator()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_factor_exposures(
        self,
        returns: pd.Series,
        factor_returns: Dict[str, pd.Series]
    ) -> List[FactorExposure]:
        """Calculate exposures to multiple factors."""
        try:
            exposures = []
        
            for factor_name, factor_ret in factor_returns.items():
                # Align series
                common_idx = returns.index.intersection(factor_ret.index)
                r = returns.loc[common_idx].values
                f = factor_ret.loc[common_idx].values
            
                if len(r) < 10:
                    continue
            
                # Calculate exposure (beta)
                cov = np.cov(r, f)
                exposure = cov[0, 1] / (cov[1, 1] + 1e-10)
            
                # Calculate contribution
                contribution = exposure * np.mean(f) * 252
            
                # Calculate t-statistic (simplified)
                n = len(r)
                se = np.std(r - exposure * f) / np.sqrt(n)
                t_stat = exposure / (se + 1e-10)
            
                # Calculate R-squared
                ss_res = np.sum((r - exposure * f) ** 2)
                ss_tot = np.sum((r - np.mean(r)) ** 2)
                r_squared = 1 - ss_res / (ss_tot + 1e-10)
            
                exposures.append(FactorExposure(
                    factor_name=factor_name,
                    exposure=exposure,
                    contribution=contribution,
                    t_statistic=t_stat,
                    r_squared=max(0, r_squared)
                ))
        
            return exposures
        except Exception as e:
            logger.error(f"Error in calculate_factor_exposures: {e}")
            raise
    
    def decompose_returns(
        self,
        returns: pd.Series,
        factor_returns: Dict[str, pd.Series]
    ) -> Dict[str, Any]:
        """Decompose returns into factor contributions."""
        try:
            exposures = self.calculate_factor_exposures(returns, factor_returns)
        
            total_factor_contribution = sum(e.contribution for e in exposures)
            total_return = returns.mean() * 252
        
            alpha = total_return - total_factor_contribution
        
            return {
                'total_return': total_return,
                'factor_contribution': total_factor_contribution,
                'alpha': alpha,
                'exposures': exposures,
                'explained_variance': sum(e.r_squared for e in exposures) / len(exposures) if exposures else 0
            }
        except Exception as e:
            logger.error(f"Error in decompose_returns: {e}")
            raise


class SkillLuckAnalyzer:
    """
    Analyzes skill vs luck in returns.
    """
    
    def __init__(self, simulations: int = 1000):
        try:
            self.simulations = simulations
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def decompose_skill_luck(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None
    ) -> SkillLuckDecomposition:
        """Decompose returns into skill and luck components."""
        try:
            if benchmark_returns is not None:
                active_returns = returns - benchmark_returns
            else:
                active_returns = returns
        
            n = len(active_returns)
            mean_return = active_returns.mean()
            std_return = active_returns.std()
        
            # Bootstrap to estimate confidence interval
            bootstrap_means = []
            for _ in range(self.simulations):
                sample = np.random.choice(active_returns, size=n, replace=True)
                bootstrap_means.append(np.mean(sample))
        
            ci_lower = np.percentile(bootstrap_means, 2.5)
            ci_upper = np.percentile(bootstrap_means, 97.5)
        
            # Skill is the consistent component (mean)
            # Luck is the random component (deviation from mean)
            skill_component = mean_return * 252  # Annualized
        
            # Estimate luck as the uncertainty
            luck_component = std_return * np.sqrt(252) / np.sqrt(n)
        
            # Calculate t-statistic for significance
            t_stat = mean_return / (std_return / np.sqrt(n) + 1e-10)
            is_significant = abs(t_stat) > 2.0
        
            total = abs(skill_component) + abs(luck_component)
            skill_ratio = abs(skill_component) / total if total > 0 else 0.5
        
            return SkillLuckDecomposition(
                total_return=mean_return * 252,
                skill_component=skill_component,
                luck_component=luck_component,
                skill_ratio=skill_ratio,
                confidence_interval=(ci_lower * 252, ci_upper * 252),
                sample_size=n,
                is_statistically_significant=is_significant
            )
        except Exception as e:
            logger.error(f"Error in decompose_skill_luck: {e}")
            raise


class AlphaDecayAnalyzer:
    """
    Analyzes alpha decay over time.
    """
    
    def __init__(self, window_size: int = 60):
        try:
            self.window_size = window_size
            self.alpha_calc = AlphaCalculator()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_rolling_alpha(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> pd.Series:
        """Calculate rolling alpha."""
        try:
            alphas = []
        
            for i in range(self.window_size, len(returns)):
                r = returns.iloc[i-self.window_size:i]
                b = benchmark_returns.iloc[i-self.window_size:i]
            
                alpha, _ = self.alpha_calc.calculate_alpha_beta(r, b)
                alphas.append(alpha)
        
            return pd.Series(alphas, index=returns.index[self.window_size:])
        except Exception as e:
            logger.error(f"Error in calculate_rolling_alpha: {e}")
            raise
    
    def analyze_decay(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> AlphaDecayAnalysis:
        """Analyze alpha decay."""
        try:
            rolling_alpha = self.calculate_rolling_alpha(returns, benchmark_returns)
        
            if len(rolling_alpha) < 10:
                return AlphaDecayAnalysis(
                    initial_alpha=0,
                    current_alpha=0,
                    decay_rate=0,
                    half_life=float('inf'),
                    is_significant_decay=False,
                    projected_alpha=0,
                    recommendation="Insufficient data"
                )
        
            initial_alpha = rolling_alpha.iloc[:10].mean()
            current_alpha = rolling_alpha.iloc[-10:].mean()
        
            # Calculate decay rate
            if initial_alpha != 0:
                total_decay = (current_alpha - initial_alpha) / initial_alpha
                periods = len(rolling_alpha)
                decay_rate = total_decay / periods if periods > 0 else 0
            else:
                decay_rate = 0
        
            # Calculate half-life
            if decay_rate < 0:
                half_life = -np.log(2) / decay_rate if decay_rate != 0 else float('inf')
            else:
                half_life = float('inf')
        
            # Check significance
            alpha_trend = np.polyfit(range(len(rolling_alpha)), rolling_alpha.values, 1)
            is_significant = abs(alpha_trend[0]) > rolling_alpha.std() / np.sqrt(len(rolling_alpha))
        
            # Project future alpha
            projected = current_alpha * (1 + decay_rate * 12)  # 12 periods ahead
        
            # Generate recommendation
            if decay_rate < -0.05:
                recommendation = "Significant alpha decay - review strategy"
            elif decay_rate < -0.02:
                recommendation = "Moderate alpha decay - monitor closely"
            elif decay_rate > 0.02:
                recommendation = "Alpha improving - consider increasing allocation"
            else:
                recommendation = "Alpha stable - maintain current approach"
        
            return AlphaDecayAnalysis(
                initial_alpha=initial_alpha,
                current_alpha=current_alpha,
                decay_rate=decay_rate,
                half_life=half_life,
                is_significant_decay=is_significant and decay_rate < 0,
                projected_alpha=projected,
                recommendation=recommendation
            )
        except Exception as e:
            logger.error(f"Error in analyze_decay: {e}")
            raise


class AlphaAttributionSystem:
    """
    Complete alpha attribution system.
    """
    
    def __init__(self):
        try:
            self.alpha_calc = AlphaCalculator()
            self.brinson = BrinsonAttribution()
            self.factor_attr = FactorAttributor()
            self.skill_luck = SkillLuckAnalyzer()
            self.decay_analyzer = AlphaDecayAnalyzer()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def full_attribution(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series,
        factor_returns: Optional[Dict[str, pd.Series]] = None
    ) -> Dict[str, Any]:
        """Perform full alpha attribution."""
        # Basic alpha/beta
        try:
            alpha, beta = self.alpha_calc.calculate_alpha_beta(returns, benchmark_returns)
            ir = self.alpha_calc.calculate_information_ratio(returns, benchmark_returns)
            te = self.alpha_calc.calculate_tracking_error(returns, benchmark_returns)
            sharpe = self.alpha_calc.calculate_sharpe_ratio(returns)
        
            # Factor attribution
            if factor_returns:
                factor_decomp = self.factor_attr.decompose_returns(returns, factor_returns)
            else:
                factor_decomp = None
        
            # Skill vs luck
            skill_luck_decomp = self.skill_luck.decompose_skill_luck(returns, benchmark_returns)
        
            # Alpha decay
            decay_analysis = self.decay_analyzer.analyze_decay(returns, benchmark_returns)
        
            return {
                'alpha': alpha,
                'beta': beta,
                'information_ratio': ir,
                'tracking_error': te,
                'sharpe_ratio': sharpe,
                'factor_decomposition': factor_decomp,
                'skill_luck': {
                    'skill_component': skill_luck_decomp.skill_component,
                    'luck_component': skill_luck_decomp.luck_component,
                    'skill_ratio': skill_luck_decomp.skill_ratio,
                    'is_significant': skill_luck_decomp.is_statistically_significant
                },
                'alpha_decay': {
                    'initial_alpha': decay_analysis.initial_alpha,
                    'current_alpha': decay_analysis.current_alpha,
                    'decay_rate': decay_analysis.decay_rate,
                    'half_life': decay_analysis.half_life,
                    'recommendation': decay_analysis.recommendation
                }
            }
        except Exception as e:
            logger.error(f"Error in full_attribution: {e}")
            raise
    
    def identify_alpha_sources(
        self,
        trade_data: pd.DataFrame
    ) -> List[AlphaContribution]:
        """Identify sources of alpha from trade data."""
        try:
            contributions = []
        
            # This would require detailed trade data analysis
            # Simplified implementation
        
            if 'timing_pnl' in trade_data.columns:
                timing_contrib = trade_data['timing_pnl'].sum()
                contributions.append(AlphaContribution(
                    source=AlphaSource.TIMING,
                    contribution=timing_contrib,
                    percentage_of_total=0,  # Calculate later
                    consistency=0.5,
                    statistical_significance=0,
                    is_decaying=False,
                    decay_rate=0
                ))
        
            if 'selection_pnl' in trade_data.columns:
                selection_contrib = trade_data['selection_pnl'].sum()
                contributions.append(AlphaContribution(
                    source=AlphaSource.SELECTION,
                    contribution=selection_contrib,
                    percentage_of_total=0,
                    consistency=0.5,
                    statistical_significance=0,
                    is_decaying=False,
                    decay_rate=0
                ))
        
            # Calculate percentages
            total = sum(abs(c.contribution) for c in contributions)
            for c in contributions:
                c.percentage_of_total = abs(c.contribution) / total if total > 0 else 0
        
            return contributions
        except Exception as e:
            logger.error(f"Error in identify_alpha_sources: {e}")
            raise


# Convenience functions
def calculate_alpha(
    returns: pd.Series,
    benchmark_returns: pd.Series
) -> Dict[str, float]:
    """Quick alpha calculation."""
    try:
        calc = AlphaCalculator()
        alpha, beta = calc.calculate_alpha_beta(returns, benchmark_returns)
        ir = calc.calculate_information_ratio(returns, benchmark_returns)
    
        return {
            'alpha': alpha,
            'beta': beta,
            'information_ratio': ir
        }
    except Exception as e:
        logger.error(f"Error in calculate_alpha: {e}")
        raise


def decompose_skill_luck(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """Decompose returns into skill and luck."""
    try:
        analyzer = SkillLuckAnalyzer()
        result = analyzer.decompose_skill_luck(returns, benchmark_returns)
    
        return {
            'skill_component': result.skill_component,
            'luck_component': result.luck_component,
            'skill_ratio': result.skill_ratio,
            'is_significant': result.is_statistically_significant,
            'confidence_interval': result.confidence_interval
        }
    except Exception as e:
        logger.error(f"Error in decompose_skill_luck: {e}")
        raise


def analyze_alpha_decay(
    returns: pd.Series,
    benchmark_returns: pd.Series
) -> Dict[str, Any]:
    """Analyze alpha decay."""
    try:
        analyzer = AlphaDecayAnalyzer()
        result = analyzer.analyze_decay(returns, benchmark_returns)
    
        return {
            'initial_alpha': result.initial_alpha,
            'current_alpha': result.current_alpha,
            'decay_rate': result.decay_rate,
            'half_life': result.half_life,
            'is_decaying': result.is_significant_decay,
            'recommendation': result.recommendation
        }
    except Exception as e:
        logger.error(f"Error in analyze_alpha_decay: {e}")
        raise
