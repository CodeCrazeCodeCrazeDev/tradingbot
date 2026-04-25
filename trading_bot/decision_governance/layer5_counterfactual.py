"""
Layer 5: Counterfactual Simulator

For each approved thesis:
- Remove one major evidence pillar
- Perturb market conditions
- Alter execution assumptions
- Test opposite-side causal narratives

Tests robustness of thesis under various perturbations.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from copy import deepcopy
import logging
import random

from .core_types import (
    Claim, ClaimType, DecisionRecord, MarketRegime, Evidence
)

logger = logging.getLogger(__name__)


@dataclass
class CounterfactualScenario:
    """A counterfactual scenario for testing thesis robustness"""
    id: str
    name: str
    description: str
    perturbation_type: str  # evidence_removal, market_perturbation, execution_change, opposite_narrative
    modified_claims: List[Claim]
    modified_regime: Optional[MarketRegime]
    expected_outcome_change: float  # Expected change in thesis confidence (-1 to 1)
    thesis_survives: bool
    robustness_contribution: float  # How much this test contributes to overall robustness


class CounterfactualSimulator:
    """
    Simulates counterfactual scenarios to test thesis robustness.
    Identifies fragile dependencies in the reasoning chain.
    """
    
    def __init__(
        self,
        min_robustness_score: float = 0.6,
        num_scenarios: int = 5
    ):
        self.min_robustness_score = min_robustness_score
        self.num_scenarios = num_scenarios
        
    def simulate_counterfactuals(
        self,
        claims: List[Claim],
        current_regime: Optional[MarketRegime],
        evidence: List[Evidence],
        original_confidence: float
    ) -> Tuple[List[CounterfactualScenario], float]:
        """
        Run counterfactual simulations on a thesis.
        
        Returns:
            Tuple of (scenarios, overall_robustness_score)
        """
        scenarios = []
        
        # Scenario 1: Remove key evidence
        evidence_scenarios = self._simulate_evidence_removal(claims, evidence, original_confidence)
        scenarios.extend(evidence_scenarios)
        
        # Scenario 2: Perturb market conditions
        if current_regime:
            market_scenarios = self._simulate_market_perturbations(claims, current_regime, original_confidence)
            scenarios.extend(market_scenarios)
            
        # Scenario 3: Alter execution assumptions
        execution_scenarios = self._simulate_execution_changes(claims, original_confidence)
        scenarios.extend(execution_scenarios)
        
        # Scenario 4: Test opposite causal narratives
        opposite_scenarios = self._simulate_opposite_narratives(claims, original_confidence)
        scenarios.extend(opposite_scenarios)
        
        # Calculate overall robustness score
        robustness = self._calculate_robustness_score(scenarios, original_confidence)
        
        # Limit to requested number of scenarios, keeping most informative
        scenarios.sort(key=lambda s: abs(s.expected_outcome_change), reverse=True)
        scenarios = scenarios[:self.num_scenarios]
        
        logger.info(f"Generated {len(scenarios)} counterfactual scenarios, robustness: {robustness:.2f}")
        return scenarios, robustness
    
    def _simulate_evidence_removal(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
        original_confidence: float
    ) -> List[CounterfactualScenario]:
        """Simulate removal of key evidence pillars"""
        
        scenarios = []
        
        # Find evidence claims (strongest evidence)
        evidence_claims = [c for c in claims if c.claim_type == ClaimType.EVIDENCE]
        evidence_claims.sort(key=lambda c: c.confidence, reverse=True)
        
        # Remove top pieces of evidence one at a time
        for i, ev_claim in enumerate(evidence_claims[:3]):
            modified_claims = deepcopy(claims)
            
            # Find and remove this evidence
            for mc in modified_claims:
                if mc.id == ev_claim.id:
                    mc.confidence = 0.0  # Neutralize the evidence
                    mc.content = f"[REMOVED] {mc.content}"
                    
            # Estimate impact
            confidence_impact = -0.15 * (1 - i * 0.2)  # Higher impact for stronger evidence
            new_confidence = max(0, original_confidence + confidence_impact)
            
            scenarios.append(CounterfactualScenario(
                id=f"",
                name=f"Remove Evidence {i+1}",
                description=f"Simulate without evidence: {ev_claim.content[:60]}...",
                perturbation_type="evidence_removal",
                modified_claims=modified_claims,
                modified_regime=None,
                expected_outcome_change=confidence_impact,
                thesis_survives=new_confidence > 0.5,
                robustness_contribution=abs(confidence_impact)
            ))
            
        return scenarios
    
    def _simulate_market_perturbations(
        self,
        claims: List[Claim],
        current_regime: MarketRegime,
        original_confidence: float
    ) -> List[CounterfactualScenario]:
        """Simulate perturbed market conditions"""
        
        scenarios = []
        
        # Perturbation 1: Higher volatility
        high_vol_regime = deepcopy(current_regime)
        high_vol_regime.volatility_state = self._worsen_volatility(current_regime.volatility_state)
        
        vol_impact = -0.25 if original_confidence > 0.7 else -0.15
        scenarios.append(CounterfactualScenario(
            id="",
            name="High Volatility Scenario",
            description=f"Thesis under {high_vol_regime.volatility_state} volatility conditions",
            perturbation_type="market_perturbation",
            modified_claims=deepcopy(claims),
            modified_regime=high_vol_regime,
            expected_outcome_change=vol_impact,
            thesis_survives=(original_confidence + vol_impact) > 0.5,
            robustness_contribution=abs(vol_impact)
        ))
        
        # Perturbation 2: Lower liquidity
        low_liq_regime = deepcopy(current_regime)
        low_liq_regime.liquidity_state = self._worsen_liquidity(current_regime.liquidity_state)
        
        liq_impact = -0.20
        scenarios.append(CounterfactualScenario(
            id="",
            name="Low Liquidity Scenario",
            description=f"Thesis under {low_liq_regime.liquidity_state} liquidity conditions",
            perturbation_type="market_perturbation",
            modified_claims=deepcopy(claims),
            modified_regime=low_liq_regime,
            expected_outcome_change=liq_impact,
            thesis_survives=(original_confidence + liq_impact) > 0.5,
            robustness_contribution=abs(liq_impact)
        ))
        
        # Perturbation 3: Toxic flow
        toxic_regime = deepcopy(current_regime)
        toxic_regime.order_flow_toxicity = "toxic"
        
        toxic_impact = -0.30  # Toxic flow is very damaging
        scenarios.append(CounterfactualScenario(
            id="",
            name="Toxic Flow Scenario",
            description="Thesis under toxic order flow conditions",
            perturbation_type="market_perturbation",
            modified_claims=deepcopy(claims),
            modified_regime=toxic_regime,
            expected_outcome_change=toxic_impact,
            thesis_survives=(original_confidence + toxic_impact) > 0.5,
            robustness_contribution=abs(toxic_impact)
        ))
        
        return scenarios
    
    def _simulate_execution_changes(
        self,
        claims: List[Claim],
        original_confidence: float
    ) -> List[CounterfactualScenario]:
        """Simulate different execution assumptions"""
        
        scenarios = []
        
        # Scenario: Higher slippage
        high_slippage_impact = -0.15
        scenarios.append(CounterfactualScenario(
            id="",
            name="High Slippage Scenario",
            description="Thesis with 2x expected slippage costs",
            perturbation_type="execution_change",
            modified_claims=deepcopy(claims),
            modified_regime=None,
            expected_outcome_change=high_slippage_impact,
            thesis_survives=(original_confidence + high_slippage_impact) > 0.5,
            robustness_contribution=abs(high_slippage_impact)
        ))
        
        # Scenario: Delayed execution
        delay_impact = -0.20
        scenarios.append(CounterfactualScenario(
            id="",
            name="Execution Delay Scenario",
            description="Thesis with 30-minute execution delay",
            perturbation_type="execution_change",
            modified_claims=deepcopy(claims),
            modified_regime=None,
            expected_outcome_change=delay_impact,
            thesis_survives=(original_confidence + delay_impact) > 0.5,
            robustness_contribution=abs(delay_impact)
        ))
        
        # Scenario: Partial fills
        partial_fill_impact = -0.10
        scenarios.append(CounterfactualScenario(
            id="",
            name="Partial Fill Scenario",
            description="Thesis with 50% partial fill rate",
            perturbation_type="execution_change",
            modified_claims=deepcopy(claims),
            modified_regime=None,
            expected_outcome_change=partial_fill_impact,
            thesis_survives=(original_confidence + partial_fill_impact) > 0.5,
            robustness_contribution=abs(partial_fill_impact)
        ))
        
        return scenarios
    
    def _simulate_opposite_narratives(
        self,
        claims: List[Claim],
        original_confidence: float
    ) -> List[CounterfactualScenario]:
        """Test opposite-side causal narratives"""
        
        scenarios = []
        
        # Find causal links and thesis
        causal_links = [c for c in claims if c.claim_type == ClaimType.INFERRED_CAUSAL_LINK]
        thesis = next((c for c in claims if c.claim_type == ClaimType.THESIS), None)
        
        if thesis:
            # Create opposite thesis
            opposite_confidence = 1 - original_confidence  # Confidence in opposite
            opposite_impact = opposite_confidence - original_confidence
            
            modified_claims = deepcopy(claims)
            for mc in modified_claims:
                if mc.id == thesis.id:
                    mc.content = f"[OPPOSITE] {mc.content}"
                    mc.confidence = opposite_confidence
                    
            scenarios.append(CounterfactualScenario(
                id="",
                name="Opposite Narrative",
                description="Test opposite thesis with same evidence",
                perturbation_type="opposite_narrative",
                modified_claims=modified_claims,
                modified_regime=None,
                expected_outcome_change=opposite_impact,
                thesis_survives=opposite_confidence < original_confidence,
                robustness_contribution=abs(opposite_impact)
            ))
            
        return scenarios
    
    def _worsen_volatility(self, current: str) -> str:
        """Increase volatility state"""
        progression = ["low", "normal", "high", "extreme"]
        if current in progression:
            idx = progression.index(current)
            return progression[min(len(progression) - 1, idx + 1)]
        return "high"
    
    def _worsen_liquidity(self, current: str) -> str:
        """Decrease liquidity state"""
        progression = ["ample", "normal", "constrained", "scarce"]
        if current in progression:
            idx = progression.index(current)
            return progression[min(len(progression) - 1, idx + 1)]
        return "constrained"
    
    def _calculate_robustness_score(
        self,
        scenarios: List[CounterfactualScenario],
        original_confidence: float
    ) -> float:
        """
        Calculate overall robustness score.
        
        A thesis is robust if it survives most counterfactuals.
        """
        if not scenarios:
            return 0.5  # Neutral if no scenarios
            
        # Count survival rate
        surviving = sum(1 for s in scenarios if s.thesis_survives)
        survival_rate = surviving / len(scenarios)
        
        # Weight by severity of perturbations survived
        total_contribution = sum(s.robustness_contribution for s in scenarios)
        survived_contribution = sum(
            s.robustness_contribution for s in scenarios if s.thesis_survives
        )
        
        if total_contribution > 0:
            weighted_survival = survived_contribution / total_contribution
        else:
            weighted_survival = survival_rate
            
        # Blend survival rate and weighted survival
        robustness = 0.6 * survival_rate + 0.4 * weighted_survival
        
        # Adjust for original confidence
        # High confidence theses should be more robust
        if original_confidence > 0.8:
            robustness *= 0.9  # Penalize high confidence that's not robust
            
        return min(1.0, max(0.0, robustness))
    
    def identify_fragile_dependencies(
        self,
        scenarios: List[CounterfactualScenario]
    ) -> List[Dict[str, Any]]:
        """Identify which dependencies make the thesis fragile"""
        
        fragile_deps = []
        
        for scenario in scenarios:
            if not scenario.thesis_survives:
                fragile_deps.append({
                    'scenario': scenario.name,
                    'type': scenario.perturbation_type,
                    'impact': scenario.expected_outcome_change,
                    'description': scenario.description,
                    'severity': 'CRITICAL' if scenario.expected_outcome_change < -0.3 else 'HIGH'
                })
                
        # Sort by severity
        fragile_deps.sort(key=lambda d: d['impact'])
        
        return fragile_deps
    
    def generate_stress_test_recommendations(
        self,
        scenarios: List[CounterfactualScenario],
        robustness_score: float
    ) -> List[str]:
        """Generate recommendations based on counterfactual analysis"""
        
        recommendations = []
        
        if robustness_score < 0.5:
            recommendations.append("CRITICAL: Thesis fails under stress - consider rejection")
            
        # Check for pattern in failures
        evidence_failures = sum(
            1 for s in scenarios
            if s.perturbation_type == "evidence_removal" and not s.thesis_survives
        )
        if evidence_failures >= 2:
            recommendations.append(
                "Thesis heavily dependent on limited evidence - gather more supporting data"
            )
            
        market_failures = sum(
            1 for s in scenarios
            if s.perturbation_type == "market_perturbation" and not s.thesis_survives
        )
        if market_failures >= 2:
            recommendations.append(
                "Thesis fragile to market regime changes - implement dynamic sizing"
            )
            
        execution_failures = sum(
            1 for s in scenarios
            if s.perturbation_type == "execution_change" and not s.thesis_survives
            
        )
        if execution_failures >= 2:
            recommendations.append(
                "Thesis sensitive to execution assumptions - use conservative slippage estimates"
            )
            
        return recommendations


class MetaStrategySelector:
    """
    Meta-Strategy Selector
    
    Instead of picking trades:
    Pick which strategy class dominates right now.
    
    Example:
    - trend strategies ON
    - mean reversion OFF
    - volatility strategies ON
    """
    
    def __init__(self):
        self.strategy_classes = {
            'trend_following': {'enabled': True, 'weight': 1.0},
            'mean_reversion': {'enabled': True, 'weight': 1.0},
            'volatility': {'enabled': True, 'weight': 1.0},
            'momentum': {'enabled': True, 'weight': 1.0},
            'breakout': {'enabled': True, 'weight': 1.0}
        }
        self.performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self.regime_performance: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
    def record_strategy_performance(
        self,
        strategy_class: str,
        pnl: float,
        regime: str,
        timestamp: Optional[datetime] = None
    ):
        """Record performance for a strategy class."""
        self.performance_history[strategy_class].append({
            'pnl': pnl,
            'regime': regime,
            'timestamp': timestamp or datetime.now()
        })
        
        self.regime_performance[regime][strategy_class].append(pnl)
        
        # Keep last 50 per strategy
        if len(self.performance_history[strategy_class]) > 50:
            self.performance_history[strategy_class] = self.performance_history[strategy_class][-50:]
    
    def select_strategies_for_regime(self, current_regime: str) -> Dict[str, Any]:
        """Select which strategy classes to enable based on regime."""
        # Get performance by regime
        regime_perf = self.regime_performance.get(current_regime, {})
        
        if not regime_perf:
            # No data for this regime - use conservative defaults
            return {
                'regime': current_regime,
                'selection_method': 'default',
                'enabled_strategies': ['trend_following', 'mean_reversion'],  # Conservative default
                'weights': {k: 0.5 for k in ['trend_following', 'mean_reversion']}
            }
        
        # Calculate Sharpe-like ratio for each strategy class in this regime
        strategy_scores = {}
        
        for strategy_class, pnls in regime_perf.items():
            if len(pnls) < 5:
                continue
            
            mean_pnl = np.mean(pnls)
            std_pnl = np.std(pnls) if len(pnls) > 1 else 0.01
            
            # Sharpe-like score
            sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0
            
            # Win rate
            win_rate = sum(1 for p in pnls if p > 0) / len(pnls)
            
            # Combined score
            score = sharpe * 0.6 + (win_rate - 0.5) * 0.4
            
            strategy_scores[strategy_class] = {
                'score': score,
                'sharpe': sharpe,
                'win_rate': win_rate,
                'sample_size': len(pnls)
            }
        
        # Sort by score
        sorted_strategies = sorted(
            strategy_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        # Enable top strategies (score > 0)
        enabled = [s[0] for s in sorted_strategies if s[1]['score'] > 0]
        
        if not enabled:
            enabled = [sorted_strategies[0][0]] if sorted_strategies else ['trend_following']
        
        # Calculate weights proportional to scores
        total_score = sum(strategy_scores[s]['score'] for s in enabled if s in strategy_scores)
        weights = {}
        
        for strategy in enabled:
            if strategy in strategy_scores:
                weights[strategy] = strategy_scores[strategy]['score'] / total_score if total_score > 0 else 1.0 / len(enabled)
            else:
                weights[strategy] = 1.0 / len(enabled)
        
        return {
            'regime': current_regime,
            'selection_method': 'data_driven',
            'enabled_strategies': enabled,
            'disabled_strategies': [s for s in self.strategy_classes.keys() if s not in enabled],
            'weights': weights,
            'strategy_scores': strategy_scores,
            'recommendation': f"Enable {len(enabled)} strategy classes for {current_regime} regime"
        }
    
    def get_strategy_activation(self, strategy_class: str, current_regime: str) -> Dict[str, Any]:
        """Get activation status and weight for a specific strategy class."""
        selection = self.select_strategies_for_regime(current_regime)
        
        is_enabled = strategy_class in selection['enabled_strategies']
        weight = selection['weights'].get(strategy_class, 0)
        
        return {
            'strategy_class': strategy_class,
            'is_enabled': is_enabled,
            'weight': weight,
            'regime': current_regime,
            'should_trade': is_enabled and weight > 0.1
        }


class FailureReplayEngine:
    """
    Failure Replay Engine
    
    You log failures. That's not enough.
    
    Replay failed trades under different conditions:
    - different entry timing
    - different execution strategy
    - different sizing
    - different regime filter
    
    Goal: Extract missed opportunities from failures
    """
    
    def __init__(self):
        self.failed_trades: List[Dict] = []
        self.replay_results: List[Dict] = []
        self.learned_insights: List[Dict] = []
        
    def record_failure(
        self,
        trade_id: str,
        symbol: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        entry_time: datetime,
        exit_time: datetime,
        size: float,
        strategy: str,
        regime: str,
        failure_reason: str,
        market_conditions: Dict[str, Any]
    ):
        """Record a failed trade for later replay analysis."""
        self.failed_trades.append({
            'trade_id': trade_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'size': size,
            'strategy': strategy,
            'regime': regime,
            'failure_reason': failure_reason,
            'market_conditions': market_conditions,
            'recorded_at': datetime.now()
        })
        
        # Keep last 100 failures
        if len(self.failed_trades) > 100:
            self.failed_trades = self.failed_trades[-100:]
    
    def replay_with_alternatives(
        self,
        trade: Dict,
        price_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Replay a failed trade under different conditions.
        
        Args:
            trade: The failed trade to replay
            price_history: Historical price data for the period
            
        Returns:
            Dictionary with alternative scenario results
        """
        alternatives = {
            'original': {'pnl': trade['pnl'], 'reason': trade['failure_reason']},
            'scenarios': []
        }
        
        # Scenario 1: Different entry timing (delay 5 minutes)
        delayed_entry = self._simulate_delayed_entry(trade, price_history, delay_minutes=5)
        alternatives['scenarios'].append({
            'name': 'delayed_entry_5min',
            'pnl': delayed_entry,
            'improvement': delayed_entry - trade['pnl']
        })
        
        # Scenario 2: Different entry timing (delay 15 minutes)
        delayed_entry_15 = self._simulate_delayed_entry(trade, price_history, delay_minutes=15)
        alternatives['scenarios'].append({
            'name': 'delayed_entry_15min',
            'pnl': delayed_entry_15,
            'improvement': delayed_entry_15 - trade['pnl']
        })
        
        # Scenario 3: Different sizing (50% smaller)
        smaller_size = self._simulate_different_size(trade, size_multiplier=0.5)
        alternatives['scenarios'].append({
            'name': 'half_size',
            'pnl': smaller_size,
            'improvement': smaller_size - trade['pnl']
        })
        
        # Scenario 4: Different sizing (50% larger)
        larger_size = self._simulate_different_size(trade, size_multiplier=1.5)
        alternatives['scenarios'].append({
            'name': 'larger_size',
            'pnl': larger_size,
            'improvement': larger_size - trade['pnl']
        })
        
        # Find best scenario
        best_scenario = max(alternatives['scenarios'], key=lambda x: x['pnl'])
        
        alternatives['best_scenario'] = best_scenario['name']
        alternatives['best_improvement'] = best_scenario['improvement']
        alternatives['missed_opportunity'] = best_scenario['improvement'] > 0
        
        return alternatives
    
    def _simulate_delayed_entry(
        self,
        trade: Dict,
        price_history: List[Dict],
        delay_minutes: int
    ) -> float:
        """Simulate delayed entry."""
        entry_time = trade['entry_time']
        delayed_time = entry_time + timedelta(minutes=delay_minutes)
        
        # Find price at delayed time
        delayed_price = None
        for ph in price_history:
            if ph['timestamp'] >= delayed_time:
                delayed_price = ph['price']
                break
        
        if delayed_price is None:
            return trade['pnl']  # Can't simulate
        
        # Calculate new PnL with delayed entry
        price_diff = trade['exit_price'] - delayed_price
        direction = 1 if trade['entry_price'] < trade['exit_price'] else -1
        
        # Rough estimate: same exit, different entry
        original_diff = trade['exit_price'] - trade['entry_price']
        new_diff = trade['exit_price'] - delayed_price
        
        if original_diff != 0:
            pnl_ratio = new_diff / original_diff
            return trade['pnl'] * pnl_ratio
        
        return trade['pnl']
    
    def _simulate_different_size(self, trade: Dict, size_multiplier: float) -> float:
        """Simulate different position size."""
        # Simple scaling (assumes no market impact)
        return trade['pnl'] * size_multiplier
    
    def analyze_failure_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in failed trades to extract insights."""
        if len(self.failed_trades) < 10:
            return {'status': 'insufficient_data'}
        
        recent_failures = self.failed_trades[-20:]
        
        # Analyze by failure reason
        reason_counts = Counter(f['failure_reason'] for f in recent_failures)
        
        # Analyze by regime
        regime_failures = defaultdict(list)
        for f in recent_failures:
            regime_failures[f['regime']].append(f['pnl'])
        
        regime_stats = {}
        for regime, pnls in regime_failures.items():
            regime_stats[regime] = {
                'count': len(pnls),
                'avg_loss': np.mean(pnls),
                'total_loss': sum(pnls)
            }
        
        # Analyze by strategy
        strategy_failures = defaultdict(list)
        for f in recent_failures:
            strategy_failures[f['strategy']].append(f['pnl'])
        
        strategy_stats = {}
        for strategy, pnls in strategy_failures.items():
            strategy_stats[strategy] = {
                'count': len(pnls),
                'avg_loss': np.mean(pnls),
                'failure_rate': len(pnls) / len(recent_failures)
            }
        
        # Identify worst performing combination
        worst_combo = None
        worst_loss = 0
        for f in recent_failures:
            combo = (f['strategy'], f['regime'])
            if f['pnl'] < worst_loss:
                worst_loss = f['pnl']
                worst_combo = combo
        
        insights = []
        
        # Generate insights
        if reason_counts:
            top_reason = reason_counts.most_common(1)[0]
            if top_reason[1] >= 5:
                insights.append(f"Most common failure: {top_reason[0]} ({top_reason[1]} times)")
        
        if regime_stats:
            worst_regime = min(regime_stats.items(), key=lambda x: x[1]['avg_loss'])
            insights.append(f"Worst regime: {worst_regime[0]} (avg loss: {worst_regime[1]['avg_loss']:.2%})")
        
        if strategy_stats:
            worst_strategy = min(strategy_stats.items(), key=lambda x: x[1]['avg_loss'])
            if worst_strategy[1]['count'] >= 3:
                insights.append(f"Worst strategy: {worst_strategy[0]} needs review")
        
        return {
            'total_failures_analyzed': len(recent_failures),
            'failure_reasons': dict(reason_counts),
            'regime_stats': regime_stats,
            'strategy_stats': strategy_stats,
            'worst_combination': worst_combo,
            'insights': insights,
            'recommendations': self._generate_failure_recommendations(insights)
        }
    
    def _generate_failure_recommendations(self, insights: List[str]) -> List[str]:
        """Generate recommendations based on failure analysis."""
        recommendations = []
        
        for insight in insights:
            if 'stop_loss' in insight.lower():
                recommendations.append("Review stop-loss placement - may be too tight")
            elif 'timing' in insight.lower():
                recommendations.append("Consider entry timing optimization")
            elif 'trend' in insight.lower():
                recommendations.append("Trend regime performing poorly - reduce trend exposure")
            elif 'mean_reversion' in insight.lower():
                recommendations.append("Mean reversion struggling - verify regime detection")
        
        return recommendations if recommendations else ['Continue monitoring failure patterns']
