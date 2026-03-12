"""Liquidity Holography Module - Revolutionary 3D Liquidity Modeling.

This module implements the Liquidity Gravity Well model that visualizes price attraction
to liquidity pools based on their relative "mass" (volume) and "density" (order cluster
tightness), predicting the path of least resistance with unprecedented accuracy.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from collections import deque
import logging
from scipy.spatial.distance import cdist
from scipy.interpolate import griddata
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from dataclasses import field
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class LiquidityNode:
    """Represents a single liquidity node in 3D space."""
    price: float
    volume: float
    density: float
    timestamp: pd.Timestamp
    mass: float = 0.0
    gravity_strength: float = 0.0
    decay_factor: float = 1.0


@dataclass
class LiquidityGravityField:
    """Represents the gravitational field around liquidity nodes."""
    nodes: List[LiquidityNode]
    field_strength: np.ndarray
    price_grid: np.ndarray
    time_grid: np.ndarray
    attraction_vectors: np.ndarray


class LiquidityGravityWell:
    """
    Models liquidity as gravitational wells in 3D space.
    
    This revolutionary approach treats liquidity pools as massive objects that
    create gravitational fields, attracting price movement based on their
    relative mass and density.
    """
    
    def __init__(self, 
                 decay_half_life: float = 3600,  # 1 hour in seconds
                 min_volume_threshold: float = 1000,
                 density_calculation_window: int = 20,
                 gravity_constant: float = 1.0):
        """
        Initialize the Liquidity Gravity Well model.
        
        Args:
            decay_half_life: Time in seconds for liquidity mass to decay by half
            min_volume_threshold: Minimum volume to consider for liquidity node
            density_calculation_window: Window size for density calculations
            gravity_constant: Scaling factor for gravitational force calculations
        """
        self.decay_half_life = decay_half_life
        self.min_volume_threshold = min_volume_threshold
        self.density_window = density_calculation_window
        self.gravity_constant = gravity_constant
        self.liquidity_nodes: List[LiquidityNode] = []
        self.gravity_field: Optional[LiquidityGravityField] = None
        
    def calculate_liquidity_mass(self, volume: float, density: float, age_seconds: float) -> float:
        """
        Calculate the effective mass of a liquidity node.
        
        Mass = Volume * Density * Decay_Factor
        Where Decay_Factor = 0.5^(age / half_life)
        """
        decay_factor = 0.5 ** (age_seconds / self.decay_half_life)
        return volume * density * decay_factor
    
    def calculate_order_density(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """
        Calculate order cluster density using DBSCAN clustering.
        
        Higher density indicates tighter clustering of orders around a price level.
        """
        if len(prices) < 2:
            return 1.0
            
        # Normalize prices for clustering
        price_points = prices.reshape(-1, 1)
        
        # Use DBSCAN to find clusters
        clustering = DBSCAN(eps=0.001, min_samples=2).fit(price_points)
        
        # Calculate density as inverse of cluster spread
        if len(set(clustering.labels_)) > 1:
            cluster_spread = np.std(prices)
            density = 1.0 / (cluster_spread + 1e-8)  # Avoid division by zero
        else:
            density = np.sum(volumes) / (np.std(prices) + 1e-8)
            
        return max(density, 1.0)  # Minimum density of 1.0
    
    def add_liquidity_observation(self, 
                                price: float, 
                                volume: float, 
                                timestamp: pd.Timestamp,
                                surrounding_prices: np.ndarray,
                                surrounding_volumes: np.ndarray):
        """
        Add a new liquidity observation to the model.
        
        Args:
            price: Price level of the liquidity
            volume: Volume at this price level
            timestamp: Time of observation
            surrounding_prices: Array of nearby prices for density calculation
            surrounding_volumes: Array of volumes at nearby prices
        """
        if volume < self.min_volume_threshold:
            return
            
        # Calculate order density
        density = self.calculate_order_density(surrounding_prices, surrounding_volumes)
        
        # Create liquidity node
        node = LiquidityNode(
            price=price,
            volume=volume,
            density=density,
            timestamp=timestamp
        )
        
        # Calculate initial mass (age = 0)
        node.mass = self.calculate_liquidity_mass(volume, density, 0.0)
        node.gravity_strength = node.mass * self.gravity_constant
        
        self.liquidity_nodes.append(node)
        logger.debug(f"Added liquidity node: Price={price}, Volume={volume}, Density={density:.2f}, Mass={node.mass:.2f}")
    
    def update_node_masses(self, current_time: pd.Timestamp):
        """Update the masses of all liquidity nodes based on time decay."""
        for node in self.liquidity_nodes:
            age_seconds = (current_time - node.timestamp).total_seconds()
            node.decay_factor = 0.5 ** (age_seconds / self.decay_half_life)
            node.mass = node.volume * node.density * node.decay_factor
            node.gravity_strength = node.mass * self.gravity_constant
    
    def calculate_gravitational_force(self, 
                                    current_price: float, 
                                    target_node: LiquidityNode) -> float:
        """
        Calculate gravitational force between current price and a liquidity node.
        
        Force = G * Mass / Distance^2
        """
        distance = abs(current_price - target_node.price)
        if distance < 1e-8:  # Avoid division by zero
            return float('inf')
            
        force = self.gravity_constant * target_node.mass / (distance ** 2)
        return force
    
    def find_path_of_least_resistance(self, 
                                    current_price: float, 
                                    current_time: pd.Timestamp,
                                    prediction_steps: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict the path of least resistance based on liquidity gravity wells.
        
        Returns:
            Tuple of (predicted_prices, force_magnitudes)
        """
        # Update all node masses
        self.update_node_masses(current_time)
        
        # Filter out nodes with negligible mass
        active_nodes = [node for node in self.liquidity_nodes if node.mass > 0.01]
        
        if not active_nodes:
            return np.array([current_price]), np.array([0.0])
        
        predicted_prices = [current_price]
        force_magnitudes = []
        
        price = current_price
        
        for step in range(prediction_steps):
            # Calculate net gravitational force
            net_force = 0.0
            total_attraction = 0.0
            
            for node in active_nodes:
                force = self.calculate_gravitational_force(price, node)
                direction = 1 if node.price > price else -1
                net_force += force * direction
                total_attraction += force
            
            force_magnitudes.append(total_attraction)
            
            # Move price based on net force (simplified physics)
            if total_attraction > 0:
                price_movement = net_force / total_attraction * 0.1  # Damping factor
                price += price_movement
            
            predicted_prices.append(price)
        
        return np.array(predicted_prices), np.array(force_magnitudes)
    
    def generate_3d_liquidity_field(self, 
                                  price_range: Tuple[float, float],
                                  time_range: Tuple[pd.Timestamp, pd.Timestamp],
                                  grid_resolution: int = 50) -> LiquidityGravityField:
        """
        Generate a 3D gravitational field representation of liquidity.
        
        Returns:
            LiquidityGravityField object containing the 3D field data
        """
        # Create price and time grids
        price_min, price_max = price_range
        time_min, time_max = time_range
        
        prices = np.linspace(price_min, price_max, grid_resolution)
        times = pd.date_range(time_min, time_max, periods=grid_resolution)
        
        price_grid, time_grid = np.meshgrid(prices, [t.timestamp() for t in times])
        field_strength = np.zeros_like(price_grid)
        attraction_vectors = np.zeros((*price_grid.shape, 2))  # Price and time components
        
        # Calculate field strength at each grid point
        for i, time in enumerate(times):
            self.update_node_masses(time)
            
            for j, price in enumerate(prices):
                total_force = 0.0
                net_price_force = 0.0
                
                for node in self.liquidity_nodes:
                    if node.mass > 0.01:  # Only consider significant nodes
                        force = self.calculate_gravitational_force(price, node)
                        total_force += force
                        
                        # Calculate directional component
                        price_direction = 1 if node.price > price else -1
                        net_price_force += force * price_direction
                
                field_strength[i, j] = total_force
                attraction_vectors[i, j, 0] = net_price_force  # Price direction
                attraction_vectors[i, j, 1] = 0.0  # Time direction (simplified)
        
        self.gravity_field = LiquidityGravityField(
            nodes=self.liquidity_nodes.copy(),
            field_strength=field_strength,
            price_grid=price_grid,
            time_grid=time_grid,
            attraction_vectors=attraction_vectors
        )
        
        return self.gravity_field
    
    def visualize_liquidity_hologram(self, 
                                   field: LiquidityGravityField,
                                   save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a 3D visualization of the liquidity hologram.
        """
        fig = plt.figure(figsize=(15, 10))
        
        # 3D surface plot
        ax1 = fig.add_subplot(221, projection='3d')
        surf = ax1.plot_surface(field.price_grid, field.time_grid, field.field_strength,
                               cmap='viridis', alpha=0.7)
        ax1.set_xlabel('Price')
        ax1.set_ylabel('Time')
        ax1.set_zlabel('Liquidity Gravity Strength')
        ax1.set_title('3D Liquidity Gravity Field')
        
        # Contour plot
        ax2 = fig.add_subplot(222)
        contour = ax2.contour(field.price_grid, field.time_grid, field.field_strength, levels=20)
        ax2.clabel(contour, inline=True, fontsize=8)
        ax2.set_xlabel('Price')
        ax2.set_ylabel('Time')
        ax2.set_title('Liquidity Gravity Contours')
        
        # Vector field showing attraction directions
        ax3 = fig.add_subplot(223)
        skip = 5  # Skip vectors for clarity
        ax3.quiver(field.price_grid[:skip, :skip], 
                  field.time_grid[:skip, :skip],
                  field.attraction_vectors[:skip, :skip, 0],
                  field.attraction_vectors[:skip, :skip, 1],
                  scale=1000)
        ax3.set_xlabel('Price')
        ax3.set_ylabel('Time')
        ax3.set_title('Liquidity Attraction Vectors')
        
        # Liquidity nodes scatter plot
        ax4 = fig.add_subplot(224)
        if field.nodes:
            node_prices = [node.price for node in field.nodes]
            node_times = [node.timestamp.timestamp() for node in field.nodes]
            node_masses = [node.mass for node in field.nodes]
            
            scatter = ax4.scatter(node_prices, node_times, s=node_masses, 
                                c=node_masses, cmap='plasma', alpha=0.6)
            plt.colorbar(scatter, ax=ax4, label='Liquidity Mass')
        
        ax4.set_xlabel('Price')
        ax4.set_ylabel('Time')
        ax4.set_title('Liquidity Nodes (Size = Mass)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig


class LiquidityHolographyEngine:
    """
    Main engine for processing and analyzing liquidity holography data.
    
    This engine coordinates multiple LiquidityGravityWell instances across
    different timeframes and instruments to provide comprehensive liquidity analysis.
    """
    
    def __init__(self, 
                 timeframes: List[str] = None,
                 max_nodes_per_timeframe: int = 1000):
        """
        Initialize the Liquidity Holography Engine.
        
        Args:
            timeframes: List of timeframes to analyze
            max_nodes_per_timeframe: Maximum liquidity nodes per timeframe
        """
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '1h']
        self.timeframes = timeframes
        self.max_nodes = max_nodes_per_timeframe
        self.gravity_wells: Dict[str, LiquidityGravityWell] = {}
        
        # Initialize gravity wells for each timeframe
        for tf in self.timeframes:
            decay_time = self._get_decay_time_for_timeframe(tf)
            self.gravity_wells[tf] = LiquidityGravityWell(decay_half_life=decay_time)
    
    def _get_decay_time_for_timeframe(self, timeframe: str) -> float:
        """Get appropriate decay time based on timeframe."""
        decay_times = {
            '1m': 300,    # 5 minutes
            '5m': 1800,   # 30 minutes
            '15m': 3600,  # 1 hour
            '1h': 14400,  # 4 hours
            '4h': 86400,  # 1 day
            '1d': 604800  # 1 week
        }
        return decay_times.get(timeframe, 3600)
    
    def process_market_data(self, 
                          data: pd.DataFrame, 
                          timeframe: str,
                          volume_column: str = 'volume',
                          price_column: str = 'close') -> None:
        """
        Process market data to extract liquidity observations.
        
        Args:
            data: DataFrame with OHLCV data
            timeframe: Timeframe identifier
            volume_column: Name of volume column
            price_column: Name of price column
        """
        if timeframe not in self.gravity_wells:
            logger.warning(f"Timeframe {timeframe} not initialized")
            return
        
        gravity_well = self.gravity_wells[timeframe]
        
        # Process each data point
        for idx in range(len(data)):
            row = data.iloc[idx]
            
            # Get surrounding data for density calculation
            start_idx = max(0, idx - 10)
            end_idx = min(len(data), idx + 11)
            
            surrounding_data = data.iloc[start_idx:end_idx]
            surrounding_prices = surrounding_data[price_column].values
            surrounding_volumes = surrounding_data[volume_column].values
            
            # Add liquidity observation
            gravity_well.add_liquidity_observation(
                price=row[price_column],
                volume=row[volume_column],
                timestamp=row.name if isinstance(row.name, pd.Timestamp) else pd.Timestamp.now(),
                surrounding_prices=surrounding_prices,
                surrounding_volumes=surrounding_volumes
            )
        
        # Limit number of nodes to prevent memory issues
        if len(gravity_well.liquidity_nodes) > self.max_nodes:
            # Keep only the most recent nodes
            gravity_well.liquidity_nodes = gravity_well.liquidity_nodes[-self.max_nodes:]
    
    def get_multi_timeframe_prediction(self, 
                                     current_price: float,
                                     current_time: pd.Timestamp) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Get path predictions from all timeframes.
        
        Returns:
            Dictionary mapping timeframe to (predicted_prices, force_magnitudes)
        """
        predictions = {}
        
        for tf, gravity_well in self.gravity_wells.items():
            try:
                pred_prices, forces = gravity_well.find_path_of_least_resistance(
                    current_price, current_time
                )
                predictions[tf] = (pred_prices, forces)
            except Exception as e:
                logger.error(f"Error predicting for timeframe {tf}: {e}")
                predictions[tf] = (np.array([current_price]), np.array([0.0]))
        
        return predictions
    
    def get_consensus_prediction(self, 
                               current_price: float,
                               current_time: pd.Timestamp,
                               weight_by_timeframe: bool = True) -> Tuple[np.ndarray, float]:
        """
        Get consensus prediction weighted across all timeframes.
        
        Returns:
            Tuple of (consensus_path, confidence_score)
        """
        predictions = self.get_multi_timeframe_prediction(current_price, current_time)
        
        if not predictions:
            return np.array([current_price]), 0.0
        
        # Weight predictions by timeframe importance
        weights = {'1m': 0.1, '5m': 0.2, '15m': 0.3, '1h': 0.4} if weight_by_timeframe else {}
        
        weighted_predictions = []
        total_weight = 0.0
        
        for tf, (pred_prices, forces) in predictions.items():
            weight = weights.get(tf, 1.0)
            weighted_predictions.append(pred_prices * weight)
            total_weight += weight
        
        if total_weight > 0:
            consensus_path = np.sum(weighted_predictions, axis=0) / total_weight
        else:
            consensus_path = np.mean([pred[0] for pred in predictions.values()], axis=0)
        
        # Calculate confidence based on agreement between timeframes
        path_variations = [pred[0] for pred in predictions.values()]
        if len(path_variations) > 1:
            std_dev = np.std(path_variations, axis=0)
            confidence = 1.0 / (1.0 + np.mean(std_dev))
        else:
            confidence = 0.5
        
        return consensus_path, confidence


class LiquidityDensityMapper:
    """
    Maps liquidity density across price levels using advanced clustering techniques.
    """
    
    def __init__(self, 
                 clustering_eps: float = 0.001,
                 min_samples: int = 3,
                 density_smoothing: float = 0.1):
        """
        Initialize the Liquidity Density Mapper.
        
        Args:
            clustering_eps: DBSCAN epsilon parameter for clustering
            min_samples: Minimum samples for DBSCAN clustering
            density_smoothing: Smoothing factor for density calculations
        """
        self.clustering_eps = clustering_eps
        self.min_samples = min_samples
        self.smoothing = density_smoothing
    
    def calculate_density_map(self, 
                            prices: np.ndarray, 
                            volumes: np.ndarray,
                            timestamps: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate comprehensive density map of liquidity.
        
        Returns:
            Dictionary containing density metrics
        """
        # Prepare data for clustering
        data_points = np.column_stack([prices, volumes, timestamps])
        
        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=self.clustering_eps, min_samples=self.min_samples)
        cluster_labels = clustering.fit_predict(data_points)
        
        # Calculate density metrics
        density_map = {
            'cluster_labels': cluster_labels,
            'cluster_centers': [],
            'cluster_densities': [],
            'price_density': np.zeros_like(prices),
            'volume_density': np.zeros_like(volumes)
        }
        
        # Process each cluster
        unique_labels = set(cluster_labels)
        for label in unique_labels:
            if label == -1:  # Noise points
                continue
                
            cluster_mask = cluster_labels == label
            cluster_prices = prices[cluster_mask]
            cluster_volumes = volumes[cluster_mask]
            
            # Calculate cluster center
            center_price = np.mean(cluster_prices)
            center_volume = np.mean(cluster_volumes)
            density_map['cluster_centers'].append((center_price, center_volume))
            
            # Calculate cluster density
            price_spread = np.std(cluster_prices)
            volume_concentration = np.sum(cluster_volumes) / len(cluster_volumes)
            cluster_density = volume_concentration / (price_spread + self.smoothing)
            density_map['cluster_densities'].append(cluster_density)
            
            # Update density arrays
            for i in np.where(cluster_mask)[0]:
                density_map['price_density'][i] = cluster_density
                density_map['volume_density'][i] = volume_concentration
        
        return density_map


class TemporalLiquidityAnalyzer:
    """
    Analyzes how liquidity evolves over time with decay functions.
    
    Implements time-powered liquidity where older liquidity pools have
    reduced influence based on market volatility and volume patterns.
    """
    
    def __init__(self, 
                 base_decay_rate: float = 0.1,
                 volatility_acceleration: float = 2.0,
                 volume_preservation: float = 0.5):
        """
        Initialize the Temporal Liquidity Analyzer.
        
        Args:
            base_decay_rate: Base rate of liquidity decay per hour
            volatility_acceleration: How much volatility accelerates decay
            volume_preservation: How much volume preserves liquidity
        """
        self.base_decay_rate = base_decay_rate
        self.volatility_acceleration = volatility_acceleration
        self.volume_preservation = volume_preservation
        self.liquidity_history: deque = deque(maxlen=10000)
    
    def calculate_temporal_weight(self, 
                                age_hours: float,
                                current_volatility: float,
                                original_volume: float,
                                current_volume: float) -> float:
        """
        Calculate temporal weight for liquidity based on age and market conditions.
        
        Weight = exp(-decay_rate * age * volatility_factor * volume_factor)
        """
        # Volatility factor: higher volatility increases decay
        volatility_factor = 1.0 + (current_volatility * self.volatility_acceleration)
        
        # Volume factor: higher current volume preserves old liquidity
        volume_ratio = current_volume / (original_volume + 1e-8)
        volume_factor = 1.0 / (1.0 + volume_ratio * self.volume_preservation)
        
        # Calculate effective decay rate
        effective_decay = self.base_decay_rate * volatility_factor * volume_factor
        
        # Calculate weight using exponential decay
        weight = np.exp(-effective_decay * age_hours)
        
        return max(weight, 0.01)  # Minimum weight of 1%
    
    def update_liquidity_weights(self, 
                               liquidity_nodes: List[LiquidityNode],
                               current_time: pd.Timestamp,
                               current_volatility: float,
                               current_volume: float) -> List[LiquidityNode]:
        """
        Update temporal weights for all liquidity nodes.
        """
        updated_nodes = []
        
        for node in liquidity_nodes:
            age_hours = (current_time - node.timestamp).total_seconds() / 3600.0
            
            temporal_weight = self.calculate_temporal_weight(
                age_hours=age_hours,
                current_volatility=current_volatility,
                original_volume=node.volume,
                current_volume=current_volume
            )
            
            # Update node with temporal weight
            updated_node = LiquidityNode(
                price=node.price,
                volume=node.volume,
                density=node.density,
                timestamp=node.timestamp,
                mass=node.mass * temporal_weight,
                gravity_strength=node.gravity_strength * temporal_weight,
                decay_factor=temporal_weight
            )
            
            updated_nodes.append(updated_node)
        
        return updated_nodes
    
    def analyze_liquidity_evolution(self, 
                                  historical_data: pd.DataFrame,
                                  price_column: str = 'close',
                                  volume_column: str = 'volume') -> Dict[str, np.ndarray]:
        """
        Analyze how liquidity has evolved over the historical period.
        
        Returns:
            Dictionary containing evolution metrics
        """
        evolution_metrics = {
            'timestamps': [],
            'liquidity_persistence': [],
            'decay_rates': [],
            'volume_preservation_scores': []
        }
        
        # Calculate rolling volatility
        returns = historical_data[price_column].pct_change()
        volatility = returns.rolling(window=20).std()
        
        # Analyze each time point
        for i in range(20, len(historical_data)):
            current_time = historical_data.index[i]
            current_vol = volatility.iloc[i]
            current_volume = historical_data[volume_column].iloc[i]
            
            # Look back at previous liquidity
            lookback_period = min(i, 100)
            historical_volumes = historical_data[volume_column].iloc[i-lookback_period:i]
            
            # Calculate persistence metrics
            persistence_scores = []
            for j, hist_volume in enumerate(historical_volumes):
                age_hours = (lookback_period - j) / 24.0  # Assuming hourly data
                weight = self.calculate_temporal_weight(
                    age_hours, current_vol, hist_volume, current_volume
                )
                persistence_scores.append(weight)
            
            # Store metrics
            evolution_metrics['timestamps'].append(current_time)
            evolution_metrics['liquidity_persistence'].append(np.mean(persistence_scores))
            evolution_metrics['decay_rates'].append(current_vol * self.volatility_acceleration)
            evolution_metrics['volume_preservation_scores'].append(
                np.mean([cv/hv for hv, cv in zip(historical_volumes, [current_volume]*len(historical_volumes))])
            )
        
        return evolution_metrics
