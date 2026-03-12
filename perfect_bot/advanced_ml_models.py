"""
Perfect Bot - Phase 2 Advanced ML Models
XGBoost, LightGBM, and Ensemble methods
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import advanced ML libraries
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available. Install with: pip install lightgbm")


class AdvancedMLEnsemble:
    """
    Ensemble of advanced ML models for trading
    
    Models:
    - Random Forest (baseline)
    - XGBoost (gradient boosting)
    - LightGBM (fast gradient boosting)
    """
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        self.feature_importance = None
        
    def create_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for ML"""
        df = data.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages (multiple periods)
        for window in [5, 10, 20, 50, 100]:
            df[f'sma_{window}'] = df['close'].rolling(window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
            df[f'price_to_sma_{window}'] = df['close'] / df[f'sma_{window}']
        
        # Momentum indicators
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'roc_{period}'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period)
        
        # Volatility
        for window in [10, 20, 30]:
            df[f'volatility_{window}'] = df['returns'].rolling(window).std()
            df[f'volatility_ratio_{window}'] = df[f'volatility_{window}'] / df[f'volatility_{window}'].rolling(50).mean()
        
        # RSI (multiple periods)
        for period in [7, 14, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        for window in [10, 20, 30]:
            sma = df['close'].rolling(window).mean()
            std = df['close'].rolling(window).std()
            df[f'bb_upper_{window}'] = sma + (std * 2)
            df[f'bb_lower_{window}'] = sma - (std * 2)
            df[f'bb_width_{window}'] = (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}']) / sma
            df[f'bb_position_{window}'] = (df['close'] - df[f'bb_lower_{window}']) / (df[f'bb_upper_{window}'] - df[f'bb_lower_{window}'])
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(14).mean()
        df['atr_ratio'] = df['atr'] / df['close']
        
        # Volume features (if available)
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['volume_momentum'] = df['volume'] / df['volume'].shift(5)
        
        # Price patterns
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        df['inside_bar'] = ((df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))).astype(int)
        
        # Trend strength
        df['trend_strength'] = abs(df['sma_20'] - df['sma_50']) / df['close']
        
        return df
    
    def create_labels(self, data: pd.DataFrame, forward_periods: int = 5, threshold: float = 0.01) -> pd.Series:
        """Create labels for classification"""
        future_returns = data['close'].shift(-forward_periods) / data['close'] - 1
        labels = (future_returns > threshold).astype(int)
        return labels
    
    def prepare_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
        """Prepare features and labels"""
        df = self.create_advanced_features(data)
        labels = self.create_labels(df)
        
        # Select feature columns
        feature_cols = [col for col in df.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'returns', 'log_returns']]
        
        X = df[feature_cols].copy()
        valid_idx = X.dropna().index.intersection(labels.dropna().index)
        
        X = X.loc[valid_idx]
        y = labels.loc[valid_idx]
        
        return X, y, feature_cols
    
    def train_ensemble(self, X_train, y_train):
        """Train ensemble of models"""
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Random Forest (baseline)
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        self.models['random_forest'] = rf_model
        
        # XGBoost
        if XGBOOST_AVAILABLE:
            xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            xgb_model.fit(X_train_scaled, y_train)
            self.models['xgboost'] = xgb_model
        
        # LightGBM
        if LIGHTGBM_AVAILABLE:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
            lgb_model.fit(X_train_scaled, y_train)
            self.models['lightgbm'] = lgb_model
        
        # Create voting ensemble
        if len(self.models) > 1:
            estimators = [(name, model) for name, model in self.models.items()]
            self.ensemble = VotingClassifier(estimators=estimators, voting='soft')
            self.ensemble.fit(X_train_scaled, y_train)
        
        # Store feature importance (from Random Forest)
        self.feature_importance = pd.Series(
            rf_model.feature_importances_,
            index=X_train.columns
        ).sort_values(ascending=False)
        
        logger.info(f"Trained {len(self.models)} models")
    
    def predict(self, X):
        """Make predictions using ensemble"""
        X_scaled = self.scaler.transform(X)
        
        if hasattr(self, 'ensemble'):
            return self.ensemble.predict(X_scaled)
        else:
            # Use Random Forest if ensemble not available
            return self.models['random_forest'].predict(X_scaled)
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        X_scaled = self.scaler.transform(X)
        
        if hasattr(self, 'ensemble'):
            return self.ensemble.predict_proba(X_scaled)
        else:
            return self.models['random_forest'].predict_proba(X_scaled)
    
    def walk_forward_validation(self, data: pd.DataFrame, n_splits: int = 5) -> Dict:
        """Walk-forward validation"""
        X, y, feature_cols = self.prepare_data(data)
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        scores = []
        all_predictions = []
        all_actuals = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            self.train_ensemble(X_train, y_train)
            y_pred = self.predict(X_test)
            
            accuracy = (y_pred == y_test).mean()
            scores.append(accuracy)
            
            all_predictions.extend(y_pred)
            all_actuals.extend(y_test)
            
            logger.info(f"Fold {fold + 1}: Accuracy = {accuracy:.3f}")
        
        avg_accuracy = np.mean(scores)
        std_accuracy = np.std(scores)
        
        return {
            'avg_accuracy': avg_accuracy,
            'std_accuracy': std_accuracy,
            'scores': scores,
            'predictions': all_predictions,
            'actuals': all_actuals
        }


def test_advanced_ml():
    """Test advanced ML models"""
    print("="*70)
    print("ADVANCED ML MODELS TEST")
    print("="*70)
    
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    returns = np.random.randn(252) * 0.015
    prices = 100 * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(252) * 0.005),
        'high': prices * (1 + abs(np.random.randn(252)) * 0.01),
        'low': prices * (1 - abs(np.random.randn(252)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    # Test ensemble
    ensemble = AdvancedMLEnsemble()
    
    print("\n1. Creating advanced features...")
    X, y, feature_cols = ensemble.prepare_data(data)
    print(f"   Created {len(feature_cols)} features")
    print(f"   Dataset size: {len(X)} samples")
    
    print("\n2. Running walk-forward validation...")
    results = ensemble.walk_forward_validation(data, n_splits=5)
    
    print(f"\n   Average Accuracy: {results['avg_accuracy']:.3f} (+/- {results['std_accuracy']:.3f})")
    
    print("\n3. Top 10 features:")
    print(ensemble.feature_importance.head(10))
    
    print("\n" + "="*70)
    print("ADVANCED ML MODELS READY!")
    print("="*70)
    
    if results['avg_accuracy'] > 0.55:
        print("SUCCESS: Accuracy > 55%!")
    else:
        print(f"Note: Accuracy {results['avg_accuracy']:.1%} (target: >55%)")


if __name__ == "__main__":
    test_advanced_ml()
