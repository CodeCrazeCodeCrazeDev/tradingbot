"""
NEUROS-FI Region 9: Default Mode Network - Offline Learning and Prospective Simulation
=======================================================================================

Biological Basis:
The DMN activates when the brain is not engaged with external stimuli — during
rest and sleep. It is not inactive: it replays memories, simulates future scenarios,
and consolidates learning. During slow-wave sleep, the hippocampus transfers
memories to the neocortex for integration into long-term schema.

This is the biological basis of "sleeping on a problem."

Citations:
- Raichle et al. (2001) - A default mode of brain function
- Buckner et al. (2008) - The brain's default network
- Andrews-Hanna (2012) - The brain's default network and its adaptive role in internal mentation
- Diekelmann & Born (2010) - The memory function of sleep

Constitutional Version: 5.0
"""

import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class DMNState(Enum):
    """Default Mode Network states."""
    
    INACTIVE = "inactive"           # Online processing active
    LIGHT_IDLE = "light_idle"       # Low-volatility periods
    DEEP_OFFLINE = "deep_offline"   # Overnight/weekend
    CONSOLIDATING = "consolidating" # Active consolidation


class ReplayType(Enum):
    """Types of memory replay."""
    
    SEQUENTIAL = auto()    # Replay in order
    RANDOM = auto()        # Random sampling
    PRIORITY = auto()      # Weighted by importance
    COUNTERFACTUAL = auto() # What-if scenarios


class SimulationType(Enum):
    """Types of prospective simulation."""
    
    FORWARD = auto()       # Simulate future scenarios
    STRESS = auto()        # Stress test scenarios
    CREATIVE = auto()      # Novel combinations
    TRANSFER = auto()      # Cross-domain transfer


@dataclass
class MemoryReplaySession:
    """A memory replay session."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    replay_type: ReplayType
    memories_replayed: int
    patterns_reinforced: int
    insights_generated: int
    consolidation_score: float


@dataclass
class ProspectiveScenario:
    """A prospective (future) scenario simulation."""
    
    scenario_id: str
    timestamp: datetime
    simulation_type: SimulationType
    
    # Scenario details
    initial_conditions: Dict[str, Any]
    simulated_trajectory: List[Dict[str, Any]]
    outcome: Dict[str, Any]
    
    # Analysis
    risk_identified: List[str]
    opportunities_identified: List[str]
    portfolio_impact: float
    confidence: float


@dataclass
class CrossDomainHypothesis:
    """A hypothesis generated from cross-domain combination."""
    
    hypothesis_id: str
    timestamp: datetime
    source_domains: List[str]
    hypothesis: str
    rationale: str
    testable_prediction: str
    confidence: float
    status: str = "pending"  # pending, testing, validated, rejected


@dataclass
class ConsolidationResult:
    """Result of overnight consolidation."""
    
    consolidation_id: str
    start_time: datetime
    end_time: datetime
    
    # What was consolidated
    memories_processed: int
    factors_updated: int
    weights_consolidated: int
    
    # Outcomes
    world_model_delta: float
    new_patterns_discovered: int
    patterns_pruned: int


class MemoryReplay:
    """
    Memory Replay System - replays memories for consolidation.
    
    During offline windows, the system replays the day's hippocampal memories
    against the full historical data — running a generative model of
    "what if this signal pattern had appeared in every prior market regime"
    to generalize learning beyond the single observed context.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Memory buffer for replay
        self._replay_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 10000
        
        # Replay sessions
        self._sessions: List[MemoryReplaySession] = []
        self._current_session: Optional[MemoryReplaySession] = None
        
        # Replay parameters
        self._replay_batch_size = 32
        self._priority_exponent = 0.6  # For prioritized replay
    
    def add_memory(self, memory: Dict[str, Any], priority: float = 1.0):
        """Add a memory to the replay buffer."""
        with self._lock:
            memory['_priority'] = priority
            memory['_timestamp'] = datetime.utcnow()
            
            self._replay_buffer.append(memory)
            
            if len(self._replay_buffer) > self._max_buffer_size:
                # Remove lowest priority memories
                self._replay_buffer.sort(key=lambda m: m.get('_priority', 0))
                self._replay_buffer = self._replay_buffer[-self._max_buffer_size//2:]
    
    def start_replay_session(self, replay_type: ReplayType) -> str:
        """Start a new replay session."""
        with self._lock:
            session_id = f"replay_{int(time.time())}"
            
            self._current_session = MemoryReplaySession(
                session_id=session_id,
                start_time=datetime.utcnow(),
                end_time=None,
                replay_type=replay_type,
                memories_replayed=0,
                patterns_reinforced=0,
                insights_generated=0,
                consolidation_score=0.0,
            )
            
            return session_id
    
    def replay_batch(
        self,
        replay_type: ReplayType = ReplayType.PRIORITY
    ) -> List[Dict[str, Any]]:
        """
        Replay a batch of memories.
        
        Returns memories for processing by the neocortex.
        """
        with self._lock:
            if not self._replay_buffer:
                return []
            
            if replay_type == ReplayType.SEQUENTIAL:
                # Replay in chronological order
                batch = sorted(
                    self._replay_buffer,
                    key=lambda m: m.get('_timestamp', datetime.min)
                )[:self._replay_batch_size]
                
            elif replay_type == ReplayType.RANDOM:
                # Random sampling
                batch = random.sample(
                    self._replay_buffer,
                    min(self._replay_batch_size, len(self._replay_buffer))
                )
                
            elif replay_type == ReplayType.PRIORITY:
                # Prioritized sampling
                priorities = np.array([
                    m.get('_priority', 1.0) ** self._priority_exponent
                    for m in self._replay_buffer
                ])
                priorities = priorities / priorities.sum()
                
                indices = np.random.choice(
                    len(self._replay_buffer),
                    size=min(self._replay_batch_size, len(self._replay_buffer)),
                    replace=False,
                    p=priorities
                )
                batch = [self._replay_buffer[i] for i in indices]
                
            else:  # COUNTERFACTUAL
                # Sample for counterfactual analysis
                batch = random.sample(
                    self._replay_buffer,
                    min(self._replay_batch_size, len(self._replay_buffer))
                )
            
            if self._current_session:
                self._current_session.memories_replayed += len(batch)
            
            return batch
    
    def end_replay_session(self) -> Optional[MemoryReplaySession]:
        """End the current replay session."""
        with self._lock:
            if self._current_session:
                self._current_session.end_time = datetime.utcnow()
                self._sessions.append(self._current_session)
                
                result = self._current_session
                self._current_session = None
                
                if len(self._sessions) > 1000:
                    self._sessions = self._sessions[-500:]
                
                return result
            return None
    
    def update_session_metrics(
        self,
        patterns_reinforced: int = 0,
        insights_generated: int = 0,
        consolidation_score: float = 0.0
    ):
        """Update current session metrics."""
        with self._lock:
            if self._current_session:
                self._current_session.patterns_reinforced += patterns_reinforced
                self._current_session.insights_generated += insights_generated
                self._current_session.consolidation_score = consolidation_score
    
    def get_buffer_size(self) -> int:
        """Get current replay buffer size."""
        with self._lock:
            return len(self._replay_buffer)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get replay statistics."""
        with self._lock:
            return {
                'buffer_size': len(self._replay_buffer),
                'total_sessions': len(self._sessions),
                'current_session_active': self._current_session is not None,
            }


class ProspectiveSimulation:
    """
    Prospective Simulation System - generates forward simulations.
    
    The DMN generates forward simulations of possible market futures —
    not from random seeds but from recombinations of historical memory patterns.
    These scenarios stress-test current portfolio construction.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Historical patterns for recombination
        self._historical_patterns: List[Dict[str, Any]] = []
        
        # Generated scenarios
        self._scenarios: List[ProspectiveScenario] = []
        
        # Simulation parameters
        self._simulation_horizon_days = 30
        self._num_trajectories = 100
    
    def add_historical_pattern(self, pattern: Dict[str, Any]):
        """Add a historical pattern for recombination."""
        with self._lock:
            self._historical_patterns.append(pattern)
            
            if len(self._historical_patterns) > 10000:
                self._historical_patterns = self._historical_patterns[-5000:]
    
    def simulate_forward(
        self,
        initial_conditions: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> ProspectiveScenario:
        """
        Simulate forward from current conditions.
        
        Generates possible future trajectories by recombining historical patterns.
        """
        with self._lock:
            # Generate trajectory by sampling and recombining patterns
            trajectory = []
            current_state = initial_conditions.copy()
            
            for day in range(self._simulation_horizon_days):
                # Sample a historical pattern
                if self._historical_patterns:
                    pattern = random.choice(self._historical_patterns)
                    
                    # Apply pattern to current state
                    next_state = self._apply_pattern(current_state, pattern)
                else:
                    # Random walk if no patterns
                    next_state = self._random_step(current_state)
                
                trajectory.append(next_state)
                current_state = next_state
            
            # Analyze trajectory
            risks = self._identify_risks(trajectory, portfolio_state)
            opportunities = self._identify_opportunities(trajectory, portfolio_state)
            impact = self._calculate_portfolio_impact(trajectory, portfolio_state)
            
            scenario = ProspectiveScenario(
                scenario_id=f"sim_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                simulation_type=SimulationType.FORWARD,
                initial_conditions=initial_conditions,
                simulated_trajectory=trajectory,
                outcome=trajectory[-1] if trajectory else {},
                risk_identified=risks,
                opportunities_identified=opportunities,
                portfolio_impact=impact,
                confidence=0.5,  # Base confidence
            )
            
            self._scenarios.append(scenario)
            if len(self._scenarios) > 1000:
                self._scenarios = self._scenarios[-500:]
            
            return scenario
    
    def simulate_stress(
        self,
        stress_scenario: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> ProspectiveScenario:
        """
        Simulate a stress scenario.
        
        Tests portfolio resilience under adverse conditions.
        """
        with self._lock:
            # Apply stress to initial conditions
            stressed_conditions = self._apply_stress(stress_scenario)
            
            # Generate stressed trajectory
            trajectory = []
            current_state = stressed_conditions.copy()
            
            for day in range(self._simulation_horizon_days):
                # Stressed evolution
                next_state = self._stressed_step(current_state, stress_scenario)
                trajectory.append(next_state)
                current_state = next_state
            
            # Analyze impact
            risks = self._identify_risks(trajectory, portfolio_state)
            impact = self._calculate_portfolio_impact(trajectory, portfolio_state)
            
            scenario = ProspectiveScenario(
                scenario_id=f"stress_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                simulation_type=SimulationType.STRESS,
                initial_conditions=stressed_conditions,
                simulated_trajectory=trajectory,
                outcome=trajectory[-1] if trajectory else {},
                risk_identified=risks,
                opportunities_identified=[],
                portfolio_impact=impact,
                confidence=0.7,  # Higher confidence for stress tests
            )
            
            self._scenarios.append(scenario)
            return scenario
    
    def _apply_pattern(
        self,
        state: Dict[str, Any],
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a historical pattern to current state."""
        next_state = state.copy()
        
        # Apply pattern changes
        for key, value in pattern.items():
            if key in state and isinstance(value, (int, float)):
                # Apply as percentage change
                next_state[key] = state[key] * (1 + value * 0.01)
        
        return next_state
    
    def _random_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a random step."""
        next_state = state.copy()
        
        for key, value in state.items():
            if isinstance(value, (int, float)):
                # Random walk
                next_state[key] = value * (1 + np.random.randn() * 0.01)
        
        return next_state
    
    def _apply_stress(self, stress_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stress scenario to generate initial conditions."""
        return {
            'volatility': stress_scenario.get('volatility_multiplier', 2.0) * 0.02,
            'correlation': stress_scenario.get('correlation', 0.8),
            'liquidity': stress_scenario.get('liquidity_factor', 0.5),
            'spread': stress_scenario.get('spread_multiplier', 3.0) * 0.001,
        }
    
    def _stressed_step(
        self,
        state: Dict[str, Any],
        stress: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a stressed step."""
        next_state = state.copy()
        
        # Higher volatility during stress
        vol_mult = stress.get('volatility_multiplier', 2.0)
        
        for key, value in state.items():
            if isinstance(value, (int, float)):
                next_state[key] = value * (1 + np.random.randn() * 0.01 * vol_mult)
        
        return next_state
    
    def _identify_risks(
        self,
        trajectory: List[Dict[str, Any]],
        portfolio: Dict[str, Any]
    ) -> List[str]:
        """Identify risks in a trajectory."""
        risks = []
        
        if not trajectory:
            return risks
        
        # Check for drawdown
        values = [t.get('portfolio_value', 100) for t in trajectory]
        max_val = max(values)
        min_val = min(values)
        drawdown = (max_val - min_val) / max_val if max_val > 0 else 0
        
        if drawdown > 0.1:
            risks.append(f"Potential drawdown: {drawdown:.1%}")
        
        # Check for volatility spike
        if trajectory[-1].get('volatility', 0) > 0.03:
            risks.append("High volatility environment")
        
        return risks
    
    def _identify_opportunities(
        self,
        trajectory: List[Dict[str, Any]],
        portfolio: Dict[str, Any]
    ) -> List[str]:
        """Identify opportunities in a trajectory."""
        opportunities = []
        
        if not trajectory:
            return opportunities
        
        # Check for positive trend
        if len(trajectory) >= 2:
            start_val = trajectory[0].get('portfolio_value', 100)
            end_val = trajectory[-1].get('portfolio_value', 100)
            
            if end_val > start_val * 1.05:
                opportunities.append(f"Potential gain: {(end_val/start_val - 1):.1%}")
        
        return opportunities
    
    def _calculate_portfolio_impact(
        self,
        trajectory: List[Dict[str, Any]],
        portfolio: Dict[str, Any]
    ) -> float:
        """Calculate portfolio impact from trajectory."""
        if not trajectory:
            return 0.0
        
        start_val = trajectory[0].get('portfolio_value', 100)
        end_val = trajectory[-1].get('portfolio_value', 100)
        
        return (end_val - start_val) / start_val if start_val > 0 else 0.0
    
    def get_recent_scenarios(self, limit: int = 10) -> List[ProspectiveScenario]:
        """Get recent scenarios."""
        with self._lock:
            return self._scenarios[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        with self._lock:
            return {
                'historical_patterns': len(self._historical_patterns),
                'scenarios_generated': len(self._scenarios),
            }


class SpontaneousHypothesisGeneration:
    """
    Spontaneous Hypothesis Generation - creative recombination.
    
    Like the creative recombination that happens in REM sleep, the DMN's
    offline processing combines signals from disparate domains in ways
    that the online system would not generate.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Domain knowledge
        self._domain_signals: Dict[str, List[Dict[str, Any]]] = {}
        
        # Generated hypotheses
        self._hypotheses: List[CrossDomainHypothesis] = []
    
    def add_domain_signal(self, domain: str, signal: Dict[str, Any]):
        """Add a signal from a domain."""
        with self._lock:
            if domain not in self._domain_signals:
                self._domain_signals[domain] = []
            
            self._domain_signals[domain].append(signal)
            
            if len(self._domain_signals[domain]) > 1000:
                self._domain_signals[domain] = self._domain_signals[domain][-500:]
    
    def generate_cross_domain_hypothesis(self) -> Optional[CrossDomainHypothesis]:
        """
        Generate a cross-domain hypothesis by combining signals.
        
        Example: "What satellite data from shipping ports might predict
        about semiconductor inventory cycles"
        """
        with self._lock:
            if len(self._domain_signals) < 2:
                return None
            
            # Select two random domains
            domains = list(self._domain_signals.keys())
            domain1, domain2 = random.sample(domains, 2)
            
            # Get recent signals from each
            signals1 = self._domain_signals[domain1][-10:]
            signals2 = self._domain_signals[domain2][-10:]
            
            if not signals1 or not signals2:
                return None
            
            # Generate hypothesis
            hypothesis = CrossDomainHypothesis(
                hypothesis_id=f"hyp_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                source_domains=[domain1, domain2],
                hypothesis=f"Signals from {domain1} may predict {domain2} movements",
                rationale=f"Cross-domain correlation exploration between {domain1} and {domain2}",
                testable_prediction=f"When {domain1} signal > threshold, {domain2} moves in same direction",
                confidence=0.3,  # Low initial confidence
            )
            
            self._hypotheses.append(hypothesis)
            if len(self._hypotheses) > 1000:
                self._hypotheses = self._hypotheses[-500:]
            
            return hypothesis
    
    def get_pending_hypotheses(self) -> List[CrossDomainHypothesis]:
        """Get hypotheses pending validation."""
        with self._lock:
            return [h for h in self._hypotheses if h.status == "pending"]
    
    def update_hypothesis_status(
        self,
        hypothesis_id: str,
        status: str,
        confidence: Optional[float] = None
    ):
        """Update hypothesis status after testing."""
        with self._lock:
            for h in self._hypotheses:
                if h.hypothesis_id == hypothesis_id:
                    h.status = status
                    if confidence is not None:
                        h.confidence = confidence
                    break
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get hypothesis generation statistics."""
        with self._lock:
            statuses = [h.status for h in self._hypotheses]
            return {
                'domains_tracked': len(self._domain_signals),
                'total_hypotheses': len(self._hypotheses),
                'pending': statuses.count('pending'),
                'validated': statuses.count('validated'),
                'rejected': statuses.count('rejected'),
            }


class OvernightConsolidation:
    """
    Overnight Consolidation Pipeline - the complete learning cycle.
    
    Orchestrates:
    - Hippocampal provisional memories → replay
    - Neocortical integration
    - Factor library update
    - Model weight consolidation
    - Next-day world model initialization
    """
    
    def __init__(
        self,
        memory_replay: MemoryReplay,
        prospective_simulation: ProspectiveSimulation,
        hypothesis_generation: SpontaneousHypothesisGeneration
    ):
        self._memory_replay = memory_replay
        self._prospective_simulation = prospective_simulation
        self._hypothesis_generation = hypothesis_generation
        
        self._lock = threading.RLock()
        
        # Consolidation history
        self._consolidations: List[ConsolidationResult] = []
        
        # Consolidation state
        self._is_consolidating = False
        self._last_consolidation: Optional[datetime] = None
    
    def run_consolidation(
        self,
        hippocampal_memories: List[Dict[str, Any]],
        factor_library: Dict[str, Any],
        model_weights: Dict[str, np.ndarray]
    ) -> ConsolidationResult:
        """
        Run the complete overnight consolidation pipeline.
        """
        with self._lock:
            if self._is_consolidating:
                raise RuntimeError("Consolidation already in progress")
            
            self._is_consolidating = True
            start_time = datetime.utcnow()
            
            try:
                # Step 1: Add memories to replay buffer
                for memory in hippocampal_memories:
                    self._memory_replay.add_memory(memory)
                
                # Step 2: Start replay session
                self._memory_replay.start_replay_session(ReplayType.PRIORITY)
                
                # Step 3: Replay memories and extract patterns
                patterns_reinforced = 0
                for _ in range(10):  # 10 replay batches
                    batch = self._memory_replay.replay_batch(ReplayType.PRIORITY)
                    patterns_reinforced += len(batch)
                    
                    # Add patterns to prospective simulation
                    for memory in batch:
                        self._prospective_simulation.add_historical_pattern(memory)
                
                # Step 4: Generate prospective scenarios
                for _ in range(5):
                    self._prospective_simulation.simulate_forward(
                        {'volatility': 0.02, 'correlation': 0.3},
                        {}
                    )
                
                # Step 5: Generate cross-domain hypotheses
                new_hypotheses = 0
                for _ in range(3):
                    hyp = self._hypothesis_generation.generate_cross_domain_hypothesis()
                    if hyp:
                        new_hypotheses += 1
                
                # Step 6: End replay session
                session = self._memory_replay.end_replay_session()
                
                # Step 7: Consolidate model weights (simplified)
                weights_consolidated = len(model_weights)
                
                # Create result
                result = ConsolidationResult(
                    consolidation_id=f"consol_{int(time.time())}",
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    memories_processed=len(hippocampal_memories),
                    factors_updated=len(factor_library),
                    weights_consolidated=weights_consolidated,
                    world_model_delta=0.01,  # Placeholder
                    new_patterns_discovered=new_hypotheses,
                    patterns_pruned=0,
                )
                
                self._consolidations.append(result)
                if len(self._consolidations) > 100:
                    self._consolidations = self._consolidations[-50:]
                
                self._last_consolidation = datetime.utcnow()
                
                return result
                
            finally:
                self._is_consolidating = False
    
    def get_last_consolidation_time(self) -> Optional[datetime]:
        """Get time of last consolidation."""
        return self._last_consolidation
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        with self._lock:
            return {
                'total_consolidations': len(self._consolidations),
                'is_consolidating': self._is_consolidating,
                'last_consolidation': self._last_consolidation.isoformat() if self._last_consolidation else None,
            }


class DefaultModeNetwork:
    """
    The complete Default Mode Network - offline learning and prospective simulation.
    
    Implements:
    - Memory replay (prioritized, sequential, counterfactual)
    - Prospective simulation (forward, stress)
    - Spontaneous hypothesis generation
    - Overnight consolidation pipeline
    """
    
    def __init__(self):
        # Initialize components
        self.memory_replay = MemoryReplay()
        self.prospective_simulation = ProspectiveSimulation()
        self.hypothesis_generation = SpontaneousHypothesisGeneration()
        self.consolidation = OvernightConsolidation(
            self.memory_replay,
            self.prospective_simulation,
            self.hypothesis_generation
        )
        
        self._lock = threading.RLock()
        self._state = DMNState.INACTIVE
        
        logger.info("Default Mode Network initialized - offline learning active")
    
    def enter_offline_mode(self, mode: DMNState = DMNState.LIGHT_IDLE):
        """Enter offline processing mode."""
        with self._lock:
            self._state = mode
            logger.info(f"DMN entering {mode.value} mode")
    
    def exit_offline_mode(self):
        """Exit offline processing mode."""
        with self._lock:
            self._state = DMNState.INACTIVE
            logger.info("DMN returning to inactive (online processing active)")
    
    def is_offline(self) -> bool:
        """Check if DMN is in offline mode."""
        return self._state != DMNState.INACTIVE
    
    def add_memory_for_replay(self, memory: Dict[str, Any], priority: float = 1.0):
        """Add a memory for later replay."""
        self.memory_replay.add_memory(memory, priority)
    
    def add_domain_signal(self, domain: str, signal: Dict[str, Any]):
        """Add a domain signal for hypothesis generation."""
        self.hypothesis_generation.add_domain_signal(domain, signal)
    
    def run_offline_cycle(
        self,
        hippocampal_memories: List[Dict[str, Any]],
        factor_library: Dict[str, Any],
        model_weights: Dict[str, np.ndarray],
        portfolio_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a complete offline processing cycle.
        
        This is the "sleeping on a problem" equivalent.
        """
        with self._lock:
            self._state = DMNState.CONSOLIDATING
            
            results = {
                'consolidation': None,
                'scenarios': [],
                'hypotheses': [],
            }
            
            try:
                # Run consolidation
                consolidation = self.consolidation.run_consolidation(
                    hippocampal_memories,
                    factor_library,
                    model_weights
                )
                results['consolidation'] = consolidation
                
                # Generate prospective scenarios
                for _ in range(3):
                    scenario = self.prospective_simulation.simulate_forward(
                        {'volatility': 0.02},
                        portfolio_state
                    )
                    results['scenarios'].append(scenario)
                
                # Generate hypotheses
                for _ in range(2):
                    hyp = self.hypothesis_generation.generate_cross_domain_hypothesis()
                    if hyp:
                        results['hypotheses'].append(hyp)
                
                return results
                
            finally:
                self._state = DMNState.INACTIVE
    
    def get_pending_hypotheses(self) -> List[CrossDomainHypothesis]:
        """Get hypotheses pending validation."""
        return self.hypothesis_generation.get_pending_hypotheses()
    
    def get_recent_scenarios(self, limit: int = 10) -> List[ProspectiveScenario]:
        """Get recent prospective scenarios."""
        return self.prospective_simulation.get_recent_scenarios(limit)
    
    def get_status(self) -> Dict[str, Any]:
        """Get DMN status."""
        return {
            'state': self._state.value,
            'memory_replay': self.memory_replay.get_statistics(),
            'prospective_simulation': self.prospective_simulation.get_statistics(),
            'hypothesis_generation': self.hypothesis_generation.get_statistics(),
            'consolidation': self.consolidation.get_statistics(),
        }
