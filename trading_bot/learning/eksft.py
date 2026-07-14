"""
EKSFT: Entropy-KL Selective Fine-Tuning - UCA V5 (July 2026)

Implements selective token masking for distribution-preserving fine-tuning.
Prevents catastrophic forgetting and the 'Delusion Loop' during online adaptation.
"""

import logging
import torch
import torch.nn.functional as F
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EKSFTTrainer:
    """
    Selective Fine-tuning based on Entropy and KL Divergence.
    """
    def __init__(self, model: Any, ref_model: Any, entropy_tau: float = 2.0, kl_tau: float = 0.5):
        self.model = model
        self.ref_model = ref_model # Frozen pre-trained model
        self.entropy_tau = entropy_tau
        self.kl_tau = kl_tau

    def compute_selective_loss(self, input_ids: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Calculates loss only on tokens that pass the Entropy-KL filter.
        """
        # 1. Get logits from both models
        with torch.no_grad():
            ref_logits = self.ref_model(input_ids).logits

        current_logits = self.model(input_ids).logits

        # 2. Calculate Entropy of current model predictions
        probs = F.softmax(current_logits, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)

        # 3. Calculate KL Divergence between reference and current
        kl_div = F.kl_div(
            F.log_softmax(current_logits, dim=-1),
            F.softmax(ref_logits, dim=-1),
            reduction='none'
        ).sum(-1)

        # 4. Generate Mask
        # Mask tokens where entropy > entropy_tau OR KL > kl_tau
        # These are tokens the model is too uncertain about or has drifted too far from the base.
        mask = (entropy <= self.entropy_tau) & (kl_div <= self.kl_tau)

        # 5. Compute masked Cross Entropy
        loss = F.cross_entropy(current_logits.view(-1, current_logits.size(-1)), labels.view(-1), reduction='none')
        masked_loss = loss * mask.view(-1).float()

        return masked_loss.sum() / (mask.sum() + 1e-10)

def apply_eksft_masking(logits: torch.Tensor, ref_logits: torch.Tensor, entropy_tau: float, kl_tau: float) -> torch.Tensor:
    """
    Utility function for runtime token filtering.
    """
    probs = F.softmax(logits, dim=-1)
    entropy = -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)

    kl_div = F.kl_div(
        F.log_softmax(logits, dim=-1),
        F.softmax(ref_logits, dim=-1),
        reduction='none'
    ).sum(-1)

    mask = (entropy <= entropy_tau) & (kl_div <= kl_tau)
    return mask
