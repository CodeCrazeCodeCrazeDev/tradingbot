"""
Data Evolution Engine - Self-Evolving Data Quality & Processing
================================================================

Continuously evolves and improves data handling:
- Data quality validation and cleaning
- Level 2 order book analysis
- Alternative data integration
- Data enrichment pipelines
- Anomaly detection
- Data freshness monitoring
- Source reliability scoring

Learns from data patterns to find better processing approaches.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import deque
import hashlib
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class DataQualityMetric(Enum):
    """Metrics for measuring data quality"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    TIMELINESS = "timeliness"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    FRESHNESS = "freshness"
    RELIABILITY = "reliability"


class DataSourceType(Enum):
    """Types of data sources"""
    MARKET_DATA = "market_data"
    LEVEL2_DATA = "level2_data"
    NEWS_SENTIMENT = "news_sentiment"
    SOCIAL_SENTIMENT = "social_sentiment"
    ECONOMIC_DATA = "economic_data"
    ALTERNATIVE_DATA = "alternative_data"
    SATELLITE_DATA = "satellite_data"
    BLOCKCHAIN_DATA = "blockchain_data"


@dataclass
class DataQualityScore:
    """Quality score for a data source"""
    source: str
    completeness: float
    accuracy: float
    timeliness: float
    consistency: float
    overall_score: float
    issues_found: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Level2Snapshot:
    """Level 2 order book snapshot"""
    symbol: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # (price, size)
    asks: List[Tuple[float, float]]
    bid_depth: float
    ask_depth: float
    spread: float
    imbalance: float
    mid_price: float


@dataclass
class AlternativeDataPoint:
    """Alternative data point"""
    source: str
    data_type: str
    value: Any
    confidence: float
    timestamp: datetime
    relevance_score: float


class Level2DataProcessor:
    """
    Level 2 Order Book Data Processor
    
    Evolves to better understand:
    - Order flow patterns
    - Liquidity dynamics
    - Market microstructure
    - Hidden orders detection
    - Iceberg order detection
    - Spoofing detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Processing parameters (evolvable)
        self.params = {
            'depth_levels': 10,
            'imbalance_threshold': 0.3,
            'spread_alert_threshold': 0.001,
            'liquidity_window': 100,
            'iceberg_detection_sensitivity': 0.7,
            'spoofing_detection_sensitivity': 0.8,
            'order_flow_smoothing': 0.1
        }
        
        # Historical data for learning
        self.snapshots: deque = deque(maxlen=10000)
        self.order_flow_history: deque = deque(maxlen=5000)
        self.detected_patterns: List[Dict] = []
        
        # Learning statistics
        self.stats = {
            'snapshots_processed': 0,
            'patterns_detected': 0,
            'icebergs_detected': 0,
            'spoofing_detected': 0,
            'liquidity_events': 0
        }
    
    def process_snapshot(self, snapshot: Level2Snapshot) -> Dict[str, Any]:
        """Process a Level 2 snapshot"""
        self.snapshots.append(snapshot)
        self.stats['snapshots_processed'] += 1
        
        analysis = {
            'timestamp': snapshot.timestamp.isoformat(),
            'symbol': snapshot.symbol,
            'spread': snapshot.spread,
            'imbalance': snapshot.imbalance,
            'bid_depth': snapshot.bid_depth,
            'ask_depth': snapshot.ask_depth,
            'signals': []
        }
        
        # Detect patterns
        if abs(snapshot.imbalance) > self.params['imbalance_threshold']:
            analysis['signals'].append({
                'type': 'imbalance',
                'direction': 'buy' if snapshot.imbalance > 0 else 'sell',
                'strength': abs(snapshot.imbalance)
            })
        
        # Detect iceberg orders
        iceberg = self._detect_iceberg(snapshot)
        if iceberg:
            analysis['signals'].append(iceberg)
            self.stats['icebergs_detected'] += 1
        
        # Detect spoofing
        spoofing = self._detect_spoofing(snapshot)
        if spoofing:
            analysis['signals'].append(spoofing)
            self.stats['spoofing_detected'] += 1
        
        # Liquidity analysis
        liquidity = self._analyze_liquidity(snapshot)
        analysis['liquidity'] = liquidity
        
        return analysis
    
    def _detect_iceberg(self, snapshot: Level2Snapshot) -> Optional[Dict]:
        """Detect potential iceberg orders"""
        if len(self.snapshots) < 10:
            return None
        
        # Look for repeated fills at same price level
        recent = list(self.snapshots)[-10:]
        
        for side, orders in [('bid', snapshot.bids), ('ask', snapshot.asks)]:
            if not orders:
                continue
            
            top_price = orders[0][0]
            sizes_at_top = []
            
            for s in recent:
                side_orders = s.bids if side == 'bid' else s.asks
                if side_orders and side_orders[0][0] == top_price:
                    sizes_at_top.append(side_orders[0][1])
            
            # Iceberg pattern: size keeps replenishing
            if len(sizes_at_top) >= 5:
                size_changes = np.diff(sizes_at_top)
                replenishments = sum(1 for c in size_changes if c > 0)
                
                if replenishments >= 3:
                    return {
                        'type': 'iceberg',
                        'side': side,
                        'price': top_price,
                        'confidence': min(replenishments / 5, 1.0)
                    }
        
        return None
    
    def _detect_spoofing(self, snapshot: Level2Snapshot) -> Optional[Dict]:
        """Detect potential spoofing activity"""
        if len(self.snapshots) < 20:
            return None
        
        recent = list(self.snapshots)[-20:]
        
        # Look for large orders that disappear quickly
        for side in ['bid', 'ask']:
            large_orders_appeared = []
            large_orders_disappeared = []
            
            for i, s in enumerate(recent[:-1]):
                current_orders = s.bids if side == 'bid' else s.asks
                next_orders = recent[i+1].bids if side == 'bid' else recent[i+1].asks
                
                if not current_orders or not next_orders:
                    continue
                
                current_total = sum(o[1] for o in current_orders[:5])
                next_total = sum(o[1] for o in next_orders[:5])
                
                # Large order appeared
                if next_total > current_total * 2:
                    large_orders_appeared.append(i)
                
                # Large order disappeared
                if current_total > next_total * 2:
                    large_orders_disappeared.append(i)
            
            # Spoofing pattern: large orders appear and disappear frequently
            if len(large_orders_appeared) >= 3 and len(large_orders_disappeared) >= 3:
                return {
                    'type': 'spoofing',
                    'side': side,
                    'confidence': self.params['spoofing_detection_sensitivity'],
                    'events': len(large_orders_appeared) + len(large_orders_disappeared)
                }
        
        return None
    
    def _analyze_liquidity(self, snapshot: Level2Snapshot) -> Dict[str, Any]:
        """Analyze liquidity conditions"""
        total_liquidity = snapshot.bid_depth + snapshot.ask_depth
        
        # Calculate liquidity score
        if len(self.snapshots) > self.params['liquidity_window']:
            recent = list(self.snapshots)[-self.params['liquidity_window']:]
            avg_liquidity = np.mean([s.bid_depth + s.ask_depth for s in recent])
            liquidity_ratio = total_liquidity / avg_liquidity if avg_liquidity > 0 else 1
        else:
            liquidity_ratio = 1
        
        return {
            'total_depth': total_liquidity,
            'bid_ask_ratio': snapshot.bid_depth / snapshot.ask_depth if snapshot.ask_depth > 0 else 1,
            'liquidity_ratio': liquidity_ratio,
            'is_thin': liquidity_ratio < 0.5,
            'is_thick': liquidity_ratio > 1.5
        }
    
    def evolve_parameters(self, performance_feedback: Dict[str, float]):
        """Evolve processing parameters based on feedback"""
        # Adjust sensitivity based on detection accuracy
        if 'iceberg_accuracy' in performance_feedback:
            accuracy = performance_feedback['iceberg_accuracy']
            if accuracy < 0.5:
                self.params['iceberg_detection_sensitivity'] *= 0.9
            elif accuracy > 0.8:
                self.params['iceberg_detection_sensitivity'] = min(
                    0.95, self.params['iceberg_detection_sensitivity'] * 1.1
                )
        
        if 'spoofing_accuracy' in performance_feedback:
            accuracy = performance_feedback['spoofing_accuracy']
            if accuracy < 0.5:
                self.params['spoofing_detection_sensitivity'] *= 0.9
            elif accuracy > 0.8:
                self.params['spoofing_detection_sensitivity'] = min(
                    0.95, self.params['spoofing_detection_sensitivity'] * 1.1
                )


class AlternativeDataEvolver:
    """
    Alternative Data Evolution Engine
    
    Evolves to better integrate and use:
    - News sentiment
    - Social media sentiment
    - Satellite imagery signals
    - Web traffic data
    - Credit card transaction data
    - Weather data
    - Supply chain data
    - Geopolitical events
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Source configurations (evolvable)
        self.sources = {
            'news': {
                'enabled': True,
                'weight': 0.25,
                'lag_hours': 0,
                'reliability': 0.7,
                'sentiment_threshold': 0.3
            },
            'social': {
                'enabled': True,
                'weight': 0.15,
                'lag_hours': 0,
                'reliability': 0.5,
                'sentiment_threshold': 0.4
            },
            'economic': {
                'enabled': True,
                'weight': 0.30,
                'lag_hours': 24,
                'reliability': 0.9,
                'impact_threshold': 0.5
            },
            'satellite': {
                'enabled': False,
                'weight': 0.10,
                'lag_hours': 48,
                'reliability': 0.6,
                'change_threshold': 0.1
            },
            'blockchain': {
                'enabled': True,
                'weight': 0.20,
                'lag_hours': 0,
                'reliability': 0.8,
                'flow_threshold': 1000000
            }
        }
        
        # Data history
        self.data_history: Dict[str, deque] = {
            source: deque(maxlen=1000) for source in self.sources
        }
        
        # Correlation tracking
        self.correlations: Dict[str, List[float]] = {
            source: [] for source in self.sources
        }
        
        # Statistics
        self.stats = {
            'data_points_processed': 0,
            'signals_generated': 0,
            'weight_adjustments': 0,
            'sources_disabled': 0,
            'sources_enabled': 0
        }
    
    def add_data_point(self, data: AlternativeDataPoint):
        """Add an alternative data point"""
        if data.source in self.data_history:
            self.data_history[data.source].append(data)
            self.stats['data_points_processed'] += 1
    
    def get_composite_signal(self, symbol: str) -> Dict[str, Any]:
        """Get composite signal from all alternative data sources"""
        signals = []
        total_weight = 0
        
        for source, config in self.sources.items():
            if not config['enabled']:
                continue
            
            # Get recent data for this source
            recent_data = list(self.data_history[source])[-10:]
            if not recent_data:
                continue
            
            # Calculate source signal
            signal_value = self._calculate_source_signal(source, recent_data)
            
            if signal_value is not None:
                weighted_signal = signal_value * config['weight'] * config['reliability']
                signals.append({
                    'source': source,
                    'raw_signal': signal_value,
                    'weighted_signal': weighted_signal,
                    'weight': config['weight'],
                    'reliability': config['reliability']
                })
                total_weight += config['weight'] * config['reliability']
        
        if not signals or total_weight == 0:
            return {'composite_signal': 0, 'confidence': 0, 'sources': []}
        
        # Calculate composite
        composite = sum(s['weighted_signal'] for s in signals) / total_weight
        
        # Calculate confidence based on agreement
        signal_values = [s['raw_signal'] for s in signals]
        agreement = 1 - np.std(signal_values) if len(signal_values) > 1 else 0.5
        
        self.stats['signals_generated'] += 1
        
        return {
            'composite_signal': composite,
            'confidence': agreement,
            'direction': 'bullish' if composite > 0 else 'bearish',
            'strength': abs(composite),
            'sources': signals
        }
    
    def _calculate_source_signal(
        self,
        source: str,
        data: List[AlternativeDataPoint]
    ) -> Optional[float]:
        """Calculate signal from a specific source"""
        if not data:
            return None
        
        config = self.sources[source]
        
        if source == 'news':
            # Average sentiment
            sentiments = [d.value for d in data if isinstance(d.value, (int, float))]
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                if abs(avg_sentiment) > config['sentiment_threshold']:
                    return avg_sentiment
        
        elif source == 'social':
            # Social sentiment with decay
            sentiments = []
            for i, d in enumerate(reversed(data)):
                decay = 0.9 ** i
                if isinstance(d.value, (int, float)):
                    sentiments.append(d.value * decay)
            if sentiments:
                return np.mean(sentiments)
        
        elif source == 'economic':
            # Economic indicator impact
            impacts = [d.value for d in data if isinstance(d.value, (int, float))]
            if impacts:
                return np.mean(impacts)
        
        elif source == 'blockchain':
            # Net flow direction
            flows = [d.value for d in data if isinstance(d.value, (int, float))]
            if flows:
                net_flow = sum(flows)
                if abs(net_flow) > config['flow_threshold']:
                    return 1 if net_flow > 0 else -1
        
        return None
    
    def record_outcome(self, source: str, signal: float, actual_move: float):
        """Record outcome for learning"""
        # Calculate correlation
        correlation = signal * actual_move  # Positive if same direction
        self.correlations[source].append(correlation)
        
        # Keep limited history
        if len(self.correlations[source]) > 100:
            self.correlations[source] = self.correlations[source][-100:]
    
    async def evolve(self) -> List[Dict[str, Any]]:
        """Evolve source weights based on performance"""
        evolutions = []
        
        for source, correlations in self.correlations.items():
            if len(correlations) < 20:
                continue
            
            # Calculate average correlation
            avg_correlation = np.mean(correlations)
            
            config = self.sources[source]
            old_weight = config['weight']
            
            # Adjust weight based on correlation
            if avg_correlation > 0.3:
                # Good predictor, increase weight
                config['weight'] = min(0.5, config['weight'] * 1.1)
            elif avg_correlation < -0.1:
                # Bad predictor, decrease weight
                config['weight'] = max(0.05, config['weight'] * 0.9)
            elif avg_correlation < -0.3:
                # Very bad, consider disabling
                config['enabled'] = False
                self.stats['sources_disabled'] += 1
            
            if config['weight'] != old_weight:
                self.stats['weight_adjustments'] += 1
                evolutions.append({
                    'source': source,
                    'old_weight': old_weight,
                    'new_weight': config['weight'],
                    'correlation': avg_correlation
                })
        
        # Normalize weights
        total_weight = sum(c['weight'] for c in self.sources.values() if c['enabled'])
        if total_weight > 0:
            for config in self.sources.values():
                if config['enabled']:
                    config['weight'] /= total_weight
        
        return evolutions


class DataEvolutionEngine:
    """
    Master Data Evolution Engine
    
    Coordinates all data evolution:
    - Data quality monitoring
    - Level 2 data processing
    - Alternative data integration
    - Source reliability tracking
    - Data pipeline optimization
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Sub-engines
        self.level2_processor = Level2DataProcessor(config)
        self.alt_data_evolver = AlternativeDataEvolver(config)
        
        # Quality thresholds (evolvable)
        self.quality_thresholds = {
            DataQualityMetric.COMPLETENESS: 0.95,
            DataQualityMetric.ACCURACY: 0.99,
            DataQualityMetric.TIMELINESS: 0.90,
            DataQualityMetric.CONSISTENCY: 0.95,
            DataQualityMetric.VALIDITY: 0.99,
            DataQualityMetric.FRESHNESS: 0.95
        }
        
        # Source reliability scores
        self.source_reliability: Dict[str, float] = {}
        
        # Quality history
        self.quality_history: List[DataQualityScore] = []
        
        # Data validation rules (evolvable)
        self.validation_rules = {
            'price_change_max': 0.10,  # Max 10% price change
            'volume_spike_threshold': 10,  # 10x average volume
            'timestamp_max_delay': 5,  # 5 seconds max delay
            'missing_fields_allowed': 0,
            'outlier_std_threshold': 4  # 4 standard deviations
        }
        
        # Statistics
        self.stats = {
            'data_points_validated': 0,
            'quality_issues_found': 0,
            'data_cleaned': 0,
            'sources_evaluated': 0,
            'evolutions_performed': 0
        }
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'data_evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        self._load_state()
        logger.info("Data Evolution Engine initialized")
    
    def validate_data(self, data: Dict[str, Any], source: str) -> Tuple[bool, List[str]]:
        """Validate incoming data"""
        self.stats['data_points_validated'] += 1
        issues = []
        
        # Check completeness
        required_fields = ['timestamp', 'symbol']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
        
        # Check timeliness
        if 'timestamp' in data:
            try:
                ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                delay = (datetime.now() - ts.replace(tzinfo=None)).total_seconds()
                if delay > self.validation_rules['timestamp_max_delay']:
                    issues.append(f"Data too old: {delay:.1f}s delay")
            except Exception:
                issues.append("Invalid timestamp format")
        
        # Check price validity
        if 'price' in data:
            price = data['price']
            if price <= 0:
                issues.append("Invalid price: must be positive")
            
            # Check for extreme price changes
            if 'previous_price' in data:
                change = abs(price - data['previous_price']) / data['previous_price']
                if change > self.validation_rules['price_change_max']:
                    issues.append(f"Extreme price change: {change:.2%}")
        
        # Check volume
        if 'volume' in data and 'average_volume' in data:
            if data['volume'] > data['average_volume'] * self.validation_rules['volume_spike_threshold']:
                issues.append(f"Volume spike: {data['volume'] / data['average_volume']:.1f}x average")
        
        # Update source reliability
        if source not in self.source_reliability:
            self.source_reliability[source] = 0.8
        
        if issues:
            self.stats['quality_issues_found'] += len(issues)
            self.source_reliability[source] *= 0.99
        else:
            self.source_reliability[source] = min(1.0, self.source_reliability[source] * 1.001)
        
        return len(issues) == 0, issues
    
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data"""
        cleaned = data.copy()
        self.stats['data_cleaned'] += 1
        
        # Normalize timestamp
        if 'timestamp' in cleaned:
            try:
                ts = datetime.fromisoformat(cleaned['timestamp'].replace('Z', '+00:00'))
                cleaned['timestamp'] = ts.isoformat()
            except Exception:
                cleaned['timestamp'] = datetime.now().isoformat()
        
        # Handle missing values
        if 'price' not in cleaned and 'close' in cleaned:
            cleaned['price'] = cleaned['close']
        
        # Remove outliers
        numeric_fields = ['price', 'volume', 'open', 'high', 'low', 'close']
        for field in numeric_fields:
            if field in cleaned and isinstance(cleaned[field], (int, float)):
                if cleaned[field] < 0:
                    cleaned[field] = abs(cleaned[field])
        
        return cleaned
    
    def calculate_quality_score(self, source: str, data_batch: List[Dict]) -> DataQualityScore:
        """Calculate quality score for a data source"""
        self.stats['sources_evaluated'] += 1
        
        if not data_batch:
            return DataQualityScore(
                source=source,
                completeness=0,
                accuracy=0,
                timeliness=0,
                consistency=0,
                overall_score=0,
                issues_found=["No data"]
            )
        
        issues = []
        
        # Completeness: percentage of non-null fields
        total_fields = 0
        non_null_fields = 0
        for data in data_batch:
            for key, value in data.items():
                total_fields += 1
                if value is not None:
                    non_null_fields += 1
        completeness = non_null_fields / total_fields if total_fields > 0 else 0
        
        if completeness < self.quality_thresholds[DataQualityMetric.COMPLETENESS]:
            issues.append(f"Low completeness: {completeness:.2%}")
        
        # Timeliness: percentage of data within acceptable delay
        timely_count = 0
        for data in data_batch:
            if 'timestamp' in data:
                try:
                    ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    delay = (datetime.now() - ts.replace(tzinfo=None)).total_seconds()
                    if delay <= self.validation_rules['timestamp_max_delay']:
                        timely_count += 1
                except Exception:
                    pass
        timeliness = timely_count / len(data_batch) if data_batch else 0
        
        if timeliness < self.quality_thresholds[DataQualityMetric.TIMELINESS]:
            issues.append(f"Low timeliness: {timeliness:.2%}")
        
        # Consistency: check for contradictions
        consistency = 1.0
        for data in data_batch:
            if 'high' in data and 'low' in data:
                if data['high'] < data['low']:
                    consistency -= 0.1
                    issues.append("Inconsistent high/low")
            if 'open' in data and 'close' in data and 'high' in data and 'low' in data:
                if not (data['low'] <= data['open'] <= data['high']):
                    consistency -= 0.1
                if not (data['low'] <= data['close'] <= data['high']):
                    consistency -= 0.1
        consistency = max(0, consistency)
        
        # Accuracy: based on source reliability
        accuracy = self.source_reliability.get(source, 0.8)
        
        # Overall score
        overall = (completeness * 0.25 + accuracy * 0.30 + 
                  timeliness * 0.25 + consistency * 0.20)
        
        score = DataQualityScore(
            source=source,
            completeness=completeness,
            accuracy=accuracy,
            timeliness=timeliness,
            consistency=consistency,
            overall_score=overall,
            issues_found=issues
        )
        
        self.quality_history.append(score)
        return score
    
    async def evolve(self) -> List[Dict[str, Any]]:
        """Run data evolution cycle"""
        logger.info("Starting data evolution cycle...")
        evolutions = []
        
        # Evolve validation rules based on quality history
        if len(self.quality_history) >= 10:
            recent_scores = self.quality_history[-10:]
            
            # Adjust thresholds based on average quality
            avg_completeness = np.mean([s.completeness for s in recent_scores])
            avg_timeliness = np.mean([s.timeliness for s in recent_scores])
            
            # If quality is consistently high, tighten thresholds
            if avg_completeness > 0.98:
                old_threshold = self.quality_thresholds[DataQualityMetric.COMPLETENESS]
                self.quality_thresholds[DataQualityMetric.COMPLETENESS] = min(0.99, old_threshold + 0.01)
                evolutions.append({
                    'type': 'threshold',
                    'metric': 'completeness',
                    'old': old_threshold,
                    'new': self.quality_thresholds[DataQualityMetric.COMPLETENESS]
                })
            
            # If timeliness is poor, relax threshold slightly
            if avg_timeliness < 0.8:
                old_threshold = self.quality_thresholds[DataQualityMetric.TIMELINESS]
                self.quality_thresholds[DataQualityMetric.TIMELINESS] = max(0.7, old_threshold - 0.02)
                evolutions.append({
                    'type': 'threshold',
                    'metric': 'timeliness',
                    'old': old_threshold,
                    'new': self.quality_thresholds[DataQualityMetric.TIMELINESS]
                })
        
        # Evolve alternative data weights
        alt_evolutions = await self.alt_data_evolver.evolve()
        for evo in alt_evolutions:
            evolutions.append({
                'type': 'alt_data_weight',
                **evo
            })
        
        self.stats['evolutions_performed'] += 1
        self._save_state()
        
        logger.info(f"Data evolution complete: {len(evolutions)} changes")
        return evolutions
    
    def process_level2(self, snapshot: Level2Snapshot) -> Dict[str, Any]:
        """Process Level 2 data"""
        return self.level2_processor.process_snapshot(snapshot)
    
    def add_alternative_data(self, data: AlternativeDataPoint):
        """Add alternative data point"""
        self.alt_data_evolver.add_data_point(data)
    
    def get_alternative_signal(self, symbol: str) -> Dict[str, Any]:
        """Get composite alternative data signal"""
        return self.alt_data_evolver.get_composite_signal(symbol)
    
    def _save_state(self):
        """Save evolution state"""
        state = {
            'quality_thresholds': {k.value: v for k, v in self.quality_thresholds.items()},
            'validation_rules': self.validation_rules,
            'source_reliability': self.source_reliability,
            'stats': self.stats,
            'alt_data_sources': self.alt_data_evolver.sources,
            'level2_params': self.level2_processor.params
        }
        
        state_file = self.state_path / 'data_evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous state"""
        state_file = self.state_path / 'data_evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                for k, v in state.get('quality_thresholds', {}).items():
                    metric = DataQualityMetric(k)
                    self.quality_thresholds[metric] = v
                
                self.validation_rules = state.get('validation_rules', self.validation_rules)
                self.source_reliability = state.get('source_reliability', {})
                self.stats = state.get('stats', self.stats)
                
                if 'alt_data_sources' in state:
                    self.alt_data_evolver.sources = state['alt_data_sources']
                if 'level2_params' in state:
                    self.level2_processor.params = state['level2_params']
                
                logger.info("Loaded previous data evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load data evolution state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            **self.stats,
            'quality_thresholds': {k.value: v for k, v in self.quality_thresholds.items()},
            'source_count': len(self.source_reliability),
            'avg_source_reliability': np.mean(list(self.source_reliability.values())) if self.source_reliability else 0,
            'level2_stats': self.level2_processor.stats,
            'alt_data_stats': self.alt_data_evolver.stats
        }
