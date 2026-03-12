"""
Comprehensive Coverage Analysis Script
Identifies all modules and their test coverage status
"""
import os
import ast
import sys
from pathlib import Path
from collections import defaultdict

# Define module categories
CRITICAL_MODULES = {
    # Money handling - MUST have 100% coverage
    'trading_bot/risk/position_sizer.py': 'Position sizing calculations',
    'trading_bot/risk/position_size_calculator.py': 'Position size calculations',
    'trading_bot/risk/kelly_criterion.py': 'Kelly criterion for position sizing',
    'trading_bot/execution/trade_executor.py': 'Order execution',
    'trading_bot/execution/live_executor.py': 'Live order execution',
    'trading_bot/execution/paper_executor.py': 'Paper trading execution',
    'trading_bot/execution/fill_tracker.py': 'Fill tracking and confirmation',
    'trading_bot/execution/order_confirmation.py': 'Order confirmation',
    'trading_bot/execution/idempotent_executor.py': 'Idempotent execution',
    'trading_bot/brokers/broker_adapter.py': 'Broker adapter interface',
    
    # Trading decisions - MUST have 100% coverage
    'trading_bot/signals/signal_lifecycle.py': 'Signal generation and lifecycle',
    'trading_bot/signals/entry_confirmation.py': 'Entry signal confirmation',
    'trading_bot/signals/complete_signal_system.py': 'Complete signal system',
    'trading_bot/core/survival_core.py': 'Core survival trading logic',
    'trading_bot/core/main_trading_loop.py': 'Main trading loop',
    'trading_bot/core/trading_system.py': 'Trading system core',
    
    # Risk management - MUST have 100% coverage
    'trading_bot/risk/MASTER_risk_manager.py': 'Master risk manager',
    'trading_bot/risk/pre_trade_checks.py': 'Pre-trade risk checks',
    'trading_bot/risk/trade_validation.py': 'Trade validation',
    'trading_bot/risk/drawdown_protector.py': 'Drawdown protection',
    'trading_bot/risk/circuit_breaker.py': 'Circuit breaker',
    'trading_bot/risk/var_engine.py': 'Value at Risk engine',
    'trading_bot/risk/portfolio_risk_manager.py': 'Portfolio risk management',
    
    # Data validation - MUST have 100% coverage
    'trading_bot/validation/data_validator.py': 'Data validation',
    'trading_bot/validation/data_quality.py': 'Data quality checks',
    'trading_bot/validation/critical_validators.py': 'Critical validators',
    'trading_bot/validation/trade_validator.py': 'Trade validation',
    'trading_bot/validation/risk_validation_gate.py': 'Risk validation gate',
}

IMPORTANT_MODULES = {
    # ML and Analysis - Should have 80%+ coverage
    'trading_bot/ml/predictive_models.py': 'ML predictive models',
    'trading_bot/ml/ensemble_models.py': 'Ensemble models',
    'trading_bot/ml/sentiment.py': 'Sentiment analysis',
    'trading_bot/ml/reinforcement.py': 'Reinforcement learning',
    'trading_bot/ml/online_learning.py': 'Online learning',
    'trading_bot/ml/hyperparameter_tuning.py': 'Hyperparameter tuning',
    'trading_bot/analysis/market_structure.py': 'Market structure analysis',
    'trading_bot/analysis/order_flow.py': 'Order flow analysis',
    'trading_bot/analysis/liquidity.py': 'Liquidity analysis',
    'trading_bot/analysis/technical_indicators.py': 'Technical indicators',
    'trading_bot/analysis/market_regime.py': 'Market regime detection',
    'trading_bot/analysis/sentiment_analyzer.py': 'Sentiment analysis',
    
    # Execution algorithms - Should have 80%+ coverage
    'trading_bot/execution/algorithms.py': 'Execution algorithms',
    'trading_bot/execution/smart_execution.py': 'Smart execution',
    'trading_bot/execution/smart_order_router.py': 'Smart order routing',
    'trading_bot/execution/market_impact.py': 'Market impact models',
    'trading_bot/execution/slippage_protection.py': 'Slippage protection',
    
    # Database and connectivity - Should have 80%+ coverage
    'trading_bot/database/timeseries_db.py': 'Time series database',
    'trading_bot/database/database_manager.py': 'Database manager',
    'trading_bot/connectivity/mt5_connector.py': 'MT5 connector',
    'trading_bot/connectivity/data_feed.py': 'Data feed',
}

NICE_TO_HAVE_MODULES = {
    # Advanced features - 60%+ coverage
    'trading_bot/advanced_features/': 'Advanced features',
    'trading_bot/aamis_v3/': 'AAMIS v3 system',
    'trading_bot/quantum/': 'Quantum computing',
    'trading_bot/blockchain/': 'Blockchain integration',
    'trading_bot/autonomous/': 'Autonomous systems',
    'trading_bot/orchestrator/': 'Orchestrator',
    'trading_bot/opportunity_scanner/': 'Opportunity scanner',
}


def get_all_python_files(base_path):
    """Get all Python files in the trading_bot directory"""
    files = []
    for root, dirs, filenames in os.walk(base_path):
        # Skip __pycache__ and test directories
        dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('test_'):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, os.path.dirname(base_path))
                files.append(rel_path.replace('\\', '/'))
    return files


def count_lines_and_functions(filepath):
    """Count lines of code and functions in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
        
        try:
            tree = ast.parse(content)
            functions = len([node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))])
            classes = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        except:
            functions = 0
            classes = 0
        
        return lines, functions, classes
    except:
        return 0, 0, 0


def analyze_test_coverage(tests_path, trading_bot_path):
    """Analyze which modules have tests"""
    test_files = []
    for root, dirs, filenames in os.walk(tests_path):
        for filename in filenames:
            if filename.startswith('test_') and filename.endswith('.py'):
                test_files.append(os.path.join(root, filename))
    
    # Read all test files and find imports
    tested_modules = set()
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find imports from trading_bot
            import_patterns = [
                'from trading_bot.',
                'import trading_bot.',
            ]
            for line in content.split('\n'):
                for pattern in import_patterns:
                    if pattern in line:
                        # Extract module path
                        if 'from trading_bot.' in line:
                            parts = line.split('from trading_bot.')[1].split(' import')[0]
                            tested_modules.add(f'trading_bot/{parts.replace(".", "/")}.py')
                        elif 'import trading_bot.' in line:
                            parts = line.split('import trading_bot.')[1].split()[0]
                            tested_modules.add(f'trading_bot/{parts.replace(".", "/")}.py')
        except:
            pass
    
    return tested_modules


def main():
    base_path = Path(__file__).parent
    trading_bot_path = base_path / 'trading_bot'
    tests_path = base_path / 'tests'
    
    print("=" * 80)
    print("COMPREHENSIVE COVERAGE ANALYSIS")
    print("=" * 80)
    
    # Get all Python files
    all_files = get_all_python_files(trading_bot_path)
    print(f"\nTotal Python files in trading_bot: {len(all_files)}")
    
    # Analyze test coverage
    tested_modules = analyze_test_coverage(tests_path, trading_bot_path)
    print(f"Modules with some test coverage: {len(tested_modules)}")
    
    # Categorize modules
    critical_untested = []
    important_untested = []
    nice_to_have_untested = []
    other_untested = []
    
    total_lines = 0
    total_functions = 0
    total_classes = 0
    
    for filepath in all_files:
        full_path = base_path / filepath
        lines, functions, classes = count_lines_and_functions(full_path)
        total_lines += lines
        total_functions += functions
        total_classes += classes
        
        is_tested = any(filepath.replace('/', '.').replace('.py', '') in t for t in tested_modules) or filepath in tested_modules
        
        if not is_tested:
            if filepath in CRITICAL_MODULES:
                critical_untested.append((filepath, lines, functions, CRITICAL_MODULES[filepath]))
            elif filepath in IMPORTANT_MODULES:
                important_untested.append((filepath, lines, functions, IMPORTANT_MODULES[filepath]))
            elif any(filepath.startswith(prefix) for prefix in NICE_TO_HAVE_MODULES):
                nice_to_have_untested.append((filepath, lines, functions))
            else:
                other_untested.append((filepath, lines, functions))
    
    print(f"\nTotal lines of code: {total_lines}")
    print(f"Total functions: {total_functions}")
    print(f"Total classes: {total_classes}")
    
    print("\n" + "=" * 80)
    print("CRITICAL MODULES NEEDING 100% COVERAGE")
    print("=" * 80)
    for filepath, lines, functions, desc in sorted(critical_untested, key=lambda x: -x[1]):
        print(f"  {filepath}")
        print(f"    - {desc}")
        print(f"    - Lines: {lines}, Functions: {functions}")
    print(f"\nTotal critical modules needing tests: {len(critical_untested)}")
    
    print("\n" + "=" * 80)
    print("IMPORTANT MODULES NEEDING 80%+ COVERAGE")
    print("=" * 80)
    for filepath, lines, functions, desc in sorted(important_untested, key=lambda x: -x[1]):
        print(f"  {filepath}")
        print(f"    - {desc}")
        print(f"    - Lines: {lines}, Functions: {functions}")
    print(f"\nTotal important modules needing tests: {len(important_untested)}")
    
    print("\n" + "=" * 80)
    print("NICE-TO-HAVE MODULES (60%+ COVERAGE)")
    print("=" * 80)
    for filepath, lines, functions in sorted(nice_to_have_untested, key=lambda x: -x[1])[:20]:
        print(f"  {filepath} - Lines: {lines}, Functions: {functions}")
    print(f"\nTotal nice-to-have modules: {len(nice_to_have_untested)}")
    
    print("\n" + "=" * 80)
    print("OTHER UNTESTED MODULES")
    print("=" * 80)
    for filepath, lines, functions in sorted(other_untested, key=lambda x: -x[1])[:30]:
        print(f"  {filepath} - Lines: {lines}, Functions: {functions}")
    print(f"\nTotal other untested modules: {len(other_untested)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Critical modules needing tests: {len(critical_untested)}")
    print(f"Important modules needing tests: {len(important_untested)}")
    print(f"Nice-to-have modules needing tests: {len(nice_to_have_untested)}")
    print(f"Other modules needing tests: {len(other_untested)}")
    print(f"Total modules needing tests: {len(critical_untested) + len(important_untested) + len(nice_to_have_untested) + len(other_untested)}")


if __name__ == '__main__':
    main()
