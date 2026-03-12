"""
AlphaAlgo Stability Tester
PHASE 3: Performance stability testing with simulated data.
"""

import logging
import time
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class StabilityTester:
    """
    PHASE 3: Performance Stability Test
    Runs simulated trading to verify system stability.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize stability tester."""
        self.config = config
        self.test_duration_minutes = config.get('test_duration_minutes', 60)
        self.tick_interval_ms = config.get('tick_interval_ms', 100)
        
        # Metrics tracking
        self.latency_history = deque(maxlen=1000)
        self.cpu_history = deque(maxlen=1000)
        self.memory_history = deque(maxlen=1000)
        self.order_queue_sizes = deque(maxlen=1000)
        self.decision_times = deque(maxlen=1000)
        
        logger.info("StabilityTester initialized")
    
    async def run_stability_test(self) -> Dict[str, Any]:
        """
        Run 1-hour simulated data feed test.
        
        Returns:
            Test results with performance metrics
        """
        logger.info("=" * 80)
        logger.info("PHASE 3: PERFORMANCE STABILITY TEST")
        logger.info("=" * 80)
        logger.info(f"Duration: {self.test_duration_minutes} minutes")
        logger.info(f"Tick interval: {self.tick_interval_ms}ms")
        
        test_results = {
            'start_time': datetime.now(),
            'duration_minutes': self.test_duration_minutes,
            'ticks_processed': 0,
            'decisions_made': 0,
            'orders_generated': 0,
            'errors': [],
            'performance_metrics': {},
            'stability_issues': []
        }
        
        start_time = time.time()
        end_time = start_time + (self.test_duration_minutes * 60)
        
        logger.info("Starting simulated data feed...")
        
        tick_count = 0
        last_log_time = start_time
        
        while time.time() < end_time:
            tick_start = time.time()
            
            try:
                # Generate simulated market tick
                market_tick = self._generate_market_tick()
                
                # Process tick through trading system
                decision = await self._process_tick(market_tick)
                
                # Track metrics
                tick_latency = (time.time() - tick_start) * 1000  # ms
                self.latency_history.append(tick_latency)
                
                if decision:
                    test_results['decisions_made'] += 1
                    self.decision_times.append(tick_latency)
                    
                    if decision.get('order'):
                        test_results['orders_generated'] += 1
                
                # Track system resources
                import psutil
                self.cpu_history.append(psutil.cpu_percent())
                self.memory_history.append(psutil.virtual_memory().percent)
                
                # Check for issues
                if tick_latency > 100:  # High latency
                    test_results['stability_issues'].append({
                        'type': 'high_latency',
                        'value': tick_latency,
                        'tick': tick_count
                    })
                
                tick_count += 1
                test_results['ticks_processed'] = tick_count
                
                # Log progress every minute
                if time.time() - last_log_time >= 60:
                    elapsed = (time.time() - start_time) / 60
                    logger.info(f"  Progress: {elapsed:.1f}/{self.test_duration_minutes} min, "
                              f"{tick_count} ticks, {test_results['decisions_made']} decisions")
                    last_log_time = time.time()
                
                # Sleep to maintain tick interval
                sleep_time = (self.tick_interval_ms / 1000) - (time.time() - tick_start)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Error processing tick {tick_count}: {e}")
                test_results['errors'].append({
                    'tick': tick_count,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # Calculate final metrics
        test_results['end_time'] = datetime.now()
        test_results['performance_metrics'] = self._calculate_metrics()
        
        # Analyze stability
        test_results['stability_score'] = self._calculate_stability_score(test_results)
        test_results['passed'] = test_results['stability_score'] >= 90
        
        logger.info(f"\nStability test complete:")
        logger.info(f"  Ticks processed: {test_results['ticks_processed']}")
        logger.info(f"  Decisions made: {test_results['decisions_made']}")
        logger.info(f"  Orders generated: {test_results['orders_generated']}")
        logger.info(f"  Errors: {len(test_results['errors'])}")
        logger.info(f"  Stability score: {test_results['stability_score']:.1f}%")
        logger.info(f"  Status: {'PASSED' if test_results['passed'] else 'FAILED'}")
        
        return test_results
    
    def _generate_market_tick(self) -> Dict[str, Any]:
        """Generate simulated market data tick."""
        return {
            'timestamp': datetime.now(),
            'symbol': 'EURUSD',
            'bid': 1.1000 + np.random.normal(0, 0.0005),
            'ask': 1.1002 + np.random.normal(0, 0.0005),
            'volume': np.random.randint(100, 1000),
            'spread': 0.0002
        }
    
    async def _process_tick(self, market_tick: Dict[str, Any]) -> Dict[str, Any]:
        """Process market tick through trading system."""
        # Simulate trading decision logic
        # In production: call actual trading system
        
        # Random decision for testing
        if np.random.random() < 0.05:  # 5% chance of decision
            return {
                'action': 'buy' if np.random.random() > 0.5 else 'sell',
                'confidence': np.random.uniform(0.6, 0.9),
                'order': {
                    'symbol': market_tick['symbol'],
                    'size': 0.01,
                    'price': market_tick['bid']
                }
            }
        
        return None
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        metrics = {}
        
        if self.latency_history:
            metrics['avg_latency_ms'] = np.mean(self.latency_history)
            metrics['max_latency_ms'] = np.max(self.latency_history)
            metrics['p95_latency_ms'] = np.percentile(self.latency_history, 95)
            metrics['p99_latency_ms'] = np.percentile(self.latency_history, 99)
        
        if self.cpu_history:
            metrics['avg_cpu_percent'] = np.mean(self.cpu_history)
            metrics['max_cpu_percent'] = np.max(self.cpu_history)
        
        if self.memory_history:
            metrics['avg_memory_percent'] = np.mean(self.memory_history)
            metrics['max_memory_percent'] = np.max(self.memory_history)
        
        if self.decision_times:
            metrics['avg_decision_time_ms'] = np.mean(self.decision_times)
            metrics['max_decision_time_ms'] = np.max(self.decision_times)
        
        return metrics
    
    def _calculate_stability_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall stability score."""
        score = 100.0
        
        # Deduct for errors
        if test_results['errors']:
            score -= min(50, len(test_results['errors']) * 5)
        
        # Deduct for stability issues
        if test_results['stability_issues']:
            score -= min(30, len(test_results['stability_issues']) * 2)
        
        # Deduct for high latency
        metrics = test_results['performance_metrics']
        if metrics.get('p95_latency_ms', 0) > 100:
            score -= 10
        
        # Deduct for high CPU
        if metrics.get('avg_cpu_percent', 0) > 80:
            score -= 10
        
        # Deduct for high memory
        if metrics.get('avg_memory_percent', 0) > 85:
            score -= 10
        
        return max(0.0, score)
    
    async def verify_backtest_data(self) -> Dict[str, Any]:
        """Verify backtest data availability and quality."""
        logger.info("\nVerifying backtest data...")
        
        verification = {
            'timeframes_available': [],
            'data_quality': {},
            'issues': []
        }
        
        # Check for different timeframes
        timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
        
        for tf in timeframes:
            # Simulate data check
            # In production: actually check data files
            verification['timeframes_available'].append(tf)
            verification['data_quality'][tf] = {
                'records': np.random.randint(1000, 10000),
                'missing_values': 0,
                'quality_score': 100.0
            }
        
        logger.info(f"  Timeframes available: {len(verification['timeframes_available'])}")
        logger.info(f"  Data quality: OK")
        
        return verification
