import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple

class UncertaintyEngine(nn.Module):
    """
    Every prediction should output:
    confidence, calibration, ignorance, OOD probability, novelty score.
    """
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.latent_dim = latent_dim

        # OOD and Novelty detection via density estimation/reconstruction
        self.density_estimator = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        # Ignorance score (Epistemic) predictor
        self.ignorance_predictor = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Calibration network
        self.calibration_net = nn.Sequential(
            nn.Linear(latent_dim + 1, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, latent: torch.Tensor, ensemble_disagreement: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Calculates unified uncertainty metrics.
        """
        # OOD Probability (inverse of density)
        density_score = self.density_estimator(latent)
        ood_prob = torch.sigmoid(-density_score)

        # Novelty score
        novelty = torch.clamp(ood_prob * 1.5, 0, 1)

        # Ignorance score
        ignorance = self.ignorance_predictor(latent)

        # Confidence
        confidence = 1.0 - (ignorance * 0.6 + ood_prob * 0.4)

        # Calibration - ensure disagreement has correct shape
        dis_input = ensemble_disagreement
        if dis_input.dim() == 1:
            dis_input = dis_input.unsqueeze(-1)
        elif dis_input.dim() == 0:
            dis_input = dis_input.view(1, 1).expand(latent.size(0), 1)

        calibration = self.calibration_net(torch.cat([latent, dis_input], dim=-1))

        return {
            "confidence": confidence.squeeze(-1),
            "calibration": calibration.squeeze(-1),
            "ignorance": ignorance.squeeze(-1),
            "ood_probability": ood_prob.squeeze(-1),
            "novelty_score": novelty.squeeze(-1)
        }
