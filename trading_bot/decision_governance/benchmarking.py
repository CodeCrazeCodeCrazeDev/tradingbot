"""
DGS Benchmarking and Load Testing Suite

Performance benchmarking, load testing, and optimization tools for DGS.
"""

import time
import asyncio
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import psutil

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark run"""
    name: str
    iterations: int
    total_time_seconds: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LoadTestResult:
    """Result of a load test"""
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    errors: List[str] = field(default_factory=list)
    latency_distribution: Dict[str, float] = field(default_factory=dict)


class DGSBenchmark:
    """
    Benchmarking suite for DGS performance measurement.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        self.results: List[BenchmarkResult] = []
        
    async def benchmark_decision_latency(
        self,
        iterations: int = 1000,
        warmup_iterations: int = 100
    ) -> BenchmarkResult:
        """
        Benchmark decision evaluation latency.
        
        Measures the end-to-end time for signal evaluation.
        """
        
        # Warmup
        for _ in range(warmup_iterations):
            await self._evaluate_test_signal()
        
        # Benchmark
        latencies = []
        start_time = time.time()
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()
        
        for i in range(iterations):
            iter_start = time.perf_counter()
            await self._evaluate_test_signal()
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)  # Convert to ms
        
        end_time = time.time()
        mem_after = process.memory_info().rss / 1024 / 1024
        cpu_after = process.cpu_percent()
        
        # Calculate statistics
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        result = BenchmarkResult(
            name="decision_latency",
            iterations=iterations,
            total_time_seconds=end_time - start_time,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_latency_ms=sorted_latencies[int(n * 0.5)],
            p95_latency_ms=sorted_latencies[int(n * 0.95)],
            p99_latency_ms=sorted_latencies[int(n * 0.99)],
            throughput_per_second=iterations / (end_time - start_time),
            memory_usage_mb=mem_after - mem_before,
            cpu_usage_percent=cpu_after - cpu_before
        )
        
        self.results.append(result)
        return result
    
    async def _evaluate_test_signal(self) -> None:
        """Evaluate a test signal for benchmarking"""
        signal = {
            'source': 'benchmark',
            'direction': 'buy',
            'confidence': 0.75,
            'size': 1.0,
            'rationale': 'Benchmark test signal',
            'evidence': ['Test evidence']
        }
        
        try:
            await self.dgs.evaluate_trade_signal(
                signal=signal,
                symbol='TEST',
                market_data={'price': 100.0, 'volume': 1000000}
            )
        except Exception as e:
            logger.warning(f"Benchmark signal evaluation error: {e}")
    
    async def benchmark_component_latency(
        self,
        component_name: str,
        component_func: Callable,
        iterations: int = 1000
    ) -> BenchmarkResult:
        """Benchmark a specific component"""
        
        latencies = []
        start_time = time.time()
        
        for _ in range(iterations):
            iter_start = time.perf_counter()
            try:
                await component_func()
            except Exception as e:
                logger.warning(f"Component benchmark error: {e}")
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)
        
        end_time = time.time()
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)
        
        result = BenchmarkResult(
            name=component_name,
            iterations=iterations,
            total_time_seconds=end_time - start_time,
            avg_latency_ms=statistics.mean(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            p50_latency_ms=sorted_latencies[int(n * 0.5)],
            p95_latency_ms=sorted_latencies[int(n * 0.95)],
            p99_latency_ms=sorted_latencies[int(n * 0.99)],
            throughput_per_second=iterations / (end_time - start_time),
            memory_usage_mb=0,
            cpu_usage_percent=0
        )
        
        self.results.append(result)
        return result
    
    async def run_full_benchmark_suite(self) -> Dict[str, BenchmarkResult]:
        """Run complete benchmark suite"""
        
        results = {}
        
        # Benchmark decision latency
        results['decision_latency'] = await self.benchmark_decision_latency(
            iterations=1000
        )
        
        # Benchmark individual components if available
        if hasattr(self.dgs, 'signal_validator'):
            results['signal_validation'] = await self.benchmark_component_latency(
                'signal_validation',
                self._benchmark_signal_validation,
                iterations=1000
            )
        
        if hasattr(self.dgs, 'risk_gatekeeper'):
            results['risk_check'] = await self.benchmark_component_latency(
                'risk_check',
                self._benchmark_risk_check,
                iterations=1000
            )
        
        return results
    
    async def _benchmark_signal_validation(self) -> None:
        """Benchmark signal validation"""
        signal = {
            'source': 'benchmark',
            'direction': 'buy',
            'confidence': 0.75
        }
        self.dgs.signal_validator.validate_signal(signal, 'TEST')
    
    async def _benchmark_risk_check(self) -> None:
        """Benchmark risk check"""
        self.dgs.risk_gatekeeper.check_risk(
            symbol='TEST',
            proposed_direction='buy',
            proposed_size=1.0,
            proposed_price=100.0,
            portfolio_value=10000.0
        )
    
    def generate_benchmark_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        
        if not self.results:
            return {"error": "No benchmark results available"}
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_benchmarks": len(self.results),
            "results": []
        }
        
        for result in self.results:
            report["results"].append({
                "name": result.name,
                "iterations": result.iterations,
                "avg_latency_ms": round(result.avg_latency_ms, 3),
                "p95_latency_ms": round(result.p95_latency_ms, 3),
                "p99_latency_ms": round(result.p99_latency_ms, 3),
                "throughput_per_second": round(result.throughput_per_second, 1),
                "memory_usage_mb": round(result.memory_usage_mb, 2),
                "cpu_usage_percent": round(result.cpu_usage_percent, 2)
            })
        
        # Add recommendations
        report["recommendations"] = self._generate_recommendations()
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on benchmarks"""
        
        recommendations = []
        
        for result in self.results:
            if result.name == "decision_latency":
                if result.p95_latency_ms > 100:
                    recommendations.append(
                        f"Decision latency P95 ({result.p95_latency_ms:.1f}ms) exceeds 100ms target. "
                        "Consider optimizing slow components."
                    )
                
                if result.p99_latency_ms > 200:
                    recommendations.append(
                        f"Decision latency P99 ({result.p99_latency_ms:.1f}ms) exceeds 200ms. "
                        "Investigate tail latency causes."
                    )
            
            if result.memory_usage_mb > 100:
                recommendations.append(
                    f"High memory usage ({result.memory_usage_mb:.1f}MB). "
                    "Consider memory optimization or leak detection."
                )
        
        if not recommendations:
            recommendations.append("All performance metrics within acceptable ranges.")
        
        return recommendations


class DGSLoadTester:
    """
    Load testing suite for DGS.
    Simulates high-throughput trading scenarios.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        
    async def run_load_test(
        self,
        duration_seconds: float = 60.0,
        target_rps: float = 100.0,
        concurrent_requests: int = 10
    ) -> LoadTestResult:
        """
        Run load test against DGS.
        
        Args:
            duration_seconds: How long to run the test
            target_rps: Target requests per second
            concurrent_requests: Number of concurrent requests
        """
        
        latencies = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            async with semaphore:
                try:
                    req_start = time.perf_counter()
                    
                    signal = self._generate_random_signal()
                    await self.dgs.evaluate_trade_signal(
                        signal=signal,
                        symbol=signal['symbol'],
                        market_data={'price': 100.0, 'volume': 1000000}
                    )
                    
                    req_end = time.perf_counter()
                    latency = (req_end - req_start) * 1000
                    
                    return {'success': True, 'latency': latency}
                    
                except Exception as e:
                    return {'success': False, 'error': str(e)}
        
        # Calculate delay between requests to achieve target RPS
        delay = 1.0 / target_rps if target_rps > 0 else 0
        
        tasks = []
        request_count = 0
        
        while time.time() - start_time < duration_seconds:
            task = asyncio.create_task(make_request())
            tasks.append(task)
            request_count += 1
            
            # Throttle to target RPS
            if delay > 0:
                await asyncio.sleep(delay)
        
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                errors.append(str(result))
            elif result.get('success'):
                successful += 1
                latencies.append(result['latency'])
            else:
                failed += 1
                errors.append(result.get('error', 'Unknown error'))
        
        # Calculate latency distribution
        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            latency_dist = {
                'p50': sorted_latencies[int(n * 0.5)],
                'p75': sorted_latencies[int(n * 0.75)],
                'p90': sorted_latencies[int(n * 0.90)],
                'p95': sorted_latencies[int(n * 0.95)],
                'p99': sorted_latencies[int(n * 0.99)]
            }
        else:
            latency_dist = {}
        
        return LoadTestResult(
            duration_seconds=end_time - start_time,
            total_requests=request_count,
            successful_requests=successful,
            failed_requests=failed,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p95_latency_ms=latency_dist.get('p95', 0),
            p99_latency_ms=latency_dist.get('p99', 0),
            errors=list(set(errors))[:10],  # Unique errors, limit to 10
            latency_distribution=latency_dist
        )
    
    def _generate_random_signal(self) -> Dict[str, Any]:
        """Generate random test signal"""
        import random
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        directions = ['buy', 'sell']
        
        return {
            'source': 'load_test',
            'symbol': random.choice(symbols),
            'direction': random.choice(directions),
            'confidence': random.uniform(0.5, 0.9),
            'size': random.uniform(0.5, 2.0),
            'timestamp': datetime.utcnow(),
            'rationale': 'Load test signal',
            'evidence': ['Test evidence 1', 'Test evidence 2']
        }
    
    def generate_load_test_report(self, result: LoadTestResult) -> Dict[str, Any]:
        """Generate load test report"""
        
        success_rate = result.successful_requests / result.total_requests if result.total_requests > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": result.duration_seconds,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "failed_requests": result.failed_requests,
            "success_rate": f"{success_rate:.1%}",
            "throughput_rps": result.total_requests / result.duration_seconds,
            "latency_ms": {
                "average": round(result.avg_latency_ms, 2),
                "p95": round(result.p95_latency_ms, 2),
                "p99": round(result.p99_latency_ms, 2),
                "distribution": {k: round(v, 2) for k, v in result.latency_distribution.items()}
            },
            "errors": result.errors,
            "status": "PASS" if success_rate > 0.95 and result.p95_latency_ms < 200 else "FAIL"
        }


class PerformanceOptimizer:
    """
    Performance optimization tools for DGS.
    Identifies bottlenecks and suggests optimizations.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        self.bottlenecks: List[Dict] = []
        
    def analyze_performance(self, benchmark_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze performance and identify bottlenecks"""
        
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "bottlenecks": [],
            "recommendations": [],
            "component_breakdown": {}
        }
        
        # Identify slow components
        for result in benchmark_results:
            analysis["component_breakdown"][result.name] = {
                "avg_latency_ms": result.avg_latency_ms,
                "p95_latency_ms": result.p95_latency_ms,
                "percentage_of_total": 0  # Will calculate below
            }
        
        # Find bottlenecks (components > 50% of total latency)
        total_latency = sum(r.avg_latency_ms for r in benchmark_results)
        
        for result in benchmark_results:
            percentage = (result.avg_latency_ms / total_latency) * 100 if total_latency > 0 else 0
            analysis["component_breakdown"][result.name]["percentage_of_total"] = percentage
            
            if percentage > 50:
                analysis["bottlenecks"].append({
                    "component": result.name,
                    "latency_ms": result.avg_latency_ms,
                    "percentage": percentage,
                    "severity": "HIGH" if percentage > 70 else "MEDIUM"
                })
        
        # Generate optimization recommendations
        analysis["recommendations"] = self._generate_optimization_recommendations(
            analysis["bottlenecks"]
        )
        
        return analysis
    
    def _generate_optimization_recommendations(
        self,
        bottlenecks: List[Dict]
    ) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        for bottleneck in bottlenecks:
            component = bottleneck["component"]
            
            if component == "signal_validation":
                recommendations.append(
                    "Signal validation is a bottleneck. Consider: "
                    "1) Caching validation results, 2) Parallel validation checks, "
                    "3) Simplifying validation rules"
                )
            
            elif component == "risk_check":
                recommendations.append(
                    "Risk checking is slow. Consider: "
                    "1) Pre-calculating risk metrics, 2) Using approximate calculations, "
                    "3) Caching portfolio risk state"
                )
            
            elif component == "evidence_auditing":
                recommendations.append(
                    "Evidence auditing is a bottleneck. Consider: "
                    "1) Reducing evidence requirements, 2) Async evidence fetching, "
                    "3) Sampling-based evidence checks"
                )
            
            elif component == "adversarial_analysis":
                recommendations.append(
                    "Adversarial analysis is slow. Consider: "
                    "1) Reducing adversarial depth, 2) Caching common challenges, "
                    "3) Selective adversarial analysis for high-confidence signals"
                )
        
        if not recommendations:
            recommendations.append(
                "No major bottlenecks detected. System performance is acceptable."
            )
        
        return recommendations
    
    def suggest_caching_strategy(self) -> Dict[str, Any]:
        """Suggest caching strategy based on usage patterns"""
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_recommendations": [
                {
                    "component": "signal_validation",
                    "cache_type": "LRU",
                    "ttl_seconds": 60,
                    "rationale": "Signal validation results stable for short periods"
                },
                {
                    "component": "risk_metrics",
                    "cache_type": "TTL",
                    "ttl_seconds": 30,
                    "rationale": "Risk metrics update frequently but not instantly"
                },
                {
                    "component": "regime_classification",
                    "cache_type": "LRU",
                    "ttl_seconds": 300,
                    "rationale": "Regime changes are relatively slow"
                },
                {
                    "component": "historical_patterns",
                    "cache_type": "Persistent",
                    "ttl_seconds": 3600,
                    "rationale": "Historical patterns rarely change"
                }
            ]
        }
