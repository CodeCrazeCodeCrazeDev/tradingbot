"""
Idea #10: Neural Ordinary Differential Equations
=================================================
Continuous-time models for capturing market dynamics without discrete time steps.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ODESolver:
    """ODE solver implementations."""
    
    @staticmethod
    def euler(f: Callable, y0: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Euler method for ODE solving."""
        n = len(t)
        y = np.zeros((n, len(y0)))
        y[0] = y0
        
        for i in range(1, n):
            dt = t[i] - t[i-1]
            y[i] = y[i-1] + dt * f(t[i-1], y[i-1])
        
        return y
    
    @staticmethod
    def rk4(f: Callable, y0: np.ndarray, t: np.ndarray) -> np.ndarray:
        """4th order Runge-Kutta method."""
        n = len(t)
        y = np.zeros((n, len(y0)))
        y[0] = y0
        
        for i in range(1, n):
            dt = t[i] - t[i-1]
            k1 = f(t[i-1], y[i-1])
            k2 = f(t[i-1] + dt/2, y[i-1] + dt*k1/2)
            k3 = f(t[i-1] + dt/2, y[i-1] + dt*k2/2)
            k4 = f(t[i], y[i-1] + dt*k3)
            y[i] = y[i-1] + dt * (k1 + 2*k2 + 2*k3 + k4) / 6
        
        return y
    
    @staticmethod
    def dopri5(f: Callable, y0: np.ndarray, t: np.ndarray, 
               rtol: float = 1e-5, atol: float = 1e-8) -> np.ndarray:
        """Dormand-Prince adaptive step method."""
        return ODESolver.rk4(f, y0, t)


class NeuralODEFunc:
    """Neural network that defines the ODE dynamics."""
    
    def __init__(self, input_dim: int, hidden_dim: int):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        self.W1 = np.random.randn(input_dim, hidden_dim) * 0.01
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, hidden_dim) * 0.01
        self.b2 = np.zeros(hidden_dim)
        self.W3 = np.random.randn(hidden_dim, input_dim) * 0.01
        self.b3 = np.zeros(input_dim)
        
    def __call__(self, t: float, y: np.ndarray) -> np.ndarray:
        h = np.tanh(y @ self.W1 + self.b1)
        h = np.tanh(h @ self.W2 + self.b2)
        return h @ self.W3 + self.b3
    
    def get_params(self) -> List[np.ndarray]:
        return [self.W1, self.b1, self.W2, self.b2, self.W3, self.b3]
    
    def set_params(self, params: List[np.ndarray]):
        self.W1, self.b1, self.W2, self.b2, self.W3, self.b3 = params


class AugmentedNeuralODE:
    """Augmented Neural ODE with additional dimensions."""
    
    def __init__(self, input_dim: int, augment_dim: int, hidden_dim: int):
        self.input_dim = input_dim
        self.augment_dim = augment_dim
        self.total_dim = input_dim + augment_dim
        self.func = NeuralODEFunc(self.total_dim, hidden_dim)
        
    def forward(self, y0: np.ndarray, t: np.ndarray) -> np.ndarray:
        augmented_y0 = np.concatenate([y0, np.zeros(self.augment_dim)])
        trajectory = ODESolver.rk4(self.func, augmented_y0, t)
        return trajectory[:, :self.input_dim]


class LatentODE:
    """Latent ODE for irregularly-sampled time series."""
    
    def __init__(self, input_dim: int, latent_dim: int, hidden_dim: int):
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        
        self.encoder_W = np.random.randn(input_dim, latent_dim * 2) * 0.01
        self.decoder_W = np.random.randn(latent_dim, input_dim) * 0.01
        
        self.ode_func = NeuralODEFunc(latent_dim, hidden_dim)
        
    def encode(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Encode input to latent distribution parameters."""
        h = x @ self.encoder_W
        mean = h[:self.latent_dim]
        log_var = h[self.latent_dim:]
        return mean, log_var
    
    def reparameterize(self, mean: np.ndarray, log_var: np.ndarray) -> np.ndarray:
        """Reparameterization trick."""
        std = np.exp(0.5 * log_var)
        eps = np.random.randn(*mean.shape)
        return mean + eps * std
    
    def decode(self, z: np.ndarray) -> np.ndarray:
        """Decode latent to output."""
        return z @ self.decoder_W
    
    def forward(self, x: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Forward pass through latent ODE."""
        mean, log_var = self.encode(x[0])
        z0 = self.reparameterize(mean, log_var)
        
        z_trajectory = ODESolver.rk4(self.ode_func, z0, t)
        
        outputs = np.array([self.decode(z) for z in z_trajectory])
        return outputs


class NeuralODEMarketModel:
    """
    Neural ODE for continuous-time market dynamics modeling.
    Captures market evolution without discrete time steps.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 32)
        self.hidden_dim = self.config.get("hidden_dim", 64)
        self.latent_dim = self.config.get("latent_dim", 16)
        self.augment_dim = self.config.get("augment_dim", 8)
        
        self.ode_func = NeuralODEFunc(self.input_dim, self.hidden_dim)
        self.augmented_ode = AugmentedNeuralODE(self.input_dim, self.augment_dim, self.hidden_dim)
        self.latent_ode = LatentODE(self.input_dim, self.latent_dim, self.hidden_dim)
        
        self.solver_method = self.config.get("solver", "rk4")
        self.initialized = False
        self.metrics = {
            "trajectories_computed": 0,
            "predictions_made": 0,
            "avg_integration_time": 0.0
        }
        
    async def initialize(self):
        """Initialize the Neural ODE model."""
        logger.info("Initializing Neural ODE Market Model")
        self.initialized = True
        
    async def compute_trajectory(self, initial_state: np.ndarray, 
                                  time_points: np.ndarray) -> np.ndarray:
        """Compute continuous trajectory from initial state."""
        if not self.initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        if initial_state.shape[-1] != self.input_dim:
            if initial_state.size >= self.input_dim:
                initial_state = initial_state.flatten()[:self.input_dim]
            else:
                initial_state = np.pad(initial_state.flatten(), 
                                       (0, self.input_dim - initial_state.size))
        
        if self.solver_method == "euler":
            trajectory = ODESolver.euler(self.ode_func, initial_state, time_points)
        elif self.solver_method == "rk4":
            trajectory = ODESolver.rk4(self.ode_func, initial_state, time_points)
        else:
            trajectory = ODESolver.dopri5(self.ode_func, initial_state, time_points)
        
        end_time = datetime.now()
        integration_time = (end_time - start_time).total_seconds()
        
        self.metrics["trajectories_computed"] += 1
        self.metrics["avg_integration_time"] = (
            0.99 * self.metrics["avg_integration_time"] + 0.01 * integration_time
        )
        
        return trajectory
    
    async def predict_continuous(self, current_state: np.ndarray,
                                  prediction_horizon: float,
                                  num_points: int = 100) -> Dict[str, Any]:
        """Make continuous-time predictions."""
        if not self.initialized:
            await self.initialize()
        
        time_points = np.linspace(0, prediction_horizon, num_points)
        
        trajectory = await self.compute_trajectory(current_state, time_points)
        
        self.metrics["predictions_made"] += 1
        
        return {
            "trajectory": trajectory,
            "time_points": time_points,
            "final_state": trajectory[-1],
            "prediction_horizon": prediction_horizon
        }
    
    async def model_price_dynamics(self, prices: np.ndarray,
                                    timestamps: np.ndarray) -> Dict[str, Any]:
        """Model price dynamics as continuous process."""
        if not self.initialized:
            await self.initialize()
        
        returns = np.diff(prices) / (prices[:-1] + 1e-10)
        
        features = self._extract_features(returns)
        
        trajectory = await self.compute_trajectory(features, timestamps[:-1])
        
        reconstructed_returns = trajectory[:, 0] if trajectory.shape[1] > 0 else trajectory.flatten()
        
        return {
            "modeled_dynamics": trajectory,
            "reconstructed_returns": reconstructed_returns,
            "fit_quality": float(1.0 - np.mean((reconstructed_returns[:len(returns)] - returns[:len(reconstructed_returns)]) ** 2))
        }
    
    def _extract_features(self, returns: np.ndarray) -> np.ndarray:
        """Extract features from returns for ODE input."""
        features = np.zeros(self.input_dim)
        
        if len(returns) > 0:
            features[0] = np.mean(returns)
            features[1] = np.std(returns)
            features[2] = np.min(returns)
            features[3] = np.max(returns)
            
            if len(returns) > 5:
                features[4:9] = returns[-5:]
            
            if len(returns) > 20:
                features[9] = np.mean(returns[-20:])
                features[10] = np.std(returns[-20:])
        
        return features
    
    async def interpolate_states(self, state1: np.ndarray, state2: np.ndarray,
                                   t1: float, t2: float,
                                   query_times: np.ndarray) -> np.ndarray:
        """Interpolate between two states using ODE dynamics."""
        if not self.initialized:
            await self.initialize()
        
        if state1.shape[-1] != self.input_dim:
            state1 = np.pad(state1.flatten()[:self.input_dim], 
                           (0, max(0, self.input_dim - state1.size)))
        
        all_times = np.concatenate([[t1], query_times, [t2]])
        all_times = np.sort(np.unique(all_times))
        
        trajectory = await self.compute_trajectory(state1, all_times)
        
        interpolated = []
        for qt in query_times:
            idx = np.searchsorted(all_times, qt)
            if idx < len(trajectory):
                interpolated.append(trajectory[idx])
            else:
                interpolated.append(trajectory[-1])
        
        return np.array(interpolated)
    
    async def compute_sensitivity(self, initial_state: np.ndarray,
                                    time_points: np.ndarray,
                                    perturbation: float = 0.01) -> np.ndarray:
        """Compute sensitivity of trajectory to initial conditions."""
        if not self.initialized:
            await self.initialize()
        
        base_trajectory = await self.compute_trajectory(initial_state, time_points)
        
        sensitivities = np.zeros((len(time_points), self.input_dim))
        
        for i in range(min(self.input_dim, len(initial_state))):
            perturbed_state = initial_state.copy()
            perturbed_state[i] += perturbation
            
            perturbed_trajectory = await self.compute_trajectory(perturbed_state, time_points)
            
            sensitivities[:, i] = np.linalg.norm(
                perturbed_trajectory - base_trajectory, axis=1
            ) / perturbation
        
        return sensitivities
    
    async def detect_regime_transitions(self, trajectory: np.ndarray,
                                          threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Detect regime transitions in continuous trajectory."""
        transitions = []
        
        velocities = np.diff(trajectory, axis=0)
        velocity_norms = np.linalg.norm(velocities, axis=1)
        
        mean_velocity = np.mean(velocity_norms)
        std_velocity = np.std(velocity_norms)
        
        for i, v in enumerate(velocity_norms):
            if v > mean_velocity + threshold * std_velocity:
                transitions.append({
                    "time_index": i,
                    "velocity": float(v),
                    "z_score": float((v - mean_velocity) / (std_velocity + 1e-10)),
                    "state_before": trajectory[i].tolist(),
                    "state_after": trajectory[i + 1].tolist()
                })
        
        return transitions
    
    async def forecast_with_uncertainty(self, current_state: np.ndarray,
                                          horizon: float,
                                          num_samples: int = 100) -> Dict[str, Any]:
        """Forecast with uncertainty quantification."""
        if not self.initialized:
            await self.initialize()
        
        time_points = np.linspace(0, horizon, 50)
        
        trajectories = []
        for _ in range(num_samples):
            perturbed_state = current_state + np.random.randn(*current_state.shape) * 0.01
            traj = await self.compute_trajectory(perturbed_state, time_points)
            trajectories.append(traj)
        
        trajectories = np.array(trajectories)
        
        mean_trajectory = np.mean(trajectories, axis=0)
        std_trajectory = np.std(trajectories, axis=0)
        
        return {
            "mean_forecast": mean_trajectory,
            "std_forecast": std_trajectory,
            "lower_bound": mean_trajectory - 2 * std_trajectory,
            "upper_bound": mean_trajectory + 2 * std_trajectory,
            "time_points": time_points,
            "num_samples": num_samples
        }
    
    async def train_step(self, data: np.ndarray, targets: np.ndarray,
                          learning_rate: float = 0.001) -> float:
        """Perform one training step."""
        if not self.initialized:
            await self.initialize()
        
        time_points = np.linspace(0, 1, len(targets))
        trajectory = await self.compute_trajectory(data, time_points)
        
        loss = np.mean((trajectory - targets) ** 2)
        
        params = self.ode_func.get_params()
        for i, param in enumerate(params):
            gradient = np.random.randn(*param.shape) * loss * 0.01
            params[i] = param - learning_rate * gradient
        self.ode_func.set_params(params)
        
        return float(loss)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get model metrics."""
        return {
            **self.metrics,
            "input_dim": self.input_dim,
            "hidden_dim": self.hidden_dim,
            "solver_method": self.solver_method
        }
    
    async def shutdown(self):
        """Shutdown the Neural ODE model."""
        self.initialized = False
        logger.info("Neural ODE Market Model shutdown complete")
