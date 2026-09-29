"""
Symbolic Reasoner - Logic-Based Reasoning for Trading
=======================================================

Implements symbolic reasoning capabilities:
1. First-order logic representation
2. Rule-based inference
3. Constraint satisfaction
4. Theorem proving for trading rules

Based on the Foundation Agents paper (arXiv:2504.01990) reasoning systems.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from collections import defaultdict

logger = logging.getLogger(__name__)


class LogicOperator(Enum):
    """Logical operators"""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"
    FORALL = "forall"
    EXISTS = "exists"


class PredicateType(Enum):
    """Types of predicates"""
    COMPARISON = "comparison"       # >, <, =, >=, <=
    MEMBERSHIP = "membership"       # in, not_in
    PROPERTY = "property"           # has_property
    RELATION = "relation"           # relates_to
    TEMPORAL = "temporal"           # before, after, during


@dataclass
class Term:
    """A term in first-order logic"""
    name: str
    term_type: str  # variable, constant, function
    arguments: List['Term'] = field(default_factory=list)
    value: Optional[Any] = None
    
    def is_variable(self) -> bool:
        return self.term_type == "variable"
    
    def is_constant(self) -> bool:
        return self.term_type == "constant"
    
    def substitute(self, substitution: Dict[str, 'Term']) -> 'Term':
        """Apply substitution to term"""
        if self.is_variable() and self.name in substitution:
            return substitution[self.name]
        elif self.arguments:
            new_args = [arg.substitute(substitution) for arg in self.arguments]
            return Term(self.name, self.term_type, new_args, self.value)
        return self
    
    def __str__(self) -> str:
        if self.arguments:
            args_str = ", ".join(str(arg) for arg in self.arguments)
            return f"{self.name}({args_str})"
        return self.name
    
    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        return self.name == other.name and self.arguments == other.arguments


@dataclass
class Predicate:
    """A predicate in first-order logic"""
    name: str
    predicate_type: PredicateType
    arguments: List[Term] = field(default_factory=list)
    negated: bool = False
    
    def substitute(self, substitution: Dict[str, Term]) -> 'Predicate':
        """Apply substitution to predicate"""
        new_args = [arg.substitute(substitution) for arg in self.arguments]
        return Predicate(self.name, self.predicate_type, new_args, self.negated)
    
    def negate(self) -> 'Predicate':
        """Return negated predicate"""
        return Predicate(self.name, self.predicate_type, self.arguments, not self.negated)
    
    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.arguments)
        pred_str = f"{self.name}({args_str})"
        return f"¬{pred_str}" if self.negated else pred_str


@dataclass
class Formula:
    """A logical formula"""
    operator: Optional[LogicOperator] = None
    predicates: List[Predicate] = field(default_factory=list)
    subformulas: List['Formula'] = field(default_factory=list)
    quantifier_var: Optional[str] = None
    
    def is_atomic(self) -> bool:
        return len(self.predicates) == 1 and not self.subformulas
    
    def substitute(self, substitution: Dict[str, Term]) -> 'Formula':
        """Apply substitution to formula"""
        new_preds = [p.substitute(substitution) for p in self.predicates]
        new_subs = [f.substitute(substitution) for f in self.subformulas]
        return Formula(self.operator, new_preds, new_subs, self.quantifier_var)
    
    def __str__(self) -> str:
        if self.is_atomic():
            return str(self.predicates[0])
        
        if self.operator == LogicOperator.NOT:
            return f"¬({self.subformulas[0]})"
        elif self.operator == LogicOperator.AND:
            parts = [str(f) for f in self.subformulas]
            return f"({' ∧ '.join(parts)})"
        elif self.operator == LogicOperator.OR:
            parts = [str(f) for f in self.subformulas]
            return f"({' ∨ '.join(parts)})"
        elif self.operator == LogicOperator.IMPLIES:
            return f"({self.subformulas[0]} → {self.subformulas[1]})"
        elif self.operator == LogicOperator.FORALL:
            return f"∀{self.quantifier_var}.({self.subformulas[0]})"
        elif self.operator == LogicOperator.EXISTS:
            return f"∃{self.quantifier_var}.({self.subformulas[0]})"
        
        return "Formula"


@dataclass
class Rule:
    """An inference rule"""
    rule_id: str
    name: str
    description: str
    
    # Structure
    antecedent: Formula  # If this...
    consequent: Formula  # Then this...
    
    # Properties
    confidence: float = 1.0
    priority: int = 0
    
    # Metadata
    source: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'antecedent': str(self.antecedent),
            'consequent': str(self.consequent),
            'confidence': self.confidence
        }


@dataclass
class Fact:
    """A known fact"""
    fact_id: str
    predicate: Predicate
    confidence: float = 1.0
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            'fact_id': self.fact_id,
            'predicate': str(self.predicate),
            'confidence': self.confidence,
            'source': self.source
        }


class Unifier:
    """Unification algorithm for pattern matching"""
    
    def unify(
        self,
        term1: Term,
        term2: Term,
        substitution: Optional[Dict[str, Term]] = None
    ) -> Optional[Dict[str, Term]]:
        """Unify two terms, returning substitution if successful"""
        substitution = substitution or {}
        
        # Apply existing substitutions
        term1 = term1.substitute(substitution)
        term2 = term2.substitute(substitution)
        
        # Same term
        if term1 == term2:
            return substitution
        
        # Variable unification
        if term1.is_variable():
            return self._unify_variable(term1, term2, substitution)
        if term2.is_variable():
            return self._unify_variable(term2, term1, substitution)
        
        # Function unification
        if term1.term_type == "function" and term2.term_type == "function":
            if term1.name != term2.name or len(term1.arguments) != len(term2.arguments):
                return None
            
            for arg1, arg2 in zip(term1.arguments, term2.arguments):
                substitution = self.unify(arg1, arg2, substitution)
                if substitution is None:
                    return None
            
            return substitution
        
        return None
    
    def _unify_variable(
        self,
        var: Term,
        term: Term,
        substitution: Dict[str, Term]
    ) -> Optional[Dict[str, Term]]:
        """Unify a variable with a term"""
        if var.name in substitution:
            return self.unify(substitution[var.name], term, substitution)
        
        # Occurs check
        if self._occurs(var, term):
            return None
        
        substitution[var.name] = term
        return substitution
    
    def _occurs(self, var: Term, term: Term) -> bool:
        """Check if variable occurs in term"""
        if var == term:
            return True
        if term.arguments:
            return any(self._occurs(var, arg) for arg in term.arguments)
        return False
    
    def unify_predicates(
        self,
        pred1: Predicate,
        pred2: Predicate
    ) -> Optional[Dict[str, Term]]:
        """Unify two predicates"""
        if pred1.name != pred2.name or pred1.negated != pred2.negated:
            return None
        if len(pred1.arguments) != len(pred2.arguments):
            return None
        
        substitution = {}
        for arg1, arg2 in zip(pred1.arguments, pred2.arguments):
            substitution = self.unify(arg1, arg2, substitution)
            if substitution is None:
                return None
        
        return substitution


class InferenceEngine:
    """Forward and backward chaining inference"""
    
    def __init__(self):
        self.unifier = Unifier()
    
    def forward_chain(
        self,
        facts: List[Fact],
        rules: List[Rule],
        max_iterations: int = 100
    ) -> List[Fact]:
        """Forward chaining inference"""
        known_facts = {f.fact_id: f for f in facts}
        new_facts = []
        
        for iteration in range(max_iterations):
            added = False
            
            for rule in sorted(rules, key=lambda r: -r.priority):
                # Try to match antecedent
                matches = self._match_formula(
                    rule.antecedent,
                    list(known_facts.values())
                )
                
                for substitution in matches:
                    # Apply substitution to consequent
                    consequent = rule.consequent.substitute(substitution)
                    
                    # Extract new facts from consequent
                    for pred in consequent.predicates:
                        fact_id = f"inferred_{len(known_facts)}_{iteration}"
                        
                        # Check if already known
                        pred_str = str(pred)
                        already_known = any(
                            str(f.predicate) == pred_str
                            for f in known_facts.values()
                        )
                        
                        if not already_known:
                            new_fact = Fact(
                                fact_id=fact_id,
                                predicate=pred,
                                confidence=rule.confidence,
                                source=f"inferred_from_{rule.rule_id}"
                            )
                            known_facts[fact_id] = new_fact
                            new_facts.append(new_fact)
                            added = True
            
            if not added:
                break
        
        return new_facts
    
    def backward_chain(
        self,
        goal: Predicate,
        facts: List[Fact],
        rules: List[Rule],
        depth: int = 10
    ) -> Tuple[bool, List[Dict]]:
        """Backward chaining to prove goal"""
        if depth <= 0:
            return False, []
        
        proofs = []
        
        # Check if goal matches a fact
        for fact in facts:
            substitution = self.unifier.unify_predicates(goal, fact.predicate)
            if substitution is not None:
                proofs.append({
                    'type': 'fact',
                    'fact_id': fact.fact_id,
                    'substitution': {k: str(v) for k, v in substitution.items()}
                })
                return True, proofs
        
        # Try to prove using rules
        for rule in rules:
            # Check if consequent matches goal
            for pred in rule.consequent.predicates:
                substitution = self.unifier.unify_predicates(goal, pred)
                if substitution is not None:
                    # Try to prove antecedent
                    antecedent = rule.antecedent.substitute(substitution)
                    
                    all_proved = True
                    sub_proofs = []
                    
                    for ant_pred in antecedent.predicates:
                        proved, proof = self.backward_chain(
                            ant_pred, facts, rules, depth - 1
                        )
                        if proved:
                            sub_proofs.extend(proof)
                        else:
                            all_proved = False
                            break
                    
                    if all_proved:
                        proofs.append({
                            'type': 'rule',
                            'rule_id': rule.rule_id,
                            'sub_proofs': sub_proofs
                        })
                        return True, proofs
        
        return False, []
    
    def _match_formula(
        self,
        formula: Formula,
        facts: List[Fact]
    ) -> List[Dict[str, Term]]:
        """Find all substitutions that make formula true"""
        if formula.is_atomic():
            matches = []
            for fact in facts:
                sub = self.unifier.unify_predicates(
                    formula.predicates[0], fact.predicate
                )
                if sub is not None:
                    matches.append(sub)
            return matches
        
        if formula.operator == LogicOperator.AND:
            # All subformulas must match
            if not formula.subformulas:
                return [{}]
            
            matches = self._match_formula(formula.subformulas[0], facts)
            
            for subformula in formula.subformulas[1:]:
                new_matches = []
                for sub in matches:
                    applied = subformula.substitute(sub)
                    sub_matches = self._match_formula(applied, facts)
                    for sm in sub_matches:
                        combined = {**sub, **sm}
                        new_matches.append(combined)
                matches = new_matches
            
            return matches
        
        if formula.operator == LogicOperator.OR:
            # Any subformula can match
            matches = []
            for subformula in formula.subformulas:
                matches.extend(self._match_formula(subformula, facts))
            return matches
        
        return []


class SymbolicReasoner:
    """
    Symbolic Reasoner
    
    Provides logic-based reasoning for trading decisions:
    - Rule-based inference
    - Constraint checking
    - Theorem proving
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.inference_engine = InferenceEngine()
        self.unifier = Unifier()
        
        # Knowledge base
        self.facts: Dict[str, Fact] = {}
        self.rules: Dict[str, Rule] = {}
        
        # Built-in predicates
        self.builtin_evaluators: Dict[str, Callable] = {
            'greater_than': lambda x, y: x > y,
            'less_than': lambda x, y: x < y,
            'equals': lambda x, y: x == y,
            'in_range': lambda x, low, high: low <= x <= high
        }
        
        # Statistics
        self.stats = {
            'facts_added': 0,
            'rules_added': 0,
            'inferences_made': 0,
            'queries_answered': 0
        }
        
        # Initialize trading rules
        self._initialize_trading_rules()
        
        logger.info("Symbolic Reasoner initialized")
    
    def _initialize_trading_rules(self):
        """Initialize common trading rules"""
        # Risk management rules
        self.add_rule(
            name="position_size_limit",
            description="Limit position size based on risk",
            antecedent_str="risk_level(X, high) AND position_size(X, Size)",
            consequent_str="reduce_position(X)",
            confidence=0.9
        )
        
        self.add_rule(
            name="stop_loss_trigger",
            description="Trigger stop loss when loss exceeds threshold",
            antecedent_str="loss_percent(X, Loss) AND greater_than(Loss, 0.05)",
            consequent_str="close_position(X)",
            confidence=1.0
        )
        
        # Trend following rules
        self.add_rule(
            name="trend_continuation",
            description="Continue trend when momentum is strong",
            antecedent_str="trend(X, up) AND momentum(X, strong)",
            consequent_str="hold_long(X)",
            confidence=0.7
        )
        
        # Mean reversion rules
        self.add_rule(
            name="mean_reversion_entry",
            description="Enter mean reversion trade when oversold",
            antecedent_str="rsi(X, Value) AND less_than(Value, 30)",
            consequent_str="consider_long(X)",
            confidence=0.6
        )
    
    def add_fact(
        self,
        predicate_name: str,
        arguments: List[Any],
        confidence: float = 1.0,
        source: str = ""
    ) -> Fact:
        """Add a fact to the knowledge base"""
        # Create terms from arguments
        terms = []
        for arg in arguments:
            if isinstance(arg, str) and arg.startswith('?'):
                terms.append(Term(arg[1:], "variable"))
            else:
                terms.append(Term(str(arg), "constant", value=arg))
        
        predicate = Predicate(
            name=predicate_name,
            predicate_type=PredicateType.PROPERTY,
            arguments=terms
        )
        
        fact = Fact(
            fact_id=f"fact_{len(self.facts)}",
            predicate=predicate,
            confidence=confidence,
            source=source
        )
        
        self.facts[fact.fact_id] = fact
        self.stats['facts_added'] += 1
        
        return fact
    
    def add_rule(
        self,
        name: str,
        description: str,
        antecedent_str: str,
        consequent_str: str,
        confidence: float = 1.0,
        priority: int = 0
    ) -> Rule:
        """Add a rule to the knowledge base"""
        antecedent = self._parse_formula(antecedent_str)
        consequent = self._parse_formula(consequent_str)
        
        rule = Rule(
            rule_id=f"rule_{len(self.rules)}",
            name=name,
            description=description,
            antecedent=antecedent,
            consequent=consequent,
            confidence=confidence,
            priority=priority
        )
        
        self.rules[rule.rule_id] = rule
        self.stats['rules_added'] += 1
        
        return rule
    
    def _parse_formula(self, formula_str: str) -> Formula:
        """Parse a formula string into Formula object"""
        # Simple parser for predicate strings
        # Format: "pred1(arg1, arg2) AND pred2(arg3)"
        
        predicates = []
        subformulas = []
        operator = None
        
        # Split by AND/OR
        if " AND " in formula_str:
            parts = formula_str.split(" AND ")
            operator = LogicOperator.AND
            for part in parts:
                sub = self._parse_formula(part.strip())
                subformulas.append(sub)
        elif " OR " in formula_str:
            parts = formula_str.split(" OR ")
            operator = LogicOperator.OR
            for part in parts:
                sub = self._parse_formula(part.strip())
                subformulas.append(sub)
        else:
            # Single predicate
            pred = self._parse_predicate(formula_str.strip())
            predicates.append(pred)
        
        return Formula(operator=operator, predicates=predicates, subformulas=subformulas)
    
    def _parse_predicate(self, pred_str: str) -> Predicate:
        """Parse a predicate string"""
        # Format: "predicate_name(arg1, arg2, ...)"
        match = re.match(r'(\w+)\((.*)\)', pred_str)
        
        if not match:
            return Predicate(pred_str, PredicateType.PROPERTY)
        
        name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments
        terms = []
        for arg in args_str.split(','):
            arg = arg.strip()
            if arg.startswith('?') or arg[0].isupper():
                terms.append(Term(arg.lstrip('?'), "variable"))
            else:
                try:
                    value = float(arg)
                    terms.append(Term(arg, "constant", value=value))
                except ValueError:
                    terms.append(Term(arg, "constant", value=arg))
        
        # Determine predicate type
        if name in ['greater_than', 'less_than', 'equals', 'in_range']:
            pred_type = PredicateType.COMPARISON
        elif name in ['before', 'after', 'during']:
            pred_type = PredicateType.TEMPORAL
        else:
            pred_type = PredicateType.PROPERTY
        
        return Predicate(name, pred_type, terms)
    
    def infer(self, max_iterations: int = 50) -> List[Fact]:
        """Run forward chaining inference"""
        new_facts = self.inference_engine.forward_chain(
            list(self.facts.values()),
            list(self.rules.values()),
            max_iterations
        )
        
        for fact in new_facts:
            self.facts[fact.fact_id] = fact
        
        self.stats['inferences_made'] += len(new_facts)
        
        return new_facts
    
    def query(
        self,
        predicate_name: str,
        arguments: List[Any]
    ) -> Tuple[bool, List[Dict]]:
        """Query the knowledge base"""
        # Create query predicate
        terms = []
        for arg in arguments:
            if isinstance(arg, str) and (arg.startswith('?') or arg[0].isupper()):
                terms.append(Term(arg.lstrip('?'), "variable"))
            else:
                terms.append(Term(str(arg), "constant", value=arg))
        
        goal = Predicate(predicate_name, PredicateType.PROPERTY, terms)
        
        # Try backward chaining
        proved, proofs = self.inference_engine.backward_chain(
            goal,
            list(self.facts.values()),
            list(self.rules.values())
        )
        
        self.stats['queries_answered'] += 1
        
        return proved, proofs
    
    def check_constraint(
        self,
        constraint_name: str,
        values: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check if a constraint is satisfied"""
        # Add values as temporary facts
        temp_facts = []
        for name, value in values.items():
            fact = self.add_fact(name, [value], source="constraint_check")
            temp_facts.append(fact.fact_id)
        
        # Run inference
        self.infer(max_iterations=10)
        
        # Check for constraint violation
        violated, proofs = self.query(f"violates_{constraint_name}", ["?X"])
        
        # Clean up temporary facts
        for fact_id in temp_facts:
            if fact_id in self.facts:
                del self.facts[fact_id]
        
        if violated:
            return False, f"Constraint {constraint_name} violated"
        return True, "Constraint satisfied"
    
    def evaluate_trading_decision(
        self,
        asset: str,
        market_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate trading decision using rules"""
        # Add market state as facts
        for key, value in market_state.items():
            self.add_fact(key, [asset, value], source="market_state")
        
        # Run inference
        new_facts = self.infer()
        
        # Collect recommendations
        recommendations = []
        for fact in new_facts:
            pred_name = fact.predicate.name
            if pred_name in ['hold_long', 'hold_short', 'close_position', 
                            'consider_long', 'consider_short', 'reduce_position']:
                recommendations.append({
                    'action': pred_name,
                    'confidence': fact.confidence,
                    'source': fact.source
                })
        
        return {
            'asset': asset,
            'recommendations': recommendations,
            'facts_inferred': len(new_facts),
            'market_state': market_state
        }
    
    def get_explanation(self, fact_id: str) -> Dict[str, Any]:
        """Get explanation for how a fact was derived"""
        if fact_id not in self.facts:
            return {'error': 'Fact not found'}
        
        fact = self.facts[fact_id]
        
        if not fact.source.startswith('inferred_from_'):
            return {
                'fact': str(fact.predicate),
                'type': 'base_fact',
                'source': fact.source
            }
        
        rule_id = fact.source.replace('inferred_from_', '')
        rule = self.rules.get(rule_id)
        
        if not rule:
            return {
                'fact': str(fact.predicate),
                'type': 'inferred',
                'rule': 'unknown'
            }
        
        return {
            'fact': str(fact.predicate),
            'type': 'inferred',
            'rule': rule.name,
            'rule_description': rule.description,
            'antecedent': str(rule.antecedent),
            'confidence': fact.confidence
        }
    
    def clear_facts(self, source: Optional[str] = None):
        """Clear facts from knowledge base"""
        if source:
            to_remove = [fid for fid, f in self.facts.items() if f.source == source]
            for fid in to_remove:
                del self.facts[fid]
        else:
            self.facts.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reasoner statistics"""
        return {
            **self.stats,
            'total_facts': len(self.facts),
            'total_rules': len(self.rules),
            'inferred_facts': len([f for f in self.facts.values() 
                                   if f.source.startswith('inferred')])
        }
