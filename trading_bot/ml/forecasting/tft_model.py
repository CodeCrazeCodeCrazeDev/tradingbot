"""
Temporal Fusion Transformer (TFT) for Multi-Horizon Probabilistic Forecasting

Based on: "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting"
arXiv: https://arxiv.org/abs/1912.09363

Provides interpretable, probabilistic multi-horizon forecasts with attention mechanisms.
"""

import torch
import torch.nn as nn
import pytorch_lightning as pl
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet, QuantileLoss
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.metrics import SMAPE, MAE, RMSE
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TFTConfig:
    """Configuration for TFT model"""
    # Data parameters
    max_encoder_length: int = 168  # 1 week of hourly data
    max_prediction_length: int = 24  # Predict next 24 hours
    
    # Model architecture
    hidden_size: int = 64
    lstm_layers: int = 2
    attention_head_size: int = 4
    dropout: float = 0.1
    hidden_continuous_size: int = 16
    
    # Training parameters
    learning_rate: float = 0.03
    batch_size: int = 128
    max_epochs: int = 50
    gradient_clip_val: float = 0.1
    
    # Quantiles for probabilistic forecasting
    quantiles: List[float] = None
    
    def __post_init__(self):
        try:
            if self.quantiles is None:
                self.quantiles = [0.1, 0.5, 0.9]  # 10th, 50th, 90th percentiles
        except Exception as e:
            logger.error(f"Error in __post_init__: {e}")
            raise


class TFTForecaster:
    """
    Temporal Fusion Transformer for price forecasting
    
    Features:
    - Multi-horizon probabilistic forecasts
    - Interpretable attention mechanisms
    - Handles static, known, and observed covariates
    - Quantile predictions for uncertainty estimation
    """
    
    def __init__(self, config: TFTConfig):
        try:
            self.config = config
            self.model = None
            self.training_data = None
            self.validation_data = None
            self.trainer = None
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def prepare_dataset(
        self,
        data: pd.DataFrame,
        target_column: str = 'return',
        time_idx_column: str = 'time_idx',
        group_ids: List[str] = None
    ) -> Tuple[TimeSeriesDataSet, TimeSeriesDataSet]:
        """
        Prepare time series dataset for TFT
        
        Args:
            data: DataFrame with columns [time_idx, symbol, price, volume, features...]
            target_column: Column to predict
            time_idx_column: Time index column
            group_ids: Columns identifying different time series (e.g., ['symbol'])
            
        Returns:
            Training and validation datasets
        """
        try:
            if group_ids is None:
                group_ids = ['symbol']
            
            # Define static features (don't change over time)
            static_categoricals = group_ids
            static_reals = []
        
            # Define known covariates (known in advance)
            time_varying_known_categoricals = ['hour', 'day_of_week', 'is_market_open']
            time_varying_known_reals = [time_idx_column]
        
            # Define observed covariates (only known up to present)
            time_varying_unknown_categoricals = []
            time_varying_unknown_reals = [
                'price', 'volume', 'rsi', 'macd', 'atr', 'bb_upper', 'bb_lower',
                'volume_ratio', 'spread', 'volatility'
            ]
        
            # Filter to only include columns that exist
            time_varying_unknown_reals = [
                col for col in time_varying_unknown_reals if col in data.columns
            ]
        
            # Create training dataset
            max_encoder_length = self.config.max_encoder_length
            max_prediction_length = self.config.max_prediction_length
        
            training_cutoff = data[time_idx_column].max() - max_prediction_length
        
            training = TimeSeriesDataSet(
                data[lambda x: x[time_idx_column] <= training_cutoff],
                time_idx=time_idx_column,
                target=target_column,
                group_ids=group_ids,
                min_encoder_length=max_encoder_length // 2,
                max_encoder_length=max_encoder_length,
                min_prediction_length=1,
                max_prediction_length=max_prediction_length,
                static_categoricals=static_categoricals,
                static_reals=static_reals,
                time_varying_known_categoricals=time_varying_known_categoricals,
                time_varying_known_reals=time_varying_known_reals,
                time_varying_unknown_categoricals=time_varying_unknown_categoricals,
                time_varying_unknown_reals=time_varying_unknown_reals,
                target_normalizer=GroupNormalizer(
                    groups=group_ids, transformation="softplus"
                ),
                add_relative_time_idx=True,
                add_target_scales=True,
                add_encoder_length=True,
            )
        
            # Create validation dataset
            validation = TimeSeriesDataSet.from_dataset(
                training,
                data,
                predict=True,
                stop_randomization=True
            )
        
            self.training_data = training
            self.validation_data = validation
        
            logger.info(f"Training dataset: {len(training)} samples")
            logger.info(f"Validation dataset: {len(validation)} samples")
        
            return training, validation
        except Exception as e:
            logger.error(f"Error in prepare_dataset: {e}")
            raise
    
    def build_model(self) -> TemporalFusionTransformer:
        """Build TFT model from configuration"""
        try:
            if self.training_data is None:
                raise ValueError("Must prepare dataset before building model")
        
            self.model = TemporalFusionTransformer.from_dataset(
                self.training_data,
                learning_rate=self.config.learning_rate,
                hidden_size=self.config.hidden_size,
                lstm_layers=self.config.lstm_layers,
                attention_head_size=self.config.attention_head_size,
                dropout=self.config.dropout,
                hidden_continuous_size=self.config.hidden_continuous_size,
                output_size=len(self.config.quantiles),
                loss=QuantileLoss(quantiles=self.config.quantiles),
                log_interval=10,
                reduce_on_plateau_patience=4,
            )
        
            logger.info(f"Built TFT model with {self.model.size()/1e6:.2f}M parameters")
        
            return self.model
        except Exception as e:
            logger.error(f"Error in build_model: {e}")
            raise
    
    def train(
        self,
        gpus: int = 0,
        checkpoint_path: Optional[str] = None
    ) -> pl.Trainer:
        """
        Train TFT model
        
        Args:
            gpus: Number of GPUs to use (0 for CPU)
            checkpoint_path: Path to save checkpoints
            
        Returns:
            PyTorch Lightning trainer
        """
        try:
            if self.model is None:
                self.build_model()
        
            # Create data loaders
            train_dataloader = self.training_data.to_dataloader(
                train=True,
                batch_size=self.config.batch_size,
                num_workers=0
            )
        
            val_dataloader = self.validation_data.to_dataloader(
                train=False,
                batch_size=self.config.batch_size * 10,
                num_workers=0
            )
        
            # Configure trainer
            trainer_kwargs = {
                'max_epochs': self.config.max_epochs,
                'gradient_clip_val': self.config.gradient_clip_val,
                'limit_train_batches': 50,  # Limit for faster training
                'enable_model_summary': True,
            }
        
            if gpus > 0:
                trainer_kwargs['gpus'] = gpus
                trainer_kwargs['accelerator'] = 'gpu'
        
            if checkpoint_path:
                from pytorch_lightning.callbacks import ModelCheckpoint
                checkpoint_callback = ModelCheckpoint(
                    dirpath=checkpoint_path,
                    filename='tft-{epoch:02d}-{val_loss:.2f}',
                    save_top_k=3,
                    monitor='val_loss',
                    mode='min'
                )
                trainer_kwargs['callbacks'] = [checkpoint_callback]
        
            self.trainer = pl.Trainer(**trainer_kwargs)
        
            # Train model
            logger.info("Starting TFT training...")
            self.trainer.fit(
                self.model,
                train_dataloaders=train_dataloader,
                val_dataloaders=val_dataloader
            )
        
            logger.info("Training complete!")
        
            return self.trainer
        except Exception as e:
            logger.error(f"Error in train: {e}")
            raise
    
    def predict(
        self,
        data: pd.DataFrame,
        return_attention: bool = False
    ) -> Dict[str, np.ndarray]:
        """
        Generate probabilistic forecasts
        
        Args:
            data: Input data
            return_attention: Whether to return attention weights
            
        Returns:
            Dictionary with predictions and optionally attention weights
        """
        try:
            if self.model is None:
                raise ValueError("Model not trained yet")
        
            # Create dataset for prediction
            predict_dataset = TimeSeriesDataSet.from_dataset(
                self.training_data,
                data,
                predict=True,
                stop_randomization=True
            )
        
            predict_dataloader = predict_dataset.to_dataloader(
                train=False,
                batch_size=self.config.batch_size * 10,
                num_workers=0
            )
        
            # Generate predictions
            self.model.eval()
            predictions = self.model.predict(
                predict_dataloader,
                mode="quantiles",
                return_x=return_attention
            )
        
            result = {
                'predictions': predictions.cpu().numpy() if torch.is_tensor(predictions) else predictions
            }
        
            # Extract attention weights if requested
            if return_attention:
                raw_predictions, x = self.model.predict(
                    predict_dataloader,
                    mode="raw",
                    return_x=True
                )
            
                interpretation = self.model.interpret_output(
                    raw_predictions,
                    reduction="sum"
                )
            
                result['attention'] = {
                    'encoder_attention': interpretation['encoder_attention'].cpu().numpy(),
                    'decoder_attention': interpretation['decoder_attention'].cpu().numpy(),
                    'static_variables': interpretation['static_variables'].cpu().numpy(),
                }
        
            return result
        except Exception as e:
            logger.error(f"Error in predict: {e}")
            raise
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Returns:
            Dictionary of metrics (MAPE, RMSE, MAE)
        """
        try:
            predictions = self.predict(data)['predictions']
        
            # Get actual values
            actual_dataset = TimeSeriesDataSet.from_dataset(
                self.training_data,
                data,
                predict=True,
                stop_randomization=True
            )
        
            actuals = []
            for batch in actual_dataset.to_dataloader(train=False, batch_size=len(actual_dataset)):
                actuals.append(batch[1][0])
            actuals = torch.cat(actuals).cpu().numpy()
        
            # Calculate metrics using median prediction
            median_pred = predictions[:, :, 1]  # 50th percentile
        
            # MAPE
            mape = np.mean(np.abs((actuals - median_pred) / (actuals + 1e-8))) * 100
        
            # RMSE
            rmse = np.sqrt(np.mean((actuals - median_pred) ** 2))
        
            # MAE
            mae = np.mean(np.abs(actuals - median_pred))
        
            # Calibration (coverage of 80% prediction interval)
            lower_bound = predictions[:, :, 0]  # 10th percentile
            upper_bound = predictions[:, :, 2]  # 90th percentile
            coverage = np.mean((actuals >= lower_bound) & (actuals <= upper_bound))
        
            metrics = {
                'mape': mape,
                'rmse': rmse,
                'mae': mae,
                'coverage_80': coverage
            }
        
            logger.info(f"Evaluation metrics: {metrics}")
        
            return metrics
        except Exception as e:
            logger.error(f"Error in evaluate: {e}")
            raise
    
    def save(self, path: str):
        """Save model to disk"""
        try:
            if self.model is None:
                raise ValueError("No model to save")
        
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'config': self.config,
                'training_data': self.training_data,
            }, save_path)
        
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error in save: {e}")
            raise
    
    def load(self, path: str):
        """Load model from disk"""
        try:
            checkpoint = torch.load(path)
        
            self.config = checkpoint['config']
            self.training_data = checkpoint['training_data']
        
            self.build_model()
            self.model.load_state_dict(checkpoint['model_state_dict'])
        
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error in load: {e}")
            raise


def create_sample_data(n_samples: int = 10000) -> pd.DataFrame:
    """Create sample data for testing"""
    try:
        np.random.seed(42)
    
        data = []
        for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
            for i in range(n_samples):
                data.append({
                    'time_idx': i,
                    'symbol': symbol,
                    'hour': i % 24,
                    'day_of_week': (i // 24) % 7,
                    'is_market_open': 1 if 8 <= (i % 24) <= 17 else 0,
                    'price': 1.0 + np.random.randn() * 0.01,
                    'volume': 1000 + np.random.randn() * 100,
                    'rsi': 50 + np.random.randn() * 10,
                    'macd': np.random.randn() * 0.001,
                    'atr': 0.001 + np.random.rand() * 0.0005,
                    'bb_upper': 1.01,
                    'bb_lower': 0.99,
                    'volume_ratio': 1.0 + np.random.randn() * 0.2,
                    'spread': 0.0001 + np.random.rand() * 0.0001,
                    'volatility': 0.01 + np.random.rand() * 0.005,
                    'return': np.random.randn() * 0.001,
                })
    
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error in create_sample_data: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    logger.info("Creating sample data...")
    data = create_sample_data(n_samples=5000)
    
    # Initialize forecaster
    config = TFTConfig(
        max_encoder_length=168,
        max_prediction_length=24,
        hidden_size=32,  # Smaller for demo
        max_epochs=5,  # Fewer epochs for demo
    )
    
    forecaster = TFTForecaster(config)
    
    # Prepare dataset
    logger.info("Preparing dataset...")
    training, validation = forecaster.prepare_dataset(data)
    
    # Train model
    logger.info("Training model...")
    forecaster.train(gpus=0)
    
    # Evaluate
    logger.info("Evaluating model...")
    metrics = forecaster.evaluate(data)
    logger.info(f"Metrics: {metrics}")
    
    # Generate predictions
    logger.info("Generating predictions...")
    predictions = forecaster.predict(data.tail(1000), return_attention=True)
    logger.info(f"Predictions shape: {predictions['predictions'].shape}")
    
    if 'attention' in predictions:
        logger.info(f"Attention weights available: {predictions['attention'].keys()}")
    
    logger.info("TFT forecaster demo complete!")
