"""
Growth Optimization Framework.

This module implements:
- Equity curve optimization
- Compound growth analysis
- Drawdown recovery optimization
- Position sizing for growth
- Risk-adjusted growth metrics
- Growth trajectory analysis
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


class GrowthPhase(Enum):
    """Phases of equity growth."""
    ACCELERATION = "acceleration"
    STEADY = "steady"
    DECELERATION = "deceleration"
    DRAWDOWN = "drawdown"
    RECOVERY = "recovery"
    STAGNATION = "stagnation"


class OptimizationGoal(Enum):
    """Optimization goals."""
    MAX_GROWTH = "max_growth"
    RISK_ADJUSTED = "risk_adjusted"
    DRAWDOWN_CONTROL = "drawdown_control"
    CONSISTENCY = "consistency"
    COMPOUND_OPTIMAL = "compound_optimal"


@dataclass
class GrowthMetrics:
    """Growth performance metrics."""
    total_return: float
    cagr: float  # Compound Annual Growth Rate
    monthly_return_avg: float
    monthly_return_std: float
    best_month: float
    worst_month: float
    positive_months: int
    negative_months: int
    current_streak: int  # Positive or negative
    longest_win_streak: int
    longest_loss_streak: int
    growth_factor: float  # Final / Initial
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DrawdownMetrics:
    """Drawdown analysis metrics."""
    current_drawdown: float
    max_drawdown: float
    avg_drawdown: float
    drawdown_duration: int  # Days
    max_drawdown_duration: int
    recovery_factor: float  # Profit / Max DD
    ulcer_index: float
    pain_index: float
    calmar_ratio: float


@dataclass
class OptimizationResult:
    """Result of growth optimization."""
    optimal_risk_per_trade: float
    optimal_position_sizing: str
    expected_cagr: float
    expected_max_drawdown: float
    kelly_fraction: float
    recommended_adjustments: List[str]
    confidence: float


@dataclass
class GrowthProjection:
    """Future growth projection."""
    target_equity: float
    time_to_target: int  # Days
    probability: float
    best_case: float
    worst_case: float
    median_case: float
    required_monthly_return: float


class EquityCurveAnalyzer:
    """
    Analyzes equity curve for growth patterns.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        try:
            self.risk_free_rate = risk_free_rate
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate returns from equity curve."""
        return equity_curve.pct_change().dropna()
    
    def calculate_cagr(
        self,
        equity_curve: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Compound Annual Growth Rate."""
        try:
            if len(equity_curve) < 2:
                return 0.0
        
            total_return = equity_curve.iloc[-1] / equity_curve.iloc[0]
            n_periods = len(equity_curve)
            years = n_periods / periods_per_year
        
            if years <= 0 or total_return <= 0:
                return 0.0
        
            cagr = (total_return ** (1 / years)) - 1
            return cagr
        except Exception as e:
            logger.error(f"Error in calculate_cagr: {e}")
            raise
    
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sharpe Ratio."""
        try:
            if len(returns) < 2 or returns.std() == 0:
                return 0.0
        
            excess_return = returns.mean() - (self.risk_free_rate / periods_per_year)
            return (excess_return / returns.std()) * np.sqrt(periods_per_year)
        except Exception as e:
            logger.error(f"Error in calculate_sharpe_ratio: {e}")
            raise
    
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sortino Ratio (downside deviation)."""
        try:
            if len(returns) < 2:
                return 0.0
        
            excess_return = returns.mean() - (self.risk_free_rate / periods_per_year)
            downside_returns = returns[returns < 0]
        
            if len(downside_returns) == 0:
                return float('inf')
        
            downside_std = downside_returns.std()
            if downside_std == 0:
                return float('inf')
        
            return (excess_return / downside_std) * np.sqrt(periods_per_year)
        except Exception as e:
            logger.error(f"Error in calculate_sortino_ratio: {e}")
            raise
    
    def calculate_drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate drawdown series."""
        try:
            rolling_max = equity_curve.expanding().max()
            drawdown = (equity_curve - rolling_max) / rolling_max
            return drawdown
        except Exception as e:
            logger.error(f"Error in calculate_drawdown_series: {e}")
            raise
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown."""
        try:
            drawdown = self.calculate_drawdown_series(equity_curve)
            return float(drawdown.min())
        except Exception as e:
            logger.error(f"Error in calculate_max_drawdown: {e}")
            raise
    
    def calculate_ulcer_index(self, equity_curve: pd.Series) -> float:
        """Calculate Ulcer Index (pain of drawdowns)."""
        try:
            drawdown = self.calculate_drawdown_series(equity_curve)
            squared_dd = drawdown ** 2
            return np.sqrt(squared_dd.mean())
        except Exception as e:
            logger.error(f"Error in calculate_ulcer_index: {e}")
            raise
    
    def calculate_calmar_ratio(
        self,
        equity_curve: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Calmar Ratio (CAGR / Max DD)."""
        try:
            cagr = self.calculate_cagr(equity_curve, periods_per_year)
            max_dd = abs(self.calculate_max_drawdown(equity_curve))
        
            if max_dd == 0:
                return float('inf')
        
            return cagr / max_dd
        except Exception as e:
            logger.error(f"Error in calculate_calmar_ratio: {e}")
            raise
    
    def get_growth_metrics(
        self,
        equity_curve: pd.Series,
        periods_per_year: int = 252
    ) -> GrowthMetrics:
        """Get comprehensive growth metrics."""
        try:
            returns = self.calculate_returns(equity_curve)
        
            # Monthly returns (approximate)
            monthly_periods = periods_per_year // 12
            monthly_returns = returns.rolling(window=monthly_periods).sum()[:monthly_periods]
        
            # Calculate streaks
            positive_streak = 0
            negative_streak = 0
            current_streak = 0
            max_pos_streak = 0
            max_neg_streak = 0
        
            for r in returns:
                if r > 0:
                    if current_streak > 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                    max_pos_streak = max(max_pos_streak, current_streak)
                elif r < 0:
                    if current_streak < 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                    max_neg_streak = max(max_neg_streak, abs(current_streak))
                else:
                    current_streak = 0
        
            return GrowthMetrics(
                total_return=(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100,
                cagr=self.calculate_cagr(equity_curve, periods_per_year) * 100,
                monthly_return_avg=monthly_returns.mean() * 100 if len(monthly_returns) > 0 else 0,
                monthly_return_std=monthly_returns.std() * 100 if len(monthly_returns) > 0 else 0,
                best_month=monthly_returns.max() * 100 if len(monthly_returns) > 0 else 0,
                worst_month=monthly_returns.min() * 100 if len(monthly_returns) > 0 else 0,
                positive_months=int((monthly_returns > 0).sum()),
                negative_months=int((monthly_returns < 0).sum()),
                current_streak=current_streak,
                longest_win_streak=max_pos_streak,
                longest_loss_streak=max_neg_streak,
                growth_factor=equity_curve.iloc[-1] / equity_curve.iloc[0]
            )
        except Exception as e:
            logger.error(f"Error in get_growth_metrics: {e}")
            raise
    
    def get_drawdown_metrics(
        self,
        equity_curve: pd.Series,
        periods_per_year: int = 252
    ) -> DrawdownMetrics:
        """Get comprehensive drawdown metrics."""
        try:
            drawdown = self.calculate_drawdown_series(equity_curve)
        
            # Current drawdown
            current_dd = float(drawdown.iloc[-1])
        
            # Max drawdown
            max_dd = float(drawdown.min())
        
            # Average drawdown
            avg_dd = float(drawdown.mean())
        
            # Drawdown duration
            in_drawdown = drawdown < 0
            current_duration = 0
            max_duration = 0
            temp_duration = 0
        
            for is_dd in in_drawdown:
                if is_dd:
                    temp_duration += 1
                    max_duration = max(max_duration, temp_duration)
                else:
                    temp_duration = 0
        
            if in_drawdown.iloc[-1]:
                current_duration = temp_duration
        
            # Recovery factor
            total_profit = equity_curve.iloc[-1] - equity_curve.iloc[0]
            recovery_factor = total_profit / (abs(max_dd) * equity_curve.iloc[0]) if max_dd != 0 else 0
        
            # Ulcer index
            ulcer = self.calculate_ulcer_index(equity_curve)
        
            # Pain index (average drawdown depth * duration)
            pain = abs(avg_dd) * (max_duration / len(equity_curve))
        
            # Calmar ratio
            calmar = self.calculate_calmar_ratio(equity_curve, periods_per_year)
        
            return DrawdownMetrics(
                current_drawdown=current_dd * 100,
                max_drawdown=max_dd * 100,
                avg_drawdown=avg_dd * 100,
                drawdown_duration=current_duration,
                max_drawdown_duration=max_duration,
                recovery_factor=recovery_factor,
                ulcer_index=ulcer * 100,
                pain_index=pain * 100,
                calmar_ratio=calmar
            )
        except Exception as e:
            logger.error(f"Error in get_drawdown_metrics: {e}")
            raise
    
    def detect_growth_phase(self, equity_curve: pd.Series) -> GrowthPhase:
        """Detect current growth phase."""
        try:
            if len(equity_curve) < 20:
                return GrowthPhase.STEADY
        
            returns = self.calculate_returns(equity_curve)
            recent_returns = returns.iloc[-20:]
            prior_returns = returns.iloc[-40:-20] if len(returns) >= 40 else returns.iloc[:20]
        
            recent_mean = recent_returns.mean()
            prior_mean = prior_returns.mean()
        
            drawdown = self.calculate_drawdown_series(equity_curve)
            current_dd = drawdown.iloc[-1]
        
            # Check for drawdown
            if current_dd < -0.1:  # More than 10% drawdown
                # Check if recovering
                if recent_mean > 0 and recent_mean > prior_mean:
                    return GrowthPhase.RECOVERY
                return GrowthPhase.DRAWDOWN
        
            # Check for acceleration/deceleration
            if recent_mean > prior_mean * 1.5 and recent_mean > 0:
                return GrowthPhase.ACCELERATION
            elif recent_mean < prior_mean * 0.5 and recent_mean > 0:
                return GrowthPhase.DECELERATION
            elif abs(recent_mean) < 0.001:
                return GrowthPhase.STAGNATION
            else:
                return GrowthPhase.STEADY
        except Exception as e:
            logger.error(f"Error in detect_growth_phase: {e}")
            raise


class GrowthOptimizer:
    """
    Optimizes trading for maximum sustainable growth.
    """
    
    def __init__(
        self,
        goal: OptimizationGoal = OptimizationGoal.RISK_ADJUSTED,
        max_drawdown_limit: float = 0.2,
        target_sharpe: float = 2.0
    ):
        try:
            self.goal = goal
            self.max_drawdown_limit = max_drawdown_limit
            self.target_sharpe = target_sharpe
            self.analyzer = EquityCurveAnalyzer()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """Calculate Kelly Criterion for optimal bet sizing."""
        try:
            if avg_loss == 0:
                return 0.0
        
            win_loss_ratio = avg_win / avg_loss
            kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
            return max(0, kelly)
        except Exception as e:
            logger.error(f"Error in calculate_kelly_criterion: {e}")
            raise
    
    def calculate_optimal_f(
        self,
        trade_results: List[float]
    ) -> float:
        """Calculate Optimal F for position sizing."""
        try:
            if not trade_results:
                return 0.0
        
            max_loss = abs(min(trade_results))
            if max_loss == 0:
                return 0.0
        
            best_f = 0.0
            best_twr = 0.0
        
            for f in np.arange(0.01, 1.0, 0.01):
                twr = 1.0
                for trade in trade_results:
                    hpr = 1 + (f * trade / max_loss)
                    if hpr <= 0:
                        twr = 0
                        break
                    twr *= hpr
            
                if twr > best_twr:
                    best_twr = twr
                    best_f = f
        
            return best_f
        except Exception as e:
            logger.error(f"Error in calculate_optimal_f: {e}")
            raise
    
    def optimize_for_goal(
        self,
        equity_curve: pd.Series,
        trade_results: List[float],
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> OptimizationResult:
        """Optimize based on selected goal."""
        # Calculate base metrics
        try:
            kelly = self.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
            optimal_f = self.calculate_optimal_f(trade_results)
        
            growth_metrics = self.analyzer.get_growth_metrics(equity_curve)
            dd_metrics = self.analyzer.get_drawdown_metrics(equity_curve)
        
            recommendations = []
        
            if self.goal == OptimizationGoal.MAX_GROWTH:
                # Use full Kelly (aggressive)
                optimal_risk = kelly * 0.75  # 75% Kelly
                sizing_method = "kelly_criterion"
                recommendations.append("Using aggressive Kelly sizing for max growth")
            
            elif self.goal == OptimizationGoal.RISK_ADJUSTED:
                # Use half Kelly with Sharpe consideration
                optimal_risk = kelly * 0.5
                sizing_method = "half_kelly"
                recommendations.append("Using half-Kelly for risk-adjusted growth")
            
            elif self.goal == OptimizationGoal.DRAWDOWN_CONTROL:
                # Limit based on max drawdown
                dd_adjusted = min(kelly * 0.5, self.max_drawdown_limit / 3)
                optimal_risk = dd_adjusted
                sizing_method = "drawdown_limited"
                recommendations.append(f"Limiting risk to control drawdown below {self.max_drawdown_limit*100}%")
            
            elif self.goal == OptimizationGoal.CONSISTENCY:
                # Use conservative sizing for consistent returns
                optimal_risk = kelly * 0.25
                sizing_method = "quarter_kelly"
                recommendations.append("Using quarter-Kelly for consistent returns")
            
            else:  # COMPOUND_OPTIMAL
                # Balance between growth and drawdown
                optimal_risk = min(kelly * 0.5, optimal_f * 0.5)
                sizing_method = "compound_optimal"
                recommendations.append("Optimizing for compound growth")
        
            # Add specific recommendations based on current state
            if dd_metrics.current_drawdown < -10:
                recommendations.append("Currently in drawdown - consider reducing size")
                optimal_risk *= 0.75
        
            if growth_metrics.current_streak < -3:
                recommendations.append("On losing streak - reduce size temporarily")
                optimal_risk *= 0.8
        
            # Expected metrics
            expected_cagr = growth_metrics.cagr * (optimal_risk / 0.02)  # Scale by risk
            expected_max_dd = dd_metrics.max_drawdown * (optimal_risk / 0.02)
        
            return OptimizationResult(
                optimal_risk_per_trade=optimal_risk,
                optimal_position_sizing=sizing_method,
                expected_cagr=expected_cagr,
                expected_max_drawdown=expected_max_dd,
                kelly_fraction=kelly,
                recommended_adjustments=recommendations,
                confidence=0.7 if len(trade_results) > 30 else 0.4
            )
        except Exception as e:
            logger.error(f"Error in optimize_for_goal: {e}")
            raise
    
    def project_growth(
        self,
        current_equity: float,
        target_equity: float,
        monthly_return: float,
        monthly_std: float,
        simulations: int = 1000
    ) -> GrowthProjection:
        """Project future growth with Monte Carlo simulation."""
        try:
            if monthly_return <= 0:
                return GrowthProjection(
                    target_equity=target_equity,
                    time_to_target=-1,
                    probability=0,
                    best_case=current_equity,
                    worst_case=current_equity,
                    median_case=current_equity,
                    required_monthly_return=0
                )
        
            # Required return
            growth_needed = target_equity / current_equity
            required_monthly = (growth_needed ** (1/12)) - 1
        
            # Monte Carlo simulation
            max_months = 120  # 10 years max
            results = []
            times_to_target = []
        
            for _ in range(simulations):
                equity = current_equity
                months = 0
            
                while equity < target_equity and months < max_months:
                    monthly_ret = np.random.normal(monthly_return, monthly_std)
                    equity *= (1 + monthly_ret)
                    months += 1
            
                results.append(equity)
                if equity >= target_equity:
                    times_to_target.append(months)
        
            # Calculate statistics
            probability = len(times_to_target) / simulations
            median_time = int(np.median(times_to_target)) if times_to_target else -1
        
            return GrowthProjection(
                target_equity=target_equity,
                time_to_target=median_time,
                probability=probability,
                best_case=max(results),
                worst_case=min(results),
                median_case=np.median(results),
                required_monthly_return=required_monthly * 100
            )
        except Exception as e:
            logger.error(f"Error in project_growth: {e}")
            raise


class UnderwaterCurveAnalyzer:
    """
    Analyzes underwater (drawdown) curves.
    """
    
    def __init__(self):
        try:
            self.analyzer = EquityCurveAnalyzer()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_underwater_curve(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate underwater curve (drawdown from peak)."""
        return self.analyzer.calculate_drawdown_series(equity_curve)
    
    def analyze_drawdown_periods(
        self,
        equity_curve: pd.Series
    ) -> List[Dict[str, Any]]:
        """Analyze individual drawdown periods."""
        try:
            underwater = self.calculate_underwater_curve(equity_curve)
        
            periods = []
            in_drawdown = False
            start_idx = 0
            peak_value = equity_curve.iloc[0]
        
            for i, (dd, eq) in enumerate(zip(underwater, equity_curve)):
                if dd < 0 and not in_drawdown:
                    # Start of drawdown
                    in_drawdown = True
                    start_idx = i
                    peak_value = equity_curve.iloc[i-1] if i > 0 else eq
                
                elif dd >= 0 and in_drawdown:
                    # End of drawdown
                    in_drawdown = False
                    trough_idx = underwater.iloc[start_idx:i].idxmin()
                    trough_value = equity_curve.loc[trough_idx]
                
                    periods.append({
                        'start_idx': start_idx,
                        'end_idx': i,
                        'trough_idx': trough_idx,
                        'duration': i - start_idx,
                        'depth': float((trough_value - peak_value) / peak_value * 100),
                        'recovery_time': i - trough_idx,
                        'peak_value': peak_value,
                        'trough_value': trough_value
                    })
        
            # Handle ongoing drawdown
            if in_drawdown:
                trough_idx = underwater.iloc[start_idx:].idxmin()
                trough_value = equity_curve.loc[trough_idx]
            
                periods.append({
                    'start_idx': start_idx,
                    'end_idx': len(equity_curve) - 1,
                    'trough_idx': trough_idx,
                    'duration': len(equity_curve) - start_idx,
                    'depth': float((trough_value - peak_value) / peak_value * 100),
                    'recovery_time': None,  # Still in drawdown
                    'peak_value': peak_value,
                    'trough_value': trough_value,
                    'ongoing': True
                })
        
            return periods
        except Exception as e:
            logger.error(f"Error in analyze_drawdown_periods: {e}")
            raise
    
    def get_drawdown_statistics(
        self,
        equity_curve: pd.Series
    ) -> Dict[str, Any]:
        """Get comprehensive drawdown statistics."""
        try:
            periods = self.analyze_drawdown_periods(equity_curve)
        
            if not periods:
                return {
                    'num_drawdowns': 0,
                    'avg_depth': 0,
                    'avg_duration': 0,
                    'avg_recovery_time': 0,
                    'max_depth': 0,
                    'max_duration': 0
                }
        
            depths = [p['depth'] for p in periods]
            durations = [p['duration'] for p in periods]
            recovery_times = [p['recovery_time'] for p in periods if p.get('recovery_time')]
        
            return {
                'num_drawdowns': len(periods),
                'avg_depth': np.mean(depths),
                'avg_duration': np.mean(durations),
                'avg_recovery_time': np.mean(recovery_times) if recovery_times else None,
                'max_depth': min(depths),  # Most negative
                'max_duration': max(durations),
                'current_drawdown': periods[-1] if periods and periods[-1].get('ongoing') else None
            }
        except Exception as e:
            logger.error(f"Error in get_drawdown_statistics: {e}")
            raise


# Convenience functions
def analyze_equity_curve(equity_curve: pd.Series) -> Dict[str, Any]:
    """Quick equity curve analysis."""
    try:
        analyzer = EquityCurveAnalyzer()
    
        growth = analyzer.get_growth_metrics(equity_curve)
        drawdown = analyzer.get_drawdown_metrics(equity_curve)
        phase = analyzer.detect_growth_phase(equity_curve)
    
        returns = analyzer.calculate_returns(equity_curve)
        sharpe = analyzer.calculate_sharpe_ratio(returns)
        sortino = analyzer.calculate_sortino_ratio(returns)
    
        return {
            'cagr': growth.cagr,
            'total_return': growth.total_return,
            'max_drawdown': drawdown.max_drawdown,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': drawdown.calmar_ratio,
            'current_phase': phase.value,
            'growth_factor': growth.growth_factor
        }
    except Exception as e:
        logger.error(f"Error in analyze_equity_curve: {e}")
        raise


def optimize_position_sizing(
    trade_results: List[float],
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    goal: str = "risk_adjusted"
) -> Dict[str, Any]:
    """Optimize position sizing for growth."""
    try:
        optimizer = GrowthOptimizer(goal=OptimizationGoal(goal))
    
        # Create simple equity curve from trades
        equity = [10000]
        for trade in trade_results:
            equity.append(equity[-1] * (1 + trade))
        equity_curve = pd.Series(equity)
    
        result = optimizer.optimize_for_goal(
            equity_curve, trade_results, win_rate, avg_win, avg_loss
        )
    
        return {
            'optimal_risk': result.optimal_risk_per_trade,
            'sizing_method': result.optimal_position_sizing,
            'kelly_fraction': result.kelly_fraction,
            'recommendations': result.recommended_adjustments
        }
    except Exception as e:
        logger.error(f"Error in optimize_position_sizing: {e}")
        raise


def project_account_growth(
    current_equity: float,
    target_equity: float,
    monthly_return: float,
    monthly_std: float
) -> Dict[str, Any]:
    """Project time to reach target equity."""
    try:
        optimizer = GrowthOptimizer()
        projection = optimizer.project_growth(
            current_equity, target_equity, monthly_return, monthly_std
        )
    
        return {
            'time_to_target_months': projection.time_to_target,
            'probability': projection.probability,
            'best_case': projection.best_case,
            'worst_case': projection.worst_case,
            'required_monthly_return': projection.required_monthly_return
        }
    except Exception as e:
        logger.error(f"Error in project_account_growth: {e}")
        raise
