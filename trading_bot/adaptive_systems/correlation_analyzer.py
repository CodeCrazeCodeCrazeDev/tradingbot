"""
Correlation Analysis System
Detects correlation breakdowns and regime changes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy.stats import pearsonr, spearmanr
from sklearn.covariance import GraphicalLassoCV
import networkx as nx
import numpy
import pandas

logger = logging.getLogger(__name__)

@dataclass
class CorrelationSignal:
    """Correlation analysis signal"""
    signal_type: str
    strength: float
    confidence: float
    timestamp: datetime
    assets: List[str]
    correlation: float
    zscore: float
    supporting_data: Dict
    metadata: Dict

class CorrelationAnalyzer:
    """
    Advanced correlation analysis system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Analysis parameters
            self.lookback_window = self.config.get('lookback_window', 100)
            self.short_window = self.config.get('short_window', 20)
            self.correlation_threshold = self.config.get('correlation_threshold', 0.7)
            self.breakdown_threshold = self.config.get('breakdown_threshold', 0.3)
        
            # State tracking
            self.correlation_history = {}
            self.correlation_network = None
            self.regime_history = []
        
            # Correlation models
            self.graphical_lasso = GraphicalLassoCV()
            self.covariance_matrix = None
            self.precision_matrix = None
        
            logger.info("Correlation Analyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_correlations(self, price_data: Dict[str, pd.DataFrame]) -> List[CorrelationSignal]:
        """
        Perform comprehensive correlation analysis
        """
        try:
            signals = []
        
            # Convert price data to returns
            returns_data = self._calculate_returns(price_data)
        
            # Update correlation matrices
            correlation_matrix = self._calculate_correlation_matrix(returns_data)
            self._update_correlation_network(correlation_matrix)
        
            # Analyze different correlation aspects
            signals.extend(self._analyze_correlation_breakdowns(correlation_matrix, returns_data))
            signals.extend(self._analyze_correlation_regimes(correlation_matrix))
            signals.extend(self._analyze_correlation_clusters(correlation_matrix))
            signals.extend(self._detect_lead_lag_relationships(returns_data))
        
            return signals
        except Exception as e:
            logger.error(f"Error in analyze_correlations: {e}")
            raise
    
    def _calculate_returns(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate returns for all assets
        """
        try:
            returns = {}
        
            for asset, data in price_data.items():
                if 'close' in data.columns and len(data) > 1:
                    returns[asset] = np.log(data['close']).diff().dropna()
        
            return pd.DataFrame(returns)
        except Exception as e:
            logger.error(f"Error in _calculate_returns: {e}")
            raise
    
    def _calculate_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix with multiple methods
        """
        # Pearson correlation (linear)
        try:
            pearson_corr = returns.corr(method='pearson')
        
            # Spearman correlation (rank-based)
            spearman_corr = returns.corr(method='spearman')
        
            # Combine correlations with weights
            correlation_matrix = 0.7 * pearson_corr + 0.3 * spearman_corr
        
            # Store in history
            timestamp = datetime.now()
            self.correlation_history[timestamp] = correlation_matrix
        
            # Clean old history
            cutoff = timestamp.timestamp() - (self.lookback_window * 86400)  # Convert days to seconds
            self.correlation_history = {
                t: v for t, v in self.correlation_history.items() 
                if t.timestamp() > cutoff
            }
        
            return correlation_matrix
        except Exception as e:
            logger.error(f"Error in _calculate_correlation_matrix: {e}")
            raise
    
    def _update_correlation_network(self, correlation_matrix: pd.DataFrame):
        """
        Update correlation network structure
        """
        # Create network from correlation matrix
        try:
            G = nx.Graph()
        
            # Add nodes
            for asset in correlation_matrix.index:
                G.add_node(asset)
        
            # Add edges with correlation as weight
            for i in range(len(correlation_matrix.index)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    asset1 = correlation_matrix.index[i]
                    asset2 = correlation_matrix.columns[j]
                    correlation = abs(correlation_matrix.iloc[i, j])
                
                    if correlation > self.correlation_threshold:
                        G.add_edge(asset1, asset2, weight=correlation)
        
            self.correlation_network = G
        except Exception as e:
            logger.error(f"Error in _update_correlation_network: {e}")
            raise
    
    def _analyze_correlation_breakdowns(self, current_corr: pd.DataFrame,
                                     returns: pd.DataFrame) -> List[CorrelationSignal]:
        """
        Analyze correlation breakdowns and anomalies
        """
        try:
            signals = []
        
            if len(self.correlation_history) < 2:
                return signals
        
            # Get historical correlation
            historical_corrs = list(self.correlation_history.values())[:-1]
            avg_historical_corr = sum(historical_corrs) / len(historical_corrs)
        
            # Calculate correlation changes
            for asset1 in current_corr.index:
                for asset2 in current_corr.columns:
                    if asset1 >= asset2:
                        continue
                
                    current_correlation = current_corr.loc[asset1, asset2]
                    historical_correlation = avg_historical_corr.loc[asset1, asset2]
                
                    # Check for correlation breakdown
                    if (abs(historical_correlation) > self.correlation_threshold and
                        abs(current_correlation - historical_correlation) > self.breakdown_threshold):
                    
                        # Calculate z-score of change
                        correlation_changes = [
                            corr.loc[asset1, asset2] - historical_correlation
                            for corr in historical_corrs
                        ]
                        zscore = self._calculate_zscore(
                            current_correlation - historical_correlation,
                            correlation_changes
                        )
                    
                        signals.append(CorrelationSignal(
                            signal_type="correlation_breakdown",
                            strength=abs(current_correlation - historical_correlation),
                            confidence=min(abs(zscore) / 3, 1.0),
                            timestamp=datetime.now(),
                            assets=[asset1, asset2],
                            correlation=current_correlation,
                            zscore=zscore,
                            supporting_data={
                                'historical_correlation': historical_correlation,
                                'correlation_change': current_correlation - historical_correlation,
                                'volatility': self._calculate_correlation_volatility(asset1, asset2)
                            },
                            metadata={'breakdown_type': 'regime_change'}
                        ))
                
                    # Check for correlation flip
                    if (historical_correlation * current_correlation < 0 and
                        abs(historical_correlation) > self.correlation_threshold):
                    
                        signals.append(CorrelationSignal(
                            signal_type="correlation_flip",
                            strength=abs(current_correlation - historical_correlation),
                            confidence=0.8,
                            timestamp=datetime.now(),
                            assets=[asset1, asset2],
                            correlation=current_correlation,
                            zscore=zscore,
                            supporting_data={
                                'historical_correlation': historical_correlation,
                                'flip_magnitude': abs(current_correlation) + abs(historical_correlation)
                            },
                            metadata={'breakdown_type': 'sign_change'}
                        ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_correlation_breakdowns: {e}")
            raise
    
    def _analyze_correlation_regimes(self, correlation_matrix: pd.DataFrame) -> List[CorrelationSignal]:
        """
        Analyze correlation regime changes
        """
        try:
            signals = []
        
            if len(self.correlation_history) < 10:
                return signals
        
            # Calculate average correlation
            avg_correlation = np.mean([
                np.mean(np.abs(corr.values[np.triu_indices_from(corr.values, k=1)]))
                for corr in self.correlation_history.values()
            ])
        
            current_avg = np.mean(np.abs(correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)]))
        
            # Detect regime changes
            if abs(current_avg - avg_correlation) > self.breakdown_threshold:
                signals.append(CorrelationSignal(
                    signal_type="correlation_regime",
                    strength=abs(current_avg - avg_correlation),
                    confidence=0.7,
                    timestamp=datetime.now(),
                    assets=list(correlation_matrix.index),
                    correlation=current_avg,
                    zscore=self._calculate_zscore(current_avg, [
                        np.mean(np.abs(corr.values[np.triu_indices_from(corr.values, k=1)]))
                        for corr in list(self.correlation_history.values())[:-1]
                    ]),
                    supporting_data={
                        'average_correlation': avg_correlation,
                        'regime_change': current_avg - avg_correlation,
                        'historical_regimes': self._identify_historical_regimes()
                    },
                    metadata={'regime_type': 'global'}
                ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_correlation_regimes: {e}")
            raise
    
    def _analyze_correlation_clusters(self, correlation_matrix: pd.DataFrame) -> List[CorrelationSignal]:
        """
        Analyze correlation-based clusters
        """
        try:
            signals = []
        
            if self.correlation_network is None:
                return signals
        
            # Find clusters using community detection
            communities = list(nx.community.greedy_modularity_communities(self.correlation_network))
        
            for i, community in enumerate(communities):
                # Calculate internal vs external correlations
                internal_corr = self._calculate_internal_correlation(correlation_matrix, community)
                external_corr = self._calculate_external_correlation(correlation_matrix, community)
            
                if internal_corr > self.correlation_threshold and internal_corr > 2 * external_corr:
                    signals.append(CorrelationSignal(
                        signal_type="correlation_cluster",
                        strength=internal_corr - external_corr,
                        confidence=0.7,
                        timestamp=datetime.now(),
                        assets=list(community),
                        correlation=internal_corr,
                        zscore=0,  # Not applicable for clusters
                        supporting_data={
                            'internal_correlation': internal_corr,
                            'external_correlation': external_corr,
                            'cluster_size': len(community)
                        },
                        metadata={'cluster_id': i}
                    ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_correlation_clusters: {e}")
            raise
    
    def _detect_lead_lag_relationships(self, returns: pd.DataFrame) -> List[CorrelationSignal]:
        """
        Detect lead-lag relationships between assets
        """
        try:
            signals = []
            max_lag = 5  # Maximum lag to consider
        
            for asset1 in returns.columns:
                for asset2 in returns.columns:
                    if asset1 >= asset2:
                        continue
                
                    # Calculate cross-correlation at different lags
                    cross_corr = []
                    for lag in range(-max_lag, max_lag + 1):
                        if lag < 0:
                            corr = returns[asset1].shift(-lag).corr(returns[asset2])
                        else:
                            corr = returns[asset1].corr(returns[asset2].shift(lag))
                        cross_corr.append((lag, corr))
                
                    # Find maximum correlation and corresponding lag
                    max_corr_lag, max_corr = max(cross_corr, key=lambda x: abs(x[1]))
                
                    if abs(max_corr) > self.correlation_threshold and abs(max_corr_lag) > 0:
                        signals.append(CorrelationSignal(
                            signal_type="lead_lag",
                            strength=abs(max_corr),
                            confidence=0.6,
                            timestamp=datetime.now(),
                            assets=[asset1, asset2],
                            correlation=max_corr,
                            zscore=0,  # Not applicable for lead-lag
                            supporting_data={
                                'lag': max_corr_lag,
                                'lead_asset': asset1 if max_corr_lag < 0 else asset2,
                                'lag_asset': asset2 if max_corr_lag < 0 else asset1,
                                'cross_correlations': dict(cross_corr)
                            },
                            metadata={'relationship_type': 'lead_lag'}
                        ))
        
            return signals
        except Exception as e:
            logger.error(f"Error in _detect_lead_lag_relationships: {e}")
            raise
    
    def _calculate_correlation_volatility(self, asset1: str, asset2: str) -> float:
        """
        Calculate volatility of correlation between two assets
        """
        try:
            if len(self.correlation_history) < 2:
                return 0
        
            correlations = [
                corr.loc[asset1, asset2]
                for corr in self.correlation_history.values()
            ]
        
            return np.std(correlations)
        except Exception as e:
            logger.error(f"Error in _calculate_correlation_volatility: {e}")
            raise
    
    def _identify_historical_regimes(self) -> List[Dict]:
        """
        Identify historical correlation regimes
        """
        try:
            if len(self.correlation_history) < 10:
                return []
        
            # Calculate average correlations over time
            avg_correlations = [
                (timestamp, np.mean(np.abs(corr.values[np.triu_indices_from(corr.values, k=1)])))
                for timestamp, corr in self.correlation_history.items()
            ]
        
            # Identify regime changes
            regimes = []
            current_regime = {
                'start': avg_correlations[0][0],
                'correlation': avg_correlations[0][1]
            }
        
            for timestamp, correlation in avg_correlations[1:]:
                if abs(correlation - current_regime['correlation']) > self.breakdown_threshold:
                    current_regime['end'] = timestamp
                    regimes.append(current_regime)
                    current_regime = {
                        'start': timestamp,
                        'correlation': correlation
                    }
        
            # Add last regime
            current_regime['end'] = avg_correlations[-1][0]
            regimes.append(current_regime)
        
            return regimes
        except Exception as e:
            logger.error(f"Error in _identify_historical_regimes: {e}")
            raise
    
    def _calculate_internal_correlation(self, correlation_matrix: pd.DataFrame, 
                                     community: set) -> float:
        """
        Calculate average internal correlation within a community
        """
        try:
            internal_corrs = []
        
            for asset1 in community:
                for asset2 in community:
                    if asset1 >= asset2:
                        continue
                    internal_corrs.append(abs(correlation_matrix.loc[asset1, asset2]))
        
            return np.mean(internal_corrs) if internal_corrs else 0
        except Exception as e:
            logger.error(f"Error in _calculate_internal_correlation: {e}")
            raise
    
    def _calculate_external_correlation(self, correlation_matrix: pd.DataFrame,
                                     community: set) -> float:
        """
        Calculate average external correlation of a community
        """
        try:
            external_corrs = []
        
            for asset1 in community:
                for asset2 in correlation_matrix.index:
                    if asset2 not in community:
                        external_corrs.append(abs(correlation_matrix.loc[asset1, asset2]))
        
            return np.mean(external_corrs) if external_corrs else 0
        except Exception as e:
            logger.error(f"Error in _calculate_external_correlation: {e}")
            raise
    
    def _calculate_zscore(self, value: float, history: List[float]) -> float:
        """
        Calculate z-score of a value against historical distribution
        """
        try:
            if not history:
                return 0
        
            mean = np.mean(history)
            std = np.std(history)
        
            return (value - mean) / std if std > 0 else 0
        except Exception as e:
            logger.error(f"Error in _calculate_zscore: {e}")
            raise
    
    def get_correlation_stats(self) -> Dict:
        """
        Get current correlation statistics
        """
        try:
            if not self.correlation_history:
                return {}
        
            current_corr = list(self.correlation_history.values())[-1]
        
            return {
                'average_correlation': np.mean(np.abs(current_corr.values[np.triu_indices_from(current_corr.values, k=1)])),
                'correlation_volatility': np.std([
                    np.mean(np.abs(corr.values[np.triu_indices_from(corr.values, k=1)]))
                    for corr in self.correlation_history.values()
                ]),
                'strongest_pair': self._find_strongest_correlation(current_corr),
                'weakest_pair': self._find_weakest_correlation(current_corr),
                'network_stats': self._calculate_network_stats(),
                'regime_stats': {
                    'current_regime': self._identify_current_regime(),
                    'regime_duration': self._calculate_regime_duration(),
                    'regime_stability': self._calculate_regime_stability()
                }
            }
        except Exception as e:
            logger.error(f"Error in get_correlation_stats: {e}")
            raise
    
    def _find_strongest_correlation(self, correlation_matrix: pd.DataFrame) -> Dict:
        """Find strongest correlated pair"""
        try:
            max_corr = 0
            max_pair = None
        
            for i in range(len(correlation_matrix.index)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    corr = abs(correlation_matrix.iloc[i, j])
                    if corr > max_corr:
                        max_corr = corr
                        max_pair = (correlation_matrix.index[i], correlation_matrix.columns[j])
        
            return {
                'assets': max_pair,
                'correlation': max_corr
            } if max_pair else {}
        except Exception as e:
            logger.error(f"Error in _find_strongest_correlation: {e}")
            raise
    
    def _find_weakest_correlation(self, correlation_matrix: pd.DataFrame) -> Dict:
        """Find weakest correlated pair"""
        try:
            min_corr = 1
            min_pair = None
        
            for i in range(len(correlation_matrix.index)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    corr = abs(correlation_matrix.iloc[i, j])
                    if corr < min_corr:
                        min_corr = corr
                        min_pair = (correlation_matrix.index[i], correlation_matrix.columns[j])
        
            return {
                'assets': min_pair,
                'correlation': min_corr
            } if min_pair else {}
        except Exception as e:
            logger.error(f"Error in _find_weakest_correlation: {e}")
            raise
    
    def _calculate_network_stats(self) -> Dict:
        """Calculate correlation network statistics"""
        try:
            if self.correlation_network is None:
                return {}
        
            return {
                'density': nx.density(self.correlation_network),
                'clustering_coefficient': nx.average_clustering(self.correlation_network),
                'communities': len(list(nx.community.greedy_modularity_communities(self.correlation_network))),
                'centrality': dict(nx.degree_centrality(self.correlation_network))
            }
        except Exception as e:
            logger.error(f"Error in _calculate_network_stats: {e}")
            raise
    
    def _identify_current_regime(self) -> str:
        """Identify current correlation regime"""
        try:
            if not self.correlation_history:
                return "unknown"
        
            current_corr = list(self.correlation_history.values())[-1]
            avg_corr = np.mean(np.abs(current_corr.values[np.triu_indices_from(current_corr.values, k=1)]))
        
            if avg_corr > 0.7:
                return "high_correlation"
            elif avg_corr > 0.3:
                return "normal_correlation"
            else:
                return "low_correlation"
        except Exception as e:
            logger.error(f"Error in _identify_current_regime: {e}")
            raise
    
    def _calculate_regime_duration(self) -> int:
        """Calculate duration of current regime"""
        try:
            if len(self.regime_history) < 2:
                return 0
        
            current_regime = self.regime_history[-1]
            duration = 1
        
            for regime in reversed(self.regime_history[:-1]):
                if regime == current_regime:
                    duration += 1
                else:
                    break
        
            return duration
        except Exception as e:
            logger.error(f"Error in _calculate_regime_duration: {e}")
            raise
    
    def _calculate_regime_stability(self) -> float:
        """Calculate stability of current regime"""
        try:
            if len(self.correlation_history) < 10:
                return 0
        
            recent_corrs = list(self.correlation_history.values())[-10:]
        
            # Calculate average change in correlations
            changes = []
            for i in range(1, len(recent_corrs)):
                change = np.mean(np.abs(recent_corrs[i] - recent_corrs[i-1]))
                changes.append(change)
        
            return 1 - min(1, np.mean(changes) * 10)
        except Exception as e:
            logger.error(f"Error in _calculate_regime_stability: {e}")
            raise
