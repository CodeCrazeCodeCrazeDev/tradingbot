"""
FWM Agent-Based Microstructure Simulation
=========================================

Specialized modules for modeling Dealers, HFTs, and CTAs.
These modules represent the "Reaction Functions" that generate emergent
market behavior within the Digital Twin.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple


class DealerHedgingLayer(nn.Module):
    """
    Models Options Dealer behavior: Gamma, Vanna, and Charm hedging.
    Dealer hedging creates "gravity" or "pinning" levels in the market.
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        # Learned mapping from latent state to Dealer Net Gamma
        self.gamma_surface = nn.Linear(latent_dim, 1)
        self.vanna_exposure = nn.Linear(latent_dim, 1)

    def forward(self, z: torch.Tensor) -> Dict[str, torch.Tensor]:
        gamma = self.gamma_surface(z)
        vanna = self.vanna_exposure(z)

        # Hedging pressure: Dealers sell into strength in Long Gamma,
        # but buy into strength in Short Gamma (reflexivity).
        pressure = -torch.sign(gamma) * 0.1 # Simplified reaction
        return {
            'net_gamma': gamma,
            'hedging_pressure': pressure,
            'stability_impact': torch.sigmoid(gamma)
        }


class HFTToxicityModel(nn.Module):
    """
    Models High-Frequency Trading flow toxicity and adverse selection.
    Toxic flow (informed HFT) precedes liquidity voids.
    """
    def __init__(self, micro_dim: int = 128):
        super().__init__()
        self.toxicity_head = nn.Sequential(
            nn.Linear(micro_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, z_micro: torch.Tensor) -> torch.Tensor:
        # VPIN-style toxicity score (Volume-synchronized Probability of Informed Trading)
        return self.toxicity_head(z_micro)


class MomentumParticipant(nn.Module):
    """
    Models CTAs and Trend-Followers.
    Their reaction function is positively correlated to historical momentum.
    """
    def __init__(self, latent_dim: int = 256):
        super().__init__()
        self.momentum_sensitivity = nn.Parameter(torch.tensor([0.5]))

    def forward(self, z: torch.Tensor, price_momentum: torch.Tensor) -> torch.Tensor:
        # Buying on breakouts, selling on breakdowns
        return self.momentum_sensitivity * price_momentum


class MicrostructureSimulator(nn.Module):
    """
    Synthesizes all participant reaction functions.
    """
    def __init__(self):
        super().__init__()
        self.dealers = DealerHedgingLayer()
        self.hft = HFTToxicityModel()
        self.momentum = MomentumParticipant()

    def compute_net_flow(self, z: torch.Tensor, z_micro: torch.Tensor) -> torch.Tensor:
        """
        Synthesize the emergent flow from all agents.
        """
        dealer_out = self.dealers(z)
        toxicity = self.hft(z_micro)

        # Emergent behavior: If toxicity is high and dealers are short Gamma,
        # liquidity voids are likely.
        emergent_impact = toxicity * (1.0 - dealer_out['net_gamma'])

        return dealer_out['hedging_pressure'] + emergent_impact
