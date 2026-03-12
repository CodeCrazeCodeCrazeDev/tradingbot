"""
Complete System Integrator
===========================

Integrates ALL modules in the trading bot:
- Recursive Evolution, Unified Evolution, AAMIS v3, TAMIC, Adaptive Systems
- Intelligence Core, Cognitive Architecture, Observability
- All other advanced systems

Fixes logging and Unicode encoding issues.
"""

import logging
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    # Set UTF-8 encoding for stdout/stderr
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    
    # Set environment variable for Python
    os.environ['PYTHONIOENCODING'] = 'utf-8'


def setup_logging_safe():
    """Setup logging with Unicode support"""
    
    # Create logs directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger with UTF-8 encoding
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / 'trading_bot.log',
                encoding='utf-8',
                mode='a'
            )
        ]
    )
    
    # Set encoding for all existing handlers
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))


# Setup logging first
setup_logging_safe()
logger = logging.getLogger(__name__)


class CompleteIntegrator:
    """
    Integrates all trading bot modules with proper error handling.
    """
    
    def __init__(self):
        self.modules = {}
        self.integration_status = {}
        
        logger.info("=" * 80)
        logger.info("COMPLETE SYSTEM INTEGRATOR - INITIALIZING")
        logger.info("=" * 80)
    
    def integrate_recursive_evolution(self):
        """Integrate recursive evolution system"""
        try:
            from trading_bot.recursive_evolution import RecursiveEvolutionOrchestrator
            
            orchestrator = RecursiveEvolutionOrchestrator()
            self.modules['recursive_evolution'] = orchestrator
            self.integration_status['recursive_evolution'] = 'success'
            logger.info("✓ Recursive Evolution integrated")
            return orchestrator
            
        except Exception as e:
            logger.error(f"✗ Recursive Evolution failed: {e}")
            self.integration_status['recursive_evolution'] = f'failed: {e}'
            return None
    
    def integrate_unified_evolution(self):
        """Integrate unified evolution system"""
        try:
            from trading_bot.unified_evolution import UnifiedEvolutionOrchestrator
            
            orchestrator = UnifiedEvolutionOrchestrator()
            self.modules['unified_evolution'] = orchestrator
            self.integration_status['unified_evolution'] = 'success'
            logger.info("✓ Unified Evolution integrated")
            return orchestrator
            
        except Exception as e:
            logger.error(f"✗ Unified Evolution failed: {e}")
            self.integration_status['unified_evolution'] = f'failed: {e}'
            return None
    
    def integrate_aamis_v3(self):
        """Integrate AAMIS v3"""
        try:
            from trading_bot.aamis_v3 import AAMISMasterOrchestrator
            
            aamis = AAMISMasterOrchestrator()
            self.modules['aamis_v3'] = aamis
            self.integration_status['aamis_v3'] = 'success'
            logger.info("✓ AAMIS v3 integrated")
            return aamis
            
        except Exception as e:
            logger.error(f"✗ AAMIS v3 failed: {e}")
            self.integration_status['aamis_v3'] = f'failed: {e}'
            return None
    
    def integrate_tamic(self):
        """Integrate TAMIC"""
        try:
            from trading_bot.tamic import TAMICOrchestrator
            
            tamic = TAMICOrchestrator()
            self.modules['tamic'] = tamic
            self.integration_status['tamic'] = 'success'
            logger.info("✓ TAMIC integrated")
            return tamic
            
        except Exception as e:
            logger.error(f"✗ TAMIC failed: {e}")
            self.integration_status['tamic'] = f'failed: {e}'
            return None
    
    def integrate_adaptive_systems(self):
        """Integrate adaptive systems"""
        try:
            # Try to import master_controller if it exists
            try:
                from trading_bot.adaptive_systems.master_controller import MasterController
                adaptive = MasterController()
            except:
                # Fallback to basic integration
                from trading_bot.adaptive_systems import AdaptiveLearningEngine
                adaptive = AdaptiveLearningEngine()
            
            self.modules['adaptive_systems'] = adaptive
            self.integration_status['adaptive_systems'] = 'success'
            logger.info("✓ Adaptive Systems integrated")
            return adaptive
            
        except Exception as e:
            logger.error(f"✗ Adaptive Systems failed: {e}")
            self.integration_status['adaptive_systems'] = f'failed: {e}'
            return None
    
    def integrate_intelligence_core(self):
        """Integrate intelligence core"""
        try:
            from trading_bot.intelligence_core import quick_start
            
            intel_core = quick_start()
            self.modules['intelligence_core'] = intel_core
            self.integration_status['intelligence_core'] = 'success'
            logger.info("✓ Intelligence Core integrated")
            return intel_core
            
        except Exception as e:
            logger.error(f"✗ Intelligence Core failed: {e}")
            self.integration_status['intelligence_core'] = f'failed: {e}'
            return None
    
    def integrate_cognitive_architecture(self):
        """Integrate cognitive architecture"""
        try:
            from trading_bot.cognitive_architecture import CognitiveOrchestrator
            
            cognitive = CognitiveOrchestrator()
            self.modules['cognitive_architecture'] = cognitive
            self.integration_status['cognitive_architecture'] = 'success'
            logger.info("✓ Cognitive Architecture integrated")
            return cognitive
            
        except Exception as e:
            logger.error(f"✗ Cognitive Architecture failed: {e}")
            self.integration_status['cognitive_architecture'] = f'failed: {e}'
            return None
    
    def integrate_observability(self):
        """Integrate observability"""
        try:
            from trading_bot.observability import ObservabilityManager
            
            observability = ObservabilityManager()
            self.modules['observability'] = observability
            self.integration_status['observability'] = 'success'
            logger.info("✓ Observability integrated")
            return observability
            
        except Exception as e:
            logger.error(f"✗ Observability failed: {e}")
            self.integration_status['observability'] = f'failed: {e}'
            return None
    
    def integrate_self_diagnostic(self):
        """Integrate self-diagnostic system"""
        try:
            from trading_bot.self_diagnostic import SelfDiagnosticManager
            
            diagnostic = SelfDiagnosticManager()
            self.modules['self_diagnostic'] = diagnostic
            self.integration_status['self_diagnostic'] = 'success'
            logger.info("✓ Self-Diagnostic integrated")
            return diagnostic
            
        except Exception as e:
            logger.error(f"✗ Self-Diagnostic failed: {e}")
            self.integration_status['self_diagnostic'] = f'failed: {e}'
            return None
    
    def integrate_eternal_evolution(self):
        """Integrate eternal evolution"""
        try:
            from trading_bot.eternal_evolution import EternalEvolutionOrchestrator
            
            # Initialize with empty config to avoid NoneType errors
            eternal = EternalEvolutionOrchestrator(config={})
            self.modules['eternal_evolution'] = eternal
            self.integration_status['eternal_evolution'] = 'success'
            logger.info("✓ Eternal Evolution integrated")
            return eternal
            
        except Exception as e:
            logger.error(f"✗ Eternal Evolution failed: {e}")
            self.integration_status['eternal_evolution'] = f'failed: {e}'
            return None
    
    def integrate_all(self):
        """Integrate all modules"""
        
        logger.info("\nStarting complete integration...")
        logger.info("-" * 80)
        
        # Core evolution systems
        self.integrate_recursive_evolution()
        self.integrate_unified_evolution()
        self.integrate_eternal_evolution()
        
        # Advanced trading systems
        self.integrate_aamis_v3()
        self.integrate_tamic()
        self.integrate_adaptive_systems()
        
        # Intelligence and cognitive
        self.integrate_intelligence_core()
        self.integrate_cognitive_architecture()
        
        # Monitoring and diagnostics
        self.integrate_observability()
        self.integrate_self_diagnostic()
        
        logger.info("-" * 80)
        logger.info("Integration complete!")
        logger.info("")
        
        # Print summary
        self.print_integration_summary()
        
        return self.modules
    
    def print_integration_summary(self):
        """Print integration summary"""
        
        logger.info("=" * 80)
        logger.info("INTEGRATION SUMMARY")
        logger.info("=" * 80)
        
        successful = []
        failed = []
        
        for module, status in self.integration_status.items():
            if status == 'success':
                successful.append(module)
            else:
                failed.append((module, status))
        
        logger.info(f"\n✓ Successfully integrated: {len(successful)}/{len(self.integration_status)}")
        for module in successful:
            logger.info(f"  ✓ {module}")
        
        if failed:
            logger.info(f"\n✗ Failed to integrate: {len(failed)}")
            for module, error in failed:
                logger.info(f"  ✗ {module}: {error}")
        
        logger.info("\n" + "=" * 80)
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        
        return {
            'total_modules': len(self.integration_status),
            'successful': sum(1 for s in self.integration_status.values() if s == 'success'),
            'failed': sum(1 for s in self.integration_status.values() if s != 'success'),
            'modules': self.integration_status,
            'available_modules': list(self.modules.keys())
        }


def quick_integrate():
    """Quick integration function"""
    
    integrator = CompleteIntegrator()
    modules = integrator.integrate_all()
    
    return integrator, modules


if __name__ == "__main__":
    # Run integration
    integrator, modules = quick_integrate()
    
    # Print final status
    status = integrator.get_status()
    logger.info(f"\nFinal Status: {status['successful']}/{status['total_modules']} modules integrated")
