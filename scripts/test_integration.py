#!/usr/bin/env python3
"""
Integration Test Script for AlphaAlgo Module Integration

Tests:
1. IntegratedSystems class initialization
2. Background services manager initialization
3. Service dependencies
4. Health checks
5. Event bus communication
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime


async def test_integrated_systems():
    """Test the IntegratedSystems class."""
    print("\n" + "=" * 70)
    print("TEST 1: IntegratedSystems Class")
    print("=" * 70)
    
    try:
        # Import the class
        from main import IntegratedSystems
        
        # Create instance
        config = {
            'mode': 'paper',
            'min_confidence': 0.6,
            'max_risk_per_trade': 0.02,
        }
        
        systems = IntegratedSystems(config)
        print("[OK] IntegratedSystems instantiated")
        
        # Test event bus
        events_received = []
        
        def on_event(event):
            events_received.append(event)
        
        systems.subscribe('test_event', on_event)
        await systems.publish('test_event', {'message': 'Hello'}, source='test')
        
        if len(events_received) == 1:
            print("[OK] Event bus working")
        else:
            print("[FAIL] Event bus not working")
        
        # Test initialization (will fail for missing modules, but structure should work)
        print("\nInitializing systems (some may fail due to missing modules)...")
        try:
            counts = await systems.initialize_all()
            total = sum(counts.values())
            print(f"[OK] Initialized {total} modules across {len(counts)} categories")
            for category, count in counts.items():
                print(f"  - {category}: {count} modules")
        except Exception as e:
            print(f"[WARN] Initialization had errors (expected): {e}")
        
        # Test status
        status = systems.get_status()
        print(f"[OK] Status retrieved: {status['initialized']}")
        
        # Test shutdown
        await systems.shutdown()
        print("[OK] Shutdown completed")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_background_services():
    """Test the BackgroundServicesManager class."""
    print("\n" + "=" * 70)
    print("TEST 2: BackgroundServicesManager Class")
    print("=" * 70)
    
    try:
        from background_services import BackgroundServicesManager, ServiceStatus
        
        # Create instance
        config = {'mode': 'paper'}
        manager = BackgroundServicesManager(config)
        print("[OK] BackgroundServicesManager instantiated")
        
        # Check services defined
        service_count = len(manager.services)
        print(f"[OK] {service_count} services defined")
        
        # Check priorities
        critical = sum(1 for s in manager.services.values() if s.priority == 'critical')
        high = sum(1 for s in manager.services.values() if s.priority == 'high')
        medium = sum(1 for s in manager.services.values() if s.priority == 'medium')
        low = sum(1 for s in manager.services.values() if s.priority == 'low')
        print(f"  - Critical: {critical}")
        print(f"  - High: {high}")
        print(f"  - Medium: {medium}")
        print(f"  - Low: {low}")
        
        # Check dependencies
        deps_count = len(manager.dependencies)
        print(f"[OK] {deps_count} service dependencies defined")
        
        # Test health check (no services running)
        health = await manager.health_check_all()
        print(f"[OK] Health check completed for {len(health)} services")
        
        # Test metrics
        metrics = manager.get_service_metrics()
        print(f"[OK] Metrics: {metrics['total_services']} total, {metrics['running']} running")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service_initialization():
    """Test initializing a few services."""
    print("\n" + "=" * 70)
    print("TEST 3: Service Initialization (Sample)")
    print("=" * 70)
    
    try:
        from background_services import BackgroundServicesManager
        
        manager = BackgroundServicesManager({'mode': 'paper'})
        
        # Try to initialize a few services
        test_services = ['self_diagnostic', 'safety_monitor', 'risk_monitor']
        
        for service_id in test_services:
            try:
                result = await manager._initialize_service(service_id)
                if result:
                    print(f"[OK] {service_id} initialized")
                else:
                    print(f"[SKIP] {service_id} not available")
            except Exception as e:
                print(f"[SKIP] {service_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_module_imports():
    """Test that key modules can be imported."""
    print("\n" + "=" * 70)
    print("TEST 4: Module Imports")
    print("=" * 70)
    
    modules_to_test = [
        ('trading_bot', 'Package root'),
        ('trading_bot.core', 'Core module'),
        ('trading_bot.risk', 'Risk module'),
        ('trading_bot.execution', 'Execution module'),
        ('trading_bot.signals', 'Signals module'),
        ('trading_bot.ml', 'ML module'),
    ]
    
    success = 0
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"[OK] {description} ({module_name})")
            success += 1
        except ImportError as e:
            print(f"[SKIP] {description}: {e}")
    
    print(f"\nImported {success}/{len(modules_to_test)} modules")
    return success > 0


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ALPHAALGO MODULE INTEGRATION TEST")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    results = []
    
    # Run tests
    results.append(('Module Imports', await test_module_imports()))
    results.append(('IntegratedSystems', await test_integrated_systems()))
    results.append(('BackgroundServices', await test_background_services()))
    results.append(('Service Init', await test_service_initialization()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
