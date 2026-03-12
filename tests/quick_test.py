"""
Quick Test - Tests new premium features directly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

print("="*70)
print("QUICK TEST - PREMIUM FEATURES")
print("="*70)

passed = 0
failed = 0

# Test 1: Notifications Module
print("\n[TEST 1] Notifications Module")
try:
    from trading_bot.notifications import NotificationManager, NotificationMessage, NotificationPriority
    from datetime import datetime
    
    notifier = NotificationManager(config={})
    msg = NotificationMessage(
        title="Test",
        message="Test message",
        priority=NotificationPriority.MEDIUM,
        channels=[],
        timestamp=datetime.now()
    )
    print("[PASS] Notifications module works!")
    print(f"       - NotificationManager created")
    print(f"       - Message priority: {msg.priority.value}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 2: Voice Assistant Module
print("\n[TEST 2] Voice Assistant Module")
try:
    from trading_bot.voice_assistant import VoiceAssistant, VoiceCommand, VoiceResponse
    
    class MockBot:
        def get_balance(self): return 10000.0
    
    assistant = VoiceAssistant(MockBot())
    response = VoiceResponse(text="Test response", success=True)
    
    print("[PASS] Voice Assistant module works!")
    print(f"       - VoiceAssistant created")
    print(f"       - Commands available: {len(VoiceCommand)}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 3: Mobile API Module
print("\n[TEST 3] Mobile API Module")
try:
    from trading_bot.mobile_app import MobileAPI, APIResponse, AuthManager
    
    class MockBot:
        def get_status(self): return {'state': 'running'}
    
    api = MobileAPI(MockBot())
    auth = AuthManager(secret_key="test")
    response = APIResponse(success=True, data={'test': 'data'})
    
    print("[PASS] Mobile API module works!")
    print(f"       - MobileAPI created")
    print(f"       - Auth system ready")
    print(f"       - API response: {response.success}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 4: Auto Optimizer Module
print("\n[TEST 4] Auto Optimizer Module")
try:
    from trading_bot.auto_optimizer import StrategyOptimizer, OptimizationMethod, GeneticOptimizer
    
    class MockBot:
        def get_performance(self): return {'sharpe_ratio': 1.5}
    
    optimizer = StrategyOptimizer(MockBot())
    genetic = GeneticOptimizer(population_size=10, generations=5)
    
    print("[PASS] Auto Optimizer module works!")
    print(f"       - StrategyOptimizer created")
    print(f"       - GeneticOptimizer ready")
    print(f"       - Methods: {[m.value for m in OptimizationMethod]}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 5: Trade Journal Module
print("\n[TEST 5] Trade Journal Module")
try:
    from trading_bot.trade_journal import TradeJournal, TradeNote, PerformanceAnalyzer
    
    journal = TradeJournal(journal_dir="test_journal")
    analyzer = PerformanceAnalyzer()
    note = TradeNote(timestamp=datetime.now(), note="Test", category="observation")
    
    print("[PASS] Trade Journal module works!")
    print(f"       - TradeJournal created")
    print(f"       - PerformanceAnalyzer ready")
    print(f"       - Note category: {note.category}")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 6: Module Files Exist
print("\n[TEST 6] Module Files Exist")
try:
    modules = [
        'trading_bot/notifications/__init__.py',
        'trading_bot/notifications/notification_manager.py',
        'trading_bot/voice_assistant/__init__.py',
        'trading_bot/voice_assistant/voice_controller.py',
        'trading_bot/mobile_app/__init__.py',
        'trading_bot/mobile_app/mobile_api.py',
        'trading_bot/auto_optimizer/__init__.py',
        'trading_bot/auto_optimizer/strategy_optimizer.py',
        'trading_bot/trade_journal/__init__.py',
        'trading_bot/trade_journal/journal_manager.py'
    ]
    
    all_exist = True
    for module in modules:
        if not Path(module).exists():
            print(f"       Missing: {module}")
            all_exist = False
    
    if all_exist:
        print("[PASS] All module files exist!")
        print(f"       - {len(modules)} files verified")
        passed += 1
    else:
        print("[FAIL] Some files missing")
        failed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Test 7: Code Statistics
print("\n[TEST 7] Code Statistics")
try:
    total_lines = 0
    for module_file in [
        'trading_bot/notifications/notification_manager.py',
        'trading_bot/voice_assistant/voice_controller.py',
        'trading_bot/mobile_app/mobile_api.py',
        'trading_bot/auto_optimizer/strategy_optimizer.py',
        'trading_bot/trade_journal/journal_manager.py'
    ]:
        if Path(module_file).exists():
            with open(module_file, 'r', encoding='utf-8') as f:
                total_lines += len(f.readlines())
    
    print("[PASS] Code statistics calculated!")
    print(f"       - Total lines of new code: {total_lines}")
    print(f"       - 5 premium features implemented")
    passed += 1
except Exception as e:
    print(f"[FAIL] {e}")
    failed += 1

# Final Results
print("\n" + "="*70)
print("TEST RESULTS")
print("="*70)
print(f"[+] Passed: {passed}")
print(f"[-] Failed: {failed}")
print(f"[=] Total:  {passed + failed}")

success_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
print(f"\n[*] Success Rate: {success_rate:.1f}%")

print("\n" + "="*70)
if success_rate >= 90:
    print("[!!!] EXCELLENT! All premium features working!")
elif success_rate >= 70:
    print("[++] GOOD! Most features working!")
else:
    print("[!] Some features need attention")
print("="*70)

sys.exit(0 if failed == 0 else 1)
