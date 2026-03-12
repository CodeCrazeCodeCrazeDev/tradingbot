"""
from typing import Dict, List, Optional, Set
Strategy Diagnostics Module
===========================
Comprehensive strategy health monitoring and diagnostics.

For every strategy tracks:
- Signal strength consistency
- Out-of-sample decay rate
- Market regime sensitivity
- Slippage sensitivity
- Execution fragility

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
import threading

import numpy as np
import pandas as pd

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Strategy health status"""
    HEALTHY = auto()
    WARNING = auto()
    DEGRADED = auto()
    CRITICAL = auto()
    FAILED = auto()


@dataclass
class SignalConsistency:
    """Signal strength consistency metrics"""
    timestamp: datetime
    strategy_name: str
    
    # Consistency metrics
    signal_variance: float = 0.0
    signal_autocorrelation: float = 0.0
    flip_rate: float = 0.0  # How often signal changes direction
    
    # Strength metrics
    avg_signal_strength: float = 0.0
    strength_decay: float = 0.0
    
    # Quality
    consistency_score: float = 0.0


@dataclass
class OOSDecay:
    """Out-of-sample decay metrics"""
    timestamp: datetime
    strategy_name: str
    
    # Performance comparison
    in_sample_sharpe: float = 0.0
    out_sample_sharpe: float = 0.0
    sharpe_decay: float = 0.0
    
    in_sample_win_rate: float = 0.0
    out_sample_win_rate: float = 0.0
    win_rate_decay: float = 0.0
    
    # Decay rate
    decay_rate_per_day: float = 0.0
    half_life_days: float = 0.0
    
    # Status
    is_decaying: bool = False


@dataclass
class RegimeSensitivity:
    """Market regime sensitivity"""
    timestamp: datetime
    strategy_name: str
    
    # Performance by regime
    regime_performance: Dict[str, float] = field(default_factory=dict)
    regime_sharpe: Dict[str, float] = field(default_factory=dict)
    
    # Sensitivity
    regime_sensitivity_score: float = 0.0  # High = very sensitive
    best_regime: str = ""
    worst_regime: str = ""
    
    # Current regime fit
    current_regime: str = ""
    current_regime_fit: float = 0.0


@dataclass
class SlippageSensitivity:
    """Slippage sensitivity analysis"""
    timestamp: datetime
    strategy_name: str
    
    # Slippage metrics
    avg_slippage_bps: float = 0.0
    slippage_variance: float = 0.0
    
    # Impact on performance
    gross_sharpe: float = 0.0
    net_sharpe: float = 0.0
    slippage_cost_pct: float = 0.0
    
    # Sensitivity
    breakeven_slippage_bps: float = 0.0
    slippage_sensitivity: float = 0.0  # How much perf degrades per bp


@dataclass
class ExecutionFragility:
    """Execution fragility metrics"""
    timestamp: datetime
    strategy_name: str
    
    # Fill metrics
    fill_rate: float = 0.0
    partial_fill_rate: float = 0.0
    rejection_rate: float = 0.0
    
    # Timing sensitivity
    timing_sensitivity: float = 0.0  # How much delay hurts
    latency_impact: float = 0.0
    
    # Fragility score
    fragility_score: float = 0.0  # High = fragile


@dataclass
class StrategyDiagnostics:
    """Complete strategy diagnostics"""
    timestamp: datetime
    strategy_name: str
    
    # Component diagnostics
    signal_consistency: SignalConsistency = None
    oos_decay: OOSDecay = None
    regime_sensitivity: RegimeSensitivity = None
    slippage_sensitivity: SlippageSensitivity = None
    execution_fragility: ExecutionFragility = None
    
    # Overall health
    health_status: HealthStatus = HealthStatus.HEALTHY
    health_score: float = 1.0
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Action
    should_disable: bool = False
    should_reduce_size: bool = False


class SignalConsistencyAnalyzer:
    """Analyze signal consistency"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.signal_history: Dict[str, deque] = {}
        
    def add_signal(self, strategy_name: str, signal: float, timestamp: datetime = None):
        """Add signal to history"""
        
        if strategy_name not in self.signal_history:
            self.signal_history[strategy_name] = deque(maxlen=1000)
        
        self.signal_history[strategy_name].append({
            'timestamp': timestamp or datetime.now(),
            'signal': signal
        })
    
    def analyze(self, strategy_name: str) -> SignalConsistency:
        """Analyze signal consistency"""
        
        if strategy_name not in self.signal_history:
            return SignalConsistency(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        history = list(self.signal_history[strategy_name])
        
        if len(history) < 20:
            return SignalConsistency(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        signals = [h['signal'] for h in history]
        
        # Variance
        signal_variance = np.var(signals)
        
        # Autocorrelation
        if len(signals) > 1:
            autocorr = np.corrcoef(signals[:-1], signals[1:])[0, 1]
            signal_autocorrelation = autocorr if not np.isnan(autocorr) else 0
        else:
            signal_autocorrelation = 0
        
        # Flip rate
        sign_changes = sum(1 for i in range(1, len(signals)) 
                         if np.sign(signals[i]) != np.sign(signals[i-1]))
        flip_rate = sign_changes / len(signals)
        
        # Average strength
        avg_signal_strength = np.mean(np.abs(signals))
        
        # Strength decay (compare recent to older)
        if len(signals) >= 50:
            old_strength = np.mean(np.abs(signals[:25]))
            new_strength = np.mean(np.abs(signals[-25:]))
            strength_decay = (old_strength - new_strength) / (old_strength + 1e-10)
        else:
            strength_decay = 0
        
        # Consistency score
        # High autocorr, low flip rate, stable strength = consistent
        consistency_score = (
            0.3 * (1 - flip_rate) +
            0.3 * max(signal_autocorrelation, 0) +
            0.2 * (1 - min(signal_variance, 1)) +
            0.2 * (1 - abs(strength_decay))
        )
        
        return SignalConsistency(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            signal_variance=signal_variance,
            signal_autocorrelation=signal_autocorrelation,
            flip_rate=flip_rate,
            avg_signal_strength=avg_signal_strength,
            strength_decay=strength_decay,
            consistency_score=consistency_score
        )


class OOSDecayAnalyzer:
    """Analyze out-of-sample decay"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.performance_history: Dict[str, deque] = {}
        self.baseline_performance: Dict[str, Dict] = {}
        
    def set_baseline(self, strategy_name: str, sharpe: float, win_rate: float):
        """Set in-sample baseline"""
        self.baseline_performance[strategy_name] = {
            'sharpe': sharpe,
            'win_rate': win_rate,
            'timestamp': datetime.now()
        }
    
    def add_performance(
        self,
        strategy_name: str,
        sharpe: float,
        win_rate: float,
        timestamp: datetime = None
    ):
        """Add performance observation"""
        
        if strategy_name not in self.performance_history:
            self.performance_history[strategy_name] = deque(maxlen=500)
        
        self.performance_history[strategy_name].append({
            'timestamp': timestamp or datetime.now(),
            'sharpe': sharpe,
            'win_rate': win_rate
        })
    
    def analyze(self, strategy_name: str) -> OOSDecay:
        """Analyze OOS decay"""
        
        if strategy_name not in self.baseline_performance:
            return OOSDecay(timestamp=datetime.now(), strategy_name=strategy_name)
        
        if strategy_name not in self.performance_history:
            return OOSDecay(timestamp=datetime.now(), strategy_name=strategy_name)
        
        baseline = self.baseline_performance[strategy_name]
        history = list(self.performance_history[strategy_name])
        
        if len(history) < 10:
            return OOSDecay(timestamp=datetime.now(), strategy_name=strategy_name)
        
        # Current performance
        recent = history[-20:]
        current_sharpe = np.mean([h['sharpe'] for h in recent])
        current_win_rate = np.mean([h['win_rate'] for h in recent])
        
        # Decay
        sharpe_decay = (baseline['sharpe'] - current_sharpe) / (baseline['sharpe'] + 1e-10)
        win_rate_decay = baseline['win_rate'] - current_win_rate
        
        # Decay rate
        sharpes = [h['sharpe'] for h in history]
        if len(sharpes) >= 10:
            days = [(h['timestamp'] - history[0]['timestamp']).days for h in history]
            if max(days) > 0:
                slope = np.polyfit(days, sharpes, 1)[0]
                decay_rate_per_day = -slope
            else:
                decay_rate_per_day = 0
        else:
            decay_rate_per_day = 0
        
        # Half-life
        if decay_rate_per_day > 0 and baseline['sharpe'] > 0:
            half_life_days = baseline['sharpe'] / 2 / decay_rate_per_day
        else:
            half_life_days = float('inf')
        
        is_decaying = sharpe_decay > 0.2 or win_rate_decay > 0.05
        
        return OOSDecay(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            in_sample_sharpe=baseline['sharpe'],
            out_sample_sharpe=current_sharpe,
            sharpe_decay=sharpe_decay,
            in_sample_win_rate=baseline['win_rate'],
            out_sample_win_rate=current_win_rate,
            win_rate_decay=win_rate_decay,
            decay_rate_per_day=decay_rate_per_day,
            half_life_days=half_life_days,
            is_decaying=is_decaying
        )


class RegimeSensitivityAnalyzer:
    """Analyze regime sensitivity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.regime_performance: Dict[str, Dict[str, List]] = {}
        
    def add_performance(
        self,
        strategy_name: str,
        regime: str,
        return_: float,
        sharpe: float = None
    ):
        """Add performance for a regime"""
        
        if strategy_name not in self.regime_performance:
            self.regime_performance[strategy_name] = {}
        
        if regime not in self.regime_performance[strategy_name]:
            self.regime_performance[strategy_name][regime] = []
        
        self.regime_performance[strategy_name][regime].append({
            'return': return_,
            'sharpe': sharpe,
            'timestamp': datetime.now()
        })
    
    def analyze(self, strategy_name: str, current_regime: str = "") -> RegimeSensitivity:
        """Analyze regime sensitivity"""
        
        if strategy_name not in self.regime_performance:
            return RegimeSensitivity(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        regime_data = self.regime_performance[strategy_name]
        
        if not regime_data:
            return RegimeSensitivity(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        # Calculate performance by regime
        regime_perf = {}
        regime_sharpe = {}
        
        for regime, data in regime_data.items():
            if len(data) >= 5:
                returns = [d['return'] for d in data]
                regime_perf[regime] = np.mean(returns)
                
                if data[0].get('sharpe') is not None:
                    sharpes = [d['sharpe'] for d in data if d.get('sharpe') is not None]
                    regime_sharpe[regime] = np.mean(sharpes) if sharpes else 0
                else:
                    regime_sharpe[regime] = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
        
        if not regime_perf:
            return RegimeSensitivity(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        # Sensitivity score (variance across regimes)
        perfs = list(regime_perf.values())
        sensitivity_score = np.std(perfs) / (np.mean(np.abs(perfs)) + 1e-10)
        
        # Best and worst regimes
        best_regime = max(regime_perf.items(), key=lambda x: x[1])[0]
        worst_regime = min(regime_perf.items(), key=lambda x: x[1])[0]
        
        # Current regime fit
        if current_regime and current_regime in regime_perf:
            current_regime_fit = regime_perf[current_regime] / (max(perfs) + 1e-10)
        else:
            current_regime_fit = 0.5
        
        return RegimeSensitivity(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            regime_performance=regime_perf,
            regime_sharpe=regime_sharpe,
            regime_sensitivity_score=sensitivity_score,
            best_regime=best_regime,
            worst_regime=worst_regime,
            current_regime=current_regime,
            current_regime_fit=current_regime_fit
        )


class SlippageSensitivityAnalyzer:
    """Analyze slippage sensitivity"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trade_history: Dict[str, deque] = {}
        
    def add_trade(
        self,
        strategy_name: str,
        gross_return: float,
        slippage_bps: float,
        timestamp: datetime = None
    ):
        """Add trade with slippage"""
        
        if strategy_name not in self.trade_history:
            self.trade_history[strategy_name] = deque(maxlen=1000)
        
        self.trade_history[strategy_name].append({
            'timestamp': timestamp or datetime.now(),
            'gross_return': gross_return,
            'slippage_bps': slippage_bps,
            'net_return': gross_return - slippage_bps / 10000
        })
    
    def analyze(self, strategy_name: str) -> SlippageSensitivity:
        """Analyze slippage sensitivity"""
        
        if strategy_name not in self.trade_history:
            return SlippageSensitivity(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        history = list(self.trade_history[strategy_name])
        
        if len(history) < 20:
            return SlippageSensitivity(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        # Slippage metrics
        slippages = [h['slippage_bps'] for h in history]
        avg_slippage = np.mean(slippages)
        slippage_variance = np.var(slippages)
        
        # Performance impact
        gross_returns = [h['gross_return'] for h in history]
        net_returns = [h['net_return'] for h in history]
        
        gross_sharpe = np.mean(gross_returns) / (np.std(gross_returns) + 1e-10) * np.sqrt(252)
        net_sharpe = np.mean(net_returns) / (np.std(net_returns) + 1e-10) * np.sqrt(252)
        
        # Slippage cost as % of gross return
        total_gross = sum(gross_returns)
        total_slippage = sum(s / 10000 for s in slippages)
        slippage_cost_pct = total_slippage / (abs(total_gross) + 1e-10)
        
        # Breakeven slippage
        avg_gross = np.mean(gross_returns)
        breakeven_slippage = avg_gross * 10000 if avg_gross > 0 else 0
        
        # Sensitivity (sharpe decay per bp of slippage)
        if avg_slippage > 0:
            slippage_sensitivity = (gross_sharpe - net_sharpe) / avg_slippage
        else:
            slippage_sensitivity = 0
        
        return SlippageSensitivity(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            avg_slippage_bps=avg_slippage,
            slippage_variance=slippage_variance,
            gross_sharpe=gross_sharpe,
            net_sharpe=net_sharpe,
            slippage_cost_pct=slippage_cost_pct,
            breakeven_slippage_bps=breakeven_slippage,
            slippage_sensitivity=slippage_sensitivity
        )


class ExecutionFragilityAnalyzer:
    """Analyze execution fragility"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.execution_history: Dict[str, deque] = {}
        
    def add_execution(
        self,
        strategy_name: str,
        filled: bool,
        partial: bool,
        rejected: bool,
        delay_ms: float,
        return_impact: float,  # How much delay affected return
        timestamp: datetime = None
    ):
        """Add execution record"""
        
        if strategy_name not in self.execution_history:
            self.execution_history[strategy_name] = deque(maxlen=1000)
        
        self.execution_history[strategy_name].append({
            'timestamp': timestamp or datetime.now(),
            'filled': filled,
            'partial': partial,
            'rejected': rejected,
            'delay_ms': delay_ms,
            'return_impact': return_impact
        })
    
    def analyze(self, strategy_name: str) -> ExecutionFragility:
        """Analyze execution fragility"""
        
        if strategy_name not in self.execution_history:
            return ExecutionFragility(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        history = list(self.execution_history[strategy_name])
        
        if len(history) < 20:
            return ExecutionFragility(
                timestamp=datetime.now(),
                strategy_name=strategy_name
            )
        
        # Fill metrics
        fill_rate = sum(1 for h in history if h['filled']) / len(history)
        partial_fill_rate = sum(1 for h in history if h['partial']) / len(history)
        rejection_rate = sum(1 for h in history if h['rejected']) / len(history)
        
        # Timing sensitivity
        delays = [h['delay_ms'] for h in history]
        impacts = [h['return_impact'] for h in history]
        
        if SCIPY_AVAILABLE and len(delays) > 10:
            corr, _ = stats.pearsonr(delays, impacts)
            timing_sensitivity = abs(corr) if not np.isnan(corr) else 0
        else:
            timing_sensitivity = 0
        
        # Latency impact
        latency_impact = np.mean([abs(h['return_impact']) for h in history if h['delay_ms'] > 100])
        
        # Fragility score
        fragility_score = (
            0.3 * (1 - fill_rate) +
            0.2 * partial_fill_rate +
            0.2 * rejection_rate +
            0.15 * timing_sensitivity +
            0.15 * min(latency_impact * 100, 1)
        )
        
        return ExecutionFragility(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            fill_rate=fill_rate,
            partial_fill_rate=partial_fill_rate,
            rejection_rate=rejection_rate,
            timing_sensitivity=timing_sensitivity,
            latency_impact=latency_impact,
            fragility_score=fragility_score
        )


class StrategyDiagnosticsSystem:
    """
    Complete Strategy Diagnostics System.
    
    Tracks for every strategy:
    - Signal strength consistency
    - Out-of-sample decay rate
    - Market regime sensitivity
    - Slippage sensitivity
    - Execution fragility
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Analyzers
        self.signal_analyzer = SignalConsistencyAnalyzer(config)
        self.oos_analyzer = OOSDecayAnalyzer(config)
        self.regime_analyzer = RegimeSensitivityAnalyzer(config)
        self.slippage_analyzer = SlippageSensitivityAnalyzer(config)
        self.execution_analyzer = ExecutionFragilityAnalyzer(config)
        
        # Diagnostics history
        self.diagnostics_history: Dict[str, List[StrategyDiagnostics]] = {}
        
        logger.info("StrategyDiagnosticsSystem initialized")
    
    def run_diagnostics(
        self,
        strategy_name: str,
        current_regime: str = ""
    ) -> StrategyDiagnostics:
        """Run full diagnostics for a strategy"""
        
        # Run all analyzers
        signal = self.signal_analyzer.analyze(strategy_name)
        oos = self.oos_analyzer.analyze(strategy_name)
        regime = self.regime_analyzer.analyze(strategy_name, current_regime)
        slippage = self.slippage_analyzer.analyze(strategy_name)
        execution = self.execution_analyzer.analyze(strategy_name)
        
        # Calculate overall health
        health_score = self._calculate_health_score(signal, oos, regime, slippage, execution)
        health_status = self._determine_health_status(health_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(signal, oos, regime, slippage, execution)
        
        # Determine actions
        should_disable = health_status in [HealthStatus.CRITICAL, HealthStatus.FAILED]
        should_reduce_size = health_status == HealthStatus.DEGRADED
        
        diagnostics = StrategyDiagnostics(
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            signal_consistency=signal,
            oos_decay=oos,
            regime_sensitivity=regime,
            slippage_sensitivity=slippage,
            execution_fragility=execution,
            health_status=health_status,
            health_score=health_score,
            recommendations=recommendations,
            should_disable=should_disable,
            should_reduce_size=should_reduce_size
        )
        
        # Store in history
        if strategy_name not in self.diagnostics_history:
            self.diagnostics_history[strategy_name] = []
        self.diagnostics_history[strategy_name].append(diagnostics)
        
        return diagnostics
    
    def _calculate_health_score(
        self,
        signal: SignalConsistency,
        oos: OOSDecay,
        regime: RegimeSensitivity,
        slippage: SlippageSensitivity,
        execution: ExecutionFragility
    ) -> float:
        """Calculate overall health score"""
        
        scores = []
        
        # Signal consistency (higher = better)
        scores.append(signal.consistency_score)
        
        # OOS decay (lower decay = better)
        oos_score = 1 - min(abs(oos.sharpe_decay), 1)
        scores.append(oos_score)
        
        # Regime sensitivity (lower = better, more robust)
        regime_score = 1 - min(regime.regime_sensitivity_score, 1)
        scores.append(regime_score)
        
        # Slippage (lower cost = better)
        slippage_score = 1 - min(slippage.slippage_cost_pct, 1)
        scores.append(slippage_score)
        
        # Execution (lower fragility = better)
        execution_score = 1 - execution.fragility_score
        scores.append(execution_score)
        
        return np.mean(scores)
    
    def _determine_health_status(self, score: float) -> HealthStatus:
        """Determine health status from score"""
        
        if score >= 0.8:
            return HealthStatus.HEALTHY
        elif score >= 0.6:
            return HealthStatus.WARNING
        elif score >= 0.4:
            return HealthStatus.DEGRADED
        elif score >= 0.2:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.FAILED
    
    def _generate_recommendations(
        self,
        signal: SignalConsistency,
        oos: OOSDecay,
        regime: RegimeSensitivity,
        slippage: SlippageSensitivity,
        execution: ExecutionFragility
    ) -> List[str]:
        """Generate recommendations"""
        
        recommendations = []
        
        # Signal recommendations
        if signal.flip_rate > 0.3:
            recommendations.append("High signal flip rate - consider adding smoothing")
        if signal.strength_decay > 0.2:
            recommendations.append("Signal strength decaying - review feature relevance")
        
        # OOS recommendations
        if oos.is_decaying:
            recommendations.append(f"Strategy is decaying (half-life: {oos.half_life_days:.0f} days) - consider retraining")
        if oos.sharpe_decay > 0.5:
            recommendations.append("Severe Sharpe decay - immediate review needed")
        
        # Regime recommendations
        if regime.regime_sensitivity_score > 0.5:
            recommendations.append(f"High regime sensitivity - best in {regime.best_regime}, worst in {regime.worst_regime}")
        if regime.current_regime_fit < 0.3:
            recommendations.append("Poor fit for current regime - consider reducing exposure")
        
        # Slippage recommendations
        if slippage.slippage_cost_pct > 0.3:
            recommendations.append("High slippage cost - review execution or increase signal threshold")
        if slippage.net_sharpe < 0.5 and slippage.gross_sharpe > 1:
            recommendations.append("Good gross performance destroyed by slippage - improve execution")
        
        # Execution recommendations
        if execution.fill_rate < 0.8:
            recommendations.append("Low fill rate - review order types and pricing")
        if execution.timing_sensitivity > 0.5:
            recommendations.append("High timing sensitivity - reduce latency or use more passive orders")
        
        return recommendations
    
    def get_strategy_summary(self, strategy_name: str) -> Dict[str, Any]:
        """Get summary for a strategy"""
        
        diagnostics = self.run_diagnostics(strategy_name)
        
        return {
            'strategy': strategy_name,
            'health_status': diagnostics.health_status.name,
            'health_score': diagnostics.health_score,
            'signal_consistency': diagnostics.signal_consistency.consistency_score,
            'oos_decay': diagnostics.oos_decay.sharpe_decay,
            'regime_sensitivity': diagnostics.regime_sensitivity.regime_sensitivity_score,
            'slippage_cost': diagnostics.slippage_sensitivity.slippage_cost_pct,
            'execution_fragility': diagnostics.execution_fragility.fragility_score,
            'recommendations': diagnostics.recommendations,
            'actions': {
                'disable': diagnostics.should_disable,
                'reduce_size': diagnostics.should_reduce_size
            }
        }


# Factory function
def create_strategy_diagnostics(config: Optional[Dict] = None) -> StrategyDiagnosticsSystem:
    """Create and return a StrategyDiagnosticsSystem instance"""
    return StrategyDiagnosticsSystem(config)
