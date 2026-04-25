"""
Three-Memory System

You need three memories, not one:

1. Decision memory - Stores thesis graph, evidence map, scores at approval time
2. Outcome memory - Stores realized PnL, slippage, fill behavior, invalidation hits
3. Failure memory - Stores recurring failure classes for pattern detection

Without these three, introspection remains hand-wavy.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
import logging
import sqlite3
import pickle
from pathlib import Path

from .core_types import (
    DecisionRecord, OutcomeRecord, FailurePattern, Claim,
    GovernanceDecision, MarketRegime
)

logger = logging.getLogger(__name__)


class DecisionMemory:
    """
    Stores complete decision context at time of approval.
    Enables post-hoc analysis of decision quality.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "decision_memory.db"
        self.decisions: Dict[str, DecisionRecord] = {}
        self.symbol_decisions: Dict[str, List[str]] = defaultdict(list)
        self.pending_outcomes: Set[str] = set()
        
        self._init_storage()
        
    def _init_storage(self) -> None:
        """Initialize persistent storage"""
        if self.storage_path.endswith('.db'):
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    symbol TEXT,
                    signal_source TEXT,
                    final_decision TEXT,
                    approved_size REAL,
                    risk_adjusted_size REAL,
                    claims BLOB,
                    evidence_coverage BLOB,
                    regime_applicability_score REAL,
                    robustness_score REAL,
                    uncertainty_profile BLOB,
                    decision_reasoning TEXT,
                    audit_log BLOB
                )
            ''')
            conn.commit()
            conn.close()
            
    def store_decision(self, record: DecisionRecord) -> None:
        """Store a decision record"""
        self.decisions[record.id] = record
        self.symbol_decisions[record.symbol].append(record.id)
        
        if record.final_decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
            self.pending_outcomes.add(record.id)
            
        self._persist_decision(record)
        logger.info(f"Stored decision {record.id} for {record.symbol}")
        
    def _persist_decision(self, record: DecisionRecord) -> None:
        """Persist decision to storage"""
        if not self.storage_path.endswith('.db'):
            return
            
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO decisions VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        ''', (
            record.id,
            record.timestamp.isoformat(),
            record.symbol,
            record.signal_source,
            record.final_decision.value,
            record.approved_size,
            record.risk_adjusted_size,
            pickle.dumps(record.claims),
            pickle.dumps(record.evidence_coverage),
            record.regime_applicability_score,
            record.robustness_score,
            pickle.dumps(record.uncertainty_profile),
            record.decision_reasoning,
            pickle.dumps(record.audit_log)
        ))
        
        conn.commit()
        conn.close()
        
    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Retrieve a decision by ID"""
        return self.decisions.get(decision_id)
        
    def get_decisions_by_symbol(
        self,
        symbol: str,
        since: Optional[datetime] = None
    ) -> List[DecisionRecord]:
        """Get all decisions for a symbol"""
        decision_ids = self.symbol_decisions.get(symbol, [])
        decisions = [self.decisions[did] for did in decision_ids if did in self.decisions]
        
        if since:
            decisions = [d for d in decisions if d.timestamp >= since]
            
        return decisions
        
    def get_decisions_awaiting_outcome(self) -> List[DecisionRecord]:
        """Get all decisions that need outcome recording"""
        return [
            self.decisions[did] for did in self.pending_outcomes
            if did in self.decisions
        ]
        
    def mark_outcome_recorded(self, decision_id: str) -> None:
        """Mark a decision as having outcome recorded"""
        self.pending_outcomes.discard(decision_id)
        
    def get_decision_statistics(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics on decisions"""
        
        if symbol:
            decisions = self.get_decisions_by_symbol(symbol, since)
        else:
            decisions = list(self.decisions.values())
            if since:
                decisions = [d for d in decisions if d.timestamp >= since]
                
        if not decisions:
            return {'count': 0}
            
        stats = {
            'count': len(decisions),
            'by_decision': defaultdict(int),
            'avg_confidence': 0.0,
            'avg_regime_fit': 0.0,
            'avg_robustness': 0.0
        }
        
        confidences = []
        regime_fits = []
        robustness = []
        
        for d in decisions:
            stats['by_decision'][d.final_decision.value] += 1
            if d.uncertainty_profile:
                confidences.append(d.uncertainty_profile.overall_confidence)
            regime_fits.append(d.regime_applicability_score)
            robustness.append(d.robustness_score)
            
        if confidences:
            stats['avg_confidence'] = sum(confidences) / len(confidences)
        if regime_fits:
            stats['avg_regime_fit'] = sum(regime_fits) / len(regime_fits)
        if robustness:
            stats['avg_robustness'] = sum(robustness) / len(robustness)
            
        return stats


class OutcomeMemory:
    """
    Stores realized outcomes for post-trade analysis.
    Enables calibration and attribution.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "outcome_memory.db"
        self.outcomes: Dict[str, OutcomeRecord] = {}
        self.symbol_outcomes: Dict[str, List[str]] = defaultdict(list)
        
        self._init_storage()
        
    def _init_storage(self) -> None:
        """Initialize persistent storage"""
        if self.storage_path.endswith('.db'):
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outcomes (
                    decision_id TEXT PRIMARY KEY,
                    realized_pnl REAL,
                    realized_slippage REAL,
                    fill_behavior TEXT,
                    invalidation_hit INTEGER,
                    confidence_error REAL,
                    calibration_error REAL,
                    timestamp TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
    def record_outcome(
        self,
        decision_id: str,
        outcome: OutcomeRecord,
        symbol: str
    ) -> None:
        """Record an outcome for a decision"""
        self.outcomes[decision_id] = outcome
        self.symbol_outcomes[symbol].append(decision_id)
        
        self._persist_outcome(decision_id, outcome)
        
        logger.info(
            f"Recorded outcome for {decision_id}: PnL={outcome.realized_pnl:.4f}, "
            f"Confidence error={outcome.confidence_error:.4f}"
        )
        
    def _persist_outcome(self, decision_id: str, outcome: OutcomeRecord) -> None:
        """Persist outcome to storage"""
        if not self.storage_path.endswith('.db'):
            return
            
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            outcome.realized_pnl,
            outcome.realized_slippage,
            outcome.fill_behavior,
            int(outcome.invalidation_hit),
            outcome.confidence_error,
            outcome.calibration_error,
            outcome.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
    def get_outcome(self, decision_id: str) -> Optional[OutcomeRecord]:
        """Get outcome for a decision"""
        return self.outcomes.get(decision_id)
        
    def get_outcomes_by_symbol(
        self,
        symbol: str,
        since: Optional[datetime] = None
    ) -> List[Tuple[OutcomeRecord, str]]:
        """Get outcomes for a symbol with decision IDs"""
        outcome_ids = self.symbol_outcomes.get(symbol, [])
        results = []
        
        for oid in outcome_ids:
            if oid in self.outcomes:
                outcome = self.outcomes[oid]
                if since is None or outcome.timestamp >= since:
                    results.append((outcome, oid))
                    
        return results
        
    def calculate_calibration_metrics(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Calculate calibration metrics"""
        
        if symbol:
            outcomes = self.get_outcomes_by_symbol(symbol, since)
            outcomes = [o for o, _ in outcomes]
        else:
            outcomes = list(self.outcomes.values())
            if since:
                outcomes = [o for o in outcomes if o.timestamp >= since]
                
        if not outcomes:
            return {'brier_score': 0.25, 'calibration_error': 1.0}
            
        # Calculate Brier score
        brier_scores = [o.calibration_error ** 2 for o in outcomes]
        avg_brier = sum(brier_scores) / len(brier_scores)
        
        # Calculate other metrics
        avg_pnl = sum(o.realized_pnl for o in outcomes) / len(outcomes)
        win_rate = sum(1 for o in outcomes if o.realized_pnl > 0) / len(outcomes)
        avg_confidence_error = sum(o.confidence_error for o in outcomes) / len(outcomes)
        
        return {
            'brier_score': avg_brier,
            'avg_calibration_error': avg_confidence_error,
            'avg_pnl': avg_pnl,
            'win_rate': win_rate,
            'sample_size': len(outcomes),
            'invalidation_rate': sum(1 for o in outcomes if o.invalidation_hit) / len(outcomes)
        }
        
    def generate_attribution_report(
        self,
        decision_memory: DecisionMemory,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate causal attribution report"""
        
        # Match decisions to outcomes
        pairs = []
        
        if symbol:
            decisions = decision_memory.get_decisions_by_symbol(symbol)
            for d in decisions:
                outcome = self.get_outcome(d.id)
                if outcome:
                    pairs.append((d, outcome))
        else:
            for decision_id, outcome in self.outcomes.items():
                decision = decision_memory.get_decision(decision_id)
                if decision:
                    pairs.append((decision, outcome))
                    
        if not pairs:
            return {'error': 'No decision-outcome pairs found'}
            
        # Analyze attribution
        profitable_decisions = [(d, o) for d, o in pairs if o.realized_pnl > 0]
        unprofitable_decisions = [(d, o) for d, o in pairs if o.realized_pnl <= 0]
        
        report = {
            'total_trades': len(pairs),
            'profitable_trades': len(profitable_decisions),
            'unprofitable_trades': len(unprofitable_decisions),
            'win_rate': len(profitable_decisions) / len(pairs),
            
            'profitable_characteristics': self._analyze_characteristics(profitable_decisions),
            'unprofitable_characteristics': self._analyze_characteristics(unprofitable_decisions),
            
            'common_failure_modes': self._identify_failure_modes(unprofitable_decisions)
        }
        
        return report
        
    def _analyze_characteristics(
        self,
        pairs: List[Tuple[DecisionRecord, OutcomeRecord]]
    ) -> Dict[str, Any]:
        """Analyze characteristics of a set of decision-outcome pairs"""
        
        if not pairs:
            return {}
            
        avg_confidence = sum(
            d.uncertainty_profile.overall_confidence if d.uncertainty_profile else 0.5
            for d, _ in pairs
        ) / len(pairs)
        
        avg_regime_fit = sum(d.regime_applicability_score for d, _ in pairs) / len(pairs)
        avg_robustness = sum(d.robustness_score for d, _ in pairs) / len(pairs)
        
        return {
            'avg_confidence': avg_confidence,
            'avg_regime_fit': avg_regime_fit,
            'avg_robustness': avg_robustness,
            'decisions': [d.final_decision.value for d, _ in pairs[:5]]  # Sample
        }
        
    def _identify_failure_modes(
        self,
        pairs: List[Tuple[DecisionRecord, OutcomeRecord]]
    ) -> List[Dict[str, Any]]:
        """Identify common failure modes"""
        
        if not pairs:
            return []
            
        modes = defaultdict(lambda: {'count': 0, 'avg_loss': 0})
        
        for d, o in pairs:
            # Categorize failure
            if o.invalidation_hit:
                key = 'invalidation_hit'
            elif d.regime_applicability_score < 0.5:
                key = 'poor_regime_fit'
            elif d.robustness_score < 0.5:
                key = 'low_robustness'
            elif o.confidence_error > 0.5:
                key = 'overconfidence'
            else:
                key = 'other'
                
            modes[key]['count'] += 1
            modes[key]['avg_loss'] += o.realized_pnl
            
        # Convert to list
        return [
            {
                'mode': k,
                'count': v['count'],
                'avg_loss': v['avg_loss'] / v['count'] if v['count'] > 0 else 0
            }
            for k, v in sorted(modes.items(), key=lambda x: x[1]['count'], reverse=True)
        ]


class FailureMemory:
    """
    Stores recurring failure patterns for systematic improvement.
    Enables gap discovery and capability enhancement.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "failure_memory.db"
        self.patterns: Dict[str, FailurePattern] = {}
        self.condition_index: Dict[str, List[str]] = defaultdict(list)
        
        self._init_storage()
        
    def _init_storage(self) -> None:
        """Initialize persistent storage"""
        if self.storage_path.endswith('.db'):
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id TEXT PRIMARY KEY,
                    pattern_name TEXT,
                    description TEXT,
                    conditions BLOB,
                    examples BLOB,
                    frequency INTEGER,
                    severity REAL,
                    root_cause_hypothesis TEXT,
                    proposed_fix TEXT
                )
            ''')
            conn.commit()
            conn.close()
            
    def record_failure(
        self,
        decision: DecisionRecord,
        outcome: OutcomeRecord,
        failure_type: Optional[str] = None
    ) -> Optional[FailurePattern]:
        """
        Record a failure and update patterns.
        
        Returns:
            Updated or new FailurePattern if failure matches a pattern
        """
        # Determine failure type
        if not failure_type:
            failure_type = self._classify_failure(decision, outcome)
            
        # Check if this matches existing pattern
        existing = self._find_matching_pattern(failure_type, decision, outcome)
        
        if existing:
            # Update existing pattern
            existing.examples.append(decision.id)
            existing.frequency += 1
            self._persist_pattern(existing)
            return existing
        else:
            # Create new pattern
            new_pattern = self._create_pattern(failure_type, decision, outcome)
            self.patterns[new_pattern.id] = new_pattern
            self._index_pattern(new_pattern)
            self._persist_pattern(new_pattern)
            return new_pattern
            
    def _classify_failure(
        self,
        decision: DecisionRecord,
        outcome: OutcomeRecord
    ) -> str:
        """Classify the type of failure"""
        
        if outcome.invalidation_hit:
            return "invalidation_not_detected"
        elif outcome.confidence_error > 0.5:
            return "overconfidence"
        elif decision.regime_applicability_score < 0.4:
            return "regime_mismatch"
        elif decision.robustness_score < 0.4:
            return "fragile_thesis"
        elif outcome.fill_behavior == "partial":
            return "execution_failure"
        else:
            return "unexplained_loss"
            
    def _find_matching_pattern(
        self,
        failure_type: str,
        decision: DecisionRecord,
        outcome: OutcomeRecord
    ) -> Optional[FailurePattern]:
        """Find existing pattern that matches this failure"""
        
        for pattern in self.patterns.values():
            if pattern.pattern_name == failure_type:
                # Check if conditions match
                if self._conditions_match(pattern.conditions, decision, outcome):
                    return pattern
                    
        return None
        
    def _conditions_match(
        self,
        conditions: Dict[str, Any],
        decision: DecisionRecord,
        outcome: OutcomeRecord
    ) -> bool:
        """Check if failure matches pattern conditions"""
        
        # Match on regime state
        if 'regime_state' in conditions:
            if decision.current_regime:
                if conditions['regime_state'] != decision.current_regime.volatility_state:
                    return False
                    
        # Match on confidence threshold
        if 'min_confidence' in conditions:
            conf = decision.uncertainty_profile.overall_confidence if decision.uncertainty_profile else 0
            if conf < conditions['min_confidence']:
                return False
                
        return True
        
    def _create_pattern(
        self,
        failure_type: str,
        decision: DecisionRecord,
        outcome: OutcomeRecord
    ) -> FailurePattern:
        """Create a new failure pattern"""
        
        # Generate conditions
        conditions = {
            'failure_type': failure_type,
            'regime_state': decision.current_regime.volatility_state if decision.current_regime else 'unknown',
            'min_confidence': (decision.uncertainty_profile.overall_confidence if decision.uncertainty_profile else 0) - 0.1
        }
        
        # Generate description
        descriptions = {
            'invalidation_not_detected': "Trade hit invalidation condition that wasn't properly monitored",
            'overconfidence': "Trade executed with excessive confidence relative to outcome",
            'regime_mismatch': "Trade executed in regime where strategy is ineffective",
            'fragile_thesis': "Trade based on thesis that fails under stress",
            'execution_failure': "Trade failed to execute as planned",
            'unexplained_loss': "Trade loss doesn't match known patterns"
        }
        
        # Generate hypothesis
        hypotheses = {
            'invalidation_not_detected': "Invalidation monitoring system has gaps or delays",
            'overconfidence': "Confidence calibration is poor or overfitted to historical data",
            'regime_mismatch': "Regime detection system is not accurate enough",
            'fragile_thesis': "Counterfactual testing is not rigorous enough",
            'execution_failure': "Execution feasibility assessment is inadequate",
            'unexplained_loss': "Unknown factors not captured in current models"
        }
        
        severity = min(1.0, abs(outcome.realized_pnl) * 10)  # Scale by loss size
        
        return FailurePattern(
            id="",
            pattern_name=failure_type,
            description=descriptions.get(failure_type, "Unknown failure pattern"),
            conditions=conditions,
            examples=[decision.id],
            frequency=1,
            severity=severity,
            root_cause_hypothesis=hypotheses.get(failure_type, "Unknown cause")
        )
        
    def _index_pattern(self, pattern: FailurePattern) -> None:
        """Index pattern for fast lookup"""
        
        for key, value in pattern.conditions.items():
            index_key = f"{key}:{value}"
            self.condition_index[index_key].append(pattern.id)
            
    def _persist_pattern(self, pattern: FailurePattern) -> None:
        """Persist pattern to storage"""
        if not self.storage_path.endswith('.db'):
            return
            
        conn = sqlite3.connect(self.storage_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO failure_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.id,
            pattern.pattern_name,
            pattern.description,
            pickle.dumps(pattern.conditions),
            pickle.dumps(pattern.examples),
            pattern.frequency,
            pattern.severity,
            pattern.root_cause_hypothesis,
            pattern.proposed_fix
        ))
        
        conn.commit()
        conn.close()
        
    def get_patterns(
        self,
        min_frequency: int = 2,
        min_severity: float = 0.3
    ) -> List[FailurePattern]:
        """Get failure patterns meeting criteria"""
        
        return [
            p for p in self.patterns.values()
            if p.frequency >= min_frequency and p.severity >= min_severity
        ]
        
    def get_top_patterns(self, n: int = 5) -> List[FailurePattern]:
        """Get top N most significant patterns"""
        
        scored = [
            (p, p.frequency * p.severity) for p in self.patterns.values()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [p for p, _ in scored[:n]]
        
    def generate_capability_gaps(self) -> List[Dict[str, Any]]:
        """
        Generate capability gaps based on failure patterns.
        
        Returns:
            List of capability gaps to address
        """
        
        gaps = []
        
        for pattern in self.get_patterns(min_frequency=2):
            gap = {
                'pattern_id': pattern.id,
                'pattern_name': pattern.pattern_name,
                'frequency': pattern.frequency,
                'severity': pattern.severity,
                'description': pattern.description,
                'root_cause': pattern.root_cause_hypothesis,
                'required_capability': self._infer_required_capability(pattern),
                'priority': pattern.frequency * pattern.severity
            }
            gaps.append(gap)
            
        # Sort by priority
        gaps.sort(key=lambda g: g['priority'], reverse=True)
        
        return gaps
        
    def _infer_required_capability(self, pattern: FailurePattern) -> str:
        """Infer what capability is needed to address this pattern"""
        
        capability_map = {
            'invalidation_not_detected': 'real_time_invalidation_monitoring',
            'overconfidence': 'better_calibration_system',
            'regime_mismatch': 'improved_regime_detection',
            'fragile_thesis': 'enhanced_counterfactual_testing',
            'execution_failure': 'better_execution_modeling',
            'unexplained_loss': 'additional_feature_discovery'
        }
        
        return capability_map.get(pattern.pattern_name, 'unknown_capability')
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get failure memory statistics"""
        
        return {
            'total_patterns': len(self.patterns),
            'high_frequency_patterns': len([p for p in self.patterns.values() if p.frequency >= 5]),
            'high_severity_patterns': len([p for p in self.patterns.values() if p.severity >= 0.7]),
            'total_failures_recorded': sum(p.frequency for p in self.patterns.values()),
            'patterns_with_proposed_fixes': len([p for p in self.patterns.values() if p.proposed_fix])
        }
