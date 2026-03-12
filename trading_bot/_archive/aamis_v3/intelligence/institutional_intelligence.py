"""
AAMIS v3.0 - Institutional Intelligence System

This module implements:
1. Behavioral Fingerprinting of Institutions - Detect institutional patterns
2. Institutional Order Flow Emulator - Mimic institutional behavior
3. Market Maker Profiling - Understand market maker strategies
4. Shadow Models - Replicate institutional strategies
5. Whale Tracking - Follow large players
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque, defaultdict
import numpy

logger = logging.getLogger(__name__)


class InstitutionType(Enum):
    """Types of institutional players"""
    HEDGE_FUND = "HEDGE_FUND"
    INVESTMENT_BANK = "INVESTMENT_BANK"
    MARKET_MAKER = "MARKET_MAKER"
    PENSION_FUND = "PENSION_FUND"
    SOVEREIGN_WEALTH = "SOVEREIGN_WEALTH"
    PROP_TRADING_FIRM = "PROP_TRADING_FIRM"
    CENTRAL_BANK = "CENTRAL_BANK"
    ALGORITHMIC_TRADER = "ALGORITHMIC_TRADER"


class TradingStyle(Enum):
    """Institutional trading styles"""
    AGGRESSIVE = "AGGRESSIVE"
    PASSIVE = "PASSIVE"
    OPPORTUNISTIC = "OPPORTUNISTIC"
    SYSTEMATIC = "SYSTEMATIC"
    DISCRETIONARY = "DISCRETIONARY"
    HIGH_FREQUENCY = "HIGH_FREQUENCY"
    LONG_TERM = "LONG_TERM"


class OrderFlowPattern(Enum):
    """Order flow patterns"""
    ICEBERG = "ICEBERG"  # Hidden large orders
    SWEEP = "SWEEP"  # Rapid execution across venues
    LAYERING = "LAYERING"  # Multiple price levels
    TIME_SLICING = "TIME_SLICING"  # TWAP/VWAP
    MOMENTUM_IGNITION = "MOMENTUM_IGNITION"  # Start momentum
    ACCUMULATION = "ACCUMULATION"  # Gradual buying
    DISTRIBUTION = "DISTRIBUTION"  # Gradual selling


@dataclass
class InstitutionalFingerprint:
    """Behavioral fingerprint of an institution"""
    institution_id: str
    institution_type: InstitutionType
    trading_style: TradingStyle
    
    # Behavioral characteristics
    avg_order_size: float = 0.0
    order_size_variance: float = 0.0
    trading_frequency: float = 0.0  # Orders per hour
    preferred_times: List[int] = field(default_factory=list)  # Hours of day
    preferred_venues: List[str] = field(default_factory=list)
    
    # Execution patterns
    execution_patterns: List[OrderFlowPattern] = field(default_factory=list)
    avg_execution_time: float = 0.0  # seconds
    slippage_tolerance: float = 0.0
    
    # Strategy indicators
    momentum_following: float = 0.0  # 0-1
    mean_reversion: float = 0.0  # 0-1
    news_sensitivity: float = 0.0  # 0-1
    
    # Confidence and tracking
    confidence: float = 0.0
    observations: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    
    def update_from_observation(self, observation: Dict):
        """Update fingerprint from new observation"""
        self.observations += 1
        self.last_seen = datetime.now()
        
        # Update averages (exponential moving average)
        alpha = 0.1  # Learning rate
        
        if 'order_size' in observation:
            self.avg_order_size = (1 - alpha) * self.avg_order_size + alpha * observation['order_size']
        
        if 'execution_time' in observation:
            self.avg_execution_time = (1 - alpha) * self.avg_execution_time + alpha * observation['execution_time']
        
        # Increase confidence with more observations
        self.confidence = min(0.95, self.confidence + 0.01)


@dataclass
class WhaleActivity:
    """Large player (whale) activity"""
    whale_id: str
    estimated_size: float  # USD
    direction: str  # BUY or SELL
    detected_at: datetime
    price_level: float
    volume: float
    impact_score: float = 0.0  # Estimated market impact
    is_active: bool = True


@dataclass
class MarketMakerProfile:
    """Profile of a market maker"""
    mm_id: str
    typical_spread: float
    quote_frequency: float  # Quotes per second
    inventory_management_style: str  # AGGRESSIVE, CONSERVATIVE
    adverse_selection_handling: str
    quote_size_avg: float
    response_to_flow: float  # How quickly they adjust to order flow


@dataclass
class ShadowModel:
    """Shadow model replicating institutional strategy"""
    model_id: str
    institution_type: InstitutionType
    strategy_description: str
    parameters: Dict = field(default_factory=dict)
    performance_correlation: float = 0.0  # Correlation with actual institution
    accuracy: float = 0.0


class BehavioralFingerprinter:
    """
    Detects and profiles institutional trading patterns
    Creates behavioral fingerprints for each institution
    """
    
    def __init__(self):
        self.fingerprints: Dict[str, InstitutionalFingerprint] = {}
        self.observations: List[Dict] = []
        
    def observe_order_flow(self, order_data: Dict) -> Optional[str]:
        """Observe order flow and identify institution"""
        self.observations.append(order_data)
        
        # Extract features
        features = self._extract_features(order_data)
        
        # Match to existing fingerprint or create new
        institution_id = self._match_or_create_fingerprint(features, order_data)
        
        if institution_id:
            # Update fingerprint
            self.fingerprints[institution_id].update_from_observation(order_data)
            logger.info(f"🔍 Identified institution: {institution_id}")
        
        return institution_id
    
    def _extract_features(self, order_data: Dict) -> Dict:
        """Extract behavioral features from order data"""
        return {
            'order_size': order_data.get('size', 0),
            'execution_speed': order_data.get('execution_time', 0),
            'time_of_day': datetime.now().hour,
            'venue': order_data.get('venue', 'UNKNOWN'),
            'order_type': order_data.get('order_type', 'MARKET'),
            'aggression': self._calculate_aggression(order_data),
            'stealth': self._calculate_stealth(order_data)
        }
    
    def _calculate_aggression(self, order_data: Dict) -> float:
        """Calculate aggression score"""
        # Market orders are more aggressive
        if order_data.get('order_type') == 'MARKET':
            aggression = 0.8
        else:
            aggression = 0.3
        
        # Large orders are more aggressive
        size = order_data.get('size', 0)
        if size > 1000000:  # >$1M
            aggression += 0.2
        
        return min(1.0, aggression)
    
    def _calculate_stealth(self, order_data: Dict) -> float:
        """Calculate stealth score (trying to hide)"""
        stealth = 0.5
        
        # Iceberg orders are stealthy
        if order_data.get('is_iceberg', False):
            stealth += 0.3
        
        # Small visible size is stealthy
        visible_size = order_data.get('visible_size', order_data.get('size', 0))
        total_size = order_data.get('size', 1)
        if visible_size < total_size * 0.3:
            stealth += 0.2
        
        return min(1.0, stealth)
    
    def _match_or_create_fingerprint(self, features: Dict, order_data: Dict) -> str:
        """Match features to existing fingerprint or create new"""
        # Try to match existing fingerprints
        best_match = None
        best_similarity = 0.0
        
        for inst_id, fingerprint in self.fingerprints.items():
            similarity = self._calculate_similarity(features, fingerprint)
            if similarity > best_similarity and similarity > 0.7:  # 70% threshold
                best_similarity = similarity
                best_match = inst_id
        
        if best_match:
            return best_match
        
        # Create new fingerprint
        new_id = f"INST_{len(self.fingerprints)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Infer institution type from features
        institution_type = self._infer_institution_type(features)
        trading_style = self._infer_trading_style(features)
        
        fingerprint = InstitutionalFingerprint(
            institution_id=new_id,
            institution_type=institution_type,
            trading_style=trading_style,
            avg_order_size=features['order_size'],
            trading_frequency=1.0,
            confidence=0.3  # Low initial confidence
        )
        
        self.fingerprints[new_id] = fingerprint
        
        logger.info(f"🆕 New institution detected: {new_id} ({institution_type.value})")
        
        return new_id
    
    def _calculate_similarity(self, features: Dict, fingerprint: InstitutionalFingerprint) -> float:
        """Calculate similarity between features and fingerprint"""
        similarity = 0.0
        
        # Order size similarity
        if fingerprint.avg_order_size > 0:
            size_ratio = min(features['order_size'], fingerprint.avg_order_size) / max(features['order_size'], fingerprint.avg_order_size)
            similarity += 0.3 * size_ratio
        
        # Time of day similarity
        if features['time_of_day'] in fingerprint.preferred_times:
            similarity += 0.2
        
        # Venue similarity
        if features['venue'] in fingerprint.preferred_venues:
            similarity += 0.2
        
        # Aggression similarity
        if fingerprint.trading_style == TradingStyle.AGGRESSIVE and features['aggression'] > 0.6:
            similarity += 0.15
        elif fingerprint.trading_style == TradingStyle.PASSIVE and features['aggression'] < 0.4:
            similarity += 0.15
        
        # Stealth similarity
        if features['stealth'] > 0.7:
            similarity += 0.15
        
        return similarity
    
    def _infer_institution_type(self, features: Dict) -> InstitutionType:
        """Infer institution type from features"""
        # Large orders + stealth = Hedge Fund
        if features['order_size'] > 1000000 and features['stealth'] > 0.6:
            return InstitutionType.HEDGE_FUND
        
        # High frequency = Prop Trading or Market Maker
        if features['execution_speed'] < 1:  # <1 second
            return InstitutionType.PROP_TRADING_FIRM
        
        # Medium size + passive = Pension Fund
        if features['order_size'] < 500000 and features['aggression'] < 0.4:
            return InstitutionType.PENSION_FUND
        
        return InstitutionType.INVESTMENT_BANK  # Default
    
    def _infer_trading_style(self, features: Dict) -> TradingStyle:
        """Infer trading style from features"""
        if features['aggression'] > 0.7:
            return TradingStyle.AGGRESSIVE
        elif features['stealth'] > 0.7:
            return TradingStyle.OPPORTUNISTIC
        elif features['execution_speed'] < 1:
            return TradingStyle.HIGH_FREQUENCY
        else:
            return TradingStyle.SYSTEMATIC
    
    def get_fingerprint(self, institution_id: str) -> Optional[InstitutionalFingerprint]:
        """Get fingerprint for institution"""
        return self.fingerprints.get(institution_id)
    
    def get_all_fingerprints(self) -> List[InstitutionalFingerprint]:
        """Get all fingerprints"""
        return list(self.fingerprints.values())


class InstitutionalOrderFlowEmulator:
    """
    Emulates institutional order flow patterns
    Learns how institutions execute large orders
    """
    
    def __init__(self):
        self.execution_strategies: Dict[OrderFlowPattern, Dict] = self._initialize_strategies()
        
    def _initialize_strategies(self) -> Dict[OrderFlowPattern, Dict]:
        """Initialize execution strategies"""
        return {
            OrderFlowPattern.ICEBERG: {
                'visible_ratio': 0.1,  # Show 10% of order
                'refresh_frequency': 30,  # seconds
                'description': 'Hide large order, show small pieces'
            },
            OrderFlowPattern.TIME_SLICING: {
                'num_slices': 10,
                'interval': 60,  # seconds between slices
                'description': 'Split order over time (TWAP)'
            },
            OrderFlowPattern.SWEEP: {
                'venues': ['VENUE_A', 'VENUE_B', 'VENUE_C'],
                'simultaneous': True,
                'description': 'Execute across multiple venues simultaneously'
            },
            OrderFlowPattern.ACCUMULATION: {
                'duration': 3600,  # 1 hour
                'randomize_timing': True,
                'description': 'Gradually accumulate position'
            }
        }
    
    def emulate_execution(self, order_size: float, pattern: OrderFlowPattern, market_data: Dict) -> List[Dict]:
        """Emulate institutional execution"""
        logger.info(f"🏦 Emulating {pattern.value} execution for ${order_size:,.0f}")
        
        if pattern == OrderFlowPattern.ICEBERG:
            return self._emulate_iceberg(order_size, market_data)
        elif pattern == OrderFlowPattern.TIME_SLICING:
            return self._emulate_time_slicing(order_size, market_data)
        elif pattern == OrderFlowPattern.SWEEP:
            return self._emulate_sweep(order_size, market_data)
        elif pattern == OrderFlowPattern.ACCUMULATION:
            return self._emulate_accumulation(order_size, market_data)
        else:
            return self._emulate_simple(order_size, market_data)
    
    def _emulate_iceberg(self, order_size: float, market_data: Dict) -> List[Dict]:
        """Emulate iceberg order execution"""
        strategy = self.execution_strategies[OrderFlowPattern.ICEBERG]
        visible_ratio = strategy['visible_ratio']
        
        executions = []
        remaining = order_size
        
        while remaining > 0:
            visible_size = min(remaining, order_size * visible_ratio)
            
            execution = {
                'timestamp': datetime.now(),
                'size': visible_size,
                'price': market_data.get('price', 1.0),
                'hidden_size': remaining - visible_size,
                'pattern': 'ICEBERG'
            }
            
            executions.append(execution)
            remaining -= visible_size
        
        return executions
    
    def _emulate_time_slicing(self, order_size: float, market_data: Dict) -> List[Dict]:
        """Emulate time-sliced execution (TWAP)"""
        strategy = self.execution_strategies[OrderFlowPattern.TIME_SLICING]
        num_slices = strategy['num_slices']
        interval = strategy['interval']
        
        slice_size = order_size / num_slices
        executions = []
        
        for i in range(num_slices):
            execution = {
                'timestamp': datetime.now() + timedelta(seconds=i * interval),
                'size': slice_size,
                'price': market_data.get('price', 1.0) * (1 + random.gauss(0, 0.001)),
                'slice_number': i + 1,
                'pattern': 'TIME_SLICING'
            }
            executions.append(execution)
        
        return executions
    
    def _emulate_sweep(self, order_size: float, market_data: Dict) -> List[Dict]:
        """Emulate sweep execution across venues"""
        strategy = self.execution_strategies[OrderFlowPattern.SWEEP]
        venues = strategy['venues']
        
        executions = []
        size_per_venue = order_size / len(venues)
        
        for venue in venues:
            execution = {
                'timestamp': datetime.now(),
                'size': size_per_venue,
                'price': market_data.get('price', 1.0),
                'venue': venue,
                'pattern': 'SWEEP'
            }
            executions.append(execution)
        
        return executions
    
    def _emulate_accumulation(self, order_size: float, market_data: Dict) -> List[Dict]:
        """Emulate gradual accumulation"""
        strategy = self.execution_strategies[OrderFlowPattern.ACCUMULATION]
        duration = strategy['duration']
        
        # Random number of executions
        num_executions = random.randint(20, 50)
        executions = []
        
        remaining = order_size
        for i in range(num_executions):
            # Random size (but total adds up to order_size)
            if i == num_executions - 1:
                size = remaining
            else:
                size = remaining * random.uniform(0.01, 0.1)
                remaining -= size
            
            # Random timing
            time_offset = random.uniform(0, duration)
            
            execution = {
                'timestamp': datetime.now() + timedelta(seconds=time_offset),
                'size': size,
                'price': market_data.get('price', 1.0) * (1 + random.gauss(0, 0.002)),
                'pattern': 'ACCUMULATION'
            }
            executions.append(execution)
        
        return sorted(executions, key=lambda x: x['timestamp'])
    
    def _emulate_simple(self, order_size: float, market_data: Dict) -> List[Dict]:
        """Simple execution (single order)"""
        return [{
            'timestamp': datetime.now(),
            'size': order_size,
            'price': market_data.get('price', 1.0),
            'pattern': 'SIMPLE'
        }]


class WhaleTracker:
    """
    Tracks large players (whales) in the market
    Detects and follows significant institutional activity
    """
    
    def __init__(self):
        self.active_whales: Dict[str, WhaleActivity] = {}
        self.whale_history: List[WhaleActivity] = []
        self.detection_threshold = 1000000  # $1M minimum
        
    def detect_whale_activity(self, order_data: Dict) -> Optional[WhaleActivity]:
        """Detect whale activity from order data"""
        order_size = order_data.get('size', 0) * order_data.get('price', 1.0)
        
        if order_size < self.detection_threshold:
            return None
        
        # Create whale activity record
        whale = WhaleActivity(
            whale_id=f"WHALE_{len(self.whale_history)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            estimated_size=order_size,
            direction=order_data.get('side', 'BUY'),
            detected_at=datetime.now(),
            price_level=order_data.get('price', 1.0),
            volume=order_data.get('size', 0),
            impact_score=self._estimate_impact(order_size, order_data)
        )
        
        self.active_whales[whale.whale_id] = whale
        self.whale_history.append(whale)
        
        logger.warning(f"🐋 WHALE DETECTED: ${order_size:,.0f} {whale.direction} at {whale.price_level:.5f}")
        logger.warning(f"   Impact Score: {whale.impact_score:.2f}")
        
        return whale
    
    def _estimate_impact(self, order_size: float, order_data: Dict) -> float:
        """Estimate market impact of whale order"""
        # Simplified impact model
        avg_daily_volume = order_data.get('avg_daily_volume', 10000000)
        
        # Impact proportional to order size relative to daily volume
        impact = (order_size / avg_daily_volume) * 100
        
        # Adjust for execution style
        if order_data.get('is_aggressive', False):
            impact *= 1.5
        
        return min(10.0, impact)  # Cap at 10
    
    def track_whale(self, whale_id: str, current_price: float) -> Dict:
        """Track ongoing whale activity"""
        if whale_id not in self.active_whales:
            return {'error': 'Whale not found'}
        
        whale = self.active_whales[whale_id]
        
        # Calculate P&L
        if whale.direction == 'BUY':
            pnl = (current_price - whale.price_level) * whale.volume
        else:
            pnl = (whale.price_level - current_price) * whale.volume
        
        return {
            'whale_id': whale_id,
            'entry_price': whale.price_level,
            'current_price': current_price,
            'estimated_pnl': pnl,
            'time_elapsed': (datetime.now() - whale.detected_at).total_seconds(),
            'is_profitable': pnl > 0
        }
    
    def get_active_whales(self) -> List[WhaleActivity]:
        """Get all active whales"""
        return [w for w in self.active_whales.values() if w.is_active]
    
    def deactivate_whale(self, whale_id: str):
        """Mark whale as inactive"""
        if whale_id in self.active_whales:
            self.active_whales[whale_id].is_active = False


class MarketMakerProfiler:
    """
    Profiles market maker behavior
    Understands how market makers quote and manage inventory
    """
    
    def __init__(self):
        self.profiles: Dict[str, MarketMakerProfile] = {}
        
    def profile_market_maker(self, mm_id: str, quote_data: List[Dict]) -> MarketMakerProfile:
        """Profile a market maker from quote data"""
        if mm_id in self.profiles:
            profile = self.profiles[mm_id]
        else:
            profile = MarketMakerProfile(
                mm_id=mm_id,
                typical_spread=0.0,
                quote_frequency=0.0,
                inventory_management_style="UNKNOWN",
                adverse_selection_handling="UNKNOWN",
                quote_size_avg=0.0,
                response_to_flow=0.0
            )
            self.profiles[mm_id] = profile
        
        # Analyze quote data
        if quote_data:
            # Calculate typical spread
            spreads = [q.get('ask', 1.0) - q.get('bid', 1.0) for q in quote_data]
            profile.typical_spread = np.mean(spreads)
            
            # Calculate quote frequency
            if len(quote_data) > 1:
                time_diffs = [(quote_data[i]['timestamp'] - quote_data[i-1]['timestamp']).total_seconds() 
                             for i in range(1, len(quote_data))]
                profile.quote_frequency = 1.0 / np.mean(time_diffs) if time_diffs else 0.0
            
            # Calculate average quote size
            sizes = [q.get('size', 0) for q in quote_data]
            profile.quote_size_avg = np.mean(sizes)
            
            # Infer inventory management style
            profile.inventory_management_style = self._infer_inventory_style(quote_data)
        
        logger.info(f"📊 Market Maker Profile: {mm_id}")
        logger.info(f"   Spread: {profile.typical_spread:.5f}")
        logger.info(f"   Quote Frequency: {profile.quote_frequency:.2f} Hz")
        logger.info(f"   Style: {profile.inventory_management_style}")
        
        return profile
    
    def _infer_inventory_style(self, quote_data: List[Dict]) -> str:
        """Infer inventory management style"""
        # Analyze spread changes
        spreads = [q.get('ask', 1.0) - q.get('bid', 1.0) for q in quote_data]
        spread_volatility = np.std(spreads) if len(spreads) > 1 else 0
        
        if spread_volatility > 0.001:
            return "AGGRESSIVE"  # Frequently adjusts spreads
        else:
            return "CONSERVATIVE"  # Stable spreads


class ShadowModelBuilder:
    """
    Builds shadow models that replicate institutional strategies
    Learns to trade like institutions
    """
    
    def __init__(self):
        self.shadow_models: Dict[str, ShadowModel] = {}
        
    def build_shadow_model(self, fingerprint: InstitutionalFingerprint) -> ShadowModel:
        """Build a shadow model from institutional fingerprint"""
        model_id = f"SHADOW_{fingerprint.institution_id}"
        
        # Extract strategy parameters
        parameters = {
            'avg_order_size': fingerprint.avg_order_size,
            'execution_time': fingerprint.avg_execution_time,
            'momentum_following': fingerprint.momentum_following,
            'mean_reversion': fingerprint.mean_reversion,
            'preferred_times': fingerprint.preferred_times
        }
        
        # Generate strategy description
        description = self._generate_strategy_description(fingerprint)
        
        model = ShadowModel(
            model_id=model_id,
            institution_type=fingerprint.institution_type,
            strategy_description=description,
            parameters=parameters,
            accuracy=0.5  # Initial estimate
        )
        
        self.shadow_models[model_id] = model
        
        logger.info(f"👥 Shadow Model Created: {model_id}")
        logger.info(f"   Strategy: {description}")
        
        return model
    
    def _generate_strategy_description(self, fingerprint: InstitutionalFingerprint) -> str:
        """Generate human-readable strategy description"""
        parts = []
        
        # Trading style
        parts.append(f"{fingerprint.trading_style.value} trading style")
        
        # Order size
        if fingerprint.avg_order_size > 1000000:
            parts.append("large orders")
        else:
            parts.append("medium orders")
        
        # Momentum vs mean reversion
        if fingerprint.momentum_following > 0.6:
            parts.append("momentum following")
        elif fingerprint.mean_reversion > 0.6:
            parts.append("mean reversion")
        
        # Execution
        if fingerprint.avg_execution_time < 60:
            parts.append("fast execution")
        else:
            parts.append("patient execution")
        
        return ", ".join(parts)
    
    def execute_shadow_trade(self, model_id: str, market_data: Dict) -> Optional[Dict]:
        """Execute a trade using shadow model"""
        if model_id not in self.shadow_models:
            return None
        
        model = self.shadow_models[model_id]
        
        # Generate trade signal based on model parameters
        signal = self._generate_signal(model, market_data)
        
        return signal
    
    def _generate_signal(self, model: ShadowModel, market_data: Dict) -> Dict:
        """Generate trading signal from shadow model"""
        params = model.parameters
        
        # Simplified signal generation
        signal = {
            'action': 'HOLD',
            'size': 0,
            'confidence': 0.5
        }
        
        # Check momentum
        if params.get('momentum_following', 0) > 0.6:
            price_change = market_data.get('price_change', 0)
            if price_change > 0.01:
                signal['action'] = 'BUY'
                signal['size'] = params.get('avg_order_size', 1000)
                signal['confidence'] = 0.7
            elif price_change < -0.01:
                signal['action'] = 'SELL'
                signal['size'] = params.get('avg_order_size', 1000)
                signal['confidence'] = 0.7
        
        return signal


class InstitutionalIntelligenceSystem:
    """
    Complete Institutional Intelligence System
    Combines all institutional analysis capabilities
    """
    
    def __init__(self):
        self.fingerprinter = BehavioralFingerprinter()
        self.order_flow_emulator = InstitutionalOrderFlowEmulator()
        self.whale_tracker = WhaleTracker()
        self.mm_profiler = MarketMakerProfiler()
        self.shadow_builder = ShadowModelBuilder()
        
    def analyze_order_flow(self, order_data: Dict) -> Dict:
        """Comprehensive order flow analysis"""
        analysis = {
            'timestamp': datetime.now(),
            'order_data': order_data,
            'institution_detected': None,
            'whale_detected': None,
            'shadow_signal': None
        }
        
        # 1. Identify institution
        institution_id = self.fingerprinter.observe_order_flow(order_data)
        analysis['institution_detected'] = institution_id
        
        # 2. Check for whale activity
        whale = self.whale_tracker.detect_whale_activity(order_data)
        if whale:
            analysis['whale_detected'] = whale
        
        # 3. Build/update shadow model
        if institution_id:
            fingerprint = self.fingerprinter.get_fingerprint(institution_id)
            if fingerprint and fingerprint.confidence > 0.7:
                shadow_model = self.shadow_builder.build_shadow_model(fingerprint)
                
                # Generate shadow signal
                market_data = {'price': order_data.get('price', 1.0), 'price_change': 0.01}
                shadow_signal = self.shadow_builder.execute_shadow_trade(shadow_model.model_id, market_data)
                analysis['shadow_signal'] = shadow_signal
        
        return analysis
    
    def get_intelligence_report(self) -> Dict:
        """Get comprehensive institutional intelligence report"""
        return {
            'total_institutions_tracked': len(self.fingerprinter.fingerprints),
            'active_whales': len(self.whale_tracker.get_active_whales()),
            'shadow_models': len(self.shadow_builder.shadow_models),
            'market_makers_profiled': len(self.mm_profiler.profiles),
            'institutions_by_type': self._count_by_type(),
            'top_whales': self._get_top_whales()
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count institutions by type"""
        counts = defaultdict(int)
        for fp in self.fingerprinter.get_all_fingerprints():
            counts[fp.institution_type.value] += 1
        return dict(counts)
    
    def _get_top_whales(self) -> List[Dict]:
        """Get top whales by size"""
        whales = sorted(self.whale_tracker.whale_history, key=lambda w: w.estimated_size, reverse=True)[:5]
        return [
            {
                'whale_id': w.whale_id,
                'size': w.estimated_size,
                'direction': w.direction,
                'impact_score': w.impact_score
            }
            for w in whales
        ]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create institutional intelligence system
    intel_system = InstitutionalIntelligenceSystem()
    
    # Simulate order flow
    orders = [
        {'size': 1500000, 'price': 1.1000, 'side': 'BUY', 'execution_time': 120, 'venue': 'NYSE', 'is_iceberg': True},
        {'size': 2000000, 'price': 1.1005, 'side': 'BUY', 'execution_time': 150, 'venue': 'NYSE', 'is_iceberg': True},
        {'size': 500000, 'price': 1.1010, 'side': 'SELL', 'execution_time': 30, 'venue': 'NASDAQ', 'is_aggressive': True},
    ]
    
    for order in orders:
        analysis = intel_system.analyze_order_flow(order)
        logger.info(f"\nOrder Analysis: ${order['size']:,.0f} {order['side']}")
        if analysis['institution_detected']:
            logger.info(f"  Institution: {analysis['institution_detected']}")
        if analysis['whale_detected']:
            logger.info(f"  🐋 WHALE: ${analysis['whale_detected'].estimated_size:,.0f}")
    
    # Get intelligence report
    report = intel_system.get_intelligence_report()
    print("\n" + "="*80)
    logger.info("INSTITUTIONAL INTELLIGENCE REPORT")
    print("="*80)
    logger.info(f"Institutions Tracked: {report['total_institutions_tracked']}")
    logger.info(f"Active Whales: {report['active_whales']}")
    logger.info(f"Shadow Models: {report['shadow_models']}")
    logger.info("\nInstitutions by Type:")
    for inst_type, count in report['institutions_by_type'].items():
        logger.info(f"  {inst_type}: {count}")
    print("="*80)
