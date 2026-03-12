"""
DeepChart Visualization Layer - Low-Cost Chart Rendering

Designed for:
- WebGL/WebGPU client-side rendering
- No expensive GPU servers required
- Incremental rendering
- Downsampled input tiles
- Lightweight overlays

Visualization Components:
1. Latent State Zones - Colored regions from ML embeddings
2. Dynamic Support/Resistance - ML-derived levels
3. Liquidity Shadows - Inferred depth visualization
4. Regime Gradient Background - Market state coloring
5. Micro-Momentum Arrows - Direction indicators
6. Compression/Expansion Bands - Volatility visualization

Output Formats:
- JSON for WebGL rendering
- SVG paths for lightweight display
- Canvas draw commands
- Pre-computed shader data
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import logging
import json
import colorsys

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class ColorScheme(Enum):
    """Color schemes for visualization."""
    DARK = "dark"
    LIGHT = "light"
    TRADING_VIEW = "trading_view"
    CUSTOM = "custom"


@dataclass
class VisualizationConfig:
    """Configuration for visualization layer."""
    # Canvas settings
    width: int = 1200                    # Default canvas width
    height: int = 600                    # Default canvas height
    padding: int = 50                    # Padding around chart
    
    # Color scheme
    color_scheme: ColorScheme = ColorScheme.DARK
    
    # Overlay settings
    show_latent_zones: bool = True
    show_support_resistance: bool = True
    show_liquidity_shadows: bool = True
    show_regime_background: bool = True
    show_momentum_arrows: bool = True
    show_compression_bands: bool = True
    
    # Rendering settings
    max_candles: int = 200               # Max candles to render
    downsample_threshold: int = 500      # Downsample if more candles
    
    # Animation
    enable_animation: bool = True
    animation_duration_ms: int = 200
    
    # Performance
    use_webgl: bool = True
    tile_size: int = 64                  # Tile size for incremental rendering
    cache_tiles: bool = True
    
    # Overlay opacity
    zone_opacity: float = 0.3
    shadow_opacity: float = 0.2
    band_opacity: float = 0.15


@dataclass
class ChartOverlay:
    """Single overlay element for chart."""
    type: str                            # Type of overlay
    data: Dict[str, Any]                 # Overlay-specific data
    z_index: int = 0                     # Rendering order
    visible: bool = True
    opacity: float = 1.0
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'type': self.type,
            'data': self.data,
            'zIndex': self.z_index,
            'visible': self.visible,
            'opacity': self.opacity,
        }


@dataclass
class LatentStateZone:
    """Latent state zone for visualization."""
    start_index: int
    end_index: int
    regime_id: int
    confidence: float
    color: str
    label: str
    
    def to_json(self) -> Dict[str, Any]:
        return {
            'startIndex': self.start_index,
            'endIndex': self.end_index,
            'regimeId': self.regime_id,
            'confidence': self.confidence,
            'color': self.color,
            'label': self.label,
        }


# =============================================================================
# COLOR UTILITIES
# =============================================================================

class ColorPalette:
    """Color palette for different schemes."""
    
    DARK = {
        'background': '#0d1117',
        'grid': '#21262d',
        'text': '#c9d1d9',
        'candle_up': '#3fb950',
        'candle_down': '#f85149',
        'volume': '#388bfd',
        
        # Regime colors
        'regime_trending': '#238636',
        'regime_ranging': '#1f6feb',
        'regime_volatile': '#f85149',
        'regime_quiet': '#6e7681',
        
        # Overlay colors
        'support': '#3fb950',
        'resistance': '#f85149',
        'liquidity_bid': '#238636',
        'liquidity_ask': '#da3633',
        'momentum_up': '#3fb950',
        'momentum_down': '#f85149',
        'compression': '#a371f7',
        'expansion': '#f0883e',
        
        # Latent state colors (gradient)
        'latent_positive': '#238636',
        'latent_neutral': '#6e7681',
        'latent_negative': '#da3633',
    }
    
    LIGHT = {
        'background': '#ffffff',
        'grid': '#d0d7de',
        'text': '#24292f',
        'candle_up': '#1a7f37',
        'candle_down': '#cf222e',
        'volume': '#0969da',
        
        'regime_trending': '#1a7f37',
        'regime_ranging': '#0969da',
        'regime_volatile': '#cf222e',
        'regime_quiet': '#6e7681',
        
        'support': '#1a7f37',
        'resistance': '#cf222e',
        'liquidity_bid': '#1a7f37',
        'liquidity_ask': '#cf222e',
        'momentum_up': '#1a7f37',
        'momentum_down': '#cf222e',
        'compression': '#8250df',
        'expansion': '#bf8700',
        
        'latent_positive': '#1a7f37',
        'latent_neutral': '#6e7681',
        'latent_negative': '#cf222e',
    }
    
    @classmethod
    def get_palette(cls, scheme: ColorScheme) -> Dict[str, str]:
        try:
            if scheme == ColorScheme.DARK:
                return cls.DARK
            elif scheme == ColorScheme.LIGHT:
                return cls.LIGHT
            else:
                return cls.DARK
        except Exception as e:
            logger.error(f"Error in get_palette: {e}")
            raise
    
    @staticmethod
    def interpolate_color(color1: str, color2: str, t: float) -> str:
        """Interpolate between two hex colors."""
        # Parse hex colors
        try:
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
            # Interpolate
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
        
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception as e:
            logger.error(f"Error in interpolate_color: {e}")
            raise
    
    @staticmethod
    def with_alpha(color: str, alpha: float) -> str:
        """Add alpha to hex color (returns rgba)."""
        try:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return f'rgba({r},{g},{b},{alpha})'
        except Exception as e:
            logger.error(f"Error in with_alpha: {e}")
            raise


# =============================================================================
# OVERLAY GENERATORS
# =============================================================================

class OverlayGenerator:
    """Generates chart overlays from inference results."""
    
    def __init__(self, config: VisualizationConfig):
        try:
            self.config = config
            self.palette = ColorPalette.get_palette(config.color_scheme)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_regime_background(self, 
                                   regime_history: List[int],
                                   confidence_history: List[float],
                                   price_range: Tuple[float, float]) -> ChartOverlay:
        """
        Generate regime gradient background.
        
        Creates colored regions based on detected market regime.
        """
        try:
            if not regime_history:
                return ChartOverlay(type='regime_background', data={})
        
            # Find regime transitions
            zones = []
            current_regime = regime_history[0]
            start_idx = 0
        
            for i, regime in enumerate(regime_history):
                if regime != current_regime:
                    zones.append({
                        'start': start_idx,
                        'end': i,
                        'regime': current_regime,
                        'confidence': np.mean(confidence_history[start_idx:i]) if confidence_history else 0.5,
                    })
                    current_regime = regime
                    start_idx = i
        
            # Add final zone
            zones.append({
                'start': start_idx,
                'end': len(regime_history),
                'regime': current_regime,
                'confidence': np.mean(confidence_history[start_idx:]) if confidence_history else 0.5,
            })
        
            # Map regimes to colors
            regime_colors = {
                0: self.palette['regime_trending'],
                1: self.palette['regime_ranging'],
                2: self.palette['regime_volatile'],
                3: self.palette['regime_quiet'],
            }
        
            # Generate gradient data
            gradient_data = []
            for zone in zones:
                color = regime_colors.get(zone['regime'], self.palette['regime_quiet'])
                gradient_data.append({
                    'x1': zone['start'],
                    'x2': zone['end'],
                    'y1': price_range[0],
                    'y2': price_range[1],
                    'color': ColorPalette.with_alpha(color, self.config.zone_opacity * zone['confidence']),
                    'regime': zone['regime'],
                })
        
            return ChartOverlay(
                type='regime_background',
                data={'zones': gradient_data},
                z_index=-10,
                opacity=self.config.zone_opacity,
            )
        except Exception as e:
            logger.error(f"Error in generate_regime_background: {e}")
            raise
    
    def generate_latent_zones(self,
                              latent_history: List[np.ndarray],
                              prices: np.ndarray) -> ChartOverlay:
        """
        Generate latent state zones.
        
        Visualizes the ML latent space as colored regions.
        """
        try:
            if not latent_history or len(latent_history) < 2:
                return ChartOverlay(type='latent_zones', data={})
        
            # Convert to array
            latent_array = np.array(latent_history)
        
            # Use first principal component for coloring
            # (simplified - just use mean of latent vector)
            latent_scores = np.mean(latent_array, axis=1)
        
            # Normalize to [0, 1]
            min_score = np.min(latent_scores)
            max_score = np.max(latent_scores)
            if max_score - min_score > 1e-8:
                normalized = (latent_scores - min_score) / (max_score - min_score)
            else:
                normalized = np.ones_like(latent_scores) * 0.5
        
            # Generate color gradient
            zones = []
            for i in range(len(normalized)):
                t = normalized[i]
                if t < 0.5:
                    color = ColorPalette.interpolate_color(
                        self.palette['latent_negative'],
                        self.palette['latent_neutral'],
                        t * 2
                    )
                else:
                    color = ColorPalette.interpolate_color(
                        self.palette['latent_neutral'],
                        self.palette['latent_positive'],
                        (t - 0.5) * 2
                    )
            
                zones.append({
                    'index': i,
                    'score': float(latent_scores[i]),
                    'normalized': float(t),
                    'color': color,
                })
        
            return ChartOverlay(
                type='latent_zones',
                data={
                    'zones': zones,
                    'colorScale': {
                        'min': self.palette['latent_negative'],
                        'mid': self.palette['latent_neutral'],
                        'max': self.palette['latent_positive'],
                    },
                },
                z_index=-5,
                opacity=self.config.zone_opacity,
            )
        except Exception as e:
            logger.error(f"Error in generate_latent_zones: {e}")
            raise
    
    def generate_support_resistance(self,
                                    support_levels: np.ndarray,
                                    resistance_levels: np.ndarray,
                                    strengths: Optional[np.ndarray] = None) -> ChartOverlay:
        """
        Generate dynamic support/resistance levels from ML embeddings.
        """
        try:
            lines = []
        
            # Support levels
            for i, level in enumerate(support_levels):
                strength = strengths[i] if strengths is not None and i < len(strengths) else 0.5
                lines.append({
                    'type': 'support',
                    'price': float(level),
                    'strength': float(strength),
                    'color': ColorPalette.with_alpha(self.palette['support'], 0.3 + 0.5 * strength),
                    'lineWidth': 1 + strength * 2,
                    'dashArray': [5, 5] if strength < 0.5 else None,
                })
        
            # Resistance levels
            for i, level in enumerate(resistance_levels):
                idx = i + len(support_levels)
                strength = strengths[idx] if strengths is not None and idx < len(strengths) else 0.5
                lines.append({
                    'type': 'resistance',
                    'price': float(level),
                    'strength': float(strength),
                    'color': ColorPalette.with_alpha(self.palette['resistance'], 0.3 + 0.5 * strength),
                    'lineWidth': 1 + strength * 2,
                    'dashArray': [5, 5] if strength < 0.5 else None,
                })
        
            return ChartOverlay(
                type='support_resistance',
                data={'lines': lines},
                z_index=5,
            )
        except Exception as e:
            logger.error(f"Error in generate_support_resistance: {e}")
            raise
    
    def generate_liquidity_shadows(self,
                                   bid_depth: np.ndarray,
                                   ask_depth: np.ndarray,
                                   current_price: float,
                                   price_range: Tuple[float, float]) -> ChartOverlay:
        """
        Generate liquidity shadow visualization.
        
        Shows inferred order book depth as shadows on the chart.
        """
        # Normalize depths
        try:
            max_depth = max(np.max(bid_depth), np.max(ask_depth), 1e-8)
            bid_normalized = bid_depth / max_depth
            ask_normalized = ask_depth / max_depth
        
            # Generate shadow data
            # Price levels (percentage from current price)
            level_offsets = np.array([0.001, 0.002, 0.005, 0.01, 0.02])[:len(bid_depth)]
        
            bid_shadows = []
            for i, (offset, depth) in enumerate(zip(level_offsets, bid_normalized)):
                price = current_price * (1 - offset)
                bid_shadows.append({
                    'price': float(price),
                    'depth': float(depth),
                    'width': float(depth * 50),  # Width in pixels
                    'color': ColorPalette.with_alpha(self.palette['liquidity_bid'], self.config.shadow_opacity * depth),
                })
        
            ask_shadows = []
            for i, (offset, depth) in enumerate(zip(level_offsets, ask_normalized)):
                price = current_price * (1 + offset)
                ask_shadows.append({
                    'price': float(price),
                    'depth': float(depth),
                    'width': float(depth * 50),
                    'color': ColorPalette.with_alpha(self.palette['liquidity_ask'], self.config.shadow_opacity * depth),
                })
        
            return ChartOverlay(
                type='liquidity_shadows',
                data={
                    'bidShadows': bid_shadows,
                    'askShadows': ask_shadows,
                    'currentPrice': current_price,
                },
                z_index=-3,
                opacity=self.config.shadow_opacity,
            )
        except Exception as e:
            logger.error(f"Error in generate_liquidity_shadows: {e}")
            raise
    
    def generate_momentum_arrows(self,
                                 momentum_history: List[float],
                                 prices: np.ndarray,
                                 threshold: float = 0.1) -> ChartOverlay:
        """
        Generate micro-momentum arrows.
        
        Shows direction and strength of short-term momentum.
        """
        try:
            if not momentum_history or len(momentum_history) < 2:
                return ChartOverlay(type='momentum_arrows', data={})
        
            arrows = []
        
            # Sample every N points to avoid clutter
            sample_rate = max(1, len(momentum_history) // 20)
        
            for i in range(0, len(momentum_history), sample_rate):
                momentum = momentum_history[i]
            
                # Skip weak momentum
                if abs(momentum) < threshold:
                    continue
            
                # Determine direction and strength
                direction = 'up' if momentum > 0 else 'down'
                strength = min(abs(momentum) / 0.5, 1.0)  # Normalize to [0, 1]
            
                price = prices[i] if i < len(prices) else prices[-1]
            
                arrows.append({
                    'index': i,
                    'price': float(price),
                    'direction': direction,
                    'strength': float(strength),
                    'color': self.palette['momentum_up'] if direction == 'up' else self.palette['momentum_down'],
                    'size': 8 + strength * 8,  # Arrow size
                })
        
            return ChartOverlay(
                type='momentum_arrows',
                data={'arrows': arrows},
                z_index=10,
            )
        except Exception as e:
            logger.error(f"Error in generate_momentum_arrows: {e}")
            raise
    
    def generate_compression_bands(self,
                                   vol_compression_history: List[float],
                                   prices: np.ndarray,
                                   atr_history: Optional[List[float]] = None) -> ChartOverlay:
        """
        Generate volatility compression/expansion bands.
        
        Shows periods of volatility compression (potential breakout) and expansion.
        """
        try:
            if not vol_compression_history:
                return ChartOverlay(type='compression_bands', data={})
        
            # Calculate bands
            compression = np.array(vol_compression_history)
        
            # Use ATR if available, otherwise estimate from prices
            if atr_history:
                atr = np.array(atr_history)
            else:
                # Simple ATR estimate
                if len(prices) > 14:
                    high_low = np.abs(np.diff(prices))
                    atr = np.zeros(len(prices))
                    atr[14:] = np.convolve(high_low, np.ones(14)/14, mode='valid')[:len(prices)-14]
                else:
                    atr = np.std(prices) * np.ones(len(prices))
        
            # Generate band data
            upper_band = []
            lower_band = []
            band_colors = []
        
            for i in range(len(compression)):
                if i >= len(prices) or i >= len(atr):
                    continue
            
                price = prices[i]
                width = atr[i] * (0.5 + compression[i])  # Wider when compressed
            
                upper_band.append(float(price + width))
                lower_band.append(float(price - width))
            
                # Color based on compression level
                if compression[i] < 0.5:
                    # Compressed - potential breakout
                    color = self.palette['compression']
                else:
                    # Expanded
                    color = self.palette['expansion']
            
                band_colors.append(ColorPalette.with_alpha(color, self.config.band_opacity))
        
            return ChartOverlay(
                type='compression_bands',
                data={
                    'upperBand': upper_band,
                    'lowerBand': lower_band,
                    'colors': band_colors,
                    'compression': [float(c) for c in compression],
                },
                z_index=-2,
                opacity=self.config.band_opacity,
            )
        except Exception as e:
            logger.error(f"Error in generate_compression_bands: {e}")
            raise


# =============================================================================
# MAIN VISUALIZER
# =============================================================================

class DeepChartVisualizer:
    """
    Main visualization class for DeepChart.
    
    Generates all chart overlays from inference results.
    Outputs JSON for client-side WebGL rendering.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        try:
            self.config = config or VisualizationConfig()
            self.overlay_generator = OverlayGenerator(self.config)
            self.palette = ColorPalette.get_palette(self.config.color_scheme)
        
            # History buffers
            self._regime_history: List[int] = []
            self._confidence_history: List[float] = []
            self._latent_history: List[np.ndarray] = []
            self._momentum_history: List[float] = []
            self._vol_compression_history: List[float] = []
        
            # Price data
            self._prices: List[float] = []
            self._volumes: List[float] = []
        
            # Current state
            self._current_support: np.ndarray = np.array([])
            self._current_resistance: np.ndarray = np.array([])
            self._current_bid_depth: np.ndarray = np.zeros(5)
            self._current_ask_depth: np.ndarray = np.zeros(5)
        
            logger.info("DeepChartVisualizer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, 
               price: float,
               volume: float,
               inference_result: Optional[Any] = None):
        """
        Update visualizer with new data.
        
        Args:
            price: Current price
            volume: Current volume
            inference_result: InferenceResult from inference engine
        """
        # Update price/volume
        try:
            self._prices.append(price)
            self._volumes.append(volume)
        
            # Trim to max candles
            max_len = self.config.max_candles * 2
            if len(self._prices) > max_len:
                self._prices = self._prices[-max_len:]
                self._volumes = self._volumes[-max_len:]
        
            # Update from inference result
            if inference_result:
                output = inference_result.model_output
            
                self._regime_history.append(output.regime_id)
                self._confidence_history.append(output.prediction_confidence)
                self._latent_history.append(output.latent_state)
                self._momentum_history.append(
                    inference_result.signals.get('momentum_signal', 0.0)
                )
                self._vol_compression_history.append(output.volatility_score)
            
                # Trim histories
                for hist in [self._regime_history, self._confidence_history, 
                            self._latent_history, self._momentum_history,
                            self._vol_compression_history]:
                    if len(hist) > max_len:
                        hist[:] = hist[-max_len:]
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def update_levels(self,
                      support_levels: np.ndarray,
                      resistance_levels: np.ndarray,
                      bid_depth: np.ndarray,
                      ask_depth: np.ndarray):
        """Update support/resistance and depth levels."""
        try:
            self._current_support = support_levels
            self._current_resistance = resistance_levels
            self._current_bid_depth = bid_depth
            self._current_ask_depth = ask_depth
        except Exception as e:
            logger.error(f"Error in update_levels: {e}")
            raise
    
    def generate_overlays(self) -> List[ChartOverlay]:
        """
        Generate all chart overlays.
        
        Returns:
            List of ChartOverlay objects
        """
        try:
            overlays = []
        
            if not self._prices:
                return overlays
        
            prices = np.array(self._prices[-self.config.max_candles:])
            price_range = (float(np.min(prices)), float(np.max(prices)))
            current_price = prices[-1]
        
            # Regime background
            if self.config.show_regime_background and self._regime_history:
                overlay = self.overlay_generator.generate_regime_background(
                    self._regime_history[-self.config.max_candles:],
                    self._confidence_history[-self.config.max_candles:],
                    price_range,
                )
                overlays.append(overlay)
        
            # Latent zones
            if self.config.show_latent_zones and self._latent_history:
                overlay = self.overlay_generator.generate_latent_zones(
                    self._latent_history[-self.config.max_candles:],
                    prices,
                )
                overlays.append(overlay)
        
            # Support/Resistance
            if self.config.show_support_resistance:
                overlay = self.overlay_generator.generate_support_resistance(
                    self._current_support,
                    self._current_resistance,
                )
                overlays.append(overlay)
        
            # Liquidity shadows
            if self.config.show_liquidity_shadows:
                overlay = self.overlay_generator.generate_liquidity_shadows(
                    self._current_bid_depth,
                    self._current_ask_depth,
                    current_price,
                    price_range,
                )
                overlays.append(overlay)
        
            # Momentum arrows
            if self.config.show_momentum_arrows and self._momentum_history:
                overlay = self.overlay_generator.generate_momentum_arrows(
                    self._momentum_history[-self.config.max_candles:],
                    prices,
                )
                overlays.append(overlay)
        
            # Compression bands
            if self.config.show_compression_bands and self._vol_compression_history:
                overlay = self.overlay_generator.generate_compression_bands(
                    self._vol_compression_history[-self.config.max_candles:],
                    prices,
                )
                overlays.append(overlay)
        
            return overlays
        except Exception as e:
            logger.error(f"Error in generate_overlays: {e}")
            raise
    
    def to_json(self) -> Dict[str, Any]:
        """
        Generate complete JSON output for frontend.
        
        Returns:
            JSON-serializable dict with all visualization data
        """
        try:
            overlays = self.generate_overlays()
        
            return {
                'config': {
                    'width': self.config.width,
                    'height': self.config.height,
                    'padding': self.config.padding,
                    'colorScheme': self.config.color_scheme.value,
                    'animation': {
                        'enabled': self.config.enable_animation,
                        'duration': self.config.animation_duration_ms,
                    },
                },
                'palette': self.palette,
                'overlays': [o.to_json() for o in overlays],
                'priceData': {
                    'prices': self._prices[-self.config.max_candles:],
                    'volumes': self._volumes[-self.config.max_candles:],
                },
                'meta': {
                    'dataPoints': len(self._prices),
                    'overlayCount': len(overlays),
                },
            }
        except Exception as e:
            logger.error(f"Error in to_json: {e}")
            raise
    
    def to_webgl_data(self) -> Dict[str, Any]:
        """
        Generate WebGL-optimized data.
        
        Returns:
            Dict with typed arrays and shader uniforms
        """
        try:
            overlays = self.generate_overlays()
        
            # Convert to typed array format
            prices = np.array(self._prices[-self.config.max_candles:], dtype=np.float32)
            volumes = np.array(self._volumes[-self.config.max_candles:], dtype=np.float32)
        
            # Regime colors as texture data
            regime_colors = np.zeros((len(self._regime_history), 4), dtype=np.float32)
            for i, regime in enumerate(self._regime_history[-self.config.max_candles:]):
                color_key = ['regime_trending', 'regime_ranging', 'regime_volatile', 'regime_quiet'][regime]
                color = self.palette[color_key]
                r, g, b = int(color[1:3], 16)/255, int(color[3:5], 16)/255, int(color[5:7], 16)/255
                confidence = self._confidence_history[i] if i < len(self._confidence_history) else 0.5
                regime_colors[i] = [r, g, b, confidence * self.config.zone_opacity]
        
            return {
                'vertices': {
                    'prices': prices.tolist(),
                    'volumes': volumes.tolist(),
                },
                'textures': {
                    'regimeColors': regime_colors.tolist(),
                },
                'uniforms': {
                    'priceRange': [float(np.min(prices)), float(np.max(prices))],
                    'volumeRange': [float(np.min(volumes)), float(np.max(volumes))],
                    'dataLength': len(prices),
                },
                'overlays': [o.to_json() for o in overlays],
            }
        except Exception as e:
            logger.error(f"Error in to_webgl_data: {e}")
            raise
    
    def to_svg_paths(self) -> str:
        """
        Generate SVG paths for lightweight rendering.
        
        Returns:
            SVG string with all overlays
        """
        try:
            if not self._prices:
                return '<svg></svg>'
        
            prices = np.array(self._prices[-self.config.max_candles:])
        
            # Normalize to SVG coordinates
            width = self.config.width - 2 * self.config.padding
            height = self.config.height - 2 * self.config.padding
        
            price_min, price_max = np.min(prices), np.max(prices)
            price_range = price_max - price_min if price_max > price_min else 1
        
            def to_x(idx):
                return self.config.padding + (idx / len(prices)) * width
        
            def to_y(price):
                return self.config.padding + (1 - (price - price_min) / price_range) * height
        
            # Build SVG
            svg_parts = [
                f'<svg width="{self.config.width}" height="{self.config.height}" xmlns="http://www.w3.org/2000/svg">',
                f'<rect width="100%" height="100%" fill="{self.palette["background"]}"/>',
            ]
        
            # Price line
            path_data = f'M {to_x(0)} {to_y(prices[0])}'
            for i, price in enumerate(prices[1:], 1):
                path_data += f' L {to_x(i)} {to_y(price)}'
        
            svg_parts.append(
                f'<path d="{path_data}" fill="none" stroke="{self.palette["candle_up"]}" stroke-width="1.5"/>'
            )
        
            # Support/Resistance lines
            for level in self._current_support:
                y = to_y(level)
                svg_parts.append(
                    f'<line x1="{self.config.padding}" y1="{y}" x2="{self.config.width - self.config.padding}" y2="{y}" '
                    f'stroke="{self.palette["support"]}" stroke-width="1" stroke-dasharray="5,5" opacity="0.7"/>'
                )
        
            for level in self._current_resistance:
                y = to_y(level)
                svg_parts.append(
                    f'<line x1="{self.config.padding}" y1="{y}" x2="{self.config.width - self.config.padding}" y2="{y}" '
                    f'stroke="{self.palette["resistance"]}" stroke-width="1" stroke-dasharray="5,5" opacity="0.7"/>'
                )
        
            svg_parts.append('</svg>')
        
            return '\n'.join(svg_parts)
        except Exception as e:
            logger.error(f"Error in to_svg_paths: {e}")
            raise
    
    def reset(self):
        """Reset all state."""
        try:
            self._regime_history.clear()
            self._confidence_history.clear()
            self._latent_history.clear()
            self._momentum_history.clear()
            self._vol_compression_history.clear()
            self._prices.clear()
            self._volumes.clear()
            self._current_support = np.array([])
            self._current_resistance = np.array([])
            self._current_bid_depth = np.zeros(5)
            self._current_ask_depth = np.zeros(5)
        except Exception as e:
            logger.error(f"Error in reset: {e}")
            raise


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_visualizer(config: Optional[Dict] = None) -> DeepChartVisualizer:
    """Factory function to create visualizer."""
    try:
        if config:
            vis_config = VisualizationConfig(**config)
        else:
            vis_config = VisualizationConfig()
        return DeepChartVisualizer(vis_config)
    except Exception as e:
        logger.error(f"Error in create_visualizer: {e}")
        raise


if __name__ == "__main__":
    # Test the visualizer
    from .inference_engine import InferenceResult
    from .lightweight_models import ModelOutput
    
    visualizer = DeepChartVisualizer()
    
    # Simulate data
    np.random.seed(42)
    price = 100.0
    
    for i in range(200):
        price += np.random.randn() * 0.5
        volume = np.random.exponential(1000)
        
        # Create mock inference result
        mock_output = ModelOutput(
            trend_confidence=0.5 + np.random.randn() * 0.2,
            trend_direction=int(np.sign(np.random.randn())),
            volatility_regime=np.random.randint(0, 3),
            volatility_score=np.random.random(),
            breakout_probability=np.random.random(),
            reversion_probability=np.random.random(),
            regime_probs=np.random.dirichlet([1, 1, 1, 1]),
            regime_id=np.random.randint(0, 4),
            latent_state=np.random.randn(8),
            prediction_confidence=0.5 + np.random.random() * 0.5,
        )
        
        mock_result = InferenceResult(
            symbol="TEST",
            model_output=mock_output,
            signals={'momentum_signal': np.random.randn() * 0.2},
        )
        
        visualizer.update(price, volume, mock_result)
    
    # Update levels
    visualizer.update_levels(
        support_levels=np.array([95.0, 90.0]),
        resistance_levels=np.array([105.0, 110.0]),
        bid_depth=np.random.random(5),
        ask_depth=np.random.random(5),
    )
    
    # Generate outputs
    json_output = visualizer.to_json()
    print(f"JSON output keys: {json_output.keys()}")
    print(f"Overlay count: {len(json_output['overlays'])}")
    
    webgl_data = visualizer.to_webgl_data()
    print(f"WebGL data keys: {webgl_data.keys()}")
    
    svg = visualizer.to_svg_paths()
    print(f"SVG length: {len(svg)} chars")
