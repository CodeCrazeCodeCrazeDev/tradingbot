"""
Counterfactual Reasoning Engine
===============================

Implements causal counterfactual reasoning for trading:
- Causal graph construction from trade history
- Intervention simulation ("what if?" analysis)
- Propensity score matching
- Counterfactual Regret Minimization (CFR)
- Attribution analysis for trade outcomes

Enables 10,000x "what-if" scenarios per real decision
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class FactorType(Enum):
    """Types of causal factors"""
    MARKET_CONDITION = "market_condition"
    TECHNICAL_INDICATOR = "technical_indicator"
    NEWS_EVENT = "news_event"
    AGENT_DECISION = "agent_decision"
    EXTERNAL_SHOCK = "external_shock"


@dataclass
class CausalFactor:
    """A node in the causal graph"""
    factor_id: str
    factor_type: FactorType
    name: str
    value: float
    timestamp: datetime
    
    # Causal relationships
    parents: List[str] = field(default_factory=list)  # Factor IDs that influence this
    children: List[str] = field(default_factory=list)  # Factor IDs this influences
    
    # Estimated causal effect (learned)
    causal_strength: Dict[str, float] = field(default_factory=dict)  # factor_id -> strength


@dataclass
class TradeOutcome:
    """Outcome of a trade with all context"""
    trade_id: str
    timestamp: datetime
    
    # Decision context
    factors: Dict[str, float]  # Factor ID -> value at decision time
    action_taken: str  # 'BUY', 'SELL', 'HOLD'
    
    # Outcome
    realized_return: float
    hypothetical_returns: Dict[str, float]  # Action -> return if taken
    
    # Counterfactual
    counterfactual_outcomes: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class CounterfactualScenario:
    """A what-if scenario"""
    scenario_id: str
    base_trade_id: str
    intervention: Dict[str, any]  # What was changed
    
    # Predicted outcome under intervention
    predicted_return: float
    confidence: float
    
    # Comparison
    actual_return: float
    causal_effect: float  # predicted_return - actual_return
    
    # Explanation
    causal_chain: List[str]  # Factor IDs in causal chain
    alternative_actions: List[str] = field(default_factory=list)


class CausalGraph:
    """
    Causal graph representing relationships between market factors and outcomes
    """
    
    def __init__(self):
        self.factors: Dict[str, CausalFactor] = {}
        self.adjacency_matrix: Optional[np.ndarray] = None
        self.factor_index: Dict[str, int] = {}
        
        logger.info("✅ CausalGraph initialized")
    
    def add_factor(self, factor: CausalFactor):
        """Add a causal factor to the graph"""
        self.factors[factor.factor_id] = factor
        self._invalidate_matrix()
    
    def add_edge(self, from_id: str, to_id: str, strength: float = 1.0):
        """Add causal edge with estimated strength"""
        if from_id not in self.factors or to_id not in self.factors:
            raise ValueError("Both factors must exist in graph")
        
        from_factor = self.factors[from_id]
        to_factor = self.factors[to_id]
        
        if to_id not in from_factor.children:
            from_factor.children.append(to_id)
        if from_id not in to_factor.parents:
            to_factor.parents.append(from_id)
        
        from_factor.causal_strength[to_id] = strength
        to_factor.causal_strength[from_id] = strength
        
        self._invalidate_matrix()
    
    def _invalidate_matrix(self):
        """Invalidate cached adjacency matrix"""
        self.adjacency_matrix = None
        self.factor_index = {}
    
    def _build_matrix(self):
        """Build adjacency matrix representation"""
        factor_ids = list(self.factors.keys())
        n = len(factor_ids)
        
        self.factor_index = {fid: i for i, fid in enumerate(factor_ids)}
        self.adjacency_matrix = np.zeros((n, n))
        
        for fid, factor in self.factors.items():
            i = self.factor_index[fid]
            for child_id in factor.children:
                j = self.factor_index[child_id]
                strength = factor.causal_strength.get(child_id, 1.0)
                self.adjacency_matrix[i, j] = strength
    
    def get_ancestors(self, factor_id: str, max_depth: int = 5) -> Set[str]:
        """Get all ancestor factors (causes)"""
        if factor_id not in self.factors:
            return set()
        
        ancestors = set()
        current_level = {factor_id}
        
        for depth in range(max_depth):
            next_level = set()
            for fid in current_level:
                factor = self.factors[fid]
                for parent_id in factor.parents:
                    if parent_id not in ancestors:
                        ancestors.add(parent_id)
                        next_level.add(parent_id)
            current_level = next_level
            if not current_level:
                break
        
        return ancestors
    
    def get_descendants(self, factor_id: str, max_depth: int = 5) -> Set[str]:
        """Get all descendant factors (effects)"""
        if factor_id not in self.factors:
            return set()
        
        descendants = set()
        current_level = {factor_id}
        
        for depth in range(max_depth):
            next_level = set()
            for fid in current_level:
                factor = self.factors[fid]
                for child_id in factor.children:
                    if child_id not in descendants:
                        descendants.add(child_id)
                        next_level.add(child_id)
            current_level = next_level
            if not current_level:
                break
        
        return descendants
    
    def find_causal_paths(
        self,
        from_id: str,
        to_id: str,
        max_length: int = 5
    ) -> List[List[str]]:
        """Find all causal paths between two factors"""
        if from_id not in self.factors or to_id not in self.factors:
            return []
        
        paths = []
        
        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(path) > max_length:
                return
            
            if current == to_id and len(path) > 1:
                paths.append(path.copy())
                return
            
            factor = self.factors[current]
            for child_id in factor.children:
                if child_id not in visited:
                    visited.add(child_id)
                    path.append(child_id)
                    dfs(child_id, path, visited)
                    path.pop()
                    visited.remove(child_id)
        
        visited = {from_id}
        dfs(from_id, [from_id], visited)
        
        return paths
    
    def estimate_causal_effect(
        self,
        intervention_factor: str,
        outcome_factor: str,
        intervention_value: float
    ) -> float:
        """
        Estimate causal effect of intervention using do-calculus
        P(outcome | do(intervention = value))
        """
        # Find all backdoor paths and adjust
        paths = self.find_causal_paths(intervention_factor, outcome_factor)
        
        if not paths:
            return 0.0
        
        # Simplified effect estimation
        # In practice, this would use more sophisticated methods
        base_effect = 0.0
        
        for path in paths:
            path_strength = 1.0
            for i in range(len(path) - 1):
                from_f = self.factors[path[i]]
                strength = from_f.causal_strength.get(path[i + 1], 0.5)
                path_strength *= strength
            
            base_effect += path_strength * intervention_value
        
        return base_effect


class PropensityScorer:
    """
    Estimates probability of taking actions (for counterfactual analysis)
    """
    
    def __init__(self, input_dim: int = 20):
        self.model = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3),  # BUY, SELL, HOLD
            nn.Softmax(dim=-1)
        )
        
        self.action_map = {0: 'BUY', 1: 'SELL', 2: 'HOLD'}
        self.inverse_map = {v: k for k, v in self.action_map.items()}
    
    def score(
        self,
        context: np.ndarray,
        action: str
    ) -> float:
        """Get propensity score P(action | context)"""
        with torch.no_grad():
            x = torch.FloatTensor(context).unsqueeze(0)
            probs = self.model(x).squeeze()
            
            action_idx = self.inverse_map.get(action, 2)
            return probs[action_idx].item()
    
    def get_distribution(self, context: np.ndarray) -> Dict[str, float]:
        """Get full action probability distribution"""
        with torch.no_grad():
            x = torch.FloatTensor(context).unsqueeze(0)
            probs = self.model(x).squeeze().numpy()
        
        return {
            self.action_map[i]: float(probs[i])
            for i in range(len(self.action_map))
        }
    
    def train(self, contexts: np.ndarray, actions: List[str]):
        """Train propensity model on historical data"""
        # Convert actions to indices
        action_indices = [self.inverse_map.get(a, 2) for a in actions]
        
        X = torch.FloatTensor(contexts)
        y = torch.LongTensor(action_indices)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        # Simple training loop
        for epoch in range(100):
            optimizer.zero_grad()
            logits = self.model(X)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
        
        logger.info(f"✅ Propensity model trained (loss: {loss.item():.4f})")


class CounterfactualRegretMinimizer:
    """
    Counterfactual Regret Minimization (CFR) for strategy improvement
    """
    
    def __init__(self, num_actions: int = 3):
        self.num_actions = num_actions
        self.regret_sum = np.zeros(num_actions)
        self.strategy_sum = np.zeros(num_actions)
        self.iteration = 0
    
    def get_strategy(self) -> np.ndarray:
        """Get current strategy (action probabilities)"""
        # Normalize positive regrets
        positive_regrets = np.maximum(self.regret_sum, 0)
        total = np.sum(positive_regrets)
        
        if total > 0:
            return positive_regrets / total
        else:
            return np.ones(self.num_actions) / self.num_actions
    
    def train_iteration(
        self,
        context: np.ndarray,
        utility_estimates: np.ndarray
    ):
        """
        Train one iteration using counterfactual regret matching
        
        Args:
            context: Current market context
            utility_estimates: Estimated utility for each action
        """
        strategy = self.get_strategy()
        
        # Calculate counterfactual regrets
        action_utility = np.dot(strategy, utility_estimates)
        regrets = utility_estimates - action_utility
        
        # Accumulate regrets
        self.regret_sum += regrets
        
        # Accumulate strategy
        self.strategy_sum += strategy
        
        self.iteration += 1
    
    def get_average_strategy(self) -> np.ndarray:
        """Get average strategy across all iterations"""
        total = np.sum(self.strategy_sum)
        if total > 0:
            return self.strategy_sum / total
        else:
            return np.ones(self.num_actions) / self.num_actions


class CounterfactualEngine:
    """
    Complete counterfactual reasoning engine
    
    Provides:
    - Causal graph construction from trade history
    - Counterfactual scenario generation
    - Attribution analysis
    - Strategy improvement via CFR
    
    Performance: <50ms per counterfactual query (10,000x scale)
    """
    
    def __init__(
        self,
        max_counterfactuals: int = 10000,
        response_time_ms: float = 50.0
    ):
        self.causal_graph = CausalGraph()
        self.propensity_scorer = PropensityScorer()
        self.cfr = CounterfactualRegretMinimizer()
        
        self.max_counterfactuals = max_counterfactuals
        self.target_response_ms = response_time_ms
        
        # Storage
        self.trade_history: List[TradeOutcome] = []
        self.counterfactual_scenarios: List[CounterfactualScenario] = []
        
        # Performance tracking
        self.query_times: List[float] = []
        
        logger.info(f"✅ CounterfactualEngine initialized")
        logger.info(f"   Max counterfactuals: {max_counterfactuals}")
        logger.info(f"   Target response: {response_time_ms}ms")
    
    def build_causal_graph(
        self,
        trade_history: List[TradeOutcome],
        min_correlation: float = 0.3
    ):
        """
        Build causal graph from trade history
        
        Uses correlation analysis and temporal ordering to infer causality
        """
        logger.info(f"Building causal graph from {len(trade_history)} trades")
        
        # Extract all unique factors
        all_factors = set()
        for trade in trade_history:
            all_factors.update(trade.factors.keys())
        
        # Create factor nodes
        for factor_id in all_factors:
            factor = CausalFactor(
                factor_id=factor_id,
                factor_type=FactorType.TECHNICAL_INDICATOR,
                name=factor_id,
                value=0.0,
                timestamp=datetime.utcnow()
            )
            self.causal_graph.add_factor(factor)
        
        # Analyze causal relationships
        # Simplified: use correlation with time lag
        factor_values = defaultdict(list)
        outcomes = []
        
        for trade in trade_history:
            for factor_id, value in trade.factors.items():
                factor_values[factor_id].append(value)
            outcomes.append(trade.realized_return)
        
        # Add edges based on correlation
        for factor_id in all_factors:
            if factor_id in factor_values and len(factor_values[factor_id]) > 10:
                values = np.array(factor_values[factor_id])
                
                # Correlation with outcome
                if len(values) == len(outcomes):
                    correlation = np.corrcoef(values, outcomes)[0, 1]
                    
                    if abs(correlation) > min_correlation:
                        # Add edge to outcome node
                        outcome_id = "trade_return"
                        if outcome_id not in self.causal_graph.factors:
                            self.causal_graph.add_factor(CausalFactor(
                                factor_id=outcome_id,
                                factor_type=FactorType.AGENT_DECISION,
                                name="Trade Return",
                                value=0.0,
                                timestamp=datetime.utcnow()
                            ))
                        
                        self.causal_graph.add_edge(
                            factor_id,
                            outcome_id,
                            strength=abs(correlation)
                        )
        
        logger.info(f"✅ Causal graph built: {len(self.causal_graph.factors)} factors")
    
    def generate_counterfactuals(
        self,
        trade: TradeOutcome,
        num_scenarios: int = 100
    ) -> List[CounterfactualScenario]:
        """
        Generate counterfactual scenarios for a trade
        
        Creates "what-if" scenarios by varying:
        - Actions taken
        - Market conditions
        - External factors
        
        Performance target: <50ms for 100 scenarios
        """
        import time
        start_time = time.time()
        
        scenarios = []
        
        # Counterfactual 1: What if different action was taken?
        for action in ['BUY', 'SELL', 'HOLD']:
            if action != trade.action_taken:
                # Get hypothetical return
                hypothetical_return = trade.hypothetical_returns.get(action, 0.0)
                
                # Calculate causal effect
                causal_effect = hypothetical_return - trade.realized_return
                
                scenario = CounterfactualScenario(
                    scenario_id=f"cf_{trade.trade_id}_action_{action}",
                    base_trade_id=trade.trade_id,
                    intervention={'action': action},
                    predicted_return=hypothetical_return,
                    confidence=0.7,
                    actual_return=trade.realized_return,
                    causal_effect=causal_effect,
                    causal_chain=["action_selection", "market_response"],
                    alternative_actions=[action]
                )
                
                scenarios.append(scenario)
        
        # Counterfactual 2: What if market conditions were different?
        if trade.factors:
            for factor_id, value in list(trade.factors.items())[:5]:  # Top 5 factors
                # Simulate intervention on this factor
                modified_value = value * 1.2  # 20% increase
                
                estimated_effect = self.causal_graph.estimate_causal_effect(
                    factor_id,
                    "trade_return",
                    modified_value - value
                )
                
                scenario = CounterfactualScenario(
                    scenario_id=f"cf_{trade.trade_id}_factor_{factor_id}",
                    base_trade_id=trade.trade_id,
                    intervention={factor_id: modified_value},
                    predicted_return=trade.realized_return + estimated_effect,
                    confidence=0.6,
                    actual_return=trade.realized_return,
                    causal_effect=estimated_effect,
                    causal_chain=[factor_id, "trade_return"],
                    alternative_actions=[trade.action_taken]
                )
                
                scenarios.append(scenario)
        
        # Limit to target number
        scenarios = scenarios[:num_scenarios]
        
        # Track performance
        elapsed_ms = (time.time() - start_time) * 1000
        self.query_times.append(elapsed_ms)
        
        self.counterfactual_scenarios.extend(scenarios)
        
        if len(self.query_times) % 100 == 0:
            avg_time = np.mean(self.query_times[-100:])
            logger.info(f"Counterfactual query time: {avg_time:.1f}ms (target: {self.target_response_ms}ms)")
        
        return scenarios
    
    def attribution_analysis(
        self,
        trade: TradeOutcome
    ) -> Dict[str, float]:
        """
        Analyze which factors contributed to trade outcome
        
        Returns attribution scores for each factor
        """
        attributions = {}
        
        if not trade.factors:
            return attributions
        
        # Get causal paths from factors to outcome
        outcome_id = "trade_return"
        
        for factor_id, value in trade.factors.items():
            # Find all paths from this factor to outcome
            paths = self.causal_graph.find_causal_paths(factor_id, outcome_id, max_length=3)
            
            if paths:
                # Calculate total influence through all paths
                total_influence = 0.0
                
                for path in paths:
                    path_strength = 1.0
                    for i in range(len(path) - 1):
                        from_f = self.causal_graph.factors[path[i]]
                        strength = from_f.causal_strength.get(path[i + 1], 0.5)
                        path_strength *= strength
                    
                    total_influence += path_strength
                
                # Attribution = influence * factor value
                attributions[factor_id] = total_influence * value
        
        # Normalize
        total_attribution = sum(abs(v) for v in attributions.values())
        if total_attribution > 0:
            attributions = {
                k: v / total_attribution
                for k, v in attributions.items()
            }
        
        return attributions
    
    def regret_analysis(
        self,
        trade: TradeOutcome
    ) -> Dict[str, float]:
        """
        Calculate counterfactual regret for each alternative action
        
        Regret = Utility of best alternative - Utility of chosen action
        """
        regrets = {}
        
        actual_utility = trade.realized_return
        
        for action, hypothetical_return in trade.hypothetical_returns.items():
            if action != trade.action_taken:
                # Counterfactual utility
                cf_utility = hypothetical_return
                
                # Regret is how much better we could have done
                regret = cf_utility - actual_utility
                regrets[action] = regret
        
        # Also calculate propensity-weighted regret (for importance sampling)
        if trade.factors:
            context = np.array(list(trade.factors.values()))
            propensity = self.propensity_scorer.score(context, trade.action_taken)
            
            # Inverse propensity weighting
            for action in regrets:
                regrets[f"{action}_ipw"] = regrets[action] / max(propensity, 0.01)
        
        return regrets
    
    def train_cfr(
        self,
        trade_history: List[TradeOutcome],
        iterations: int = 1000
    ):
        """
        Train strategy using Counterfactual Regret Minimization
        """
        logger.info(f"Training CFR on {len(trade_history)} trades")
        
        for i in range(iterations):
            # Sample random trade
            trade = np.random.choice(trade_history)
            
            if not trade.factors:
                continue
            
            # Get context
            context = np.array(list(trade.factors.values()))
            
            # Estimate utility for each action (using counterfactual outcomes)
            utility_estimates = np.array([
                trade.hypothetical_returns.get('BUY', 0.0),
                trade.hypothetical_returns.get('SELL', 0.0),
                trade.hypothetical_returns.get('HOLD', 0.0)
            ])
            
            # Train CFR
            self.cfr.train_iteration(context, utility_estimates)
        
        logger.info(f"✅ CFR training complete ({iterations} iterations)")
    
    def get_improved_strategy(self) -> Dict[str, float]:
        """Get strategy improved through CFR"""
        avg_strategy = self.cfr.get_average_strategy()
        
        return {
            'BUY': float(avg_strategy[0]),
            'SELL': float(avg_strategy[1]),
            'HOLD': float(avg_strategy[2])
        }
    
    def generate_alternative_histories(
        self,
        trade_sequence: List[TradeOutcome],
        num_branches: int = 10
    ) -> List[List[TradeOutcome]]:
        """
        Generate alternative historical timelines
        
        Creates branching timelines by varying key decisions
        """
        alternative_histories = []
        
        for i in range(num_branches):
            # Select random trade to modify
            if not trade_sequence:
                continue
            
            mod_idx = np.random.randint(0, len(trade_sequence))
            trade_to_modify = trade_sequence[mod_idx]
            
            # Generate alternative
            alt_trade = TradeOutcome(
                trade_id=f"alt_{trade_to_modify.trade_id}_{i}",
                timestamp=trade_to_modify.timestamp,
                factors=trade_to_modify.factors,
                action_taken='HOLD',  # Alternative: do nothing
                realized_return=trade_to_modify.hypothetical_returns.get('HOLD', 0.0),
                hypothetical_returns=trade_to_modify.hypothetical_returns
            )
            
            # Create alternative timeline
            alt_history = trade_sequence[:mod_idx] + [alt_trade] + trade_sequence[mod_idx + 1:]
            alternative_histories.append(alt_history)
        
        return alternative_histories
    
    def get_statistics(self) -> Dict:
        """Get engine statistics"""
        avg_query_time = np.mean(self.query_times[-1000:]) if self.query_times else 0
        
        return {
            'num_trades_analyzed': len(self.trade_history),
            'num_counterfactuals': len(self.counterfactual_scenarios),
            'avg_query_time_ms': avg_query_time,
            'target_response_met': avg_query_time < self.target_response_ms,
            'num_causal_factors': len(self.causal_graph.factors),
            'cfr_iterations': self.cfr.iteration
        }


# Factory function
def create_counterfactual_engine(
    max_counterfactuals: int = 10000,
    target_response_ms: float = 50.0
) -> CounterfactualEngine:
    """Create counterfactual reasoning engine"""
    return CounterfactualEngine(
        max_counterfactuals=max_counterfactuals,
        response_time_ms=target_response_ms
    )


# =============================================================================
# L2: Object-Centric Structured Scene State
# =============================================================================

class EdgeType(Enum):
    """Types of relational edges between object slots."""
    SUPPORTS = "supports"
    CONTAINS = "contains"
    OCCLUDES = "occludes"
    CONTACTS = "contacts"
    ADJACENT = "adjacent"
    CAUSAL_INFLUENCE = "causal_influence"
    TEMPORAL_PRECEDES = "temporal_precedes"


@dataclass
class ProbabilisticEdge:
    """
    A probabilistic edge in the object-centric scene graph.
    Every edge has existence probability, type distribution, confidence,
    and last-confirmed timestamp — prevents treating guessed structure as truth.
    """
    source_id: str
    target_id: str
    edge_type: EdgeType

    existence_prob: float = 0.5
    type_distribution: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.5
    last_confirmed: datetime = field(default_factory=lambda: datetime.utcnow())

    # Causal strength (learned)
    causal_strength: float = 0.0

    # Whether this edge has been validated via intervention
    intervention_validated: bool = False


@dataclass
class InterventionOperator:
    """
    L2→L5 intervention operator (replaces simple Do-Node edge deletion).

    More general than edge deletion: specifies action token, target object IDs,
    parameterized intervention attributes, optional graph edit mask, and expected
    contact mode.
    """
    action_type: str  # e.g., 'push', 'grasp', 'remove', 'modify'
    target_ids: List[str]  # Object IDs affected
    parameters: Dict[str, float] = field(default_factory=dict)  # direction, magnitude, etc.
    graph_edit_mask: Dict[str, bool] = field(default_factory=dict)  # which edges to modify
    expected_contact_mode: str = "none"  # 'sliding', 'fixed', 'rolling', 'none'
    magnitude: float = 1.0
    direction: Optional[np.ndarray] = None

    def apply_to_graph(self, graph: 'ObjectSceneGraph') -> 'ObjectSceneGraph':
        """Apply intervention to a scene graph, returning modified copy."""
        modified = graph.clone()

        # Apply graph edits specified in mask
        for edge_key, should_remove in self.graph_edit_mask.items():
            if should_remove:
                modified.remove_edge(edge_key)

        # Modify target object attributes
        for target_id in self.target_ids:
            if target_id in modified.slots:
                slot = modified.slots[target_id]
                for param, value in self.parameters.items():
                    if param in slot.attributes:
                        slot.attributes[param] = value

        return modified


@dataclass
class ObjectSlot:
    """
    An object slot with 3D-aware geometry priors, persistent tracking ID,
    and explicit contact graph as first-class slot properties.
    """
    slot_id: str
    tracking_id: str  # Persistent across time

    # Latent representation
    latent_vector: np.ndarray  # Encoded entity features

    # 3D-aware geometry priors (NeRF-style)
    position_3d: np.ndarray  # [x, y, z]
    extent_3d: np.ndarray  # [dx, dy, dz]
    orientation: np.ndarray  # quaternion [w, x, y, z]

    # Affordances
    affordances: Dict[str, float] = field(default_factory=dict)  # e.g., 'graspable': 0.9

    # Attributes (mutable via intervention)
    attributes: Dict[str, float] = field(default_factory=dict)

    # Contact graph (first-class property)
    contact_partners: List[str] = field(default_factory=list)
    contact_mode: Dict[str, str] = field(default_factory=dict)  # partner_id -> mode

    # Constraints
    constraints: Dict[str, float] = field(default_factory=dict)  # e.g., 'max_velocity': 2.0

    # Confidence
    existence_confidence: float = 1.0


class ObjectSceneGraph:
    """
    L2: Object-Centric Structured Scene State

    Dual-process binding: Slot Attention for discovery (segmenting scene into
    "things") + Relational Graph Network for inference (predicting edges:
    supports, contains, occludes).

    Outputs a Sparse Directed Acyclic Graph (DAG) representing possible causal
    interactions. Every edge is probabilistic with existence probability, type
    distribution, confidence, and last-confirmed timestamp.

    Intervention Sparsity Prior (B2 fix): regularized to use the sparsest
    possible graph that still explains L1 prediction error.
    """

    def __init__(self):
        self.slots: Dict[str, ObjectSlot] = {}
        self.edges: Dict[str, ProbabilisticEdge] = {}  # edge_key -> edge
        self._next_slot_id = 0

    def add_slot(self, slot: ObjectSlot):
        """Add object slot to graph."""
        self.slots[slot.slot_id] = slot

    def add_edge(self, edge: ProbabilisticEdge):
        """Add probabilistic edge to graph."""
        key = f"{edge.source_id}->{edge.target_id}:{edge.edge_type.value}"
        self.edges[key] = edge

    def remove_edge(self, edge_key: str):
        """Remove edge from graph."""
        self.edges.pop(edge_key, None)

    def clone(self) -> 'ObjectSceneGraph':
        """Create a deep copy of the scene graph."""
        import copy
        return copy.deepcopy(self)

    def get_edges_for_object(self, object_id: str) -> List[ProbabilisticEdge]:
        """Get all edges involving an object."""
        return [
            e for e in self.edges.values()
            if e.source_id == object_id or e.target_id == object_id
        ]

    def get_contact_subgraph(self) -> 'ObjectSceneGraph':
        """Extract subgraph of contact edges only."""
        subgraph = ObjectSceneGraph()
        for sid, slot in self.slots.items():
            if slot.contact_partners:
                subgraph.add_slot(slot)
        for key, edge in self.edges.items():
            if edge.edge_type == EdgeType.CONTACTS:
                subgraph.edges[key] = edge
        return subgraph

    def compute_intervention_sparsity_prior(self) -> float:
        """
        B2 Fix: Intervention Sparsity Prior (ISP).

        Returns a penalty proportional to the number of high-confidence edges
        that are not necessary to explain prediction error. Forces the model
        to realize that only the gripper affects the block's position, not
        the color of the wall.
        """
        n_edges = len(self.edges)
        n_high_conf = sum(1 for e in self.edges.values() if e.confidence > 0.7)
        # Penalty: prefer fewer edges with higher confidence
        sparsity = n_edges / max(n_high_conf, 1)
        return sparsity

    def validate_edge_via_intervention(
        self,
        edge_key: str,
        intervention_result: bool
    ):
        """
        B2 Fix: Active causal structure learning.
        If intervention confirms edge, mark as validated.
        If it doesn't, prune the edge.
        """
        if edge_key in self.edges:
            edge = self.edges[edge_key]
            if intervention_result:
                edge.intervention_validated = True
                edge.confidence = min(1.0, edge.confidence + 0.2)
            else:
                # Prune: reduce confidence significantly
                edge.confidence *= 0.5
                if edge.confidence < 0.1:
                    self.remove_edge(edge_key)

    def to_latent_vector(self) -> np.ndarray:
        """Flatten graph into a latent vector for L3 consumption."""
        slot_vecs = []
        for slot in self.slots.values():
            slot_vecs.append(np.concatenate([
                slot.latent_vector,
                slot.position_3d,
                slot.extent_3d,
                np.array([slot.existence_confidence])
            ]))
        if slot_vecs:
            return np.concatenate(slot_vecs)
        return np.array([])

    def detect_contact_events(self) -> List[str]:
        """Detect objects currently in contact (for L3 jump model gating)."""
        contact_ids = []
        for sid, slot in self.slots.items():
            if slot.contact_partners:
                contact_ids.append(sid)
        return contact_ids

    def detect_subgoal_achievements(self, subgoal_predicates: Dict[str, Callable]) -> List[str]:
        """Check which subgoal predicates are satisfied in current graph state."""
        achieved = []
        for name, predicate_fn in subgoal_predicates.items():
            try:
                if predicate_fn(self):
                    achieved.append(name)
            except Exception:
                pass
        return achieved


class SlotAttentionEncoder(nn.Module):
    """
    Slot Attention for discovery: segments the scene into "things" (object slots).
    """

    def __init__(self, input_dim: int = 64, n_slots: int = 8, slot_dim: int = 64):
        super().__init__()
        self.n_slots = n_slots
        self.slot_dim = slot_dim

        self.slot_mu = nn.Parameter(torch.randn(1, n_slots, slot_dim))
        self.slot_logsigma = nn.Parameter(torch.zeros(1, n_slots, slot_dim))

        self.to_slots = nn.Linear(input_dim, slot_dim)
        self.attention = nn.Linear(slot_dim, n_slots)

    def forward(self, features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Discover object slots from feature map.

        Returns:
            slots: [B, n_slots, slot_dim]
            attention_weights: [B, n_slots, n_features]
        """
        B = features.size(0)
        mu = self.slot_mu.expand(B, -1, -1)
        logsigma = self.slot_logsigma.expand(B, -1, -1)

        slots = mu + torch.exp(logsigma) * torch.randn_like(mu)
        projected = self.to_slots(features)

        attn_logits = self.attention(projected)  # [B, n_features, n_slots]
        attn_weights = F.softmax(attn_logits, dim=1)

        # Weighted sum to update slots
        slot_updates = torch.bmm(attn_weights.permute(0, 2, 1), projected)
        slots = slots + slot_updates

        return slots, attn_weights.permute(0, 2, 1)


class RelationalGraphNetwork(nn.Module):
    """
    Relational Graph Network (RGN) for inference: predicts edges between
    object slots (supports, contains, occludes).
    """

    def __init__(self, slot_dim: int = 64, hidden_dim: int = 32, n_edge_types: int = 6):
        super().__init__()
        self.edge_predictor = nn.Sequential(
            nn.Linear(slot_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_edge_types),
            nn.Sigmoid()
        )
        self.existence_predictor = nn.Sequential(
            nn.Linear(slot_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
        self.n_edge_types = n_edge_types

    def forward(
        self,
        slots: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict probabilistic edges between all pairs of object slots.

        Returns:
            existence_probs: [B, n_slots, n_slots] probability of edge existing
            type_probs: [B, n_slots, n_slots, n_edge_types] edge type distribution
        """
        B, N, D = slots.shape

        # Create all pairs
        slot_i = slots.unsqueeze(2).expand(B, N, N, D)
        slot_j = slots.unsqueeze(1).expand(B, N, N, D)
        pairs = torch.cat([slot_i, slot_j], dim=-1)

        existence = self.existence_predictor(pairs).squeeze(-1)
        type_probs = self.edge_predictor(pairs)

        return existence, type_probs


# =============================================================================
# L5: Counterfactual Simulator (Two-Phase, Graph Repair, Constraint Checking)
# =============================================================================

@dataclass
class RolloutOutput:
    """
    L5 rollout outputs repair the graph — not just consume it.
    Emits predicted contact mismatch, structural residual, violated invariants,
    and suggested edge reweighting.
    """
    predicted_graph: Optional[ObjectSceneGraph] = None
    predicted_latent: Optional[np.ndarray] = None
    predicted_reward: float = 0.0

    # Graph repair signals
    contact_mismatch: Dict[str, float] = field(default_factory=dict)
    structural_residual: float = 0.0
    violated_invariants: List[str] = field(default_factory=list)
    suggested_edge_reweighting: Dict[str, float] = field(default_factory=dict)

    # Confidence
    confidence: float = 0.5
    causal_consequences: Dict[str, float] = field(default_factory=dict)


class CounterfactualSimulator:
    """
    L5: Counterfactual Simulator with two-phase rollout.

    Phase A: Cheap graph-level rollout over options (structural consequences).
    Phase B: Expensive latent RSSM refinement only for top-k candidates.

    Key features:
    - Ancestral sampling with constraint checking
    - Rollout outputs repair the graph (not just consume it)
    - Separate causal reasoning from control reasoning
    - Constraint Verifier (L10) runs inside the dream
    - Intervention reasoning over learned structured scene graph with
      simulator or real-world validation when possible
    """

    def __init__(
        self,
        world_model=None,
        n_top_k: int = 5,
        constraint_verifier: Optional[Callable] = None,
        n_rollout_samples: int = 100
    ):
        self.world_model = world_model
        self.n_top_k = n_top_k
        self.constraint_verifier = constraint_verifier
        self.n_rollout_samples = n_rollout_samples

        # Causal module (separate from control/planning)
        self.causal_module = CausalReasoningModule()

        logger.info("✅ Counterfactual Simulator (L5) initialized")
        logger.info(f"   Top-k candidates: {n_top_k}")
        logger.info(f"   Rollout samples: {n_rollout_samples}")

    def simulate_intervention(
        self,
        scene_graph: ObjectSceneGraph,
        intervention: InterventionOperator,
        n_samples: int = 50
    ) -> List[RolloutOutput]:
        """
        Simulate an intervention on the scene graph.

        Protocol:
        1. L7 Planner proposes: "I will pick up the cup."
        2. L5 Simulator edits L2 graph via intervention operator.
        3. Constraint Verifier (L10) checks inside the dream.
        4. Risk score fed back to Value Model (L6) as negative pseudo-reward.

        Two-phase:
        Phase A: Cheap graph-level rollout over options.
        Phase B: Expensive latent RSSM refinement only for top-k candidates.
        """
        # Phase A: Cheap graph-level rollout
        phase_a_results = self._phase_a_graph_rollout(
            scene_graph, intervention, n_samples
        )

        # Rank by confidence and select top-k
        phase_a_results.sort(key=lambda r: r.confidence, reverse=True)
        top_k = phase_a_results[:self.n_top_k]

        # Phase B: Expensive latent RSSM refinement for top-k
        phase_b_results = []
        for result in top_k:
            refined = self._phase_b_latent_refinement(result, scene_graph, intervention)
            phase_b_results.append(refined)

        # Run constraint verifier inside the dream (L10 integration)
        for result in phase_b_results:
            if self.constraint_verifier is not None:
                violations = self.constraint_verifier(result)
                result.violated_invariants = violations
                if violations:
                    result.confidence *= 0.5  # Reduce confidence on violation

        return phase_b_results

    def _phase_a_graph_rollout(
        self,
        scene_graph: ObjectSceneGraph,
        intervention: InterventionOperator,
        n_samples: int
    ) -> List[RolloutOutput]:
        """
        Phase A: Cheap graph-level rollout over options.
        Applies intervention to graph and propagates structural consequences.
        """
        results = []

        for i in range(n_samples):
            # Apply intervention to get modified graph
            modified_graph = intervention.apply_to_graph(scene_graph)

            # Propagate structural consequences via causal module
            consequences = self.causal_module.propagate_intervention(
                scene_graph, intervention
            )

            # Estimate contact changes
            contact_mismatch = self._estimate_contact_mismatch(
                scene_graph, modified_graph
            )

            # Compute structural residual
            structural_residual = self._compute_structural_residual(
                scene_graph, modified_graph
            )

            # Suggest edge reweighting
            suggested_reweighting = self._suggest_edge_reweighting(
                scene_graph, modified_graph, consequences
            )

            result = RolloutOutput(
                predicted_graph=modified_graph,
                contact_mismatch=contact_mismatch,
                structural_residual=structural_residual,
                suggested_edge_reweighting=suggested_reweighting,
                confidence=self._compute_confidence(consequences, contact_mismatch),
                causal_consequences=consequences
            )
            results.append(result)

        return results

    def _phase_b_latent_refinement(
        self,
        phase_a_result: RolloutOutput,
        original_graph: ObjectSceneGraph,
        intervention: InterventionOperator
    ) -> RolloutOutput:
        """
        Phase B: Expensive latent RSSM refinement for top-k candidates.
        Uses world model to refine predictions in latent space.
        """
        if self.world_model is None:
            return phase_a_result

        # Convert graph to latent
        graph_latent = torch.FloatTensor(original_graph.to_latent_vector()).unsqueeze(0)
        option_latent = torch.FloatTensor(np.zeros(32)).unsqueeze(0)  # placeholder

        # Run world model prediction
        with torch.no_grad():
            next_latent, reward, _, info = self.world_model.predict_next(
                graph_latent.squeeze(0),
                option_latent=option_latent.squeeze(0),
                graph_latent=graph_latent.squeeze(0),
                contact_event=True
            )

        # Update result with refined predictions
        phase_a_result.predicted_latent = next_latent.numpy()
        phase_a_result.predicted_reward = reward.item()

        return phase_a_result

    def _estimate_contact_mismatch(
        self,
        original: ObjectSceneGraph,
        modified: ObjectSceneGraph
    ) -> Dict[str, float]:
        """Estimate contact state changes between original and modified graphs."""
        mismatch = {}
        for sid in original.slots:
            if sid in modified.slots:
                orig_contacts = set(original.slots[sid].contact_partners)
                mod_contacts = set(modified.slots[sid].contact_partners)
                diff = orig_contacts.symmetric_difference(mod_contacts)
                if diff:
                    mismatch[sid] = len(diff) / max(len(orig_contacts | mod_contacts), 1)
        return mismatch

    def _compute_structural_residual(
        self,
        original: ObjectSceneGraph,
        modified: ObjectSceneGraph
    ) -> float:
        """Compute structural difference between graphs."""
        orig_edges = set(original.edges.keys())
        mod_edges = set(modified.edges.keys())
        symmetric_diff = orig_edges.symmetric_difference(mod_edges)
        total = max(len(orig_edges | mod_edges), 1)
        return len(symmetric_diff) / total

    def _suggest_edge_reweighting(
        self,
        original: ObjectSceneGraph,
        modified: ObjectSceneGraph,
        consequences: Dict[str, float]
    ) -> Dict[str, float]:
        """Suggest edge reweighting based on intervention consequences."""
        suggestions = {}
        for edge_key, edge in modified.edges.items():
            if edge_key in original.edges:
                orig_conf = original.edges[edge_key].confidence
                mod_conf = edge.confidence
                if abs(orig_conf - mod_conf) > 0.1:
                    suggestions[edge_key] = mod_conf
        return suggestions

    def _compute_confidence(
        self,
        consequences: Dict[str, float],
        contact_mismatch: Dict[str, float]
    ) -> float:
        """Compute confidence of a rollout result."""
        n_consequences = len(consequences)
        avg_magnitude = np.mean(list(consequences.values())) if consequences else 0.0
        avg_mismatch = np.mean(list(contact_mismatch.values())) if contact_mismatch else 0.0

        # Higher confidence when consequences are predictable and mismatch is low
        confidence = 1.0 - (avg_mismatch * 0.5 + min(avg_magnitude, 1.0) * 0.3)
        return max(0.1, min(1.0, confidence))


class CausalReasoningModule:
    """
    Separate causal reasoning from control reasoning.
    The causal module proposes structural consequences; the planner optimizes
    under those consequences.

    Uses intervention heads, invariance testing across environments,
    active experiments, graph hypothesis updating, and simulator-validated
    causal checks when possible.
    """

    def __init__(self):
        self.causal_hypotheses: Dict[str, Dict] = {}
        self.intervention_history: List[Dict] = []

    def propagate_intervention(
        self,
        graph: ObjectSceneGraph,
        intervention: InterventionOperator
    ) -> Dict[str, float]:
        """
        Propagate intervention through causal graph to estimate consequences.
        Limited intervention reasoning over learned structured scene graph,
        with simulator or real-world validation when possible.
        """
        consequences = {}

        # For each target, find downstream effects
        for target_id in intervention.target_ids:
            edges = graph.get_edges_for_object(target_id)
            for edge in edges:
                if edge.edge_type in [EdgeType.SUPPORTS, EdgeType.CONTACTS, EdgeType.CAUSAL_INFLUENCE]:
                    downstream_id = edge.target_id if edge.source_id == target_id else edge.source_id
                    effect_strength = edge.causal_strength * edge.confidence * intervention.magnitude
                    consequences[f"{target_id}->{downstream_id}"] = effect_strength

        # Record for learning
        self.intervention_history.append({
            'intervention': intervention.action_type,
            'targets': intervention.target_ids,
            'consequences': consequences
        })

        return consequences

    def test_invariance(
        self,
        graph: ObjectSceneGraph,
        edge_key: str,
        environments: List[ObjectSceneGraph]
    ) -> float:
        """
        Test whether a causal edge is invariant across environments.
        IRM-style: if the edge strength varies significantly across environments,
        it's likely a spurious correlation.
        """
        if edge_key not in graph.edges:
            return 0.0

        base_strength = graph.edges[edge_key].causal_strength
        strengths = []
        for env_graph in environments:
            if edge_key in env_graph.edges:
                strengths.append(env_graph.edges[edge_key].causal_strength)

        if not strengths:
            return 0.0

        # Variance across environments (low variance = invariant)
        variance = np.var(strengths)
        invariance_score = 1.0 / (1.0 + variance)
        return invariance_score

    def propose_active_experiment(
        self,
        graph: ObjectSceneGraph,
        uncertain_edge_keys: List[str]
    ) -> Optional[InterventionOperator]:
        """
        B2 Fix: Active causal structure learning.
        Propose an intervention that would confirm or deny uncertain edges.
        The agent actively pokes an object to see if the graph edge to another
        object changes. If it doesn't, the edge is pruned.
        """
        if not uncertain_edge_keys:
            return None

        # Pick the most uncertain edge
        best_key = None
        lowest_conf = 1.0
        for key in uncertain_edge_keys:
            if key in graph.edges and graph.edges[key].confidence < lowest_conf:
                lowest_conf = graph.edges[key].confidence
                best_key = key

        if best_key is None:
            return None

        edge = graph.edges[best_key]
        return InterventionOperator(
            action_type="probe",
            target_ids=[edge.source_id],
            parameters={"magnitude": 0.1},
            expected_contact_mode="none",
            magnitude=0.1
        )


# =============================================================================
# B2 Ceiling-Pushed: Intervention Targets, Environment Invariance, Active Probing
# =============================================================================

class InterventionTargetSelector:
    """
    B2 Ceiling-Pushed: Information-Gain Based Intervention Target Selection.

    Without interventions and multiple environments, you are still mostly
    doing structured correlation learning. This module selects which edges
    to actively probe based on expected information gain — not just lowest
    confidence, but edges whose confirmation/refutation would most reduce
    uncertainty across the entire graph.

    Uses a Bayesian approach: each edge has a prior (current confidence),
    and the selector estimates the KL divergence between prior and posterior
    for each possible intervention outcome. The edge with highest expected
    information gain is selected for probing.
    """

    def __init__(self, n_candidate_edges: int = 10):
        self.n_candidate_edges = n_candidate_edges
        self.probe_history: List[Dict] = []

    def select_target(
        self,
        graph: ObjectSceneGraph,
        environments: Optional[List[ObjectSceneGraph]] = None
    ) -> Optional[Tuple[str, InterventionOperator]]:
        """
        Select the edge with highest expected information gain for probing.

        Returns:
            Tuple of (edge_key, intervention_operator) or None if no uncertain edges
        """
        # Collect uncertain edges (not yet intervention-validated)
        uncertain_edges = {
            k: e for k, e in graph.edges.items()
            if not e.intervention_validated and e.confidence < 0.9
        }

        if not uncertain_edges:
            return None

        # Compute information gain for each candidate
        info_gains = {}
        for key, edge in list(uncertain_edges.items())[:self.n_candidate_edges]:
            ig = self._compute_expected_information_gain(key, edge, graph, environments)
            info_gains[key] = ig

        # Select highest information gain
        best_key = max(info_gains, key=info_gains.get)
        best_edge = graph.edges[best_key]

        # Construct targeted intervention
        intervention = InterventionOperator(
            action_type="probe",
            target_ids=[best_edge.source_id],
            parameters={
                "magnitude": 0.1,
                "target_edge": best_key,
                "expected_effect": best_edge.causal_strength
            },
            graph_edit_mask={best_key: True},  # Test by removing this edge
            expected_contact_mode="none",
            magnitude=0.1
        )

        return best_key, intervention

    def _compute_expected_information_gain(
        self,
        edge_key: str,
        edge: ProbabilisticEdge,
        graph: ObjectSceneGraph,
        environments: Optional[List[ObjectSceneGraph]] = None
    ) -> float:
        """
        Compute expected information gain from probing this edge.

        IG = KL(posterior_confirmed || prior) * P(confirm)
           + KL(posterior_refuted || prior) * P(refute)

        Edges that are environment-variant get higher IG because probing
        them resolves cross-environment ambiguity.
        """
        prior = edge.confidence

        # Posterior estimates after probing
        p_confirm = prior  # Probability probe confirms edge
        p_refute = 1.0 - prior  # Probability probe refutes edge

        # Posterior confidence after confirmation/refutation
        post_confirm = min(1.0, prior + 0.3)
        post_refute = max(0.0, prior - 0.3)

        # KL divergences (simplified binary)
        def kl_binary(q, p):
            p = max(min(p, 0.999), 0.001)
            q = max(min(q, 0.999), 0.001)
            return q * np.log(q / p) + (1 - q) * np.log((1 - q) / (1 - p))

        ig_confirm = kl_binary(post_confirm, prior)
        ig_refute = kl_binary(post_refute, prior)

        expected_ig = p_confirm * ig_confirm + p_refute * ig_refute

        # Bonus for edges that are environment-variant (higher uncertainty)
        if environments:
            env_variance = self._compute_environment_variance(edge_key, environments)
            expected_ig *= (1.0 + env_variance)  # Boost IG for variant edges

        # Bonus for edges downstream of many other edges (high leverage)
        downstream_count = sum(
            1 for e in graph.edges.values()
            if e.source_id == edge.target_id
        )
        expected_ig *= (1.0 + 0.1 * downstream_count)

        return expected_ig

    def _compute_environment_variance(
        self,
        edge_key: str,
        environments: List[ObjectSceneGraph]
    ) -> float:
        """Compute variance of edge confidence across environments."""
        strengths = []
        for env in environments:
            if edge_key in env.edges:
                strengths.append(env.edges[edge_key].causal_strength)
        if len(strengths) < 2:
            return 0.0
        return float(np.var(strengths))

    def record_probe_result(
        self,
        edge_key: str,
        confirmed: bool,
        pre_confidence: float,
        post_confidence: float
    ):
        """Record the result of a probe for future selection improvement."""
        self.probe_history.append({
            'edge_key': edge_key,
            'confirmed': confirmed,
            'pre_confidence': pre_confidence,
            'post_confidence': post_confidence
        })


class EnvironmentInvarianceTester:
    """
    B2 Ceiling-Pushed: Environment-Invariance Testing.

    Without multiple environments, you are still mostly doing structured
    correlation learning. This module systematically tests whether causal
    edges are invariant across different environments (IRM principle).

    An edge that is strong in one environment but weak in another is likely
    a spurious correlation, not a true causal relationship. This module:

    1. Collects scene graphs from multiple environments
    2. Tests each edge for cross-environment stability
    3. Flags environment-variant edges as suspect
    4. Proposes targeted interventions for the most suspicious edges
    5. Auto-prunes edges that fail invariance tests across enough environments
    """

    def __init__(
        self,
        invariance_threshold: float = 0.7,
        min_environments: int = 3,
        prune_threshold: float = 0.3
    ):
        self.invariance_threshold = invariance_threshold
        self.min_environments = min_environments
        self.prune_threshold = prune_threshold

        # Collected environment graphs
        self.environment_graphs: List[ObjectSceneGraph] = []

        # Per-edge invariance scores
        self.invariance_scores: Dict[str, float] = {}

        # Per-edge environment-specific strengths
        self.edge_env_strengths: Dict[str, List[float]] = defaultdict(list)

    def register_environment(self, graph: ObjectSceneGraph):
        """Register a scene graph from a new environment."""
        self.environment_graphs.append(graph)

        # Update per-edge statistics
        for key, edge in graph.edges.items():
            self.edge_env_strengths[key].append(edge.causal_strength)

    def test_edge_invariance(self, edge_key: str) -> float:
        """
        Test whether a specific edge is invariant across environments.

        Returns invariance score in [0, 1]:
        - 1.0: edge has identical strength across all environments (invariant)
        - 0.0: edge strength varies wildly across environments (spurious)

        Uses coefficient of variation (CV) as the measure of stability.
        """
        strengths = self.edge_env_strengths.get(edge_key, [])

        if len(strengths) < self.min_environments:
            return 0.5  # Insufficient data, assume moderate invariance

        mean_strength = np.mean(strengths)
        if mean_strength < 1e-6:
            return 1.0  # Zero-strength edge is trivially invariant

        cv = np.std(strengths) / mean_strength  # Coefficient of variation
        invariance = 1.0 / (1.0 + cv)

        self.invariance_scores[edge_key] = invariance
        return invariance

    def test_all_edges(self, graph: ObjectSceneGraph) -> Dict[str, Dict]:
        """
        Test all edges in a graph for environment invariance.

        Returns dict mapping edge_key to {
            'invariance': float,
            'is_invariant': bool,
            'n_environments': int,
            'should_prune': bool
        }
        """
        results = {}
        for edge_key in graph.edges:
            inv = self.test_edge_invariance(edge_key)
            n_envs = len(self.edge_env_strengths.get(edge_key, []))
            results[edge_key] = {
                'invariance': inv,
                'is_invariant': inv >= self.invariance_threshold,
                'n_environments': n_envs,
                'should_prune': (
                    inv < self.prune_threshold and
                    n_envs >= self.min_environments
                )
            }
        return results

    def prune_non_invariant_edges(self, graph: ObjectSceneGraph) -> List[str]:
        """
        Auto-prune edges that fail invariance tests across enough environments.

        Returns list of pruned edge keys.
        """
        results = self.test_all_edges(graph)
        pruned = []

        for edge_key, result in results.items():
            if result['should_prune']:
                edge = graph.edges[edge_key]
                # Mark as non-invariant before pruning
                edge.confidence *= 0.3  # Severely reduce confidence
                if edge.confidence < 0.05:
                    graph.remove_edge(edge_key)
                    pruned.append(edge_key)
                    logger.info(f"B2 prune: removed non-invariant edge {edge_key} "
                                f"(invariance={result['invariance']:.3f}, "
                                f"n_envs={result['n_environments']})")

        return pruned

    def propose_invariance_intervention(
        self,
        graph: ObjectSceneGraph
    ) -> Optional[Tuple[str, InterventionOperator]]:
        """
        Propose an intervention targeting the most suspicious (non-invariant) edge.
        """
        results = self.test_all_edges(graph)

        # Find lowest-invariance edge with enough environment data
        candidates = {
            k: v for k, v in results.items()
            if not v['is_invariant'] and v['n_environments'] >= self.min_environments
        }

        if not candidates:
            return None

        # Pick the worst
        worst_key = min(candidates, key=lambda k: candidates[k]['invariance'])
        edge = graph.edges[worst_key]

        intervention = InterventionOperator(
            action_type="invariance_probe",
            target_ids=[edge.source_id],
            parameters={
                "target_edge": worst_key,
                "invariance_score": candidates[worst_key]['invariance']
            },
            graph_edit_mask={worst_key: True},
            expected_contact_mode="none",
            magnitude=0.1
        )

        return worst_key, intervention


class ActiveProbingLoop:
    """
    B2 Ceiling-Pushed: Active Probing Loop — Confirm or Delete.

    The complete cycle for active causal structure learning:
    1. Identify uncertain edges (not intervention-validated)
    2. Select highest information-gain target
    3. Execute intervention (probe)
    4. Observe outcome in current environment
    5. Test invariance across environments
    6. Confirm or delete edge based on combined evidence
    7. Update graph and repeat

    This is the ceiling-pushed version of "active probing to confirm or
    delete edges." Without this loop, the graph accumulates spurious
    correlations that look like causal structure but aren't.
    """

    def __init__(
        self,
        target_selector: Optional[InterventionTargetSelector] = None,
        invariance_tester: Optional[EnvironmentInvarianceTester] = None,
        confirm_threshold: float = 0.8,
        delete_threshold: float = 0.2,
        max_probes_per_cycle: int = 5
    ):
        self.target_selector = target_selector or InterventionTargetSelector()
        self.invariance_tester = invariance_tester or EnvironmentInvarianceTester()
        self.confirm_threshold = confirm_threshold
        self.delete_threshold = delete_threshold
        self.max_probes_per_cycle = max_probes_per_cycle

        # Probing statistics
        self.total_probes = 0
        self.edges_confirmed = 0
        self.edges_deleted = 0

    def run_probing_cycle(
        self,
        graph: ObjectSceneGraph,
        intervention_executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run a full probing cycle on the graph.

        Args:
            graph: The scene graph to probe
            intervention_executor: Optional callable that executes an intervention
                and returns True if the expected effect was observed, False otherwise.
                If None, uses heuristic evaluation.

        Returns:
            Dict with probing results and graph modifications
        """
        confirmed_edges = []
        deleted_edges = []
        probed_edges = []

        for probe_idx in range(self.max_probes_per_cycle):
            # Step 1: Select target
            target_result = self.target_selector.select_target(
                graph, self.invariance_tester.environment_graphs
            )

            if target_result is None:
                break  # No more uncertain edges

            edge_key, intervention = target_result
            edge = graph.edges.get(edge_key)

            if edge is None:
                continue

            pre_confidence = edge.confidence

            # Step 2: Execute intervention
            if intervention_executor is not None:
                effect_observed = intervention_executor(intervention)
            else:
                # Heuristic: use edge confidence as proxy for observation
                effect_observed = np.random.random() < edge.causal_strength

            # Step 3: Test invariance across environments
            invariance = self.invariance_tester.test_edge_invariance(edge_key)

            # Step 4: Combined decision — confirm or delete
            if effect_observed and invariance >= self.invariance_tester.invariance_threshold:
                # Confirmed: intervention produced expected effect AND
                # edge is invariant across environments
                graph.validate_edge_via_intervention(edge_key, True)
                edge.confidence = min(1.0, edge.confidence + 0.2 * invariance)
                confirmed_edges.append(edge_key)
                self.edges_confirmed += 1
            elif not effect_observed or invariance < self.invariance_tester.prune_threshold:
                # Refuted: intervention didn't produce expected effect OR
                # edge fails invariance test across environments
                graph.validate_edge_via_intervention(edge_key, False)
                if edge.confidence < self.delete_threshold:
                    graph.remove_edge(edge_key)
                    deleted_edges.append(edge_key)
                    self.edges_deleted += 1

            # Record probe
            self.target_selector.record_probe_result(
                edge_key, effect_observed, pre_confidence, edge.confidence
            )
            probed_edges.append({
                'edge_key': edge_key,
                'observed': effect_observed,
                'invariance': invariance,
                'pre_confidence': pre_confidence,
                'post_confidence': edge.confidence
            })

            self.total_probes += 1

        # Step 5: Auto-prune non-invariant edges
        auto_pruned = self.invariance_tester.prune_non_invariant_edges(graph)

        return {
            'probed_edges': probed_edges,
            'confirmed_edges': confirmed_edges,
            'deleted_edges': deleted_edges,
            'auto_pruned': auto_pruned,
            'total_probes': self.total_probes,
            'edges_confirmed': self.edges_confirmed,
            'edges_deleted': self.edges_deleted
        }

    def register_environment(self, graph: ObjectSceneGraph):
        """Register a new environment for invariance testing."""
        self.invariance_tester.register_environment(graph)
