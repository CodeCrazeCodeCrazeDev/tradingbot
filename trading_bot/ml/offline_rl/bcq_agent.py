"""
Batch-Constrained Q-Learning (BCQ) Agent

Implementation of BCQ for offline RL training.
"""

import os
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
import time
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.utils.tensorboard import SummaryWriter
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Install with: pip install torch")
    TORCH_AVAILABLE = False

try:
    import d3rlpy
    from d3rlpy.algos import BCQ as D3BCQ
    D3RLPY_AVAILABLE = True
except ImportError:
    logger.warning("d3rlpy not available. Install with: pip install d3rlpy")
    D3RLPY_AVAILABLE = False


class BCQAgent:
    """
    Batch-Constrained Q-Learning (BCQ) agent for offline RL.
    
    BCQ restricts actions to those in the dataset support to avoid
    extrapolation errors in offline settings.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        threshold: float = 0.3,
        tau: float = 0.005,
        discount: float = 0.99,
        lr: float = 3e-4,
        hidden_sizes: List[int] = [256, 256],
        use_gpu: bool = True,
        log_dir: str = "logs/bcq",
        use_d3rlpy: bool = True
    ):
        """
        Initialize BCQ agent.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            threshold: BCQ threshold for action selection
            tau: Target network update rate
            discount: Reward discount factor
            lr: Learning rate
            hidden_sizes: Hidden layer sizes
            use_gpu: Use GPU if available
            log_dir: Directory for logs
            use_d3rlpy: Use d3rlpy implementation
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.threshold = threshold
        self.tau = tau
        self.discount = discount
        self.lr = lr
        self.hidden_sizes = hidden_sizes
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.log_dir = log_dir
        self.use_d3rlpy = use_d3rlpy and D3RLPY_AVAILABLE
        
        # Create log directory
        os.makedirs(log_dir, exist_ok=True)
        
        if self.use_d3rlpy:
            self._init_d3rlpy()
        else:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for custom BCQ implementation")
            self._init_custom()
        
        logger.info(f"BCQ agent initialized: state_dim={state_dim}, action_dim={action_dim}")
        logger.info(f"Using {'d3rlpy' if self.use_d3rlpy else 'custom'} implementation")
    
    def _init_d3rlpy(self):
        """Initialize d3rlpy BCQ implementation."""
        self.model = D3BCQ(
            learning_rate=self.lr,
            batch_size=256,
            n_critics=2,
            bootstrap=True,
            share_encoder=False,
            target_update_interval=100,
            use_gpu=self.use_gpu,
            q_func_factory='qr',
            scaler='standard',
            reward_scaler='standard',
            action_flexibility=self.threshold,
            soft_q_backup=True,
            dynamics=None
        )
    
    def _init_custom(self):
        """Initialize custom BCQ implementation."""
        # Create networks
        self.q_network = self._build_q_network()
        self.target_q_network = self._build_q_network()
        self.vae = self._build_vae()
        self.perturbation_network = self._build_perturbation_network()
        
        # Copy parameters to target network
        self.target_q_network.load_state_dict(self.q_network.state_dict())
        
        # Freeze target network
        for param in self.target_q_network.parameters():
            param.requires_grad = False
        
        # Create optimizers
        self.q_optimizer = optim.Adam(self.q_network.parameters(), lr=self.lr)
        self.vae_optimizer = optim.Adam(self.vae.parameters(), lr=self.lr)
        self.perturbation_optimizer = optim.Adam(self.perturbation_network.parameters(), lr=self.lr)
        
        # Move to GPU if available
        if self.use_gpu:
            self.q_network = self.q_network.cuda()
            self.target_q_network = self.target_q_network.cuda()
            self.vae = self.vae.cuda()
            self.perturbation_network = self.perturbation_network.cuda()
        
        # Create tensorboard writer
        self.writer = SummaryWriter(log_dir=self.log_dir)
        
        # Training info
        self.train_steps = 0
    
    def _build_q_network(self) -> nn.Module:
        """
        Build Q network.
        
        Returns:
            Q network
        """
        layers = []
        input_dim = self.state_dim
        
        # Hidden layers
        for hidden_dim in self.hidden_sizes:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            input_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(input_dim, self.action_dim))
        
        return nn.Sequential(*layers)
    
    def _build_vae(self) -> nn.Module:
        """
        Build VAE for action generation.
        
        Returns:
            VAE
        """
        class VAE(nn.Module):
            def __init__(self, state_dim, action_dim, hidden_sizes, latent_dim=8):
                super(VAE, self).__init__()
                
                self.state_dim = state_dim
                self.action_dim = action_dim
                self.latent_dim = latent_dim
                
                # Encoder
                encoder_layers = []
                input_dim = state_dim + action_dim
                for hidden_dim in hidden_sizes:
                    encoder_layers.append(nn.Linear(input_dim, hidden_dim))
                    encoder_layers.append(nn.ReLU())
                    input_dim = hidden_dim
                
                self.encoder = nn.Sequential(*encoder_layers)
                self.mean = nn.Linear(input_dim, latent_dim)
                self.log_std = nn.Linear(input_dim, latent_dim)
                
                # Decoder
                decoder_layers = []
                input_dim = state_dim + latent_dim
                for hidden_dim in hidden_sizes:
                    decoder_layers.append(nn.Linear(input_dim, hidden_dim))
                    decoder_layers.append(nn.ReLU())
                    input_dim = hidden_dim
                
                self.decoder = nn.Sequential(*decoder_layers)
                self.action_out = nn.Linear(input_dim, action_dim)
            
            def encode(self, state, action):
                x = torch.cat([state, action], dim=1)
                x = self.encoder(x)
                mean = self.mean(x)
                log_std = self.log_std(x)
                return mean, log_std
            
            def reparameterize(self, mean, log_std):
                std = torch.exp(0.5 * log_std)
                eps = torch.randn_like(std)
                return mean + eps * std
            
            def decode(self, state, z):
                x = torch.cat([state, z], dim=1)
                x = self.decoder(x)
                return self.action_out(x)
            
            def forward(self, state, action):
                mean, log_std = self.encode(state, action)
                z = self.reparameterize(mean, log_std)
                recon = self.decode(state, z)
                return recon, mean, log_std
            
            def generate(self, state, num_samples=10):
                batch_size = state.size(0)
                z = torch.randn(batch_size, num_samples, self.latent_dim)
                if state.is_cuda:
                    z = z.cuda()
                
                state_rep = state.unsqueeze(1).repeat(1, num_samples, 1)
                state_rep = state_rep.view(batch_size * num_samples, -1)
                z_flat = z.view(batch_size * num_samples, -1)
                
                actions = self.decode(state_rep, z_flat)
                return actions.view(batch_size, num_samples, -1)
        
        return VAE(self.state_dim, self.action_dim, self.hidden_sizes)
    
    def _build_perturbation_network(self) -> nn.Module:
        """
        Build perturbation network.
        
        Returns:
            Perturbation network
        """
        class PerturbationNetwork(nn.Module):
            def __init__(self, state_dim, action_dim, hidden_sizes, max_perturbation=0.05):
                super(PerturbationNetwork, self).__init__()
                
                self.max_perturbation = max_perturbation
                
                layers = []
                input_dim = state_dim + action_dim
                for hidden_dim in hidden_sizes:
                    layers.append(nn.Linear(input_dim, hidden_dim))
                    layers.append(nn.ReLU())
                    input_dim = hidden_dim
                
                layers.append(nn.Linear(input_dim, action_dim))
                layers.append(nn.Tanh())  # Output in [-1, 1]
                
                self.net = nn.Sequential(*layers)
            
            def forward(self, state, action):
                x = torch.cat([state, action], dim=1)
                perturbation = self.net(x) * self.max_perturbation
                return perturbation
        
        return PerturbationNetwork(self.state_dim, self.action_dim, self.hidden_sizes)
    
    def train(
        self,
        dataset,
        n_epochs: int = 100,
        batch_size: int = 256,
        eval_dataset = None
    ):
        """
        Train BCQ agent.
        
        Args:
            dataset: Training dataset (OfflineRLDataset or d3rlpy MDPDataset)
            n_epochs: Number of training epochs
            batch_size: Batch size
            eval_dataset: Evaluation dataset
        
        Returns:
            Training metrics
        """
        if self.use_d3rlpy:
            return self._train_d3rlpy(dataset, n_epochs, eval_dataset)
        else:
            return self._train_custom(dataset, n_epochs, batch_size)
    
    def _train_d3rlpy(self, dataset, n_epochs: int, eval_dataset = None):
        """Train with d3rlpy."""
        # Convert dataset to d3rlpy format if needed
        if hasattr(dataset, 'to_d3rlpy'):
            d3_dataset = dataset.to_d3rlpy()
        else:
            d3_dataset = dataset
        
        # Convert eval dataset if provided
        d3_eval_dataset = None
        if eval_dataset:
            if hasattr(eval_dataset, 'to_d3rlpy'):
                d3_eval_dataset = eval_dataset.to_d3rlpy()
            else:
                d3_eval_dataset = eval_dataset
        
        # Train model
        start_time = time.time()
        
        self.model.fit(
            d3_dataset,
            n_epochs=n_epochs,
            verbose=True,
            eval_episodes=d3_eval_dataset,
            logdir=self.log_dir
        )
        
        train_time = time.time() - start_time
        logger.info(f"Training completed in {train_time:.2f}s")
        
        return {
            "train_time": train_time,
            "n_epochs": n_epochs,
            "final_loss": self.model.loss_history[-1] if hasattr(self.model, 'loss_history') else None
        }
    
    def _train_custom(self, dataset, n_epochs: int, batch_size: int):
        """Train with custom implementation."""
        # Create data loader
        from .replay_buffer import ReplayBuffer
        buffer = ReplayBuffer(capacity=len(dataset.states))
        buffer.load_from_dataset(dataset)
        
        # Training loop
        start_time = time.time()
        total_loss = 0.0
        
        for epoch in range(n_epochs):
            epoch_q_loss = 0.0
            epoch_vae_loss = 0.0
            epoch_perturb_loss = 0.0
            n_batches = 0
            
            for _ in range(len(dataset.states) // batch_size):
                # Sample batch
                states, actions, rewards, next_states, dones = buffer.sample(batch_size)
                
                # Convert to tensors
                states = torch.FloatTensor(states)
                actions = torch.LongTensor(actions)
                rewards = torch.FloatTensor(rewards)
                next_states = torch.FloatTensor(next_states)
                dones = torch.FloatTensor(dones)
                
                if self.use_gpu:
                    states = states.cuda()
                    actions = actions.cuda()
                    rewards = rewards.cuda()
                    next_states = next_states.cuda()
                    dones = dones.cuda()
                
                # Train VAE
                recon_actions, mean, log_std = self.vae(states, actions.float().unsqueeze(1))
                recon_loss = F.mse_loss(recon_actions, actions.float().unsqueeze(1))
                kl_loss = -0.5 * torch.mean(1 + log_std - mean.pow(2) - log_std.exp())
                vae_loss = recon_loss + 0.5 * kl_loss
                
                self.vae_optimizer.zero_grad()
                vae_loss.backward()
                self.vae_optimizer.step()
                
                # Train Q network
                with torch.no_grad():
                    # Generate actions for next states
                    next_actions = self.vae.generate(next_states)
                    next_actions = next_actions.view(-1, self.action_dim)
                    next_states_rep = next_states.unsqueeze(1).repeat(1, 10, 1).view(-1, self.state_dim)
                    
                    # Add perturbation
                    perturbations = self.perturbation_network(next_states_rep, next_actions)
                    perturbed_actions = next_actions + perturbations
                    
                    # Get Q values
                    target_q_values = self.target_q_network(next_states_rep)
                    target_q_values = target_q_values.gather(1, perturbed_actions.argmax(dim=1, keepdim=True))
                    target_q_values = target_q_values.view(batch_size, -1).max(1, keepdim=True)[0]
                    
                    # Compute target
                    target_q = rewards + (1 - dones) * self.discount * target_q_values
                
                # Update Q network
                q_values = self.q_network(states)
                q_values = q_values.gather(1, actions.unsqueeze(1))
                q_loss = F.mse_loss(q_values, target_q)
                
                self.q_optimizer.zero_grad()
                q_loss.backward()
                self.q_optimizer.step()
                
                # Train perturbation network
                with torch.no_grad():
                    vae_actions = self.vae.decode(states, torch.randn(batch_size, self.vae.latent_dim).cuda() if self.use_gpu else torch.randn(batch_size, self.vae.latent_dim))
                
                perturbations = self.perturbation_network(states, vae_actions)
                perturbed_actions = vae_actions + perturbations
                
                perturb_loss = -self.q_network(states).gather(1, perturbed_actions.argmax(dim=1, keepdim=True)).mean()
                
                self.perturbation_optimizer.zero_grad()
                perturb_loss.backward()
                self.perturbation_optimizer.step()
                
                # Update target network
                for param, target_param in zip(self.q_network.parameters(), self.target_q_network.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                
                # Log metrics
                epoch_q_loss += q_loss.item()
                epoch_vae_loss += vae_loss.item()
                epoch_perturb_loss += perturb_loss.item()
                n_batches += 1
                self.train_steps += 1
                
                # Log to tensorboard
                self.writer.add_scalar('Loss/q', q_loss.item(), self.train_steps)
                self.writer.add_scalar('Loss/vae', vae_loss.item(), self.train_steps)
                self.writer.add_scalar('Loss/perturbation', perturb_loss.item(), self.train_steps)
            
            # Log epoch metrics
            avg_q_loss = epoch_q_loss / n_batches
            avg_vae_loss = epoch_vae_loss / n_batches
            avg_perturb_loss = epoch_perturb_loss / n_batches
            
            logger.info(f"Epoch {epoch+1}/{n_epochs}, Q Loss: {avg_q_loss:.4f}, VAE Loss: {avg_vae_loss:.4f}, Perturb Loss: {avg_perturb_loss:.4f}")
        
        train_time = time.time() - start_time
        logger.info(f"Training completed in {train_time:.2f}s")
        
        return {
            "train_time": train_time,
            "n_epochs": n_epochs,
            "final_q_loss": avg_q_loss,
            "final_vae_loss": avg_vae_loss,
            "final_perturb_loss": avg_perturb_loss
        }
    
    def predict(self, state: np.ndarray) -> int:
        """
        Predict action for state.
        
        Args:
            state: State vector
        
        Returns:
            Action index
        """
        if self.use_d3rlpy:
            return self.model.predict([state])[0]
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                if self.use_gpu:
                    state_tensor = state_tensor.cuda()
                
                # Generate action from VAE
                z = torch.randn(1, self.vae.latent_dim)
                if self.use_gpu:
                    z = z.cuda()
                
                vae_action = self.vae.decode(state_tensor, z)
                
                # Add perturbation
                perturbation = self.perturbation_network(state_tensor, vae_action)
                perturbed_action = vae_action + perturbation
                
                return perturbed_action.argmax(dim=1).item()
    
    def predict_batch(self, states: np.ndarray) -> np.ndarray:
        """
        Predict actions for batch of states.
        
        Args:
            states: Batch of state vectors
        
        Returns:
            Batch of action indices
        """
        if self.use_d3rlpy:
            return self.model.predict(states)
        else:
            with torch.no_grad():
                states_tensor = torch.FloatTensor(states)
                if self.use_gpu:
                    states_tensor = states_tensor.cuda()
                
                # Generate actions from VAE
                batch_size = states.shape[0]
                z = torch.randn(batch_size, self.vae.latent_dim)
                if self.use_gpu:
                    z = z.cuda()
                
                vae_actions = self.vae.decode(states_tensor, z)
                
                # Add perturbation
                perturbations = self.perturbation_network(states_tensor, vae_actions)
                perturbed_actions = vae_actions + perturbations
                
                return perturbed_actions.argmax(dim=1).cpu().numpy()
    
    def save(self, path: str):
        """
        Save agent.
        
        Args:
            path: Path to save directory
        """
        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        if self.use_d3rlpy:
            self.model.save_model(str(save_dir / "model.pt"))
        else:
            torch.save({
                'q_network': self.q_network.state_dict(),
                'target_q_network': self.target_q_network.state_dict(),
                'vae': self.vae.state_dict(),
                'perturbation_network': self.perturbation_network.state_dict(),
                'q_optimizer': self.q_optimizer.state_dict(),
                'vae_optimizer': self.vae_optimizer.state_dict(),
                'perturbation_optimizer': self.perturbation_optimizer.state_dict(),
                'train_steps': self.train_steps,
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'threshold': self.threshold,
                'tau': self.tau,
                'discount': self.discount,
                'lr': self.lr,
                'hidden_sizes': self.hidden_sizes,
            }, save_dir / "model.pt")
        
        logger.info(f"Agent saved to {path}")
    
    def load(self, path: str):
        """
        Load agent.
        
        Args:
            path: Path to load directory
        """
        load_dir = Path(path)
        
        if self.use_d3rlpy:
            self.model.load_model(str(load_dir / "model.pt"))
        else:
            checkpoint = torch.load(load_dir / "model.pt")
            
            # Update attributes
            self.state_dim = checkpoint['state_dim']
            self.action_dim = checkpoint['action_dim']
            self.threshold = checkpoint['threshold']
            self.tau = checkpoint['tau']
            self.discount = checkpoint['discount']
            self.lr = checkpoint['lr']
            self.hidden_sizes = checkpoint['hidden_sizes']
            self.train_steps = checkpoint['train_steps']
            
            # Reinitialize networks
            self.q_network = self._build_q_network()
            self.target_q_network = self._build_q_network()
            self.vae = self._build_vae()
            self.perturbation_network = self._build_perturbation_network()
            
            # Load state dicts
            self.q_network.load_state_dict(checkpoint['q_network'])
            self.target_q_network.load_state_dict(checkpoint['target_q_network'])
            self.vae.load_state_dict(checkpoint['vae'])
            self.perturbation_network.load_state_dict(checkpoint['perturbation_network'])
            
            # Create optimizers
            self.q_optimizer = optim.Adam(self.q_network.parameters(), lr=self.lr)
            self.vae_optimizer = optim.Adam(self.vae.parameters(), lr=self.lr)
            self.perturbation_optimizer = optim.Adam(self.perturbation_network.parameters(), lr=self.lr)
            
            # Load optimizer state
            self.q_optimizer.load_state_dict(checkpoint['q_optimizer'])
            self.vae_optimizer.load_state_dict(checkpoint['vae_optimizer'])
            self.perturbation_optimizer.load_state_dict(checkpoint['perturbation_optimizer'])
            
            # Move to GPU if available
            if self.use_gpu:
                self.q_network = self.q_network.cuda()
                self.target_q_network = self.target_q_network.cuda()
                self.vae = self.vae.cuda()
                self.perturbation_network = self.perturbation_network.cuda()
        
        logger.info(f"Agent loaded from {path}")
