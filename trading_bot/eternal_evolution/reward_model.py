"""
Tailored Reward Model for Eternal Evolution Trading Bot
========================================================

A sophisticated reward model that guides the bot's evolution by:
1. Rewarding profitable and safe behaviors
2. Penalizing harmful or risky evolutions
3. Balancing multiple objectives (profit, risk, stability)
4. Learning from outcomes to improve reward signals

This reward model is specifically tailored for trading:
- Sharpe ratio optimization
- Drawdown minimization
- Win rate improvement
- Risk-adjusted returns
- System stability
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class RewardComponent(Enum):
    """Components of the reward function"""
    PROFIT = "profit"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return"
    DRAWDOWN = "drawdown"
    WIN_RATE = "win_rate"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    STABILITY = "stability"
    CONSISTENCY = "consistency"
    RECOVERY = "recovery"
    CAPITAL_PRESERVATION = "capital_preservation"


class PenaltyType(Enum):
    """Types of penalties for harmful behaviors"""
    EXCESSIVE_RISK = "excessive_risk"
    LARGE_DRAWDOWN = "large_drawdown"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    OVERTRADING = "overtrading"
    POSITION_CONCENTRATION = "position_concentration"
    VOLATILITY_SPIKE = "volatility_spike"
    SYSTEM_INSTABILITY = "system_instability"
    RULE_VIOLATION = "rule_violation"
    CAPITAL_DESTRUCTION = "capital_destruction"


@dataclass
class RewardSignal:
    """A reward signal from the reward model"""
    timestamp: datetime
    total_reward: float
    components: Dict[str, float]
    penalties: Dict[str, float]
    evolution_id: str
    is_positive: bool
    explanation: str


@dataclass
class EvolutionOutcome:
    """Outcome of an evolution for reward calculation"""
    evolution_id: str
    dimension: str
    changes: List[Dict]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    trades_during: List[Dict]
    duration_hours: float
    timestamp: datetime = field(default_factory=datetime.now)


class TradingRewardModel:
    """
    Tailored Reward Model for Trading Bot Evolution
    
    This model calculates rewards based on:
    1. Profitability metrics (returns, Sharpe, Sortino)
    2. Risk metrics (drawdown, volatility, VaR)
    3. Stability metrics (uptime, error rate, latency)
    4. Consistency metrics (win rate, profit factor)
    
    Penalties are applied for:
    - Excessive risk taking
    - Large drawdowns
    - System instability
    - Rule violations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config if config is not None else {}
        
        # Reward weights (sum to 1.0)
        self.reward_weights = {
            RewardComponent.PROFIT: 0.15,
            RewardComponent.RISK_ADJUSTED_RETURN: 0.20,
            RewardComponent.DRAWDOWN: 0.15,
            RewardComponent.WIN_RATE: 0.10,
            RewardComponent.SHARPE_RATIO: 0.15,
            RewardComponent.SORTINO_RATIO: 0.10,
            RewardComponent.STABILITY: 0.05,
            RewardComponent.CONSISTENCY: 0.05,
            RewardComponent.RECOVERY: 0.03,
            RewardComponent.CAPITAL_PRESERVATION: 0.02
        }
        
        # Penalty multipliers
        self.penalty_multipliers = {
            PenaltyType.EXCESSIVE_RISK: 2.0,
            PenaltyType.LARGE_DRAWDOWN: 3.0,
            PenaltyType.CONSECUTIVE_LOSSES: 1.5,
            PenaltyType.OVERTRADING: 1.0,
            PenaltyType.POSITION_CONCENTRATION: 1.5,
            PenaltyType.VOLATILITY_SPIKE: 1.0,
            PenaltyType.SYSTEM_INSTABILITY: 2.0,
            PenaltyType.RULE_VIOLATION: 5.0,
            PenaltyType.CAPITAL_DESTRUCTION: 10.0
        }
        
        # Thresholds for rewards and penalties
        self.thresholds = {
            'min_sharpe': 0.5,
            'target_sharpe': 2.0,
            'max_drawdown': 0.20,
            'critical_drawdown': 0.30,
            'min_win_rate': 0.40,
            'target_win_rate': 0.55,
            'max_daily_trades': 50,
            'max_position_concentration': 0.25,
            'max_consecutive_losses': 5,
            'min_profit_factor': 1.2,
            'max_volatility_ratio': 2.0,
            'min_uptime': 0.99,
            'max_error_rate': 0.01
        }
        
        # Historical data for learning
        self.reward_history: deque = deque(maxlen=1000)
        self.evolution_outcomes: List[EvolutionOutcome] = []
        
        # Adaptive weights (learned over time)
        self.adaptive_weights = dict(self.reward_weights)
        
        # State
        self.state_path = Path(self.config.get('state_path', 'reward_model_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        logger.info("Trading Reward Model initialized")
    
    def calculate_reward(
        self,
        outcome: EvolutionOutcome
    ) -> RewardSignal:
        """
        Calculate reward for an evolution outcome.
        
        Returns a reward signal with:
        - Total reward (can be negative for harmful evolutions)
        - Component breakdown
        - Penalties applied
        - Explanation
        """
        components = {}
        penalties = {}
        
        # Calculate improvement metrics
        improvement = self._calculate_improvement(
            outcome.metrics_before,
            outcome.metrics_after
        )
        
        # Calculate each reward component
        components[RewardComponent.PROFIT.value] = self._reward_profit(
            outcome.metrics_after, improvement
        )
        
        components[RewardComponent.RISK_ADJUSTED_RETURN.value] = self._reward_risk_adjusted(
            outcome.metrics_after
        )
        
        components[RewardComponent.DRAWDOWN.value] = self._reward_drawdown(
            outcome.metrics_after
        )
        
        components[RewardComponent.WIN_RATE.value] = self._reward_win_rate(
            outcome.metrics_after
        )
        
        components[RewardComponent.SHARPE_RATIO.value] = self._reward_sharpe(
            outcome.metrics_after, improvement
        )
        
        components[RewardComponent.SORTINO_RATIO.value] = self._reward_sortino(
            outcome.metrics_after
        )
        
        components[RewardComponent.STABILITY.value] = self._reward_stability(
            outcome.metrics_after
        )
        
        components[RewardComponent.CONSISTENCY.value] = self._reward_consistency(
            outcome.trades_during
        )
        
        components[RewardComponent.RECOVERY.value] = self._reward_recovery(
            outcome.metrics_after
        )
        
        components[RewardComponent.CAPITAL_PRESERVATION.value] = self._reward_capital_preservation(
            outcome.metrics_before, outcome.metrics_after
        )
        
        # Calculate penalties
        penalties = self._calculate_penalties(outcome)
        
        # Calculate weighted total
        total_reward = sum(
            components[comp.value] * self.adaptive_weights[comp]
            for comp in RewardComponent
        )
        
        # Apply penalties
        total_penalty = sum(penalties.values())
        total_reward -= total_penalty
        
        # Create reward signal
        signal = RewardSignal(
            timestamp=datetime.now(),
            total_reward=total_reward,
            components=components,
            penalties=penalties,
            evolution_id=outcome.evolution_id,
            is_positive=total_reward > 0,
            explanation=self._generate_explanation(components, penalties, total_reward)
        )
        
        # Record for learning
        self.reward_history.append(signal)
        self.evolution_outcomes.append(outcome)
        
        # Update adaptive weights based on outcomes
        self._update_adaptive_weights(signal, outcome)
        
        self._save_state()
        
        return signal
    
    def _calculate_improvement(
        self,
        before: Dict[str, float],
        after: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate improvement between before and after metrics"""
        improvement = {}
        
        for key in after:
            if key in before and before[key] != 0:
                improvement[key] = (after[key] - before[key]) / abs(before[key])
            else:
                improvement[key] = 0
        
        return improvement
    
    def _reward_profit(self, metrics: Dict, improvement: Dict) -> float:
        """Reward for profit improvement"""
        profit = metrics.get('total_profit', 0)
        profit_improvement = improvement.get('total_profit', 0)
        
        # Base reward for positive profit
        if profit > 0:
            base_reward = min(profit / 1000, 1.0)  # Cap at 1.0
        else:
            base_reward = max(profit / 1000, -1.0)  # Floor at -1.0
        
        # Bonus for improvement
        improvement_bonus = min(profit_improvement * 0.5, 0.5)
        
        return base_reward + improvement_bonus
    
    def _reward_risk_adjusted(self, metrics: Dict) -> float:
        """Reward for risk-adjusted returns"""
        sharpe = metrics.get('sharpe_ratio', 0)
        sortino = metrics.get('sortino_ratio', 0)
        
        # Combine Sharpe and Sortino
        risk_adjusted = (sharpe + sortino) / 2
        
        if risk_adjusted >= self.thresholds['target_sharpe']:
            return 1.0
        elif risk_adjusted >= self.thresholds['min_sharpe']:
            return (risk_adjusted - self.thresholds['min_sharpe']) / (
                self.thresholds['target_sharpe'] - self.thresholds['min_sharpe']
            )
        else:
            return -0.5 * (self.thresholds['min_sharpe'] - risk_adjusted)
    
    def _reward_drawdown(self, metrics: Dict) -> float:
        """Reward for low drawdown"""
        drawdown = abs(metrics.get('max_drawdown', 0))
        
        if drawdown <= 0.05:
            return 1.0  # Excellent
        elif drawdown <= 0.10:
            return 0.7  # Good
        elif drawdown <= self.thresholds['max_drawdown']:
            return 0.3  # Acceptable
        elif drawdown <= self.thresholds['critical_drawdown']:
            return -0.5  # Concerning
        else:
            return -1.0  # Critical
    
    def _reward_win_rate(self, metrics: Dict) -> float:
        """Reward for win rate"""
        win_rate = metrics.get('win_rate', 0.5)
        
        if win_rate >= self.thresholds['target_win_rate']:
            return 1.0
        elif win_rate >= self.thresholds['min_win_rate']:
            return (win_rate - self.thresholds['min_win_rate']) / (
                self.thresholds['target_win_rate'] - self.thresholds['min_win_rate']
            )
        else:
            return -0.5 * (self.thresholds['min_win_rate'] - win_rate) / self.thresholds['min_win_rate']
    
    def _reward_sharpe(self, metrics: Dict, improvement: Dict) -> float:
        """Reward for Sharpe ratio"""
        sharpe = metrics.get('sharpe_ratio', 0)
        sharpe_improvement = improvement.get('sharpe_ratio', 0)
        
        # Base reward
        if sharpe >= self.thresholds['target_sharpe']:
            base = 1.0
        elif sharpe >= self.thresholds['min_sharpe']:
            base = sharpe / self.thresholds['target_sharpe']
        else:
            base = -0.5
        
        # Improvement bonus
        improvement_bonus = min(sharpe_improvement * 0.3, 0.3)
        
        return base + improvement_bonus
    
    def _reward_sortino(self, metrics: Dict) -> float:
        """Reward for Sortino ratio (focuses on downside risk)"""
        sortino = metrics.get('sortino_ratio', 0)
        
        if sortino >= 2.5:
            return 1.0
        elif sortino >= 1.0:
            return sortino / 2.5
        else:
            return -0.3
    
    def _reward_stability(self, metrics: Dict) -> float:
        """Reward for system stability"""
        uptime = metrics.get('uptime', 1.0)
        error_rate = metrics.get('error_rate', 0)
        
        uptime_score = 1.0 if uptime >= self.thresholds['min_uptime'] else uptime / self.thresholds['min_uptime']
        error_score = 1.0 if error_rate <= self.thresholds['max_error_rate'] else max(0, 1 - error_rate * 10)
        
        return (uptime_score + error_score) / 2
    
    def _reward_consistency(self, trades: List[Dict]) -> float:
        """Reward for trading consistency"""
        if not trades:
            return 0
        
        # Calculate profit consistency
        profits = [t.get('profit', 0) for t in trades]
        if not profits:
            return 0
        
        avg_profit = sum(profits) / len(profits)
        if avg_profit <= 0:
            return -0.3
        
        # Calculate coefficient of variation (lower is more consistent)
        std_profit = (sum((p - avg_profit) ** 2 for p in profits) / len(profits)) ** 0.5
        cv = std_profit / avg_profit if avg_profit > 0 else float('inf')
        
        if cv <= 0.5:
            return 1.0
        elif cv <= 1.0:
            return 0.5
        elif cv <= 2.0:
            return 0.2
        else:
            return -0.2
    
    def _reward_recovery(self, metrics: Dict) -> float:
        """Reward for recovery from drawdowns"""
        recovery_factor = metrics.get('recovery_factor', 1.0)
        
        if recovery_factor >= 2.0:
            return 1.0
        elif recovery_factor >= 1.0:
            return recovery_factor / 2.0
        else:
            return -0.3
    
    def _reward_capital_preservation(
        self,
        before: Dict,
        after: Dict
    ) -> float:
        """Reward for preserving capital"""
        capital_before = before.get('account_balance', 10000)
        capital_after = after.get('account_balance', 10000)
        
        if capital_before <= 0:
            return 0
        
        preservation_ratio = capital_after / capital_before
        
        if preservation_ratio >= 1.0:
            return 1.0  # Capital preserved or grown
        elif preservation_ratio >= 0.95:
            return 0.5  # Minor loss
        elif preservation_ratio >= 0.90:
            return 0  # Moderate loss
        elif preservation_ratio >= 0.80:
            return -0.5  # Significant loss
        else:
            return -1.0  # Major loss
    
    def _calculate_penalties(self, outcome: EvolutionOutcome) -> Dict[str, float]:
        """Calculate penalties for harmful behaviors"""
        penalties = {}
        metrics = outcome.metrics_after
        trades = outcome.trades_during
        
        # Excessive risk penalty
        risk_per_trade = metrics.get('avg_risk_per_trade', 0)
        if risk_per_trade > 0.05:  # > 5% risk per trade
            penalties[PenaltyType.EXCESSIVE_RISK.value] = (
                (risk_per_trade - 0.05) * 10 * self.penalty_multipliers[PenaltyType.EXCESSIVE_RISK]
            )
        
        # Large drawdown penalty
        drawdown = abs(metrics.get('max_drawdown', 0))
        if drawdown > self.thresholds['max_drawdown']:
            penalties[PenaltyType.LARGE_DRAWDOWN.value] = (
                (drawdown - self.thresholds['max_drawdown']) * 5 * 
                self.penalty_multipliers[PenaltyType.LARGE_DRAWDOWN]
            )
        
        # Consecutive losses penalty
        max_consecutive_losses = self._count_max_consecutive_losses(trades)
        if max_consecutive_losses > self.thresholds['max_consecutive_losses']:
            penalties[PenaltyType.CONSECUTIVE_LOSSES.value] = (
                (max_consecutive_losses - self.thresholds['max_consecutive_losses']) * 0.1 *
                self.penalty_multipliers[PenaltyType.CONSECUTIVE_LOSSES]
            )
        
        # Overtrading penalty
        trades_per_day = len(trades) / max(outcome.duration_hours / 24, 1)
        if trades_per_day > self.thresholds['max_daily_trades']:
            penalties[PenaltyType.OVERTRADING.value] = (
                (trades_per_day - self.thresholds['max_daily_trades']) * 0.01 *
                self.penalty_multipliers[PenaltyType.OVERTRADING]
            )
        
        # Position concentration penalty
        max_concentration = metrics.get('max_position_concentration', 0)
        if max_concentration > self.thresholds['max_position_concentration']:
            penalties[PenaltyType.POSITION_CONCENTRATION.value] = (
                (max_concentration - self.thresholds['max_position_concentration']) * 2 *
                self.penalty_multipliers[PenaltyType.POSITION_CONCENTRATION]
            )
        
        # System instability penalty
        error_rate = metrics.get('error_rate', 0)
        if error_rate > self.thresholds['max_error_rate']:
            penalties[PenaltyType.SYSTEM_INSTABILITY.value] = (
                error_rate * 10 * self.penalty_multipliers[PenaltyType.SYSTEM_INSTABILITY]
            )
        
        # Capital destruction penalty (most severe)
        capital_loss = 1 - (metrics.get('account_balance', 10000) / 
                          outcome.metrics_before.get('account_balance', 10000))
        if capital_loss > 0.10:  # > 10% capital loss
            penalties[PenaltyType.CAPITAL_DESTRUCTION.value] = (
                capital_loss * self.penalty_multipliers[PenaltyType.CAPITAL_DESTRUCTION]
            )
        
        return penalties
    
    def _count_max_consecutive_losses(self, trades: List[Dict]) -> int:
        """Count maximum consecutive losing trades"""
        if not trades:
            return 0
        
        max_consecutive = 0
        current_consecutive = 0
        
        for trade in trades:
            if trade.get('profit', 0) < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _generate_explanation(
        self,
        components: Dict[str, float],
        penalties: Dict[str, float],
        total: float
    ) -> str:
        """Generate human-readable explanation of reward"""
        parts = []
        
        # Top positive components
        positive = [(k, v) for k, v in components.items() if v > 0]
        positive.sort(key=lambda x: x[1], reverse=True)
        if positive:
            top = positive[:3]
            parts.append(f"Positive: {', '.join(f'{k}={v:.2f}' for k, v in top)}")
        
        # Penalties
        if penalties:
            parts.append(f"Penalties: {', '.join(f'{k}={v:.2f}' for k, v in penalties.items())}")
        
        # Overall assessment
        if total > 0.5:
            assessment = "Excellent evolution - strongly beneficial"
        elif total > 0:
            assessment = "Good evolution - net positive"
        elif total > -0.5:
            assessment = "Marginal evolution - slight negative"
        else:
            assessment = "Harmful evolution - should be reverted"
        
        parts.append(assessment)
        
        return " | ".join(parts)
    
    def _update_adaptive_weights(
        self,
        signal: RewardSignal,
        outcome: EvolutionOutcome
    ):
        """Update adaptive weights based on outcomes"""
        # Simple learning: increase weight of components that correlate with success
        if len(self.reward_history) < 10:
            return
        
        # Get recent successful and unsuccessful evolutions
        recent = list(self.reward_history)[-50:]
        successful = [s for s in recent if s.is_positive]
        unsuccessful = [s for s in recent if not s.is_positive]
        
        if not successful or not unsuccessful:
            return
        
        # Calculate average component values for each group
        for comp in RewardComponent:
            key = comp.value
            
            avg_success = sum(s.components.get(key, 0) for s in successful) / len(successful)
            avg_fail = sum(s.components.get(key, 0) for s in unsuccessful) / len(unsuccessful)
            
            # If component differentiates success from failure, increase its weight
            if avg_success > avg_fail:
                self.adaptive_weights[comp] *= 1.01  # Slight increase
            else:
                self.adaptive_weights[comp] *= 0.99  # Slight decrease
        
        # Normalize weights
        total_weight = sum(self.adaptive_weights.values())
        for comp in self.adaptive_weights:
            self.adaptive_weights[comp] /= total_weight
    
    def get_evolution_guidance(self) -> Dict[str, Any]:
        """Get guidance for future evolutions based on reward history"""
        if len(self.reward_history) < 5:
            return {'status': 'insufficient_data', 'recommendations': []}
        
        recent = list(self.reward_history)[-20:]
        
        # Analyze which components need improvement
        avg_components = {}
        for comp in RewardComponent:
            key = comp.value
            avg_components[key] = sum(s.components.get(key, 0) for s in recent) / len(recent)
        
        # Find weakest components
        sorted_components = sorted(avg_components.items(), key=lambda x: x[1])
        weakest = sorted_components[:3]
        
        # Analyze common penalties
        penalty_counts = {}
        for signal in recent:
            for penalty in signal.penalties:
                penalty_counts[penalty] = penalty_counts.get(penalty, 0) + 1
        
        recommendations = []
        
        for comp, score in weakest:
            if score < 0.3:
                recommendations.append(f"Focus on improving {comp} (current: {score:.2f})")
        
        for penalty, count in penalty_counts.items():
            if count > len(recent) * 0.3:  # Occurs in >30% of evolutions
                recommendations.append(f"Reduce {penalty} occurrences ({count}/{len(recent)})")
        
        return {
            'status': 'ready',
            'avg_reward': sum(s.total_reward for s in recent) / len(recent),
            'success_rate': sum(1 for s in recent if s.is_positive) / len(recent),
            'weakest_components': weakest,
            'common_penalties': penalty_counts,
            'recommendations': recommendations,
            'adaptive_weights': {k.value: v for k, v in self.adaptive_weights.items()}
        }
    
    def should_revert_evolution(self, signal: RewardSignal) -> Tuple[bool, str]:
        """Determine if an evolution should be reverted"""
        # Immediate revert conditions
        if signal.total_reward < -1.0:
            return True, "Severely harmful evolution (reward < -1.0)"
        
        if PenaltyType.CAPITAL_DESTRUCTION.value in signal.penalties:
            if signal.penalties[PenaltyType.CAPITAL_DESTRUCTION.value] > 0.5:
                return True, "Capital destruction detected"
        
        if PenaltyType.RULE_VIOLATION.value in signal.penalties:
            return True, "Rule violation detected"
        
        # Check for consistent negative trend
        if len(self.reward_history) >= 3:
            recent = list(self.reward_history)[-3:]
            if all(s.total_reward < 0 for s in recent):
                return True, "Three consecutive negative evolutions"
        
        return False, "Evolution acceptable"
    
    def _save_state(self):
        """Save reward model state"""
        state = {
            'adaptive_weights': {k.value: v for k, v in self.adaptive_weights.items()},
            'thresholds': self.thresholds,
            'reward_history': [
                {
                    'timestamp': s.timestamp.isoformat(),
                    'total_reward': s.total_reward,
                    'evolution_id': s.evolution_id,
                    'is_positive': s.is_positive
                }
                for s in list(self.reward_history)[-100:]
            ]
        }
        
        state_file = self.state_path / 'reward_model_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'reward_model_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore adaptive weights
                for key, value in state.get('adaptive_weights', {}).items():
                    comp = RewardComponent(key)
                    self.adaptive_weights[comp] = value
                
                self.thresholds.update(state.get('thresholds', {}))
                
                logger.info("Loaded reward model state")
                
            except Exception as e:
                logger.error(f"Failed to load reward model state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reward model statistics"""
        if not self.reward_history:
            return {'status': 'no_data'}
        
        rewards = [s.total_reward for s in self.reward_history]
        
        return {
            'total_evaluations': len(self.reward_history),
            'avg_reward': sum(rewards) / len(rewards),
            'max_reward': max(rewards),
            'min_reward': min(rewards),
            'positive_rate': sum(1 for r in rewards if r > 0) / len(rewards),
            'adaptive_weights': {k.value: v for k, v in self.adaptive_weights.items()}
        }
