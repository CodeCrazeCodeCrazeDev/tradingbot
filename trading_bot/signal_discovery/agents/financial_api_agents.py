"""
Financial API Agents (15 agents)
================================

Agents that monitor financial data APIs for anomalies:
- Bloomberg Terminal API
- Reuters
- Alpha Vantage
- Quandl
- FRED (Federal Reserve Economic Data)
- TradingView
- CoinGecko (crypto)
- And others

Detects:
- Price outliers
- Volume anomalies
- Cross-asset divergences
- Technical indicator extremes
"""

from typing import Any, Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent import BaseAnomalyAgent, MarketAnomaly, AnomalyType, DataSource

logger = logging.getLogger(__name__)


class FinancialAPIAgent(BaseAnomalyAgent):
    """
    Agent for monitoring financial data APIs and detecting anomalies.
    
    Each instance can be configured for specific assets and data sources.
    """
    
    def __init__(self, agent_id: str, check_interval_seconds: float = 30.0):
        """
        Initialize Financial API Agent.
        
        Args:
            agent_id: Unique identifier
            check_interval_seconds: Check frequency
        """
        # Assign data sources based on agent index
        sources = self._assign_data_sources(agent_id)
        
        super().__init__(
            agent_id=agent_id,
            data_sources=sources,
            check_interval_seconds=check_interval_seconds
        )
        
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}
        self.max_history = 1000
        
        logger.info(f"FinancialAPIAgent {agent_id} initialized with sources: {[s.value for s in sources]}")
    
    def _assign_data_sources(self, agent_id: str) -> List[DataSource]:
        """Assign data sources based on agent ID."""
        # Parse index from agent_id (format: financial_api_XXX)
        try:
            idx = int(agent_id.split('_')[-1])
        except:
            idx = 0
        
        # Distribute sources across agents
        all_sources = [
            DataSource.BLOOMBERG,
            DataSource.REUTERS,
            DataSource.ALPHA_VANTAGE,
            DataSource.QUANDL,
            DataSource.FRED,
            DataSource.TRADINGVIEW,
            DataSource.COINGECKO,
        ]
        
        # Each agent gets primary source + overflow
        primary = all_sources[idx % len(all_sources)]
        return [primary]
    
    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch data from assigned financial APIs.
        
        Returns:
            Dictionary with price, volume, and metadata
        """
        data = {
            'prices': {},
            'volumes': {},
            'indicators': {},
            'timestamp': datetime.now(),
        }
        
        # This is a stub - real implementation would call actual APIs
        for source in self.data_sources:
            try:
                # Simulate API fetch
                await asyncio.sleep(0.01)
                data['prices'][source.value] = self._get_latest_prices(source)
                data['volumes'][source.value] = self._get_latest_volumes(source)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.value}: {e}")
        
        return data
    
    def _get_latest_prices(self, source: DataSource) -> Dict[str, float]:
        """Get latest prices from source (stub)."""
        # In production, this calls actual APIs
        return {'SPY': 450.0, 'QQQ': 380.0, 'BTC': 65000.0}  # Stub
    
    def _get_latest_volumes(self, source: DataSource) -> Dict[str, float]:
        """Get latest volumes from source (stub)."""
        return {'SPY': 50000000, 'QQQ': 30000000, 'BTC': 20000}  # Stub
    
    async def detect_anomalies(self) -> List[MarketAnomaly]:
        """
        Detect anomalies in financial data.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Fetch data
        data = await self.fetch_data()
        
        # Check each asset
        for source, prices in data['prices'].items():
            for asset, price in prices.items() if isinstance(prices, dict) else []:
                # Update history
                if asset not in self.price_history:
                    self.price_history[asset] = []
                self.price_history[asset].append(price)
                if len(self.price_history[asset]) > self.max_history:
                    self.price_history[asset] = self.price_history[asset][-self.max_history:]
                
                # Statistical outlier detection
                if len(self.price_history[asset]) >= 20:
                    anomaly = self._detect_price_outlier(asset, price, self.price_history[asset])
                    if anomaly:
                        anomalies.append(anomaly)
        
        # Volume anomaly detection
        for source, volumes in data.get('volumes', {}).items():
            for asset, volume in volumes.items() if isinstance(volumes, dict) else []:
                if asset not in self.volume_history:
                    self.volume_history[asset] = []
                self.volume_history[asset].append(volume)
                if len(self.volume_history[asset]) > self.max_history:
                    self.volume_history[asset] = self.volume_history[asset][-self.max_history:]
                
                if len(self.volume_history[asset]) >= 20:
                    anomaly = self._detect_volume_anomaly(asset, volume, self.volume_history[asset])
                    if anomaly:
                        anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_price_outlier(self, asset: str, current_price: float, 
                              history: List[float]) -> Optional[MarketAnomaly]:
        """
        Detect price outliers using Z-score.
        
        Returns:
            MarketAnomaly if outlier detected, None otherwise
        """
        if len(history) < 20:
            return None
        
        mean = sum(history[-20:]) / 20
        variance = sum((p - mean) ** 2 for p in history[-20:]) / 20
        std = variance ** 0.5
        
        if std == 0:
            return None
        
        z_score = abs((current_price - mean) / std)
        
        if z_score > 2.5:  # 2.5 sigma threshold
            confidence = min(1.0, z_score / 4.0)
            
            return self._create_anomaly(
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                data_source=self.data_sources[0],
                confidence=confidence,
                description=f"Price outlier detected for {asset}: z-score={z_score:.2f}",
                primary_asset=asset,
                detection_method="z_score",
                statistical_significance=z_score,
            )
        
        return None
    
    def _detect_volume_anomaly(self, asset: str, current_volume: float,
                               history: List[float]) -> Optional[MarketAnomaly]:
        """Detect volume anomalies."""
        if len(history) < 20:
            return None
        
        mean = sum(history[-20:]) / 20
        if mean == 0:
            return None
        
        ratio = current_volume / mean
        
        if ratio > 3.0:  # 3x average volume
            confidence = min(1.0, ratio / 5.0)
            
            return self._create_anomaly(
                anomaly_type=AnomalyType.VOLUME_ANOMALY,
                data_source=self.data_sources[0],
                confidence=confidence,
                description=f"Volume spike for {asset}: {ratio:.1f}x average",
                primary_asset=asset,
                detection_method="volume_ratio",
                statistical_significance=ratio,
            )
        
        return None
