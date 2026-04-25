"""
GETS Real-Time Inference Pipeline

High-performance streaming pipeline for production inference:
- Low-latency signal generation (<10ms target)
- Async data ingestion
- Batch processing for efficiency
- Model hot-swapping
- Circuit breaker pattern for fault tolerance
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Coroutine
from datetime import datetime
from dataclasses import dataclass
from collections import deque
import threading
import numpy as np

from .types import MarketData, GETSSignal, ForecastHorizon
from .gets_system import GETS

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Real-time pipeline performance metrics."""
    timestamp: datetime
    
    # Latency metrics (microseconds)
    p50_latency_us: float
    p95_latency_us: float
    p99_latency_us: float
    max_latency_us: float
    
    # Throughput
    signals_per_second: float
    predictions_per_second: float
    
    # Quality
    signals_generated: int
    signals_abstained: int
    abstention_rate: float
    
    # Health
    queue_depth: int
    model_health: Dict[str, bool]
    circuit_breaker_states: Dict[str, str]


class CircuitBreaker:
    """Circuit breaker pattern for fault-tolerant model inference."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        with self._lock:
            if self.state == "CLOSED":
                return True
            elif self.state == "OPEN":
                if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker {self.name}: OPEN -> HALF_OPEN")
                    return True
                return False
            elif self.state == "HALF_OPEN":
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False
            return False
    
    def record_success(self):
        with self._lock:
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                self.half_open_calls = 0
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN -> CLOSED")
            elif self.state == "CLOSED":
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == "HALF_OPEN":
                self.state = "OPEN"
                logger.warning(f"Circuit breaker {self.name}: HALF_OPEN -> OPEN")
            elif self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker {self.name}: CLOSED -> OPEN")


class StreamingBuffer:
    """Thread-safe ring buffer for streaming market data."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._buffer: deque = deque(maxlen=max_size)
        self._callbacks: List[Callable[[MarketData], None]] = []
        self._lock = threading.RLock()
    
    def append(self, data: MarketData):
        with self._lock:
            self._buffer.append(data)
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def get_recent(self, n: int) -> List[MarketData]:
        with self._lock:
            return list(self._buffer)[-n:]
    
    def register_callback(self, callback: Callable[[MarketData], None]):
        with self._lock:
            self._callbacks.append(callback)
    
    def get_buffer_for_symbol(self, symbol: str, n: int) -> List[MarketData]:
        with self._lock:
            return [d for d in self._buffer if d.symbol == symbol][-n:]


class ModelRegistry:
    """Registry for managing foundation model checkpoints."""
    
    def __init__(self, checkpoint_path: str = "./checkpoints"):
        self.checkpoint_path = checkpoint_path
        self.loaded_models: Dict[str, Any] = {}
        self.model_versions: Dict[str, str] = {}
        self._lock = threading.RLock()
    
    def load_model(self, model_name: str, version: Optional[str] = None) -> Any:
        """Load a foundation model checkpoint."""
        with self._lock:
            if model_name in self.loaded_models:
                return self.loaded_models[model_name]
            
            # Load model based on name
            if model_name == "kronos":
                model = self._load_kronos(version)
            elif model_name == "timesfm":
                model = self._load_timesfm(version)
            elif model_name == "moirai":
                model = self._load_moirai(version)
            elif model_name == "ttm":
                model = self._load_ttm(version)
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            self.loaded_models[model_name] = model
            self.model_versions[model_name] = version or "latest"
            
            logger.info(f"Loaded {model_name} model (version: {self.model_versions[model_name]})")
            return model
    
    def _load_kronos(self, version: Optional[str]) -> Any:
        """Load Kronos model checkpoint."""
        # Placeholder: actual implementation would load from checkpoint_path
        logger.info("Loading Kronos checkpoint...")
        return {"name": "kronos", "type": "encoder", "version": version or "2.0"}
    
    def _load_timesfm(self, version: Optional[str]) -> Any:
        """Load TimesFM model checkpoint."""
        logger.info("Loading TimesFM checkpoint...")
        return {"name": "timesfm", "type": "forecaster", "version": version or "2.5"}
    
    def _load_moirai(self, version: Optional[str]) -> Any:
        """Load Moirai model checkpoint."""
        logger.info("Loading Moirai checkpoint...")
        return {"name": "moirai", "type": "multivariate", "version": version or "2.0"}
    
    def _load_ttm(self, version: Optional[str]) -> Any:
        """Load TinyTimeMixers model checkpoint."""
        logger.info("Loading TTM checkpoint...")
        return {"name": "ttm", "type": "fast", "version": version or "1.0"}
    
    def hot_swap(self, model_name: str, new_version: str) -> bool:
        """Hot-swap a model without stopping the pipeline."""
        with self._lock:
            try:
                old_model = self.loaded_models.get(model_name)
                new_model = self.load_model(model_name, new_version)
                
                # Atomic swap
                self.loaded_models[model_name] = new_model
                
                logger.info(f"Hot-swapped {model_name}: {self.model_versions[model_name]} -> {new_version}")
                self.model_versions[model_name] = new_version
                
                # Cleanup old model
                if old_model and hasattr(old_model, 'cleanup'):
                    old_model.cleanup()
                
                return True
            except Exception as e:
                logger.error(f"Hot-swap failed for {model_name}: {e}")
                return False
    
    def get_model_status(self) -> Dict[str, Dict]:
        """Get status of all loaded models."""
        with self._lock:
            return {
                name: {
                    "loaded": name in self.loaded_models,
                    "version": self.model_versions.get(name, "unknown"),
                    "type": self.loaded_models[name].get("type", "unknown") if name in self.loaded_models else None
                }
                for name in ["kronos", "timesfm", "moirai", "ttm"]
            }


class RealtimeInferencePipeline:
    """
    High-performance real-time inference pipeline for GETS.
    
    Features:
    - Sub-10ms latency target
    - Async processing
    - Circuit breaker protection
    - Automatic batching
    - Model hot-swapping
    """
    
    def __init__(
        self,
        gets_instance: GETS,
        max_latency_ms: float = 10.0,
        batch_size: int = 32,
        queue_size: int = 1000
    ):
        self.gets = gets_instance
        self.max_latency_ms = max_latency_ms
        self.batch_size = batch_size
        self.queue_size = queue_size
        
        # Components
        self.buffer = StreamingBuffer(max_size=10000)
        self.registry = ModelRegistry()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "kronos": CircuitBreaker("kronos"),
            "timesfm": CircuitBreaker("timesfm"),
            "moirai": CircuitBreaker("moirai"),
            "ttm": CircuitBreaker("ttm"),
            "pipeline": CircuitBreaker("pipeline", failure_threshold=3)
        }
        
        # State
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._signal_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._result_callbacks: List[Callable[[GETSSignal], None]] = []
        
        # Metrics
        self._latency_history: deque = deque(maxlen=1000)
        self._signal_count = 0
        self._abstain_count = 0
    
    async def start(self):
        """Start the real-time pipeline."""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting real-time inference pipeline...")
        
        # Load models
        for model_name in ["kronos", "timesfm", "moirai", "ttm"]:
            self.registry.load_model(model_name)
        
        # Start worker tasks
        self._tasks = [
            asyncio.create_task(self._inference_worker())
            for _ in range(2)  # Multiple workers for throughput
        ]
        
        logger.info("Real-time pipeline started")
    
    async def stop(self):
        """Stop the pipeline gracefully."""
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Real-time pipeline stopped")
    
    async def ingest_market_data(self, data: MarketData) -> Optional[GETSSignal]:
        """
        Ingest market data and optionally return signal immediately.
        
        For low-latency path, returns signal directly.
        For batch path, queues for processing.
        """
        start_time = time.perf_counter()
        
        # Add to buffer
        self.buffer.append(data)
        
        # Check circuit breaker
        if not self.circuit_breakers["pipeline"].can_execute():
            logger.warning("Pipeline circuit breaker OPEN - skipping inference")
            return None
        
        try:
            # Fast path for TTM (<5ms)
            latency_budget = self.max_latency_ms * 1000  # Convert to microseconds
            
            # Try to generate signal
            signal = await self._generate_signal_fast(data, latency_budget)
            
            if signal:
                # Record latency
                elapsed_us = (time.perf_counter() - start_time) * 1e6
                self._latency_history.append(elapsed_us)
                self._signal_count += 1
                
                if signal.abstain_recommended:
                    self._abstain_count += 1
                
                # Notify callbacks
                for callback in self._result_callbacks:
                    try:
                        callback(signal)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                self.circuit_breakers["pipeline"].record_success()
                return signal
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            self.circuit_breakers["pipeline"].record_failure()
        
        return None
    
    async def _generate_signal_fast(
        self,
        data: MarketData,
        latency_budget_us: float
    ) -> Optional[GETSSignal]:
        """Generate signal with strict latency budget."""
        start = time.perf_counter()
        
        # Check if we have time for full inference
        if latency_budget_us < 5000:  # <5ms budget
            # Use TTM only for ultra-low latency
            if self.circuit_breakers["ttm"].can_execute():
                try:
                    signal = self.gets.generate_signal(data, ForecastHorizon.IMMEDIATE)
                    if (time.perf_counter() - start) * 1e6 < latency_budget_us:
                        self.circuit_breakers["ttm"].record_success()
                        return signal
                    else:
                        self.circuit_breakers["ttm"].record_failure()
                except Exception as e:
                    self.circuit_breakers["ttm"].record_failure()
            return None
        
        # Full inference path
        try:
            signal = self.gets.generate_signal(data, ForecastHorizon.SHORT)
            
            elapsed_us = (time.perf_counter() - start) * 1e6
            if elapsed_us > latency_budget_us:
                logger.warning(f"Latency budget exceeded: {elapsed_us:.0f}us > {latency_budget_us:.0f}us")
            
            return signal
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return None
    
    async def _inference_worker(self):
        """Background worker for batch processing."""
        while self._running:
            try:
                # Wait for data
                data = await asyncio.wait_for(self._signal_queue.get(), timeout=1.0)
                
                # Process
                signal = await self._generate_signal_fast(data, self.max_latency_ms * 1000)
                
                if signal:
                    for callback in self._result_callbacks:
                        callback(signal)
                
                self._signal_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def register_result_callback(self, callback: Callable[[GETSSignal], None]):
        """Register callback for signal results."""
        self._result_callbacks.append(callback)
    
    def get_metrics(self) -> PipelineMetrics:
        """Get current pipeline metrics."""
        if not self._latency_history:
            return PipelineMetrics(
                timestamp=datetime.now(),
                p50_latency_us=0,
                p95_latency_us=0,
                p99_latency_us=0,
                max_latency_us=0,
                signals_per_second=0,
                predictions_per_second=0,
                signals_generated=self._signal_count,
                signals_abstained=self._abstain_count,
                abstention_rate=self._abstain_count / max(self._signal_count, 1),
                queue_depth=self._signal_queue.qsize(),
                model_health={k: v == "CLOSED" for k, v in [(name, cb.state) for name, cb in self.circuit_breakers.items()]},
                circuit_breaker_states={k: v.state for k, v in self.circuit_breakers.items()}
            )
        
        latencies = np.array(self._latency_history)
        
        return PipelineMetrics(
            timestamp=datetime.now(),
            p50_latency_us=np.percentile(latencies, 50),
            p95_latency_us=np.percentile(latencies, 95),
            p99_latency_us=np.percentile(latencies, 99),
            max_latency_us=np.max(latencies),
            signals_per_second=self._signal_count / max(1, len(self._latency_history)),
            predictions_per_second=self._signal_count * 4 / max(1, len(self._latency_history)),  # 4 models
            signals_generated=self._signal_count,
            signals_abstained=self._abstain_count,
            abstention_rate=self._abstain_count / max(self._signal_count, 1),
            queue_depth=self._signal_queue.qsize(),
            model_health=self.registry.get_model_status(),
            circuit_breaker_states={k: v.state for k, v in self.circuit_breakers.items()}
        )
    
    def hot_swap_model(self, model_name: str, new_version: str) -> bool:
        """Hot-swap a model without stopping the pipeline."""
        return self.registry.hot_swap(model_name, new_version)


class BatchInferenceEngine:
    """Batch processing engine for historical/backtesting scenarios."""
    
    def __init__(self, gets_instance: GETS, batch_size: int = 64):
        self.gets = gets_instance
        self.batch_size = batch_size
    
    async def process_historical_data(
        self,
        market_data_list: List[MarketData],
        horizon: ForecastHorizon = ForecastHorizon.SHORT,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[GETSSignal]:
        """
        Process historical data in batches.
        
        Args:
            market_data_list: List of market data points
            horizon: Forecast horizon
            progress_callback: Optional callback(current, total)
            
        Returns:
            List of generated signals
        """
        signals = []
        total = len(market_data_list)
        
        for i in range(0, total, self.batch_size):
            batch = market_data_list[i:i + self.batch_size]
            
            # Process batch
            batch_signals = await self._process_batch(batch, horizon)
            signals.extend(batch_signals)
            
            if progress_callback:
                progress_callback(min(i + self.batch_size, total), total)
        
        return signals
    
    async def _process_batch(
        self,
        batch: List[MarketData],
        horizon: ForecastHorizon
    ) -> List[GETSSignal]:
        """Process a single batch."""
        signals = []
        
        for data in batch:
            try:
                signal = self.gets.generate_signal(data, horizon)
                signals.append(signal)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
        
        return signals


def create_realtime_pipeline(
    gets_config: Optional[Dict] = None,
    max_latency_ms: float = 10.0
) -> RealtimeInferencePipeline:
    """
    Factory function to create a real-time inference pipeline.
    
    Args:
        gets_config: GETS configuration
        max_latency_ms: Maximum allowed latency in milliseconds
        
    Returns:
        Configured RealtimeInferencePipeline
    """
    gets = GETS(gets_config)
    
    if not gets.initialize():
        raise RuntimeError("Failed to initialize GETS")
    
    pipeline = RealtimeInferencePipeline(
        gets_instance=gets,
        max_latency_ms=max_latency_ms
    )
    
    return pipeline
