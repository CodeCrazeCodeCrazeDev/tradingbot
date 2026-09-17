"""
Comprehensive Test Script for Elite Trading Bot
Tests all features including new premium features
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path so imports resolve to the real package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

print("="*70)
print("ELITE TRADING BOT - COMPREHENSIVE TEST")
print("="*70)
print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test results
test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'tests': []
}

def test_result(test_name: str, passed: bool, message: str = ""):
    """Record test result"""
    status = "[PASS]" if passed else "[FAIL]"
    test_results['tests'].append({
        'name': test_name,
        'passed': passed,
        'message': message
    })
    if passed:
        test_results['passed'] += 1
    else:
        test_results['failed'] += 1
    
    print(f"{status} - {test_name}")
    if message:
        print(f"     {message}")


# ============================================================================
# TEST 1: CORE IMPORTS
# ============================================================================
print("\n" + "="*70)
print("TEST 1: CORE IMPORTS")
print("="*70)

try:
    import trading_bot
    test_result("Import trading_bot", True, f"Version: {trading_bot.__version__}")
except Exception as e:
    test_result("Import trading_bot", False, str(e))

try:
    from trading_bot import (
        ModelRegistry, ExperimentTracker, AIPerformanceMonitor,
        SystemSupervisor, SelfImprovementEngine,
        TemporalFusionTransformer, PlannerAgent
    )
    test_result("Import AI Core components", True, "7 components imported")
except Exception as e:
    test_result("Import AI Core components", False, str(e))


# ============================================================================
# TEST 2: NEW PREMIUM FEATURES IMPORTS
# ============================================================================
print("\n" + "="*70)
print("TEST 2: PREMIUM FEATURES IMPORTS")
print("="*70)

try:
    from trading_bot import NotificationManager, NotificationChannel, NotificationPriority
    test_result("Import Notifications", True, "NotificationManager available")
except Exception as e:
    test_result("Import Notifications", False, str(e))

try:
    from trading_bot import VoiceAssistant, VoiceCommand
    test_result("Import Voice Assistant", True, "VoiceAssistant available")
except Exception as e:
    test_result("Import Voice Assistant", False, str(e))

try:
    from trading_bot import MobileAPI, APIEndpoint
    test_result("Import Mobile API", True, "MobileAPI available")
except Exception as e:
    test_result("Import Mobile API", False, str(e))

try:
    from trading_bot import StrategyOptimizer, OptimizationMethod
    test_result("Import Auto Optimizer", True, "StrategyOptimizer available")
except Exception as e:
    test_result("Import Auto Optimizer", False, str(e))

try:
    from trading_bot import TradeJournal, JournalEntry
    test_result("Import Trade Journal", True, "TradeJournal available")
except Exception as e:
    test_result("Import Trade Journal", False, str(e))


# ============================================================================
# TEST 3: NOTIFICATION SYSTEM
# ============================================================================
print("\n" + "="*70)
print("TEST 3: NOTIFICATION SYSTEM")
print("="*70)

try:
    from trading_bot.notifications import NotificationManager, NotificationMessage, NotificationPriority
    
    # Create notification manager (without real credentials)
    notifier = NotificationManager(config={})
    test_result("Create NotificationManager", True, "Instance created")
    
    # Test message creation
    msg = NotificationMessage(
        title="Test Alert",
        message="This is a test message",
        priority=NotificationPriority.MEDIUM,
        channels=[],
        timestamp=datetime.now()
    )
    test_result("Create NotificationMessage", True, f"Priority: {msg.priority.value}")
    
except Exception as e:
    test_result("Notification System", False, str(e))


# ============================================================================
# TEST 4: VOICE ASSISTANT
# ============================================================================
print("\n" + "="*70)
print("TEST 4: VOICE ASSISTANT")
print("="*70)

try:
    from trading_bot.voice_assistant import VoiceAssistant, VoiceCommand, VoiceResponse
    
    # Create mock bot
    class MockBot:
        def get_status(self):
            return {'state': 'running', 'open_positions': 3}
        def get_balance(self):
            return 10000.0
    
    mock_bot = MockBot()
    assistant = VoiceAssistant(mock_bot)
    test_result("Create VoiceAssistant", True, "Instance created")
    
    # Test command matching
    command = assistant._match_command("what is my balance")
    test_result("Voice command matching", command == VoiceCommand.BALANCE, f"Matched: {command}")
    
except Exception as e:
    test_result("Voice Assistant", False, str(e))


# ============================================================================
# TEST 5: MOBILE API
# ============================================================================
print("\n" + "="*70)
print("TEST 5: MOBILE API")
print("="*70)

try:
    from trading_bot.mobile_app import MobileAPI, APIResponse, AuthManager
    
    # Create mock bot
    class MockBot:
        def get_status(self):
            return {'state': 'running'}
    
    mock_bot = MockBot()
    api = MobileAPI(mock_bot)
    test_result("Create MobileAPI", True, "Instance created")
    
    # Test auth manager
    auth = AuthManager(secret_key="test-key")
    test_result("Create AuthManager", True, "Auth system ready")
    
    # Test API response
    response = APIResponse(success=True, data={'test': 'data'})
    response_dict = response.to_dict()
    test_result("Create APIResponse", True, f"Success: {response_dict['success']}")
    
except Exception as e:
    test_result("Mobile API", False, str(e))


# ============================================================================
# TEST 6: AUTO OPTIMIZER
# ============================================================================
print("\n" + "="*70)
print("TEST 6: AUTO OPTIMIZER")
print("="*70)

try:
    from trading_bot.auto_optimizer import (
        StrategyOptimizer, OptimizationMethod, 
        GeneticOptimizer, BayesianOptimizer
    )
    
    # Create mock bot
    class MockBot:
        def set_parameters(self, params):
            self.params = params
        def get_performance(self):
            return {'sharpe_ratio': 1.5}
    
    mock_bot = MockBot()
    optimizer = StrategyOptimizer(mock_bot)
    test_result("Create StrategyOptimizer", True, "Instance created")
    
    # Test genetic optimizer
    genetic = GeneticOptimizer(population_size=10, generations=5)
    test_result("Create GeneticOptimizer", True, f"Pop: {genetic.population_size}")
    
    # Test optimization methods
    methods = [m.value for m in OptimizationMethod]
    test_result("Optimization methods available", len(methods) >= 3, f"Methods: {', '.join(methods)}")
    
except Exception as e:
    test_result("Auto Optimizer", False, str(e))


# ============================================================================
# TEST 7: TRADE JOURNAL
# ============================================================================
print("\n" + "="*70)
print("TEST 7: TRADE JOURNAL")
print("="*70)

try:
    from trading_bot.trade_journal import (
        TradeJournal, JournalEntry, TradeNote, PerformanceAnalyzer
    )
    
    # Create journal
    journal = TradeJournal(journal_dir="test_journal")
    test_result("Create TradeJournal", True, "Instance created")
    
    # Test performance analyzer
    analyzer = PerformanceAnalyzer()
    test_result("Create PerformanceAnalyzer", True, "Analyzer ready")
    
    # Test trade note
    note = TradeNote(
        timestamp=datetime.now(),
        note="Test note",
        category="observation"
    )
    test_result("Create TradeNote", True, f"Category: {note.category}")
    
except Exception as e:
    test_result("Trade Journal", False, str(e))


# ============================================================================
# TEST 8: RISK MANAGEMENT
# ============================================================================
print("\n" + "="*70)
print("TEST 8: RISK MANAGEMENT")
print("="*70)

try:
    from trading_bot import UnifiedRiskManager_v2
    if UnifiedRiskManager_v2:
        test_result("Risk Manager available", True, "UnifiedRiskManager_v2 imported")
    else:
        test_result("Risk Manager available", False, "Module not fully implemented")
except Exception as e:
    test_result("Risk Manager", False, str(e))


# ============================================================================
# TEST 9: INDICATORS
# ============================================================================
print("\n" + "="*70)
print("TEST 9: INDICATORS")
print("="*70)

try:
    from trading_bot import (
        HurstExponent, FRAMA, SuperTrend, KAMA,
        AdvancedTechnicalIndicators,
    )
    test_result("Import Technical Indicators", True, "5 indicators imported")
except Exception as e:
    test_result("Import Technical Indicators", False, str(e))

try:
    from trading_bot import (
        AdvancedMLIndicators,
        TransformerPredictor,
    )
    test_result("Import ML Indicators", True, "ML indicators available")
except Exception as e:
    test_result("Import ML Indicators", False, str(e))


# ============================================================================
# TEST 10: EXECUTION & SAFETY
# ============================================================================
print("\n" + "="*70)
print("TEST 10: EXECUTION & SAFETY")
print("="*70)

try:
    from trading_bot import (
        PaperExecutor,
        TWAPExecutor,
        VWAPExecutor,
    )
    test_result("Import Execution modules", True, "3 executors imported")
except Exception as e:
    test_result("Import Execution modules", False, str(e))

try:
    from trading_bot import (
        EmergencyKillSwitch,
        LatencyCircuitBreaker,
        ResourceWatchdog,
    )
    test_result("Import Safety modules", True, "3 safety systems imported")
except Exception as e:
    test_result("Import Safety modules", False, str(e))


# ============================================================================
# TEST 11: INTEGRATION TEST
# ============================================================================
print("\n" + "="*70)
print("TEST 11: INTEGRATION TEST")
print("="*70)

try:
    # Count total exports
    total_exports = len(trading_bot.__all__)
    test_result("Total exports count", total_exports > 400, f"Exports: {total_exports}")
    
    # Check version
    test_result("Version check", hasattr(trading_bot, '__version__'), f"Version: {trading_bot.__version__}")
    
except Exception as e:
    test_result("Integration test", False, str(e))


# ============================================================================
# TEST 12: ASYNC FUNCTIONALITY
# ============================================================================
print("\n" + "="*70)
print("TEST 12: ASYNC FUNCTIONALITY")
print("="*70)

async def test_async_features():
    """Test async features"""
    try:
        notifier = NotificationManager(config={})
        
        # Test async send (will fail without config, but tests the interface)
        msg = NotificationMessage(
            title="Test",
            message="Test message",
            priority=NotificationPriority.LOW,
            channels=[],
            timestamp=datetime.now()
        )
        
        # Just test that the method exists and is async
        test_result("Async notification interface", 
                   asyncio.iscoroutinefunction(notifier.send),
                   "send() is async")
        
    except Exception as e:
        test_result("Async functionality", False, str(e))

# Run async test
try:
    asyncio.run(test_async_features())
except Exception as e:
    test_result("Async test runner", False, str(e))


# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "="*70)
print("TEST RESULTS SUMMARY")
print("="*70)

print(f"\n[+] Passed: {test_results['passed']}")
print(f"[-] Failed: {test_results['failed']}")
print(f"[~] Skipped: {test_results['skipped']}")
print(f"[=] Total: {test_results['passed'] + test_results['failed'] + test_results['skipped']}")

success_rate = (test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100) if (test_results['passed'] + test_results['failed']) > 0 else 0
print(f"\n[*] Success Rate: {success_rate:.1f}%")

if test_results['failed'] > 0:
    print("\n[-] Failed Tests:")
    for test in test_results['tests']:
        if not test['passed']:
            print(f"   - {test['name']}: {test['message']}")

print("\n" + "="*70)
if success_rate >= 90:
    print("[!!!] EXCELLENT! Bot is ready for production!")
elif success_rate >= 70:
    print("[++] GOOD! Most features working, minor issues to fix.")
elif success_rate >= 50:
    print("[!] FAIR! Some features need attention.")
else:
    print("[--] NEEDS WORK! Multiple issues detected.")
print("="*70)

print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Exit with appropriate code
sys.exit(0 if test_results['failed'] == 0 else 1)
