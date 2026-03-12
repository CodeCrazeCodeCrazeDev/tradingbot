"""
Performance Optimization Script

Optimizes network latency and memory usage to ensure optimal bot performance.
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run performance optimization"""
    print("\n" + "="*70)
    print("  ALPHAALGO PERFORMANCE OPTIMIZATION")
    print("="*70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Import optimizers
    try:
        from trading_bot.infrastructure.network_optimizer import (
            get_network_optimizer,
            measure_endpoint_latency
        )
        from trading_bot.infrastructure.memory_optimizer import (
            get_memory_optimizer,
            optimize_memory_now
        )
        print("[OK] Optimizers imported successfully\n")
    except Exception as e:
        print(f"[ERROR] Failed to import optimizers: {e}\n")
        return 1
    
    # 1. Memory Optimization
    print("="*70)
    print("  1. MEMORY OPTIMIZATION")
    print("="*70)
    
    try:
        memory_opt = get_memory_optimizer({
            'min_free_memory_mb': 500,
            'enable_aggressive_gc': True
        })
        
        # Get current stats
        before_stats = memory_opt.get_memory_stats()
        print(f"\nBefore Optimization:")
        print(f"  Process Memory: {before_stats['current_usage_mb']:.1f} MB")
        print(f"  Available Memory: {before_stats['available_mb']:.1f} MB")
        print(f"  System Usage: {before_stats['system_percent']:.1f}%")
        
        # Optimize
        print(f"\nOptimizing memory...")
        result = optimize_memory_now()
        
        print(f"\nAfter Optimization:")
        print(f"  Freed: {result['freed_mb']:.1f} MB")
        print(f"  Objects Collected: {result['objects_collected']}")
        print(f"  Final Memory: {result['after_mb']:.1f} MB")
        
        # Recommendations
        recommendations = memory_opt.get_optimization_recommendations()
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
        else:
            print(f"\n[SUCCESS] Memory usage is optimal!")
        
    except Exception as e:
        print(f"[ERROR] Memory optimization failed: {e}")
    
    # 2. Network Optimization
    print("\n" + "="*70)
    print("  2. NETWORK OPTIMIZATION")
    print("="*70)
    
    try:
        network_opt = get_network_optimizer({
            'max_latency_ms': 100,
            'connection_pool_size': 20,
            'enable_compression': True,
            'enable_keepalive': True
        })
        
        # Test endpoints
        test_endpoints = [
            ('google.com', 443),
            ('cloudflare.com', 443),
        ]
        
        print(f"\nTesting network latency...")
        for host, port in test_endpoints:
            latency = network_opt.measure_latency(host, port)
            status = "[OK]" if latency < 100 else "[WARNING]"
            print(f"  {status} {host}:{port} - {latency:.1f}ms")
        
        # Get stats
        stats = network_opt.get_latency_stats()
        if stats:
            print(f"\nLatency Statistics:")
            for host, stat in stats.items():
                status = "[OK]" if stat['acceptable'] else "[WARNING]"
                print(f"  {status} {host}: Avg={stat['avg_ms']:.1f}ms, "
                      f"Min={stat['min_ms']:.1f}ms, Max={stat['max_ms']:.1f}ms")
        
        # Recommendations
        recommendations = network_opt.get_optimization_recommendations()
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
        else:
            print(f"\n[SUCCESS] Network latency is optimal!")
        
    except Exception as e:
        print(f"[ERROR] Network optimization failed: {e}")
    
    # 3. Final Status
    print("\n" + "="*70)
    print("  3. FINAL STATUS")
    print("="*70)
    
    try:
        # Memory check
        final_memory = memory_opt.get_memory_stats()
        memory_ok = final_memory['available_mb'] > 500
        memory_status = "[OK]" if memory_ok else "[WARNING]"
        print(f"\n{memory_status} Memory: {final_memory['available_mb']:.0f}MB available "
              f"(target: >500MB)")
        
        # Network check
        avg_latencies = [
            stat['avg_ms'] for stat in network_opt.get_latency_stats().values()
        ]
        if avg_latencies:
            avg_latency = sum(avg_latencies) / len(avg_latencies)
            latency_ok = avg_latency < 100
            latency_status = "[OK]" if latency_ok else "[WARNING]"
            print(f"{latency_status} Network: {avg_latency:.1f}ms average latency "
                  f"(target: <100ms)")
        else:
            latency_ok = True
            print(f"[OK] Network: No latency issues detected")
        
        # Overall status
        print("\n" + "="*70)
        if memory_ok and latency_ok:
            print("  [SUCCESS] PERFORMANCE OPTIMIZED!")
            print("  All metrics within acceptable ranges")
            print("\n  Status: PRODUCTION READY")
            exit_code = 0
        else:
            print("  [WARNING] Some metrics need attention")
            print("  Review recommendations above")
            exit_code = 1
        
        print("="*70 + "\n")
        return exit_code
        
    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
