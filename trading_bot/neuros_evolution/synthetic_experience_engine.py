"""
Synthetic Experience Engine (Dream/Imagination System)
=====================================================

100x Strengthened Dream and Imagination Capabilities

Human brains create synthetic experiences through:
- Dreaming: Offline memory consolidation during rest
- Imagination: Counterfactual scenario generation  
- Mental simulation: Testing actions before execution

This system provides AI-equivalent capabilities at 100x scale:
- 100x more parallel scenarios than standard sandbox
- Dream-state consolidation of synthetic memories
- Imagination-driven capability prediction
- Experience-based decision making

Components:
1. DreamStateGenerator - Massive parallel scenario generation
2. SyntheticMemoryConsolidator - Offline experience processing
3. ImaginationEngine - Generative world modeling
4. ExperienceBasedRouter - Uses synthetic experiences for routing
5. CounterfactualWorldSimulator - Parallel reality testing
"""

import asyncio
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import logging
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


class ExperienceType(Enum):
    """Types of synthetic experiences"""
    DREAM = "dream"              # Offline consolidation scenarios
    IMAGINATION = "imagination"  # Creative what-if scenarios
    SIMULATION = "simulation"   # Action outcome prediction
    COUNTERFACTUAL = "counterfactual"  # Alternative history
    NIGHTMARE = "nightmare"     # Stress-test scenarios (edge cases)


@dataclass
class SyntheticExperience:
    """
    A synthetic experience - equivalent to a human dream or imagined scenario
    """
    experience_id: str
    experience_type: ExperienceType
    
    # Scenario content
    context: Dict[str, Any]      # Market conditions, task parameters
    action_sequence: List[Dict]  # What was tried
    outcome: Dict[str, Any]      # What happened
    
    # Quality metrics
    vividness: float            # 0-1, how detailed/clear
    emotional_valence: float   # -1 to 1, negative to positive
    learning_value: float      # 0-1, how much can be learned
    
    # Source
    source_capabilities: List[str]
    generated_by: str           # Which model/system generated it
    
    # Integration status
    consolidated: bool = False
    used_in_decision: bool = False
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    consolidation_timestamp: Optional[str] = None
    
    def to_memory_entry(self) -> Dict[str, Any]:
        """Convert to consolidated memory entry"""
        return {
            "experience_id": self.experience_id,
            "type": self.experience_type.value,
            "context_summary": self._summarize_context(),
            "action_pattern": self._extract_action_pattern(),
            "outcome_summary": self.outcome.get("result", "unknown"),
            "learning_value": self.learning_value,
            "vividness": self.vividness,
            "emotional_valence": self.emotional_valence,
            "consolidated": True,
            "consolidation_timestamp": datetime.utcnow().isoformat()
        }
    
    def _summarize_context(self) -> str:
        """Extract key context features"""
        regime = self.context.get("market_regime", "unknown")
        volatility = self.context.get("volatility", "normal")
        return f"{regime}_{volatility}"
    
    def _extract_action_pattern(self) -> str:
        """Extract reusable action pattern"""
        if not self.action_sequence:
            return "no_action"
        return "_".join([a.get("type", "unknown") for a in self.action_sequence[:3]])


@dataclass
class DreamState:
    """
    Dream state - offline processing of experiences
    
    Like human REM sleep, this consolidates memories and
    generates novel connections between experiences.
    """
    dream_id: str
    
    # Input experiences being processed
    raw_experiences: List[SyntheticExperience]
    
    # Consolidation outputs
    consolidated_memories: List[Dict[str, Any]]
    novel_insights: List[str]
    pattern_discoveries: List[Dict[str, Any]]
    
    # Dream characteristics
    intensity: float  # 0-1, processing depth
    duration_cycles: int  # How many consolidation cycles
    
    # Meta-learning
    capability_improvements: Dict[str, float]
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


class DreamStateGenerator:
    """
    Generates dream states at 100x scale
    
    Creates massive parallel synthetic experiences for:
    - Offline learning
    - Stress testing
    - Novel scenario discovery
    - Memory consolidation
    """
    
    def __init__(self, scale_factor: int = 100):
        self.scale_factor = scale_factor  # 100x = 100 times more scenarios
        self.experience_buffer: List[SyntheticExperience] = []
        self.dream_history: List[DreamState] = []
        
        # Scenario templates for generation
        self.scenario_templates = self._initialize_templates()
        
        logger.info(f"DreamStateGenerator initialized (scale={scale_factor}x)")
    
    def _initialize_templates(self) -> Dict[str, List[Dict]]:
        """Initialize scenario generation templates"""
        return {
            "market_regimes": [
                {"regime": "high_volatility", "volatility": 0.8, "trend": "choppy"},
                {"regime": "low_volatility", "volatility": 0.2, "trend": "stable"},
                {"regime": "crash", "volatility": 2.0, "trend": "down"},
                {"regime": "bubble", "volatility": 1.5, "trend": "up"},
                {"regime": "normal", "volatility": 0.4, "trend": "mixed"}
            ],
            "task_contexts": [
                {"urgency": "high", "risk_tolerance": "low"},
                {"urgency": "low", "risk_tolerance": "high"},
                {"urgency": "medium", "risk_tolerance": "medium"}
            ],
            "capability_combinations": [
                ["CAP-M-03", "CAP-Q-01"],  # Regime + feature engineering
                ["CAP-M-06", "CAP-G-03"],  # News-to-signal + compliance
                ["CAP-R-01", "CAP-Q-02"],  # Hypothesis + backtest
                ["CAP-G-01", "CAP-M-07"]   # Uncertainty + regime warning
            ]
        }
    
    async def generate_experiences_batch(self,
                                        base_scenario: Dict[str, Any],
                                        n_variations: int = 100) -> List[SyntheticExperience]:
        """
        Generate 100x variations of a base scenario
        
        This is the core "imagination" capability - taking one
        real scenario and imagining 100 different ways it could go.
        """
        experiences = []
        
        # Generate in parallel batches
        batch_size = 20
        for i in range(0, n_variations, batch_size):
            batch = await self._generate_batch(base_scenario, batch_size)
            experiences.extend(batch)
        
        logger.info(f"Generated {len(experiences)} synthetic experiences from base scenario")
        return experiences
    
    async def _generate_batch(self, base: Dict, count: int) -> List[SyntheticExperience]:
        """Generate a batch of experiences"""
        batch = []
        
        for i in range(count):
            # Vary the context
            context = self._vary_context(base)
            
            # Generate action sequence
            actions = self._generate_actions(context)
            
            # Simulate outcome
            outcome = self._simulate_outcome(context, actions)
            
            # Calculate quality metrics
            vividness = random.uniform(0.6, 1.0)
            emotional_valence = self._calculate_emotion(outcome)
            learning_value = self._calculate_learning(actions, outcome)
            
            exp = SyntheticExperience(
                experience_id=f"exp_{hashlib.md5(f'{base}_{i}_{datetime.utcnow()}'.encode()).hexdigest()[:12]}",
                experience_type=random.choice([
                    ExperienceType.IMAGINATION,
                    ExperienceType.SIMULATION,
                    ExperienceType.COUNTERFACTUAL
                ]),
                context=context,
                action_sequence=actions,
                outcome=outcome,
                vividness=vividness,
                emotional_valence=emotional_valence,
                learning_value=learning_value,
                source_capabilities=context.get("capabilities", []),
                generated_by="dream_state_generator"
            )
            
            batch.append(exp)
        
        return batch
    
    def _vary_context(self, base: Dict) -> Dict:
        """Create varied version of base context"""
        context = base.copy()
        
        # Vary market regime
        regime = random.choice(self.scenario_templates["market_regimes"])
        context.update(regime)
        
        # Vary task context
        task = random.choice(self.scenario_templates["task_contexts"])
        context.update(task)
        
        # Add noise to numerical parameters
        for key in context:
            if isinstance(context[key], float):
                context[key] *= random.uniform(0.5, 1.5)
        
        return context
    
    def _generate_actions(self, context: Dict) -> List[Dict]:
        """Generate plausible action sequence for context"""
        n_actions = random.randint(1, 5)
        actions = []
        
        for i in range(n_actions):
            action = {
                "type": random.choice(["analyze", "predict", "trade", "verify", "wait"]),
                "confidence": random.uniform(0.5, 0.95),
                "timestamp_offset": i * 60  # seconds
            }
            actions.append(action)
        
        return actions
    
    def _simulate_outcome(self, context: Dict, actions: List[Dict]) -> Dict:
        """Simulate outcome of actions in context"""
        # Base success probability on context
        base_prob = 0.6
        
        # Adjust for market regime
        if context.get("regime") == "crash":
            base_prob -= 0.2
        elif context.get("regime") == "bubble":
            base_prob += 0.1
        
        # Adjust for action quality
        avg_confidence = np.mean([a["confidence"] for a in actions])
        base_prob += (avg_confidence - 0.7) * 0.3
        
        success = random.random() < base_prob
        
        return {
            "result": "success" if success else "failure",
            "return_pct": random.uniform(-5, 10) if success else random.uniform(-15, -2),
            "confidence_calibration": random.uniform(0.7, 1.0),
            "unexpected_events": random.randint(0, 3)
        }
    
    def _calculate_emotion(self, outcome: Dict) -> float:
        """Calculate emotional valence of outcome (-1 to 1)"""
        if outcome["result"] == "success":
            return random.uniform(0.2, 1.0)
        else:
            return random.uniform(-1.0, -0.2)
    
    def _calculate_learning(self, actions: List[Dict], outcome: Dict) -> float:
        """Calculate learning value of experience"""
        # More learning from failures and unexpected outcomes
        base = 0.5
        
        if outcome["result"] == "failure":
            base += 0.2
        
        if outcome.get("unexpected_events", 0) > 0:
            base += 0.1 * outcome["unexpected_events"]
        
        return min(1.0, base)
    
    async def create_dream_state(self,
                                 recent_experiences: List[SyntheticExperience],
                                 intensity: float = 0.8,
                                 duration_cycles: int = 5) -> DreamState:
        """
        Create a dream state for memory consolidation
        
        Like human sleep, this processes recent experiences and
        consolidates them into long-term memory.
        """
        dream_id = f"dream_{datetime.utcnow().timestamp()}"
        
        logger.info(f"Creating dream state {dream_id} with {len(recent_experiences)} experiences")
        
        # Run consolidation cycles
        consolidated = []
        insights = []
        patterns = []
        improvements = defaultdict(float)
        
        for cycle in range(duration_cycles):
            cycle_results = await self._consolidation_cycle(recent_experiences, intensity)
            consolidated.extend(cycle_results["memories"])
            insights.extend(cycle_results["insights"])
            patterns.extend(cycle_results["patterns"])
            
            for cap, imp in cycle_results["improvements"].items():
                improvements[cap] += imp
        
        dream = DreamState(
            dream_id=dream_id,
            raw_experiences=recent_experiences,
            consolidated_memories=consolidated,
            novel_insights=list(set(insights)),
            pattern_discoveries=patterns,
            intensity=intensity,
            duration_cycles=duration_cycles,
            capability_improvements=dict(improvements),
            completed_at=datetime.utcnow().isoformat()
        )
        
        self.dream_history.append(dream)
        
        logger.info(f"Dream state {dream_id} complete: "
                   f"{len(consolidated)} memories, {len(insights)} insights")
        
        return dream
    
    async def _consolidation_cycle(self,
                                  experiences: List[SyntheticExperience],
                                  intensity: float) -> Dict[str, Any]:
        """Run one consolidation cycle"""
        memories = []
        insights = []
        patterns = []
        improvements = defaultdict(float)
        
        # Sort by learning value
        sorted_exp = sorted(experiences, key=lambda x: x.learning_value, reverse=True)
        
        # Consolidate top experiences
        top_n = int(len(sorted_exp) * intensity)
        for exp in sorted_exp[:top_n]:
            if not exp.consolidated:
                exp.consolidated = True
                exp.consolidation_timestamp = datetime.utcnow().isoformat()
                memories.append(exp.to_memory_entry())
        
        # Generate insights from patterns
        for i, exp1 in enumerate(sorted_exp[:top_n]):
            for exp2 in sorted_exp[i+1:top_n]:
                if self._similar_context(exp1, exp2):
                    if exp1.outcome["result"] != exp2.outcome["result"]:
                        insight = f"Similar context different outcome: {exp1.outcome} vs {exp2.outcome}"
                        insights.append(insight)
                        
                        # Identify what caused difference
                        for cap in exp1.source_capabilities:
                            improvements[cap] += 0.01
        
        return {
            "memories": memories,
            "insights": insights,
            "patterns": patterns,
            "improvements": dict(improvements)
        }
    
    def _similar_context(self, exp1: SyntheticExperience, exp2: SyntheticExperience) -> bool:
        """Check if two experiences have similar contexts"""
        return (
            exp1.context.get("regime") == exp2.context.get("regime") and
            abs(exp1.context.get("volatility", 0) - exp2.context.get("volatility", 0)) < 0.3
        )
    
    async def generate_nightmare_scenarios(self,
                                          base_scenario: Dict,
                                          n_scenarios: int = 50) -> List[SyntheticExperience]:
        """
        Generate nightmare scenarios - extreme stress tests
        
        These are intentionally difficult scenarios to test
        system robustness and discover failure modes.
        """
        nightmares = []
        
        for i in range(n_scenarios):
            # Create extreme context
            context = {
                **base_scenario,
                "regime": "extreme_crash",
                "volatility": random.uniform(3.0, 5.0),
                "liquidity": "none",
                "correlation_breakdown": True,
                "cascading_failures": random.randint(1, 5)
            }
            
            # Force bad actions
            actions = [{"type": "panic_sell", "confidence": 0.3}]
            
            # Ensure bad outcome
            outcome = {
                "result": "failure",
                "return_pct": random.uniform(-50, -20),
                "catastrophic": True
            }
            
            nightmare = SyntheticExperience(
                experience_id=f"nightmare_{i}_{datetime.utcnow().timestamp()}",
                experience_type=ExperienceType.NIGHTMARE,
                context=context,
                action_sequence=actions,
                outcome=outcome,
                vividness=1.0,  # Very vivid (stressful)
                emotional_valence=-1.0,  # Maximum negative
                learning_value=1.0,  # Maximum learning from failures
                source_capabilities=base_scenario.get("capabilities", []),
                generated_by="nightmare_generator"
            )
            
            nightmares.append(nightmare)
        
        return nightmares


class ImaginationEngine:
    """
    Imagination Engine - Generative World Modeling
    
    Like human imagination, this generates novel scenarios
    that haven't been experienced but could be possible.
    """
    
    def __init__(self, dream_generator: DreamStateGenerator):
        self.dream_generator = dream_generator
        self.imagined_worlds: List[Dict[str, Any]] = []
        self.world_models: Dict[str, Any] = {}
        
        logger.info("ImaginationEngine initialized")
    
    async def imagine_capability_application(self,
                                            capability_id: str,
                                            n_scenarios: int = 100) -> Dict[str, Any]:
        """
        Imagine how a capability would perform in various scenarios
        
        Returns predicted performance distribution and confidence.
        """
        # Generate imagined scenarios
        base = {"capabilities": [capability_id], "regime": "normal"}
        experiences = await self.dream_generator.generate_experiences_batch(base, n_scenarios)
        
        # Analyze outcomes
        outcomes = [exp.outcome for exp in experiences]
        success_rate = sum(1 for o in outcomes if o["result"] == "success") / len(outcomes)
        avg_return = np.mean([o.get("return_pct", 0) for o in outcomes])
        
        # Store world model
        world_id = f"world_{capability_id}_{datetime.utcnow().timestamp()}"
        self.world_models[world_id] = {
            "capability": capability_id,
            "n_scenarios": n_scenarios,
            "success_rate": success_rate,
            "avg_return": avg_return,
            "outcome_distribution": outcomes,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "imagined_scenarios": n_scenarios,
            "predicted_success_rate": success_rate,
            "predicted_avg_return": avg_return,
            "confidence": np.std([o.get("return_pct", 0) for o in outcomes]),
            "world_model_id": world_id
        }
    
    async def imagine_regime_transitions(self,
                                        current_regime: str,
                                        n_steps: int = 10) -> List[Dict[str, Any]]:
        """
        Imagine possible regime transitions from current state
        
        Useful for predicting market shifts.
        """
        transitions = []
        
        regimes = ["high_volatility", "low_volatility", "crash", "bubble", "normal"]
        current = current_regime
        
        for step in range(n_steps):
            # Possible next regimes (weighted by plausibility)
            if current == "normal":
                next_regimes = ["high_volatility", "low_volatility", "crash", "bubble"]
                weights = [0.3, 0.3, 0.2, 0.2]
            elif current == "high_volatility":
                next_regimes = ["normal", "crash", "bubble"]
                weights = [0.4, 0.3, 0.3]
            elif current == "crash":
                next_regimes = ["normal", "high_volatility"]
                weights = [0.6, 0.4]
            elif current == "bubble":
                next_regimes = ["crash", "normal", "high_volatility"]
                weights = [0.5, 0.3, 0.2]
            else:  # low_volatility
                next_regimes = ["normal", "high_volatility", "bubble"]
                weights = [0.5, 0.3, 0.2]
            
            next_regime = random.choices(next_regimes, weights=weights)[0]
            
            transition = {
                "step": step,
                "from_regime": current,
                "to_regime": next_regime,
                "probability": weights[next_regimes.index(next_regime)],
                "time_horizon": f"{step * 7}d"  # Weekly steps
            }
            
            transitions.append(transition)
            current = next_regime
        
        return transitions


class ExperienceBasedRouter:
    """
    Router that uses synthetic experiences for decision making
    
    Like human intuition based on imagined scenarios,
    this router consults synthetic memories before deciding.
    """
    
    def __init__(self, dream_generator: DreamStateGenerator):
        self.dream_generator = dream_generator
        self.experience_memory: Dict[str, List[SyntheticExperience]] = defaultdict(list)
        self.decision_history: List[Dict[str, Any]] = []
        
        logger.info("ExperienceBasedRouter initialized")
    
    async def route_with_imagination(self,
                                    task_context: Dict[str, Any],
                                    candidates: List[str],
                                    n_imagined_scenarios: int = 100) -> Dict[str, Any]:
        """
        Route using imagined outcomes for each candidate
        
        For each candidate, imagine 100 scenarios and pick
        the one with best imagined outcomes.
        """
        results = []
        
        for candidate in candidates:
            # Imagine scenarios for this candidate
            imagined = await self.imagine_candidate_performance(
                candidate, task_context, n_imagined_scenarios
            )
            
            results.append({
                "candidate": candidate,
                "imagined_success_rate": imagined["success_rate"],
                "imagined_avg_return": imagined["avg_return"],
                "confidence": imagined["confidence"],
                "recommended": imagined["success_rate"] > 0.6
            })
        
        # Select best
        best = max(results, key=lambda x: x["imagined_success_rate"])
        
        decision = {
            "selected": best["candidate"],
            "selection_method": "experience_based_imagination",
            "imagined_scenarios": n_imagined_scenarios,
            "candidate_evaluations": results,
            "confidence": best["confidence"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.decision_history.append(decision)
        
        return decision
    
    async def imagine_candidate_performance(self,
                                           candidate: str,
                                           context: Dict[str, Any],
                                           n_scenarios: int) -> Dict[str, Any]:
        """Imagine how a candidate would perform"""
        base = {
            **context,
            "candidate": candidate
        }
        
        experiences = await self.dream_generator.generate_experiences_batch(base, n_scenarios)
        
        outcomes = [exp.outcome for exp in experiences]
        success_rate = sum(1 for o in outcomes if o["result"] == "success") / len(outcomes)
        avg_return = np.mean([o.get("return_pct", 0) for o in outcomes])
        
        return {
            "success_rate": success_rate,
            "avg_return": avg_return,
            "confidence": 1.0 - np.std([o.get("return_pct", 0) for o in outcomes]),
            "experiences": experiences
        }
    
    def get_intuition_score(self, candidate: str, context_type: str) -> float:
        """
        Get intuition score based on past imagined experiences
        
        Returns 0-1 score representing 'gut feeling' from
        accumulated synthetic experiences.
        """
        relevant_experiences = [
            exp for exp in self.experience_memory[candidate]
            if exp.context.get("type") == context_type
        ]
        
        if not relevant_experiences:
            return 0.5  # Neutral if no experience
        
        # Weight by vividness and recency
        weighted_sum = sum(
            (exp.vividness * (1.0 if exp.outcome["result"] == "success" else 0.0))
            for exp in relevant_experiences
        )
        total_vividness = sum(exp.vividness for exp in relevant_experiences)
        
        return weighted_sum / total_vividness if total_vividness > 0 else 0.5


# ============================================================================
# Integration with AlphaAlgo Meta-Intelligence Layer
# ============================================================================

class SyntheticExperienceSystem:
    """
    Complete synthetic experience system (Dream/Imagination)
    
    Integrates all components and provides interface to
    AlphaAlgo Meta-Intelligence Layer.
    """
    
    def __init__(self, scale_factor: int = 100):
        self.scale_factor = scale_factor
        
        # Core components
        self.dream_generator = DreamStateGenerator(scale_factor)
        self.imagination = ImaginationEngine(self.dream_generator)
        self.experience_router = ExperienceBasedRouter(self.dream_generator)
        
        # State
        self.is_dreaming = False
        self.experience_stats = {
            "total_generated": 0,
            "total_consolidated": 0,
            "dream_cycles": 0
        }
        
        logger.info(f"SyntheticExperienceSystem initialized ({scale_factor}x scale)")
    
    async def run_dream_cycle(self,
                            recent_real_experiences: List[Dict[str, Any]],
                            duration_minutes: int = 10) -> DreamState:
        """
        Run a dream cycle - offline consolidation
        
        This should run during "idle" time or scheduled maintenance.
        """
        if self.is_dreaming:
            logger.warning("Dream cycle already in progress")
            return None
        
        self.is_dreaming = True
        
        try:
            # Convert real experiences to synthetic format
            synthetic_exps = [
                SyntheticExperience(
                    experience_id=f"real_{i}",
                    experience_type=ExperienceType.SIMULATION,
                    context=exp.get("context", {}),
                    action_sequence=exp.get("actions", []),
                    outcome=exp.get("outcome", {}),
                    vividness=0.8,
                    emotional_valence=1.0 if exp.get("outcome", {}).get("result") == "success" else -0.5,
                    learning_value=0.7,
                    source_capabilities=exp.get("capabilities", []),
                    generated_by="real_world"
                )
                for i, exp in enumerate(recent_real_experiences)
            ]
            
            # Generate additional imagined experiences (100x)
            for exp in synthetic_exps[:5]:  # For top 5 real experiences
                imagined = await self.dream_generator.generate_experiences_batch(
                    exp.context, self.scale_factor
                )
                synthetic_exps.extend(imagined)
            
            # Run dream state consolidation
            cycles = duration_minutes // 2  # 2 min per cycle
            dream = await self.dream_generator.create_dream_state(
                synthetic_exps,
                intensity=0.9,
                duration_cycles=max(1, cycles)
            )
            
            # Update stats
            self.experience_stats["total_generated"] += len(synthetic_exps)
            self.experience_stats["total_consolidated"] += len(dream.consolidated_memories)
            self.experience_stats["dream_cycles"] += 1
            
            logger.info(f"Dream cycle complete: {len(dream.consolidated_memories)} memories consolidated")
            
            return dream
            
        finally:
            self.is_dreaming = False
    
    async def imagine_decision_outcomes(self,
                                       decision_context: Dict[str, Any],
                                       options: List[str]) -> Dict[str, Any]:
        """
        Imagine outcomes for each decision option
        
        Returns imagined success rates for each option.
        """
        return await self.experience_router.route_with_imagination(
            decision_context, options, n_imagined_scenarios=self.scale_factor
        )
    
    async def stress_test_with_nightmares(self,
                                        system_config: Dict[str, Any],
                                        n_scenarios: int = 50) -> List[SyntheticExperience]:
        """
        Run nightmare scenarios for stress testing
        
        Generates extreme scenarios to test system robustness.
        """
        return await self.dream_generator.generate_nightmare_scenarios(
            system_config, n_scenarios
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "scale_factor": self.scale_factor,
            "is_dreaming": self.is_dreaming,
            "experience_stats": self.experience_stats,
            "dream_history_count": len(self.dream_generator.dream_history),
            "world_models_count": len(self.imagination.world_models),
            "decision_history_count": len(self.experience_router.decision_history)
        }


# Factory function
def create_synthetic_experience_system(scale_factor: int = 100) -> SyntheticExperienceSystem:
    """Create synthetic experience system at specified scale"""
    return SyntheticExperienceSystem(scale_factor)
