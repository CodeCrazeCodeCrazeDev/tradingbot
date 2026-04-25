"""
Layer 2: Forecast & Representation Layer

Trading-native multi-task heads on frozen foundation backbones.
Implements LoRA/Adapter-based adaptation for:
- Expected signed return
- Volatility forecast
- Drawdown risk probability
- Rank score across assets
- Probability of move exceeding cost threshold
- Regime label classification
- Execution difficulty score

Uses regime-conditioned adapters (not full fine-tuning).
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
import numpy as np
from dataclasses import dataclass, field
from enum import Enum

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

from ..types import (
    ModelType, ForecastHorizon, MarketData, FoundationForecast,
    TradingNativeHeads, RegimeType, GETSConfig
)

logger = logging.getLogger(__name__)


class AdapterType(Enum):
    """Types of parameter-efficient adapters."""
    LORA = "lora"           # Low-Rank Adaptation
    ADAPTER = "adapter"     # Bottleneck adapters
    PROMPT = "prompt"       # Prompt tuning (for applicable models)


@dataclass
class LoRAConfig:
    """Configuration for LoRA adapters."""
    r: int = 8              # LoRA rank
    alpha: float = 16.0     # LoRA alpha (scaling)
    dropout: float = 0.1
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])


@dataclass
class AdapterConfig:
    """Configuration for bottleneck adapters."""
    hidden_dim: int = 64
    adapter_dim: int = 16
    dropout: float = 0.1


@dataclass
class TradingHeadConfig:
    """Configuration for trading-native prediction heads."""
    # Expected signed return
    signed_return_hidden_dims: List[int] = field(default_factory=lambda: [128, 64])
    
    # Volatility forecast
    volatility_hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    
    # Drawdown risk (binary classification)
    drawdown_hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    
    # Rank score
    rank_hidden_dims: List[int] = field(default_factory=lambda: [128, 64, 32])
    
    # Cost threshold probability
    cost_threshold_hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    
    # Regime classification
    regime_hidden_dims: List[int] = field(default_factory=lambda: [128, 64])
    num_regimes: int = 8
    
    # Execution difficulty
    execution_hidden_dims: List[int] = field(default_factory=lambda: [32, 16])
    
    # Edge-after-cost (final trading signal)
    edge_hidden_dims: List[int] = field(default_factory=lambda: [256, 128, 64])


class LoRALayer(nn.Module if TORCH_AVAILABLE else object):
    """
    Low-Rank Adaptation (LoRA) layer implementation.
    
    Implements: h = Wx + (B @ A)x * (alpha / r)
    where B and A are low-rank matrices (r << d).
    """
    
    def __init__(self, in_features: int, out_features: int, config: LoRAConfig):
        super().__init__()
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for LoRA")
        
        self.in_features = in_features
        self.out_features = out_features
        self.r = config.r
        self.alpha = config.alpha
        self.scaling = config.alpha / config.r
        
        # LoRA matrices: B (out x r), A (r x in)
        self.lora_A = nn.Parameter(torch.randn(config.r, in_features) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(out_features, config.r))
        
        self.dropout = nn.Dropout(config.dropout) if config.dropout > 0 else None
    
    def forward(self, x: torch.Tensor, base_output: torch.Tensor) -> torch.Tensor:
        """
        Apply LoRA adaptation to base output.
        
        Args:
            x: Input features
            base_output: Output from frozen base layer
            
        Returns:
            Adapted output: base + LoRA term
        """
        # LoRA path: x @ A.T @ B.T * scaling
        result = base_output
        
        if self.dropout:
            x = self.dropout(x)
        
        # (batch, in) @ (in, r) @ (r, out) * scaling
        lora_output = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
        
        return result + lora_output


class TradingPredictionHead(nn.Module if TORCH_AVAILABLE else object):
    """
    Multi-layer prediction head for a specific trading task.
    
    Architecture: Embedding -> Hidden Layers -> Output
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        output_dim: int,
        output_activation: str = "linear",
        dropout: float = 0.1
    ):
        super().__init__()
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for prediction heads")
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, output_dim))
        
        # Output activation
        if output_activation == "sigmoid":
            layers.append(nn.Sigmoid())
        elif output_activation == "tanh":
            layers.append(nn.Tanh())
        elif output_activation == "softmax":
            layers.append(nn.Softmax(dim=-1))
        # "linear" needs no activation
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class MultiTaskTradingHeads(nn.Module if TORCH_AVAILABLE else object):
    """
    Multi-task learning system with trading-native prediction heads.
    
    Heads:
    1. Expected signed return (regression)
    2. Volatility forecast (regression)
    3. Drawdown risk probability (classification)
    4. Rank score across assets (regression)
    5. Probability of move exceeding cost threshold (classification)
    6. Regime label (multi-class classification)
    7. Execution difficulty score (regression)
    8. Edge-after-cost (final trading signal, regression)
    
    Loss functions combine:
    - Standard MSE for regression tasks
    - Cross-entropy for classification
    - Ranking losses for relative predictions
    - Information coefficient objective
    """
    
    def __init__(
        self,
        embedding_dim: int,
        head_config: TradingHeadConfig,
        use_ranking_loss: bool = True
    ):
        super().__init__()
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for multi-task heads")
        
        self.embedding_dim = embedding_dim
        self.head_config = head_config
        self.use_ranking_loss = use_ranking_loss
        
        # Initialize all heads
        self._init_heads()
    
    def _init_heads(self):
        """Initialize all trading-native prediction heads."""
        cfg = self.head_config
        
        # 1. Expected signed return
        self.signed_return_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.signed_return_hidden_dims,
            output_dim=1,
            output_activation="tanh"  # Bounded [-1, 1] scaled by expected return
        )
        
        # 2. Volatility forecast
        self.volatility_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.volatility_hidden_dims,
            output_dim=1,
            output_activation="sigmoid"  # Normalized volatility
        )
        
        # 3. Drawdown risk probability
        self.drawdown_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.drawdown_hidden_dims,
            output_dim=1,
            output_activation="sigmoid"
        )
        
        # 4. Rank score across assets
        self.rank_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.rank_hidden_dims,
            output_dim=1,
            output_activation="tanh"  # Relative ranking score
        )
        
        # 5. Probability of move exceeding cost threshold
        self.cost_threshold_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.cost_threshold_hidden_dims,
            output_dim=1,
            output_activation="sigmoid"
        )
        
        # 6. Regime classification
        self.regime_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.regime_hidden_dims,
            output_dim=cfg.num_regimes,
            output_activation="softmax"
        )
        
        # 7. Execution difficulty score
        self.execution_head = TradingPredictionHead(
            self.embedding_dim,
            cfg.execution_hidden_dims,
            output_dim=1,
            output_activation="sigmoid"
        )
        
        # 8. Edge-after-cost (main trading signal)
        # This combines outputs from other heads + direct features
        edge_input_dim = self.embedding_dim + 7  # embedding + other head outputs
        self.edge_head = TradingPredictionHead(
            edge_input_dim,
            cfg.edge_hidden_dims,
            output_dim=1,
            output_activation="linear"  # Unbounded edge estimate
        )
    
    def forward(self, embedding: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through all heads.
        
        Args:
            embedding: Foundation model embedding (batch, embedding_dim)
            
        Returns:
            Dictionary of predictions from each head
        """
        # Primary predictions
        signed_return = self.signed_return_head(embedding)
        volatility = self.volatility_head(embedding)
        drawdown_prob = self.drawdown_head(embedding)
        rank_score = self.rank_head(embedding)
        cost_threshold_prob = self.cost_threshold_head(embedding)
        regime_logits = self.regime_head(embedding)
        execution_difficulty = self.execution_head(embedding)
        
        # Combine for edge-after-cost prediction
        # Concatenate embedding with other head outputs
        combined = torch.cat([
            embedding,
            signed_return,
            volatility,
            drawdown_prob,
            rank_score,
            cost_threshold_prob,
            execution_difficulty,
            torch.max(regime_logits, dim=-1, keepdim=True)[0]  # Max regime probability
        ], dim=-1)
        
        edge_after_cost = self.edge_head(combined)
        
        return {
            'signed_return': signed_return,
            'volatility': volatility,
            'drawdown_prob': drawdown_prob,
            'rank_score': rank_score,
            'cost_threshold_prob': cost_threshold_prob,
            'regime_logits': regime_logits,
            'execution_difficulty': execution_difficulty,
            'edge_after_cost': edge_after_cost
        }
    
    def compute_loss(
        self,
        predictions: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        batch_assets: Optional[List[str]] = None
    ) -> torch.Tensor:
        """
        Compute multi-task loss with trading-relevant objectives.
        
        Args:
            predictions: Output from forward pass
            targets: Ground truth values
            batch_assets: List of asset symbols for ranking loss
            
        Returns:
            Combined loss scalar
        """
        losses = {}
        
        # 1. Signed return: MSE
        losses['signed_return'] = nn.MSELoss()(
            predictions['signed_return'],
            targets['signed_return']
        )
        
        # 2. Volatility: MSE
        losses['volatility'] = nn.MSELoss()(
            predictions['volatility'],
            targets['volatility']
        )
        
        # 3. Drawdown: BCE
        losses['drawdown'] = nn.BCELoss()(
            predictions['drawdown_prob'],
            targets['drawdown_occurred']
        )
        
        # 4. Rank score: Ranking loss if batch_assets provided
        if self.use_ranking_loss and batch_assets and len(batch_assets) > 1:
            losses['rank'] = self._ranking_loss(
                predictions['rank_score'].squeeze(),
                targets['rank_score'].squeeze(),
                batch_assets
            )
        else:
            losses['rank'] = nn.MSELoss()(
                predictions['rank_score'],
                targets['rank_score']
            )
        
        # 5. Cost threshold: BCE
        losses['cost_threshold'] = nn.BCELoss()(
            predictions['cost_threshold_prob'],
            targets['exceeded_cost']
        )
        
        # 6. Regime: Cross-entropy
        losses['regime'] = nn.CrossEntropyLoss()(
            predictions['regime_logits'],
            targets['regime_label'].long()
        )
        
        # 7. Execution difficulty: MSE
        losses['execution'] = nn.MSELoss()(
            predictions['execution_difficulty'],
            targets['execution_difficulty']
        )
        
        # 8. Edge-after-cost: Primary objective
        # Use combination of MSE and directional accuracy
        edge_mse = nn.MSELoss()(
            predictions['edge_after_cost'],
            targets['edge_after_cost']
        )
        # Directional accuracy component
        edge_direction_match = (
            (predictions['edge_after_cost'] * targets['edge_after_cost']) > 0
        ).float().mean()
        losses['edge'] = edge_mse - 0.1 * edge_direction_match  # Reward correct direction
        
        # Combine with task-specific weights
        # Edge-after-cost is the primary objective
        weights = {
            'signed_return': 0.5,
            'volatility': 0.3,
            'drawdown': 0.4,
            'rank': 0.5,
            'cost_threshold': 0.6,
            'regime': 0.3,
            'execution': 0.3,
            'edge': 2.0  # Higher weight for primary trading signal
        }
        
        total_loss = sum(weights.get(k, 1.0) * v for k, v in losses.items())
        return total_loss
    
    def _ranking_loss(
        self,
        predicted_scores: torch.Tensor,
        actual_returns: torch.Tensor,
        assets: List[str]
    ) -> torch.Tensor:
        """
        Pairwise ranking loss for cross-asset ranking.
        
        Minimizes inversions: predicted rank should match actual rank.
        """
        # Simple margin-based ranking loss
        n = len(predicted_scores)
        if n < 2:
            return torch.tensor(0.0, requires_grad=True)
        
        loss = torch.tensor(0.0, requires_grad=True)
        margin = 0.1
        
        for i in range(n):
            for j in range(i + 1, n):
                # If asset i outperformed asset j
                if actual_returns[i] > actual_returns[j]:
                    # Penalize if predicted score doesn't reflect this
                    if predicted_scores[i] <= predicted_scores[j]:
                        loss = loss + (predicted_scores[j] - predicted_scores[i] + margin)
                elif actual_returns[j] > actual_returns[i]:
                    if predicted_scores[j] <= predicted_scores[i]:
                        loss = loss + (predicted_scores[i] - predicted_scores[j] + margin)
        
        # Normalize by number of pairs
        num_pairs = n * (n - 1) / 2
        return loss / max(num_pairs, 1)


class RegimeConditionedAdapter:
    """
    Regime-conditioned adapter system.
    
    Uses different LoRA/Adapter weights based on detected regime:
    - Adapter by asset class
    - Adapter by timeframe
    - Adapter by volatility regime
    - Adapter by venue type
    
    Instead of full fine-tuning, only adapter weights change.
    """
    
    def __init__(
        self,
        base_model_dim: int,
        lora_config: LoRAConfig,
        regime_types: List[RegimeType]
    ):
        self.base_dim = base_model_dim
        self.lora_config = lora_config
        self.regime_types = regime_types
        
        # Create adapter bank: one per regime
        self.adapters: Dict[RegimeType, Optional[Any]] = {}
        for regime in regime_types:
            if TORCH_AVAILABLE:
                # Create LoRA layers for key transformer components
                # Simplified: single adapter per regime
                self.adapters[regime] = self._create_adapter()
            else:
                self.adapters[regime] = None
    
    def _create_adapter(self) -> nn.Module:
        """Create adapter module for a specific regime."""
        if not TORCH_AVAILABLE:
            return None
        
        # Simple bottleneck adapter
        return nn.Sequential(
            nn.Linear(self.base_dim, self.lora_config.r),
            nn.ReLU(),
            nn.Dropout(self.lora_config.dropout),
            nn.Linear(self.lora_config.r, self.base_dim)
        )
    
    def get_adapted_embedding(
        self,
        base_embedding: torch.Tensor,
        detected_regime: RegimeType
    ) -> torch.Tensor:
        """
        Apply regime-specific adapter to base embedding.
        
        Args:
            base_embedding: Frozen foundation model embedding
            detected_regime: Current market regime
            
        Returns:
            Adapted embedding for downstream heads
        """
        adapter = self.adapters.get(detected_regime)
        
        if adapter is None or not TORCH_AVAILABLE:
            return base_embedding
        
        # Apply adapter: residual connection preserves base signal
        adapted = base_embedding + adapter(base_embedding)
        return adapted


class ForecastRepresentationLayer:
    """
    Layer 2: Forecast & Representation Layer
    
    Manages trading-native multi-task heads and regime-conditioned adapters.
    Bridges foundation model outputs to trading-relevant predictions.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.heads: Optional[MultiTaskTradingHeads] = None
        self.adapter: Optional[RegimeConditionedAdapter] = None
        self._initialized = False
        
        # Cost threshold for edge calculation
        self.cost_threshold_bps = 5.0  # 5 basis points default
    
    def initialize(self, embedding_dim: int = 256) -> bool:
        """Initialize trading heads and adapters."""
        logger.info("Initializing Forecast & Representation Layer...")
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, using statistical fallback")
            self._initialized = True
            return True
        
        try:
            # Initialize multi-task heads
            head_config = TradingHeadConfig()
            self.heads = MultiTaskTradingHeads(
                embedding_dim=embedding_dim,
                head_config=head_config,
                use_ranking_loss=True
            )
            
            # Initialize regime-conditioned adapters
            if self.config.use_lora_adapters:
                lora_config = LoRAConfig(
                    r=self.config.lora_rank,
                    alpha=self.config.lora_alpha
                )
                self.adapter = RegimeConditionedAdapter(
                    base_model_dim=embedding_dim,
                    lora_config=lora_config,
                    regime_types=list(RegimeType)
                )
            
            self._initialized = True
            logger.info("Forecast & Representation Layer initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Layer 2: {e}")
            return False
    
    def generate_trading_predictions(
        self,
        foundation_forecasts: Dict[ModelType, FoundationForecast],
        market_data: MarketData,
        detected_regime: RegimeType = RegimeType.UNKNOWN
    ) -> TradingNativeHeads:
        """
        Generate trading-native predictions from foundation forecasts.
        
        Args:
            foundation_forecasts: Outputs from Layer 1
            market_data: Current market state
            detected_regime: Detected market regime
            
        Returns:
            TradingNativeHeads with all predictions
        """
        if not self._initialized:
            raise RuntimeError("ForecastRepresentationLayer not initialized")
        
        # Aggregate foundation embeddings
        combined_embedding = self._aggregate_embeddings(foundation_forecasts)
        
        if TORCH_AVAILABLE and self.heads is not None:
            # PyTorch path: use trained heads
            return self._generate_torch_predictions(
                combined_embedding, market_data, detected_regime
            )
        else:
            # Statistical fallback path
            return self._generate_statistical_predictions(
                foundation_forecasts, market_data
            )
    
    def _aggregate_embeddings(
        self,
        forecasts: Dict[ModelType, FoundationForecast]
    ) -> np.ndarray:
        """Aggregate embeddings from multiple foundation models."""
        embeddings = []
        
        for model_type, forecast in forecasts.items():
            if forecast.latent_embedding is not None:
                embeddings.append(forecast.latent_embedding)
            elif forecast.regime_encoding is not None:
                embeddings.append(forecast.regime_encoding)
        
        if not embeddings:
            # Fallback: create simple feature vector
            return np.zeros(64)
        
        # Weight by model confidence
        weights = []
        for model_type, forecast in forecasts.items():
            weights.append(forecast.model_confidence)
        
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Weighted average of embeddings
        max_len = max(len(e) for e in embeddings)
        padded = [np.pad(e, (0, max_len - len(e))) for e in embeddings]
        
        aggregated = np.average(padded, axis=0, weights=weights)
        return aggregated
    
    def _generate_torch_predictions(
        self,
        embedding: np.ndarray,
        market_data: MarketData,
        detected_regime: RegimeType
    ) -> TradingNativeHeads:
        """Generate predictions using PyTorch heads."""
        if not TORCH_AVAILABLE or self.heads is None:
            raise RuntimeError("PyTorch not available")
        
        # Convert to tensor
        embedding_tensor = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0)
        
        # Apply regime-conditioned adapter
        if self.adapter is not None:
            adapted_embedding = self.adapter.get_adapted_embedding(
                embedding_tensor, detected_regime
            )
        else:
            adapted_embedding = embedding_tensor
        
        # Forward through heads
        self.heads.eval()
        with torch.no_grad():
            predictions = self.heads(adapted_embedding)
        
        # Extract values
        signed_return = predictions['signed_return'].item()
        volatility = predictions['volatility'].item()
        drawdown_prob = predictions['drawdown_prob'].item()
        rank_score = predictions['rank_score'].item()
        cost_threshold_prob = predictions['cost_threshold_prob'].item()
        execution_difficulty = predictions['execution_difficulty'].item()
        edge_after_cost = predictions['edge_after_cost'].item()
        
        # Regime label from logits
        regime_idx = torch.argmax(predictions['regime_logits'], dim=-1).item()
        regime_label = list(RegimeType)[min(regime_idx, len(RegimeType) - 1)]
        
        # Tradability check
        tradable = (
            edge_after_cost > self.cost_threshold_bps / 10000 and
            execution_difficulty < 0.7 and
            drawdown_prob < 0.3
        )
        
        return TradingNativeHeads(
            expected_signed_return=signed_return,
            volatility_forecast=volatility,
            drawdown_risk_prob=drawdown_prob,
            rank_score=rank_score,
            prob_exceed_cost_threshold=cost_threshold_prob,
            regime_label=regime_label,
            execution_difficulty_score=execution_difficulty,
            edge_after_cost=edge_after_cost,
            tradable=tradable
        )
    
    def _generate_statistical_predictions(
        self,
        forecasts: Dict[ModelType, FoundationForecast],
        market_data: MarketData
    ) -> TradingNativeHeads:
        """Generate predictions using statistical aggregation."""
        
        if not forecasts:
            return TradingNativeHeads(
                expected_signed_return=0.0,
                volatility_forecast=0.5,
                drawdown_risk_prob=0.5,
                rank_score=0.0,
                prob_exceed_cost_threshold=0.5,
                regime_label=RegimeType.UNKNOWN,
                execution_difficulty_score=0.5,
                edge_after_cost=0.0,
                tradable=False
            )
        
        # Aggregate point predictions weighted by confidence
        total_weight = 0.0
        weighted_return = 0.0
        weighted_vol = 0.0
        
        for forecast in forecasts.values():
            weight = forecast.model_confidence
            # Implied return from point prediction
            current_price = market_data.ohlcv['close']
            implied_return = (forecast.point_prediction / current_price) - 1
            
            weighted_return += weight * implied_return
            weighted_vol += weight * (forecast.forecast_std / current_price)
            total_weight += weight
        
        if total_weight > 0:
            expected_return = weighted_return / total_weight
            volatility = weighted_vol / total_weight
        else:
            expected_return = 0.0
            volatility = 0.01
        
        # Estimate drawdown risk from volatility and forecast spread
        forecast_spread = max(forecasts.values(), key=lambda f: f.model_confidence).prediction_interval_width
        price = market_data.ohlcv['close']
        relative_spread = forecast_spread / price
        drawdown_prob = min(volatility * 10 + relative_spread, 0.99)
        
        # Cost threshold based on spread
        spread = market_data.bid_ask_spread or 0.001
        cost_threshold = 3 * spread  # Need 3x spread to be profitable
        prob_exceed = 1.0 - (volatility / cost_threshold) if cost_threshold > 0 else 0.5
        prob_exceed = max(0.0, min(1.0, prob_exceed))
        
        # Edge after cost
        estimated_cost = spread + 0.0002  # Spread + slippage estimate
        edge_after_cost = expected_return - estimated_cost
        
        # Execution difficulty
        execution_diff = 0.5
        if market_data.depth_imbalance:
            execution_diff = 0.3 + abs(market_data.depth_imbalance) * 0.4
        if market_data.bid_ask_spread:
            execution_diff += market_data.bid_ask_spread * 100  # Scale up
        execution_diff = min(execution_diff, 1.0)
        
        tradable = edge_after_cost > estimated_cost and execution_diff < 0.7
        
        return TradingNativeHeads(
            expected_signed_return=expected_return,
            volatility_forecast=volatility,
            drawdown_risk_prob=drawdown_prob,
            rank_score=np.sign(expected_return) * abs(expected_return) ** 0.5,
            prob_exceed_cost_threshold=prob_exceed,
            regime_label=RegimeType.UNKNOWN,
            execution_difficulty_score=execution_diff,
            edge_after_cost=edge_after_cost,
            tradable=tradable
        )
