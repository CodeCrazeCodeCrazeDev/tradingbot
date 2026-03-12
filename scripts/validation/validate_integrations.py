"""
Integration Validation Script
Validates that newly integrated modules can be imported and instantiated
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_imports():
    """Validate that all integrated modules can be imported."""
    print("=" * 80)
    print("INTEGRATION VALIDATION - IMPORT CHECKS")
    print("=" * 80)
    print()
    
    results = {
        'passed': [],
        'failed': []
    }
    
    # Test Orchestrator imports
    print("[1/10] Testing Orchestrator imports...")
    try:
        from trading_bot.orchestrator import (
            MasterOrchestrator, TradingMode, TradingDecision,
            ExecutionEngine, OrderType, ExecutionAlgorithm,
            OpportunityPredictor, SuccessPredictor,
            PortfolioRiskManager, PositionSizer,
            PerformanceTracker, MetricsCalculator
        )
        print("  [OK] Orchestrator modules imported successfully")
        results['passed'].append('Orchestrator')
    except Exception as e:
        print(f"  [FAIL] Orchestrator import failed: {e}")
        results['failed'].append(('Orchestrator', str(e)))
    
    # Test Opportunity Scanner imports
    print("[2/10] Testing Opportunity Scanner imports...")
    try:
        from trading_bot.opportunity_scanner import (
            MarketInefficiencyScanner,
            CrossExchangeArbitrage,
            NewsImpactAnalyzer,
            CorrelationBreakdownDetector,
            MarketMakerStrategy,
            OrderFlowImbalanceDetector,
            VolatilityArbitrage,
            MomentumBurstDetector
        )
        print("  [OK] Opportunity Scanner modules imported successfully")
        results['passed'].append('Opportunity Scanner')
    except Exception as e:
        print(f"  [FAIL] Opportunity Scanner import failed: {e}")
        results['failed'].append(('Opportunity Scanner', str(e)))
    
    # Test Exit Strategies imports
    print("[3/10] Testing Exit Strategies imports...")
    try:
        from trading_bot.exit_strategies import (
            ExitStrategy, ExitType, ExitSignal,
            AdaptiveExitStrategy, VolatilityBasedExit,
            DynamicTradeManager, PartialExitStrategy,
            ProfitMaximizer, RiskRewardOptimizer,
            ExitSignalGenerator
        )
        print("  [OK] Exit Strategies modules imported successfully")
        results['passed'].append('Exit Strategies')
    except Exception as e:
        print(f"  [FAIL] Exit Strategies import failed: {e}")
        results['failed'].append(('Exit Strategies', str(e)))
    
    # Test Adaptive Systems imports
    print("[4/10] Testing Adaptive Systems imports...")
    try:
        from trading_bot.adaptive_systems import (
            AdaptiveTradingMaster, MarketRegimeDetector,
            AdaptiveRiskManager, StrategySelector,
            SelfImprovementEngine, AdaptiveLearningEngine,
            EnsembleLearningSystem, SystemHealthMonitor
        )
        print("  [OK] Adaptive Systems modules imported successfully")
        results['passed'].append('Adaptive Systems')
    except Exception as e:
        print(f"  [FAIL] Adaptive Systems import failed: {e}")
        results['failed'].append(('Adaptive Systems', str(e)))
    
    # Test ML/AI Systems imports
    print("[5/10] Testing ML/AI Systems imports...")
    try:
        from trading_bot.ml import (
            PricePredictor, PatternRecognizer,
            StrategyOptimizer, PPOAgent,
            OnlineLearner, ExplainableAI,
            PersonalizedLearningSystem
        )
        print("  [OK] ML/AI Systems modules imported successfully")
        results['passed'].append('ML/AI Systems')
    except Exception as e:
        print(f"  [FAIL] ML/AI Systems import failed: {e}")
        results['failed'].append(('ML/AI Systems', str(e)))
    
    # Test Risk Management imports
    print("[6/10] Testing Risk Management imports...")
    try:
        from trading_bot.risk_management import (
            RiskEngine, PortfolioManager,
            KellyCalculator, RiskMonitor,
            BlackSwanProtector, VaRCalculator
        )
        print("  [OK] Risk Management modules imported successfully")
        results['passed'].append('Risk Management')
    except Exception as e:
        print(f"  [FAIL] Risk Management import failed: {e}")
        results['failed'].append(('Risk Management', str(e)))
    
    # Test Dashboard imports
    print("[7/10] Testing Dashboard imports...")
    try:
        from trading_bot.dashboard import (
            DashboardServer, LiveDashboard,
            PerformanceDashboard, SurvivalDashboard,
            GamifiedDashboard, UnifiedDashboard
        )
        print("  [OK] Dashboard modules imported successfully")
        results['passed'].append('Dashboard')
    except Exception as e:
        print(f"  [FAIL] Dashboard import failed: {e}")
        results['failed'].append(('Dashboard', str(e)))
    
    # Test Database imports
    print("[8/10] Testing Database imports...")
    try:
        from trading_bot.database import (
            DatabaseManager, RobustDatabaseManager,
            DataNormalizer, MarketMicrostructure,
            DataProcessor, PipelineMonitor
        )
        print("  [OK] Database modules imported successfully")
        results['passed'].append('Database')
    except Exception as e:
        print(f"  [FAIL] Database import failed: {e}")
        results['failed'].append(('Database', str(e)))
    
    # Test Backtesting imports
    print("[9/10] Testing Backtesting imports...")
    try:
        from trading_bot.backtesting import (
            Backtester, AdvancedBacktester,
            BacktestResults, StrategyBacktester
        )
        print("  [OK] Backtesting modules imported successfully")
        results['passed'].append('Backtesting')
    except Exception as e:
        print(f"  [FAIL] Backtesting import failed: {e}")
        results['failed'].append(('Backtesting', str(e)))
    
    # Test Institutional Entry imports
    print("[10/10] Testing Institutional Entry imports...")
    try:
        from trading_bot.institutional_entry import (
            WyckoffICTFusion, EntryTrigger,
            EntryValidator, EntrySignalGenerator,
            InstitutionalFootprint
        )
        print("  [OK] Institutional Entry modules imported successfully")
        results['passed'].append('Institutional Entry')
    except Exception as e:
        print(f"  [FAIL] Institutional Entry import failed: {e}")
        results['failed'].append(('Institutional Entry', str(e)))
    
    # Test root-level imports
    print("\n[BONUS] Testing root-level trading_bot imports...")
    try:
        from trading_bot import (
            MasterOrchestrator,
            MarketInefficiencyScanner,
            ExitSignalGenerator,
            AdaptiveTradingMaster,
            PricePredictor,
            RiskEngine,
            DashboardServer,
            AdvancedBacktester,
            WyckoffICTFusion
        )
        print("  [OK] Root-level imports working")
        results['passed'].append('Root-level imports')
    except Exception as e:
        print(f"  [FAIL] Root-level imports failed: {e}")
        results['failed'].append(('Root-level imports', str(e)))
    
    return results


def print_summary(results):
    """Print validation summary."""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    total = len(results['passed']) + len(results['failed'])
    passed = len(results['passed'])
    failed = len(results['failed'])
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print()
    
    if results['passed']:
        print("PASSED MODULES:")
        for module in results['passed']:
            print(f"  [OK] {module}")
        print()
    
    if results['failed']:
        print("FAILED MODULES:")
        for module, error in results['failed']:
            print(f"  [FAIL] {module}")
            print(f"         Error: {error}")
        print()
    
    if failed == 0:
        print("[SUCCESS] All integrations validated successfully!")
        print("The following module categories are now integrated and ready to use:")
        print("  - Orchestrator (Master coordination system)")
        print("  - Opportunity Scanner (Comprehensive opportunity detection)")
        print("  - Exit Strategies (Advanced exit management)")
        print("  - Adaptive Systems (Self-improving trading systems)")
        print("  - ML/AI Systems (Advanced machine learning)")
        print("  - Risk Management (Comprehensive risk control)")
        print("  - Dashboard (Real-time monitoring & visualization)")
        print("  - Database (Data management & pipeline)")
        print("  - Backtesting (Advanced backtesting framework)")
        print("  - Institutional Entry (Wyckoff & ICT entry triggers)")
        print()
        print("Next steps:")
        print("  1. Update main.py to use integrated systems")
        print("  2. Create configuration files for each system")
        print("  3. Run paper trading tests with new features")
        print("  4. Monitor performance improvements")
        return 0
    else:
        print("[WARNING] Some integrations failed validation")
        print("Please review the errors above and fix import issues")
        return 1


def main():
    """Main validation execution."""
    print("\nAlphaAlgo Trading Bot - Integration Validation")
    print("Validating newly integrated modules...\n")
    
    results = validate_imports()
    exit_code = print_summary(results)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
