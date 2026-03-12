"""
Phase 5: Meta-Learning - Model-Agnostic Meta-Learning (MAML)
Quick adaptation to new market regimes
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class MAMLPolicy(nn.Module):
    """
    Meta-learning policy that can quickly adapt to new market regimes.
    Uses MAML (Model-Agnostic Meta-Learning) algorithm.
    """
    
    def __init__(
        self,
        input_dim: int = 20,
        hidden_dim: int = 64,
        output_dim: int = 3,  # BUY, SELL, HOLD
        alpha: float = 0.01,  # Inner loop learning rate
        beta: float = 0.001   # Outer loop learning rate
    ):
        super().__init__()
        
        # Policy network
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
        self.alpha = alpha
        self.beta = beta
        
        # Optimizer for meta-updates
        self.meta_optimizer = torch.optim.Adam(self.parameters(), lr=beta)
        
        logger.info("✅ MAML Policy initialized")
        logger.info(f"   Input dim: {input_dim}")
        logger.info(f"   Hidden dim: {hidden_dim}")
        logger.info(f"   Output dim: {output_dim}")
        logger.info(f"   Alpha: {alpha}")
        logger.info(f"   Beta: {beta}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through policy network."""
        return self.network(x)
    
    def adapt(
        self,
        support_data: Dict[str, torch.Tensor],
        num_steps: int = 5
    ) -> nn.Module:
        """
        Adapt policy to new market regime using support data.
        
        Args:
            support_data: Dictionary with states and rewards
            num_steps: Number of gradient steps for adaptation
        
        Returns:
            Adapted policy network
        """
        # Create clone of current policy
        adapted_policy = deepcopy(self)
        
        # Temporary optimizer for adaptation
        temp_optimizer = torch.optim.SGD(
            adapted_policy.parameters(),
            lr=self.alpha
        )
        
        # Adapt policy
        for step in range(num_steps):
            # Forward pass
            logits = adapted_policy(support_data['states'])
            loss = F.cross_entropy(logits, support_data['actions'])
            
            # Backward pass
            temp_optimizer.zero_grad()
            loss.backward()
            temp_optimizer.step()
            
            if (step + 1) % 1 == 0:
                logger.debug(f"   Adaptation step {step + 1}/{num_steps}, "
                           f"loss: {loss.item():.4f}")
        
        return adapted_policy
    
    def meta_learn(
        self,
        tasks: List[Dict[str, torch.Tensor]],
        num_inner_steps: int = 5,
        num_outer_steps: int = 1000
    ):
        """
        Meta-train policy across multiple market regimes.
        
        Args:
            tasks: List of task data (different market regimes)
            num_inner_steps: Steps per adaptation
            num_outer_steps: Meta-training steps
        """
        for step in range(num_outer_steps):
            meta_loss = 0.0
            
            # Iterate through tasks
            for task_data in tasks:
                # Split task data into support and query sets
                support_data, query_data = self._split_task_data(task_data)
                
                # Adapt policy to task
                adapted_policy = self.adapt(support_data, num_inner_steps)
                
                # Evaluate on query set
                query_logits = adapted_policy(query_data['states'])
                task_loss = F.cross_entropy(query_logits, query_data['actions'])
                
                meta_loss += task_loss
            
            # Meta-update
            self.meta_optimizer.zero_grad()
            meta_loss.backward()
            self.meta_optimizer.step()
            
            if (step + 1) % 100 == 0:
                logger.info(f"Meta-training step {step + 1}/{num_outer_steps}, "
                          f"loss: {meta_loss.item():.4f}")
    
    def _split_task_data(
        self,
        task_data: Dict[str, torch.Tensor]
    ) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        """Split task data into support and query sets."""
        n = len(task_data['states'])
        n_support = n // 2
        
        support_data = {
            'states': task_data['states'][:n_support],
            'actions': task_data['actions'][:n_support],
            'rewards': task_data['rewards'][:n_support]
        }
        
        query_data = {
            'states': task_data['states'][n_support:],
            'actions': task_data['actions'][n_support:],
            'rewards': task_data['rewards'][n_support:]
        }
        
        return support_data, query_data
    
    def save(self, filepath: str):
        """Save meta-learned policy."""
        torch.save({
            'network': self.state_dict(),
            'alpha': self.alpha,
            'beta': self.beta
        }, filepath)
        logger.info(f"💾 MAML Policy saved to {filepath}")
    
    def load(self, filepath: str):
        """Load meta-learned policy."""
        state = torch.load(filepath)
        self.load_state_dict(state['network'])
        self.alpha = state['alpha']
        self.beta = state['beta']
        logger.info(f"📂 MAML Policy loaded from {filepath}")


class MAMLMetaLearner:
    """
    High-level interface for meta-learning trading strategies.
    Manages task generation and adaptation.
    """
    
    def __init__(
        self,
        input_dim: int = 20,
        hidden_dim: int = 64,
        output_dim: int = 3,
        alpha: float = 0.01,
        beta: float = 0.001
    ):
        self.policy = MAMLPolicy(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            alpha=alpha,
            beta=beta
        )
        
        self.task_buffer = []
        self.adaptation_history = []
    
    def add_task(self, task_data: Dict[str, torch.Tensor]):
        """Add new task (market regime) to buffer."""
        self.task_buffer.append(task_data)
        logger.info(f"📊 Added task to buffer (total: {len(self.task_buffer)})")
    
    def meta_train(
        self,
        num_inner_steps: int = 5,
        num_outer_steps: int = 1000,
        min_tasks: int = 5
    ):
        """Train meta-policy on collected tasks."""
        if len(self.task_buffer) < min_tasks:
            logger.warning(f"⚠️ Not enough tasks for meta-training "
                         f"({len(self.task_buffer)} < {min_tasks})")
            return
        
        logger.info(f"🎯 Starting meta-training on {len(self.task_buffer)} tasks")
        self.policy.meta_learn(
            self.task_buffer,
            num_inner_steps=num_inner_steps,
            num_outer_steps=num_outer_steps
        )
    
    def adapt_to_regime(
        self,
        regime_data: Dict[str, torch.Tensor],
        num_steps: int = 5
    ) -> MAMLPolicy:
        """
        Quick adaptation to new market regime.
        
        Args:
            regime_data: Recent market data
            num_steps: Adaptation steps
        
        Returns:
            Adapted policy
        """
        logger.info("🔄 Adapting to new market regime...")
        adapted_policy = self.policy.adapt(regime_data, num_steps)
        
        # Record adaptation
        self.adaptation_history.append({
            'timestamp': np.datetime64('now'),
            'num_steps': num_steps,
            'data_size': len(regime_data['states'])
        })
        
        return adapted_policy
    
    def get_adaptation_stats(self) -> Dict:
        """Get statistics about adaptations."""
        if not self.adaptation_history:
            return {}
        
        recent = self.adaptation_history[-10:]
        
        return {
            'total_adaptations': len(self.adaptation_history),
            'avg_steps': np.mean([h['num_steps'] for h in recent]),
            'avg_data_size': np.mean([h['data_size'] for h in recent]),
            'last_adaptation': self.adaptation_history[-1]['timestamp']
        }
    
    def save_state(self, filepath: str):
        """Save complete meta-learner state."""
        state = {
            'policy': self.policy.state_dict(),
            'task_buffer': self.task_buffer,
            'adaptation_history': self.adaptation_history
        }
        torch.save(state, filepath)
        logger.info(f"💾 Meta-learner state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load complete meta-learner state."""
        state = torch.load(filepath)
        self.policy.load_state_dict(state['policy'])
        self.task_buffer = state['task_buffer']
        self.adaptation_history = state['adaptation_history']
        logger.info(f"📂 Meta-learner state loaded from {filepath}")
