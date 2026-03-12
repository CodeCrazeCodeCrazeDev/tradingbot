"""
Liquidity Gravity Well Model

Advanced 3D liquidity modeling that visualizes price attraction to liquidity pools
based on their relative "mass" (volume) and "density" (order cluster tightness).

Features:
- 3D liquidity mapping with gravitational attraction
- Path of least resistance prediction
- Liquidity pool mass and density calculation
- Gravitational force vectors
- Price trajectory forecasting
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available - using fallback calculations")


class LiquidityType(Enum):
    """Types of liquidity pools."""
    BUY_SIDE = "buy_side"  # Stop losses above price
    SELL_SIDE = "sell_side"  # Stop losses below price
    RESTING_BIDS = "resting_bids"
    RESTING_ASKS = "resting_asks"
    ICEBERG = "iceberg"
    DARK_POOL = "dark_pool"


class GravityStrength(Enum):
    """Gravitational pull strength."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXTREME = 4


@dataclass
class LiquidityPool:
    """Represents a liquidity pool with gravitational properties."""
    pool_id: str
    price_level: float
    volume: float  # Total volume (mass)
    order_count: int  # Number of orders
    price_range: float  # Price spread of the cluster
    liquidity_type: LiquidityType
    timestamp: datetime
    decay_factor: float = 1.0  # Time-based decay
    
    @property
    def density(self) -> float:
        """Calculate order density (orders per price unit)."""
        if self.price_range > 0:
            return self.order_count / self.price_range
        return self.order_count
    
    @property
    def mass(self) -> float:
        """Effective mass considering volume and density."""
        return self.volume * (1 + math.log1p(self.density))
    
    @property
    def gravitational_constant(self) -> float:
        """Pool-specific gravitational constant based on type."""
        type_multipliers = {
            LiquidityType.BUY_SIDE: 1.2,  # Stop hunts are attractive
            LiquidityType.SELL_SIDE: 1.2,
            LiquidityType.RESTING_BIDS: 1.0,
            LiquidityType.RESTING_ASKS: 1.0,
            LiquidityType.ICEBERG: 1.5,  # Hidden liquidity very attractive
            LiquidityType.DARK_POOL: 1.8,
        }
        return type_multipliers.get(self.liquidity_type, 1.0)
    
    def calculate_force(self, current_price: float) -> float:
        """
        Calculate gravitational force on price.
        
        F = G * (M1 * M2) / r^2
        Simplified: F = G * mass / distance^2
        """
        distance = abs(self.price_level - current_price)
        if distance < 0.0001:  # Avoid division by zero
            distance = 0.0001
        
        force = (self.gravitational_constant * self.mass * self.decay_factor) / (distance ** 2)
        
        # Direction: positive if pool is above price, negative if below
        if self.price_level > current_price:
            return force
        else:
            return -force
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pool_id': self.pool_id,
            'price_level': self.price_level,
            'volume': self.volume,
            'order_count': self.order_count,
            'density': self.density,
            'mass': self.mass,
            'liquidity_type': self.liquidity_type.value,
            'decay_factor': self.decay_factor
        }


@dataclass
class GravityVector:
    """Represents a gravitational force vector."""
    magnitude: float
    direction: float  # Positive = upward, Negative = downward
    dominant_pool: Optional[LiquidityPool]
    contributing_pools: List[LiquidityPool]
    
    @property
    def strength(self) -> GravityStrength:
        """Categorize gravity strength."""
        abs_mag = abs(self.magnitude)
        if abs_mag > 1000:
            return GravityStrength.EXTREME
        elif abs_mag > 500:
            return GravityStrength.STRONG
        elif abs_mag > 100:
            return GravityStrength.MODERATE
        else:
            return GravityStrength.WEAK
    
    @property
    def bias(self) -> str:
        """Get directional bias."""
        if self.direction > 0.1:
            return "BULLISH"
        elif self.direction < -0.1:
            return "BEARISH"
        else:
            return "NEUTRAL"


@dataclass
class PathPrediction:
    """Predicted price path based on liquidity gravity."""
    current_price: float
    target_price: float
    probability: float
    time_estimate_minutes: int
    path_resistance: float  # 0-1, lower is easier path
    intermediate_levels: List[float]
    gravity_vector: GravityVector
    analysis: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_price': self.current_price,
            'target_price': self.target_price,
            'probability': self.probability,
            'time_estimate_minutes': self.time_estimate_minutes,
            'path_resistance': self.path_resistance,
            'intermediate_levels': self.intermediate_levels,
            'bias': self.gravity_vector.bias,
            'gravity_strength': self.gravity_vector.strength.name,
            'analysis': self.analysis
        }


@dataclass
class LiquidityHeatmap:
    """3D representation of liquidity landscape."""
    price_levels: List[float]
    time_slices: List[datetime]
    gravity_matrix: List[List[float]]  # price x time
    hotspots: List[Tuple[float, datetime, float]]  # (price, time, intensity)
    
    def get_intensity_at(self, price: float, time: datetime) -> float:
        """Get gravity intensity at specific price/time."""
        # Find nearest indices
        price_idx = min(range(len(self.price_levels)), 
                       key=lambda i: abs(self.price_levels[i] - price))
        time_idx = min(range(len(self.time_slices)),
                      key=lambda i: abs((self.time_slices[i] - time).total_seconds()))
        
        if price_idx < len(self.gravity_matrix) and time_idx < len(self.gravity_matrix[0]):
            return self.gravity_matrix[price_idx][time_idx]
        return 0.0


class TemporalDecayCalculator:
    """
    Calculates time-based decay for liquidity pools.
    
    Recent liquidity is more potent than old liquidity.
    Decay is adjusted based on current volatility.
    """
    
    def __init__(self, base_half_life_hours: float = 4.0):
        self.base_half_life = base_half_life_hours
        self.volatility_factor = 1.0
    
    def update_volatility(self, current_atr: float, average_atr: float):
        """Adjust decay rate based on volatility."""
        if average_atr > 0:
            # Higher volatility = faster decay
            self.volatility_factor = current_atr / average_atr
        else:
            self.volatility_factor = 1.0
    
    def calculate_decay(self, pool_age_hours: float) -> float:
        """
        Calculate decay factor for a pool.
        
        Returns value between 0 and 1.
        """
        adjusted_half_life = self.base_half_life / max(0.5, self.volatility_factor)
        
        # Exponential decay: e^(-λt) where λ = ln(2)/half_life
        decay_constant = math.log(2) / adjusted_half_life
        decay = math.exp(-decay_constant * pool_age_hours)
        
        return max(0.01, decay)  # Minimum 1% potency


class LiquidityGravityWell:
    """
    Main Liquidity Gravity Well model.
    
    Models liquidity as gravitational wells that attract price.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Pools storage
        self.pools: Dict[str, LiquidityPool] = {}
        self.pool_history: List[LiquidityPool] = []
        
        # Decay calculator
        self.decay_calc = TemporalDecayCalculator(
            base_half_life_hours=self.config.get('decay_half_life_hours', 4.0)
        )
        
        # Configuration
        self.min_pool_volume = self.config.get('min_pool_volume', 1000)
        self.cluster_distance = self.config.get('cluster_distance', 0.001)  # 0.1%
        
        logger.info("LiquidityGravityWell initialized")
    
    def add_liquidity_level(
        self,
        price: float,
        volume: float,
        order_count: int,
        liquidity_type: LiquidityType,
        price_range: Optional[float] = None
    ):
        """
        Add a liquidity level to the model.
        
        Args:
            price: Price level
            volume: Total volume at level
            order_count: Number of orders
            liquidity_type: Type of liquidity
            price_range: Price spread of cluster
        """
        if volume < self.min_pool_volume:
            return
        
        pool_id = f"{liquidity_type.value}_{price:.5f}"
        
        pool = LiquidityPool(
            pool_id=pool_id,
            price_level=price,
            volume=volume,
            order_count=order_count,
            price_range=price_range or (price * self.cluster_distance),
            liquidity_type=liquidity_type,
            timestamp=datetime.now()
        )
        
        self.pools[pool_id] = pool
        self.pool_history.append(pool)
    
    def add_order_book_snapshot(
        self,
        bids: List[Tuple[float, float]],  # (price, volume)
        asks: List[Tuple[float, float]]
    ):
        """
        Add liquidity from order book snapshot.
        
        Args:
            bids: List of (price, volume) tuples
            asks: List of (price, volume) tuples
        """
        # Cluster nearby bids
        bid_clusters = self._cluster_levels(bids)
        for price, volume, count, price_range in bid_clusters:
            self.add_liquidity_level(
                price, volume, count,
                LiquidityType.RESTING_BIDS,
                price_range
            )
        
        # Cluster nearby asks
        ask_clusters = self._cluster_levels(asks)
        for price, volume, count, price_range in ask_clusters:
            self.add_liquidity_level(
                price, volume, count,
                LiquidityType.RESTING_ASKS,
                price_range
            )
    
    def _cluster_levels(
        self,
        levels: List[Tuple[float, float]]
    ) -> List[Tuple[float, float, int, float]]:
        """
        Cluster nearby price levels.
        
        Returns:
            List of (avg_price, total_volume, count, price_range)
        """
        if not levels:
            return []
        
        clusters = []
        current_cluster = [levels[0]]
        
        for i in range(1, len(levels)):
            price, volume = levels[i]
            cluster_price = sum(p for p, v in current_cluster) / len(current_cluster)
            
            # Check if within cluster distance
            if abs(price - cluster_price) / cluster_price <= self.cluster_distance:
                current_cluster.append((price, volume))
            else:
                # Finalize current cluster
                if current_cluster:
                    clusters.append(self._finalize_cluster(current_cluster))
                current_cluster = [(price, volume)]
        
        # Don't forget last cluster
        if current_cluster:
            clusters.append(self._finalize_cluster(current_cluster))
        
        return clusters
    
    def _finalize_cluster(
        self,
        cluster: List[Tuple[float, float]]
    ) -> Tuple[float, float, int, float]:
        """Finalize a cluster into summary stats."""
        prices = [p for p, v in cluster]
        volumes = [v for p, v in cluster]
        
        avg_price = sum(p * v for p, v in cluster) / sum(volumes)  # Volume-weighted
        total_volume = sum(volumes)
        count = len(cluster)
        price_range = max(prices) - min(prices) if len(prices) > 1 else prices[0] * 0.001
        
        return (avg_price, total_volume, count, price_range)
    
    def update_decay(self, current_atr: float, average_atr: float):
        """Update decay factors based on volatility."""
        self.decay_calc.update_volatility(current_atr, average_atr)
        
        now = datetime.now()
        for pool in self.pools.values():
            age_hours = (now - pool.timestamp).total_seconds() / 3600
            pool.decay_factor = self.decay_calc.calculate_decay(age_hours)
    
    def calculate_gravity_vector(self, current_price: float) -> GravityVector:
        """
        Calculate net gravitational force on current price.
        
        Returns:
            GravityVector with magnitude and direction
        """
        if not self.pools:
            return GravityVector(
                magnitude=0,
                direction=0,
                dominant_pool=None,
                contributing_pools=[]
            )
        
        total_force = 0
        forces_by_pool = []
        
        for pool in self.pools.values():
            force = pool.calculate_force(current_price)
            total_force += force
            forces_by_pool.append((pool, force))
        
        # Find dominant pool
        forces_by_pool.sort(key=lambda x: abs(x[1]), reverse=True)
        dominant = forces_by_pool[0][0] if forces_by_pool else None
        
        # Get contributing pools (top 5)
        contributing = [p for p, f in forces_by_pool[:5]]
        
        # Normalize direction
        direction = 1 if total_force > 0 else -1 if total_force < 0 else 0
        
        return GravityVector(
            magnitude=abs(total_force),
            direction=direction * (abs(total_force) / (abs(total_force) + 100)),  # Normalize
            dominant_pool=dominant,
            contributing_pools=contributing
        )
    
    def predict_path(
        self,
        current_price: float,
        volatility: float,
        lookforward_minutes: int = 60
    ) -> PathPrediction:
        """
        Predict price path based on liquidity gravity.
        
        Args:
            current_price: Current market price
            volatility: Current ATR or volatility measure
            lookforward_minutes: Prediction horizon
            
        Returns:
            PathPrediction with target and probability
        """
        gravity = self.calculate_gravity_vector(current_price)
        
        if gravity.magnitude < 1:
            return PathPrediction(
                current_price=current_price,
                target_price=current_price,
                probability=0.5,
                time_estimate_minutes=lookforward_minutes,
                path_resistance=0.5,
                intermediate_levels=[],
                gravity_vector=gravity,
                analysis="No significant liquidity attraction detected"
            )
        
        # Calculate target based on dominant pool
        if gravity.dominant_pool:
            target = gravity.dominant_pool.price_level
        else:
            # Estimate based on gravity direction
            move = volatility * gravity.direction * math.sqrt(lookforward_minutes / 60)
            target = current_price + move
        
        # Calculate path resistance
        resistance = self._calculate_path_resistance(current_price, target)
        
        # Calculate probability based on gravity strength and resistance
        base_prob = 0.5 + (gravity.magnitude / (gravity.magnitude + 500)) * 0.3
        prob = base_prob * (1 - resistance * 0.5)
        
        # Find intermediate levels
        intermediates = self._find_intermediate_levels(current_price, target)
        
        # Time estimate based on distance and volatility
        distance = abs(target - current_price)
        time_est = int((distance / volatility) * 60) if volatility > 0 else lookforward_minutes
        
        # Generate analysis
        analysis = self._generate_analysis(gravity, target, current_price, resistance)
        
        return PathPrediction(
            current_price=current_price,
            target_price=target,
            probability=min(0.95, max(0.05, prob)),
            time_estimate_minutes=min(time_est, lookforward_minutes * 2),
            path_resistance=resistance,
            intermediate_levels=intermediates,
            gravity_vector=gravity,
            analysis=analysis
        )
    
    def _calculate_path_resistance(self, start: float, end: float) -> float:
        """Calculate resistance along price path."""
        if not self.pools:
            return 0.5
        
        min_price = min(start, end)
        max_price = max(start, end)
        
        # Find pools in the path
        blocking_pools = [
            p for p in self.pools.values()
            if min_price < p.price_level < max_price
        ]
        
        if not blocking_pools:
            return 0.1  # Low resistance
        
        # Calculate resistance based on blocking pool mass
        total_blocking_mass = sum(p.mass * p.decay_factor for p in blocking_pools)
        
        # Normalize to 0-1
        resistance = total_blocking_mass / (total_blocking_mass + 10000)
        
        return min(0.9, resistance)
    
    def _find_intermediate_levels(
        self,
        start: float,
        end: float,
        max_levels: int = 5
    ) -> List[float]:
        """Find significant intermediate price levels."""
        min_price = min(start, end)
        max_price = max(start, end)
        
        # Get pools in range
        pools_in_range = [
            p for p in self.pools.values()
            if min_price < p.price_level < max_price
        ]
        
        # Sort by mass
        pools_in_range.sort(key=lambda p: p.mass * p.decay_factor, reverse=True)
        
        # Return top levels
        return [p.price_level for p in pools_in_range[:max_levels]]
    
    def _generate_analysis(
        self,
        gravity: GravityVector,
        target: float,
        current: float,
        resistance: float
    ) -> str:
        """Generate human-readable analysis."""
        parts = []
        
        # Direction
        if gravity.bias == "BULLISH":
            parts.append(f"Bullish gravity pull toward {target:.5f}")
        elif gravity.bias == "BEARISH":
            parts.append(f"Bearish gravity pull toward {target:.5f}")
        else:
            parts.append("Neutral gravity - no clear directional bias")
        
        # Strength
        parts.append(f"Gravity strength: {gravity.strength.name}")
        
        # Dominant pool
        if gravity.dominant_pool:
            parts.append(
                f"Dominant pool: {gravity.dominant_pool.liquidity_type.value} "
                f"at {gravity.dominant_pool.price_level:.5f} "
                f"(mass: {gravity.dominant_pool.mass:,.0f})"
            )
        
        # Resistance
        if resistance > 0.6:
            parts.append("HIGH path resistance - expect choppy movement")
        elif resistance > 0.3:
            parts.append("Moderate path resistance")
        else:
            parts.append("LOW path resistance - clear path")
        
        return " | ".join(parts)
    
    def generate_heatmap(
        self,
        price_range: Tuple[float, float],
        time_range_hours: int = 24,
        resolution: int = 50
    ) -> LiquidityHeatmap:
        """
        Generate 3D liquidity heatmap.
        
        Args:
            price_range: (min_price, max_price)
            time_range_hours: Hours of history
            resolution: Number of price levels
            
        Returns:
            LiquidityHeatmap with gravity intensities
        """
        min_price, max_price = price_range
        price_step = (max_price - min_price) / resolution
        
        price_levels = [min_price + i * price_step for i in range(resolution)]
        
        # Time slices (hourly)
        now = datetime.now()
        time_slices = [now - timedelta(hours=i) for i in range(time_range_hours, -1, -1)]
        
        # Calculate gravity matrix
        gravity_matrix = []
        hotspots = []
        
        for price in price_levels:
            row = []
            for t in time_slices:
                # Calculate gravity at this price/time
                intensity = self._calculate_intensity_at(price, t)
                row.append(intensity)
                
                # Track hotspots
                if intensity > 500:
                    hotspots.append((price, t, intensity))
            
            gravity_matrix.append(row)
        
        return LiquidityHeatmap(
            price_levels=price_levels,
            time_slices=time_slices,
            gravity_matrix=gravity_matrix,
            hotspots=sorted(hotspots, key=lambda x: x[2], reverse=True)[:10]
        )
    
    def _calculate_intensity_at(self, price: float, time: datetime) -> float:
        """Calculate gravity intensity at specific price/time."""
        intensity = 0
        
        for pool in self.pools.values():
            # Time-based filtering
            if pool.timestamp > time:
                continue
            
            # Calculate contribution
            distance = abs(pool.price_level - price)
            if distance < 0.0001:
                distance = 0.0001
            
            contribution = (pool.mass * pool.decay_factor) / (distance ** 1.5)
            intensity += contribution
        
        return intensity
    
    def get_strongest_pools(self, n: int = 5) -> List[LiquidityPool]:
        """Get the N strongest liquidity pools."""
        pools = list(self.pools.values())
        pools.sort(key=lambda p: p.mass * p.decay_factor, reverse=True)
        return pools[:n]
    
    def cleanup_old_pools(self, max_age_hours: int = 48):
        """Remove old pools."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = [
            pool_id for pool_id, pool in self.pools.items()
            if pool.timestamp < cutoff
        ]
        
        for pool_id in to_remove:
            del self.pools[pool_id]
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status."""
        gravity = self.calculate_gravity_vector(0) if self.pools else None
        
        return {
            'total_pools': len(self.pools),
            'total_mass': sum(p.mass for p in self.pools.values()),
            'strongest_pools': [p.to_dict() for p in self.get_strongest_pools(3)],
            'current_bias': gravity.bias if gravity else 'UNKNOWN',
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_liquidity_gravity_well(config: Optional[Dict] = None) -> LiquidityGravityWell:
    """Create LiquidityGravityWell instance."""
    return LiquidityGravityWell(config)


# Example usage
if __name__ == "__main__":
    import random
    
    model = create_liquidity_gravity_well()
    
    current_price = 1.1000
    
    # Add some liquidity pools
    # Buy-side liquidity (stops above)
    model.add_liquidity_level(1.1050, 5000000, 150, LiquidityType.BUY_SIDE)
    model.add_liquidity_level(1.1080, 3000000, 100, LiquidityType.BUY_SIDE)
    
    # Sell-side liquidity (stops below)
    model.add_liquidity_level(1.0950, 4000000, 120, LiquidityType.SELL_SIDE)
    model.add_liquidity_level(1.0920, 2500000, 80, LiquidityType.SELL_SIDE)
    
    # Resting orders
    model.add_liquidity_level(1.0980, 2000000, 200, LiquidityType.RESTING_BIDS)
    model.add_liquidity_level(1.1020, 1800000, 180, LiquidityType.RESTING_ASKS)
    
    # Dark pool
    model.add_liquidity_level(1.1030, 8000000, 10, LiquidityType.DARK_POOL)
    
    print("=" * 60)
    print("LIQUIDITY GRAVITY WELL MODEL")
    print("=" * 60)
    
    # Calculate gravity
    gravity = model.calculate_gravity_vector(current_price)
    
    print(f"\nCurrent Price: {current_price}")
    print(f"Gravity Magnitude: {gravity.magnitude:,.0f}")
    print(f"Direction: {gravity.bias}")
    print(f"Strength: {gravity.strength.name}")
    
    if gravity.dominant_pool:
        print(f"\nDominant Pool:")
        print(f"  Type: {gravity.dominant_pool.liquidity_type.value}")
        print(f"  Price: {gravity.dominant_pool.price_level}")
        print(f"  Mass: {gravity.dominant_pool.mass:,.0f}")
    
    # Predict path
    print("\n" + "=" * 60)
    print("PATH PREDICTION")
    print("=" * 60)
    
    prediction = model.predict_path(current_price, volatility=0.0010, lookforward_minutes=60)
    
    print(f"\nTarget Price: {prediction.target_price:.5f}")
    print(f"Probability: {prediction.probability:.1%}")
    print(f"Time Estimate: {prediction.time_estimate_minutes} minutes")
    print(f"Path Resistance: {prediction.path_resistance:.1%}")
    
    if prediction.intermediate_levels:
        print(f"Intermediate Levels: {[f'{l:.5f}' for l in prediction.intermediate_levels]}")
    
    print(f"\nAnalysis: {prediction.analysis}")
    
    # Strongest pools
    print("\n" + "=" * 60)
    print("STRONGEST LIQUIDITY POOLS")
    print("=" * 60)
    
    for pool in model.get_strongest_pools(5):
        print(f"\n{pool.liquidity_type.value} @ {pool.price_level:.5f}")
        print(f"  Volume: {pool.volume:,.0f}")
        print(f"  Mass: {pool.mass:,.0f}")
        print(f"  Density: {pool.density:.1f}")
