"""
Test all module imports from main.py and identify failures.
"""
import sys
import importlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Dictionary to track module availability
_AVAILABLE = {}
failed_modules = []
success_modules = []

# List of all modules from main.py (extracted from the import section)
MODULES_TO_TEST = [
    ('elite_ai', 'trading_bot.elite_ai_system', ['EliteTradingOrchestrator', 'SlowInferenceEngine', 'MarketPsychologyEngine', 'EmergencyResponseSystem']),
    ('market_intelligence', 'trading_bot.market_intelligence', ['MarketDataMonitor', 'WyckoffAccumulationDetector', 'WyckoffDistributionAnalyzer', 'LiquidityPoolDetector', 'OrderBlockAnalysis', 'MarketEventDetector', 'PricePatternRecognition']),
    ('complete_system', 'trading_bot.master_integration', ['MasterTradingSystem']),
    ('enhanced_risk', 'trading_bot.risk.complete_risk_system', ['CompleteRiskSystem']),
    ('smart_execution', 'trading_bot.execution.complete_execution_system', ['CompleteExecutionSystem']),
    ('performance_analytics', 'trading_bot.performance.complete_performance_system', ['CompletePerformanceSystem']),
    ('market_student', 'trading_bot.market_student', ['MarketStudentOrchestrator']),
    ('eternal_evolution', 'trading_bot.eternal_evolution', ['EternalEvolutionOrchestrator']),
    ('self_diagnostic', 'trading_bot.self_diagnostic', ['SelfManager']),
    ('hedge_fund_safety', 'trading_bot.hedge_fund_safety', ['HedgeFundSafetyOrchestrator']),
    ('alpha_research', 'trading_bot.alpha_research', ['AlphaResearchOrchestrator']),
    ('intelligent_delegation', 'trading_bot.intelligent_delegation', ['DelegationOrchestrator']),
    ('trading_engine', 'trading_bot.trading_engine', ['TradingEngine']),
    ('main_orchestrator', 'trading_bot.master_orchestrator', ['MasterOrchestrator']),
    ('unified_brain', 'trading_bot.unified_ai_brain', ['UnifiedAIBrain', 'BrainConfig']),
    ('reality_gates', 'trading_bot.reality_gates', ['RealityGateOrchestrator']),
    ('safety', 'trading_bot.safety', ['SafetyOrchestrator']),
    ('stealth_safety', 'trading_bot.stealth_safety', ['StealthSafetyManager']),
    ('compliance', 'trading_bot.compliance', ['ComplianceManager']),
    ('position_manager', 'trading_bot.position', ['PositionManager']),
    ('ai_core', 'trading_bot.ai_core', ['AICoreOrchestrator']),
    ('brain', 'trading_bot.brain', ['BrainOrchestrator']),
    ('alpha_engine', 'trading_bot.alpha_engine', ['AlphaEngine']),
    ('decision_layer', 'trading_bot.decision_layer', ['DecisionLayerOrchestrator']),
    ('cognitive', 'trading_bot.cognitive_architecture', ['CognitiveOrchestrator']),
    ('profit_maximizer', 'trading_bot.profit_maximizer', ['ProfitMaximizer']),
    ('aamis_v3', 'trading_bot.aamis_v3', ['AAMISOrchestrator']),
    ('alphaalgo_core', 'trading_bot.alphaalgo_core', ['AlphaAlgoCore']),
    ('sentient_core', 'trading_bot.sentient_core', ['SentientOrchestrator']),
    ('ingestion', 'trading_bot.ingestion', ['IngestionOrchestrator']),
    ('streaming', 'trading_bot.streaming', ['StreamingManager']),
    ('data_feeds', 'trading_bot.data_feeds', ['DataFeedManager']),
    ('database', 'trading_bot.database', ['DatabaseManager']),
    ('monitoring', 'trading_bot.monitoring', ['MonitoringOrchestrator']),
    ('system_health', 'trading_bot.system_health', ['SystemHealthManager']),
]

def test_import(module_name, import_path, classes):
    """Test if a module can be imported."""
    try:
        module = importlib.import_module(import_path)
        # Try to access the classes
        for cls in classes:
            if not hasattr(module, cls):
                raise AttributeError(f"Module {import_path} missing class {cls}")
        return True, None
    except Exception as e:
        return False, str(e)

print("=" * 80)
print("MODULE IMPORT TEST")
print("=" * 80)
print()

for module_name, import_path, classes in MODULES_TO_TEST:
    success, error = test_import(module_name, import_path, classes)
    _AVAILABLE[module_name] = success
    
    if success:
        success_modules.append(module_name)
        print(f"[OK] {module_name:30s} SUCCESS")
    else:
        failed_modules.append((module_name, import_path, error))
        print(f"[FAIL] {module_name:30s} FAILED: {error[:60]}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
total = len(_AVAILABLE)
loaded = sum(1 for v in _AVAILABLE.values() if v)
failed = total - loaded
percentage = (loaded / total * 100) if total > 0 else 0

print(f"Total modules: {total}")
print(f"Loaded successfully: {loaded} ({percentage:.1f}%)")
print(f"Failed: {failed}")
print()

if failed_modules:
    print("=" * 80)
    print("FAILED MODULES DETAILS")
    print("=" * 80)
    for module_name, import_path, error in failed_modules:
        print(f"\nModule: {module_name}")
        print(f"Path: {import_path}")
        print(f"Error: {error}")
        print("-" * 80)
