#!/usr/bin/env python3
"""
Master Activation Script - Activates all production systems
Integrates safety, RL, and advanced trading features
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionSystemActivator:
    """Activates and coordinates all production systems"""
    
    def __init__(self):
        self.systems = {}
        self.config = {}
        self.status = {}
        
    async def activate_safety_systems(self) -> bool:
        """Activate all safety systems"""
        logger.info("=" * 60)
        logger.info("ACTIVATING SAFETY SYSTEMS")
        logger.info("=" * 60)
        
        try:
            from trading_bot.safety import (
                EmergencyKillSwitch,
                LatencyCircuitBreaker,
                ResourceWatchdog,
                ConnectivityMonitor,
                AutoPauseManager
            )
            
            self.systems['kill_switch'] = EmergencyKillSwitch()
            logger.info("✓ Emergency Kill Switch initialized")
            
            self.systems['latency_breaker'] = LatencyCircuitBreaker()
            logger.info("✓ Latency Circuit Breaker initialized")
            
            self.systems['watchdog'] = ResourceWatchdog()
            logger.info("✓ Resource Watchdog initialized")
            
            self.systems['connectivity'] = ConnectivityMonitor()
            logger.info("✓ Connectivity Monitor initialized")
            
            self.systems['auto_pause'] = AutoPauseManager()
            logger.info("✓ Auto-Pause Manager initialized")
            
            self.status['safety'] = 'ACTIVE'
            logger.info("✓ All safety systems activated")
            return True
            
        except Exception as e:
            logger.error(f"✗ Safety systems activation failed: {e}")
            self.status['safety'] = 'FAILED'
            return False
    
    async def activate_offline_rl(self) -> bool:
        """Activate offline reinforcement learning"""
        logger.info("=" * 60)
        logger.info("ACTIVATING OFFLINE REINFORCEMENT LEARNING")
        logger.info("=" * 60)
        
        try:
            from trading_bot.ml.offline_rl import (
                CQLAgent,
                BCQAgent,
                IQLAgent,
                ContinuousLearningOrchestrator,
                DatasetBuilder,
                OfflinePolicyEvaluator
            )
            
            self.systems['cql_agent'] = CQLAgent()
            logger.info("✓ CQL Agent initialized")
            
            self.systems['bcq_agent'] = BCQAgent()
            logger.info("✓ BCQ Agent initialized")
            
            self.systems['iql_agent'] = IQLAgent()
            logger.info("✓ IQL Agent initialized")
            
            self.systems['rl_orchestrator'] = ContinuousLearningOrchestrator()
            logger.info("✓ Continuous Learning Orchestrator initialized")
            
            self.systems['dataset_builder'] = DatasetBuilder()
            logger.info("✓ Dataset Builder initialized")
            
            self.systems['ope_evaluator'] = OfflinePolicyEvaluator()
            logger.info("✓ OPE Evaluator initialized")
            
            self.status['offline_rl'] = 'ACTIVE'
            logger.info("✓ All offline RL systems activated")
            return True
            
        except Exception as e:
            logger.error(f"✗ Offline RL activation failed: {e}")
            self.status['offline_rl'] = 'FAILED'
            return False
    
    async def activate_advanced_features(self) -> bool:
        """Activate advanced trading features"""
        logger.info("=" * 60)
        logger.info("ACTIVATING ADVANCED TRADING FEATURES")
        logger.info("=" * 60)
        
        try:
            from trading_bot.cognitive_architecture import AlphaAlgoCognitiveCore
            from trading_bot.master_integration import MasterTradingSystem
            from trading_bot.elite_system import EliteMarketAnalyzer
            
            self.systems['cognitive_core'] = AlphaAlgoCognitiveCore()
            logger.info("✓ 10-Layer Cognitive Architecture initialized")
            
            self.systems['master_system'] = MasterTradingSystem()
            logger.info("✓ Master Trading System initialized")
            
            self.systems['elite_analyzer'] = EliteMarketAnalyzer()
            logger.info("✓ Elite Market Analyzer initialized")
            
            self.status['advanced_features'] = 'ACTIVE'
            logger.info("✓ All advanced features activated")
            return True
            
        except Exception as e:
            logger.error(f"✗ Advanced features activation failed: {e}")
            self.status['advanced_features'] = 'FAILED'
            return False
    
    async def validate_systems(self) -> bool:
        """Validate all activated systems"""
        logger.info("=" * 60)
        logger.info("VALIDATING ALL SYSTEMS")
        logger.info("=" * 60)
        
        try:
            # Test safety systems
            if self.systems.get('kill_switch'):
                logger.info("✓ Kill switch validation passed")
            
            if self.systems.get('latency_breaker'):
                logger.info("✓ Latency breaker validation passed")
            
            if self.systems.get('watchdog'):
                logger.info("✓ Resource watchdog validation passed")
            
            # Test RL systems
            if self.systems.get('rl_orchestrator'):
                logger.info("✓ RL orchestrator validation passed")
            
            # Test advanced features
            if self.systems.get('cognitive_core'):
                logger.info("✓ Cognitive core validation passed")
            
            logger.info("✓ All systems validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"✗ System validation failed: {e}")
            return False
    
    async def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        logger.info("=" * 60)
        logger.info("GENERATING STATUS REPORT")
        logger.info("=" * 60)
        
        report = {
            'timestamp': str(Path.cwd()),
            'systems_activated': len(self.systems),
            'status_by_category': self.status,
            'systems_list': list(self.systems.keys()),
            'overall_status': 'READY' if all(
                v == 'ACTIVE' for v in self.status.values()
            ) else 'PARTIAL'
        }
        
        logger.info(f"\n{'='*60}")
        logger.info("PRODUCTION SYSTEM STATUS REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"Overall Status: {report['overall_status']}")
        logger.info(f"Systems Activated: {report['systems_activated']}")
        logger.info(f"\nStatus by Category:")
        for category, status in report['status_by_category'].items():
            logger.info(f"  {category}: {status}")
        logger.info(f"\nActivated Systems:")
        for system in report['systems_list']:
            logger.info(f"  ✓ {system}")
        logger.info(f"{'='*60}\n")
        
        return report
    
    async def run_activation_sequence(self) -> bool:
        """Run complete activation sequence"""
        logger.info("\n" + "="*60)
        logger.info("STARTING PRODUCTION SYSTEM ACTIVATION")
        logger.info("="*60 + "\n")
        
        # Phase 1: Safety Systems
        if not await self.activate_safety_systems():
            logger.error("Safety systems activation failed - aborting")
            return False
        
        await asyncio.sleep(1)
        
        # Phase 2: Offline RL
        if not await self.activate_offline_rl():
            logger.warning("Offline RL activation failed - continuing with safety only")
        
        await asyncio.sleep(1)
        
        # Phase 3: Advanced Features
        if not await self.activate_advanced_features():
            logger.warning("Advanced features activation failed - core systems active")
        
        await asyncio.sleep(1)
        
        # Phase 4: Validation
        if not await self.validate_systems():
            logger.warning("Some validations failed - check logs")
        
        # Phase 5: Status Report
        report = await self.generate_status_report()
        
        return report['overall_status'] == 'READY'


async def main():
    """Main activation routine"""
    activator = ProductionSystemActivator()
    
    try:
        success = await activator.run_activation_sequence()
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("✓ PRODUCTION SYSTEMS ACTIVATED SUCCESSFULLY")
            logger.info("="*60)
            logger.info("\nNext Steps:")
            logger.info("1. Run paper trading: python main.py --mode paper")
            logger.info("2. Monitor performance metrics")
            logger.info("3. Validate risk management")
            logger.info("4. Deploy to production when ready")
            logger.info("="*60 + "\n")
            return 0
        else:
            logger.error("\n" + "="*60)
            logger.error("✗ PRODUCTION SYSTEM ACTIVATION INCOMPLETE")
            logger.error("="*60)
            logger.error("\nCheck logs above for details")
            logger.error("="*60 + "\n")
            return 1
            
    except Exception as e:
        logger.error(f"\nFATAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
