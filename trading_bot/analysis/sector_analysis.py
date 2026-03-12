"""
Sector Analysis Module.

This module implements:
- Sector rotation analysis
- Relative strength ranking
- Sector momentum tracking
- Industry group analysis
- Sector correlation analysis
- Business cycle positioning
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


class BusinessCyclePhase(Enum):
    """Business cycle phases."""
    EARLY_EXPANSION = "early_expansion"
    MID_EXPANSION = "mid_expansion"
    LATE_EXPANSION = "late_expansion"
    EARLY_CONTRACTION = "early_contraction"
    LATE_CONTRACTION = "late_contraction"


class SectorStrength(Enum):
    """Sector strength levels."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


class RotationDirection(Enum):
    """Sector rotation direction."""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"


@dataclass
class SectorMetrics:
    """Metrics for a sector."""
    symbol: str
    name: str
    relative_strength: float
    momentum_1w: float
    momentum_1m: float
    momentum_3m: float
    rank: int
    strength: SectorStrength
    is_leading: bool
    is_lagging: bool
    volume_trend: float
    breadth: float  # % of stocks above MA
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RotationAnalysis:
    """Sector rotation analysis result."""
    direction: RotationDirection
    cycle_phase: BusinessCyclePhase
    leading_sectors: List[str]
    lagging_sectors: List[str]
    improving_sectors: List[str]
    weakening_sectors: List[str]
    rotation_strength: float
    confidence: float
    recommendations: List[str]


@dataclass
class SectorSignal:
    """Trading signal for a sector."""
    sector: str
    signal: str  # 'buy', 'sell', 'hold'
    strength: float
    relative_rank: int
    momentum_score: float
    rotation_aligned: bool
    reasons: List[str]


class SectorDefinitions:
    """Sector and industry definitions."""
    
    # S&P 500 Sectors (SPDR ETFs)
    SP500_SECTORS = {
        'XLK': {'name': 'Technology', 'cycle': 'mid', 'risk': 'on'},
        'XLF': {'name': 'Financials', 'cycle': 'early', 'risk': 'on'},
        'XLE': {'name': 'Energy', 'cycle': 'late', 'risk': 'on'},
        'XLV': {'name': 'Healthcare', 'cycle': 'late', 'risk': 'neutral'},
        'XLI': {'name': 'Industrials', 'cycle': 'early', 'risk': 'on'},
        'XLP': {'name': 'Consumer Staples', 'cycle': 'late', 'risk': 'off'},
        'XLY': {'name': 'Consumer Discretionary', 'cycle': 'mid', 'risk': 'on'},
        'XLB': {'name': 'Materials', 'cycle': 'early', 'risk': 'on'},
        'XLU': {'name': 'Utilities', 'cycle': 'late', 'risk': 'off'},
        'XLRE': {'name': 'Real Estate', 'cycle': 'late', 'risk': 'neutral'},
        'XLC': {'name': 'Communication Services', 'cycle': 'mid', 'risk': 'on'}
    }
    
    # Cycle order for rotation analysis
    CYCLE_ORDER = {
        BusinessCyclePhase.EARLY_EXPANSION: ['XLF', 'XLI', 'XLB'],
        BusinessCyclePhase.MID_EXPANSION: ['XLK', 'XLY', 'XLC'],
        BusinessCyclePhase.LATE_EXPANSION: ['XLE', 'XLV', 'XLRE'],
        BusinessCyclePhase.EARLY_CONTRACTION: ['XLP', 'XLU', 'XLV'],
        BusinessCyclePhase.LATE_CONTRACTION: ['XLF', 'XLI', 'XLB']
    }
    
    # Risk-on vs Risk-off sectors
    RISK_ON_SECTORS = ['XLK', 'XLF', 'XLY', 'XLI', 'XLB', 'XLE', 'XLC']
    RISK_OFF_SECTORS = ['XLP', 'XLU', 'XLV', 'XLRE']


class SectorAnalyzer:
    """
    Comprehensive sector analysis system.
    """
    
    def __init__(
        self,
        momentum_periods: List[int] = None,
        ranking_period: int = 20,
        breadth_ma_period: int = 50
    ):
        try:
            self.momentum_periods = momentum_periods or [5, 20, 60]  # 1w, 1m, 3m
            self.ranking_period = ranking_period
            self.breadth_ma_period = breadth_ma_period
            self.definitions = SectorDefinitions()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_relative_strength(
        self,
        sector_data: pd.Series,
        benchmark_data: pd.Series,
        period: int = 20
    ) -> float:
        """Calculate relative strength vs benchmark."""
        try:
            if len(sector_data) < period or len(benchmark_data) < period:
                return 0.0
        
            sector_return = (sector_data.iloc[-1] / sector_data.iloc[-period] - 1) * 100
            benchmark_return = (benchmark_data.iloc[-1] / benchmark_data.iloc[-period] - 1) * 100
        
            return sector_return - benchmark_return
        except Exception as e:
            logger.error(f"Error in calculate_relative_strength: {e}")
            raise
    
    def calculate_momentum(
        self,
        data: pd.Series,
        period: int
    ) -> float:
        """Calculate momentum (rate of change)."""
        try:
            if len(data) < period:
                return 0.0
        
            return (data.iloc[-1] / data.iloc[-period] - 1) * 100
        except Exception as e:
            logger.error(f"Error in calculate_momentum: {e}")
            raise
    
    def calculate_volume_trend(
        self,
        volume: pd.Series,
        period: int = 20
    ) -> float:
        """Calculate volume trend."""
        try:
            if len(volume) < period * 2:
                return 0.0
        
            recent_avg = volume.iloc[-period:].mean()
            prior_avg = volume.iloc[-period*2:-period].mean()
        
            if prior_avg > 0:
                return (recent_avg / prior_avg - 1) * 100
            return 0.0
        except Exception as e:
            logger.error(f"Error in calculate_volume_trend: {e}")
            raise
    
    def determine_strength(
        self,
        relative_strength: float,
        momentum: float,
        rank: int,
        total_sectors: int
    ) -> SectorStrength:
        """Determine sector strength level."""
        try:
            percentile = (total_sectors - rank + 1) / total_sectors
        
            if percentile >= 0.8 and relative_strength > 2 and momentum > 0:
                return SectorStrength.VERY_STRONG
            elif percentile >= 0.6 and relative_strength > 0:
                return SectorStrength.STRONG
            elif percentile <= 0.2 and relative_strength < -2 and momentum < 0:
                return SectorStrength.VERY_WEAK
            elif percentile <= 0.4 and relative_strength < 0:
                return SectorStrength.WEAK
            else:
                return SectorStrength.NEUTRAL
        except Exception as e:
            logger.error(f"Error in determine_strength: {e}")
            raise
    
    def analyze_sector(
        self,
        symbol: str,
        sector_data: pd.Series,
        benchmark_data: pd.Series,
        volume_data: Optional[pd.Series] = None,
        rank: int = 1,
        total_sectors: int = 11
    ) -> SectorMetrics:
        """Analyze a single sector."""
        # Get sector info
        try:
            sector_info = self.definitions.SP500_SECTORS.get(symbol, {})
            name = sector_info.get('name', symbol)
        
            # Calculate metrics
            rs = self.calculate_relative_strength(sector_data, benchmark_data, self.ranking_period)
        
            mom_1w = self.calculate_momentum(sector_data, self.momentum_periods[0])
            mom_1m = self.calculate_momentum(sector_data, self.momentum_periods[1])
            mom_3m = self.calculate_momentum(sector_data, self.momentum_periods[2])
        
            vol_trend = self.calculate_volume_trend(volume_data) if volume_data is not None else 0
        
            # Determine strength
            strength = self.determine_strength(rs, mom_1m, rank, total_sectors)
        
            # Leading/lagging
            is_leading = rank <= 3 and rs > 0
            is_lagging = rank >= total_sectors - 2 and rs < 0
        
            return SectorMetrics(
                symbol=symbol,
                name=name,
                relative_strength=rs,
                momentum_1w=mom_1w,
                momentum_1m=mom_1m,
                momentum_3m=mom_3m,
                rank=rank,
                strength=strength,
                is_leading=is_leading,
                is_lagging=is_lagging,
                volume_trend=vol_trend,
                breadth=0.5  # Would need constituent data
            )
        except Exception as e:
            logger.error(f"Error in analyze_sector: {e}")
            raise
    
    def rank_sectors(
        self,
        sector_data: Dict[str, pd.Series],
        benchmark_data: pd.Series
    ) -> List[SectorMetrics]:
        """Rank all sectors by relative strength."""
        # Calculate RS for all sectors
        try:
            rs_scores = {}
            for symbol, data in sector_data.items():
                rs_scores[symbol] = self.calculate_relative_strength(data, benchmark_data)
        
            # Sort by RS
            sorted_sectors = sorted(rs_scores.items(), key=lambda x: x[1], reverse=True)
        
            # Analyze each sector
            metrics = []
            for rank, (symbol, _) in enumerate(sorted_sectors, 1):
                metric = self.analyze_sector(
                    symbol=symbol,
                    sector_data=sector_data[symbol],
                    benchmark_data=benchmark_data,
                    rank=rank,
                    total_sectors=len(sector_data)
                )
                metrics.append(metric)
        
            return metrics
        except Exception as e:
            logger.error(f"Error in rank_sectors: {e}")
            raise
    
    def detect_rotation(
        self,
        sector_data: Dict[str, pd.Series],
        benchmark_data: pd.Series
    ) -> RotationAnalysis:
        """Detect sector rotation patterns."""
        # Rank sectors
        try:
            metrics = self.rank_sectors(sector_data, benchmark_data)
        
            # Identify leaders and laggards
            leaders = [m.symbol for m in metrics if m.is_leading]
            laggards = [m.symbol for m in metrics if m.is_lagging]
        
            # Identify improving and weakening
            improving = []
            weakening = []
        
            for m in metrics:
                if m.momentum_1w > m.momentum_1m > 0:
                    improving.append(m.symbol)
                elif m.momentum_1w < m.momentum_1m < 0:
                    weakening.append(m.symbol)
        
            # Determine rotation direction
            risk_on_strength = sum(
                m.relative_strength for m in metrics 
                if m.symbol in self.definitions.RISK_ON_SECTORS
            )
            risk_off_strength = sum(
                m.relative_strength for m in metrics 
                if m.symbol in self.definitions.RISK_OFF_SECTORS
            )
        
            if risk_on_strength > risk_off_strength + 5:
                direction = RotationDirection.RISK_ON
            elif risk_off_strength > risk_on_strength + 5:
                direction = RotationDirection.RISK_OFF
            else:
                direction = RotationDirection.NEUTRAL
        
            # Determine cycle phase
            cycle_phase = self._determine_cycle_phase(leaders)
        
            # Calculate rotation strength
            rotation_strength = abs(risk_on_strength - risk_off_strength) / 10
            rotation_strength = min(1.0, rotation_strength)
        
            # Generate recommendations
            recommendations = self._generate_recommendations(
                direction, cycle_phase, leaders, improving
            )
        
            return RotationAnalysis(
                direction=direction,
                cycle_phase=cycle_phase,
                leading_sectors=leaders,
                lagging_sectors=laggards,
                improving_sectors=improving,
                weakening_sectors=weakening,
                rotation_strength=rotation_strength,
                confidence=rotation_strength * 0.8,
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in detect_rotation: {e}")
            raise
    
    def _determine_cycle_phase(self, leaders: List[str]) -> BusinessCyclePhase:
        """Determine business cycle phase from leading sectors."""
        try:
            for phase, sectors in self.definitions.CYCLE_ORDER.items():
                matches = sum(1 for s in leaders if s in sectors)
                if matches >= 2:
                    return phase
        
            return BusinessCyclePhase.MID_EXPANSION
        except Exception as e:
            logger.error(f"Error in _determine_cycle_phase: {e}")
            raise
    
    def _generate_recommendations(
        self,
        direction: RotationDirection,
        phase: BusinessCyclePhase,
        leaders: List[str],
        improving: List[str]
    ) -> List[str]:
        """Generate trading recommendations."""
        try:
            recommendations = []
        
            if direction == RotationDirection.RISK_ON:
                recommendations.append("Favor growth and cyclical sectors")
                recommendations.append("Consider reducing defensive exposure")
            elif direction == RotationDirection.RISK_OFF:
                recommendations.append("Favor defensive sectors")
                recommendations.append("Consider reducing cyclical exposure")
        
            if leaders:
                recommendations.append(f"Leading sectors: {', '.join(leaders)}")
        
            if improving:
                recommendations.append(f"Improving sectors to watch: {', '.join(improving)}")
        
            # Phase-specific recommendations
            phase_recs = {
                BusinessCyclePhase.EARLY_EXPANSION: "Early cycle - favor financials, industrials",
                BusinessCyclePhase.MID_EXPANSION: "Mid cycle - favor technology, consumer discretionary",
                BusinessCyclePhase.LATE_EXPANSION: "Late cycle - favor energy, healthcare",
                BusinessCyclePhase.EARLY_CONTRACTION: "Early contraction - favor staples, utilities",
                BusinessCyclePhase.LATE_CONTRACTION: "Late contraction - prepare for cycle turn"
            }
            recommendations.append(phase_recs.get(phase, ""))
        
            return [r for r in recommendations if r]
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise
    
    def get_sector_signal(
        self,
        symbol: str,
        sector_data: Dict[str, pd.Series],
        benchmark_data: pd.Series
    ) -> SectorSignal:
        """Get trading signal for a specific sector."""
        # Rank sectors
        try:
            metrics = self.rank_sectors(sector_data, benchmark_data)
        
            # Find target sector
            target = next((m for m in metrics if m.symbol == symbol), None)
        
            if not target:
                return SectorSignal(
                    sector=symbol,
                    signal='hold',
                    strength=0,
                    relative_rank=0,
                    momentum_score=0,
                    rotation_aligned=False,
                    reasons=["Sector not found"]
                )
        
            # Get rotation analysis
            rotation = self.detect_rotation(sector_data, benchmark_data)
        
            # Determine signal
            reasons = []
        
            # Check strength
            if target.strength in [SectorStrength.VERY_STRONG, SectorStrength.STRONG]:
                signal = 'buy'
                strength = 0.7 if target.strength == SectorStrength.STRONG else 0.9
                reasons.append(f"Sector showing {target.strength.value} relative strength")
            elif target.strength in [SectorStrength.VERY_WEAK, SectorStrength.WEAK]:
                signal = 'sell'
                strength = 0.7 if target.strength == SectorStrength.WEAK else 0.9
                reasons.append(f"Sector showing {target.strength.value} relative strength")
            else:
                signal = 'hold'
                strength = 0.3
                reasons.append("Sector showing neutral strength")
        
            # Check momentum
            if target.momentum_1w > 0 and target.momentum_1m > 0:
                reasons.append("Positive momentum across timeframes")
                strength = min(1.0, strength + 0.1)
            elif target.momentum_1w < 0 and target.momentum_1m < 0:
                reasons.append("Negative momentum across timeframes")
                if signal == 'buy':
                    signal = 'hold'
                    strength *= 0.5
        
            # Check rotation alignment
            sector_info = self.definitions.SP500_SECTORS.get(symbol, {})
            sector_risk = sector_info.get('risk', 'neutral')
        
            rotation_aligned = (
                (rotation.direction == RotationDirection.RISK_ON and sector_risk == 'on') or
                (rotation.direction == RotationDirection.RISK_OFF and sector_risk == 'off')
            )
        
            if rotation_aligned:
                reasons.append("Aligned with current rotation")
                strength = min(1.0, strength + 0.1)
            elif rotation.direction != RotationDirection.NEUTRAL:
                reasons.append("Not aligned with current rotation")
                strength *= 0.8
        
            # Momentum score
            momentum_score = (target.momentum_1w + target.momentum_1m + target.momentum_3m) / 3
        
            return SectorSignal(
                sector=symbol,
                signal=signal,
                strength=strength,
                relative_rank=target.rank,
                momentum_score=momentum_score,
                rotation_aligned=rotation_aligned,
                reasons=reasons
            )
        except Exception as e:
            logger.error(f"Error in get_sector_signal: {e}")
            raise


# Convenience functions
def rank_sectors_by_strength(
    sector_data: Dict[str, pd.Series],
    benchmark_data: pd.Series
) -> List[Dict[str, Any]]:
    """Quick sector ranking."""
    try:
        analyzer = SectorAnalyzer()
        metrics = analyzer.rank_sectors(sector_data, benchmark_data)
    
        return [
            {
                'symbol': m.symbol,
                'name': m.name,
                'rank': m.rank,
                'relative_strength': m.relative_strength,
                'strength': m.strength.value,
                'momentum_1m': m.momentum_1m
            }
            for m in metrics
        ]
    except Exception as e:
        logger.error(f"Error in rank_sectors_by_strength: {e}")
        raise


def get_rotation_direction(
    sector_data: Dict[str, pd.Series],
    benchmark_data: pd.Series
) -> Dict[str, Any]:
    """Get current rotation direction."""
    try:
        analyzer = SectorAnalyzer()
        rotation = analyzer.detect_rotation(sector_data, benchmark_data)
    
        return {
            'direction': rotation.direction.value,
            'cycle_phase': rotation.cycle_phase.value,
            'leaders': rotation.leading_sectors,
            'laggards': rotation.lagging_sectors,
            'strength': rotation.rotation_strength,
            'recommendations': rotation.recommendations
        }
    except Exception as e:
        logger.error(f"Error in get_rotation_direction: {e}")
        raise


def get_best_sectors(
    sector_data: Dict[str, pd.Series],
    benchmark_data: pd.Series,
    top_n: int = 3
) -> List[str]:
    """Get top N sectors by relative strength."""
    try:
        analyzer = SectorAnalyzer()
        metrics = analyzer.rank_sectors(sector_data, benchmark_data)
    
        return [m.symbol for m in metrics[:top_n]]
    except Exception as e:
        logger.error(f"Error in get_best_sectors: {e}")
        raise
