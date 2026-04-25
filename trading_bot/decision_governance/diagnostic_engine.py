"""
Diagnostic Introspection Engine

Provides deep diagnostic analysis explaining WHY failures happened.
Answers: Where did this decision come from? What assumptions were made?
What failed? How can it be fixed?
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticInsight:
    """A single diagnostic insight"""
    category: str
    finding: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    evidence: List[str]
    recommendation: str
    related_decisions: List[str]


@dataclass
class FailureDiagnosis:
    """Complete diagnosis of a failure"""
    decision_id: str
    symbol: str
    failure_type: str
    root_cause: str
    causal_chain: List[str]
    contributing_factors: List[str]
    missed_warnings: List[str]
    lessons: List[str]
    fix_suggestions: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DiagnosticIntrospectionEngine:
    """
    Diagnostic introspection explaining WHY failures happen.
    
    Actively answers:
    - Where did this decision come from?
    - Which assumptions were made?
    - What evidence was missing?
    - What contradicted this?
    - What uncertainty was ignored?
    - What failed in similar past cases?
    """
    
    def __init__(self):
        self.diagnosis_history: List[FailureDiagnosis] = []
        self.pattern_database: Dict[str, List[Dict]] = defaultdict(list)
        
    def diagnose_failure(
        self,
        decision: Dict[str, Any],
        outcome: Dict[str, Any],
        audit_trail: List[Dict],
        market_context: Dict[str, Any]
    ) -> FailureDiagnosis:
        """
        Perform deep diagnostic analysis of a failure.
        
        Returns:
            FailureDiagnosis with complete root cause analysis
        """
        
        # Determine failure type
        failure_type = self._classify_failure(decision, outcome)
        
        # Trace decision provenance
        causal_chain = self._trace_decision_provenance(decision, audit_trail)
        
        # Identify assumptions made
        assumptions = self._identify_assumptions(decision, audit_trail)
        
        # Find missing evidence
        missing_evidence = self._identify_missing_evidence(decision, audit_trail)
        
        # Find contradictions
        contradictions = self._find_contradictions(audit_trail)
        
        # Find ignored uncertainties
        ignored_uncertainties = self._find_ignored_uncertainties(decision, audit_trail)
        
        # Find similar past failures
        similar_failures = self._find_similar_failures(decision, outcome)
        
        # Determine root cause
        root_cause = self._determine_root_cause(
            failure_type, assumptions, missing_evidence, 
            contradictions, ignored_uncertainties
        )
        
        # Collect contributing factors
        contributing = self._collect_contributing_factors(
            assumptions, missing_evidence, contradictions, ignored_uncertainties
        )
        
        # Find missed warnings
        missed_warnings = self._find_missed_warnings(audit_trail, decision)
        
        # Extract lessons
        lessons = self._extract_lessons(
            root_cause, contributing, similar_failures, decision
        )
        
        # Generate fix suggestions
        fix_suggestions = self._generate_fix_suggestions(
            root_cause, contributing, decision
        )
        
        diagnosis = FailureDiagnosis(
            decision_id=decision.get('id', 'unknown'),
            symbol=decision.get('symbol', 'unknown'),
            failure_type=failure_type,
            root_cause=root_cause,
            causal_chain=causal_chain,
            contributing_factors=contributing,
            missed_warnings=missed_warnings,
            lessons=lessons,
            fix_suggestions=fix_suggestions
        )
        
        self.diagnosis_history.append(diagnosis)
        
        # Store pattern for future reference
        pattern_key = f"{decision.get('symbol')}_{failure_type}"
        self.pattern_database[pattern_key].append({
            'decision_id': decision.get('id'),
            'outcome': outcome,
            'diagnosis': diagnosis,
            'timestamp': datetime.utcnow()
        })
        
        return diagnosis
    
    def _classify_failure(
        self,
        decision: Dict,
        outcome: Dict
    ) -> str:
        """Classify the type of failure"""
        
        pnl = outcome.get('pnl', 0)
        
        if pnl < -0.05:  # >5% loss
            return "major_loss"
        elif pnl < 0:
            return "minor_loss"
        elif outcome.get('invalidation_hit'):
            return "invalidation_hit"
        elif outcome.get('confidence_error', 0) > 0.3:
            return "calibration_failure"
        else:
            return "unexpected_outcome"
    
    def _trace_decision_provenance(
        self,
        decision: Dict,
        audit_trail: List[Dict]
    ) -> List[str]:
        """Trace where the decision came from"""
        
        chain = []
        
        # Find origin
        signal_event = next(
            (e for e in audit_trail if e.get('event_type') == 'signal_received'),
            None
        )
        
        if signal_event:
            chain.append(
                f"Signal from {signal_event.get('data', {}).get('source', 'unknown')}"
            )
            
        # Track through validation
        validation_event = next(
            (e for e in audit_trail if e.get('event_type') == 'signal_validated'),
            None
        )
        if validation_event:
            chain.append("Passed signal validation")
            
        # Track through governance layers
        layer_events = [
            e for e in audit_trail
            if e.get('event_type') in [
                'claim_constructed', 'evidence_audited', 'adversarial_challenge',
                'regime_evaluated', 'counterfactual_run', 'uncertainty_computed'
            ]
        ]
        
        for event in layer_events:
            chain.append(f"Processed through {event.get('event_type')}")
            
        # Final decision
        decision_event = next(
            (e for e in audit_trail if e.get('event_type') == 'decision_rendered'),
            None
        )
        if decision_event:
            chain.append(
                f"Final decision: {decision_event.get('data', {}).get('decision', 'unknown')}"
            )
            
        return chain
    
    def _identify_assumptions(
        self,
        decision: Dict,
        audit_trail: List[Dict]
    ) -> List[str]:
        """Identify assumptions made in the decision"""
        
        assumptions = []
        
        # From decision record
        if decision.get('assumptions'):
            assumptions.extend(decision.get('assumptions', []))
            
        # From claims
        claims_event = next(
            (e for e in audit_trail if e.get('event_type') == 'claim_constructed'),
            None
        )
        if claims_event:
            claims = claims_event.get('data', {}).get('claims', [])
            for claim in claims:
                if claim.get('type') == 'assumption':
                    assumptions.append(claim.get('content', ''))
                    
        # Inferred assumptions
        assumptions.append("Assumed market conditions stable through execution")
        assumptions.append("Assumed no major news events during position")
        
        return assumptions
    
    def _identify_missing_evidence(
        self,
        decision: Dict,
        audit_trail: List[Dict]
    ) -> List[str]:
        """Identify what evidence was missing"""
        
        missing = []
        
        evidence_event = next(
            (e for e in audit_trail if e.get('event_type') == 'evidence_audited'),
            None
        )
        
        if evidence_event:
            gaps = evidence_event.get('data', {}).get('evidence_gaps', [])
            missing.extend(gaps)
            
        # Check for common missing evidence
        if not any('volume' in str(e) for e in audit_trail):
            missing.append("Volume confirmation not validated")
            
        if not any('correlation' in str(e) for e in audit_trail):
            missing.append("Correlation regime not assessed")
            
        return missing
    
    def _find_contradictions(
        self,
        audit_trail: List[Dict]
    ) -> List[str]:
        """Find contradictions in the decision process"""
        
        contradictions = []
        
        # Check adversarial challenges
        challenge_event = next(
            (e for e in audit_trail if e.get('event_type') == 'adversarial_challenge'),
            None
        )
        
        if challenge_event:
            challenges = challenge_event.get('data', {}).get('challenges', [])
            for challenge in challenges:
                if challenge.get('severity', 0) > 0.7:
                    contradictions.append(
                        f"High-severity challenge: {challenge.get('content', '')[:60]}"
                    )
                    
        return contradictions
    
    def _find_ignored_uncertainties(
        self,
        decision: Dict,
        audit_trail: List[Dict]
    ) -> List[str]:
        """Find uncertainties that were present but ignored"""
        
        ignored = []
        
        uncertainty_event = next(
            (e for e in audit_trail if e.get('event_type') == 'uncertainty_computed'),
            None
        )
        
        if uncertainty_event:
            profile = uncertainty_event.get('data', {}).get('uncertainty_profile', {})
            decomposition = profile.get('decomposition', {})
            
            # Check for high uncertainties
            for uncertainty_type, value in decomposition.items():
                if value > 0.4:
                    ignored.append(
                        f"High {uncertainty_type} ({value:.1%}) present but not mitigated"
                    )
                    
        # Check abstention probability
        abstention_prob = decision.get('uncertainty_profile', {}).get('abstention_probability', 0)
        if abstention_prob > 0.3:
            ignored.append(
                f"Abstention probability {abstention_prob:.1%} suggests uncertainty not adequately resolved"
            )
            
        return ignored
    
    def _find_similar_failures(
        self,
        decision: Dict,
        outcome: Dict
    ) -> List[Dict]:
        """Find similar past failures"""
        
        symbol = decision.get('symbol', '')
        failure_type = self._classify_failure(decision, outcome)
        
        pattern_key = f"{symbol}_{failure_type}"
        similar = self.pattern_database.get(pattern_key, [])
        
        # Filter to recent similar failures
        cutoff = datetime.utcnow() - timedelta(days=90)
        recent_similar = [
            s for s in similar
            if s.get('timestamp', datetime.utcnow()) > cutoff
        ]
        
        return recent_similar[:5]  # Top 5 most recent
    
    def _determine_root_cause(
        self,
        failure_type: str,
        assumptions: List[str],
        missing_evidence: List[str],
        contradictions: List[str],
        ignored_uncertainties: List[str]
    ) -> str:
        """Determine the root cause of failure"""
        
        # Priority: contradictions > missing evidence > ignored uncertainties > assumptions
        
        if contradictions:
            return f"Adversarial challenges not adequately addressed: {contradictions[0][:80]}"
            
        if missing_evidence:
            return f"Insufficient evidence: {missing_evidence[0][:80]}"
            
        if ignored_uncertainties:
            return f"Excessive uncertainty not mitigated: {ignored_uncertainties[0][:80]}"
            
        if len(assumptions) > 3:
            return f"Too many unverified assumptions ({len(assumptions)})"
            
        return "Unknown - requires deeper investigation"
    
    def _collect_contributing_factors(
        self,
        assumptions: List[str],
        missing_evidence: List[str],
        contradictions: List[str],
        ignored_uncertainties: List[str]
    ) -> List[str]:
        """Collect all contributing factors"""
        
        factors = []
        
        if assumptions:
            factors.append(f"{len(assumptions)} assumptions made")
        if missing_evidence:
            factors.append(f"{len(missing_evidence)} evidence gaps")
        if contradictions:
            factors.append(f"{len(contradictions)} unaddressed contradictions")
        if ignored_uncertainties:
            factors.append(f"{len(ignored_uncertainties)} ignored uncertainties")
            
        return factors
    
    def _find_missed_warnings(
        self,
        audit_trail: List[Dict],
        decision: Dict
    ) -> List[str]:
        """Find warnings that were present but not acted upon"""
        
        warnings = []
        
        # Check for regime mismatch warnings
        regime_event = next(
            (e for e in audit_trail if e.get('event_type') == 'regime_evaluated'),
            None
        )
        if regime_event:
            if regime_event.get('data', {}).get('regime_underrepresented'):
                warnings.append("Regime underrepresentation warning ignored")
                
        # Check for counterfactual failures
        cf_event = next(
            (e for e in audit_trail if e.get('event_type') == 'counterfactual_run'),
            None
        )
        if cf_event:
            scenarios = cf_event.get('data', {}).get('scenarios', [])
            failed_cf = [s for s in scenarios if not s.get('survives', True)]
            if failed_cf:
                warnings.append(
                    f"Counterfactual failure ignored ({len(failed_cf)} scenarios failed)"
                )
                
        # Check confidence calibration
        if decision.get('uncertainty_profile', {}).get('calibration_quality', 1.0) < 0.5:
            warnings.append("Poor calibration quality not addressed")
            
        return warnings
    
    def _extract_lessons(
        self,
        root_cause: str,
        contributing: List[str],
        similar_failures: List[Dict],
        decision: Dict
    ) -> List[str]:
        """Extract actionable lessons from the failure"""
        
        lessons = []
        
        # From root cause
        if "contradictions" in root_cause.lower():
            lessons.append("Require stronger adversarial challenge responses before approval")
        if "evidence" in root_cause.lower():
            lessons.append("Raise minimum evidence requirements")
        if "uncertainty" in root_cause.lower():
            lessons.append("Implement mandatory uncertainty mitigation for high-abstention cases")
            
        # From similar failures
        if similar_failures:
            lessons.append(
                f"Pattern detected: {len(similar_failures)} similar failures in past 90 days - "
                "consider adding specific safeguards"
            )
            
        # From decision characteristics
        if decision.get('robustness_score', 1.0) < 0.5:
            lessons.append("Low robustness scores should block approval, not just warn")
            
        return lessons if lessons else ["No clear lessons - outcome may be within normal variance"]
    
    def _generate_fix_suggestions(
        self,
        root_cause: str,
        contributing: List[str],
        decision: Dict
    ) -> List[str]:
        """Generate specific suggestions to fix the issue"""
        
        fixes = []
        
        # Based on root cause
        if "contradictions" in root_cause.lower():
            fixes.append("Increase adversarial depth from 3 to 5 challenges")
            fixes.append("Add adversarial response quality check before approval")
            
        if "evidence" in root_cause.lower():
            fixes.append("Raise minimum evidence coverage from 0.5 to 0.7")
            fixes.append("Add evidence diversity requirement (must have >2 evidence types)")
            
        if "uncertainty" in root_cause.lower():
            fixes.append("Lower abstention threshold from 0.5 to 0.4")
            fixes.append("Add uncertainty decomposition as approval criterion")
            
        if decision.get('regime_applicability_score', 1.0) < 0.5:
            fixes.append("Implement stricter regime match requirements")
            
        # General improvements
        fixes.append("Add post-trade diagnostic review to feedback loop")
        
        return fixes
    
    def generate_comprehensive_diagnostic_report(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        
        diagnoses = self.diagnosis_history
        
        if symbol:
            diagnoses = [d for d in diagnoses if d.symbol == symbol]
        if since:
            diagnoses = [d for d in diagnoses if d.timestamp >= since]
            
        if not diagnoses:
            return {'error': 'No diagnoses found for criteria'}
            
        # Aggregate by failure type
        by_type = defaultdict(list)
        for d in diagnoses:
            by_type[d.failure_type].append(d)
            
        # Find most common root causes
        root_causes = defaultdict(int)
        for d in diagnoses:
            root_causes[d.root_cause] += 1
            
        top_causes = sorted(root_causes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Aggregate fix suggestions
        all_fixes = []
        for d in diagnoses:
            all_fixes.extend(d.fix_suggestions)
            
        fix_frequency = defaultdict(int)
        for fix in all_fixes:
            fix_frequency[fix] += 1
            
        top_fixes = sorted(fix_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_diagnoses': len(diagnoses),
            'by_failure_type': {k: len(v) for k, v in by_type.items()},
            'top_root_causes': [
                {'cause': c, 'frequency': f} for c, f in top_causes
            ],
            'common_fix_suggestions': [
                {'fix': f, 'frequency': c} for f, c in top_fixes
            ],
            'pattern_repetition': sum(
                1 for d in diagnoses
                if len(self._find_similar_failures({'symbol': d.symbol}, {'pnl': -0.01})) > 0
            ),
            'recommendations': [
                "Prioritize fixes with highest frequency across failures",
                "Add safeguards for top 3 root causes",
                "Implement pattern detection to prevent repeated failures"
            ]
        }


class SelfCorrectionEngine:
    """
    Self-Correction Engine
    
    AI self-correction and continuous improvement system.
    
    Core Philosophy:
    - Detect errors automatically
    - Learn from mistakes without human intervention  
    - Adjust behavior based on outcomes
    - Maintain correction history for pattern analysis
    
    Capabilities:
    1. Error Detection: Identify when predictions/decisions were wrong
    2. Root Cause Analysis: Determine why the error occurred
    3. Behavioral Adjustment: Modify future behavior based on learnings
    4. Validation: Test if corrections actually work
    5. Meta-Learning: Learn how to learn better
    """
    
    def __init__(self, correction_threshold: float = 0.7):
        self.correction_threshold = correction_threshold
        self.error_history: List[Dict] = []
        self.corrections_applied: List[Dict] = []
        self.behavioral_adjustments: Dict[str, Any] = {}
        self.learning_rate: float = 0.1
        self.correction_success_rate: float = 0.0
        
    def detect_and_record_error(
        self,
        decision_id: str,
        predicted_outcome: str,
        actual_outcome: str,
        confidence: float,
        features: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Detect when the AI made an incorrect prediction/decision.
        
        Returns:
            Error record with classification
        """
        is_error = predicted_outcome != actual_outcome
        
        # Also flag low-confidence correct predictions as warnings
        is_warning = confidence < 0.6 and not is_error
        
        if not is_error and not is_warning:
            return {'status': 'no_error', 'decision_id': decision_id}
        
        error_record = {
            'decision_id': decision_id,
            'timestamp': timestamp or datetime.now(),
            'predicted': predicted_outcome,
            'actual': actual_outcome,
            'confidence': confidence,
            'features': features,
            'error_type': self._classify_error_type(predicted_outcome, actual_outcome, features),
            'severity': 'high' if is_error else 'warning',
            'corrected': False
        }
        
        self.error_history.append(error_record)
        
        # Keep last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.warning(
            f"Self-correction: Detected {error_record['error_type']} error "
            f"in decision {decision_id} (confidence: {confidence:.2f})"
        )
        
        return error_record
    
    def _classify_error_type(
        self,
        predicted: str,
        actual: str,
        features: Dict[str, Any]
    ) -> str:
        """Classify the type of error for targeted correction."""
        if predicted == 'buy' and actual == 'sell':
            return 'false_positive'
        elif predicted == 'sell' and actual == 'buy':
            return 'false_negative'
        elif predicted == 'trade' and actual == 'abstain':
            return 'overtrading_bias'
        elif predicted == 'abstain' and actual == 'trade':
            return 'opportunity_miss'
        elif 'regime' in features and features.get('regime_mismatch', False):
            return 'regime_misclassification'
        else:
            return 'general_error'
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in errors to identify systematic issues.
        
        Returns:
            Pattern analysis with targeted correction suggestions
        """
        if len(self.error_history) < 10:
            return {'status': 'insufficient_data'}
        
        recent_errors = self.error_history[-20:]
        
        # Analyze by error type
        type_counts = Counter(e['error_type'] for e in recent_errors)
        
        # Analyze by features
        feature_correlations = self._analyze_feature_correlations(recent_errors)
        
        # Calculate error rate trend
        error_rates_by_period = self._calculate_error_rate_trend()
        
        # Identify systematic biases
        biases = self._identify_systematic_biases(recent_errors)
        
        return {
            'error_type_distribution': dict(type_counts),
            'most_common_error': type_counts.most_common(1)[0] if type_counts else None,
            'feature_correlations': feature_correlations,
            'error_rate_trend': error_rates_by_period,
            'systematic_biases': biases,
            'improving': error_rates_by_period[-1] < error_rates_by_period[0] if len(error_rates_by_period) > 1 else None,
            'needs_intervention': type_counts.most_common(1)[0][1] > 5 if type_counts else False
        }
    
    def _analyze_feature_correlations(self, errors: List[Dict]) -> Dict[str, float]:
        """Find which features correlate with errors."""
        correlations = {}
        
        # Check confidence correlation
        confidences = [e['confidence'] for e in errors]
        avg_confidence = np.mean(confidences)
        correlations['low_confidence_errors'] = avg_confidence < 0.6
        
        # Check regime correlation
        regime_errors = [e for e in errors if 'volatile' in str(e.get('features', {}).get('regime', ''))]
        correlations['volatile_regime_errors'] = len(regime_errors) / len(errors) if errors else 0
        
        # Check timing correlation
        recent_errors = [e for e in errors if (datetime.now() - e['timestamp']).days < 7]
        correlations['recent_error_spike'] = len(recent_errors) > len(errors) * 0.5
        
        return correlations
    
    def _calculate_error_rate_trend(self) -> List[float]:
        """Calculate error rate trend over time periods."""
        # Group by week
        weekly_errors = defaultdict(int)
        weekly_total = defaultdict(int)
        
        for error in self.error_history:
            week_key = error['timestamp'].strftime('%Y-%W')
            weekly_errors[week_key] += 1
        
        # Get last 4 weeks
        sorted_weeks = sorted(weekly_errors.keys())[-4:]
        return [weekly_errors[w] for w in sorted_weeks]
    
    def _identify_systematic_biases(self, errors: List[Dict]) -> List[Dict]:
        """Identify systematic biases in AI behavior."""
        biases = []
        
        # Check for overconfidence bias
        high_conf_errors = [e for e in errors if e['confidence'] > 0.8]
        if len(high_conf_errors) > len(errors) * 0.3:
            biases.append({
                'type': 'overconfidence',
                'description': 'Making errors despite high confidence',
                'frequency': len(high_conf_errors) / len(errors),
                'severity': 'high'
            })
        
        # Check for recency bias
        recent_wins = [e for e in errors if e['actual'] == 'win' and (datetime.now() - e['timestamp']).days < 3]
        if len(recent_wins) > 5:
            biases.append({
                'type': 'recency_bias',
                'description': 'Overweighting recent outcomes',
                'frequency': len(recent_wins) / len(errors),
                'severity': 'medium'
            })
        
        return biases
    
    def apply_behavioral_correction(self, error_type: str) -> Dict[str, Any]:
        """
        Apply behavioral correction based on error type.
        
        Returns:
            Correction details and expected impact
        """
        correction = {
            'error_type': error_type,
            'timestamp': datetime.now(),
            'adjustments': [],
            'expected_impact': 'unknown'
        }
        
        if error_type == 'false_positive':
            # Reduce sensitivity to positive signals
            self.behavioral_adjustments['signal_threshold'] = \
                self.behavioral_adjustments.get('signal_threshold', 0.5) + 0.05
            correction['adjustments'].append(
                f"Increased signal threshold to {self.behavioral_adjustments['signal_threshold']:.2f}"
            )
            correction['expected_impact'] = 'Reduce false buy signals'
            
        elif error_type == 'false_negative':
            # Increase sensitivity to negative signals
            self.behavioral_adjustments['signal_threshold'] = \
                self.behavioral_adjustments.get('signal_threshold', 0.5) - 0.03
            correction['adjustments'].append(
                f"Decreased signal threshold to {self.behavioral_adjustments['signal_threshold']:.2f}"
            )
            correction['expected_impact'] = 'Catch more valid signals'
            
        elif error_type == 'overtrading_bias':
            # Add cooling-off mechanism
            self.behavioral_adjustments['min_time_between_trades'] = \
                self.behavioral_adjustments.get('min_time_between_trades', 0) + 1
            correction['adjustments'].append(
                f"Added {self.behavioral_adjustments['min_time_between_trades']} minute cooling-off"
            )
            correction['expected_impact'] = 'Reduce overtrading'
            
        elif error_type == 'regime_misclassification':
            # Strengthen regime validation
            self.behavioral_adjustments['regime_confidence_threshold'] = \
                self.behavioral_adjustments.get('regime_confidence_threshold', 0.6) + 0.1
            correction['adjustments'].append(
                f"Increased regime confidence threshold to {self.behavioral_adjustments['regime_confidence_threshold']:.2f}"
            )
            correction['expected_impact'] = 'More conservative regime classification'
            
        elif error_type == 'opportunity_miss':
            # Lower barriers for valid signals
            self.behavioral_adjustments['opportunity_threshold'] = \
                self.behavioral_adjustments.get('opportunity_threshold', 0.7) - 0.05
            correction['adjustments'].append(
                f"Lowered opportunity threshold to {self.behavioral_adjustments['opportunity_threshold']:.2f}"
            )
            correction['expected_impact'] = 'Capture more valid opportunities'
        
        self.corrections_applied.append(correction)
        
        logger.info(f"Self-correction applied: {error_type} - {correction['adjustments']}")
        
        return correction
    
    def validate_corrections(self, validation_window: int = 20) -> Dict[str, Any]:
        """
        Validate if applied corrections are working.
        
        Returns:
            Validation results with success metrics
        """
        if len(self.corrections_applied) < 3:
            return {'status': 'insufficient_corrections'}
        
        # Get recent errors after corrections
        recent_errors = [e for e in self.error_history if e.get('corrected', False)][-validation_window:]
        
        if not recent_errors:
            return {'status': 'no_corrected_errors'}
        
        # Check if same error types are still occurring
        pre_correction_types = Counter(
            e['error_type'] for e in self.error_history 
            if not e.get('corrected', False)
        )
        
        post_correction_types = Counter(
            e['error_type'] for e in recent_errors
        )
        
        # Calculate correction success
        total_corrected = len(recent_errors)
        successful_corrections = sum(
            1 for e in recent_errors 
            if e['error_type'] not in pre_correction_types or 
            post_correction_types[e['error_type']] < pre_correction_types.get(e['error_type'], 0)
        )
        
        success_rate = successful_corrections / total_corrected if total_corrected > 0 else 0
        self.correction_success_rate = success_rate
        
        return {
            'total_corrections_applied': len(self.corrections_applied),
            'corrections_validated': total_corrected,
            'successful_corrections': successful_corrections,
            'success_rate': success_rate,
            'correction_working': success_rate > 0.6,
            'recommendation': 'Continue current corrections' if success_rate > 0.6 else 'Review and adjust corrections',
            'error_type_reduction': {
                error_type: pre_correction_types.get(error_type, 0) - post_correction_types.get(error_type, 0)
                for error_type in set(pre_correction_types.keys()) | set(post_correction_types.keys())
            }
        }
    
    def get_self_correction_status(self) -> Dict[str, Any]:
        """Get comprehensive self-correction status."""
        pattern_analysis = self.analyze_error_patterns()
        validation = self.validate_corrections()
        
        return {
            'total_errors_recorded': len(self.error_history),
            'total_corrections_applied': len(self.corrections_applied),
            'correction_success_rate': self.correction_success_rate,
            'current_adjustments': self.behavioral_adjustments,
            'error_patterns': pattern_analysis,
            'validation_results': validation,
            'self_awareness_score': self._calculate_self_awareness(),
            'improvement_trajectory': pattern_analysis.get('improving', None),
            'action_required': validation.get('correction_working', True) == False or 
                             pattern_analysis.get('needs_intervention', False)
        }
    
    def _calculate_self_awareness(self) -> float:
        """Calculate how well the AI knows its own limitations."""
        if not self.error_history:
            return 0.0
        
        # Factors:
        # 1. Error detection rate (should be high)
        # 2. Correction application rate (should be moderate)
        # 3. Validation success (should be tracked)
        
        detection_coverage = min(1.0, len(self.error_history) / 50)  # Expect at least 50 tracked
        correction_activity = min(1.0, len(self.corrections_applied) / 10)  # Some corrections applied
        validation_present = 1.0 if self.correction_success_rate > 0 else 0.0
        
        return (detection_coverage * 0.4 + correction_activity * 0.3 + validation_present * 0.3)
    
    def auto_correct(self) -> Dict[str, Any]:
        """
        Automatically detect issues and apply corrections.
        
        This is the main entry point for autonomous self-correction.
        """
        # Analyze current patterns
        patterns = self.analyze_error_patterns()
        
        if patterns.get('status') == 'insufficient_data':
            return {'status': 'insufficient_data', 'action': 'none'}
        
        corrections_made = []
        
        # Check for systematic biases
        biases = patterns.get('systematic_biases', [])
        for bias in biases:
            if bias['severity'] == 'high':
                correction = self.apply_behavioral_correction(bias['type'])
                corrections_made.append(correction)
        
        # Check most common error type
        most_common = patterns.get('most_common_error')
        if most_common and most_common[1] > 3:  # More than 3 occurrences
            correction = self.apply_behavioral_correction(most_common[0])
            corrections_made.append(correction)
        
        # Validate previous corrections
        validation = self.validate_corrections()
        
        return {
            'status': 'completed',
            'corrections_applied': len(corrections_made),
            'correction_details': corrections_made,
            'validation_status': validation,
            'current_self_awareness': self._calculate_self_awareness(),
            'recommendation': 'Monitor corrections' if corrections_made else 'No corrections needed'
        }
