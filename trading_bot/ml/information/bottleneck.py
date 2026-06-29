"""
Information Bottleneck (IB) Implementation
Extracts relevant information while compressing noise.
"""

import torch
import torch.nn as nn
from typing import Tuple

class InformationBottleneck(nn.Module):
    """
    Compresses input X to latent Z such that I(Z, Y) is maximized
    while I(X, Z) is minimized (Tishby et al.).
    """
    def __init__(self, input_dim: int, latent_dim: int, beta: float = 0.01):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim * 2) # Mean and logvar
        )
        self.beta = beta

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        params = self.encoder(x)
        return torch.chunk(params, 2, dim=-1)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def kl_divergence(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Rate term: I(X, Z) proxy."""
        return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=-1).mean()

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        kl = self.kl_divergence(mu, logvar)
        return z, kl
