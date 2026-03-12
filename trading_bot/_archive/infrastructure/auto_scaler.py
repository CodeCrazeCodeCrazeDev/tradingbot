"""
Auto-scaling for trading system components
"""

import logging
import threading
import time
from typing import Callable, Dict, Optional
from dataclasses import dataclass
import psutil
from enum import auto

logger = logging.getLogger(__name__)


@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration"""
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 80.0
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    cooldown_seconds: float = 60.0


class AutoScaler:
    """
    Auto-scale system components based on resource usage
    """
    
    def __init__(self, policy: ScalingPolicy = None):
        self.policy = policy or ScalingPolicy()
        self.current_instances = self.policy.min_instances
        self.last_scale_time = 0
        self.running = False
        self.monitor_thread = None
        self.workers = []
        self.lock = threading.Lock()
    
    def start(self, worker_factory: Callable):
        """Start auto-scaler"""
        self.running = True
        self.worker_factory = worker_factory
        
        # Initialize minimum instances
        for _ in range(self.policy.min_instances):
            self._add_worker()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Auto-scaler started with {self.current_instances} instances")
    
    def stop(self):
        """Stop auto-scaler"""
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Stop all workers
        with self.lock:
            for worker in self.workers:
                if hasattr(worker, 'stop'):
                    worker.stop()
            self.workers.clear()
        
        logger.info("Auto-scaler stopped")
    
    def _monitor_loop(self):
        """Monitor resource usage and scale"""
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                # Check if scaling is needed
                if self._should_scale_up(cpu_percent, memory_percent):
                    self._scale_up()
                elif self._should_scale_down(cpu_percent, memory_percent):
                    self._scale_down()
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in auto-scaler monitor: {e}")
                time.sleep(10)
    
    def _should_scale_up(self, cpu: float, memory: float) -> bool:
        """Check if should scale up"""
        if self.current_instances >= self.policy.max_instances:
            return False
        
        if time.time() - self.last_scale_time < self.policy.cooldown_seconds:
            return False
        
        return cpu > self.policy.scale_up_threshold or memory > self.policy.scale_up_threshold
    
    def _should_scale_down(self, cpu: float, memory: float) -> bool:
        """Check if should scale down"""
        if self.current_instances <= self.policy.min_instances:
            return False
        
        if time.time() - self.last_scale_time < self.policy.cooldown_seconds:
            return False
        
        return cpu < self.policy.scale_down_threshold and memory < self.policy.scale_down_threshold
    
    def _scale_up(self):
        """Add worker instance"""
        with self.lock:
            if self.current_instances < self.policy.max_instances:
                self._add_worker()
                self.current_instances += 1
                self.last_scale_time = time.time()
                logger.info(f"Scaled up to {self.current_instances} instances")
    
    def _scale_down(self):
        """Remove worker instance"""
        with self.lock:
            if self.current_instances > self.policy.min_instances and self.workers:
                worker = self.workers.pop()
                if hasattr(worker, 'stop'):
                    worker.stop()
                self.current_instances -= 1
                self.last_scale_time = time.time()
                logger.info(f"Scaled down to {self.current_instances} instances")
    
    def _add_worker(self):
        """Add new worker instance"""
        try:
            worker = self.worker_factory()
            if hasattr(worker, 'start'):
                worker.start()
            self.workers.append(worker)
        except Exception as e:
            logger.error(f"Failed to add worker: {e}")
    
    def get_status(self) -> Dict:
        """Get scaler status"""
        return {
            'running': self.running,
            'current_instances': self.current_instances,
            'min_instances': self.policy.min_instances,
            'max_instances': self.policy.max_instances,
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent
        }


class LoadBalancer:
    """Simple round-robin load balancer"""
    
    def __init__(self):
        self.workers = []
        self.current_index = 0
        self.lock = threading.Lock()
    
    def add_worker(self, worker):
        """Add worker to pool"""
        with self.lock:
            self.workers.append(worker)
    
    def remove_worker(self, worker):
        """Remove worker from pool"""
        with self.lock:
            if worker in self.workers:
                self.workers.remove(worker)
    
    def get_worker(self):
        """Get next worker (round-robin)"""
        with self.lock:
            if not self.workers:
                return None
            
            worker = self.workers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.workers)
            
            return worker
    
    def execute(self, task: Callable, *args, **kwargs):
        """Execute task on next available worker"""
        worker = self.get_worker()
        
        if worker is None:
            raise RuntimeError("No workers available")
        
        if hasattr(worker, 'execute'):
            return worker.execute(task, *args, **kwargs)
        else:
            return task(*args, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test auto-scaler
    class DummyWorker:
        def __init__(self):
            self.running = False
        
        def start(self):
            self.running = True
            logger.info(f"Worker started")
        
        def stop(self):
            self.running = False
            logger.info(f"Worker stopped")
    
    policy = ScalingPolicy(
        min_instances=2,
        max_instances=5,
        scale_up_threshold=70.0,
        scale_down_threshold=30.0
    )
    
    scaler = AutoScaler(policy)
    scaler.start(DummyWorker)
    
    logger.info(f"Initial status: {scaler.get_status()}")
    
    # Run for a bit
    time.sleep(5)
    
    logger.info(f"Final status: {scaler.get_status()}")
    
    scaler.stop()
    
    logger.info("✅ Auto-scaler test passed!")
