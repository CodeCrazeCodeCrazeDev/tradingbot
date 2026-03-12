"""
Hivemind Quantum Entanglement System
=====================================

Quantum-inspired entanglement for synchronized decision making:
- Entangled node pairs that share state instantly
- Quantum superposition of trading decisions
- Wave function collapse on observation (decision)
- Quantum tunneling for escaping local optima
- Entanglement swapping for network expansion
- Decoherence management for stability

This creates spooky action at a distance - when one node
decides, entangled nodes instantly align.
"""

import asyncio
import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
import hashlib
import cmath

logger = logging.getLogger(__name__)


class QuantumState(Enum):
    """Quantum states for trading decisions"""
    SUPERPOSITION = "superposition"  # Both buy and sell simultaneously
    BUY = "buy"                      # Collapsed to buy
    SELL = "sell"                    # Collapsed to sell
    HOLD = "hold"                    # Collapsed to hold
    ENTANGLED = "entangled"          # Entangled with another qubit


class EntanglementType(Enum):
    """Types of quantum entanglement"""
    BELL_STATE = "bell_state"        # Maximally entangled pair
    GHZ_STATE = "ghz_state"          # Multi-particle entanglement
    W_STATE = "w_state"              # Robust multi-particle state
    CLUSTER_STATE = "cluster_state"  # Graph-based entanglement


@dataclass
class QuantumAmplitude:
    """Complex amplitude for quantum state"""
    real: float = 0.0
    imag: float = 0.0
    
    @property
    def probability(self) -> float:
        """Get probability (|amplitude|^2)"""
        return self.real ** 2 + self.imag ** 2
    
    @property
    def phase(self) -> float:
        """Get phase angle"""
        return math.atan2(self.imag, self.real)
    
    def normalize(self, total: float) -> 'QuantumAmplitude':
        """Normalize amplitude"""
        if total > 0:
            factor = 1 / math.sqrt(total)
            return QuantumAmplitude(self.real * factor, self.imag * factor)
        return self
    
    def __mul__(self, other: float) -> 'QuantumAmplitude':
        return QuantumAmplitude(self.real * other, self.imag * other)
    
    def __add__(self, other: 'QuantumAmplitude') -> 'QuantumAmplitude':
        return QuantumAmplitude(self.real + other.real, self.imag + other.imag)


@dataclass
class TradingQubit:
    """A quantum bit representing a trading decision"""
    qubit_id: str
    node_id: str
    
    # Quantum state amplitudes
    alpha_buy: QuantumAmplitude = field(default_factory=lambda: QuantumAmplitude(1/math.sqrt(3), 0))
    alpha_sell: QuantumAmplitude = field(default_factory=lambda: QuantumAmplitude(1/math.sqrt(3), 0))
    alpha_hold: QuantumAmplitude = field(default_factory=lambda: QuantumAmplitude(1/math.sqrt(3), 0))
    
    # State
    state: QuantumState = QuantumState.SUPERPOSITION
    collapsed_value: Optional[str] = None
    
    # Entanglement
    entangled_with: List[str] = field(default_factory=list)
    entanglement_type: Optional[EntanglementType] = None
    
    # Decoherence
    coherence: float = 1.0
    decoherence_rate: float = 0.01
    
    # Measurement history
    measurement_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_probabilities(self) -> Dict[str, float]:
        """Get probabilities for each outcome"""
        total = (self.alpha_buy.probability + 
                 self.alpha_sell.probability + 
                 self.alpha_hold.probability)
        
        if total == 0:
            return {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}
        
        return {
            'buy': self.alpha_buy.probability / total,
            'sell': self.alpha_sell.probability / total,
            'hold': self.alpha_hold.probability / total,
        }
    
    def apply_rotation(self, theta: float, axis: str = 'z') -> None:
        """Apply quantum rotation gate"""
        cos_t = math.cos(theta / 2)
        sin_t = math.sin(theta / 2)
        
        if axis == 'z':
            # Z rotation - phase shift
            phase = cmath.exp(1j * theta)
            self.alpha_buy = QuantumAmplitude(
                self.alpha_buy.real * phase.real - self.alpha_buy.imag * phase.imag,
                self.alpha_buy.real * phase.imag + self.alpha_buy.imag * phase.real
            )
        elif axis == 'x':
            # X rotation - amplitude mixing
            new_buy = QuantumAmplitude(
                cos_t * self.alpha_buy.real - sin_t * self.alpha_sell.real,
                cos_t * self.alpha_buy.imag - sin_t * self.alpha_sell.imag
            )
            new_sell = QuantumAmplitude(
                sin_t * self.alpha_buy.real + cos_t * self.alpha_sell.real,
                sin_t * self.alpha_buy.imag + cos_t * self.alpha_sell.imag
            )
            self.alpha_buy = new_buy
            self.alpha_sell = new_sell
    
    def measure(self) -> str:
        """Collapse the wave function and return result"""
        if self.state != QuantumState.SUPERPOSITION:
            return self.collapsed_value or 'hold'
        
        probs = self.get_probabilities()
        r = random.random()
        
        cumulative = 0
        result = 'hold'
        for outcome, prob in probs.items():
            cumulative += prob
            if r <= cumulative:
                result = outcome
                break
        
        # Collapse
        self.collapsed_value = result
        if result == 'buy':
            self.state = QuantumState.BUY
            self.alpha_buy = QuantumAmplitude(1, 0)
            self.alpha_sell = QuantumAmplitude(0, 0)
            self.alpha_hold = QuantumAmplitude(0, 0)
        elif result == 'sell':
            self.state = QuantumState.SELL
            self.alpha_buy = QuantumAmplitude(0, 0)
            self.alpha_sell = QuantumAmplitude(1, 0)
            self.alpha_hold = QuantumAmplitude(0, 0)
        else:
            self.state = QuantumState.HOLD
            self.alpha_buy = QuantumAmplitude(0, 0)
            self.alpha_sell = QuantumAmplitude(0, 0)
            self.alpha_hold = QuantumAmplitude(1, 0)
        
        self.measurement_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'result': result,
            'probabilities': probs,
        })
        
        return result
    
    def reset_to_superposition(self) -> None:
        """Reset to superposition state"""
        self.state = QuantumState.SUPERPOSITION
        self.collapsed_value = None
        self.alpha_buy = QuantumAmplitude(1/math.sqrt(3), 0)
        self.alpha_sell = QuantumAmplitude(1/math.sqrt(3), 0)
        self.alpha_hold = QuantumAmplitude(1/math.sqrt(3), 0)
    
    def apply_decoherence(self) -> None:
        """Apply decoherence (loss of quantum properties)"""
        self.coherence *= (1 - self.decoherence_rate)
        
        # Mix towards classical probabilities
        if self.coherence < 0.5:
            noise = (1 - self.coherence) * 0.1
            self.alpha_buy = QuantumAmplitude(
                self.alpha_buy.real + random.gauss(0, noise),
                self.alpha_buy.imag * self.coherence
            )
            self.alpha_sell = QuantumAmplitude(
                self.alpha_sell.real + random.gauss(0, noise),
                self.alpha_sell.imag * self.coherence
            )
            self.alpha_hold = QuantumAmplitude(
                self.alpha_hold.real + random.gauss(0, noise),
                self.alpha_hold.imag * self.coherence
            )
    
    def bias_towards(self, direction: str, strength: float = 0.1) -> None:
        """Bias the qubit towards a particular outcome"""
        if direction == 'buy':
            self.alpha_buy = QuantumAmplitude(
                self.alpha_buy.real + strength,
                self.alpha_buy.imag
            )
        elif direction == 'sell':
            self.alpha_sell = QuantumAmplitude(
                self.alpha_sell.real + strength,
                self.alpha_sell.imag
            )
        elif direction == 'hold':
            self.alpha_hold = QuantumAmplitude(
                self.alpha_hold.real + strength,
                self.alpha_hold.imag
            )
        
        # Renormalize
        self._normalize()
    
    def _normalize(self) -> None:
        """Normalize amplitudes"""
        total = (self.alpha_buy.probability + 
                 self.alpha_sell.probability + 
                 self.alpha_hold.probability)
        
        if total > 0:
            self.alpha_buy = self.alpha_buy.normalize(total)
            self.alpha_sell = self.alpha_sell.normalize(total)
            self.alpha_hold = self.alpha_hold.normalize(total)


@dataclass
class EntangledPair:
    """A pair of entangled qubits"""
    pair_id: str
    qubit_a: str
    qubit_b: str
    entanglement_type: EntanglementType
    correlation: float = 1.0  # Perfect correlation
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get correlation matrix for outcomes"""
        # For Bell state: perfectly correlated
        if self.entanglement_type == EntanglementType.BELL_STATE:
            return {
                'buy': {'buy': self.correlation, 'sell': 0, 'hold': 1 - self.correlation},
                'sell': {'buy': 0, 'sell': self.correlation, 'hold': 1 - self.correlation},
                'hold': {'buy': (1 - self.correlation) / 2, 'sell': (1 - self.correlation) / 2, 'hold': self.correlation},
            }
        return {}


class QuantumEntanglementEngine:
    """
    Quantum Entanglement Engine for Hivemind
    
    Manages quantum entanglement between trading nodes:
    - Creates entangled pairs/groups
    - Propagates measurements through entanglement
    - Manages decoherence
    - Enables quantum-inspired consensus
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.qubits: Dict[str, TradingQubit] = {}
        self.entangled_pairs: Dict[str, EntangledPair] = {}
        self.entanglement_groups: Dict[str, List[str]] = {}
        
        # Global quantum state
        self.global_phase: float = 0.0
        self.total_measurements: int = 0
        self.total_entanglements: int = 0
        
        logger.info("QuantumEntanglementEngine initialized")
    
    def create_qubit(self, node_id: str) -> TradingQubit:
        """Create a qubit for a node"""
        qubit_id = f"qubit_{node_id}"
        qubit = TradingQubit(qubit_id=qubit_id, node_id=node_id)
        self.qubits[qubit_id] = qubit
        return qubit
    
    def entangle_pair(
        self,
        qubit_a_id: str,
        qubit_b_id: str,
        entanglement_type: EntanglementType = EntanglementType.BELL_STATE
    ) -> Optional[EntangledPair]:
        """Create entanglement between two qubits"""
        qubit_a = self.qubits.get(qubit_a_id)
        qubit_b = self.qubits.get(qubit_b_id)
        
        if not qubit_a or not qubit_b:
            logger.warning("Cannot entangle: qubits not found")
            return None
        
        pair_id = f"pair_{qubit_a_id}_{qubit_b_id}"
        
        pair = EntangledPair(
            pair_id=pair_id,
            qubit_a=qubit_a_id,
            qubit_b=qubit_b_id,
            entanglement_type=entanglement_type,
        )
        
        self.entangled_pairs[pair_id] = pair
        
        # Update qubits
        qubit_a.entangled_with.append(qubit_b_id)
        qubit_a.entanglement_type = entanglement_type
        qubit_b.entangled_with.append(qubit_a_id)
        qubit_b.entanglement_type = entanglement_type
        
        self.total_entanglements += 1
        
        logger.debug(f"Created entanglement: {pair_id}")
        return pair
    
    def create_ghz_state(self, qubit_ids: List[str]) -> str:
        """Create GHZ state (multi-particle entanglement)"""
        group_id = f"ghz_{datetime.utcnow().strftime('%H%M%S%f')}"
        
        # Entangle all qubits in the group
        for i, qid in enumerate(qubit_ids):
            qubit = self.qubits.get(qid)
            if qubit:
                qubit.entangled_with = [q for q in qubit_ids if q != qid]
                qubit.entanglement_type = EntanglementType.GHZ_STATE
        
        self.entanglement_groups[group_id] = qubit_ids
        
        logger.info(f"Created GHZ state with {len(qubit_ids)} qubits")
        return group_id
    
    def measure_qubit(self, qubit_id: str) -> Dict[str, Any]:
        """Measure a qubit and propagate to entangled partners"""
        qubit = self.qubits.get(qubit_id)
        if not qubit:
            return {'error': 'Qubit not found'}
        
        # Measure
        result = qubit.measure()
        self.total_measurements += 1
        
        # Propagate to entangled qubits
        propagated = []
        for partner_id in qubit.entangled_with:
            partner = self.qubits.get(partner_id)
            if partner and partner.state == QuantumState.SUPERPOSITION:
                # Correlated collapse
                pair_id = f"pair_{qubit_id}_{partner_id}"
                pair = self.entangled_pairs.get(pair_id)
                
                if pair and pair.entanglement_type == EntanglementType.BELL_STATE:
                    # Perfect correlation for Bell state
                    partner.collapsed_value = result
                    if result == 'buy':
                        partner.state = QuantumState.BUY
                    elif result == 'sell':
                        partner.state = QuantumState.SELL
                    else:
                        partner.state = QuantumState.HOLD
                    propagated.append(partner_id)
                
                elif partner.entanglement_type == EntanglementType.GHZ_STATE:
                    # GHZ: all collapse to same state
                    partner.collapsed_value = result
                    partner.state = QuantumState(result) if result in ['buy', 'sell', 'hold'] else QuantumState.HOLD
                    propagated.append(partner_id)
        
        return {
            'qubit_id': qubit_id,
            'result': result,
            'propagated_to': propagated,
            'total_affected': len(propagated) + 1,
        }
    
    def apply_market_influence(self, market_signal: float) -> None:
        """Apply market signal to all qubits"""
        # market_signal: -1 (bearish) to 1 (bullish)
        for qubit in self.qubits.values():
            if qubit.state == QuantumState.SUPERPOSITION:
                if market_signal > 0:
                    qubit.bias_towards('buy', abs(market_signal) * 0.1)
                elif market_signal < 0:
                    qubit.bias_towards('sell', abs(market_signal) * 0.1)
    
    def apply_decoherence_all(self) -> None:
        """Apply decoherence to all qubits"""
        for qubit in self.qubits.values():
            qubit.apply_decoherence()
    
    def reset_all(self) -> None:
        """Reset all qubits to superposition"""
        for qubit in self.qubits.values():
            qubit.reset_to_superposition()
    
    def quantum_consensus(self) -> Dict[str, Any]:
        """Reach consensus through quantum measurement"""
        # Measure all qubits
        results = {'buy': 0, 'sell': 0, 'hold': 0}
        measurements = []
        
        for qubit_id, qubit in self.qubits.items():
            if qubit.state == QuantumState.SUPERPOSITION:
                result = self.measure_qubit(qubit_id)
                measurements.append(result)
                results[result['result']] += 1
            elif qubit.collapsed_value:
                results[qubit.collapsed_value] += 1
        
        total = sum(results.values())
        if total > 0:
            probabilities = {k: v / total for k, v in results.items()}
        else:
            probabilities = {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}
        
        winner = max(results, key=results.get)
        
        return {
            'consensus': winner,
            'vote_counts': results,
            'probabilities': probabilities,
            'confidence': probabilities[winner],
            'measurements': len(measurements),
            'entanglement_effects': sum(len(m.get('propagated_to', [])) for m in measurements),
        }
    
    def quantum_tunneling_escape(self, qubit_id: str, barrier_height: float = 0.5) -> bool:
        """Attempt quantum tunneling to escape local optimum"""
        qubit = self.qubits.get(qubit_id)
        if not qubit:
            return False
        
        # Tunneling probability decreases with barrier height
        tunnel_prob = math.exp(-barrier_height * 2)
        
        if random.random() < tunnel_prob:
            # Successful tunnel - randomize state
            qubit.reset_to_superposition()
            # Apply random rotation
            qubit.apply_rotation(random.uniform(0, 2 * math.pi), 'x')
            qubit.apply_rotation(random.uniform(0, 2 * math.pi), 'z')
            logger.debug(f"Qubit {qubit_id} tunneled through barrier")
            return True
        
        return False
    
    def get_entanglement_map(self) -> Dict[str, List[str]]:
        """Get map of all entanglements"""
        entanglement_map = {}
        for qubit_id, qubit in self.qubits.items():
            entanglement_map[qubit_id] = qubit.entangled_with.copy()
        return entanglement_map
    
    def get_quantum_state_summary(self) -> Dict[str, Any]:
        """Get summary of quantum state"""
        states = {'superposition': 0, 'buy': 0, 'sell': 0, 'hold': 0}
        avg_coherence = 0
        
        for qubit in self.qubits.values():
            if qubit.state == QuantumState.SUPERPOSITION:
                states['superposition'] += 1
            elif qubit.collapsed_value:
                states[qubit.collapsed_value] += 1
            avg_coherence += qubit.coherence
        
        num_qubits = len(self.qubits)
        
        return {
            'num_qubits': num_qubits,
            'states': states,
            'avg_coherence': avg_coherence / num_qubits if num_qubits > 0 else 0,
            'num_entangled_pairs': len(self.entangled_pairs),
            'num_entanglement_groups': len(self.entanglement_groups),
            'total_measurements': self.total_measurements,
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive quantum report"""
        return {
            'state_summary': self.get_quantum_state_summary(),
            'entanglement_map': self.get_entanglement_map(),
            'qubits': {
                qid: {
                    'state': q.state.value,
                    'probabilities': q.get_probabilities(),
                    'coherence': q.coherence,
                    'entangled_with': q.entangled_with,
                }
                for qid, q in self.qubits.items()
            },
        }


class QuantumHivemindBridge:
    """
    Bridge between Quantum Entanglement and Hivemind
    
    Translates quantum states to trading decisions
    and hivemind signals to quantum operations.
    """
    
    def __init__(self, engine: QuantumEntanglementEngine):
        self.engine = engine
        self.decision_history: List[Dict[str, Any]] = []
    
    async def initialize_quantum_nodes(self, node_ids: List[str]) -> None:
        """Initialize quantum qubits for hivemind nodes"""
        for node_id in node_ids:
            self.engine.create_qubit(node_id)
        
        # Create GHZ entanglement for collective decision making
        qubit_ids = [f"qubit_{nid}" for nid in node_ids]
        self.engine.create_ghz_state(qubit_ids)
    
    async def apply_node_analysis(
        self,
        node_id: str,
        analysis: Dict[str, Any]
    ) -> None:
        """Apply node's analysis to its qubit"""
        qubit_id = f"qubit_{node_id}"
        qubit = self.engine.qubits.get(qubit_id)
        
        if not qubit:
            return
        
        # Extract signal from analysis
        signal = analysis.get('signal', 0)  # -1 to 1
        confidence = analysis.get('confidence', 0.5)
        
        # Bias qubit based on analysis
        if signal > 0.3:
            qubit.bias_towards('buy', signal * confidence * 0.2)
        elif signal < -0.3:
            qubit.bias_towards('sell', abs(signal) * confidence * 0.2)
        else:
            qubit.bias_towards('hold', confidence * 0.1)
    
    async def get_quantum_decision(self) -> Dict[str, Any]:
        """Get collective quantum decision"""
        # Apply decoherence
        self.engine.apply_decoherence_all()
        
        # Get quantum consensus
        consensus = self.engine.quantum_consensus()
        
        decision = {
            'action': consensus['consensus'],
            'confidence': consensus['confidence'],
            'quantum_effects': {
                'entanglement_propagation': consensus['entanglement_effects'],
                'measurements': consensus['measurements'],
            },
            'vote_distribution': consensus['probabilities'],
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        self.decision_history.append(decision)
        
        # Reset for next decision
        self.engine.reset_all()
        
        return decision
    
    async def quantum_override(self, direction: str, strength: float = 0.5) -> None:
        """Override quantum state with strong bias"""
        for qubit in self.engine.qubits.values():
            qubit.bias_towards(direction, strength)


# Factory function
def create_quantum_entanglement(
    node_ids: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Tuple[QuantumEntanglementEngine, QuantumHivemindBridge]:
    """Create quantum entanglement system for hivemind"""
    engine = QuantumEntanglementEngine(config)
    bridge = QuantumHivemindBridge(engine)
    
    # Initialize will be called async
    return engine, bridge
