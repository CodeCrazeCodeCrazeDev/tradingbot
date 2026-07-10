"""
EKSFT (Entropy-KL Selective Fine-Tuning) Logic.
Implements selective token masking for safe strategy internalization.
"""

import torch
import torch.nn.functional as F
import numpy as np
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

class EKSFTMasker:
    """
    Implements Entropy-KL Selective Fine-Tuning (arXiv:2605.29303).
    """
    def __init__(self, tau_h: float = 2.0, tau_kl: float = 0.5):
        self.tau_h = tau_h
        self.tau_kl = tau_kl

    def calculate_masks(self, logits: torch.Tensor, ref_logits: torch.Tensor) -> torch.Tensor:
        """
        Calculates a binary mask for each token in the sequence.
        1 = Keep (Exploration/Task-relevant)
        0 = Mask (Safety Anchor or High Noise)
        """
        # 1. Entropy Masking (H > tau_h)
        probs = F.softmax(logits, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-9), dim=-1)

        # 2. KL Divergence Masking (KL > tau_kl)
        ref_probs = F.softmax(ref_logits, dim=-1)
        kl_div = F.kl_div(torch.log(probs + 1e-9), ref_probs, reduction='none').sum(dim=-1)

        # Token is an "Anchor" if it has low entropy and low KL from reference
        # Token is "Noise" if entropy is extremely high
        # Token is "Exploration" if it has moderate entropy and KL

        # EKSFT Rule: Mask if Entropy is too high (noise) OR if it's an Anchor (to preserve distribution)
        # We want to train on tokens that represent the NEW knowledge/strategy
        is_anchor = (entropy < 1.0) & (kl_div < 0.2)
        is_noise = entropy > self.tau_h

        mask = torch.ones_like(entropy)
        mask[is_anchor] = 0
        mask[is_noise] = 0

        logger.debug(f"EKSFT: Masked {torch.sum(mask == 0).item()} tokens out of {mask.numel()}")
        return mask

    def apply_selective_loss(self, loss: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Applies the mask to the loss tensor."""
        return (loss * mask).sum() / (mask.sum() + 1e-9)
