"""
Collective Intelligence - Emergent Group Intelligence
=========================================================

Implements collective intelligence mechanisms:
1. Wisdom of crowds aggregation
2. Prediction market mechanisms
3. Collaborative filtering
4. Emergent problem solving

Based on swarm intelligence and collective decision-making research.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
from statistics import median

logger = logging.getLogger(__name__)


@dataclass
class CollectivePrediction:
    """A prediction made by the collective"""
    prediction_id: str
    target: str  # What is being predicted
    
    # Individual predictions
    individual_predictions: Dict[str, float] = field(default_factory=dict)  # agent_id -> prediction
    individual_confidences: Dict[str, float] = field(default_factory=dict)
    
    # Aggregated result
    collective_prediction: float = 0.0
    collective_confidence: float = 0.0
    uncertainty: float = 0.0
    
    # Meta
    aggregation_method: str = "weighted_mean"
    
    def to_dict(self) -> Dict:
        return {
            'prediction_id': self.prediction_id,
            'target': self.target,
            'collective_value': self.collective_prediction,
            'confidence': self.collective_confidence,
            'uncertainty': self.uncertainty,
            'n_agents': len(self.individual_predictions)
        }


@dataclass
class CollectiveDecision:
    """A decision made by the collective"""
    decision_id: str
    options: List[str]
    
    # Votes
    votes: Dict[str, Dict[str, float]] = field(default_factory=dict)  # agent_id -> {option: weight}
    
    # Result
    selected_option: Optional[str] = None
    confidence: float = 0.0
    support_scores: Dict[str, float] = field(default_factory=dict)
    
    # Timing
    decided_at: Optional[datetime] = None


class AggregationMethods:
    """Various methods for aggregating individual predictions"""
    
    @staticmethod
    def mean(predictions: List[float]) -> float:
        return np.mean(predictions)
    
    @staticmethod
    def median(predictions: List[float]) -> float:
        return median(predictions)
    
    @staticmethod
    def weighted_mean(predictions: List[float], weights: List[float]) -> float:
        if sum(weights) == 0:
            return np.mean(predictions)
        return np.average(predictions, weights=weights)
    
    @staticmethod
    def trimmed_mean(predictions: List[float], trim_percent: float = 0.1) -> float:
        n = len(predictions)
        k = int(n * trim_percent)
        sorted_preds = sorted(predictions)
        trimmed = sorted_preds[k:n-k] if k > 0 else sorted_preds
        return np.mean(trimmed) if trimmed else 0.0
    
    @staticmethod
    def geometric_mean(predictions: List[float]) -> float:
        return np.exp(np.mean(np.log(predictions))) if all(p > 0 for p in predictions) else 0.0
    
    @staticmethod
    def extremized_mean(predictions: List[float], extremization: float = 1.5) -> float:
        """Extremize predictions (push towards extremes)"""
        mean_pred = np.mean(predictions)
        # Apply sigmoid transformation
        from scipy.special import expit, logit
        try:
            logit_mean = logit(mean_pred)
            extremized_logit = logit_mean * extremization
            return expit(extremized_logit)
        except:
            return mean_pred


class CollectiveIntelligence:
    """
    Collective Intelligence Engine
    
    Aggregates individual agent predictions and decisions to produce
    emergent collective intelligence that outperforms individuals.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Default aggregation method
        self.default_method = self.config.get('aggregation_method', 'weighted_mean')
        self.extremization = self.config.get('extremization', 1.5)
        
        # Agent accuracy tracking
        self.agent_accuracy: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        # agent_id -> [(prediction, actual), ...]
        
        # Predictions and decisions
        self.predictions: Dict[str, CollectivePrediction] = {}
        self.decisions: Dict[str, CollectiveDecision] = {}
        
        # History
        self.prediction_history: List[CollectivePrediction] = []
        self.decision_history: List[CollectiveDecision] = []
        
        # Statistics
        self.stats = {
            'predictions_made': 0,
            'decisions_made': 0,
            'avg_collective_error': 0.0
        }
        
        logger.info("Collective Intelligence Engine initialized")
    
    def add_prediction(
        self,
        prediction_id: str,
        target: str,
        agent_id: str,
        prediction_value: float,
        confidence: float = 0.5,
        expertise_weight: float = 1.0
    ) -> CollectivePrediction:
        """Add an individual prediction to the collective"""
        if prediction_id not in self.predictions:
            self.predictions[prediction_id] = CollectivePrediction(
                prediction_id=prediction_id,
                target=target,
                individual_predictions={},
                individual_confidences={}
            )
        
        pred = self.predictions[prediction_id]
        pred.individual_predictions[agent_id] = prediction_value
        pred.individual_confidences[agent_id] = confidence * expertise_weight
        
        return pred
    
    def aggregate_prediction(
        self,
        prediction_id: str,
        method: Optional[str] = None
    ) -> CollectivePrediction:
        """Aggregate individual predictions into collective prediction"""
        if prediction_id not in self.predictions:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        pred = self.predictions[prediction_id]
        method = method or self.default_method
        
        predictions = list(pred.individual_predictions.values())
        confidences = list(pred.individual_confidences.values())
        
        if not predictions:
            return pred
        
        # Apply aggregation
        if method == 'mean':
            collective = AggregationMethods.mean(predictions)
        elif method == 'median':
            collective = AggregationMethods.median(predictions)
        elif method == 'weighted_mean':
            collective = AggregationMethods.weighted_mean(predictions, confidences)
        elif method == 'trimmed_mean':
            collective = AggregationMethods.trimmed_mean(predictions)
        elif method == 'extremized':
            mean_pred = AggregationMethods.weighted_mean(predictions, confidences)
            collective = AggregationMethods.extremized_mean([mean_pred], self.extremization)
        else:
            collective = np.mean(predictions)
        
        pred.collective_prediction = collective
        pred.aggregation_method = method
        
        # Calculate collective confidence
        # Higher when predictions agree
        pred_range = max(predictions) - min(predictions)
        agreement = 1.0 - min(1.0, pred_range / max(1e-10, abs(collective)))
        avg_confidence = np.mean(confidences)
        pred.collective_confidence = agreement * avg_confidence
        
        # Calculate uncertainty
        pred.uncertainty = np.std(predictions)
        
        self.stats['predictions_made'] += 1
        
        return pred
    
    def record_outcome(
        self,
        prediction_id: str,
        actual_value: float
    ) -> Dict[str, float]:
        """Record actual outcome to assess accuracy"""
        if prediction_id not in self.predictions:
            return {}
        
        pred = self.predictions[prediction_id]
        
        # Calculate individual errors
        individual_errors = {}
        for agent_id, pred_value in pred.individual_predictions.items():
            error = abs(pred_value - actual_value)
            individual_errors[agent_id] = error
            
            # Update agent accuracy history
            self.agent_accuracy[agent_id].append((pred_value, actual_value))
        
        # Calculate collective error
        collective_error = abs(pred.collective_prediction - actual_value)
        
        # Compare to average individual error
        avg_individual_error = np.mean(list(individual_errors.values()))
        
        # Wisdom of crowds: collective should beat average individual
        crowd_wisdom = collective_error < avg_individual_error
        
        result = {
            'collective_error': collective_error,
            'avg_individual_error': avg_individual_error,
            'best_individual_error': min(individual_errors.values()),
            'wisdom_of_crowds_achieved': crowd_wisdom,
            'individual_errors': individual_errors
        }
        
        # Update stats
        self.stats['avg_collective_error'] = (
            0.9 * self.stats['avg_collective_error'] + 0.1 * collective_error
        )
        
        # Store in history
        self.prediction_history.append(pred)
        
        return result
    
    def get_agent_weights(self) -> Dict[str, float]:
        """Get weights for agents based on historical accuracy"""
        weights = {}
        
        for agent_id, history in self.agent_accuracy.items():
            if len(history) >= 5:
                # Calculate accuracy
                errors = [abs(pred - actual) for pred, actual in history[-20:]]
                avg_error = np.mean(errors)
                
                # Convert to weight (lower error = higher weight)
                weight = 1.0 / (1.0 + avg_error)
                weights[agent_id] = weight
            else:
                # Default weight for new agents
                weights[agent_id] = 0.5
        
        return weights
    
    def make_collective_decision(
        self,
        decision_id: str,
        options: List[str],
        votes: Dict[str, Dict[str, float]],
        require_consensus: bool = False,
        consensus_threshold: float = 0.7
    ) -> CollectiveDecision:
        """Make a decision based on collective voting"""
        decision = CollectiveDecision(
            decision_id=decision_id,
            options=options,
            votes=votes
        )
        
        # Aggregate votes
        option_scores = defaultdict(float)
        option_counts = defaultdict(int)
        
        for agent_id, agent_votes in votes.items():
            agent_weight = self.get_agent_weights().get(agent_id, 0.5)
            
            for option, vote_strength in agent_votes.items():
                option_scores[option] += vote_strength * agent_weight
                option_counts[option] += 1
        
        decision.support_scores = dict(option_scores)
        
        # Select winner
        if option_scores:
            winner = max(option_scores.items(), key=lambda x: x[1])
            decision.selected_option = winner[0]
            
            total_score = sum(option_scores.values())
            confidence = winner[1] / total_score if total_score > 0 else 0.0
            
            if require_consensus:
                # Check if winner exceeds consensus threshold
                if confidence >= consensus_threshold:
                    decision.confidence = confidence
                else:
                    decision.selected_option = None  # No consensus
                    decision.confidence = confidence
            else:
                decision.confidence = confidence
        
        decision.decided_at = datetime.utcnow()
        
        self.decisions[decision_id] = decision
        self.decision_history.append(decision)
        self.stats['decisions_made'] += 1
        
        return decision
    
    def collaborative_filtering(
        self,
        target_agent: str,
        item_pool: List[str],
        agent_preferences: Dict[str, Dict[str, float]]
    ) -> List[Tuple[str, float]]:
        """Recommend items based on similar agents' preferences"""
        if target_agent not in agent_preferences:
            return []
        
        target_prefs = agent_preferences[target_agent]
        
        # Find similar agents
        similarities = {}
        for agent_id, prefs in agent_preferences.items():
            if agent_id == target_agent:
                continue
            
            # Calculate cosine similarity
            common_items = set(target_prefs.keys()) & set(prefs.keys())
            if not common_items:
                continue
            
            target_vec = np.array([target_prefs[item] for item in common_items])
            other_vec = np.array([prefs[item] for item in common_items])
            
            similarity = np.dot(target_vec, other_vec) / (
                np.linalg.norm(target_vec) * np.linalg.norm(other_vec) + 1e-10
            )
            similarities[agent_id] = similarity
        
        # Predict preferences for unrated items
        predictions = {}
        for item in item_pool:
            if item in target_prefs:
                continue
            
            weighted_sum = 0.0
            weight_sum = 0.0
            
            for agent_id, similarity in similarities.items():
                prefs = agent_preferences[agent_id]
                if item in prefs:
                    weighted_sum += similarity * prefs[item]
                    weight_sum += abs(similarity)
            
            if weight_sum > 0:
                predictions[item] = weighted_sum / weight_sum
        
        # Sort by predicted rating
        return sorted(predictions.items(), key=lambda x: x[1], reverse=True)
    
    def get_wisdom_score(self) -> float:
        """Calculate wisdom of crowds effectiveness"""
        if not self.prediction_history:
            return 0.0
        
        recent = self.prediction_history[-50:]
        
        # Count how often collective beat average individual
        wisdom_count = 0
        for pred in recent:
            # This requires outcomes to be recorded
            # Simplified metric: variance reduction
            individual_variance = np.var(list(pred.individual_predictions.values()))
            # Collective prediction should have lower uncertainty
            wisdom_count += 1 if pred.uncertainty < individual_variance else 0
        
        return wisdom_count / len(recent) if recent else 0.0
    
    def get_diversity_index(self, prediction_id: str) -> float:
        """Calculate diversity of predictions (higher = more diverse)"""
        if prediction_id not in self.predictions:
            return 0.0
        
        pred = self.predictions[prediction_id]
        predictions = list(pred.individual_predictions.values())
        
        if len(predictions) < 2:
            return 0.0
        
        # Coefficient of variation
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        
        return std_pred / max(abs(mean_pred), 1e-10)
    
    def get_statistics(self) -> Dict:
        """Get collective intelligence statistics"""
        return {
            **self.stats,
            'wisdom_score': self.get_wisdom_score(),
            'agents_tracked': len(self.agent_accuracy),
            'total_predictions': len(self.prediction_history),
            'total_decisions': len(self.decision_history),
            'avg_diversity': np.mean([
                self.get_diversity_index(pid)
                for pid in self.predictions.keys()
            ]) if self.predictions else 0.0
        }
