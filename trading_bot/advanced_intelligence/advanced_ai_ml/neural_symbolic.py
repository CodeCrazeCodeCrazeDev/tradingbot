"""
Idea #14: Neural Symbolic Integration
======================================
Combine neural networks with symbolic reasoning for explainable trading decisions.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class LogicalOperator(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"


@dataclass
class Symbol:
    name: str
    value: Optional[float] = None
    is_grounded: bool = False


@dataclass
class Rule:
    rule_id: str
    antecedent: List[Tuple[str, str, float]]
    consequent: str
    confidence: float = 1.0
    learned: bool = False


@dataclass
class Explanation:
    decision: str
    confidence: float
    rules_fired: List[Rule]
    neural_contribution: float
    symbolic_contribution: float
    reasoning_chain: List[str]


class SymbolicKnowledgeBase:
    """Knowledge base for symbolic reasoning."""
    
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.rules: List[Rule] = []
        self.facts: Dict[str, float] = {}
        
    def add_symbol(self, name: str, value: Optional[float] = None):
        self.symbols[name] = Symbol(name=name, value=value, is_grounded=value is not None)
        
    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        
    def add_fact(self, name: str, value: float):
        self.facts[name] = value
        self.add_symbol(name, value)
        
    def evaluate_condition(self, symbol: str, operator: str, threshold: float) -> bool:
        if symbol not in self.facts:
            return False
        
        value = self.facts[symbol]
        
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 1e-6
        elif operator == "!=":
            return abs(value - threshold) >= 1e-6
        
        return False
    
    def forward_chain(self) -> List[Tuple[Rule, str]]:
        fired_rules = []
        changed = True
        
        while changed:
            changed = False
            for rule in self.rules:
                all_conditions_met = True
                for symbol, operator, threshold in rule.antecedent:
                    if not self.evaluate_condition(symbol, operator, threshold):
                        all_conditions_met = False
                        break
                
                if all_conditions_met and rule.consequent not in self.facts:
                    self.facts[rule.consequent] = rule.confidence
                    fired_rules.append((rule, rule.consequent))
                    changed = True
        
        return fired_rules


class NeuralEncoder:
    """Neural network for encoding market data."""
    
    def __init__(self, input_dim: int, hidden_dim: int, symbol_dim: int):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.symbol_dim = symbol_dim
        
        self.weights = {
            "encoder1": np.random.randn(input_dim, hidden_dim) * 0.01,
            "encoder2": np.random.randn(hidden_dim, symbol_dim) * 0.01
        }
        
    def encode(self, x: np.ndarray) -> np.ndarray:
        h = np.tanh(x @ self.weights["encoder1"])
        symbols = np.sigmoid(h @ self.weights["encoder2"])
        return symbols


class NeuralSymbolicReasoner:
    """
    Neural-Symbolic Integration for explainable trading.
    Combines neural perception with symbolic reasoning.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.hidden_dim = self.config.get("hidden_dim", 128)
        self.symbol_dim = self.config.get("symbol_dim", 32)
        
        self.neural_encoder = NeuralEncoder(self.input_dim, self.hidden_dim, self.symbol_dim)
        self.knowledge_base = SymbolicKnowledgeBase()
        
        self._initialize_trading_rules()
        
        self.neural_weight = self.config.get("neural_weight", 0.6)
        self.symbolic_weight = self.config.get("symbolic_weight", 0.4)
        
        self.initialized = False
        self.metrics = {
            "decisions_made": 0,
            "rules_fired": 0,
            "avg_confidence": 0.0,
            "neural_dominant": 0,
            "symbolic_dominant": 0
        }
        
    def _initialize_trading_rules(self):
        """Initialize default trading rules."""
        self.knowledge_base.add_rule(Rule(
            rule_id="bull_trend",
            antecedent=[("momentum", ">", 0.5), ("trend_strength", ">", 0.6)],
            consequent="bullish_signal",
            confidence=0.8
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="bear_trend",
            antecedent=[("momentum", "<", -0.5), ("trend_strength", ">", 0.6)],
            consequent="bearish_signal",
            confidence=0.8
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="high_volatility_caution",
            antecedent=[("volatility", ">", 0.8)],
            consequent="reduce_position",
            confidence=0.7
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="oversold_bounce",
            antecedent=[("rsi", "<", 0.3), ("support_level", ">", 0.7)],
            consequent="bullish_signal",
            confidence=0.6
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="overbought_reversal",
            antecedent=[("rsi", ">", 0.7), ("resistance_level", ">", 0.7)],
            consequent="bearish_signal",
            confidence=0.6
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="volume_confirmation",
            antecedent=[("volume_surge", ">", 0.6), ("bullish_signal", ">", 0.5)],
            consequent="strong_buy",
            confidence=0.85
        ))
        
        self.knowledge_base.add_rule(Rule(
            rule_id="divergence_warning",
            antecedent=[("price_momentum", ">", 0.5), ("indicator_momentum", "<", -0.3)],
            consequent="divergence_alert",
            confidence=0.7
        ))
        
    async def initialize(self):
        """Initialize the neural-symbolic reasoner."""
        logger.info("Initializing Neural-Symbolic Reasoner")
        self.initialized = True
        
    async def reason(self, market_data: np.ndarray) -> Explanation:
        """Perform neural-symbolic reasoning."""
        if not self.initialized:
            await self.initialize()
        
        if len(market_data) != self.input_dim:
            if len(market_data) >= self.input_dim:
                market_data = market_data[:self.input_dim]
            else:
                market_data = np.pad(market_data, (0, self.input_dim - len(market_data)))
        
        neural_symbols = self.neural_encoder.encode(market_data)
        
        symbol_names = [
            "momentum", "trend_strength", "volatility", "rsi", 
            "support_level", "resistance_level", "volume_surge",
            "price_momentum", "indicator_momentum", "market_regime"
        ]
        
        self.knowledge_base.facts.clear()
        for i, name in enumerate(symbol_names):
            if i < len(neural_symbols):
                self.knowledge_base.add_fact(name, float(neural_symbols[i]))
        
        fired_rules = self.knowledge_base.forward_chain()
        
        neural_decision = self._neural_decision(neural_symbols)
        symbolic_decision = self._symbolic_decision(fired_rules)
        
        combined_decision, confidence = self._combine_decisions(
            neural_decision, symbolic_decision, fired_rules
        )
        
        reasoning_chain = self._build_reasoning_chain(fired_rules, neural_symbols)
        
        neural_contrib = self.neural_weight
        symbolic_contrib = self.symbolic_weight * len(fired_rules) / max(1, len(self.knowledge_base.rules))
        
        self.metrics["decisions_made"] += 1
        self.metrics["rules_fired"] += len(fired_rules)
        self.metrics["avg_confidence"] = 0.99 * self.metrics["avg_confidence"] + 0.01 * confidence
        
        if neural_contrib > symbolic_contrib:
            self.metrics["neural_dominant"] += 1
        else:
            self.metrics["symbolic_dominant"] += 1
        
        return Explanation(
            decision=combined_decision,
            confidence=confidence,
            rules_fired=[rule for rule, _ in fired_rules],
            neural_contribution=neural_contrib,
            symbolic_contribution=symbolic_contrib,
            reasoning_chain=reasoning_chain
        )
    
    def _neural_decision(self, symbols: np.ndarray) -> Tuple[str, float]:
        """Make decision based on neural output."""
        buy_score = np.mean(symbols[:len(symbols)//3])
        sell_score = np.mean(symbols[len(symbols)//3:2*len(symbols)//3])
        hold_score = np.mean(symbols[2*len(symbols)//3:])
        
        scores = {"BUY": buy_score, "SELL": sell_score, "HOLD": hold_score}
        decision = max(scores, key=scores.get)
        confidence = scores[decision]
        
        return decision, float(confidence)
    
    def _symbolic_decision(self, fired_rules: List[Tuple[Rule, str]]) -> Tuple[str, float]:
        """Make decision based on symbolic reasoning."""
        buy_confidence = 0.0
        sell_confidence = 0.0
        
        for rule, consequent in fired_rules:
            if consequent in ["bullish_signal", "strong_buy"]:
                buy_confidence += rule.confidence
            elif consequent in ["bearish_signal"]:
                sell_confidence += rule.confidence
            elif consequent == "reduce_position":
                sell_confidence += rule.confidence * 0.5
        
        if buy_confidence > sell_confidence:
            return "BUY", min(1.0, buy_confidence)
        elif sell_confidence > buy_confidence:
            return "SELL", min(1.0, sell_confidence)
        else:
            return "HOLD", 0.5
    
    def _combine_decisions(self, neural: Tuple[str, float], 
                           symbolic: Tuple[str, float],
                           fired_rules: List) -> Tuple[str, float]:
        """Combine neural and symbolic decisions."""
        neural_decision, neural_conf = neural
        symbolic_decision, symbolic_conf = symbolic
        
        if neural_decision == symbolic_decision:
            combined_conf = (self.neural_weight * neural_conf + 
                           self.symbolic_weight * symbolic_conf)
            return neural_decision, combined_conf
        
        if len(fired_rules) > 2:
            return symbolic_decision, symbolic_conf * 0.9
        
        if neural_conf > symbolic_conf + 0.2:
            return neural_decision, neural_conf * 0.8
        
        return "HOLD", 0.5
    
    def _build_reasoning_chain(self, fired_rules: List[Tuple[Rule, str]], 
                                symbols: np.ndarray) -> List[str]:
        """Build human-readable reasoning chain."""
        chain = []
        
        chain.append(f"Neural analysis detected {len(symbols)} market features")
        
        for rule, consequent in fired_rules:
            conditions = " AND ".join([
                f"{sym} {op} {thresh:.2f}" 
                for sym, op, thresh in rule.antecedent
            ])
            chain.append(f"Rule '{rule.rule_id}': IF {conditions} THEN {consequent} (confidence: {rule.confidence:.2f})")
        
        if not fired_rules:
            chain.append("No symbolic rules were triggered")
        
        return chain
    
    async def learn_rule(self, market_data: np.ndarray, 
                         outcome: str, success: bool) -> Optional[Rule]:
        """Learn new rules from experience."""
        if not self.initialized:
            await self.initialize()
        
        if not success:
            return None
        
        symbols = self.neural_encoder.encode(market_data)
        symbol_names = ["momentum", "trend_strength", "volatility", "rsi"]
        
        antecedent = []
        for i, name in enumerate(symbol_names[:min(4, len(symbols))]):
            value = symbols[i]
            if value > 0.6:
                antecedent.append((name, ">", 0.5))
            elif value < 0.4:
                antecedent.append((name, "<", 0.5))
        
        if len(antecedent) >= 2:
            new_rule = Rule(
                rule_id=f"learned_rule_{len(self.knowledge_base.rules)}",
                antecedent=antecedent,
                consequent=f"learned_{outcome.lower()}",
                confidence=0.6,
                learned=True
            )
            self.knowledge_base.add_rule(new_rule)
            logger.info(f"Learned new rule: {new_rule.rule_id}")
            return new_rule
        
        return None
    
    async def explain_decision(self, explanation: Explanation) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"Decision: {explanation.decision}",
            f"Confidence: {explanation.confidence:.2%}",
            "",
            "Reasoning:",
        ]
        
        for step in explanation.reasoning_chain:
            lines.append(f"  - {step}")
        
        lines.append("")
        lines.append(f"Neural contribution: {explanation.neural_contribution:.2%}")
        lines.append(f"Symbolic contribution: {explanation.symbolic_contribution:.2%}")
        
        if explanation.rules_fired:
            lines.append("")
            lines.append("Rules that fired:")
            for rule in explanation.rules_fired:
                lines.append(f"  - {rule.rule_id}: {rule.consequent}")
        
        return "\n".join(lines)
    
    def add_custom_rule(self, rule_id: str, conditions: List[Tuple[str, str, float]],
                        consequent: str, confidence: float = 0.7):
        """Add a custom trading rule."""
        rule = Rule(
            rule_id=rule_id,
            antecedent=conditions,
            consequent=consequent,
            confidence=confidence,
            learned=False
        )
        self.knowledge_base.add_rule(rule)
        logger.info(f"Added custom rule: {rule_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get reasoner metrics."""
        return {
            **self.metrics,
            "total_rules": len(self.knowledge_base.rules),
            "learned_rules": sum(1 for r in self.knowledge_base.rules if r.learned),
            "neural_weight": self.neural_weight,
            "symbolic_weight": self.symbolic_weight
        }
    
    async def shutdown(self):
        """Shutdown the reasoner."""
        self.knowledge_base.rules.clear()
        self.knowledge_base.facts.clear()
        self.initialized = False
        logger.info("Neural-Symbolic Reasoner shutdown complete")
