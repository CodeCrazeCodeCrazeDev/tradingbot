"""
Task Router
===========

Intelligent routing of tasks to the best available capability or frontier model.
Implements epsilon-greedy exploration with learned routing based on historical performance.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import numpy as np

from .capability_registry import CapabilityRegistry, CapabilityRecord, RoutingDecision

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategy types"""
    GREEDY = "greedy"  # Always pick best known
    EPSILON_GREEDY = "epsilon_greedy"  # Explore with probability epsilon
    UCB = "ucb"  # Upper Confidence Bound
    SIMILARITY = "similarity"  # Based on task embedding similarity
    ADAPTIVE = "adaptive"  # Dynamic strategy selection


@dataclass
class TaskRequest:
    """Incoming task request"""
    task_id: str
    task_type: str
    task_category: str
    input_data: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher = more urgent
    timeout_ms: int = 5000
    required_latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_hash(self) -> str:
        """Generate hash for task identification"""
        content = f"{self.task_type}:{self.task_category}:{json.dumps(self.input_data, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class RoutingResult:
    """Result of routing decision"""
    decision_id: str
    task_id: str
    selected_capability: Optional[str]
    selected_model: Optional[str]  # Frontier model fallback
    strategy_used: str
    confidence: float
    estimated_latency_ms: float
    estimated_success_rate: float
    alternatives: List[Dict[str, Any]]
    reasoning: str


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    decision_id: str
    success: bool
    output: Any
    latency_ms: float
    capability_used: Optional[str]
    model_used: Optional[str]
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskClassifier:
    """Classifies tasks into categories for routing"""
    
    def __init__(self):
        self.category_patterns = {
            'signal_generation': ['signal', 'generate signal', 'buy', 'sell', 'entry', 'exit'],
            'risk_assessment': ['risk', 'assess', 'calculate risk', 'position sizing', 'drawdown'],
            'market_analysis': ['analyze', 'market', 'trend', 'pattern', 'technical analysis'],
            'portfolio_optimization': ['portfolio', 'optimize', 'allocation', 'rebalance'],
            'execution': ['execute', 'order', 'trade execution', 'slippage'],
            'sentiment_analysis': ['sentiment', 'news', 'social', 'twitter', 'sentiment score'],
            'forecasting': ['predict', 'forecast', 'price target', 'projection'],
            'anomaly_detection': ['anomaly', 'outlier', 'unusual', 'detect anomaly'],
        }
    
    def classify(self, task_request: TaskRequest) -> str:
        """Classify task into category"""
        # Use provided category if available
        if task_request.task_category:
            return task_request.task_category
        
        # Classify based on task type and tags
        text = f"{task_request.task_type} {' '.join(task_request.tags)}".lower()
        
        scores = {}
        for category, patterns in self.category_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return 'general'
    
    def add_pattern(self, category: str, patterns: List[str]):
        """Add classification patterns for a category"""
        if category not in self.category_patterns:
            self.category_patterns[category] = []
        self.category_patterns[category].extend(patterns)


class RoutingLearner:
    """Learns optimal routing decisions from historical performance"""
    
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.exploration_rate = 0.15  # Epsilon for epsilon-greedy
        self.min_exploration = 0.05
        self.decay_rate = 0.995
        self.ucb_c = 2.0  # Exploration constant for UCB
    
    def select_capability(self, task_category: str, 
                         candidates: List[CapabilityRecord],
                         strategy: RoutingStrategy = RoutingStrategy.EPSILON_GREEDY,
                         task_tags: Optional[List[str]] = None) -> Tuple[Optional[CapabilityRecord], float, str]:
        """
        Select best capability using specified strategy.
        Returns: (selected_capability, confidence, reasoning)
        """
        if not candidates:
            return None, 0.0, "No candidates available"
        
        if strategy == RoutingStrategy.GREEDY:
            return self._greedy_select(candidates)
        
        elif strategy == RoutingStrategy.EPSILON_GREEDY:
            return self._epsilon_greedy_select(candidates)
        
        elif strategy == RoutingStrategy.UCB:
            return self._ucb_select(candidates)
        
        elif strategy == RoutingStrategy.SIMILARITY:
            return self._similarity_select(candidates, task_tags or [])
        
        else:
            return self._greedy_select(candidates)
    
    def _greedy_select(self, candidates: List[CapabilityRecord]) -> Tuple[CapabilityRecord, float, str]:
        """Select best performing capability"""
        # Score = performance * reliability
        best = max(candidates, 
                  key=lambda c: c.performance_score * c.reliability_score * (1 + np.log1p(c.usage_count)))
        
        score = best.performance_score * best.reliability_score
        confidence = min(0.95, score * (1 - 1 / (1 + best.usage_count)))
        
        return best, confidence, f"Greedy: best performer ({best.performance_score:.3f})"
    
    def _epsilon_greedy_select(self, candidates: List[CapabilityRecord]) -> Tuple[CapabilityRecord, float, str]:
        """Epsilon-greedy selection: explore with probability epsilon"""
        if np.random.random() < self.exploration_rate:
            # Explore: random selection weighted by inverse usage (favor less-used)
            weights = [1.0 / (1 + c.usage_count) for c in candidates]
            weights = np.array(weights) / sum(weights)
            selected = np.random.choice(candidates, p=weights)
            
            self.exploration_rate = max(self.min_exploration, 
                                       self.exploration_rate * self.decay_rate)
            
            return selected, 0.5, f"Exploration: trying {selected.name}"
        else:
            # Exploit: greedy selection
            return self._greedy_select(candidates)
    
    def _ucb_select(self, candidates: List[CapabilityRecord]) -> Tuple[CapabilityRecord, float, str]:
        """Upper Confidence Bound selection"""
        total_usage = sum(c.usage_count for c in candidates)
        
        best_ucb = None
        best_score = -float('inf')
        
        for c in candidates:
            # Average reward
            avg_reward = c.performance_score * (c.success_count / max(1, c.usage_count))
            
            # Exploration bonus
            if c.usage_count == 0:
                exploration = float('inf')
            else:
                exploration = self.ucb_c * np.sqrt(np.log(total_usage + 1) / c.usage_count)
            
            ucb_score = avg_reward + exploration
            
            if ucb_score > best_score:
                best_score = ucb_score
                best_ucb = c
        
        confidence = min(0.95, best_ucb.performance_score if best_ucb else 0.5)
        return best_ucb, confidence, f"UCB: score={best_score:.3f}"
    
    def _similarity_select(self, candidates: List[CapabilityRecord], 
                          task_tags: List[str]) -> Tuple[CapabilityRecord, float, str]:
        """Select based on tag similarity"""
        best_match = None
        best_score = 0
        
        for c in candidates:
            # Jaccard similarity between task tags and capability tags
            cap_tags = set(c.task_tags)
            task_tags_set = set(task_tags)
            
            if not cap_tags and not task_tags_set:
                similarity = 0.5
            elif not cap_tags or not task_tags_set:
                similarity = 0
            else:
                intersection = len(cap_tags & task_tags_set)
                union = len(cap_tags | task_tags_set)
                similarity = intersection / union
            
            # Weight by performance
            score = similarity * c.performance_score
            
            if score > best_score:
                best_score = score
                best_match = c
        
        if best_match:
            return best_match, best_score, f"Similarity: {best_score:.3f} match"
        
        # Fall back to greedy
        return self._greedy_select(candidates)
    
    def update_exploration_rate(self, recent_success_rate: float):
        """Adjust exploration rate based on recent performance"""
        # More exploration if things are going well, less if struggling
        if recent_success_rate > 0.8:
            self.exploration_rate = min(0.3, self.exploration_rate * 1.05)
        elif recent_success_rate < 0.5:
            self.exploration_rate = max(self.min_exploration, self.exploration_rate * 0.9)


class TaskRouter:
    """
    Main task routing component.
    
    Routes incoming tasks to either:
    - A distilled capability from the registry
    - A frontier model (fallback)
    """
    
    def __init__(self, registry: CapabilityRegistry, 
                 frontier_models: Optional[Dict[str, Callable]] = None):
        self.registry = registry
        self.classifier = TaskClassifier()
        self.learner = RoutingLearner(registry)
        self.frontier_models = frontier_models or {}
        
        # Performance tracking
        self.routing_history: List[RoutingDecision] = []
        self.decision_counter = 0
        
        # Default model preferences by category
        self.category_defaults: Dict[str, str] = {}
        
        logger.info(f"TaskRouter initialized with {len(self.frontier_models)} frontier models")
    
    def register_frontier_model(self, model_id: str, 
                               model_fn: Callable[[Dict[str, Any]], Any],
                               capabilities: List[str]):
        """Register a frontier model as fallback option"""
        self.frontier_models[model_id] = {
            'fn': model_fn,
            'capabilities': capabilities,
            'avg_latency_ms': 1000,  # Default estimate
            'reliability': 0.9
        }
        
        logger.info(f"Registered frontier model {model_id}")
    
    def set_category_default(self, category: str, model_id: str):
        """Set default frontier model for a category"""
        self.category_defaults[category] = model_id
    
    async def route(self, task_request: TaskRequest,
                   strategy: RoutingStrategy = RoutingStrategy.EPSILON_GREEDY) -> RoutingResult:
        """
        Route a task to the best available option.
        
        Decision hierarchy:
        1. Check for distilled capabilities in registry
        2. If found: use learned routing to select best
        3. If not found: use frontier model fallback
        """
        self.decision_counter += 1
        decision_id = f"route_{self.decision_counter}_{datetime.utcnow().timestamp()}"
        
        # Classify task
        task_category = self.classifier.classify(task_request)
        task_hash = task_request.get_hash()
        
        # Find candidates in registry
        candidates = self.registry.find_capabilities_for_task(
            task_category=task_category,
            min_score=0.5,
            limit=10
        )
        
        # Filter by latency if specified
        if task_request.required_latency_ms:
            candidates = [c for c in candidates 
                       if c.latency_ms <= task_request.required_latency_ms]
        
        selected_capability = None
        selected_model = None
        confidence = 0.0
        reasoning = ""
        alternatives = []
        
        if candidates:
            # Use learned routing
            selected, confidence, reasoning = self.learner.select_capability(
                task_category, candidates, strategy, task_request.tags
            )
            
            if selected:
                selected_capability = selected.capability_id
                
                # Build alternatives list
                for c in candidates[:3]:
                    if c.capability_id != selected_capability:
                        alternatives.append({
                            'capability_id': c.capability_id,
                            'name': c.name,
                            'performance_score': c.performance_score,
                            'latency_ms': c.latency_ms
                        })
                
                estimated_latency = selected.latency_ms
                estimated_success = selected.performance_score * selected.reliability_score
            else:
                # Fall back to frontier model
                selected_model = self._select_frontier_model(task_category)
                reasoning = f"No capability selected, using frontier model {selected_model}"
                confidence = 0.6
                estimated_latency = self.frontier_models.get(selected_model, {}).get('avg_latency_ms', 1000)
                estimated_success = 0.8
        else:
            # No distilled capabilities - use frontier model
            selected_model = self._select_frontier_model(task_category)
            reasoning = f"No distilled capabilities for {task_category}, using frontier model"
            confidence = 0.5
            estimated_latency = self.frontier_models.get(selected_model, {}).get('avg_latency_ms', 1000)
            estimated_success = 0.75
        
        # Record decision
        decision = RoutingDecision(
            decision_id=decision_id,
            task_hash=task_hash,
            task_category=task_category,
            selected_capability=selected_capability,
            alternative_options=[a['capability_id'] for a in alternatives],
            confidence=confidence,
            latency_ms=estimated_latency
        )
        
        self.registry.record_routing_decision(decision)
        
        return RoutingResult(
            decision_id=decision_id,
            task_id=task_request.task_id,
            selected_capability=selected_capability,
            selected_model=selected_model,
            strategy_used=strategy.value,
            confidence=confidence,
            estimated_latency_ms=estimated_latency,
            estimated_success_rate=estimated_success,
            alternatives=alternatives,
            reasoning=reasoning
        )
    
    def _select_frontier_model(self, task_category: str) -> str:
        """Select appropriate frontier model for task category"""
        # Check for category default
        if task_category in self.category_defaults:
            return self.category_defaults[task_category]
        
        # Find model with matching capabilities
        for model_id, model_info in self.frontier_models.items():
            if task_category in model_info.get('capabilities', []):
                return model_id
        
        # Return first available
        return list(self.frontier_models.keys())[0] if self.frontier_models else "unknown"
    
    async def execute_with_capability(self, routing: RoutingResult, 
                                     task_request: TaskRequest,
                                     capability_impl: Callable) -> ExecutionResult:
        """Execute task using a distilled capability"""
        start_time = datetime.utcnow()
        
        try:
            # Execute the capability
            output = await asyncio.wait_for(
                self._run_capability(capability_impl, task_request.input_data),
                timeout=task_request.timeout_ms / 1000
            )
            
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Record success
            self.registry.update_capability_performance(
                capability_id=routing.selected_capability,
                success=True,
                latency_ms=latency_ms,
                additional_metrics={'task_completion': 1.0}
            )
            
            # Update routing outcome
            self.registry.update_routing_outcome(routing.decision_id, success=True)
            
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=True,
                output=output,
                latency_ms=latency_ms,
                capability_used=routing.selected_capability,
                model_used=None
            )
            
        except asyncio.TimeoutError:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.registry.update_capability_performance(
                capability_id=routing.selected_capability,
                success=False,
                latency_ms=latency_ms,
                additional_metrics={'timeout': 1.0}
            )
            
            self.registry.update_routing_outcome(routing.decision_id, success=False)
            
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=False,
                output=None,
                latency_ms=latency_ms,
                capability_used=routing.selected_capability,
                model_used=None,
                error="Execution timeout"
            )
            
        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.registry.update_capability_performance(
                capability_id=routing.selected_capability,
                success=False,
                latency_ms=latency_ms,
                additional_metrics={'error': 1.0}
            )
            
            self.registry.update_routing_outcome(routing.decision_id, success=False)
            
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=False,
                output=None,
                latency_ms=latency_ms,
                capability_used=routing.selected_capability,
                model_used=None,
                error=str(e)
            )
    
    async def execute_with_model(self, routing: RoutingResult,
                                 task_request: TaskRequest) -> ExecutionResult:
        """Execute task using a frontier model"""
        start_time = datetime.utcnow()
        
        model_info = self.frontier_models.get(routing.selected_model)
        if not model_info:
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=False,
                output=None,
                latency_ms=0,
                capability_used=None,
                model_used=routing.selected_model,
                error="Model not found"
            )
        
        try:
            # Call frontier model
            model_fn = model_info['fn']
            output = await asyncio.wait_for(
                model_fn(task_request.input_data),
                timeout=task_request.timeout_ms / 1000
            )
            
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update routing outcome
            self.registry.update_routing_outcome(routing.decision_id, success=True)
            
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=True,
                output=output,
                latency_ms=latency_ms,
                capability_used=None,
                model_used=routing.selected_model
            )
            
        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.registry.update_routing_outcome(routing.decision_id, success=False)
            
            return ExecutionResult(
                task_id=task_request.task_id,
                decision_id=routing.decision_id,
                success=False,
                output=None,
                latency_ms=latency_ms,
                capability_used=None,
                model_used=routing.selected_model,
                error=str(e)
            )
    
    async def _run_capability(self, capability_impl: Callable, input_data: Dict[str, Any]) -> Any:
        """Run a distilled capability implementation"""
        if asyncio.iscoroutinefunction(capability_impl):
            return await capability_impl(input_data)
        else:
            return capability_impl(input_data)
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        recent_decisions = self.registry.get_routing_history(limit=1000)
        
        if not recent_decisions:
            return {'total_routes': 0}
        
        successful = sum(1 for d in recent_decisions if d.success)
        capability_routes = sum(1 for d in recent_decisions if d.selected_capability)
        model_routes = sum(1 for d in recent_decisions if d.selected_model or not d.selected_capability)
        
        return {
            'total_routes': len(recent_decisions),
            'success_rate': successful / len(recent_decisions),
            'capability_routes': capability_routes,
            'model_routes': model_routes,
            'exploration_rate': self.learner.exploration_rate,
            'avg_confidence': np.mean([d.confidence for d in recent_decisions])
        }
    
    def get_category_routing_summary(self) -> Dict[str, Any]:
        """Get routing summary by category"""
        summary = {}
        
        for category in self.classifier.category_patterns.keys():
            decisions = self.registry.get_routing_history(task_category=category, limit=100)
            
            if decisions:
                summary[category] = {
                    'total_routes': len(decisions),
                    'success_rate': sum(1 for d in decisions if d.success) / len(decisions),
                    'preferred_capability': self._get_most_used_capability(decisions),
                    'avg_latency': np.mean([d.latency_ms for d in decisions])
                }
        
        return summary
    
    def _get_most_used_capability(self, decisions: List[RoutingDecision]) -> Optional[str]:
        """Get most frequently used capability from decisions"""
        from collections import Counter
        
        capabilities = [d.selected_capability for d in decisions if d.selected_capability]
        if not capabilities:
            return None
        
        return Counter(capabilities).most_common(1)[0][0]


def create_router(registry: CapabilityRegistry,
                 frontier_models: Optional[Dict[str, Callable]] = None) -> TaskRouter:
    """Factory function to create a task router"""
    return TaskRouter(registry, frontier_models)
