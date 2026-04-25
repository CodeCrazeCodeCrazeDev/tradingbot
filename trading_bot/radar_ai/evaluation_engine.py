"""
Evaluation Engine - Comprehensive Assessment of Strategies and Decisions
=========================================================================

Evaluates trading strategies, risk, performance, and confidence:
- Strategy Evaluator: Multi-dimensional strategy assessment
- Risk Assessor: Comprehensive risk analysis
- Performance Analyzer: Attribution and benchmarking
- Confidence Calibrator: Ensuring predictions are well-calibrated
"""

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


class StrategyRating(Enum):
    """Strategy quality ratings"""
    EXCEPTIONAL = "exceptional"  # Top tier
    STRONG = "strong"           # Above average
    ADEQUATE = "adequate"       # Acceptable
    WEAK = "weak"              # Below average
    POOR = "poor"              # Unacceptable


class RiskLevel(Enum):
    """Risk level classifications"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class StrategyEvaluation:
    """Comprehensive strategy evaluation"""
    evaluation_id: str
    strategy_name: str
    timestamp: datetime
    overall_rating: StrategyRating
    overall_score: float  # 0-100
    
    # Component scores
    return_score: float
    risk_score: float
    consistency_score: float
    robustness_score: float
    capacity_score: float
    
    # Metrics
    metrics: Dict[str, float]
    
    # Insights
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'evaluation_id': self.evaluation_id,
            'strategy_name': self.strategy_name,
            'timestamp': self.timestamp.isoformat(),
            'overall_rating': self.overall_rating.value,
            'overall_score': self.overall_score,
            'component_scores': {
                'return': self.return_score,
                'risk': self.risk_score,
                'consistency': self.consistency_score,
                'robustness': self.robustness_score,
                'capacity': self.capacity_score,
            },
            'metrics': self.metrics,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
        }


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    assessment_id: str
    timestamp: datetime
    overall_risk_level: RiskLevel
    risk_score: float  # 0-100
    
    # Risk components
    market_risk: float
    liquidity_risk: float
    concentration_risk: float
    volatility_risk: float
    tail_risk: float
    correlation_risk: float
    
    # Risk metrics
    var_95: float
    var_99: float
    cvar_95: float
    max_drawdown: float
    
    # Warnings and recommendations
    warnings: List[str]
    mitigations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_risk_level': self.overall_risk_level.value,
            'risk_score': self.risk_score,
            'risk_components': {
                'market': self.market_risk,
                'liquidity': self.liquidity_risk,
                'concentration': self.concentration_risk,
                'volatility': self.volatility_risk,
                'tail': self.tail_risk,
                'correlation': self.correlation_risk,
            },
            'risk_metrics': {
                'var_95': self.var_95,
                'var_99': self.var_99,
                'cvar_95': self.cvar_95,
                'max_drawdown': self.max_drawdown,
            },
            'warnings': self.warnings,
            'mitigations': self.mitigations,
        }


@dataclass
class PerformanceAttribution:
    """Performance attribution analysis"""
    attribution_id: str
    timestamp: datetime
    period: str
    
    # Total return decomposition
    total_return: float
    benchmark_return: float
    alpha: float
    
    # Attribution factors
    factor_contributions: Dict[str, float]
    sector_contributions: Dict[str, float]
    timing_contribution: float
    selection_contribution: float
    
    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    information_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'attribution_id': self.attribution_id,
            'timestamp': self.timestamp.isoformat(),
            'period': self.period,
            'returns': {
                'total': self.total_return,
                'benchmark': self.benchmark_return,
                'alpha': self.alpha,
            },
            'attribution': {
                'factors': self.factor_contributions,
                'sectors': self.sector_contributions,
                'timing': self.timing_contribution,
                'selection': self.selection_contribution,
            },
            'risk_adjusted': {
                'sharpe': self.sharpe_ratio,
                'sortino': self.sortino_ratio,
                'information_ratio': self.information_ratio,
            },
        }


@dataclass
class CalibrationResult:
    """Confidence calibration result"""
    calibration_id: str
    timestamp: datetime
    
    # Calibration metrics
    brier_score: float
    calibration_error: float
    resolution: float
    reliability: float
    
    # Calibration curve
    predicted_probabilities: List[float]
    actual_frequencies: List[float]
    
    # Recommendations
    is_well_calibrated: bool
    adjustment_needed: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'calibration_id': self.calibration_id,
            'timestamp': self.timestamp.isoformat(),
            'metrics': {
                'brier_score': self.brier_score,
                'calibration_error': self.calibration_error,
                'resolution': self.resolution,
                'reliability': self.reliability,
            },
            'calibration_curve': {
                'predicted': self.predicted_probabilities,
                'actual': self.actual_frequencies,
            },
            'is_well_calibrated': self.is_well_calibrated,
            'adjustment_needed': self.adjustment_needed,
        }


class StrategyEvaluator:
    """
    Comprehensive strategy evaluation system.
    
    Evaluates strategies across multiple dimensions:
    - Returns: Absolute and risk-adjusted
    - Risk: Downside and tail risk
    - Consistency: Performance stability
    - Robustness: Sensitivity to parameters
    - Capacity: Scalability
    """
    
    def __init__(self):
        self.evaluation_history: List[StrategyEvaluation] = []
        self.benchmark_returns = 0.08  # Default annual benchmark
    
    async def evaluate_strategy(
        self,
        strategy_name: str,
        returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StrategyEvaluation:
        """Perform comprehensive strategy evaluation"""
        if not returns:
            raise ValueError("Returns data required for evaluation")
        
        metadata = metadata or {}
        
        # Calculate return metrics
        return_metrics = self._calculate_return_metrics(returns, benchmark_returns)
        return_score = self._score_returns(return_metrics)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(returns)
        risk_score = self._score_risk(risk_metrics)
        
        # Calculate consistency
        consistency_metrics = self._calculate_consistency(returns)
        consistency_score = self._score_consistency(consistency_metrics)
        
        # Calculate robustness (simplified)
        robustness_score = self._estimate_robustness(returns, metadata)
        
        # Calculate capacity (simplified)
        capacity_score = self._estimate_capacity(metadata)
        
        # Overall score (weighted average)
        weights = {'return': 0.30, 'risk': 0.25, 'consistency': 0.20, 'robustness': 0.15, 'capacity': 0.10}
        overall_score = (
            return_score * weights['return'] +
            risk_score * weights['risk'] +
            consistency_score * weights['consistency'] +
            robustness_score * weights['robustness'] +
            capacity_score * weights['capacity']
        )
        
        # Determine rating
        if overall_score >= 80:
            rating = StrategyRating.EXCEPTIONAL
        elif overall_score >= 65:
            rating = StrategyRating.STRONG
        elif overall_score >= 50:
            rating = StrategyRating.ADEQUATE
        elif overall_score >= 35:
            rating = StrategyRating.WEAK
        else:
            rating = StrategyRating.POOR
        
        # Generate insights
        strengths, weaknesses, recommendations = self._generate_insights(
            return_score, risk_score, consistency_score, robustness_score, capacity_score,
            return_metrics, risk_metrics
        )
        
        # Combine all metrics
        all_metrics = {**return_metrics, **risk_metrics, **consistency_metrics}
        
        evaluation = StrategyEvaluation(
            evaluation_id=f"EVAL-{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            timestamp=datetime.now(timezone.utc),
            overall_rating=rating,
            overall_score=overall_score,
            return_score=return_score,
            risk_score=risk_score,
            consistency_score=consistency_score,
            robustness_score=robustness_score,
            capacity_score=capacity_score,
            metrics=all_metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
        
        self.evaluation_history.append(evaluation)
        return evaluation
    
    def _calculate_return_metrics(
        self,
        returns: List[float],
        benchmark: Optional[List[float]] = None,
    ) -> Dict[str, float]:
        """Calculate return-related metrics"""
        n = len(returns)
        
        # Total and average return
        total_return = math.prod(1 + r for r in returns) - 1
        avg_return = sum(returns) / n
        
        # Annualized return (assuming daily returns)
        annual_return = (1 + total_return) ** (252 / n) - 1 if n > 0 else 0
        
        # Benchmark comparison
        if benchmark and len(benchmark) == n:
            benchmark_total = math.prod(1 + r for r in benchmark) - 1
            alpha = total_return - benchmark_total
        else:
            benchmark_total = self.benchmark_returns * (n / 252)
            alpha = total_return - benchmark_total
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'avg_daily_return': avg_return,
            'benchmark_return': benchmark_total,
            'alpha': alpha,
        }
    
    def _calculate_risk_metrics(self, returns: List[float]) -> Dict[str, float]:
        """Calculate risk-related metrics"""
        n = len(returns)
        if n < 2:
            return {'volatility': 0, 'sharpe': 0, 'sortino': 0, 'max_drawdown': 0}
        
        # Volatility
        avg = sum(returns) / n
        variance = sum((r - avg) ** 2 for r in returns) / (n - 1)
        volatility = math.sqrt(variance)
        annual_vol = volatility * math.sqrt(252)
        
        # Sharpe ratio
        risk_free = 0.04 / 252  # Daily risk-free rate
        excess_return = avg - risk_free
        sharpe = (excess_return / volatility * math.sqrt(252)) if volatility > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_var = sum(r ** 2 for r in downside_returns) / len(downside_returns)
            downside_dev = math.sqrt(downside_var)
            sortino = (excess_return / downside_dev * math.sqrt(252)) if downside_dev > 0 else 0
        else:
            sortino = sharpe * 1.5  # No downside, estimate higher
        
        # Maximum drawdown
        cumulative = [1.0]
        for r in returns:
            cumulative.append(cumulative[-1] * (1 + r))
        
        peak = cumulative[0]
        max_dd = 0
        for value in cumulative:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        
        return {
            'volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_dd,
        }
    
    def _calculate_consistency(self, returns: List[float]) -> Dict[str, float]:
        """Calculate consistency metrics"""
        n = len(returns)
        if n < 20:
            return {'win_rate': 0.5, 'profit_factor': 1.0, 'consistency_score': 50}
        
        # Win rate
        wins = sum(1 for r in returns if r > 0)
        win_rate = wins / n
        
        # Profit factor
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 10
        
        # Monthly consistency (assuming 21 trading days per month)
        monthly_returns = []
        for i in range(0, n, 21):
            month = returns[i:i+21]
            if month:
                monthly_returns.append(sum(month))
        
        if monthly_returns:
            positive_months = sum(1 for m in monthly_returns if m > 0)
            monthly_win_rate = positive_months / len(monthly_returns)
        else:
            monthly_win_rate = win_rate
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'monthly_win_rate': monthly_win_rate,
        }
    
    def _score_returns(self, metrics: Dict[str, float]) -> float:
        """Score return metrics (0-100)"""
        annual_return = metrics.get('annual_return', 0)
        alpha = metrics.get('alpha', 0)
        
        # Score based on absolute and relative performance
        return_score = min(100, max(0, 50 + annual_return * 200))
        alpha_score = min(100, max(0, 50 + alpha * 300))
        
        return (return_score + alpha_score) / 2
    
    def _score_risk(self, metrics: Dict[str, float]) -> float:
        """Score risk metrics (0-100, higher is better/lower risk)"""
        sharpe = metrics.get('sharpe_ratio', 0)
        sortino = metrics.get('sortino_ratio', 0)
        max_dd = metrics.get('max_drawdown', 0)
        
        # Sharpe score
        sharpe_score = min(100, max(0, sharpe * 30 + 40))
        
        # Sortino score
        sortino_score = min(100, max(0, sortino * 25 + 40))
        
        # Drawdown score (lower is better)
        dd_score = max(0, 100 - max_dd * 300)
        
        return (sharpe_score + sortino_score + dd_score) / 3
    
    def _score_consistency(self, metrics: Dict[str, float]) -> float:
        """Score consistency metrics (0-100)"""
        win_rate = metrics.get('win_rate', 0.5)
        profit_factor = metrics.get('profit_factor', 1.0)
        monthly_wr = metrics.get('monthly_win_rate', 0.5)
        
        wr_score = win_rate * 100
        pf_score = min(100, profit_factor * 30)
        monthly_score = monthly_wr * 100
        
        return (wr_score + pf_score + monthly_score) / 3
    
    def _estimate_robustness(self, returns: List[float], metadata: Dict[str, Any]) -> float:
        """Estimate strategy robustness"""
        # Check for parameter sensitivity (simplified)
        num_parameters = metadata.get('num_parameters', 5)
        lookback_period = metadata.get('lookback_period', 20)
        
        # More parameters = less robust
        param_penalty = min(30, num_parameters * 3)
        
        # Shorter lookback = less robust
        lookback_bonus = min(20, lookback_period / 5)
        
        # Check return stability
        if len(returns) >= 60:
            first_half = returns[:len(returns)//2]
            second_half = returns[len(returns)//2:]
            
            avg1 = sum(first_half) / len(first_half)
            avg2 = sum(second_half) / len(second_half)
            
            stability = 1 - min(1, abs(avg1 - avg2) / max(abs(avg1), abs(avg2), 0.001))
            stability_score = stability * 40
        else:
            stability_score = 20
        
        return max(0, min(100, 50 - param_penalty + lookback_bonus + stability_score))
    
    def _estimate_capacity(self, metadata: Dict[str, Any]) -> float:
        """Estimate strategy capacity"""
        # Factors affecting capacity
        avg_volume = metadata.get('avg_volume', 1000000)
        holding_period = metadata.get('holding_period_days', 1)
        num_positions = metadata.get('num_positions', 10)
        
        # Higher volume = more capacity
        volume_score = min(40, math.log10(avg_volume + 1) * 5)
        
        # Longer holding = more capacity
        holding_score = min(30, holding_period * 3)
        
        # More positions = more capacity (diversification)
        position_score = min(30, num_positions * 2)
        
        return volume_score + holding_score + position_score
    
    def _generate_insights(
        self,
        return_score: float,
        risk_score: float,
        consistency_score: float,
        robustness_score: float,
        capacity_score: float,
        return_metrics: Dict[str, float],
        risk_metrics: Dict[str, float],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate insights from evaluation"""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Return insights
        if return_score >= 70:
            strengths.append(f"Strong returns: {return_metrics.get('annual_return', 0):.1%} annually")
        elif return_score < 40:
            weaknesses.append(f"Weak returns: {return_metrics.get('annual_return', 0):.1%} annually")
            recommendations.append("Review signal generation for higher alpha")
        
        # Risk insights
        if risk_score >= 70:
            strengths.append(f"Excellent risk-adjusted returns: Sharpe {risk_metrics.get('sharpe_ratio', 0):.2f}")
        elif risk_score < 40:
            weaknesses.append(f"Poor risk management: Max DD {risk_metrics.get('max_drawdown', 0):.1%}")
            recommendations.append("Implement tighter stop-losses or position sizing")
        
        # Consistency insights
        if consistency_score >= 70:
            strengths.append("Highly consistent performance across periods")
        elif consistency_score < 40:
            weaknesses.append("Inconsistent returns, high variance")
            recommendations.append("Consider regime-based position sizing")
        
        # Robustness insights
        if robustness_score >= 70:
            strengths.append("Robust to parameter changes")
        elif robustness_score < 40:
            weaknesses.append("Sensitive to parameter choices (potential overfitting)")
            recommendations.append("Reduce model complexity or use ensemble methods")
        
        # Capacity insights
        if capacity_score >= 70:
            strengths.append("High capacity for scaling")
        elif capacity_score < 40:
            weaknesses.append("Limited capacity for larger positions")
            recommendations.append("Consider longer holding periods or more liquid instruments")
        
        return strengths, weaknesses, recommendations


class RiskAssessor:
    """
    Comprehensive risk assessment system.
    
    Evaluates multiple dimensions of risk:
    - Market risk
    - Liquidity risk
    - Concentration risk
    - Volatility risk
    - Tail risk
    - Correlation risk
    """
    
    def __init__(self):
        self.risk_thresholds = {
            'var_95': 0.02,
            'max_drawdown': 0.15,
            'concentration': 0.25,
            'volatility': 0.25,
        }
    
    async def assess_risk(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        positions = portfolio.get('positions', [])
        total_value = sum(p.get('value', 0) for p in positions)
        
        # Calculate individual risk components
        market_risk = self._calculate_market_risk(positions, market_data)
        liquidity_risk = self._calculate_liquidity_risk(positions, market_data)
        concentration_risk = self._calculate_concentration_risk(positions, total_value)
        volatility_risk = self._calculate_volatility_risk(positions, market_data)
        tail_risk = self._calculate_tail_risk(positions, market_data)
        correlation_risk = self._calculate_correlation_risk(positions, market_data)
        
        # Calculate VaR metrics
        var_95, var_99, cvar_95 = self._calculate_var_metrics(positions, market_data, total_value)
        
        # Calculate max drawdown potential
        max_dd = self._estimate_max_drawdown(positions, market_data)
        
        # Overall risk score (0-100, higher = more risk)
        risk_score = (
            market_risk * 0.25 +
            liquidity_risk * 0.15 +
            concentration_risk * 0.15 +
            volatility_risk * 0.20 +
            tail_risk * 0.15 +
            correlation_risk * 0.10
        )
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = RiskLevel.EXTREME
        elif risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MODERATE
        elif risk_score >= 20:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.MINIMAL
        
        # Generate warnings and mitigations
        warnings, mitigations = self._generate_risk_insights(
            market_risk, liquidity_risk, concentration_risk,
            volatility_risk, tail_risk, correlation_risk,
            var_95, max_dd, total_value
        )
        
        return RiskAssessment(
            assessment_id=f"RISK-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            overall_risk_level=risk_level,
            risk_score=risk_score,
            market_risk=market_risk,
            liquidity_risk=liquidity_risk,
            concentration_risk=concentration_risk,
            volatility_risk=volatility_risk,
            tail_risk=tail_risk,
            correlation_risk=correlation_risk,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            warnings=warnings,
            mitigations=mitigations,
        )
    
    def _calculate_market_risk(self, positions: List[Dict], market_data: Dict) -> float:
        """Calculate market risk score"""
        if not positions:
            return 0
        
        # Beta-weighted exposure
        total_beta = 0
        total_value = sum(p.get('value', 0) for p in positions)
        
        for pos in positions:
            beta = pos.get('beta', 1.0)
            value = pos.get('value', 0)
            weight = value / total_value if total_value > 0 else 0
            total_beta += beta * weight
        
        # Market volatility
        market_vol = market_data.get('market_volatility', 0.15)
        
        # Risk score
        return min(100, total_beta * market_vol * 200)
    
    def _calculate_liquidity_risk(self, positions: List[Dict], market_data: Dict) -> float:
        """Calculate liquidity risk score"""
        if not positions:
            return 0
        
        liquidity_scores = []
        for pos in positions:
            avg_volume = pos.get('avg_volume', 1000000)
            position_size = pos.get('shares', 0)
            
            # Days to liquidate
            days_to_liquidate = position_size / (avg_volume * 0.1) if avg_volume > 0 else 100
            
            # Score (more days = higher risk)
            score = min(100, days_to_liquidate * 10)
            liquidity_scores.append(score)
        
        return sum(liquidity_scores) / len(liquidity_scores) if liquidity_scores else 0
    
    def _calculate_concentration_risk(self, positions: List[Dict], total_value: float) -> float:
        """Calculate concentration risk score"""
        if not positions or total_value <= 0:
            return 0
        
        # Calculate position weights
        weights = [p.get('value', 0) / total_value for p in positions]
        
        # Herfindahl-Hirschman Index
        hhi = sum(w ** 2 for w in weights)
        
        # Max position weight
        max_weight = max(weights) if weights else 0
        
        # Score (higher concentration = higher risk)
        hhi_score = hhi * 100
        max_weight_score = max_weight * 100
        
        return (hhi_score + max_weight_score) / 2
    
    def _calculate_volatility_risk(self, positions: List[Dict], market_data: Dict) -> float:
        """Calculate volatility risk score"""
        if not positions:
            return 0
        
        # Portfolio volatility
        portfolio_vol = market_data.get('portfolio_volatility', 0.15)
        
        # Compare to historical
        historical_vol = market_data.get('historical_volatility', 0.15)
        vol_ratio = portfolio_vol / historical_vol if historical_vol > 0 else 1
        
        # Score
        base_score = min(100, portfolio_vol * 200)
        ratio_adjustment = (vol_ratio - 1) * 20
        
        return min(100, max(0, base_score + ratio_adjustment))
    
    def _calculate_tail_risk(self, positions: List[Dict], market_data: Dict) -> float:
        """Calculate tail risk score"""
        # Simplified tail risk based on skewness and kurtosis
        skewness = market_data.get('return_skewness', 0)
        kurtosis = market_data.get('return_kurtosis', 3)
        
        # Negative skew = more tail risk
        skew_risk = max(0, -skewness * 20)
        
        # Excess kurtosis = more tail risk
        kurt_risk = max(0, (kurtosis - 3) * 10)
        
        return min(100, skew_risk + kurt_risk + 20)  # Base tail risk
    
    def _calculate_correlation_risk(self, positions: List[Dict], market_data: Dict) -> float:
        """Calculate correlation risk score"""
        # Average pairwise correlation
        avg_correlation = market_data.get('avg_correlation', 0.3)
        
        # Higher correlation = less diversification = more risk
        return min(100, avg_correlation * 100)
    
    def _calculate_var_metrics(
        self,
        positions: List[Dict],
        market_data: Dict,
        total_value: float,
    ) -> Tuple[float, float, float]:
        """Calculate VaR and CVaR metrics"""
        portfolio_vol = market_data.get('portfolio_volatility', 0.15)
        
        # Parametric VaR (assuming normal distribution)
        var_95 = total_value * portfolio_vol * 1.645 / math.sqrt(252)
        var_99 = total_value * portfolio_vol * 2.326 / math.sqrt(252)
        
        # CVaR approximation
        cvar_95 = var_95 * 1.25  # Simplified
        
        return var_95, var_99, cvar_95
    
    def _estimate_max_drawdown(self, positions: List[Dict], market_data: Dict) -> float:
        """Estimate potential maximum drawdown"""
        portfolio_vol = market_data.get('portfolio_volatility', 0.15)
        
        # Empirical relationship: max DD ≈ 2-3x annual volatility
        estimated_max_dd = portfolio_vol * 2.5
        
        return min(1.0, estimated_max_dd)
    
    def _generate_risk_insights(
        self,
        market_risk: float,
        liquidity_risk: float,
        concentration_risk: float,
        volatility_risk: float,
        tail_risk: float,
        correlation_risk: float,
        var_95: float,
        max_dd: float,
        total_value: float,
    ) -> Tuple[List[str], List[str]]:
        """Generate risk warnings and mitigations"""
        warnings = []
        mitigations = []
        
        if market_risk > 60:
            warnings.append(f"High market exposure: Consider reducing beta")
            mitigations.append("Add hedges or reduce equity allocation")
        
        if liquidity_risk > 60:
            warnings.append("Liquidity concerns: Some positions may be difficult to exit")
            mitigations.append("Reduce position sizes in illiquid names")
        
        if concentration_risk > 60:
            warnings.append("High concentration: Portfolio lacks diversification")
            mitigations.append("Spread exposure across more positions")
        
        if volatility_risk > 60:
            warnings.append("Elevated volatility: Expect larger swings")
            mitigations.append("Reduce position sizes or add volatility hedges")
        
        if tail_risk > 60:
            warnings.append("Significant tail risk: Large losses possible")
            mitigations.append("Consider tail hedges (puts, VIX calls)")
        
        if var_95 / total_value > 0.03:
            warnings.append(f"Daily VaR exceeds 3% of portfolio")
            mitigations.append("Review overall risk budget")
        
        if max_dd > 0.20:
            warnings.append(f"Potential max drawdown: {max_dd:.1%}")
            mitigations.append("Implement drawdown-based position sizing")
        
        return warnings, mitigations


class PerformanceAnalyzer:
    """
    Performance attribution and analysis system.
    
    Decomposes returns into:
    - Factor contributions
    - Sector contributions
    - Timing vs selection
    """
    
    def __init__(self):
        self.factor_exposures = ['market', 'size', 'value', 'momentum', 'quality', 'volatility']
    
    async def analyze_performance(
        self,
        returns: List[float],
        benchmark_returns: List[float],
        positions: List[Dict[str, Any]],
        period: str = "YTD",
    ) -> PerformanceAttribution:
        """Perform comprehensive performance attribution"""
        if not returns or not benchmark_returns:
            raise ValueError("Returns data required")
        
        n = min(len(returns), len(benchmark_returns))
        returns = returns[:n]
        benchmark_returns = benchmark_returns[:n]
        
        # Total returns
        total_return = math.prod(1 + r for r in returns) - 1
        benchmark_total = math.prod(1 + r for r in benchmark_returns) - 1
        alpha = total_return - benchmark_total
        
        # Factor attribution (simplified)
        factor_contributions = self._attribute_to_factors(returns, positions)
        
        # Sector attribution (simplified)
        sector_contributions = self._attribute_to_sectors(returns, positions)
        
        # Timing vs selection
        timing, selection = self._decompose_timing_selection(returns, benchmark_returns, positions)
        
        # Risk-adjusted metrics
        sharpe = self._calculate_sharpe(returns)
        sortino = self._calculate_sortino(returns)
        info_ratio = self._calculate_information_ratio(returns, benchmark_returns)
        
        return PerformanceAttribution(
            attribution_id=f"PERF-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            period=period,
            total_return=total_return,
            benchmark_return=benchmark_total,
            alpha=alpha,
            factor_contributions=factor_contributions,
            sector_contributions=sector_contributions,
            timing_contribution=timing,
            selection_contribution=selection,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            information_ratio=info_ratio,
        )
    
    def _attribute_to_factors(self, returns: List[float], positions: List[Dict]) -> Dict[str, float]:
        """Attribute returns to factors"""
        # Simplified factor attribution
        total_return = sum(returns)
        
        contributions = {}
        for factor in self.factor_exposures:
            # Estimate factor contribution based on position characteristics
            factor_exposure = sum(p.get(f'{factor}_exposure', 0) for p in positions) / max(len(positions), 1)
            contributions[factor] = total_return * factor_exposure * 0.1  # Simplified
        
        # Residual
        explained = sum(contributions.values())
        contributions['residual'] = total_return - explained
        
        return contributions
    
    def _attribute_to_sectors(self, returns: List[float], positions: List[Dict]) -> Dict[str, float]:
        """Attribute returns to sectors"""
        sector_returns = {}
        
        for pos in positions:
            sector = pos.get('sector', 'Other')
            pos_return = pos.get('return', 0)
            weight = pos.get('weight', 0)
            
            if sector not in sector_returns:
                sector_returns[sector] = 0
            sector_returns[sector] += pos_return * weight
        
        return sector_returns
    
    def _decompose_timing_selection(
        self,
        returns: List[float],
        benchmark: List[float],
        positions: List[Dict],
    ) -> Tuple[float, float]:
        """Decompose alpha into timing and selection"""
        # Simplified Brinson attribution
        total_alpha = sum(returns) - sum(benchmark)
        
        # Estimate timing (being in/out of market at right times)
        timing = total_alpha * 0.3  # Simplified
        
        # Selection (picking right securities)
        selection = total_alpha * 0.7  # Simplified
        
        return timing, selection
    
    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0
        
        avg = sum(returns) / len(returns)
        rf = 0.04 / 252
        excess = avg - rf
        
        variance = sum((r - avg) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(variance)
        
        return (excess / std * math.sqrt(252)) if std > 0 else 0
    
    def _calculate_sortino(self, returns: List[float]) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0
        
        avg = sum(returns) / len(returns)
        rf = 0.04 / 252
        excess = avg - rf
        
        downside = [r for r in returns if r < 0]
        if not downside:
            return self._calculate_sharpe(returns) * 1.5
        
        downside_var = sum(r ** 2 for r in downside) / len(downside)
        downside_std = math.sqrt(downside_var)
        
        return (excess / downside_std * math.sqrt(252)) if downside_std > 0 else 0
    
    def _calculate_information_ratio(self, returns: List[float], benchmark: List[float]) -> float:
        """Calculate Information Ratio"""
        if len(returns) < 2 or len(benchmark) < 2:
            return 0
        
        n = min(len(returns), len(benchmark))
        active_returns = [returns[i] - benchmark[i] for i in range(n)]
        
        avg_active = sum(active_returns) / n
        variance = sum((r - avg_active) ** 2 for r in active_returns) / (n - 1)
        tracking_error = math.sqrt(variance)
        
        return (avg_active / tracking_error * math.sqrt(252)) if tracking_error > 0 else 0


class ConfidenceCalibrator:
    """
    Ensures predictions are well-calibrated.
    
    A well-calibrated model means:
    - When it predicts 70% probability, the event occurs 70% of the time
    """
    
    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins
        self.prediction_history: List[Tuple[float, bool]] = []
    
    def record_prediction(self, predicted_probability: float, actual_outcome: bool):
        """Record a prediction and its outcome"""
        self.prediction_history.append((predicted_probability, actual_outcome))
        
        # Trim history
        if len(self.prediction_history) > 10000:
            self.prediction_history = self.prediction_history[-5000:]
    
    async def calibrate(self) -> CalibrationResult:
        """Analyze calibration of predictions"""
        if len(self.prediction_history) < 50:
            return CalibrationResult(
                calibration_id=f"CAL-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc),
                brier_score=0.25,
                calibration_error=0,
                resolution=0,
                reliability=0,
                predicted_probabilities=[],
                actual_frequencies=[],
                is_well_calibrated=False,
                adjustment_needed="Insufficient data for calibration",
            )
        
        # Bin predictions
        bins = [[] for _ in range(self.num_bins)]
        
        for prob, outcome in self.prediction_history:
            bin_idx = min(int(prob * self.num_bins), self.num_bins - 1)
            bins[bin_idx].append((prob, outcome))
        
        # Calculate calibration curve
        predicted_probs = []
        actual_freqs = []
        
        for i, bin_data in enumerate(bins):
            if bin_data:
                avg_pred = sum(p for p, _ in bin_data) / len(bin_data)
                actual_freq = sum(1 for _, o in bin_data if o) / len(bin_data)
                predicted_probs.append(avg_pred)
                actual_freqs.append(actual_freq)
        
        # Brier score
        brier = sum((p - (1 if o else 0)) ** 2 for p, o in self.prediction_history) / len(self.prediction_history)
        
        # Calibration error (ECE)
        calibration_error = 0
        total_samples = len(self.prediction_history)
        
        for i, bin_data in enumerate(bins):
            if bin_data:
                bin_weight = len(bin_data) / total_samples
                avg_pred = sum(p for p, _ in bin_data) / len(bin_data)
                actual_freq = sum(1 for _, o in bin_data if o) / len(bin_data)
                calibration_error += bin_weight * abs(avg_pred - actual_freq)
        
        # Resolution and reliability (simplified)
        base_rate = sum(1 for _, o in self.prediction_history if o) / len(self.prediction_history)
        resolution = sum((f - base_rate) ** 2 for f in actual_freqs) / len(actual_freqs) if actual_freqs else 0
        reliability = calibration_error
        
        # Determine if well-calibrated
        is_calibrated = calibration_error < 0.1
        
        # Adjustment recommendation
        if calibration_error < 0.05:
            adjustment = "Well calibrated, no adjustment needed"
        elif calibration_error < 0.1:
            adjustment = "Minor calibration drift, consider Platt scaling"
        elif calibration_error < 0.2:
            adjustment = "Moderate miscalibration, apply isotonic regression"
        else:
            adjustment = "Severe miscalibration, review model fundamentally"
        
        return CalibrationResult(
            calibration_id=f"CAL-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            brier_score=brier,
            calibration_error=calibration_error,
            resolution=resolution,
            reliability=reliability,
            predicted_probabilities=predicted_probs,
            actual_frequencies=actual_freqs,
            is_well_calibrated=is_calibrated,
            adjustment_needed=adjustment,
        )
    
    def adjust_probability(self, raw_probability: float) -> float:
        """Adjust probability based on historical calibration"""
        if len(self.prediction_history) < 100:
            return raw_probability
        
        # Simple linear adjustment based on historical bias
        predictions = [p for p, _ in self.prediction_history]
        outcomes = [1 if o else 0 for _, o in self.prediction_history]
        
        avg_pred = sum(predictions) / len(predictions)
        avg_outcome = sum(outcomes) / len(outcomes)
        
        # Bias correction
        bias = avg_pred - avg_outcome
        adjusted = raw_probability - bias * 0.5  # Partial correction
        
        return max(0, min(1, adjusted))


class EvaluationEngine:
    """
    Master evaluation engine coordinating all assessment modules.
    """
    
    def __init__(self):
        self.engine_id = f"EVAL-{uuid.uuid4().hex[:8]}"
        self.strategy_evaluator = StrategyEvaluator()
        self.risk_assessor = RiskAssessor()
        self.performance_analyzer = PerformanceAnalyzer()
        self.confidence_calibrator = ConfidenceCalibrator()
        
        logger.info(f"EvaluationEngine initialized: {self.engine_id}")
    
    async def comprehensive_evaluation(
        self,
        strategy_name: str,
        returns: List[float],
        benchmark_returns: List[float],
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Perform comprehensive evaluation"""
        # Strategy evaluation
        strategy_eval = await self.strategy_evaluator.evaluate_strategy(
            strategy_name=strategy_name,
            returns=returns,
            benchmark_returns=benchmark_returns,
        )
        
        # Risk assessment
        risk_assessment = await self.risk_assessor.assess_risk(
            portfolio=portfolio,
            market_data=market_data,
        )
        
        # Performance attribution
        performance = await self.performance_analyzer.analyze_performance(
            returns=returns,
            benchmark_returns=benchmark_returns,
            positions=portfolio.get('positions', []),
        )
        
        # Calibration
        calibration = await self.confidence_calibrator.calibrate()
        
        return {
            'strategy_evaluation': strategy_eval.to_dict(),
            'risk_assessment': risk_assessment.to_dict(),
            'performance_attribution': performance.to_dict(),
            'calibration': calibration.to_dict(),
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'engine_id': self.engine_id,
            'evaluations_performed': len(self.strategy_evaluator.evaluation_history),
            'predictions_tracked': len(self.confidence_calibrator.prediction_history),
        }
