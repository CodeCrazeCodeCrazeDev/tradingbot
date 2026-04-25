"""
Counterfactual Reasoner - "What-If" Scenario Analysis
=========================================================

Implements counterfactual reasoning capabilities:
1. Historical scenario replay
2. Alternative history generation
3. Causal attribution
4. Decision post-mortem analysis

Enables analysis of "what would have happened if..." scenarios.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass
class CounterfactualScenario:
    """A counterfactual scenario definition"""
    scenario_id: str
    name: str
    description: str
    
    # Changes from actual history
    interventions: Dict[str, Any] = field(default_factory=dict)  # variable -> new value
    
    # Scope
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Baseline
    baseline_data: Optional[Dict] = None


@dataclass
class CounterfactualResult:
    """Result of a counterfactual analysis"""
    scenario_id: str
    
    # Outcomes
    actual_outcome: float
    counterfactual_outcome: float
    
    # Impact
    absolute_difference: float = 0.0
    relative_difference: float = 0.0
    
    # Causal attribution
    attribution_by_variable: Dict[str, float] = field(default_factory=dict)
    
    # Confidence
    confidence: float = 0.5
    
    # Timing
    computed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'scenario_id': self.scenario_id,
            'actual': self.actual_outcome,
            'counterfactual': self.counterfactual_outcome,
            'difference': self.absolute_difference,
            'relative_diff': self.relative_difference,
            'confidence': self.confidence
        }


class CounterfactualReasoner:
    """
    Counterfactual Reasoner
    
    Analyzes "what-if" scenarios to understand causal relationships
    and improve decision-making through retrospective analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Scenarios
        self.scenarios: Dict[str, CounterfactualScenario] = {}
        self.results: List[CounterfactualResult] = []
        
        # Historical data storage
        self.historical_data: Dict[str, List[Dict]] = {}
        
        # Model for prediction (placeholder)
        self.prediction_model: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            'scenarios_created': 0,
            'scenarios_analyzed': 0,
            'total_counterfactuals': 0
        }
        
        logger.info("Counterfactual Reasoner initialized")
    
    def create_scenario(
        self,
        name: str,
        description: str,
        interventions: Dict[str, Any],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        baseline_data: Optional[Dict] = None
    ) -> CounterfactualScenario:
        """Create a new counterfactual scenario"""
        scenario = CounterfactualScenario(
            scenario_id=f"cf_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.scenarios)}",
            name=name,
            description=description,
            interventions=interventions,
            start_time=start_time,
            end_time=end_time,
            baseline_data=baseline_data
        )
        
        self.scenarios[scenario.scenario_id] = scenario
        self.stats['scenarios_created'] += 1
        
        logger.info(f"Created counterfactual scenario: {name}")
        
        return scenario
    
    def analyze_scenario(
        self,
        scenario_id: str,
        outcome_variable: str,
        historical_data: Optional[Dict[str, np.ndarray]] = None
    ) -> CounterfactualResult:
        """Analyze a counterfactual scenario"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        scenario = self.scenarios[scenario_id]
        data = historical_data or scenario.baseline_data
        
        if data is None:
            raise ValueError("No data provided for analysis")
        
        # Get actual outcome
        actual_outcome = self._compute_outcome(data, outcome_variable)
        
        # Apply interventions
        counterfactual_data = self._apply_interventions(
            deepcopy(data),
            scenario.interventions
        )
        
        # Compute counterfactual outcome
        counterfactual_outcome = self._compute_outcome(
            counterfactual_data,
            outcome_variable
        )
        
        # Calculate differences
        abs_diff = counterfactual_outcome - actual_outcome
        rel_diff = abs_diff / max(abs(actual_outcome), 1e-10)
        
        # Causal attribution
        attribution = self._attribute_effects(
            data,
            scenario.interventions,
            outcome_variable
        )
        
        result = CounterfactualResult(
            scenario_id=scenario_id,
            actual_outcome=actual_outcome,
            counterfactual_outcome=counterfactual_outcome,
            absolute_difference=abs_diff,
            relative_difference=rel_diff,
            attribution_by_variable=attribution,
            confidence=0.7  # Based on model confidence
        )
        
        self.results.append(result)
        self.stats['scenarios_analyzed'] += 1
        self.stats['total_counterfactuals'] += 1
        
        return result
    
    def _apply_interventions(
        self,
        data: Dict[str, np.ndarray],
        interventions: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """Apply counterfactual interventions to data"""
        modified_data = deepcopy(data)
        
        for variable, new_value in interventions.items():
            if variable in modified_data:
                if isinstance(new_value, (int, float)):
                    # Constant intervention
                    modified_data[variable] = np.full_like(
                        modified_data[variable],
                        new_value
                    )
                elif isinstance(new_value, str) and new_value.startswith('shift_'):
                    # Shift intervention
                    shift = float(new_value.split('_')[1])
                    modified_data[variable] = modified_data[variable] * (1 + shift)
                elif callable(new_value):
                    # Function intervention
                    modified_data[variable] = new_value(modified_data[variable])
        
        return modified_data
    
    def _compute_outcome(
        self,
        data: Dict[str, np.ndarray],
        outcome_variable: str
    ) -> float:
        """Compute the outcome from data"""
        if outcome_variable in data:
            # Simple aggregation - could be more sophisticated
            return np.mean(data[outcome_variable])
        
        # Try to compute composite outcome
        if outcome_variable == 'portfolio_return':
            returns = data.get('returns', np.array([0]))
            weights = data.get('weights', np.ones_like(returns) / len(returns))
            return np.sum(returns * weights)
        
        if outcome_variable == 'sharpe_ratio':
            returns = data.get('returns', np.array([0]))
            if len(returns) > 1:
                return np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
            return 0.0
        
        return 0.0
    
    def _attribute_effects(
        self,
        data: Dict[str, np.ndarray],
        interventions: Dict[str, Any],
        outcome_variable: str
    ) -> Dict[str, float]:
        """Attribute effects to individual interventions"""
        attributions = {}
        
        baseline_outcome = self._compute_outcome(data, outcome_variable)
        
        for variable, intervention in interventions.items():
            # Apply single intervention
            single_intervention = {variable: intervention}
            modified_data = self._apply_interventions(deepcopy(data), single_intervention)
            single_outcome = self._compute_outcome(modified_data, outcome_variable)
            
            attributions[variable] = single_outcome - baseline_outcome
        
        return attributions
    
    def decision_post_mortem(
        self,
        decision_time: datetime,
        decision: str,
        actual_outcome: float,
        alternative_decisions: List[str],
        historical_context: Dict[str, np.ndarray]
    ) -> Dict:
        """Analyze what would have happened with different decisions"""
        results = {
            'decision_time': decision_time.isoformat(),
            'actual_decision': decision,
            'actual_outcome': actual_outcome,
            'alternatives': []
        }
        
        for alt_decision in alternative_decisions:
            # Create scenario for alternative
            scenario = self.create_scenario(
                name=f"Alternative: {alt_decision}",
                description=f"What if we had chosen {alt_decision} instead of {decision}?",
                interventions={'decision': alt_decision},
                baseline_data=historical_context
            )
            
            # Analyze
            cf_result = self.analyze_scenario(
                scenario.scenario_id,
                outcome_variable='outcome',
                historical_data=historical_context
            )
            
            results['alternatives'].append({
                'decision': alt_decision,
                'predicted_outcome': cf_result.counterfactual_outcome,
                'difference_from_actual': cf_result.absolute_difference,
                'would_have_been_better': cf_result.counterfactual_outcome > actual_outcome
            })
        
        # Determine if right decision was made
        best_alternative = max(results['alternatives'], key=lambda x: x['predicted_outcome'])
        results['decision_quality'] = 'optimal' if actual_outcome >= best_alternative['predicted_outcome'] else 'suboptimal'
        results['opportunity_cost'] = best_alternative['predicted_outcome'] - actual_outcome if results['decision_quality'] == 'suboptimal' else 0.0
        
        return results
    
    def historical_replay(
        self,
        start_date: datetime,
        end_date: datetime,
        strategy_function: Callable,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """Replay historical period with modified strategy"""
        # This would replay actual historical data with different strategy
        # Simplified implementation
        
        scenario = self.create_scenario(
            name=f"Historical Replay {start_date.date()} to {end_date.date()}",
            description="Replay with modified strategy parameters",
            interventions=modifications or {},
            start_time=start_date,
            end_time=end_date
        )
        
        # Simulate replay
        n_days = (end_date - start_date).days
        
        # Generate synthetic data for demonstration
        np.random.seed(42)
        returns = np.random.normal(0.0001, 0.02, n_days)
        
        # Apply strategy
        if modifications:
            # Modify returns based on strategy changes
            leverage = modifications.get('leverage', 1.0)
            returns = returns * leverage
        
        historical_data = {
            'returns': returns,
            'dates': [start_date + timedelta(days=i) for i in range(n_days)]
        }
        
        # Analyze
        result = self.analyze_scenario(
            scenario.scenario_id,
            outcome_variable='portfolio_return',
            historical_data=historical_data
        )
        
        return {
            'scenario_id': scenario.scenario_id,
            'period': f"{start_date.date()} to {end_date.date()}",
            'actual_return': result.actual_outcome,
            'counterfactual_return': result.counterfactual_outcome,
            'modifications': modifications,
            'result': result.to_dict()
        }
    
    def sensitivity_analysis(
        self,
        base_data: Dict[str, np.ndarray],
        outcome_variable: str,
        variables: List[str],
        perturbation_range: Tuple[float, float] = (-0.2, 0.2),
        steps: int = 10
    ) -> Dict[str, List[Tuple[float, float]]]:
        """Perform sensitivity analysis on variables"""
        results = {}
        
        for variable in variables:
            if variable not in base_data:
                continue
            
            variable_results = []
            
            for perturbation in np.linspace(perturbation_range[0], perturbation_range[1], steps):
                # Apply perturbation
                intervention = {variable: f"shift_{perturbation}"}
                modified_data = self._apply_interventions(deepcopy(base_data), intervention)
                
                # Compute outcome
                outcome = self._compute_outcome(modified_data, outcome_variable)
                
                variable_results.append((perturbation, outcome))
            
            results[variable] = variable_results
        
        return results
    
    def what_if_analysis(
        self,
        base_data: Dict[str, np.ndarray],
        outcome_variable: str,
        questions: List[Dict]
    ) -> List[Dict]:
        """Answer "what if" questions"""
        answers = []
        
        for question in questions:
            q_text = question.get('question', '')
            interventions = question.get('interventions', {})
            
            # Create scenario
            scenario = self.create_scenario(
                name=q_text[:50],
                description=q_text,
                interventions=interventions,
                baseline_data=base_data
            )
            
            # Analyze
            result = self.analyze_scenario(
                scenario.scenario_id,
                outcome_variable=outcome_variable,
                historical_data=base_data
            )
            
            answers.append({
                'question': q_text,
                'actual': result.actual_outcome,
                'what_if': result.counterfactual_outcome,
                'difference': result.absolute_difference,
                'conclusion': self._generate_conclusion(result)
            })
        
        return answers
    
    def _generate_conclusion(self, result: CounterfactualResult) -> str:
        """Generate natural language conclusion from result"""
        if abs(result.relative_difference) < 0.01:
            return "The intervention would have minimal impact"
        elif result.relative_difference > 0.1:
            return f"The intervention would significantly improve outcomes by {result.relative_difference:.1%}"
        elif result.relative_difference < -0.1:
            return f"The intervention would significantly harm outcomes by {abs(result.relative_difference):.1%}"
        elif result.relative_difference > 0:
            return f"The intervention would moderately improve outcomes by {result.relative_difference:.1%}"
        else:
            return f"The intervention would moderately harm outcomes by {abs(result.relative_difference):.1%}"
    
    def get_statistics(self) -> Dict:
        """Get reasoner statistics"""
        return {
            **self.stats,
            'scenarios_available': len(self.scenarios),
            'results_computed': len(self.results),
            'avg_confidence': np.mean([r.confidence for r in self.results]) if self.results else 0.0
        }
