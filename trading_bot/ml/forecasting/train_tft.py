"""
Training pipeline for Temporal Fusion Transformer

Handles data preparation, training, validation, and model persistence.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional
try:
    import yaml
except ImportError:
    yaml = None

from .tft_model import TFTForecaster, TFTConfig
import numpy
import pandas

logger = logging.getLogger(__name__)


class TFTTrainingPipeline:
    """
    Complete training pipeline for TFT forecasting
    
    Features:
    - Data loading and preprocessing
    - Walk-forward validation
    - Model training and evaluation
    - Model persistence and versioning
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.forecaster = None
        self.training_history = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            'data': {
                'source': 'mt5',
                'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'timeframe': '1H',
                'lookback_days': 730,  # 2 years
                'validation_days': 90,  # 3 months
            },
            'model': {
                'max_encoder_length': 168,
                'max_prediction_length': 24,
                'hidden_size': 64,
                'lstm_layers': 2,
                'attention_head_size': 4,
                'dropout': 0.1,
                'hidden_continuous_size': 16,
                'learning_rate': 0.03,
                'batch_size': 128,
                'max_epochs': 50,
            },
            'training': {
                'gpus': 0,
                'checkpoint_dir': 'models/tft/checkpoints',
                'model_dir': 'models/tft',
                'log_dir': 'logs/tft',
            }
        }
    
    def load_data(self) -> pd.DataFrame:
        """
        Load historical data for training
        
        Returns:
            DataFrame with OHLCV and technical indicators
        """
        logger.info("Loading historical data...")
        
        # In production, load from MT5 or database
        # For now, generate sample data
        data = self._generate_sample_data()
        
        logger.info(f"Loaded {len(data)} samples for {data['symbol'].nunique()} symbols")
        
        return data
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate sample data for testing"""
        symbols = self.config['data']['symbols']
        lookback_days = self.config['data']['lookback_days']
        
        # Generate hourly data
        n_hours = lookback_days * 24
        
        data = []
        for symbol in symbols:
            base_price = {'EURUSD': 1.08, 'GBPUSD': 1.25, 'USDJPY': 150.0}.get(symbol, 1.0)
            
            # Random walk for price
            returns = np.random.randn(n_hours) * 0.001
            prices = base_price * np.exp(np.cumsum(returns))
            
            for i in range(n_hours):
                timestamp = datetime.now() - timedelta(hours=n_hours-i)
                
                data.append({
                    'time_idx': i,
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'hour': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'is_market_open': 1 if 8 <= timestamp.hour <= 17 else 0,
                    'price': prices[i],
                    'volume': 1000 + np.random.randn() * 100,
                    'rsi': 50 + np.random.randn() * 15,
                    'macd': np.random.randn() * 0.001,
                    'atr': 0.001 + np.random.rand() * 0.0005,
                    'bb_upper': prices[i] * 1.01,
                    'bb_lower': prices[i] * 0.99,
                    'volume_ratio': 1.0 + np.random.randn() * 0.3,
                    'spread': 0.0001 + np.random.rand() * 0.0001,
                    'volatility': 0.01 + np.random.rand() * 0.005,
                })
            
            # Calculate returns
            df = pd.DataFrame(data)
            df['return'] = df.groupby('symbol')['price'].pct_change().fillna(0)
        
        return pd.DataFrame(data)
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess data for TFT
        
        - Handle missing values
        - Normalize features
        - Create time indices
        """
        logger.info("Preprocessing data...")
        
        # Sort by symbol and time
        data = data.sort_values(['symbol', 'time_idx']).reset_index(drop=True)
        
        # Fill missing values
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        data[numeric_cols] = data[numeric_cols].fillna(method='ffill').fillna(0)
        
        # Ensure time_idx is continuous per symbol
        for symbol in data['symbol'].unique():
            mask = data['symbol'] == symbol
            data.loc[mask, 'time_idx'] = range(mask.sum())
        
        # Calculate target (next hour return)
        data['return'] = data.groupby('symbol')['price'].pct_change().shift(-1).fillna(0)
        
        logger.info(f"Preprocessed {len(data)} samples")
        
        return data
    
    def train(self, data: Optional[pd.DataFrame] = None) -> TFTForecaster:
        """
        Train TFT model
        
        Args:
            data: Training data (if None, will load from source)
            
        Returns:
            Trained forecaster
        """
        if data is None:
            data = self.load_data()
        
        data = self.preprocess_data(data)
        
        # Create TFT config
        model_config = TFTConfig(**self.config['model'])
        
        # Initialize forecaster
        self.forecaster = TFTForecaster(model_config)
        
        # Prepare dataset
        logger.info("Preparing TFT dataset...")
        self.forecaster.prepare_dataset(data, target_column='return')
        
        # Train model
        logger.info("Training TFT model...")
        checkpoint_dir = self.config['training']['checkpoint_dir']
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        
        self.forecaster.train(
            gpus=self.config['training']['gpus'],
            checkpoint_path=checkpoint_dir
        )
        
        # Evaluate
        logger.info("Evaluating model...")
        metrics = self.forecaster.evaluate(data)
        
        # Save training history
        self.training_history.append({
            'timestamp': datetime.now(),
            'metrics': metrics,
            'config': self.config
        })
        
        # Save model
        model_dir = Path(self.config['training']['model_dir'])
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = model_dir / f"tft_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
        self.forecaster.save(str(model_path))
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Training complete! Metrics: {metrics}")
        
        return self.forecaster
    
    def walk_forward_validation(
        self,
        data: pd.DataFrame,
        n_splits: int = 5
    ) -> Dict[str, list]:
        """
        Perform walk-forward validation
        
        Args:
            data: Full dataset
            n_splits: Number of validation splits
            
        Returns:
            Dictionary of metrics for each split
        """
        logger.info(f"Starting walk-forward validation with {n_splits} splits...")
        
        results = {
            'mape': [],
            'rmse': [],
            'mae': [],
            'coverage_80': []
        }
        
        # Split data into chunks
        data = data.sort_values(['symbol', 'time_idx'])
        total_samples = len(data)
        chunk_size = total_samples // (n_splits + 1)
        
        for i in range(n_splits):
            logger.info(f"Validation split {i+1}/{n_splits}")
            
            # Training data: all data up to this point
            train_end = chunk_size * (i + 1)
            train_data = data.iloc[:train_end]
            
            # Validation data: next chunk
            val_start = train_end
            val_end = min(train_end + chunk_size, total_samples)
            val_data = data.iloc[val_start:val_end]
            
            # Train model
            model_config = TFTConfig(**self.config['model'])
            model_config.max_epochs = 10  # Fewer epochs for validation
            
            forecaster = TFTForecaster(model_config)
            forecaster.prepare_dataset(train_data, target_column='return')
            forecaster.train(gpus=self.config['training']['gpus'])
            
            # Evaluate on validation set
            metrics = forecaster.evaluate(val_data)
            
            for key in results.keys():
                results[key].append(metrics[key])
            
            logger.info(f"Split {i+1} metrics: {metrics}")
        
        # Calculate average metrics
        avg_metrics = {
            key: np.mean(values) for key, values in results.items()
        }
        
        logger.info(f"Average metrics across {n_splits} splits: {avg_metrics}")
        
        return results
    
    def load_latest_model(self) -> TFTForecaster:
        """Load the most recent trained model"""
        model_dir = Path(self.config['training']['model_dir'])
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {model_dir}")
        
        # Find latest model file
        model_files = list(model_dir.glob("tft_model_*.pt"))
        
        if not model_files:
            raise FileNotFoundError(f"No model files found in {model_dir}")
        
        latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
        
        logger.info(f"Loading model from {latest_model}")
        
        # Load model
        self.forecaster = TFTForecaster(TFTConfig())
        self.forecaster.load(str(latest_model))
        
        return self.forecaster


def main():
    """Main training script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize pipeline
    pipeline = TFTTrainingPipeline()
    
    # Load data
    data = pipeline.load_data()
    
    # Train model
    forecaster = pipeline.train(data)
    
    # Perform walk-forward validation
    results = pipeline.walk_forward_validation(data, n_splits=3)
    
    print("\n" + "="*50)
    logger.info("TFT Training Complete!")
    print("="*50)
    logger.info(f"MAPE: {np.mean(results['mape']):.2f}%")
    logger.info(f"RMSE: {np.mean(results['rmse']):.6f}")
    logger.info(f"MAE: {np.mean(results['mae']):.6f}")
    logger.info(f"Coverage (80%): {np.mean(results['coverage_80']):.2%}")
    print("="*50)


if __name__ == "__main__":
    main()
