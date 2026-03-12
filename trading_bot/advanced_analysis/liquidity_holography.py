"""
Liquidity Holography - 3D Liquidity Modeling

Don't just map liquidity; model it in 3D. Creates a "Liquidity Gravity Well" model
that visualizes price attraction to liquidity pools not just by proximity, but by
their relative "mass" (volume) and "density" (order cluster tightness).

Features:
- 3D liquidity gravity well modeling
- Liquidity mass and density calculation
- Path of least resistance prediction
- Temporal liquidity decay
- Liquidity DNA fingerprinting
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)


class LiquidityType(Enum):
    """Types of liquidity"""
    RESTING_BID = "resting_bid"
    RESTING_ASK = "resting_ask"
    STOP_CLUSTER = "stop_cluster"
    LIMIT_CLUSTER = "limit_cluster"
    ICEBERG = "iceberg"
    DARK_POOL = "dark_pool"
    INSTITUTIONAL = "institutional"


class GravityDirection(Enum):
    """Direction of liquidity gravity"""
    ATTRACTING = "attracting"  # Price pulled toward
    REPELLING = "repelling"    # Price pushed away
    NEUTRAL = "neutral"


@dataclass
class LiquidityPool:
    """Single liquidity pool"""
    pool_id: str
    price_level: float
    volume: float
    density: float  # Orders per price tick
    liquidity_type: LiquidityType
    timestamp: datetime
    age_hours: float
    
    # Gravity metrics
    mass: float  # Volume-weighted importance
    gravity_strength: float  # Attraction/repulsion strength
    gravity_direction: GravityDirection
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'pool_id': self.pool_id,
            'price_level': self.price_level,
            'volume': self.volume,
            'density': self.density,
            'liquidity_type': self.liquidity_type.value,
            'age_hours': self.age_hours,
            'mass': self.mass,
            'gravity_strength': self.gravity_strength,
            'gravity_direction': self.gravity_direction.value
        }


@dataclass
class GravityWell:
    """3D gravity well representation"""
    center_price: float
    center_time: datetime
    depth: float  # How deep the well is (attraction strength)
    radius: float  # Price range of influence
    mass: float
    pools_contributing: List[str]  # Pool IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'center_price': self.center_price,
            'center_time': self.center_time.isoformat(),
            'depth': self.depth,
            'radius': self.radius,
            'mass': self.mass,
            'pools_contributing': self.pools_contributing
        }


@dataclass
class LiquidityPath:
    """Predicted path of least resistance"""
    start_price: float
    target_price: float
    path_points: List[Tuple[float, float]]  # (price, probability)
    resistance_score: float  # 0-1, lower is easier path
    gravity_wells_crossed: List[str]
    estimated_time: timedelta
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'start_price': self.start_price,
            'target_price': self.target_price,
            'path_points': self.path_points,
            'resistance_score': self.resistance_score,
            'gravity_wells_crossed': self.gravity_wells_crossed,
            'estimated_time_minutes': self.estimated_time.total_seconds() / 60,
            'confidence': self.confidence
        }


@dataclass
class LiquidityDNA:
    """Liquidity DNA fingerprint"""
    symbol: str
    timestamp: datetime
    sequence: List[str]  # Encoded liquidity pattern
    pattern_hash: str
    similarity_to_institutional: float
    similarity_to_retail: float
    classification: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'sequence_length': len(self.sequence),
            'pattern_hash': self.pattern_hash,
            'similarity_to_institutional': self.similarity_to_institutional,
            'similarity_to_retail': self.similarity_to_retail,
            'classification': self.classification
        }


class LiquidityHolography:
    """
    Liquidity Holography System
    
    Creates 3D models of liquidity distribution with gravity well
    analysis for predicting price movement paths.
    """
    
    # Decay constants
    LIQUIDITY_HALF_LIFE_HOURS = 4.0  # Liquidity importance halves every 4 hours
    
    # Gravity constants
    GRAVITY_CONSTANT = 1.0
    MIN_MASS_THRESHOLD = 100  # Minimum volume to create gravity
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
        
            # Liquidity pools
            self.pools: Dict[str, LiquidityPool] = {}
        
            # Gravity wells
            self.gravity_wells: List[GravityWell] = []
        
            # History
            self.pool_history: deque = deque(maxlen=10000)
            self.path_predictions: deque = deque(maxlen=1000)
        
            # Current price
            self.current_price: float = 0
        
            # DNA patterns
            self.institutional_patterns: List[str] = [
                'LLLS', 'SLLL', 'LSLS', 'SLSL',  # Large-Small patterns
                'IIII', 'IIIS', 'SIII',  # Iceberg patterns
            ]
            self.retail_patterns: List[str] = [
                'SSSS', 'SSLS', 'LSSS',  # Small order patterns
                'RRRR', 'RRRS',  # Rapid patterns
            ]
        
            logger.info("LiquidityHolography initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_liquidity_pool(
        self,
        price_level: float,
        volume: float,
        liquidity_type: LiquidityType,
        density: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> LiquidityPool:
        """Add or update a liquidity pool"""
        try:
            import uuid
        
            timestamp = timestamp or datetime.now()
            pool_id = f"pool_{price_level:.5f}_{timestamp.timestamp():.0f}"
        
            # Calculate density if not provided
            if density is None:
                density = volume / 10  # Approximate
        
            # Calculate age
            age_hours = 0.0
        
            # Calculate mass with time decay
            decay_factor = np.exp(-0.693 * age_hours / self.LIQUIDITY_HALF_LIFE_HOURS)
            mass = volume * density * decay_factor
        
            # Determine gravity direction
            if liquidity_type in [LiquidityType.RESTING_BID, LiquidityType.STOP_CLUSTER]:
                gravity_direction = GravityDirection.ATTRACTING
            elif liquidity_type == LiquidityType.RESTING_ASK:
                gravity_direction = GravityDirection.ATTRACTING
            else:
                gravity_direction = GravityDirection.NEUTRAL
        
            # Calculate gravity strength
            gravity_strength = self.GRAVITY_CONSTANT * mass / (1 + abs(price_level - self.current_price) ** 2)
        
            pool = LiquidityPool(
                pool_id=pool_id,
                price_level=price_level,
                volume=volume,
                density=density,
                liquidity_type=liquidity_type,
                timestamp=timestamp,
                age_hours=age_hours,
                mass=mass,
                gravity_strength=gravity_strength,
                gravity_direction=gravity_direction
            )
        
            self.pools[pool_id] = pool
            self.pool_history.append(pool)
        
            # Update gravity wells
            self._update_gravity_wells()
        
            return pool
        except Exception as e:
            logger.error(f"Error in add_liquidity_pool: {e}")
            raise
    
    def update_current_price(self, price: float):
        """Update current price and recalculate gravity"""
        try:
            self.current_price = price
            self._recalculate_gravity()
        except Exception as e:
            logger.error(f"Error in update_current_price: {e}")
            raise
    
    def _recalculate_gravity(self):
        """Recalculate gravity for all pools"""
        try:
            for pool in self.pools.values():
                # Update age
                pool.age_hours = (datetime.now() - pool.timestamp).total_seconds() / 3600
            
                # Recalculate mass with decay
                decay_factor = np.exp(-0.693 * pool.age_hours / self.LIQUIDITY_HALF_LIFE_HOURS)
                pool.mass = pool.volume * pool.density * decay_factor
            
                # Recalculate gravity strength
                distance = abs(pool.price_level - self.current_price)
                pool.gravity_strength = self.GRAVITY_CONSTANT * pool.mass / (1 + distance ** 2)
        except Exception as e:
            logger.error(f"Error in _recalculate_gravity: {e}")
            raise
    
    def _update_gravity_wells(self):
        """Update gravity wells from pools"""
        try:
            self.gravity_wells = []
        
            # Group nearby pools
            if not self.pools:
                return
        
            pools_list = list(self.pools.values())
            pools_list.sort(key=lambda p: p.price_level)
        
            # Cluster pools within price range
            cluster_range = self.current_price * 0.001  # 0.1% range
        
            current_cluster = [pools_list[0]]
        
            for pool in pools_list[1:]:
                if pool.price_level - current_cluster[-1].price_level < cluster_range:
                    current_cluster.append(pool)
                else:
                    # Create gravity well from cluster
                    if len(current_cluster) > 0:
                        well = self._create_gravity_well(current_cluster)
                        if well.mass > self.MIN_MASS_THRESHOLD:
                            self.gravity_wells.append(well)
                    current_cluster = [pool]
        
            # Don't forget last cluster
            if current_cluster:
                well = self._create_gravity_well(current_cluster)
                if well.mass > self.MIN_MASS_THRESHOLD:
                    self.gravity_wells.append(well)
        except Exception as e:
            logger.error(f"Error in _update_gravity_wells: {e}")
            raise
    
    def _create_gravity_well(self, pools: List[LiquidityPool]) -> GravityWell:
        """Create gravity well from pool cluster"""
        try:
            total_mass = sum(p.mass for p in pools)
        
            # Mass-weighted center
            if total_mass > 0:
                center_price = sum(p.price_level * p.mass for p in pools) / total_mass
            else:
                center_price = np.mean([p.price_level for p in pools])
        
            # Depth based on total mass
            depth = np.log1p(total_mass) / 10
        
            # Radius based on price spread
            prices = [p.price_level for p in pools]
            radius = (max(prices) - min(prices)) / 2 if len(prices) > 1 else center_price * 0.001
        
            return GravityWell(
                center_price=center_price,
                center_time=datetime.now(),
                depth=depth,
                radius=radius,
                mass=total_mass,
                pools_contributing=[p.pool_id for p in pools]
            )
        except Exception as e:
            logger.error(f"Error in _create_gravity_well: {e}")
            raise
    
    def calculate_gravity_field(
        self,
        price_range: Tuple[float, float],
        resolution: int = 100
    ) -> np.ndarray:
        """
        Calculate gravity field across price range
        
        Returns 2D array of gravity values (price x time)
        """
        try:
            prices = np.linspace(price_range[0], price_range[1], resolution)
            gravity_field = np.zeros(resolution)
        
            for i, price in enumerate(prices):
                total_gravity = 0
            
                for pool in self.pools.values():
                    distance = abs(price - pool.price_level)
                
                    # Gravity calculation (inverse square with mass)
                    if distance > 0:
                        gravity = pool.mass / (distance ** 2)
                    else:
                        gravity = pool.mass * 100  # At the pool
                
                    # Direction
                    if pool.gravity_direction == GravityDirection.ATTRACTING:
                        if price > pool.price_level:
                            total_gravity -= gravity  # Pull down
                        else:
                            total_gravity += gravity  # Pull up
                    elif pool.gravity_direction == GravityDirection.REPELLING:
                        if price > pool.price_level:
                            total_gravity += gravity  # Push up
                        else:
                            total_gravity -= gravity  # Push down
            
                gravity_field[i] = total_gravity
        
            return gravity_field
        except Exception as e:
            logger.error(f"Error in calculate_gravity_field: {e}")
            raise
    
    def predict_path_of_least_resistance(
        self,
        target_price: float,
        time_horizon_minutes: int = 60
    ) -> LiquidityPath:
        """
        Predict the path of least resistance to target price
        
        Uses gravity field to find optimal path
        """
        try:
            if self.current_price == 0:
                raise ValueError("Current price not set")
        
            start = self.current_price
            end = target_price
        
            # Generate path points
            num_points = 20
            path_points = []
        
            # Simple path following gravity gradient
            current = start
            step = (end - start) / num_points
        
            total_resistance = 0
            wells_crossed = []
        
            for i in range(num_points):
                next_price = current + step
            
                # Calculate resistance at this point
                resistance = 0
                for pool in self.pools.values():
                    if min(current, next_price) <= pool.price_level <= max(current, next_price):
                        # Crossing this pool
                        resistance += pool.mass / 1000
                    
                # Check gravity wells
                for well in self.gravity_wells:
                    if min(current, next_price) <= well.center_price <= max(current, next_price):
                        wells_crossed.append(f"well_{well.center_price:.2f}")
                        resistance += well.depth
            
                total_resistance += resistance
            
                # Probability of reaching this point
                prob = max(0.1, 1 - resistance / 10)
                path_points.append((next_price, prob))
            
                current = next_price
        
            # Normalize resistance
            resistance_score = min(1.0, total_resistance / 10)
        
            # Estimate time based on resistance
            base_time = time_horizon_minutes
            estimated_time = timedelta(minutes=base_time * (1 + resistance_score))
        
            # Confidence based on gravity well analysis
            confidence = max(0.3, 1 - resistance_score)
        
            path = LiquidityPath(
                start_price=start,
                target_price=target_price,
                path_points=path_points,
                resistance_score=resistance_score,
                gravity_wells_crossed=list(set(wells_crossed)),
                estimated_time=estimated_time,
                confidence=confidence
            )
        
            self.path_predictions.append(path)
        
            return path
        except Exception as e:
            logger.error(f"Error in predict_path_of_least_resistance: {e}")
            raise
    
    def analyze_liquidity_dna(
        self,
        order_sequence: List[Dict[str, Any]]
    ) -> LiquidityDNA:
        """
        Analyze order sequence to create liquidity DNA fingerprint
        
        Identifies if pattern matches institutional or retail behavior
        """
        try:
            import hashlib
        
            # Encode sequence
            encoded = []
            for order in order_sequence:
                volume = order.get('volume', 0)
                order_type = order.get('type', 'limit')
            
                # Encode based on characteristics
                if volume > 10000:
                    encoded.append('L')  # Large
                elif volume > 1000:
                    encoded.append('M')  # Medium
                else:
                    encoded.append('S')  # Small
            
                if order_type == 'iceberg':
                    encoded.append('I')
                elif order_type == 'market':
                    encoded.append('R')  # Rapid/aggressive
        
            sequence_str = ''.join(encoded)
        
            # Create hash
            pattern_hash = hashlib.md5(sequence_str.encode()).hexdigest()[:8]
        
            # Calculate similarity to known patterns
            inst_similarity = self._pattern_similarity(sequence_str, self.institutional_patterns)
            retail_similarity = self._pattern_similarity(sequence_str, self.retail_patterns)
        
            # Classification
            if inst_similarity > retail_similarity + 0.2:
                classification = "INSTITUTIONAL"
            elif retail_similarity > inst_similarity + 0.2:
                classification = "RETAIL"
            else:
                classification = "MIXED"
        
            return LiquidityDNA(
                symbol="",
                timestamp=datetime.now(),
                sequence=encoded,
                pattern_hash=pattern_hash,
                similarity_to_institutional=inst_similarity,
                similarity_to_retail=retail_similarity,
                classification=classification
            )
        except Exception as e:
            logger.error(f"Error in analyze_liquidity_dna: {e}")
            raise
    
    def _pattern_similarity(self, sequence: str, patterns: List[str]) -> float:
        """Calculate similarity to pattern set"""
        try:
            if not sequence or not patterns:
                return 0.0
        
            max_similarity = 0.0
        
            for pattern in patterns:
                # Simple substring matching
                matches = 0
                for i in range(len(sequence) - len(pattern) + 1):
                    substr = sequence[i:i+len(pattern)]
                    match_count = sum(1 for a, b in zip(substr, pattern) if a == b)
                    matches = max(matches, match_count / len(pattern))
            
                max_similarity = max(max_similarity, matches)
        
            return max_similarity
        except Exception as e:
            logger.error(f"Error in _pattern_similarity: {e}")
            raise
    
    def get_liquidity_heatmap(
        self,
        price_range: Tuple[float, float],
        time_range_hours: int = 24,
        resolution: int = 50
    ) -> Dict[str, Any]:
        """
        Generate liquidity heatmap data
        
        Returns data for 3D visualization
        """
        try:
            prices = np.linspace(price_range[0], price_range[1], resolution)
            times = np.linspace(0, time_range_hours, resolution)
        
            heatmap = np.zeros((resolution, resolution))
        
            for pool in self.pools.values():
                # Find price index
                price_idx = int((pool.price_level - price_range[0]) / (price_range[1] - price_range[0]) * (resolution - 1))
                price_idx = max(0, min(resolution - 1, price_idx))
            
                # Find time index
                time_idx = int(pool.age_hours / time_range_hours * (resolution - 1))
                time_idx = max(0, min(resolution - 1, time_idx))
            
                # Add mass to heatmap with gaussian spread
                for di in range(-2, 3):
                    for dj in range(-2, 3):
                        ni, nj = price_idx + di, time_idx + dj
                        if 0 <= ni < resolution and 0 <= nj < resolution:
                            spread = np.exp(-(di**2 + dj**2) / 2)
                            heatmap[ni, nj] += pool.mass * spread
        
            return {
                'heatmap': heatmap.tolist(),
                'price_range': price_range,
                'time_range_hours': time_range_hours,
                'resolution': resolution,
                'max_intensity': float(heatmap.max()),
                'total_liquidity': float(heatmap.sum())
            }
        except Exception as e:
            logger.error(f"Error in get_liquidity_heatmap: {e}")
            raise
    
    def get_gravity_summary(self) -> Dict[str, Any]:
        """Get summary of gravity analysis"""
        try:
            if not self.pools:
                return {'message': 'No liquidity pools'}
        
            total_mass = sum(p.mass for p in self.pools.values())
        
            # Find strongest gravity wells
            wells_sorted = sorted(self.gravity_wells, key=lambda w: w.depth, reverse=True)
        
            # Nearest significant liquidity
            if self.current_price > 0:
                pools_by_distance = sorted(
                    self.pools.values(),
                    key=lambda p: abs(p.price_level - self.current_price)
                )
                nearest = pools_by_distance[:5] if pools_by_distance else []
            else:
                nearest = []
        
            return {
                'total_pools': len(self.pools),
                'total_mass': total_mass,
                'gravity_wells': len(self.gravity_wells),
                'strongest_wells': [w.to_dict() for w in wells_sorted[:3]],
                'nearest_liquidity': [p.to_dict() for p in nearest],
                'current_price': self.current_price
            }
        except Exception as e:
            logger.error(f"Error in get_gravity_summary: {e}")
            raise


# Factory function
def create_liquidity_holography(config: Optional[Dict[str, Any]] = None) -> LiquidityHolography:
    """Create liquidity holography system"""
    return LiquidityHolography(config)
