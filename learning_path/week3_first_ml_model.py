"""
Week 3-4 Assignment: Build Your First ML Trading Model
Learn: Feature engineering, model training, cross-validation

Goal: Create a profitable ML-based trading strategy
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class MLTradingStrategy:
    """Machine Learning trading strategy with proper validation"""
    
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create trading features from OHLC data
        
        CRITICAL: Features must NOT use future information!
        """
        df = data.copy()
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = df['close'].rolling(window).mean()
            df[f'ema_{window}'] = df['close'].ewm(span=window).mean()
        
        # Price momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
        
        # Volatility
        df['volatility_10'] = df['returns'].rolling(10).std()
        df['volatility_20'] = df['returns'].rolling(20).std()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_diff'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Volume features
        if 'volume' in df.columns:
            df['volume_sma'] = df['volume'].rolling(20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price patterns
        df['higher_high'] = (df['high'] > df['high'].shift(1)).astype(int)
        df['lower_low'] = (df['low'] < df['low'].shift(1)).astype(int)
        
        # Trend strength
        df['trend_strength'] = abs(df['close'] - df['sma_50']) / df['sma_50']
        
        return df
    
    def create_labels(self, data: pd.DataFrame, forward_periods: int = 5, 
                     threshold: float = 0.01) -> pd.Series:
        """
        Create labels for classification
        
        Label = 1 if price increases by threshold% in next N periods
        Label = 0 otherwise
        """
        future_returns = data['close'].shift(-forward_periods) / data['close'] - 1
        labels = (future_returns > threshold).astype(int)
        return labels
    
    def prepare_data(self, data: pd.DataFrame, forward_periods: int = 5):
        """Prepare features and labels for training"""
        
        # Create features
        df = self.create_features(data)
        
        # Create labels
        labels = self.create_labels(df, forward_periods)
        
        # Select feature columns (exclude OHLC and intermediate calculations)
        feature_cols = [col for col in df.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'returns', 'log_returns']]
        
        # Remove rows with NaN
        df = df[feature_cols].copy()
        valid_idx = df.dropna().index.intersection(labels.dropna().index)
        
        X = df.loc[valid_idx]
        y = labels.loc[valid_idx]
        
        return X, y, feature_cols
    
    def train(self, X_train, y_train):
        """Train the model"""
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Initialize model
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        
        # Train
        self.model.fit(X_train_scaled, y_train)
        
        # Store feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.Series(
                self.model.feature_importances_,
                index=X_train.columns
            ).sort_values(ascending=False)
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Get prediction probabilities"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def walk_forward_validation(self, data: pd.DataFrame, n_splits: int = 5):
        """
        Walk-forward validation (proper time series validation)
        
        CRITICAL: Never train on future data!
        """
        X, y, feature_cols = self.prepare_data(data)
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        scores = []
        predictions_all = []
        actuals_all = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            # Train model
            self.train(X_train, y_train)
            
            # Predict
            y_pred = self.predict(X_test)
            
            # Calculate accuracy
            accuracy = (y_pred == y_test).mean()
            scores.append(accuracy)
            
            predictions_all.extend(y_pred)
            actuals_all.extend(y_test)
            
            print(f"Fold {fold + 1}: Accuracy = {accuracy:.3f}")
        
        print(f"\nAverage Accuracy: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
        
        # Final classification report
        print("\nOverall Classification Report:")
        print(classification_report(actuals_all, predictions_all))
        
        return scores
    
    def show_feature_importance(self, top_n: int = 10):
        """Display top N most important features"""
        if self.feature_importance is not None:
            print("\nTop Feature Importances:")
            print(self.feature_importance.head(top_n))


def example_ml_strategy():
    """Example: Train and test ML trading strategy"""
    
    print("="*70)
    print("ML TRADING STRATEGY EXAMPLE")
    print("="*70)
    
    # Generate sample data (1 year)
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
    
    # Simulate realistic price movement
    returns = np.random.randn(252) * 0.02
    prices = 100 * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'close': prices,
        'open': prices * (1 + np.random.randn(252) * 0.01),
        'high': prices * (1 + abs(np.random.randn(252)) * 0.01),
        'low': prices * (1 - abs(np.random.randn(252)) * 0.01),
        'volume': np.random.randint(1000, 10000, 252)
    }, index=dates)
    
    # Create and train strategy
    strategy = MLTradingStrategy(model_type='random_forest')
    
    print("\n1. Creating features...")
    X, y, feature_cols = strategy.prepare_data(data)
    print(f"   Created {len(feature_cols)} features")
    print(f"   Dataset size: {len(X)} samples")
    print(f"   Positive class: {y.sum()} ({y.mean()*100:.1f}%)")
    
    print("\n2. Running walk-forward validation...")
    scores = strategy.walk_forward_validation(data, n_splits=5)
    
    print("\n3. Feature importance...")
    strategy.show_feature_importance(top_n=10)
    
    # Backtest the strategy
    print("\n4. Backtesting ML strategy...")
    X, y, _ = strategy.prepare_data(data)
    
    # Train on first 80% of data
    split_idx = int(len(X) * 0.8)
    strategy.train(X.iloc[:split_idx], y.iloc[:split_idx])
    
    # Test on last 20%
    predictions = strategy.predict(X.iloc[split_idx:])
    probabilities = strategy.predict_proba(X.iloc[split_idx:])
    
    # Convert predictions to trading signals
    signals = pd.Series(0, index=X.iloc[split_idx:].index)
    signals[predictions == 1] = 1  # Buy signal
    
    # Calculate returns
    test_data = data.loc[signals.index]
    returns = test_data['close'].pct_change()
    strategy_returns = signals.shift(1) * returns
    
    cumulative_returns = (1 + strategy_returns).cumprod()
    total_return = (cumulative_returns.iloc[-1] - 1) * 100
    
    print(f"\nBacktest Results (Out-of-Sample):")
    print(f"  Total Return: {total_return:.2f}%")
    print(f"  Buy Signals: {(predictions == 1).sum()}")
    print(f"  Accuracy: {(predictions == y.iloc[split_idx:]).mean()*100:.1f}%")


if __name__ == "__main__":
    example_ml_strategy()
    
    print("\n" + "="*70)
    print("KEY LESSONS:")
    print("="*70)
    print("""
1. ALWAYS use walk-forward validation (not random split!)
2. Features must NOT use future information
3. Scale features before training
4. Check for class imbalance
5. Monitor feature importance
6. Test on out-of-sample data

EXERCISES:
1. Add more features (ATR, Stochastic, ADX)
2. Try different models (XGBoost, LightGBM)
3. Implement feature selection
4. Add hyperparameter optimization
5. Create ensemble of models
6. Implement online learning (update model with new data)

CHALLENGE: Build a model that achieves >55% accuracy on out-of-sample data
    """)
