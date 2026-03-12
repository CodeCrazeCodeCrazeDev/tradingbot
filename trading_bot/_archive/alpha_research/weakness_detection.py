"""
Root Cause Weakness Detection Module
====================================
Continuously monitor live performance and detect weaknesses:
- Drawdown patterns
- Volatility regime shifts
- Correlation spikes
- Slippage increases
- Execution failure
- Signal drift

Classify root cause and generate new hypotheses, then feed them back into the pipeline.

Author: AlphaAlgo Research Team
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    CausalMechanism,
    FeatureFamily,
    Hypothesis,
    RegimeType,
    WeaknessCategory,
    WeaknessDetection,
    generate_id
)

logger = logging.getLogger(__name__)


class WeaknessSeverity(Enum):
    """Severity levels for detected weaknesses"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RootCauseType(Enum):
    """Types of root causes"""
    MARKET_STRUCTURE = "market_structure"
    REGIME_CHANGE = "regime_change"
    ALPHA_DECAY = "alpha_decay"
    EXECUTION_DEGRADATION = "execution_degradation"
    DATA_QUALITY = "data_quality"
    MODEL_DRIFT = "model_drift"
    CROWDING = "crowding"
    LIQUIDITY_CHANGE = "liquidity_change"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    UNKNOWN = "unknown"


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics"""
    timestamp: datetime
    
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    cumulative_return: float = 0.0
    daily_return: float = 0.0
    
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    
    volatility: float = 0.0
    
    win_rate: float = 0.0
    profit_factor: float = 0.0
    
    avg_slippage_bps: float = 0.0
    execution_success_rate: float = 1.0
    
    signal_strength: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "cumulative_return": self.cumulative_return,
            "daily_return": self.daily_return,
            "current_drawdown": self.current_drawdown,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_slippage_bps": self.avg_slippage_bps,
            "execution_success_rate": self.execution_success_rate,
            "signal_strength": self.signal_strength
        }


@dataclass
class RootCauseAnalysis:
    """Analysis of root cause for a weakness"""
    weakness_id: str
    
    primary_cause: RootCauseType
    confidence: float
    
    contributing_factors: List[RootCauseType] = field(default_factory=list)
    
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    recommended_actions: List[str] = field(default_factory=list)
    
    new_hypothesis: Optional[Hypothesis] = None
    
    def to_dict(self) -> Dict:
        return {
            "weakness_id": self.weakness_id,
            "primary_cause": self.primary_cause.value,
            "confidence": self.confidence,
            "contributing_factors": [f.value for f in self.contributing_factors],
            "evidence": self.evidence,
            "recommended_actions": self.recommended_actions
        }


class DrawdownPatternDetector:
    """
    Detect problematic drawdown patterns.
    
    Patterns:
    - Prolonged drawdown
    - Increasing drawdown frequency
    - Drawdown clustering
    - Recovery failure
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.prolonged_days = self.config.get("prolonged_drawdown_days", 20)
        self.frequency_window = self.config.get("frequency_window_days", 60)
        self.max_drawdown_events = self.config.get("max_drawdown_events", 5)
        self.recovery_threshold = self.config.get("recovery_threshold_pct", 50)
    
    def detect(
        self,
        drawdown_history: List[Tuple[datetime, float]],
        current_drawdown: float
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect drawdown patterns"""
        
        if not drawdown_history:
            return False, "", WeaknessSeverity.LOW
        
        # Check prolonged drawdown
        in_drawdown_days = 0
        for dt, dd in reversed(drawdown_history):
            if dd > 0:
                in_drawdown_days += 1
            else:
                break
        
        if in_drawdown_days >= self.prolonged_days:
            return True, f"Prolonged drawdown for {in_drawdown_days} days", WeaknessSeverity.HIGH
        
        # Check frequency
        recent_cutoff = datetime.utcnow() - timedelta(days=self.frequency_window)
        recent_drawdowns = [
            dd for dt, dd in drawdown_history
            if dt >= recent_cutoff and dd > 5  # Significant drawdowns
        ]
        
        if len(recent_drawdowns) >= self.max_drawdown_events:
            return True, f"{len(recent_drawdowns)} significant drawdowns in {self.frequency_window} days", WeaknessSeverity.MEDIUM
        
        # Check recovery failure
        if current_drawdown > 0:
            peak_drawdown = max(dd for _, dd in drawdown_history[-20:]) if drawdown_history else 0
            if peak_drawdown > 0:
                recovery_pct = (peak_drawdown - current_drawdown) / peak_drawdown * 100
                if recovery_pct < self.recovery_threshold and in_drawdown_days > 10:
                    return True, f"Recovery stalled at {recovery_pct:.1f}%", WeaknessSeverity.MEDIUM
        
        return False, "", WeaknessSeverity.LOW


class VolatilityRegimeDetector:
    """
    Detect volatility regime shifts.
    
    Monitors:
    - Volatility level changes
    - Volatility clustering
    - Volatility breakouts
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.vol_change_threshold = self.config.get("vol_change_threshold", 0.5)  # 50% change
        self.high_vol_percentile = self.config.get("high_vol_percentile", 0.9)
    
    def detect(
        self,
        volatility_history: List[float],
        current_volatility: float
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect volatility regime shifts"""
        
        if len(volatility_history) < 20:
            return False, "", WeaknessSeverity.LOW
        
        # Compute baseline volatility
        baseline_vol = np.mean(volatility_history[-60:]) if len(volatility_history) >= 60 else np.mean(volatility_history)
        
        # Check for significant change
        if baseline_vol > 0:
            vol_change = (current_volatility - baseline_vol) / baseline_vol
            
            if abs(vol_change) > self.vol_change_threshold:
                direction = "increased" if vol_change > 0 else "decreased"
                severity = WeaknessSeverity.HIGH if vol_change > 1.0 else WeaknessSeverity.MEDIUM
                return True, f"Volatility {direction} by {abs(vol_change)*100:.1f}%", severity
        
        # Check for extreme volatility
        vol_percentile = sum(1 for v in volatility_history if v <= current_volatility) / len(volatility_history)
        
        if vol_percentile >= self.high_vol_percentile:
            return True, f"Volatility at {vol_percentile*100:.0f}th percentile", WeaknessSeverity.MEDIUM
        
        return False, "", WeaknessSeverity.LOW


class CorrelationSpikeDetector:
    """
    Detect correlation spikes.
    
    Monitors:
    - Cross-asset correlations
    - Factor correlations
    - Correlation regime changes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.correlation_spike_threshold = self.config.get("correlation_spike_threshold", 0.8)
        self.correlation_change_threshold = self.config.get("correlation_change_threshold", 0.3)
    
    def detect(
        self,
        correlation_history: List[float],
        current_correlation: float
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect correlation spikes"""
        
        if len(correlation_history) < 10:
            return False, "", WeaknessSeverity.LOW
        
        # Check absolute level
        if abs(current_correlation) >= self.correlation_spike_threshold:
            return True, f"Correlation spike to {current_correlation:.2f}", WeaknessSeverity.HIGH
        
        # Check for sudden change
        baseline_corr = np.mean(correlation_history[-20:])
        corr_change = abs(current_correlation - baseline_corr)
        
        if corr_change >= self.correlation_change_threshold:
            return True, f"Correlation changed by {corr_change:.2f}", WeaknessSeverity.MEDIUM
        
        return False, "", WeaknessSeverity.LOW


class SlippageDetector:
    """
    Detect slippage increases.
    
    Monitors:
    - Average slippage
    - Slippage trends
    - Extreme slippage events
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.slippage_increase_threshold = self.config.get("slippage_increase_threshold", 0.5)  # 50% increase
        self.max_slippage_bps = self.config.get("max_slippage_bps", 20)
    
    def detect(
        self,
        slippage_history: List[float],
        current_slippage: float
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect slippage issues"""
        
        if len(slippage_history) < 10:
            return False, "", WeaknessSeverity.LOW
        
        # Check absolute level
        if current_slippage >= self.max_slippage_bps:
            return True, f"Slippage at {current_slippage:.1f} bps exceeds limit", WeaknessSeverity.HIGH
        
        # Check for increase
        baseline_slippage = np.mean(slippage_history[-20:])
        if baseline_slippage > 0:
            slippage_change = (current_slippage - baseline_slippage) / baseline_slippage
            
            if slippage_change >= self.slippage_increase_threshold:
                return True, f"Slippage increased by {slippage_change*100:.1f}%", WeaknessSeverity.MEDIUM
        
        return False, "", WeaknessSeverity.LOW


class ExecutionFailureDetector:
    """
    Detect execution failures.
    
    Monitors:
    - Fill rates
    - Rejection rates
    - Latency issues
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.min_fill_rate = self.config.get("min_fill_rate", 0.95)
        self.max_rejection_rate = self.config.get("max_rejection_rate", 0.05)
    
    def detect(
        self,
        execution_success_rate: float,
        rejection_count: int,
        total_orders: int
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect execution failures"""
        
        # Check fill rate
        if execution_success_rate < self.min_fill_rate:
            severity = WeaknessSeverity.CRITICAL if execution_success_rate < 0.8 else WeaknessSeverity.HIGH
            return True, f"Execution success rate {execution_success_rate*100:.1f}% below threshold", severity
        
        # Check rejection rate
        if total_orders > 0:
            rejection_rate = rejection_count / total_orders
            if rejection_rate > self.max_rejection_rate:
                return True, f"Rejection rate {rejection_rate*100:.1f}% exceeds limit", WeaknessSeverity.MEDIUM
        
        return False, "", WeaknessSeverity.LOW


class SignalDriftDetector:
    """
    Detect signal drift.
    
    Monitors:
    - Signal strength degradation
    - Signal-return correlation
    - Signal distribution changes
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Thresholds
        self.strength_decay_threshold = self.config.get("strength_decay_threshold", 0.3)
        self.correlation_decay_threshold = self.config.get("correlation_decay_threshold", 0.5)
    
    def detect(
        self,
        signal_strength_history: List[float],
        signal_return_correlation: float
    ) -> Tuple[bool, str, WeaknessSeverity]:
        """Detect signal drift"""
        
        if len(signal_strength_history) < 20:
            return False, "", WeaknessSeverity.LOW
        
        # Check strength decay
        initial_strength = np.mean(signal_strength_history[:10])
        recent_strength = np.mean(signal_strength_history[-10:])
        
        if initial_strength > 0:
            strength_decay = (initial_strength - recent_strength) / initial_strength
            
            if strength_decay >= self.strength_decay_threshold:
                return True, f"Signal strength decayed by {strength_decay*100:.1f}%", WeaknessSeverity.MEDIUM
        
        # Check signal-return correlation
        if signal_return_correlation < self.correlation_decay_threshold:
            return True, f"Signal-return correlation dropped to {signal_return_correlation:.2f}", WeaknessSeverity.HIGH
        
        return False, "", WeaknessSeverity.LOW


class RootCauseAnalyzer:
    """
    Analyze root causes of detected weaknesses.
    
    Combines evidence from multiple detectors to identify
    the primary cause and contributing factors.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def analyze(
        self,
        weakness: WeaknessDetection,
        performance_history: List[PerformanceSnapshot],
        market_data: Optional[pd.DataFrame] = None
    ) -> RootCauseAnalysis:
        """Analyze root cause of weakness"""
        
        evidence = {}
        contributing_factors = []
        
        # Analyze based on weakness category
        if weakness.category == WeaknessCategory.DRAWDOWN:
            primary_cause, evidence = self._analyze_drawdown(performance_history)
        
        elif weakness.category == WeaknessCategory.VOLATILITY:
            primary_cause, evidence = self._analyze_volatility(performance_history, market_data)
        
        elif weakness.category == WeaknessCategory.CORRELATION:
            primary_cause, evidence = self._analyze_correlation(performance_history)
        
        elif weakness.category == WeaknessCategory.SLIPPAGE:
            primary_cause, evidence = self._analyze_slippage(performance_history)
        
        elif weakness.category == WeaknessCategory.EXECUTION:
            primary_cause, evidence = self._analyze_execution(performance_history)
        
        elif weakness.category == WeaknessCategory.SIGNAL_DRIFT:
            primary_cause, evidence = self._analyze_signal_drift(performance_history)
        
        else:
            primary_cause = RootCauseType.UNKNOWN
        
        # Generate recommended actions
        actions = self._generate_actions(primary_cause, weakness.severity)
        
        # Compute confidence
        confidence = self._compute_confidence(evidence)
        
        return RootCauseAnalysis(
            weakness_id=weakness.detection_id,
            primary_cause=primary_cause,
            confidence=confidence,
            contributing_factors=contributing_factors,
            evidence=evidence,
            recommended_actions=actions
        )
    
    def _analyze_drawdown(
        self,
        history: List[PerformanceSnapshot]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze drawdown root cause"""
        evidence = {}
        
        if not history:
            return RootCauseType.UNKNOWN, evidence
        
        recent = history[-20:]
        
        # Check for volatility spike
        vol_increase = False
        if len(recent) >= 2:
            initial_vol = np.mean([s.volatility for s in recent[:5]])
            recent_vol = np.mean([s.volatility for s in recent[-5:]])
            if initial_vol > 0 and (recent_vol - initial_vol) / initial_vol > 0.5:
                vol_increase = True
                evidence["volatility_increase"] = (recent_vol - initial_vol) / initial_vol
        
        if vol_increase:
            return RootCauseType.REGIME_CHANGE, evidence
        
        # Check for signal degradation
        signal_decay = False
        if len(recent) >= 2:
            initial_signal = np.mean([s.signal_strength for s in recent[:5]])
            recent_signal = np.mean([s.signal_strength for s in recent[-5:]])
            if initial_signal > 0 and (initial_signal - recent_signal) / initial_signal > 0.3:
                signal_decay = True
                evidence["signal_decay"] = (initial_signal - recent_signal) / initial_signal
        
        if signal_decay:
            return RootCauseType.ALPHA_DECAY, evidence
        
        return RootCauseType.MARKET_STRUCTURE, evidence
    
    def _analyze_volatility(
        self,
        history: List[PerformanceSnapshot],
        market_data: Optional[pd.DataFrame]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze volatility root cause"""
        evidence = {}
        
        return RootCauseType.REGIME_CHANGE, evidence
    
    def _analyze_correlation(
        self,
        history: List[PerformanceSnapshot]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze correlation root cause"""
        evidence = {}
        
        return RootCauseType.CORRELATION_BREAKDOWN, evidence
    
    def _analyze_slippage(
        self,
        history: List[PerformanceSnapshot]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze slippage root cause"""
        evidence = {}
        
        if not history:
            return RootCauseType.UNKNOWN, evidence
        
        recent = history[-20:]
        
        # Check for liquidity issues
        avg_slippage = np.mean([s.avg_slippage_bps for s in recent])
        evidence["avg_slippage_bps"] = avg_slippage
        
        if avg_slippage > 15:
            return RootCauseType.LIQUIDITY_CHANGE, evidence
        
        return RootCauseType.EXECUTION_DEGRADATION, evidence
    
    def _analyze_execution(
        self,
        history: List[PerformanceSnapshot]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze execution root cause"""
        evidence = {}
        
        return RootCauseType.EXECUTION_DEGRADATION, evidence
    
    def _analyze_signal_drift(
        self,
        history: List[PerformanceSnapshot]
    ) -> Tuple[RootCauseType, Dict]:
        """Analyze signal drift root cause"""
        evidence = {}
        
        return RootCauseType.MODEL_DRIFT, evidence
    
    def _generate_actions(
        self,
        cause: RootCauseType,
        severity: str
    ) -> List[str]:
        """Generate recommended actions"""
        actions = []
        
        action_map = {
            RootCauseType.REGIME_CHANGE: [
                "Reduce position size",
                "Re-evaluate regime conditions",
                "Consider temporary pause"
            ],
            RootCauseType.ALPHA_DECAY: [
                "Prepare replacement alpha",
                "Reduce allocation",
                "Investigate decay cause"
            ],
            RootCauseType.EXECUTION_DEGRADATION: [
                "Review execution parameters",
                "Check venue connectivity",
                "Consider alternative execution"
            ],
            RootCauseType.LIQUIDITY_CHANGE: [
                "Reduce order sizes",
                "Extend execution horizon",
                "Review capacity limits"
            ],
            RootCauseType.CORRELATION_BREAKDOWN: [
                "Review portfolio correlations",
                "Reduce correlated positions",
                "Update correlation model"
            ],
            RootCauseType.MODEL_DRIFT: [
                "Retrain model",
                "Review feature stability",
                "Check data quality"
            ]
        }
        
        actions = action_map.get(cause, ["Investigate further"])
        
        if severity == "critical":
            actions.insert(0, "IMMEDIATE: Reduce exposure to minimum")
        
        return actions
    
    def _compute_confidence(self, evidence: Dict) -> float:
        """Compute confidence in root cause analysis"""
        if not evidence:
            return 0.5
        
        # More evidence = higher confidence
        confidence = min(0.9, 0.5 + len(evidence) * 0.1)
        return confidence


class HypothesisGenerator:
    """
    Generate new hypotheses from detected weaknesses.
    
    Feeds learnings back into the research pipeline.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def generate(
        self,
        weakness: WeaknessDetection,
        analysis: RootCauseAnalysis,
        family: FeatureFamily
    ) -> Optional[Hypothesis]:
        """Generate new hypothesis from weakness"""
        
        # Create causal mechanism from analysis
        cause = self._cause_to_string(analysis.primary_cause)
        effect = f"degradation in {family.alpha_source} alpha"
        
        conditions = []
        for factor in analysis.contributing_factors:
            conditions.append(self._cause_to_string(factor))
        
        mechanism = CausalMechanism(
            cause=cause,
            effect=effect,
            conditions=conditions,
            confidence=analysis.confidence,
            evidence_strength="moderate"
        )
        
        # Create hypothesis
        hypothesis = Hypothesis(
            hypothesis_id=generate_id("hyp"),
            paper_id=f"weakness_{weakness.detection_id}",
            statement=f"{cause} causes {effect}",
            causal_mechanism=mechanism,
            required_data=["price", "volume"],
            feature_definitions={
                "weakness_indicator": f"Indicator for {analysis.primary_cause.value}"
            },
            regime_sensitivity=family.regime_conditions,
            failure_conditions=[weakness.description],
            testable=True,
            test_methodology="Analyze historical weakness patterns"
        )
        
        return hypothesis
    
    def _cause_to_string(self, cause: RootCauseType) -> str:
        """Convert root cause to string"""
        cause_strings = {
            RootCauseType.MARKET_STRUCTURE: "market structure change",
            RootCauseType.REGIME_CHANGE: "regime shift",
            RootCauseType.ALPHA_DECAY: "alpha decay",
            RootCauseType.EXECUTION_DEGRADATION: "execution quality degradation",
            RootCauseType.DATA_QUALITY: "data quality issues",
            RootCauseType.MODEL_DRIFT: "model drift",
            RootCauseType.CROWDING: "strategy crowding",
            RootCauseType.LIQUIDITY_CHANGE: "liquidity conditions change",
            RootCauseType.CORRELATION_BREAKDOWN: "correlation breakdown"
        }
        return cause_strings.get(cause, "unknown factor")


class WeaknessDetectionEngine:
    """
    Main engine for weakness detection.
    
    Coordinates:
    - Multiple weakness detectors
    - Root cause analysis
    - Hypothesis generation
    - Feedback to research pipeline
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize detectors
        self.drawdown_detector = DrawdownPatternDetector(config)
        self.volatility_detector = VolatilityRegimeDetector(config)
        self.correlation_detector = CorrelationSpikeDetector(config)
        self.slippage_detector = SlippageDetector(config)
        self.execution_detector = ExecutionFailureDetector(config)
        self.signal_detector = SignalDriftDetector(config)
        
        # Initialize analyzers
        self.root_cause_analyzer = RootCauseAnalyzer(config)
        self.hypothesis_generator = HypothesisGenerator(config)
        
        # State
        self.performance_history: Dict[str, List[PerformanceSnapshot]] = {}
        self.detected_weaknesses: List[WeaknessDetection] = []
        self.generated_hypotheses: List[Hypothesis] = []
        
        logger.info("Weakness Detection Engine initialized")
    
    def record_performance(
        self,
        family_id: str,
        snapshot: PerformanceSnapshot
    ):
        """Record performance snapshot"""
        if family_id not in self.performance_history:
            self.performance_history[family_id] = []
        
        self.performance_history[family_id].append(snapshot)
        
        # Keep last 252 days (1 year)
        if len(self.performance_history[family_id]) > 252:
            self.performance_history[family_id] = self.performance_history[family_id][-252:]
    
    def detect_weaknesses(
        self,
        family_id: str,
        current_snapshot: PerformanceSnapshot,
        market_data: Optional[pd.DataFrame] = None
    ) -> List[WeaknessDetection]:
        """Detect all weaknesses for a family"""
        
        weaknesses = []
        history = self.performance_history.get(family_id, [])
        
        # Drawdown detection
        drawdown_history = [(s.timestamp, s.current_drawdown) for s in history]
        detected, message, severity = self.drawdown_detector.detect(
            drawdown_history,
            current_snapshot.current_drawdown
        )
        if detected:
            weakness = self._create_weakness(
                family_id,
                WeaknessCategory.DRAWDOWN,
                severity.value,
                message,
                "Drawdown pattern indicates potential issues",
                current_snapshot
            )
            weaknesses.append(weakness)
        
        # Volatility detection
        vol_history = [s.volatility for s in history]
        detected, message, severity = self.volatility_detector.detect(
            vol_history,
            current_snapshot.volatility
        )
        if detected:
            weakness = self._create_weakness(
                family_id,
                WeaknessCategory.VOLATILITY,
                severity.value,
                message,
                "Volatility regime shift detected",
                current_snapshot
            )
            weaknesses.append(weakness)
        
        # Slippage detection
        slippage_history = [s.avg_slippage_bps for s in history]
        detected, message, severity = self.slippage_detector.detect(
            slippage_history,
            current_snapshot.avg_slippage_bps
        )
        if detected:
            weakness = self._create_weakness(
                family_id,
                WeaknessCategory.SLIPPAGE,
                severity.value,
                message,
                "Slippage increase indicates liquidity or execution issues",
                current_snapshot
            )
            weaknesses.append(weakness)
        
        # Execution detection
        detected, message, severity = self.execution_detector.detect(
            current_snapshot.execution_success_rate,
            0,  # rejection count
            100  # total orders
        )
        if detected:
            weakness = self._create_weakness(
                family_id,
                WeaknessCategory.EXECUTION,
                severity.value,
                message,
                "Execution quality degradation",
                current_snapshot
            )
            weaknesses.append(weakness)
        
        # Signal drift detection
        signal_history = [s.signal_strength for s in history]
        detected, message, severity = self.signal_detector.detect(
            signal_history,
            0.5  # placeholder correlation
        )
        if detected:
            weakness = self._create_weakness(
                family_id,
                WeaknessCategory.SIGNAL_DRIFT,
                severity.value,
                message,
                "Signal drift indicates model degradation",
                current_snapshot
            )
            weaknesses.append(weakness)
        
        # Store detected weaknesses
        self.detected_weaknesses.extend(weaknesses)
        
        return weaknesses
    
    def _create_weakness(
        self,
        family_id: str,
        category: WeaknessCategory,
        severity: str,
        description: str,
        root_cause: str,
        snapshot: PerformanceSnapshot
    ) -> WeaknessDetection:
        """Create weakness detection record"""
        return WeaknessDetection(
            detection_id=generate_id("weak"),
            family_id=family_id,
            category=category,
            severity=severity,
            description=description,
            root_cause=root_cause,
            metrics_at_detection=snapshot.to_dict()
        )
    
    def analyze_and_generate_hypothesis(
        self,
        weakness: WeaknessDetection,
        family: FeatureFamily,
        market_data: Optional[pd.DataFrame] = None
    ) -> Tuple[RootCauseAnalysis, Optional[Hypothesis]]:
        """Analyze weakness and generate new hypothesis"""
        
        history = self.performance_history.get(weakness.family_id, [])
        
        # Analyze root cause
        analysis = self.root_cause_analyzer.analyze(
            weakness,
            history,
            market_data
        )
        
        # Generate hypothesis
        hypothesis = self.hypothesis_generator.generate(
            weakness,
            analysis,
            family
        )
        
        if hypothesis:
            weakness.new_hypothesis_generated = True
            weakness.new_hypothesis_id = hypothesis.hypothesis_id
            self.generated_hypotheses.append(hypothesis)
        
        return analysis, hypothesis
    
    def get_detected_weaknesses(self, family_id: Optional[str] = None) -> List[WeaknessDetection]:
        """Get detected weaknesses"""
        if family_id:
            return [w for w in self.detected_weaknesses if w.family_id == family_id]
        return self.detected_weaknesses
    
    def get_generated_hypotheses(self) -> List[Hypothesis]:
        """Get hypotheses generated from weaknesses"""
        return self.generated_hypotheses
    
    def clear_old_weaknesses(self, days: int = 30):
        """Clear old weakness records"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.detected_weaknesses = [
            w for w in self.detected_weaknesses
            if w.detected_at >= cutoff
        ]


def create_weakness_engine(config: Optional[Dict] = None) -> WeaknessDetectionEngine:
    """Factory function to create weakness detection engine"""
    return WeaknessDetectionEngine(config)
