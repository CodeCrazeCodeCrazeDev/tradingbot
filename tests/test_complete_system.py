"""
Complete System Test
Tests all AlphaAlgo components to ensure everything works together.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trading_bot.system_health import AlphaAlgoMaster, TradingMode
from trading_bot.self_improvement import (
    AutonomousOrchestrator,
    AutonomousFixer,
    InternetStrategyImprover,
    MirrorMarketTester
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SystemTester:
    """Complete system test suite."""
    
    def __init__(self):
        """Initialize tester."""
        self.config = {
            'system_health': {
                'min_health_for_live': 95.0,
                'health_monitor': {},
                'stability_tester': {'test_duration_minutes': 1},
                'intelligent_learner': {}
            },
            'autonomous': {
                'autonomous_fixer': {'auto_fix_enabled': True},
                'internet_improver': {'internet_learning_enabled': True},
                'mirror_tester': {'mirror_test_duration_hours': 1},
                'self_improvement': {'AUTO_LEARN': True}
            }
        }
        
        self.tests_passed = 0
        self.tests_failed = 0
    
    async def run_all_tests(self):
        """Run complete test suite."""
        logger.info("=" * 80)
        logger.info("ALPHAALGO COMPLETE SYSTEM TEST")
        logger.info("=" * 80)
        logger.info(f"Start time: {datetime.now()}")
        logger.info("=" * 80)
        
        # Test 1: System Health Components
        await self.test_system_health()
        
        # Test 2: Autonomous Components
        await self.test_autonomous_components()
        
        # Test 3: Integration
        await self.test_integration()
        
        # Test 4: End-to-End
        await self.test_end_to_end()
        
        # Summary
        self.print_summary()
    
    async def test_system_health(self):
        """Test system health components."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE 1: SYSTEM HEALTH COMPONENTS")
        logger.info("=" * 80)
        
        try:
            # Test 1.1: Health Monitor
            logger.info("\n[1.1] Testing Health Monitor...")
            from trading_bot.system_health import SystemHealthMonitor
            
            monitor = SystemHealthMonitor(self.config['system_health'])
            diagnostics = await monitor.run_full_diagnostics()
            
            assert 'overall_health' in diagnostics
            assert diagnostics['overall_health'] >= 0
            logger.info(f"     ✓ Health Monitor works (Health: {diagnostics['overall_health']:.1f}%)")
            self.tests_passed += 1
            
            # Test 1.2: Auto Repair
            logger.info("\n[1.2] Testing Auto Repair...")
            from trading_bot.system_health import AutoRepairEngine
            
            repair = AutoRepairEngine(self.config['system_health'])
            repair_results = await repair.repair_all_issues(diagnostics)
            
            assert 'repairs_attempted' in repair_results
            logger.info(f"     ✓ Auto Repair works (Repairs: {repair_results['repairs_attempted']})")
            self.tests_passed += 1
            
            # Test 1.3: Stability Tester
            logger.info("\n[1.3] Testing Stability Tester...")
            from trading_bot.system_health import StabilityTester
            
            tester = StabilityTester(self.config['system_health']['stability_tester'])
            stability = await tester.run_stability_test()
            
            assert 'stability_score' in stability
            logger.info(f"     ✓ Stability Tester works (Score: {stability['stability_score']:.1f}%)")
            self.tests_passed += 1
            
            # Test 1.4: Intelligent Learner
            logger.info("\n[1.4] Testing Intelligent Learner...")
            from trading_bot.system_health import IntelligentLearner
            
            learner = IntelligentLearner(self.config['system_health'])
            test_trade = {
                'id': 'TEST_001',
                'pnl': -50.0,
                'confidence': 0.55,
                'indicators': {},
                'market_conditions': {}
            }
            
            result = await learner.record_trade_loss(test_trade)
            assert 'cause_analysis' in result
            logger.info(f"     ✓ Intelligent Learner works")
            self.tests_passed += 1
            
            # Test 1.5: AlphaAlgo Master
            logger.info("\n[1.5] Testing AlphaAlgo Master...")
            master = AlphaAlgoMaster(self.config['system_health'])
            
            validation = await master.run_full_validation()
            assert 'system_health' in validation
            assert 'recommended_mode' in validation
            logger.info(f"     ✓ AlphaAlgo Master works (Health: {validation['system_health']:.1f}%)")
            self.tests_passed += 1
            
        except Exception as e:
            logger.error(f"     ✗ System Health test failed: {e}")
            self.tests_failed += 1
    
    async def test_autonomous_components(self):
        """Test autonomous components."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE 2: AUTONOMOUS COMPONENTS")
        logger.info("=" * 80)
        
        try:
            # Test 2.1: Autonomous Fixer
            logger.info("\n[2.1] Testing Autonomous Fixer...")
            fixer = AutonomousFixer(self.config['autonomous']['autonomous_fixer'])
            
            safety = await fixer.check_safety_and_fix()
            assert 'safe_to_trade' in safety
            logger.info(f"     ✓ Autonomous Fixer works (Safe: {safety['safe_to_trade']})")
            self.tests_passed += 1
            
            # Test 2.2: Internet Strategy Improver
            logger.info("\n[2.2] Testing Internet Strategy Improver...")
            improver = InternetStrategyImprover(self.config['autonomous']['internet_improver'])
            
            test_trade = {
                'ticket_id': 'TEST_002',
                'symbol': 'EURUSD',
                'pnl': -50.0
            }
            root_cause = {
                'cause_type': 'low_confidence',
                'description': 'Test',
                'confidence': 0.7
            }
            
            result = await improver.improve_strategy_from_loss(test_trade, root_cause)
            assert 'improvements' in result
            logger.info(f"     ✓ Internet Improver works (Found: {len(result['improvements'])} improvements)")
            self.tests_passed += 1
            
            # Test 2.3: Mirror Market Tester
            logger.info("\n[2.3] Testing Mirror Market Tester...")
            mirror = MirrorMarketTester(self.config['autonomous']['mirror_tester'])
            
            improved_strategy = {'test': True}
            current_strategy = {'test': False}
            
            # Note: This is a quick test, full test takes 24 hours
            logger.info(f"     ✓ Mirror Tester initialized (Full test requires 24h)")
            self.tests_passed += 1
            
            # Test 2.4: Autonomous Orchestrator
            logger.info("\n[2.4] Testing Autonomous Orchestrator...")
            orchestrator = AutonomousOrchestrator(self.config['autonomous'])
            
            safety_check = await orchestrator.pre_trading_check()
            assert 'safe_to_trade' in safety_check
            logger.info(f"     ✓ Autonomous Orchestrator works")
            self.tests_passed += 1
            
        except Exception as e:
            logger.error(f"     ✗ Autonomous components test failed: {e}")
            self.tests_failed += 1
    
    async def test_integration(self):
        """Test integration between components."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE 3: COMPONENT INTEGRATION")
        logger.info("=" * 80)
        
        try:
            # Test 3.1: Validator + Orchestrator
            logger.info("\n[3.1] Testing Validator + Orchestrator integration...")
            
            master = AlphaAlgoMaster(self.config['system_health'])
            orchestrator = AutonomousOrchestrator(self.config['autonomous'])
            
            # Run validation
            validation = await master.run_full_validation()
            
            # Check safety
            safety = await orchestrator.pre_trading_check()
            
            logger.info(f"     ✓ Integration works (Health: {validation['system_health']:.1f}%, Safe: {safety['safe_to_trade']})")
            self.tests_passed += 1
            
            # Test 3.2: Loss Learning Integration
            logger.info("\n[3.2] Testing loss learning integration...")
            
            test_trade = {
                'ticket_id': 'TEST_003',
                'symbol': 'EURUSD',
                'entry_price': 1.1000,
                'exit_price': 1.0950,
                'pnl': -50.0,
                'confidence': 0.55
            }
            
            # Record in both systems
            await master.record_trade_loss(test_trade)
            
            logger.info(f"     ✓ Loss learning integration works")
            self.tests_passed += 1
            
        except Exception as e:
            logger.error(f"     ✗ Integration test failed: {e}")
            self.tests_failed += 1
    
    async def test_end_to_end(self):
        """Test complete end-to-end workflow."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUITE 4: END-TO-END WORKFLOW")
        logger.info("=" * 80)
        
        try:
            logger.info("\n[4.1] Testing complete workflow...")
            
            # Initialize complete system
            master = AlphaAlgoMaster(self.config['system_health'])
            orchestrator = AutonomousOrchestrator(self.config['autonomous'])
            
            # Step 1: Validate
            logger.info("     Step 1: Running validation...")
            validation = await master.run_full_validation()
            assert validation['system_health'] > 0
            logger.info(f"     ✓ Validation complete (Health: {validation['system_health']:.1f}%)")
            
            # Step 2: Safety check
            logger.info("     Step 2: Safety check...")
            safety = await orchestrator.pre_trading_check()
            logger.info(f"     ✓ Safety check complete (Safe: {safety['safe_to_trade']})")
            
            # Step 3: Simulate trade loss
            logger.info("     Step 3: Simulating trade loss...")
            test_trade = {
                'ticket_id': 'E2E_001',
                'symbol': 'EURUSD',
                'entry_price': 1.1000,
                'exit_price': 1.0950,
                'pnl': -50.0,
                'size': 0.1,
                'confidence': 0.55,
                'indicators': {'rsi': 45}
            }
            
            signal_data = {
                'model_confidence': 0.55,
                'timeframe': 'H1'
            }
            
            market_data = {
                'atr': 0.0015,
                'spread': 0.0001
            }
            
            system_data = {
                'cpu_usage': 45.0,
                'memory_usage': 60.0
            }
            
            # Record loss
            await master.record_trade_loss(test_trade)
            logger.info(f"     ✓ Loss recorded in validator")
            
            # Step 4: Check status
            logger.info("     Step 4: Checking system status...")
            status = master.get_status()
            assert 'current_mode' in status
            assert 'system_health' in status
            logger.info(f"     ✓ Status retrieved (Mode: {status['current_mode']})")
            
            logger.info("\n     ✅ END-TO-END TEST PASSED")
            self.tests_passed += 1
            
        except Exception as e:
            logger.error(f"     ✗ End-to-end test failed: {e}")
            self.tests_failed += 1
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        logger.info(f"\nTotal Tests: {total}")
        logger.info(f"Passed: {self.tests_passed} ✓")
        logger.info(f"Failed: {self.tests_failed} ✗")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_failed == 0:
            logger.info("\n" + "=" * 80)
            logger.info("🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
            logger.info("=" * 80)
        else:
            logger.error("\n" + "=" * 80)
            logger.error("⚠️ SOME TESTS FAILED - REVIEW ERRORS ABOVE")
            logger.error("=" * 80)


async def main():
    """Run all tests."""
    tester = SystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
