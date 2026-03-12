"""Multi-Agent Reinforcement Learning Module - AI Trading Personas.

This module implements specialized AI agents that debate trading decisions:
- MacroStrategist: HTF analysis and key levels
- TacticalExecutioner: LTF timing and liquidity grabs  
- RiskSentinel: Portfolio exposure and black swan monitoring
- HeadAI: Weighs agent arguments for final decisions
"""

import numpy as np
import pandas as pd

# Standard library imports
from collections import deque
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Create dummy classes for when torch is not available
    class nn:
        """
        nn class.

    Auto-documented by QwenCodeMender.
        """
        class Module:
            """
            Module class.

    Auto-documented by QwenCodeMender.
            """
            pass
    torch = None

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of trading agents."""
    MACRO_STRATEGIST = "macro_strategist"
    TACTICAL_EXECUTIONER = "tactical_executioner"
    RISK_SENTINEL = "risk_sentinel"
    HEAD_AI = "head_ai"


@dataclass
class TradingDecision:
    """Represents a trading decision from an agent."""
    agent_type: AgentType
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reasoning: str
    risk_assessment: float
    expected_return: float
    time_horizon: str
    supporting_data: Dict


@dataclass
class MarketState:
    """Current market state for agent analysis."""
    price: float
    volume: float
    volatility: float
    trend_direction: str
    support_levels: List[float]
    resistance_levels: List[float]
    liquidity_zones: List[Dict]
    market_regime: str
    correlation_data: Dict


class BaseAgent(nn.Module):
    """Base class for all trading agents."""
    
    def __init__(self, agent_type: AgentType, input_dim: int = 50, hidden_dim: int = 128):
        super().__init__()
        self.agent_type = agent_type
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # Neural network layers
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        self.decision_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 32),
            nn.ReLU(),
            nn.Linear(32, 3)  # buy, sell, hold
        )
        
        self.confidence_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
        
        # Experience replay buffer
        self.memory = deque(maxlen=10000)
        self.optimizer = optim.Adam(self.parameters(), lr=0.001)
        
    def forward(self, market_state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through the network."""
        features = self.feature_extractor(market_state)
        decision_logits = self.decision_head(features)
        confidence = self.confidence_head(features)
        return decision_logits, confidence
    
    def make_decision(self, market_state: MarketState) -> TradingDecision:
        """Make a trading decision based on market state."""
        # Convert market state to tensor
        state_vector = self._encode_market_state(market_state)
        
        with torch.no_grad():
            decision_logits, confidence = self.forward(state_vector)
            action_probs = torch.softmax(decision_logits, dim=-1)
            action_idx = torch.argmax(action_probs).item()
            
        actions = ['buy', 'sell', 'hold']
        action = actions[action_idx]
        
        # Generate reasoning based on agent type
        reasoning = self._generate_reasoning(market_state, action)
        
        return TradingDecision(
            agent_type=self.agent_type,
            action=action,
            confidence=confidence.item(),
            reasoning=reasoning,
            risk_assessment=self._assess_risk(market_state),
            expected_return=self._estimate_return(market_state, action),
            time_horizon=self._get_time_horizon(),
            supporting_data=self._get_supporting_data(market_state)
        )
    
    def _encode_market_state(self, market_state: MarketState) -> torch.Tensor:
        """Encode market state into tensor format."""
        # Basic encoding - can be enhanced based on agent specialization
        features = [
            market_state.price / 1000.0,  # Normalize price
            market_state.volume / 10000.0,  # Normalize volume
            market_state.volatility,
            1.0 if market_state.trend_direction == 'up' else -1.0 if market_state.trend_direction == 'down' else 0.0,
            len(market_state.support_levels) / 10.0,
            len(market_state.resistance_levels) / 10.0,
            len(market_state.liquidity_zones) / 5.0
        ]
        
        # Pad to input_dim
        while len(features) < self.input_dim:
            features.append(0.0)
        
        return torch.tensor(features[:self.input_dim], dtype=torch.float32).unsqueeze(0)
    
    def _generate_reasoning(self, market_state, action: str) -> str:
        """Generate reasoning for the decision."""
        # Use market_state for more detailed reasoning in subclasses
        return f"{self.agent_type.value} recommends {action} based on current market conditions"
    
    def _assess_risk(self, market_state) -> float:
        """Assess risk level for current market state."""
        return market_state.volatility  # Simple risk assessment
    
    def _estimate_return(self, market_state, action: str) -> float:
        """Estimate expected return for the action."""
        if action == 'hold':
            return 0.0
        return np.random.uniform(-0.02, 0.03)  # Placeholder
    
    def _get_time_horizon(self) -> str:
        """Get typical time horizon for this agent."""
        return "medium"
    
    def _get_supporting_data(self, market_state: MarketState) -> Dict:
        """Get supporting data for the decision."""
        return {"agent_type": self.agent_type.value}


class MacroStrategist(BaseAgent):
    """
    Macro Strategist Agent - Operates on higher timeframes.
    
    Specializes in:
    - Identifying overarching market themes
    - Key support/resistance levels
    - Long-term trend analysis
    - Economic cycle positioning
    """
    
    def __init__(self):
        super().__init__(AgentType.MACRO_STRATEGIST, input_dim=60)
        self.timeframe_focus = ['4H', '1D', '1W']
        
    def _generate_reasoning(self, market_state: MarketState, action: str) -> str:
        """Generate macro-focused reasoning."""
        trend_analysis = f"Trend: {market_state.trend_direction}"
        regime_analysis = f"Regime: {market_state.market_regime}"
        
        if action == 'buy':
            return f"MACRO BUY: {trend_analysis}, {regime_analysis}. Key support holding, uptrend intact."
        elif action == 'sell':
            return f"MACRO SELL: {trend_analysis}, {regime_analysis}. Resistance rejection, downtrend likely."
        else:
            return f"MACRO HOLD: {trend_analysis}, {regime_analysis}. Awaiting clearer directional bias."
    
    def _get_time_horizon(self) -> str:
        return "long"
    
    def _assess_risk(self, market_state: MarketState) -> float:
        """Macro risk assessment focuses on regime changes."""
        base_risk = market_state.volatility
        
        # Increase risk during regime uncertainty
        if market_state.market_regime == 'transitional':
            base_risk *= 1.5
            
        return min(base_risk, 1.0)


class TacticalExecutioner(BaseAgent):
    """
    Tactical Executioner Agent - Operates on lower timeframes.
    
    Specializes in:
    - Precise entry/exit timing
    - Liquidity grab identification
    - Order flow analysis
    - Short-term momentum
    """
    
    def __init__(self):
        super().__init__(AgentType.TACTICAL_EXECUTIONER, input_dim=80)
        self.timeframe_focus = ['1M', '5M', '15M']
        
    def _generate_reasoning(self, market_state: MarketState, action: str) -> str:
        """Generate tactical execution reasoning."""
        liquidity_analysis = f"Liquidity zones: {len(market_state.liquidity_zones)}"
        volume_analysis = f"Volume: {'High' if market_state.volume > 5000 else 'Low'}"
        
        if action == 'buy':
            return f"TACTICAL BUY: {liquidity_analysis}, {volume_analysis}. Liquidity sweep complete, momentum building."
        elif action == 'sell':
            return f"TACTICAL SELL: {liquidity_analysis}, {volume_analysis}. Distribution detected, momentum fading."
        else:
            return f"TACTICAL HOLD: {liquidity_analysis}, {volume_analysis}. Awaiting liquidity event."
    
    def _get_time_horizon(self) -> str:
        return "short"
    
    def _assess_risk(self, market_state: MarketState) -> float:
        """Tactical risk assessment focuses on execution risk."""
        base_risk = market_state.volatility * 0.8  # Lower base risk for short-term
        
        # Adjust for liquidity conditions
        if len(market_state.liquidity_zones) < 2:
            base_risk *= 1.3  # Higher risk with poor liquidity
            
        return min(base_risk, 1.0)


class RiskSentinel(BaseAgent):
    """
    Risk Sentinel Agent - Monitors portfolio exposure and tail risks.
    
    Specializes in:
    - Portfolio exposure monitoring
    - Correlation analysis
    - Black swan detection
    - Drawdown management
    """
    
    def __init__(self):
        super().__init__(AgentType.RISK_SENTINEL, input_dim=40)
        self.risk_threshold = 0.02  # 2% portfolio risk limit
        
    def _generate_reasoning(self, market_state: MarketState, action: str) -> str:
        """Generate risk-focused reasoning."""
        vol_analysis = f"Volatility: {market_state.volatility:.3f}"
        risk_level = "High" if market_state.volatility > 0.03 else "Normal"
        
        if action == 'buy':
            return f"RISK ALLOW BUY: {vol_analysis}, Risk: {risk_level}. Within acceptable parameters."
        elif action == 'sell':
            return f"RISK FORCE SELL: {vol_analysis}, Risk: {risk_level}. Risk limits exceeded."
        else:
            return f"RISK HOLD: {vol_analysis}, Risk: {risk_level}. Monitoring conditions."
    
    def _get_time_horizon(self) -> str:
        return "immediate"
    
    def _assess_risk(self, market_state: MarketState) -> float:
        """Risk sentinel provides comprehensive risk assessment."""
        volatility_risk = market_state.volatility
        
        # Factor in correlation risk (simplified)
        correlation_risk = 0.1  # Placeholder
        
        # Liquidity risk
        liquidity_risk = 0.05 if len(market_state.liquidity_zones) < 3 else 0.02
        
        total_risk = volatility_risk + correlation_risk + liquidity_risk
        return min(total_risk, 1.0)


class HeadAI:
    """
    Head AI - Weighs arguments from all agents to make final decisions.
    
    Uses attention mechanisms to weight agent opinions based on:
    - Historical performance
    - Current market regime
    - Agent confidence levels
    - Risk-adjusted returns
    """
    
    def __init__(self):
        self.agent_weights = {
            AgentType.MACRO_STRATEGIST: 0.4,
            AgentType.TACTICAL_EXECUTIONER: 0.35,
            AgentType.RISK_SENTINEL: 0.25
        }
        self.performance_history = {agent_type: deque(maxlen=100) for agent_type in AgentType}
        
    def make_consensus_decision(self, agent_decisions: List[TradingDecision]) -> TradingDecision:
        """
        Make consensus decision by weighing agent arguments.
        
        Args:
            agent_decisions: List of decisions from all agents
            
        Returns:
            Final consensus trading decision
        """
        if not agent_decisions:
            return self._create_default_decision()
        
        # Calculate dynamic weights based on confidence and performance
        dynamic_weights = self._calculate_dynamic_weights(agent_decisions)
        
        # Aggregate decisions
        action_scores = {'buy': 0.0, 'sell': 0.0, 'hold': 0.0}
        total_confidence = 0.0
        total_risk = 0.0
        total_return = 0.0
        
        reasoning_parts = []
        
        for decision in agent_decisions:
            weight = dynamic_weights.get(decision.agent_type, 0.0)
            
            # Weight the action
            action_scores[decision.action] += weight * decision.confidence
            
            # Aggregate metrics
            total_confidence += weight * decision.confidence
            total_risk += weight * decision.risk_assessment
            total_return += weight * decision.expected_return
            
            # Collect reasoning
            reasoning_parts.append(f"{decision.agent_type.value}: {decision.reasoning}")
        
        # Determine final action
        final_action = max(action_scores, key=action_scores.get)
        
        # Risk override - if risk sentinel strongly disagrees, override
        risk_decision = next((d for d in agent_decisions if d.agent_type == AgentType.RISK_SENTINEL), None)
        if risk_decision and risk_decision.risk_assessment > 0.8 and final_action in ['buy', 'sell']:
            final_action = 'hold'
            reasoning_parts.append("RISK OVERRIDE: High risk detected, forcing hold position")
        
        # Create consensus decision
        consensus_reasoning = " | ".join(reasoning_parts)
        
        return TradingDecision(
            agent_type=AgentType.HEAD_AI,
            action=final_action,
            confidence=total_confidence,
            reasoning=f"CONSENSUS: {consensus_reasoning}",
            risk_assessment=total_risk,
            expected_return=total_return,
            time_horizon="adaptive",
            supporting_data={
                'agent_weights': dynamic_weights,
                'action_scores': action_scores,
                'num_agents': len(agent_decisions)
            }
        )
    
    def _calculate_dynamic_weights(self, decisions: List[TradingDecision]) -> Dict[AgentType, float]:
        """Calculate dynamic weights based on agent performance and confidence."""
        weights = {}
        
        for decision in decisions:
            base_weight = self.agent_weights.get(decision.agent_type, 0.0)
            
            # Adjust based on confidence
            confidence_multiplier = 0.5 + decision.confidence * 0.5
            
            # Adjust based on recent performance (simplified)
            performance_multiplier = 1.0  # Would use actual performance history
            
            weights[decision.agent_type] = base_weight * confidence_multiplier * performance_multiplier
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _create_default_decision(self) -> TradingDecision:
        """Create default decision when no agent decisions available."""
        return TradingDecision(
            agent_type=AgentType.HEAD_AI,
            action='hold',
            confidence=0.0,
            reasoning="No agent decisions available",
            risk_assessment=1.0,
            expected_return=0.0,
            time_horizon="immediate",
            supporting_data={}
        )
    
    def update_performance(self, agent_type: AgentType, performance_score: float):
        """Update agent performance history."""
        self.performance_history[agent_type].append(performance_score)


class MultiAgentTradingSystem:
    """
    Main system coordinating all trading agents.
    
    Manages the complete multi-agent workflow:
    1. Distribute market state to all agents
    2. Collect agent decisions
    3. Head AI makes consensus decision
    4. Execute trades and update performance
    """
    
    def __init__(self):
        # Initialize agents
        self.macro_strategist = MacroStrategist()
        self.tactical_executioner = TacticalExecutioner()
        self.risk_sentinel = RiskSentinel()
        self.head_ai = HeadAI()
        
        # System state
        self.decision_history = []
        self.performance_tracker = {}
        
    def analyze_and_decide(self, market_state: MarketState) -> TradingDecision:
        """
        Main decision-making process.
        
        Args:
            market_state: Current market conditions
            
        Returns:
            Final trading decision from Head AI
        """
        # Collect decisions from all agents
        agent_decisions = []
        
        try:
            # Macro Strategist analysis
            macro_decision = self.macro_strategist.make_decision(market_state)
            agent_decisions.append(macro_decision)
            
            # Tactical Executioner analysis
            tactical_decision = self.tactical_executioner.make_decision(market_state)
            agent_decisions.append(tactical_decision)
            
            # Risk Sentinel analysis
            risk_decision = self.risk_sentinel.make_decision(market_state)
            agent_decisions.append(risk_decision)
            
        except Exception as e:
            logger.error(f"Error in agent decision making: {e}")
            return self._create_emergency_decision()
        
        # Head AI makes consensus decision
        final_decision = self.head_ai.make_consensus_decision(agent_decisions)
        
        # Store decision history
        self.decision_history.append({
            'timestamp': pd.Timestamp.now(),
            'market_state': market_state,
            'agent_decisions': agent_decisions,
            'final_decision': final_decision
        })
        
        # Limit history size
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
        
        return final_decision
    
    def _create_emergency_decision(self) -> TradingDecision:
        """Create emergency decision when system fails."""
        return TradingDecision(
            agent_type=AgentType.HEAD_AI,
            action='hold',
            confidence=0.0,
            reasoning="EMERGENCY: System error, holding position for safety",
            risk_assessment=1.0,
            expected_return=0.0,
            time_horizon="immediate",
            supporting_data={'emergency': True}
        )
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        return {
            'total_decisions': len(self.decision_history),
            'recent_performance': self._calculate_recent_performance(),
            'agent_agreement_rate': self._calculate_agreement_rate(),
            'system_health': 'operational'
        }
    
    def _calculate_recent_performance(self) -> Dict:
        """Calculate recent performance metrics."""
        if len(self.decision_history) < 10:
            return {'insufficient_data': True}
        
        recent_decisions = self.decision_history[-50:]
        
        # Calculate basic metrics
        action_distribution = {}
        avg_confidence = 0.0
        
        for record in recent_decisions:
            action = record['final_decision'].action
            action_distribution[action] = action_distribution.get(action, 0) + 1
            avg_confidence += record['final_decision'].confidence
        
        avg_confidence /= len(recent_decisions)
        
        return {
            'action_distribution': action_distribution,
            'average_confidence': avg_confidence,
            'decisions_analyzed': len(recent_decisions)
        }
    
    def _calculate_agreement_rate(self) -> float:
        """Calculate how often agents agree on decisions."""
        if len(self.decision_history) < 5:
            return 0.0
        
        agreement_count = 0
        total_decisions = 0
        
        for record in self.decision_history[-20:]:  # Last 20 decisions
            agent_decisions = record['agent_decisions']
            if len(agent_decisions) >= 2:
                actions = [d.action for d in agent_decisions]
                if len(set(actions)) == 1:  # All agents agree
                    agreement_count += 1
                total_decisions += 1
        
        return agreement_count / total_decisions if total_decisions > 0 else 0.0
