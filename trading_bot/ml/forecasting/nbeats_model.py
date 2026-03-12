"""
N-BEATS (Neural Basis Expansion Analysis for Time Series)

Simple but powerful baseline for time series forecasting.
Paper: https://openreview.net/forum?id=r1ecqn4YwB

Used as baseline to compare against TFT performance.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import numpy as np
from typing import List, Optional, Tuple
import logging
import numpy

logger = logging.getLogger(__name__)


class NBeatsBlock(nn.Module):
    """Single N-BEATS block with basis expansion"""
    
    def __init__(
        self,
        input_size: int,
        theta_size: int,
        basis_function: nn.Module,
        layers: int = 4,
        layer_size: int = 256
    ):
        super().__init__()
        
        self.input_size = input_size
        self.theta_size = theta_size
        self.basis_function = basis_function
        
        # Fully connected stack
        fc_layers = []
        fc_layers.append(nn.Linear(input_size, layer_size))
        fc_layers.append(nn.ReLU())
        
        for _ in range(layers - 1):
            fc_layers.append(nn.Linear(layer_size, layer_size))
            fc_layers.append(nn.ReLU())
        
        self.fc_stack = nn.Sequential(*fc_layers)
        
        # Theta layers for backcast and forecast
        self.theta_b = nn.Linear(layer_size, theta_size)
        self.theta_f = nn.Linear(layer_size, theta_size)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            x: Input tensor [batch, input_size]
            
        Returns:
            Tuple of (backcast, forecast)
        """
        # Fully connected stack
        h = self.fc_stack(x)
        
        # Generate theta parameters
        theta_b = self.theta_b(h)
        theta_f = self.theta_f(h)
        
        # Apply basis functions
        backcast = self.basis_function(theta_b, is_forecast=False)
        forecast = self.basis_function(theta_f, is_forecast=True)
        
        return backcast, forecast


class GenericBasis(nn.Module):
    """Generic basis function (learned)"""
    
    def __init__(self, backcast_size: int, forecast_size: int):
        super().__init__()
        self.backcast_size = backcast_size
        self.forecast_size = forecast_size
    
    def forward(self, theta: torch.Tensor, is_forecast: bool) -> torch.Tensor:
        """
        Apply basis function
        
        Args:
            theta: Basis coefficients [batch, theta_size]
            is_forecast: Whether this is for forecast or backcast
            
        Returns:
            Expanded signal [batch, size]
        """
        if is_forecast:
            # Forecast: theta directly maps to forecast
            return theta[:, :self.forecast_size]
        else:
            # Backcast: theta directly maps to backcast
            return theta[:, :self.backcast_size]


class TrendBasis(nn.Module):
    """Trend basis function (polynomial)"""
    
    def __init__(self, backcast_size: int, forecast_size: int, degree: int = 3):
        super().__init__()
        self.backcast_size = backcast_size
        self.forecast_size = forecast_size
        self.degree = degree
        
        # Polynomial basis
        backcast_time = torch.arange(backcast_size, dtype=torch.float32) / backcast_size
        forecast_time = torch.arange(forecast_size, dtype=torch.float32) / forecast_size
        
        self.register_buffer('backcast_basis', self._polynomial_basis(backcast_time, degree))
        self.register_buffer('forecast_basis', self._polynomial_basis(forecast_time, degree))
    
    def _polynomial_basis(self, t: torch.Tensor, degree: int) -> torch.Tensor:
        """Create polynomial basis [time, degree+1]"""
        basis = torch.stack([t ** i for i in range(degree + 1)], dim=1)
        return basis
    
    def forward(self, theta: torch.Tensor, is_forecast: bool) -> torch.Tensor:
        """Apply polynomial basis"""
        if is_forecast:
            return torch.matmul(theta[:, :self.degree+1], self.forecast_basis.T)
        else:
            return torch.matmul(theta[:, :self.degree+1], self.backcast_basis.T)


class SeasonalityBasis(nn.Module):
    """Seasonality basis function (Fourier)"""
    
    def __init__(self, backcast_size: int, forecast_size: int, harmonics: int = 5):
        super().__init__()
        self.backcast_size = backcast_size
        self.forecast_size = forecast_size
        self.harmonics = harmonics
        
        # Fourier basis
        backcast_time = 2 * np.pi * torch.arange(backcast_size, dtype=torch.float32) / backcast_size
        forecast_time = 2 * np.pi * torch.arange(forecast_size, dtype=torch.float32) / forecast_size
        
        self.register_buffer('backcast_basis', self._fourier_basis(backcast_time, harmonics))
        self.register_buffer('forecast_basis', self._fourier_basis(forecast_time, harmonics))
    
    def _fourier_basis(self, t: torch.Tensor, harmonics: int) -> torch.Tensor:
        """Create Fourier basis [time, 2*harmonics]"""
        basis = []
        for i in range(1, harmonics + 1):
            basis.append(torch.cos(i * t))
            basis.append(torch.sin(i * t))
        return torch.stack(basis, dim=1)
    
    def forward(self, theta: torch.Tensor, is_forecast: bool) -> torch.Tensor:
        """Apply Fourier basis"""
        if is_forecast:
            return torch.matmul(theta[:, :2*self.harmonics], self.forecast_basis.T)
        else:
            return torch.matmul(theta[:, :2*self.harmonics], self.backcast_basis.T)


class NBeatsStack(nn.Module):
    """Stack of N-BEATS blocks"""
    
    def __init__(
        self,
        input_size: int,
        forecast_size: int,
        num_blocks: int,
        block_type: str = 'generic',
        **block_kwargs
    ):
        super().__init__()
        
        self.input_size = input_size
        self.forecast_size = forecast_size
        self.num_blocks = num_blocks
        
        # Create basis function
        if block_type == 'trend':
            basis_function = TrendBasis(input_size, forecast_size, degree=block_kwargs.get('degree', 3))
            theta_size = block_kwargs.get('degree', 3) + 1
        elif block_type == 'seasonality':
            basis_function = SeasonalityBasis(input_size, forecast_size, harmonics=block_kwargs.get('harmonics', 5))
            theta_size = 2 * block_kwargs.get('harmonics', 5)
        else:  # generic
            basis_function = GenericBasis(input_size, forecast_size)
            theta_size = max(input_size, forecast_size)
        
        # Create blocks
        self.blocks = nn.ModuleList([
            NBeatsBlock(
                input_size=input_size,
                theta_size=theta_size,
                basis_function=basis_function,
                layers=block_kwargs.get('layers', 4),
                layer_size=block_kwargs.get('layer_size', 256)
            )
            for _ in range(num_blocks)
        ])
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, List[torch.Tensor]]:
        """
        Forward pass through stack
        
        Args:
            x: Input [batch, input_size]
            
        Returns:
            Tuple of (stack_forecast, block_forecasts)
        """
        residual = x
        stack_forecast = torch.zeros(x.size(0), self.forecast_size, device=x.device)
        block_forecasts = []
        
        for block in self.blocks:
            backcast, forecast = block(residual)
            residual = residual - backcast
            stack_forecast = stack_forecast + forecast
            block_forecasts.append(forecast)
        
        return stack_forecast, block_forecasts


class NBeatsModel(nn.Module):
    """
    Complete N-BEATS model
    
    Architecture:
    - Trend stack (polynomial basis)
    - Seasonality stack (Fourier basis)
    - Generic stack (learned basis)
    """
    
    def __init__(
        self,
        input_size: int = 168,  # 1 week
        forecast_size: int = 24,  # 1 day
        num_stacks: int = 3,
        num_blocks_per_stack: int = 3,
        layer_size: int = 256,
        layers: int = 4
    ):
        super().__init__()
        
        self.input_size = input_size
        self.forecast_size = forecast_size
        
        # Create stacks
        self.stacks = nn.ModuleList()
        
        # Trend stack
        self.stacks.append(
            NBeatsStack(
                input_size=input_size,
                forecast_size=forecast_size,
                num_blocks=num_blocks_per_stack,
                block_type='trend',
                degree=3,
                layers=layers,
                layer_size=layer_size
            )
        )
        
        # Seasonality stack
        if num_stacks >= 2:
            self.stacks.append(
                NBeatsStack(
                    input_size=input_size,
                    forecast_size=forecast_size,
                    num_blocks=num_blocks_per_stack,
                    block_type='seasonality',
                    harmonics=5,
                    layers=layers,
                    layer_size=layer_size
                )
            )
        
        # Generic stacks
        for _ in range(max(0, num_stacks - 2)):
            self.stacks.append(
                NBeatsStack(
                    input_size=input_size,
                    forecast_size=forecast_size,
                    num_blocks=num_blocks_per_stack,
                    block_type='generic',
                    layers=layers,
                    layer_size=layer_size
                )
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input [batch, input_size]
            
        Returns:
            Forecast [batch, forecast_size]
        """
        forecast = torch.zeros(x.size(0), self.forecast_size, device=x.device)
        
        for stack in self.stacks:
            stack_forecast, _ = stack(x)
            forecast = forecast + stack_forecast
        
        return forecast
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        """
        Predict on numpy array
        
        Args:
            x: Input array [batch, input_size]
            
        Returns:
            Forecast array [batch, forecast_size]
        """
        self.eval()
        with torch.no_grad():
            x_tensor = torch.FloatTensor(x)
            forecast = self.forward(x_tensor)
            return forecast.cpu().numpy()


def train_nbeats(
    model: NBeatsModel,
    train_data: np.ndarray,
    train_targets: np.ndarray,
    val_data: Optional[np.ndarray] = None,
    val_targets: Optional[np.ndarray] = None,
    epochs: int = 100,
    batch_size: int = 128,
    learning_rate: float = 1e-3
) -> dict:
    """
    Train N-BEATS model
    
    Args:
        model: N-BEATS model
        train_data: Training inputs [n_samples, input_size]
        train_targets: Training targets [n_samples, forecast_size]
        val_data: Validation inputs
        val_targets: Validation targets
        epochs: Number of epochs
        batch_size: Batch size
        learning_rate: Learning rate
        
    Returns:
        Training history
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    history = {'train_loss': [], 'val_loss': []}
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        n_batches = 0
        
        # Training
        for i in range(0, len(train_data), batch_size):
            batch_x = torch.FloatTensor(train_data[i:i+batch_size])
            batch_y = torch.FloatTensor(train_targets[i:i+batch_size])
            
            optimizer.zero_grad()
            predictions = model(batch_x)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            n_batches += 1
        
        train_loss /= n_batches
        history['train_loss'].append(train_loss)
        
        # Validation
        if val_data is not None:
            model.eval()
            with torch.no_grad():
                val_x = torch.FloatTensor(val_data)
                val_y = torch.FloatTensor(val_targets)
                val_pred = model(val_x)
                val_loss = criterion(val_pred, val_y).item()
                history['val_loss'].append(val_loss)
        
        if (epoch + 1) % 10 == 0:
            log_msg = f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}"
            if val_data is not None:
                log_msg += f", Val Loss: {val_loss:.6f}"
            logger.info(log_msg)
    
    return history


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    input_size = 168
    forecast_size = 24
    n_samples = 1000
    
    X = np.random.randn(n_samples, input_size).astype(np.float32)
    y = np.random.randn(n_samples, forecast_size).astype(np.float32)
    
    # Split train/val
    split = int(0.8 * n_samples)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    # Create model
    model = NBeatsModel(
        input_size=input_size,
        forecast_size=forecast_size,
        num_stacks=3,
        num_blocks_per_stack=3,
        layer_size=128,
        layers=4
    )
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Train
    history = train_nbeats(
        model,
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=64
    )
    
    # Test prediction
    test_input = X_val[:10]
    predictions = model.predict(test_input)
    
    logger.info(f"\nPredictions shape: {predictions.shape}")
    logger.info(f"Final train loss: {history['train_loss'][-1]:.6f}")
    logger.info(f"Final val loss: {history['val_loss'][-1]:.6f}")
