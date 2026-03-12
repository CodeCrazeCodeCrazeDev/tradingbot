"""
MAML (Model-Agnostic Meta-Learning) for Fast Adaptation

Based on: "Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks"
arXiv: https://arxiv.org/abs/1703.03400

Enables fast adaptation to new market regimes with few gradient steps.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Optional, Tuple
import numpy as np
from copy import deepcopy
import logging
import numpy

logger = logging.getLogger(__name__)


class TradingPolicy(nn.Module):
    """Simple trading policy network"""
    
    def __init__(self, input_dim: int = 50, hidden_dim: int = 128, output_dim: int = 3):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Softmax(dim=-1)
        )
    
    def forward(self, x):
        return self.network(x)


class MAML:
    """
    MAML for trading strategy adaptation
    
    Meta-trains on multiple market days to learn initialization
    that can quickly adapt to new market conditions.
    """
    
    def __init__(
        self,
        model: nn.Module,
        inner_lr: float = 0.01,
        outer_lr: float = 0.001,
        inner_steps: int = 10,
        meta_batch_size: int = 16
    ):
        """
        Args:
            model: Base model to meta-train
            inner_lr: Learning rate for inner loop (task adaptation)
            outer_lr: Learning rate for outer loop (meta-update)
            inner_steps: Number of gradient steps in inner loop
            meta_batch_size: Number of tasks per meta-batch
        """
        self.model = model
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.inner_steps = inner_steps
        self.meta_batch_size = meta_batch_size
        
        self.meta_optimizer = optim.Adam(self.model.parameters(), lr=outer_lr)
        self.loss_fn = nn.CrossEntropyLoss()
    
    def inner_loop(
        self,
        task_data: Tuple[torch.Tensor, torch.Tensor],
        model: nn.Module
    ) -> nn.Module:
        """
        Inner loop: Adapt model to specific task
        
        Args:
            task_data: Tuple of (features, labels) for this task
            model: Model to adapt
            
        Returns:
            Adapted model
        """
        features, labels = task_data
        
        # Clone model for adaptation
        adapted_model = deepcopy(model)
        optimizer = optim.SGD(adapted_model.parameters(), lr=self.inner_lr)
        
        # Adaptation steps
        for _ in range(self.inner_steps):
            optimizer.zero_grad()
            predictions = adapted_model(features)
            loss = self.loss_fn(predictions, labels)
            loss.backward()
            optimizer.step()
        
        return adapted_model
    
    def meta_train_step(
        self,
        tasks: List[Tuple[torch.Tensor, torch.Tensor]]
    ) -> float:
        """
        Single meta-training step
        
        Args:
            tasks: List of tasks, each is (support_data, query_data)
            
        Returns:
            Meta-loss
        """
        meta_loss = 0.0
        
        # Sample meta-batch of tasks
        batch_tasks = np.random.choice(len(tasks), self.meta_batch_size, replace=False)
        
        for task_idx in batch_tasks:
            support_data, query_data = tasks[task_idx]
            
            # Inner loop: adapt to support set
            adapted_model = self.inner_loop(support_data, self.model)
            
            # Evaluate on query set
            query_features, query_labels = query_data
            predictions = adapted_model(query_features)
            task_loss = self.loss_fn(predictions, query_labels)
            
            meta_loss += task_loss
        
        # Meta-update
        meta_loss = meta_loss / self.meta_batch_size
        
        self.meta_optimizer.zero_grad()
        meta_loss.backward()
        self.meta_optimizer.step()
        
        return meta_loss.item()
    
    def meta_train(
        self,
        tasks: List[Tuple[torch.Tensor, torch.Tensor]],
        epochs: int = 100,
        validation_tasks: Optional[List] = None
    ) -> Dict[str, List[float]]:
        """
        Meta-training loop
        
        Args:
            tasks: List of training tasks
            epochs: Number of meta-training epochs
            validation_tasks: Optional validation tasks
            
        Returns:
            Training history
        """
        history = {'train_loss': [], 'val_loss': []}
        
        for epoch in range(epochs):
            # Meta-training
            train_loss = self.meta_train_step(tasks)
            history['train_loss'].append(train_loss)
            
            # Validation
            if validation_tasks:
                val_loss = self.meta_validate(validation_tasks)
                history['val_loss'].append(val_loss)
            
            if (epoch + 1) % 10 == 0:
                log_msg = f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}"
                if validation_tasks:
                    log_msg += f", Val Loss: {val_loss:.4f}"
                logger.info(log_msg)
        
        return history
    
    def meta_validate(
        self,
        validation_tasks: List[Tuple[torch.Tensor, torch.Tensor]]
    ) -> float:
        """Validate on held-out tasks"""
        total_loss = 0.0
        
        with torch.no_grad():
            for support_data, query_data in validation_tasks:
                # Adapt to support set
                adapted_model = self.inner_loop(support_data, self.model)
                
                # Evaluate on query set
                query_features, query_labels = query_data
                predictions = adapted_model(query_features)
                loss = self.loss_fn(predictions, query_labels)
                
                total_loss += loss.item()
        
        return total_loss / len(validation_tasks)
    
    def fast_adapt(
        self,
        new_data: Tuple[torch.Tensor, torch.Tensor],
        steps: Optional[int] = None
    ) -> nn.Module:
        """
        Fast adaptation to new market conditions
        
        Args:
            new_data: Recent market data (features, labels)
            steps: Number of adaptation steps (default: self.inner_steps)
            
        Returns:
            Adapted model
        """
        if steps is None:
            steps = self.inner_steps
        
        features, labels = new_data
        
        # Clone meta-learned model
        adapted_model = deepcopy(self.model)
        optimizer = optim.SGD(adapted_model.parameters(), lr=self.inner_lr)
        
        # Fast adaptation
        for step in range(steps):
            optimizer.zero_grad()
            predictions = adapted_model(features)
            loss = self.loss_fn(predictions, labels)
            loss.backward()
            optimizer.step()
            
            if step == 0 or step == steps - 1:
                logger.debug(f"Adaptation step {step+1}: loss {loss.item():.4f}")
        
        logger.info(f"Fast adaptation complete in {steps} steps")
        
        return adapted_model


class FastAdaptationPipeline:
    """
    Pipeline for fast adaptation at market open
    
    Process:
    1. At market open: collect last 2 hours of data
    2. Fine-tune meta-policy with 10 gradient steps
    3. Use adapted policy for current day
    4. Re-adapt every 4 hours
    """
    
    def __init__(self, maml: MAML, adaptation_interval_hours: int = 4):
        self.maml = maml
        self.adaptation_interval_hours = adaptation_interval_hours
        self.current_policy = None
        self.last_adaptation_time = None
    
    def should_adapt(self, current_time) -> bool:
        """Check if it's time to re-adapt"""
        if self.last_adaptation_time is None:
            return True
        
        hours_since_adaptation = (current_time - self.last_adaptation_time).total_seconds() / 3600
        return hours_since_adaptation >= self.adaptation_interval_hours
    
    def adapt_to_current_market(
        self,
        recent_data: Tuple[torch.Tensor, torch.Tensor],
        current_time
    ) -> nn.Module:
        """Adapt policy to current market conditions"""
        logger.info(f"Adapting policy at {current_time}")
        
        # Fast adaptation
        self.current_policy = self.maml.fast_adapt(recent_data)
        self.last_adaptation_time = current_time
        
        return self.current_policy
    
    def get_current_policy(self) -> nn.Module:
        """Get current adapted policy"""
        if self.current_policy is None:
            return self.maml.model
        return self.current_policy


def create_sample_tasks(n_tasks: int = 100, n_samples_per_task: int = 100) -> List:
    """Create sample tasks for testing"""
    tasks = []
    
    for _ in range(n_tasks):
        # Support set (for adaptation)
        support_features = torch.randn(n_samples_per_task, 50)
        support_labels = torch.randint(0, 3, (n_samples_per_task,))
        
        # Query set (for evaluation)
        query_features = torch.randn(n_samples_per_task, 50)
        query_labels = torch.randint(0, 3, (n_samples_per_task,))
        
        tasks.append(((support_features, support_labels), (query_features, query_labels)))
    
    return tasks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create model
    model = TradingPolicy(input_dim=50, hidden_dim=128, output_dim=3)
    
    # Create MAML
    maml = MAML(
        model=model,
        inner_lr=0.01,
        outer_lr=0.001,
        inner_steps=10,
        meta_batch_size=16
    )
    
    # Create sample tasks
    logger.info("Creating sample tasks...")
    train_tasks = create_sample_tasks(n_tasks=80)
    val_tasks = create_sample_tasks(n_tasks=20)
    
    # Meta-train
    logger.info("Meta-training...")
    history = maml.meta_train(
        tasks=train_tasks,
        epochs=50,
        validation_tasks=val_tasks
    )
    
    # Test fast adaptation
    logger.info("\nTesting fast adaptation...")
    new_task_data = (torch.randn(100, 50), torch.randint(0, 3, (100,)))
    adapted_model = maml.fast_adapt(new_task_data, steps=10)
    
    print("\n" + "="*60)
    logger.info("MAML Meta-Learning Complete!")
    print("="*60)
    logger.info(f"Final train loss: {history['train_loss'][-1]:.4f}")
    logger.info(f"Final val loss: {history['val_loss'][-1]:.4f}")
    logger.info(f"Model adapted successfully to new task")
    print("="*60)
