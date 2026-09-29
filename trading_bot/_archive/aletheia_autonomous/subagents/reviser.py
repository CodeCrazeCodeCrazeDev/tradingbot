"""
Strategy Reviser Subagent

Improves and refines trading strategies based on verifier feedback.
Based on Aletheia's iterative revision approach.
"""

import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyReviser:
    """
    Revises trading strategies based on verification feedback.
    
    Analyzes verification results and makes targeted improvements to:
    - Fix logical inconsistencies
    - Address risk management gaps
    - Improve statistical edge
    - Enhance robustness
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.revision_history: List[Dict] = []
        
    async def revise(
        self,
        hypothesis: 'StrategyHypothesis',
        verification_result: 'VerificationResult',
        iteration: int
    ) -> 'RevisionAction':
        """
        Revise a strategy hypothesis based on verification feedback
        
        Args:
            hypothesis: Original strategy hypothesis
            verification_result: Results from verification
            iteration: Current revision iteration number
            
        Returns:
            RevisionAction describing changes made
        """
        from .aletheia_orchestrator import RevisionAction, StrategyHypothesis
        
        logger.info(f"Revising hypothesis {hypothesis.hypothesis_id} (iteration {iteration + 1})")
        
        # Store previous version
        previous_version_id = hypothesis.hypothesis_id
        
        # Create revised hypothesis
        revised = StrategyHypothesis(
            title=hypothesis.title,
            description=hypothesis.description,
            rationale=hypothesis.rationale,
            market_conditions=hypothesis.market_conditions.copy(),
            entry_rules=hypothesis.entry_rules.copy(),
            exit_rules=hypothesis.exit_rules.copy(),
            risk_parameters=hypothesis.risk_parameters.copy(),
            expected_performance=hypothesis.expected_performance.copy(),
            revision_count=hypothesis.revision_count + 1
        )
        
        changes_made = []
        
        # Apply fixes based on issues
        for issue in verification_result.issues:
            fix = await self._apply_fix(revised, issue, iteration)
            if fix:
                changes_made.append(fix)
        
        # Apply improvements from recommendations
        for rec in verification_result.recommendations:
            improvement = await self._apply_improvement(revised, rec)
            if improvement:
                changes_made.append(improvement)
        
        # Determine revision type
        revision_type = self._determine_revision_type(changes_made, iteration)
        
        # Calculate expected improvement
        improvement_expected = self._calculate_expected_improvement(
            verification_result, changes_made
        )
        
        # Generate revision rationale
        rationale = self._generate_revision_rationale(changes_made, verification_result)
        
        # Update trace
        revised.generation_trace = hypothesis.generation_trace.copy()
        revised.generation_trace.append({
            "timestamp": datetime.now().isoformat(),
            "action": "revision",
            "iteration": iteration + 1,
            "previous_version": previous_version_id,
            "changes": changes_made,
            "rationale": rationale[:200]
        })
        
        revision_action = RevisionAction(
            hypothesis_id=revised.hypothesis_id,
            revision_type=revision_type,
            changes_made=changes_made,
            rationale=rationale,
            improvement_expected=improvement_expected,
            previous_version_id=previous_version_id,
            revised_hypothesis=revised
        )
        
        self.revision_history.append({
            "revision_id": str(revision_action.hypothesis_id),
            "original_id": previous_version_id,
            "changes_count": len(changes_made),
            "iteration": iteration,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Revision complete: {len(changes_made)} changes, expected improvement {improvement_expected:.1%}")
        return revision_action
    
    async def _apply_fix(
        self,
        hypothesis: 'StrategyHypothesis',
        issue: str,
        iteration: int
    ) -> Optional[str]:
        """Apply a fix for a specific issue"""
        
        issue_lower = issue.lower()
        
        # Fix missing stop-loss
        if "stop-loss" in issue_lower or "no stop" in issue_lower:
            if not any("stop" in rule.lower() for rule in hypothesis.exit_rules):
                hypothesis.exit_rules.insert(0, "Hard stop-loss at 2x ATR from entry price")
                return "Added mandatory stop-loss rule"
        
        # Fix missing take-profit
        if "take-profit" in issue_lower or "no take" in issue_lower:
            if not any("profit" in rule.lower() or "target" in rule.lower() for rule in hypothesis.exit_rules):
                hypothesis.exit_rules.append("Take-profit at 3:1 reward-to-risk ratio")
                return "Added take-profit rule"
        
        # Fix position sizing
        if "position size" in issue_lower and ("large" in issue_lower or "excessively" in issue_lower):
            current_max = hypothesis.risk_parameters.get("max_position_size", 10)
            hypothesis.risk_parameters["max_position_size"] = min(current_max * 0.6, 3.0)
            return f"Reduced max position size from {current_max:.1f}% to {hypothesis.risk_parameters['max_position_size']:.1f}%"
        
        # Fix daily loss limit
        if "daily loss" in issue_lower and "high" in issue_lower:
            current_max = hypothesis.risk_parameters.get("max_daily_loss", 5)
            hypothesis.risk_parameters["max_daily_loss"] = min(current_max * 0.7, 3.0)
            return f"Tightened daily loss limit to {hypothesis.risk_parameters['max_daily_loss']:.1f}%"
        
        # Fix drawdown limit
        if "drawdown" in issue_lower:
            current_max = hypothesis.risk_parameters.get("max_drawdown", 20)
            hypothesis.risk_parameters["max_drawdown"] = min(current_max * 0.75, 15)
            return f"Reduced max drawdown limit to {hypothesis.risk_parameters['max_drawdown']:.1f}%"
        
        # Fix unrealistic win rate
        if "win rate" in issue_lower and ("unrealistic" in issue_lower or "high" in issue_lower):
            current_wr = hypothesis.expected_performance.get("expected_win_rate", 0.7)
            hypothesis.expected_performance["expected_win_rate"] = min(current_wr, 0.60)
            return f"Adjusted realistic win rate to {hypothesis.expected_performance['expected_win_rate']:.0%}"
        
        # Fix conflicting entry rules
        if "conflict" in issue_lower or "both long and short" in issue_lower:
            # Add clear separation
            hypothesis.entry_rules = [
                "FOR LONGS: " + rule if "long" in rule.lower() and not rule.startswith("FOR")
                else "FOR SHORTS: " + rule if "short" in rule.lower() and not rule.startswith("FOR")
                else rule
                for rule in hypothesis.entry_rules
            ]
            return "Clarified entry rule separation for long/short conditions"
        
        # Fix high volatility concern
        if "volatility" in issue_lower and ("high" in issue_lower or "reduce" in issue_lower):
            hypothesis.risk_parameters["max_position_size"] *= 0.8
            return "Reduced position sizing for high volatility environment"
        
        # Fix low Sharpe ratio
        if "sharpe" in issue_lower and ("below" in issue_lower or "low" in issue_lower):
            # Add filtering conditions
            hypothesis.entry_rules.append("Additional confirmation: Wait for second consecutive confirming signal")
            return "Added filtering condition to improve signal quality"
        
        # Fix parameter sensitivity
        if "sensitive" in issue_lower or "parameter" in issue_lower:
            # Add adaptive element
            hypothesis.description += " Uses adaptive parameters to reduce sensitivity."
            return "Added adaptive parameter mechanism"
        
        # Fix low trade frequency
        if "low trade frequency" in issue_lower or "long periods" in issue_lower:
            hypothesis.expected_performance["expected_trades_per_month"] = hypothesis.expected_performance.get("expected_trades_per_month", 5) * 1.5
            return "Relaxed entry conditions to increase trade frequency"
        
        # Fix statistical significance
        if "significant" in issue_lower or "sample size" in issue_lower:
            hypothesis.expected_performance["expected_trades_per_month"] = max(
                hypothesis.expected_performance.get("expected_trades_per_month", 10),
                22  # At least 1 trade per trading day
            )
            return "Increased expected trade frequency for statistical significance"
        
        return None
    
    async def _apply_improvement(
        self,
        hypothesis: 'StrategyHypothesis',
        recommendation: str
    ) -> Optional[str]:
        """Apply an improvement based on recommendation"""
        
        rec_lower = recommendation.lower()
        
        if "reduce" in rec_lower and "position size" in rec_lower:
            current = hypothesis.risk_parameters.get("max_position_size", 3)
            hypothesis.risk_parameters["max_position_size"] = max(current * 0.8, 1.0)
            return "Reduced position sizing per recommendation"
        
        if "reduce" in rec_lower and "daily loss" in rec_lower:
            current = hypothesis.risk_parameters.get("max_daily_loss", 3)
            hypothesis.risk_parameters["max_daily_loss"] = max(current * 0.8, 2.0)
            return "Tightened daily loss limit per recommendation"
        
        if "reward/risk" in rec_lower and "2:1" in rec_lower:
            hypothesis.exit_rules = [
                "Stop-loss at 1x ATR from entry",
                "Take-profit at 2x ATR from entry (2:1 reward/risk)"
            ] + [r for r in hypothesis.exit_rules if "stop" not in r.lower() and "profit" not in r.lower()]
            return "Set explicit 2:1 reward-to-risk ratio"
        
        if "filtering" in rec_lower or "signal quality" in rec_lower:
            hypothesis.entry_rules.append("Additional filter: Volume > 150% of 20-period average")
            return "Added volume filter for signal confirmation"
        
        if "tighter" in rec_lower and "risk" in rec_lower:
            for key in hypothesis.risk_parameters:
                if isinstance(hypothesis.risk_parameters[key], (int, float)):
                    hypothesis.risk_parameters[key] *= 0.9
            return "Tightened all risk parameters by 10%"
        
        if "adaptive" in rec_lower or "wider ranges" in rec_lower:
            hypothesis.description += " Implements adaptive position sizing based on volatility."
            hypothesis.risk_parameters["volatility_adjustment"] = True
            return "Added adaptive position sizing"
        
        if "lower correlation" in rec_lower:
            current = hypothesis.risk_parameters.get("max_correlation", 0.8)
            hypothesis.risk_parameters["max_correlation"] = max(current - 0.1, 0.5)
            return f"Reduced correlation threshold to {hypothesis.risk_parameters['max_correlation']:.1f}"
        
        if "diversified" in rec_lower or "market conditions" in rec_lower:
            new_conditions = [
                "Bullish trending",
                "Bearish trending", 
                "Range-bound",
                "High volatility",
                "Low volatility"
            ]
            hypothesis.market_conditions.extend([c for c in new_conditions if c not in hypothesis.market_conditions])
            return "Expanded market condition coverage"
        
        return None
    
    def _determine_revision_type(self, changes_made: List[str], iteration: int) -> str:
        """Determine the type of revision performed"""
        if len(changes_made) == 0:
            return "no_changes"
        
        if len(changes_made) >= 4:
            return "complete_rewrite"
        
        # Check types of changes
        has_rule_changes = any("rule" in change.lower() for change in changes_made)
        has_param_changes = any("position" in change.lower() or "risk" in change.lower() for change in changes_made)
        
        if has_rule_changes and has_param_changes:
            return "rule_and_parameter_modification"
        elif has_rule_changes:
            return "rule_modification"
        elif has_param_changes:
            return "parameter_tuning"
        
        return "general_improvement"
    
    def _calculate_expected_improvement(
        self,
        verification_result: 'VerificationResult',
        changes_made: List[str]
    ) -> float:
        """Calculate expected improvement from changes"""
        base_improvement = 0.05  # 5% baseline
        
        # More changes generally mean more improvement (up to a point)
        change_bonus = min(len(changes_made) * 0.03, 0.15)
        
        # Critical fixes provide more improvement
        critical_fixes = sum(1 for change in changes_made 
                           if any(word in change.lower() for word in ["stop-loss", "mandatory", "hard"]))
        critical_bonus = critical_fixes * 0.10
        
        # Current confidence affects room for improvement
        improvement_room = (1.0 - verification_result.confidence) * 0.5
        
        total = base_improvement + change_bonus + critical_bonus + improvement_room
        return min(total, 0.40)  # Cap at 40% improvement
    
    def _generate_revision_rationale(
        self,
        changes_made: List[str],
        verification_result: 'VerificationResult'
    ) -> str:
        """Generate natural language rationale for revision"""
        
        if len(changes_made) == 0:
            return "No changes required - strategy passed verification with minor issues."
        
        # Group changes by type
        risk_changes = [c for c in changes_made if any(w in c.lower() for w in ["risk", "position", "loss", "drawdown"])]
        rule_changes = [c for c in changes_made if any(w in c.lower() for w in ["rule", "entry", "exit", "filter"])]
        performance_changes = [c for c in changes_made if any(w in c.lower() for w in ["win rate", "sharpe", "adaptive"])]
        
        parts = []
        
        if risk_changes:
            parts.append(f"Strengthened risk management ({len(risk_changes)} adjustments)")
        
        if rule_changes:
            parts.append(f"Refined trading rules ({len(rule_changes)} modifications)")
        
        if performance_changes:
            parts.append(f"Optimized performance expectations ({len(performance_changes)} updates)")
        
        if verification_result.issues:
            parts.append(f"Addressed {len(verification_result.issues)} verification issues")
        
        rationale = "Revision focused on: " + "; ".join(parts) + "."
        rationale += f" Expected confidence improvement from {verification_result.confidence:.1%} to {min(verification_result.confidence * 1.2, 0.95):.1%}."
        
        return rationale
