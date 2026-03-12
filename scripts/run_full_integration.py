"""
Full System Integration Runner
==============================

Runs the complete integration of all trading_bot modules in the correct order.

Usage:
    python scripts/run_full_integration.py
    python scripts/run_full_integration.py --phase 1  # Run specific phase
    python scripts/run_full_integration.py --validate  # Validate only
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.integration.master_integrator import (
    MasterIntegrator,
    IntegrationPhase,
)
from trading_bot.integration.module_registry import (
    ModuleRegistry,
    ModuleLayer,
    PromotionState,
    get_module_registry,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullIntegrationRunner:
    """Runs the complete integration process."""
    
    def __init__(self):
        self.integrator = MasterIntegrator()
        self.registry = get_module_registry()
        self.start_time = time.time()
        self.results = {
            'phases_completed': [],
            'errors': [],
            'warnings': [],
            'stats': {},
        }
    
    async def run_phase_1(self) -> bool:
        """Phase 1: Foundation - Infrastructure, Security, Governance."""
        logger.info("=" * 60)
        logger.info("PHASE 1: FOUNDATION LAYER")
        logger.info("=" * 60)
        
        # Initialize the integrator
        await self.integrator.initialize()
        
        # Validate imports for foundation layers
        logger.info("Validating foundation module imports...")
        await self.integrator.validate_imports(max_per_batch=200)
        
        # Load foundation modules
        logger.info("Loading foundation modules...")
        foundation_layers = [
            ModuleLayer.INFRASTRUCTURE,
            ModuleLayer.GOVERNANCE,
        ]
        await self.integrator.load_modules(layers=foundation_layers)
        
        self.results['phases_completed'].append('phase_1_foundation')
        self.results['stats']['phase_1'] = {
            'loaded': self.integrator.stats['loaded'],
            'failed': self.integrator.stats['failed'],
        }
        
        return True
    
    async def run_phase_2(self) -> bool:
        """Phase 2: Data Infrastructure."""
        logger.info("=" * 60)
        logger.info("PHASE 2: DATA INFRASTRUCTURE")
        logger.info("=" * 60)
        
        # Load data foundation modules
        await self.integrator.load_modules(layers=[ModuleLayer.DATA_FOUNDATION])
        
        self.results['phases_completed'].append('phase_2_data')
        self.results['stats']['phase_2'] = {
            'loaded': self.integrator.stats['loaded'],
            'failed': self.integrator.stats['failed'],
        }
        
        return True
    
    async def run_phase_3(self) -> bool:
        """Phase 3: Risk & Execution."""
        logger.info("=" * 60)
        logger.info("PHASE 3: RISK & EXECUTION")
        logger.info("=" * 60)
        
        # Load risk and execution modules
        await self.integrator.load_modules(layers=[
            ModuleLayer.RISK_SAFETY,
            ModuleLayer.EXECUTION,
        ])
        
        self.results['phases_completed'].append('phase_3_risk_execution')
        self.results['stats']['phase_3'] = {
            'loaded': self.integrator.stats['loaded'],
            'failed': self.integrator.stats['failed'],
        }
        
        return True
    
    async def run_phase_4(self) -> bool:
        """Phase 4: Signals & AI/ML."""
        logger.info("=" * 60)
        logger.info("PHASE 4: SIGNALS & AI/ML")
        logger.info("=" * 60)
        
        # Load signal generation and intelligence modules
        await self.integrator.load_modules(layers=[
            ModuleLayer.SIGNAL_GENERATION,
            ModuleLayer.INTELLIGENCE_CORE,
        ])
        
        self.results['phases_completed'].append('phase_4_signals_ai')
        self.results['stats']['phase_4'] = {
            'loaded': self.integrator.stats['loaded'],
            'failed': self.integrator.stats['failed'],
        }
        
        return True
    
    async def run_phase_5(self) -> bool:
        """Phase 5: Orchestration & Advanced Systems."""
        logger.info("=" * 60)
        logger.info("PHASE 5: ORCHESTRATION & ADVANCED SYSTEMS")
        logger.info("=" * 60)
        
        # Load orchestration modules
        await self.integrator.load_modules(layers=[ModuleLayer.ORCHESTRATION])
        
        self.results['phases_completed'].append('phase_5_orchestration')
        self.results['stats']['phase_5'] = {
            'loaded': self.integrator.stats['loaded'],
            'failed': self.integrator.stats['failed'],
        }
        
        return True
    
    async def run_phase_6(self) -> bool:
        """Phase 6: Wire all modules together."""
        logger.info("=" * 60)
        logger.info("PHASE 6: WIRING MODULES")
        logger.info("=" * 60)
        
        await self.integrator.wire_modules()
        
        self.results['phases_completed'].append('phase_6_wiring')
        
        return True
    
    async def run_all_phases(self) -> bool:
        """Run all integration phases."""
        try:
            await self.run_phase_1()
            await self.run_phase_2()
            await self.run_phase_3()
            await self.run_phase_4()
            await self.run_phase_5()
            await self.run_phase_6()
            return True
        except Exception as e:
            logger.error(f"Integration failed: {e}")
            self.results['errors'].append(str(e))
            return False
    
    async def validate_only(self) -> Dict:
        """Run validation without full integration."""
        logger.info("=" * 60)
        logger.info("VALIDATION MODE")
        logger.info("=" * 60)
        
        # Initialize
        await self.integrator.initialize()
        
        # Validate all imports
        counts = await self.integrator.validate_imports(max_per_batch=500)
        
        return {
            'validation_counts': counts,
            'registry_report': self.registry.status_report(),
        }
    
    def generate_report(self) -> Dict:
        """Generate final integration report."""
        elapsed = time.time() - self.start_time
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'phases_completed': self.results['phases_completed'],
            'integration_stats': self.integrator.stats,
            'registry_report': self.registry.status_report(),
            'services_count': len(self.integrator.services),
            'errors': self.results['errors'],
            'warnings': self.results['warnings'],
            'phase_stats': self.results['stats'],
        }
        
        return report
    
    def save_report(self, output_path: str) -> None:
        """Save the integration report."""
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved to: {output_path}")
    
    def print_summary(self) -> None:
        """Print integration summary."""
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("INTEGRATION SUMMARY")
        print("=" * 60)
        print(f"Elapsed Time: {report['elapsed_seconds']} seconds")
        print(f"Phases Completed: {len(report['phases_completed'])}")
        print(f"Services Loaded: {report['services_count']}")
        print(f"Errors: {len(report['errors'])}")
        
        print("\nIntegration Stats:")
        for key, value in report['integration_stats'].items():
            print(f"  {key}: {value}")
        
        print("\nRegistry Summary:")
        reg = report['registry_report']
        print(f"  Total Modules: {reg['total_modules']}")
        print(f"  Quarantined: {reg['quarantined']}")
        print(f"  Promoted: {reg['promoted']}")
        
        print("\nBy Layer:")
        for layer, count in sorted(reg['by_layer'].items()):
            print(f"  {layer}: {count}")
        
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description='Run full system integration')
    parser.add_argument('--phase', type=int, help='Run specific phase (1-6)')
    parser.add_argument('--validate', action='store_true', help='Validation only')
    parser.add_argument('--output', type=str, help='Output report path')
    args = parser.parse_args()
    
    runner = FullIntegrationRunner()
    
    if args.validate:
        result = await runner.validate_only()
        print(json.dumps(result, indent=2, default=str))
        return
    
    if args.phase:
        phase_methods = {
            1: runner.run_phase_1,
            2: runner.run_phase_2,
            3: runner.run_phase_3,
            4: runner.run_phase_4,
            5: runner.run_phase_5,
            6: runner.run_phase_6,
        }
        if args.phase in phase_methods:
            await phase_methods[args.phase]()
        else:
            print(f"Invalid phase: {args.phase}")
            return
    else:
        await runner.run_all_phases()
    
    # Print summary
    runner.print_summary()
    
    # Save report
    output_path = args.output or f"docs/integration/integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    runner.save_report(output_path)


if __name__ == '__main__':
    asyncio.run(main())
