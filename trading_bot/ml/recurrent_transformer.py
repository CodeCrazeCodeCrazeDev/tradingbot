"""
Recurrent Depth Transformer Base Class

Implements Universal Transformer / Recurrent Depth architecture:
- Shared Transformer weights across depth
- Optional Adaptive Computation Time (ACT) halting
- Fixed and variable recurrent depth
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class ACTController(nn.Module):
    """
    Adaptive Computation Time (ACT) controller.

    Predicts halting probability at each step.
    """
    def __init__(self, d_model: int, threshold: float = 0.99):
        super().__init__()
        self.halting_layer = nn.Linear(d_model, 1)
        self.threshold = threshold

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Predict halting probability."""
        return torch.sigmoid(self.halting_layer(state))

class RecurrentDepthTransformerBase(nn.Module):
    """
    Base class for Recurrent Depth Transformers (Universal Transformers).

    Architecture:
    Input -> Embedding -> [Shared Block]^depth -> Output
    """

    def __init__(
        self,
        d_model: int,
        nhead: int,
        dim_feedforward: int,
        dropout: float = 0.1,
        recurrent_depth: int = 6,
        max_depth: int = 12,
        use_act: bool = False,
        act_threshold: float = 0.99
    ):
        super().__init__()
        self.d_model = d_model
        self.recurrent_depth = recurrent_depth
        self.max_depth = max_depth
        self.use_act = use_act

        # Shared Transformer Block
        self.shared_block = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )

        # ACT Halting Controller
        if use_act:
            self.act_controller = ACTController(d_model, act_threshold)

        # Attention Tracking
        self.last_attention_weights = None
        self.depth_stats = []

    def _recurrent_forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        padding_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Apply the shared transformer block recurrently.
        """
        batch_size, seq_len, _ = x.shape

        # ACT state initialization
        if self.use_act:
            halting_probabilities = torch.zeros(batch_size, seq_len, 1).to(x.device)
            remainders = torch.ones(batch_size, seq_len, 1).to(x.device)
            accumulated_state = torch.zeros_like(x)
            step_counts = torch.zeros(batch_size, seq_len, 1).to(x.device)
            still_running = torch.ones(batch_size, seq_len, 1, dtype=torch.bool).to(x.device)

        current_state = x
        depth = 0
        max_steps = self.max_depth if self.use_act else self.recurrent_depth

        while depth < max_steps:
            # Apply shared block
            next_state = self.shared_block(current_state, src_mask=mask, src_key_padding_mask=padding_mask)

            if self.use_act:
                # Calculate halting prob
                p = self.act_controller(next_state)

                # Mask out already halted elements
                p = p * still_running.float()

                # Check if this step would push accumulated prob over 1.0
                mask_halting = (halting_probabilities + p >= 1.0)

                # Probability to add in this step
                p_to_add = torch.where(mask_halting, remainders, p)

                # Update accumulated state
                accumulated_state = accumulated_state + (p_to_add * next_state)

                # Update probabilities and remainders
                halting_probabilities = halting_probabilities + p_to_add
                remainders = remainders - p_to_add
                step_counts = step_counts + still_running.float()

                # Update which elements are still running
                still_running = (halting_probabilities < self.act_controller.threshold)

                if not still_running.any():
                    depth += 1
                    break
            else:
                current_state = next_state

            depth += 1

        final_state = accumulated_state if self.use_act else current_state

        stats = {
            "actual_depth": depth,
            "mean_steps": step_counts.mean().item() if self.use_act else depth
        }

        return final_state, stats

    def forward(self, x, mask=None, padding_mask=None):
        """Standard forward pass."""
        return self._recurrent_forward(x, mask, padding_mask)

class RecurrentDepthTransformerEncoder(RecurrentDepthTransformerBase):
    """Concrete implementation of a Recurrent Depth Encoder."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add positional encoding or input projection if needed in subclasses

class RecurrentDepthTransformerDecoder(RecurrentDepthTransformerBase):
    """Concrete implementation of a Recurrent Depth Decoder."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared Decoder Block
        self.shared_block = nn.TransformerDecoderLayer(
            d_model=self.d_model,
            nhead=kwargs.get('nhead', 8),
            dim_feedforward=kwargs.get('dim_feedforward', 2048),
            dropout=kwargs.get('dropout', 0.1),
            batch_first=True
        )

    def forward(self, tgt, memory, tgt_mask=None, memory_mask=None, tgt_key_padding_mask=None, memory_key_padding_mask=None):
        """Recurrent decoder forward pass."""
        # Note: RecurrentDepthTransformerBase's _recurrent_forward is designed for Encoder.
        # Decoder needs cross-attention with memory.

        current_state = tgt
        depth = 0
        while depth < self.recurrent_depth:
            current_state = self.shared_block(
                current_state,
                memory,
                tgt_mask=tgt_mask,
                memory_mask=memory_mask,
                tgt_key_padding_mask=tgt_key_padding_mask,
                memory_key_padding_mask=memory_key_padding_mask
            )
            depth += 1
        return current_state, {"actual_depth": depth}
