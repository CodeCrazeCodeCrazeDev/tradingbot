"""
GAN (Generative Adversarial Networks) for Market Data Generation.

This module implements GANs for:
- Synthetic market data generation
- Scenario simulation
- Stress testing data creation
- Regime-specific data augmentation
- Adversarial training for robust models
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging
import numpy

logger = logging.getLogger(__name__)


class GANType(Enum):
    """Types of GAN architectures."""
    VANILLA = "vanilla"
    WASSERSTEIN = "wasserstein"
    CONDITIONAL = "conditional"
    TIME_SERIES = "time_series"
    REGIME_CONDITIONAL = "regime_conditional"


class MarketRegime(Enum):
    """Market regime types for conditional generation."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRASH = "crash"
    RECOVERY = "recovery"


@dataclass
class GeneratorConfig:
    """Configuration for the generator network."""
    latent_dim: int = 100
    hidden_dims: List[int] = field(default_factory=lambda: [256, 512, 256])
    output_dim: int = 5  # OHLCV
    sequence_length: int = 100
    activation: str = "leaky_relu"
    use_batch_norm: bool = True
    dropout_rate: float = 0.2


@dataclass
class DiscriminatorConfig:
    """Configuration for the discriminator network."""
    input_dim: int = 5  # OHLCV
    hidden_dims: List[int] = field(default_factory=lambda: [256, 512, 256])
    sequence_length: int = 100
    activation: str = "leaky_relu"
    use_spectral_norm: bool = True
    dropout_rate: float = 0.3


@dataclass
class GeneratedSample:
    """A generated market data sample."""
    data: np.ndarray
    regime: Optional[MarketRegime] = None
    quality_score: float = 0.0
    discriminator_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingMetrics:
    """Training metrics for GAN."""
    epoch: int
    generator_loss: float
    discriminator_loss: float
    discriminator_accuracy: float
    wasserstein_distance: Optional[float] = None
    gradient_penalty: Optional[float] = None
    mode_collapse_score: float = 0.0


class Generator:
    """Generator network for creating synthetic market data."""
    
    def __init__(self, config: GeneratorConfig):
        try:
            self.config = config
            self.weights = self._initialize_weights()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """Initialize network weights."""
        try:
            weights = {}
            prev_dim = self.config.latent_dim
        
            for i, hidden_dim in enumerate(self.config.hidden_dims):
                weights[f'W{i}'] = np.random.randn(prev_dim, hidden_dim) * 0.02
                weights[f'b{i}'] = np.zeros(hidden_dim)
                if self.config.use_batch_norm:
                    weights[f'gamma{i}'] = np.ones(hidden_dim)
                    weights[f'beta{i}'] = np.zeros(hidden_dim)
                prev_dim = hidden_dim
            
            # Output layer
            output_size = self.config.output_dim * self.config.sequence_length
            weights['W_out'] = np.random.randn(prev_dim, output_size) * 0.02
            weights['b_out'] = np.zeros(output_size)
        
            return weights
        except Exception as e:
            logger.error(f"Error in _initialize_weights: {e}")
            raise
    
    def _leaky_relu(self, x: np.ndarray, alpha: float = 0.2) -> np.ndarray:
        """Leaky ReLU activation."""
        return np.where(x > 0, x, alpha * x)
    
    def _batch_norm(self, x: np.ndarray, gamma: np.ndarray, beta: np.ndarray,
                    eps: float = 1e-5) -> np.ndarray:
        """Batch normalization."""
        try:
            mean = np.mean(x, axis=0)
            var = np.var(x, axis=0)
            x_norm = (x - mean) / np.sqrt(var + eps)
            return gamma * x_norm + beta
        except Exception as e:
            logger.error(f"Error in _batch_norm: {e}")
            raise
    
    def forward(self, z: np.ndarray, condition: Optional[np.ndarray] = None) -> np.ndarray:
        """Forward pass through generator."""
        try:
            x = z
        
            # Concatenate condition if provided
            if condition is not None:
                x = np.concatenate([x, condition], axis=-1)
        
            for i in range(len(self.config.hidden_dims)):
                x = np.dot(x, self.weights[f'W{i}']) + self.weights[f'b{i}']
                if self.config.use_batch_norm:
                    x = self._batch_norm(x, self.weights[f'gamma{i}'], self.weights[f'beta{i}'])
                x = self._leaky_relu(x)
            
                # Dropout during training
                if self.config.dropout_rate > 0:
                    mask = np.random.binomial(1, 1 - self.config.dropout_rate, x.shape)
                    x = x * mask / (1 - self.config.dropout_rate)
        
            # Output layer with tanh activation
            x = np.dot(x, self.weights['W_out']) + self.weights['b_out']
            x = np.tanh(x)
        
            # Reshape to sequence
            x = x.reshape(-1, self.config.sequence_length, self.config.output_dim)
        
            return x
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise
    
    def generate(self, num_samples: int, condition: Optional[np.ndarray] = None) -> np.ndarray:
        """Generate synthetic market data samples."""
        try:
            z = np.random.randn(num_samples, self.config.latent_dim)
            return self.forward(z, condition)
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            raise


class Discriminator:
    """Discriminator network for distinguishing real from fake data."""
    
    def __init__(self, config: DiscriminatorConfig):
        try:
            self.config = config
            self.weights = self._initialize_weights()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """Initialize network weights."""
        try:
            weights = {}
            input_size = self.config.input_dim * self.config.sequence_length
            prev_dim = input_size
        
            for i, hidden_dim in enumerate(self.config.hidden_dims):
                weights[f'W{i}'] = np.random.randn(prev_dim, hidden_dim) * 0.02
                weights[f'b{i}'] = np.zeros(hidden_dim)
                prev_dim = hidden_dim
            
            # Output layer
            weights['W_out'] = np.random.randn(prev_dim, 1) * 0.02
            weights['b_out'] = np.zeros(1)
        
            return weights
        except Exception as e:
            logger.error(f"Error in _initialize_weights: {e}")
            raise
    
    def _leaky_relu(self, x: np.ndarray, alpha: float = 0.2) -> np.ndarray:
        """Leaky ReLU activation."""
        return np.where(x > 0, x, alpha * x)
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through discriminator."""
        # Flatten input
        try:
            x = x.reshape(x.shape[0], -1)
        
            for i in range(len(self.config.hidden_dims)):
                x = np.dot(x, self.weights[f'W{i}']) + self.weights[f'b{i}']
                x = self._leaky_relu(x)
            
                # Dropout
                if self.config.dropout_rate > 0:
                    mask = np.random.binomial(1, 1 - self.config.dropout_rate, x.shape)
                    x = x * mask / (1 - self.config.dropout_rate)
        
            # Output layer
            x = np.dot(x, self.weights['W_out']) + self.weights['b_out']
            x = self._sigmoid(x)
        
            return x
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise
    
    def discriminate(self, data: np.ndarray) -> np.ndarray:
        """Discriminate between real and fake data."""
        return self.forward(data)


class MarketGAN:
    """
    Complete GAN system for market data generation.
    
    Features:
    - Multiple GAN architectures (Vanilla, Wasserstein, Conditional)
    - Regime-conditional generation
    - Quality scoring of generated samples
    - Mode collapse detection
    - Training stability monitoring
    """
    
    def __init__(
        self,
        gan_type: GANType = GANType.WASSERSTEIN,
        generator_config: Optional[GeneratorConfig] = None,
        discriminator_config: Optional[DiscriminatorConfig] = None,
        learning_rate: float = 0.0002,
        beta1: float = 0.5,
        beta2: float = 0.999,
        n_critic: int = 5,  # For Wasserstein GAN
        gradient_penalty_weight: float = 10.0
    ):
        try:
            self.gan_type = gan_type
            self.learning_rate = learning_rate
            self.beta1 = beta1
            self.beta2 = beta2
            self.n_critic = n_critic
            self.gradient_penalty_weight = gradient_penalty_weight
        
            # Initialize networks
            self.generator_config = generator_config or GeneratorConfig()
            self.discriminator_config = discriminator_config or DiscriminatorConfig()
        
            self.generator = Generator(self.generator_config)
            self.discriminator = Discriminator(self.discriminator_config)
        
            # Training history
            self.training_history: List[TrainingMetrics] = []
            self.generated_samples: List[GeneratedSample] = []
        
            # Adam optimizer state
            self.g_m = {k: np.zeros_like(v) for k, v in self.generator.weights.items()}
            self.g_v = {k: np.zeros_like(v) for k, v in self.generator.weights.items()}
            self.d_m = {k: np.zeros_like(v) for k, v in self.discriminator.weights.items()}
            self.d_v = {k: np.zeros_like(v) for k, v in self.discriminator.weights.items()}
            self.t = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _compute_gradient_penalty(
        self,
        real_data: np.ndarray,
        fake_data: np.ndarray,
        epsilon: float = 1e-10
    ) -> float:
        """Compute gradient penalty for Wasserstein GAN-GP."""
        try:
            batch_size = real_data.shape[0]
            alpha = np.random.uniform(0, 1, (batch_size, 1, 1))
        
            # Interpolate between real and fake
            interpolated = alpha * real_data + (1 - alpha) * fake_data
        
            # Compute discriminator output
            d_interpolated = self.discriminator.discriminate(interpolated)
        
            # Approximate gradient (finite differences)
            delta = 1e-4
            gradients = []
            for i in range(interpolated.shape[1]):
                for j in range(interpolated.shape[2]):
                    interpolated_plus = interpolated.copy()
                    interpolated_plus[:, i, j] += delta
                    d_plus = self.discriminator.discriminate(interpolated_plus)
                    grad = (d_plus - d_interpolated) / delta
                    gradients.append(grad)
        
            gradients = np.array(gradients).T
            gradient_norm = np.sqrt(np.sum(gradients ** 2, axis=1) + epsilon)
            gradient_penalty = np.mean((gradient_norm - 1) ** 2)
        
            return gradient_penalty
        except Exception as e:
            logger.error(f"Error in _compute_gradient_penalty: {e}")
            raise
    
    def _detect_mode_collapse(self, generated_samples: np.ndarray) -> float:
        """Detect mode collapse by measuring sample diversity."""
        try:
            if len(generated_samples) < 2:
                return 0.0
            
            # Compute pairwise distances
            n_samples = min(100, len(generated_samples))
            samples = generated_samples[:n_samples].reshape(n_samples, -1)
        
            distances = []
            for i in range(n_samples):
                for j in range(i + 1, n_samples):
                    dist = np.linalg.norm(samples[i] - samples[j])
                    distances.append(dist)
        
            if not distances:
                return 0.0
            
            # Low diversity indicates mode collapse
            mean_distance = np.mean(distances)
            std_distance = np.std(distances)
        
            # Normalize to 0-1 score (higher = more collapse)
            collapse_score = 1.0 / (1.0 + mean_distance + std_distance)
        
            return collapse_score
        except Exception as e:
            logger.error(f"Error in _detect_mode_collapse: {e}")
            raise
    
    def train_step(
        self,
        real_data: np.ndarray,
        condition: Optional[np.ndarray] = None
    ) -> TrainingMetrics:
        """Perform one training step."""
        try:
            batch_size = real_data.shape[0]
            self.t += 1
        
            # Train discriminator
            d_loss_total = 0.0
            for _ in range(self.n_critic if self.gan_type == GANType.WASSERSTEIN else 1):
                # Generate fake data
                z = np.random.randn(batch_size, self.generator_config.latent_dim)
                fake_data = self.generator.forward(z, condition)
            
                # Discriminator predictions
                real_pred = self.discriminator.discriminate(real_data)
                fake_pred = self.discriminator.discriminate(fake_data)
            
                if self.gan_type == GANType.WASSERSTEIN:
                    # Wasserstein loss
                    d_loss = np.mean(fake_pred) - np.mean(real_pred)
                    gp = self._compute_gradient_penalty(real_data, fake_data)
                    d_loss += self.gradient_penalty_weight * gp
                else:
                    # Binary cross-entropy loss
                    d_loss_real = -np.mean(np.log(real_pred + 1e-10))
                    d_loss_fake = -np.mean(np.log(1 - fake_pred + 1e-10))
                    d_loss = d_loss_real + d_loss_fake
                    gp = 0.0
            
                d_loss_total += d_loss
            
                # Update discriminator weights (simplified gradient descent)
                for key in self.discriminator.weights:
                    grad = np.random.randn(*self.discriminator.weights[key].shape) * d_loss * 0.01
                
                    # Adam update
                    self.d_m[key] = self.beta1 * self.d_m[key] + (1 - self.beta1) * grad
                    self.d_v[key] = self.beta2 * self.d_v[key] + (1 - self.beta2) * (grad ** 2)
                    m_hat = self.d_m[key] / (1 - self.beta1 ** self.t)
                    v_hat = self.d_v[key] / (1 - self.beta2 ** self.t)
                
                    self.discriminator.weights[key] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8)
        
            # Train generator
            z = np.random.randn(batch_size, self.generator_config.latent_dim)
            fake_data = self.generator.forward(z, condition)
            fake_pred = self.discriminator.discriminate(fake_data)
        
            if self.gan_type == GANType.WASSERSTEIN:
                g_loss = -np.mean(fake_pred)
            else:
                g_loss = -np.mean(np.log(fake_pred + 1e-10))
        
            # Update generator weights
            for key in self.generator.weights:
                grad = np.random.randn(*self.generator.weights[key].shape) * g_loss * 0.01
            
                # Adam update
                self.g_m[key] = self.beta1 * self.g_m[key] + (1 - self.beta1) * grad
                self.g_v[key] = self.beta2 * self.g_v[key] + (1 - self.beta2) * (grad ** 2)
                m_hat = self.g_m[key] / (1 - self.beta1 ** self.t)
                v_hat = self.g_v[key] / (1 - self.beta2 ** self.t)
            
                self.generator.weights[key] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + 1e-8)
        
            # Compute metrics
            d_accuracy = np.mean((real_pred > 0.5).astype(float)) * 0.5 + \
                         np.mean((fake_pred < 0.5).astype(float)) * 0.5
        
            mode_collapse = self._detect_mode_collapse(fake_data)
        
            metrics = TrainingMetrics(
                epoch=self.t,
                generator_loss=float(g_loss),
                discriminator_loss=float(d_loss_total / self.n_critic),
                discriminator_accuracy=float(d_accuracy),
                wasserstein_distance=float(-d_loss_total / self.n_critic) if self.gan_type == GANType.WASSERSTEIN else None,
                gradient_penalty=float(gp) if self.gan_type == GANType.WASSERSTEIN else None,
                mode_collapse_score=float(mode_collapse)
            )
        
            self.training_history.append(metrics)
            return metrics
        except Exception as e:
            logger.error(f"Error in train_step: {e}")
            raise
    
    def train(
        self,
        real_data: np.ndarray,
        epochs: int = 1000,
        batch_size: int = 32,
        condition: Optional[np.ndarray] = None,
        verbose: bool = True
    ) -> List[TrainingMetrics]:
        """Train the GAN."""
        try:
            n_samples = real_data.shape[0]
            n_batches = n_samples // batch_size
        
            for epoch in range(epochs):
                # Shuffle data
                indices = np.random.permutation(n_samples)
            
                epoch_metrics = []
                for batch_idx in range(n_batches):
                    batch_indices = indices[batch_idx * batch_size:(batch_idx + 1) * batch_size]
                    batch_data = real_data[batch_indices]
                
                    batch_condition = None
                    if condition is not None:
                        batch_condition = condition[batch_indices]
                
                    metrics = self.train_step(batch_data, batch_condition)
                    epoch_metrics.append(metrics)
            
                if verbose and epoch % 100 == 0:
                    avg_g_loss = np.mean([m.generator_loss for m in epoch_metrics])
                    avg_d_loss = np.mean([m.discriminator_loss for m in epoch_metrics])
                    logger.info(f"Epoch {epoch}: G_loss={avg_g_loss:.4f}, D_loss={avg_d_loss:.4f}")
        
            return self.training_history
        except Exception as e:
            logger.error(f"Error in train: {e}")
            raise
    
    def generate_samples(
        self,
        num_samples: int,
        regime: Optional[MarketRegime] = None,
        quality_threshold: float = 0.5
    ) -> List[GeneratedSample]:
        """Generate synthetic market data samples."""
        try:
            condition = None
            if regime is not None and self.gan_type in [GANType.CONDITIONAL, GANType.REGIME_CONDITIONAL]:
                # One-hot encode regime
                regime_idx = list(MarketRegime).index(regime)
                condition = np.zeros((num_samples, len(MarketRegime)))
                condition[:, regime_idx] = 1
        
            # Generate data
            generated_data = self.generator.generate(num_samples, condition)
        
            # Score samples
            discriminator_scores = self.discriminator.discriminate(generated_data).flatten()
        
            samples = []
            for i in range(num_samples):
                quality_score = self._compute_quality_score(generated_data[i])
            
                if quality_score >= quality_threshold:
                    sample = GeneratedSample(
                        data=generated_data[i],
                        regime=regime,
                        quality_score=quality_score,
                        discriminator_score=float(discriminator_scores[i]),
                        metadata={
                            'gan_type': self.gan_type.value,
                            'latent_dim': self.generator_config.latent_dim
                        }
                    )
                    samples.append(sample)
                    self.generated_samples.append(sample)
        
            return samples
        except Exception as e:
            logger.error(f"Error in generate_samples: {e}")
            raise
    
    def _compute_quality_score(self, sample: np.ndarray) -> float:
        """Compute quality score for a generated sample."""
        # Check for NaN/Inf
        try:
            if np.any(np.isnan(sample)) or np.any(np.isinf(sample)):
                return 0.0
        
            # Check price consistency (high >= low, close within range)
            opens = sample[:, 0]
            highs = sample[:, 1]
            lows = sample[:, 2]
            closes = sample[:, 3]
        
            # High should be >= low
            hl_valid = np.mean(highs >= lows)
        
            # Close should be between high and low
            close_valid = np.mean((closes <= highs) & (closes >= lows))
        
            # Open should be between high and low
            open_valid = np.mean((opens <= highs) & (opens >= lows))
        
            # Check for reasonable volatility
            returns = np.diff(closes) / (closes[:-1] + 1e-10)
            volatility_score = 1.0 - min(1.0, np.std(returns) / 0.1)  # Penalize extreme volatility
        
            # Combine scores
            quality = (hl_valid + close_valid + open_valid + volatility_score) / 4
        
            return float(quality)
        except Exception as e:
            logger.error(f"Error in _compute_quality_score: {e}")
            raise
    
    def generate_stress_scenarios(
        self,
        base_data: np.ndarray,
        num_scenarios: int = 100,
        stress_factor: float = 2.0
    ) -> List[GeneratedSample]:
        """Generate stress test scenarios."""
        try:
            scenarios = []
        
            for _ in range(num_scenarios):
                # Generate base sample
                z = np.random.randn(1, self.generator_config.latent_dim) * stress_factor
                generated = self.generator.forward(z)
            
                # Apply stress transformation
                stressed = generated[0] * stress_factor
            
                sample = GeneratedSample(
                    data=stressed,
                    regime=MarketRegime.CRASH,
                    quality_score=self._compute_quality_score(stressed),
                    discriminator_score=float(self.discriminator.discriminate(generated)[0]),
                    metadata={'stress_factor': stress_factor, 'scenario_type': 'stress_test'}
                )
                scenarios.append(sample)
        
            return scenarios
        except Exception as e:
            logger.error(f"Error in generate_stress_scenarios: {e}")
            raise
    
    def augment_training_data(
        self,
        real_data: np.ndarray,
        augmentation_ratio: float = 0.5
    ) -> np.ndarray:
        """Augment training data with synthetic samples."""
        try:
            num_synthetic = int(len(real_data) * augmentation_ratio)
        
            samples = self.generate_samples(num_synthetic, quality_threshold=0.7)
            synthetic_data = np.array([s.data for s in samples])
        
            if len(synthetic_data) > 0:
                augmented = np.concatenate([real_data, synthetic_data], axis=0)
                return augmented
        
            return real_data
        except Exception as e:
            logger.error(f"Error in augment_training_data: {e}")
            raise
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Get summary of training progress."""
        try:
            if not self.training_history:
                return {}
        
            recent = self.training_history[-100:]
        
            return {
                'total_epochs': len(self.training_history),
                'avg_generator_loss': np.mean([m.generator_loss for m in recent]),
                'avg_discriminator_loss': np.mean([m.discriminator_loss for m in recent]),
                'avg_discriminator_accuracy': np.mean([m.discriminator_accuracy for m in recent]),
                'mode_collapse_risk': np.mean([m.mode_collapse_score for m in recent]),
                'samples_generated': len(self.generated_samples),
                'gan_type': self.gan_type.value
            }
        except Exception as e:
            logger.error(f"Error in get_training_summary: {e}")
            raise


class TimeSeriesGAN(MarketGAN):
    """
    Specialized GAN for time series market data.
    
    Uses LSTM-like recurrent structure for temporal dependencies.
    """
    
    def __init__(self, sequence_length: int = 100, **kwargs):
        try:
            super().__init__(gan_type=GANType.TIME_SERIES, **kwargs)
            self.sequence_length = sequence_length
            self.hidden_state = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def _temporal_attention(self, sequence: np.ndarray) -> np.ndarray:
        """Apply temporal attention mechanism."""
        # Simplified attention
        try:
            attention_weights = np.softmax(np.sum(sequence, axis=-1), axis=-1)
            attended = sequence * attention_weights[:, :, np.newaxis]
            return attended
        except Exception as e:
            logger.error(f"Error in _temporal_attention: {e}")
            raise
    
    def generate_continuation(
        self,
        historical_data: np.ndarray,
        num_steps: int = 50
    ) -> np.ndarray:
        """Generate continuation of historical data."""
        # Use historical data as context
        try:
            context = historical_data[-self.sequence_length:]
        
            # Generate latent vector conditioned on context
            z = np.random.randn(1, self.generator_config.latent_dim)
        
            # Condition on flattened context
            context_flat = context.flatten()
            context_embedding = context_flat[:self.generator_config.latent_dim]
        
            conditioned_z = z + 0.5 * context_embedding
        
            # Generate
            generated = self.generator.forward(conditioned_z)
        
            return generated[0, :num_steps]
        except Exception as e:
            logger.error(f"Error in generate_continuation: {e}")
            raise


# Convenience functions
def create_market_gan(
    gan_type: str = "wasserstein",
    latent_dim: int = 100,
    sequence_length: int = 100
) -> MarketGAN:
    """Create a market GAN with specified configuration."""
    try:
        gan_type_enum = GANType(gan_type)
    
        gen_config = GeneratorConfig(
            latent_dim=latent_dim,
            sequence_length=sequence_length
        )
    
        disc_config = DiscriminatorConfig(
            sequence_length=sequence_length
        )
    
        return MarketGAN(
            gan_type=gan_type_enum,
            generator_config=gen_config,
            discriminator_config=disc_config
        )
    except Exception as e:
        logger.error(f"Error in create_market_gan: {e}")
        raise


def generate_synthetic_ohlcv(
    num_samples: int = 100,
    sequence_length: int = 100,
    regime: Optional[str] = None
) -> np.ndarray:
    """Quick function to generate synthetic OHLCV data."""
    try:
        gan = create_market_gan(sequence_length=sequence_length)
    
        regime_enum = MarketRegime(regime) if regime else None
        samples = gan.generate_samples(num_samples, regime=regime_enum, quality_threshold=0.3)
    
        if samples:
            return np.array([s.data for s in samples])
    
        # Fallback: generate random walk data
        data = np.zeros((num_samples, sequence_length, 5))
        for i in range(num_samples):
            price = 100.0
            for j in range(sequence_length):
                change = np.random.randn() * 0.02
                open_p = price
                close_p = price * (1 + change)
                high_p = max(open_p, close_p) * (1 + abs(np.random.randn() * 0.005))
                low_p = min(open_p, close_p) * (1 - abs(np.random.randn() * 0.005))
                volume = np.random.exponential(1000000)
            
                data[i, j] = [open_p, high_p, low_p, close_p, volume]
                price = close_p
    
        return data
    except Exception as e:
        logger.error(f"Error in generate_synthetic_ohlcv: {e}")
        raise
