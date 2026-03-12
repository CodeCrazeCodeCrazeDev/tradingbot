#!/usr/bin/env python3
"""
Performance Benchmark Runner
============================
Runs comprehensive performance benchmarks and generates reports.
"""

import sys
import os
import time
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, asdict
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    p50_time: float
    p95_time: float
    p99_time: float
    throughput: float
    passed: bool
    threshold: float
    error: str = None


class BenchmarkRunner:
    """Runs performance benchmarks."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
    
    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 1000,
        warmup: int = 10,
        threshold_ms: float = 10.0,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        print(f"\n  Running: {name}...")
        
        # Warmup
        for _ in range(warmup):
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        
        # Benchmark
        times = []
        errors = []
        
        for i in range(iterations):
            try:
                start = time.perf_counter()
                func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                times.append(elapsed)
            except Exception as e:
                errors.append(str(e))
        
        if not times:
            return BenchmarkResult(
                name=name,
                iterations=iterations,
                total_time=0,
                avg_time=0,
                min_time=0,
                max_time=0,
                p50_time=0,
                p95_time=0,
                p99_time=0,
                throughput=0,
                passed=False,
                threshold=threshold_ms,
                error=errors[0] if errors else "No successful runs"
            )
        
        sorted_times = sorted(times)
        avg_time = statistics.mean(times) * 1000  # Convert to ms
        
        result = BenchmarkResult(
            name=name,
            iterations=len(times),
            total_time=sum(times),
            avg_time=avg_time,
            min_time=min(times) * 1000,
            max_time=max(times) * 1000,
            p50_time=sorted_times[int(len(sorted_times) * 0.5)] * 1000,
            p95_time=sorted_times[int(len(sorted_times) * 0.95)] * 1000,
            p99_time=sorted_times[int(len(sorted_times) * 0.99)] * 1000,
            throughput=len(times) / sum(times) if sum(times) > 0 else 0,
            passed=avg_time < threshold_ms,
            threshold=threshold_ms
        )
        
        self.results.append(result)
        
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"    {status} | Avg: {result.avg_time:.3f}ms | P95: {result.p95_time:.3f}ms | Throughput: {result.throughput:.0f}/s")
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate benchmark report."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_benchmarks': total,
                'passed': passed,
                'failed': total - passed,
                'pass_rate': f"{100 * passed / total:.1f}%" if total > 0 else "N/A"
            },
            'results': [asdict(r) for r in self.results]
        }
        
        # Save report
        report_file = self.output_dir / f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Report saved to: {report_file}")
        
        return report


def run_all_benchmarks():
    """Run all performance benchmarks."""
    print("=" * 70)
    print("ALPHAALGO PERFORMANCE BENCHMARKS")
    print("=" * 70)
    
    runner = BenchmarkRunner()
    
    # ========================================================================
    # RISK MANAGER BENCHMARKS
    # ========================================================================
    print("\n[1] Risk Manager Benchmarks")
    print("-" * 40)
    
    try:
        from trading_bot.risk.MASTER_risk_manager import MasterRiskManager, TradeDirection
        risk_manager = MasterRiskManager()
        
        runner.run_benchmark(
            name="Position Size Calculation",
            func=lambda: risk_manager.calculate_position_size(
                symbol='EURUSD',
                stop_loss_pips=50,
                direction=TradeDirection.LONG,
                confidence=0.8
            ),
            iterations=1000,
            threshold_ms=10.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # EXECUTION ENGINE BENCHMARKS
    # ========================================================================
    print("\n[2] Execution Engine Benchmarks")
    print("-" * 40)
    
    try:
        from trading_bot.execution.advanced_algorithms import (
            TWAPExecutor, VWAPExecutor, ExecutionAlgorithm, OrderSide
        )
        from trading_bot.execution import ExecutionEngine
        
        twap = TWAPExecutor()
        vwap = VWAPExecutor()
        engine = ExecutionEngine()
        
        runner.run_benchmark(
            name="TWAP Plan Creation",
            func=lambda: twap.create_plan(
                symbol='EURUSD',
                side=OrderSide.BUY,
                quantity=1000,
                duration_seconds=60
            ),
            iterations=500,
            threshold_ms=20.0
        )
        
        runner.run_benchmark(
            name="VWAP Plan Creation",
            func=lambda: vwap.create_plan(
                symbol='EURUSD',
                side=OrderSide.SELL,
                quantity=1000,
                duration_seconds=60
            ),
            iterations=500,
            threshold_ms=20.0
        )
        
        runner.run_benchmark(
            name="Execution Engine Plan Creation",
            func=lambda: engine.create_plan(
                algorithm=ExecutionAlgorithm.TWAP,
                symbol='EURUSD',
                side=OrderSide.BUY,
                quantity=1000,
                duration_seconds=60
            ),
            iterations=500,
            threshold_ms=25.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # DATA PROCESSING BENCHMARKS
    # ========================================================================
    print("\n[3] Data Processing Benchmarks")
    print("-" * 40)
    
    try:
        import numpy as np
        import pandas as pd
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=1000, freq='h')
        prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices - np.random.rand(1000) * 0.3,
            'high': prices + np.random.rand(1000) * 0.5,
            'low': prices - np.random.rand(1000) * 0.5,
            'close': prices,
            'volume': np.random.randint(1000, 100000, 1000)
        })
        
        def process_ohlcv():
            data = df.copy()
            data['returns'] = data['close'].pct_change()
            data['sma_20'] = data['close'].rolling(20).mean()
            data['sma_50'] = data['close'].rolling(50).mean()
            data['volatility'] = data['returns'].rolling(20).std()
            return data
        
        runner.run_benchmark(
            name="OHLCV Processing (1000 bars)",
            func=process_ohlcv,
            iterations=100,
            threshold_ms=100.0
        )
        
        # Large dataset
        large_df = pd.DataFrame({
            'timestamp': pd.date_range(start='2020-01-01', periods=100000, freq='min'),
            'close': np.random.randn(100000) * 100 + 1000,
            'volume': np.random.randint(1000, 100000, 100000)
        })
        
        def process_large_dataset():
            data = large_df.copy()
            data['returns'] = data['close'].pct_change()
            data['sma'] = data['close'].rolling(100).mean()
            return data
        
        runner.run_benchmark(
            name="Large Dataset Processing (100k rows)",
            func=process_large_dataset,
            iterations=20,
            threshold_ms=500.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # SIGNAL SYSTEM BENCHMARKS
    # ========================================================================
    print("\n[4] Signal System Benchmarks")
    print("-" * 40)
    
    try:
        from trading_bot.signals import CompleteSignalSystem
        
        runner.run_benchmark(
            name="Signal System Initialization",
            func=lambda: CompleteSignalSystem(),
            iterations=10,
            threshold_ms=500.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # ML PIPELINE BENCHMARKS
    # ========================================================================
    print("\n[5] ML Pipeline Benchmarks")
    print("-" * 40)
    
    try:
        from trading_bot.ml import PricePredictor
        
        runner.run_benchmark(
            name="Price Predictor Initialization",
            func=lambda: PricePredictor(),
            iterations=5,
            threshold_ms=1000.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # MEGA INTEGRATION BENCHMARKS
    # ========================================================================
    print("\n[6] Mega Integration Benchmarks")
    print("-" * 40)
    
    try:
        from trading_bot.mega_integration import MegaIntegration
        
        runner.run_benchmark(
            name="Mega Integration Initialization",
            func=lambda: MegaIntegration(),
            iterations=3,
            threshold_ms=5000.0
        )
    except Exception as e:
        print(f"  Skipped: {e}")
    
    # ========================================================================
    # GENERATE REPORT
    # ========================================================================
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    
    report = runner.generate_report()
    
    print(f"\n  Total Benchmarks: {report['summary']['total_benchmarks']}")
    print(f"  Passed: {report['summary']['passed']}")
    print(f"  Failed: {report['summary']['failed']}")
    print(f"  Pass Rate: {report['summary']['pass_rate']}")
    
    # Print failed benchmarks
    failed = [r for r in runner.results if not r.passed]
    if failed:
        print("\n  Failed Benchmarks:")
        for r in failed:
            print(f"    - {r.name}: {r.avg_time:.3f}ms (threshold: {r.threshold}ms)")
    
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run AlphaAlgo performance benchmarks')
    parser.add_argument('--output', '-o', default='benchmark_results', help='Output directory')
    args = parser.parse_args()
    
    run_all_benchmarks()
