"""
NEUROS-FI: Master Orchestrator - Free Energy Principle and Global Workspace
============================================================================

Core Operating Principles:
1. Free Energy Principle (Karl Friston): Minimize surprise via predictive coding
2. Global Workspace Theory (Bernard Baars): Unified decision-making from distributed specialists
3. Hebbian Learning: "Neurons that fire together, wire together"

The orchestrator coordinates all nine brain regions and five oscillation bands
into a coherent, self-improving trading intelligence.

Initialization Sequence (12 Steps):
1. Boot brainstem constitutional layer
2. Initialize thalamic routing
3. Load cortical column weights
4. Restore hippocampal memory index
5. Calibrate amygdala threat thresholds
6. Sync basal ganglia Q-tables
7. Load cerebellar forward models
8. Initialize ACC conflict monitors
9. Restore DMN offline state
10. Synchronize oscillation phases
11. Verify constitutional constraints
12. Enter active inference loop

Citations:
- Friston (2010) - The free-energy principle: a unified brain theory?
- Baars (1988) - A Cognitive Theory of Consciousness
- Hebb (1949) - The Organization of Behavior

Constitutional Version: 5.0
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .brainstem_constitutional import BrainstemConstitution, get_brainstem
from .region1_neocortex import Neocortex
from .region2_prefrontal import PrefrontalCortex
from .region3_thalamus import Thalamus
from .region4_hippocampus import Hippocampus
from .region5_amygdala import Amygdala
from .region6_basal_ganglia import BasalGanglia
from .region7_cerebellum import Cerebellum
from .region8_acc import AnteriorCingulateCortex
from .region9_dmn import DefaultModeNetwork
from .neural_oscillations import OscillationSynchronizer, OscillationBandType

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """NEUROS-FI system states."""
    
    UNINITIALIZED = "uninitialized"
    BOOTING = "booting"
    INITIALIZING = "initializing"
    CALIBRATING = "calibrating"
    ACTIVE = "active"
    OFFLINE = "offline"
    HALTED = "halted"
    ERROR = "error"


class InferenceMode(Enum):
    """Active inference modes."""
    
    EXPLOITATION = "exploitation"
    EXPLORATION = "exploration"
    BALANCED = "balanced"


@dataclass
class FreeEnergyState:
    """State of the Free Energy minimization process."""
    
    total_free_energy: float
    prediction_error: float
    model_complexity: float
    expected_free_energy: float
    information_gain: float
    pragmatic_value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GlobalWorkspaceState:
    """State of the Global Workspace."""
    
    broadcast_content: Dict[str, Any]
    attending_regions: List[str]
    competition_winner: str
    broadcast_timestamp: datetime
    coherence: float


@dataclass
class HebbianUpdate:
    """A Hebbian learning update."""
    
    source_region: str
    target_region: str
    pre_activation: float
    post_activation: float
    weight_delta: float
    timestamp: datetime


class FreeEnergyPrinciple:
    """
    Free Energy Principle Implementation
    
    Minimizes variational free energy: F = prediction_error + complexity_penalty
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._prediction_errors: List[float] = []
        self._model_complexity: float = 0.0
        self._free_energy_history: List[FreeEnergyState] = []
    
    def compute_free_energy(
        self,
        predictions: Dict[str, float],
        observations: Dict[str, float],
        model_params: int
    ) -> FreeEnergyState:
        """Compute variational free energy."""
        with self._lock:
            errors = []
            for key in predictions:
                if key in observations:
                    error = (predictions[key] - observations[key]) ** 2
                    errors.append(error)
            
            prediction_error = np.mean(errors) if errors else 0.0
            complexity_penalty = 0.001 * model_params
            total_fe = prediction_error + complexity_penalty
            
            info_gain = np.var(list(predictions.values())) if predictions else 0.0
            pragmatic = np.mean(list(predictions.values())) if predictions else 0.0
            expected_fe = -info_gain - pragmatic
            
            state = FreeEnergyState(
                total_free_energy=total_fe,
                prediction_error=prediction_error,
                model_complexity=complexity_penalty,
                expected_free_energy=expected_fe,
                information_gain=info_gain,
                pragmatic_value=pragmatic,
            )
            
            self._free_energy_history.append(state)
            return state
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get free energy statistics."""
        if not self._free_energy_history:
            return {'current_fe': 0}
        
        recent = self._free_energy_history[-100:]
        return {
            'current_fe': recent[-1].total_free_energy,
            'mean_fe': np.mean([s.total_free_energy for s in recent]),
        }


class GlobalWorkspace:
    """
    Global Workspace Theory Implementation
    
    Distributed specialists compete for access to a global workspace.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._current_broadcast: Optional[GlobalWorkspaceState] = None
        self._broadcast_history: List[GlobalWorkspaceState] = []
    
    def compete_for_workspace(
        self,
        candidates: Dict[str, Dict[str, Any]]
    ) -> GlobalWorkspaceState:
        """
        Competition for global workspace access.
        
        Returns winning broadcast.
        """
        with self._lock:
            if not candidates:
                return None
            
            # Score each candidate by salience
            scores = {}
            for region, content in candidates.items():
                salience = content.get('salience', 0.5)
                urgency = content.get('urgency', 0.5)
                confidence = content.get('confidence', 0.5)
                scores[region] = salience * 0.4 + urgency * 0.4 + confidence * 0.2
            
            # Winner takes all
            winner = max(scores, key=scores.get)
            
            broadcast = GlobalWorkspaceState(
                broadcast_content=candidates[winner],
                attending_regions=list(candidates.keys()),
                competition_winner=winner,
                broadcast_timestamp=datetime.utcnow(),
                coherence=scores[winner],
            )
            
            self._current_broadcast = broadcast
            self._broadcast_history.append(broadcast)
            
            return broadcast
    
    def get_current_broadcast(self) -> Optional[GlobalWorkspaceState]:
        """Get current broadcast."""
        return self._current_broadcast


class HebbianLearning:
    """
    Hebbian Learning Implementation
    
    "Neurons that fire together, wire together"
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._connection_weights: Dict[Tuple[str, str], float] = {}
        self._updates: List[HebbianUpdate] = []
        self._learning_rate = 0.01
    
    def update_connection(
        self,
        source: str,
        target: str,
        pre_activation: float,
        post_activation: float
    ) -> float:
        """
        Update connection weight via Hebbian rule.
        
        Δw = η * pre * post
        """
        with self._lock:
            key = (source, target)
            current_weight = self._connection_weights.get(key, 0.0)
            
            delta = self._learning_rate * pre_activation * post_activation
            new_weight = current_weight + delta
            new_weight = max(-1.0, min(1.0, new_weight))
            
            self._connection_weights[key] = new_weight
            
            update = HebbianUpdate(
                source_region=source,
                target_region=target,
                pre_activation=pre_activation,
                post_activation=post_activation,
                weight_delta=delta,
                timestamp=datetime.utcnow(),
            )
            self._updates.append(update)
            
            return new_weight
    
    def get_weight(self, source: str, target: str) -> float:
        """Get connection weight."""
        return self._connection_weights.get((source, target), 0.0)


class NEUROSOrchestrator:
    """
    NEUROS-FI Master Orchestrator
    
    Coordinates all 9 brain regions and 5 oscillation bands.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._lock = threading.RLock()
        
        # System state
        self._state = SystemState.UNINITIALIZED
        self._inference_mode = InferenceMode.BALANCED
        
        # Core principles
        self.free_energy = FreeEnergyPrinciple()
        self.global_workspace = GlobalWorkspace()
        self.hebbian = HebbianLearning()
        
        # Brain regions (initialized in initialize())
        self.brainstem: Optional[BrainstemConstitution] = None
        self.neocortex: Optional[Neocortex] = None
        self.prefrontal: Optional[PrefrontalCortex] = None
        self.thalamus: Optional[Thalamus] = None
        self.hippocampus: Optional[Hippocampus] = None
        self.amygdala: Optional[Amygdala] = None
        self.basal_ganglia: Optional[BasalGanglia] = None
        self.cerebellum: Optional[Cerebellum] = None
        self.acc: Optional[AnteriorCingulateCortex] = None
        self.dmn: Optional[DefaultModeNetwork] = None
        
        # Oscillation synchronizer
        self.oscillations: Optional[OscillationSynchronizer] = None
        
        logger.info("NEUROS-FI Orchestrator created")
    
    async def initialize(self) -> bool:
        """
        Initialize NEUROS-FI system (12-step sequence).
        """
        try:
            self._state = SystemState.BOOTING
            logger.info("NEUROS-FI initialization started")
            
            # Step 1: Boot brainstem
            logger.info("Step 1/12: Booting brainstem constitutional layer")
            self.brainstem = get_brainstem()
            
            # Step 2: Initialize thalamus
            logger.info("Step 2/12: Initializing thalamic routing")
            self.thalamus = Thalamus()
            
            # Step 3: Load neocortex
            logger.info("Step 3/12: Loading cortical column weights")
            self.neocortex = Neocortex()
            
            # Step 4: Restore hippocampus
            logger.info("Step 4/12: Restoring hippocampal memory index")
            self.hippocampus = Hippocampus()
            
            # Step 5: Calibrate amygdala
            logger.info("Step 5/12: Calibrating amygdala threat thresholds")
            self.amygdala = Amygdala()
            
            # Step 6: Sync basal ganglia
            logger.info("Step 6/12: Syncing basal ganglia Q-tables")
            self.basal_ganglia = BasalGanglia()
            
            # Step 7: Load cerebellum
            logger.info("Step 7/12: Loading cerebellar forward models")
            self.cerebellum = Cerebellum()
            
            # Step 8: Initialize ACC
            logger.info("Step 8/12: Initializing ACC conflict monitors")
            self.acc = AnteriorCingulateCortex()
            
            # Step 9: Restore DMN
            logger.info("Step 9/12: Restoring DMN offline state")
            self.dmn = DefaultModeNetwork()
            
            # Step 10: Synchronize oscillations
            logger.info("Step 10/12: Synchronizing oscillation phases")
            self.oscillations = OscillationSynchronizer()
            
            # Step 11: Verify constitutional constraints
            logger.info("Step 11/12: Verifying constitutional constraints")
            if not self.brainstem.verify_compliance({}):
                logger.error("Constitutional verification failed")
                self._state = SystemState.ERROR
                return False
            
            # Step 12: Enter active inference
            logger.info("Step 12/12: Entering active inference loop")
            self._state = SystemState.ACTIVE
            
            logger.info("NEUROS-FI initialization complete - system ACTIVE")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self._state = SystemState.ERROR
            return False
    
    async def process_market_data(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process market data through the full neuromorphic architecture.
        """
        if self._state != SystemState.ACTIVE:
            return {'error': 'System not active', 'state': self._state.value}
        
        with self._lock:
            result = {
                'timestamp': datetime.utcnow(),
                'system_state': self._state.value,
            }
            
            try:
                # 1. Thalamic gating
                gated_data = self.thalamus.gate_signals(market_data)
                
                # 2. Neocortical prediction
                predictions = self.neocortex.predict(gated_data)
                
                # 3. Prefrontal executive control
                decision = self.prefrontal.deliberate(predictions, market_data)
                
                # 4. Amygdala threat detection
                threat = self.amygdala.process_market_state(market_data, {})
                
                # 5. ACC conflict detection
                conflict = self.acc.process_model_parliament(predictions)
                
                # 6. Basal ganglia action selection
                action = self.basal_ganglia.select_execution_action(market_data, {})
                
                # 7. Cerebellar execution prediction
                exec_pred = self.cerebellum.predict_execution({}, market_data)
                
                # 8. Global workspace competition
                candidates = {
                    'neocortex': {'content': predictions, 'salience': 0.7},
                    'prefrontal': {'content': decision, 'salience': 0.8},
                    'amygdala': {'content': threat, 'salience': 0.9 if threat.get('threat_detected') else 0.3},
                }
                broadcast = self.global_workspace.compete_for_workspace(candidates)
                
                # 9. Free energy computation
                fe_state = self.free_energy.compute_free_energy(
                    predictions, market_data, 1000
                )
                
                result.update({
                    'predictions': predictions,
                    'decision': decision,
                    'threat': threat,
                    'conflict': conflict,
                    'action': action,
                    'broadcast': broadcast.competition_winner if broadcast else None,
                    'free_energy': fe_state.total_free_energy,
                })
                
                return result
                
            except Exception as e:
                logger.error(f"Processing error: {e}")
                return {'error': str(e)}
    
    async def run_offline_consolidation(self) -> Dict[str, Any]:
        """Run overnight consolidation cycle."""
        if self._state != SystemState.ACTIVE:
            return {'error': 'System not active'}
        
        logger.info("Starting offline consolidation")
        self._state = SystemState.OFFLINE
        self.dmn.enter_offline_mode()
        
        try:
            result = self.dmn.run_offline_cycle([], {}, {}, {})
            logger.info("Offline consolidation complete")
            return result
        finally:
            self.dmn.exit_offline_mode()
            self._state = SystemState.ACTIVE
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            'system_state': self._state.value,
            'inference_mode': self._inference_mode.value,
            'free_energy': self.free_energy.get_statistics() if self.free_energy else {},
            'brainstem': self.brainstem.get_status() if self.brainstem else {},
            'neocortex': self.neocortex.get_status() if self.neocortex else {},
            'prefrontal': self.prefrontal.get_status() if self.prefrontal else {},
            'thalamus': self.thalamus.get_status() if self.thalamus else {},
            'hippocampus': self.hippocampus.get_status() if self.hippocampus else {},
            'amygdala': self.amygdala.get_status() if self.amygdala else {},
            'basal_ganglia': self.basal_ganglia.get_status() if self.basal_ganglia else {},
            'cerebellum': self.cerebellum.get_status() if self.cerebellum else {},
            'acc': self.acc.get_status() if self.acc else {},
            'dmn': self.dmn.get_status() if self.dmn else {},
            'oscillations': self.oscillations.get_status() if self.oscillations else {},
        }
    
    def halt(self):
        """Emergency halt."""
        logger.warning("NEUROS-FI emergency halt initiated")
        self._state = SystemState.HALTED
        if self.brainstem:
            self.brainstem.emergency_halt("Manual halt")


async def quick_start(config: Optional[Dict[str, Any]] = None) -> NEUROSOrchestrator:
    """Quick start NEUROS-FI system."""
    orchestrator = NEUROSOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator
