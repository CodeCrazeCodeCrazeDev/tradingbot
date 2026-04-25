"""
Offline Research and Failure Analysis Plane

Its job:
- Analyze rejected and accepted decisions
- Compare expected vs realized outcomes
- Run counterfactuals
- Detect repeated failure modes
- Discover missing capabilities
- Generate upgrade proposals

This plane must NEVER directly affect live decisions.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import asyncio

from .core_types import (
    GovernanceDecision, DecisionRecord, OutcomeRecord, FailurePattern,
    CapabilityHypothesis
)
from .layer3_adversarial_analyst import AdversarialCounterAnalyst
from .layer5_counterfactual import CounterfactualSimulator
from .memory_system import DecisionMemory, OutcomeMemory, FailureMemory

logger = logging.getLogger(__name__)


class OfflineResearchPlane:
    """
    Deep analysis plane that runs offline.
    Identifies failure patterns and generates improvement proposals.
    """
    
    def __init__(
        self,
        decision_memory: DecisionMemory,
        outcome_memory: OutcomeMemory,
        failure_memory: FailureMemory
    ):
        self.decision_memory = decision_memory
        self.outcome_memory = outcome_memory
        self.failure_memory = failure_memory
        
        # Analysis components
        self.adversarial_analyst = AdversarialCounterAnalyst(attack_depth=5)
        self.counterfactual_simulator = CounterfactualSimulator()
        
        # Analysis results cache
        self.last_analysis_time: Optional[datetime] = None
        self.analysis_results: Dict[str, Any] = {}
        
    async def run_comprehensive_analysis(
        self,
        since: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive offline analysis.
        
        Args:
            since: Analyze decisions since this time
            symbol: Limit to specific symbol
            
        Returns:
            Analysis results
        """
        if since is None:
            since = datetime.utcnow() - timedelta(days=30)
            
        results = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'period_start': since.isoformat(),
            'symbol': symbol,
            'sections': {}
        }
        
        # Section 1: Decision-outcome analysis
        results['sections']['outcome_analysis'] = await self._analyze_outcomes(since, symbol)
        
        # Section 2: Failure pattern detection
        results['sections']['failure_patterns'] = await self._detect_failure_patterns(since, symbol)
        
        # Section 3: Deep adversarial analysis
        results['sections']['adversarial_analysis'] = await self._run_adversarial_analysis(since, symbol)
        
        # Section 4: Counterfactual analysis
        results['sections']['counterfactual_analysis'] = await self._run_counterfactual_analysis(since, symbol)
        
        # Section 5: Capability gap analysis
        results['sections']['capability_gaps'] = await self._identify_capability_gaps()
        
        # Section 6: Generate upgrade proposals
        results['sections']['upgrade_proposals'] = await self._generate_upgrade_proposals(results)
        
        self.last_analysis_time = datetime.utcnow()
        self.analysis_results = results
        
        logger.info(f"Completed comprehensive analysis with {len(results['sections'])} sections")
        
        return results
    
    async def _analyze_outcomes(
        self,
        since: datetime,
        symbol: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze decision outcomes"""
        
        # Get attribution report
        report = self.outcome_memory.generate_attribution_report(
            self.decision_memory,
            symbol
        )
        
        # Get calibration metrics
        calibration = self.outcome_memory.calculate_calibration_metrics(symbol, since)
        
        return {
            'attribution_report': report,
            'calibration_metrics': calibration,
            'summary': {
                'total_trades_analyzed': report.get('total_trades', 0),
                'win_rate': report.get('win_rate', 0),
                'calibration_quality': calibration.get('brier_score', 0.25)
            }
        }
    
    async def _detect_failure_patterns(
        self,
        since: datetime,
        symbol: Optional[str]
    ) -> Dict[str, Any]:
        """Detect and catalog failure patterns"""
        
        # Get decisions with outcomes
        if symbol:
            decisions = self.decision_memory.get_decisions_by_symbol(symbol, since)
        else:
            decisions = [
                d for d in self.decision_memory.decisions.values()
                if d.timestamp >= since
            ]
            
        # Match with outcomes and record failures
        patterns_updated = 0
        
        for decision in decisions:
            outcome = self.outcome_memory.get_outcome(decision.id)
            if outcome and outcome.realized_pnl < 0:
                pattern = self.failure_memory.record_failure(decision, outcome)
                if pattern:
                    patterns_updated += 1
                    
        # Get current patterns
        top_patterns = self.failure_memory.get_top_patterns(n=10)
        
        return {
            'patterns_updated': patterns_updated,
            'total_patterns': len(self.failure_memory.patterns),
            'top_patterns': [
                {
                    'name': p.pattern_name,
                    'frequency': p.frequency,
                    'severity': p.severity,
                    'description': p.description,
                    'root_cause': p.root_cause_hypothesis
                }
                for p in top_patterns
            ],
            'failure_statistics': self.failure_memory.get_statistics()
        }
    
    async def _run_adversarial_analysis(
        self,
        since: datetime,
        symbol: Optional[str]
    ) -> Dict[str, Any]:
        """Run deep adversarial analysis on recent decisions"""
        
        # Get recent approved decisions
        if symbol:
            decisions = self.decision_memory.get_decisions_by_symbol(symbol, since)
        else:
            decisions = [
                d for d in self.decision_memory.decisions.values()
                if d.timestamp >= since
            ]
            
        approved = [
            d for d in decisions
            if d.final_decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]
        ][:20]  # Limit to 20 for performance
        
        adversarial_results = []
        
        for decision in approved:
            # Generate deep challenges
            challenges = self.adversarial_analyst.generate_challenges(
                claims=decision.claims,
                current_regime=decision.current_regime,
                symbol=decision.symbol
            )
            
            # Check if any high-severity challenges were missed
            missed_challenges = [
                c for c in challenges
                if c.severity > 0.7 and c.id not in [ch.id for ch in decision.adversarial_challenges]
            ]
            
            if missed_challenges:
                adversarial_results.append({
                    'decision_id': decision.id,
                    'symbol': decision.symbol,
                    'missed_challenges': [
                        {
                            'type': c.challenge_type,
                            'severity': c.severity,
                            'content': c.content[:100]
                        }
                        for c in missed_challenges
                    ]
                })
                
        return {
            'decisions_analyzed': len(approved),
            'with_missed_challenges': len(adversarial_results),
            'missed_challenges_summary': adversarial_results,
            'recommendation': 'Increase adversarial depth in real-time plane' if adversarial_results else 'Adversarial coverage adequate'
        }
    
    async def _run_counterfactual_analysis(
        self,
        since: datetime,
        symbol: Optional[str]
    ) -> Dict[str, Any]:
        """Run counterfactual analysis on recent decisions"""
        
        # Get decisions that resulted in losses
        if symbol:
            outcomes = self.outcome_memory.get_outcomes_by_symbol(symbol, since)
        else:
            outcomes = [
                (o, oid) for oid, o in self.outcome_memory.outcomes.items()
                if o.timestamp >= since
            ]
            
        losing_outcomes = [(o, oid) for o, oid in outcomes if o.realized_pnl < 0]
        
        counterfactual_insights = []
        
        for outcome, decision_id in losing_outcomes[:10]:  # Limit for performance
            decision = self.decision_memory.get_decision(decision_id)
            if not decision:
                continue
                
            # Run counterfactuals
            scenarios, robustness = self.counterfactual_simulator.simulate_counterfactuals(
                claims=decision.claims,
                current_regime=decision.current_regime,
                evidence=[],
                original_confidence=outcome.confidence_error
            )
            
            # Check if thesis would have failed counterfactuals
            fragile_deps = self.counterfactual_simulator.identify_fragile_dependencies(scenarios)
            
            if fragile_deps:
                counterfactual_insights.append({
                    'decision_id': decision_id,
                    'symbol': decision.symbol,
                    'pnl': outcome.realized_pnl,
                    'fragile_dependencies': fragile_deps,
                    'robustness_score': robustness
                })
                
        return {
            'losing_trades_analyzed': len(losing_outcomes),
            'fragile_theses_identified': len(counterfactual_insights),
            'insights': counterfactual_insights,
            'recommendations': self._generate_counterfactual_recommendations(counterfactual_insights)
        }
    
    def _generate_counterfactual_recommendations(
        self,
        insights: List[Dict]
    ) -> List[str]:
        """Generate recommendations from counterfactual analysis"""
        
        if not insights:
            return ["Counterfactual robustness adequate"]
            
        recommendations = []
        
        # Count types of fragility
        evidence_deps = sum(
            1 for i in insights
            for d in i['fragile_dependencies']
            if d['type'] == 'evidence_removal'
        )
        market_deps = sum(
            1 for i in insights
            for d in i['fragile_dependencies']
            if d['type'] == 'market_perturbation'
        )
        
        if evidence_deps > 5:
            recommendations.append(
                "Too many theses are fragile to evidence removal - improve evidence requirements"
            )
            
        if market_deps > 5:
            recommendations.append(
                "Too many theses fail under market stress - require higher robustness scores"
            )
            
        return recommendations if recommendations else ["Improve robustness testing"]
    
    async def _identify_capability_gaps(self) -> Dict[str, Any]:
        """Identify missing capabilities based on failures"""
        
        gaps = self.failure_memory.generate_capability_gaps()
        
        return {
            'total_gaps_identified': len(gaps),
            'priority_gaps': gaps[:5],
            'capability_requirements': list(set(g['required_capability'] for g in gaps))
        }
    
    async def _generate_upgrade_proposals(
        self,
        analysis_results: Dict[str, Any]
    ) -> List[CapabilityHypothesis]:
        """Generate concrete upgrade proposals based on analysis"""
        
        proposals = []
        
        # Analyze gaps
        gaps = analysis_results['sections']['capability_gaps']['priority_gaps']
        
        for gap in gaps:
            proposal = self._create_capability_hypothesis(gap)
            if proposal:
                proposals.append(proposal)
                
        # Add proposals from counterfactual analysis
        counterfactual_rec = analysis_results['sections']['counterfactual_analysis'].get('recommendations', [])
        for rec in counterfactual_rec:
            if 'evidence' in rec.lower():
                proposals.append(CapabilityHypothesis(
                    id="",
                    gap_description="Insufficient evidence requirements",
                    capability_type="feature",
                    implementation_sketch="Add stricter evidence validation layer",
                    expected_improvement=0.15
                ))
            elif 'robustness' in rec.lower():
                proposals.append(CapabilityHypothesis(
                    id="",
                    gap_description="Insufficient robustness testing",
                    capability_type="model",
                    implementation_sketch="Enhance counterfactual simulator with more scenarios",
                    expected_improvement=0.20
                ))
                
        return proposals
    
    def _create_capability_hypothesis(
        self,
        gap: Dict[str, Any]
    ) -> Optional[CapabilityHypothesis]:
        """Create a capability hypothesis from a gap"""
        
        capability = gap['required_capability']
        
        # Map capability to implementation
        implementation_map = {
            'real_time_invalidation_monitoring': 'Add continuous invalidation monitoring with alerts',
            'better_calibration_system': 'Implement Platt scaling or isotonic regression for calibration',
            'improved_regime_detection': 'Add regime detection using HMM or clustering',
            'enhanced_counterfactual_testing': 'Increase counterfactual scenarios to 10+ per decision',
            'better_execution_modeling': 'Add execution cost model using market impact data',
            'additional_feature_discovery': 'Run automated feature discovery on failure cases'
        }
        
        return CapabilityHypothesis(
            id="",
            gap_description=gap['description'],
            capability_type='feature',
            implementation_sketch=implementation_map.get(capability, 'Research required'),
            expected_improvement=gap['severity'] * 0.2  # Higher severity = more improvement
        )
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of last analysis"""
        
        if not self.last_analysis_time:
            return {'error': 'No analysis has been run yet'}
            
        return {
            'last_analysis': self.last_analysis_time.isoformat(),
            'sections_analyzed': list(self.analysis_results.get('sections', {}).keys()),
            'key_findings': self._extract_key_findings(self.analysis_results)
        }
        
    def _extract_key_findings(self, results: Dict[str, Any]) -> List[str]:
        """Extract key findings from analysis"""
        
        findings = []
        
        # From outcome analysis
        outcome = results['sections'].get('outcome_analysis', {})
        if outcome.get('summary', {}).get('win_rate', 0.5) < 0.45:
            findings.append("Win rate below 45% - system performance concerning")
            
        # From failure patterns
        failures = results['sections'].get('failure_patterns', {})
        if failures.get('total_patterns', 0) > 10:
            findings.append(f"{failures['total_patterns']} failure patterns detected - systematic issues present")
            
        # From adversarial analysis
        adversarial = results['sections'].get('adversarial_analysis', {})
        if adversarial.get('with_missed_challenges', 0) > 5:
            findings.append("Many adversarial challenges missed in real-time - improve adversarial depth")
            
        return findings if findings else ["No critical findings - system operating within normal parameters"]
