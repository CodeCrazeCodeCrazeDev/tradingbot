"""
DeepChart Inference Engine - Real-Time ML Inference

Optimized for:
- Low latency (<5ms per symbol)
- Minimal memory footprint
- Batch processing for multiple symbols
- Caching and downsampling
- Graceful degradation

Architecture:
    Feature Pipeline → Model Inference → Output Cache → API
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import deque
import threading
import time
import logging
import json

logger = logging.getLogger(__name__)

from .feature_pipeline import DeepChartFeatureEngine, FeatureConfig
from .lightweight_models import DeepChartModel, ModelConfig, ModelOutput


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class InferenceConfig:
    """Configuration for inference engine."""
    # Timing
    inference_interval_ms: int = 100      # Min time between inferences
    max_inference_latency_ms: float = 5.0 # Max allowed latency
    
    # Batching
    batch_size: int = 8                   # Max symbols per batch
    enable_batching: bool = True
    
    # Caching
    cache_ttl_ms: int = 500               # Cache time-to-live
    max_cache_size: int = 100             # Max cached results
    
    # Downsampling
    downsample_factor: int = 1            # Skip every N updates
    adaptive_downsample: bool = True      # Auto-adjust based on load
    
    # Memory
    max_symbols: int = 50                 # Max concurrent symbols
    history_per_symbol: int = 1000        # Max history bars per symbol
    
    # Degradation
    enable_degradation: bool = True       # Enable graceful degradation
    degradation_threshold_ms: float = 10.0 # Latency threshold for degradation
    
    # Feature config
    feature_config: Optional[FeatureConfig] = None
    model_config: Optional[ModelConfig] = None


@dataclass
class InferenceResult:
    """Result from inference engine."""
    symbol: str
    model_output: ModelOutput
    
    # Timing
    timestamp: float = 0.0
    inference_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    
    # Status
    from_cache: bool = False
    degraded: bool = False
    
    # Additional signals
    signals: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    update_count: int = 0
    feature_count: int = 0


# =============================================================================
# SYMBOL STATE
# =============================================================================

class SymbolState:
    """State management for a single symbol."""
    
    def __init__(self, symbol: str, config: InferenceConfig):
        self.symbol = symbol
        self.config = config
        
        # Feature engine
        feature_config = config.feature_config or FeatureConfig()
        self.feature_engine = DeepChartFeatureEngine(feature_config)
        
        # Counters
        self.update_count = 0
        self.inference_count = 0
        self.last_inference_time = 0.0
        
        # Cache
        self._cached_result: Optional[InferenceResult] = None
        self._cache_time: float = 0.0
        
        # Downsample counter
        self._downsample_counter = 0
    
    def update(self, price: float, volume: float, 
               bid: Optional[float] = None, ask: Optional[float] = None,
               timestamp: Optional[float] = None) -> Dict[str, Any]:
        """Update with new market data."""
        self.update_count += 1
        
        # Downsample check
        self._downsample_counter += 1
        if self._downsample_counter < self.config.downsample_factor:
            return {}
        self._downsample_counter = 0
        
        # Update feature engine
        features = self.feature_engine.update(
            price=price,
            volume=volume,
            bid=bid,
            ask=ask,
            timestamp=timestamp,
        )
        
        return features
    
    def get_feature_vector(self) -> np.ndarray:
        """Get current feature vector."""
        return self.feature_engine.get_feature_vector()
    
    def get_cached_result(self) -> Optional[InferenceResult]:
        """Get cached result if valid."""
        if self._cached_result is None:
            return None
        
        # Check TTL
        age_ms = (time.time() - self._cache_time) * 1000
        if age_ms > self.config.cache_ttl_ms:
            return None
        
        return self._cached_result
    
    def set_cached_result(self, result: InferenceResult):
        """Cache inference result."""
        self._cached_result = result
        self._cache_time = time.time()
    
    def should_infer(self) -> bool:
        """Check if inference should run."""
        # Check interval
        elapsed_ms = (time.time() - self.last_inference_time) * 1000
        if elapsed_ms < self.config.inference_interval_ms:
            return False
        
        # Check if feature engine is initialized
        if not self.feature_engine._initialized:
            return False
        
        return True
    
    def reset(self):
        """Reset state."""
        self.feature_engine.reset()
        self.update_count = 0
        self.inference_count = 0
        self._cached_result = None


# =============================================================================
# INFERENCE ENGINE
# =============================================================================

class InferenceEngine:
    """
    Main inference engine for DeepChart.
    
    Manages multiple symbols with:
    - Efficient batch inference
    - Caching and downsampling
    - Graceful degradation under load
    - Thread-safe operations
    """
    
    def __init__(self, config: Optional[InferenceConfig] = None):
        self.config = config or InferenceConfig()
        
        # Model
        model_config = self.config.model_config or ModelConfig()
        self._model = DeepChartModel(model_config)
        
        # Symbol states
        self._symbols: Dict[str, SymbolState] = {}
        self._lock = threading.RLock()
        
        # Metrics
        self._metrics = {
            'total_inferences': 0,
            'cache_hits': 0,
            'degraded_inferences': 0,
            'avg_latency_ms': 0.0,
            'max_latency_ms': 0.0,
        }
        
        # Degradation state
        self._degraded = False
        self._current_downsample = 1
        
        # Callbacks
        self._callbacks: List[Callable[[InferenceResult], None]] = []
        
        logger.info(f"InferenceEngine initialized (max_symbols: {self.config.max_symbols})")
    
    def add_symbol(self, symbol: str) -> bool:
        """Add a symbol to track."""
        with self._lock:
            if symbol in self._symbols:
                return True
            
            if len(self._symbols) >= self.config.max_symbols:
                logger.warning(f"Max symbols reached ({self.config.max_symbols})")
                return False
            
            self._symbols[symbol] = SymbolState(symbol, self.config)
            logger.info(f"Added symbol: {symbol}")
            return True
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol."""
        with self._lock:
            if symbol in self._symbols:
                del self._symbols[symbol]
                logger.info(f"Removed symbol: {symbol}")
    
    def update(self, symbol: str, price: float, volume: float,
               bid: Optional[float] = None, ask: Optional[float] = None,
               timestamp: Optional[float] = None) -> Optional[InferenceResult]:
        """
        Update with new market data and optionally run inference.
        
        Args:
            symbol: Symbol identifier
            price: Current price
            volume: Current volume
            bid: Best bid (optional)
            ask: Best ask (optional)
            timestamp: Unix timestamp (optional)
        
        Returns:
            InferenceResult if inference was run, None otherwise
        """
        start_time = time.time()
        
        with self._lock:
            # Get or create symbol state
            if symbol not in self._symbols:
                if not self.add_symbol(symbol):
                    return None
            
            state = self._symbols[symbol]
            
            # Update features
            features = state.update(price, volume, bid, ask, timestamp)
            
            # Check if we should run inference
            if not state.should_infer():
                # Return cached result if available
                cached = state.get_cached_result()
                if cached:
                    cached.from_cache = True
                    self._metrics['cache_hits'] += 1
                    return cached
                return None
            
            # Run inference
            result = self._run_inference(state, start_time)
            
            # Cache result
            state.set_cached_result(result)
            
            # Update metrics
            self._update_metrics(result)
            
            # Trigger callbacks
            self._trigger_callbacks(result)
            
            return result
    
    def _run_inference(self, state: SymbolState, start_time: float) -> InferenceResult:
        """Run inference for a symbol."""
        # Get feature vector
        feature_vector = state.get_feature_vector()
        
        # Check for degradation
        degraded = self._degraded
        
        # Run model
        inference_start = time.time()
        
        if degraded:
            # Simplified inference in degraded mode
            model_output = self._degraded_inference(feature_vector)
        else:
            model_output = self._model.predict(feature_vector)
        
        inference_time = (time.time() - inference_start) * 1000
        total_time = (time.time() - start_time) * 1000
        
        # Check if we should degrade
        if self.config.enable_degradation:
            if inference_time > self.config.degradation_threshold_ms:
                self._enter_degraded_mode()
            elif self._degraded and inference_time < self.config.max_inference_latency_ms:
                self._exit_degraded_mode()
        
        # Update state
        state.last_inference_time = time.time()
        state.inference_count += 1
        
        # Build result
        result = InferenceResult(
            symbol=state.symbol,
            model_output=model_output,
            timestamp=time.time(),
            inference_latency_ms=inference_time,
            total_latency_ms=total_time,
            from_cache=False,
            degraded=degraded,
            update_count=state.update_count,
            feature_count=len(feature_vector),
        )
        
        # Add derived signals
        result.signals = self._compute_signals(model_output)
        
        return result
    
    def _degraded_inference(self, feature_vector: np.ndarray) -> ModelOutput:
        """Simplified inference for degraded mode."""
        # Use only basic statistics from feature vector
        output = ModelOutput()
        
        if len(feature_vector) >= 10:
            # Extract basic signals from features
            output.trend_confidence = float(1 / (1 + np.exp(-feature_vector[0])))
            output.trend_direction = int(np.sign(feature_vector[0]))
            output.volatility_score = float(1 / (1 + np.exp(-feature_vector[7])))
            output.volatility_regime = 0 if output.volatility_score < 0.33 else (2 if output.volatility_score > 0.66 else 1)
            output.breakout_probability = float(1 / (1 + np.exp(-feature_vector[2])))
            output.reversion_probability = float(1 / (1 + np.exp(-feature_vector[3])))
        
        output.timestamp = time.time()
        return output
    
    def _compute_signals(self, output: ModelOutput) -> Dict[str, float]:
        """Compute derived trading signals from model output."""
        signals = {}
        
        # Trend signal
        signals['trend_signal'] = output.trend_direction * output.trend_confidence
        
        # Momentum signal
        signals['momentum_signal'] = (output.breakout_probability - output.reversion_probability)
        
        # Volatility signal
        signals['volatility_signal'] = output.volatility_score
        
        # Regime signal (one-hot encoded)
        for i, prob in enumerate(output.regime_probs):
            signals[f'regime_{i}_prob'] = float(prob)
        
        # Composite signal
        # Positive when: trending + breakout likely + not reverting
        signals['composite_signal'] = (
            signals['trend_signal'] * 0.4 +
            signals['momentum_signal'] * 0.4 +
            (1 - output.model_uncertainty) * 0.2
        )
        
        # Confidence-weighted signal
        signals['confidence_weighted'] = signals['composite_signal'] * output.prediction_confidence
        
        return signals
    
    def _enter_degraded_mode(self):
        """Enter degraded mode."""
        if not self._degraded:
            self._degraded = True
            self._current_downsample = min(self._current_downsample * 2, 8)
            
            # Update all symbol configs
            for state in self._symbols.values():
                state.config.downsample_factor = self._current_downsample
            
            logger.warning(f"Entering degraded mode (downsample: {self._current_downsample})")
    
    def _exit_degraded_mode(self):
        """Exit degraded mode."""
        if self._degraded:
            self._degraded = False
            self._current_downsample = max(self._current_downsample // 2, 1)
            
            # Update all symbol configs
            for state in self._symbols.values():
                state.config.downsample_factor = self._current_downsample
            
            logger.info(f"Exiting degraded mode (downsample: {self._current_downsample})")
    
    def _update_metrics(self, result: InferenceResult):
        """Update performance metrics."""
        self._metrics['total_inferences'] += 1
        
        if result.degraded:
            self._metrics['degraded_inferences'] += 1
        
        # Update latency stats
        n = self._metrics['total_inferences']
        old_avg = self._metrics['avg_latency_ms']
        self._metrics['avg_latency_ms'] = old_avg + (result.inference_latency_ms - old_avg) / n
        self._metrics['max_latency_ms'] = max(self._metrics['max_latency_ms'], result.inference_latency_ms)
    
    def _trigger_callbacks(self, result: InferenceResult):
        """Trigger registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def register_callback(self, callback: Callable[[InferenceResult], None]):
        """Register a callback for inference results."""
        self._callbacks.append(callback)
    
    def batch_update(self, updates: List[Dict[str, Any]]) -> List[InferenceResult]:
        """
        Batch update multiple symbols.
        
        Args:
            updates: List of dicts with keys: symbol, price, volume, bid, ask, timestamp
        
        Returns:
            List of InferenceResults
        """
        results = []
        
        for update in updates:
            result = self.update(
                symbol=update['symbol'],
                price=update['price'],
                volume=update['volume'],
                bid=update.get('bid'),
                ask=update.get('ask'),
                timestamp=update.get('timestamp'),
            )
            if result:
                results.append(result)
        
        return results
    
    def get_result(self, symbol: str) -> Optional[InferenceResult]:
        """Get latest result for a symbol."""
        with self._lock:
            if symbol not in self._symbols:
                return None
            return self._symbols[symbol].get_cached_result()
    
    def get_all_results(self) -> Dict[str, InferenceResult]:
        """Get latest results for all symbols."""
        results = {}
        with self._lock:
            for symbol, state in self._symbols.items():
                cached = state.get_cached_result()
                if cached:
                    results[symbol] = cached
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = self._metrics.copy()
        metrics['active_symbols'] = len(self._symbols)
        metrics['degraded'] = self._degraded
        metrics['current_downsample'] = self._current_downsample
        metrics['cache_hit_rate'] = (
            self._metrics['cache_hits'] / max(self._metrics['total_inferences'], 1)
        )
        return metrics
    
    def get_symbol_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a symbol."""
        with self._lock:
            if symbol not in self._symbols:
                return None
            
            state = self._symbols[symbol]
            return {
                'symbol': symbol,
                'update_count': state.update_count,
                'inference_count': state.inference_count,
                'initialized': state.feature_engine._initialized,
                'last_inference': state.last_inference_time,
            }
    
    def reset_symbol(self, symbol: str):
        """Reset a symbol's state."""
        with self._lock:
            if symbol in self._symbols:
                self._symbols[symbol].reset()
    
    def reset_all(self):
        """Reset all state."""
        with self._lock:
            for state in self._symbols.values():
                state.reset()
            self._metrics = {
                'total_inferences': 0,
                'cache_hits': 0,
                'degraded_inferences': 0,
                'avg_latency_ms': 0.0,
                'max_latency_ms': 0.0,
            }
            self._degraded = False
            self._current_downsample = 1


# =============================================================================
# STREAMING INTERFACE
# =============================================================================

class StreamingInference:
    """
    Streaming interface for continuous inference.
    
    Provides async-compatible interface for real-time data streams.
    """
    
    def __init__(self, engine: InferenceEngine):
        self.engine = engine
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._queue: deque = deque(maxlen=10000)
    
    def start(self):
        """Start streaming processor."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        logger.info("Streaming inference started")
    
    def stop(self):
        """Stop streaming processor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Streaming inference stopped")
    
    def push(self, symbol: str, price: float, volume: float,
             bid: Optional[float] = None, ask: Optional[float] = None,
             timestamp: Optional[float] = None):
        """Push data to processing queue."""
        self._queue.append({
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'bid': bid,
            'ask': ask,
            'timestamp': timestamp or time.time(),
        })
    
    def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                if self._queue:
                    # Process batch
                    batch = []
                    while self._queue and len(batch) < self.engine.config.batch_size:
                        batch.append(self._queue.popleft())
                    
                    if batch:
                        self.engine.batch_update(batch)
                else:
                    time.sleep(0.001)  # 1ms sleep when idle
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    @property
    def queue_size(self) -> int:
        return len(self._queue)


# =============================================================================
# API INTERFACE
# =============================================================================

class InferenceAPI:
    """
    REST-like API interface for inference engine.
    
    Provides JSON-serializable responses for frontend integration.
    """
    
    def __init__(self, engine: InferenceEngine):
        self.engine = engine
    
    def get_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get prediction for a symbol."""
        result = self.engine.get_result(symbol)
        if not result:
            return {'error': 'No data available', 'symbol': symbol}
        
        return self._serialize_result(result)
    
    def get_all_predictions(self) -> Dict[str, Any]:
        """Get predictions for all symbols."""
        results = self.engine.get_all_results()
        return {
            symbol: self._serialize_result(result)
            for symbol, result in results.items()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        metrics = self.engine.get_metrics()
        return {
            'status': 'degraded' if metrics['degraded'] else 'healthy',
            'metrics': metrics,
            'model_info': self.engine._model.get_model_info(),
        }
    
    def _serialize_result(self, result: InferenceResult) -> Dict[str, Any]:
        """Serialize InferenceResult to JSON-compatible dict."""
        output = result.model_output
        
        return {
            'symbol': result.symbol,
            'timestamp': result.timestamp,
            'predictions': {
                'trend': {
                    'direction': output.trend_direction,
                    'confidence': round(output.trend_confidence, 4),
                },
                'volatility': {
                    'regime': output.volatility_regime,
                    'score': round(output.volatility_score, 4),
                },
                'probabilities': {
                    'breakout': round(output.breakout_probability, 4),
                    'reversion': round(output.reversion_probability, 4),
                    'liquidity_zone': round(output.liquidity_zone_prob, 4),
                },
                'regime': {
                    'id': output.regime_id,
                    'probs': [round(p, 4) for p in output.regime_probs],
                },
            },
            'signals': {k: round(v, 4) for k, v in result.signals.items()},
            'latent_state': [round(x, 4) for x in output.latent_state],
            'confidence': round(output.prediction_confidence, 4),
            'uncertainty': round(output.model_uncertainty, 4),
            'meta': {
                'inference_ms': round(result.inference_latency_ms, 2),
                'from_cache': result.from_cache,
                'degraded': result.degraded,
            },
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_inference_engine(config: Optional[Dict] = None) -> InferenceEngine:
    """Factory function to create inference engine."""
    if config:
        inference_config = InferenceConfig(**config)
    else:
        inference_config = InferenceConfig()
    return InferenceEngine(inference_config)


if __name__ == "__main__":
    # Test the inference engine
    engine = InferenceEngine()
    api = InferenceAPI(engine)
    
    # Add symbols
    engine.add_symbol("BTCUSDT")
    engine.add_symbol("ETHUSDT")
    
    # Simulate data
    np.random.seed(42)
    btc_price = 50000.0
    eth_price = 3000.0
    
    print("Running inference test...")
    
    for i in range(200):
        # Random walk
        btc_price += np.random.randn() * 50
        eth_price += np.random.randn() * 5
        
        # Update
        btc_result = engine.update(
            symbol="BTCUSDT",
            price=btc_price,
            volume=np.random.exponential(100),
            bid=btc_price - 5,
            ask=btc_price + 5,
        )
        
        eth_result = engine.update(
            symbol="ETHUSDT",
            price=eth_price,
            volume=np.random.exponential(500),
            bid=eth_price - 0.5,
            ask=eth_price + 0.5,
        )
        
        if i % 50 == 0:
            print(f"\n--- Step {i} ---")
            if btc_result:
                print(f"BTC: trend={btc_result.model_output.trend_direction}, "
                      f"breakout={btc_result.model_output.breakout_probability:.3f}, "
                      f"latency={btc_result.inference_latency_ms:.2f}ms")
            
            # Get API response
            prediction = api.get_prediction("BTCUSDT")
            if 'predictions' in prediction:
                print(f"API: {json.dumps(prediction['predictions'], indent=2)}")
    
    # Print metrics
    print("\n--- Final Metrics ---")
    print(json.dumps(api.get_status(), indent=2))
