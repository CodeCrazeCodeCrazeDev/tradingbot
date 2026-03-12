"""
Implicit Q-Learning (IQL) Agent

IQL avoids explicit policy extraction and learns implicitly through value functions.
More stable than CQL for certain offline RL tasks.
"""

import os
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import time
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Install with: pip install torch")
    TORCH_AVAILABLE = False

try:
    import d3rlpy
    from d3rlpy.algos import IQL as D3IQL
    D3RLPY_AVAILABLE = True
except ImportError:
    logger.warning("d3rlpy not available. Install with: pip install d3rlpy")
    D3RLPY_AVAILABLE = False


class IQLAgent:
    """
    Implicit Q-Learning (IQL) agent for offline RL.
    
    IQL learns Q-values and value functions without explicit policy optimization,
    making it more stable for offline learning.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        expectile: float = 0.7,
        temperature: float = 3.0,
        tau: float = 0.005,
        discount: float = 0.99,
        lr: float = 3e-4,
        hidden_sizes: List[int] = [256, 256],
        use_gpu: bool = True,
        log_dir: str = "logs/iql",
        use_d3rlpy: bool = True
    ):
        """
        Initialize IQL agent.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            expectile: Expectile for value function (0.7 = focus on upper tail)
            temperature: Temperature for advantage weighting
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
        self.expectile = expectile
        self.temperature = temperature
        self.tau = tau
        self.discount = discount
        self.lr = lr
        self.hidden_sizes = hidden_sizes
        self.use_gpu = use_gpu and torch.cuda.is_available() if TORCH_AVAILABLE else False
        self.log_dir = log_dir
        self.use_d3rlpy = use_d3rlpy and D3RLPY_AVAILABLE
        
        os.makedirs(log_dir, exist_ok=True)
        
        if self.use_d3rlpy:
            self._init_d3rlpy()
        else:
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch is required for custom IQL implementation")
            self._init_custom()
        
        logger.info(f"IQL agent initialized: state_dim={state_dim}, action_dim={action_dim}")
        logger.info(f"Using {'d3rlpy' if self.use_d3rlpy else 'custom'} implementation")
    
    def _init_d3rlpy(self):
        """Initialize d3rlpy IQL implementation."""
        self.model = D3IQL(
            learning_rate=self.lr,
            batch_size=256,
            n_critics=2,
            expectile=self.expectile,
            weight_temp=self.temperature,
            max_weight=100.0,
            use_gpu=self.use_gpu,
            scaler='standard',
            reward_scaler='standard'
        )
    
    def _init_custom(self):
        """Initialize custom IQL implementation."""
        # Create networks
        self.q_network1 = self._build_q_network()
        self.q_network2 = self._build_q_network()
        self.v_network = self._build_v_network()
        
        # Target networks
        self.target_q_network1 = self._build_q_network()
        self.target_q_network2 = self._build_q_network()
        
        self.target_q_network1.load_state_dict(self.q_network1.state_dict())
        self.target_q_network2.load_state_dict(self.q_network2.state_dict())
        
        # Freeze target networks
        for param in self.target_q_network1.parameters():
            param.requires_grad = False
        for param in self.target_q_network2.parameters():
            param.requires_grad = False
        
        # Optimizers
        self.q_optimizer = optim.Adam(
            list(self.q_network1.parameters()) + list(self.q_network2.parameters()),
            lr=self.lr
        )
        self.v_optimizer = optim.Adam(self.v_network.parameters(), lr=self.lr)
        
        # Move to GPU
        if self.use_gpu:
            self.q_network1 = self.q_network1.cuda()
            self.q_network2 = self.q_network2.cuda()
            self.v_network = self.v_network.cuda()
            self.target_q_network1 = self.target_q_network1.cuda()
            self.target_q_network2 = self.target_q_network2.cuda()
        
        self.train_steps = 0
    
    def _build_q_network(self) -> nn.Module:
        """Build Q network."""
        layers = []
        input_dim = self.state_dim
        
        for hidden_dim in self.hidden_sizes:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, self.action_dim))
        
        return nn.Sequential(*layers)
    
    def _build_v_network(self) -> nn.Module:
        """Build V network."""
        layers = []
        input_dim = self.state_dim
        
        for hidden_dim in self.hidden_sizes:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, 1))
        
        return nn.Sequential(*layers)
    
    def _expectile_loss(self, diff: torch.Tensor, expectile: float) -> torch.Tensor:
        """Compute expectile loss (asymmetric L2 loss)."""
        weight = torch.where(diff > 0, expectile, 1 - expectile)
        return weight * (diff ** 2)
    
    def train(
        self,
        dataset,
        n_epochs: int = 100,
        batch_size: int = 256,
        eval_dataset = None
    ):
        """
        Train IQL agent.
        
        Args:
            dataset: Training dataset
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
        if hasattr(dataset, 'to_d3rlpy'):
            d3_dataset = dataset.to_d3rlpy()
        else:
            d3_dataset = dataset
        
        d3_eval_dataset = None
        if eval_dataset:
            if hasattr(eval_dataset, 'to_d3rlpy'):
                d3_eval_dataset = eval_dataset.to_d3rlpy()
            else:
                d3_eval_dataset = eval_dataset
        
        start_time = time.time()
        
        self.model.fit(
            d3_dataset,
            n_epochs=n_epochs,
            verbose=True,
            eval_episodes=d3_eval_dataset,
            logdir=self.log_dir
        )
        
        train_time = time.time() - start_time
        logger.info(f"IQL training completed in {train_time:.2f}s")
        
        return {
            "train_time": train_time,
            "n_epochs": n_epochs,
            "algorithm": "IQL"
        }
    
    def _train_custom(self, dataset, n_epochs: int, batch_size: int):
        """Train with custom implementation."""
        from .replay_buffer import ReplayBuffer
        buffer = ReplayBuffer(capacity=len(dataset.states))
        buffer.load_from_dataset(dataset)
        
        start_time = time.time()
        
        for epoch in range(n_epochs):
            epoch_q_loss = 0.0
            epoch_v_loss = 0.0
            n_batches = 0
            
            for _ in range(len(dataset.states) // batch_size):
                states, actions, rewards, next_states, dones = buffer.sample(batch_size)
                
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
                
                # Update V network
                with torch.no_grad():
                    target_q1 = self.target_q_network1(states)
                    target_q2 = self.target_q_network2(states)
                    target_q = torch.min(target_q1, target_q2)
                    target_q = target_q.gather(1, actions.unsqueeze(1))
                
                v_values = self.v_network(states)
                v_loss = self._expectile_loss(target_q - v_values, self.expectile).mean()
                
                self.v_optimizer.zero_grad()
                v_loss.backward()
                self.v_optimizer.step()
                
                # Update Q networks
                with torch.no_grad():
                    next_v = self.v_network(next_states)
                    target_q_value = rewards.unsqueeze(1) + (1 - dones.unsqueeze(1)) * self.discount * next_v
                
                q1_values = self.q_network1(states).gather(1, actions.unsqueeze(1))
                q2_values = self.q_network2(states).gather(1, actions.unsqueeze(1))
                
                q1_loss = F.mse_loss(q1_values, target_q_value)
                q2_loss = F.mse_loss(q2_values, target_q_value)
                q_loss = q1_loss + q2_loss
                
                self.q_optimizer.zero_grad()
                q_loss.backward()
                self.q_optimizer.step()
                
                # Update target networks
                for param, target_param in zip(self.q_network1.parameters(), self.target_q_network1.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                
                for param, target_param in zip(self.q_network2.parameters(), self.target_q_network2.parameters()):
                    target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
                
                epoch_q_loss += q_loss.item()
                epoch_v_loss += v_loss.item()
                n_batches += 1
                self.train_steps += 1
            
            avg_q_loss = epoch_q_loss / n_batches
            avg_v_loss = epoch_v_loss / n_batches
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{n_epochs}, Q Loss: {avg_q_loss:.4f}, V Loss: {avg_v_loss:.4f}")
        
        train_time = time.time() - start_time
        logger.info(f"IQL training completed in {train_time:.2f}s")
        
        return {
            "train_time": train_time,
            "n_epochs": n_epochs,
            "final_q_loss": avg_q_loss,
            "final_v_loss": avg_v_loss
        }
    
    def predict(self, state: np.ndarray) -> int:
        """Predict action for state."""
        if self.use_d3rlpy:
            return self.model.predict([state])[0]
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                if self.use_gpu:
                    state_tensor = state_tensor.cuda()
                
                q1 = self.q_network1(state_tensor)
                q2 = self.q_network2(state_tensor)
                q_values = torch.min(q1, q2)
                
                return q_values.argmax(dim=1).item()
    
    def predict_batch(self, states: np.ndarray) -> np.ndarray:
        """Predict actions for batch of states."""
        if self.use_d3rlpy:
            return self.model.predict(states)
        else:
            with torch.no_grad():
                states_tensor = torch.FloatTensor(states)
                if self.use_gpu:
                    states_tensor = states_tensor.cuda()
                
                q1 = self.q_network1(states_tensor)
                q2 = self.q_network2(states_tensor)
                q_values = torch.min(q1, q2)
                
                return q_values.argmax(dim=1).cpu().numpy()
    
    def save(self, path: str):
        """Save agent."""
        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        if self.use_d3rlpy:
            self.model.save_model(str(save_dir / "model.pt"))
        else:
            torch.save({
                'q_network1': self.q_network1.state_dict(),
                'q_network2': self.q_network2.state_dict(),
                'v_network': self.v_network.state_dict(),
                'target_q_network1': self.target_q_network1.state_dict(),
                'target_q_network2': self.target_q_network2.state_dict(),
                'q_optimizer': self.q_optimizer.state_dict(),
                'v_optimizer': self.v_optimizer.state_dict(),
                'train_steps': self.train_steps,
                'config': {
                    'state_dim': self.state_dim,
                    'action_dim': self.action_dim,
                    'expectile': self.expectile,
                    'temperature': self.temperature,
                    'tau': self.tau,
                    'discount': self.discount,
                    'lr': self.lr,
                    'hidden_sizes': self.hidden_sizes,
                }
            }, save_dir / "model.pt")
        
        logger.info(f"IQL agent saved to {path}")
    
    def load(self, path: str):
        """Load agent."""
        load_dir = Path(path)
        
        if self.use_d3rlpy:
            self.model.load_model(str(load_dir / "model.pt"))
        else:
            checkpoint = torch.load(load_dir / "model.pt")
            
            # Update config
            config = checkpoint['config']
            self.state_dim = config['state_dim']
            self.action_dim = config['action_dim']
            self.expectile = config['expectile']
            self.temperature = config['temperature']
            self.tau = config['tau']
            self.discount = config['discount']
            self.lr = config['lr']
            self.hidden_sizes = config['hidden_sizes']
            self.train_steps = checkpoint['train_steps']
            
            # Reinitialize networks
            self._init_custom()
            
            # Load state dicts
            self.q_network1.load_state_dict(checkpoint['q_network1'])
            self.q_network2.load_state_dict(checkpoint['q_network2'])
            self.v_network.load_state_dict(checkpoint['v_network'])
            self.target_q_network1.load_state_dict(checkpoint['target_q_network1'])
            self.target_q_network2.load_state_dict(checkpoint['target_q_network2'])
            self.q_optimizer.load_state_dict(checkpoint['q_optimizer'])
            self.v_optimizer.load_state_dict(checkpoint['v_optimizer'])
        
        logger.info(f"IQL agent loaded from {path}")
