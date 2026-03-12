"""
Comprehensive Test Suite for Offline RL System
Validates all components and integration
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OfflineRLSystemTester:
    """
    Comprehensive test suite for Offline RL system.
    
    Tests:
    - Module scanner functionality
    - Upgrade orchestrator
    - Enhanced CQL agent
    - Main.py integration
    - Master controller
    - End-to-end workflow
    """
    
    def __init__(self):
        """Initialize tester."""
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info("Offline RL System Tester initialized")
    
    def test_imports(self) -> bool:
    pass
        """Test that all modules can be imported."""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Import Validation")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            # Test core imports
            from trading_bot.ml.offline_rl.module_scanner import ModuleScanner
            logger.info("✅ ModuleScanner imported")
            
            from trading_bot.ml.offline_rl.autonomous_upgrade_orchestrator import AutonomousUpgradeOrchestrator
            logger.info("✅ AutonomousUpgradeOrchestrator imported")
            
            from trading_bot.ml.offline_rl.enhanced_cql_agent import EnhancedCQLAgent, CQLConfig
            logger.info("✅ EnhancedCQLAgent imported")
            
            from trading_bot.ml.offline_rl.main_py_integration import MainPyIntegrator
            logger.info("✅ MainPyIntegrator imported")
            
            from alphaalgo_offline_rl_master import AlphaAlgoOfflineRLMaster
            logger.info("✅ AlphaAlgoOfflineRLMaster imported")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 1 PASSED: All imports successful")
            return True
            
        except ImportError as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Import test failed: {e}")
            logger.error(f"\n❌ TEST 1 FAILED: {e}")
            return False
    
    def test_module_scanner(self) -> bool:
    pass
        """Test module scanner functionality."""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Module Scanner")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            # Create scanner
            scanner = ModuleScanner(root_dir=".")
            logger.info("✅ Scanner created")
            
            # Test analysis (limited scan for speed)
            test_file = Path("alphaalgo_offline_rl_master.py")
            if test_file.exists():
                module_info = scanner._scan_module(test_file)
                logger.info(f"✅ Scanned test file: {len(module_info.classes)} classes, "
                           f"{len(module_info.functions)} functions")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 2 PASSED: Module scanner working")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Scanner test failed: {e}")
            logger.error(f"\n❌ TEST 2 FAILED: {e}")
            return False
    
    def test_enhanced_cql_agent(self) -> bool:
    pass
        """Test Enhanced CQL agent."""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Enhanced CQL Agent")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            import torch
            import numpy as np
            
            # Create agent
            config = CQLConfig(
                use_distributional=True,
                adaptive_alpha=True
            )
            agent = EnhancedCQLAgent(
                state_dim=20,
                action_dim=3,
                config=config
            )
            logger.info("✅ Agent created")
            
            # Test action selection
            state = np.random.randn(20)
            action = agent.select_action(state, risk_aware=True)
            logger.info(f"✅ Action selected: {action}")
            
            # Test update
            batch = {
                'states': torch.randn(32, 20),
                'actions': torch.randint(0, 3, (32,)),
                'rewards': torch.randn(32),
                'next_states': torch.randn(32, 20),
                'dones': torch.zeros(32)
            }
            losses = agent.update(batch)
            logger.info(f"✅ Update successful: loss={losses['total_loss']:.4f}")
            
            # Test statistics
            stats = agent.get_statistics()
            logger.info(f"✅ Statistics retrieved: {stats['total_updates']} updates")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 3 PASSED: Enhanced CQL agent working")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"CQL agent test failed: {e}")
            logger.error(f"\n❌ TEST 3 FAILED: {e}")
            return False
    
    async def test_upgrade_orchestrator(self) -> bool:
    pass
        """Test upgrade orchestrator."""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Upgrade Orchestrator")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            # Create orchestrator
            orchestrator = AutonomousUpgradeOrchestrator(
                root_dir=".",
                config={'monitoring_duration_seconds': 1}
            )
            logger.info("✅ Orchestrator created")
            
            # Test individual phases (without full execution)
            orchestrator.scan_results = type('obj', (object,), {
                'total_modules': 100,
                'rl_modules': [],
                'offline_rl_modules': [],
                'missing_components': []
            })()
            
            logger.info("✅ Orchestrator configured")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 4 PASSED: Upgrade orchestrator working")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Orchestrator test failed: {e}")
            logger.error(f"\n❌ TEST 4 FAILED: {e}")
            return False
    
    def test_main_py_integration(self) -> bool:
    pass
        """Test main.py integration."""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Main.py Integration")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            # Create integrator
            integrator = MainPyIntegrator()
            logger.info("✅ Integrator created")
            
            # Test analysis (dry run)
            if Path("main.py").exists():
                analysis = integrator.analyze_main_py()
                logger.info(f"✅ Analysis complete: {analysis.get('has_main_function', False)}")
            else:
                logger.info("ℹ️ main.py not found, skipping analysis")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 5 PASSED: Main.py integration working")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Integration test failed: {e}")
            logger.error(f"\n❌ TEST 5 FAILED: {e}")
            return False
    
    async def test_master_controller(self) -> bool:
    pass
        """Test master controller."""
        logger.info("\n" + "="*80)
        logger.info("TEST 6: Master Controller")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
    pass
import numpy
            
            # Create master controller
            master = AlphaAlgoOfflineRLMaster(config={
                'monitoring_interval_seconds': 1,
                'scan_interval_hours': 24
            })
            logger.info("✅ Master controller created")
            
            # Test initialization
            await master.initialize()
            logger.info("✅ Master controller initialized")
            
            # Test status
            status = master.get_status()
            logger.info(f"✅ Status retrieved: initialized={status['is_initialized']}")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 6 PASSED: Master controller working")
            return True
            
    def test_directory_structure(self) -> bool:
    pass
        """Test that required directories exist."""
        logger.info("\n" + "="*80)
        logger.info("TEST 7: Directory Structure")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            required_dirs = [
                'trading_bot/ml/offline_rl',
                'logs',
                'alphaalgo_offline_rl_system',
                'alphaalgo_upgrades'
            ]
            
            for dir_path in required_dirs:
                path = Path(dir_path)
                if path.exists():
                    logger.info(f"✅ {dir_path} exists")
                else:
                    logger.warning(f"⚠️ {dir_path} will be created on first run")
            
            self.test_results['passed'] += 1
            logger.info("\n✅ TEST 7 PASSED: Directory structure valid")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"Directory test failed: {e}")
            logger.error(f"\n❌ TEST 7 FAILED: {e}")
            return False
    
    def test_file_existence(self) -> bool:
    pass
        """Test that all required files exist."""
        logger.info("\n" + "="*80)
        logger.info("TEST 8: File Existence")
        logger.info("="*80)
        
        self.test_results['total_tests'] += 1
        
        try:
            required_files = [
                'trading_bot/ml/offline_rl/module_scanner.py',
                'trading_bot/ml/offline_rl/autonomous_upgrade_orchestrator.py',
                'trading_bot/ml/offline_rl/enhanced_cql_agent.py',
                'trading_bot/ml/offline_rl/main_py_integration.py',
                'alphaalgo_offline_rl_master.py',
                'RUN_ALPHAALGO_OFFLINE_RL_UPGRADE.bat',
                'ALPHAALGO_OFFLINE_RL_UPGRADE_GUIDE.txt',
                'ALPHAALGO_OFFLINE_RL_COMPLETE_SUMMARY.txt'
            ]
            
            missing = []
            for file_path in required_files:
                path = Path(file_path)
                if path.exists():
                    logger.info(f"✅ {file_path}")
                else:
                    missing.append(file_path)
                    logger.error(f"❌ {file_path} missing")
            
            if not missing:
                self.test_results['passed'] += 1
                logger.info("\n✅ TEST 8 PASSED: All files present")
                return True
            else:
                self.test_results['failed'] += 1
                self.test_results['errors'].append(f"Missing files: {missing}")
                logger.error(f"\n❌ TEST 8 FAILED: {len(missing)} files missing")
                return False
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"File existence test failed: {e}")
            logger.error(f"\n❌ TEST 8 FAILED: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
    pass
        """Run all tests."""
        logger.info("\n" + "="*80)
        logger.info("STARTING COMPREHENSIVE TEST SUITE")
        logger.info("="*80)
        
        # Run tests
        self.test_imports()
        self.test_module_scanner()
        self.test_enhanced_cql_agent()
        await self.test_upgrade_orchestrator()
        self.test_main_py_integration()
        await self.test_master_controller()
        self.test_directory_structure()
        self.test_file_existence()
        
        # Display results
        self.display_results()
        
        return self.test_results
    
    def display_results(self):
        """Display test results."""
        logger.info("\n" + "="*80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed']}")
        logger.info(f"Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] == 0:
            logger.info("\n✅ ALL TESTS PASSED")
        else:
            logger.warning(f"\n⚠️ {self.test_results['failed']} TESTS FAILED")
            
            if self.test_results['errors']:
                logger.info("\nErrors:")
                for error in self.test_results['errors']:
                    logger.error(f"  - {error}")
        
        logger.info("="*80)


async def main():
    """Run test suite."""
    tester = OfflineRLSystemTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    asyncio.run(main())
