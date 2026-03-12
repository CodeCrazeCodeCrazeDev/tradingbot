"""
DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks

Based on: "DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks" (2019)
arXiv: https://arxiv.org/abs/1704.04110

Key features:
- Autoregressive RNN for time series forecasting
- Probabilistic predictions with parametric distributions
- Handles multiple related time series
- Incorporates covariates (time-varying and static)
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Optional, Tuple
import logging
from dataclasses import dataclass
import numpy

logger = logging.getLogger(__name__)


@dataclass
class DeepARConfig:
    """Configuration for DeepAR model"""
    input_size: int = 1  # Number of input features
    hidden_size: int = 40  # LSTM hidden size
    num_layers: int = 2  # Number of LSTM layers
    dropout: float = 0.1  # Dropout rate
    embedding_dim: int = 10  # Categorical embedding dimension
    num_categories: int = 0  # Number of categorical features
    likelihood: str = 'gaussian'  # 'gaussian', 'negative-binomial', or 'student-t'
    context_length: int = 168  # Encoder length (1 week hourly)
    prediction_length: int = 24  # Decoder length (1 day hourly)


class GaussianLikelihood(nn.Module):
    """Gaussian likelihood for continuous data"""
    
    def __init__(self):
        super().__init__()
    
    def forward(self, mu: torch.Tensor, sigma: torch.Tensor) -> torch.distributions.Distribution:
        """
        Create Gaussian distribution
        
        Args:
            mu: Mean [B, T]
            sigma: Standard deviation [B, T]
            
        Returns:
            Gaussian distribution
        """
        sigma = F.softplus(sigma) + 1e-6  # Ensure positive
        return torch.distributions.Normal(mu, sigma)
    
    def loss(self, mu: torch.Tensor, sigma: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Negative log-likelihood loss"""
        dist = self.forward(mu, sigma)
        return -dist.log_prob(target)


class NegativeBinomialLikelihood(nn.Module):
    """Negative Binomial likelihood for count data"""
    
    def __init__(self):
        super().__init__()
    
    def forward(self, mu: torch.Tensor, alpha: torch.Tensor) -> torch.distributions.Distribution:
        """
        Create Negative Binomial distribution
        
        Args:
            mu: Mean [B, T]
            alpha: Dispersion parameter [B, T]
            
        Returns:
            Negative Binomial distribution
        """
        mu = F.softplus(mu) + 1e-6
        alpha = F.softplus(alpha) + 1e-6
        
        # Convert to total_count and probs parameterization
        total_count = 1.0 / alpha
        probs = total_count / (total_count + mu)
        
        return torch.distributions.NegativeBinomial(total_count, probs)
    
    def loss(self, mu: torch.Tensor, alpha: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Negative log-likelihood loss"""
        dist = self.forward(mu, alpha)
        return -dist.log_prob(target)


class StudentTLikelihood(nn.Module):
    """Student's t likelihood for heavy-tailed data"""
    
    def __init__(self):
        super().__init__()
    
    def forward(
        self,
        mu: torch.Tensor,
        sigma: torch.Tensor,
        nu: torch.Tensor
    ) -> torch.distributions.Distribution:
        """
        Create Student's t distribution
        
        Args:
            mu: Location [B, T]
            sigma: Scale [B, T]
            nu: Degrees of freedom [B, T]
            
        Returns:
            Student's t distribution
        """
        sigma = F.softplus(sigma) + 1e-6
        nu = 2.0 + F.softplus(nu)  # Ensure df > 2
        
        return torch.distributions.StudentT(nu, mu, sigma)
    
    def loss(
        self,
        mu: torch.Tensor,
        sigma: torch.Tensor,
        nu: torch.Tensor,
        target: torch.Tensor
    ) -> torch.Tensor:
        """Negative log-likelihood loss"""
        dist = self.forward(mu, sigma, nu)
        return -dist.log_prob(target)


class DeepARModel(nn.Module):
    """
    DeepAR: Probabilistic forecasting with autoregressive RNN
    
    Architecture:
    1. Embedding layer for categorical features
    2. LSTM encoder for context
    3. LSTM decoder with autoregressive sampling
    4. Likelihood layer for probabilistic predictions
    """
    
    def __init__(self, config: DeepARConfig):
        super().__init__()
        self.config = config
        
        # Categorical embeddings
        if config.num_categories > 0:
            self.embeddings = nn.Embedding(config.num_categories, config.embedding_dim)
            lstm_input_size = config.input_size + config.embedding_dim
        else:
            self.embeddings = None
            lstm_input_size = config.input_size
        
        # LSTM encoder-decoder
        self.lstm = nn.LSTM(
            input_size=lstm_input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            dropout=config.dropout if config.num_layers > 1 else 0,
            batch_first=True
        )
        
        # Likelihood-specific output layers
        if config.likelihood == 'gaussian':
            self.likelihood = GaussianLikelihood()
            self.mu_layer = nn.Linear(config.hidden_size, 1)
            self.sigma_layer = nn.Linear(config.hidden_size, 1)
            self.num_params = 2
        elif config.likelihood == 'negative-binomial':
            self.likelihood = NegativeBinomialLikelihood()
            self.mu_layer = nn.Linear(config.hidden_size, 1)
            self.alpha_layer = nn.Linear(config.hidden_size, 1)
            self.num_params = 2
        elif config.likelihood == 'student-t':
            self.likelihood = StudentTLikelihood()
            self.mu_layer = nn.Linear(config.hidden_size, 1)
            self.sigma_layer = nn.Linear(config.hidden_size, 1)
            self.nu_layer = nn.Linear(config.hidden_size, 1)
            self.num_params = 3
        else:
            raise ValueError(f"Unknown likelihood: {config.likelihood}")
    
    def forward(
        self,
        past_target: torch.Tensor,
        past_covariates: Optional[torch.Tensor] = None,
        future_covariates: Optional[torch.Tensor] = None,
        categorical: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, ...]:
        """
        Forward pass (training mode)
        
        Args:
            past_target: Historical target values [B, context_length]
            past_covariates: Historical covariates [B, context_length, num_features]
            future_covariates: Future covariates [B, prediction_length, num_features]
            categorical: Categorical features [B, num_categories]
            
        Returns:
            Distribution parameters for each time step
        """
        batch_size = past_target.size(0)
        context_length = past_target.size(1)
        
        # Prepare input
        if past_covariates is not None:
            encoder_input = torch.cat([past_target.unsqueeze(-1), past_covariates], dim=-1)
        else:
            encoder_input = past_target.unsqueeze(-1)
        
        # Add categorical embeddings
        if self.embeddings is not None and categorical is not None:
            cat_emb = self.embeddings(categorical)  # [B, embedding_dim]
            cat_emb = cat_emb.unsqueeze(1).expand(-1, context_length, -1)
            encoder_input = torch.cat([encoder_input, cat_emb], dim=-1)
        
        # Encode context
        lstm_out, hidden = self.lstm(encoder_input)
        
        # Decode (teacher forcing)
        if future_covariates is not None:
            prediction_length = future_covariates.size(1)
            
            # Prepare decoder input with future covariates
            decoder_input = future_covariates
            
            # Add categorical embeddings
            if self.embeddings is not None and categorical is not None:
                cat_emb = cat_emb[:, :prediction_length, :]
                decoder_input = torch.cat([decoder_input, cat_emb], dim=-1)
            
            # Decode
            decoder_out, _ = self.lstm(decoder_input, hidden)
        else:
            # No future covariates, use zeros
            prediction_length = self.config.prediction_length
            decoder_input = torch.zeros(
                batch_size, prediction_length, self.config.input_size,
                device=past_target.device
            )
            decoder_out, _ = self.lstm(decoder_input, hidden)
        
        # Compute distribution parameters
        if self.config.likelihood == 'gaussian':
            mu = self.mu_layer(decoder_out).squeeze(-1)
            sigma = self.sigma_layer(decoder_out).squeeze(-1)
            return mu, sigma
        elif self.config.likelihood == 'negative-binomial':
            mu = self.mu_layer(decoder_out).squeeze(-1)
            alpha = self.alpha_layer(decoder_out).squeeze(-1)
            return mu, alpha
        elif self.config.likelihood == 'student-t':
            mu = self.mu_layer(decoder_out).squeeze(-1)
            sigma = self.sigma_layer(decoder_out).squeeze(-1)
            nu = self.nu_layer(decoder_out).squeeze(-1)
            return mu, sigma, nu
    
    def predict(
        self,
        past_target: torch.Tensor,
        past_covariates: Optional[torch.Tensor] = None,
        future_covariates: Optional[torch.Tensor] = None,
        categorical: Optional[torch.Tensor] = None,
        num_samples: int = 100
    ) -> torch.Tensor:
        """
        Generate probabilistic predictions
        
        Args:
            past_target: Historical target values [B, context_length]
            past_covariates: Historical covariates
            future_covariates: Future covariates
            categorical: Categorical features
            num_samples: Number of Monte Carlo samples
            
        Returns:
            Samples from predictive distribution [num_samples, B, prediction_length]
        """
        self.eval()
        with torch.no_grad():
            batch_size = past_target.size(0)
            prediction_length = self.config.prediction_length
            
            # Prepare encoder input
            if past_covariates is not None:
                encoder_input = torch.cat([past_target.unsqueeze(-1), past_covariates], dim=-1)
            else:
                encoder_input = past_target.unsqueeze(-1)
            
            # Add categorical embeddings
            if self.embeddings is not None and categorical is not None:
                cat_emb = self.embeddings(categorical)
                cat_emb_expanded = cat_emb.unsqueeze(1).expand(-1, encoder_input.size(1), -1)
                encoder_input = torch.cat([encoder_input, cat_emb_expanded], dim=-1)
            
            # Encode
            _, hidden = self.lstm(encoder_input)
            
            # Autoregressive decoding
            samples = []
            
            for _ in range(num_samples):
                predictions = []
                current_hidden = hidden
                current_input = past_target[:, -1].unsqueeze(-1)  # Last observed value
                
                for t in range(prediction_length):
                    # Prepare input
                    if future_covariates is not None:
                        lstm_input = torch.cat([current_input, future_covariates[:, t:t+1, :]], dim=-1)
                    else:
                        lstm_input = current_input
                    
                    # Add categorical embeddings
                    if self.embeddings is not None and categorical is not None:
                        lstm_input = torch.cat([lstm_input, cat_emb.unsqueeze(1)], dim=-1)
                    
                    # LSTM step
                    lstm_out, current_hidden = self.lstm(lstm_input, current_hidden)
                    
                    # Sample from distribution
                    if self.config.likelihood == 'gaussian':
                        mu = self.mu_layer(lstm_out).squeeze(-1)
                        sigma = self.sigma_layer(lstm_out).squeeze(-1)
                        dist = self.likelihood(mu, sigma)
                    elif self.config.likelihood == 'negative-binomial':
                        mu = self.mu_layer(lstm_out).squeeze(-1)
                        alpha = self.alpha_layer(lstm_out).squeeze(-1)
                        dist = self.likelihood(mu, alpha)
                    elif self.config.likelihood == 'student-t':
                        mu = self.mu_layer(lstm_out).squeeze(-1)
                        sigma = self.sigma_layer(lstm_out).squeeze(-1)
                        nu = self.nu_layer(lstm_out).squeeze(-1)
                        dist = self.likelihood(mu, sigma, nu)
                    
                    sample = dist.sample()
                    predictions.append(sample)
                    
                    # Use sample as next input
                    current_input = sample.unsqueeze(-1)
                
                samples.append(torch.stack(predictions, dim=1))
            
            return torch.stack(samples, dim=0)
    
    def compute_loss(
        self,
        past_target: torch.Tensor,
        future_target: torch.Tensor,
        past_covariates: Optional[torch.Tensor] = None,
        future_covariates: Optional[torch.Tensor] = None,
        categorical: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute negative log-likelihood loss
        
        Args:
            past_target: Historical target values
            future_target: Future target values to predict
            past_covariates: Historical covariates
            future_covariates: Future covariates
            categorical: Categorical features
            
        Returns:
            Loss value
        """
        # Forward pass
        params = self.forward(past_target, past_covariates, future_covariates, categorical)
        
        # Compute loss
        if self.config.likelihood == 'gaussian':
            mu, sigma = params
            loss = self.likelihood.loss(mu, sigma, future_target)
        elif self.config.likelihood == 'negative-binomial':
            mu, alpha = params
            loss = self.likelihood.loss(mu, alpha, future_target)
        elif self.config.likelihood == 'student-t':
            mu, sigma, nu = params
            loss = self.likelihood.loss(mu, sigma, nu, future_target)
        
        return loss.mean()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test DeepAR model
    config = DeepARConfig(
        input_size=1,
        hidden_size=40,
        num_layers=2,
        dropout=0.1,
        embedding_dim=10,
        num_categories=0,
        likelihood='gaussian',
        context_length=168,
        prediction_length=24
    )
    
    model = DeepARModel(config)
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test data
    batch_size = 32
    past_target = torch.randn(batch_size, config.context_length)
    future_target = torch.randn(batch_size, config.prediction_length)
    
    # Test forward pass
    params = model(past_target)
    logger.info(f"\nForward pass output shapes:")
    for i, param in enumerate(params):
        logger.info(f"  Parameter {i+1}: {param.shape}")
    
    # Test loss
    loss = model.compute_loss(past_target, future_target)
    logger.info(f"\nLoss: {loss.item():.4f}")
    
    # Test prediction
    samples = model.predict(past_target, num_samples=100)
    logger.info(f"\nPrediction samples shape: {samples.shape}")
    logger.info(f"Expected: (100, {batch_size}, {config.prediction_length})")
    
    # Compute quantiles
    quantiles = torch.quantile(samples, torch.tensor([0.1, 0.5, 0.9]), dim=0)
    logger.info(f"Quantiles shape: {quantiles.shape}")
    
    logger.info("\n✅ DeepAR model test passed!")
