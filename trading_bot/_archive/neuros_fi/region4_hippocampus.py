"""
NEUROS-FI Region 4: Hippocampus - Memory Consolidation, Neurogenesis, and Self-Discovery
=========================================================================================

Biological Basis:
The hippocampus converts short-term experience into long-term memory via consolidation.
The dentate gyrus performs pattern separation — distinguishing similar inputs into
maximally distinct representations. Crucially, the hippocampus is one of the only
brain structures where new neurons are born throughout adult life (neurogenesis).

New neurons are initially hyperexcitable and weakly connected — ideal for encoding
genuinely novel experiences without corrupting existing memories.

Citations:
- Squire (1992) - Memory and the hippocampus
- Leutgeb et al. (2007) - Pattern separation in the dentate gyrus
- Aimone et al. (2011) - Resolving new memories: A critical look at the dentate gyrus
- Sahay et al. (2011) - Increasing adult hippocampal neurogenesis is sufficient to improve pattern separation

Constitutional Version: 5.0
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories stored in the hippocampus."""
    
    EPISODIC = auto()      # Specific trading events
    SEMANTIC = auto()      # General market knowledge
    PROCEDURAL = auto()    # Trading procedures/patterns
    PROSPECTIVE = auto()   # Future predictions/plans


class MemoryState(Enum):
    """State of a memory in the consolidation process."""
    
    ENCODING = "encoding"           # Being encoded
    PROVISIONAL = "provisional"     # Short-term, not yet consolidated
    CONSOLIDATING = "consolidating" # Being transferred to long-term
    CONSOLIDATED = "consolidated"   # In long-term storage
    DECAYING = "decaying"          # Losing strength
    ARCHIVED = "archived"          # Rarely accessed but preserved


class NeurogenesisState(Enum):
    """State of a new neuron (signal node) in the neurogenesis process."""
    
    NEWBORN = "newborn"         # Just created, high plasticity
    MATURING = "maturing"       # Learning connections
    EVALUATING = "evaluating"   # Being tested for validity
    PROMOTED = "promoted"       # Passed validation, permanent
    PRUNED = "pruned"          # Failed validation, removed


@dataclass
class Memory:
    """A memory stored in the hippocampus."""
    
    memory_id: str
    memory_type: MemoryType
    state: MemoryState
    content: Dict[str, Any]
    encoding_time: datetime
    last_access: datetime
    access_count: int
    strength: float  # 0-1, decays over time
    associations: List[str]  # IDs of associated memories
    context: Dict[str, Any] = field(default_factory=dict)
    consolidation_score: float = 0.0
    
    def get_current_strength(self) -> float:
        """Get current memory strength with decay."""
        elapsed_hours = (datetime.utcnow() - self.last_access).total_seconds() / 3600
        decay_rate = 0.01  # Per hour
        return self.strength * np.exp(-decay_rate * elapsed_hours)


@dataclass
class SignalNeuron:
    """
    A signal neuron - the representational node for a discovered pattern.
    
    New neurons begin in high-plasticity state and must prove predictive
    validity to be promoted to the permanent factor library.
    """
    
    neuron_id: str
    pattern_signature: str
    state: NeurogenesisState
    creation_time: datetime
    
    # Plasticity (learning rate multiplier)
    plasticity: float = 10.0  # 10x normal for newborn
    
    # Activation properties
    activation_threshold: float = 0.3  # Low threshold for newborn
    current_activation: float = 0.0
    
    # Connections
    input_weights: Dict[str, float] = field(default_factory=dict)
    output_weights: Dict[str, float] = field(default_factory=dict)
    
    # Validation metrics
    information_coefficient: float = 0.0
    sharpe_contribution: float = 0.0
    out_of_sample_persistence: float = 0.0
    evaluation_days: int = 0
    
    # Survival window
    survival_window_days: int = 60
    
    def is_valid_for_promotion(self) -> bool:
        """Check if neuron passes validation criteria."""
        return (
            self.evaluation_days >= self.survival_window_days and
            self.information_coefficient > 0.02 and
            self.sharpe_contribution > 0.0 and
            self.out_of_sample_persistence > 0.5
        )


@dataclass
class PatternMatch:
    """Result of pattern matching/completion."""
    
    query_pattern: Dict[str, float]
    matched_memory_id: str
    similarity: float
    completed_pattern: Dict[str, float]
    confidence: float


class PatternSeparation:
    """
    Dentate Gyrus Pattern Separation - distinguishes similar inputs
    into maximally distinct representations.
    
    A pattern less than 30% correlated with existing factors is
    classified as genuinely novel.
    """
    
    NOVELTY_THRESHOLD = 0.30  # Max correlation to be considered novel
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Existing pattern library
        self._pattern_library: Dict[str, np.ndarray] = {}
        
        # Pattern statistics
        self._patterns_evaluated = 0
        self._patterns_novel = 0
    
    def orthogonalize(
        self,
        new_pattern: np.ndarray,
        pattern_id: str
    ) -> Tuple[bool, float, np.ndarray]:
        """
        Orthogonalize a new pattern against the existing library.
        
        Returns:
            Tuple of (is_novel, max_correlation, orthogonalized_pattern)
        """
        with self._lock:
            self._patterns_evaluated += 1
            
            if not self._pattern_library:
                # First pattern is always novel
                self._pattern_library[pattern_id] = new_pattern
                self._patterns_novel += 1
                return True, 0.0, new_pattern
            
            # Compute correlations with all existing patterns
            max_correlation = 0.0
            most_similar_id = None
            
            for existing_id, existing_pattern in self._pattern_library.items():
                if len(new_pattern) != len(existing_pattern):
                    continue
                
                # Pearson correlation
                correlation = np.corrcoef(new_pattern, existing_pattern)[0, 1]
                if np.isnan(correlation):
                    correlation = 0.0
                
                if abs(correlation) > max_correlation:
                    max_correlation = abs(correlation)
                    most_similar_id = existing_id
            
            # Check novelty threshold
            is_novel = max_correlation < self.NOVELTY_THRESHOLD
            
            if is_novel:
                # Orthogonalize using Gram-Schmidt
                orthogonalized = self._gram_schmidt(new_pattern)
                self._pattern_library[pattern_id] = orthogonalized
                self._patterns_novel += 1
                return True, max_correlation, orthogonalized
            else:
                return False, max_correlation, new_pattern
    
    def _gram_schmidt(self, vector: np.ndarray) -> np.ndarray:
        """Apply Gram-Schmidt orthogonalization."""
        result = vector.copy()
        
        for existing in self._pattern_library.values():
            if len(existing) == len(result):
                # Subtract projection
                projection = np.dot(result, existing) / np.dot(existing, existing)
                result = result - projection * existing
        
        # Normalize
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        
        return result
    
    def get_similarity(self, pattern1_id: str, pattern2_id: str) -> float:
        """Get similarity between two patterns."""
        with self._lock:
            p1 = self._pattern_library.get(pattern1_id)
            p2 = self._pattern_library.get(pattern2_id)
            
            if p1 is None or p2 is None or len(p1) != len(p2):
                return 0.0
            
            return abs(np.corrcoef(p1, p2)[0, 1])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern separation statistics."""
        with self._lock:
            return {
                'patterns_evaluated': self._patterns_evaluated,
                'patterns_novel': self._patterns_novel,
                'novelty_rate': self._patterns_novel / max(1, self._patterns_evaluated),
                'library_size': len(self._pattern_library),
            }


class Neurogenesis:
    """
    Hippocampal Neurogenesis - creates new signal neurons for novel patterns.
    
    New neurons begin with:
    - High plasticity (10x normal learning rate)
    - Low activation threshold
    - No connections to production factor library
    - 60-day evaluation window
    """
    
    def __init__(self, pattern_separation: PatternSeparation):
        self._pattern_separation = pattern_separation
        self._lock = threading.RLock()
        
        # Neuron registry
        self._neurons: Dict[str, SignalNeuron] = {}
        
        # Promoted neurons (permanent factor library)
        self._factor_library: Dict[str, SignalNeuron] = {}
        
        # Pruned neurons (archived)
        self._pruned_archive: List[str] = []
        
        # Neurogenesis parameters
        self._novelty_z_threshold = 3.5  # Z-score for novelty detection
        self._survival_window_days = 60
        self._min_ic_threshold = 0.02
        
        # Statistics
        self._neurons_created = 0
        self._neurons_promoted = 0
        self._neurons_pruned = 0
    
    def detect_novelty(
        self,
        prediction_error: float,
        error_distribution: Tuple[float, float]  # (mean, std)
    ) -> bool:
        """
        Detect if a prediction error indicates genuine novelty.
        
        Returns True if error exceeds novelty Z-score threshold.
        """
        mean, std = error_distribution
        if std == 0:
            return False
        
        z_score = abs(prediction_error - mean) / std
        return z_score > self._novelty_z_threshold
    
    def create_neuron(
        self,
        pattern: np.ndarray,
        context: Dict[str, Any]
    ) -> Optional[SignalNeuron]:
        """
        Create a new signal neuron for a novel pattern.
        
        The neuron must pass pattern separation (orthogonalization)
        before being created.
        """
        with self._lock:
            # Generate pattern signature
            pattern_bytes = pattern.tobytes()
            signature = hashlib.sha256(pattern_bytes).hexdigest()[:16]
            neuron_id = f"neuron_{signature}_{int(time.time())}"
            
            # Orthogonalize against existing patterns
            is_novel, max_corr, orthogonalized = self._pattern_separation.orthogonalize(
                pattern, neuron_id
            )
            
            if not is_novel:
                logger.debug(f"Pattern not novel (max_corr={max_corr:.2f}), neuron not created")
                return None
            
            # Create new neuron
            neuron = SignalNeuron(
                neuron_id=neuron_id,
                pattern_signature=signature,
                state=NeurogenesisState.NEWBORN,
                creation_time=datetime.utcnow(),
                plasticity=10.0,  # High plasticity
                activation_threshold=0.3,  # Low threshold
            )
            
            self._neurons[neuron_id] = neuron
            self._neurons_created += 1
            
            logger.info(f"New neuron created: {neuron_id} (max_corr={max_corr:.2f})")
            
            return neuron
    
    def update_neuron(
        self,
        neuron_id: str,
        ic: float,
        sharpe: float,
        persistence: float
    ):
        """Update neuron validation metrics."""
        with self._lock:
            if neuron_id not in self._neurons:
                return
            
            neuron = self._neurons[neuron_id]
            
            # Update metrics with exponential moving average
            alpha = 0.1
            neuron.information_coefficient = (
                alpha * ic + (1 - alpha) * neuron.information_coefficient
            )
            neuron.sharpe_contribution = (
                alpha * sharpe + (1 - alpha) * neuron.sharpe_contribution
            )
            neuron.out_of_sample_persistence = (
                alpha * persistence + (1 - alpha) * neuron.out_of_sample_persistence
            )
            
            # Increment evaluation days
            neuron.evaluation_days += 1
            
            # Update state
            if neuron.state == NeurogenesisState.NEWBORN:
                neuron.state = NeurogenesisState.MATURING
            elif neuron.state == NeurogenesisState.MATURING:
                if neuron.evaluation_days >= 30:
                    neuron.state = NeurogenesisState.EVALUATING
            
            # Reduce plasticity over time
            neuron.plasticity = max(1.0, neuron.plasticity * 0.95)
    
    def evaluate_neurons(self) -> Tuple[List[str], List[str]]:
        """
        Evaluate all neurons for promotion or pruning.
        
        Returns:
            Tuple of (promoted_ids, pruned_ids)
        """
        with self._lock:
            promoted = []
            pruned = []
            
            for neuron_id, neuron in list(self._neurons.items()):
                if neuron.state != NeurogenesisState.EVALUATING:
                    continue
                
                if neuron.is_valid_for_promotion():
                    # Promote to factor library
                    neuron.state = NeurogenesisState.PROMOTED
                    neuron.plasticity = 1.0  # Normal plasticity
                    self._factor_library[neuron_id] = neuron
                    del self._neurons[neuron_id]
                    promoted.append(neuron_id)
                    self._neurons_promoted += 1
                    logger.info(f"Neuron promoted: {neuron_id}")
                    
                elif neuron.evaluation_days >= neuron.survival_window_days:
                    # Failed validation - prune
                    neuron.state = NeurogenesisState.PRUNED
                    self._pruned_archive.append(neuron_id)
                    del self._neurons[neuron_id]
                    pruned.append(neuron_id)
                    self._neurons_pruned += 1
                    logger.info(f"Neuron pruned: {neuron_id}")
            
            return promoted, pruned
    
    def get_factor_library(self) -> Dict[str, SignalNeuron]:
        """Get the permanent factor library."""
        with self._lock:
            return self._factor_library.copy()
    
    def get_developing_neurons(self) -> List[SignalNeuron]:
        """Get neurons still in development."""
        with self._lock:
            return list(self._neurons.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get neurogenesis statistics."""
        with self._lock:
            return {
                'neurons_created': self._neurons_created,
                'neurons_promoted': self._neurons_promoted,
                'neurons_pruned': self._neurons_pruned,
                'promotion_rate': self._neurons_promoted / max(1, self._neurons_created),
                'developing_count': len(self._neurons),
                'factor_library_size': len(self._factor_library),
            }


class MemoryConsolidation:
    """
    Memory Consolidation System - transfers short-term to long-term memory.
    
    During offline periods, the hippocampus replays provisional memories
    to the neocortex for integration into the long-term world model.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Memory stores
        self._short_term: Dict[str, Memory] = {}
        self._long_term: Dict[str, Memory] = {}
        
        # Consolidation queue
        self._consolidation_queue: List[str] = []
        
        # Consolidation parameters
        self._consolidation_threshold = 0.7  # Min strength to consolidate
        self._decay_threshold = 0.1  # Below this, memory decays
        
        # Statistics
        self._memories_encoded = 0
        self._memories_consolidated = 0
        self._memories_decayed = 0
    
    def encode(
        self,
        content: Dict[str, Any],
        memory_type: MemoryType,
        associations: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """Encode a new memory."""
        with self._lock:
            memory_id = f"mem_{int(time.time()*1000)}_{self._memories_encoded}"
            
            memory = Memory(
                memory_id=memory_id,
                memory_type=memory_type,
                state=MemoryState.ENCODING,
                content=content,
                encoding_time=datetime.utcnow(),
                last_access=datetime.utcnow(),
                access_count=1,
                strength=1.0,
                associations=associations or [],
                context=context or {},
            )
            
            self._short_term[memory_id] = memory
            memory.state = MemoryState.PROVISIONAL
            self._memories_encoded += 1
            
            return memory
    
    def access(self, memory_id: str) -> Optional[Memory]:
        """Access a memory (strengthens it)."""
        with self._lock:
            # Check short-term
            if memory_id in self._short_term:
                memory = self._short_term[memory_id]
                memory.last_access = datetime.utcnow()
                memory.access_count += 1
                memory.strength = min(1.0, memory.strength + 0.1)
                return memory
            
            # Check long-term
            if memory_id in self._long_term:
                memory = self._long_term[memory_id]
                memory.last_access = datetime.utcnow()
                memory.access_count += 1
                return memory
            
            return None
    
    def consolidate(self) -> List[str]:
        """
        Run consolidation process - transfer strong memories to long-term.
        
        Returns list of consolidated memory IDs.
        """
        with self._lock:
            consolidated = []
            
            for memory_id, memory in list(self._short_term.items()):
                current_strength = memory.get_current_strength()
                
                if current_strength >= self._consolidation_threshold:
                    # Strong enough to consolidate
                    memory.state = MemoryState.CONSOLIDATING
                    memory.consolidation_score = current_strength
                    
                    # Transfer to long-term
                    self._long_term[memory_id] = memory
                    del self._short_term[memory_id]
                    
                    memory.state = MemoryState.CONSOLIDATED
                    consolidated.append(memory_id)
                    self._memories_consolidated += 1
                    
                elif current_strength < self._decay_threshold:
                    # Too weak - let it decay
                    memory.state = MemoryState.DECAYING
                    del self._short_term[memory_id]
                    self._memories_decayed += 1
            
            return consolidated
    
    def replay(self, memory_ids: Optional[List[str]] = None) -> List[Memory]:
        """
        Replay memories for consolidation/learning.
        
        Returns memories for replay to neocortex.
        """
        with self._lock:
            if memory_ids:
                return [
                    self._short_term.get(mid) or self._long_term.get(mid)
                    for mid in memory_ids
                    if mid in self._short_term or mid in self._long_term
                ]
            
            # Default: replay recent provisional memories
            recent = sorted(
                self._short_term.values(),
                key=lambda m: m.encoding_time,
                reverse=True
            )[:100]
            
            return recent
    
    def search(
        self,
        query: Dict[str, Any],
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search for memories matching a query."""
        with self._lock:
            results = []
            
            # Search both stores
            all_memories = list(self._short_term.values()) + list(self._long_term.values())
            
            for memory in all_memories:
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                # Simple content matching
                match_score = self._compute_match_score(query, memory.content)
                if match_score > 0.5:
                    results.append((match_score, memory))
            
            # Sort by match score
            results.sort(key=lambda x: x[0], reverse=True)
            
            return [m for _, m in results[:limit]]
    
    def _compute_match_score(self, query: Dict, content: Dict) -> float:
        """Compute similarity between query and content."""
        if not query or not content:
            return 0.0
        
        matches = 0
        total = len(query)
        
        for key, value in query.items():
            if key in content:
                if content[key] == value:
                    matches += 1
                elif isinstance(value, (int, float)) and isinstance(content[key], (int, float)):
                    # Numeric similarity
                    diff = abs(value - content[key])
                    max_val = max(abs(value), abs(content[key]), 1)
                    matches += max(0, 1 - diff / max_val)
        
        return matches / max(total, 1)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        with self._lock:
            return {
                'memories_encoded': self._memories_encoded,
                'memories_consolidated': self._memories_consolidated,
                'memories_decayed': self._memories_decayed,
                'short_term_count': len(self._short_term),
                'long_term_count': len(self._long_term),
                'consolidation_rate': self._memories_consolidated / max(1, self._memories_encoded),
            }


class PatternCompletion:
    """
    Pattern Completion - retrieve full patterns from partial/noisy input.
    
    When a partial signal matches an existing memory pattern with >60% overlap,
    the hippocampus completes the pattern.
    """
    
    COMPLETION_THRESHOLD = 0.60
    
    def __init__(self, memory_consolidation: MemoryConsolidation):
        self._memory = memory_consolidation
        self._lock = threading.RLock()
        
        # Pattern templates
        self._templates: Dict[str, Dict[str, float]] = {}
    
    def register_template(self, template_id: str, pattern: Dict[str, float]):
        """Register a pattern template for completion."""
        with self._lock:
            self._templates[template_id] = pattern
    
    def complete(
        self,
        partial_pattern: Dict[str, float]
    ) -> Optional[PatternMatch]:
        """
        Complete a partial pattern by matching to templates.
        
        Returns the completed pattern if match found.
        """
        with self._lock:
            best_match = None
            best_similarity = 0.0
            
            for template_id, template in self._templates.items():
                similarity = self._compute_overlap(partial_pattern, template)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = template_id
            
            if best_similarity >= self.COMPLETION_THRESHOLD and best_match:
                template = self._templates[best_match]
                
                # Complete the pattern
                completed = template.copy()
                completed.update(partial_pattern)  # Override with known values
                
                return PatternMatch(
                    query_pattern=partial_pattern,
                    matched_memory_id=best_match,
                    similarity=best_similarity,
                    completed_pattern=completed,
                    confidence=best_similarity,
                )
            
            return None
    
    def _compute_overlap(
        self,
        partial: Dict[str, float],
        template: Dict[str, float]
    ) -> float:
        """Compute overlap between partial pattern and template."""
        if not partial or not template:
            return 0.0
        
        common_keys = set(partial.keys()) & set(template.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            # Check if values are similar
            diff = abs(partial[key] - template[key])
            max_val = max(abs(partial[key]), abs(template[key]), 0.001)
            if diff / max_val < 0.2:  # Within 20%
                matches += 1
        
        return matches / len(template)


class ThetaOscillationEncoder:
    """
    Theta Oscillation Encoding - encodes sequential events as temporal sequences.
    
    Uses theta-band timing to encode event sequences like:
    earnings → reaction → analyst revision → institutional repositioning
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Sequence templates
        self._sequences: Dict[str, List[Dict[str, Any]]] = {}
        
        # Current encoding buffer
        self._encoding_buffer: List[Dict[str, Any]] = []
        self._buffer_start: Optional[datetime] = None
        
        # Theta parameters
        self._theta_frequency_hz = 6.0  # 6 Hz theta
        self._theta_phase = 0.0
    
    def encode_event(self, event: Dict[str, Any]) -> str:
        """Encode an event into the current sequence."""
        with self._lock:
            now = datetime.utcnow()
            
            if self._buffer_start is None:
                self._buffer_start = now
            
            # Add theta phase to event
            elapsed = (now - self._buffer_start).total_seconds()
            self._theta_phase = (2 * np.pi * self._theta_frequency_hz * elapsed) % (2 * np.pi)
            
            event_with_phase = {
                **event,
                'theta_phase': self._theta_phase,
                'timestamp': now,
                'sequence_position': len(self._encoding_buffer),
            }
            
            self._encoding_buffer.append(event_with_phase)
            
            return f"event_{len(self._encoding_buffer)}"
    
    def finalize_sequence(self, sequence_id: str) -> List[Dict[str, Any]]:
        """Finalize and store the current sequence."""
        with self._lock:
            sequence = self._encoding_buffer.copy()
            self._sequences[sequence_id] = sequence
            
            # Reset buffer
            self._encoding_buffer = []
            self._buffer_start = None
            
            return sequence
    
    def match_sequence(
        self,
        partial_sequence: List[Dict[str, Any]]
    ) -> Optional[Tuple[str, float]]:
        """
        Match a partial sequence to stored templates.
        
        Returns (sequence_id, similarity) if match found.
        """
        with self._lock:
            best_match = None
            best_similarity = 0.0
            
            for seq_id, template in self._sequences.items():
                similarity = self._sequence_similarity(partial_sequence, template)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = seq_id
            
            if best_similarity > 0.6:
                return best_match, best_similarity
            
            return None
    
    def _sequence_similarity(
        self,
        seq1: List[Dict[str, Any]],
        seq2: List[Dict[str, Any]]
    ) -> float:
        """Compute similarity between two sequences."""
        if not seq1 or not seq2:
            return 0.0
        
        # Compare event types in order
        min_len = min(len(seq1), len(seq2))
        matches = 0
        
        for i in range(min_len):
            if seq1[i].get('event_type') == seq2[i].get('event_type'):
                matches += 1
        
        return matches / max(len(seq1), len(seq2))


class Hippocampus:
    """
    The complete Hippocampus - memory consolidation, neurogenesis, and self-discovery.
    
    Implements:
    - Memory encoding and consolidation
    - Pattern separation (dentate gyrus)
    - Neurogenesis (new signal discovery)
    - Pattern completion
    - Theta oscillation sequence encoding
    """
    
    def __init__(self):
        # Initialize components
        self.pattern_separation = PatternSeparation()
        self.neurogenesis = Neurogenesis(self.pattern_separation)
        self.memory_consolidation = MemoryConsolidation()
        self.pattern_completion = PatternCompletion(self.memory_consolidation)
        self.theta_encoder = ThetaOscillationEncoder()
        
        self._lock = threading.RLock()
        
        # Novelty detection state
        self._prediction_errors: List[float] = []
        self._error_window = 1000
        
        logger.info("Hippocampus initialized - memory and discovery systems active")
    
    def process_signal_anomaly(
        self,
        signal: Dict[str, Any],
        prediction_error: float
    ) -> Optional[SignalNeuron]:
        """
        Process a signal anomaly - potentially create new neuron.
        
        If the prediction error exceeds novelty threshold, triggers
        the neurogenesis protocol.
        """
        with self._lock:
            # Update error distribution
            self._prediction_errors.append(prediction_error)
            if len(self._prediction_errors) > self._error_window:
                self._prediction_errors = self._prediction_errors[-self._error_window:]
            
            # Compute error distribution
            if len(self._prediction_errors) < 100:
                return None  # Not enough data
            
            mean_error = np.mean(self._prediction_errors)
            std_error = np.std(self._prediction_errors)
            
            # Check for novelty
            if self.neurogenesis.detect_novelty(prediction_error, (mean_error, std_error)):
                # Extract pattern from signal
                pattern = self._extract_pattern(signal)
                
                # Attempt to create new neuron
                neuron = self.neurogenesis.create_neuron(pattern, signal)
                
                if neuron:
                    # Encode as memory
                    self.memory_consolidation.encode(
                        content={'signal': signal, 'neuron_id': neuron.neuron_id},
                        memory_type=MemoryType.EPISODIC,
                        context={'prediction_error': prediction_error},
                    )
                
                return neuron
            
            return None
    
    def _extract_pattern(self, signal: Dict[str, Any]) -> np.ndarray:
        """Extract a numeric pattern from a signal."""
        values = []
        for key, value in sorted(signal.items()):
            if isinstance(value, (int, float)):
                values.append(float(value))
        
        if not values:
            values = [0.0]
        
        return np.array(values)
    
    def encode_memory(
        self,
        content: Dict[str, Any],
        memory_type: MemoryType = MemoryType.EPISODIC
    ) -> Memory:
        """Encode a new memory."""
        return self.memory_consolidation.encode(content, memory_type)
    
    def recall(self, query: Dict[str, Any]) -> List[Memory]:
        """Recall memories matching a query."""
        return self.memory_consolidation.search(query)
    
    def complete_pattern(
        self,
        partial: Dict[str, float]
    ) -> Optional[PatternMatch]:
        """Complete a partial pattern."""
        return self.pattern_completion.complete(partial)
    
    def run_consolidation(self) -> Dict[str, Any]:
        """
        Run the consolidation cycle (typically during offline periods).
        
        Returns consolidation results.
        """
        with self._lock:
            # Consolidate memories
            consolidated_memories = self.memory_consolidation.consolidate()
            
            # Evaluate neurons
            promoted, pruned = self.neurogenesis.evaluate_neurons()
            
            return {
                'memories_consolidated': len(consolidated_memories),
                'neurons_promoted': len(promoted),
                'neurons_pruned': len(pruned),
                'promoted_ids': promoted,
                'pruned_ids': pruned,
            }
    
    def replay_memories(self, count: int = 100) -> List[Memory]:
        """Replay recent memories for learning."""
        return self.memory_consolidation.replay()[:count]
    
    def get_factor_library(self) -> Dict[str, SignalNeuron]:
        """Get the permanent factor library (promoted neurons)."""
        return self.neurogenesis.get_factor_library()
    
    def get_status(self) -> Dict[str, Any]:
        """Get hippocampus status."""
        return {
            'memory': self.memory_consolidation.get_statistics(),
            'neurogenesis': self.neurogenesis.get_statistics(),
            'pattern_separation': self.pattern_separation.get_statistics(),
            'prediction_error_stats': {
                'mean': np.mean(self._prediction_errors) if self._prediction_errors else 0,
                'std': np.std(self._prediction_errors) if self._prediction_errors else 0,
                'count': len(self._prediction_errors),
            },
        }
