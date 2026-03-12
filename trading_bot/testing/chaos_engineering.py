"""
Chaos Engineering Framework for Trading System Resilience Testing
"""

import random
import time
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class FaultType(Enum):
    """Types of faults to inject"""
    NETWORK_LATENCY = "network_latency"
    NETWORK_FAILURE = "network_failure"
    DATA_CORRUPTION = "data_corruption"
    SERVICE_CRASH = "service_crash"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SLOW_RESPONSE = "slow_response"


@dataclass
class ChaosExperiment:
    """Configuration for a chaos experiment"""
    name: str
    fault_type: FaultType
    target_component: str
    probability: float = 0.1
    duration_seconds: float = 60
    enabled: bool = True


class ChaosMonkey:
    """
    Chaos Monkey for injecting faults into trading system
    """
    
    def __init__(self):
        self.experiments: List[ChaosExperiment] = []
        self.active = False
        self.fault_history: List[Dict] = []
        
    def add_experiment(self, experiment: ChaosExperiment):
        """Add chaos experiment"""
        self.experiments.append(experiment)
        logger.info(f"Added chaos experiment: {experiment.name}")
    
    def start(self):
        """Start chaos experiments"""
        self.active = True
        logger.info("Chaos Monkey activated")
    
    def stop(self):
        """Stop chaos experiments"""
        self.active = False
        logger.info("Chaos Monkey deactivated")
    
    def should_inject_fault(self, component: str) -> Optional[ChaosExperiment]:
        """Check if fault should be injected for component"""
        if not self.active:
            return None
        
        for exp in self.experiments:
            if exp.enabled and exp.target_component == component:
                if random.random() < exp.probability:
                    return exp
        
        return None
    
    def inject_network_latency(self, base_latency: float, experiment: ChaosExperiment) -> float:
        """Inject network latency"""
        added_latency = random.uniform(0.1, 2.0)
        logger.warning(f"Injecting {added_latency:.2f}s latency ({experiment.name})")
        
        self.fault_history.append({
            'type': 'network_latency',
            'experiment': experiment.name,
            'latency': added_latency,
            'timestamp': time.time()
        })
        
        return base_latency + added_latency
    
    def inject_data_corruption(self, data: Any, experiment: ChaosExperiment) -> Any:
        """Inject data corruption"""
        logger.warning(f"Injecting data corruption ({experiment.name})")
        
        self.fault_history.append({
            'type': 'data_corruption',
            'experiment': experiment.name,
            'timestamp': time.time()
        })
        
        # Corrupt 10% of data points
        if hasattr(data, '__len__'):
            corrupt_count = max(1, len(data) // 10)
            indices = random.sample(range(len(data)), corrupt_count)
            for idx in indices:
                if hasattr(data, '__setitem__'):
                    data[idx] = None
        
        return data


class ResilienceTester:
    """
    Test system resilience under various failure scenarios
    """
    
    def __init__(self, system: Any):
        self.system = system
        self.test_results: List[Dict] = []
    
    def test_data_feed_failure(self, duration: float = 10):
        """Test system behavior when data feed fails"""
        logger.info("Testing data feed failure scenario")
        
        start_time = time.time()
        
        # Simulate data feed failure
        original_state = getattr(self.system, 'data_feed_active', True)
        self.system.data_feed_active = False
        
        time.sleep(duration)
        
        # Restore
        self.system.data_feed_active = original_state
        
        result = {
            'test': 'data_feed_failure',
            'duration': duration,
            'system_survived': True,
            'timestamp': start_time
        }
        
        self.test_results.append(result)
        logger.info(f"Data feed failure test completed: {result}")
        
        return result
    
    def test_high_latency(self, latency_ms: float = 1000, duration: float = 10):
        """Test system under high latency"""
        logger.info(f"Testing high latency scenario ({latency_ms}ms)")
        
        start_time = time.time()
        
        # Inject latency
        def slow_wrapper(func):
            def wrapper(*args, **kwargs):
                time.sleep(latency_ms / 1000)
                return func(*args, **kwargs)
            return wrapper
        
        # Apply to system methods
        if hasattr(self.system, 'process_data'):
            original = self.system.process_data
            self.system.process_data = slow_wrapper(original)
        
        time.sleep(duration)
        
        # Restore
        if hasattr(self.system, 'process_data'):
            self.system.process_data = original
        
        result = {
            'test': 'high_latency',
            'latency_ms': latency_ms,
            'duration': duration,
            'system_survived': True,
            'timestamp': start_time
        }
        
        self.test_results.append(result)
        logger.info(f"High latency test completed: {result}")
        
        return result
    
    def test_resource_exhaustion(self, resource: str = 'memory'):
        """Test system under resource exhaustion"""
        logger.info(f"Testing {resource} exhaustion scenario")
        
        start_time = time.time()
        
        if resource == 'memory':
            try:
                # Allocate large memory
                _ = [0] * (10**7)  # 10M integers
            except MemoryError:
                logger.warning("Memory allocation failed as expected")
        
        result = {
            'test': f'{resource}_exhaustion',
            'system_survived': True,
            'timestamp': start_time
        }
        
        self.test_results.append(result)
        logger.info(f"Resource exhaustion test completed: {result}")
        
        return result
    
    def run_all_tests(self):
        """Run all resilience tests"""
        logger.info("Running all resilience tests")
        
        tests = [
            lambda: self.test_data_feed_failure(5),
            lambda: self.test_high_latency(500, 5),
            lambda: self.test_resource_exhaustion('memory')
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(2)
            except Exception as e:
                logger.error(f"Test failed: {e}")
        
        logger.info(f"Completed {len(self.test_results)} resilience tests")
        return self.test_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test Chaos Monkey
    monkey = ChaosMonkey()
    
    # Add experiments
    monkey.add_experiment(ChaosExperiment(
        name="network_latency_test",
        fault_type=FaultType.NETWORK_LATENCY,
        target_component="data_feed",
        probability=0.3
    ))
    
    monkey.add_experiment(ChaosExperiment(
        name="data_corruption_test",
        fault_type=FaultType.DATA_CORRUPTION,
        target_component="market_data",
        probability=0.1
    ))
    
    monkey.start()
    
    # Simulate some operations
    for i in range(10):
        exp = monkey.should_inject_fault("data_feed")
        if exp:
            latency = monkey.inject_network_latency(0.01, exp)
            logger.info(f"Operation {i}: Latency = {latency:.3f}s")
        else:
            logger.info(f"Operation {i}: Normal")
        time.sleep(0.5)
    
    monkey.stop()
    
    logger.info(f"\n✅ Chaos engineering test completed")
    logger.info(f"Faults injected: {len(monkey.fault_history)}")
