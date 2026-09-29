"""
Multi-Model Router for Perplexity Trading Architecture
============================================================

Routes subtasks to the most appropriate specialized agent/model
based on task type, complexity, and performance history.

Like Perplexity Computer's 19-model roster, this routes:
- Research queries → Research Agent
- Technical analysis → Technical Agent
- Risk calculations → Risk Agent
- Execution → Execution Agent
- Reasoning → Reasoning Agent (chain-of-thought)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from .core_types import (
    SubTask,
    TaskType,
    AgentType,
)

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Strategy for routing tasks to agents"""
    TASK_TYPE = "task_type"         # Route based on task type
    COMPLEXITY = "complexity"        # Route based on estimated complexity
    LATENCY = "latency"             # Route to fastest available agent
    QUALITY = "quality"             # Route to highest quality agent
    BALANCED = "balanced"           # Balance latency and quality
    SPECIALIZED = "specialized"     # Route to most specialized agent


@dataclass
class AgentConfig:
    """Configuration for a specialized agent"""
    agent_type: AgentType
    name: str
    description: str
    
    # Capabilities
    supported_task_types: List[TaskType] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    
    # Performance characteristics
    avg_latency_ms: float = 1000.0
    quality_score: float = 0.8  # 0-1
    reliability: float = 0.95   # Success rate
    
    # Resource requirements
    max_concurrent: int = 5
    current_load: int = 0
    
    # Cost (for prioritization)
    cost_per_call: float = 0.0
    
    # Status
    enabled: bool = True
    last_used: Optional[datetime] = None
    total_calls: int = 0
    total_errors: int = 0
    
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        return self.enabled and self.current_load < self.max_concurrent
    
    def get_effective_score(self, task: SubTask) -> float:
        """Calculate effective score for routing decision"""
        base_score = self.quality_score * self.reliability
        
        # Bonus for specialization match
        if task.task_type in self.supported_task_types:
            base_score *= 1.2
        
        # Penalty for high load
        load_factor = 1.0 - (self.current_load / self.max_concurrent) * 0.3
        base_score *= load_factor
        
        return min(base_score, 1.0)


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    subtask_id: str
    selected_agent: AgentType
    agent_config: AgentConfig
    confidence: float
    reasoning: str
    alternatives: List[AgentType] = field(default_factory=list)
    estimated_latency_ms: float = 0.0


class ModelRouter:
    """
    Routes subtasks to specialized agents.
    
    Implements multi-model routing similar to Perplexity Computer:
    - Maintains roster of specialized agents
    - Routes based on task type, complexity, and load
    - Tracks performance for adaptive routing
    - Supports fallback to alternative agents
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.strategy = RoutingStrategy(
            self.config.get('strategy', RoutingStrategy.BALANCED.value)
        )
        
        # Initialize agent roster
        self.agents: Dict[AgentType, AgentConfig] = {}
        self._initialize_default_agents()
        
        # Routing history for learning
        self.routing_history: List[Dict[str, Any]] = []
        
        # Custom routing rules
        self.custom_rules: List[Callable[[SubTask], Optional[AgentType]]] = []
    
    def _initialize_default_agents(self) -> None:
        """Initialize the default agent roster"""
        
        # Research Agent - Information gathering
        self.agents[AgentType.RESEARCH] = AgentConfig(
            agent_type=AgentType.RESEARCH,
            name="Research Agent",
            description="Gathers market research, news, and fundamental data",
            supported_task_types=[TaskType.RESEARCH, TaskType.EXTRACTION],
            specializations=["news", "fundamentals", "economic_data", "company_info"],
            avg_latency_ms=2000.0,
            quality_score=0.85,
            reliability=0.92,
        )
        
        # Technical Agent - Chart analysis
        self.agents[AgentType.TECHNICAL] = AgentConfig(
            agent_type=AgentType.TECHNICAL,
            name="Technical Agent",
            description="Performs technical analysis on price data",
            supported_task_types=[TaskType.ANALYSIS, TaskType.EXTRACTION],
            specializations=["patterns", "indicators", "support_resistance", "trend"],
            avg_latency_ms=500.0,
            quality_score=0.88,
            reliability=0.95,
        )
        
        # Risk Agent - Risk calculations
        self.agents[AgentType.RISK] = AgentConfig(
            agent_type=AgentType.RISK,
            name="Risk Agent",
            description="Calculates risk parameters and position sizing",
            supported_task_types=[TaskType.CALCULATION, TaskType.ANALYSIS],
            specializations=["position_sizing", "stop_loss", "risk_reward", "exposure"],
            avg_latency_ms=300.0,
            quality_score=0.95,
            reliability=0.98,
        )
        
        # Execution Agent - Order execution
        self.agents[AgentType.EXECUTION] = AgentConfig(
            agent_type=AgentType.EXECUTION,
            name="Execution Agent",
            description="Handles order routing and execution",
            supported_task_types=[TaskType.EXECUTION],
            specializations=["order_routing", "timing", "slippage", "market_impact"],
            avg_latency_ms=100.0,
            quality_score=0.90,
            reliability=0.99,
        )
        
        # Reasoning Agent - Chain-of-thought
        self.agents[AgentType.REASONING] = AgentConfig(
            agent_type=AgentType.REASONING,
            name="Reasoning Agent",
            description="Performs multi-step reasoning and synthesis",
            supported_task_types=[TaskType.SYNTHESIS, TaskType.DECISION],
            specializations=["chain_of_thought", "multi_step", "synthesis", "decision"],
            avg_latency_ms=3000.0,
            quality_score=0.92,
            reliability=0.90,
        )
        
        # Sentiment Agent - Sentiment analysis
        self.agents[AgentType.SENTIMENT] = AgentConfig(
            agent_type=AgentType.SENTIMENT,
            name="Sentiment Agent",
            description="Analyzes market sentiment from various sources",
            supported_task_types=[TaskType.ANALYSIS, TaskType.EXTRACTION],
            specializations=["social_media", "news_sentiment", "positioning", "fear_greed"],
            avg_latency_ms=1500.0,
            quality_score=0.80,
            reliability=0.88,
        )
        
        # Macro Agent - Macroeconomic analysis
        self.agents[AgentType.MACRO] = AgentConfig(
            agent_type=AgentType.MACRO,
            name="Macro Agent",
            description="Analyzes macroeconomic factors and policy",
            supported_task_types=[TaskType.ANALYSIS, TaskType.RESEARCH],
            specializations=["economic_indicators", "central_bank", "global_factors", "correlations"],
            avg_latency_ms=2500.0,
            quality_score=0.85,
            reliability=0.90,
        )
        
        # Microstructure Agent - Market microstructure
        self.agents[AgentType.MICROSTRUCTURE] = AgentConfig(
            agent_type=AgentType.MICROSTRUCTURE,
            name="Microstructure Agent",
            description="Analyzes order flow and market depth",
            supported_task_types=[TaskType.ANALYSIS, TaskType.EXTRACTION],
            specializations=["order_flow", "liquidity", "market_depth", "toxicity"],
            avg_latency_ms=200.0,
            quality_score=0.88,
            reliability=0.94,
        )
        
        # Summarizer Agent - Final synthesis
        self.agents[AgentType.SUMMARIZER] = AgentConfig(
            agent_type=AgentType.SUMMARIZER,
            name="Summarizer Agent",
            description="Synthesizes results into final output",
            supported_task_types=[TaskType.SUMMARY, TaskType.SYNTHESIS],
            specializations=["summarization", "explanation", "citation"],
            avg_latency_ms=1000.0,
            quality_score=0.90,
            reliability=0.95,
        )
        
        # Validator Agent - Verification
        self.agents[AgentType.VALIDATOR] = AgentConfig(
            agent_type=AgentType.VALIDATOR,
            name="Validator Agent",
            description="Cross-references and validates data",
            supported_task_types=[TaskType.VERIFICATION],
            specializations=["cross_reference", "consistency", "validation"],
            avg_latency_ms=800.0,
            quality_score=0.92,
            reliability=0.96,
        )
    
    def route(self, subtask: SubTask) -> RoutingDecision:
        """
        Route a subtask to the most appropriate agent.
        
        Uses the configured routing strategy to select the best agent.
        """
        logger.debug(f"Routing subtask {subtask.id} (type={subtask.task_type.name})")
        
        # Check custom rules first
        for rule in self.custom_rules:
            custom_agent = rule(subtask)
            if custom_agent and custom_agent in self.agents:
                agent_config = self.agents[custom_agent]
                if agent_config.is_available():
                    return RoutingDecision(
                        subtask_id=subtask.id,
                        selected_agent=custom_agent,
                        agent_config=agent_config,
                        confidence=0.95,
                        reasoning="Matched custom routing rule",
                        estimated_latency_ms=agent_config.avg_latency_ms,
                    )
        
        # If subtask specifies agent type, use it directly
        if subtask.agent_type in self.agents:
            agent_config = self.agents[subtask.agent_type]
            if agent_config.is_available():
                return RoutingDecision(
                    subtask_id=subtask.id,
                    selected_agent=subtask.agent_type,
                    agent_config=agent_config,
                    confidence=0.90,
                    reasoning=f"Direct routing to specified agent: {subtask.agent_type.value}",
                    estimated_latency_ms=agent_config.avg_latency_ms,
                )
        
        # Score all available agents
        candidates: List[tuple] = []
        for agent_type, agent_config in self.agents.items():
            if not agent_config.is_available():
                continue
            
            score = self._calculate_routing_score(subtask, agent_config)
            candidates.append((agent_type, agent_config, score))
        
        if not candidates:
            # Fallback to reasoning agent
            logger.warning(f"No available agents for subtask {subtask.id}, falling back to REASONING")
            return RoutingDecision(
                subtask_id=subtask.id,
                selected_agent=AgentType.REASONING,
                agent_config=self.agents[AgentType.REASONING],
                confidence=0.5,
                reasoning="Fallback to reasoning agent (no available specialized agents)",
                estimated_latency_ms=self.agents[AgentType.REASONING].avg_latency_ms,
            )
        
        # Sort by score and select best
        candidates.sort(key=lambda x: x[2], reverse=True)
        best_agent, best_config, best_score = candidates[0]
        
        # Get alternatives
        alternatives = [c[0] for c in candidates[1:4]]  # Top 3 alternatives
        
        return RoutingDecision(
            subtask_id=subtask.id,
            selected_agent=best_agent,
            agent_config=best_config,
            confidence=best_score,
            reasoning=self._generate_routing_reasoning(subtask, best_agent, best_score),
            alternatives=alternatives,
            estimated_latency_ms=best_config.avg_latency_ms,
        )
    
    def _calculate_routing_score(self, subtask: SubTask, agent_config: AgentConfig) -> float:
        """Calculate routing score for an agent"""
        score = 0.0
        
        if self.strategy == RoutingStrategy.TASK_TYPE:
            # Primary: task type match
            if subtask.task_type in agent_config.supported_task_types:
                score = 0.9
            else:
                score = 0.3
        
        elif self.strategy == RoutingStrategy.QUALITY:
            # Primary: quality score
            score = agent_config.quality_score
            if subtask.task_type in agent_config.supported_task_types:
                score *= 1.1
        
        elif self.strategy == RoutingStrategy.LATENCY:
            # Primary: inverse latency (faster = better)
            max_latency = 5000.0
            score = 1.0 - (agent_config.avg_latency_ms / max_latency)
            if subtask.task_type in agent_config.supported_task_types:
                score *= 1.1
        
        elif self.strategy == RoutingStrategy.BALANCED:
            # Balanced: quality * reliability * task_match * load_factor
            score = agent_config.get_effective_score(subtask)
        
        else:  # SPECIALIZED
            # Specialized: prioritize specialization match
            if subtask.task_type in agent_config.supported_task_types:
                score = 0.8
            else:
                score = 0.2
            score *= agent_config.quality_score
        
        return min(score, 1.0)
    
    def _generate_routing_reasoning(self, subtask: SubTask, agent: AgentType, score: float) -> str:
        """Generate human-readable routing reasoning"""
        config = self.agents[agent]
        
        reasons = []
        reasons.append(f"Selected {config.name} for {subtask.task_type.name} task")
        
        if subtask.task_type in config.supported_task_types:
            reasons.append(f"Task type {subtask.task_type.name} is supported")
        
        reasons.append(f"Quality score: {config.quality_score:.0%}")
        reasons.append(f"Reliability: {config.reliability:.0%}")
        reasons.append(f"Current load: {config.current_load}/{config.max_concurrent}")
        reasons.append(f"Routing confidence: {score:.0%}")
        
        return "; ".join(reasons)
    
    def route_batch(self, subtasks: List[SubTask]) -> Dict[str, RoutingDecision]:
        """Route multiple subtasks, considering load balancing"""
        decisions = {}
        
        # Sort by priority (higher first)
        sorted_tasks = sorted(subtasks, key=lambda t: t.priority, reverse=True)
        
        for subtask in sorted_tasks:
            decision = self.route(subtask)
            decisions[subtask.id] = decision
            
            # Update load for selected agent
            if decision.selected_agent in self.agents:
                self.agents[decision.selected_agent].current_load += 1
        
        return decisions
    
    def release_agent(self, agent_type: AgentType) -> None:
        """Release an agent after task completion"""
        if agent_type in self.agents:
            self.agents[agent_type].current_load = max(0, self.agents[agent_type].current_load - 1)
            self.agents[agent_type].last_used = datetime.utcnow()
    
    def record_result(self, agent_type: AgentType, success: bool, latency_ms: float) -> None:
        """Record task result for adaptive routing"""
        if agent_type not in self.agents:
            return
        
        config = self.agents[agent_type]
        config.total_calls += 1
        
        if not success:
            config.total_errors += 1
        
        # Update reliability (exponential moving average)
        alpha = 0.1
        current_success = 1.0 if success else 0.0
        config.reliability = alpha * current_success + (1 - alpha) * config.reliability
        
        # Update latency (exponential moving average)
        config.avg_latency_ms = alpha * latency_ms + (1 - alpha) * config.avg_latency_ms
        
        # Record in history
        self.routing_history.append({
            'agent': agent_type.value,
            'success': success,
            'latency_ms': latency_ms,
            'timestamp': datetime.utcnow().isoformat(),
        })
        
        # Trim history
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-500:]
    
    def add_custom_rule(self, rule: Callable[[SubTask], Optional[AgentType]]) -> None:
        """Add a custom routing rule"""
        self.custom_rules.append(rule)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents"""
        stats = {}
        for agent_type, config in self.agents.items():
            stats[agent_type.value] = {
                'name': config.name,
                'enabled': config.enabled,
                'quality_score': config.quality_score,
                'reliability': config.reliability,
                'avg_latency_ms': config.avg_latency_ms,
                'current_load': config.current_load,
                'max_concurrent': config.max_concurrent,
                'total_calls': config.total_calls,
                'total_errors': config.total_errors,
            }
        return stats
