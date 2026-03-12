import logging
logger = logging.getLogger(__name__)
"""Latent Space Analysis for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from loguru import logger
from sklearn.decomposition import PCA, FastICA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import numpy
import pandas


class LatentPatternRecognition:
    """Advanced pattern recognition using latent space analysis."""
    
    def __init__(self, latent_dim: int = 10):
        """Initialize latent pattern recognition.
        
        Args:
            latent_dim: Dimensionality of latent space
        """
        self.latent_dim = latent_dim
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=latent_dim)
        self.ica = FastICA(n_components=latent_dim, random_state=42)
        self.autoencoder = None
        self.is_fitted = False
        logger.info(f"Initialized LatentPatternRecognition with {latent_dim} dimensions")
    
    def fit_dimensionality_reduction(self, features: pd.DataFrame) -> Dict:
        """Fit dimensionality reduction models.
        
        Args:
            features: DataFrame with market features
            
        Returns:
            Dictionary with fitting results
        """
        # Prepare data
        X = self.scaler.fit_transform(features.dropna())
        
        # Fit PCA
        pca_components = self.pca.fit_transform(X)
        pca_variance_ratio = self.pca.explained_variance_ratio_
        
        # Fit ICA
        ica_components = self.ica.fit_transform(X)
        
        # Create autoencoder
        self.autoencoder = self._create_autoencoder(X.shape[1])
        
        # Train autoencoder
        autoencoder_loss = self._train_autoencoder(X)
        
        self.is_fitted = True
        
        return {
            'pca_variance_explained': pca_variance_ratio.sum(),
            'pca_components': pca_components,
            'ica_components': ica_components,
            'autoencoder_loss': autoencoder_loss,
            'n_features': X.shape[1],
            'n_samples': X.shape[0]
        }
    
    def transform_to_latent_space(self, features: pd.DataFrame, 
                                method: str = 'pca') -> np.ndarray:
        """Transform features to latent space.
        
        Args:
            features: DataFrame with market features
            method: Method to use ('pca', 'ica', 'autoencoder')
            
        Returns:
            Latent space representation
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before transformation")
        
        X = self.scaler.transform(features.dropna())
        
        if method == 'pca':
            return self.pca.transform(X)
        elif method == 'ica':
            return self.ica.transform(X)
        elif method == 'autoencoder':
            return self._encode_with_autoencoder(X)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def detect_latent_patterns(self, latent_features: np.ndarray, 
                             method: str = 'kmeans') -> Dict:
        """Detect patterns in latent space.
        
        Args:
            latent_features: Latent space features
            method: Clustering method ('kmeans', 'dbscan')
            
        Returns:
            Dictionary with pattern detection results
        """
        if method == 'kmeans':
            # Determine optimal number of clusters using elbow method
            n_clusters = self._find_optimal_clusters(latent_features)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(latent_features)
            
            return {
                'method': 'kmeans',
                'n_clusters': n_clusters,
                'cluster_labels': cluster_labels,
                'cluster_centers': kmeans.cluster_centers_,
                'inertia': kmeans.inertia_
            }
        
        elif method == 'dbscan':
            # Use DBSCAN for density-based clustering
            dbscan = DBSCAN(eps=0.5, min_samples=5)
            cluster_labels = dbscan.fit_predict(latent_features)
            
            n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)
            
            return {
                'method': 'dbscan',
                'n_clusters': n_clusters,
                'n_noise_points': n_noise,
                'cluster_labels': cluster_labels
            }
        
        else:
            raise ValueError(f"Unknown clustering method: {method}")
    
    def _create_autoencoder(self, input_dim: int) -> nn.Module:
        """Create autoencoder neural network."""
        class Autoencoder(nn.Module):
            def __init__(self, input_dim, latent_dim):
                super(Autoencoder, self).__init__()
                
                # Encoder
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, input_dim // 2),
                    nn.ReLU(),
                    nn.Linear(input_dim // 2, input_dim // 4),
                    nn.ReLU(),
                    nn.Linear(input_dim // 4, latent_dim)
                )
                
                # Decoder
                self.decoder = nn.Sequential(
                    nn.Linear(latent_dim, input_dim // 4),
                    nn.ReLU(),
                    nn.Linear(input_dim // 4, input_dim // 2),
                    nn.ReLU(),
                    nn.Linear(input_dim // 2, input_dim)
                )
            
            def forward(self, x):
                encoded = self.encoder(x)
                decoded = self.decoder(encoded)
                return decoded
            
            def encode(self, x):
                return self.encoder(x)
        
        return Autoencoder(input_dim, self.latent_dim)
    
    def _train_autoencoder(self, X: np.ndarray, epochs: int = 100) -> float:
        """Train the autoencoder."""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.autoencoder.to(device)
        
        # Convert to tensor
        X_tensor = torch.FloatTensor(X).to(device)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.autoencoder.parameters(), lr=0.001)
        
        # Training loop
        self.autoencoder.train()
        final_loss = 0
        
        for epoch in range(epochs):
            optimizer.zero_grad()
            
            # Forward pass
            reconstructed = self.autoencoder(X_tensor)
            loss = criterion(reconstructed, X_tensor)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            final_loss = loss.item()
            
            if epoch % 20 == 0:
                logger.debug(f"Autoencoder epoch {epoch}, loss: {final_loss:.6f}")
        
        self.autoencoder.eval()
        return final_loss
    
    def _encode_with_autoencoder(self, X: np.ndarray) -> np.ndarray:
        """Encode data using trained autoencoder."""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(device)
            encoded = self.autoencoder.encode(X_tensor)
            return encoded.cpu().numpy()
    
    def _find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10) -> int:
        """Find optimal number of clusters using elbow method."""
        inertias = []
        K_range = range(2, min(max_clusters + 1, len(X)))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Find elbow point
        if len(inertias) < 2:
            return 2
        
        # Calculate rate of change
        rates = []
        for i in range(1, len(inertias)):
            rate = (inertias[i-1] - inertias[i]) / inertias[i-1]
            rates.append(rate)
        
        # Find the point where rate of improvement slows down significantly
        if len(rates) >= 2:
            for i in range(1, len(rates)):
                if rates[i] < rates[i-1] * 0.5:  # 50% reduction in improvement
                    return K_range[i]
        
        # Default to middle value if no clear elbow
        return K_range[len(K_range) // 2]


class MarketStateAnalysis:
    """Analyze market states using latent space techniques."""
    
    def __init__(self):
        self.market_states = {}
        self.state_transitions = {}
        logger.info("Initialized MarketStateAnalysis")
    
    def create_market_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create comprehensive market features for latent analysis.
        
        Args:
            df: DataFrame with OHLC and volume data
            
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame(index=df.index)
        
        # Price-based features
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        features['price_momentum_5'] = df['close'].pct_change(5)
        features['price_momentum_20'] = df['close'].pct_change(20)
        
        # Volatility features
        features['volatility_5'] = features['returns'].rolling(5).std()
        features['volatility_20'] = features['returns'].rolling(20).std()
        features['volatility_ratio'] = features['volatility_5'] / features['volatility_20']
        
        # Range-based features
        features['true_range'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        features['range_ratio'] = features['true_range'] / df['close']
        
        # Volume features (if available)
        if 'volume' in df.columns:
            features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            features['volume_momentum'] = df['volume'].pct_change(5)
            features['price_volume_trend'] = (features['returns'] * df['volume']).rolling(10).sum()
        
        # Technical indicators
        features['rsi'] = self._calculate_rsi(df['close'])
        features['bb_position'] = self._calculate_bb_position(df['close'])
        features['macd_signal'] = self._calculate_macd_signal(df['close'])
        
        # Microstructure features
        features['body_size'] = abs(df['close'] - df['open']) / df['close']
        features['upper_shadow'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['close']
        features['lower_shadow'] = (np.minimum(df['open'], df['close']) - df['low']) / df['close']
        
        # Trend features
        features['sma_5'] = df['close'].rolling(5).mean()
        features['sma_20'] = df['close'].rolling(20).mean()
        features['trend_strength'] = (features['sma_5'] - features['sma_20']) / features['sma_20']
        
        return features.dropna()
    
    def identify_market_regimes(self, features: pd.DataFrame, 
                              latent_analyzer: LatentPatternRecognition) -> Dict:
        """Identify market regimes using latent space clustering.
        
        Args:
            features: Market features DataFrame
            latent_analyzer: Fitted latent pattern recognition model
            
        Returns:
            Dictionary with regime analysis
        """
        # Transform to latent space
        latent_features = latent_analyzer.transform_to_latent_space(features, 'pca')
        
        # Detect patterns/regimes
        regime_results = latent_analyzer.detect_latent_patterns(latent_features, 'kmeans')
        
        # Analyze regime characteristics
        regime_analysis = self._analyze_regime_characteristics(
            features, regime_results['cluster_labels']
        )
        
        # Calculate regime transitions
        transitions = self._calculate_regime_transitions(regime_results['cluster_labels'])
        
        return {
            'n_regimes': regime_results['n_clusters'],
            'regime_labels': regime_results['cluster_labels'],
            'regime_characteristics': regime_analysis,
            'regime_transitions': transitions,
            'latent_features': latent_features
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bb_position(self, prices: pd.Series, period: int = 20, std: int = 2) -> pd.Series:
        """Calculate Bollinger Band position."""
        sma = prices.rolling(period).mean()
        std_dev = prices.rolling(period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        # Position within bands (0 = lower band, 1 = upper band)
        bb_position = (prices - lower_band) / (upper_band - lower_band)
        return bb_position.clip(0, 1)
    
    def _calculate_macd_signal(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD signal."""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        return macd - signal
    
    def _analyze_regime_characteristics(self, features: pd.DataFrame, 
                                     regime_labels: np.ndarray) -> Dict:
        """Analyze characteristics of each regime."""
        regime_chars = {}
        
        for regime_id in np.unique(regime_labels):
            regime_mask = regime_labels == regime_id
            regime_data = features.iloc[regime_mask]
            
            if len(regime_data) > 0:
                regime_chars[f'regime_{regime_id}'] = {
                    'count': len(regime_data),
                    'avg_return': regime_data['returns'].mean(),
                    'volatility': regime_data['returns'].std(),
                    'avg_volume_ratio': regime_data.get('volume_ratio', pd.Series()).mean(),
                    'trend_strength': regime_data['trend_strength'].mean(),
                    'avg_rsi': regime_data['rsi'].mean(),
                    'regime_type': self._classify_regime_type(regime_data)
                }
        
        return regime_chars
    
    def _classify_regime_type(self, regime_data: pd.DataFrame) -> str:
        """Classify regime type based on characteristics."""
        avg_return = regime_data['returns'].mean()
        volatility = regime_data['returns'].std()
        trend_strength = regime_data['trend_strength'].mean()
        
        # Classification logic
        if abs(trend_strength) > 0.02:  # Strong trend
            if avg_return > 0:
                return 'bullish_trending'
            else:
                return 'bearish_trending'
        elif volatility > regime_data['volatility_20'].mean():
            return 'high_volatility_ranging'
        else:
            return 'low_volatility_ranging'
    
    def _calculate_regime_transitions(self, regime_labels: np.ndarray) -> Dict:
        """Calculate regime transition probabilities."""
        transitions = {}
        transition_counts = {}
        
        # Count transitions
        for i in range(1, len(regime_labels)):
            from_regime = regime_labels[i-1]
            to_regime = regime_labels[i]
            
            if from_regime not in transition_counts:
                transition_counts[from_regime] = {}
            
            if to_regime not in transition_counts[from_regime]:
                transition_counts[from_regime][to_regime] = 0
            
            transition_counts[from_regime][to_regime] += 1
        
        # Calculate probabilities
        for from_regime, to_regimes in transition_counts.items():
            total_transitions = sum(to_regimes.values())
            transitions[from_regime] = {
                to_regime: count / total_transitions
                for to_regime, count in to_regimes.items()
            }
        
        return transitions
