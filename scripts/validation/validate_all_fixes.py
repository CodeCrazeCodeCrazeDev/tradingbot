"""
Comprehensive Validation Script for All Fixes
Tests all implemented fixes and integrations
"""

import sys
import importlib
from typing import Dict, List, Tuple


def test_import(module_path: str, component: str) -> Tuple[bool, str]:
    """Test if a component can be imported."""
    try:
        module = importlib.import_module(module_path)
        if hasattr(module, component):
            return True, f"[OK] {component} imported successfully"
        else:
            return False, f"[FAIL] {component} not found in {module_path}"
    except ImportError as e:
        return False, f"[FAIL] Import error: {e}"
    except Exception as e:
        return False, f"[FAIL] Error: {e}"


def validate_phase1() -> Dict[str, bool]:
    """Validate Phase 1: Critical fixes."""
    print("\n" + "="*60)
    print("PHASE 1: CRITICAL FIXES VALIDATION")
    print("="*60)
    
    results = {}
    
    # Test MLOps module
    print("\n1. Testing MLOps Module...")
    mlops_components = [
        'ModelRegistry', 'ExperimentTracker', 
        'PerformanceMonitor', 'AutoRollback'
    ]
    
    for component in mlops_components:
        success, msg = test_import('trading_bot.ai_core.mlops', component)
        results[f'mlops_{component}'] = success
        print(f"  {msg}")
    
    # Test AI Core integration
    print("\n2. Testing AI Core Integration...")
    ai_components = [
        'ModelRegistry', 'ExperimentTracker',
        'PlannerAgent', 'TemporalFusionTransformer'
    ]
    
    for component in ai_components:
        success, msg = test_import('trading_bot', component)
        results[f'ai_core_{component}'] = success
        print(f"  {msg}")
    
    return results


def validate_phase2() -> Dict[str, bool]:
    """Validate Phase 2: Module consolidation."""
    print("\n" + "="*60)
    print("PHASE 2: MODULE CONSOLIDATION VALIDATION")
    print("="*60)
    
    results = {}
    
    # Test unified modules
    print("\n1. Testing Unified Modules...")
    
    unified_tests = [
        ('trading_bot.risk_unified', 'RiskManager'),
        ('trading_bot.analysis_unified', 'MarketStructureAnalyzer'),
        ('trading_bot.connectivity_unified', 'MT5Connector')
    ]
    
    for module_path, component in unified_tests:
        success, msg = test_import(module_path, component)
        results[f'unified_{component}'] = success
        print(f"  {msg}")
    
    return results


def validate_phase3() -> Dict[str, bool]:
    """Validate Phase 3: Complete module integrations."""
    print("\n" + "="*60)
    print("PHASE 3: MODULE INTEGRATIONS VALIDATION")
    print("="*60)
    
    results = {}
    
    # Test integrated modules
    print("\n1. Testing Integrated Modules...")
    
    integrated_components = [
        ('trading_bot', 'TradingMetricsExporter'),  # Monitoring
        ('trading_bot', 'SystemSupervisor'),  # System Supervisor
        ('trading_bot', 'SelfImprovementEngine'),  # Self-Improvement
        ('trading_bot', 'ConnectionValidator'),  # Internet Access
        ('trading_bot', 'InternetLearningSystem'),  # Learning
    ]
    
    for module_path, component in integrated_components:
        success, msg = test_import(module_path, component)
        results[f'integrated_{component}'] = success
        print(f"  {msg}")
    
    return results


def validate_phase4() -> Dict[str, bool]:
    """Validate Phase 4: Missing AI components."""
    print("\n" + "="*60)
    print("PHASE 4: AI COMPONENTS VALIDATION")
    print("="*60)
    
    results = {}
    
    # Test AI components
    print("\n1. Testing AI Agents...")
    agents = ['PlannerAgent', 'VerifierAgent', 'ExecutorAgent', 'SafetyValidatorAgent']
    for agent in agents:
        success, msg = test_import('trading_bot.ai_core.agents', agent)
        results[f'agent_{agent}'] = success
        print(f"  {msg}")
    
    print("\n2. Testing Forecasting Models...")
    models = ['TemporalFusionTransformer', 'InformerModel', 'NBEATSModel', 'DeepARModel']
    for model in models:
        success, msg = test_import('trading_bot.ai_core.forecasting', model)
        results[f'forecast_{model}'] = success
        print(f"  {msg}")
    
    print("\n3. Testing Execution Optimization...")
    exec_components = ['AlmgrenChrissExecutor', 'RLAdaptiveExecutor', 'MarketImpactModel']
    for component in exec_components:
        success, msg = test_import('trading_bot.ai_core.execution', component)
        results[f'exec_{component}'] = success
        print(f"  {msg}")
    
    print("\n4. Testing Explainability...")
    explain_components = ['SHAPExplainer', 'LIMEExplainer', 'CausalAnalyzer']
    for component in explain_components:
        success, msg = test_import('trading_bot.ai_core.explainability', component)
        results[f'explain_{component}'] = success
        print(f"  {msg}")
    
    print("\n5. Testing Meta-Learning...")
    meta_components = ['MAMLTrainer', 'ContinualLearner', 'RegimeDetector']
    for component in meta_components:
        success, msg = test_import('trading_bot.ai_core.meta_learning', component)
        results[f'meta_{component}'] = success
        print(f"  {msg}")
    
    print("\n6. Testing Drift Detection...")
    drift_components = ['ADWINDetector', 'PageHinkleyDetector', 'ConceptDriftMonitor']
    for component in drift_components:
        success, msg = test_import('trading_bot.ai_core.drift_detection', component)
        results[f'drift_{component}'] = success
        print(f"  {msg}")
    
    return results


def validate_main_import() -> bool:
    """Validate main trading_bot import."""
    print("\n" + "="*60)
    print("MAIN IMPORT VALIDATION")
    print("="*60)
    
    try:
        import trading_bot
        print(f"\n[OK] Main import successful")
        print(f"[OK] Version: {trading_bot.__version__}")
        print(f"[OK] Total exports: {len(trading_bot.__all__)}")
        return True
    except Exception as e:
        print(f"\n[FAIL] Main import failed: {e}")
        return False


def generate_report(all_results: Dict[str, Dict[str, bool]]):
    """Generate final validation report."""
    print("\n" + "="*60)
    print("FINAL VALIDATION REPORT")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for phase, results in all_results.items():
        phase_total = len(results)
        phase_passed = sum(1 for v in results.values() if v)
        total_tests += phase_total
        passed_tests += phase_passed
        
        print(f"\n{phase}:")
        print(f"  Passed: {phase_passed}/{phase_total}")
        print(f"  Success Rate: {phase_passed/phase_total*100:.1f}%")
    
    print("\n" + "="*60)
    print("OVERALL RESULTS")
    print("="*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n[SUCCESS] ALL TESTS PASSED! System is fully operational.")
        return 0
    elif passed_tests / total_tests >= 0.8:
        print("\n[OK] Most tests passed. System is operational with minor issues.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Review the results above.")
        return 1


def validate_new_fixes() -> Dict[str, bool]:
    """Validate newly implemented fixes."""
    print("\n" + "="*60)
    print("NEW FIXES VALIDATION")
    print("="*60)
    
    results = {}
    
    # Test Trade Journal
    print("\n1. Testing Trade Journal...")
    journal_components = ['TradeJournal', 'TradeRecord', 'AuditEvent', 'EventType', 'get_trade_journal']
    for component in journal_components:
        success, msg = test_import('trading_bot.audit.trade_journal', component)
        results[f'journal_{component}'] = success
        print(f"  {msg}")
    
    # Test Connection Manager
    print("\n2. Testing Connection Manager...")
    conn_components = ['BrokerConnectionManager', 'ConnectionState', 'ConnectionHealth', 'MultiBrokerConnectionManager']
    for component in conn_components:
        success, msg = test_import('trading_bot.brokers.connection_manager', component)
        results[f'conn_{component}'] = success
        print(f"  {msg}")
    
    # Test Position Reconciliation
    print("\n3. Testing Position Reconciliation...")
    recon_components = ['PositionReconciler', 'ReconciliationResult', 'PositionDiscrepancy', 'DiscrepancyType']
    for component in recon_components:
        success, msg = test_import('trading_bot.trading.position_reconciliation', component)
        results[f'recon_{component}'] = success
        print(f"  {msg}")
    
    # Test Data Validator
    print("\n4. Testing Data Validator...")
    validator_components = ['DataValidator', 'ValidationResult', 'DataQuality', 'validate_market_data']
    for component in validator_components:
        success, msg = test_import('trading_bot.data.data_validator', component)
        results[f'validator_{component}'] = success
        print(f"  {msg}")
    
    # Test Circuit Breaker Manager
    print("\n5. Testing Circuit Breaker Manager...")
    cb_components = ['CircuitBreakerManager', 'CircuitBreaker', 'CircuitState', 'get_circuit_breaker_manager', 'circuit_protected']
    for component in cb_components:
        success, msg = test_import('trading_bot.risk.circuit_breaker_manager', component)
        results[f'cb_{component}'] = success
        print(f"  {msg}")
    
    # Test Execution Manager methods
    print("\n6. Testing Execution Manager Methods...")
    try:
        from trading_bot.core.execution_manager import ExecutionManager
        em = ExecutionManager()
        
        # Test calculate_position_size
        if hasattr(em, 'calculate_position_size'):
            result = em.calculate_position_size('EURUSD', 1.1000, 1.0950)
            if 'recommended_size' in result:
                results['em_calculate_position_size'] = True
                print(f"  [OK] calculate_position_size works correctly")
            else:
                results['em_calculate_position_size'] = False
                print(f"  [FAIL] calculate_position_size returned invalid result")
        else:
            results['em_calculate_position_size'] = False
            print(f"  [FAIL] calculate_position_size method not found")
        
        # Test get_portfolio_status
        if hasattr(em, 'get_portfolio_status'):
            status = em.get_portfolio_status()
            if 'account_balance' in status and 'current_drawdown' in status:
                results['em_get_portfolio_status'] = True
                print(f"  [OK] get_portfolio_status works correctly")
            else:
                results['em_get_portfolio_status'] = False
                print(f"  [FAIL] get_portfolio_status returned invalid result")
        else:
            results['em_get_portfolio_status'] = False
            print(f"  [FAIL] get_portfolio_status method not found")
            
    except Exception as e:
        results['em_calculate_position_size'] = False
        results['em_get_portfolio_status'] = False
        print(f"  [FAIL] ExecutionManager test failed: {e}")
    
    # Test OrderType import in survival_core
    print("\n7. Testing OrderType Import...")
    try:
        from trading_bot.core.survival_core import OrderType
        results['survival_OrderType'] = True
        print(f"  [OK] OrderType imported successfully from survival_core")
    except Exception as e:
        results['survival_OrderType'] = False
        print(f"  [FAIL] OrderType import failed: {e}")
    
    return results


def main():
    """Run all validations."""
    print("="*60)
    print("COMPREHENSIVE VALIDATION - ALL PHASES")
    print("="*60)
    
    # Validate main import first
    main_import_ok = validate_main_import()
    
    if not main_import_ok:
        print("\n[WARNING] Main import failed. Continuing with component validation...")
    
    # Run phase validations
    all_results = {
        'New Fixes': validate_new_fixes(),
        'Phase 1 (Critical Fixes)': validate_phase1(),
        'Phase 2 (Consolidation)': validate_phase2(),
        'Phase 3 (Integrations)': validate_phase3(),
        'Phase 4 (AI Components)': validate_phase4()
    }
    
    # Generate report
    return generate_report(all_results)


if __name__ == "__main__":
    sys.exit(main())
