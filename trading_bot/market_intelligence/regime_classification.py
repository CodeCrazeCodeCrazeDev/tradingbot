import logging
logger = logging.getLogger(__name__)
"""Advanced Market Regime Classification System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from enum import Enum
from datetime import datetime, timedelta
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
import warnings
import numpy
import pandas
warnings.filterwarnings('ignore')


class MarketRegime(Enum):
    """Market regime classifications."""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING_HIGH_VOL = "ranging_high_vol"
    RANGING_LOW_VOL = "ranging_low_vol"
    CRISIS = "crisis"
    RECOVERY = "recovery"
    EUPHORIA = "euphoria"
    CAPITULATION = "capitulation"


class RegimeFeatures(Enum):
    """Features used for regime classification."""
    VOLATILITY = "volatility"
    TREND_STRENGTH = "trend_strength"
    VOLUME_PROFILE = "volume_profile"
    CORRELATION = "correlation"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"


class MarketRegimeClassifier:
    """Advanced market regime classification using multiple methodologies."""
    
    def __init__(self):
        self.regime_history = []
        self.feature_scaler = StandardScaler()
        self.pca_transformer = PCA(n_components=5)
        self.regime_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        logger.info("Initialized MarketRegimeClassifier")
    
    def extract_regime_features(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """Extract comprehensive features for regime classification."""
        if len(df) < lookback:
            return {}
        
        features = {}
        
        # Price-based features
        returns = df['close'].pct_change().dropna()
        
        # Volatility features
        features['realized_volatility'] = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        features['volatility_regime'] = self._classify_volatility_regime(returns)
        features['garch_volatility'] = self._estimate_garch_volatility(returns)
        
        # Trend features
        features['trend_strength'] = self._calculate_trend_strength(df)
        features['trend_consistency'] = self._calculate_trend_consistency(df)
        features['breakout_frequency'] = self._calculate_breakout_frequency(df)
        
        # Volume features
        if 'volume' in df.columns:
            features['volume_trend'] = self._analyze_volume_trend(df)
            features['volume_volatility'] = df['volume'].rolling(20).std().iloc[-1]
            features['volume_price_correlation'] = returns.rolling(20).corr(
                df['volume'].pct_change()
            ).iloc[-1]
        
        # Momentum features
        features['momentum_score'] = self._calculate_momentum_score(df)
        features['mean_reversion_score'] = self._calculate_mean_reversion_score(df)
        features['autocorrelation'] = returns.rolling(20).apply(
            lambda x: x.autocorr(lag=1)
        ).iloc[-1]
        
        # Market structure features
        features['support_resistance_strength'] = self._calculate_sr_strength(df)
        features['range_efficiency'] = self._calculate_range_efficiency(df)
        features['fractal_dimension'] = self._calculate_fractal_dimension(df['close'])
        
        # Cross-asset features (if multiple symbols available)
        features['market_correlation'] = self._calculate_market_correlation(df)
        features['sector_rotation'] = self._detect_sector_rotation(df)
        
        return {k: v for k, v in features.items() if not pd.isna(v)}
    
    def classify_current_regime(self, df: pd.DataFrame) -> Dict:
        """Classify current market regime using multiple approaches."""
        features = self.extract_regime_features(df)
        
        if not features:
            return {'regime': MarketRegime.RANGING_LOW_VOL, 'confidence': 0.5}
        
        # Rule-based classification
        rule_based_regime = self._rule_based_classification(features)
        
        # Statistical clustering approach
        clustering_regime = self._clustering_based_classification(df)
        
        # ML-based classification (if trained)
        ml_regime = None
        if self.is_trained:
            ml_regime = self._ml_based_classification(features)
        
        # Ensemble approach
        final_regime = self._ensemble_regime_decision(
            rule_based_regime, clustering_regime, ml_regime
        )
        
        return {
            'regime': final_regime['regime'],
            'confidence': final_regime['confidence'],
            'features': features,
            'regime_probability': final_regime.get('probabilities', {}),
            'regime_components': {
                'rule_based': rule_based_regime,
                'clustering': clustering_regime,
                'ml_based': ml_regime
            }
        }
    
    def detect_regime_transitions(self, df: pd.DataFrame, 
                                window_size: int = 20) -> List[Dict]:
        """Detect regime transition points."""
        transitions = []
        
        if len(df) < window_size * 2:
            return transitions
        
        # Rolling regime classification
        regimes = []
        for i in range(window_size, len(df)):
            window_df = df.iloc[i-window_size:i]
            regime_info = self.classify_current_regime(window_df)
            regimes.append({
                'timestamp': df.index[i],
                'regime': regime_info['regime'],
                'confidence': regime_info['confidence']
            })
        
        # Detect transitions
        for i in range(1, len(regimes)):
            if regimes[i]['regime'] != regimes[i-1]['regime']:
                # Validate transition with confidence threshold
                if (regimes[i]['confidence'] > 0.7 and 
                    regimes[i-1]['confidence'] > 0.7):
                    
                    transitions.append({
                        'timestamp': regimes[i]['timestamp'],
                        'from_regime': regimes[i-1]['regime'],
                        'to_regime': regimes[i]['regime'],
                        'transition_strength': abs(regimes[i]['confidence'] - 
                                                 regimes[i-1]['confidence']),
                        'market_impact': self._estimate_transition_impact(
                            regimes[i-1]['regime'], regimes[i]['regime']
                        )
                    })
        
        return transitions
    
    def train_regime_classifier(self, historical_data: List[Dict]):
        """Train ML classifier on historical regime data."""
        if len(historical_data) < 100:
            logger.warning("Insufficient data for training regime classifier")
            return
        
        # Prepare training data
        X = []
        y = []
        
        for data_point in historical_data:
            features = data_point.get('features', {})
            regime = data_point.get('regime')
            
            if features and regime:
                feature_vector = [features.get(key, 0) for key in sorted(features.keys())]
                X.append(feature_vector)
                y.append(regime.value if isinstance(regime, MarketRegime) else regime)
        
        if len(X) < 50:
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(X)
        
        # Apply PCA
        X_pca = self.pca_transformer.fit_transform(X_scaled)
        
        # Train classifier
        self.regime_classifier.fit(X_pca, y)
        self.is_trained = True
        
        logger.info(f"Regime classifier trained on {len(X)} samples")
    
    def _classify_volatility_regime(self, returns: pd.Series) -> str:
        """Classify volatility regime."""
        vol = returns.rolling(20).std().iloc[-1] * np.sqrt(252)
        
        if vol > 0.25:
            return 'high_volatility'
        elif vol < 0.10:
            return 'low_volatility'
        else:
            return 'normal_volatility'
    
    def _estimate_garch_volatility(self, returns: pd.Series) -> float:
        """Estimate GARCH volatility (simplified)."""
        # Simplified GARCH(1,1) estimation
        returns_clean = returns.dropna()
        if len(returns_clean) < 20:
            return returns_clean.std()
        
        # Simple exponential smoothing as GARCH proxy
        alpha = 0.1
        variance = returns_clean.var()
        
        for ret in returns_clean[-20:]:
            variance = alpha * ret**2 + (1 - alpha) * variance
        
        return np.sqrt(variance * 252)
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate trend strength indicator."""
        if len(df) < 20:
            return 0.0
        
        # Linear regression slope
        prices = df['close'].values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        # Normalize by price level
        return slope / prices[-1] * 100
    
    def _calculate_trend_consistency(self, df: pd.DataFrame) -> float:
        """Calculate trend consistency score."""
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 10:
            return 0.0
        
        # Calculate percentage of returns in same direction as overall trend
        overall_trend = 1 if df['close'].iloc[-1] > df['close'].iloc[0] else -1
        consistent_moves = sum(1 for r in returns if np.sign(r) == overall_trend)
        
        return consistent_moves / len(returns)
    
    def _calculate_breakout_frequency(self, df: pd.DataFrame) -> float:
        """Calculate frequency of range breakouts."""
        if len(df) < 20:
            return 0.0
        
        # Rolling 20-period high/low
        rolling_high = df['high'].rolling(20).max()
        rolling_low = df['low'].rolling(20).min()
        
        # Count breakouts
        breakouts = 0
        for i in range(20, len(df)):
            if (df['high'].iloc[i] > rolling_high.iloc[i-1] or
                df['low'].iloc[i] < rolling_low.iloc[i-1]):
                breakouts += 1
        
        return breakouts / (len(df) - 20) if len(df) > 20 else 0
    
    def _analyze_volume_trend(self, df: pd.DataFrame) -> float:
        """Analyze volume trend."""
        if 'volume' not in df.columns or len(df) < 20:
            return 0.0
        
        volume = df['volume'].values
        x = np.arange(len(volume))
        slope = np.polyfit(x, volume, 1)[0]
        
        return slope / volume[-1] if volume[-1] > 0 else 0
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate momentum score."""
        if len(df) < 20:
            return 0.0
        
        # Multiple timeframe momentum
        mom_5 = (df['close'].iloc[-1] / df['close'].iloc[-6] - 1) * 100
        mom_10 = (df['close'].iloc[-1] / df['close'].iloc[-11] - 1) * 100
        mom_20 = (df['close'].iloc[-1] / df['close'].iloc[-21] - 1) * 100
        
        # Weighted average
        return (mom_5 * 0.5 + mom_10 * 0.3 + mom_20 * 0.2)
    
    def _calculate_mean_reversion_score(self, df: pd.DataFrame) -> float:
        """Calculate mean reversion tendency."""
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 20:
            return 0.0
        
        # Hurst exponent estimation (simplified)
        lags = range(2, 20)
        tau = [np.sqrt(np.std(np.subtract(returns[lag:], returns[:-lag]))) 
               for lag in lags]
        
        # Linear regression on log-log plot
        log_lags = np.log(lags)
        log_tau = np.log(tau)
        
        hurst = np.polyfit(log_lags, log_tau, 1)[0]
        
        # Convert to mean reversion score (H < 0.5 indicates mean reversion)
        return max(0, 0.5 - hurst) * 2
    
    def _calculate_sr_strength(self, df: pd.DataFrame) -> float:
        """Calculate support/resistance strength."""
        if len(df) < 50:
            return 0.0
        
        # Find local maxima and minima
        highs = df['high'].rolling(5).max()
        lows = df['low'].rolling(5).min()
        
        # Count touches at similar levels
        price_levels = []
        for i in range(5, len(df)-5):
            if df['high'].iloc[i] == highs.iloc[i]:
                price_levels.append(df['high'].iloc[i])
            if df['low'].iloc[i] == lows.iloc[i]:
                price_levels.append(df['low'].iloc[i])
        
        if not price_levels:
            return 0.0
        
        # Cluster similar price levels
        price_array = np.array(price_levels).reshape(-1, 1)
        
        try:
            kmeans = KMeans(n_clusters=min(5, len(price_levels)), random_state=42)
            clusters = kmeans.fit_predict(price_array)
            
            # Calculate strength based on cluster sizes
            unique, counts = np.unique(clusters, return_counts=True)
            max_cluster_size = max(counts)
            
            return max_cluster_size / len(price_levels)
        except Exception:
            return 0.0
    
    def _calculate_range_efficiency(self, df: pd.DataFrame) -> float:
        """Calculate range trading efficiency."""
        if len(df) < 20:
            return 0.0
        
        # Price movement vs range
        price_move = abs(df['close'].iloc[-1] - df['close'].iloc[0])
        total_range = df['high'].max() - df['low'].min()
        
        return price_move / total_range if total_range > 0 else 0
    
    def _calculate_fractal_dimension(self, prices: pd.Series) -> float:
        """Calculate fractal dimension (Hurst exponent)."""
        if len(prices) < 20:
            return 1.5
        
        # Simplified fractal dimension calculation
        N = len(prices)
        
        # Calculate range statistics
        mean_price = prices.mean()
        cumsum = (prices - mean_price).cumsum()
        
        R = cumsum.max() - cumsum.min()
        S = prices.std()
        
        if S == 0:
            return 1.5
        
        # Rescaled range
        rs = R / S
        
        # Hurst exponent approximation
        hurst = np.log(rs) / np.log(N)
        
        # Convert to fractal dimension
        return 2 - hurst
    
    def _calculate_market_correlation(self, df: pd.DataFrame) -> float:
        """Calculate market correlation (simplified)."""
        # This would typically use multiple assets
        # For now, return autocorrelation
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 20:
            return 0.0
        
        return returns.rolling(20).apply(lambda x: x.autocorr(lag=1)).iloc[-1]
    
    def _detect_sector_rotation(self, df: pd.DataFrame) -> float:
        """Detect sector rotation patterns (simplified)."""
        # Simplified sector rotation indicator
        # In practice, this would analyze multiple sector ETFs
        
        # Use volume as proxy for rotation activity
        if 'volume' not in df.columns:
            return 0.0
        
        volume_trend = df['volume'].rolling(20).mean().pct_change().iloc[-1]
        return abs(volume_trend) if not pd.isna(volume_trend) else 0.0
    
    def _rule_based_classification(self, features: Dict) -> Dict:
        """Rule-based regime classification."""
        volatility = features.get('realized_volatility', 0.15)
        trend_strength = features.get('trend_strength', 0)
        momentum = features.get('momentum_score', 0)
        
        # Classification rules
        if volatility > 0.3:
            if abs(momentum) > 5:
                regime = MarketRegime.CRISIS
            else:
                regime = MarketRegime.RANGING_HIGH_VOL
        elif volatility < 0.1:
            if abs(trend_strength) > 0.1:
                regime = MarketRegime.TRENDING_BULL if trend_strength > 0 else MarketRegime.TRENDING_BEAR
            else:
                regime = MarketRegime.RANGING_LOW_VOL
        else:
            if momentum > 10:
                regime = MarketRegime.EUPHORIA
            elif momentum < -10:
                regime = MarketRegime.CAPITULATION
            elif abs(trend_strength) > 0.05:
                regime = MarketRegime.TRENDING_BULL if trend_strength > 0 else MarketRegime.TRENDING_BEAR
            else:
                regime = MarketRegime.RECOVERY
        
        return {'regime': regime, 'confidence': 0.7}
    
    def _clustering_based_classification(self, df: pd.DataFrame) -> Dict:
        """Clustering-based regime classification."""
        if len(df) < 50:
            return {'regime': MarketRegime.RANGING_LOW_VOL, 'confidence': 0.5}
        
        # Extract features for clustering
        returns = df['close'].pct_change().dropna()
        
        # Create feature matrix
        features = []
        window_size = 20
        
        for i in range(window_size, len(returns)):
            window_returns = returns.iloc[i-window_size:i]
            
            feature_vector = [
                window_returns.mean(),
                window_returns.std(),
                window_returns.skew(),
                window_returns.kurtosis(),
                window_returns.autocorr(lag=1) if len(window_returns) > 1 else 0
            ]
            
            features.append(feature_vector)
        
        if len(features) < 10:
            return {'regime': MarketRegime.RANGING_LOW_VOL, 'confidence': 0.5}
        
        # Perform clustering
        features_array = np.array(features)
        features_scaled = StandardScaler().fit_transform(features_array)
        
        try:
            kmeans = KMeans(n_clusters=4, random_state=42)
            clusters = kmeans.fit_predict(features_scaled)
            
            # Classify current regime based on latest cluster
            current_cluster = clusters[-1]
            
            # Map clusters to regimes (simplified)
            cluster_to_regime = {
                0: MarketRegime.TRENDING_BULL,
                1: MarketRegime.TRENDING_BEAR,
                2: MarketRegime.RANGING_HIGH_VOL,
                3: MarketRegime.RANGING_LOW_VOL
            }
            
            regime = cluster_to_regime.get(current_cluster, MarketRegime.RANGING_LOW_VOL)
            
            return {'regime': regime, 'confidence': 0.6}
            
        except Exception:
            return {'regime': MarketRegime.RANGING_LOW_VOL, 'confidence': 0.5}
    
    def _ml_based_classification(self, features: Dict) -> Dict:
        """ML-based regime classification."""
        if not self.is_trained:
            return None
        
        # Prepare feature vector
        feature_vector = [features.get(key, 0) for key in sorted(features.keys())]
        
        try:
            # Scale and transform
            X_scaled = self.feature_scaler.transform([feature_vector])
            X_pca = self.pca_transformer.transform(X_scaled)
            
            # Predict
            regime_pred = self.regime_classifier.predict(X_pca)[0]
            probabilities = self.regime_classifier.predict_proba(X_pca)[0]
            
            # Get regime enum
            regime = MarketRegime(regime_pred)
            confidence = max(probabilities)
            
            return {
                'regime': regime,
                'confidence': confidence,
                'probabilities': dict(zip(self.regime_classifier.classes_, probabilities))
            }
            
        except Exception:
            return None
    
    def _ensemble_regime_decision(self, rule_based: Dict, 
                                clustering: Dict, ml_based: Optional[Dict]) -> Dict:
        """Combine multiple regime classifications."""
        regimes = [rule_based, clustering]
        if ml_based:
            regimes.append(ml_based)
        
        # Weighted voting
        regime_votes = {}
        total_weight = 0
        
        for i, regime_result in enumerate(regimes):
            regime = regime_result['regime']
            confidence = regime_result['confidence']
            
            # Weight based on method and confidence
            if i == 0:  # Rule-based
                weight = 0.4 * confidence
            elif i == 1:  # Clustering
                weight = 0.3 * confidence
            else:  # ML-based
                weight = 0.3 * confidence
            
            regime_votes[regime] = regime_votes.get(regime, 0) + weight
            total_weight += weight
        
        # Select regime with highest weighted vote
        best_regime = max(regime_votes, key=regime_votes.get)
        final_confidence = regime_votes[best_regime] / total_weight if total_weight > 0 else 0.5
        
        return {
            'regime': best_regime,
            'confidence': final_confidence,
            'probabilities': {k: v/total_weight for k, v in regime_votes.items()}
        }
    
    def _estimate_transition_impact(self, from_regime: MarketRegime, 
                                  to_regime: MarketRegime) -> str:
        """Estimate market impact of regime transition."""
        high_impact_transitions = [
            (MarketRegime.RANGING_LOW_VOL, MarketRegime.CRISIS),
            (MarketRegime.TRENDING_BULL, MarketRegime.CAPITULATION),
            (MarketRegime.EUPHORIA, MarketRegime.CRISIS)
        ]
        
        medium_impact_transitions = [
            (MarketRegime.TRENDING_BULL, MarketRegime.RANGING_HIGH_VOL),
            (MarketRegime.RANGING_LOW_VOL, MarketRegime.TRENDING_BEAR),
            (MarketRegime.RECOVERY, MarketRegime.TRENDING_BULL)
        ]
        
        if (from_regime, to_regime) in high_impact_transitions:
            return 'high'
        elif (from_regime, to_regime) in medium_impact_transitions:
            return 'medium'
        else:
            return 'low'


class EconomicCycleAwareness:
    """Economic cycle awareness and integration."""
    
    def __init__(self):
        self.cycle_indicators = {}
        self.cycle_history = []
        logger.info("Initialized EconomicCycleAwareness")
    
    def analyze_economic_cycle_stage(self, economic_data: Dict) -> Dict:
        """Analyze current economic cycle stage."""
        # Simplified economic cycle analysis
        gdp_growth = economic_data.get('gdp_growth', 0)
        unemployment = economic_data.get('unemployment', 5)
        inflation = economic_data.get('inflation', 2)
        interest_rates = economic_data.get('interest_rates', 2)
        
        # Cycle stage classification
        if gdp_growth > 3 and unemployment < 4:
            stage = 'expansion'
        elif gdp_growth < 0 and unemployment > 7:
            stage = 'recession'
        elif gdp_growth > 0 and unemployment > 6:
            stage = 'recovery'
        else:
            stage = 'peak'
        
        return {
            'cycle_stage': stage,
            'indicators': {
                'gdp_growth': gdp_growth,
                'unemployment': unemployment,
                'inflation': inflation,
                'interest_rates': interest_rates
            },
            'market_implications': self._get_market_implications(stage)
        }
    
    def _get_market_implications(self, cycle_stage: str) -> Dict:
        """Get market implications for economic cycle stage."""
        implications = {
            'expansion': {
                'equity_outlook': 'positive',
                'bond_outlook': 'negative',
                'volatility_expectation': 'low',
                'sector_rotation': 'cyclicals_outperform'
            },
            'peak': {
                'equity_outlook': 'cautious',
                'bond_outlook': 'neutral',
                'volatility_expectation': 'increasing',
                'sector_rotation': 'defensive_rotation'
            },
            'recession': {
                'equity_outlook': 'negative',
                'bond_outlook': 'positive',
                'volatility_expectation': 'high',
                'sector_rotation': 'flight_to_quality'
            },
            'recovery': {
                'equity_outlook': 'improving',
                'bond_outlook': 'neutral',
                'volatility_expectation': 'decreasing',
                'sector_rotation': 'growth_revival'
            }
        }
        
        return implications.get(cycle_stage, {})


class RegimeBasedRiskManagement:
    """Regime-based risk management system."""
    
    def __init__(self):
        self.risk_adjustments = {}
        logger.info("Initialized RegimeBasedRiskManagement")
    
    def adjust_risk_parameters(self, current_regime: MarketRegime, 
                             base_risk_params: Dict) -> Dict:
        """Adjust risk parameters based on current market regime."""
        # Regime-specific risk multipliers
        regime_multipliers = {
            MarketRegime.TRENDING_BULL: {'position_size': 1.2, 'stop_loss': 0.8, 'take_profit': 1.3},
            MarketRegime.TRENDING_BEAR: {'position_size': 0.8, 'stop_loss': 0.7, 'take_profit': 1.1},
            MarketRegime.RANGING_HIGH_VOL: {'position_size': 0.6, 'stop_loss': 0.6, 'take_profit': 0.8},
            MarketRegime.RANGING_LOW_VOL: {'position_size': 1.0, 'stop_loss': 1.0, 'take_profit': 1.0},
            MarketRegime.CRISIS: {'position_size': 0.3, 'stop_loss': 0.5, 'take_profit': 0.6},
            MarketRegime.RECOVERY: {'position_size': 0.9, 'stop_loss': 0.9, 'take_profit': 1.2},
            MarketRegime.EUPHORIA: {'position_size': 0.7, 'stop_loss': 0.8, 'take_profit': 0.9},
            MarketRegime.CAPITULATION: {'position_size': 0.4, 'stop_loss': 0.6, 'take_profit': 1.5}
        }
        
        multipliers = regime_multipliers.get(current_regime, {'position_size': 1.0, 'stop_loss': 1.0, 'take_profit': 1.0})
        
        adjusted_params = {}
        for param, value in base_risk_params.items():
            if param in multipliers:
                adjusted_params[param] = value * multipliers[param]
            else:
                adjusted_params[param] = value
        
        return adjusted_params
