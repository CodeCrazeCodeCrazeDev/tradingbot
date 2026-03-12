"""
Model-Agnostic Meta-Learning (MAML) for Trading

Paper: "Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks"
Finn et al. (ICML 2017)

Enables few-shot adaptation to new market regimes with minimal data.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from copy import deepcopy
import numpy

logger = logging.getLogger(__name__)


@dataclass
class MAMLConfig:
    """MAML configuration."""
    inner_lr: float = 0.01  # Learning rate for inner loop
    outer_lr: float = 0.001  # Learning rate for outer loop
    num_inner_steps: int = 5  # Number of gradient steps in inner loop
    num_tasks_per_batch: int = 4  # Number of tasks per meta-batch
    support_size: int = 10  # Number of samples for adaptation
    query_size: int = 10  # Number of samples for evaluation


class TradingPolicy(nn.Module):
    """Simple trading policy network."""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
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


class MAMLTrainer:
    """
    MAML trainer for trading policies.
    
    Meta-trains on multiple market regimes to enable fast adaptation.
    """
    
    def __init__(
        self,
        policy: nn.Module,
        config: Optional[MAMLConfig] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize MAML trainer.
        
        Args:
            policy: Policy network to meta-train
            config: MAML configuration
            device: Device to use
        """
        self.policy = policy.to(device)
        self.config = config or MAMLConfig()
        self.device = torch.device(device)
        
        # Meta-optimizer
        self.meta_optimizer = torch.optim.Adam(
            self.policy.parameters(),
            lr=self.config.outer_lr
        )
        
        # Track meta-training history
        self.meta_train_losses = []
        self.meta_val_losses = []
        
        logger.info(f"MAML trainer initialized: inner_lr={config.inner_lr}, outer_lr={config.outer_lr}")
    
    def meta_train_step(
        self,
        tasks: List[Dict[str, torch.Tensor]]
    ) -> Dict[str, float]:
        """
        Perform one meta-training step.
        
        Args:
            tasks: List of task dictionaries, each containing:
                - support_states: States for adaptation
                - support_actions: Actions for adaptation
                - query_states: States for evaluation
                - query_actions: Actions for evaluation
        
        Returns:
            Dictionary of losses
        """
        meta_loss = 0.0
        task_losses = []
        
        for task in tasks:
            # Inner loop: Adapt to task
            adapted_params = self._inner_loop(
                task['support_states'],
                task['support_actions']
            )
            
            # Outer loop: Evaluate on query set
            query_loss = self._compute_loss(
                task['query_states'],
                task['query_actions'],
                adapted_params
            )
            
            meta_loss += query_loss
            task_losses.append(query_loss.item())
        
        # Average over tasks
        meta_loss = meta_loss / len(tasks)
        
        # Meta-update
        self.meta_optimizer.zero_grad()
        meta_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 1.0)
        self.meta_optimizer.step()
        
        # Track
        self.meta_train_losses.append(meta_loss.item())
        
        return {
            'meta_loss': meta_loss.item(),
            'mean_task_loss': np.mean(task_losses),
            'std_task_loss': np.std(task_losses)
        }
    
    def _inner_loop(
        self,
        support_states: torch.Tensor,
        support_actions: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Inner loop: Adapt policy to task.
        
        Args:
            support_states: Support set states
            support_actions: Support set actions
        
        Returns:
            Adapted parameters
        """
        # Clone current parameters
        adapted_params = {
            name: param.clone()
            for name, param in self.policy.named_parameters()
        }
        
        # Gradient descent on support set
        for _ in range(self.config.num_inner_steps):
            # Compute loss with current adapted params
            loss = self._compute_loss(
                support_states,
                support_actions,
                adapted_params
            )
            
            # Compute gradients
            grads = torch.autograd.grad(
                loss,
                adapted_params.values(),
                create_graph=True
            )
            
            # Update adapted params
            adapted_params = {
                name: param - self.config.inner_lr * grad
                for (name, param), grad in zip(adapted_params.items(), grads)
            }
        
        return adapted_params
    
    def _compute_loss(
        self,
        states: torch.Tensor,
        actions: torch.Tensor,
        params: Optional[Dict[str, torch.Tensor]] = None
    ) -> torch.Tensor:
        """
        Compute loss with given parameters.
        
        Args:
            states: Input states
            actions: Target actions
            params: Parameters to use (if None, use current policy params)
        
        Returns:
            Loss value
        """
        if params is None:
            # Use current policy
            predictions = self.policy(states)
        else:
            # Use provided parameters
            predictions = self._forward_with_params(states, params)
        
        return F.mse_loss(predictions, actions)
    
    def _forward_with_params(
        self,
        states: torch.Tensor,
        params: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Forward pass with custom parameters."""
        # Manual forward pass using provided parameters
        x = states
        
        # Layer 1
        x = F.linear(x, params['fc1.weight'], params['fc1.bias'])
        x = F.layer_norm(x, [params['fc1.weight'].shape[0]], 
                        params['ln1.weight'], params['ln1.bias'])
        x = F.relu(x)
        
        # Layer 2
        x = F.linear(x, params['fc2.weight'], params['fc2.bias'])
        x = F.layer_norm(x, [params['fc2.weight'].shape[0]],
                        params['ln2.weight'], params['ln2.bias'])
        x = F.relu(x)
        
        # Layer 3
        x = F.linear(x, params['fc3.weight'], params['fc3.bias'])
        x = torch.tanh(x)
        
        return x
    
    def adapt(
        self,
        support_states: torch.Tensor,
        support_actions: torch.Tensor,
        num_steps: Optional[int] = None
    ) -> nn.Module:
        """
        Adapt policy to new task.
        
        Args:
            support_states: Support set states
            support_actions: Support set actions
            num_steps: Number of adaptation steps (default: config.num_inner_steps)
        
        Returns:
            Adapted policy
        """
        if num_steps is None:
            num_steps = self.config.num_inner_steps
        
        # Clone policy
        adapted_policy = deepcopy(self.policy)
        optimizer = torch.optim.SGD(adapted_policy.parameters(), lr=self.config.inner_lr)
        
        # Adapt
        for _ in range(num_steps):
            predictions = adapted_policy(support_states)
            loss = F.mse_loss(predictions, support_actions)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        return adapted_policy
    
    def evaluate_adaptation(
        self,
        task: Dict[str, torch.Tensor]
    ) -> Dict[str, float]:
        """
        Evaluate adaptation performance.
        
        Args:
            task: Task with support and query sets
        
        Returns:
            Evaluation metrics
        """
        # Before adaptation
        with torch.no_grad():
            pre_adapt_pred = self.policy(task['query_states'])
            pre_adapt_loss = F.mse_loss(pre_adapt_pred, task['query_actions']).item()
        
        # Adapt
        adapted_policy = self.adapt(
            task['support_states'],
            task['support_actions']
        )
        
        # After adaptation
        with torch.no_grad():
            post_adapt_pred = adapted_policy(task['query_states'])
            post_adapt_loss = F.mse_loss(post_adapt_pred, task['query_actions']).item()
        
        improvement = (pre_adapt_loss - post_adapt_loss) / pre_adapt_loss * 100
        
        return {
            'pre_adapt_loss': pre_adapt_loss,
            'post_adapt_loss': post_adapt_loss,
            'improvement_pct': improvement
        }


class RegimeAdaptiveTrader:
    """
    Trading system with MAML-based regime adaptation.
    
    Quickly adapts to new market regimes with few samples.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize regime-adaptive trader.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            hidden_dim: Hidden layer dimension
            device: Device to use
        """
        self.device = torch.device(device)
        
        # Create policy
        self.policy = TradingPolicy(state_dim, action_dim, hidden_dim).to(self.device)
        
        # MAML trainer
        self.maml_trainer = MAMLTrainer(self.policy, device=device)
        
        # Current adapted policy
        self.current_policy = self.policy
        
        # Regime history
        self.regime_history = []
        
        logger.info("Regime-adaptive trader initialized")
    
    def meta_train(
        self,
        regime_tasks: List[Dict[str, Any]],
        num_epochs: int = 100
    ) -> Dict[str, List[float]]:
        """
        Meta-train on multiple market regimes.
        
        Args:
            regime_tasks: List of regime tasks
            num_epochs: Number of meta-training epochs
        
        Returns:
            Training history
        """
        history = {'meta_loss': [], 'task_loss': []}
        
        for epoch in range(num_epochs):
            # Sample batch of tasks
            batch_tasks = np.random.choice(regime_tasks, size=4, replace=True)
            
            # Meta-train step
            metrics = self.maml_trainer.meta_train_step(batch_tasks)
            
            history['meta_loss'].append(metrics['meta_loss'])
            history['task_loss'].append(metrics['mean_task_loss'])
            
            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{num_epochs}: "
                    f"Meta-loss={metrics['meta_loss']:.4f}, "
                    f"Task-loss={metrics['mean_task_loss']:.4f}"
                )
        
        return history
    
    def adapt_to_regime(
        self,
        regime_data: Dict[str, torch.Tensor],
        num_steps: int = 5
    ):
        """
        Adapt to new market regime.
        
        Args:
            regime_data: Recent data from new regime
            num_steps: Number of adaptation steps
        """
        logger.info(f"Adapting to new regime with {len(regime_data['states'])} samples...")
        
        # Adapt policy
        self.current_policy = self.maml_trainer.adapt(
            regime_data['states'],
            regime_data['actions'],
            num_steps=num_steps
        )
        
        # Evaluate adaptation
        if 'query_states' in regime_data:
            metrics = self.maml_trainer.evaluate_adaptation(regime_data)
            logger.info(
                f"Adaptation complete: "
                f"Improvement={metrics['improvement_pct']:.1f}%"
            )
            
            self.regime_history.append(metrics)
    
    def get_action(self, state: np.ndarray) -> np.ndarray:
        """Get action from current (possibly adapted) policy."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            action = self.current_policy(state_tensor)
        
        return action.cpu().numpy()[0]


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("MAML TRADER DEMO")
    print("="*80)
    
    # Create trader
    trader = RegimeAdaptiveTrader(
        state_dim=10,
        action_dim=3,
        hidden_dim=64
    )
    
    # Generate dummy regime tasks
    logger.info("\n[1] Generating regime tasks...")
    regime_tasks = []
    for i in range(5):
        task = {
            'support_states': torch.randn(10, 10),
            'support_actions': torch.randn(10, 3),
            'query_states': torch.randn(10, 10),
            'query_actions': torch.randn(10, 3)
        }
        regime_tasks.append(task)
    
    # Meta-train
    logger.info("\n[2] Meta-training on regimes...")
    history = trader.meta_train(regime_tasks, num_epochs=50)
    
    logger.info(f"\nFinal meta-loss: {history['meta_loss'][-1]:.4f}")
    
    # Test adaptation
    logger.info("\n[3] Testing adaptation to new regime...")
    new_regime = {
        'states': torch.randn(10, 10),
        'actions': torch.randn(10, 3),
        'query_states': torch.randn(10, 10),
        'query_actions': torch.randn(10, 3)
    }
    
    trader.adapt_to_regime(new_regime, num_steps=5)
    
    # Get action
    logger.info("\n[4] Getting action from adapted policy...")
    state = np.random.randn(10)
    action = trader.get_action(state)
    logger.info(f"Action: {action}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
