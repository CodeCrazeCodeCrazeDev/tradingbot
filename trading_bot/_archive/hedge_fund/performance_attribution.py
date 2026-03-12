"""
Performance Attribution System
==============================
Institutional-grade performance attribution:
- Brinson Attribution (allocation, selection, interaction)
- Factor Attribution (Fama-French, Carhart, custom)
- Risk-Adjusted Metrics (Sharpe, Sortino, Information Ratio)
- Peer Comparison
- Benchmark Tracking
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    from scipy import stats
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AttributionMethod(Enum):
    """Attribution methodologies"""
    BRINSON = "brinson"
    FACTOR = "factor"
    RETURNS_BASED = "returns_based"
    HOLDINGS_BASED = "holdings_based"
    TRANSACTION_BASED = "transaction_based"


class BenchmarkType(Enum):
    """Benchmark types"""
    MARKET_INDEX = "market_index"
    PEER_GROUP = "peer_group"
    CUSTOM = "custom"
    ABSOLUTE = "absolute"


@dataclass
class BrinsonAttribution:
    """Brinson attribution results"""
    period_start: date
    period_end: date
    portfolio_return: float
    benchmark_return: float
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    total_active_return: float
    sector_attribution: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': f"{self.period_start} to {self.period_end}",
            'portfolio_return': f"{self.portfolio_return * 100:.2f}%",
            'benchmark_return': f"{self.benchmark_return * 100:.2f}%",
            'allocation_effect': f"{self.allocation_effect * 100:.2f}%",
            'selection_effect': f"{self.selection_effect * 100:.2f}%",
            'interaction_effect': f"{self.interaction_effect * 100:.2f}%",
            'total_active_return': f"{self.total_active_return * 100:.2f}%",
            'sector_attribution': {
                k: {kk: f"{vv*100:.2f}%" for kk, vv in v.items()}
                for k, v in self.sector_attribution.items()
            }
        }


@dataclass
class FactorAttribution:
    """Factor attribution results"""
    period_start: date
    period_end: date
    total_return: float
    factor_returns: Dict[str, float]
    factor_exposures: Dict[str, float]
    factor_contributions: Dict[str, float]
    specific_return: float
    r_squared: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': f"{self.period_start} to {self.period_end}",
            'total_return': f"{self.total_return * 100:.2f}%",
            'factor_contributions': {
                k: f"{v * 100:.2f}%" for k, v in self.factor_contributions.items()
            },
            'specific_return': f"{self.specific_return * 100:.2f}%",
            'r_squared': f"{self.r_squared * 100:.1f}%"
        }


@dataclass
class RiskAdjustedMetrics:
    """Risk-adjusted performance metrics"""
    period_start: date
    period_end: date
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    treynor_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    omega_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': f"{self.period_start} to {self.period_end}",
            'total_return': f"{self.total_return * 100:.2f}%",
            'annualized_return': f"{self.annualized_return * 100:.2f}%",
            'volatility': f"{self.volatility * 100:.2f}%",
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'calmar_ratio': round(self.calmar_ratio, 2),
            'information_ratio': round(self.information_ratio, 2),
            'treynor_ratio': round(self.treynor_ratio, 2),
            'max_drawdown': f"{self.max_drawdown * 100:.2f}%",
            'var_95': f"{self.var_95 * 100:.2f}%",
            'cvar_95': f"{self.cvar_95 * 100:.2f}%",
            'omega_ratio': round(self.omega_ratio, 2)
        }


@dataclass
class PeerComparison:
    """Peer group comparison"""
    fund_name: str
    peer_group: str
    period: str
    fund_return: float
    peer_median: float
    peer_mean: float
    percentile_rank: float
    quartile: int
    num_peers: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fund_name': self.fund_name,
            'peer_group': self.peer_group,
            'period': self.period,
            'fund_return': f"{self.fund_return * 100:.2f}%",
            'peer_median': f"{self.peer_median * 100:.2f}%",
            'percentile_rank': f"{self.percentile_rank:.0f}th",
            'quartile': self.quartile,
            'num_peers': self.num_peers
        }


class BenchmarkTracker:
    """
    Benchmark Tracking System
    Tracks performance against various benchmarks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Benchmarks
        self.benchmarks: Dict[str, Dict[str, Any]] = {}
        
        # Default benchmarks
        self._setup_default_benchmarks()
        
        # Tracking history
        self.tracking_history: List[Dict[str, Any]] = []
        
        logger.info("Benchmark Tracker initialized")
    
    def _setup_default_benchmarks(self):
        """Setup default benchmarks"""
        self.benchmarks = {
            'SPY': {
                'name': 'S&P 500',
                'type': BenchmarkType.MARKET_INDEX,
                'returns': []
            },
            'QQQ': {
                'name': 'NASDAQ 100',
                'type': BenchmarkType.MARKET_INDEX,
                'returns': []
            },
            'IWM': {
                'name': 'Russell 2000',
                'type': BenchmarkType.MARKET_INDEX,
                'returns': []
            },
            'AGG': {
                'name': 'US Aggregate Bond',
                'type': BenchmarkType.MARKET_INDEX,
                'returns': []
            },
            'HFRI': {
                'name': 'HFRI Fund Weighted',
                'type': BenchmarkType.PEER_GROUP,
                'returns': []
            },
            'ABSOLUTE_8': {
                'name': '8% Absolute Return',
                'type': BenchmarkType.ABSOLUTE,
                'target_return': 0.08
            }
        }
    
    def add_benchmark(
        self,
        benchmark_id: str,
        name: str,
        benchmark_type: BenchmarkType,
        returns: Optional[List[float]] = None,
        target_return: Optional[float] = None
    ):
        """Add a benchmark"""
        self.benchmarks[benchmark_id] = {
            'name': name,
            'type': benchmark_type,
            'returns': returns or [],
            'target_return': target_return
        }
    
    def update_benchmark_returns(
        self,
        benchmark_id: str,
        returns: List[float]
    ):
        """Update benchmark returns"""
        if benchmark_id in self.benchmarks:
            self.benchmarks[benchmark_id]['returns'] = returns
    
    def calculate_tracking_error(
        self,
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """Calculate tracking error"""
        if not NUMPY_AVAILABLE:
            return 0.0
        
        active_returns = portfolio_returns - benchmark_returns
        tracking_error = np.std(active_returns) * np.sqrt(252)
        return tracking_error
    
    def calculate_information_ratio(
        self,
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """Calculate information ratio"""
        if not NUMPY_AVAILABLE:
            return 0.0
        
        active_returns = portfolio_returns - benchmark_returns
        active_return_ann = np.mean(active_returns) * 252
        tracking_error = np.std(active_returns) * np.sqrt(252)
        
        if tracking_error == 0:
            return 0.0
        
        return active_return_ann / tracking_error
    
    def get_benchmark_comparison(
        self,
        portfolio_returns: np.ndarray,
        benchmark_id: str
    ) -> Dict[str, Any]:
        """Compare portfolio to benchmark"""
        if benchmark_id not in self.benchmarks:
            return {}
        
        benchmark = self.benchmarks[benchmark_id]
        
        if benchmark['type'] == BenchmarkType.ABSOLUTE:
            # Compare to absolute return target
            target = benchmark.get('target_return', 0.08)
            portfolio_ann = np.mean(portfolio_returns) * 252 if NUMPY_AVAILABLE else 0
            
            return {
                'benchmark': benchmark['name'],
                'target_return': f"{target * 100:.1f}%",
                'portfolio_return': f"{portfolio_ann * 100:.2f}%",
                'excess_return': f"{(portfolio_ann - target) * 100:.2f}%",
                'meets_target': portfolio_ann >= target
            }
        
        benchmark_returns = np.array(benchmark['returns'])
        
        if len(benchmark_returns) == 0 or len(portfolio_returns) == 0:
            return {}
        
        # Align lengths
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        port_ret = portfolio_returns[-min_len:]
        bench_ret = benchmark_returns[-min_len:]
        
        tracking_error = self.calculate_tracking_error(port_ret, bench_ret)
        info_ratio = self.calculate_information_ratio(port_ret, bench_ret)
        
        port_total = np.prod(1 + port_ret) - 1 if NUMPY_AVAILABLE else 0
        bench_total = np.prod(1 + bench_ret) - 1 if NUMPY_AVAILABLE else 0
        
        return {
            'benchmark': benchmark['name'],
            'portfolio_return': f"{port_total * 100:.2f}%",
            'benchmark_return': f"{bench_total * 100:.2f}%",
            'active_return': f"{(port_total - bench_total) * 100:.2f}%",
            'tracking_error': f"{tracking_error * 100:.2f}%",
            'information_ratio': round(info_ratio, 2)
        }


class PerformanceAttributor:
    """
    Master Performance Attribution System
    Comprehensive performance analysis and attribution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Benchmark tracker
        self.benchmark_tracker = BenchmarkTracker(config.get('benchmarks', {}))
        
        # Risk-free rate
        self.risk_free_rate = config.get('risk_free_rate', 0.05)  # 5%
        
        # Attribution history
        self.brinson_history: List[BrinsonAttribution] = []
        self.factor_history: List[FactorAttribution] = []
        self.metrics_history: List[RiskAdjustedMetrics] = []
        
        logger.info("Performance Attributor initialized")
    
    def calculate_brinson_attribution(
        self,
        portfolio_weights: Dict[str, float],
        portfolio_returns: Dict[str, float],
        benchmark_weights: Dict[str, float],
        benchmark_returns: Dict[str, float],
        sector_mapping: Dict[str, str],
        period_start: date,
        period_end: date
    ) -> BrinsonAttribution:
        """Calculate Brinson attribution"""
        # Group by sector
        sectors = set(sector_mapping.values())
        
        sector_attribution = {}
        total_allocation = 0
        total_selection = 0
        total_interaction = 0
        
        for sector in sectors:
            # Get securities in sector
            sector_securities = [s for s, sec in sector_mapping.items() if sec == sector]
            
            # Portfolio sector weight and return
            port_sector_weight = sum(portfolio_weights.get(s, 0) for s in sector_securities)
            port_sector_return = sum(
                portfolio_weights.get(s, 0) * portfolio_returns.get(s, 0)
                for s in sector_securities
            ) / port_sector_weight if port_sector_weight > 0 else 0
            
            # Benchmark sector weight and return
            bench_sector_weight = sum(benchmark_weights.get(s, 0) for s in sector_securities)
            bench_sector_return = sum(
                benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0)
                for s in sector_securities
            ) / bench_sector_weight if bench_sector_weight > 0 else 0
            
            # Total benchmark return
            total_bench_return = sum(
                benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0)
                for s in benchmark_weights
            )
            
            # Brinson effects
            allocation = (port_sector_weight - bench_sector_weight) * (bench_sector_return - total_bench_return)
            selection = bench_sector_weight * (port_sector_return - bench_sector_return)
            interaction = (port_sector_weight - bench_sector_weight) * (port_sector_return - bench_sector_return)
            
            sector_attribution[sector] = {
                'allocation': allocation,
                'selection': selection,
                'interaction': interaction,
                'total': allocation + selection + interaction
            }
            
            total_allocation += allocation
            total_selection += selection
            total_interaction += interaction
        
        # Total returns
        portfolio_total = sum(
            portfolio_weights.get(s, 0) * portfolio_returns.get(s, 0)
            for s in portfolio_weights
        )
        benchmark_total = sum(
            benchmark_weights.get(s, 0) * benchmark_returns.get(s, 0)
            for s in benchmark_weights
        )
        
        result = BrinsonAttribution(
            period_start=period_start,
            period_end=period_end,
            portfolio_return=portfolio_total,
            benchmark_return=benchmark_total,
            allocation_effect=total_allocation,
            selection_effect=total_selection,
            interaction_effect=total_interaction,
            total_active_return=portfolio_total - benchmark_total,
            sector_attribution=sector_attribution
        )
        
        self.brinson_history.append(result)
        return result
    
    def calculate_factor_attribution(
        self,
        portfolio_returns: np.ndarray,
        factor_returns: Dict[str, np.ndarray],
        period_start: date,
        period_end: date
    ) -> FactorAttribution:
        """Calculate factor-based attribution"""
        if not NUMPY_AVAILABLE:
            return FactorAttribution(
                period_start=period_start,
                period_end=period_end,
                total_return=0,
                factor_returns={},
                factor_exposures={},
                factor_contributions={},
                specific_return=0,
                r_squared=0
            )
        
        # Build factor matrix
        factors = list(factor_returns.keys())
        n_obs = len(portfolio_returns)
        
        X = np.column_stack([factor_returns[f][:n_obs] for f in factors])
        X = np.column_stack([np.ones(n_obs), X])  # Add intercept
        
        y = portfolio_returns[:n_obs]
        
        # OLS regression
        try:
            betas, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        except Exception:
            betas = np.zeros(len(factors) + 1)
            residuals = y
        
        # Extract results
        alpha = betas[0]
        factor_exposures = {factors[i]: betas[i+1] for i in range(len(factors))}
        
        # Factor contributions
        factor_contributions = {}
        for i, factor in enumerate(factors):
            factor_mean = np.mean(factor_returns[factor][:n_obs])
            factor_contributions[factor] = betas[i+1] * factor_mean
        
        # R-squared
        ss_res = np.sum((y - X @ betas) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        
        # Total return
        total_return = np.prod(1 + y) - 1
        
        # Specific return (alpha)
        specific_return = alpha * n_obs  # Cumulative alpha
        
        result = FactorAttribution(
            period_start=period_start,
            period_end=period_end,
            total_return=total_return,
            factor_returns={f: np.mean(factor_returns[f][:n_obs]) * 252 for f in factors},
            factor_exposures=factor_exposures,
            factor_contributions=factor_contributions,
            specific_return=specific_return,
            r_squared=r_squared
        )
        
        self.factor_history.append(result)
        return result
    
    def calculate_risk_adjusted_metrics(
        self,
        returns: np.ndarray,
        benchmark_returns: Optional[np.ndarray] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> RiskAdjustedMetrics:
        """Calculate comprehensive risk-adjusted metrics"""
        if not NUMPY_AVAILABLE or len(returns) == 0:
            return RiskAdjustedMetrics(
                period_start=period_start or date.today(),
                period_end=period_end or date.today(),
                total_return=0, annualized_return=0, volatility=0,
                sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                information_ratio=0, treynor_ratio=0, max_drawdown=0,
                var_95=0, cvar_95=0, omega_ratio=1
            )
        
        # Basic metrics
        total_return = np.prod(1 + returns) - 1
        n_periods = len(returns)
        annualized_return = (1 + total_return) ** (252 / n_periods) - 1 if n_periods > 0 else 0
        volatility = np.std(returns) * np.sqrt(252)
        
        # Sharpe Ratio
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_vol = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
        sortino_ratio = excess_return / downside_vol
        
        # Max Drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        max_drawdown = abs(np.min(drawdowns))
        
        # Calmar Ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Information Ratio
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            min_len = min(len(returns), len(benchmark_returns))
            active_returns = returns[:min_len] - benchmark_returns[:min_len]
            active_return_ann = np.mean(active_returns) * 252
            tracking_error = np.std(active_returns) * np.sqrt(252)
            information_ratio = active_return_ann / tracking_error if tracking_error > 0 else 0
            
            # Beta and Treynor
            covariance = np.cov(returns[:min_len], benchmark_returns[:min_len])[0, 1]
            benchmark_var = np.var(benchmark_returns[:min_len])
            beta = covariance / benchmark_var if benchmark_var > 0 else 1
            treynor_ratio = excess_return / beta if beta != 0 else 0
        else:
            information_ratio = 0
            treynor_ratio = 0
        
        # VaR and CVaR
        var_95 = abs(np.percentile(returns, 5))
        cvar_95 = abs(np.mean(returns[returns <= np.percentile(returns, 5)]))
        
        # Omega Ratio
        threshold = 0  # MAR = 0
        gains = returns[returns > threshold] - threshold
        losses = threshold - returns[returns <= threshold]
        omega_ratio = np.sum(gains) / np.sum(losses) if np.sum(losses) > 0 else float('inf')
        
        result = RiskAdjustedMetrics(
            period_start=period_start or date.today() - timedelta(days=n_periods),
            period_end=period_end or date.today(),
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            information_ratio=information_ratio,
            treynor_ratio=treynor_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            omega_ratio=min(omega_ratio, 10)  # Cap for display
        )
        
        self.metrics_history.append(result)
        return result
    
    def calculate_peer_comparison(
        self,
        fund_return: float,
        peer_returns: List[float],
        fund_name: str,
        peer_group: str,
        period: str
    ) -> PeerComparison:
        """Compare fund to peer group"""
        if not NUMPY_AVAILABLE or len(peer_returns) == 0:
            return PeerComparison(
                fund_name=fund_name,
                peer_group=peer_group,
                period=period,
                fund_return=fund_return,
                peer_median=0,
                peer_mean=0,
                percentile_rank=50,
                quartile=2,
                num_peers=0
            )
        
        peer_array = np.array(peer_returns)
        
        # Calculate percentile rank
        percentile_rank = stats.percentileofscore(peer_array, fund_return)
        
        # Determine quartile
        if percentile_rank >= 75:
            quartile = 1
        elif percentile_rank >= 50:
            quartile = 2
        elif percentile_rank >= 25:
            quartile = 3
        else:
            quartile = 4
        
        return PeerComparison(
            fund_name=fund_name,
            peer_group=peer_group,
            period=period,
            fund_return=fund_return,
            peer_median=np.median(peer_array),
            peer_mean=np.mean(peer_array),
            percentile_rank=percentile_rank,
            quartile=quartile,
            num_peers=len(peer_returns)
        )
    
    def generate_performance_report(
        self,
        returns: np.ndarray,
        positions: Dict[str, Dict[str, Any]],
        benchmark_returns: Optional[np.ndarray] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        period_start = period_start or date.today() - timedelta(days=len(returns))
        period_end = period_end or date.today()
        
        report = {
            'report_date': datetime.now().isoformat(),
            'period': f"{period_start} to {period_end}",
            'risk_adjusted_metrics': None,
            'benchmark_comparisons': {},
            'attribution': {},
            'summary': {}
        }
        
        # Risk-adjusted metrics
        metrics = self.calculate_risk_adjusted_metrics(
            returns, benchmark_returns, period_start, period_end
        )
        report['risk_adjusted_metrics'] = metrics.to_dict()
        
        # Benchmark comparisons
        for bench_id in self.benchmark_tracker.benchmarks:
            comparison = self.benchmark_tracker.get_benchmark_comparison(
                returns, bench_id
            )
            if comparison:
                report['benchmark_comparisons'][bench_id] = comparison
        
        # Summary
        report['summary'] = {
            'total_return': f"{metrics.total_return * 100:.2f}%",
            'annualized_return': f"{metrics.annualized_return * 100:.2f}%",
            'sharpe_ratio': round(metrics.sharpe_ratio, 2),
            'max_drawdown': f"{metrics.max_drawdown * 100:.2f}%",
            'volatility': f"{metrics.volatility * 100:.2f}%"
        }
        
        return report
    
    def get_attribution_summary(self) -> Dict[str, Any]:
        """Get attribution summary"""
        return {
            'brinson_analyses': len(self.brinson_history),
            'factor_analyses': len(self.factor_history),
            'metrics_calculations': len(self.metrics_history),
            'benchmarks_tracked': len(self.benchmark_tracker.benchmarks),
            'latest_metrics': self.metrics_history[-1].to_dict() if self.metrics_history else None
        }
