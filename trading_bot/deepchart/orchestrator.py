"""
DeepChart Orchestrator - Main System Coordinator

Integrates all DeepChart components:
- Feature Pipeline
- Lightweight Models
- Inference Engine
- Visualization Layer
- Self-Improvement Loop

Provides unified API for:
- Real-time data processing
- ML inference
- Visualization generation
- Model management
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
import threading
import time
import logging
import json
import os

logger = logging.getLogger(__name__)

from .feature_pipeline import DeepChartFeatureEngine, FeatureConfig
from .lightweight_models import DeepChartModel, ModelConfig, ModelOutput
from .inference_engine import InferenceEngine, InferenceConfig, InferenceResult, InferenceAPI
from .visualization_layer import DeepChartVisualizer, VisualizationConfig
from .self_improvement import SelfImprovementLoop, TrainingConfig, DriftMetrics


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class OrchestratorConfig:
    """Configuration for DeepChart orchestrator."""
    # Component configs
    feature_config: Optional[FeatureConfig] = None
    model_config: Optional[ModelConfig] = None
    inference_config: Optional[InferenceConfig] = None
    visualization_config: Optional[VisualizationConfig] = None
    training_config: Optional[TrainingConfig] = None
    
    # Orchestrator settings
    enable_visualization: bool = True
    enable_self_improvement: bool = True
    enable_api: bool = True
    
    # Data collection
    collect_training_data: bool = True
    training_data_dir: str = "data/deepchart"
    max_training_samples_per_file: int = 10000
    
    # Performance
    max_symbols: int = 50
    update_interval_ms: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_predictions: bool = False


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class DeepChartOrchestrator:
    """
    Main orchestrator for DeepChart system.
    
    Coordinates all components and provides unified interface.
    
    Usage:
        orchestrator = DeepChartOrchestrator()
        orchestrator.add_symbol("BTCUSDT")
        
        # Update with market data
        result = orchestrator.update(
            symbol="BTCUSDT",
            price=50000.0,
            volume=100.0,
            bid=49995.0,
            ask=50005.0,
        )
        
        # Get visualization
        viz_data = orchestrator.get_visualization("BTCUSDT")
        
        # Get API response
        api_response = orchestrator.api.get_prediction("BTCUSDT")
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        
        # Initialize components
        self._init_components()
        
        # Symbol management
        self._symbols: Dict[str, Dict[str, Any]] = {}
        
        # Training data collection
        self._training_buffer: List[Dict[str, Any]] = []
        self._training_file_counter = 0
        
        # Callbacks
        self._on_prediction: List[Callable[[str, InferenceResult], None]] = []
        self._on_signal: List[Callable[[str, Dict[str, float]], None]] = []
        
        # State
        self._running = False
        self._lock = threading.RLock()
        
        logger.info("DeepChartOrchestrator initialized")
    
    def _init_components(self):
        """Initialize all components."""
        # Inference engine (includes feature pipeline and models)
        inference_config = self.config.inference_config or InferenceConfig()
        inference_config.feature_config = self.config.feature_config
        inference_config.model_config = self.config.model_config
        self.inference_engine = InferenceEngine(inference_config)
        
        # Visualization layer
        if self.config.enable_visualization:
            vis_config = self.config.visualization_config or VisualizationConfig()
            self._visualizers: Dict[str, DeepChartVisualizer] = {}
        
        # Self-improvement loop
        if self.config.enable_self_improvement:
            training_config = self.config.training_config or TrainingConfig()
            training_config.data_dir = self.config.training_data_dir
            self.improvement_loop = SelfImprovementLoop(training_config)
            
            # Set callbacks
            self.improvement_loop.set_callbacks(
                on_model_updated=self._on_model_updated,
                on_rollback=self._on_model_rollback,
            )
        else:
            self.improvement_loop = None
        
        # API interface
        if self.config.enable_api:
            self.api = InferenceAPI(self.inference_engine)
        else:
            self.api = None
        
        # Ensure data directory exists
        if self.config.collect_training_data:
            os.makedirs(self.config.training_data_dir, exist_ok=True)
    
    def add_symbol(self, symbol: str) -> bool:
        """
        Add a symbol to track.
        
        Args:
            symbol: Symbol identifier (e.g., "BTCUSDT")
        
        Returns:
            True if added successfully
        """
        with self._lock:
            if symbol in self._symbols:
                return True
            
            if len(self._symbols) >= self.config.max_symbols:
                logger.warning(f"Max symbols reached ({self.config.max_symbols})")
                return False
            
            # Add to inference engine
            if not self.inference_engine.add_symbol(symbol):
                return False
            
            # Create visualizer
            if self.config.enable_visualization:
                vis_config = self.config.visualization_config or VisualizationConfig()
                self._visualizers[symbol] = DeepChartVisualizer(vis_config)
            
            # Initialize symbol state
            self._symbols[symbol] = {
                'update_count': 0,
                'last_update': 0.0,
                'last_price': 0.0,
                'last_result': None,
            }
            
            logger.info(f"Added symbol: {symbol}")
            return True
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol."""
        with self._lock:
            if symbol in self._symbols:
                del self._symbols[symbol]
                self.inference_engine.remove_symbol(symbol)
                
                if self.config.enable_visualization and symbol in self._visualizers:
                    del self._visualizers[symbol]
                
                logger.info(f"Removed symbol: {symbol}")
    
    def update(self,
               symbol: str,
               price: float,
               volume: float,
               bid: Optional[float] = None,
               ask: Optional[float] = None,
               timestamp: Optional[float] = None,
               l2_bids: Optional[np.ndarray] = None,
               l2_asks: Optional[np.ndarray] = None) -> Optional[InferenceResult]:
        """
        Update with new market data.
        
        Args:
            symbol: Symbol identifier
            price: Current price
            volume: Current volume
            bid: Best bid (optional)
            ask: Best ask (optional)
            timestamp: Unix timestamp (optional)
            l2_bids: Aggregated L2 bid levels (optional)
            l2_asks: Aggregated L2 ask levels (optional)
        
        Returns:
            InferenceResult if inference was run
        """
        timestamp = timestamp or time.time()
        
        with self._lock:
            # Ensure symbol exists
            if symbol not in self._symbols:
                if not self.add_symbol(symbol):
                    return None
            
            # Update inference engine
            result = self.inference_engine.update(
                symbol=symbol,
                price=price,
                volume=volume,
                bid=bid,
                ask=ask,
                timestamp=timestamp,
            )
            
            # Update symbol state
            self._symbols[symbol]['update_count'] += 1
            self._symbols[symbol]['last_update'] = timestamp
            self._symbols[symbol]['last_price'] = price
            
            if result:
                self._symbols[symbol]['last_result'] = result
                
                # Update visualization
                if self.config.enable_visualization and symbol in self._visualizers:
                    self._update_visualization(symbol, price, volume, result)
                
                # Collect training data
                if self.config.collect_training_data:
                    self._collect_training_data(symbol, result)
                
                # Update improvement loop
                if self.improvement_loop and not result.from_cache:
                    self._update_improvement_loop(result)
                
                # Trigger callbacks
                self._trigger_callbacks(symbol, result)
                
                # Log prediction
                if self.config.log_predictions:
                    self._log_prediction(symbol, result)
            
            return result
    
    def _update_visualization(self, 
                              symbol: str, 
                              price: float, 
                              volume: float,
                              result: InferenceResult):
        """Update visualization for a symbol."""
        visualizer = self._visualizers[symbol]
        visualizer.update(price, volume, result)
        
        # Update levels from inference
        # Get feature state from inference engine
        state = self.inference_engine._symbols.get(symbol)
        if state and state.feature_engine._initialized:
            features = state.feature_engine.update(
                price=price,
                volume=volume,
                timestamp=time.time(),
            )
            
            if features.get('initialized'):
                liquidity = features.get('liquidity')
                if liquidity:
                    visualizer.update_levels(
                        support_levels=liquidity.support_levels,
                        resistance_levels=liquidity.resistance_levels,
                        bid_depth=liquidity.synthetic_bid_depth,
                        ask_depth=liquidity.synthetic_ask_depth,
                    )
    
    def _collect_training_data(self, symbol: str, result: InferenceResult):
        """Collect data for training."""
        # Get feature vector
        state = self.inference_engine._symbols.get(symbol)
        if not state:
            return
        
        feature_vector = state.get_feature_vector()
        
        # Store with metadata
        self._training_buffer.append({
            'symbol': symbol,
            'timestamp': result.timestamp,
            'features': feature_vector.tolist(),
            'prediction': {
                'trend_direction': result.model_output.trend_direction,
                'trend_confidence': result.model_output.trend_confidence,
                'breakout_prob': result.model_output.breakout_probability,
            },
            'price': self._symbols[symbol]['last_price'],
        })
        
        # Save to file periodically
        if len(self._training_buffer) >= self.config.max_training_samples_per_file:
            self._save_training_data()
    
    def _save_training_data(self):
        """Save training buffer to file."""
        if not self._training_buffer:
            return
        
        # Convert to numpy arrays
        features = np.array([d['features'] for d in self._training_buffer])
        
        # Labels: next price direction (will be filled in post-processing)
        # For now, use trend_direction as proxy
        labels = np.array([d['prediction']['trend_direction'] for d in self._training_buffer])
        
        # Save
        filename = f"training_data_{self._training_file_counter:04d}.npz"
        filepath = os.path.join(self.config.training_data_dir, filename)
        
        np.savez(filepath, features=features, labels=labels)
        
        logger.info(f"Saved {len(self._training_buffer)} training samples to {filepath}")
        
        self._training_buffer.clear()
        self._training_file_counter += 1
    
    def _update_improvement_loop(self, result: InferenceResult):
        """Update improvement loop with new observation."""
        # Get feature vector
        state = self.inference_engine._symbols.get(result.symbol)
        if not state:
            return
        
        feature_vector = state.get_feature_vector()
        
        # For now, use trend confidence as prediction
        prediction = result.model_output.trend_confidence
        
        # Actual outcome will be determined later
        # For now, use a placeholder
        actual = 0.5
        direction_correct = True  # Placeholder
        
        self.improvement_loop.update(
            features=feature_vector,
            prediction=prediction,
            actual=actual,
            direction_correct=direction_correct,
        )
    
    def _trigger_callbacks(self, symbol: str, result: InferenceResult):
        """Trigger registered callbacks."""
        for callback in self._on_prediction:
            try:
                callback(symbol, result)
            except Exception as e:
                logger.error(f"Prediction callback error: {e}")
        
        for callback in self._on_signal:
            try:
                callback(symbol, result.signals)
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
    
    def _log_prediction(self, symbol: str, result: InferenceResult):
        """Log prediction details."""
        output = result.model_output
        logger.info(
            f"{symbol}: trend={output.trend_direction} ({output.trend_confidence:.2f}), "
            f"breakout={output.breakout_probability:.2f}, "
            f"regime={output.regime_id}, "
            f"latency={result.inference_latency_ms:.1f}ms"
        )
    
    def _on_model_updated(self, model_path: str):
        """Callback when model is updated."""
        logger.info(f"Model updated: {model_path}")
        # Reload model in inference engine
        # This would require implementing model hot-swap
    
    def _on_model_rollback(self, model_path: str):
        """Callback when model is rolled back."""
        logger.warning(f"Model rolled back to: {model_path}")
    
    def get_visualization(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get visualization data for a symbol.
        
        Args:
            symbol: Symbol identifier
        
        Returns:
            JSON-serializable visualization data
        """
        if not self.config.enable_visualization:
            return None
        
        with self._lock:
            if symbol not in self._visualizers:
                return None
            
            return self._visualizers[symbol].to_json()
    
    def get_webgl_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get WebGL-optimized visualization data."""
        if not self.config.enable_visualization:
            return None
        
        with self._lock:
            if symbol not in self._visualizers:
                return None
            
            return self._visualizers[symbol].to_webgl_data()
    
    def get_svg(self, symbol: str) -> Optional[str]:
        """Get SVG visualization."""
        if not self.config.enable_visualization:
            return None
        
        with self._lock:
            if symbol not in self._visualizers:
                return None
            
            return self._visualizers[symbol].to_svg_paths()
    
    def get_prediction(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest prediction for a symbol."""
        if self.api:
            return self.api.get_prediction(symbol)
        
        result = self.inference_engine.get_result(symbol)
        if not result:
            return None
        
        return {
            'symbol': symbol,
            'timestamp': result.timestamp,
            'model_output': {
                'trend_direction': result.model_output.trend_direction,
                'trend_confidence': result.model_output.trend_confidence,
                'breakout_probability': result.model_output.breakout_probability,
                'reversion_probability': result.model_output.reversion_probability,
                'regime_id': result.model_output.regime_id,
            },
            'signals': result.signals,
        }
    
    def get_all_predictions(self) -> Dict[str, Any]:
        """Get predictions for all symbols."""
        if self.api:
            return self.api.get_all_predictions()
        
        return {
            symbol: self.get_prediction(symbol)
            for symbol in self._symbols
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        status = {
            'symbols': list(self._symbols.keys()),
            'symbol_count': len(self._symbols),
            'inference_metrics': self.inference_engine.get_metrics(),
        }
        
        if self.improvement_loop:
            status['improvement'] = self.improvement_loop.get_status()
        
        return status
    
    def get_symbol_status(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific symbol."""
        with self._lock:
            if symbol not in self._symbols:
                return None
            
            state = self._symbols[symbol]
            inference_stats = self.inference_engine.get_symbol_stats(symbol)
            
            return {
                'symbol': symbol,
                'update_count': state['update_count'],
                'last_update': state['last_update'],
                'last_price': state['last_price'],
                'inference': inference_stats,
            }
    
    def register_prediction_callback(self, callback: Callable[[str, InferenceResult], None]):
        """Register callback for predictions."""
        self._on_prediction.append(callback)
    
    def register_signal_callback(self, callback: Callable[[str, Dict[str, float]], None]):
        """Register callback for trading signals."""
        self._on_signal.append(callback)
    
    def check_improvement(self) -> Dict[str, Any]:
        """
        Check if model improvement is needed.
        
        Returns:
            Improvement check result
        """
        if not self.improvement_loop:
            return {'enabled': False}
        
        return self.improvement_loop.check_and_improve()
    
    def reset_symbol(self, symbol: str):
        """Reset a symbol's state."""
        with self._lock:
            if symbol in self._symbols:
                self._symbols[symbol] = {
                    'update_count': 0,
                    'last_update': 0.0,
                    'last_price': 0.0,
                    'last_result': None,
                }
                self.inference_engine.reset_symbol(symbol)
                
                if self.config.enable_visualization and symbol in self._visualizers:
                    self._visualizers[symbol].reset()
    
    def reset_all(self):
        """Reset all state."""
        with self._lock:
            for symbol in list(self._symbols.keys()):
                self.reset_symbol(symbol)
            
            self.inference_engine.reset_all()
            
            if self.improvement_loop:
                self.improvement_loop.reset()
    
    def shutdown(self):
        """Shutdown orchestrator."""
        logger.info("Shutting down DeepChartOrchestrator")
        
        # Save any remaining training data
        if self.config.collect_training_data:
            self._save_training_data()
        
        self._running = False


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_orchestrator(config: Optional[Dict] = None) -> DeepChartOrchestrator:
    """Factory function to create orchestrator."""
    if config:
        orch_config = OrchestratorConfig(**config)
    else:
        orch_config = OrchestratorConfig()
    return DeepChartOrchestrator(orch_config)


async def quick_start(symbols: List[str], config: Optional[Dict] = None) -> DeepChartOrchestrator:
    """
    Quick start helper for async usage.
    
    Args:
        symbols: List of symbols to track
        config: Optional configuration dict
    
    Returns:
        Initialized orchestrator
    """
    orchestrator = create_orchestrator(config)
    
    for symbol in symbols:
        orchestrator.add_symbol(symbol)
    
    return orchestrator


# =============================================================================
# PERFORMANCE BUDGET
# =============================================================================

PERFORMANCE_BUDGET = """
DeepChart Performance Budget
============================

INFERENCE LATENCY (per symbol):
- Target: <5ms
- Max acceptable: 10ms
- Degraded mode: <2ms

STORAGE COST (per day, per symbol):
- Feature history: ~2MB (2000 bars × 32 features × 4 bytes)
- Training data: ~10MB (if collecting)
- Model files: ~5MB (ONNX)
- Total: <20MB/day/symbol

RAM USAGE:
- Per symbol state: ~500KB
- Model in memory: ~10MB (shared)
- Inference buffers: ~1MB
- Total for 50 symbols: <100MB

CLIENT RENDERING LOAD:
- WebGL draw calls: <100 per frame
- Texture memory: <50MB
- Frame time target: <16ms (60fps)
- Overlay computation: <5ms

BATCH PROCESSING:
- Max batch size: 8 symbols
- Batch latency: <20ms
- Throughput: >400 updates/second

MODEL CONSTRAINTS:
- Max parameters: 1M
- Max model size: 10MB
- ONNX compatible: Required
- CPU inference: Required (no GPU)

NETWORK:
- API response size: <10KB per symbol
- WebSocket message rate: <10/second
- Compression: gzip for large payloads

RETRAINING:
- Frequency: Weekly (configurable)
- Duration: <1 hour
- Data requirement: >10K samples
- Validation: Required before deploy
"""


if __name__ == "__main__":
    # Test the orchestrator
    print("Testing DeepChartOrchestrator...")
    
    orchestrator = DeepChartOrchestrator()
    
    # Add symbols
    orchestrator.add_symbol("BTCUSDT")
    orchestrator.add_symbol("ETHUSDT")
    
    # Simulate data
    np.random.seed(42)
    btc_price = 50000.0
    eth_price = 3000.0
    
    print("\nRunning simulation...")
    
    for i in range(200):
        # Random walk
        btc_price += np.random.randn() * 50
        eth_price += np.random.randn() * 5
        
        # Update
        btc_result = orchestrator.update(
            symbol="BTCUSDT",
            price=btc_price,
            volume=np.random.exponential(100),
            bid=btc_price - 5,
            ask=btc_price + 5,
        )
        
        eth_result = orchestrator.update(
            symbol="ETHUSDT",
            price=eth_price,
            volume=np.random.exponential(500),
            bid=eth_price - 0.5,
            ask=eth_price + 0.5,
        )
        
        if i % 50 == 0:
            print(f"\n--- Step {i} ---")
            
            # Get prediction
            pred = orchestrator.get_prediction("BTCUSDT")
            if pred and 'model_output' in pred:
                print(f"BTC Prediction: {pred['model_output']}")
            
            # Get visualization
            viz = orchestrator.get_visualization("BTCUSDT")
            if viz:
                print(f"Visualization overlays: {len(viz.get('overlays', []))}")
    
    # Get status
    print("\n--- Final Status ---")
    status = orchestrator.get_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Print performance budget
    print("\n" + PERFORMANCE_BUDGET)
    
    # Shutdown
    orchestrator.shutdown()
    print("\nTest complete!")
