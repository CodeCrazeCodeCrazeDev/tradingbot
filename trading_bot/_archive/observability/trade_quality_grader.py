"""
Trade Quality Grader
====================

Comprehensive trade quality scoring and grading system.
Evaluates trades across multiple dimensions to assign quality grades.

Features:
- Multi-dimensional quality assessment
- Letter grade assignment (A+ to F)
- Quality trend tracking
- Improvement recommendations
- Historical comparison
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
import threading
import logging
import statistics

logger = logging.getLogger(__name__)


class TradeGrade(Enum):
    """Trade quality grades."""
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D_PLUS = "D+"
    D = "D"
    D_MINUS = "D-"
    F = "F"
    
    @classmethod
    def from_score(cls, score: float) -> "TradeGrade":
        """Convert numeric score (0-100) to grade."""
        if score >= 97:
            return cls.A_PLUS
        elif score >= 93:
            return cls.A
        elif score >= 90:
            return cls.A_MINUS
        elif score >= 87:
            return cls.B_PLUS
        elif score >= 83:
            return cls.B
        elif score >= 80:
            return cls.B_MINUS
        elif score >= 77:
            return cls.C_PLUS
        elif score >= 73:
            return cls.C
        elif score >= 70:
            return cls.C_MINUS
        elif score >= 67:
            return cls.D_PLUS
        elif score >= 63:
            return cls.D
        elif score >= 60:
            return cls.D_MINUS
        else:
            return cls.F
    
    @property
    def is_passing(self) -> bool:
        return self not in (TradeGrade.D_MINUS, TradeGrade.F)
    
    @property
    def numeric_value(self) -> float:
        """GPA-style numeric value."""
        values = {
            TradeGrade.A_PLUS: 4.0,
            TradeGrade.A: 4.0,
            TradeGrade.A_MINUS: 3.7,
            TradeGrade.B_PLUS: 3.3,
            TradeGrade.B: 3.0,
            TradeGrade.B_MINUS: 2.7,
            TradeGrade.C_PLUS: 2.3,
            TradeGrade.C: 2.0,
            TradeGrade.C_MINUS: 1.7,
            TradeGrade.D_PLUS: 1.3,
            TradeGrade.D: 1.0,
            TradeGrade.D_MINUS: 0.7,
            TradeGrade.F: 0.0,
        }
        return values[self]


class QualityDimension(Enum):
    """Dimensions of trade quality."""
    ENTRY_TIMING = auto()         # How well timed was the entry
    EXIT_TIMING = auto()          # How well timed was the exit
    POSITION_SIZING = auto()      # Was position size appropriate
    RISK_REWARD = auto()          # Risk/reward ratio quality
    SIGNAL_STRENGTH = auto()      # Underlying signal quality
    EXECUTION_QUALITY = auto()    # Slippage, fill quality
    MARKET_ALIGNMENT = auto()     # Alignment with market conditions
    STRATEGY_ADHERENCE = auto()   # Did it follow strategy rules
    DRAWDOWN_CONTROL = auto()     # Drawdown during trade
    PROFIT_CAPTURE = auto()       # How much of the move was captured


@dataclass
class DimensionScore:
    """Score for a single quality dimension."""
    dimension: QualityDimension
    score: float  # 0-100
    weight: float  # Importance weight
    details: str
    factors: Dict[str, float] = field(default_factory=dict)
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class TradeScore:
    """Complete trade quality score."""
    trade_id: str
    symbol: str
    strategy_id: str
    direction: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    
    # Scores
    overall_score: float
    grade: TradeGrade
    dimension_scores: Dict[QualityDimension, DimensionScore]
    
    # Metadata
    entry_time: datetime
    exit_time: datetime
    graded_at: datetime = field(default_factory=datetime.utcnow)
    
    # Analysis
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "strategy_id": self.strategy_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "overall_score": self.overall_score,
            "grade": self.grade.value,
            "dimension_scores": {
                d.name: {"score": s.score, "weight": s.weight, "details": s.details}
                for d, s in self.dimension_scores.items()
            },
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "graded_at": self.graded_at.isoformat(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
        }


@dataclass
class GradingConfig:
    """Configuration for trade grading."""
    # Dimension weights (must sum to 1.0)
    dimension_weights: Dict[QualityDimension, float] = field(default_factory=lambda: {
        QualityDimension.ENTRY_TIMING: 0.15,
        QualityDimension.EXIT_TIMING: 0.15,
        QualityDimension.POSITION_SIZING: 0.10,
        QualityDimension.RISK_REWARD: 0.15,
        QualityDimension.SIGNAL_STRENGTH: 0.10,
        QualityDimension.EXECUTION_QUALITY: 0.10,
        QualityDimension.MARKET_ALIGNMENT: 0.10,
        QualityDimension.STRATEGY_ADHERENCE: 0.05,
        QualityDimension.DRAWDOWN_CONTROL: 0.05,
        QualityDimension.PROFIT_CAPTURE: 0.05,
    })
    
    # Thresholds
    min_acceptable_grade: TradeGrade = TradeGrade.C
    excellent_threshold: float = 90.0
    good_threshold: float = 75.0
    acceptable_threshold: float = 60.0
    
    # Benchmarks
    target_win_rate: float = 0.55
    target_profit_factor: float = 1.5
    target_risk_reward: float = 2.0
    max_acceptable_slippage_bps: float = 10.0
    max_acceptable_drawdown_pct: float = 0.02


class DimensionGrader:
    """Base class for dimension graders."""
    
    def __init__(self, dimension: QualityDimension, weight: float):
        self.dimension = dimension
        self.weight = weight
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        pass


class EntryTimingGrader(DimensionGrader):
    """Grades entry timing quality."""
    
    def __init__(self, weight: float):
        super().__init__(QualityDimension.ENTRY_TIMING, weight)
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        entry_price = trade_data.get("entry_price", 0)
        direction = trade_data.get("direction", "BUY")
        high_after_entry = context.get("high_after_entry", entry_price)
        low_after_entry = context.get("low_after_entry", entry_price)
        
        # Calculate how close to optimal entry
        if direction == "BUY":
            optimal = low_after_entry
            range_size = high_after_entry - low_after_entry
            if range_size > 0:
                entry_quality = 1 - (entry_price - optimal) / range_size
            else:
                entry_quality = 0.5
        else:
            optimal = high_after_entry
            range_size = high_after_entry - low_after_entry
            if range_size > 0:
                entry_quality = 1 - (optimal - entry_price) / range_size
            else:
                entry_quality = 0.5
        
        score = max(0, min(100, entry_quality * 100))
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"Entry at {entry_quality:.1%} of optimal range",
            factors={"entry_quality": entry_quality},
        )


class ExitTimingGrader(DimensionGrader):
    """Grades exit timing quality."""
    
    def __init__(self, weight: float):
        super().__init__(QualityDimension.EXIT_TIMING, weight)
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        exit_price = trade_data.get("exit_price", 0)
        direction = trade_data.get("direction", "BUY")
        high_during_trade = context.get("high_during_trade", exit_price)
        low_during_trade = context.get("low_during_trade", exit_price)
        
        # Calculate how close to optimal exit
        if direction == "BUY":
            optimal = high_during_trade
            range_size = high_during_trade - low_during_trade
            if range_size > 0:
                exit_quality = (exit_price - low_during_trade) / range_size
            else:
                exit_quality = 0.5
        else:
            optimal = low_during_trade
            range_size = high_during_trade - low_during_trade
            if range_size > 0:
                exit_quality = (high_during_trade - exit_price) / range_size
            else:
                exit_quality = 0.5
        
        score = max(0, min(100, exit_quality * 100))
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"Exit at {exit_quality:.1%} of optimal range",
            factors={"exit_quality": exit_quality},
        )


class PositionSizingGrader(DimensionGrader):
    """Grades position sizing quality."""
    
    def __init__(self, weight: float):
        super().__init__(QualityDimension.POSITION_SIZING, weight)
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        position_size_pct = trade_data.get("position_size_pct", 0.02)
        volatility = context.get("volatility", 0.02)
        signal_confidence = trade_data.get("signal_confidence", 0.5)
        
        # Optimal position size based on Kelly-like criterion
        win_rate = context.get("strategy_win_rate", 0.5)
        avg_win = context.get("avg_win", 1.0)
        avg_loss = context.get("avg_loss", 1.0)
        
        if avg_loss > 0:
            kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            kelly = max(0, min(0.25, kelly))  # Cap at 25%
        else:
            kelly = 0.02
        
        # Adjust for volatility and confidence
        optimal_size = kelly * signal_confidence * (0.02 / max(volatility, 0.01))
        optimal_size = max(0.01, min(0.10, optimal_size))
        
        # Score based on deviation from optimal
        if optimal_size > 0:
            deviation = abs(position_size_pct - optimal_size) / optimal_size
            score = max(0, 100 - deviation * 100)
        else:
            score = 50
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"Position {position_size_pct:.2%} vs optimal {optimal_size:.2%}",
            factors={"actual": position_size_pct, "optimal": optimal_size},
        )


class RiskRewardGrader(DimensionGrader):
    """Grades risk/reward ratio quality."""
    
    def __init__(self, weight: float, target_rr: float = 2.0):
        super().__init__(QualityDimension.RISK_REWARD, weight)
        self.target_rr = target_rr
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        entry_price = trade_data.get("entry_price", 0)
        exit_price = trade_data.get("exit_price", 0)
        stop_loss = trade_data.get("stop_loss")
        take_profit = trade_data.get("take_profit")
        direction = trade_data.get("direction", "BUY")
        
        # Calculate actual R:R
        if stop_loss and entry_price:
            if direction == "BUY":
                risk = entry_price - stop_loss
                reward = exit_price - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - exit_price
            
            if risk > 0:
                actual_rr = reward / risk
            else:
                actual_rr = 0
        else:
            actual_rr = 1.0
        
        # Score based on R:R
        if actual_rr >= self.target_rr:
            score = 100
        elif actual_rr >= 1.0:
            score = 70 + (actual_rr - 1.0) / (self.target_rr - 1.0) * 30
        elif actual_rr >= 0:
            score = actual_rr * 70
        else:
            score = 0
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"R:R = {actual_rr:.2f} (target: {self.target_rr:.1f})",
            factors={"actual_rr": actual_rr, "target_rr": self.target_rr},
        )


class ExecutionQualityGrader(DimensionGrader):
    """Grades execution quality (slippage, fills)."""
    
    def __init__(self, weight: float, max_slippage_bps: float = 10.0):
        super().__init__(QualityDimension.EXECUTION_QUALITY, weight)
        self.max_slippage_bps = max_slippage_bps
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        slippage_bps = trade_data.get("slippage_bps", 0)
        fill_rate = trade_data.get("fill_rate", 1.0)
        execution_time_ms = trade_data.get("execution_time_ms", 100)
        
        # Slippage score
        if slippage_bps <= 0:
            slippage_score = 100  # Positive slippage (improvement)
        elif slippage_bps <= self.max_slippage_bps:
            slippage_score = 100 - (slippage_bps / self.max_slippage_bps) * 50
        else:
            slippage_score = max(0, 50 - (slippage_bps - self.max_slippage_bps) * 2)
        
        # Fill rate score
        fill_score = fill_rate * 100
        
        # Execution time score
        if execution_time_ms <= 100:
            time_score = 100
        elif execution_time_ms <= 500:
            time_score = 90
        elif execution_time_ms <= 1000:
            time_score = 70
        else:
            time_score = max(0, 70 - (execution_time_ms - 1000) / 100)
        
        # Combined score
        score = slippage_score * 0.5 + fill_score * 0.3 + time_score * 0.2
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"Slippage: {slippage_bps:.1f}bps, Fill: {fill_rate:.1%}",
            factors={
                "slippage_bps": slippage_bps,
                "fill_rate": fill_rate,
                "execution_time_ms": execution_time_ms,
            },
        )


class SignalStrengthGrader(DimensionGrader):
    """Grades underlying signal strength."""
    
    def __init__(self, weight: float):
        super().__init__(QualityDimension.SIGNAL_STRENGTH, weight)
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        signal_confidence = trade_data.get("signal_confidence", 0.5)
        signal_count = context.get("confirming_signals", 1)
        signal_alignment = context.get("signal_alignment", 0.5)
        
        # Base score from confidence
        base_score = signal_confidence * 100
        
        # Bonus for multiple confirming signals
        confirmation_bonus = min(20, (signal_count - 1) * 5)
        
        # Alignment bonus
        alignment_bonus = signal_alignment * 10
        
        score = min(100, base_score + confirmation_bonus + alignment_bonus)
        
        return DimensionScore(
            dimension=self.dimension,
            score=score,
            weight=self.weight,
            details=f"Confidence: {signal_confidence:.1%}, Confirmations: {signal_count}",
            factors={
                "confidence": signal_confidence,
                "confirmations": signal_count,
                "alignment": signal_alignment,
            },
        )


class MarketAlignmentGrader(DimensionGrader):
    """Grades alignment with market conditions."""
    
    def __init__(self, weight: float):
        super().__init__(QualityDimension.MARKET_ALIGNMENT, weight)
    
    def grade(self, trade_data: Dict[str, Any], context: Dict[str, Any]) -> DimensionScore:
        direction = trade_data.get("direction", "BUY")
        market_trend = context.get("market_trend", "NEUTRAL")  # UP, DOWN, NEUTRAL
        regime = context.get("market_regime", "NORMAL")
        volatility_regime = context.get("volatility_regime", "NORMAL")
        
        # Trend alignment
        if market_trend == "UP" and direction == "BUY":
            trend_score = 100
        elif market_trend == "DOWN" and direction == "SELL":
            trend_score = 100
        elif market_trend == "NEUTRAL":
            trend_score = 70
        else:
            trend_score = 30  # Counter-trend
        
        # Regime penalty
        regime_multiplier = {
            "NORMAL": 1.0,
            "VOLATILE": 0.8,
            "TRENDING": 1.1,
            "RANGING": 0.9,
            "CRISIS": 0.5,
        }.get(regime, 1.0)
        
        score = trend_score * regime_multiplier
        
        return DimensionScore(
            dimension=self.dimension,
            score=min(100, score),
            weight=self.weight,
            details=f"Trend: {market_trend}, Regime: {regime}",
            factors={
                "trend_alignment": trend_score,
                "regime": regime,
                "regime_multiplier": regime_multiplier,
            },
        )


class TradeQualityGrader:
    """
    Comprehensive trade quality grading system.
    
    Evaluates trades across multiple dimensions and assigns grades.
    """
    
    def __init__(self, config: Optional[GradingConfig] = None):
        self.config = config or GradingConfig()
        
        # Initialize dimension graders
        self._graders: Dict[QualityDimension, DimensionGrader] = {}
        self._init_graders()
        
        # History
        self._grade_history: deque = deque(maxlen=10000)
        self._lock = threading.Lock()
        
        # Statistics
        self._grade_counts: Dict[TradeGrade, int] = {g: 0 for g in TradeGrade}
        self._dimension_averages: Dict[QualityDimension, List[float]] = {
            d: [] for d in QualityDimension
        }
        
        logger.info("TradeQualityGrader initialized")
    
    def _init_graders(self) -> None:
        """Initialize dimension graders."""
        weights = self.config.dimension_weights
        
        self._graders = {
            QualityDimension.ENTRY_TIMING: EntryTimingGrader(
                weights.get(QualityDimension.ENTRY_TIMING, 0.15)
            ),
            QualityDimension.EXIT_TIMING: ExitTimingGrader(
                weights.get(QualityDimension.EXIT_TIMING, 0.15)
            ),
            QualityDimension.POSITION_SIZING: PositionSizingGrader(
                weights.get(QualityDimension.POSITION_SIZING, 0.10)
            ),
            QualityDimension.RISK_REWARD: RiskRewardGrader(
                weights.get(QualityDimension.RISK_REWARD, 0.15),
                self.config.target_risk_reward
            ),
            QualityDimension.EXECUTION_QUALITY: ExecutionQualityGrader(
                weights.get(QualityDimension.EXECUTION_QUALITY, 0.10),
                self.config.max_acceptable_slippage_bps
            ),
            QualityDimension.SIGNAL_STRENGTH: SignalStrengthGrader(
                weights.get(QualityDimension.SIGNAL_STRENGTH, 0.10)
            ),
            QualityDimension.MARKET_ALIGNMENT: MarketAlignmentGrader(
                weights.get(QualityDimension.MARKET_ALIGNMENT, 0.10)
            ),
        }
    
    def grade_trade(
        self,
        trade_id: str,
        trade_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> TradeScore:
        """
        Grade a completed trade.
        
        Args:
            trade_id: Unique trade identifier
            trade_data: Trade details (entry/exit prices, direction, etc.)
            context: Market context during trade
        
        Returns:
            TradeScore with grades and analysis
        """
        context = context or {}
        dimension_scores: Dict[QualityDimension, DimensionScore] = {}
        
        # Grade each dimension
        for dimension, grader in self._graders.items():
            try:
                score = grader.grade(trade_data, context)
                dimension_scores[dimension] = score
            except Exception as e:
                logger.error(f"Error grading {dimension.name}: {e}")
                dimension_scores[dimension] = DimensionScore(
                    dimension=dimension,
                    score=50,
                    weight=grader.weight,
                    details=f"Grading error: {str(e)}",
                )
        
        # Calculate overall score
        total_weight = sum(s.weight for s in dimension_scores.values())
        if total_weight > 0:
            overall_score = sum(s.weighted_score for s in dimension_scores.values()) / total_weight
        else:
            overall_score = 50
        
        # Determine grade
        grade = TradeGrade.from_score(overall_score)
        
        # Analyze strengths and weaknesses
        strengths, weaknesses, recommendations = self._analyze(dimension_scores, overall_score)
        
        # Create trade score
        trade_score = TradeScore(
            trade_id=trade_id,
            symbol=trade_data.get("symbol", "UNKNOWN"),
            strategy_id=trade_data.get("strategy_id", "UNKNOWN"),
            direction=trade_data.get("direction", "BUY"),
            entry_price=trade_data.get("entry_price", 0),
            exit_price=trade_data.get("exit_price", 0),
            quantity=trade_data.get("quantity", 0),
            pnl=trade_data.get("pnl", 0),
            pnl_percent=trade_data.get("pnl_percent", 0),
            overall_score=overall_score,
            grade=grade,
            dimension_scores=dimension_scores,
            entry_time=trade_data.get("entry_time", datetime.utcnow()),
            exit_time=trade_data.get("exit_time", datetime.utcnow()),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
        
        # Update statistics
        with self._lock:
            self._grade_history.append(trade_score)
            self._grade_counts[grade] += 1
            for dim, score in dimension_scores.items():
                if dim not in self._dimension_averages:
                    self._dimension_averages[dim] = []
                self._dimension_averages[dim].append(score.score)
                # Keep only last 1000
                if len(self._dimension_averages[dim]) > 1000:
                    self._dimension_averages[dim] = self._dimension_averages[dim][-1000:]
        
        logger.info(f"Trade {trade_id} graded: {grade.value} ({overall_score:.1f})")
        return trade_score
    
    def _analyze(
        self,
        dimension_scores: Dict[QualityDimension, DimensionScore],
        overall_score: float,
    ) -> Tuple[List[str], List[str], List[str]]:
        """Analyze trade for strengths, weaknesses, and recommendations."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        for dim, score in dimension_scores.items():
            if score.score >= self.config.excellent_threshold:
                strengths.append(f"{dim.name}: {score.details}")
            elif score.score < self.config.acceptable_threshold:
                weaknesses.append(f"{dim.name}: {score.details}")
                
                # Generate recommendations
                if dim == QualityDimension.ENTRY_TIMING:
                    recommendations.append("Consider waiting for better entry confirmation")
                elif dim == QualityDimension.EXIT_TIMING:
                    recommendations.append("Review exit rules - may be exiting too early/late")
                elif dim == QualityDimension.POSITION_SIZING:
                    recommendations.append("Adjust position sizing based on volatility and confidence")
                elif dim == QualityDimension.RISK_REWARD:
                    recommendations.append("Target higher R:R setups or tighter stops")
                elif dim == QualityDimension.EXECUTION_QUALITY:
                    recommendations.append("Review execution timing and order types")
                elif dim == QualityDimension.SIGNAL_STRENGTH:
                    recommendations.append("Wait for stronger signal confirmation")
                elif dim == QualityDimension.MARKET_ALIGNMENT:
                    recommendations.append("Consider trading with the trend")
        
        return strengths, weaknesses, recommendations
    
    def get_grade_distribution(self) -> Dict[str, int]:
        """Get distribution of grades."""
        return {g.value: c for g, c in self._grade_counts.items()}
    
    def get_dimension_averages(self) -> Dict[str, float]:
        """Get average scores by dimension."""
        averages = {}
        for dim, scores in self._dimension_averages.items():
            if scores:
                averages[dim.name] = statistics.mean(scores)
        return averages
    
    def get_gpa(self) -> float:
        """Get overall GPA (grade point average)."""
        with self._lock:
            if not self._grade_history:
                return 0.0
            
            total_gpa = sum(s.grade.numeric_value for s in self._grade_history)
            return total_gpa / len(self._grade_history)
    
    def get_recent_grades(self, limit: int = 100) -> List[TradeScore]:
        """Get recent trade grades."""
        with self._lock:
            return list(self._grade_history)[-limit:]
    
    def get_strategy_grades(self, strategy_id: str) -> Dict[str, Any]:
        """Get grade summary for a strategy."""
        with self._lock:
            strategy_trades = [s for s in self._grade_history if s.strategy_id == strategy_id]
            
            if not strategy_trades:
                return {"strategy_id": strategy_id, "trade_count": 0}
            
            grades = [t.grade for t in strategy_trades]
            scores = [t.overall_score for t in strategy_trades]
            
            return {
                "strategy_id": strategy_id,
                "trade_count": len(strategy_trades),
                "average_score": statistics.mean(scores),
                "gpa": statistics.mean([g.numeric_value for g in grades]),
                "grade_distribution": {
                    g.value: grades.count(g) for g in TradeGrade if grades.count(g) > 0
                },
                "best_grade": max(grades, key=lambda g: g.numeric_value).value,
                "worst_grade": min(grades, key=lambda g: g.numeric_value).value,
            }
    
    def get_improvement_areas(self) -> List[Dict[str, Any]]:
        """Identify areas needing improvement."""
        averages = self.get_dimension_averages()
        
        improvements = []
        for dim_name, avg_score in sorted(averages.items(), key=lambda x: x[1]):
            if avg_score < self.config.good_threshold:
                improvements.append({
                    "dimension": dim_name,
                    "average_score": avg_score,
                    "gap_to_good": self.config.good_threshold - avg_score,
                    "priority": "HIGH" if avg_score < self.config.acceptable_threshold else "MEDIUM",
                })
        
        return improvements
    
    def get_summary(self) -> Dict[str, Any]:
        """Get grading summary."""
        return {
            "total_trades_graded": sum(self._grade_counts.values()),
            "gpa": self.get_gpa(),
            "grade_distribution": self.get_grade_distribution(),
            "dimension_averages": self.get_dimension_averages(),
            "improvement_areas": self.get_improvement_areas(),
            "passing_rate": self._calculate_passing_rate(),
        }
    
    def _calculate_passing_rate(self) -> float:
        """Calculate percentage of passing grades."""
        total = sum(self._grade_counts.values())
        if total == 0:
            return 0.0
        
        passing = sum(
            count for grade, count in self._grade_counts.items()
            if grade.is_passing
        )
        return passing / total
