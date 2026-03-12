"""
AlphaAlgo Offline RL System Validation Script

Validates all components and generates comprehensive report.
"""

import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Tuple
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlphaAlgoValidator:
    """Validates AlphaAlgo Offline RL system."""
    
    def __init__(self):
        self.results = {
            'modules': {},
            'dependencies': {},
            'integration': {},
            'functionality': {}
        }
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> Dict:
        """Run all validations."""
        logger.info("="*80)
        logger.info("ALPHAALGO OFFLINE RL SYSTEM VALIDATION")
        logger.info("="*80)
        
        self.validate_modules()
        self.validate_dependencies()
        self.validate_integration()
        self.validate_functionality()
        
        return self.generate_report()
    
    def validate_modules(self):
        """Validate all required modules exist."""
        logger.info("\n[1/4] Validating Modules...")
        
        required_modules = [
            'trading_bot.ml.offline_rl.cql_agent',
            'trading_bot.ml.offline_rl.iql_agent',
            'trading_bot.ml.offline_rl.bcq_agent',
            'trading_bot.ml.offline_rl.ope',
            'trading_bot.ml.offline_rl.risk_adjusted_ope',
            'trading_bot.ml.offline_rl.policy_selector',
            'trading_bot.ml.offline_rl.continuous_learning_orchestrator',
            'trading_bot.ml.offline_rl.dataset_builder',
            'trading_bot.ml.offline_rl.replay_buffer',
            'trading_bot.ml.offline_rl.alphaalgo_autonomous_system',
            'trading_bot.ml.offline_rl.state_builder',
            'trading_bot.ml.offline_rl.main_integration',
        ]
        
        for module_name in required_modules:
            try:
                module = importlib.import_module(module_name)
                self.results['modules'][module_name] = '✅ OK'
                logger.info(f"  ✅ {module_name}")
            except Exception as e:
                self.results['modules'][module_name] = f'❌ FAILED: {str(e)}'
                self.errors.append(f"Module {module_name}: {str(e)}")
                logger.error(f"  ❌ {module_name}: {str(e)}")
    
    def validate_dependencies(self):
        """Validate required dependencies."""
        logger.info("\n[2/4] Validating Dependencies...")
        
        required_deps = {
            'numpy': 'Core numerical computing',
            'pandas': 'Data manipulation',
            'scipy': 'Scientific computing',
            'torch': 'Deep learning framework',
        }
        
        optional_deps = {
            'd3rlpy': 'Advanced offline RL library',
        }
        
        # Check required
        for dep, description in required_deps.items():
            try:
                importlib.import_module(dep)
                self.results['dependencies'][dep] = '✅ OK'
                logger.info(f"  ✅ {dep}: {description}")
            except ImportError:
                self.results['dependencies'][dep] = '❌ MISSING'
                self.errors.append(f"Required dependency {dep} not found")
                logger.error(f"  ❌ {dep}: MISSING ({description})")
        
        # Check optional
        for dep, description in optional_deps.items():
            try:
                importlib.import_module(dep)
                self.results['dependencies'][dep] = '✅ OK (Optional)'
                logger.info(f"  ✅ {dep}: {description} (Optional)")
            except ImportError:
                self.results['dependencies'][dep] = '⚠️  MISSING (Optional)'
                self.warnings.append(f"Optional dependency {dep} not found")
                logger.warning(f"  ⚠️  {dep}: MISSING ({description}) - Optional")
    
    def validate_integration(self):
        """Validate integration points."""
        logger.info("\n[3/4] Validating Integration...")
        
        # Check __init__.py exports
        try:
            from trading_bot.ml.offline_rl import (
                CQLAgent, IQLAgent, BCQAgent,
                ImportanceSampling, DoublyRobust, FittedQEvaluation,
                CVaRPolicyEvaluator, RiskAdjustedPolicySelector,
                ContinuousLearningOrchestrator,
                AlphaAlgoAutonomousSystem, create_alphaalgo_system,
                MarketStateBuilder, ActionMapper, RewardCalculator
            )
            self.results['integration']['__init__ exports'] = '✅ OK'
            logger.info("  ✅ All exports available in __init__.py")
        except Exception as e:
            self.results['integration']['__init__ exports'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"Integration exports: {str(e)}")
            logger.error(f"  ❌ Integration exports failed: {str(e)}")
        
        # Check main integration
        try:
            from trading_bot.ml.offline_rl.main_integration import (
                AlphaAlgoTradingIntegration,
                create_alphaalgo_trader
            )
            self.results['integration']['main.py integration'] = '✅ OK'
            logger.info("  ✅ Main.py integration available")
        except Exception as e:
            self.results['integration']['main.py integration'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"Main integration: {str(e)}")
            logger.error(f"  ❌ Main integration failed: {str(e)}")
    
    def validate_functionality(self):
        """Validate core functionality."""
        logger.info("\n[4/4] Validating Functionality...")
        
        # Test state builder
        try:
            from trading_bot.ml.offline_rl import MarketStateBuilder
            import pandas as pd
            import numpy as np
            
            builder = MarketStateBuilder(lookback_window=50)
            data = pd.DataFrame({
                'close': np.random.randn(100).cumsum() + 100,
                'volume': np.random.randint(1000, 10000, 100),
                'rsi': np.random.uniform(30, 70, 100),
            })
            state = builder.build_state(data)
            
            if len(state) > 0:
                self.results['functionality']['State Builder'] = '✅ OK'
                logger.info(f"  ✅ State Builder: Generated state with {len(state)} features")
            else:
                raise ValueError("Empty state generated")
                
        except Exception as e:
            self.results['functionality']['State Builder'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"State Builder: {str(e)}")
            logger.error(f"  ❌ State Builder failed: {str(e)}")
        
        # Test action mapper
        try:
            from trading_bot.ml.offline_rl import ActionMapper
            
            mapper = ActionMapper('simple')
            action = mapper.map_action(1)
            
            if 'type' in action and 'size' in action:
                self.results['functionality']['Action Mapper'] = '✅ OK'
                logger.info(f"  ✅ Action Mapper: Mapped action to {action}")
            else:
                raise ValueError("Invalid action mapping")
                
        except Exception as e:
            self.results['functionality']['Action Mapper'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"Action Mapper: {str(e)}")
            logger.error(f"  ❌ Action Mapper failed: {str(e)}")
        
        # Test reward calculator
        try:
            from trading_bot.ml.offline_rl import RewardCalculator
            
            calc = RewardCalculator('sharpe')
            reward = calc.calculate_reward(pnl=10.0, transaction_cost=0.5)
            
            if isinstance(reward, (int, float)):
                self.results['functionality']['Reward Calculator'] = '✅ OK'
                logger.info(f"  ✅ Reward Calculator: Calculated reward = {reward:.4f}")
            else:
                raise ValueError("Invalid reward type")
                
        except Exception as e:
            self.results['functionality']['Reward Calculator'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"Reward Calculator: {str(e)}")
            logger.error(f"  ❌ Reward Calculator failed: {str(e)}")
        
        # Test autonomous system creation
        try:
            from trading_bot.ml.offline_rl import create_alphaalgo_system
            
            system = create_alphaalgo_system(state_dim=20, action_dim=3)
            
            if system is not None:
                self.results['functionality']['Autonomous System'] = '✅ OK'
                logger.info("  ✅ Autonomous System: Created successfully")
            else:
                raise ValueError("Failed to create system")
                
        except Exception as e:
            self.results['functionality']['Autonomous System'] = f'❌ FAILED: {str(e)}'
            self.errors.append(f"Autonomous System: {str(e)}")
            logger.error(f"  ❌ Autonomous System failed: {str(e)}")
    
    def generate_report(self) -> Dict:
        """Generate validation report."""
        logger.info("\n" + "="*80)
        logger.info("VALIDATION REPORT")
        logger.info("="*80)
        
        # Count results
        total_checks = sum(len(v) for v in self.results.values())
        passed_checks = sum(
            1 for section in self.results.values()
            for result in section.values()
            if '✅' in result
        )
        failed_checks = len(self.errors)
        warning_checks = len(self.warnings)
        
        logger.info(f"\nTotal Checks: {total_checks}")
        logger.info(f"✅ Passed: {passed_checks}")
        logger.info(f"❌ Failed: {failed_checks}")
        logger.info(f"⚠️  Warnings: {warning_checks}")
        
        # Overall status
        if failed_checks == 0:
            status = "✅ SYSTEM READY FOR DEPLOYMENT"
            logger.info(f"\n{status}")
        else:
            status = "❌ SYSTEM NOT READY - FIX ERRORS FIRST"
            logger.error(f"\n{status}")
        
        # Print errors
        if self.errors:
            logger.error("\nERRORS:")
            for error in self.errors:
                logger.error(f"  ❌ {error}")
        
        # Print warnings
        if self.warnings:
            logger.warning("\nWARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  ⚠️  {warning}")
        
        # Detailed results
        logger.info("\nDETAILED RESULTS:")
        for section, checks in self.results.items():
            logger.info(f"\n{section.upper()}:")
            for check, result in checks.items():
                logger.info(f"  {check}: {result}")
        
        logger.info("\n" + "="*80)
        
        # Save report
        report = {
            'timestamp': str(pd.Timestamp.now()),
            'status': status,
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'warnings': warning_checks
            },
            'results': self.results,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        report_path = Path('alphaalgo_validation_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\n📊 Report saved to: {report_path}")
        
        return report


def main():
    """Run validation."""
    validator = AlphaAlgoValidator()
    report = validator.validate_all()
    
    # Exit code
    if report['summary']['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
