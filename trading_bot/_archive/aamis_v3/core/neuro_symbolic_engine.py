"""
Neuro-Symbolic Reasoning Engine
Combines neural networks (pattern recognition) with symbolic logic (causal reasoning)
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict
import logging
from datetime import datetime
import numpy
import pandas

logger = logging.getLogger(__name__)


class LogicOperator(Enum):
    """Logical operators for symbolic reasoning"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    IMPLIES = "IMPLIES"
    IFF = "IFF"  # If and only if
    XOR = "XOR"


class ModalOperator(Enum):
    """Modal logic operators"""
    NECESSARY = "NECESSARY"  # Must be true
    POSSIBLE = "POSSIBLE"    # Could be true
    PROBABLE = "PROBABLE"    # Likely true


@dataclass
class Predicate:
    """First-order logic predicate"""
    name: str
    arguments: List[str]
    truth_value: Optional[bool] = None
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        args = ", ".join(self.arguments)
        return f"{self.name}({args})"
    
    def __hash__(self):
        return hash((self.name, tuple(self.arguments)))


@dataclass
class LogicalRule:
    """If-then logical rule"""
    premises: List[Predicate]
    conclusion: Predicate
    operator: LogicOperator = LogicOperator.AND
    confidence: float = 1.0
    
    def evaluate(self, knowledge_base: Dict[str, Predicate]) -> Tuple[bool, float]:
        """Evaluate rule given current knowledge"""
        premise_values = []
        min_confidence = 1.0
        
        for premise in self.premises:
            key = str(premise)
            if key in knowledge_base:
                pred = knowledge_base[key]
                premise_values.append(pred.truth_value)
                min_confidence = min(min_confidence, pred.confidence)
            else:
                return False, 0.0  # Unknown premise
        
        # Apply logical operator
        if self.operator == LogicOperator.AND:
            result = all(premise_values)
        elif self.operator == LogicOperator.OR:
            result = any(premise_values)
        elif self.operator == LogicOperator.NOT:
            result = not premise_values[0] if premise_values else False
        elif self.operator == LogicOperator.IMPLIES:
            result = (not premise_values[0]) or premise_values[1] if len(premise_values) >= 2 else False
        else:
            result = False
        
        # Combine confidences
        combined_confidence = min_confidence * self.confidence
        
        return result, combined_confidence


@dataclass
class CausalEdge:
    """Causal relationship between variables"""
    cause: str
    effect: str
    strength: float  # -1 to 1 (negative = inverse relationship)
    lag: int  # Time lag in periods
    confidence: float = 1.0
    mechanism: str = ""  # Explanation of causal mechanism


class CausalGraph:
    """Directed Acyclic Graph representing causal relationships"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.edges: Dict[Tuple[str, str], CausalEdge] = {}
        
    def add_causal_edge(self, edge: CausalEdge):
        """Add causal relationship"""
        self.graph.add_edge(edge.cause, edge.effect, 
                           strength=edge.strength, 
                           lag=edge.lag,
                           confidence=edge.confidence)
        self.edges[(edge.cause, edge.effect)] = edge
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(edge.cause, edge.effect)
            del self.edges[(edge.cause, edge.effect)]
            raise ValueError(f"Adding edge {edge.cause} -> {edge.effect} would create cycle")
    
    def get_causal_chain(self, cause: str, effect: str) -> List[List[str]]:
        """Find all causal paths from cause to effect"""
        try:
            paths = list(nx.all_simple_paths(self.graph, cause, effect))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    def get_total_effect(self, cause: str, effect: str) -> float:
        """Calculate total causal effect along all paths"""
        paths = self.get_causal_chain(cause, effect)
        total_effect = 0.0
        
        for path in paths:
            path_effect = 1.0
            for i in range(len(path) - 1):
                edge = self.edges.get((path[i], path[i+1]))
                if edge:
                    path_effect *= edge.strength
            total_effect += path_effect
        
        return total_effect
    
    def do_intervention(self, variable: str, value: Any) -> 'CausalGraph':
        """Perform do-calculus intervention (set variable, remove incoming edges)"""
        new_graph = CausalGraph()
        
        # Copy all edges except those pointing to intervened variable
        for (cause, effect), edge in self.edges.items():
            if effect != variable:
                new_graph.add_causal_edge(edge)
        
        return new_graph
    
    def counterfactual(self, variable: str, actual_value: Any, 
                      counterfactual_value: Any) -> Dict[str, float]:
        """Reason about counterfactual: 'What if X had been Y instead of Z?'"""
        # Get all variables affected by this variable
        descendants = nx.descendants(self.graph, variable)
        
        effects = {}
        for descendant in descendants:
            # Calculate effect of changing variable
            total_effect = self.get_total_effect(variable, descendant)
            value_diff = counterfactual_value - actual_value if isinstance(actual_value, (int, float)) else 0
            effects[descendant] = total_effect * value_diff
        
        return effects


class SymbolicReasoner:
    """Symbolic logic reasoning system"""
    
    def __init__(self):
        self.knowledge_base: Dict[str, Predicate] = {}
        self.rules: List[LogicalRule] = []
        self.causal_graph = CausalGraph()
        
    def add_fact(self, predicate: Predicate):
        """Add fact to knowledge base"""
        self.knowledge_base[str(predicate)] = predicate
    
    def add_rule(self, rule: LogicalRule):
        """Add logical rule"""
        self.rules.append(rule)
    
    def forward_chain(self, max_iterations: int = 100) -> Set[Predicate]:
        """Forward chaining inference"""
        new_facts = set()
        
        for _ in range(max_iterations):
            derived_anything = False
            
            for rule in self.rules:
                result, confidence = rule.evaluate(self.knowledge_base)
                
                if result:
                    conclusion_key = str(rule.conclusion)
                    if conclusion_key not in self.knowledge_base:
                        # Derive new fact
                        new_fact = Predicate(
                            name=rule.conclusion.name,
                            arguments=rule.conclusion.arguments,
                            truth_value=True,
                            confidence=confidence
                        )
                        self.knowledge_base[conclusion_key] = new_fact
                        new_facts.add(new_fact)
                        derived_anything = True
            
            if not derived_anything:
                break
        
        return new_facts
    
    def check_consistency(self) -> List[str]:
        """Check for logical contradictions"""
        contradictions = []
        
        # Check for P and NOT P
        for key, pred in self.knowledge_base.items():
            # Look for negation
            neg_key = f"NOT({key})"
            if neg_key in self.knowledge_base:
                neg_pred = self.knowledge_base[neg_key]
                if pred.truth_value and neg_pred.truth_value:
                    contradictions.append(f"Contradiction: {key} and {neg_key} both true")
        
        return contradictions
    
    def explain_reasoning(self, conclusion: Predicate) -> List[str]:
        """Generate explanation for how conclusion was derived"""
        explanation = []
        conclusion_key = str(conclusion)
        
        # Find rules that could derive this conclusion
        for rule in self.rules:
            if str(rule.conclusion) == conclusion_key:
                result, confidence = rule.evaluate(self.knowledge_base)
                if result:
                    explanation.append(f"Derived {conclusion} from:")
                    for premise in rule.premises:
                        explanation.append(f"  - {premise}")
                    explanation.append(f"  Confidence: {confidence:.2%}")
        
        return explanation


class NeuralPatternExtractor:
    """Neural network for pattern extraction from data"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        # Simplified - in production use PyTorch/TensorFlow
        self.weights_1 = np.random.randn(input_dim, hidden_dim) * 0.01
        self.weights_2 = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.weights_3 = np.random.randn(hidden_dim, input_dim) * 0.01
        
    def extract_features(self, data: np.ndarray) -> np.ndarray:
        """Extract high-level features from raw data"""
        # Forward pass through network
        h1 = np.tanh(data @ self.weights_1)
        h2 = np.tanh(h1 @ self.weights_2)
        features = h2
        return features
    
    def detect_patterns(self, data: np.ndarray, threshold: float = 0.8) -> List[Dict]:
        """Detect patterns in data"""
        features = self.extract_features(data)
        
        patterns = []
        # Simplified pattern detection
        for i in range(len(features)):
            pattern_strength = np.abs(features[i]).mean()
            if pattern_strength > threshold:
                patterns.append({
                    'index': i,
                    'strength': float(pattern_strength),
                    'features': features[i].tolist()
                })
        
        return patterns


class NeuroSymbolicEngine:
    """
    Integrates neural pattern recognition with symbolic logical reasoning
    """
    
    def __init__(self, input_dim: int = 100):
        self.neural_extractor = NeuralPatternExtractor(input_dim)
        self.symbolic_reasoner = SymbolicReasoner()
        self.pattern_to_predicate_map: Dict[str, Predicate] = {}
        
    def process_data(self, data: np.ndarray, variable_names: List[str]) -> Dict[str, Any]:
        """Process raw data through neural-symbolic pipeline"""
        
        # Step 1: Neural pattern extraction
        patterns = self.neural_extractor.detect_patterns(data)
        
        # Step 2: Convert patterns to symbolic predicates
        for pattern in patterns:
            pred_name = f"Pattern_{pattern['index']}"
            predicate = Predicate(
                name=pred_name,
                arguments=variable_names,
                truth_value=True,
                confidence=pattern['strength']
            )
            self.symbolic_reasoner.add_fact(predicate)
            self.pattern_to_predicate_map[pred_name] = predicate
        
        # Step 3: Apply symbolic reasoning
        new_facts = self.symbolic_reasoner.forward_chain()
        
        # Step 4: Check consistency
        contradictions = self.symbolic_reasoner.check_consistency()
        
        return {
            'patterns': patterns,
            'predicates': list(self.symbolic_reasoner.knowledge_base.values()),
            'new_facts': list(new_facts),
            'contradictions': contradictions
        }
    
    def add_causal_relationship(self, cause: str, effect: str, 
                               strength: float, lag: int, mechanism: str = ""):
        """Add causal relationship to graph"""
        edge = CausalEdge(
            cause=cause,
            effect=effect,
            strength=strength,
            lag=lag,
            mechanism=mechanism
        )
        self.symbolic_reasoner.causal_graph.add_causal_edge(edge)
    
    def reason_about_intervention(self, variable: str, value: Any) -> Dict[str, float]:
        """Reason about intervention: 'What if we set X to Y?'"""
        intervened_graph = self.symbolic_reasoner.causal_graph.do_intervention(variable, value)
        
        # Calculate effects on all descendants
        effects = {}
        if variable in intervened_graph.graph:
            descendants = nx.descendants(intervened_graph.graph, variable)
            for desc in descendants:
                effect = intervened_graph.get_total_effect(variable, desc)
                effects[desc] = effect
        
        return effects
    
    def counterfactual_analysis(self, variable: str, actual: Any, 
                                counterfactual: Any) -> Dict[str, Any]:
        """Counterfactual reasoning: 'If X had been Y instead of Z, what would have happened?'"""
        effects = self.symbolic_reasoner.causal_graph.counterfactual(
            variable, actual, counterfactual
        )
        
        return {
            'variable': variable,
            'actual_value': actual,
            'counterfactual_value': counterfactual,
            'predicted_effects': effects
        }
    
    def explain_decision(self, decision: str) -> Dict[str, Any]:
        """Generate comprehensive explanation for a decision"""
        
        # Find relevant predicates
        relevant_preds = [p for p in self.symbolic_reasoner.knowledge_base.values() 
                         if decision.lower() in str(p).lower()]
        
        # Generate reasoning chain
        explanations = []
        for pred in relevant_preds:
            exp = self.symbolic_reasoner.explain_reasoning(pred)
            if exp:
                explanations.extend(exp)
        
        # Find causal chains
        causal_chains = []
        for (cause, effect), edge in self.symbolic_reasoner.causal_graph.edges.items():
            if decision.lower() in effect.lower():
                chain = self.symbolic_reasoner.causal_graph.get_causal_chain(cause, effect)
                if chain:
                    causal_chains.append({
                        'chain': chain,
                        'strength': edge.strength,
                        'mechanism': edge.mechanism
                    })
        
        return {
            'decision': decision,
            'relevant_facts': [str(p) for p in relevant_preds],
            'logical_reasoning': explanations,
            'causal_chains': causal_chains,
            'confidence': np.mean([p.confidence for p in relevant_preds]) if relevant_preds else 0.0
        }
    
    def build_market_causal_model(self):
        """Build comprehensive causal model for financial markets"""
        
        # Macro causality chains
        self.add_causal_relationship("oil_price", "inflation", 0.3, 2, 
                                    "Energy costs pass through to CPI")
        self.add_causal_relationship("inflation", "fed_rates", 0.7, 1,
                                    "Fed reaction function to inflation")
        self.add_causal_relationship("fed_rates", "usd_strength", 0.5, 0,
                                    "Higher rates attract capital flows")
        self.add_causal_relationship("fed_rates", "equity_valuations", -0.6, 1,
                                    "Higher discount rate lowers PV of future cash flows")
        self.add_causal_relationship("usd_strength", "emerging_markets", -0.4, 1,
                                    "Strong USD creates EM debt stress")
        
        # Microstructure causality
        self.add_causal_relationship("order_flow_imbalance", "price_movement", 0.8, 0,
                                    "Supply-demand imbalance drives price")
        self.add_causal_relationship("volatility", "bid_ask_spread", 0.6, 0,
                                    "Uncertainty increases market maker risk premium")
        
        # Sentiment causality
        self.add_causal_relationship("vix", "equity_prices", -0.7, 0,
                                    "Fear gauge inversely correlated with risk assets")
        self.add_causal_relationship("put_call_ratio", "market_bottom", 0.5, 1,
                                    "Extreme fear often marks bottoms")
        
        logger.info("Built comprehensive market causal model")


# Example usage and testing
if __name__ == "__main__":
    # Initialize engine
    engine = NeuroSymbolicEngine(input_dim=50)
    
    # Build market causal model
    engine.build_market_causal_model()
    
    # Add some logical rules
    # Rule: If inflation rising AND Fed hawkish THEN rates will increase
    premise1 = Predicate("inflation_rising", ["CPI"], True, 0.9)
    premise2 = Predicate("fed_hawkish", ["FOMC"], True, 0.85)
    conclusion = Predicate("rates_increasing", ["Fed_Funds"], True, 0.95)
    
    rule = LogicalRule(
        premises=[premise1, premise2],
        conclusion=conclusion,
        operator=LogicOperator.AND,
        confidence=0.9
    )
    
    engine.symbolic_reasoner.add_fact(premise1)
    engine.symbolic_reasoner.add_fact(premise2)
    engine.symbolic_reasoner.add_rule(rule)
    
    # Forward chain to derive conclusions
    new_facts = engine.symbolic_reasoner.forward_chain()
    logger.info(f"Derived {len(new_facts)} new facts")
    
    # Counterfactual analysis
    result = engine.counterfactual_analysis("oil_price", 90, 70)
    logger.info(f"\nCounterfactual: If oil was $70 instead of $90:")
    for var, effect in result['predicted_effects'].items():
        logger.info(f"  {var}: {effect:+.2f} impact")
    
    # Intervention analysis
    effects = engine.reason_about_intervention("fed_rates", 5.0)
    logger.info(f"\nIntervention: If Fed sets rates to 5%:")
    for var, effect in effects.items():
        logger.info(f"  {var}: {effect:+.2f} effect")
    
    # Generate explanation
    explanation = engine.explain_decision("rates_increasing")
    logger.info(f"\nExplanation for 'rates_increasing':")
    logger.info(f"Confidence: {explanation['confidence']:.2%}")
    for line in explanation['logical_reasoning']:
        logger.info(f"  {line}")
