"""
Master Orchestrator - DeepMind Hierarchical Control Pattern

Inspired by:
- DeepMind's AlphaGo: Hierarchical decision making with policy/value evaluation
- DeepMind's MuZero: Model-based planning with learned dynamics
- OpenAI's GPT-4: Unified orchestration with tool dispatch

This is the single source of truth for all agent coordination.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class DecisionPriority(Enum):
    """Priority levels for decisions - inspired by AlphaGo's move ordering"""
    CRITICAL = 1      # Safety-critical, must execute immediately
    HIGH = 2          # High-value opportunities
    MEDIUM = 3        # Standard operations
    LOW = 4           # Background tasks
    EXPLORATORY = 5   # Exploration/research


class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    LEARNING = "learning"
    SAFETY_HOLD = "safety_hold"
    SHUTDOWN = "shutdown"


@dataclass
class Decision:
    """
    A decision in the system - inspired by AlphaGo's move representation.
    
    Contains both the action (policy) and its expected value (value network).
    """
    decision_id: str
    decision_type: str
    
    # Policy Network output (what to do)
    action: Dict[str, Any]
    action_probabilities: Dict[str, float]  # Distribution over possible actions
    
    # Value Network output (how good is it)
    expected_value: float  # V(s) - expected outcome
    confidence: float      # How certain we are
    
    # Constitutional AI checks
    safety_score: float    # 0-1, must be > threshold
    constitutional_violations: List[str]
    
    # Reasoning trace (ReAct pattern)
    reasoning_chain: List[str]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source_agent: Optional[str] = None
    priority: DecisionPriority = DecisionPriority.MEDIUM
    
    # Execution tracking
    executed: bool = False
    execution_result: Optional[Dict] = None
    
    def is_safe(self, threshold: float = 0.7) -> bool:
        """Check if decision passes safety threshold"""
        return self.safety_score >= threshold and len(self.constitutional_violations) == 0


@dataclass
class SystemContext:
    """Current system context - the 'state' in RL terms"""
    timestamp: datetime
    market_state: Dict[str, Any]
    portfolio_state: Dict[str, Any]
    agent_states: Dict[str, Any]
    pending_decisions: List[Decision]
    recent_outcomes: List[Dict]
    risk_metrics: Dict[str, float]
    
    def to_feature_vector(self) -> List[float]:
        """Convert context to feature vector for neural networks"""
        # This would be implemented with actual feature extraction
        features = []
        # Market features
        features.extend([
            self.market_state.get('price', 0),
            self.market_state.get('volatility', 0),
            self.market_state.get('trend', 0),
        ])
        # Portfolio features
        features.extend([
            self.portfolio_state.get('equity', 0),
            self.portfolio_state.get('exposure', 0),
            self.portfolio_state.get('pnl', 0),
        ])
        # Risk features
        features.extend([
            self.risk_metrics.get('var', 0),
            self.risk_metrics.get('sharpe', 0),
        ])
        return features


class MasterOrchestrator:
    """
    Master Orchestrator - The brain of the system.
    
    Implements a hierarchical control pattern inspired by:
    1. DeepMind's AlphaGo: Policy network (what to do) + Value network (how good)
    2. DeepMind's MuZero: Model-based planning with learned world model
    3. OpenAI's GPT-4: ReAct loop with tool dispatch
    4. Anthropic's Constitutional AI: Safety verification at every step
    
    Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    MASTER ORCHESTRATOR                       │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
    │  │   Policy    │  │   Value     │  │   Constitutional    │ │
    │  │   Network   │  │   Network   │  │   Safety Layer      │ │
    │  │  (Action)   │  │  (Eval)     │  │   (Verification)    │ │
    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
    │         │                │                     │            │
    │         └────────────────┼─────────────────────┘            │
    │                          ▼                                   │
    │              ┌───────────────────────┐                      │
    │              │    Decision Fusion    │                      │
    │              │  (MCTS-style search)  │                      │
    │              └───────────┬───────────┘                      │
    │                          ▼                                   │
    │              ┌───────────────────────┐                      │
    │              │   Execution Engine    │                      │
    │              └───────────────────────┘                      │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Core components (will be injected)
        self.policy_network = None      # What action to take
        self.value_network = None       # How good is the state
        self.constitutional_layer = None # Safety verification
        self.react_loop = None          # Reasoning engine
        self.agent_registry = None      # All agents
        self.tool_registry = None       # All tools
        self.memory_system = None       # Unified memory
        
        # State management
        self.state = SystemState.INITIALIZING
        self.current_context: Optional[SystemContext] = None
        
        # Decision tracking
        self.decision_queue: List[Decision] = []
        self.decision_history: List[Decision] = []
        self.max_history = self.config.get('max_history', 10000)
        
        # MCTS-style search parameters (AlphaGo pattern)
        self.search_depth = self.config.get('search_depth', 5)
        self.exploration_constant = self.config.get('exploration_constant', 1.41)  # sqrt(2)
        self.num_simulations = self.config.get('num_simulations', 100)
        
        # Safety thresholds (Constitutional AI pattern)
        self.safety_threshold = self.config.get('safety_threshold', 0.7)
        self.max_risk_per_decision = self.config.get('max_risk', 0.02)  # 2% max risk
        
        # Async coordination
        self.running = False
        self._lock = asyncio.Lock()
        
        logger.info("Master Orchestrator initialized")
    
    def inject_dependencies(
        self,
        policy_network,
        value_network,
        constitutional_layer,
        react_loop,
        agent_registry,
        tool_registry,
        memory_system
    ):
        """Inject all dependencies - enables testing and modularity"""
        self.policy_network = policy_network
        self.value_network = value_network
        self.constitutional_layer = constitutional_layer
        self.react_loop = react_loop
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.memory_system = memory_system
        
        logger.info("Dependencies injected into Master Orchestrator")
    
    async def initialize(self):
        """Initialize the orchestrator and all subsystems"""
        logger.info("=" * 60)
        logger.info("INITIALIZING MASTER ORCHESTRATOR")
        logger.info("=" * 60)
        
        # Initialize subsystems
        if self.memory_system:
            await self.memory_system.initialize()
        if self.agent_registry:
            await self.agent_registry.initialize()
        if self.tool_registry:
            await self.tool_registry.initialize()
        if self.policy_network:
            await self.policy_network.initialize()
        if self.value_network:
            await self.value_network.initialize()
        if self.constitutional_layer:
            await self.constitutional_layer.initialize()
        
        self.state = SystemState.READY
        self.running = True
        
        logger.info("Master Orchestrator READY")
    
    async def think(self, context: SystemContext) -> Decision:
        """
        Main thinking loop - AlphaGo + ReAct + Constitutional AI fusion.
        
        This implements the core decision-making process:
        1. Generate candidate actions (Policy Network)
        2. Evaluate each action (Value Network)
        3. Search for best action (MCTS-style)
        4. Verify safety (Constitutional AI)
        5. Generate reasoning trace (ReAct)
        
        Args:
            context: Current system state
            
        Returns:
            Best decision after search and verification
        """
        self.state = SystemState.PLANNING
        self.current_context = context
        
        # Step 1: Generate candidate actions using Policy Network
        # (Like AlphaGo's policy network suggesting moves)
        candidate_actions = await self._generate_candidate_actions(context)
        
        # Step 2: Evaluate each candidate using Value Network
        # (Like AlphaGo's value network estimating win probability)
        evaluated_candidates = await self._evaluate_candidates(context, candidate_actions)
        
        # Step 3: MCTS-style search to find best action
        # (Like AlphaGo's Monte Carlo Tree Search)
        best_action = await self._mcts_search(context, evaluated_candidates)
        
        # Step 4: Constitutional AI verification
        # (Like Anthropic's multi-stage safety checks)
        # Ensure best_action has required fields for verification
        if 'type' not in best_action:
            best_action['type'] = best_action.get('decision_type', 'unknown')
        if 'action' not in best_action:
            best_action['action'] = {}

        verified_action = await self._constitutional_verify(best_action)
        
        # Step 5: Generate reasoning trace (ReAct pattern)
        # (Like GPT-4's chain-of-thought reasoning)
        reasoning_chain = await self._generate_reasoning(context, verified_action)
        
        # Create final decision
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            decision_type=verified_action.get('type', 'unknown'),
            action=verified_action.get('action', {}),
            action_probabilities=verified_action.get('probabilities', {}),
            expected_value=verified_action.get('value', 0.5),
            confidence=verified_action.get('confidence', 0.5),
            safety_score=verified_action.get('safety_score', 0.5),
            safety_score=verified_action.get('safety_score', 0.8),
            constitutional_violations=verified_action.get('violations', []),
            reasoning_chain=reasoning_chain,
            source_agent=verified_action.get('source_agent'),
            priority=self._determine_priority(verified_action)
        )
        
        # Store in memory
        if self.memory_system:
            await self.memory_system.store_decision(decision)
        
        self.state = SystemState.READY
        return decision
    
    async def _generate_candidate_actions(
        self, 
        context: SystemContext
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate actions using Policy Network.
        
        Inspired by AlphaGo's policy network that outputs a probability
        distribution over all legal moves.
        """
        candidates = []
        
        # Get policy network suggestions
        if self.policy_network:
            policy_output = await self.policy_network.predict(context)
            # Handle both object (PolicyOutput) and dictionary formats
            if hasattr(policy_output, 'actions'):
                candidates.extend(policy_output.actions)
            elif isinstance(policy_output, dict) and 'actions' in policy_output:
                candidates.extend(policy_output['actions'])
        
        # Get suggestions from registered agents
        if self.agent_registry:
            agent_suggestions = await self.agent_registry.get_all_proposals(context)
            candidates.extend(agent_suggestions)
        
        # Retrieve relevant past actions from memory
        if self.memory_system:
            try:
                similar_situations = await self.memory_system.retrieve_similar(context, k=5)
                for situation in similar_situations:
                    if not isinstance(situation, dict):
                        continue
                    outcome = situation.get('outcome')
                    if outcome and outcome.get('success', False):
                        candidates.append({
                            'type': 'memory_replay',
                            'action': situation.get('action', {}),
                            'source': 'episodic_memory',
                            'historical_success': outcome.get('value', 0.5)
                        })
            except Exception as e:
                logger.error(f"Error retrieving similar situations: {e}")
        
        # Always include a "do nothing" option (important for safety)
        candidates.append({
            'type': 'hold',
            'action': {'operation': 'no_action'},
            'source': 'default',
            'probability': 0.1
        })
        
        logger.debug(f"Generated {len(candidates)} candidate actions")
        return candidates
    
    async def _evaluate_candidates(
        self,
        context: SystemContext,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate each candidate action using Value Network.
        
        Inspired by AlphaGo's value network that estimates the probability
        of winning from a given position.
        """
        evaluated = []
        
        for candidate in candidates:
            if candidate is None:
                continue
            # Simulate the action to get next state
            simulated_state = await self._simulate_action(context, candidate)
            
            # Get value network evaluation
            if self.value_network:
                value = await self.value_network.evaluate(simulated_state)
            else:
                value = candidate.get('historical_success', 0.5)
            
            # Calculate confidence based on uncertainty
            confidence = self._calculate_confidence(candidate, value)
            
            evaluated.append({
                **candidate,
                'value': value,
                'confidence': confidence,
                'simulated_state': simulated_state
            })
        
        # Sort by expected value (descending)
        evaluated.sort(key=lambda x: x['value'], reverse=True)
        
        return evaluated
    
    async def _simulate_action(
        self,
        context: SystemContext,
        action: Dict[str, Any]
    ) -> SystemContext:
        """
        Simulate an action to predict next state.
        
        Inspired by MuZero's learned dynamics model that predicts
        the next state given current state and action.
        """
        # Create a copy of context
        simulated = SystemContext(
            timestamp=datetime.now(),
            market_state=context.market_state.copy(),
            portfolio_state=context.portfolio_state.copy(),
            agent_states=context.agent_states.copy(),
            pending_decisions=context.pending_decisions.copy(),
            recent_outcomes=context.recent_outcomes.copy(),
            risk_metrics=context.risk_metrics.copy()
        )
        
        # Apply action effects (simplified simulation)
        action_type = action.get('type', 'unknown')
        
        if action_type == 'trade':
            # Simulate trade impact
            trade_size = action.get('action', {}).get('size', 0)
            simulated.portfolio_state['exposure'] += trade_size
            simulated.risk_metrics['var'] *= (1 + abs(trade_size) * 0.1)
            
        elif action_type == 'risk_adjustment':
            # Simulate risk adjustment
            adjustment = action.get('action', {}).get('adjustment', 0)
            simulated.risk_metrics['var'] *= (1 - adjustment)
            
        return simulated
    
    async def _mcts_search(
        self,
        context: SystemContext,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        MCTS-style search to find the best action.
        
        Inspired by AlphaGo's Monte Carlo Tree Search that combines:
        - Prior probability from policy network (exploitation)
        - UCB exploration bonus (exploration)
        - Value estimates from simulations
        
        Simplified version for trading (not full MCTS tree).
        """
        if not candidates:
            return {
                'type': 'hold',
                'action': {'operation': 'no_action'},
                'value': 0.5,
                'confidence': 1.0,
                'safety_score': 1.0
            }
        
        # UCB1 formula: value + c * sqrt(ln(N) / n)
        # Where N = total visits, n = visits to this node, c = exploration constant
        
        visit_counts = {i: 1 for i in range(len(candidates))}
        total_visits = len(candidates)
        value_sums = {i: c['value'] for i, c in enumerate(candidates)}
        
        # Run simulations
        for _ in range(self.num_simulations):
            # Select action using UCB
            ucb_scores = []
            for i, candidate in enumerate(candidates):
                exploitation = value_sums[i] / visit_counts[i]
                exploration = self.exploration_constant * (
                    (total_visits ** 0.5) / visit_counts[i]
                ) ** 0.5
                ucb_scores.append(exploitation + exploration)
            
            # Select best UCB action
            best_idx = ucb_scores.index(max(ucb_scores))
            
            # Simulate and get value
            simulated_state = await self._simulate_action(context, candidates[best_idx])
            if self.value_network:
                value = await self.value_network.evaluate(simulated_state)
            else:
                value = candidates[best_idx]['value']
            
            # Update statistics
            visit_counts[best_idx] += 1
            value_sums[best_idx] += value
            total_visits += 1
        
        # Select action with highest average value
        avg_values = {i: value_sums[i] / visit_counts[i] for i in range(len(candidates))}
        best_idx = max(avg_values, key=avg_values.get)
        
        best_candidate = candidates[best_idx]
        best_candidate['value'] = avg_values[best_idx]
        best_candidate['visit_count'] = visit_counts[best_idx]
        
        logger.debug(f"MCTS selected action with value {best_candidate['value']:.3f}")
        
        return best_candidate
    
    async def _constitutional_verify(
        self,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constitutional AI verification.
        
        Inspired by Anthropic's Constitutional AI that:
        1. Checks action against constitutional principles
        2. Critiques and revises if violations found
        3. Ensures safety constraints are met
        
        Returns action with safety score and any violations.
        """
        if not self.constitutional_layer:
            # Default safe if no constitutional layer
            action['safety_score'] = 0.8
            action['violations'] = []
            return action
        
        # Run constitutional checks
        verification_result = await self.constitutional_layer.verify(action)
        
        action['safety_score'] = verification_result['safety_score']
        action['violations'] = verification_result['violations']
        
        # If violations found, attempt revision (Constitutional AI pattern)
        if verification_result['violations']:
            logger.warning(f"Constitutional violations found: {verification_result['violations']}")
            
            # Attempt to revise action
            revised_action = await self.constitutional_layer.revise(
                action, 
                verification_result['violations']
            )
            
            if revised_action:
                # Re-verify revised action
                re_verification = await self.constitutional_layer.verify(revised_action)
                if re_verification['safety_score'] > action['safety_score']:
                    action = revised_action
                    action['safety_score'] = re_verification['safety_score']
                    action['violations'] = re_verification['violations']
                    action['revised'] = True
        
        return action
    
    async def _generate_reasoning(
        self,
        context: SystemContext,
        action: Dict[str, Any]
    ) -> List[str]:
        """
        Generate reasoning trace using ReAct pattern.
        
        Inspired by OpenAI's ReAct (Reasoning + Acting) that produces:
        - Thought: What the agent is thinking
        - Action: What action to take
        - Observation: What was observed
        
        This creates an interpretable chain of reasoning.
        """
        reasoning = []
        
        # Thought 1: Situation assessment
        reasoning.append(
            f"THOUGHT: Current market state shows "
            f"volatility={context.market_state.get('volatility', 'unknown')}, "
            f"trend={context.market_state.get('trend', 'unknown')}. "
            f"Portfolio exposure is {context.portfolio_state.get('exposure', 0):.2%}."
        )
        
        # Thought 2: Action consideration
        reasoning.append(
            f"THOUGHT: Considering action '{action['type']}' with "
            f"expected value {action.get('value', 0):.3f} and "
            f"confidence {action.get('confidence', 0):.2%}."
        )
        
        # Thought 3: Risk assessment
        reasoning.append(
            f"THOUGHT: Safety score is {action.get('safety_score', 0):.2f}. "
            f"Risk metrics show VaR={context.risk_metrics.get('var', 0):.4f}."
        )
        
        # Action declaration
        reasoning.append(
            f"ACTION: Execute {action['type']} - {action.get('action', {})}"
        )
        
        # Expected observation
        reasoning.append(
            f"EXPECTED_OBSERVATION: Anticipate outcome with "
            f"value={action.get('value', 0):.3f} based on "
            f"{action.get('visit_count', 1)} simulations."
        )
        
        return reasoning
    
    def _calculate_confidence(
        self,
        candidate: Dict[str, Any],
        value: float
    ) -> float:
        """Calculate confidence in a candidate action"""
        base_confidence = 0.5
        
        # Higher value = higher confidence
        base_confidence += value * 0.3
        
        # Memory-based actions have historical confidence
        if candidate.get('source') == 'episodic_memory':
            base_confidence += 0.1
        
        # Policy network suggestions have prior confidence
        if 'probability' in candidate:
            base_confidence += candidate['probability'] * 0.2
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _determine_priority(self, action: Dict[str, Any]) -> DecisionPriority:
        """Determine priority of an action"""
        action_type = action.get('type', '')
        value = action.get('value', 0.5)
        
        # Safety-critical actions
        if action_type in ['emergency_exit', 'risk_reduction']:
            return DecisionPriority.CRITICAL
        
        # High-value opportunities
        if value > 0.8:
            return DecisionPriority.HIGH
        
        # Exploratory actions
        if action_type in ['research', 'experiment']:
            return DecisionPriority.EXPLORATORY
        
        # Standard actions
        if value > 0.5:
            return DecisionPriority.MEDIUM
        
        return DecisionPriority.LOW
    
    async def execute(self, decision: Decision) -> Dict[str, Any]:
        """
        Execute a decision.
        
        This dispatches the action to the appropriate executor
        and tracks the result.
        """
        if not decision.is_safe(self.safety_threshold):
            logger.warning(f"Decision {decision.decision_id} failed safety check")
            return {
                'success': False,
                'reason': 'safety_check_failed',
                'violations': decision.constitutional_violations
            }
        
        self.state = SystemState.EXECUTING
        
        try:
            # Get appropriate executor from agent registry
            if self.agent_registry:
                executor = await self.agent_registry.get_executor(decision.decision_type)
                if executor:
                    result = await executor.execute(decision.action)
                else:
                    result = await self._default_execute(decision)
            else:
                result = await self._default_execute(decision)
            
            # Record result
            decision.executed = True
            decision.execution_result = result
            self.decision_history.append(decision)
            
            # Trim history if needed
            if len(self.decision_history) > self.max_history:
                self.decision_history = self.decision_history[-self.max_history:]
            
            # Store in memory for learning
            if self.memory_system:
                await self.memory_system.store_experience({
                    'decision': decision,
                    'result': result,
                    'context': self.current_context
                })
            
            self.state = SystemState.READY
            return result
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            self.state = SystemState.READY
            return {
                'success': False,
                'reason': 'execution_error',
                'error': str(e)
            }
    
    async def _default_execute(self, decision: Decision) -> Dict[str, Any]:
        """Default execution handler"""
        logger.info(f"Executing decision: {decision.decision_type}")
        
        # Use tool registry if available
        if self.tool_registry:
            action = decision.action
            tool_name = action.get('tool', decision.decision_type)
            tool = await self.tool_registry.get_tool(tool_name)
            
            if tool:
                return await tool.execute(action)
        
        return {
            'success': True,
            'decision_id': decision.decision_id,
            'action': decision.action
        }
    
    async def learn(self, outcome: Dict[str, Any]):
        """
        Learn from an outcome - Self-play improvement loop.
        
        Inspired by AlphaGo's self-play where the system:
        1. Plays games against itself
        2. Uses outcomes to improve policy and value networks
        3. Continuously gets stronger
        """
        self.state = SystemState.LEARNING
        
        # Update value network with actual outcome
        if self.value_network and self.current_context:
            await self.value_network.update(
                self.current_context,
                outcome.get('actual_value', 0)
            )
        
        # Update policy network based on successful actions
        if self.policy_network and outcome.get('success', False):
            decision = outcome.get('decision')
            if decision:
                await self.policy_network.reinforce(
                    decision.action,
                    outcome.get('reward', 0)
                )
        
        # Store in episodic memory
        if self.memory_system:
            await self.memory_system.store_episode(outcome)
        
        self.state = SystemState.READY
        logger.info("Learning update completed")
    
    async def run(self):
        """Main orchestration loop"""
        logger.info("Starting Master Orchestrator main loop")
        
        while self.running:
            try:
                async with self._lock:
                    # Get current context
                    context = await self._gather_context()
                    
                    # Think and decide
                    decision = await self.think(context)
                    
                    # Execute if safe and valuable
                    if decision.is_safe() and decision.expected_value > 0.5:
                        result = await self.execute(decision)
                        
                        # Learn from result
                        await self.learn({
                            'decision': decision,
                            'result': result,
                            'success': result.get('success', False),
                            'actual_value': result.get('value', decision.expected_value)
                        })
                
                # Small delay to prevent tight loop
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(5)
    
    async def _gather_context(self) -> SystemContext:
        """Gather current system context"""
        return SystemContext(
            timestamp=datetime.now(),
            market_state=await self._get_market_state(),
            portfolio_state=await self._get_portfolio_state(),
            agent_states=await self._get_agent_states(),
            pending_decisions=self.decision_queue.copy(),
            recent_outcomes=[d.execution_result for d in self.decision_history[-10:] if d.execution_result],
            risk_metrics=await self._get_risk_metrics()
        )
    
    async def _get_market_state(self) -> Dict[str, Any]:
        """Get current market state"""
        if self.tool_registry:
            market_tool = await self.tool_registry.get_tool('market_data')
            if market_tool:
                # Use default symbol from config or fallback to EURUSD
                symbol = self.config.get('default_symbol', 'EURUSD')
                return await market_tool.execute({'symbol': symbol})
        return {'price': 0, 'volatility': 0, 'trend': 'unknown'}
    
    async def _get_portfolio_state(self) -> Dict[str, Any]:
        """Get current portfolio state"""
        if self.tool_registry:
            portfolio_tool = await self.tool_registry.get_tool('portfolio')
            if portfolio_tool:
                return await portfolio_tool.execute({'operation': 'get_state'})
        return {'equity': 0, 'exposure': 0, 'pnl': 0}
    
    async def _get_agent_states(self) -> Dict[str, Any]:
        """Get states of all agents"""
        if self.agent_registry:
            return await self.agent_registry.get_all_states()
        return {}
    
    async def _get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics"""
        if self.tool_registry:
            risk_tool = await self.tool_registry.get_tool('risk_calculator')
            if risk_tool:
                return await risk_tool.execute({'operation': 'get_metrics'})
        return {'var': 0, 'sharpe': 0}
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Master Orchestrator")
        self.running = False
        self.state = SystemState.SHUTDOWN
        
        # Shutdown subsystems
        if self.memory_system:
            await self.memory_system.shutdown()
        if self.agent_registry:
            await self.agent_registry.shutdown()
        if self.tool_registry:
            await self.tool_registry.shutdown()
        
        logger.info("Master Orchestrator shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'state': self.state.value,
            'running': self.running,
            'pending_decisions': len(self.decision_queue),
            'decision_history_size': len(self.decision_history),
            'safety_threshold': self.safety_threshold,
            'search_depth': self.search_depth,
            'num_simulations': self.num_simulations
        }
