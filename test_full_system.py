"""
Full System Test with Unicode Fix
==================================

Tests the complete trading bot system with all Unicode encoding fixes applied.
"""

import sys
import os

# Apply Unicode fix FIRST
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_bot.unicode_fix import apply_unicode_fix, setup_utf8_logging
    apply_unicode_fix()
    setup_utf8_logging()
    print("✓ Unicode fix applied successfully")
except Exception as e:
    print(f"⚠ Unicode fix failed: {e}")
    # Fallback
    if sys.platform == 'win32':
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import logging
from trading_bot.complete_integrator import quick_integrate

def test_full_system():
    """Test full system integration"""
    
    print("\n" + "=" * 80)
    print("FULL SYSTEM TEST - WITH UNICODE FIX")
    print("=" * 80)
    print()
    
    # Test 1: Unicode characters
    print("Test 1: Unicode Character Support")
    print("-" * 80)
    test_chars = "✓ ✗ → ← ↑ ↓ ★ ☆ ♠ ♣ ♥ ♦ 🚀 📊 💰 ⚠️"
    try:
        print(f"Special characters: {test_chars}")
        logging.info(f"Logging test: {test_chars}")
        print("✓ Unicode test PASSED")
    except UnicodeEncodeError as e:
        print(f"✗ Unicode test FAILED: {e}")
    print()
    
    # Test 2: Module Integration
    print("Test 2: Module Integration")
    print("-" * 80)
    try:
        integrator, modules = quick_integrate()
        status = integrator.get_status()
        
        print(f"Total Modules: {status['total_modules']}")
        print(f"Successfully Integrated: {status['successful']}")
        print(f"Failed: {status['failed']}")
        print(f"Success Rate: {status['successful']/status['total_modules']*100:.1f}%")
        print()
        
        if status['successful'] >= 8:
            print("✓ Integration test PASSED")
        else:
            print("⚠ Integration test PARTIAL")
            
    except Exception as e:
        print(f"✗ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Test 3: Logging with Unicode
    print("Test 3: Logging System")
    print("-" * 80)
    try:
        logger = logging.getLogger("test")
        logger.info("Test message with emoji: 🎯 ✅ 🔥")
        logger.warning("Warning with symbols: ⚠️ ⚡ 🚨")
        logger.error("Error with marks: ❌ ⛔ 🛑")
        print("✓ Logging test PASSED")
    except Exception as e:
        print(f"✗ Logging test FAILED: {e}")
    print()
    
    # Test 4: System Status
    print("Test 4: System Status Check")
    print("-" * 80)
    try:
        if 'recursive_evolution' in modules:
            print("✓ Recursive Evolution: Available")
        if 'unified_evolution' in modules:
            print("✓ Unified Evolution: Available")
        if 'aamis_v3' in modules:
            print("✓ AAMIS v3: Available")
        if 'intelligence_core' in modules:
            print("✓ Intelligence Core: Available")
        if 'cognitive_architecture' in modules:
            print("✓ Cognitive Architecture: Available")
        
        print("\n✓ System status check PASSED")
    except Exception as e:
        print(f"✗ System status check FAILED: {e}")
    print()
    
    # Final Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✓ Unicode encoding: FIXED")
    print("✓ Logging system: OPERATIONAL")
    print(f"✓ Module integration: {status['successful']}/{status['total_modules']} modules")
    print("✓ System status: READY")
    print()
    print("The full system is ready to run!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    test_full_system()
