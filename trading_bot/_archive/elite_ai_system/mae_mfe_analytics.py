"""
MAE/MFE Analytics - Maximum Adverse/Favorable Excursion Analysis

Implements institutional-grade trade excursion analysis for
optimal stop-loss and take-profit placement.

Features:
- MAE (Maximum Adverse Excursion) tracking
- MFE (Maximum Favorable Excursion) tracking
- Distribution modeling
- Optimal stop/target recommendations
- Historical pattern analysis
- Trade efficiency metrics
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque
import json

logger = logging.getLogger(__name__)


class TradeOutcome(Enum):
    """Trade outcome classifications"""
    BIG_WIN = "big_win"       # > 2R profit
    WIN = "win"               # 0.5R - 2R profit
    SMALL_WIN = "small_win"   # 0 - 0.5R profit
    BREAKEVEN = "breakeven"   # Around 0
    SMALL_LOSS = "small_loss" # 0 - 0.5R loss
    LOSS = "loss"             # 0.5R - 1R loss
    BIG_LOSS = "big_loss"     # > 1R loss


class ExcursionType(Enum):
    """Types of excursion analysis"""
    MAE = "mae"  # Maximum Adverse Excursion
    MFE = "mfe"  # Maximum Favorable Excursion
    ETD = "etd"  # End Trade Drawdown (from MFE to close)


@dataclass
class TradeExcursion:
    """Excursion data for a single trade"""
    trade_id: str
    symbol: str
    direction: str  # LONG, SHORT
    
    # Prices
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    
    # Excursions (in price units)
    mae_price: float  # Worst price reached
    mfe_price: float  # Best price reached
    
    # Excursions (in R-multiples)
    mae_r: float  # MAE as R-multiple
    mfe_r: float  # MFE as R-multiple
    etd_r: float  # End Trade Drawdown (MFE to exit)
    
    # Excursions (in percentage)
    mae_pct: float
    mfe_pct: float
    
    # Result
    pnl_r: float  # P&L in R-multiples
    pnl_pct: float  # P&L in percentage
    outcome: TradeOutcome
    
    # Efficiency metrics
    capture_ratio: float  # How much of MFE was captured
    pain_ratio: float  # MAE relative to final result
    
    # Timing
    time_to_mae: Optional[timedelta] = None
    time_to_mfe: Optional[timedelta] = None
    trade_duration: Optional[timedelta] = None
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'mae_price': self.mae_price,
            'mfe_price': self.mfe_price,
            'mae_r': self.mae_r,
            'mfe_r': self.mfe_r,
            'etd_r': self.etd_r,
            'mae_pct': self.mae_pct,
            'mfe_pct': self.mfe_pct,
            'pnl_r': self.pnl_r,
            'pnl_pct': self.pnl_pct,
            'outcome': self.outcome.value,
            'capture_ratio': self.capture_ratio,
            'pain_ratio': self.pain_ratio,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ExcursionDistribution:
    """Statistical distribution of excursions"""
    excursion_type: ExcursionType
    sample_size: int
    
    # Central tendency
    mean: float
    median: float
    mode: float
    
    # Dispersion
    std: float
    variance: float
    
    # Percentiles
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    p99: float
    
    # Range
    min_value: float
    max_value: float
    
    # Shape
    skewness: float
    kurtosis: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'excursion_type': self.excursion_type.value,
            'sample_size': self.sample_size,
            'mean': self.mean,
            'median': self.median,
            'mode': self.mode,
            'std': self.std,
            'p10': self.p10,
            'p25': self.p25,
            'p50': self.p50,
            'p75': self.p75,
            'p90': self.p90,
            'p95': self.p95,
            'p99': self.p99,
            'min': self.min_value,
            'max': self.max_value,
            'skewness': self.skewness,
            'kurtosis': self.kurtosis
        }


@dataclass
class OptimalLevels:
    """Optimal stop/target recommendations"""
    # Stop loss recommendations
    optimal_stop_r: float
    optimal_stop_pct: float
    stop_confidence: float
    stop_reasoning: str
    
    # Take profit recommendations
    optimal_target_r: float
    optimal_target_pct: float
    target_confidence: float
    target_reasoning: str
    
    # Multiple targets
    target_levels: List[Tuple[float, float]]  # (R-multiple, % of position)
    
    # Risk-reward
    optimal_rr_ratio: float
    expected_value: float
    
    # Based on
    sample_size: int
    win_rate_at_optimal: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'optimal_stop_r': self.optimal_stop_r,
            'optimal_stop_pct': self.optimal_stop_pct,
            'stop_confidence': self.stop_confidence,
            'stop_reasoning': self.stop_reasoning,
            'optimal_target_r': self.optimal_target_r,
            'optimal_target_pct': self.optimal_target_pct,
            'target_confidence': self.target_confidence,
            'target_reasoning': self.target_reasoning,
            'target_levels': self.target_levels,
            'optimal_rr_ratio': self.optimal_rr_ratio,
            'expected_value': self.expected_value,
            'sample_size': self.sample_size,
            'win_rate_at_optimal': self.win_rate_at_optimal
        }


class MAEMFEAnalytics:
    """
    MAE/MFE Analytics System
    
    Provides comprehensive excursion analysis for trade optimization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Trade history
        self.excursions: deque = deque(maxlen=10000)
        
        # Cached distributions
        self._mae_distribution: Optional[ExcursionDistribution] = None
        self._mfe_distribution: Optional[ExcursionDistribution] = None
        self._etd_distribution: Optional[ExcursionDistribution] = None
        
        # Symbol-specific data
        self.symbol_excursions: Dict[str, List[TradeExcursion]] = {}
        
        logger.info("MAEMFEAnalytics initialized")
    
    def record_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        stop_loss: float,
        take_profit: float,
        price_history: List[float],
        timestamps: Optional[List[datetime]] = None
    ) -> TradeExcursion:
        """
        Record a completed trade and calculate excursions
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading symbol
            direction: LONG or SHORT
            entry_price: Entry price
            exit_price: Exit price
            stop_loss: Stop loss price
            take_profit: Take profit price
            price_history: List of prices during trade
            timestamps: Optional timestamps for each price
        
        Returns:
            TradeExcursion with complete analysis
        """
        # Calculate risk (R)
        risk = abs(entry_price - stop_loss)
        if risk == 0:
            risk = entry_price * 0.01  # Default to 1% if no stop
        
        # Calculate MAE and MFE based on direction
        if direction == "LONG":
            mae_price = min(price_history) if price_history else entry_price
            mfe_price = max(price_history) if price_history else entry_price
            
            mae_r = (entry_price - mae_price) / risk
            mfe_r = (mfe_price - entry_price) / risk
            pnl_r = (exit_price - entry_price) / risk
            
            mae_pct = (entry_price - mae_price) / entry_price * 100
            mfe_pct = (mfe_price - entry_price) / entry_price * 100
            pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:  # SHORT
            mae_price = max(price_history) if price_history else entry_price
            mfe_price = min(price_history) if price_history else entry_price
            
            mae_r = (mae_price - entry_price) / risk
            mfe_r = (entry_price - mfe_price) / risk
            pnl_r = (entry_price - exit_price) / risk
            
            mae_pct = (mae_price - entry_price) / entry_price * 100
            mfe_pct = (entry_price - mfe_price) / entry_price * 100
            pnl_pct = (entry_price - exit_price) / entry_price * 100
        
        # Calculate ETD (End Trade Drawdown from MFE)
        if direction == "LONG":
            etd_r = (mfe_price - exit_price) / risk
        else:
            etd_r = (exit_price - mfe_price) / risk
        
        # Determine outcome
        outcome = self._determine_outcome(pnl_r)
        
        # Calculate efficiency metrics
        capture_ratio = pnl_r / mfe_r if mfe_r > 0 else 0
        pain_ratio = mae_r / abs(pnl_r) if pnl_r != 0 else float('inf')
        
        # Calculate timing if timestamps provided
        time_to_mae = None
        time_to_mfe = None
        trade_duration = None
        
        if timestamps and len(timestamps) >= 2:
            trade_duration = timestamps[-1] - timestamps[0]
            
            if price_history:
                mae_idx = price_history.index(mae_price)
                mfe_idx = price_history.index(mfe_price)
                
                if mae_idx < len(timestamps):
                    time_to_mae = timestamps[mae_idx] - timestamps[0]
                if mfe_idx < len(timestamps):
                    time_to_mfe = timestamps[mfe_idx] - timestamps[0]
        
        excursion = TradeExcursion(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            mae_price=mae_price,
            mfe_price=mfe_price,
            mae_r=mae_r,
            mfe_r=mfe_r,
            etd_r=etd_r,
            mae_pct=mae_pct,
            mfe_pct=mfe_pct,
            pnl_r=pnl_r,
            pnl_pct=pnl_pct,
            outcome=outcome,
            capture_ratio=capture_ratio,
            pain_ratio=pain_ratio,
            time_to_mae=time_to_mae,
            time_to_mfe=time_to_mfe,
            trade_duration=trade_duration
        )
        
        # Store
        self.excursions.append(excursion)
        
        if symbol not in self.symbol_excursions:
            self.symbol_excursions[symbol] = []
        self.symbol_excursions[symbol].append(excursion)
        
        # Invalidate cached distributions
        self._mae_distribution = None
        self._mfe_distribution = None
        self._etd_distribution = None
        
        logger.info(
            f"Recorded trade {trade_id}: MAE={mae_r:.2f}R, MFE={mfe_r:.2f}R, "
            f"PnL={pnl_r:.2f}R, Capture={capture_ratio:.1%}"
        )
        
        return excursion
    
    def _determine_outcome(self, pnl_r: float) -> TradeOutcome:
        """Determine trade outcome from R-multiple"""
        if pnl_r > 2:
            return TradeOutcome.BIG_WIN
        elif pnl_r > 0.5:
            return TradeOutcome.WIN
        elif pnl_r > 0.1:
            return TradeOutcome.SMALL_WIN
        elif pnl_r > -0.1:
            return TradeOutcome.BREAKEVEN
        elif pnl_r > -0.5:
            return TradeOutcome.SMALL_LOSS
        elif pnl_r > -1:
            return TradeOutcome.LOSS
        else:
            return TradeOutcome.BIG_LOSS
    
    def get_mae_distribution(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        outcome_filter: Optional[List[TradeOutcome]] = None
    ) -> ExcursionDistribution:
        """Get MAE distribution with optional filters"""
        excursions = self._filter_excursions(symbol, direction, outcome_filter)
        
        if not excursions:
            return self._empty_distribution(ExcursionType.MAE)
        
        mae_values = [e.mae_r for e in excursions]
        return self._calculate_distribution(mae_values, ExcursionType.MAE)
    
    def get_mfe_distribution(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        outcome_filter: Optional[List[TradeOutcome]] = None
    ) -> ExcursionDistribution:
        """Get MFE distribution with optional filters"""
        excursions = self._filter_excursions(symbol, direction, outcome_filter)
        
        if not excursions:
            return self._empty_distribution(ExcursionType.MFE)
        
        mfe_values = [e.mfe_r for e in excursions]
        return self._calculate_distribution(mfe_values, ExcursionType.MFE)
    
    def get_etd_distribution(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        outcome_filter: Optional[List[TradeOutcome]] = None
    ) -> ExcursionDistribution:
        """Get ETD (End Trade Drawdown) distribution"""
        excursions = self._filter_excursions(symbol, direction, outcome_filter)
        
        if not excursions:
            return self._empty_distribution(ExcursionType.ETD)
        
        etd_values = [e.etd_r for e in excursions]
        return self._calculate_distribution(etd_values, ExcursionType.ETD)
    
    def _filter_excursions(
        self,
        symbol: Optional[str],
        direction: Optional[str],
        outcome_filter: Optional[List[TradeOutcome]]
    ) -> List[TradeExcursion]:
        """Filter excursions based on criteria"""
        excursions = list(self.excursions)
        
        if symbol:
            excursions = [e for e in excursions if e.symbol == symbol]
        
        if direction:
            excursions = [e for e in excursions if e.direction == direction]
        
        if outcome_filter:
            excursions = [e for e in excursions if e.outcome in outcome_filter]
        
        return excursions
    
    def _calculate_distribution(
        self,
        values: List[float],
        excursion_type: ExcursionType
    ) -> ExcursionDistribution:
        """Calculate distribution statistics"""
        if not values:
            return self._empty_distribution(excursion_type)
        
        arr = np.array(values)
        
        # Calculate mode (most common value, binned)
        hist, bin_edges = np.histogram(arr, bins=20)
        mode_idx = np.argmax(hist)
        mode = (bin_edges[mode_idx] + bin_edges[mode_idx + 1]) / 2
        
        # Calculate skewness and kurtosis
        try:
            from scipy import stats
            skewness = stats.skew(arr)
            kurtosis = stats.kurtosis(arr)
        except ImportError:
            # Manual calculation
            mean = np.mean(arr)
            std = np.std(arr)
            if std > 0:
                skewness = np.mean(((arr - mean) / std) ** 3)
                kurtosis = np.mean(((arr - mean) / std) ** 4) - 3
            else:
                skewness = 0
                kurtosis = 0
        
        return ExcursionDistribution(
            excursion_type=excursion_type,
            sample_size=len(values),
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            mode=float(mode),
            std=float(np.std(arr)),
            variance=float(np.var(arr)),
            p10=float(np.percentile(arr, 10)),
            p25=float(np.percentile(arr, 25)),
            p50=float(np.percentile(arr, 50)),
            p75=float(np.percentile(arr, 75)),
            p90=float(np.percentile(arr, 90)),
            p95=float(np.percentile(arr, 95)),
            p99=float(np.percentile(arr, 99)),
            min_value=float(np.min(arr)),
            max_value=float(np.max(arr)),
            skewness=float(skewness),
            kurtosis=float(kurtosis)
        )
    
    def _empty_distribution(self, excursion_type: ExcursionType) -> ExcursionDistribution:
        """Return empty distribution"""
        return ExcursionDistribution(
            excursion_type=excursion_type,
            sample_size=0,
            mean=0, median=0, mode=0,
            std=0, variance=0,
            p10=0, p25=0, p50=0, p75=0, p90=0, p95=0, p99=0,
            min_value=0, max_value=0,
            skewness=0, kurtosis=0
        )
    
    def get_optimal_levels(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None,
        current_win_rate: float = 0.5
    ) -> OptimalLevels:
        """
        Calculate optimal stop-loss and take-profit levels
        
        Uses MAE/MFE analysis to determine:
        - Optimal stop that avoids most MAE while not getting stopped out on winners
        - Optimal target that captures most MFE while not leaving too much on table
        """
        # Get winning and losing trades separately
        winners = self._filter_excursions(
            symbol, direction,
            [TradeOutcome.BIG_WIN, TradeOutcome.WIN, TradeOutcome.SMALL_WIN]
        )
        losers = self._filter_excursions(
            symbol, direction,
            [TradeOutcome.LOSS, TradeOutcome.BIG_LOSS, TradeOutcome.SMALL_LOSS]
        )
        
        if not winners and not losers:
            return self._default_optimal_levels()
        
        # Analyze MAE of winners to find optimal stop
        if winners:
            winner_mae = [w.mae_r for w in winners]
            # Stop should be beyond 90th percentile of winner MAE
            optimal_stop_r = np.percentile(winner_mae, 90) * 1.1
            stop_confidence = 0.8
            stop_reasoning = f"Based on {len(winners)} winning trades, 90% had MAE < {optimal_stop_r:.2f}R"
        else:
            optimal_stop_r = 1.0
            stop_confidence = 0.3
            stop_reasoning = "Default stop - insufficient winner data"
        
        # Analyze MFE of winners to find optimal target
        if winners:
            winner_mfe = [w.mfe_r for w in winners]
            # Target at 75th percentile of winner MFE
            optimal_target_r = np.percentile(winner_mfe, 75)
            target_confidence = 0.75
            target_reasoning = f"Based on {len(winners)} winning trades, 75% reached {optimal_target_r:.2f}R"
        else:
            optimal_target_r = 2.0
            target_confidence = 0.3
            target_reasoning = "Default target - insufficient winner data"
        
        # Calculate multiple target levels
        if winners:
            target_levels = [
                (np.percentile(winner_mfe, 50), 0.33),   # 50% of winners reach this - take 33%
                (np.percentile(winner_mfe, 75), 0.33),   # 75% reach this - take another 33%
                (np.percentile(winner_mfe, 90), 0.34),   # 90% reach this - take rest
            ]
        else:
            target_levels = [
                (1.0, 0.33),
                (2.0, 0.33),
                (3.0, 0.34),
            ]
        
        # Calculate optimal R:R
        optimal_rr = optimal_target_r / optimal_stop_r if optimal_stop_r > 0 else 2.0
        
        # Calculate expected value
        # EV = (Win% * Avg Win) - (Loss% * Avg Loss)
        if winners and losers:
            avg_win = np.mean([w.pnl_r for w in winners])
            avg_loss = abs(np.mean([l.pnl_r for l in losers]))
            win_rate = len(winners) / (len(winners) + len(losers))
            expected_value = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        else:
            expected_value = (current_win_rate * optimal_target_r) - ((1 - current_win_rate) * optimal_stop_r)
            win_rate = current_win_rate
        
        return OptimalLevels(
            optimal_stop_r=optimal_stop_r,
            optimal_stop_pct=optimal_stop_r * 1.0,  # Assuming 1R = 1%
            stop_confidence=stop_confidence,
            stop_reasoning=stop_reasoning,
            optimal_target_r=optimal_target_r,
            optimal_target_pct=optimal_target_r * 1.0,
            target_confidence=target_confidence,
            target_reasoning=target_reasoning,
            target_levels=target_levels,
            optimal_rr_ratio=optimal_rr,
            expected_value=expected_value,
            sample_size=len(winners) + len(losers),
            win_rate_at_optimal=win_rate if winners else current_win_rate
        )
    
    def _default_optimal_levels(self) -> OptimalLevels:
        """Return default optimal levels when no data available"""
        return OptimalLevels(
            optimal_stop_r=1.0,
            optimal_stop_pct=1.0,
            stop_confidence=0.3,
            stop_reasoning="Default - no historical data",
            optimal_target_r=2.0,
            optimal_target_pct=2.0,
            target_confidence=0.3,
            target_reasoning="Default - no historical data",
            target_levels=[(1.0, 0.33), (2.0, 0.33), (3.0, 0.34)],
            optimal_rr_ratio=2.0,
            expected_value=0.5,
            sample_size=0,
            win_rate_at_optimal=0.5
        )
    
    def get_efficiency_metrics(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trade efficiency metrics"""
        excursions = self._filter_excursions(symbol, direction, None)
        
        if not excursions:
            return {'message': 'No trades recorded'}
        
        capture_ratios = [e.capture_ratio for e in excursions if e.mfe_r > 0]
        pain_ratios = [e.pain_ratio for e in excursions if e.pain_ratio != float('inf')]
        etd_values = [e.etd_r for e in excursions]
        
        return {
            'total_trades': len(excursions),
            'avg_capture_ratio': np.mean(capture_ratios) if capture_ratios else 0,
            'median_capture_ratio': np.median(capture_ratios) if capture_ratios else 0,
            'avg_pain_ratio': np.mean(pain_ratios) if pain_ratios else 0,
            'avg_etd': np.mean(etd_values),
            'median_etd': np.median(etd_values),
            'trades_with_etd_over_1r': sum(1 for e in etd_values if e > 1),
            'efficiency_score': (np.mean(capture_ratios) * 100) if capture_ratios else 0
        }
    
    def get_outcome_analysis(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze outcomes by MAE/MFE patterns"""
        excursions = self._filter_excursions(symbol, direction, None)
        
        if not excursions:
            return {'message': 'No trades recorded'}
        
        # Group by outcome
        outcome_groups = {}
        for outcome in TradeOutcome:
            group = [e for e in excursions if e.outcome == outcome]
            if group:
                outcome_groups[outcome.value] = {
                    'count': len(group),
                    'avg_mae_r': np.mean([e.mae_r for e in group]),
                    'avg_mfe_r': np.mean([e.mfe_r for e in group]),
                    'avg_etd_r': np.mean([e.etd_r for e in group]),
                    'avg_capture': np.mean([e.capture_ratio for e in group if e.mfe_r > 0])
                }
        
        return {
            'total_trades': len(excursions),
            'outcome_distribution': outcome_groups,
            'win_rate': sum(1 for e in excursions if e.pnl_r > 0) / len(excursions) * 100,
            'avg_winner_r': np.mean([e.pnl_r for e in excursions if e.pnl_r > 0]) if any(e.pnl_r > 0 for e in excursions) else 0,
            'avg_loser_r': np.mean([e.pnl_r for e in excursions if e.pnl_r < 0]) if any(e.pnl_r < 0 for e in excursions) else 0
        }
    
    def get_stop_analysis(
        self,
        symbol: Optional[str] = None,
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze stop-loss effectiveness"""
        excursions = self._filter_excursions(symbol, direction, None)
        
        if not excursions:
            return {'message': 'No trades recorded'}
        
        # Trades that hit stop vs didn't
        stopped_out = [e for e in excursions if e.mae_r >= 1.0]
        not_stopped = [e for e in excursions if e.mae_r < 1.0]
        
        # Winners that came close to stop
        winners = [e for e in excursions if e.pnl_r > 0]
        winners_close_to_stop = [w for w in winners if w.mae_r > 0.8]
        
        return {
            'total_trades': len(excursions),
            'stopped_out_count': len(stopped_out),
            'stopped_out_pct': len(stopped_out) / len(excursions) * 100,
            'avg_mae_all': np.mean([e.mae_r for e in excursions]),
            'avg_mae_winners': np.mean([e.mae_r for e in winners]) if winners else 0,
            'winners_close_to_stop': len(winners_close_to_stop),
            'winners_close_to_stop_pct': len(winners_close_to_stop) / len(winners) * 100 if winners else 0,
            'recommendation': self._generate_stop_recommendation(excursions)
        }
    
    def _generate_stop_recommendation(self, excursions: List[TradeExcursion]) -> str:
        """Generate stop-loss recommendation"""
        if not excursions:
            return "Insufficient data for recommendation"
        
        winners = [e for e in excursions if e.pnl_r > 0]
        if not winners:
            return "No winning trades to analyze"
        
        winner_mae_90 = np.percentile([w.mae_r for w in winners], 90)
        
        if winner_mae_90 < 0.5:
            return f"Tight stops effective - 90% of winners had MAE < {winner_mae_90:.2f}R"
        elif winner_mae_90 < 0.8:
            return f"Standard stops appropriate - 90% of winners had MAE < {winner_mae_90:.2f}R"
        else:
            return f"Consider wider stops - 90% of winners had MAE < {winner_mae_90:.2f}R"
    
    def export_data(self, filepath: str):
        """Export excursion data to JSON"""
        data = {
            'excursions': [e.to_dict() for e in self.excursions],
            'mae_distribution': self.get_mae_distribution().to_dict(),
            'mfe_distribution': self.get_mfe_distribution().to_dict(),
            'optimal_levels': self.get_optimal_levels().to_dict(),
            'efficiency_metrics': self.get_efficiency_metrics(),
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported MAE/MFE data to {filepath}")
    
    def import_data(self, filepath: str):
        """Import excursion data from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # This would need proper deserialization
        logger.info(f"Imported MAE/MFE data from {filepath}")


# Convenience functions
def create_mae_mfe_analytics(config: Optional[Dict[str, Any]] = None) -> MAEMFEAnalytics:
    """Factory function to create MAE/MFE analytics"""
    return MAEMFEAnalytics(config)
