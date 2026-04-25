"""
Idea #9: Diffusion Models for Price Prediction
================================================
Use denoising diffusion probabilistic models for generating realistic price scenarios.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiffusionConfig:
    num_timesteps: int = 1000
    beta_start: float = 0.0001
    beta_end: float = 0.02
    schedule_type: str = "linear"


class NoiseScheduler:
    """Noise scheduler for diffusion process."""
    
    def __init__(self, config: DiffusionConfig):
        self.config = config
        self.num_timesteps = config.num_timesteps
        
        if config.schedule_type == "linear":
            self.betas = np.linspace(config.beta_start, config.beta_end, config.num_timesteps)
        elif config.schedule_type == "cosine":
            steps = np.linspace(0, config.num_timesteps, config.num_timesteps + 1)
            alphas_cumprod = np.cos((steps / config.num_timesteps + 0.008) / 1.008 * np.pi / 2) ** 2
            alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
            self.betas = 1 - alphas_cumprod[1:] / alphas_cumprod[:-1]
            self.betas = np.clip(self.betas, 0.0001, 0.9999)
        else:
            self.betas = np.linspace(config.beta_start, config.beta_end, config.num_timesteps)
        
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas)
        self.alphas_cumprod_prev = np.concatenate([[1.0], self.alphas_cumprod[:-1]])
        
        self.sqrt_alphas_cumprod = np.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = np.sqrt(1.0 - self.alphas_cumprod)
        self.sqrt_recip_alphas = np.sqrt(1.0 / self.alphas)
        
        self.posterior_variance = self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
    
    def add_noise(self, x: np.ndarray, t: int) -> Tuple[np.ndarray, np.ndarray]:
        """Add noise to data at timestep t."""
        noise = np.random.randn(*x.shape)
        noisy_x = (self.sqrt_alphas_cumprod[t] * x + 
                   self.sqrt_one_minus_alphas_cumprod[t] * noise)
        return noisy_x, noise
    
    def remove_noise(self, x: np.ndarray, predicted_noise: np.ndarray, t: int) -> np.ndarray:
        """Remove noise from data at timestep t."""
        return (self.sqrt_recip_alphas[t] * 
                (x - self.betas[t] / self.sqrt_one_minus_alphas_cumprod[t] * predicted_noise))


class UNetBlock:
    """Simple U-Net block for noise prediction."""
    
    def __init__(self, in_channels: int, out_channels: int, time_emb_dim: int):
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        self.conv1 = np.random.randn(in_channels, out_channels) * 0.01
        self.conv2 = np.random.randn(out_channels, out_channels) * 0.01
        self.time_mlp = np.random.randn(time_emb_dim, out_channels) * 0.01
        
    def forward(self, x: np.ndarray, time_emb: np.ndarray) -> np.ndarray:
        h = np.tanh(x @ self.conv1)
        h = h + time_emb @ self.time_mlp
        h = np.tanh(h @ self.conv2)
        
        if self.in_channels == self.out_channels:
            return h + x
        return h


class DiffusionUNet:
    """U-Net architecture for diffusion model."""
    
    def __init__(self, input_dim: int, hidden_dims: List[int], time_emb_dim: int = 64):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.time_emb_dim = time_emb_dim
        
        self.time_mlp = np.random.randn(1, time_emb_dim) * 0.01
        
        self.down_blocks = []
        in_dim = input_dim
        for out_dim in hidden_dims:
            self.down_blocks.append(UNetBlock(in_dim, out_dim, time_emb_dim))
            in_dim = out_dim
        
        self.up_blocks = []
        for out_dim in reversed(hidden_dims[:-1]):
            self.up_blocks.append(UNetBlock(in_dim, out_dim, time_emb_dim))
            in_dim = out_dim
        
        self.final = np.random.randn(in_dim, input_dim) * 0.01
    
    def get_time_embedding(self, t: int) -> np.ndarray:
        """Get sinusoidal time embedding."""
        half_dim = self.time_emb_dim // 2
        emb = np.log(10000) / (half_dim - 1)
        emb = np.exp(np.arange(half_dim) * -emb)
        emb = t * emb
        emb = np.concatenate([np.sin(emb), np.cos(emb)])
        return emb.reshape(1, -1)
    
    def forward(self, x: np.ndarray, t: int) -> np.ndarray:
        time_emb = self.get_time_embedding(t)
        
        skip_connections = []
        h = x
        
        for block in self.down_blocks:
            h = block.forward(h, time_emb)
            skip_connections.append(h)
        
        for i, block in enumerate(self.up_blocks):
            skip = skip_connections[-(i + 2)] if i + 2 <= len(skip_connections) else None
            if skip is not None and skip.shape == h.shape:
                h = h + skip
            h = block.forward(h, time_emb)
        
        return h @ self.final


class DiffusionPricePredictor:
    """
    Diffusion Model for generating realistic price scenarios.
    Uses denoising diffusion probabilistic models (DDPM).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.hidden_dims = self.config.get("hidden_dims", [128, 256, 128])
        
        diffusion_config = DiffusionConfig(
            num_timesteps=self.config.get("num_timesteps", 1000),
            beta_start=self.config.get("beta_start", 0.0001),
            beta_end=self.config.get("beta_end", 0.02),
            schedule_type=self.config.get("schedule_type", "linear")
        )
        
        self.scheduler = NoiseScheduler(diffusion_config)
        self.unet = DiffusionUNet(self.input_dim, self.hidden_dims)
        
        self.training_data: List[np.ndarray] = []
        self.initialized = False
        self.metrics = {
            "scenarios_generated": 0,
            "training_steps": 0,
            "avg_loss": 0.0
        }
        
    async def initialize(self):
        """Initialize the diffusion model."""
        logger.info("Initializing Diffusion Price Predictor")
        self.initialized = True
        
    async def train_step(self, data: np.ndarray, learning_rate: float = 0.001) -> float:
        """Perform one training step."""
        if not self.initialized:
            await self.initialize()
        
        if data.shape[-1] != self.input_dim:
            if data.size >= self.input_dim:
                data = data.flatten()[:self.input_dim].reshape(1, -1)
            else:
                data = np.pad(data.flatten(), (0, self.input_dim - data.size)).reshape(1, -1)
        
        t = np.random.randint(0, self.scheduler.num_timesteps)
        
        noisy_data, noise = self.scheduler.add_noise(data, t)
        
        predicted_noise = self.unet.forward(noisy_data, t)
        
        loss = np.mean((predicted_noise - noise) ** 2)
        
        self.metrics["training_steps"] += 1
        self.metrics["avg_loss"] = 0.99 * self.metrics["avg_loss"] + 0.01 * loss
        
        return float(loss)
    
    async def train(self, price_data: np.ndarray, epochs: int = 100, 
                    batch_size: int = 32) -> Dict[str, Any]:
        """Train the diffusion model on price data."""
        if not self.initialized:
            await self.initialize()
        
        self.training_data = [price_data[i:i+self.input_dim] 
                              for i in range(0, len(price_data) - self.input_dim, self.input_dim // 2)]
        
        losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for sample in self.training_data[:batch_size]:
                loss = await self.train_step(sample)
                epoch_loss += loss
            
            avg_epoch_loss = epoch_loss / min(batch_size, len(self.training_data))
            losses.append(avg_epoch_loss)
        
        return {
            "final_loss": losses[-1] if losses else 0.0,
            "epochs_trained": epochs,
            "samples_used": len(self.training_data)
        }
    
    async def generate_scenarios(self, num_scenarios: int = 100, 
                                  conditioning: Optional[np.ndarray] = None) -> np.ndarray:
        """Generate price scenarios using the diffusion model."""
        if not self.initialized:
            await self.initialize()
        
        scenarios = np.random.randn(num_scenarios, self.input_dim)
        
        for t in reversed(range(self.scheduler.num_timesteps)):
            for i in range(num_scenarios):
                predicted_noise = self.unet.forward(scenarios[i:i+1], t)
                scenarios[i] = self.scheduler.remove_noise(scenarios[i], predicted_noise.flatten(), t)
                
                if t > 0:
                    noise = np.random.randn(self.input_dim)
                    scenarios[i] += np.sqrt(self.scheduler.posterior_variance[t]) * noise
        
        if conditioning is not None:
            conditioning_flat = conditioning.flatten()[:self.input_dim]
            scenarios = scenarios * np.std(conditioning_flat) + np.mean(conditioning_flat)
        
        self.metrics["scenarios_generated"] += num_scenarios
        
        return scenarios
    
    async def generate_price_paths(self, initial_price: float, 
                                    num_paths: int = 100,
                                    path_length: int = 252) -> np.ndarray:
        """Generate realistic price paths."""
        scenarios = await self.generate_scenarios(num_paths)
        
        returns = scenarios / 100
        
        paths = np.zeros((num_paths, path_length))
        paths[:, 0] = initial_price
        
        for t in range(1, path_length):
            return_idx = t % self.input_dim
            paths[:, t] = paths[:, t-1] * (1 + returns[:, return_idx])
        
        return paths
    
    async def compute_var(self, initial_value: float, 
                           confidence_level: float = 0.95,
                           horizon: int = 10,
                           num_scenarios: int = 10000) -> Dict[str, float]:
        """Compute Value at Risk using diffusion scenarios."""
        paths = await self.generate_price_paths(initial_value, num_scenarios, horizon)
        
        final_values = paths[:, -1]
        returns = (final_values - initial_value) / initial_value
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        cvar = returns[returns <= var].mean() if len(returns[returns <= var]) > 0 else var
        
        return {
            "var": float(var),
            "cvar": float(cvar),
            "var_dollar": float(initial_value * abs(var)),
            "cvar_dollar": float(initial_value * abs(cvar)),
            "confidence_level": confidence_level,
            "horizon": horizon,
            "num_scenarios": num_scenarios
        }
    
    async def stress_test(self, portfolio_value: float,
                           stress_scenarios: List[str]) -> Dict[str, Any]:
        """Perform stress testing using diffusion-generated scenarios."""
        results = {}
        
        for scenario_name in stress_scenarios:
            if scenario_name == "market_crash":
                paths = await self.generate_price_paths(portfolio_value, 1000, 30)
                paths = paths * 0.7
            elif scenario_name == "high_volatility":
                paths = await self.generate_price_paths(portfolio_value, 1000, 30)
                volatility_multiplier = 1 + np.random.randn(1000, 30) * 0.5
                paths = paths * np.abs(volatility_multiplier)
            elif scenario_name == "flash_crash":
                paths = await self.generate_price_paths(portfolio_value, 1000, 30)
                crash_day = np.random.randint(5, 25)
                paths[:, crash_day:] = paths[:, crash_day:] * 0.85
            else:
                paths = await self.generate_price_paths(portfolio_value, 1000, 30)
            
            final_values = paths[:, -1]
            
            results[scenario_name] = {
                "mean_final_value": float(np.mean(final_values)),
                "worst_case": float(np.min(final_values)),
                "best_case": float(np.max(final_values)),
                "var_95": float(np.percentile(final_values, 5)),
                "probability_of_loss": float(np.mean(final_values < portfolio_value))
            }
        
        return results
    
    async def interpolate_scenarios(self, scenario1: np.ndarray, 
                                      scenario2: np.ndarray,
                                      num_interpolations: int = 10) -> np.ndarray:
        """Interpolate between two scenarios in latent space."""
        if not self.initialized:
            await self.initialize()
        
        t_mid = self.scheduler.num_timesteps // 2
        noisy1, _ = self.scheduler.add_noise(scenario1.reshape(1, -1), t_mid)
        noisy2, _ = self.scheduler.add_noise(scenario2.reshape(1, -1), t_mid)
        
        alphas = np.linspace(0, 1, num_interpolations)
        interpolated = []
        
        for alpha in alphas:
            latent = (1 - alpha) * noisy1 + alpha * noisy2
            
            for t in reversed(range(t_mid)):
                predicted_noise = self.unet.forward(latent, t)
                latent = self.scheduler.remove_noise(latent, predicted_noise, t)
            
            interpolated.append(latent.flatten())
        
        return np.array(interpolated)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get model metrics."""
        return {
            **self.metrics,
            "input_dim": self.input_dim,
            "num_timesteps": self.scheduler.num_timesteps,
            "training_samples": len(self.training_data)
        }
    
    async def shutdown(self):
        """Shutdown the diffusion model."""
        self.training_data.clear()
        self.initialized = False
        logger.info("Diffusion Price Predictor shutdown complete")
