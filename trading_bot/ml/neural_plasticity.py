"""
Synaptic Pruning and Neural Plasticity for Adaptive Trading Models.

This module implements:
- Synaptic pruning for model optimization
- Neural plasticity for continuous learning
- Adaptive network architecture
- Hebbian learning principles
- Catastrophic forgetting prevention
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import copy
import numpy

logger = logging.getLogger(__name__)


class PruningStrategy(Enum):
    """Strategies for synaptic pruning."""
    MAGNITUDE = "magnitude"  # Prune by weight magnitude
    GRADIENT = "gradient"  # Prune by gradient importance
    ACTIVATION = "activation"  # Prune by activation frequency
    SENSITIVITY = "sensitivity"  # Prune by loss sensitivity
    LOTTERY_TICKET = "lottery_ticket"  # Find winning tickets
    STRUCTURED = "structured"  # Prune entire neurons/filters


class PlasticityMode(Enum):
    """Modes of neural plasticity."""
    HEBBIAN = "hebbian"  # Fire together, wire together
    ANTI_HEBBIAN = "anti_hebbian"  # Decorrelation
    BCM = "bcm"  # Bienenstock-Cooper-Munro
    STDP = "stdp"  # Spike-timing dependent plasticity
    HOMEOSTATIC = "homeostatic"  # Maintain activity levels


class AdaptationType(Enum):
    """Types of network adaptation."""
    GROWTH = "growth"  # Add neurons/connections
    PRUNING = "pruning"  # Remove neurons/connections
    REWIRING = "rewiring"  # Change connection patterns
    CONSOLIDATION = "consolidation"  # Strengthen important paths


@dataclass
class SynapseState:
    """State of a synapse (connection)."""
    weight: float
    importance: float = 0.0
    activation_count: int = 0
    last_activation: Optional[datetime] = None
    gradient_history: List[float] = field(default_factory=list)
    is_pruned: bool = False
    creation_time: datetime = field(default_factory=datetime.now)


@dataclass
class NeuronState:
    """State of a neuron."""
    activation_mean: float = 0.0
    activation_std: float = 1.0
    firing_rate: float = 0.5
    importance: float = 0.0
    is_active: bool = True
    incoming_synapses: int = 0
    outgoing_synapses: int = 0


@dataclass
class PruningResult:
    """Result of a pruning operation."""
    original_params: int
    pruned_params: int
    sparsity: float
    performance_before: float
    performance_after: float
    pruned_indices: List[Tuple[int, int]]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PlasticityEvent:
    """Record of a plasticity event."""
    event_type: AdaptationType
    layer_index: int
    affected_synapses: int
    magnitude: float
    trigger: str
    timestamp: datetime = field(default_factory=datetime.now)


class SynapticPruner:
    """
    Implements synaptic pruning for neural network optimization.
    
    Features:
    - Multiple pruning strategies
    - Gradual pruning schedules
    - Importance scoring
    - Recovery mechanisms
    """
    
    def __init__(
        self,
        strategy: PruningStrategy = PruningStrategy.MAGNITUDE,
        target_sparsity: float = 0.5,
        pruning_rate: float = 0.1,
        min_weight_threshold: float = 0.01,
        importance_decay: float = 0.99
    ):
        try:
            self.strategy = strategy
            self.target_sparsity = target_sparsity
            self.pruning_rate = pruning_rate
            self.min_weight_threshold = min_weight_threshold
            self.importance_decay = importance_decay
        
            self.synapse_states: Dict[Tuple[int, int, int], SynapseState] = {}
            self.pruning_history: List[PruningResult] = []
            self.pruning_mask: Dict[int, np.ndarray] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def initialize_synapse_tracking(self, weights: Dict[str, np.ndarray]) -> None:
        """Initialize tracking for all synapses."""
        try:
            for layer_idx, (name, weight_matrix) in enumerate(weights.items()):
                if weight_matrix.ndim < 2:
                    continue
                
                for i in range(weight_matrix.shape[0]):
                    for j in range(weight_matrix.shape[1]):
                        key = (layer_idx, i, j)
                        self.synapse_states[key] = SynapseState(
                            weight=float(weight_matrix[i, j])
                        )
            
                # Initialize pruning mask
                self.pruning_mask[layer_idx] = np.ones_like(weight_matrix, dtype=bool)
        except Exception as e:
            logger.error(f"Error in initialize_synapse_tracking: {e}")
            raise
    
    def compute_importance_scores(
        self,
        weights: Dict[str, np.ndarray],
        gradients: Optional[Dict[str, np.ndarray]] = None,
        activations: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[Tuple[int, int, int], float]:
        """Compute importance scores for all synapses."""
        try:
            importance_scores = {}
        
            for layer_idx, (name, weight_matrix) in enumerate(weights.items()):
                if weight_matrix.ndim < 2:
                    continue
                
                for i in range(weight_matrix.shape[0]):
                    for j in range(weight_matrix.shape[1]):
                        key = (layer_idx, i, j)
                    
                        if self.strategy == PruningStrategy.MAGNITUDE:
                            importance = abs(weight_matrix[i, j])
                        
                        elif self.strategy == PruningStrategy.GRADIENT:
                            if gradients and name in gradients:
                                grad = gradients[name][i, j]
                                importance = abs(weight_matrix[i, j] * grad)
                            else:
                                importance = abs(weight_matrix[i, j])
                            
                        elif self.strategy == PruningStrategy.ACTIVATION:
                            state = self.synapse_states.get(key)
                            if state:
                                importance = state.activation_count / max(1, sum(
                                    s.activation_count for s in self.synapse_states.values()
                                ))
                            else:
                                importance = 0.0
                            
                        elif self.strategy == PruningStrategy.SENSITIVITY:
                            # Approximate sensitivity by weight * gradient
                            if gradients and name in gradients:
                                importance = abs(weight_matrix[i, j]) * abs(gradients[name][i, j])
                            else:
                                importance = abs(weight_matrix[i, j])
                        else:
                            importance = abs(weight_matrix[i, j])
                    
                        importance_scores[key] = importance
                    
                        # Update synapse state
                        if key in self.synapse_states:
                            self.synapse_states[key].importance = importance
        
            return importance_scores
        except Exception as e:
            logger.error(f"Error in compute_importance_scores: {e}")
            raise
    
    def prune_weights(
        self,
        weights: Dict[str, np.ndarray],
        gradients: Optional[Dict[str, np.ndarray]] = None,
        current_performance: float = 0.0
    ) -> Tuple[Dict[str, np.ndarray], PruningResult]:
        """Prune weights based on importance scores."""
        # Compute importance
        try:
            importance_scores = self.compute_importance_scores(weights, gradients)
        
            # Sort by importance
            sorted_synapses = sorted(importance_scores.items(), key=lambda x: x[1])
        
            # Determine how many to prune
            total_synapses = len(sorted_synapses)
            current_sparsity = sum(1 for s in self.synapse_states.values() if s.is_pruned) / max(1, total_synapses)
        
            if current_sparsity >= self.target_sparsity:
                # Already at target sparsity
                return weights, PruningResult(
                    original_params=total_synapses,
                    pruned_params=int(current_sparsity * total_synapses),
                    sparsity=current_sparsity,
                    performance_before=current_performance,
                    performance_after=current_performance,
                    pruned_indices=[]
                )
        
            # Calculate number to prune this iteration
            remaining_to_prune = int((self.target_sparsity - current_sparsity) * total_synapses)
            to_prune_now = min(remaining_to_prune, int(self.pruning_rate * total_synapses))
        
            # Prune lowest importance synapses
            pruned_indices = []
            pruned_weights = {k: v.copy() for k, v in weights.items()}
            weight_names = list(weights.keys())
        
            for (layer_idx, i, j), importance in sorted_synapses[:to_prune_now]:
                if layer_idx < len(weight_names):
                    name = weight_names[layer_idx]
                    if name in pruned_weights:
                        pruned_weights[name][i, j] = 0.0
                    
                        # Update mask
                        if layer_idx in self.pruning_mask:
                            self.pruning_mask[layer_idx][i, j] = False
                    
                        # Update synapse state
                        key = (layer_idx, i, j)
                        if key in self.synapse_states:
                            self.synapse_states[key].is_pruned = True
                    
                        pruned_indices.append((layer_idx, i, j))
        
            # Calculate new sparsity
            new_sparsity = sum(1 for s in self.synapse_states.values() if s.is_pruned) / max(1, total_synapses)
        
            result = PruningResult(
                original_params=total_synapses,
                pruned_params=len(pruned_indices),
                sparsity=new_sparsity,
                performance_before=current_performance,
                performance_after=current_performance,  # Will be updated after evaluation
                pruned_indices=pruned_indices
            )
        
            self.pruning_history.append(result)
        
            return pruned_weights, result
        except Exception as e:
            logger.error(f"Error in prune_weights: {e}")
            raise
    
    def apply_pruning_mask(self, weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Apply pruning mask to weights."""
        try:
            masked_weights = {}
            weight_names = list(weights.keys())
        
            for layer_idx, (name, weight_matrix) in enumerate(weights.items()):
                if layer_idx in self.pruning_mask and weight_matrix.shape == self.pruning_mask[layer_idx].shape:
                    masked_weights[name] = weight_matrix * self.pruning_mask[layer_idx]
                else:
                    masked_weights[name] = weight_matrix
        
            return masked_weights
        except Exception as e:
            logger.error(f"Error in apply_pruning_mask: {e}")
            raise
    
    def regrow_connections(
        self,
        weights: Dict[str, np.ndarray],
        regrowth_ratio: float = 0.1
    ) -> Dict[str, np.ndarray]:
        """Regrow pruned connections based on gradient information."""
        try:
            regrown_weights = {k: v.copy() for k, v in weights.items()}
            weight_names = list(weights.keys())
        
            # Find pruned synapses
            pruned_synapses = [
                key for key, state in self.synapse_states.items()
                if state.is_pruned
            ]
        
            # Randomly select some to regrow
            num_to_regrow = int(len(pruned_synapses) * regrowth_ratio)
            to_regrow = np.random.choice(len(pruned_synapses), min(num_to_regrow, len(pruned_synapses)), replace=False)
        
            for idx in to_regrow:
                layer_idx, i, j = pruned_synapses[idx]
                if layer_idx < len(weight_names):
                    name = weight_names[layer_idx]
                    if name in regrown_weights:
                        # Initialize with small random weight
                        regrown_weights[name][i, j] = np.random.randn() * 0.01
                    
                        # Update mask and state
                        if layer_idx in self.pruning_mask:
                            self.pruning_mask[layer_idx][i, j] = True
                    
                        key = (layer_idx, i, j)
                        if key in self.synapse_states:
                            self.synapse_states[key].is_pruned = False
        
            return regrown_weights
        except Exception as e:
            logger.error(f"Error in regrow_connections: {e}")
            raise
    
    def get_sparsity_stats(self) -> Dict[str, Any]:
        """Get statistics about current sparsity."""
        try:
            total = len(self.synapse_states)
            pruned = sum(1 for s in self.synapse_states.values() if s.is_pruned)
        
            return {
                'total_synapses': total,
                'pruned_synapses': pruned,
                'active_synapses': total - pruned,
                'sparsity': pruned / max(1, total),
                'target_sparsity': self.target_sparsity,
                'pruning_iterations': len(self.pruning_history)
            }
        except Exception as e:
            logger.error(f"Error in get_sparsity_stats: {e}")
            raise


class NeuralPlasticity:
    """
    Implements neural plasticity for continuous learning.
    
    Features:
    - Hebbian learning
    - Homeostatic plasticity
    - Synaptic scaling
    - Metaplasticity
    - Catastrophic forgetting prevention
    """
    
    def __init__(
        self,
        mode: PlasticityMode = PlasticityMode.HEBBIAN,
        learning_rate: float = 0.01,
        homeostatic_target: float = 0.5,
        consolidation_threshold: float = 0.8,
        ewc_lambda: float = 1000.0  # Elastic Weight Consolidation
    ):
        try:
            self.mode = mode
            self.learning_rate = learning_rate
            self.homeostatic_target = homeostatic_target
            self.consolidation_threshold = consolidation_threshold
            self.ewc_lambda = ewc_lambda
        
            self.neuron_states: Dict[Tuple[int, int], NeuronState] = {}
            self.plasticity_events: List[PlasticityEvent] = []
        
            # For EWC (catastrophic forgetting prevention)
            self.fisher_information: Dict[str, np.ndarray] = {}
            self.optimal_weights: Dict[str, np.ndarray] = {}
            self.task_count: int = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def initialize_neuron_tracking(self, layer_sizes: List[int]) -> None:
        """Initialize tracking for all neurons."""
        try:
            for layer_idx, size in enumerate(layer_sizes):
                for neuron_idx in range(size):
                    key = (layer_idx, neuron_idx)
                    self.neuron_states[key] = NeuronState()
        except Exception as e:
            logger.error(f"Error in initialize_neuron_tracking: {e}")
            raise
    
    def hebbian_update(
        self,
        weights: np.ndarray,
        pre_activation: np.ndarray,
        post_activation: np.ndarray
    ) -> np.ndarray:
        """Apply Hebbian learning rule: Δw = η * pre * post."""
        # Outer product gives correlation
        try:
            delta_w = self.learning_rate * np.outer(post_activation, pre_activation)
        
            # Normalize to prevent unbounded growth
            delta_w = delta_w / (np.linalg.norm(delta_w) + 1e-10)
        
            return weights + delta_w
        except Exception as e:
            logger.error(f"Error in hebbian_update: {e}")
            raise
    
    def anti_hebbian_update(
        self,
        weights: np.ndarray,
        pre_activation: np.ndarray,
        post_activation: np.ndarray
    ) -> np.ndarray:
        """Apply anti-Hebbian learning for decorrelation."""
        try:
            delta_w = -self.learning_rate * np.outer(post_activation, pre_activation)
            delta_w = delta_w / (np.linalg.norm(delta_w) + 1e-10)
        
            return weights + delta_w
        except Exception as e:
            logger.error(f"Error in anti_hebbian_update: {e}")
            raise
    
    def bcm_update(
        self,
        weights: np.ndarray,
        pre_activation: np.ndarray,
        post_activation: np.ndarray,
        threshold: float
    ) -> np.ndarray:
        """
        Apply BCM (Bienenstock-Cooper-Munro) learning rule.
        
        Δw = η * pre * post * (post - θ)
        where θ is a sliding threshold based on average activity.
        """
        # BCM modification factor
        try:
            bcm_factor = post_activation * (post_activation - threshold)
        
            delta_w = self.learning_rate * np.outer(bcm_factor, pre_activation)
            delta_w = delta_w / (np.linalg.norm(delta_w) + 1e-10)
        
            return weights + delta_w
        except Exception as e:
            logger.error(f"Error in bcm_update: {e}")
            raise
    
    def homeostatic_scaling(
        self,
        weights: np.ndarray,
        current_activity: float,
        layer_idx: int
    ) -> np.ndarray:
        """Apply homeostatic synaptic scaling to maintain target activity."""
        # Calculate scaling factor
        try:
            if current_activity < 1e-10:
                scaling_factor = 1.1  # Increase weights if no activity
            else:
                scaling_factor = self.homeostatic_target / current_activity
        
            # Limit scaling to prevent instability
            scaling_factor = np.clip(scaling_factor, 0.9, 1.1)
        
            scaled_weights = weights * scaling_factor
        
            # Record event
            self.plasticity_events.append(PlasticityEvent(
                event_type=AdaptationType.CONSOLIDATION,
                layer_index=layer_idx,
                affected_synapses=weights.size,
                magnitude=scaling_factor,
                trigger='homeostatic_scaling'
            ))
        
            return scaled_weights
        except Exception as e:
            logger.error(f"Error in homeostatic_scaling: {e}")
            raise
    
    def apply_plasticity(
        self,
        weights: Dict[str, np.ndarray],
        activations: Dict[str, np.ndarray],
        layer_idx: int = 0
    ) -> Dict[str, np.ndarray]:
        """Apply plasticity rules to weights based on activations."""
        try:
            updated_weights = {}
        
            weight_names = list(weights.keys())
            activation_names = list(activations.keys())
        
            for i, (name, weight_matrix) in enumerate(weights.items()):
                if weight_matrix.ndim < 2:
                    updated_weights[name] = weight_matrix
                    continue
            
                # Get pre and post activations
                if i < len(activation_names) - 1:
                    pre_act = activations.get(activation_names[i], np.ones(weight_matrix.shape[1]))
                    post_act = activations.get(activation_names[i + 1], np.ones(weight_matrix.shape[0]))
                else:
                    updated_weights[name] = weight_matrix
                    continue
            
                # Ensure correct shapes
                if len(pre_act.shape) > 1:
                    pre_act = pre_act.mean(axis=0)
                if len(post_act.shape) > 1:
                    post_act = post_act.mean(axis=0)
            
                # Resize if needed
                if len(pre_act) != weight_matrix.shape[1]:
                    pre_act = np.resize(pre_act, weight_matrix.shape[1])
                if len(post_act) != weight_matrix.shape[0]:
                    post_act = np.resize(post_act, weight_matrix.shape[0])
            
                # Apply plasticity based on mode
                if self.mode == PlasticityMode.HEBBIAN:
                    updated_weights[name] = self.hebbian_update(weight_matrix, pre_act, post_act)
                elif self.mode == PlasticityMode.ANTI_HEBBIAN:
                    updated_weights[name] = self.anti_hebbian_update(weight_matrix, pre_act, post_act)
                elif self.mode == PlasticityMode.BCM:
                    threshold = np.mean(post_act ** 2)
                    updated_weights[name] = self.bcm_update(weight_matrix, pre_act, post_act, threshold)
                elif self.mode == PlasticityMode.HOMEOSTATIC:
                    current_activity = np.mean(np.abs(post_act))
                    updated_weights[name] = self.homeostatic_scaling(weight_matrix, current_activity, i)
                else:
                    updated_weights[name] = weight_matrix
        
            return updated_weights
        except Exception as e:
            logger.error(f"Error in apply_plasticity: {e}")
            raise
    
    def compute_fisher_information(
        self,
        weights: Dict[str, np.ndarray],
        gradients: Dict[str, np.ndarray]
    ) -> None:
        """Compute Fisher Information Matrix for EWC."""
        try:
            for name, grad in gradients.items():
                if name not in self.fisher_information:
                    self.fisher_information[name] = np.zeros_like(grad)
            
                # Fisher information is expectation of squared gradients
                self.fisher_information[name] += grad ** 2
        
            # Store optimal weights for this task
            self.optimal_weights = {k: v.copy() for k, v in weights.items()}
            self.task_count += 1
        except Exception as e:
            logger.error(f"Error in compute_fisher_information: {e}")
            raise
    
    def ewc_regularization(
        self,
        weights: Dict[str, np.ndarray]
    ) -> float:
        """Compute EWC regularization loss to prevent catastrophic forgetting."""
        try:
            if not self.fisher_information or not self.optimal_weights:
                return 0.0
        
            ewc_loss = 0.0
            for name, weight in weights.items():
                if name in self.fisher_information and name in self.optimal_weights:
                    diff = weight - self.optimal_weights[name]
                    ewc_loss += np.sum(self.fisher_information[name] * (diff ** 2))
        
            return 0.5 * self.ewc_lambda * ewc_loss
        except Exception as e:
            logger.error(f"Error in ewc_regularization: {e}")
            raise
    
    def consolidate_learning(
        self,
        weights: Dict[str, np.ndarray],
        importance_threshold: float = 0.5
    ) -> Dict[str, np.ndarray]:
        """Consolidate important weights to prevent forgetting."""
        try:
            consolidated = {}
        
            for name, weight_matrix in weights.items():
                if name in self.fisher_information:
                    # Identify important weights
                    importance = self.fisher_information[name]
                    important_mask = importance > (importance_threshold * np.max(importance))
                
                    # Reduce plasticity for important weights
                    plasticity_factor = np.where(important_mask, 0.1, 1.0)
                
                    consolidated[name] = weight_matrix * plasticity_factor + \
                                        self.optimal_weights.get(name, weight_matrix) * (1 - plasticity_factor)
                else:
                    consolidated[name] = weight_matrix
        
            return consolidated
        except Exception as e:
            logger.error(f"Error in consolidate_learning: {e}")
            raise
    
    def get_plasticity_summary(self) -> Dict[str, Any]:
        """Get summary of plasticity state."""
        return {
            'mode': self.mode.value,
            'total_neurons': len(self.neuron_states),
            'active_neurons': sum(1 for n in self.neuron_states.values() if n.is_active),
            'plasticity_events': len(self.plasticity_events),
            'tasks_learned': self.task_count,
            'has_fisher_info': len(self.fisher_information) > 0
        }


class AdaptiveArchitecture:
    """
    Implements adaptive network architecture that grows and shrinks.
    
    Features:
    - Dynamic neuron addition/removal
    - Connection rewiring
    - Architecture search
    - Capacity estimation
    """
    
    def __init__(
        self,
        min_neurons_per_layer: int = 10,
        max_neurons_per_layer: int = 1000,
        growth_threshold: float = 0.9,
        shrink_threshold: float = 0.1
    ):
        try:
            self.min_neurons = min_neurons_per_layer
            self.max_neurons = max_neurons_per_layer
            self.growth_threshold = growth_threshold
            self.shrink_threshold = shrink_threshold
        
            self.architecture_history: List[List[int]] = []
            self.adaptation_events: List[PlasticityEvent] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def should_grow(self, layer_utilization: float) -> bool:
        """Determine if layer should grow."""
        return layer_utilization > self.growth_threshold
    
    def should_shrink(self, layer_utilization: float) -> bool:
        """Determine if layer should shrink."""
        return layer_utilization < self.shrink_threshold
    
    def add_neurons(
        self,
        weights_in: np.ndarray,
        weights_out: np.ndarray,
        num_neurons: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Add neurons to a layer."""
        try:
            current_size = weights_in.shape[0]
        
            if current_size + num_neurons > self.max_neurons:
                num_neurons = self.max_neurons - current_size
        
            if num_neurons <= 0:
                return weights_in, weights_out
        
            # Add rows to incoming weights
            new_rows = np.random.randn(num_neurons, weights_in.shape[1]) * 0.01
            new_weights_in = np.vstack([weights_in, new_rows])
        
            # Add columns to outgoing weights
            new_cols = np.random.randn(weights_out.shape[0], num_neurons) * 0.01
            new_weights_out = np.hstack([weights_out, new_cols])
        
            return new_weights_in, new_weights_out
        except Exception as e:
            logger.error(f"Error in add_neurons: {e}")
            raise
    
    def remove_neurons(
        self,
        weights_in: np.ndarray,
        weights_out: np.ndarray,
        neuron_importance: np.ndarray,
        num_neurons: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Remove least important neurons from a layer."""
        try:
            current_size = weights_in.shape[0]
        
            if current_size - num_neurons < self.min_neurons:
                num_neurons = current_size - self.min_neurons
        
            if num_neurons <= 0:
                return weights_in, weights_out
        
            # Find least important neurons
            indices_to_remove = np.argsort(neuron_importance)[:num_neurons]
            indices_to_keep = np.setdiff1d(np.arange(current_size), indices_to_remove)
        
            # Remove from weights
            new_weights_in = weights_in[indices_to_keep]
            new_weights_out = weights_out[:, indices_to_keep]
        
            return new_weights_in, new_weights_out
        except Exception as e:
            logger.error(f"Error in remove_neurons: {e}")
            raise
    
    def rewire_connections(
        self,
        weights: np.ndarray,
        connection_importance: np.ndarray,
        rewire_ratio: float = 0.1
    ) -> np.ndarray:
        """Rewire low-importance connections."""
        try:
            flat_weights = weights.flatten()
            flat_importance = connection_importance.flatten()
        
            # Find lowest importance connections
            num_to_rewire = int(len(flat_weights) * rewire_ratio)
            indices_to_rewire = np.argsort(flat_importance)[:num_to_rewire]
        
            # Rewire to random new values
            flat_weights[indices_to_rewire] = np.random.randn(num_to_rewire) * 0.01
        
            return flat_weights.reshape(weights.shape)
        except Exception as e:
            logger.error(f"Error in rewire_connections: {e}")
            raise
    
    def estimate_capacity(
        self,
        weights: Dict[str, np.ndarray],
        activations: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Estimate remaining capacity of each layer."""
        try:
            capacity = {}
        
            for name, weight_matrix in weights.items():
                if weight_matrix.ndim < 2:
                    continue
            
                # Estimate based on weight saturation
                weight_saturation = np.mean(np.abs(weight_matrix) > 0.9)
            
                # Estimate based on activation diversity
                if name in activations:
                    act = activations[name]
                    if act.ndim > 1:
                        act = act.mean(axis=0)
                    activation_diversity = np.std(act) / (np.mean(np.abs(act)) + 1e-10)
                else:
                    activation_diversity = 1.0
            
                # Combine estimates
                capacity[name] = (1 - weight_saturation) * min(1.0, activation_diversity)
        
            return capacity
        except Exception as e:
            logger.error(f"Error in estimate_capacity: {e}")
            raise


# Convenience functions
def create_adaptive_network(
    layer_sizes: List[int],
    pruning_strategy: str = "magnitude",
    plasticity_mode: str = "hebbian"
) -> Tuple[SynapticPruner, NeuralPlasticity, AdaptiveArchitecture]:
    """Create a complete adaptive network system."""
    try:
        pruner = SynapticPruner(
            strategy=PruningStrategy(pruning_strategy),
            target_sparsity=0.5
        )
    
        plasticity = NeuralPlasticity(
            mode=PlasticityMode(plasticity_mode)
        )
        plasticity.initialize_neuron_tracking(layer_sizes)
    
        architecture = AdaptiveArchitecture()
    
        return pruner, plasticity, architecture
    except Exception as e:
        logger.error(f"Error in create_adaptive_network: {e}")
        raise


def apply_neural_adaptation(
    weights: Dict[str, np.ndarray],
    gradients: Dict[str, np.ndarray],
    activations: Dict[str, np.ndarray],
    pruner: SynapticPruner,
    plasticity: NeuralPlasticity
) -> Dict[str, np.ndarray]:
    """Apply complete neural adaptation pipeline."""
    # Apply plasticity
    try:
        adapted_weights = plasticity.apply_plasticity(weights, activations)
    
        # Apply pruning
        pruned_weights, _ = pruner.prune_weights(adapted_weights, gradients)
    
        # Apply pruning mask
        final_weights = pruner.apply_pruning_mask(pruned_weights)
    
        return final_weights
    except Exception as e:
        logger.error(f"Error in apply_neural_adaptation: {e}")
        raise
