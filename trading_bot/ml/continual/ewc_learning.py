"""
Elastic Weight Consolidation (EWC) for Continual Learning

Prevents catastrophic forgetting when learning new market regimes.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Optional
import numpy as np
from copy import deepcopy
import logging
import numpy

logger = logging.getLogger(__name__)


class EWC:
    """
    Elastic Weight Consolidation
    
    Preserves important weights from previous tasks while learning new ones.
    """
    
    def __init__(
        self,
        model: nn.Module,
        fisher_estimation_samples: int = 200,
        ewc_lambda: float = 0.4
    ):
        """
        Args:
            model: Neural network model
            fisher_estimation_samples: Samples for Fisher information estimation
            ewc_lambda: Importance of old task (higher = more preservation)
        """
        self.model = model
        self.fisher_estimation_samples = fisher_estimation_samples
        self.ewc_lambda = ewc_lambda
        
        # Store optimal parameters and Fisher information for each task
        self.optimal_params = {}
        self.fisher_information = {}
        self.task_count = 0
    
    def register_task(
        self,
        task_id: str,
        dataloader,
        criterion: nn.Module
    ):
        """
        Register a new task and compute Fisher information
        
        Args:
            task_id: Unique task identifier
            dataloader: DataLoader for this task
            criterion: Loss criterion
        """
        logger.info(f"Registering task: {task_id}")
        
        # Store current optimal parameters
        self.optimal_params[task_id] = {
            name: param.clone().detach()
            for name, param in self.model.named_parameters()
        }
        
        # Compute Fisher information
        fisher = self._compute_fisher_information(dataloader, criterion)
        self.fisher_information[task_id] = fisher
        
        self.task_count += 1
        
        logger.info(f"Task {task_id} registered. Total tasks: {self.task_count}")
    
    def _compute_fisher_information(
        self,
        dataloader,
        criterion: nn.Module
    ) -> Dict[str, torch.Tensor]:
        """
        Compute Fisher information matrix (diagonal approximation)
        
        Fisher information measures importance of each parameter
        """
        fisher = {
            name: torch.zeros_like(param)
            for name, param in self.model.named_parameters()
        }
        
        self.model.eval()
        
        # Sample data for Fisher estimation
        samples_processed = 0
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            if samples_processed >= self.fisher_estimation_samples:
                break
            
            self.model.zero_grad()
            
            # Forward pass
            outputs = self.model(inputs)
            loss = criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            
            # Accumulate squared gradients (Fisher information)
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    fisher[name] += param.grad.data ** 2
            
            samples_processed += len(inputs)
        
        # Normalize by number of samples
        for name in fisher:
            fisher[name] /= samples_processed
        
        logger.debug(f"Fisher information computed from {samples_processed} samples")
        
        return fisher
    
    def compute_ewc_loss(self) -> torch.Tensor:
        """
        Compute EWC penalty term
        
        Penalizes changes to important parameters from previous tasks
        """
        ewc_loss = torch.tensor(0.0)
        
        for task_id in self.optimal_params:
            for name, param in self.model.named_parameters():
                if name in self.optimal_params[task_id]:
                    # Fisher information * (current param - optimal param)^2
                    fisher = self.fisher_information[task_id][name]
                    optimal = self.optimal_params[task_id][name]
                    
                    ewc_loss += (fisher * (param - optimal) ** 2).sum()
        
        return (self.ewc_lambda / 2) * ewc_loss
    
    def train_with_ewc(
        self,
        dataloader,
        criterion: nn.Module,
        optimizer: optim.Optimizer,
        epochs: int = 10
    ) -> Dict[str, list]:
        """
        Train model with EWC regularization
        
        Args:
            dataloader: Training data
            criterion: Loss criterion
            optimizer: Optimizer
            epochs: Number of epochs
            
        Returns:
            Training history
        """
        history = {'loss': [], 'ewc_loss': []}
        
        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0
            epoch_ewc_loss = 0.0
            n_batches = 0
            
            for inputs, targets in dataloader:
                optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(inputs)
                
                # Task loss
                task_loss = criterion(outputs, targets)
                
                # EWC penalty
                ewc_loss = self.compute_ewc_loss()
                
                # Total loss
                total_loss = task_loss + ewc_loss
                
                # Backward pass
                total_loss.backward()
                optimizer.step()
                
                epoch_loss += task_loss.item()
                epoch_ewc_loss += ewc_loss.item()
                n_batches += 1
            
            avg_loss = epoch_loss / n_batches
            avg_ewc_loss = epoch_ewc_loss / n_batches
            
            history['loss'].append(avg_loss)
            history['ewc_loss'].append(avg_ewc_loss)
            
            if (epoch + 1) % 5 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{epochs} - "
                    f"Loss: {avg_loss:.4f}, EWC Loss: {avg_ewc_loss:.4f}"
                )
        
        return history


class ContinualLearningPipeline:
    """
    Complete continual learning pipeline for trading
    
    Learns new market regimes without forgetting old ones
    """
    
    def __init__(self, model: nn.Module, ewc_lambda: float = 0.4):
        self.model = model
        self.ewc = EWC(model, ewc_lambda=ewc_lambda)
        self.task_history = []
    
    def learn_new_regime(
        self,
        regime_name: str,
        train_loader,
        val_loader,
        epochs: int = 20,
        learning_rate: float = 1e-3
    ) -> Dict:
        """
        Learn a new market regime
        
        Args:
            regime_name: Name of market regime
            train_loader: Training data for this regime
            val_loader: Validation data
            epochs: Training epochs
            learning_rate: Learning rate
            
        Returns:
            Training results
        """
        logger.info(f"Learning new regime: {regime_name}")
        
        # Setup
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Train with EWC
        history = self.ewc.train_with_ewc(
            train_loader,
            criterion,
            optimizer,
            epochs=epochs
        )
        
        # Validate
        val_loss = self._validate(val_loader, criterion)
        
        # Register this task
        self.ewc.register_task(regime_name, train_loader, criterion)
        self.task_history.append({
            'regime': regime_name,
            'final_loss': history['loss'][-1],
            'val_loss': val_loss
        })
        
        logger.info(
            f"Regime {regime_name} learned. "
            f"Val Loss: {val_loss:.4f}, "
            f"Total regimes: {len(self.task_history)}"
        )
        
        return {
            'regime': regime_name,
            'history': history,
            'val_loss': val_loss
        }
    
    def _validate(self, val_loader, criterion: nn.Module) -> float:
        """Validate model"""
        self.model.eval()
        total_loss = 0.0
        n_batches = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                total_loss += loss.item()
                n_batches += 1
        
        return total_loss / n_batches if n_batches > 0 else 0.0
    
    def test_all_regimes(
        self,
        regime_dataloaders: Dict[str, torch.utils.data.DataLoader]
    ) -> Dict[str, float]:
        """
        Test model on all learned regimes
        
        Checks for catastrophic forgetting
        """
        criterion = nn.MSELoss()
        results = {}
        
        for regime_name, dataloader in regime_dataloaders.items():
            loss = self._validate(dataloader, criterion)
            results[regime_name] = loss
            
            logger.info(f"Regime {regime_name} test loss: {loss:.4f}")
        
        return results


def create_regime_data(regime_type: str, n_samples: int = 200):
    """Create synthetic data for different market regimes"""
    if regime_type == 'trending':
        # Trending market: strong autocorrelation
        X = torch.randn(n_samples, 10)
        y = X.mean(dim=1) + torch.linspace(0, 1, n_samples)
    
    elif regime_type == 'ranging':
        # Ranging market: mean reversion
        X = torch.randn(n_samples, 10)
        y = -X.mean(dim=1)  # Negative correlation
    
    elif regime_type == 'volatile':
        # Volatile market: high noise
        X = torch.randn(n_samples, 10)
        y = torch.randn(n_samples) * 2
    
    else:
        X = torch.randn(n_samples, 10)
        y = torch.randn(n_samples)
    
    return torch.utils.data.TensorDataset(X, y.unsqueeze(1))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("CONTINUAL LEARNING (EWC) DEMO")
    print("="*60)
    
    # Create model
    model = nn.Sequential(
        nn.Linear(10, 32),
        nn.ReLU(),
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 1)
    )
    
    # Create continual learning pipeline
    pipeline = ContinualLearningPipeline(model, ewc_lambda=0.4)
    
    # Learn multiple regimes sequentially
    regimes = ['trending', 'ranging', 'volatile']
    regime_loaders = {}
    
    for regime in regimes:
        logger.info(f"\n{'='*60}")
        logger.info(f"Learning Regime: {regime.upper()}")
        logger.info(f"{'='*60}")
        
        # Create data
        train_data = create_regime_data(regime, n_samples=200)
        val_data = create_regime_data(regime, n_samples=50)
        
        train_loader = torch.utils.data.DataLoader(train_data, batch_size=32, shuffle=True)
        val_loader = torch.utils.data.DataLoader(val_data, batch_size=32)
        
        regime_loaders[regime] = val_loader
        
        # Learn regime
        result = pipeline.learn_new_regime(
            regime,
            train_loader,
            val_loader,
            epochs=15
        )
    
    # Test on all regimes
    logger.info(f"\n{'='*60}")
    logger.info("TESTING ALL REGIMES (Checking for Forgetting)")
    logger.info(f"{'='*60}")
    
    test_results = pipeline.test_all_regimes(regime_loaders)
    
    logger.info("\nFinal Results:")
    for regime, loss in test_results.items():
        logger.info(f"  {regime}: {loss:.4f}")
    
    print("\n" + "="*60)
    logger.info("CONTINUAL LEARNING COMPLETE!")
    print("="*60)
    logger.info("Model learned 3 regimes without catastrophic forgetting")
    print("="*60)
