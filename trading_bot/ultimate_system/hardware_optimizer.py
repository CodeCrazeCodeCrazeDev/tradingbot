"""
Hardware Optimizer - Adaptive Resource Management
==================================================

Optimizes system performance based on available hardware:
1. CPU/GPU detection and utilization
2. Memory management
3. Parallel processing optimization
4. Dynamic scaling based on load
5. Power-efficient operation modes
"""

import asyncio
import logging
import os
import sys
import threading
import time
import psutil
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """Performance modes"""
    ULTRA_LOW_LATENCY = "ultra_low_latency"  # Maximum speed, high power
    HIGH_PERFORMANCE = "high_performance"  # Fast, balanced power
    BALANCED = "balanced"  # Good performance, moderate power
    POWER_SAVER = "power_saver"  # Lower performance, low power
    ADAPTIVE = "adaptive"  # Auto-adjust based on conditions


class ResourceType(Enum):
    """Resource types"""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ResourceAllocation:
    """Resource allocation configuration"""
    cpu_cores: int
    cpu_threads: int
    memory_mb: int
    gpu_enabled: bool
    gpu_memory_mb: int
    max_parallel_tasks: int
    batch_size: int
    cache_size_mb: int
    
    # Performance settings
    use_vectorization: bool = True
    use_jit: bool = True
    use_multiprocessing: bool = True
    use_async: bool = True


@dataclass
class HardwareProfile:
    """Hardware profile"""
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    cpu_freq_mhz: float
    
    total_memory_mb: int
    available_memory_mb: int
    
    gpu_available: bool
    gpu_model: str
    gpu_memory_mb: int
    
    disk_type: str  # SSD, HDD, NVMe
    disk_free_gb: float
    
    network_speed_mbps: float
    
    os_type: str
    python_version: str


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    gpu_usage_percent: float
    disk_io_mbps: float
    network_io_mbps: float
    
    latency_ms: float
    throughput_ops: float
    queue_depth: int
    
    bottleneck: Optional[str] = None


class HardwareOptimizer:
    """
    Hardware Optimizer
    
    Capabilities:
    - Detect and profile hardware
    - Optimize resource allocation
    - Dynamic scaling
    - Performance monitoring
    - Bottleneck detection
    - Power management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Performance mode
        self.mode = PerformanceMode(
            self.config.get('mode', 'adaptive')
        )
        
        # Hardware profile
        self.hardware_profile = self._detect_hardware()
        
        # Current allocation
        self.allocation = self._calculate_optimal_allocation()
        
        # Performance history
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history = 1000
        
        # Monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = self.config.get('monitor_interval', 5)
        
        # Optimization state
        self.optimization_count = 0
        self.last_optimization = datetime.now()
        
        # Statistics
        self.stats = {
            'optimizations': 0,
            'mode_changes': 0,
            'bottlenecks_detected': 0,
            'avg_cpu_usage': 0,
            'avg_memory_usage': 0
        }
        
        logger.info(f"Hardware Optimizer initialized - Mode: {self.mode.value}")
        logger.info(f"Hardware: {self.hardware_profile.cpu_cores} cores, "
                   f"{self.hardware_profile.total_memory_mb}MB RAM, "
                   f"GPU: {self.hardware_profile.gpu_available}")
    
    def _detect_hardware(self) -> HardwareProfile:
        """Detect hardware capabilities"""
        try:
            import platform
            
            # CPU info
            cpu_count = os.cpu_count() or 4
            
            try:
                # Memory info
                mem = psutil.virtual_memory()
                total_memory = mem.total // (1024 * 1024)
                available_memory = mem.available // (1024 * 1024)
            except ImportError:
                total_memory = 8192  # Default 8GB
                available_memory = 4096
            
            # GPU detection
            gpu_available = False
            gpu_model = "None"
            gpu_memory = 0
            
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_available = True
                    gpu_model = torch.cuda.get_device_name(0)
                    gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
            except ImportError:
                pass
            
            # Disk info
            try:
                disk = psutil.disk_usage('/')
                disk_free = disk.free / (1024 * 1024 * 1024)
            except Exception:
                disk_free = 100.0
            
            return HardwareProfile(
                cpu_model=platform.processor() or "Unknown",
                cpu_cores=cpu_count,
                cpu_threads=cpu_count * 2,  # Assume hyperthreading
                cpu_freq_mhz=2400.0,  # Default
                total_memory_mb=total_memory,
                available_memory_mb=available_memory,
                gpu_available=gpu_available,
                gpu_model=gpu_model,
                gpu_memory_mb=gpu_memory,
                disk_type="SSD",  # Assume SSD
                disk_free_gb=disk_free,
                network_speed_mbps=100.0,  # Default
                os_type=platform.system(),
                python_version=platform.python_version()
            )
            
        except Exception as e:
            logger.error(f"Hardware detection failed: {e}")
            return HardwareProfile(
                cpu_model="Unknown",
                cpu_cores=4,
                cpu_threads=8,
                cpu_freq_mhz=2400.0,
                total_memory_mb=8192,
                available_memory_mb=4096,
                gpu_available=False,
                gpu_model="None",
                gpu_memory_mb=0,
                disk_type="Unknown",
                disk_free_gb=100.0,
                network_speed_mbps=100.0,
                os_type=sys.platform,
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}"
            )
    
    def _calculate_optimal_allocation(self) -> ResourceAllocation:
        """Calculate optimal resource allocation"""
        hw = self.hardware_profile
        
        # Base allocation on mode
        if self.mode == PerformanceMode.ULTRA_LOW_LATENCY:
            cpu_cores = hw.cpu_cores
            memory_pct = 0.8
            parallel_tasks = hw.cpu_threads
            batch_size = 1  # Process immediately
            
        elif self.mode == PerformanceMode.HIGH_PERFORMANCE:
            cpu_cores = max(1, hw.cpu_cores - 1)
            memory_pct = 0.7
            parallel_tasks = hw.cpu_threads - 2
            batch_size = 10
            
        elif self.mode == PerformanceMode.BALANCED:
            cpu_cores = max(1, hw.cpu_cores // 2)
            memory_pct = 0.5
            parallel_tasks = hw.cpu_cores
            batch_size = 50
            
        elif self.mode == PerformanceMode.POWER_SAVER:
            cpu_cores = max(1, hw.cpu_cores // 4)
            memory_pct = 0.3
            parallel_tasks = 2
            batch_size = 100
            
        else:  # ADAPTIVE
            cpu_cores = max(1, hw.cpu_cores - 1)
            memory_pct = 0.6
            parallel_tasks = hw.cpu_cores
            batch_size = 25
        
        return ResourceAllocation(
            cpu_cores=cpu_cores,
            cpu_threads=min(parallel_tasks, hw.cpu_threads),
            memory_mb=int(hw.available_memory_mb * memory_pct),
            gpu_enabled=hw.gpu_available,
            gpu_memory_mb=int(hw.gpu_memory_mb * 0.8) if hw.gpu_available else 0,
            max_parallel_tasks=parallel_tasks,
            batch_size=batch_size,
            cache_size_mb=min(1024, int(hw.available_memory_mb * 0.1)),
            use_vectorization=True,
            use_jit=True,
            use_multiprocessing=cpu_cores > 1,
            use_async=True
        )
    
    def set_mode(self, mode: PerformanceMode):
        """Set performance mode"""
        if mode != self.mode:
            self.mode = mode
            self.allocation = self._calculate_optimal_allocation()
            self.stats['mode_changes'] += 1
            logger.info(f"Performance mode changed to: {mode.value}")
    
    def get_allocation(self) -> ResourceAllocation:
        """Get current resource allocation"""
        return self.allocation
    
    def optimize(self) -> ResourceAllocation:
        """Optimize resource allocation based on current conditions"""
        if self.mode != PerformanceMode.ADAPTIVE:
            return self.allocation
        
        # Get current metrics
        metrics = self._get_current_metrics()
        
        # Detect bottlenecks
        bottleneck = self._detect_bottleneck(metrics)
        
        if bottleneck:
            self.stats['bottlenecks_detected'] += 1
            self._adjust_for_bottleneck(bottleneck)
        
        self.optimization_count += 1
        self.last_optimization = datetime.now()
        self.stats['optimizations'] += 1
        
        return self.allocation
    
    def _get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
            
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_mbps = (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024) if disk_io else 0
            
            # Network I/O
            net_io = psutil.net_io_counters()
            net_mbps = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024) if net_io else 0
            
        except ImportError:
            cpu_usage = 50.0
            memory_usage = 50.0
            disk_mbps = 0.0
            net_mbps = 0.0
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory_usage,
            gpu_usage_percent=0.0,  # Would need GPU monitoring
            disk_io_mbps=disk_mbps,
            network_io_mbps=net_mbps,
            latency_ms=1.0,  # Would measure actual latency
            throughput_ops=1000.0,  # Would measure actual throughput
            queue_depth=0
        )
        
        # Store in history
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        # Update stats
        self.stats['avg_cpu_usage'] = sum(
            m.cpu_usage_percent for m in self.metrics_history[-100:]
        ) / min(100, len(self.metrics_history))
        self.stats['avg_memory_usage'] = sum(
            m.memory_usage_percent for m in self.metrics_history[-100:]
        ) / min(100, len(self.metrics_history))
        
        return metrics
    
    def _detect_bottleneck(self, metrics: PerformanceMetrics) -> Optional[str]:
        """Detect performance bottleneck"""
        if metrics.cpu_usage_percent > 90:
            metrics.bottleneck = "CPU"
            return "CPU"
        
        if metrics.memory_usage_percent > 85:
            metrics.bottleneck = "MEMORY"
            return "MEMORY"
        
        if metrics.gpu_usage_percent > 95:
            metrics.bottleneck = "GPU"
            return "GPU"
        
        if metrics.latency_ms > 100:
            metrics.bottleneck = "LATENCY"
            return "LATENCY"
        
        return None
    
    def _adjust_for_bottleneck(self, bottleneck: str):
        """Adjust allocation for bottleneck"""
        if bottleneck == "CPU":
            # Reduce parallel tasks
            self.allocation.max_parallel_tasks = max(
                1, self.allocation.max_parallel_tasks - 2
            )
            # Increase batch size
            self.allocation.batch_size = min(
                1000, self.allocation.batch_size * 2
            )
            logger.info("Adjusted for CPU bottleneck")
            
        elif bottleneck == "MEMORY":
            # Reduce memory allocation
            self.allocation.memory_mb = int(self.allocation.memory_mb * 0.8)
            # Reduce cache
            self.allocation.cache_size_mb = int(self.allocation.cache_size_mb * 0.5)
            logger.info("Adjusted for memory bottleneck")
            
        elif bottleneck == "GPU":
            # Reduce GPU memory
            self.allocation.gpu_memory_mb = int(self.allocation.gpu_memory_mb * 0.8)
            logger.info("Adjusted for GPU bottleneck")
            
        elif bottleneck == "LATENCY":
            # Reduce batch size for faster processing
            self.allocation.batch_size = max(1, self.allocation.batch_size // 2)
            logger.info("Adjusted for latency bottleneck")
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Hardware monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Hardware monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                metrics = self._get_current_metrics()
                
                # Auto-optimize if adaptive mode
                if self.mode == PerformanceMode.ADAPTIVE:
                    bottleneck = self._detect_bottleneck(metrics)
                    if bottleneck:
                        self._adjust_for_bottleneck(bottleneck)
                
                time.sleep(self._monitor_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self._monitor_interval)
    
    def get_parallel_executor(self):
        """Get configured parallel executor"""
        from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
        
        if self.allocation.use_multiprocessing:
            return ProcessPoolExecutor(max_workers=self.allocation.cpu_cores)
        else:
            return ThreadPoolExecutor(max_workers=self.allocation.cpu_threads)
    
    def get_optimal_batch_size(self, data_size: int) -> int:
        """Get optimal batch size for data"""
        if data_size <= self.allocation.batch_size:
            return data_size
        
        # Calculate based on memory
        estimated_item_size = 1024  # 1KB per item estimate
        max_batch_by_memory = self.allocation.memory_mb * 1024 // estimated_item_size
        
        return min(self.allocation.batch_size, max_batch_by_memory, data_size)
    
    def should_use_gpu(self, operation: str) -> bool:
        """Determine if GPU should be used for operation"""
        if not self.allocation.gpu_enabled:
            return False
        
        gpu_operations = [
            'neural_network', 'deep_learning', 'matrix_multiply',
            'convolution', 'transformer', 'embedding'
        ]
        
        return any(op in operation.lower() for op in gpu_operations)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        return {
            **self.stats,
            'mode': self.mode.value,
            'hardware': {
                'cpu_cores': self.hardware_profile.cpu_cores,
                'memory_mb': self.hardware_profile.total_memory_mb,
                'gpu': self.hardware_profile.gpu_model if self.hardware_profile.gpu_available else "None"
            },
            'allocation': {
                'cpu_cores': self.allocation.cpu_cores,
                'memory_mb': self.allocation.memory_mb,
                'parallel_tasks': self.allocation.max_parallel_tasks,
                'batch_size': self.allocation.batch_size
            },
            'monitoring': self._monitoring,
            'metrics_count': len(self.metrics_history)
        }
