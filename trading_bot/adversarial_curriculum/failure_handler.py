"""
Failure Handler for Adversarial Curriculum Learning

Handles agent failures with:
- Detailed failure diagnostics
- Root cause analysis
- Targeted retraining recommendations
- Level regression when necessary
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .core_types import (
    AgentState,
    CurriculumLevel,
    EpisodeResult,
    FailureDiagnostic,
    FailureMode,
    HardeningMechanism,
    LevelConfig,
    MarketRegime,
    get_level_config,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FAILURE ANALYZER
# =============================================================================

class FailureAnalyzer:
    """
    Analyzes agent failures to identify root causes.
    """
    
    def __init__(self):
        try:
            self.failure_history: List[FailureDiagnostic] = []
            self.failure_counts: Dict[FailureMode, int] = defaultdict(int)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_episode_failure(
        self,
        result: EpisodeResult,
        agent_state: AgentState,
        market_conditions: Dict[str, Any]
    ) -> Optional[FailureDiagnostic]:
        """
        Analyze a failed episode to determine failure mode.
        """
        # Determine primary failure mode
        try:
            failure_mode = self._identify_failure_mode(result, agent_state)
        
            if failure_mode is None:
                return None
        
            # Determine severity
            severity = self._assess_severity(failure_mode, result)
        
            # Identify contributing factors
            contributing_factors = self._identify_contributing_factors(
                failure_mode, result, agent_state, market_conditions
            )
        
            # Generate recommendations
            recommended_action, retrain_level, training_focus = self._generate_recommendations(
                failure_mode, result, contributing_factors
            )
        
            diagnostic = FailureDiagnostic(
                failure_mode=failure_mode,
                severity=severity,
                level=result.level,
                episode_id=result.episode_id,
                step=result.duration_steps,
                description=self._generate_description(failure_mode, result),
                contributing_factors=contributing_factors,
                market_conditions=market_conditions,
                agent_state_at_failure=agent_state,
                recommended_action=recommended_action,
                retrain_from_level=retrain_level,
                targeted_training_focus=training_focus,
            )
        
            self.failure_history.append(diagnostic)
            self.failure_counts[failure_mode] += 1
        
            return diagnostic
        except Exception as e:
            logger.error(f"Error in analyze_episode_failure: {e}")
            raise
    
    def _identify_failure_mode(
        self,
        result: EpisodeResult,
        agent_state: AgentState
    ) -> Optional[FailureMode]:
        """Identify the primary failure mode."""
        
        # Check for blown account
        try:
            if agent_state.capital <= 0:
                if agent_state.leverage > 3.0:
                    return FailureMode.LEVERAGE_ABUSE
                elif agent_state.consecutive_losses > 5:
                    return FailureMode.MARTINGALE_BEHAVIOR
                else:
                    return FailureMode.RISK_MISMANAGEMENT
        
            # Check for excessive drawdown
            if result.max_drawdown > 0.3:
                return FailureMode.DRAWDOWN_EXCEEDED
        
            # Check for tail risk
            if result.tail_ratio > 3.0:
                return FailureMode.TAIL_RISK_EXPOSURE
        
            # Check for regime blindness
            if len(result.regimes_encountered) > 1:
                # If performance varies wildly by regime
                # This would need more detailed data in practice
                pass
        
            # Check for overfitting (via anti-cheat flags)
            if any('PATTERN' in str(f) or 'DETERMINISTIC' in str(f) for f in result.anti_cheat_flags):
                return FailureMode.OVERFITTING
        
            # Check for latency sensitivity
            if HardeningMechanism.LATENCY_VARIANCE in result.hardening_events:
                if result.sharpe_ratio < 0:
                    return FailureMode.LATENCY_SENSITIVITY
        
            # Check for correlation blindness
            if HardeningMechanism.CORRELATION_BREAKDOWN in result.hardening_events:
                if result.max_drawdown > 0.2:
                    return FailureMode.CORRELATION_BLINDNESS
        
            # Check for liquidity trap
            if HardeningMechanism.LIQUIDITY_DROUGHTS in result.hardening_events:
                if result.total_return < -0.1:
                    return FailureMode.LIQUIDITY_TRAP
        
            # Check for reward hacking
            if any('REWARD' in str(f) for f in result.anti_cheat_flags):
                return FailureMode.REWARD_HACKING
        
            # Check for deterministic exploit
            if any('DETERMINISTIC' in str(f) for f in result.anti_cheat_flags):
                return FailureMode.DETERMINISTIC_EXPLOIT
        
            return None
        except Exception as e:
            logger.error(f"Error in _identify_failure_mode: {e}")
            raise
    
    def _assess_severity(self, failure_mode: FailureMode, result: EpisodeResult) -> str:
        """Assess the severity of the failure."""
        
        try:
            critical_modes = {
                FailureMode.LEVERAGE_ABUSE,
                FailureMode.MARTINGALE_BEHAVIOR,
                FailureMode.TAIL_RISK_EXPOSURE,
                FailureMode.REWARD_HACKING,
            }
        
            high_modes = {
                FailureMode.RISK_MISMANAGEMENT,
                FailureMode.DRAWDOWN_EXCEEDED,
                FailureMode.OVERFITTING,
                FailureMode.DETERMINISTIC_EXPLOIT,
            }
        
            if failure_mode in critical_modes:
                return 'critical'
            elif failure_mode in high_modes:
                return 'high'
            elif result.max_drawdown > 0.25:
                return 'high'
            elif result.total_return < -0.15:
                return 'high'
            else:
                return 'medium'
        except Exception as e:
            logger.error(f"Error in _assess_severity: {e}")
            raise
    
    def _identify_contributing_factors(
        self,
        failure_mode: FailureMode,
        result: EpisodeResult,
        agent_state: AgentState,
        market_conditions: Dict[str, Any]
    ) -> List[str]:
        """Identify factors that contributed to the failure."""
        try:
            factors = []
        
            # Market-related factors
            if market_conditions.get('volatility', 0) > 0.03:
                factors.append("High market volatility")
        
            if market_conditions.get('regime') == MarketRegime.CRISIS:
                factors.append("Crisis market regime")
        
            if market_conditions.get('liquidity', 1.0) < 0.3:
                factors.append("Low market liquidity")
        
            # Agent-related factors
            if agent_state.leverage > 2.0:
                factors.append(f"High leverage ({agent_state.leverage:.1f}x)")
        
            if agent_state.consecutive_losses > 3:
                factors.append(f"Consecutive losses ({agent_state.consecutive_losses})")
        
            if result.trade_frequency > 0.3:
                factors.append(f"High trade frequency ({result.trade_frequency:.1%})")
        
            if result.win_rate < 0.4:
                factors.append(f"Low win rate ({result.win_rate:.1%})")
        
            # Hardening-related factors
            for event in result.hardening_events:
                factors.append(f"Hardening event: {event.name}")
        
            return factors
        except Exception as e:
            logger.error(f"Error in _identify_contributing_factors: {e}")
            raise
    
    def _generate_recommendations(
        self,
        failure_mode: FailureMode,
        result: EpisodeResult,
        contributing_factors: List[str]
    ) -> Tuple[str, Optional[CurriculumLevel], List[str]]:
        """Generate recommendations for addressing the failure."""
        
        try:
            recommendations = {
                FailureMode.RISK_MISMANAGEMENT: (
                    "Implement stricter position sizing and risk limits",
                    CurriculumLevel(max(0, result.level.value - 1)),
                    ["Position sizing", "Risk limits", "Capital preservation"]
                ),
                FailureMode.REGIME_BLINDNESS: (
                    "Train on more diverse regime scenarios",
                    CurriculumLevel(max(0, result.level.value - 2)),
                    ["Regime detection", "Adaptive strategies", "Multi-regime training"]
                ),
                FailureMode.OVERFITTING: (
                    "Increase regularization and train on more diverse data",
                    CurriculumLevel(max(0, result.level.value - 2)),
                    ["Regularization", "Data diversity", "Out-of-sample testing"]
                ),
                FailureMode.LATENCY_SENSITIVITY: (
                    "Train with higher latency variance",
                    result.level,
                    ["Latency tolerance", "Execution robustness"]
                ),
                FailureMode.DRAWDOWN_EXCEEDED: (
                    "Implement drawdown-based position reduction",
                    CurriculumLevel(max(0, result.level.value - 1)),
                    ["Drawdown management", "Dynamic position sizing"]
                ),
                FailureMode.TAIL_RISK_EXPOSURE: (
                    "Add tail risk hedging and position limits",
                    CurriculumLevel(max(0, result.level.value - 2)),
                    ["Tail risk hedging", "Position limits", "VaR constraints"]
                ),
                FailureMode.MARTINGALE_BEHAVIOR: (
                    "Eliminate position doubling after losses",
                    CurriculumLevel.LEVEL_0,  # Start from scratch
                    ["Anti-martingale", "Fixed position sizing", "Loss acceptance"]
                ),
                FailureMode.LEVERAGE_ABUSE: (
                    "Implement strict leverage limits",
                    CurriculumLevel.LEVEL_0,  # Start from scratch
                    ["Leverage limits", "Risk budgeting"]
                ),
                FailureMode.CORRELATION_BLINDNESS: (
                    "Train on correlation breakdown scenarios",
                    CurriculumLevel(max(0, result.level.value - 1)),
                    ["Correlation monitoring", "Diversification", "Hedging"]
                ),
                FailureMode.LIQUIDITY_TRAP: (
                    "Implement liquidity-aware position sizing",
                    result.level,
                    ["Liquidity analysis", "Position sizing", "Exit planning"]
                ),
                FailureMode.REWARD_HACKING: (
                    "Redesign reward function and add constraints",
                    CurriculumLevel.LEVEL_0,  # Start from scratch
                    ["Reward design", "Constraint satisfaction"]
                ),
                FailureMode.DETERMINISTIC_EXPLOIT: (
                    "Add noise and randomization to environment",
                    CurriculumLevel(max(0, result.level.value - 1)),
                    ["Generalization", "Noise tolerance"]
                ),
            }
        
            return recommendations.get(
                failure_mode,
                ("Review and retrain", result.level, ["General improvement"])
            )
        except Exception as e:
            logger.error(f"Error in _generate_recommendations: {e}")
            raise
    
    def _generate_description(self, failure_mode: FailureMode, result: EpisodeResult) -> str:
        """Generate a human-readable description of the failure."""
        
        try:
            descriptions = {
                FailureMode.RISK_MISMANAGEMENT: 
                    f"Agent failed to manage risk properly. Max drawdown: {result.max_drawdown:.1%}, "
                    f"Total return: {result.total_return:.1%}",
                FailureMode.REGIME_BLINDNESS:
                    f"Agent failed to adapt to regime changes. Regimes encountered: "
                    f"{[r.name for r in result.regimes_encountered]}",
                FailureMode.OVERFITTING:
                    f"Agent showed signs of overfitting. Win rate: {result.win_rate:.1%}, "
                    f"but poor generalization",
                FailureMode.LATENCY_SENSITIVITY:
                    f"Agent performance degraded under latency. Sharpe: {result.sharpe_ratio:.2f}",
                FailureMode.DRAWDOWN_EXCEEDED:
                    f"Maximum drawdown exceeded threshold: {result.max_drawdown:.1%}",
                FailureMode.TAIL_RISK_EXPOSURE:
                    f"Agent exposed to excessive tail risk. Tail ratio: {result.tail_ratio:.2f}",
                FailureMode.MARTINGALE_BEHAVIOR:
                    f"Agent exhibited martingale-like behavior (doubling down on losses)",
                FailureMode.LEVERAGE_ABUSE:
                    f"Agent abused leverage. Max leverage used: {result.max_leverage_used:.1f}x",
                FailureMode.CORRELATION_BLINDNESS:
                    f"Agent failed during correlation breakdown event",
                FailureMode.LIQUIDITY_TRAP:
                    f"Agent got trapped in illiquid position",
                FailureMode.REWARD_HACKING:
                    f"Agent exploited reward function without genuine performance",
                FailureMode.DETERMINISTIC_EXPLOIT:
                    f"Agent exploited deterministic patterns in environment",
            }
        
            return descriptions.get(failure_mode, f"Unknown failure mode: {failure_mode.name}")
        except Exception as e:
            logger.error(f"Error in _generate_description: {e}")
            raise
    
    def get_failure_summary(self) -> str:
        """Get summary of all failures."""
        try:
            if not self.failure_history:
                return "No failures recorded"
        
            lines = [
                f"FAILURE ANALYSIS SUMMARY ({len(self.failure_history)} failures)",
                "=" * 60,
            ]
        
            # Count by mode
            lines.append("\nFailures by Mode:")
            for mode, count in sorted(self.failure_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {mode.name}: {count}")
        
            # Count by severity
            severity_counts = defaultdict(int)
            for f in self.failure_history:
                severity_counts[f.severity] += 1
        
            lines.append("\nFailures by Severity:")
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in severity_counts:
                    lines.append(f"  {severity}: {severity_counts[severity]}")
        
            # Most common contributing factors
            factor_counts = defaultdict(int)
            for f in self.failure_history:
                for factor in f.contributing_factors:
                    factor_counts[factor] += 1
        
            lines.append("\nTop Contributing Factors:")
            for factor, count in sorted(factor_counts.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"  {factor}: {count}")
        
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in get_failure_summary: {e}")
            raise


# =============================================================================
# RETRAINING SCHEDULER
# =============================================================================

class RetrainingScheduler:
    """
    Schedules and manages retraining based on failures.
    """
    
    def __init__(self):
        try:
            self.retraining_queue: List[Dict[str, Any]] = []
            self.completed_retraining: List[Dict[str, Any]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def schedule_retraining(
        self,
        diagnostic: FailureDiagnostic,
        priority: str = 'normal'
    ) -> Dict[str, Any]:
        """
        Schedule retraining based on failure diagnostic.
        """
        try:
            retraining_task = {
                'id': f"retrain_{len(self.retraining_queue)}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'failure_mode': diagnostic.failure_mode,
                'from_level': diagnostic.retrain_from_level,
                'focus_areas': diagnostic.targeted_training_focus,
                'priority': priority,
                'status': 'scheduled',
                'scheduled_at': datetime.now(),
                'diagnostic': diagnostic,
            }
        
            # Insert based on priority
            if priority == 'critical':
                self.retraining_queue.insert(0, retraining_task)
            elif priority == 'high':
                # Insert after critical tasks
                insert_idx = sum(1 for t in self.retraining_queue if t['priority'] == 'critical')
                self.retraining_queue.insert(insert_idx, retraining_task)
            else:
                self.retraining_queue.append(retraining_task)
        
            logger.info(f"Scheduled retraining: {retraining_task['id']}, priority: {priority}")
        
            return retraining_task
        except Exception as e:
            logger.error(f"Error in schedule_retraining: {e}")
            raise
    
    def get_next_retraining(self) -> Optional[Dict[str, Any]]:
        """Get the next retraining task."""
        try:
            if not self.retraining_queue:
                return None
        
            task = self.retraining_queue[0]
            task['status'] = 'in_progress'
            task['started_at'] = datetime.now()
        
            return task
        except Exception as e:
            logger.error(f"Error in get_next_retraining: {e}")
            raise
    
    def complete_retraining(self, task_id: str, success: bool, notes: str = ""):
        """Mark retraining as complete."""
        try:
            for i, task in enumerate(self.retraining_queue):
                if task['id'] == task_id:
                    task['status'] = 'completed' if success else 'failed'
                    task['completed_at'] = datetime.now()
                    task['success'] = success
                    task['notes'] = notes
                
                    self.completed_retraining.append(task)
                    self.retraining_queue.pop(i)
                
                    logger.info(f"Retraining {task_id} {'completed' if success else 'failed'}")
                    return
        
            logger.warning(f"Retraining task {task_id} not found")
        except Exception as e:
            logger.error(f"Error in complete_retraining: {e}")
            raise
    
    def get_retraining_plan(self, diagnostic: FailureDiagnostic) -> Dict[str, Any]:
        """
        Generate a detailed retraining plan based on failure diagnostic.
        """
        try:
            plan = {
                'failure_mode': diagnostic.failure_mode.name,
                'target_level': diagnostic.retrain_from_level.value if diagnostic.retrain_from_level else 0,
                'focus_areas': diagnostic.targeted_training_focus,
                'phases': [],
            }
        
            # Phase 1: Foundation
            if diagnostic.retrain_from_level and diagnostic.retrain_from_level.value <= 2:
                plan['phases'].append({
                    'name': 'Foundation',
                    'levels': [0, 1],
                    'focus': 'Basic market mechanics and risk management',
                    'min_episodes': 100,
                    'success_criteria': {
                        'min_sharpe': 0.3,
                        'max_drawdown': 0.15,
                    }
                })
        
            # Phase 2: Targeted Training
            plan['phases'].append({
                'name': 'Targeted Training',
                'levels': [diagnostic.retrain_from_level.value if diagnostic.retrain_from_level else 0],
                'focus': ', '.join(diagnostic.targeted_training_focus),
                'min_episodes': 200,
                'success_criteria': {
                    'min_sharpe': 0.5,
                    'max_drawdown': 0.20,
                }
            })
        
            # Phase 3: Stress Testing
            plan['phases'].append({
                'name': 'Stress Testing',
                'levels': [diagnostic.level.value],
                'focus': 'Robustness under adverse conditions',
                'min_episodes': 100,
                'success_criteria': {
                    'ood_degradation': 0.25,
                    'no_violations': True,
                }
            })
        
            return plan
        except Exception as e:
            logger.error(f"Error in get_retraining_plan: {e}")
            raise


# =============================================================================
# REGRESSION MANAGER
# =============================================================================

class RegressionManager:
    """
    Manages level regression when agent fails repeatedly.
    """
    
    def __init__(self, max_failures_before_regression: int = 3):
        try:
            self.max_failures = max_failures_before_regression
            self.level_failure_counts: Dict[CurriculumLevel, int] = defaultdict(int)
            self.regression_history: List[Dict[str, Any]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_failure(self, level: CurriculumLevel) -> Optional[CurriculumLevel]:
        """
        Record a failure at a level and determine if regression is needed.
        
        Returns:
            New level to regress to, or None if no regression needed
        """
        try:
            self.level_failure_counts[level] += 1
        
            if self.level_failure_counts[level] >= self.max_failures:
                # Determine regression level
                regression_level = self._calculate_regression_level(level)
            
                self.regression_history.append({
                    'from_level': level,
                    'to_level': regression_level,
                    'failure_count': self.level_failure_counts[level],
                    'timestamp': datetime.now(),
                })
            
                # Reset failure count for the level
                self.level_failure_counts[level] = 0
            
                logger.warning(f"REGRESSION: Level {level.value} -> Level {regression_level.value}")
            
                return regression_level
        
            return None
        except Exception as e:
            logger.error(f"Error in record_failure: {e}")
            raise
    
    def _calculate_regression_level(self, current_level: CurriculumLevel) -> CurriculumLevel:
        """Calculate the appropriate regression level."""
        # Regress by 1-2 levels depending on failure severity
        try:
            regression_amount = min(2, current_level.value)
        
            # Check if we've regressed from this level before
            recent_regressions = [
                r for r in self.regression_history[-5:]
                if r['from_level'] == current_level
            ]
        
            if len(recent_regressions) >= 2:
                # Multiple regressions from same level - go back further
                regression_amount = min(3, current_level.value)
        
            return CurriculumLevel(max(0, current_level.value - regression_amount))
        except Exception as e:
            logger.error(f"Error in _calculate_regression_level: {e}")
            raise
    
    def record_success(self, level: CurriculumLevel):
        """Record a success at a level (resets failure count)."""
        try:
            self.level_failure_counts[level] = 0
        except Exception as e:
            logger.error(f"Error in record_success: {e}")
            raise
    
    def get_regression_summary(self) -> str:
        """Get summary of regressions."""
        try:
            if not self.regression_history:
                return "No regressions recorded"
        
            lines = [
                f"REGRESSION HISTORY ({len(self.regression_history)} regressions)",
                "-" * 40,
            ]
        
            for reg in self.regression_history[-10:]:  # Last 10
                lines.append(
                    f"Level {reg['from_level'].value} -> {reg['to_level'].value} "
                    f"(failures: {reg['failure_count']}) at {reg['timestamp'].strftime('%Y-%m-%d %H:%M')}"
                )
        
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in get_regression_summary: {e}")
            raise
