"""
Anti-Cheat System for Adversarial Curriculum Learning

Detects and punishes:
- Strategy memorization
- Deterministic exploitation
- Single-regime dependence
- Excessive trade frequency
- Unrealistic execution assumptions
- Reward hacking
- Tail risk hiding

When violations are detected:
- Inject adversarial noise
- Alter market mechanics
- Increase penalties
- Force retraining
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

from .core_types import (
    AgentAction,
    AgentState,
    AntiCheatViolation,
    AntiCheatViolationType,
    CurriculumLevel,
    EpisodeResult,
    HardeningMechanism,
    LevelConfig,
    MarketRegime,
    MarketState,
)

logger = logging.getLogger(__name__)


# =============================================================================
# OVERFIT DETECTOR
# =============================================================================

class OverfitDetector:
    """
    Detects overfitting through various statistical tests.
    """
    
    def __init__(self, window_size: int = 100):
        try:
            self.window_size = window_size
            self.action_history: deque = deque(maxlen=window_size * 10)
            self.state_action_pairs: Dict[str, List[AgentAction]] = defaultdict(list)
            self.pattern_counts: Dict[str, int] = defaultdict(int)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_action(self, state: MarketState, action: AgentAction):
        """Record state-action pair for analysis."""
        # Create simplified state hash
        try:
            state_hash = self._hash_state(state)
            self.state_action_pairs[state_hash].append(action)
            self.action_history.append((state_hash, action))
        
            # Track action patterns
            if len(self.action_history) >= 3:
                pattern = tuple(a for _, a in list(self.action_history)[-3:])
                self.pattern_counts[str(pattern)] += 1
        except Exception as e:
            logger.error(f"Error in record_action: {e}")
            raise
    
    def _hash_state(self, state: MarketState) -> str:
        """Create a simplified hash of market state."""
        # Discretize continuous values
        try:
            price_bucket = int(state.price / 0.1)
            vol_bucket = int(state.volatility * 100)
            regime = state.regime.name
        
            return f"{price_bucket}_{vol_bucket}_{regime}"
        except Exception as e:
            logger.error(f"Error in _hash_state: {e}")
            raise
    
    def check_deterministic_behavior(self, min_samples: int = 20) -> Tuple[bool, float, str]:
        """
        Check if agent exhibits deterministic behavior (same action for same state).
        """
        try:
            deterministic_count = 0
            total_checked = 0
        
            for state_hash, actions in self.state_action_pairs.items():
                if len(actions) < min_samples:
                    continue
            
                total_checked += 1
            
                # Check if actions are too consistent
                action_counts = defaultdict(int)
                for action in actions:
                    action_counts[action] += 1
            
                max_count = max(action_counts.values())
                consistency = max_count / len(actions)
            
                if consistency > 0.95:  # 95% same action = deterministic
                    deterministic_count += 1
        
            if total_checked == 0:
                return False, 0.0, "Insufficient data for determinism check"
        
            determinism_rate = deterministic_count / total_checked
            is_deterministic = determinism_rate > 0.3  # 30% of states are deterministic
        
            return is_deterministic, determinism_rate, f"Determinism rate: {determinism_rate:.1%}"
        except Exception as e:
            logger.error(f"Error in check_deterministic_behavior: {e}")
            raise
    
    def check_pattern_memorization(self, max_pattern_frequency: float = 0.1) -> Tuple[bool, float, str]:
        """
        Check if agent has memorized specific patterns.
        """
        try:
            if not self.pattern_counts:
                return False, 0.0, "No patterns recorded"
        
            total_patterns = sum(self.pattern_counts.values())
            max_pattern_count = max(self.pattern_counts.values())
        
            max_frequency = max_pattern_count / total_patterns
        
            is_memorizing = max_frequency > max_pattern_frequency
        
            return is_memorizing, max_frequency, f"Max pattern frequency: {max_frequency:.1%}"
        except Exception as e:
            logger.error(f"Error in check_pattern_memorization: {e}")
            raise
    
    def check_action_entropy(self, min_entropy: float = 1.0) -> Tuple[bool, float, str]:
        """
        Check if action distribution has sufficient entropy.
        Low entropy suggests overfitting to specific actions.
        """
        try:
            if len(self.action_history) < 100:
                return False, 0.0, "Insufficient action history"
        
            action_counts = defaultdict(int)
            for _, action in self.action_history:
                action_counts[action] += 1
        
            total = sum(action_counts.values())
            probs = [count / total for count in action_counts.values()]
        
            entropy = -sum(p * np.log2(p + 1e-10) for p in probs)
        
            is_low_entropy = entropy < min_entropy
        
            return is_low_entropy, entropy, f"Action entropy: {entropy:.2f} (min: {min_entropy})"
        except Exception as e:
            logger.error(f"Error in check_action_entropy: {e}")
            raise
    
    def reset(self):
        """Reset detector state."""
        try:
            self.action_history.clear()
            self.state_action_pairs.clear()
            self.pattern_counts.clear()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# =============================================================================
# EXPLOIT DETECTOR
# =============================================================================

class ExploitDetector:
    """
    Detects exploitation of environment mechanics.
    """
    
    def __init__(self):
        try:
            self.trade_timings: List[int] = []
            self.position_sizes: List[float] = []
            self.leverage_history: List[float] = []
            self.pnl_history: List[float] = []
            self.regime_performance: Dict[MarketRegime, List[float]] = defaultdict(list)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_trade(
        self,
        step: int,
        position_size: float,
        leverage: float,
        pnl: float,
        regime: MarketRegime
    ):
        """Record trade for analysis."""
        try:
            self.trade_timings.append(step)
            self.position_sizes.append(position_size)
            self.leverage_history.append(leverage)
            self.pnl_history.append(pnl)
            self.regime_performance[regime].append(pnl)
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def check_timing_exploit(self, episode_length: int) -> Tuple[bool, float, str]:
        """
        Check if agent exploits predictable timing patterns.
        """
        try:
            if len(self.trade_timings) < 20:
                return False, 0.0, "Insufficient trades for timing analysis"
        
            # Check for clustering at specific times
            timing_mod = [t % 100 for t in self.trade_timings]  # Check 100-step cycles
        
            # Chi-square test for uniform distribution
            observed = np.bincount(timing_mod, minlength=100)
            expected = len(self.trade_timings) / 100
        
            chi2, p_value = stats.chisquare(observed, [expected] * 100)
        
            is_exploiting = p_value < 0.01  # Significant clustering
        
            return is_exploiting, p_value, f"Timing uniformity p-value: {p_value:.4f}"
        except Exception as e:
            logger.error(f"Error in check_timing_exploit: {e}")
            raise
    
    def check_regime_exploitation(self) -> Tuple[bool, float, str]:
        """
        Check if agent only performs well in specific regimes.
        """
        try:
            if len(self.regime_performance) < 3:
                return False, 0.0, "Insufficient regime data"
        
            regime_means = {k.name: np.mean(v) for k, v in self.regime_performance.items() if len(v) >= 5}
        
            if len(regime_means) < 2:
                return False, 0.0, "Insufficient regime data"
        
            means = list(regime_means.values())
            max_mean = max(means)
            min_mean = min(means)
        
            # Check for extreme regime dependence
            if max_mean > 0 and min_mean < 0:
                dependence_ratio = abs(max_mean - min_mean) / (abs(max_mean) + abs(min_mean))
            else:
                dependence_ratio = 0
        
            is_exploiting = dependence_ratio > 0.7  # 70% performance difference
        
            return is_exploiting, dependence_ratio, f"Regime dependence: {dependence_ratio:.1%}, means: {regime_means}"
        except Exception as e:
            logger.error(f"Error in check_regime_exploitation: {e}")
            raise
    
    def check_leverage_abuse(self, max_leverage: float = 3.0) -> Tuple[bool, float, str]:
        """
        Check for leverage abuse patterns.
        """
        try:
            if not self.leverage_history:
                return False, 0.0, "No leverage data"
        
            max_observed = max(self.leverage_history)
            avg_leverage = np.mean(self.leverage_history)
        
            # Check for leverage spikes after losses
            leverage_after_loss = []
            for i in range(1, len(self.pnl_history)):
                if self.pnl_history[i-1] < 0:
                    leverage_after_loss.append(self.leverage_history[i])
        
            avg_leverage_after_loss = np.mean(leverage_after_loss) if leverage_after_loss else 0
        
            is_abusing = (
                max_observed > max_leverage * 2 or
                avg_leverage_after_loss > avg_leverage * 1.5  # Martingale-like
            )
        
            return is_abusing, max_observed, f"Max leverage: {max_observed:.2f}, avg after loss: {avg_leverage_after_loss:.2f}"
        except Exception as e:
            logger.error(f"Error in check_leverage_abuse: {e}")
            raise
    
    def check_reward_hacking(self) -> Tuple[bool, float, str]:
        """
        Check for reward hacking patterns.
        """
        try:
            if len(self.pnl_history) < 50:
                return False, 0.0, "Insufficient P&L history"
        
            # Check for suspicious patterns:
            # 1. Many small wins followed by large losses (tail risk hiding)
            # 2. Extremely consistent returns (unrealistic)
        
            wins = [p for p in self.pnl_history if p > 0]
            losses = [p for p in self.pnl_history if p < 0]
        
            if not wins or not losses:
                return False, 0.0, "Need both wins and losses for analysis"
        
            avg_win = np.mean(wins)
            avg_loss = np.mean(losses)
            max_loss = min(losses)
        
            # Check for tail risk hiding
            tail_ratio = abs(max_loss) / (avg_win + 1e-8)
        
            # Check for unrealistic consistency
            return_std = np.std(self.pnl_history)
            return_mean = np.mean(self.pnl_history)
            cv = return_std / (abs(return_mean) + 1e-8)  # Coefficient of variation
        
            is_hacking = tail_ratio > 10 or cv < 0.1  # Suspicious patterns
        
            return is_hacking, tail_ratio, f"Tail ratio: {tail_ratio:.2f}, CV: {cv:.2f}"
        except Exception as e:
            logger.error(f"Error in check_reward_hacking: {e}")
            raise
    
    def reset(self):
        """Reset detector state."""
        try:
            self.trade_timings.clear()
            self.position_sizes.clear()
            self.leverage_history.clear()
            self.pnl_history.clear()
            self.regime_performance.clear()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# =============================================================================
# BEHAVIOR ANALYZER
# =============================================================================

class BehaviorAnalyzer:
    """
    Analyzes agent behavior for suspicious patterns.
    """
    
    def __init__(self):
        try:
            self.action_sequences: List[AgentAction] = []
            self.position_changes: List[float] = []
            self.drawdown_responses: List[Tuple[float, AgentAction]] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_behavior(
        self,
        action: AgentAction,
        position_change: float,
        current_drawdown: float
    ):
        """Record behavior for analysis."""
        try:
            self.action_sequences.append(action)
            self.position_changes.append(position_change)
            self.drawdown_responses.append((current_drawdown, action))
        except Exception as e:
            logger.error(f"Error in record_behavior: {e}")
            raise
    
    def check_panic_behavior(self, drawdown_threshold: float = 0.1) -> Tuple[bool, float, str]:
        """
        Check if agent panics during drawdowns.
        """
        try:
            if len(self.drawdown_responses) < 50:
                return False, 0.0, "Insufficient data"
        
            # Analyze behavior during drawdowns
            high_dd_actions = [a for dd, a in self.drawdown_responses if dd > drawdown_threshold]
        
            if not high_dd_actions:
                return False, 0.0, "No high drawdown periods"
        
            # Check for excessive closing/reducing
            close_actions = {AgentAction.CLOSE_ALL, AgentAction.EMERGENCY_EXIT, AgentAction.REDUCE_EXPOSURE}
            panic_rate = sum(1 for a in high_dd_actions if a in close_actions) / len(high_dd_actions)
        
            is_panicking = panic_rate > 0.8  # 80% panic actions during drawdown
        
            return is_panicking, panic_rate, f"Panic rate during drawdown: {panic_rate:.1%}"
        except Exception as e:
            logger.error(f"Error in check_panic_behavior: {e}")
            raise
    
    def check_overtrading(self, max_frequency: float = 0.3) -> Tuple[bool, float, str]:
        """
        Check for overtrading behavior.
        """
        try:
            if len(self.action_sequences) < 100:
                return False, 0.0, "Insufficient data"
        
            # Count non-hold actions
            active_actions = sum(1 for a in self.action_sequences if a != AgentAction.HOLD)
            frequency = active_actions / len(self.action_sequences)
        
            is_overtrading = frequency > max_frequency
        
            return is_overtrading, frequency, f"Trade frequency: {frequency:.1%} (max: {max_frequency:.1%})"
        except Exception as e:
            logger.error(f"Error in check_overtrading: {e}")
            raise
    
    def check_position_oscillation(self, threshold: float = 0.5) -> Tuple[bool, float, str]:
        """
        Check for rapid position oscillation (sign changes).
        """
        try:
            if len(self.position_changes) < 20:
                return False, 0.0, "Insufficient data"
        
            # Count sign changes
            signs = np.sign(self.position_changes)
            sign_changes = np.sum(np.abs(np.diff(signs)) > 0)
            oscillation_rate = sign_changes / len(self.position_changes)
        
            is_oscillating = oscillation_rate > threshold
        
            return is_oscillating, oscillation_rate, f"Position oscillation rate: {oscillation_rate:.1%}"
        except Exception as e:
            logger.error(f"Error in check_position_oscillation: {e}")
            raise
    
    def reset(self):
        """Reset analyzer state."""
        try:
            self.action_sequences.clear()
            self.position_changes.clear()
            self.drawdown_responses.clear()
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# =============================================================================
# ANTI-CHEAT SYSTEM
# =============================================================================

class AntiCheatSystem:
    """
    Main anti-cheat system that coordinates all detection mechanisms.
    """
    
    def __init__(self, level: CurriculumLevel):
        try:
            self.level = level
            self.overfit_detector = OverfitDetector()
            self.exploit_detector = ExploitDetector()
            self.behavior_analyzer = BehaviorAnalyzer()
        
            self.violations: List[AntiCheatViolation] = []
            self.penalty_multiplier = 1.0
            self.hardening_active = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_step(
        self,
        state: MarketState,
        action: AgentAction,
        agent_state: AgentState,
        step: int
    ):
        """Record step data for analysis."""
        try:
            self.overfit_detector.record_action(state, action)
        
            if agent_state.trade_count > 0:
                self.exploit_detector.record_trade(
                    step=step,
                    position_size=abs(agent_state.position),
                    leverage=agent_state.leverage,
                    pnl=agent_state.realized_pnl + agent_state.unrealized_pnl,
                    regime=state.regime
                )
        
            position_change = agent_state.position - (agent_state.position_history[-1] if agent_state.position_history else 0)
            self.behavior_analyzer.record_behavior(
                action=action,
                position_change=position_change,
                current_drawdown=agent_state.current_drawdown
            )
        except Exception as e:
            logger.error(f"Error in record_step: {e}")
            raise
    
    def run_checks(self, episode_length: int = 1000) -> List[AntiCheatViolation]:
        """
        Run all anti-cheat checks and return violations.
        """
        try:
            new_violations = []
        
            # Overfit checks
            is_deterministic, score, explanation = self.overfit_detector.check_deterministic_behavior()
            if is_deterministic:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.DETERMINISTIC_EXPLOITATION,
                    severity='high',
                    evidence={'score': score, 'explanation': explanation},
                    detection_method='deterministic_behavior_check',
                    confidence=min(score * 2, 1.0),
                    level=self.level,
                ))
        
            is_memorizing, score, explanation = self.overfit_detector.check_pattern_memorization()
            if is_memorizing:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.PATTERN_MEMORIZATION,
                    severity='high',
                    evidence={'score': score, 'explanation': explanation},
                    detection_method='pattern_memorization_check',
                    confidence=min(score * 5, 1.0),
                    level=self.level,
                ))
        
            is_low_entropy, entropy, explanation = self.overfit_detector.check_action_entropy()
            if is_low_entropy:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.PATTERN_MEMORIZATION,
                    severity='medium',
                    evidence={'entropy': entropy, 'explanation': explanation},
                    detection_method='action_entropy_check',
                    confidence=0.7,
                    level=self.level,
                ))
        
            # Exploit checks
            is_timing_exploit, score, explanation = self.exploit_detector.check_timing_exploit(episode_length)
            if is_timing_exploit:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.DETERMINISTIC_EXPLOITATION,
                    severity='high',
                    evidence={'p_value': score, 'explanation': explanation},
                    detection_method='timing_exploit_check',
                    confidence=0.9,
                    level=self.level,
                ))
        
            is_regime_exploit, score, explanation = self.exploit_detector.check_regime_exploitation()
            if is_regime_exploit:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.SINGLE_REGIME_DEPENDENCE,
                    severity='high',
                    evidence={'dependence_ratio': score, 'explanation': explanation},
                    detection_method='regime_exploitation_check',
                    confidence=min(score, 1.0),
                    level=self.level,
                ))
        
            is_leverage_abuse, score, explanation = self.exploit_detector.check_leverage_abuse()
            if is_leverage_abuse:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.UNREALISTIC_EXECUTION,
                    severity='critical',
                    evidence={'max_leverage': score, 'explanation': explanation},
                    detection_method='leverage_abuse_check',
                    confidence=0.95,
                    level=self.level,
                ))
        
            is_reward_hacking, score, explanation = self.exploit_detector.check_reward_hacking()
            if is_reward_hacking:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.REWARD_HACKING,
                    severity='critical',
                    evidence={'tail_ratio': score, 'explanation': explanation},
                    detection_method='reward_hacking_check',
                    confidence=0.85,
                    level=self.level,
                ))
        
            # Behavior checks
            is_overtrading, score, explanation = self.behavior_analyzer.check_overtrading()
            if is_overtrading:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.EXCESSIVE_TRADING,
                    severity='medium',
                    evidence={'frequency': score, 'explanation': explanation},
                    detection_method='overtrading_check',
                    confidence=0.8,
                    level=self.level,
                ))
        
            is_oscillating, score, explanation = self.behavior_analyzer.check_position_oscillation()
            if is_oscillating:
                new_violations.append(AntiCheatViolation(
                    violation_type=AntiCheatViolationType.EXCESSIVE_TRADING,
                    severity='medium',
                    evidence={'oscillation_rate': score, 'explanation': explanation},
                    detection_method='position_oscillation_check',
                    confidence=0.75,
                    level=self.level,
                ))
        
            self.violations.extend(new_violations)
        
            # Apply penalties based on violations
            self._apply_penalties(new_violations)
        
            return new_violations
        except Exception as e:
            logger.error(f"Error in run_checks: {e}")
            raise
    
    def _apply_penalties(self, violations: List[AntiCheatViolation]):
        """Apply penalties based on violations."""
        try:
            for violation in violations:
                if violation.severity == 'critical':
                    self.penalty_multiplier *= 2.0
                    self.hardening_active = True
                    violation.penalty_applied = "2x penalty multiplier, hardening activated"
                elif violation.severity == 'high':
                    self.penalty_multiplier *= 1.5
                    violation.penalty_applied = "1.5x penalty multiplier"
                elif violation.severity == 'medium':
                    self.penalty_multiplier *= 1.2
                    violation.penalty_applied = "1.2x penalty multiplier"
        
            logger.warning(f"Anti-cheat penalties applied. Multiplier: {self.penalty_multiplier:.2f}")
        except Exception as e:
            logger.error(f"Error in _apply_penalties: {e}")
            raise
    
    def get_hardening_modifications(self) -> Dict[str, Any]:
        """
        Get environment modifications to counter detected exploits.
        """
        try:
            modifications = {}
        
            if not self.hardening_active:
                return modifications
        
            # Analyze violations and create targeted countermeasures
            for violation in self.violations:
                if violation.violation_type == AntiCheatViolationType.DETERMINISTIC_EXPLOITATION:
                    modifications['noise_multiplier'] = modifications.get('noise_multiplier', 1.0) * 2.0
                    modifications['regime_switch_multiplier'] = modifications.get('regime_switch_multiplier', 1.0) * 1.5
            
                elif violation.violation_type == AntiCheatViolationType.SINGLE_REGIME_DEPENDENCE:
                    modifications['force_regime_diversity'] = True
                    modifications['regime_switch_multiplier'] = modifications.get('regime_switch_multiplier', 1.0) * 2.0
            
                elif violation.violation_type == AntiCheatViolationType.EXCESSIVE_TRADING:
                    modifications['transaction_cost_multiplier'] = modifications.get('transaction_cost_multiplier', 1.0) * 2.0
            
                elif violation.violation_type == AntiCheatViolationType.REWARD_HACKING:
                    modifications['tail_risk_penalty_multiplier'] = modifications.get('tail_risk_penalty_multiplier', 1.0) * 3.0
        
            return modifications
        except Exception as e:
            logger.error(f"Error in get_hardening_modifications: {e}")
            raise
    
    def reset(self):
        """Reset anti-cheat system."""
        try:
            self.overfit_detector.reset()
            self.exploit_detector.reset()
            self.behavior_analyzer.reset()
            self.violations.clear()
            self.penalty_multiplier = 1.0
            self.hardening_active = False
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise
    
    def get_violation_summary(self) -> str:
        """Get summary of all violations."""
        try:
            if not self.violations:
                return "No violations detected"
        
            lines = [
                f"ANTI-CHEAT VIOLATION SUMMARY ({len(self.violations)} violations)",
                "-" * 50,
            ]
        
            by_type = defaultdict(list)
            for v in self.violations:
                by_type[v.violation_type.name].append(v)
        
            for vtype, violations in by_type.items():
                lines.append(f"\n{vtype}: {len(violations)} violations")
                for v in violations[:3]:  # Show first 3
                    lines.append(f"  - Severity: {v.severity}, Confidence: {v.confidence:.1%}")
                    lines.append(f"    {v.evidence.get('explanation', 'No details')}")
        
            lines.append(f"\nPenalty multiplier: {self.penalty_multiplier:.2f}")
            lines.append(f"Hardening active: {self.hardening_active}")
        
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in get_violation_summary: {e}")
            raise
