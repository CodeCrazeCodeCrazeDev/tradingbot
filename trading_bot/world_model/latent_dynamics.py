"""
Phase 4: World Models - Latent Dynamics
DreamerV3-style world model for market simulation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


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


class WorldModel:
    """
    Complete world model for market simulation.
    Combines all components for imagination-based planning.
    """
    
    def __init__(
        self,
        config = None,
        input_dim: int = 20,
        latent_dim: int = 32,
        hidden_dim: int = 64
    ):
        # Handle config dict or individual parameters
        if config is not None and isinstance(config, dict):
            input_dim = config.get('world_model', {}).get('input_dim', input_dim)
            latent_dim = config.get('world_model', {}).get('latent_dim', latent_dim)
            hidden_dim = config.get('world_model', {}).get('hidden_dim', hidden_dim)
        
        self.encoder = MarketStateEncoder(input_dim, latent_dim)
        self.decoder = MarketStateDecoder(latent_dim, input_dim)
        self.dynamics = LatentDynamicsModel(latent_dim, hidden_dim)
        self.reward_predictor = RewardPredictor(latent_dim)
        
        # Training mode
        self.training = True
        
        logger.info("✅ World Model initialized")
        logger.info(f"   Input dim: {input_dim}")
        logger.info(f"   Latent dim: {latent_dim}")
        logger.info(f"   Hidden dim: {hidden_dim}")
    
    def encode(self, market_state: torch.Tensor) -> torch.Tensor:
        """Encode market state to latent."""
        mean, logvar = self.encoder(market_state)
        if self.training:
            return self.encoder.sample(mean, logvar)
        else:
            return mean
    
    def decode(self, latent_state: torch.Tensor) -> torch.Tensor:
        """Decode latent to market state."""
        return self.decoder(latent_state)
    
    def predict_next(
        self,
        latent_state: torch.Tensor,
        hidden_state: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict next latent state and reward.
        
        Returns:
            next_state, predicted_reward
        """
        # Predict next state distribution
        mean, logvar, new_hidden = self.dynamics(latent_state, hidden_state)
        
        # Sample next state
        if self.training:
            next_state = self.dynamics.sample_prediction(mean, logvar)
        else:
            next_state = mean
        
        # Predict reward
        reward = self.reward_predictor(next_state)
        
        return next_state, reward, new_hidden
    
    def imagine_trajectory(
        self,
        initial_state: torch.Tensor,
        horizon: int = 50
    ) -> Dict[str, torch.Tensor]:
        """
        Imagine future trajectory from current state.
        
        Args:
            initial_state: Current market state
            horizon: Number of steps to predict
        
        Returns:
            Dictionary with predicted states and rewards
        """
        self.training = False  # Use mean predictions
        
        # Initialize
        current_latent = self.encode(initial_state)
        hidden_state = None
        
        # Store predictions
        latent_states = [current_latent]
        predicted_rewards = []
        
        # Generate trajectory
        for _ in range(horizon):
            # Predict next state and reward
            next_latent, reward, hidden_state = self.predict_next(
                current_latent,
                hidden_state
            )
            
            # Store predictions
            latent_states.append(next_latent)
            predicted_rewards.append(reward)
            
            # Update current state
            current_latent = next_latent
        
        # Stack predictions
        latent_states = torch.stack(latent_states)
        predicted_rewards = torch.stack(predicted_rewards)
        
        # Decode trajectory
        decoded_states = self.decode(latent_states)
        
        return {
            'latent_states': latent_states,
            'decoded_states': decoded_states,
            'predicted_rewards': predicted_rewards
        }
    
    def train_step(
        self,
        market_states: torch.Tensor,
        rewards: torch.Tensor
    ) -> Dict[str, float]:
        """
        Training step for world model.
        
        Args:
            market_states: Sequence of market states [batch, time, features]
            rewards: Actual rewards [batch, time]
        
        Returns:
            Dictionary of losses
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
            # Predict next state
            pred_mean, pred_logvar, hidden_state = self.dynamics(
                latent_states[:, t],
                hidden_state
            )
            
            # True next state
            true_mean = mean[:, t+1]
            true_logvar = logvar[:, t+1]
            
            # KL divergence between predicted and true distribution
            dynamics_loss += -0.5 * torch.sum(
                1 + pred_logvar - true_logvar
                - (pred_mean - true_mean).pow(2) / true_logvar.exp()
                - pred_logvar.exp() / true_logvar.exp()
            ) / batch_size
            
            # Reward prediction loss
            pred_reward = self.reward_predictor(latent_states[:, t])
            reward_loss += F.mse_loss(pred_reward.squeeze(), rewards[:, t])
        
        # Total loss
        total_loss = (
            recon_loss +
            0.1 * kl_loss +  # Beta-VAE style weighting
            dynamics_loss +
            reward_loss
        )
        
        return {
            'total_loss': total_loss.item(),
            'recon_loss': recon_loss.item(),
            'kl_loss': kl_loss.item(),
            'dynamics_loss': dynamics_loss.item(),
            'reward_loss': reward_loss.item()
        }
    
    def save(self, filepath: str):
        """Save world model."""
        torch.save({
            'encoder': self.encoder.state_dict(),
            'decoder': self.decoder.state_dict(),
            'dynamics': self.dynamics.state_dict(),
            'reward_predictor': self.reward_predictor.state_dict()
        }, filepath)
        logger.info(f"💾 World Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load world model."""
        state = torch.load(filepath)
        self.encoder.load_state_dict(state['encoder'])
        self.decoder.load_state_dict(state['decoder'])
        self.dynamics.load_state_dict(state['dynamics'])
        self.reward_predictor.load_state_dict(state['reward_predictor'])
        logger.info(f"📂 World Model loaded from {filepath}")
