import logging
"""MAE/MFE (Maximum Adverse/Favorable Excursion) Analysis Module.

from enum import Enum
Implements comprehensive trade excursion analysis including:
- Maximum Adverse Excursion (MAE) - Worst drawdown during trade
- Maximum Favorable Excursion (MFE) - Best unrealized profit during trade
- MAE/MFE distribution modeling
- Optimal stop-loss placement based on MAE
- Optimal take-profit placement based on MFE
- Trade efficiency analysis (actual profit vs MFE)
- Edge Ratio calculation
- Trade quality scoring
- Position sizing optimization based on MAE

This module enables optimization of stop-loss and take-profit
placement based on historical trade behavior analysis.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

try:
    from scipy import stats
    from scipy.optimize import minimize

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None


class TradeDirection(enum.Enum):
    """Trade direction."""
    LONG = "long"
    SHORT = "short"


class TradeOutcome(enum.Enum):
    """Trade outcome classification."""
    WINNER = "winner"
    LOSER = "loser"
    BREAKEVEN = "breakeven"


@dataclass
class TradeExcursion:
    """Excursion data for a single trade."""
    trade_id: str
    direction: TradeDirection
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    mae: float  # Maximum Adverse Excursion (negative value)
    mfe: float  # Maximum Favorable Excursion (positive value)
    mae_price: float  # Price at MAE
    mfe_price: float  # Price at MFE
    mae_time: Optional[datetime]
    mfe_time: Optional[datetime]
    actual_profit: float
    actual_profit_pct: float
    mae_pct: float  # MAE as percentage of entry
    mfe_pct: float  # MFE as percentage of entry
    efficiency: float  # actual_profit / MFE (0-1)
    outcome: TradeOutcome
    hold_time: timedelta
    mae_to_mfe_ratio: float


@dataclass
class MAEDistribution:
    """MAE distribution analysis."""
    mean: float
    median: float
    std: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float
    percentile_99: float
    max_mae: float
    optimal_stop_loss: float  # Based on distribution
    stop_loss_confidence: float  # Percentage of trades that would survive


@dataclass
class MFEDistribution:
    """MFE distribution analysis."""
    mean: float
    median: float
    std: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float
    max_mfe: float
    optimal_take_profit: float  # Based on distribution
    take_profit_capture_rate: float  # Expected capture percentage


@dataclass
class EdgeRatio:
    """Edge Ratio analysis."""
    edge_ratio: float  # MFE / MAE
    average_mfe: float
    average_mae: float
    win_rate: float
    expectancy: float
    profit_factor: float
    edge_quality: str  # 'excellent', 'good', 'fair', 'poor'


@dataclass
class OptimalLevels:
    """Optimal stop-loss and take-profit levels."""
    optimal_stop_loss_pct: float
    optimal_take_profit_pct: float
    risk_reward_ratio: float
    expected_win_rate: float
    expected_expectancy: float
    confidence_level: float
    recommendation: str


@dataclass
class TradeQuality:
    """Trade quality assessment."""
    trade_id: str
    quality_score: float  # 0-100
    efficiency_score: float
    timing_score: float
    execution_score: float
    risk_management_score: float
    grade: str  # A+, A, B, C, D, F
    improvements: List[str]


class MAEMFEAnalyzer:
    """MAE/MFE Analysis Engine.
    
    Provides comprehensive analysis of trade excursions for
    optimizing stop-loss and take-profit placement.
    """
    
    def __init__(
        self,
        min_trades: int = 30,
        confidence_level: float = 0.95,
        efficiency_threshold: float = 0.5
    ):
        """Initialize MAE/MFE Analyzer.
        
        Args:
            min_trades: Minimum trades required for analysis
            confidence_level: Confidence level for statistical analysis
            efficiency_threshold: Threshold for good trade efficiency
        """
        self.min_trades = min_trades
        self.confidence_level = confidence_level
        self.efficiency_threshold = efficiency_threshold
        
        # Storage
        self._trades: List[TradeExcursion] = []
        
    def calculate_excursion(
        self,
        trade_id: str,
        direction: TradeDirection,
        entry_price: float,
        exit_price: float,
        entry_time: datetime,
        exit_time: datetime,
        price_data: pd.DataFrame
    ) -> TradeExcursion:
        """Calculate MAE and MFE for a single trade.
        
        Args:
            trade_id: Unique trade identifier
            direction: Trade direction (long/short)
            entry_price: Entry price
            exit_price: Exit price
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            price_data: DataFrame with OHLC data during trade
            
        Returns:
            TradeExcursion with complete analysis
        """
        # Filter price data to trade duration
        if isinstance(price_data.index, pd.DatetimeIndex):
            trade_data = price_data[(price_data.index >= entry_time) & (price_data.index <= exit_time)]
        else:
            trade_data = price_data
            
        if len(trade_data) == 0:
            trade_data = price_data
            
        # Calculate excursions based on direction
        if direction == TradeDirection.LONG:
            # For long: MAE is lowest low, MFE is highest high
            mae_price = trade_data['low'].min()
            mfe_price = trade_data['high'].max()
            mae = entry_price - mae_price  # Positive value = adverse
            mfe = mfe_price - entry_price  # Positive value = favorable
            actual_profit = exit_price - entry_price
        else:
            # For short: MAE is highest high, MFE is lowest low
            mae_price = trade_data['high'].max()
            mfe_price = trade_data['low'].min()
            mae = mae_price - entry_price  # Positive value = adverse
            mfe = entry_price - mfe_price  # Positive value = favorable
            actual_profit = entry_price - exit_price
            
        # Calculate percentages
        mae_pct = (mae / entry_price) * 100
        mfe_pct = (mfe / entry_price) * 100
        actual_profit_pct = (actual_profit / entry_price) * 100
        
        # Calculate efficiency (how much of MFE was captured)
        efficiency = actual_profit / mfe if mfe > 0 else 0
        efficiency = max(0, min(1, efficiency))  # Clamp to 0-1
        
        # Determine outcome
        if actual_profit > entry_price * 0.001:  # > 0.1% profit
            outcome = TradeOutcome.WINNER
        elif actual_profit < -entry_price * 0.001:  # > 0.1% loss
            outcome = TradeOutcome.LOSER
        else:
            outcome = TradeOutcome.BREAKEVEN
            
        # Find MAE and MFE times
        mae_time = None
        mfe_time = None
        
        if isinstance(trade_data.index, pd.DatetimeIndex):
            if direction == TradeDirection.LONG:
                mae_idx = trade_data['low'].idxmin()
                mfe_idx = trade_data['high'].idxmax()
            else:
                mae_idx = trade_data['high'].idxmax()
                mfe_idx = trade_data['low'].idxmin()
            mae_time = mae_idx
            mfe_time = mfe_idx
            
        # Hold time
        hold_time = exit_time - entry_time
        
        # MAE to MFE ratio
        mae_to_mfe = mae / mfe if mfe > 0 else float('inf')
        
        excursion = TradeExcursion(
            trade_id=trade_id,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            entry_time=entry_time,
            exit_time=exit_time,
            mae=-mae,  # Store as negative
            mfe=mfe,
            mae_price=mae_price,
            mfe_price=mfe_price,
            mae_time=mae_time,
            mfe_time=mfe_time,
            actual_profit=actual_profit,
            actual_profit_pct=actual_profit_pct,
            mae_pct=-mae_pct,  # Store as negative
            mfe_pct=mfe_pct,
            efficiency=efficiency,
            outcome=outcome,
            hold_time=hold_time,
            mae_to_mfe_ratio=mae_to_mfe
        )
        
        self._trades.append(excursion)
        return excursion
        
    def analyze_mae_distribution(
        self,
        trades: Optional[List[TradeExcursion]] = None,
        by_outcome: Optional[TradeOutcome] = None
    ) -> MAEDistribution:
        """Analyze MAE distribution.
        
        Args:
            trades: List of trades (uses stored trades if None)
            by_outcome: Filter by trade outcome
            
        Returns:
            MAEDistribution analysis
        """
        trades = trades or self._trades
        
        if by_outcome:
            trades = [t for t in trades if t.outcome == by_outcome]
            
        if len(trades) < self.min_trades:
            logger.warning(f"Insufficient trades for MAE analysis: {len(trades)}")
            return self._empty_mae_distribution()
            
        mae_values = [abs(t.mae_pct) for t in trades]  # Use absolute values
        
        mean = np.mean(mae_values)
        median = np.median(mae_values)
        std = np.std(mae_values)
        
        percentiles = np.percentile(mae_values, [25, 75, 90, 95, 99])
        
        # Optimal stop-loss: Use percentile that captures most trades
        # 90th percentile means 90% of trades would survive this stop
        optimal_stop = percentiles[2]  # 90th percentile
        
        # Calculate confidence (percentage of trades that would survive)
        stop_confidence = sum(1 for m in mae_values if m <= optimal_stop) / len(mae_values) * 100
        
        return MAEDistribution(
            mean=mean,
            median=median,
            std=std,
            percentile_25=percentiles[0],
            percentile_75=percentiles[1],
            percentile_90=percentiles[2],
            percentile_95=percentiles[3],
            percentile_99=percentiles[4],
            max_mae=max(mae_values),
            optimal_stop_loss=optimal_stop,
            stop_loss_confidence=stop_confidence
        )
        
    def analyze_mfe_distribution(
        self,
        trades: Optional[List[TradeExcursion]] = None,
        by_outcome: Optional[TradeOutcome] = None
    ) -> MFEDistribution:
        """Analyze MFE distribution.
        
        Args:
            trades: List of trades (uses stored trades if None)
            by_outcome: Filter by trade outcome
            
        Returns:
            MFEDistribution analysis
        """
        trades = trades or self._trades
        
        if by_outcome:
            trades = [t for t in trades if t.outcome == by_outcome]
            
        if len(trades) < self.min_trades:
            logger.warning(f"Insufficient trades for MFE analysis: {len(trades)}")
            return self._empty_mfe_distribution()
            
        mfe_values = [t.mfe_pct for t in trades]
        
        mean = np.mean(mfe_values)
        median = np.median(mfe_values)
        std = np.std(mfe_values)
        
        percentiles = np.percentile(mfe_values, [25, 75, 90, 95])
        
        # Optimal take-profit: Use median for realistic target
        optimal_tp = median
        
        # Calculate expected capture rate at this level
        capture_rate = sum(1 for m in mfe_values if m >= optimal_tp) / len(mfe_values) * 100
        
        return MFEDistribution(
            mean=mean,
            median=median,
            std=std,
            percentile_25=percentiles[0],
            percentile_75=percentiles[1],
            percentile_90=percentiles[2],
            percentile_95=percentiles[3],
            max_mfe=max(mfe_values),
            optimal_take_profit=optimal_tp,
            take_profit_capture_rate=capture_rate
        )
        
    def calculate_edge_ratio(
        self,
        trades: Optional[List[TradeExcursion]] = None
    ) -> EdgeRatio:
        """Calculate Edge Ratio (MFE/MAE).
        
        Edge Ratio > 1 indicates positive edge.
        
        Args:
            trades: List of trades (uses stored trades if None)
            
        Returns:
            EdgeRatio analysis
        """
        trades = trades or self._trades
        
        if len(trades) < self.min_trades:
            return EdgeRatio(
                edge_ratio=1.0,
                average_mfe=0,
                average_mae=0,
                win_rate=0,
                expectancy=0,
                profit_factor=1.0,
                edge_quality='insufficient_data'
            )
            
        avg_mfe = np.mean([t.mfe_pct for t in trades])
        avg_mae = np.mean([abs(t.mae_pct) for t in trades])
        
        edge_ratio = avg_mfe / avg_mae if avg_mae > 0 else 0
        
        # Win rate
        winners = [t for t in trades if t.outcome == TradeOutcome.WINNER]
        win_rate = len(winners) / len(trades) * 100
        
        # Expectancy
        avg_win = np.mean([t.actual_profit_pct for t in winners]) if winners else 0
        losers = [t for t in trades if t.outcome == TradeOutcome.LOSER]
        avg_loss = abs(np.mean([t.actual_profit_pct for t in losers])) if losers else 0
        
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)
        
        # Profit factor
        gross_profit = sum(t.actual_profit_pct for t in winners)
        gross_loss = abs(sum(t.actual_profit_pct for t in losers))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Edge quality
        if edge_ratio >= 2.0 and expectancy > 0.5:
            edge_quality = 'excellent'
        elif edge_ratio >= 1.5 and expectancy > 0.2:
            edge_quality = 'good'
        elif edge_ratio >= 1.0 and expectancy > 0:
            edge_quality = 'fair'
        else:
            edge_quality = 'poor'
            
        return EdgeRatio(
            edge_ratio=edge_ratio,
            average_mfe=avg_mfe,
            average_mae=avg_mae,
            win_rate=win_rate,
            expectancy=expectancy,
            profit_factor=profit_factor,
            edge_quality=edge_quality
        )
        
    def find_optimal_levels(
        self,
        trades: Optional[List[TradeExcursion]] = None
    ) -> OptimalLevels:
        """Find optimal stop-loss and take-profit levels.
        
        Uses MAE/MFE distributions to optimize risk/reward.
        
        Args:
            trades: List of trades (uses stored trades if None)
            
        Returns:
            OptimalLevels recommendation
        """
        trades = trades or self._trades
        
        if len(trades) < self.min_trades:
            return OptimalLevels(
                optimal_stop_loss_pct=2.0,
                optimal_take_profit_pct=4.0,
                risk_reward_ratio=2.0,
                expected_win_rate=50.0,
                expected_expectancy=0,
                confidence_level=0,
                recommendation="Insufficient data for optimization"
            )
            
        mae_dist = self.analyze_mae_distribution(trades)
        mfe_dist = self.analyze_mfe_distribution(trades)
        
        # Optimal stop-loss: 90th percentile of MAE
        optimal_sl = mae_dist.percentile_90
        
        # Optimal take-profit: Median MFE (50% capture rate)
        optimal_tp = mfe_dist.median
        
        # Risk-reward ratio
        rr_ratio = optimal_tp / optimal_sl if optimal_sl > 0 else 0
        
        # Simulate expected performance with these levels
        simulated_wins = 0
        simulated_losses = 0
        
        for trade in trades:
            mae = abs(trade.mae_pct)
            mfe = trade.mfe_pct
            
            # Would this trade hit stop-loss?
            if mae >= optimal_sl:
                simulated_losses += 1
            # Would this trade hit take-profit?
            elif mfe >= optimal_tp:
                simulated_wins += 1
            else:
                # Partial outcome based on actual result
                if trade.outcome == TradeOutcome.WINNER:
                    simulated_wins += 0.5
                else:
                    simulated_losses += 0.5
                    
        total = simulated_wins + simulated_losses
        expected_win_rate = (simulated_wins / total * 100) if total > 0 else 50
        
        # Expected expectancy
        expected_expectancy = (expected_win_rate / 100 * optimal_tp) - ((100 - expected_win_rate) / 100 * optimal_sl)
        
        # Generate recommendation
        if expected_expectancy > 0.5 and rr_ratio >= 1.5:
            recommendation = f"Strong setup: {optimal_sl:.2f}% SL, {optimal_tp:.2f}% TP (R:R {rr_ratio:.1f})"
        elif expected_expectancy > 0:
            recommendation = f"Acceptable setup: Consider tighter stops or wider targets"
        else:
            recommendation = f"Negative expectancy: Review strategy before trading"
            
        return OptimalLevels(
            optimal_stop_loss_pct=optimal_sl,
            optimal_take_profit_pct=optimal_tp,
            risk_reward_ratio=rr_ratio,
            expected_win_rate=expected_win_rate,
            expected_expectancy=expected_expectancy,
            confidence_level=self.confidence_level * 100,
            recommendation=recommendation
        )
        
    def assess_trade_quality(
        self,
        trade: TradeExcursion
    ) -> TradeQuality:
        """Assess quality of a single trade.
        
        Args:
            trade: Trade to assess
            
        Returns:
            TradeQuality assessment
        """
        improvements = []
        
        # Efficiency score (how much MFE was captured)
        efficiency_score = trade.efficiency * 100
        if efficiency_score < 50:
            improvements.append("Exit earlier to capture more profit")
            
        # Timing score (was entry near MFE or MAE?)
        # Good timing: Entry closer to MAE (got good price)
        if trade.mae_to_mfe_ratio < 0.3:
            timing_score = 90
        elif trade.mae_to_mfe_ratio < 0.5:
            timing_score = 70
        elif trade.mae_to_mfe_ratio < 0.7:
            timing_score = 50
            improvements.append("Consider waiting for better entry")
        else:
            timing_score = 30
            improvements.append("Entry timing needs improvement")
            
        # Execution score (based on actual vs potential)
        if trade.outcome == TradeOutcome.WINNER:
            execution_score = min(100, efficiency_score + 20)
        elif trade.outcome == TradeOutcome.BREAKEVEN:
            execution_score = 50
            improvements.append("Aim for better risk/reward")
        else:
            # For losers, check if MAE was excessive
            if abs(trade.mae_pct) > trade.mfe_pct:
                execution_score = 30
                improvements.append("Stop-loss may be too wide")
            else:
                execution_score = 40
                improvements.append("Review exit criteria")
                
        # Risk management score
        if abs(trade.mae_pct) < 2:
            risk_score = 90
        elif abs(trade.mae_pct) < 3:
            risk_score = 70
        elif abs(trade.mae_pct) < 5:
            risk_score = 50
            improvements.append("Consider tighter risk control")
        else:
            risk_score = 30
            improvements.append("Risk exposure too high")
            
        # Overall quality score
        quality_score = (efficiency_score * 0.3 + timing_score * 0.2 + 
                        execution_score * 0.3 + risk_score * 0.2)
                        
        # Grade
        if quality_score >= 90:
            grade = 'A+'
        elif quality_score >= 80:
            grade = 'A'
        elif quality_score >= 70:
            grade = 'B'
        elif quality_score >= 60:
            grade = 'C'
        elif quality_score >= 50:
            grade = 'D'
        else:
            grade = 'F'
            
        return TradeQuality(
            trade_id=trade.trade_id,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            timing_score=timing_score,
            execution_score=execution_score,
            risk_management_score=risk_score,
            grade=grade,
            improvements=improvements
        )
        
    def get_position_size_recommendation(
        self,
        account_balance: float,
        risk_per_trade_pct: float = 1.0,
        trades: Optional[List[TradeExcursion]] = None
    ) -> Dict[str, Any]:
        """Get position size recommendation based on MAE analysis.
        
        Args:
            account_balance: Current account balance
            risk_per_trade_pct: Risk per trade as percentage
            trades: List of trades for analysis
            
        Returns:
            Position sizing recommendation
        """
        trades = trades or self._trades
        
        if len(trades) < self.min_trades:
            return {
                'recommended_stop_pct': 2.0,
                'position_size_pct': risk_per_trade_pct / 2.0 * 100,
                'max_position_value': account_balance * risk_per_trade_pct / 100 / 0.02,
                'confidence': 'low',
                'note': 'Using default values due to insufficient trade history'
            }
            
        mae_dist = self.analyze_mae_distribution(trades)
        
        # Use 95th percentile MAE for conservative stop
        recommended_stop = mae_dist.percentile_95
        
        # Position size = Risk Amount / Stop Distance
        risk_amount = account_balance * (risk_per_trade_pct / 100)
        position_size_pct = (risk_per_trade_pct / recommended_stop) * 100
        max_position_value = risk_amount / (recommended_stop / 100)
        
        return {
            'recommended_stop_pct': recommended_stop,
            'position_size_pct': position_size_pct,
            'max_position_value': max_position_value,
            'risk_amount': risk_amount,
            'mae_analysis': {
                'mean': mae_dist.mean,
                'median': mae_dist.median,
                '95th_percentile': mae_dist.percentile_95,
                'max': mae_dist.max_mae
            },
            'confidence': 'high' if len(trades) >= 100 else 'medium',
            'note': f'Based on {len(trades)} historical trades'
        }
        
    def generate_report(
        self,
        trades: Optional[List[TradeExcursion]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive MAE/MFE report.
        
        Args:
            trades: List of trades (uses stored trades if None)
            
        Returns:
            Complete analysis report
        """
        trades = trades or self._trades
        
        if len(trades) < self.min_trades:
            return {
                'status': 'insufficient_data',
                'trades_analyzed': len(trades),
                'minimum_required': self.min_trades
            }
            
        mae_dist = self.analyze_mae_distribution(trades)
        mfe_dist = self.analyze_mfe_distribution(trades)
        edge_ratio = self.calculate_edge_ratio(trades)
        optimal_levels = self.find_optimal_levels(trades)
        
        # Analyze by outcome
        winners = [t for t in trades if t.outcome == TradeOutcome.WINNER]
        losers = [t for t in trades if t.outcome == TradeOutcome.LOSER]
        
        winner_mae = self.analyze_mae_distribution(winners) if len(winners) >= 10 else None
        winner_mfe = self.analyze_mfe_distribution(winners) if len(winners) >= 10 else None
        loser_mae = self.analyze_mae_distribution(losers) if len(losers) >= 10 else None
        loser_mfe = self.analyze_mfe_distribution(losers) if len(losers) >= 10 else None
        
        # Average efficiency
        avg_efficiency = np.mean([t.efficiency for t in trades])
        
        # Trade quality distribution
        qualities = [self.assess_trade_quality(t) for t in trades]
        grade_distribution = {}
        for q in qualities:
            grade_distribution[q.grade] = grade_distribution.get(q.grade, 0) + 1
            
        return {
            'status': 'complete',
            'trades_analyzed': len(trades),
            'summary': {
                'win_rate': edge_ratio.win_rate,
                'edge_ratio': edge_ratio.edge_ratio,
                'expectancy': edge_ratio.expectancy,
                'profit_factor': edge_ratio.profit_factor,
                'edge_quality': edge_ratio.edge_quality,
                'average_efficiency': avg_efficiency * 100
            },
            'mae_distribution': {
                'mean': mae_dist.mean,
                'median': mae_dist.median,
                'std': mae_dist.std,
                'percentile_90': mae_dist.percentile_90,
                'percentile_95': mae_dist.percentile_95,
                'max': mae_dist.max_mae,
                'optimal_stop_loss': mae_dist.optimal_stop_loss
            },
            'mfe_distribution': {
                'mean': mfe_dist.mean,
                'median': mfe_dist.median,
                'std': mfe_dist.std,
                'percentile_75': mfe_dist.percentile_75,
                'percentile_90': mfe_dist.percentile_90,
                'max': mfe_dist.max_mfe,
                'optimal_take_profit': mfe_dist.optimal_take_profit
            },
            'optimal_levels': {
                'stop_loss_pct': optimal_levels.optimal_stop_loss_pct,
                'take_profit_pct': optimal_levels.optimal_take_profit_pct,
                'risk_reward': optimal_levels.risk_reward_ratio,
                'expected_win_rate': optimal_levels.expected_win_rate,
                'expected_expectancy': optimal_levels.expected_expectancy,
                'recommendation': optimal_levels.recommendation
            },
            'by_outcome': {
                'winners': {
                    'count': len(winners),
                    'avg_mae': winner_mae.mean if winner_mae else None,
                    'avg_mfe': winner_mfe.mean if winner_mfe else None
                },
                'losers': {
                    'count': len(losers),
                    'avg_mae': loser_mae.mean if loser_mae else None,
                    'avg_mfe': loser_mfe.mean if loser_mfe else None
                }
            },
            'trade_quality': {
                'average_score': np.mean([q.quality_score for q in qualities]),
                'grade_distribution': grade_distribution
            }
        }
        
    def _empty_mae_distribution(self) -> MAEDistribution:
        """Create empty MAE distribution."""
        return MAEDistribution(
            mean=0, median=0, std=0,
            percentile_25=0, percentile_75=0,
            percentile_90=0, percentile_95=0, percentile_99=0,
            max_mae=0, optimal_stop_loss=2.0, stop_loss_confidence=0
        )
        
    def _empty_mfe_distribution(self) -> MFEDistribution:
        """Create empty MFE distribution."""
        return MFEDistribution(
            mean=0, median=0, std=0,
            percentile_25=0, percentile_75=0,
            percentile_90=0, percentile_95=0,
            max_mfe=0, optimal_take_profit=2.0, take_profit_capture_rate=0
        )


# Convenience functions
def calculate_trade_excursion(
    entry_price: float,
    exit_price: float,
    high_during_trade: float,
    low_during_trade: float,
    direction: str = 'long'
) -> Dict[str, float]:
    """Quick function to calculate MAE/MFE for a trade."""
    if direction.lower() == 'long':
        mae = entry_price - low_during_trade
        mfe = high_during_trade - entry_price
        profit = exit_price - entry_price
    else:
        mae = high_during_trade - entry_price
        mfe = entry_price - low_during_trade
        profit = entry_price - exit_price
        
    efficiency = profit / mfe if mfe > 0 else 0
    
    return {
        'mae': mae,
        'mfe': mfe,
        'mae_pct': (mae / entry_price) * 100,
        'mfe_pct': (mfe / entry_price) * 100,
        'profit': profit,
        'profit_pct': (profit / entry_price) * 100,
        'efficiency': efficiency
    }


def get_optimal_stop_loss(trades_mae_pct: List[float], percentile: float = 90) -> float:
    """Quick function to get optimal stop-loss from MAE data."""
    return np.percentile([abs(m) for m in trades_mae_pct], percentile)


def get_optimal_take_profit(trades_mfe_pct: List[float], percentile: float = 50) -> float:
    """Quick function to get optimal take-profit from MFE data."""
    return np.percentile(trades_mfe_pct, percentile)
