"""
Discovery Engine - Finds new data sources, models, and modules

Automatically discovers:
- Stock data sources (Yahoo, Alpha Vantage, IEX, Polygon, etc.)
- Forex data providers (OANDA, Dukascopy, FXCM, etc.)
- Equity data (Quandl, Tiingo, etc.)
- Futures data (CME, ICE, etc.)
- Alternative data (satellite imagery, sentiment, social media, etc.)
- New ML models and trading modules

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import importlib.util
import inspect
from pathlib import Path
import json
import aiohttp
import hashlib

logger = logging.getLogger(__name__)


class DiscoveryType(Enum):
    """Types of items that can be discovered"""
    STOCK_DATA = "stock_data"
    FOREX_DATA = "forex_data"
    EQUITY_DATA = "equity_data"
    FUTURES_DATA = "futures_data"
    CRYPTO_DATA = "crypto_data"
    ALTERNATIVE_DATA = "alternative_data"
    SATELLITE_DATA = "satellite_data"
    SENTIMENT_DATA = "sentiment_data"
    SOCIAL_DATA = "social_data"
    NEWS_DATA = "news_data"
    ML_MODEL = "ml_model"
    TRADING_MODULE = "trading_module"
    INDICATOR = "indicator"
    STRATEGY = "strategy"


@dataclass
class DiscoveredItem:
    """Represents a discovered data source or model"""
    item_id: str
    item_type: DiscoveryType
    name: str
    source: str  # URL, file path, or module path
    description: str
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0  # 0-1
    estimated_value: float = 0.0  # Estimated trading value
    
    # Technical details
    requires_api_key: bool = False
    cost: str = "free"  # free, paid, freemium
    rate_limit: Optional[str] = None
    data_format: str = "json"
    
    # Validation
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    # Status
    status: str = "discovered"  # discovered, validated, sandboxed, tested, approved, deployed
    
    def to_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'item_type': self.item_type.value,
            'name': self.name,
            'source': self.source,
            'description': self.description,
            'discovered_at': self.discovered_at.isoformat(),
            'quality_score': self.quality_score,
            'estimated_value': self.estimated_value,
            'requires_api_key': self.requires_api_key,
            'cost': self.cost,
            'rate_limit': self.rate_limit,
            'data_format': self.data_format,
            'validated': self.validated,
            'validation_errors': self.validation_errors,
            'status': self.status
        }


class DataSourceDiscovery:
    """Discovers new data sources"""
    
    # Known high-quality data sources
    KNOWN_SOURCES = {
        'stock': [
            {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com', 'free': True},
            {'name': 'Alpha Vantage', 'url': 'https://www.alphavantage.co', 'free': True},
            {'name': 'IEX Cloud', 'url': 'https://iexcloud.io', 'free': False},
            {'name': 'Polygon.io', 'url': 'https://polygon.io', 'free': False},
            {'name': 'Finnhub', 'url': 'https://finnhub.io', 'free': True},
            {'name': 'Twelve Data', 'url': 'https://twelvedata.com', 'free': True},
        ],
        'forex': [
            {'name': 'OANDA', 'url': 'https://www.oanda.com', 'free': False},
            {'name': 'Dukascopy', 'url': 'https://www.dukascopy.com', 'free': True},
            {'name': 'FXCM', 'url': 'https://www.fxcm.com', 'free': False},
            {'name': 'Forex.com', 'url': 'https://www.forex.com', 'free': False},
        ],
        'crypto': [
            {'name': 'Binance', 'url': 'https://www.binance.com', 'free': True},
            {'name': 'Coinbase', 'url': 'https://www.coinbase.com', 'free': True},
            {'name': 'Kraken', 'url': 'https://www.kraken.com', 'free': True},
            {'name': 'CoinGecko', 'url': 'https://www.coingecko.com', 'free': True},
        ],
        'alternative': [
            {'name': 'Quandl', 'url': 'https://www.quandl.com', 'free': True},
            {'name': 'Tiingo', 'url': 'https://www.tiingo.com', 'free': True},
            {'name': 'Intrinio', 'url': 'https://intrinio.com', 'free': False},
        ],
        'sentiment': [
            {'name': 'StockTwits', 'url': 'https://stocktwits.com', 'free': True},
            {'name': 'Reddit WallStreetBets', 'url': 'https://www.reddit.com/r/wallstreetbets', 'free': True},
            {'name': 'Twitter Financial', 'url': 'https://twitter.com', 'free': True},
        ],
        'satellite': [
            {'name': 'Planet Labs', 'url': 'https://www.planet.com', 'free': False},
            {'name': 'Maxar', 'url': 'https://www.maxar.com', 'free': False},
            {'name': 'Sentinel Hub', 'url': 'https://www.sentinel-hub.com', 'free': True},
        ],
        'news': [
            {'name': 'NewsAPI', 'url': 'https://newsapi.org', 'free': True},
            {'name': 'Bloomberg', 'url': 'https://www.bloomberg.com', 'free': False},
            {'name': 'Reuters', 'url': 'https://www.reuters.com', 'free': True},
        ]
    }
    
    def __init__(self):
        self.discovered_sources: List[DiscoveredItem] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def discover_all(self) -> List[DiscoveredItem]:
        """Discover all available data sources"""
        logger.info("Starting data source discovery...")
        
        self.session = aiohttp.ClientSession()
        try:
            for category, sources in self.KNOWN_SOURCES.items():
                for source in sources:
                    item = await self._discover_source(category, source)
                    if item:
                        self.discovered_sources.append(item)
                        logger.info(f"Discovered: {item.name} ({item.item_type.value})")
        finally:
            await self.session.close()
        
        logger.info(f"Discovery complete: {len(self.discovered_sources)} sources found")
        return self.discovered_sources
    
    async def _discover_source(self, category: str, source_info: Dict) -> Optional[DiscoveredItem]:
        """Discover a single data source"""
        try:
            # Map category to DiscoveryType
            type_map = {
                'stock': DiscoveryType.STOCK_DATA,
                'forex': DiscoveryType.FOREX_DATA,
                'crypto': DiscoveryType.CRYPTO_DATA,
                'alternative': DiscoveryType.ALTERNATIVE_DATA,
                'sentiment': DiscoveryType.SENTIMENT_DATA,
                'satellite': DiscoveryType.SATELLITE_DATA,
                'news': DiscoveryType.NEWS_DATA
            }
            
            item_type = type_map.get(category, DiscoveryType.ALTERNATIVE_DATA)
            
            # Generate unique ID
            item_id = hashlib.md5(f"{source_info['name']}_{source_info['url']}".encode()).hexdigest()[:16]
            
            # Check if source is accessible
            quality_score = await self._check_source_quality(source_info['url'])
            
            item = DiscoveredItem(
                item_id=item_id,
                item_type=item_type,
                name=source_info['name'],
                source=source_info['url'],
                description=f"{category.title()} data from {source_info['name']}",
                quality_score=quality_score,
                estimated_value=self._estimate_value(category, source_info),
                requires_api_key=not source_info['free'],
                cost='free' if source_info['free'] else 'paid'
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error discovering {source_info['name']}: {e}")
            return None
    
    async def _check_source_quality(self, url: str) -> float:
        """Check if source is accessible and estimate quality"""
        try:
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    return 0.8  # Accessible
                else:
                    return 0.3  # Not accessible
        except Exception as e:
            logger.error(f"Error: {e}")
            return 0.1  # Error
    
    def _estimate_value(self, category: str, source_info: Dict) -> float:
        """Estimate trading value of data source"""
        # Higher value for real-time, low-latency, unique data
        base_value = {
            'stock': 0.7,
            'forex': 0.8,
            'crypto': 0.9,
            'alternative': 0.95,
            'sentiment': 0.85,
            'satellite': 0.99,
            'news': 0.75
        }.get(category, 0.5)
        
        # Paid sources often have higher quality
        if not source_info['free']:
            base_value += 0.1
        
        return min(base_value, 1.0)


class ModelDiscovery:
    """Discovers new ML models and trading modules"""
    
    def __init__(self, search_paths: List[str] = None):
        self.search_paths = search_paths or [
            'trading_bot/ml',
            'trading_bot/strategies',
            'trading_bot/indicators',
            'trading_bot/signals'
        ]
        self.discovered_models: List[DiscoveredItem] = []
    
    async def discover_all(self) -> List[DiscoveredItem]:
        """Discover all available models and modules"""
        logger.info("Starting model/module discovery...")
        
        for search_path in self.search_paths:
            await self._scan_directory(search_path)
        
        logger.info(f"Discovery complete: {len(self.discovered_models)} models/modules found")
        return self.discovered_models
    
    async def _scan_directory(self, directory: str):
        """Scan directory for Python modules"""
        try:
            path = Path(directory)
            if not path.exists():
                return
            
            for py_file in path.rglob('*.py'):
                if py_file.name.startswith('_'):
                    continue
                
                item = await self._analyze_module(py_file)
                if item:
                    self.discovered_models.append(item)
                    logger.info(f"Discovered: {item.name} ({item.item_type.value})")
                    
        except Exception as e:
            logger.error(f"Error scanning {directory}: {e}")
    
    async def _analyze_module(self, file_path: Path) -> Optional[DiscoveredItem]:
        """Analyze a Python module"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine type
            item_type = self._determine_type(file_path, content)
            if not item_type:
                return None
            
            # Extract info
            name = file_path.stem
            description = self._extract_description(content)
            quality_score = self._assess_code_quality(content)
            
            item_id = hashlib.md5(str(file_path).encode()).hexdigest()[:16]
            
            item = DiscoveredItem(
                item_id=item_id,
                item_type=item_type,
                name=name,
                source=str(file_path),
                description=description,
                quality_score=quality_score,
                estimated_value=quality_score * 0.9,
                cost='free'
            )
            
            return item
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
    
    def _determine_type(self, file_path: Path, content: str) -> Optional[DiscoveryType]:
        """Determine module type"""
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        if 'ml' in path_str or 'model' in content_lower:
            return DiscoveryType.ML_MODEL
        elif 'strategy' in path_str or 'strategy' in content_lower:
            return DiscoveryType.STRATEGY
        elif 'indicator' in path_str or 'indicator' in content_lower:
            return DiscoveryType.INDICATOR
        elif 'signal' in path_str:
            return DiscoveryType.TRADING_MODULE
        
        return None
    
    def _extract_description(self, content: str) -> str:
        """Extract module description from docstring"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                # Found docstring
                desc_lines = []
                for j in range(i+1, min(i+10, len(lines))):
                    if '"""' in lines[j] or "'''" in lines[j]:
                        break
                    desc_lines.append(lines[j].strip())
                return ' '.join(desc_lines)[:200]
        return "No description available"
    
    def _assess_code_quality(self, content: str) -> float:
        """Assess code quality"""
        score = 0.5
        
        # Has docstring
        if '"""' in content or "'''" in content:
            score += 0.1
        
        # Has type hints
        if '->' in content:
            score += 0.1
        
        # Has error handling
        if 'try:' in content and 'except' in content:
            score += 0.1
        
        # Has logging
        if 'logger' in content or 'logging' in content:
            score += 0.1
        
        # Has tests
        if 'test_' in content or 'assert' in content:
            score += 0.1
        
        return min(score, 1.0)


class DiscoveryEngine:
    """Master discovery engine"""
    
    def __init__(self):
        self.data_discovery = DataSourceDiscovery()
        self.model_discovery = ModelDiscovery()
        self.all_discovered: List[DiscoveredItem] = []
    
    async def discover_everything(self) -> List[DiscoveredItem]:
        """Discover all data sources and models"""
        logger.info("=" * 80)
        logger.info("AUTONOMOUS DISCOVERY ENGINE - STARTING")
        logger.info("=" * 80)
        
        # Discover data sources
        data_sources = await self.data_discovery.discover_all()
        
        # Discover models
        models = await self.model_discovery.discover_all()
        
        # Combine
        self.all_discovered = data_sources + models
        
        # Sort by estimated value
        self.all_discovered.sort(key=lambda x: x.estimated_value, reverse=True)
        
        logger.info("=" * 80)
        logger.info(f"DISCOVERY COMPLETE: {len(self.all_discovered)} items found")
        logger.info(f"  Data Sources: {len(data_sources)}")
        logger.info(f"  Models/Modules: {len(models)}")
        logger.info("=" * 80)
        
        return self.all_discovered
    
    def get_top_discoveries(self, n: int = 10) -> List[DiscoveredItem]:
        """Get top N discoveries by value"""
        return self.all_discovered[:n]
    
    def filter_by_type(self, item_type: DiscoveryType) -> List[DiscoveredItem]:
        """Filter discoveries by type"""
        return [item for item in self.all_discovered if item.item_type == item_type]
    
    def save_discoveries(self, filepath: str = "discoveries.json"):
        """Save discoveries to file"""
        data = [item.to_dict() for item in self.all_discovered]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Discoveries saved to {filepath}")
