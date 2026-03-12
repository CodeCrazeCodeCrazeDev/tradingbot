"""
Conservative Q-Learning (CQL) Agent

Implementation of CQL for offline RL training.
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
    from d3rlpy.algos import CQL as D3CQL
    D3RLPY_AVAILABLE = True
except ImportError:
    logger.warning("d3rlpy not available. Install with: pip install d3rlpy")
    D3RLPY_AVAILABLE = False


class CQLAgent:
    """
    Conservative Q-Learning (CQL) agent for offline RL.
    
    CQL minimizes Q-values on out-of-distribution actions to avoid
    overestimation in offline settings.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        alpha: float = 1.0,
        tau: float = 0.005,
        discount: float = 0.99,
        lr: float = 3e-4,
        hidden_sizes: List[int] = [256, 256],
        use_gpu: bool = True,
        log_dir: str = "logs/cql",
        use_d3rlpy: bool = True
    ):
        """
        Initialize CQL agent.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            alpha: CQL regularization weight
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
        self.alpha = alpha
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
                raise ImportError("PyTorch is required for custom CQL implementation")
            self._init_custom()
        
        logger.info(f"CQL agent initialized: state_dim={state_dim}, action_dim={action_dim}")
        logger.info(f"Using {'d3rlpy' if self.use_d3rlpy else 'custom'} implementation")
    
    def _init_d3rlpy(self):
        """Initialize d3rlpy CQL implementation."""
        self.model = D3CQL(
            learning_rate=self.lr,
            batch_size=256,
            n_critics=2,
            bootstrap=True,
            share_encoder=False,
            target_update_interval=100,
            use_gpu=self.use_gpu,
            alpha=self.alpha,
            conservative_weight=self.alpha,
            q_func_factory='qr',
            scaler='standard',
            reward_scaler='standard',
            n_action_samples=10,
            soft_q_backup=True,
            dynamics=None
        )
    
    def _init_custom(self):
        """Initialize custom CQL implementation."""
        # Create Q networks
        self.q_network = self._build_q_network()
        self.target_q_network = self._build_q_network()
        
        # Copy parameters to target network
        self.target_q_network.load_state_dict(self.q_network.state_dict())
        
        # Freeze target network
        for param in self.target_q_network.parameters():
            param.requires_grad = False
        
        # Create optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.lr)
        
        # Move to GPU if available
        if self.use_gpu:
            self.q_network = self.q_network.cuda()
            self.target_q_network = self.target_q_network.cuda()
        
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
    
    def train(
        self,
        dataset,
        n_epochs: int = 100,
        batch_size: int = 256,
        eval_dataset = None
    ):
        """
        Train CQL agent.
        
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
            epoch_loss = 0.0
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
                
                # Compute Q values
                q_values = self.q_network(states)
                q_values_taken = q_values.gather(1, actions.unsqueeze(1))
                
                # Compute target Q values
                with torch.no_grad():
                    next_q_values = self.target_q_network(next_states)
                    next_q_values_max = next_q_values.max(1, keepdim=True)[0]
                    target_q_values = rewards + (1 - dones) * self.discount * next_q_values_max
                
                # Compute TD loss
                td_loss = F.mse_loss(q_values_taken, target_q_values)
                
                # Compute CQL loss
                cql_loss = torch.logsumexp(q_values, dim=1, keepdim=True) - q_values_taken
                cql_loss = cql_loss.mean()
                
                # Total loss
                loss = td_loss + self.alpha * cql_loss
                
                # Update network
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                # Update target network
                for param, target_param in zip(self.q_network.parameters(), self.target_q_network.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                
                # Log metrics
                epoch_loss += loss.item()
                n_batches += 1
                self.train_steps += 1
                
                # Log to tensorboard
                self.writer.add_scalar('Loss/total', loss.item(), self.train_steps)
                self.writer.add_scalar('Loss/td', td_loss.item(), self.train_steps)
                self.writer.add_scalar('Loss/cql', cql_loss.item(), self.train_steps)
            
            # Log epoch metrics
            avg_epoch_loss = epoch_loss / n_batches
            logger.info(f"Epoch {epoch+1}/{n_epochs}, Loss: {avg_epoch_loss:.4f}")
            total_loss += avg_epoch_loss
        
        train_time = time.time() - start_time
        logger.info(f"Training completed in {train_time:.2f}s")
        
        return {
            "train_time": train_time,
            "n_epochs": n_epochs,
            "final_loss": avg_epoch_loss
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
                q_values = self.q_network(state_tensor)
                return q_values.argmax(dim=1).item()
    
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
                q_values = self.q_network(states_tensor)
                return q_values.argmax(dim=1).cpu().numpy()
    
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
                'optimizer': self.optimizer.state_dict(),
                'train_steps': self.train_steps,
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'alpha': self.alpha,
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
            self.alpha = checkpoint['alpha']
            self.tau = checkpoint['tau']
            self.discount = checkpoint['discount']
            self.lr = checkpoint['lr']
            self.hidden_sizes = checkpoint['hidden_sizes']
            self.train_steps = checkpoint['train_steps']
            
            # Reinitialize networks
            self.q_network = self._build_q_network()
            self.target_q_network = self._build_q_network()
            
            # Load state dicts
            self.q_network.load_state_dict(checkpoint['q_network'])
            self.target_q_network.load_state_dict(checkpoint['target_q_network'])
            
            # Create optimizer
            self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.lr)
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            
            # Move to GPU if available
            if self.use_gpu:
                self.q_network = self.q_network.cuda()
                self.target_q_network = self.target_q_network.cuda()
        
        logger.info(f"Agent loaded from {path}")
