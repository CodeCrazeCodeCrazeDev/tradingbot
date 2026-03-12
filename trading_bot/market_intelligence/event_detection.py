import logging
logger = logging.getLogger(__name__)
"""Event Detection System for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
from datetime import datetime, timedelta
import scipy.stats as stats
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


class MarketEventDetector:
    """Detect significant market events and anomalies."""
    
    def __init__(self, sensitivity: float = 2.0):
        """Initialize the market event detector.
        
        Args:
            sensitivity: Sensitivity threshold for event detection (standard deviations)
        """
        try:
            self.sensitivity = sensitivity
            self.event_history = []
            self.baseline_metrics = {}
            logger.info(f"Initialized MarketEventDetector with sensitivity {sensitivity}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_price_gaps(self, df: pd.DataFrame, gap_threshold: float = 0.005) -> List[Dict]:
        """Detect price gaps between consecutive periods.
        
        Args:
            df: DataFrame with OHLC data
            gap_threshold: Minimum gap size as percentage of price
            
        Returns:
            List of detected gaps
        """
        try:
            gaps = []
        
            for i in range(1, len(df)):
                prev_close = df.iloc[i-1]['close']
                curr_open = df.iloc[i]['open']
            
                gap_size = abs(curr_open - prev_close) / prev_close
            
                if gap_size > gap_threshold:
                    gap_direction = 'up' if curr_open > prev_close else 'down'
                
                    gaps.append({
                        'timestamp': df.index[i],
                        'gap_size': gap_size,
                        'gap_direction': gap_direction,
                        'prev_close': prev_close,
                        'curr_open': curr_open,
                        'gap_points': abs(curr_open - prev_close)
                    })
        
            return gaps
        except Exception as e:
            logger.error(f"Error in detect_price_gaps: {e}")
            raise
    
    def detect_volume_spikes(self, volumes: pd.Series, 
                           multiplier: float = 3.0, 
                           window: int = 20) -> List[Dict]:
        """Detect unusual volume spikes.
        
        Args:
            volumes: Volume data series
            multiplier: Volume spike threshold as multiple of average
            window: Window for calculating average volume
            
        Returns:
            List of volume spike events
        """
        try:
            avg_volume = volumes.rolling(window=window).mean()
            volume_spikes = []
        
            for i, (timestamp, volume) in enumerate(volumes.items()):
                if i >= window and not pd.isna(avg_volume.iloc[i]):
                    if volume > avg_volume.iloc[i] * multiplier:
                        volume_spikes.append({
                            'timestamp': timestamp,
                            'volume': volume,
                            'avg_volume': avg_volume.iloc[i],
                            'spike_ratio': volume / avg_volume.iloc[i]
                        })
        
            return volume_spikes
        except Exception as e:
            logger.error(f"Error in detect_volume_spikes: {e}")
            raise
    
    def detect_volatility_breakouts(self, returns: pd.Series, 
                                  window: int = 20, 
                                  threshold: float = 2.0) -> List[Dict]:
        """Detect volatility breakouts.
        
        Args:
            returns: Price returns series
            window: Window for volatility calculation
            threshold: Breakout threshold in standard deviations
            
        Returns:
            List of volatility breakout events
        """
        try:
            rolling_vol = returns.rolling(window=window).std()
            vol_mean = rolling_vol.rolling(window=window*2).mean()
            vol_std = rolling_vol.rolling(window=window*2).std()
        
            breakouts = []
        
            for i, (timestamp, vol) in enumerate(rolling_vol.items()):
                if i >= window*3 and not pd.isna(vol_std.iloc[i]):
                    z_score = (vol - vol_mean.iloc[i]) / vol_std.iloc[i]
                
                    if abs(z_score) > threshold:
                        breakouts.append({
                            'timestamp': timestamp,
                            'volatility': vol,
                            'mean_volatility': vol_mean.iloc[i],
                            'z_score': z_score,
                            'breakout_type': 'high' if z_score > 0 else 'low'
                        })
        
            return breakouts
        except Exception as e:
            logger.error(f"Error in detect_volatility_breakouts: {e}")
            raise
    
    def detect_momentum_shifts(self, prices: pd.Series, 
                             short_window: int = 10, 
                             long_window: int = 30) -> List[Dict]:
        """Detect momentum shifts using moving average crossovers.
        
        Args:
            prices: Price series
            short_window: Short-term moving average window
            long_window: Long-term moving average window
            
        Returns:
            List of momentum shift events
        """
        try:
            short_ma = prices.rolling(window=short_window).mean()
            long_ma = prices.rolling(window=long_window).mean()
        
            # Detect crossovers
            momentum_shifts = []
            prev_signal = None
        
            for i, timestamp in enumerate(prices.index):
                if i >= long_window:
                    short_val = short_ma.iloc[i]
                    long_val = long_ma.iloc[i]
                
                    if not pd.isna(short_val) and not pd.isna(long_val):
                        current_signal = 'bullish' if short_val > long_val else 'bearish'
                    
                        if prev_signal and prev_signal != current_signal:
                            momentum_shifts.append({
                                'timestamp': timestamp,
                                'shift_type': current_signal,
                                'short_ma': short_val,
                                'long_ma': long_val,
                                'price': prices.iloc[i]
                            })
                    
                        prev_signal = current_signal
        
            return momentum_shifts
        except Exception as e:
            logger.error(f"Error in detect_momentum_shifts: {e}")
            raise


class EconomicEventDetector:
    """Detect and analyze economic events impact."""
    
    def __init__(self):
        try:
            self.economic_calendar = []
            self.event_impacts = {}
            logger.info("Initialized EconomicEventDetector")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_news_impact(self, price_data: pd.Series, 
                          news_timestamps: List[datetime], 
                          analysis_window: int = 60) -> List[Dict]:
        """Analyze price impact of news events.
        
        Args:
            price_data: Price series
            news_timestamps: List of news event timestamps
            analysis_window: Minutes to analyze after news
            
        Returns:
            List of news impact analyses
        """
        try:
            impacts = []
        
            for news_time in news_timestamps:
                # Find price data around news time
                start_time = news_time - timedelta(minutes=30)
                end_time = news_time + timedelta(minutes=analysis_window)
            
                # Filter price data
                mask = (price_data.index >= start_time) & (price_data.index <= end_time)
                event_prices = price_data[mask]
            
                if len(event_prices) > 2:
                    pre_news_price = event_prices.iloc[0]
                    post_news_price = event_prices.iloc[-1]
                    max_price = event_prices.max()
                    min_price = event_prices.min()
                
                    # Calculate impact metrics
                    immediate_impact = (event_prices.iloc[1] - pre_news_price) / pre_news_price
                    total_impact = (post_news_price - pre_news_price) / pre_news_price
                    max_excursion = max(
                        (max_price - pre_news_price) / pre_news_price,
                        (pre_news_price - min_price) / pre_news_price
                    )
                
                    impacts.append({
                        'news_timestamp': news_time,
                        'pre_news_price': pre_news_price,
                        'post_news_price': post_news_price,
                        'immediate_impact': immediate_impact,
                        'total_impact': total_impact,
                        'max_excursion': max_excursion,
                        'volatility_increase': event_prices.pct_change().std()
                    })
        
            return impacts
        except Exception as e:
            logger.error(f"Error in analyze_news_impact: {e}")
            raise
    
    def detect_central_bank_impact(self, price_data: pd.Series, 
                                 cb_announcements: List[Dict]) -> List[Dict]:
        """Detect central bank announcement impacts.
        
        Args:
            price_data: Price series
            cb_announcements: List of central bank announcements
            
        Returns:
            List of central bank impact analyses
        """
        try:
            impacts = []
        
            for announcement in cb_announcements:
                announcement_time = announcement['timestamp']
            
                # Analyze price movement around announcement
                impact_analysis = self.analyze_news_impact(
                    price_data, 
                    [announcement_time], 
                    analysis_window=120  # 2 hours for CB announcements
                )
            
                if impact_analysis:
                    impact = impact_analysis[0]
                    impact.update({
                        'announcement_type': announcement.get('type', 'unknown'),
                        'expected_rate': announcement.get('expected_rate'),
                        'actual_rate': announcement.get('actual_rate'),
                        'surprise_factor': announcement.get('surprise_factor', 0)
                    })
                    impacts.append(impact)
        
            return impacts
        except Exception as e:
            logger.error(f"Error in detect_central_bank_impact: {e}")
            raise


class AnomalyDetector:
    """Detect market anomalies using statistical methods."""
    
    def __init__(self, contamination: float = 0.1):
        """Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies in data
        """
        try:
            self.contamination = contamination
            self.scaler = StandardScaler()
            logger.info(f"Initialized AnomalyDetector with contamination {contamination}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_statistical_anomalies(self, data: pd.DataFrame, 
                                   method: str = 'isolation_forest') -> pd.Series:
        """Detect anomalies using statistical methods.
        
        Args:
            data: DataFrame with features for anomaly detection
            method: Method to use ('isolation_forest', 'local_outlier_factor', 'one_class_svm')
            
        Returns:
            Series indicating anomalies (True for anomaly)
        """
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.neighbors import LocalOutlierFactor
            from sklearn.svm import OneClassSVM
        
            # Prepare data
            X = self.scaler.fit_transform(data.dropna())
        
            # Select method
            if method == 'isolation_forest':
                detector = IsolationForest(contamination=self.contamination, random_state=42)
                predictions = detector.fit_predict(X)
            elif method == 'local_outlier_factor':
                detector = LocalOutlierFactor(contamination=self.contamination)
                predictions = detector.fit_predict(X)
            elif method == 'one_class_svm':
                detector = OneClassSVM(nu=self.contamination)
                predictions = detector.fit_predict(X)
            else:
                raise ValueError(f"Unknown method: {method}")
        
            # Convert predictions to boolean (True for anomaly)
            anomalies = pd.Series(predictions == -1, index=data.dropna().index)
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_statistical_anomalies: {e}")
            raise
    
    def detect_price_anomalies(self, prices: pd.Series, 
                             window: int = 30, 
                             threshold: float = 3.0) -> List[Dict]:
        """Detect price anomalies using z-score method.
        
        Args:
            prices: Price series
            window: Rolling window for statistics
            threshold: Z-score threshold for anomaly detection
            
        Returns:
            List of price anomalies
        """
        try:
            returns = prices.pct_change()
            rolling_mean = returns.rolling(window=window).mean()
            rolling_std = returns.rolling(window=window).std()
        
            z_scores = (returns - rolling_mean) / rolling_std
        
            anomalies = []
            for i, (timestamp, z_score) in enumerate(z_scores.items()):
                if abs(z_score) > threshold and not pd.isna(z_score):
                    anomalies.append({
                        'timestamp': timestamp,
                        'price': prices.iloc[i],
                        'return': returns.iloc[i],
                        'z_score': z_score,
                        'anomaly_type': 'positive' if z_score > 0 else 'negative'
                    })
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_price_anomalies: {e}")
            raise
    
    def detect_correlation_anomalies(self, asset_data: Dict[str, pd.Series], 
                                   window: int = 60, 
                                   threshold: float = 0.3) -> List[Dict]:
        """Detect anomalies in asset correlations.
        
        Args:
            asset_data: Dictionary of asset price series
            window: Rolling window for correlation calculation
            threshold: Threshold for correlation change detection
            
        Returns:
            List of correlation anomalies
        """
        # Calculate returns
        try:
            returns_data = {asset: prices.pct_change() for asset, prices in asset_data.items()}
            returns_df = pd.DataFrame(returns_data)
        
            # Calculate rolling correlations
            correlations = {}
            asset_pairs = []
        
            assets = list(returns_data.keys())
            for i in range(len(assets)):
                for j in range(i+1, len(assets)):
                    pair = f"{assets[i]}_{assets[j]}"
                    asset_pairs.append((assets[i], assets[j], pair))
                    correlations[pair] = returns_df[assets[i]].rolling(window=window).corr(returns_df[assets[j]])
        
            # Detect anomalies in correlations
            anomalies = []
            for asset1, asset2, pair in asset_pairs:
                corr_series = correlations[pair]
                corr_mean = corr_series.rolling(window=window*2).mean()
                corr_std = corr_series.rolling(window=window*2).std()
            
                for timestamp, corr in corr_series.items():
                    if not pd.isna(corr) and not pd.isna(corr_mean.get(timestamp)) and not pd.isna(corr_std.get(timestamp)):
                        z_score = abs(corr - corr_mean[timestamp]) / corr_std[timestamp]
                    
                        if z_score > threshold:
                            anomalies.append({
                                'timestamp': timestamp,
                                'asset_pair': f"{asset1}-{asset2}",
                                'correlation': corr,
                                'expected_correlation': corr_mean[timestamp],
                                'z_score': z_score,
                                'anomaly_severity': 'high' if z_score > threshold * 2 else 'medium'
                            })
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_correlation_anomalies: {e}")
            raise
    
    def detect_clustering_anomalies(self, features: pd.DataFrame, 
                                  eps: float = 0.5, 
                                  min_samples: int = 5) -> pd.Series:
        """Detect anomalies using DBSCAN clustering.
        
        Args:
            features: DataFrame with features for clustering
            eps: DBSCAN epsilon parameter
            min_samples: DBSCAN minimum samples parameter
            
        Returns:
            Series indicating anomalies (True for anomaly)
        """
        # Prepare data
        try:
            X = self.scaler.fit_transform(features.dropna())
        
            # Apply DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            cluster_labels = dbscan.fit_predict(X)
        
            # Points with label -1 are considered anomalies
            anomalies = pd.Series(cluster_labels == -1, index=features.dropna().index)
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_clustering_anomalies: {e}")
            raise
