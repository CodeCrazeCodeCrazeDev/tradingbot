"""
AlphaAlgo Offline RL - Validation and Auto-Run Script

This script:
1. Validates all Offline RL components
2. Checks dependencies
3. Runs comprehensive tests
4. Starts the continuous learning system
5. Monitors and reports status
"""

import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('offline_rl_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class OfflineRLValidator:
    """Validates Offline RL system components."""
    
    def __init__(self):
        self.results = {
            'dependencies': {},
            'modules': {},
            'integration': {},
            'tests': {}
        }
    
    def validate_dependencies(self) -> bool:
        """Check required dependencies."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING DEPENDENCIES")
        logger.info("="*80)
        
        required = {
            'numpy': 'numpy',
            'torch': 'torch',
            'd3rlpy': 'd3rlpy',
            'scipy': 'scipy',
            'matplotlib': 'matplotlib'
        }
        
        all_ok = True
        
        for name, import_name in required.items():
            try:
                mod = importlib.import_module(import_name)
                version = getattr(mod, '__version__', 'unknown')
                logger.info(f"✅ {name}: {version}")
                self.results['dependencies'][name] = {'status': 'OK', 'version': version}
            except ImportError:
                logger.error(f"❌ {name}: NOT INSTALLED")
                self.results['dependencies'][name] = {'status': 'MISSING'}
                all_ok = False
        
        return all_ok
    
    def validate_modules(self) -> bool:
        """Check all Offline RL modules exist."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING MODULES")
        logger.info("="*80)
        
        modules = [
            'trading_bot.ml.offline_rl.cql_agent',
            'trading_bot.ml.offline_rl.bcq_agent',
            'trading_bot.ml.offline_rl.iql_agent',
            'trading_bot.ml.offline_rl.ope',
            'trading_bot.ml.offline_rl.policy_selector',
            'trading_bot.ml.offline_rl.risk_adjusted_ope',
            'trading_bot.ml.offline_rl.continuous_learning_orchestrator',
            'trading_bot.ml.offline_rl.dataset_builder',
            'trading_bot.ml.offline_rl.replay_buffer'
        ]
        
        all_ok = True
        
        for module_name in modules:
            try:
                mod = importlib.import_module(module_name)
                logger.info(f"✅ {module_name}")
                self.results['modules'][module_name] = 'OK'
            except ImportError as e:
                logger.error(f"❌ {module_name}: {e}")
                self.results['modules'][module_name] = f'FAILED: {e}'
                all_ok = False
        
        return all_ok
    
    def validate_integration(self) -> bool:
        """Check integration module."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATING INTEGRATION")
        logger.info("="*80)
        
        try:
            from alphaalgo_offline_rl_integration import AlphaAlgoOfflineRLIntegration
            logger.info("✅ AlphaAlgo integration module loaded")
            self.results['integration']['module'] = 'OK'
            
            # Try to instantiate
            state_features = ['close', 'open', 'high', 'low', 'volume']
            integration = AlphaAlgoOfflineRLIntegration(
                state_features=state_features,
                min_buffer_size=100,
                buffer_size=1000
            )
            logger.info("✅ Integration instance created successfully")
            self.results['integration']['instantiation'] = 'OK'
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration validation failed: {e}")
            self.results['integration']['error'] = str(e)
            return False
    
    def run_component_tests(self) -> bool:
        """Run tests for each component."""
        logger.info("\n" + "="*80)
        logger.info("RUNNING COMPONENT TESTS")
        logger.info("="*80)
        
        all_ok = True
        
        # Test IQL Agent
        try:
            logger.info("\n--- Testing IQL Agent ---")
            from trading_bot.ml.offline_rl.iql_agent import IQLAgent
            import numpy as np
            
            agent = IQLAgent(state_dim=5, action_dim=3, use_d3rlpy=False)
            test_state = np.random.randn(5)
            action = agent.predict(test_state)
            
            logger.info(f"✅ IQL Agent: Action={action}")
            self.results['tests']['iql_agent'] = 'PASS'
            
        except Exception as e:
            logger.error(f"❌ IQL Agent test failed: {e}")
            self.results['tests']['iql_agent'] = f'FAIL: {e}'
            all_ok = False
        
        # Test CVaR Evaluator
        try:
            logger.info("\n--- Testing CVaR Evaluator ---")
            from trading_bot.ml.offline_rl.risk_adjusted_ope import CVaRPolicyEvaluator
            
            evaluator = CVaRPolicyEvaluator(alpha=0.05)
            logger.info("✅ CVaR Evaluator created")
            self.results['tests']['cvar_evaluator'] = 'PASS'
            
        except Exception as e:
            logger.error(f"❌ CVaR Evaluator test failed: {e}")
            self.results['tests']['cvar_evaluator'] = f'FAIL: {e}'
            all_ok = False
        
        # Test Orchestrator
        try:
            logger.info("\n--- Testing Orchestrator ---")
            from trading_bot.ml.offline_rl.continuous_learning_orchestrator import ContinuousLearningOrchestrator
            
            orchestrator = ContinuousLearningOrchestrator(
                state_dim=5,
                action_dim=3,
                min_buffer_size=100,
                buffer_size=1000
            )
            
            # Test data collection
            import numpy as np
            state = np.random.randn(5)
            action = 1
            reward = 0.1
            next_state = np.random.randn(5)
            done = False
            
            orchestrator.collect_experience(state, action, reward, next_state, done)
            
            logger.info(f"✅ Orchestrator: Buffer size={len(orchestrator.data_buffer['states'])}")
            self.results['tests']['orchestrator'] = 'PASS'
            
        except Exception as e:
            logger.error(f"❌ Orchestrator test failed: {e}")
            self.results['tests']['orchestrator'] = f'FAIL: {e}'
            all_ok = False
        
        return all_ok
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = "\n" + "="*80 + "\n"
        report += "OFFLINE RL VALIDATION REPORT\n"
        report += "="*80 + "\n\n"
        
        # Dependencies
        report += "## Dependencies\n\n"
        for name, result in self.results['dependencies'].items():
            status = result['status']
            version = result.get('version', 'N/A')
            symbol = "✅" if status == 'OK' else "❌"
            report += f"{symbol} {name}: {status} (v{version})\n"
        
        # Modules
        report += "\n## Modules\n\n"
        for name, result in self.results['modules'].items():
            symbol = "✅" if result == 'OK' else "❌"
            report += f"{symbol} {name}: {result}\n"
        
        # Integration
        report += "\n## Integration\n\n"
        for name, result in self.results['integration'].items():
            symbol = "✅" if result == 'OK' else "❌"
            report += f"{symbol} {name}: {result}\n"
        
        # Tests
        report += "\n## Component Tests\n\n"
        for name, result in self.results['tests'].items():
            symbol = "✅" if result == 'PASS' else "❌"
            report += f"{symbol} {name}: {result}\n"
        
        # Summary
        dep_ok = all(r['status'] == 'OK' for r in self.results['dependencies'].values())
        mod_ok = all(r == 'OK' for r in self.results['modules'].values())
        int_ok = all(r == 'OK' for r in self.results['integration'].values())
        test_ok = all(r == 'PASS' for r in self.results['tests'].values())
        
        all_ok = dep_ok and mod_ok and int_ok and test_ok
        
        report += "\n" + "="*80 + "\n"
        report += "OVERALL STATUS: " + ("✅ PASS" if all_ok else "❌ FAIL") + "\n"
        report += "="*80 + "\n"
        
        return report
    
    def run_full_validation(self) -> bool:
        """Run complete validation."""
        logger.info("\n" + "="*80)
        logger.info("STARTING FULL VALIDATION")
        logger.info("="*80)
        
        dep_ok = self.validate_dependencies()
        mod_ok = self.validate_modules()
        int_ok = self.validate_integration()
        test_ok = self.run_component_tests()
        
        report = self.generate_report()
        logger.info(report)
        
        # Save report
        with open('offline_rl_validation_report.txt', 'w') as f:
            f.write(report)
        
        logger.info("\n📄 Report saved to: offline_rl_validation_report.txt")
        
        return dep_ok and mod_ok and int_ok and test_ok


def main():
    """Main entry point."""
    print("\n" + "="*80)
    print("ALPHAALGO OFFLINE RL - VALIDATION & AUTO-RUN")
    print("="*80)
    
    # Run validation
    validator = OfflineRLValidator()
    validation_passed = validator.run_full_validation()
    
    if not validation_passed:
        logger.error("\n❌ VALIDATION FAILED - Cannot proceed")
        logger.error("Please fix the issues above and try again")
        return 1
    
    logger.info("\n✅ VALIDATION PASSED - System ready!")
    
    # Ask user if they want to run the system
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print("\nThe Offline RL system is ready to run.")
    print("\nOptions:")
    print("1. Run integration test (recommended)")
    print("2. Start continuous learning system (production)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        logger.info("\n🧪 Running integration test...")
        try:
            from alphaalgo_offline_rl_integration import main as integration_main
            integration_main()
        except Exception as e:
            logger.error(f"Integration test failed: {e}", exc_info=True)
            return 1
    
    elif choice == '2':
        logger.info("\n🚀 Starting continuous learning system...")
        logger.info("⚠️  This will run indefinitely. Press Ctrl+C to stop.")
        
        try:
            from alphaalgo_offline_rl_integration import AlphaAlgoOfflineRLIntegration
            import numpy as np
            import time
            
            # Initialize
            state_features = [
                'close', 'open', 'high', 'low', 'volume',
                'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower',
                'atr', 'adx', 'cci', 'stoch_k', 'stoch_d',
                'obv', 'mfi', 'willr', 'roc', 'trix'
            ]
            
            integration = AlphaAlgoOfflineRLIntegration(
                state_features=state_features,
                training_interval_hours=24,
                min_buffer_size=10000
            )
            
            logger.info("✅ System initialized - collecting data...")
            
            # Main loop (replace with actual trading data source)
            step = 0
            while True:
                # TODO: Replace with actual market data
                market_data = {
                    'close': 1.0 + np.random.randn() * 0.01,
                    'open': 1.0 + np.random.randn() * 0.01,
                    'high': 1.01 + np.random.randn() * 0.01,
                    'low': 0.99 + np.random.randn() * 0.01,
                    'volume': 1000 + np.random.randn() * 100,
                    'rsi': 50 + np.random.randn() * 10,
                    'macd': np.random.randn() * 0.001,
                    'macd_signal': np.random.randn() * 0.001,
                    'bb_upper': 1.02,
                    'bb_lower': 0.98,
                    'atr': 0.01,
                    'adx': 25 + np.random.randn() * 5,
                    'cci': np.random.randn() * 50,
                    'stoch_k': 50 + np.random.randn() * 20,
                    'stoch_d': 50 + np.random.randn() * 20,
                    'obv': 10000 + np.random.randn() * 1000,
                    'mfi': 50 + np.random.randn() * 10,
                    'willr': -50 + np.random.randn() * 20,
                    'roc': np.random.randn() * 0.01,
                    'trix': np.random.randn() * 0.001
                }
                
                action = integration.process_market_update(market_data)
                
                if step % 1000 == 0:
                    stats = integration.get_statistics()
                    logger.info(f"Step {step}: Buffer={stats['buffer_size']}, Trades={stats['total_trades']}, Policy={stats['deployed_policy']}")
                
                step += 1
                time.sleep(0.01)  # Simulate tick rate
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            integration.shutdown()
            logger.info("✅ Shutdown complete")
        except Exception as e:
            logger.error(f"System error: {e}", exc_info=True)
            return 1
    
    else:
        logger.info("\n👋 Exiting...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
