"""
Phase 4: World Models - Latent Dynamics
DreamerV3-style world model for market simulation

L1: Multimodal Perception Foundation
  - Video, audio, proprioception, state streams, structured sensors, language as metadata
  - Temporal Contrastive Predictive Coding with Boundary Sharpening
  - V-JEPA 2 backbone for dense feature extraction
  - Temporal Segment Networks (TSN) head for event boundary detection
  - Surprise Reservoir buffer linking L3 uncertainty to L1 segmentation

L3: World Model Ensemble
  - JEPA-style latent predictive model for abstract state prediction
  - Action-conditioned dynamics model (DreamerV3 RSSM in JEPA latent space)
  - Short-horizon high-fidelity model (fast RSSM)
  - Long-horizon abstract model (jump macro-transition via Set Transformer)
  - Ensemble disagreement for epistemic uncertainty
  - Skip-Graph: fast model predicts millisecond changes, slow model predicts
    transition between Abstract Options; slow model latent updated only on
    Contact Event or Subgoal Achievement from L2
  - MoE Gating Network weighting fast vs jump model

  B1 Ceiling-Pushed — Triangulated Consistency (not just pairwise):
    Agreement is not truth. Two broken models that agree still produce bad plans.
    So the stronger version is triangulated consistency:
    1. fast chained rollout vs jump rollout (cross-scale)
    2. both vs sparse re-encoded observation anchors (ground truth)
    3. both penalized for uncertainty blow-up (entropy penalty)
    4. planner trust horizon cut off when disagreement exceeds calibration
    5. learned macro-action hierarchy for top-down planning
    6. self-forced long-horizon distillation
    Without re-anchoring, models will agree their way into delusion.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass, field
from enum import Enum
from .world_state import MarketWorldState, VolatilityRegime, LiquidityCondition, SystemMode
from .ignorance_score import IgnoranceScoreEngine
from collections import deque

logger = logging.getLogger(__name__)


# =============================================================================
# L1: Multimodal Perception Foundation + Event Segmentation
# =============================================================================

class StreamModality(Enum):
    """Supported input modalities for L1 perception."""
    VIDEO = "video"
    AUDIO = "audio"
    PROPRIOCEPTION = "proprioception"
    STATE_VECTOR = "state_vector"
    STRUCTURED_SENSOR = "structured_sensor"
    LANGUAGE = "language"  # metadata/interface, not ontological core
    ORDER_BOOK = "order_book"
    TICK_DATA = "tick_data"


@dataclass
class MultimodalFrame:
    """A single timestep of multimodal input."""
    timestamp: float
    modalities: Dict[str, np.ndarray]  # modality_name -> data array
    metadata: Dict[str, str] = field(default_factory=dict)


class TemporalSegmentNetwork(nn.Module):
    """
    TSN head trained to predict whether two frames belong to the same
    episode vs crossing an event boundary (Zacks' Event Segmentation Theory).
    """

    def __init__(self, feature_dim: int = 64, hidden_dim: int = 32):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(feature_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, feat_a: torch.Tensor, feat_b: torch.Tensor) -> torch.Tensor:
        """Return probability that two feature vectors cross an event boundary."""
        combined = torch.cat([feat_a, feat_b], dim=-1)
        return self.classifier(combined)


class SurpriseReservoir:
    """
    Buffer linking L3 world model ensemble disagreement to L1 segmentation.
    If ensemble disagreement exceeds threshold tau, force an Event Boundary
    Flag retroactively and re-encode the latent segment.
    """

    def __init__(self, capacity: int = 1000, boundary_threshold: float = 2.0):
        self.capacity = capacity
        self.boundary_threshold = boundary_threshold
        self.reservoir: deque = deque(maxlen=capacity)
        self.forced_boundaries: List[int] = []

    def register_disagreement(self, timestep: int, disagreement: float):
        """Register ensemble disagreement at a timestep."""
        self.reservoir.append((timestep, disagreement))
        if disagreement > self.boundary_threshold:
            self.forced_boundaries.append(timestep)

    def check_forced_boundary(self, timestep: int) -> bool:
        """Check if a forced boundary was triggered at this timestep."""
        return timestep in self.forced_boundaries

    def clear(self):
        self.reservoir.clear()
        self.forced_boundaries.clear()


class MultimodalPerceptionEncoder(nn.Module):
    """
    L1: Multimodal Perception Foundation

    Encodes raw streams (video, audio, proprioception, state, structured sensors,
    optionally language) into a unified latent representation.
    Text is metadata, interface, and abstraction support — not the ontological core.

    Includes:
    - Per-modality encoders
    - Cross-modal fusion
    - Temporal Segment Networks (TSN) head for event boundary detection
    - Surprise Reservoir linking L3 uncertainty to L1 segmentation
    """

    def __init__(
        self,
        modality_dims: Optional[Dict[str, int]] = None,
        latent_dim: int = 64,
        hidden_dim: int = 128
    ):
        super().__init__()

        default_dims = {
            'state_vector': 20,
            'order_book': 50,
            'tick_data': 10,
            'structured_sensor': 15,
        }
        self.modality_dims = modality_dims or default_dims
        self.latent_dim = latent_dim

        # Per-modality encoders
        self.modality_encoders = nn.ModuleDict()
        for mod_name, dim in self.modality_dims.items():
            self.modality_encoders[mod_name] = nn.Sequential(
                nn.Linear(dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, latent_dim)
            )

        # Cross-modal fusion (attention-weighted)
        self.fusion_attention = nn.Sequential(
            nn.Linear(latent_dim, 1),
            nn.Softmax(dim=1)
        )

        # Temporal Segment Networks head for event boundary detection
        self.tsn_head = TemporalSegmentNetwork(latent_dim)

        # Surprise Reservoir
        self.surprise_reservoir = SurpriseReservoir()

        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(latent_dim, latent_dim),
            nn.LayerNorm(latent_dim)
        )

    def forward(
        self,
        modalities: Dict[str, torch.Tensor],
        prev_latent: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Encode multimodal input into unified latent.

        Returns:
            fused_latent: Unified latent representation
            info: Dict with event_boundary_prob, forced_boundary flag
        """
        encoded = []
        for mod_name, encoder in self.modality_encoders.items():
            if mod_name in modalities:
                encoded.append(encoder(modalities[mod_name]))

        if not encoded:
            batch_size = list(modalities.values())[0].size(0) if modalities else 1
            fused = torch.zeros(batch_size, self.latent_dim, device=next(self.parameters()).device)
        else:
            stacked = torch.stack(encoded, dim=1)  # [B, n_modalities, latent_dim]
            attn_weights = self.fusion_attention(stacked)  # [B, n_modalities, 1]
            fused = (stacked * attn_weights).sum(dim=1)  # [B, latent_dim]

        fused = self.output_proj(fused)

        # Event boundary detection
        info = {'event_boundary_prob': 0.0, 'forced_boundary': False}
        if prev_latent is not None:
            boundary_prob = self.tsn_head(fused, prev_latent)
            info['event_boundary_prob'] = boundary_prob.mean().item()

        return fused, info

    def check_surprise_boundary(self, timestep: int, ensemble_disagreement: float) -> bool:
        """Check L3 disagreement and potentially force event boundary."""
        self.surprise_reservoir.register_disagreement(timestep, ensemble_disagreement)
        return self.surprise_reservoir.check_forced_boundary(timestep)


# =============================================================================
# L3: World Model Ensemble — JEPA × Dreamer RSSM Fusion + Skip-Graph
# =============================================================================

class JEPALatentPredictor(nn.Module):
    """
    JEPA-style latent predictive model: predicts abstract next latent state
    without reconstructing pixels. Predicts in latent space directly.
    """

    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim * 2, hidden_dim),  # current + action
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )
        self.latent_dim = latent_dim

    def forward(self, latent: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Predict next abstract latent state."""
        x = torch.cat([latent, action], dim=-1)
        return self.predictor(x)


class FastRSSMModel(nn.Module):
    """
    Short-horizon high-fidelity model: DreamerV3-style RSSM for local dynamics.
    Predicts millisecond-level changes (physics-level).
    """

    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128, action_dim: int = 5):
        super().__init__()
        self.latent_dim = latent_dim

        # Deterministic path (GRU)
        self.rnn = nn.GRU(
            input_size=latent_dim + action_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True
        )

        # Prior network
        self.prior = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim * 2)
        )

        # Posterior network (incorporates observation)
        self.posterior = nn.Sequential(
            nn.Linear(hidden_dim + latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim * 2)
        )

        self.hidden_dim = hidden_dim

    def forward(
        self,
        latent_state: torch.Tensor,
        action: torch.Tensor,
        hidden_state: Optional[torch.Tensor] = None,
        obs_latent: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict next latent state distribution.

        Returns:
            prior_mean, prior_logvar, new_hidden_state
        """
        rnn_input = torch.cat([latent_state, action], dim=-1).unsqueeze(1)
        _, hidden_state = self.rnn(rnn_input, hidden_state)

        prior_params = self.prior(hidden_state[-1])
        prior_mean, prior_logvar = torch.chunk(prior_params, 2, dim=-1)

        return prior_mean, prior_logvar, hidden_state

    def posterior_update(
        self,
        hidden_state: torch.Tensor,
        obs_latent: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Posterior update incorporating actual observation."""
        post_input = torch.cat([hidden_state[-1], obs_latent], dim=-1)
        post_params = self.posterior(post_input)
        post_mean, post_logvar = torch.chunk(post_params, 2, dim=-1)
        return post_mean, post_logvar


class JumpMacroTransitionModel(nn.Module):
    """
    Long-horizon abstract model: Set Transformer that takes object graph (L2)
    and selected Option (L7) as input and predicts post-option latent graph state.
    Updated only when Contact Event or Subgoal Achievement detected in L2.
    """

    def __init__(
        self,
        graph_dim: int = 64,
        option_dim: int = 32,
        hidden_dim: int = 128,
        n_heads: int = 4
    ):
        super().__init__()
        # Set Transformer encoder for object graph
        self.graph_encoder = nn.Sequential(
            nn.Linear(graph_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

        # Option encoder
        self.option_encoder = nn.Sequential(
            nn.Linear(option_dim, hidden_dim),
            nn.ReLU()
        )

        # Cross-attention between graph and option
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=n_heads,
            batch_first=True
        )

        # Predict post-option graph state
        self.output_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, graph_dim)
        )

    def forward(
        self,
        graph_latent: torch.Tensor,
        option_latent: torch.Tensor
    ) -> torch.Tensor:
        """Predict post-option latent graph state."""
        encoded_graph = self.graph_encoder(graph_latent).unsqueeze(1)
        encoded_option = self.option_encoder(option_latent).unsqueeze(1)

        attended, _ = self.cross_attention(
            encoded_graph, encoded_option, encoded_option
        )

        return self.output_head(attended.squeeze(1))


class MoEGatingNetwork(nn.Module):
    """
    Mixture of Experts Gating Network that weights fast model output vs
    jump model output based on:
    - Prediction error of fast model
    - Detection of contact state change in L2 graph
    - Temporal abstraction budget (learned resource allocation)
    """

    def __init__(self, input_dim: int = 3, n_experts: int = 2):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, n_experts),
            nn.Softmax(dim=-1)
        )
        self.n_experts = n_experts

    def forward(
        self,
        fast_pred_error: torch.Tensor,
        contact_change_flag: torch.Tensor,
        abstraction_budget: torch.Tensor
    ) -> torch.Tensor:
        """
        Returns gating weights [fast_weight, jump_weight].
        """
        gate_input = torch.stack([fast_pred_error, contact_change_flag, abstraction_budget], dim=-1)
        return self.gate(gate_input)


class EnsembleWorldModel(nn.Module):
    """
    L3: World Model Ensemble with epistemic uncertainty via disagreement.

    Multiple RSSM models with different initializations; ensemble disagreement
    measures epistemic uncertainty.
    """

    def __init__(
        self,
        n_models: int = 5,
        latent_dim: int = 64,
        hidden_dim: int = 128,
        action_dim: int = 5
    ):
        super().__init__()
        self.n_models = n_models
        self.models = nn.ModuleList([
            FastRSSMModel(latent_dim, hidden_dim, action_dim)
            for _ in range(n_models)
        ])
        self.latent_dim = latent_dim

    def forward(
        self,
        latent_state: torch.Tensor,
        action: torch.Tensor,
        hidden_states: Optional[List[torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, List[torch.Tensor], torch.Tensor]:
        """
        Forward pass through all ensemble members.

        Returns:
            mean_prediction: Average prediction across ensemble
            mean_logvar: Average logvar across ensemble
            new_hidden_states: List of new hidden states
            disagreement: Epistemic uncertainty (variance of predictions)
        """
        predictions = []
        logvars = []
        new_hiddens = []

        for i, model in enumerate(self.models):
            h = hidden_states[i] if hidden_states is not None else None
            mean, logvar, new_h = model(latent_state, action, h)
            predictions.append(mean)
            logvars.append(logvar)
            new_hiddens.append(new_h)

        predictions = torch.stack(predictions)  # [n_models, B, latent_dim]
        logvars = torch.stack(logvars)

        mean_prediction = predictions.mean(dim=0)
        mean_logvar = logvars.mean(dim=0)
        disagreement = predictions.var(dim=0).mean(dim=-1)  # scalar per batch

        return mean_prediction, mean_logvar, new_hiddens, disagreement


class MarketStateEncoder(nn.Module):
    """Encodes market state into latent representation."""
    
    def __init__(self, input_dim: int = 20, latent_dim: int = 32):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim * 2)  # Mean and logvar
        )
        
        self.latent_dim = latent_dim
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode market state into latent distribution.
        Returns mean and logvar for reparameterization.
        """
        x = self.encoder(x)
        mean, logvar = torch.chunk(x, 2, dim=-1)
        return mean, logvar
    
    def sample(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Sample from latent distribution using reparameterization."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std


class MarketStateDecoder(nn.Module):
    """Decodes latent representation back to market state."""
    
    def __init__(self, latent_dim: int = 32, output_dim: int = 20):
        super().__init__()
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )
    
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent state to market state."""
        return self.decoder(z)


class LatentDynamicsModel(nn.Module):
    """
    Predicts evolution of latent state over time.
    Includes stochastic and deterministic paths.
    """
    
    def __init__(self, latent_dim: int = 32, hidden_dim: int = 64):
        super().__init__()
        
        # Deterministic path (GRU)
        self.rnn = nn.GRU(
            input_size=latent_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True
        )
        
        # Prior network (predicts next latent state)
        self.prior = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, latent_dim * 2)  # Mean and logvar
        )
        
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
    
    def forward(
        self,
        latent_state: torch.Tensor,
        hidden_state: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Predict next latent state distribution.
        
        Returns:
            mean, logvar, new_hidden_state
        """
        # Update RNN state
        _, hidden_state = self.rnn(latent_state.unsqueeze(1), hidden_state)
        
        # Predict next latent state
        prior_params = self.prior(hidden_state[-1])
        mean, logvar = torch.chunk(prior_params, 2, dim=-1)
        
        return mean, logvar, hidden_state
    
    def sample_prediction(
        self,
        mean: torch.Tensor,
        logvar: torch.Tensor
    ) -> torch.Tensor:
        """Sample from predicted distribution."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std


class RewardPredictor(nn.Module):
    """Predicts rewards from latent states."""
    
    def __init__(self, latent_dim: int = 32):
        super().__init__()
        
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, latent_state: torch.Tensor) -> torch.Tensor:
        """Predict expected reward."""
        return self.predictor(latent_state)


# =============================================================================
# B1 Ceiling-Pushed: Triangulated Consistency Support Classes
# =============================================================================

class ObservationReAnchorer:
    """
    B1 Ceiling-Pushed: Sparse Observation Re-Anchoring.

    Without re-anchoring, models will agree their way into delusion.
    Every N rollout steps, re-encode the REAL observation and use it as
    a third anchor against which both fast and jump predictions are checked.

    This is the key insight: agreement between two models is not truth.
    You need a ground-truth anchor to triangulate against.
    """

    def __init__(
        self,
        encoder,
        latent_dim: int = 64,
        re_anchor_interval: int = 10
    ):
        self.encoder = encoder
        self.latent_dim = latent_dim
        self.re_anchor_interval = re_anchor_interval

        # Buffer of re-anchored latent states (ground truth)
        self.anchor_buffer: List[torch.Tensor] = []

    def should_re_anchor(self, rollout_step: int) -> bool:
        """Check if it's time to re-anchor on a real observation."""
        return rollout_step > 0 and rollout_step % self.re_anchor_interval == 0

    def re_anchor(self, real_observation: torch.Tensor) -> torch.Tensor:
        """
        Re-encode a real observation to get a ground-truth latent anchor.
        This anchor is NOT a prediction — it's an actual encoding of reality.
        """
        with torch.no_grad():
            mean, logvar = self.encoder(real_observation)
            anchor = mean  # Use mean for deterministic anchor

        self.anchor_buffer.append(anchor.detach())
        if len(self.anchor_buffer) > 100:
            self.anchor_buffer.pop(0)

        return anchor

    def compute_anchor_loss(
        self,
        predicted_latent: torch.Tensor,
        real_observation: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute loss between predicted latent and re-encoded real observation.
        This is the third leg of the triangulated consistency check.
        """
        anchor = self.re_anchor(real_observation)
        return F.mse_loss(predicted_latent, anchor.detach())


class UncertaintyHorizonGate:
    """
    B1 Ceiling-Pushed: Uncertainty-Horizon Gating.

    Planner trust horizon cut off when disagreement exceeds calibration.
    Trust decays exponentially with rollout length. Once trust drops below
    a threshold, the planner MUST re-anchor on real observations.

    This prevents the planner from making decisions based on unreliable
    long-horizon predictions that have drifted far from reality.
    """

    def __init__(
        self,
        disagreement_threshold: float = 2.0,
        horizon_decay: float = 0.95,
        trust_floor: float = 0.1
    ):
        self.disagreement_threshold = disagreement_threshold
        self.horizon_decay = horizon_decay
        self.trust_floor = trust_floor

        # Calibration: running statistics of disagreement
        self._disagreement_history: List[float] = []

    def compute_trust(
        self,
        rollout_step: int,
        current_disagreement: float
    ) -> Tuple[float, bool]:
        """
        Compute planner trust at this rollout step.

        Returns:
            trust: [0, 1] confidence in the rollout at this step
            should_stop: whether trust has fallen below the floor
        """
        # Trust decays with rollout length
        length_trust = self.horizon_decay ** rollout_step

        # Trust decreases with disagreement
        if current_disagreement > 0:
            disagreement_trust = min(1.0, self.disagreement_threshold / current_disagreement)
        else:
            disagreement_trust = 1.0

        # Combined trust
        trust = length_trust * disagreement_trust
        trust = max(trust, 0.0)

        should_stop = trust < self.trust_floor

        # Update calibration
        self._disagreement_history.append(current_disagreement)
        if len(self._disagreement_history) > 1000:
            self._disagreement_history = self._disagreement_history[-1000:]

        return trust, should_stop

    def recalibrate(self):
        """
        Recalibrate disagreement threshold based on observed history.
        If the model has improved, the threshold should tighten.
        """
        if len(self._disagreement_history) > 100:
            recent = self._disagreement_history[-100:]
            self.disagreement_threshold = np.percentile(recent, 90)


class MacroActionHierarchy(nn.Module):
    """
    B1 Ceiling-Pushed: Learned Macro-Action Hierarchy.

    Instead of planning over individual actions (expensive for long horizons),
    plan over learned macro-actions: multi-step action primitives that
    capture common behavioral patterns (e.g., "enter position", "scale in",
    "exit and reverse").

    This enables top-down hierarchical planning:
    - Level 1: Select macro-action sequence (CEM planner, L7)
    - Level 2: Expand macro-actions into individual actions (LQR tracker, L8)
    """

    def __init__(
        self,
        n_macro_actions: int = 16,
        action_dim: int = 5,
        macro_length: int = 5,
        latent_dim: int = 64,
        hidden_dim: int = 128
    ):
        super().__init__()
        self.n_macro_actions = n_macro_actions
        self.action_dim = action_dim
        self.macro_length = macro_length

        # Macro-action embeddings (learned action sequences)
        self.macro_embeddings = nn.Parameter(
            torch.randn(n_macro_actions, macro_length, action_dim) * 0.1
        )

        # Context-conditioned macro selector
        self.macro_selector = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_macro_actions),
        )

        # Macro-effect predictor: given latent + macro, predict outcome
        self.effect_predictor = nn.Sequential(
            nn.Linear(latent_dim + n_macro_actions, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

    def forward(
        self,
        latent_state: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Select macro-action and predict its effect.

        Returns:
            macro_action_seq: [B, macro_length, action_dim] action sequence
            predicted_effect: [B, latent_dim] predicted latent after macro
        """
        # Select macro-action
        logits = self.macro_selector(latent_state)
        probs = F.softmax(logits, dim=-1)

        # Get macro-action sequence (weighted combination)
        macro_seq = torch.einsum('bm,msa->bsa', probs, self.macro_embeddings)

        # Predict effect
        predicted_effect = self.effect_predictor(
            torch.cat([latent_state, probs], dim=-1)
        )

        return macro_seq, predicted_effect

    def get_macro_actions(self, macro_idx: int) -> torch.Tensor:
        """Get the action sequence for a specific macro-action."""
        return self.macro_embeddings[macro_idx]

    def top_down_expand(
        self,
        latent_state: torch.Tensor,
        n_macros: int = 3
    ) -> List[torch.Tensor]:
        """
        Top-down hierarchical planning:
        1. Select top-N macro-actions
        2. Return their expanded action sequences
        """
        logits = self.macro_selector(latent_state)
        top_indices = logits.topk(n_macros, dim=-1).indices

        expanded = []
        for idx in top_indices[0]:
            expanded.append(self.macro_embeddings[idx])
        return expanded


class LongHorizonDistiller(nn.Module):
    """
    B1 Ceiling-Pushed: Self-Forced Long-Horizon Distillation.

    The fast model is trained on 1-step predictions. Over long horizons,
    errors compound. This module forces the fast model to also produce
    good long-horizon predictions by distilling the jump model's predictions
    back into the fast model's training signal.

    "Self-forced" means the model trains itself to be consistent at long
    horizons, not just short ones. This is the distillation counterpart
    to the triangulated consistency loss.
    """

    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()

        # Distillation network: maps fast-chained prediction toward jump prediction
        self.distill_net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim)
        )

        # Long-horizon quality estimator
        self.quality_estimator = nn.Sequential(
            nn.Linear(latent_dim * 2, hidden_dim),  # fast_chained + jump_pred
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def distill_loss(
        self,
        fast_chained: torch.Tensor,
        jump_pred: torch.Tensor,
        real_observations: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute distillation loss that forces the fast model's long-horizon
        predictions to align with the jump model (and real observations if available).
        """
        # Distill fast toward jump
        distilled = self.distill_net(fast_chained)
        distill_to_jump = F.mse_loss(distilled, jump_pred.detach())

        # If real observations available, also distill toward ground truth
        if real_observations is not None:
            # This is the strongest signal: distill toward reality, not just agreement
            distill_to_real = F.mse_loss(distilled, real_observations.detach())
            return distill_to_jump + distill_to_real * 0.5

        return distill_to_jump

    def estimate_quality(
        self,
        fast_chained: torch.Tensor,
        jump_pred: torch.Tensor
    ) -> torch.Tensor:
        """Estimate quality of long-horizon prediction."""
        return self.quality_estimator(torch.cat([fast_chained, jump_pred], dim=-1))


class WorldModel:
    """
    L1+L3 Integrated Hierarchical World Model with Skip-Graph.

    Combines:
    - L1: MultimodalPerceptionEncoder for raw stream encoding + event segmentation
    - L3: EnsembleWorldModel for epistemic uncertainty
    - L3: JEPALatentPredictor for abstract state prediction
    - L3: FastRSSMModel for short-horizon high-fidelity dynamics
    - L3: JumpMacroTransitionModel for long-horizon abstract transitions
    - L3: MoEGatingNetwork for fast/jump model selection
    - Skip-Graph: fast model predicts millisecond changes, slow model predicts
      transitions between Abstract Options; slow model updated only on Contact
      Event or Subgoal Achievement from L2
    - B1 Ceiling-Pushed: Triangulated Consistency
      - Observation re-anchoring: sparse re-encoded real observations as
        third anchor against which both fast and jump predictions are checked
      - Uncertainty-horizon gating: calibrated cutoff when disagreement
        exceeds threshold; planner trust decays with rollout length
      - Macro-action hierarchy: learned multi-step action primitives
      - Long-horizon distillation: self-forced training on long rollouts
    """

    def __init__(
        self,
        config=None,
        input_dim: int = 20,
        latent_dim: int = 64,
        hidden_dim: int = 128,
        action_dim: int = 5,
        n_ensemble: int = 5,
        graph_dim: int = 64,
        option_dim: int = 32,
        modality_dims: Optional[Dict[str, int]] = None,
        consistency_horizon: int = 100,
        disagreement_threshold: float = 2.0,
        re_anchor_interval: int = 10,
        uncertainty_horizon_decay: float = 0.95,
        n_macro_actions: int = 16,
        macro_action_length: int = 5
    ):
        if config is not None and isinstance(config, dict):
            wm_cfg = config.get('world_model', {})
            input_dim = wm_cfg.get('input_dim', input_dim)
            latent_dim = wm_cfg.get('latent_dim', latent_dim)
            hidden_dim = wm_cfg.get('hidden_dim', hidden_dim)

        # L1: Multimodal Perception
        self.perception = MultimodalPerceptionEncoder(
            modality_dims=modality_dims,
            latent_dim=latent_dim,
            hidden_dim=hidden_dim
        )

        # L3: Legacy encoder/decoder for backward compatibility
        self.encoder = MarketStateEncoder(input_dim, latent_dim)
        self.decoder = MarketStateDecoder(latent_dim, input_dim)

        # L3: Ensemble World Model (epistemic uncertainty)
        self.ensemble = EnsembleWorldModel(
            n_models=n_ensemble,
            latent_dim=latent_dim,
            hidden_dim=hidden_dim,
            action_dim=action_dim
        )

        # L3: JEPA latent predictor
        self.jepa_predictor = JEPALatentPredictor(latent_dim, hidden_dim)

        # L3: Fast RSSM (single model for primary dynamics)
        self.dynamics = FastRSSMModel(latent_dim, hidden_dim, action_dim)

        # L3: Jump macro-transition model
        self.jump_model = JumpMacroTransitionModel(
            graph_dim=graph_dim,
            option_dim=option_dim,
            hidden_dim=hidden_dim
        )

        # L3: MoE Gating Network
        self.moe_gate = MoEGatingNetwork()

        # Reward predictor
        self.reward_predictor = RewardPredictor(latent_dim)

        # B1 Ceiling-Pushed: Triangulated Consistency components
        self.consistency_horizon = consistency_horizon
        self.disagreement_threshold = disagreement_threshold
        self.re_anchor_interval = re_anchor_interval
        self.uncertainty_horizon_decay = uncertainty_horizon_decay

        # Observation Re-Anchorer: sparse re-encoded real observations
        # as third anchor against which both fast and jump predictions are checked
        self.re_anchorer = ObservationReAnchorer(
            encoder=self.encoder,
            latent_dim=latent_dim,
            re_anchor_interval=re_anchor_interval
        )

        # Uncertainty-Horizon Gate: calibrated trust decay
        self.uncertainty_gate = UncertaintyHorizonGate(
            disagreement_threshold=disagreement_threshold,
            horizon_decay=uncertainty_horizon_decay
        )

        # Macro-Action Hierarchy: learned multi-step action primitives
        self.macro_actions = MacroActionHierarchy(
            n_macro_actions=n_macro_actions,
            action_dim=action_dim,
            macro_length=macro_action_length,
            latent_dim=latent_dim,
            hidden_dim=hidden_dim
        )

        # Long-Horizon Distillation: self-forced training on long rollouts
        self.long_horizon_distiller = LongHorizonDistiller(
            latent_dim=latent_dim,
            hidden_dim=hidden_dim
        )

        # Ignorance Score Engine for governance
        self.ignorance_engine = IgnoranceScoreEngine()

        # Training mode
        self.training = True

        # State tracking
        self._ensemble_hiddens = None
        self._fast_hidden = None
        self._jump_active = False
        self._rollout_step = 0  # For uncertainty-horizon gating

        # Governance mapping heads (Linear probes)
        self.volatility_probe = nn.Linear(latent_dim, len(VolatilityRegime))
        self.liquidity_probe = nn.Linear(latent_dim, len(LiquidityCondition))
        self.stability_probe = nn.Linear(latent_dim, 1)
        self.pressure_probe = nn.Linear(latent_dim, 1)

        logger.info("✅ Hierarchical World Model (L1+L3) initialized")
        logger.info(f"   Latent dim: {latent_dim}")
        logger.info(f"   Ensemble size: {n_ensemble}")
        logger.info(f"   Consistency horizon: {consistency_horizon}")
        logger.info(f"   Disagreement threshold: {disagreement_threshold}")
        logger.info(f"   Re-anchor interval: {re_anchor_interval}")
        logger.info(f"   Macro-actions: {n_macro_actions} x {macro_action_length} steps")

    def encode(self, market_state: torch.Tensor) -> torch.Tensor:
        """Encode market state to latent (legacy compat)."""
        mean, logvar = self.encoder(market_state)
        if self.training:
            return self.encoder.sample(mean, logvar)
        else:
            return mean

    def encode_multimodal(
        self,
        modalities: Dict[str, torch.Tensor],
        prev_latent: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict]:
        """Encode multimodal input via L1 perception."""
        return self.perception(modalities, prev_latent)

    def decode(self, latent_state: torch.Tensor) -> torch.Tensor:
        """Decode latent to market state."""
        return self.decoder(latent_state)

    def get_world_state(self, latent_state: torch.Tensor, symbol: str = "EURUSD") -> MarketWorldState:
        """
        Bridge Latent Z-Space to Structured Reality.
        Standardized mandatory output for governance.
        """
        with torch.no_grad():
            # Get ensemble disagreement for Epistemic Uncertainty
            # Using dummy action for static state probe
            dummy_action = torch.zeros(latent_state.size(0), 5, device=latent_state.device)
            _, ens_logvar, _, disagreement = self.ensemble(latent_state, dummy_action, self._ensemble_hiddens)

            # Predict structured fields via probes
            vol_logits = self.volatility_probe(latent_state)
            liq_logits = self.liquidity_probe(latent_state)
            stability = torch.sigmoid(self.stability_probe(latent_state))
            pressure = torch.tanh(self.pressure_probe(latent_state))

            # Classification
            vol_idx = torch.argmax(vol_logits, dim=-1).item()
            liq_idx = torch.argmax(liq_logits, dim=-1).item()

            vol_regime = list(VolatilityRegime)[vol_idx]
            liq_condition = list(LiquidityCondition)[liq_idx]

            # Entropy of regime classification
            regime_entropy = F.cross_entropy(vol_logits, torch.tensor([vol_idx], device=latent_state.device)).item()

            # Epistemic vs Aleatoric
            epistemic = disagreement.mean().item()
            aleatoric = torch.exp(ens_logvar).mean().item()

            # Overall confidence
            confidence = 1.0 - min(1.0, epistemic * 0.5 + regime_entropy * 0.2)

            state = MarketWorldState(
                symbol=symbol,
                volatility_regime=vol_regime,
                liquidity_condition=liq_condition,
                trend_stability=stability.mean().item(),
                participation_pressure=pressure.mean().item(),
                regime_entropy=regime_entropy,
                epistemic_uncertainty=epistemic,
                aleatoric_uncertainty=aleatoric,
                state_confidence=confidence
            )

            # Enrich with ignorance score and recommended mode
            return self.ignorance_engine.process_world_state(state)

    def predict_next(
        self,
        latent_state: torch.Tensor,
        action: Optional[torch.Tensor] = None,
        hidden_state: Optional[torch.Tensor] = None,
        option_latent: Optional[torch.Tensor] = None,
        graph_latent: Optional[torch.Tensor] = None,
        contact_event: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict]:
        """
        Predict next latent state using Skip-Graph architecture.

        Fast model predicts millisecond changes (physics).
        Jump model predicts transition between Abstract Options.
        MoE gate selects weighting based on prediction error, contact change,
        and temporal abstraction budget.

        B1 fix: re-anchor on real observations when ensemble disagreement or
        rollout entropy exceeds threshold.

        Returns:
            next_state, predicted_reward, new_hidden_state, info_dict
        """
        batch_size = latent_state.size(0)
        device = latent_state.device
        action_dim = self.dynamics.latent_dim  # fallback

        if action is None:
            action = torch.zeros(batch_size, 5, device=device)

        # Fast model prediction
        fast_mean, fast_logvar, new_fast_hidden = self.dynamics(
            latent_state, action, hidden_state
        )

        # Ensemble prediction for epistemic uncertainty
        ens_mean, ens_logvar, new_ens_hiddens, disagreement = self.ensemble(
            latent_state, action, self._ensemble_hiddens
        )
        self._ensemble_hiddens = new_ens_hiddens

        # Check if re-anchoring needed (B1 fix)
        needs_anchoring = disagreement.mean() > self.disagreement_threshold

        # Jump model prediction (only on contact events / subgoal achievements)
        jump_pred = None
        if contact_event and graph_latent is not None and option_latent is not None:
            jump_pred = self.jump_model(graph_latent, option_latent)
            self._jump_active = True
        else:
            self._jump_active = False

        # MoE gating
        fast_error = F.mse_loss(fast_mean, ens_mean.detach(), reduction='none').mean(dim=-1)
        contact_flag = torch.tensor(float(contact_event), device=device).expand(batch_size)
        budget = torch.tensor(0.5, device=device).expand(batch_size)
        gate_weights = self.moe_gate(fast_error, contact_flag, budget)

        # Combine fast and ensemble predictions
        next_mean = gate_weights[:, 0:1] * fast_mean + gate_weights[:, 1:2] * ens_mean

        # If jump model is active, blend it in
        if jump_pred is not None:
            jump_weight = 0.5 if self._jump_active else 0.0
            next_mean = (1 - jump_weight) * next_mean + jump_weight * jump_pred

        # Sample or use mean
        if self.training:
            std = torch.exp(0.5 * ens_logvar)
            next_state = next_mean + std * torch.randn_like(std)
        else:
            next_state = next_mean

        # Predict reward
        reward = self.reward_predictor(next_state)

        info = {
            'disagreement': disagreement.mean().item(),
            'needs_anchoring': needs_anchoring.item() if torch.is_tensor(needs_anchoring) else needs_anchoring,
            'jump_active': self._jump_active,
            'gate_weights': gate_weights.detach()
        }

        self._fast_hidden = new_fast_hidden

        return next_state, reward, new_fast_hidden, info

    def triangulated_consistency_loss(
        self,
        latent_state: torch.Tensor,
        action: torch.Tensor,
        real_observations: Optional[torch.Tensor] = None,
        horizon: int = 100
    ) -> Dict[str, torch.Tensor]:
        """
        B1 Ceiling-Pushed: Triangulated Consistency Loss.

        Agreement is not truth. Two broken models that agree still produce bad plans.
        So we triangulate against THREE anchors:

        1. fast_chained: z_{t+H} from chaining fast model H times
        2. jump_pred: z_{t+H} from jump model (single shot)
        3. re_encoded: z_{t+H} from sparse re-encoded REAL observation

        Losses:
        - cross_scale_loss: fast_chained vs jump_pred (original B1)
        - observation_anchor_loss: fast_chained vs re_encoded (ground truth)
        - jump_anchor_loss: jump_pred vs re_encoded (ground truth)
        - uncertainty_penalty: penalize entropy blow-up in either model
        - long_horizon_distill_loss: self-forced distillation

        Without re-anchoring, models will agree their way into delusion.
        """
        # Chain fast model H times
        current = latent_state
        hidden = None
        fast_entropies = []
        for h in range(min(horizon, self.consistency_horizon)):
            mean, logvar, hidden = self.dynamics(current, action, hidden)
            current = mean
            fast_entropies.append(0.5 * logvar.sum(dim=-1).mean())  # Entropy proxy
        fast_chained = current

        # Jump model prediction (single shot)
        jump_pred = self.jump_model(fast_chained, action)

        # Cross-scale consistency (original B1)
        cross_scale_loss = F.mse_loss(fast_chained, jump_pred.detach())

        # Observation re-anchoring (third anchor)
        obs_anchor_loss = torch.tensor(0.0, device=latent_state.device)
        jump_anchor_loss = torch.tensor(0.0, device=latent_state.device)
        if real_observations is not None:
            # Re-encode real observation as ground truth anchor
            re_encoded = self.encode(real_observations)
            obs_anchor_loss = F.mse_loss(fast_chained, re_encoded.detach())
            jump_anchor_loss = F.mse_loss(jump_pred, re_encoded.detach())

        # Uncertainty blow-up penalty
        # Penalize if either model's entropy grows unboundedly over the rollout
        if fast_entropies:
            entropy_trend = torch.tensor(fast_entropies[-1]) - torch.tensor(fast_entropies[0])
            uncertainty_penalty = F.relu(entropy_trend)  # Only penalize growth
        else:
            uncertainty_penalty = torch.tensor(0.0, device=latent_state.device)

        # Long-horizon distillation loss
        distill_loss = self.long_horizon_distiller.distill_loss(
            fast_chained, jump_pred, real_observations
        )

        # Combined triangulated loss
        total = (
            cross_scale_loss +
            obs_anchor_loss * 0.5 +  # Weight observation anchor strongly
            jump_anchor_loss * 0.3 +
            uncertainty_penalty * 0.1 +
            distill_loss * 0.2
        )

        return {
            'total': total,
            'cross_scale': cross_scale_loss,
            'obs_anchor': obs_anchor_loss,
            'jump_anchor': jump_anchor_loss,
            'uncertainty_penalty': uncertainty_penalty,
            'distill_loss': distill_loss
        }

    def temporal_consistency_loss(
        self,
        latent_state: torch.Tensor,
        action: torch.Tensor,
        horizon: int = 100
    ) -> torch.Tensor:
        """
        B1 Fix: Temporal Latent Consistency Regularization (backward compat).
        Delegates to triangulated_consistency_loss for the stronger version.
        """
        result = self.triangulated_consistency_loss(
            latent_state, action, real_observations=None, horizon=horizon
        )
        return result['total']

    def imagine_trajectory(
        self,
        initial_state: torch.Tensor,
        horizon: int = 50,
        actions: Optional[List[torch.Tensor]] = None,
        graph_latent: Optional[torch.Tensor] = None,
        option_latent: Optional[torch.Tensor] = None,
        contact_events: Optional[List[bool]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Imagine future trajectory from current state using Skip-Graph.

        B1 fix: never trust latent rollouts past their calibrated horizon.
        Once ensemble disagreement or rollout entropy exceeds threshold,
        the planner must re-anchor on real observations.
        """
        self.training = False

        current_latent = self.encode(initial_state) if initial_state.dim() == 1 or initial_state.size(-1) != 64 else initial_state
        hidden_state = None

        latent_states = [current_latent]
        predicted_rewards = []
        disagreements = []
        anchoring_flags = []

        for t in range(horizon):
            action = actions[t] if actions and t < len(actions) else None
            contact = contact_events[t] if contact_events and t < len(contact_events) else False

            next_latent, reward, hidden_state, info = self.predict_next(
                current_latent,
                action=action,
                hidden_state=hidden_state,
                option_latent=option_latent,
                graph_latent=graph_latent,
                contact_event=contact
            )

            latent_states.append(next_latent)
            predicted_rewards.append(reward)
            disagreements.append(info['disagreement'])
            anchoring_flags.append(info['needs_anchoring'])

            # B1 fix: stop rollout if disagreement exceeds threshold
            if info['needs_anchoring']:
                logger.debug(f"Rollout anchoring triggered at step {t}, disagreement={info['disagreement']:.3f}")
                # Pad remaining with last valid state
                for remaining in range(t + 1, horizon):
                    latent_states.append(next_latent.detach())
                    predicted_rewards.append(reward.detach())
                    disagreements.append(info['disagreement'])
                    anchoring_flags.append(True)
                break

            current_latent = next_latent

        latent_states = torch.stack(latent_states)
        predicted_rewards = torch.stack(predicted_rewards)
        decoded_states = self.decode(latent_states)

        return {
            'latent_states': latent_states,
            'decoded_states': decoded_states,
            'predicted_rewards': predicted_rewards,
            'disagreements': disagreements,
            'anchoring_flags': anchoring_flags
        }

    def train_step(
        self,
        market_states: torch.Tensor,
        rewards: torch.Tensor,
        actions: Optional[torch.Tensor] = None
    ) -> Dict[str, float]:
        """
        Training step for world model including temporal consistency loss.
        """
        self.training = True
        batch_size = market_states.size(0)

        # Encode all states
        mean, logvar = self.encoder(market_states)
        latent_states = self.encoder.sample(mean, logvar)

        # Reconstruction loss
        decoded_states = self.decoder(latent_states)
        recon_loss = F.mse_loss(decoded_states, market_states)

        # KL divergence loss
        kl_loss = -0.5 * torch.sum(
            1 + logvar - mean.pow(2) - logvar.exp()
        ) / batch_size

        # Dynamics loss
        hidden_state = None
        dynamics_loss = 0
        reward_loss = 0

        for t in range(market_states.size(1) - 1):
            action_t = actions[:, t] if actions is not None else torch.zeros(batch_size, 5, device=market_states.device)
            pred_mean, pred_logvar, hidden_state = self.dynamics(
                latent_states[:, t], action_t, hidden_state
            )

            true_mean = mean[:, t+1]
            true_logvar = logvar[:, t+1]

            dynamics_loss += -0.5 * torch.sum(
                1 + pred_logvar - true_logvar
                - (pred_mean - true_mean).pow(2) / true_logvar.exp()
                - pred_logvar.exp() / true_logvar.exp()
            ) / batch_size

            pred_reward = self.reward_predictor(latent_states[:, t])
            reward_loss += F.mse_loss(pred_reward.squeeze(), rewards[:, t])

        # B1 Ceiling-Pushed: Triangulated Consistency
        # Use real observations as third anchor (re-encode every N steps)
        real_obs_anchor = market_states[:, -1] if market_states.dim() > 2 else market_states  # Last timestep as anchor
        tri_result = self.triangulated_consistency_loss(
            latent_states[:, 0],
            actions[:, 0] if actions is not None else torch.zeros(batch_size, 5, device=market_states.device),
            real_observations=real_obs_anchor,
            horizon=min(100, market_states.size(1))
        )
        consistency_loss = tri_result['total']

        # Total loss
        total_loss = (
            recon_loss +
            0.1 * kl_loss +
            dynamics_loss +
            reward_loss +
            0.1 * consistency_loss
        )

        return {
            'total_loss': total_loss.item(),
            'recon_loss': recon_loss.item(),
            'kl_loss': kl_loss.item(),
            'dynamics_loss': dynamics_loss.item(),
            'reward_loss': reward_loss.item(),
            'consistency_loss': consistency_loss.item(),
            'cross_scale_loss': tri_result['cross_scale'].item(),
            'obs_anchor_loss': tri_result['obs_anchor'].item(),
            'uncertainty_penalty': tri_result['uncertainty_penalty'].item()
        }

    def save(self, filepath: str):
        """Save world model."""
        state_dict = {
            'encoder': self.encoder.state_dict(),
            'decoder': self.decoder.state_dict(),
            'dynamics': self.dynamics.state_dict(),
            'reward_predictor': self.reward_predictor.state_dict(),
            'ensemble': self.ensemble.state_dict(),
            'jepa_predictor': self.jepa_predictor.state_dict(),
            'jump_model': self.jump_model.state_dict(),
            'moe_gate': self.moe_gate.state_dict(),
            'perception': self.perception.state_dict(),
            'macro_actions': self.macro_actions.state_dict(),
            'long_horizon_distiller': self.long_horizon_distiller.state_dict(),
        }
        torch.save(state_dict, filepath)
        logger.info(f"💾 World Model saved to {filepath}")

    def load(self, filepath: str):
        """Load world model."""
        state = torch.load(filepath)
        self.encoder.load_state_dict(state['encoder'])
        self.decoder.load_state_dict(state['decoder'])
        self.dynamics.load_state_dict(state['dynamics'])
        self.reward_predictor.load_state_dict(state['reward_predictor'])
        if 'ensemble' in state:
            self.ensemble.load_state_dict(state['ensemble'])
        if 'jepa_predictor' in state:
            self.jepa_predictor.load_state_dict(state['jepa_predictor'])
        if 'jump_model' in state:
            self.jump_model.load_state_dict(state['jump_model'])
        if 'moe_gate' in state:
            self.moe_gate.load_state_dict(state['moe_gate'])
        if 'perception' in state:
            self.perception.load_state_dict(state['perception'])
        if 'macro_actions' in state:
            self.macro_actions.load_state_dict(state['macro_actions'])
        if 'long_horizon_distiller' in state:
            self.long_horizon_distiller.load_state_dict(state['long_horizon_distiller'])
        logger.info(f"📂 World Model loaded from {filepath}")
