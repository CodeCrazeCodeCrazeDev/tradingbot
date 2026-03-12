"""
Phase 3: Neuro-Symbolic Reasoning - Neural + Symbolic Fusion
Combines neural networks with symbolic reasoning
"""

import logging
from typing import Dict, List, Optional
import numpy as np
import torch
import torch.nn as nn
from .knowledge_graph import FinancialKnowledgeGraph
from .chain_of_thought import ChainOfThoughtReasoner

logger = logging.getLogger(__name__)


class NeuroSymbolicFusion(nn.Module):
    """
    Neural network that incorporates symbolic knowledge.
    Combines learned patterns with financial rules.
    """
    
    def __init__(self, input_dim: int = 20, hidden_dim: int = 64):
        super().__init__()
        
        # Neural components
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Fusion layer
        self.fusion = nn.Linear(hidden_dim * 2, hidden_dim)
        
        # Output heads
        self.action_head = nn.Linear(hidden_dim, 3)  # BUY, SELL, HOLD
        self.confidence_head = nn.Linear(hidden_dim, 1)
        
        # Symbolic components
        self.knowledge_graph = FinancialKnowledgeGraph()
        self.reasoner = ChainOfThoughtReasoner()
        
        logger.info("✅ NeuroSymbolic Fusion initialized")
    
    def forward(self, market_state: Dict) -> Dict:
        """
        Combine neural and symbolic reasoning.
        
        Args:
            market_state: Current market conditions
        
        Returns:
            Dictionary with action, confidence, and reasoning
        """
        # 1. Neural analysis
        neural_features = self._neural_analysis(market_state)
        
        # 2. Symbolic reasoning
        symbolic_features = self._symbolic_reasoning(market_state)
        
        # 3. Fusion
        fused = self._fuse_features(neural_features, symbolic_features)
        
        # 4. Decision
        action_logits = self.action_head(fused)
        confidence = torch.sigmoid(self.confidence_head(fused))
        
        # 5. Get reasoning chain
        reasoning = self.reasoner.reason_about_trade(market_state)
        
        # Convert to probabilities
        action_probs = torch.softmax(action_logits, dim=-1)
        
        return {
            'action_probs': action_probs.detach().numpy(),
            'confidence': float(confidence.item()),
            'reasoning': reasoning['reasoning_chain'],
            'explanation': reasoning['explanation']
        }
    
    def _neural_analysis(self, market_state: Dict) -> torch.Tensor:
        """Neural network analysis of market state."""
        # Convert market state to tensor
        features = self._encode_market_state(market_state)
        
        # Extract features
        return self.feature_extractor(features)
    
    def _symbolic_reasoning(self, market_state: Dict) -> torch.Tensor:
        """Symbolic reasoning about market state."""
        # Get conclusions from knowledge graph
        conclusions = self.knowledge_graph.reason(market_state)
        
        # Convert conclusions to features
        symbolic_features = self._encode_conclusions(conclusions)
        
        return symbolic_features
    
    def _fuse_features(
        self,
        neural_features: torch.Tensor,
        symbolic_features: torch.Tensor
    ) -> torch.Tensor:
        """Fuse neural and symbolic features."""
        # Concatenate features
        combined = torch.cat([neural_features, symbolic_features], dim=-1)
        
        # Fuse through neural network
        return self.fusion(combined)
    
    def _encode_market_state(self, market_state: Dict) -> torch.Tensor:
        """Encode market state as tensor."""
        features = [
            market_state.get('price', 0),
            market_state.get('volume', 0),
            market_state.get('rsi', 50),
            market_state.get('macd', 0),
            market_state.get('sma_20', 0),
            market_state.get('sma_50', 0),
            market_state.get('volatility', 1.0),
            market_state.get('adx', 0),
            market_state.get('sentiment', 0),
            market_state.get('trend', 0)
        ]
        
        # Pad to input_dim
        while len(features) < 20:
            features.append(0.0)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def _encode_conclusions(self, conclusions: Dict) -> torch.Tensor:
        """Encode symbolic conclusions as tensor."""
        # Extract key information
        regime = conclusions['market_regime']
        risk_profile = conclusions['risk_profile']
        confidence = conclusions['confidence']
        
        # One-hot encode regime
        regime_encoding = {
            'trending': [1, 0, 0, 0],
            'ranging': [0, 1, 0, 0],
            'high_volatility': [0, 0, 1, 0],
            'low_volatility': [0, 0, 0, 1]
        }.get(regime, [0, 0, 0, 0])
        
        # One-hot encode risk profile
        risk_encoding = {
            'low': [1, 0, 0],
            'moderate': [0, 1, 0],
            'high': [0, 0, 1]
        }.get(risk_profile, [0, 1, 0])
        
        # Combine features
        features = regime_encoding + risk_encoding + [confidence]
        
        # Pad to match neural features
        while len(features) < 64:  # hidden_dim
            features.append(0.0)
        
        return torch.tensor(features, dtype=torch.float32)
    
    def explain_decision(self, market_state: Dict, output: Dict) -> str:
        """
        Generate detailed explanation of decision process.
        
        Args:
            market_state: Input market state
            output: Model output including probabilities and reasoning
        
        Returns:
            Human-readable explanation
        """
        # Get action probabilities
        actions = ['BUY', 'SELL', 'HOLD']
        probs = output['action_probs']
        action = actions[np.argmax(probs)]
        
        # Get symbolic reasoning
        knowledge = self.knowledge_graph.reason(market_state)
        
        # Build explanation
        explanation = [
            f"Decision: {action} (Confidence: {output['confidence']:.1%})\n",
            "\nMarket Analysis:",
            f"- Regime: {knowledge['market_regime']}",
            f"- Risk Profile: {knowledge['risk_profile']}",
            f"- Rule Confidence: {knowledge['confidence']:.1%}",
            "\nProbabilities:",
            f"- BUY: {probs[0]:.1%}",
            f"- SELL: {probs[1]:.1%}",
            f"- HOLD: {probs[2]:.1%}",
            "\nReasoning Chain:",
        ]
        
        # Add reasoning steps
        for step in output['reasoning']:
            explanation.append(f"- {step['step']}: {step['conclusion']}")
        
        return "\n".join(explanation)
    
    def update_knowledge(self, new_rule: str, category: str):
        """Add new rule to knowledge graph."""
        self.knowledge_graph.add_rule(category, new_rule)
    
    def save_model(self, filepath: str):
        """Save both neural and symbolic components."""
        state = {
            'neural_state': self.state_dict(),
            'knowledge_rules': self.knowledge_graph.rules,
            'market_regimes': self.knowledge_graph.market_regimes
        }
        torch.save(state, filepath)
        logger.info(f"💾 NeuroSymbolic model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load both neural and symbolic components."""
        state = torch.load(filepath)
        self.load_state_dict(state['neural_state'])
        self.knowledge_graph.rules = state['knowledge_rules']
        self.knowledge_graph.market_regimes = state['market_regimes']
        logger.info(f"📂 NeuroSymbolic model loaded from {filepath}")
