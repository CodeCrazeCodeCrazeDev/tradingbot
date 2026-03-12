"""
Load Testing Suite

Tests system performance under high load conditions.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
import statistics
from typing import Dict

logger = logging.getLogger(__name__)


class LoadTestSuite:
    """
    Comprehensive load testing for trading bot
    """
    
    def __init__(self, execution_manager, data_stream, config: Dict[str, Any] = None):
        self.execution = execution_manager
        self.data_stream = data_stream
        self.config = config or {}
        
        # Test results
        self.results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
    pass
        """Run all load tests"""
        logger.info("=" * 60)
        logger.info("LOAD TESTING SUITE - STARTING")
        logger.info("=" * 60)
        
        results = {}
        
        # Test 1: High-frequency order placement
        logger.info("\n[TEST 1] High-Frequency Order Placement")
        results['high_frequency_orders'] = await self.test_high_frequency_orders()
        
        # Test 2: Concurrent order execution
        logger.info("\n[TEST 2] Concurrent Order Execution")
        results['concurrent_orders'] = await self.test_concurrent_orders()
        
        # Test 3: Market data throughput
        logger.info("\n[TEST 3] Market Data Throughput")
        results['data_throughput'] = await self.test_data_throughput()
        
        # Test 4: Stress test with multiple symbols
        logger.info("\n[TEST 4] Multi-Symbol Stress Test")
        results['multi_symbol_stress'] = await self.test_multi_symbol_stress()
        
        # Test 5: Memory leak detection
        logger.info("\n[TEST 5] Memory Leak Detection")
        results['memory_leak'] = await self.test_memory_leak()
        
        # Test 6: API rate limit testing
        logger.info("\n[TEST 6] API Rate Limit Testing")
        results['rate_limits'] = await self.test_rate_limits()
        
        # Generate summary
        summary = self._generate_summary(results)
        
        logger.info("\n" + "=" * 60)
        logger.info("LOAD TESTING COMPLETE")
        logger.info("=" * 60)
        
        return {
            'results': results,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    async def test_high_frequency_orders(self, count: int = 1000) -> Dict[str, Any]:
    pass
        """
        Test high-frequency order placement
        
        Args:
    pass
            count: Number of orders to place
        
        Returns:
    pass
            Test results
        """
        orders = []
        start_time = time.time()
        
        for i in range(count):
            order = await self.execution.place_order(
                    symbol='EURUSD',
                    order_type='market',
                    side='buy',
                    quantity=0.01,
                    metadata={'test': 'load_test', 'index': i}
                )
                orders.append(order)
        duration = time.time() - start_time
        orders_per_second = count / duration if duration > 0 else 0
        
        result = {
            'total_orders': count,
            'successful_orders': len(orders),
            'failed_orders': count - len(orders),
            'duration_seconds': duration,
            'orders_per_second': orders_per_second,
            'avg_latency_ms': (duration / count * 1000) if count > 0 else 0
        }
        
        logger.info(f"  Placed {count} orders in {duration:.2f}s ({orders_per_second:.2f} orders/sec)")
        logger.info(f"  Success rate: {len(orders)/count*100:.1f}%")
        
        return result
    
    async def test_concurrent_orders(self, concurrent_count: int = 50) -> Dict[str, Any]:
    pass
        """
        Test concurrent order execution
        
        Args:
    pass
            concurrent_count: Number of concurrent orders
        
        Returns:
    pass
            Test results
        """
        start_time = time.time()
        
        # Create concurrent order tasks
        tasks = [
            self.execution.place_order(
                symbol='EURUSD',
                order_type='market',
                side='buy' if i % 2 == 0 else 'sell',
                quantity=0.01,
                metadata={'test': 'concurrent', 'index': i}
            )
            for i in range(concurrent_count)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        result = {
            'concurrent_orders': concurrent_count,
            'successful': len(successful),
            'failed': len(failed),
            'duration_seconds': duration,
            'success_rate': len(successful) / concurrent_count if concurrent_count > 0 else 0
        }
        
        logger.info(f"  {concurrent_count} concurrent orders in {duration:.2f}s")
        logger.info(f"  Success: {len(successful)}, Failed: {len(failed)}")
        
        return result
    
    async def test_data_throughput(self, duration_seconds: int = 10) -> Dict[str, Any]:
    pass
        """
        Test market data throughput
        
        Args:
    pass
            duration_seconds: Test duration
        
        Returns:
    pass
            Test results
        """
        ticks_processed = 0
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        latencies = []
        
        while time.time() < end_time:
    pass
            try:
                tick = await self.data_stream.get_tick('EURUSD')
                
                if tick:
                    # Calculate latency
                    if 'timestamp' in tick:
                        tick_time = datetime.fromisoformat(tick['timestamp'])
                        latency = (datetime.now() - tick_time).total_seconds() * 1000
                        latencies.append(latency)
                    
                    ticks_processed += 1
            except Exception as e:
                logger.error(f"Tick processing error: {e}")
        
        actual_duration = time.time() - start_time
        ticks_per_second = ticks_processed / actual_duration if actual_duration > 0 else 0
        
        result = {
            'duration_seconds': actual_duration,
            'ticks_processed': ticks_processed,
            'ticks_per_second': ticks_per_second,
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0
        }
        
        logger.info(f"  Processed {ticks_processed} ticks in {actual_duration:.2f}s ({ticks_per_second:.2f} ticks/sec)")
        if latencies:
            logger.info(f"  Latency - Avg: {result['avg_latency_ms']:.2f}ms, Max: {result['max_latency_ms']:.2f}ms")
        
        return result
    
    async def test_multi_symbol_stress(self, symbols: List[str] = None, duration: int = 30) -> Dict[str, Any]:
    pass
        """
        Stress test with multiple symbols
        
        Args:
            symbols: List of symbols to test
            duration: Test duration in seconds
        
        Returns:
    pass
            Test results
        """
        symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
        
        start_time = time.time()
        end_time = start_time + duration
        
        orders_placed = {symbol: 0 for symbol in symbols}
        errors = {symbol: 0 for symbol in symbols}
        
        while time.time() < end_time:
            for symbol in symbols:
                await self.execution.place_order(
                        symbol=symbol,
                        order_type='market',
                        side='buy',
                        quantity=0.01,
                        metadata={'test': 'multi_symbol'}
                    )
                    orders_placed[symbol] += 1
                await asyncio.sleep(0.1)  # Small delay between orders
        
        actual_duration = time.time() - start_time
        total_orders = sum(orders_placed.values())
        total_errors = sum(errors.values())
        
        result = {
            'symbols_tested': len(symbols),
            'duration_seconds': actual_duration,
            'total_orders': total_orders,
            'total_errors': total_errors,
            'orders_per_symbol': orders_placed,
            'errors_per_symbol': errors,
            'overall_success_rate': total_orders / (total_orders + total_errors) if (total_orders + total_errors) > 0 else 0
        }
        
        logger.info(f"  Tested {len(symbols)} symbols for {actual_duration:.2f}s")
        logger.info(f"  Total orders: {total_orders}, Errors: {total_errors}")
        
        return result
    
    async def test_memory_leak(self, iterations: int = 1000) -> Dict[str, Any]:
    pass
        """
        Test for memory leaks
        
        Args:
            iterations: Number of iterations
        
        Returns:
    pass
            Test results
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run iterations
        for i in range(iterations):
            await self.execution.place_order(
                symbol='EURUSD',
                order_type='market',
                side='buy',
                quantity=0.01,
                metadata={'test': 'memory_leak', 'iteration': i}
            )
            
            if i % 100 == 0:
                # Force garbage collection
                import gc
                gc.collect()
        
        # Final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        memory_per_iteration = memory_increase / iterations if iterations > 0 else 0
        
        result = {
            'iterations': iterations,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_increase_mb': memory_increase,
            'memory_per_iteration_kb': memory_per_iteration * 1024,
            'leak_detected': memory_per_iteration > 0.1  # More than 100KB per iteration
        }
        
        logger.info(f"  Memory: {initial_memory:.2f}MB → {final_memory:.2f}MB (+{memory_increase:.2f}MB)")
        logger.info(f"  Per iteration: {memory_per_iteration*1024:.2f}KB")
        
        if result['leak_detected']:
            logger.warning("  ⚠ Potential memory leak detected!")
        
        return result
    
    async def test_rate_limits(self) -> Dict[str, Any]:
    pass
        """
        Test API rate limits
        
        Returns:
    pass
            Test results
        """
        max_rate = 0
        rate_limit_hit = False
        
        # Gradually increase order rate until limit is hit
        for rate in range(1, 101, 10):  # 1 to 100 orders/sec
            try:
                start = time.time()
                
                for _ in range(rate):
                    await self.execution.place_order(
                        symbol='EURUSD',
                        order_type='market',
                        side='buy',
                        quantity=0.01,
                        metadata={'test': 'rate_limit'}
                    )
                
                duration = time.time() - start
                
                if duration < 1.0:
                    max_rate = rate
                else:
                    rate_limit_hit = True
                    break
                    
            except Exception as e:
                logger.info(f"  Rate limit hit at {rate} orders/sec: {e}")
                rate_limit_hit = True
                break
        
        result = {
            'max_rate_orders_per_sec': max_rate,
            'rate_limit_hit': rate_limit_hit,
            'recommended_rate': max_rate * 0.8  # 80% of max for safety
        }
        
        logger.info(f"  Max rate: {max_rate} orders/sec")
        logger.info(f"  Recommended: {result['recommended_rate']:.0f} orders/sec")
        
        return result
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
    pass
        """Generate test summary"""
        summary = {
            'overall_status': 'PASS',
            'issues_found': [],
            'recommendations': []
        }
        
        # Check high-frequency test
        if results['high_frequency_orders']['orders_per_second'] < 10:
            summary['issues_found'].append("Low order throughput (< 10 orders/sec)")
            summary['overall_status'] = 'FAIL'
        
        # Check concurrent test
        if results['concurrent_orders']['success_rate'] < 0.95:
            summary['issues_found'].append("Low concurrent success rate (< 95%)")
            summary['overall_status'] = 'FAIL'
        
        # Check data throughput
        if results['data_throughput']['avg_latency_ms'] > 100:
            summary['issues_found'].append("High data latency (> 100ms)")
            summary['recommendations'].append("Optimize data pipeline")
        
        # Check memory leak
        if results['memory_leak']['leak_detected']:
            summary['issues_found'].append("Potential memory leak detected")
            summary['recommendations'].append("Review object lifecycle and cleanup")
        
        # Add recommendations
        if results['rate_limits']['rate_limit_hit']:
            summary['recommendations'].append(
                f"Limit order rate to {results['rate_limits']['recommended_rate']:.0f} orders/sec"
            )
        
        return summary


# Export
__all__ = ['LoadTestSuite']
