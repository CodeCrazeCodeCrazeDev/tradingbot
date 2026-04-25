"""
Hivemind Controller - AI Swarm of Ontology-Driven Agents
=========================================================

A Palantir AIP Agent Studio inspired architecture for creating and managing
swarms of intelligent agents that operate on the Financial Ontology.

Key Features:
- Ontology-Driven Agents: Agents understand and operate on semantic knowledge
- Swarm Intelligence: Collective decision-making through consensus
- Hierarchical Control: Tiered agent architecture (Ad-hoc → Automated)
- Emergent Behavior: Complex patterns from simple agent interactions
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid
import random

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized roles for ontology-driven agents"""
    # Analysis Agents
    MARKET_ANALYST = "market_analyst"
    RISK_ANALYST = "risk_analyst"
    ALPHA_HUNTER = "alpha_hunter"
    MACRO_ECONOMIST = "macro_economist"
    QUANT_RESEARCHER = "quant_researcher"
    SENTIMENT_ANALYST = "sentiment_analyst"
    
    # Execution Agents
    TRADE_EXECUTOR = "trade_executor"
    ORDER_OPTIMIZER = "order_optimizer"
    PORTFOLIO_MANAGER = "portfolio_manager"
    
    # Intelligence Agents
    PATTERN_RECOGNIZER = "pattern_recognizer"
    ANOMALY_DETECTOR = "anomaly_detector"
    REGIME_CLASSIFIER = "regime_classifier"
    CAUSAL_REASONER = "causal_reasoner"
    
    # Meta Agents
    COORDINATOR = "coordinator"
    EVALUATOR = "evaluator"
    LEARNER = "learner"
    STRATEGIST = "strategist"


class AgentTier(Enum):
    """Agent autonomy tiers (Palantir AIP inspired)"""
    TIER_1_ADHOC = 1       # Ad-hoc analysis, human-driven
    TIER_2_TASK = 2        # Task-specific, reusable
    TIER_3_AGENTIC = 3     # Agentic application, state-aware
    TIER_4_AUTOMATED = 4   # Fully automated, autonomous


class ConsensusMethod(Enum):
    """Methods for reaching swarm consensus"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    BAYESIAN_AGGREGATION = "bayesian_aggregation"
    DELPHI_METHOD = "delphi_method"
    HIERARCHICAL = "hierarchical"


@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    role: AgentRole
    tier: AgentTier
    is_active: bool = True
    current_task: Optional[str] = None
    confidence: float = 0.5
    performance_score: float = 0.5
    last_action: Optional[datetime] = None
    memory: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    """A decision made by an agent"""
    decision_id: str
    agent_id: str
    timestamp: datetime
    action: str
    target: str
    confidence: float
    reasoning: str
    supporting_evidence: List[str] = field(default_factory=list)
    ontology_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'target': self.target,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'supporting_evidence': self.supporting_evidence,
            'ontology_context': self.ontology_context,
        }


@dataclass
class SwarmConsensus:
    """Consensus reached by a swarm of agents"""
    consensus_id: str
    timestamp: datetime
    action: str
    target: str
    confidence: float
    agreement_level: float  # 0-1, how much agents agree
    participating_agents: List[str]
    individual_decisions: List[AgentDecision]
    reasoning_summary: str
    dissenting_views: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'consensus_id': self.consensus_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'target': self.target,
            'confidence': self.confidence,
            'agreement_level': self.agreement_level,
            'participating_agents': self.participating_agents,
            'individual_decisions': [d.to_dict() for d in self.individual_decisions],
            'reasoning_summary': self.reasoning_summary,
            'dissenting_views': self.dissenting_views,
        }


class OntologyDrivenAgent(ABC):
    """
    Base class for ontology-driven agents.
    
    These agents:
    1. Understand the financial ontology (objects, links, actions)
    2. Make decisions based on semantic knowledge
    3. Communicate with other agents
    4. Learn from outcomes
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        role: AgentRole = AgentRole.MARKET_ANALYST,
        tier: AgentTier = AgentTier.TIER_2_TASK,
        ontology: Optional[Any] = None,
    ):
        self.agent_id = agent_id or f"AGENT-{uuid.uuid4().hex[:8]}"
        self.role = role
        self.tier = tier
        self.ontology = ontology
        
        # Agent state
        self.state = AgentState(
            agent_id=self.agent_id,
            role=role,
            tier=tier,
        )
        
        # Communication
        self._message_queue: List[Dict[str, Any]] = []
        self._peers: Set[str] = set()
        
        # Learning
        self._decision_history: List[AgentDecision] = []
        self._outcome_history: List[Dict[str, Any]] = []
        
        # Callbacks
        self._decision_callbacks: List[Callable] = []
        
        logger.info(f"OntologyDrivenAgent created: {self.agent_id} ({role.value})")
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze context and make a decision"""
        pass
    
    @abstractmethod
    async def learn(self, outcome: Dict[str, Any]):
        """Learn from an outcome"""
        pass
    
    def query_ontology(self, query_type: str, **kwargs) -> Any:
        """Query the ontology for information"""
        if not self.ontology:
            return None
        
        if query_type == 'get_object':
            return self.ontology.get_object(kwargs.get('object_id'))
        elif query_type == 'get_related':
            return self.ontology.get_related_objects(
                kwargs.get('object_id'),
                kwargs.get('link_type'),
            )
        elif query_type == 'find_path':
            return self.ontology.find_path(
                kwargs.get('source_id'),
                kwargs.get('target_id'),
            )
        elif query_type == 'query':
            return self.ontology.query_objects(
                kwargs.get('object_type'),
                kwargs.get('properties'),
            )
        
        return None
    
    def receive_message(self, message: Dict[str, Any]):
        """Receive a message from another agent"""
        self._message_queue.append({
            **message,
            'received_at': datetime.now(timezone.utc).isoformat(),
        })
    
    def process_messages(self) -> List[Dict[str, Any]]:
        """Process pending messages"""
        messages = self._message_queue.copy()
        self._message_queue.clear()
        return messages
    
    def broadcast(self, message: Dict[str, Any], peer_ids: Optional[List[str]] = None):
        """Broadcast a message to peers (handled by controller)"""
        return {
            'from': self.agent_id,
            'to': peer_ids or list(self._peers),
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
    
    def record_decision(self, decision: AgentDecision):
        """Record a decision for learning"""
        self._decision_history.append(decision)
        
        # Trim history
        if len(self._decision_history) > 1000:
            self._decision_history = self._decision_history[-500:]
        
        # Notify callbacks
        for callback in self._decision_callbacks:
            try:
                callback(decision)
            except Exception as e:
                logger.error(f"Decision callback error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'role': self.role.value,
            'tier': self.tier.value,
            'is_active': self.state.is_active,
            'confidence': self.state.confidence,
            'performance_score': self.state.performance_score,
            'decisions_made': len(self._decision_history),
            'pending_messages': len(self._message_queue),
        }


class MarketAnalystAgent(OntologyDrivenAgent):
    """Agent specialized in market analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.MARKET_ANALYST, **kwargs)
        self.analysis_methods = ['technical', 'fundamental', 'sentiment']
    
    async def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze market context"""
        symbol = context.get('symbol', 'UNKNOWN')
        market_data = context.get('market_data', {})
        
        # Query ontology for related information
        asset_info = self.query_ontology('query', object_type='ASSET', properties={'symbol': symbol})
        
        # Perform analysis (simplified)
        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)
        trend = market_data.get('trend', 'neutral')
        
        # Generate decision
        if trend == 'bullish' and volume > market_data.get('avg_volume', 0):
            action = 'BUY'
            confidence = 0.7
            reasoning = f"Bullish trend with above-average volume for {symbol}"
        elif trend == 'bearish':
            action = 'SELL'
            confidence = 0.6
            reasoning = f"Bearish trend detected for {symbol}"
        else:
            action = 'HOLD'
            confidence = 0.5
            reasoning = f"No clear signal for {symbol}"
        
        decision = AgentDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=symbol,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=[f"Price: {price}", f"Volume: {volume}", f"Trend: {trend}"],
            ontology_context={'asset_info': str(asset_info)},
        )
        
        self.record_decision(decision)
        return decision
    
    async def learn(self, outcome: Dict[str, Any]):
        """Learn from trading outcome"""
        was_correct = outcome.get('was_correct', False)
        profit = outcome.get('profit', 0)
        
        # Adjust confidence based on outcome
        if was_correct:
            self.state.confidence = min(1.0, self.state.confidence + 0.05)
            self.state.performance_score = min(1.0, self.state.performance_score + 0.02)
        else:
            self.state.confidence = max(0.1, self.state.confidence - 0.03)
            self.state.performance_score = max(0.1, self.state.performance_score - 0.01)
        
        self._outcome_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **outcome,
        })


class RiskAnalystAgent(OntologyDrivenAgent):
    """Agent specialized in risk analysis"""
    
    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.RISK_ANALYST, **kwargs)
        self.risk_thresholds = {
            'max_position_size': 0.1,
            'max_drawdown': 0.15,
            'max_var': 0.05,
        }
    
    async def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze risk context"""
        symbol = context.get('symbol', 'UNKNOWN')
        position = context.get('position', {})
        portfolio = context.get('portfolio', {})
        
        # Calculate risk metrics
        position_size = position.get('size', 0) / portfolio.get('total_value', 1)
        volatility = context.get('volatility', 0.2)
        var = position_size * volatility * 2.33  # 99% VaR approximation
        
        # Risk assessment
        risk_score = 0
        warnings = []
        
        if position_size > self.risk_thresholds['max_position_size']:
            risk_score += 0.3
            warnings.append(f"Position size {position_size:.1%} exceeds limit")
        
        if var > self.risk_thresholds['max_var']:
            risk_score += 0.4
            warnings.append(f"VaR {var:.1%} exceeds limit")
        
        # Generate decision
        if risk_score > 0.5:
            action = 'REDUCE_RISK'
            confidence = 0.8
            reasoning = f"High risk detected: {'; '.join(warnings)}"
        elif risk_score > 0.3:
            action = 'MONITOR'
            confidence = 0.6
            reasoning = f"Elevated risk: {'; '.join(warnings)}"
        else:
            action = 'APPROVE'
            confidence = 0.7
            reasoning = f"Risk within acceptable limits for {symbol}"
        
        decision = AgentDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=symbol,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=warnings or ['All risk metrics within limits'],
            ontology_context={'risk_score': risk_score, 'var': var},
        )
        
        self.record_decision(decision)
        return decision
    
    async def learn(self, outcome: Dict[str, Any]):
        """Learn from risk outcome"""
        actual_loss = outcome.get('actual_loss', 0)
        predicted_risk = outcome.get('predicted_risk', 0)
        
        # Calibrate risk thresholds based on outcomes
        if actual_loss > predicted_risk * 1.5:
            # Underestimated risk, be more conservative
            for key in self.risk_thresholds:
                self.risk_thresholds[key] *= 0.95
        elif actual_loss < predicted_risk * 0.5:
            # Overestimated risk, can be slightly less conservative
            for key in self.risk_thresholds:
                self.risk_thresholds[key] = min(self.risk_thresholds[key] * 1.02, 0.2)


class AlphaHunterAgent(OntologyDrivenAgent):
    """Agent specialized in finding alpha opportunities"""
    
    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.ALPHA_HUNTER, **kwargs)
        self.alpha_sources = ['momentum', 'mean_reversion', 'arbitrage', 'event_driven']
    
    async def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Hunt for alpha opportunities"""
        symbol = context.get('symbol', 'UNKNOWN')
        market_data = context.get('market_data', {})
        
        # Look for alpha signals
        alpha_signals = []
        total_alpha = 0
        
        # Momentum alpha
        returns = market_data.get('returns', [])
        if returns and len(returns) >= 5:
            momentum = sum(returns[-5:])
            if abs(momentum) > 0.02:
                alpha_signals.append(f"Momentum: {momentum:.2%}")
                total_alpha += momentum * 0.3
        
        # Mean reversion alpha
        price = market_data.get('price', 0)
        ma_20 = market_data.get('ma_20', price)
        deviation = (price - ma_20) / ma_20 if ma_20 else 0
        if abs(deviation) > 0.03:
            alpha_signals.append(f"Mean reversion: {deviation:.2%} from MA20")
            total_alpha -= deviation * 0.2  # Negative because we expect reversion
        
        # Generate decision
        if total_alpha > 0.01:
            action = 'BUY'
            confidence = min(0.9, 0.5 + abs(total_alpha) * 5)
            reasoning = f"Positive alpha detected: {total_alpha:.2%}"
        elif total_alpha < -0.01:
            action = 'SELL'
            confidence = min(0.9, 0.5 + abs(total_alpha) * 5)
            reasoning = f"Negative alpha detected: {total_alpha:.2%}"
        else:
            action = 'NO_ALPHA'
            confidence = 0.5
            reasoning = "No significant alpha opportunity"
        
        decision = AgentDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=symbol,
            confidence=confidence,
            reasoning=reasoning,
            supporting_evidence=alpha_signals or ['No alpha signals'],
            ontology_context={'total_alpha': total_alpha},
        )
        
        self.record_decision(decision)
        return decision
    
    async def learn(self, outcome: Dict[str, Any]):
        """Learn from alpha hunting outcome"""
        realized_alpha = outcome.get('realized_alpha', 0)
        predicted_alpha = outcome.get('predicted_alpha', 0)
        
        # Track alpha prediction accuracy
        self._outcome_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'predicted': predicted_alpha,
            'realized': realized_alpha,
            'error': abs(predicted_alpha - realized_alpha),
        })


class CausalReasonerAgent(OntologyDrivenAgent):
    """Agent specialized in causal reasoning and understanding"""
    
    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.CAUSAL_REASONER, **kwargs)
        self.causal_models = {}
    
    async def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Perform causal analysis"""
        symbol = context.get('symbol', 'UNKNOWN')
        events = context.get('events', [])
        
        # Query ontology for causal relationships
        causal_links = []
        if self.ontology:
            asset = self.query_ontology('query', object_type='ASSET', properties={'symbol': symbol})
            if asset:
                for obj in asset:
                    related = self.query_ontology('get_related', object_id=obj.object_id, link_type='CAUSES')
                    causal_links.extend(related or [])
        
        # Analyze causal chains
        causal_factors = []
        impact_score = 0
        
        for event in events:
            event_type = event.get('type', 'unknown')
            magnitude = event.get('magnitude', 0)
            
            # Simple causal reasoning
            if event_type == 'earnings':
                if magnitude > 0:
                    causal_factors.append(f"Positive earnings surprise → Price increase expected")
                    impact_score += magnitude * 0.5
                else:
                    causal_factors.append(f"Negative earnings surprise → Price decrease expected")
                    impact_score += magnitude * 0.5
            
            elif event_type == 'fed_decision':
                if magnitude > 0:  # Rate hike
                    causal_factors.append(f"Rate hike → Equity pressure expected")
                    impact_score -= 0.1
                else:
                    causal_factors.append(f"Rate cut → Equity support expected")
                    impact_score += 0.1
        
        # Generate decision with causal explanation
        if impact_score > 0.05:
            action = 'BULLISH_CAUSE'
            reasoning = f"Causal analysis suggests positive impact: {impact_score:.2%}"
        elif impact_score < -0.05:
            action = 'BEARISH_CAUSE'
            reasoning = f"Causal analysis suggests negative impact: {impact_score:.2%}"
        else:
            action = 'NEUTRAL_CAUSE'
            reasoning = "No significant causal factors identified"
        
        decision = AgentDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=symbol,
            confidence=0.6 + abs(impact_score),
            reasoning=reasoning,
            supporting_evidence=causal_factors or ['No causal factors'],
            ontology_context={'impact_score': impact_score, 'causal_links': len(causal_links)},
        )
        
        self.record_decision(decision)
        return decision
    
    async def learn(self, outcome: Dict[str, Any]):
        """Learn causal relationships from outcomes"""
        predicted_cause = outcome.get('predicted_cause')
        actual_effect = outcome.get('actual_effect')
        
        if predicted_cause and actual_effect:
            # Update causal model
            if predicted_cause not in self.causal_models:
                self.causal_models[predicted_cause] = {'correct': 0, 'total': 0}
            
            self.causal_models[predicted_cause]['total'] += 1
            if outcome.get('was_correct'):
                self.causal_models[predicted_cause]['correct'] += 1


class AgentSwarm:
    """
    A swarm of ontology-driven agents that work together.
    
    Features:
    - Parallel analysis by multiple agents
    - Consensus building through various methods
    - Emergent intelligence from agent interactions
    - Adaptive agent weights based on performance
    """
    
    def __init__(
        self,
        swarm_id: Optional[str] = None,
        consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_AVERAGE,
        ontology: Optional[Any] = None,
    ):
        self.swarm_id = swarm_id or f"SWARM-{uuid.uuid4().hex[:8]}"
        self.consensus_method = consensus_method
        self.ontology = ontology
        
        # Agents
        self.agents: Dict[str, OntologyDrivenAgent] = {}
        self.agent_weights: Dict[str, float] = {}
        
        # History
        self.consensus_history: List[SwarmConsensus] = []
        
        logger.info(f"AgentSwarm created: {self.swarm_id}")
    
    def add_agent(self, agent: OntologyDrivenAgent, weight: float = 1.0):
        """Add an agent to the swarm"""
        agent.ontology = self.ontology
        self.agents[agent.agent_id] = agent
        self.agent_weights[agent.agent_id] = weight
        
        # Register as peer to other agents
        for other_id in self.agents:
            if other_id != agent.agent_id:
                agent._peers.add(other_id)
                self.agents[other_id]._peers.add(agent.agent_id)
    
    def remove_agent(self, agent_id: str):
        """Remove an agent from the swarm"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_weights[agent_id]
            
            # Remove from peer lists
            for agent in self.agents.values():
                agent._peers.discard(agent_id)
    
    async def analyze(self, context: Dict[str, Any]) -> SwarmConsensus:
        """Have all agents analyze and reach consensus"""
        if not self.agents:
            raise ValueError("No agents in swarm")
        
        # Parallel analysis
        tasks = [agent.analyze(context) for agent in self.agents.values()]
        decisions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid decisions
        valid_decisions: List[AgentDecision] = []
        for decision in decisions:
            if isinstance(decision, AgentDecision):
                valid_decisions.append(decision)
            elif isinstance(decision, Exception):
                logger.warning(f"Agent error: {decision}")
        
        if not valid_decisions:
            raise ValueError("No valid decisions from agents")
        
        # Facilitate communication
        await self._facilitate_communication(valid_decisions)
        
        # Build consensus
        consensus = self._build_consensus(valid_decisions)
        
        self.consensus_history.append(consensus)
        
        # Trim history
        if len(self.consensus_history) > 500:
            self.consensus_history = self.consensus_history[-250:]
        
        return consensus
    
    async def _facilitate_communication(self, decisions: List[AgentDecision]):
        """Allow agents to share their decisions"""
        for decision in decisions:
            message = {
                'type': 'share_decision',
                'decision': decision.to_dict(),
            }
            
            for agent in self.agents.values():
                if agent.agent_id != decision.agent_id:
                    agent.receive_message(message)
        
        # Process messages
        for agent in self.agents.values():
            agent.process_messages()
    
    def _build_consensus(self, decisions: List[AgentDecision]) -> SwarmConsensus:
        """Build consensus from individual decisions"""
        if self.consensus_method == ConsensusMethod.MAJORITY_VOTE:
            return self._majority_vote_consensus(decisions)
        elif self.consensus_method == ConsensusMethod.WEIGHTED_AVERAGE:
            return self._weighted_average_consensus(decisions)
        elif self.consensus_method == ConsensusMethod.BAYESIAN_AGGREGATION:
            return self._bayesian_consensus(decisions)
        else:
            return self._weighted_average_consensus(decisions)
    
    def _majority_vote_consensus(self, decisions: List[AgentDecision]) -> SwarmConsensus:
        """Simple majority vote"""
        action_votes: Dict[str, int] = {}
        
        for decision in decisions:
            action_votes[decision.action] = action_votes.get(decision.action, 0) + 1
        
        winning_action = max(action_votes, key=action_votes.get)
        agreement = action_votes[winning_action] / len(decisions)
        
        # Get decisions for winning action
        winning_decisions = [d for d in decisions if d.action == winning_action]
        avg_confidence = sum(d.confidence for d in winning_decisions) / len(winning_decisions)
        
        # Get dissenting views
        dissenting = [d.reasoning for d in decisions if d.action != winning_action]
        
        return SwarmConsensus(
            consensus_id=f"CONS-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            action=winning_action,
            target=decisions[0].target,
            confidence=avg_confidence * agreement,
            agreement_level=agreement,
            participating_agents=[d.agent_id for d in decisions],
            individual_decisions=decisions,
            reasoning_summary=f"Majority ({action_votes[winning_action]}/{len(decisions)}) voted {winning_action}",
            dissenting_views=dissenting[:3],
        )
    
    def _weighted_average_consensus(self, decisions: List[AgentDecision]) -> SwarmConsensus:
        """Weighted average based on agent performance"""
        # Map actions to numeric values
        action_values = {
            'BUY': 1.0, 'BULLISH_CAUSE': 0.8, 'APPROVE': 0.5,
            'HOLD': 0.0, 'NEUTRAL_CAUSE': 0.0, 'NO_ALPHA': 0.0, 'MONITOR': 0.0,
            'SELL': -1.0, 'BEARISH_CAUSE': -0.8, 'REDUCE_RISK': -0.5,
        }
        
        total_weight = 0
        weighted_sum = 0
        weighted_confidence = 0
        
        for decision in decisions:
            agent_weight = self.agent_weights.get(decision.agent_id, 1.0)
            performance = self.agents[decision.agent_id].state.performance_score
            weight = agent_weight * performance * decision.confidence
            
            action_value = action_values.get(decision.action, 0)
            weighted_sum += action_value * weight
            weighted_confidence += decision.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            total_weight = 1
        
        avg_value = weighted_sum / total_weight
        avg_confidence = weighted_confidence / total_weight
        
        # Determine action from average value
        if avg_value > 0.3:
            action = 'BUY'
        elif avg_value < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Calculate agreement
        values = [action_values.get(d.action, 0) for d in decisions]
        variance = sum((v - avg_value) ** 2 for v in values) / len(values) if values else 0
        agreement = max(0, 1 - variance)
        
        return SwarmConsensus(
            consensus_id=f"CONS-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=decisions[0].target,
            confidence=avg_confidence,
            agreement_level=agreement,
            participating_agents=[d.agent_id for d in decisions],
            individual_decisions=decisions,
            reasoning_summary=f"Weighted consensus: {avg_value:.2f} → {action}",
            dissenting_views=[d.reasoning for d in decisions if action_values.get(d.action, 0) * avg_value < 0][:3],
        )
    
    def _bayesian_consensus(self, decisions: List[AgentDecision]) -> SwarmConsensus:
        """Bayesian aggregation of agent beliefs"""
        # Simplified Bayesian aggregation
        # P(action | all_decisions) ∝ ∏ P(decision_i | action) * P(action)
        
        actions = set(d.action for d in decisions)
        action_probs: Dict[str, float] = {}
        
        for action in actions:
            # Prior (uniform)
            prob = 1.0 / len(actions)
            
            # Likelihood from each agent
            for decision in decisions:
                if decision.action == action:
                    prob *= decision.confidence
                else:
                    prob *= (1 - decision.confidence) / (len(actions) - 1)
            
            action_probs[action] = prob
        
        # Normalize
        total_prob = sum(action_probs.values())
        if total_prob > 0:
            action_probs = {a: p / total_prob for a, p in action_probs.items()}
        
        # Select action with highest probability
        best_action = max(action_probs, key=action_probs.get)
        confidence = action_probs[best_action]
        
        return SwarmConsensus(
            consensus_id=f"CONS-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            action=best_action,
            target=decisions[0].target,
            confidence=confidence,
            agreement_level=confidence,
            participating_agents=[d.agent_id for d in decisions],
            individual_decisions=decisions,
            reasoning_summary=f"Bayesian consensus: P({best_action}) = {confidence:.2%}",
            dissenting_views=[d.reasoning for d in decisions if d.action != best_action][:3],
        )
    
    async def learn_from_outcome(self, outcome: Dict[str, Any]):
        """Have all agents learn from an outcome"""
        tasks = [agent.learn(outcome) for agent in self.agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update agent weights based on performance
        for agent_id, agent in self.agents.items():
            self.agent_weights[agent_id] = agent.state.performance_score
    
    def get_status(self) -> Dict[str, Any]:
        """Get swarm status"""
        return {
            'swarm_id': self.swarm_id,
            'consensus_method': self.consensus_method.value,
            'agent_count': len(self.agents),
            'consensus_count': len(self.consensus_history),
            'agents': {aid: agent.get_status() for aid, agent in self.agents.items()},
            'agent_weights': self.agent_weights,
        }


class HivemindController:
    """
    Master controller for the AI Hivemind.
    
    Manages multiple swarms, coordinates inter-swarm communication,
    and provides the interface for the higher-level system.
    """
    
    def __init__(
        self,
        controller_id: Optional[str] = None,
        ontology: Optional[Any] = None,
    ):
        self.controller_id = controller_id or f"HIVE-{uuid.uuid4().hex[:8]}"
        self.ontology = ontology
        
        # Swarms
        self.swarms: Dict[str, AgentSwarm] = {}
        
        # Global state
        self.is_active = False
        self.total_decisions = 0
        
        # Initialize default swarms
        self._initialize_default_swarms()
        
        logger.info(f"HivemindController created: {self.controller_id}")
    
    def _initialize_default_swarms(self):
        """Initialize default agent swarms"""
        # Market Analysis Swarm
        market_swarm = AgentSwarm(
            swarm_id="SWARM-MARKET",
            consensus_method=ConsensusMethod.WEIGHTED_AVERAGE,
            ontology=self.ontology,
        )
        market_swarm.add_agent(MarketAnalystAgent(agent_id="AGENT-MKT-1"))
        market_swarm.add_agent(MarketAnalystAgent(agent_id="AGENT-MKT-2"))
        market_swarm.add_agent(AlphaHunterAgent(agent_id="AGENT-ALPHA-1"))
        self.swarms['market'] = market_swarm
        
        # Risk Analysis Swarm
        risk_swarm = AgentSwarm(
            swarm_id="SWARM-RISK",
            consensus_method=ConsensusMethod.MAJORITY_VOTE,
            ontology=self.ontology,
        )
        risk_swarm.add_agent(RiskAnalystAgent(agent_id="AGENT-RISK-1"))
        risk_swarm.add_agent(RiskAnalystAgent(agent_id="AGENT-RISK-2"))
        self.swarms['risk'] = risk_swarm
        
        # Intelligence Swarm
        intel_swarm = AgentSwarm(
            swarm_id="SWARM-INTEL",
            consensus_method=ConsensusMethod.BAYESIAN_AGGREGATION,
            ontology=self.ontology,
        )
        intel_swarm.add_agent(CausalReasonerAgent(agent_id="AGENT-CAUSAL-1"))
        intel_swarm.add_agent(AlphaHunterAgent(agent_id="AGENT-ALPHA-2"))
        self.swarms['intelligence'] = intel_swarm
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, SwarmConsensus]:
        """Have all swarms analyze in parallel"""
        self.is_active = True
        
        tasks = {
            swarm_name: swarm.analyze(context)
            for swarm_name, swarm in self.swarms.items()
        }
        
        results = {}
        for swarm_name, task in tasks.items():
            try:
                results[swarm_name] = await task
            except Exception as e:
                logger.error(f"Swarm {swarm_name} error: {e}")
        
        self.total_decisions += 1
        
        return results
    
    async def get_unified_decision(self, context: Dict[str, Any]) -> SwarmConsensus:
        """Get a unified decision from all swarms"""
        swarm_results = await self.analyze(context)
        
        # Combine all individual decisions
        all_decisions = []
        for consensus in swarm_results.values():
            all_decisions.extend(consensus.individual_decisions)
        
        # Create meta-consensus
        action_scores: Dict[str, float] = {}
        for consensus in swarm_results.values():
            action = consensus.action
            score = consensus.confidence * consensus.agreement_level
            action_scores[action] = action_scores.get(action, 0) + score
        
        best_action = max(action_scores, key=action_scores.get)
        total_score = sum(action_scores.values())
        confidence = action_scores[best_action] / total_score if total_score > 0 else 0
        
        return SwarmConsensus(
            consensus_id=f"META-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            action=best_action,
            target=context.get('symbol', 'UNKNOWN'),
            confidence=confidence,
            agreement_level=confidence,
            participating_agents=[d.agent_id for d in all_decisions],
            individual_decisions=all_decisions,
            reasoning_summary=f"Meta-consensus from {len(swarm_results)} swarms: {best_action}",
            dissenting_views=[],
        )
    
    async def learn_from_outcome(self, outcome: Dict[str, Any]):
        """Have all swarms learn from an outcome"""
        tasks = [swarm.learn_from_outcome(outcome) for swarm in self.swarms.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def add_swarm(self, swarm_name: str, swarm: AgentSwarm):
        """Add a swarm to the controller"""
        swarm.ontology = self.ontology
        self.swarms[swarm_name] = swarm
    
    def get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        total_agents = sum(len(s.agents) for s in self.swarms.values())
        
        return {
            'controller_id': self.controller_id,
            'is_active': self.is_active,
            'swarm_count': len(self.swarms),
            'total_agents': total_agents,
            'total_decisions': self.total_decisions,
            'swarms': {name: swarm.get_status() for name, swarm in self.swarms.items()},
        }
