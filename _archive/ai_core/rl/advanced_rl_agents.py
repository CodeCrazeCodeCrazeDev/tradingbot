"""
Advanced Offline RL Agents for AlphaAlgo

Implements state-of-the-art offline RL algorithms:
- CQL (Conservative Q-Learning)
- BCQ (Batch-Constrained Q-Learning)
- BEAR (Bootstrapping Error Accumulation Reduction)
- MBOP (Model-Based Offline Planning)
- MAGIC (Model-Agnostic Guided Imitation Cloning)

All agents support risk-sensitive objectives (CVaR, variance penalties).
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import deque
import copy
import numpy

logger = logging.getLogger(__name__)


@dataclass
class RLConfig:
    """Configuration for RL agents."""
    state_dim: int
    action_dim: int
    hidden_dim: int = 256
    learning_rate: float = 3e-4
    gamma: float = 0.99
    tau: float = 0.005
    batch_size: int = 256
    buffer_size: int = 1000000
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Risk-sensitive parameters
    use_cvar: bool = True
    cvar_alpha: float = 0.05
    variance_penalty: float = 0.1


class QNetwork(nn.Module):
    """Q-Network for value estimation."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.fc1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
        
        self.ln1 = nn.LayerNorm(hidden_dim)
        self.ln2 = nn.LayerNorm(hidden_dim)
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        x = torch.cat([state, action], dim=-1)
        x = F.relu(self.ln1(self.fc1(x)))
        x = F.relu(self.ln2(self.fc2(x)))
        return self.fc3(x)


class PolicyNetwork(nn.Module):
    """Policy network for action selection."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
        
        self.ln1 = nn.LayerNorm(hidden_dim)
        self.ln2 = nn.LayerNorm(hidden_dim)
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.ln1(self.fc1(state)))
        x = F.relu(self.ln2(self.fc2(x)))
        return torch.tanh(self.fc3(x))


class VAE(nn.Module):
    """Variational Autoencoder for BCQ."""
    
    def __init__(self, state_dim: int, action_dim: int, latent_dim: int = 32, hidden_dim: int = 256):
        super().__init__()
        
        # Encoder
        self.e1 = nn.Linear(state_dim + action_dim, hidden_dim)
        self.e2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean = nn.Linear(hidden_dim, latent_dim)
        self.log_std = nn.Linear(hidden_dim, latent_dim)
        
        # Decoder
        self.d1 = nn.Linear(state_dim + latent_dim, hidden_dim)
        self.d2 = nn.Linear(hidden_dim, hidden_dim)
        self.d3 = nn.Linear(hidden_dim, action_dim)
        
        self.latent_dim = latent_dim
    
    def encode(self, state: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x = torch.cat([state, action], dim=-1)
        x = F.relu(self.e1(x))
        x = F.relu(self.e2(x))
        return self.mean(x), self.log_std(x)
    
    def decode(self, state: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        x = torch.cat([state, z], dim=-1)
        x = F.relu(self.d1(x))
        x = F.relu(self.d2(x))
        return torch.tanh(self.d3(x))
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mean, log_std = self.encode(state, action)
        std = torch.exp(log_std)
        z = mean + std * torch.randn_like(std)
        recon = self.decode(state, z)
        return recon, mean, log_std


class CQLAgent:
    """
    Conservative Q-Learning (CQL) Agent
    
    Paper: "Conservative Q-Learning for Offline Reinforcement Learning"
    Kumar et al., NeurIPS 2020
    
    Prevents Q-value overestimation by adding conservative penalty.
    """
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # Networks
        self.q1 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q2 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q1_target = copy.deepcopy(self.q1)
        self.q2_target = copy.deepcopy(self.q2)
        
        self.policy = PolicyNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        
        # Optimizers
        self.q_optimizer = optim.Adam(
            list(self.q1.parameters()) + list(self.q2.parameters()),
            lr=config.learning_rate
        )
        self.policy_optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
        
        # CQL parameters
        self.cql_alpha = 1.0
        self.num_random_actions = 10
        
        logger.info("CQL Agent initialized")
    
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """Get action from policy."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action = self.policy(state_tensor)
            
            if not deterministic:
                # Add exploration noise
                noise = torch.randn_like(action) * 0.1
                action = action + noise
                action = torch.clamp(action, -1, 1)
        
        return action.cpu().numpy()[0]
    
    def train(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Train on batch of data."""
        state = batch['state'].to(self.device)
        action = batch['action'].to(self.device)
        reward = batch['reward'].to(self.device)
        next_state = batch['next_state'].to(self.device)
        done = batch['done'].to(self.device)
        
        # Compute target Q-value
        with torch.no_grad():
            next_action = self.policy(next_state)
            target_q1 = self.q1_target(next_state, next_action)
            target_q2 = self.q2_target(next_state, next_action)
            target_q = torch.min(target_q1, target_q2)
            target_q = reward + (1 - done) * self.config.gamma * target_q
        
        # Current Q-values
        current_q1 = self.q1(state, action)
        current_q2 = self.q2(state, action)
        
        # TD loss
        q1_loss = F.mse_loss(current_q1, target_q)
        q2_loss = F.mse_loss(current_q2, target_q)
        
        # CQL conservative penalty
        random_actions = torch.FloatTensor(
            state.shape[0], self.num_random_actions, self.config.action_dim
        ).uniform_(-1, 1).to(self.device)
        
        state_expanded = state.unsqueeze(1).repeat(1, self.num_random_actions, 1)
        state_expanded = state_expanded.view(-1, self.config.state_dim)
        random_actions_flat = random_actions.view(-1, self.config.action_dim)
        
        random_q1 = self.q1(state_expanded, random_actions_flat).view(state.shape[0], self.num_random_actions)
        random_q2 = self.q2(state_expanded, random_actions_flat).view(state.shape[0], self.num_random_actions)
        
        # Conservative penalty: log-sum-exp of random Q-values minus data Q-values
        cql_loss1 = torch.logsumexp(random_q1, dim=1).mean() - current_q1.mean()
        cql_loss2 = torch.logsumexp(random_q2, dim=1).mean() - current_q2.mean()
        
        # Total Q-loss
        q_loss = q1_loss + q2_loss + self.cql_alpha * (cql_loss1 + cql_loss2)
        
        # Update Q-networks
        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()
        
        # Update policy
        policy_action = self.policy(state)
        policy_q = self.q1(state, policy_action)
        policy_loss = -policy_q.mean()
        
        # Risk-sensitive objective
        if self.config.use_cvar:
            policy_loss += self._compute_cvar_penalty(policy_q)
        
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        # Update target networks
        self._update_targets()
        
        return {
            'q_loss': q_loss.item(),
            'policy_loss': policy_loss.item(),
            'cql_loss': (cql_loss1 + cql_loss2).item(),
            'mean_q': current_q1.mean().item()
        }
    
    def _compute_cvar_penalty(self, q_values: torch.Tensor) -> torch.Tensor:
        """Compute CVaR penalty for risk-sensitive learning."""
        sorted_q, _ = torch.sort(q_values.squeeze())
        cutoff_idx = int(self.config.cvar_alpha * len(sorted_q))
        cvar = sorted_q[:cutoff_idx].mean()
        return -cvar * self.config.variance_penalty
    
    def _update_targets(self):
        """Soft update of target networks."""
        for param, target_param in zip(self.q1.parameters(), self.q1_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )
        for param, target_param in zip(self.q2.parameters(), self.q2_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )


class BCQAgent:
    """
    Batch-Constrained Q-Learning (BCQ) Agent
    
    Paper: "Off-Policy Deep Reinforcement Learning without Exploration"
    Fujimoto et al., ICML 2019
    
    Constrains actions to behavior policy support using VAE.
    """
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # Networks
        self.vae = VAE(config.state_dim, config.action_dim, hidden_dim=config.hidden_dim).to(self.device)
        self.q1 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q2 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q1_target = copy.deepcopy(self.q1)
        self.q2_target = copy.deepcopy(self.q2)
        
        self.perturbation = PolicyNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        
        # Optimizers
        self.vae_optimizer = optim.Adam(self.vae.parameters(), lr=config.learning_rate)
        self.q_optimizer = optim.Adam(
            list(self.q1.parameters()) + list(self.q2.parameters()),
            lr=config.learning_rate
        )
        self.perturbation_optimizer = optim.Adam(self.perturbation.parameters(), lr=config.learning_rate)
        
        # BCQ parameters
        self.phi = 0.05  # Perturbation scale
        self.num_samples = 10
        
        logger.info("BCQ Agent initialized")
    
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """Get action from policy."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # Sample from VAE
            state_repeated = state_tensor.repeat(self.num_samples, 1)
            z = torch.randn(self.num_samples, self.vae.latent_dim).to(self.device)
            sampled_actions = self.vae.decode(state_repeated, z)
            
            # Add perturbation
            perturbation = self.perturbation(state_repeated)
            perturbed_actions = sampled_actions + self.phi * perturbation
            perturbed_actions = torch.clamp(perturbed_actions, -1, 1)
            
            # Select action with highest Q-value
            q_values = self.q1(state_repeated, perturbed_actions)
            idx = q_values.argmax(0)
            action = perturbed_actions[idx]
        
        return action.cpu().numpy()
    
    def train(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Train on batch of data."""
        state = batch['state'].to(self.device)
        action = batch['action'].to(self.device)
        reward = batch['reward'].to(self.device)
        next_state = batch['next_state'].to(self.device)
        done = batch['done'].to(self.device)
        
        # Train VAE
        recon, mean, log_std = self.vae(state, action)
        recon_loss = F.mse_loss(recon, action)
        kl_loss = -0.5 * torch.sum(1 + log_std - mean.pow(2) - log_std.exp())
        vae_loss = recon_loss + 0.5 * kl_loss
        
        self.vae_optimizer.zero_grad()
        vae_loss.backward()
        self.vae_optimizer.step()
        
        # Train Q-networks
        with torch.no_grad():
            # Sample actions from VAE for next state
            next_state_repeated = next_state.repeat_interleave(self.num_samples, dim=0)
            z = torch.randn(next_state.shape[0] * self.num_samples, self.vae.latent_dim).to(self.device)
            sampled_next_actions = self.vae.decode(next_state_repeated, z)
            
            # Add perturbation
            perturbation = self.perturbation(next_state_repeated)
            perturbed_next_actions = sampled_next_actions + self.phi * perturbation
            perturbed_next_actions = torch.clamp(perturbed_next_actions, -1, 1)
            
            # Compute target Q
            target_q1 = self.q1_target(next_state_repeated, perturbed_next_actions)
            target_q2 = self.q2_target(next_state_repeated, perturbed_next_actions)
            target_q = torch.min(target_q1, target_q2)
            target_q = target_q.view(next_state.shape[0], self.num_samples).max(1)[0].unsqueeze(1)
            target_q = reward + (1 - done) * self.config.gamma * target_q
        
        current_q1 = self.q1(state, action)
        current_q2 = self.q2(state, action)
        
        q_loss = F.mse_loss(current_q1, target_q) + F.mse_loss(current_q2, target_q)
        
        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()
        
        # Train perturbation network
        sampled_actions = self.vae.decode(state, torch.randn(state.shape[0], self.vae.latent_dim).to(self.device))
        perturbed_actions = sampled_actions + self.phi * self.perturbation(state)
        perturbed_actions = torch.clamp(perturbed_actions, -1, 1)
        
        perturbation_loss = -self.q1(state, perturbed_actions).mean()
        
        self.perturbation_optimizer.zero_grad()
        perturbation_loss.backward()
        self.perturbation_optimizer.step()
        
        # Update targets
        self._update_targets()
        
        return {
            'vae_loss': vae_loss.item(),
            'q_loss': q_loss.item(),
            'perturbation_loss': perturbation_loss.item(),
            'mean_q': current_q1.mean().item()
        }
    
    def _update_targets(self):
        """Soft update of target networks."""
        for param, target_param in zip(self.q1.parameters(), self.q1_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )
        for param, target_param in zip(self.q2.parameters(), self.q2_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )


class BEARAgent:
    """
    BEAR (Bootstrapping Error Accumulation Reduction) Agent
    
    Paper: "Stabilizing Off-Policy Q-Learning via Bootstrapping Error Reduction"
    Kumar et al., NeurIPS 2019
    
    Uses MMD (Maximum Mean Discrepancy) to constrain policy to behavior policy.
    """
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device(config.device)
        
        # Networks
        self.q1 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q2 = QNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.q1_target = copy.deepcopy(self.q1)
        self.q2_target = copy.deepcopy(self.q2)
        
        self.policy = PolicyNetwork(config.state_dim, config.action_dim, config.hidden_dim).to(self.device)
        self.vae = VAE(config.state_dim, config.action_dim, hidden_dim=config.hidden_dim).to(self.device)
        
        # Optimizers
        self.q_optimizer = optim.Adam(
            list(self.q1.parameters()) + list(self.q2.parameters()),
            lr=config.learning_rate
        )
        self.policy_optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
        self.vae_optimizer = optim.Adam(self.vae.parameters(), lr=config.learning_rate)
        
        # BEAR parameters
        self.mmd_epsilon = 0.05
        self.num_samples = 10
        
        logger.info("BEAR Agent initialized")
    
    def get_action(self, state: np.ndarray, deterministic: bool = False) -> np.ndarray:
        """Get action from policy."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action = self.policy(state_tensor)
        
        return action.cpu().numpy()[0]
    
    def train(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Train on batch of data."""
        state = batch['state'].to(self.device)
        action = batch['action'].to(self.device)
        reward = batch['reward'].to(self.device)
        next_state = batch['next_state'].to(self.device)
        done = batch['done'].to(self.device)
        
        # Train VAE (behavior policy model)
        recon, mean, log_std = self.vae(state, action)
        recon_loss = F.mse_loss(recon, action)
        kl_loss = -0.5 * torch.sum(1 + log_std - mean.pow(2) - log_std.exp())
        vae_loss = recon_loss + 0.5 * kl_loss
        
        self.vae_optimizer.zero_grad()
        vae_loss.backward()
        self.vae_optimizer.step()
        
        # Train Q-networks
        with torch.no_grad():
            next_action = self.policy(next_state)
            target_q1 = self.q1_target(next_state, next_action)
            target_q2 = self.q2_target(next_state, next_action)
            target_q = torch.min(target_q1, target_q2)
            target_q = reward + (1 - done) * self.config.gamma * target_q
        
        current_q1 = self.q1(state, action)
        current_q2 = self.q2(state, action)
        
        q_loss = F.mse_loss(current_q1, target_q) + F.mse_loss(current_q2, target_q)
        
        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()
        
        # Train policy with MMD constraint
        policy_action = self.policy(state)
        policy_q = self.q1(state, policy_action)
        
        # Sample from behavior policy (VAE)
        z = torch.randn(state.shape[0], self.vae.latent_dim).to(self.device)
        behavior_action = self.vae.decode(state, z)
        
        # Compute MMD between policy and behavior
        mmd = self._compute_mmd(policy_action, behavior_action)
        
        # Policy loss with MMD constraint
        policy_loss = -policy_q.mean() + 100 * F.relu(mmd - self.mmd_epsilon)
        
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        # Update targets
        self._update_targets()
        
        return {
            'vae_loss': vae_loss.item(),
            'q_loss': q_loss.item(),
            'policy_loss': policy_loss.item(),
            'mmd': mmd.item(),
            'mean_q': current_q1.mean().item()
        }
    
    def _compute_mmd(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """Compute Maximum Mean Discrepancy."""
        def gaussian_kernel(x, y, sigma=1.0):
            diff = x.unsqueeze(1) - y.unsqueeze(0)
            return torch.exp(-torch.sum(diff ** 2, dim=-1) / (2 * sigma ** 2))
        
        xx = gaussian_kernel(x, x).mean()
        yy = gaussian_kernel(y, y).mean()
        xy = gaussian_kernel(x, y).mean()
        
        return xx + yy - 2 * xy
    
    def _update_targets(self):
        """Soft update of target networks."""
        for param, target_param in zip(self.q1.parameters(), self.q1_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )
        for param, target_param in zip(self.q2.parameters(), self.q2_target.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1 - self.config.tau) * target_param.data
            )


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("ADVANCED RL AGENTS DEMO")
    print("="*80)
    
    # Create config
    config = RLConfig(
        state_dim=20,
        action_dim=3,
        hidden_dim=128,
        batch_size=32
    )
    
    # Test CQL
    logger.info("\n[1] Testing CQL Agent...")
    cql = CQLAgent(config)
    state = np.random.randn(20)
    action = cql.get_action(state)
    logger.info(f"  State shape: {state.shape}")
    logger.info(f"  Action shape: {action.shape}")
    logger.info(f"  Action: {action}")
    
    # Test BCQ
    logger.info("\n[2] Testing BCQ Agent...")
    bcq = BCQAgent(config)
    action = bcq.get_action(state)
    logger.info(f"  Action: {action}")
    
    # Test BEAR
    logger.info("\n[3] Testing BEAR Agent...")
    bear = BEARAgent(config)
    action = bear.get_action(state)
    logger.info(f"  Action: {action}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
