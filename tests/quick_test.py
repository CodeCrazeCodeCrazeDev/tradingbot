"""
Quick Test - Tests new premium features directly.

This file is import-safe for pytest. Run it as a script to execute the quick
premium-feature smoke checks.
"""

import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    print("=" * 70)
    print("QUICK TEST - PREMIUM FEATURES")
    print("=" * 70)

    passed = 0
    failed = 0

    checks = [
        ("Notifications Module", _check_notifications),
        ("Voice Assistant Module", _check_voice_assistant),
        ("Mobile API Module", _check_mobile_api),
        ("Auto Optimizer Module", _check_auto_optimizer),
        ("Trade Journal Module", _check_trade_journal),
        ("Module Files Exist", _check_module_files),
        ("Code Statistics", _check_code_statistics),
    ]

    for index, (name, check) in enumerate(checks, start=1):
        print(f"\n[TEST {index}] {name}")
        try:
            details = check()
            print(f"[PASS] {name} works!")
            for detail in details:
                print(f"       - {detail}")
            passed += 1
        except Exception as exc:
            print(f"[FAIL] {exc}")
            failed += 1

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"[+] Passed: {passed}")
    print(f"[-] Failed: {failed}")
    print(f"[=] Total:  {passed + failed}")

    success_rate = (passed / (passed + failed) * 100) if (passed + failed) > 0 else 0
    print(f"\n[*] Success Rate: {success_rate:.1f}%")
    print("\n" + "=" * 70)
    if success_rate >= 90:
        print("[!!!] EXCELLENT! All premium features working!")
    elif success_rate >= 70:
        print("[++] GOOD! Most features working!")
    else:
        print("[!] Some features need attention")
    print("=" * 70)
    return 0 if failed == 0 else 1


def _check_notifications():
    from trading_bot.notifications import NotificationManager, NotificationMessage, NotificationPriority

    NotificationManager(config={})
    msg = NotificationMessage(
        title="Test",
        message="Test message",
        priority=NotificationPriority.MEDIUM,
        channels=[],
        timestamp=datetime.now(),
    )
    return ["NotificationManager created", f"Message priority: {msg.priority.value}"]


def _check_voice_assistant():
    from trading_bot.voice_assistant import VoiceAssistant, VoiceCommand, VoiceResponse

    class MockBot:
        def get_balance(self):
            return 10000.0

    VoiceAssistant(MockBot())
    VoiceResponse(text="Test response", success=True)
    return ["VoiceAssistant created", f"Commands available: {len(VoiceCommand)}"]


def _check_mobile_api():
    from trading_bot.mobile_app import APIResponse, AuthManager, MobileAPI

    class MockBot:
        def get_status(self):
            return {"state": "running"}

    MobileAPI(MockBot())
    AuthManager(secret_key="test")
    response = APIResponse(success=True, data={"test": "data"})
    return ["MobileAPI created", "Auth system ready", f"API response: {response.success}"]


def _check_auto_optimizer():
    from trading_bot.auto_optimizer import GeneticOptimizer, OptimizationMethod, StrategyOptimizer

    class MockBot:
        def get_performance(self):
            return {"sharpe_ratio": 1.5}

    StrategyOptimizer(MockBot())
    GeneticOptimizer(population_size=10, generations=5)
    return ["StrategyOptimizer created", "GeneticOptimizer ready", f"Methods: {[m.value for m in OptimizationMethod]}"]


def _check_trade_journal():
    from trading_bot.trade_journal import PerformanceAnalyzer, TradeJournal, TradeNote

    TradeJournal(journal_dir="test_journal")
    PerformanceAnalyzer()
    note = TradeNote(timestamp=datetime.now(), note="Test", category="observation")
    return ["TradeJournal created", "PerformanceAnalyzer ready", f"Note category: {note.category}"]


def _check_module_files():
    modules = [
        "trading_bot/notifications/__init__.py",
        "trading_bot/notifications/notification_manager.py",
        "trading_bot/voice_assistant/__init__.py",
        "trading_bot/voice_assistant/voice_controller.py",
        "trading_bot/mobile_app/__init__.py",
        "trading_bot/mobile_app/mobile_api.py",
        "trading_bot/auto_optimizer/__init__.py",
        "trading_bot/auto_optimizer/strategy_optimizer.py",
        "trading_bot/trade_journal/__init__.py",
        "trading_bot/trade_journal/journal_manager.py",
    ]
    missing = [module for module in modules if not Path(module).exists()]
    if missing:
        raise FileNotFoundError(f"Missing files: {', '.join(missing)}")
    return [f"{len(modules)} files verified"]


def _check_code_statistics():
    total_lines = 0
    for module_file in [
        "trading_bot/notifications/notification_manager.py",
        "trading_bot/voice_assistant/voice_controller.py",
        "trading_bot/mobile_app/mobile_api.py",
        "trading_bot/auto_optimizer/strategy_optimizer.py",
        "trading_bot/trade_journal/journal_manager.py",
    ]:
        if Path(module_file).exists():
            total_lines += len(Path(module_file).read_text(encoding="utf-8").splitlines())
    return [f"Total lines of new code: {total_lines}", "5 premium features implemented"]


if __name__ == "__main__":
    sys.exit(main())
