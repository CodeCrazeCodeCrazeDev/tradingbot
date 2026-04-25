"""
Data Fusion Agent - Perception Layer
=====================================

The ONLY agent allowed to access raw data directly.
All other agents must request data through this agent.

Responsibilities:
- Fuse all data sources into a live market picture
- Market feeds, alternative data, news/sentiment, order book, macro indicators
- Provide unified data interface to other agents
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of data sources"""
    MARKET_FEED = "market_feed"
    ORDER_BOOK = "order_book"
    NEWS = "news"
    SENTIMENT = "sentiment"
    ALTERNATIVE = "alternative"
    MACRO = "macro"
    ON_CHAIN = "on_chain"


@dataclass
class FusedMarketPicture:
    """Complete fused market picture"""
    picture_id: str
    timestamp: datetime
    
    # Market data
    prices: Dict[str, float]
    volumes: Dict[str, float]
    order_books: Dict[str, Dict[str, Any]]
    
    # Sentiment & news
    sentiment_scores: Dict[str, float]
    news_events: List[Dict[str, Any]]
    
    # Alternative data
    alternative_signals: Dict[str, Any]
    
    # Macro indicators
    macro_indicators: Dict[str, float]
    
    # On-chain data (for crypto)
    on_chain_metrics: Dict[str, Any]
    
    # Metadata
    data_quality: float
    completeness: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'picture_id': self.picture_id,
            'timestamp': self.timestamp.isoformat(),
            'prices': self.prices,
            'volumes': self.volumes,
            'sentiment_scores': self.sentiment_scores,
            'news_events': self.news_events,
            'alternative_signals': self.alternative_signals,
            'macro_indicators': self.macro_indicators,
            'on_chain_metrics': self.on_chain_metrics,
            'data_quality': self.data_quality,
            'completeness': self.completeness,
        }


class DataFusionAgent:
    """
    Data Fusion Agent - ASI-Evolve Enhanced Perception Layer
    =================================================
    
    The ONLY agent with permission to access raw data sources.
    All other agents must request data through this agent.
    
    ASI-EVOLVE ENHANCEMENTS:
    - Cognition Store integration for context-aware fusion
    - Multi-stage data quality assessment
    - Semantic embedding-based data source management
    - LLM-based data quality reasoning
    """
    
    def __init__(self, meta_orchestrator: Any, cognition_store: Optional[Any] = None):
        self.agent_id = f"FUSION-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        self.cognition_store = cognition_store  # ASI-Evolve Cognition Store
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("DataFusionAgent", self)
        
        # Data source connections
        self.data_sources: Dict[str, Any] = {}
        
        # Cache
        self.latest_picture: Optional[FusedMarketPicture] = None
        self.picture_history: List[FusedMarketPicture] = []
        
        # Metrics
        self.total_fusions = 0
        self.data_requests_served = 0
        
        logger.info(f"DataFusionAgent initialized: {self.agent_id}")
    
    def register_data_source(self, source_type: DataSourceType, source_connection: Any):
        """Register a data source"""
        self.data_sources[source_type.value] = source_connection
        
        # ASI-Evolve: assess source quality and reliability
        source_quality = self._assess_data_source_quality(source_connection)
        self.cognition_store.add_cognition_item(CognitionItem(
            id=f"source_{source_type.value}",
            content=f"Data source {source_type.value} registered with quality: {source_quality}",
            source_domain="data_fusion",
            novelty_score=0.7,
            actionability_score=0.8
        ))
        
        logger.info(f"Registered data source: {source_type.value} with quality assessment")
    
    async def fuse_market_data(self) -> FusedMarketPicture:
        """
        Fuse all data sources into a unified market picture.
        
        This is perception layer that creates situational awareness.
        
        # ASI-Evolve: analyze data quality and completeness before fusion
        quality_assessment = await self._assess_data_quality()
        
        # ASI-Evolve: retrieve relevant cognition for data fusion
        cognition_items = self.cognition_store.search("data quality assessment", top_k=3) if self.cognition_store else []
        
        # Collect data from all sources
        prices = await self._collect_prices()
        volumes = await self._collect_volumes()
        order_books = await self._collect_order_books()
        sentiment = await self._collect_sentiment()
        news = await self._collect_news()
        alternative = await self._collect_alternative_data()
        macro = await self._collect_macro_indicators()
        on_chain = await self._collect_on_chain_data()
        
        # ASI-Evolve: multi-stage data processing
        processed_data = await self._process_with_quality_control(prices, volumes, sentiment, news, alternative, macro, on_chain)
        
        # Create fused picture with ASI-Evolve quality metrics
        picture = FusedMarketPicture(
            picture_id=f"PIC-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            prices=processed_data['prices'],
            volumes=processed_data['volumes'],
            order_books=processed_data['order_books'],
            sentiment_scores=processed_data['sentiment'],
            news_events=processed_data['news'],
            alternative_signals=processed_data['alternative'],
            macro_indicators=processed_data['macro'],
            on_chain_metrics=processed_data['on_chain'],
            data_quality=processed_data['quality'],
            completeness=processed_data['completeness'],
        )
        
        # Cache
        self.latest_picture = picture
        self.picture_history.append(picture)
        
        # Trim history
        if len(self.picture_history) > 1000:
            self.picture_history = self.picture_history[-500:]
        
        self.total_fusions += 1
        
        # ASI-Evolve: log fusion outcome for learning
        logger.info(f"Fused market picture: quality={quality_assessment['overall_score']:.2f}, completeness={processed_data['completeness']:.2f}")
        
        return picture
    
    async def get_market_picture(self, requesting_agent: str) -> FusedMarketPicture:
        """
        Provide market picture to requesting agent.
        
        This enforces Rule 1: Agents NEVER access raw data directly.
        
        self.data_requests_served += 1
        
        if not self.latest_picture:
            return await self.fuse_market_data()
        
        return self.latest_picture
    
    async def _collect_prices(self) -> Dict[str, float]:
        """Collect price data from market feeds"""
        # In production, would connect to real market feeds
        # For now, simulate
        return {
            'AAPL': 175.50,
            'GOOGL': 140.25,
            'MSFT': 380.75,
            'TSLA': 245.30,
            'BTC': 67500.00,
            'ETH': 3200.00,
        }
    
    async def _collect_volumes(self) -> Dict[str, float]:
        """Collect volume data"""
        return {
            'AAPL': 50000000,
            'GOOGL': 25000000,
            'MSFT': 35000000,
            'TSLA': 80000000,
            'BTC': 25000,
            'ETH': 150000,
        }
    
    async def _collect_order_books(self) -> Dict[str, Dict[str, Any]]:
        """Collect order book data"""
        return {
            'AAPL': {
                'bids': [[175.49, 1000], [175.48, 2000]],
                'asks': [[175.51, 1500], [175.52, 2500]],
                'spread': 0.02,
            },
        }
    
    async def _collect_sentiment(self) -> Dict[str, float]:
        """Collect sentiment scores"""
        return {
            'AAPL': 0.65,
            'GOOGL': 0.55,
            'MSFT': 0.70,
            'TSLA': 0.45,
            'market_overall': 0.60,
        }
    
    async def _collect_news(self) -> List[Dict[str, Any]]:
        """Collect news events"""
        return [
            {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'headline': 'Fed signals potential rate cut',
                'sentiment': 0.7,
                'relevance': 0.9,
                'symbols': ['SPY', 'QQQ'],
            },
        ]
    
    async def _collect_alternative_data(self) -> Dict[str, Any]:
        """Collect alternative data signals"""
        return {
            'satellite_imagery': {'retail_traffic': 0.85},
            'credit_card_data': {'consumer_spending': 1.05},
            'web_scraping': {'product_mentions': 1200},
        }
    
    async def _collect_macro_indicators(self) -> Dict[str, float]:
        """Collect macro economic indicators"""
        return {
            'gdp_growth': 2.5,
            'inflation': 3.2,
            'unemployment': 3.8,
            'fed_rate': 5.25,
            'vix': 15.5,
        }
    
    async def _collect_on_chain_data(self) -> Dict[str, Any]:
        """Collect on-chain metrics (for crypto)"""
        return {
            'btc_active_addresses': 950000,
            'eth_gas_price': 25,
            'exchange_inflows': -15000,
            'whale_transactions': 45,
        }
    
    async def _normalize_prices(self, data: Dict[str, float]) -> Dict[str, float]:
        """Remove outliers and normalize"""
        # ASI-Evolve: statistical outlier detection and normalization
        prices = list(data.values())
        if not prices:
            return {}
        
        # Calculate statistics
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        # Remove outliers (2 standard deviations)
        normalized_prices = {}
        for symbol, price in data.items():
            if isinstance(price, (int, float)):
                z_score = abs(price - mean_price) / std_price
                if z_score > 2.0:  # Outlier
                    normalized_prices[symbol] = mean_price + (price - mean_price) * 0.5
                else:
                    normalized_prices[symbol] = price
        
        return normalized_prices
        
        # ASI-Evolve: log normalization process for learning
        logger.info(f"Price normalization applied: removed outliers from {len([p for p in normalized_prices.values() if p != data.get(symbol, p)])} symbols")
    
    async def _sentiment_calibration(self, data: Dict[str, float]) -> Dict[str, Any]:
        """Validate and calibrate sentiment scores"""
        # ASI-Evolve: advanced sentiment analysis and calibration
        scores = list(data.values())
        
        # Statistical analysis
        if not scores:
            return {'passed': False, 'reason': 'No sentiment scores provided'}
        
        # Calculate statistics
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Detect and correct systematic bias
        bias_correction = 0.0  # Simplified bias detection
        for i, score in enumerate(scores):
            if i > len(scores) // 2 and score < mean_score:
                bias_correction += 0.01
        
        # Apply bias correction
        calibration_factor = 0.5 - (mean_score / 0.2)
        
        # Calibrate scores
        calibrated_scores = {}
        for symbol, score in data.items():
            if isinstance(score, (int, float)):
                # Apply bias correction and calibration
                calibrated_score = min(1.0, max(score + bias_correction + calibration_factor, 0.0))
                calibrated_scores[symbol] = calibrated_score
            else:
                calibrated_scores[symbol] = score
        
        return calibrated_scores
        
        # Log calibration process
        logger.info(f"Sentiment calibration applied: bias_correction={bias_correction:.3f}, calibration_factor={calibration_factor:.3f}")
        
        return calibrated_scores
    
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness"""
        total_sources = len(data)
        complete_sources = sum(1 for value in data.values() if value)
        
        return complete_sources / total_sources if total_sources > 0 else 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'data_sources': list(self.data_sources.keys()),
            'total_fusions': self.total_fusions,
            'data_requests_served': self.data_requests_served,
            'latest_picture_quality': self.latest_picture.data_quality if self.latest_picture else 0.0,
            'latest_picture_completeness': self.latest_picture.completeness if self.latest_picture else 0.0,
            'cognition_items_count': self.cognition_store.get_statistics()['total_items'] if self.cognition_store else 0,
        }
