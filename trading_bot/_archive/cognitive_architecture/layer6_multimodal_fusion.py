"""
Layer 6: Multi-Modal Fusion Intelligence
Integrates multiple data types for comprehensive analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import numpy as np
import logging
import numpy

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of data for fusion."""
    MARKET = "market"
    SENTIMENT = "sentiment"
    MACRO = "macro"
    BLOCKCHAIN = "blockchain"
    ALTERNATIVE = "alternative"
    NEWS = "news"
    SOCIAL = "social"


@dataclass
class DataSource:
    """Represents a data source."""
    data_type: DataType
    data: Dict[str, Any]
    quality: float = 1.0
    timestamp: float = 0.0
    weight: float = 1.0


@dataclass
class FusedSignal:
    """Result of multi-modal fusion."""
    direction: str  # 'bullish', 'bearish', 'neutral'
    strength: float
    confidence: float
    contributing_sources: List[str]
    explanation: str


class DataTypeProcessor:
    """
    Processes specific data types into normalized features.
    """
    
    def __init__(self, data_type: DataType):
        self.data_type = data_type
        self.feature_extractors: Dict[str, callable] = {}
        logger.debug(f"DataTypeProcessor initialized for {data_type.value}")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process data into normalized features."""
        features = {}
        
        if self.data_type == DataType.MARKET:
            features = self._process_market(data)
        elif self.data_type == DataType.SENTIMENT:
            features = self._process_sentiment(data)
        elif self.data_type == DataType.MACRO:
            features = self._process_macro(data)
        elif self.data_type == DataType.BLOCKCHAIN:
            features = self._process_blockchain(data)
        elif self.data_type == DataType.ALTERNATIVE:
            features = self._process_alternative(data)
        elif self.data_type == DataType.NEWS:
            features = self._process_news(data)
        elif self.data_type == DataType.SOCIAL:
            features = self._process_social(data)
        
        return features
    
    def _process_market(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process market data."""
        return {
            'price_change': data.get('price_change', 0.0),
            'volume_ratio': data.get('volume_ratio', 1.0),
            'volatility': data.get('volatility', 0.0),
            'trend': data.get('trend', 0.0),
            'momentum': data.get('momentum', 0.0)
        }
    
    def _process_sentiment(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process sentiment data."""
        return {
            'overall_sentiment': data.get('sentiment', 0.0),
            'fear_greed': data.get('fear_greed', 50.0) / 100.0,
            'bullish_ratio': data.get('bullish_ratio', 0.5)
        }
    
    def _process_macro(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process macro economic data."""
        return {
            'interest_rate_trend': data.get('rate_trend', 0.0),
            'inflation_expectation': data.get('inflation', 0.0),
            'gdp_growth': data.get('gdp_growth', 0.0)
        }
    
    def _process_blockchain(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process blockchain data."""
        return {
            'whale_activity': data.get('whale_activity', 0.0),
            'exchange_flow': data.get('exchange_flow', 0.0),
            'network_activity': data.get('network_activity', 0.0)
        }
    
    def _process_alternative(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process alternative data."""
        return {
            'satellite_signal': data.get('satellite', 0.0),
            'web_traffic': data.get('web_traffic', 0.0),
            'job_postings': data.get('job_postings', 0.0)
        }
    
    def _process_news(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process news data."""
        return {
            'news_sentiment': data.get('sentiment', 0.0),
            'news_volume': data.get('volume', 0.0),
            'breaking_news': 1.0 if data.get('breaking', False) else 0.0
        }
    
    def _process_social(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Process social media data."""
        return {
            'social_sentiment': data.get('sentiment', 0.0),
            'mention_volume': data.get('mentions', 0.0),
            'influencer_activity': data.get('influencer', 0.0)
        }


class TransformerFusion:
    """
    Transformer-based fusion model for multi-modal data.
    Uses attention mechanism to weight different data sources.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.attention_weights: Dict[str, float] = {
            DataType.MARKET.value: 0.3,
            DataType.SENTIMENT.value: 0.15,
            DataType.MACRO.value: 0.1,
            DataType.BLOCKCHAIN.value: 0.1,
            DataType.ALTERNATIVE.value: 0.1,
            DataType.NEWS.value: 0.15,
            DataType.SOCIAL.value: 0.1
        }
        logger.info("TransformerFusion initialized")
    
    def compute_attention(self, sources: List[DataSource]) -> Dict[str, float]:
        """Compute attention weights for data sources."""
        weights = {}
        total_quality = sum(s.quality for s in sources)
        
        for source in sources:
            base_weight = self.attention_weights.get(source.data_type.value, 0.1)
            quality_factor = source.quality / total_quality if total_quality > 0 else 1.0
            weights[source.data_type.value] = base_weight * quality_factor * source.weight
        
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    def fuse(self, features_by_type: Dict[str, Dict[str, float]], 
             attention_weights: Dict[str, float]) -> Dict[str, float]:
        """Fuse features using attention weights."""
        fused = {}
        
        for data_type, features in features_by_type.items():
            weight = attention_weights.get(data_type, 0.1)
            for feature_name, value in features.items():
                key = f"{data_type}_{feature_name}"
                fused[key] = value * weight
        
        return fused


class MultiModalFusion:
    """
    Multi-Modal Fusion - Layer 6 of Cognitive Architecture.
    Integrates multiple data types for comprehensive market analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.processors: Dict[DataType, DataTypeProcessor] = {
            dt: DataTypeProcessor(dt) for dt in DataType
        }
        self.fusion_model = TransformerFusion(config)
        logger.info("MultiModalFusion initialized")
    
    def process_sources(self, sources: List[DataSource]) -> FusedSignal:
        """Process multiple data sources and generate fused signal."""
        if not sources:
            return FusedSignal(
                direction='neutral',
                strength=0.0,
                confidence=0.0,
                contributing_sources=[],
                explanation="No data sources provided"
            )
        
        # Process each source
        features_by_type: Dict[str, Dict[str, float]] = {}
        for source in sources:
            processor = self.processors.get(source.data_type)
            if processor:
                features = processor.process(source.data)
                features_by_type[source.data_type.value] = features
        
        # Compute attention weights
        attention_weights = self.fusion_model.compute_attention(sources)
        
        # Fuse features
        fused_features = self.fusion_model.fuse(features_by_type, attention_weights)
        
        # Generate signal from fused features
        signal = self._generate_signal(fused_features, attention_weights)
        
        return signal
    
    def _generate_signal(self, fused_features: Dict[str, float], 
                         attention_weights: Dict[str, float]) -> FusedSignal:
        """Generate trading signal from fused features."""
        # Calculate directional bias
        bullish_signals = 0.0
        bearish_signals = 0.0
        total_weight = 0.0
        
        for key, value in fused_features.items():
            weight = 1.0
            if 'sentiment' in key.lower() or 'trend' in key.lower() or 'momentum' in key.lower():
                if value > 0:
                    bullish_signals += value * weight
                else:
                    bearish_signals += abs(value) * weight
                total_weight += weight
        
        # Determine direction
        if total_weight > 0:
            bullish_ratio = bullish_signals / total_weight
            bearish_ratio = bearish_signals / total_weight
        else:
            bullish_ratio = bearish_ratio = 0.5
        
        if bullish_ratio > bearish_ratio + 0.1:
            direction = 'bullish'
            strength = bullish_ratio - bearish_ratio
        elif bearish_ratio > bullish_ratio + 0.1:
            direction = 'bearish'
            strength = bearish_ratio - bullish_ratio
        else:
            direction = 'neutral'
            strength = 0.0
        
        # Calculate confidence from data quality
        confidence = sum(attention_weights.values()) / len(attention_weights) if attention_weights else 0.5
        
        return FusedSignal(
            direction=direction,
            strength=min(strength, 1.0),
            confidence=confidence,
            contributing_sources=list(attention_weights.keys()),
            explanation=f"Fused {len(attention_weights)} data sources: {direction} signal with {strength:.2f} strength"
        )
    
    def add_source(self, data_type: DataType, data: Dict[str, Any], 
                   quality: float = 1.0) -> DataSource:
        """Create and add a data source."""
        return DataSource(
            data_type=data_type,
            data=data,
            quality=quality
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of fusion system."""
        return {
            'processors': [dt.value for dt in self.processors.keys()],
            'attention_weights': self.fusion_model.attention_weights
        }
