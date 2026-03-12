"""
Unified Evolution Orchestrator
===============================

Master orchestrator that coordinates recursive evolution across all advanced systems:
- AAMIS v3, TAMIC, Adaptive Systems, Advanced Analysis, Advanced ML, Adversarial Decision

Integrates model evolution, system integration, and advanced optimization.
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .unified_model_evolver import (
    UnifiedModelEvolver,
    ModelType,
    ModelPerformance,
    EvolutionProposal
)
from .system_integrator import (
    SystemIntegrator,
    SystemType,
    CrossSystemLearning
)
from .advanced_model_optimizer import (
    AdvancedModelOptimizer,
    OptimizationMethod,
    HyperparameterSpace
)

# Import recursive evolution components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from recursive_evolution import (
    RecursiveEvolutionOrchestrator,
    EvolutionDimension
)

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """Configuration for unified evolution"""
    # Evolution settings
    evolution_interval_seconds: int = 3600
    max_concurrent_evolutions: int = 3
    enable_cross_system_learning: bool = True
    
    # Optimization settings
    default_optimization_method: OptimizationMethod = OptimizationMethod.BAYESIAN
    max_optimization_iterations: int = 100
    
    # Integration settings
    enable_knowledge_transfer: bool = True
    min_transfer_confidence: float = 0.7
    
    # Safety settings
    require_human_approval: bool = True
    enable_rollback: bool = True
    max_degradation_tolerance: float = 0.05


class UnifiedEvolutionOrchestrator:
    """
    Master orchestrator for unified evolution across all advanced systems.
    
    Coordinates:
    - Model evolution across all systems
    - Cross-system knowledge transfer
    - Advanced optimization
    - Recursive self-improvement
    """
    
    def __init__(self, config: Optional[EvolutionConfig] = None):
        self.config = config or EvolutionConfig()
        
        # Initialize components
        self.model_evolver = UnifiedModelEvolver()
        self.system_integrator = SystemIntegrator()
        self.optimizer = AdvancedModelOptimizer()
        self.recursive_evolver = RecursiveEvolutionOrchestrator()
        
        # Evolution state
        self.is_running = False
        self.evolution_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.system_performance: Dict[SystemType, List[float]] = {}
        self.evolution_cycles: int = 0
        
        logger.info("UnifiedEvolutionOrchestrator initialized")
    
    async def start(self):
        """Start unified evolution"""
        
        if self.is_running:
            logger.warning("Evolution already running")
            return
        
        self.is_running = True
        logger.info("Starting unified evolution system")
        
        # Start recursive evolution
        await self.recursive_evolver.start_continuous_evolution(
            self.config.evolution_interval_seconds
        )
        
        # Start unified evolution loop
        self.evolution_task = asyncio.create_task(self._evolution_loop())
    
    async def stop(self):
        """Stop unified evolution"""
        
        self.is_running = False
        
        # Stop recursive evolution
        await self.recursive_evolver.stop_continuous_evolution()
        
        # Stop unified evolution
        if self.evolution_task:
            self.evolution_task.cancel()
            try:
                await self.evolution_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Unified evolution stopped")
    
    async def _evolution_loop(self):
        """Main unified evolution loop"""
        
        while self.is_running:
            try:
                # Run one unified evolution cycle
                await self.run_unified_cycle()
                
                # Wait for next cycle
                await asyncio.sleep(self.config.evolution_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in evolution loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def run_unified_cycle(self) -> Dict[str, Any]:
        """Run one complete unified evolution cycle"""
        
        cycle_start = datetime.utcnow()
        self.evolution_cycles += 1
        
        logger.info(f"Starting unified evolution cycle #{self.evolution_cycles}")
        
        results = {
            'cycle_number': self.evolution_cycles,
            'start_time': cycle_start,
            'phases': {}
        }
        
        # Phase 1: Model Evolution
        model_results = await self._phase_model_evolution()
        results['phases']['model_evolution'] = model_results
        
        # Phase 2: Cross-System Learning
        if self.config.enable_cross_system_learning:
            learning_results = await self._phase_cross_system_learning()
            results['phases']['cross_system_learning'] = learning_results
        
        # Phase 3: Advanced Optimization
        optimization_results = await self._phase_advanced_optimization()
        results['phases']['advanced_optimization'] = optimization_results
        
        # Phase 4: Integration and Deployment
        integration_results = await self._phase_integration()
        results['phases']['integration'] = integration_results
        
        # Phase 5: Performance Validation
        validation_results = await self._phase_validation()
        results['phases']['validation'] = validation_results
        
        results['end_time'] = datetime.utcnow()
        results['duration_seconds'] = (results['end_time'] - cycle_start).total_seconds()
        
        logger.info(f"Unified evolution cycle #{self.evolution_cycles} complete")
        
        return results
    
    async def _phase_model_evolution(self) -> Dict[str, Any]:
        """Phase 1: Evolve models across all systems"""
        
        logger.info("Phase 1: Model Evolution")
        
        # Identify evolution opportunities
        opportunities = self.model_evolver.identify_evolution_opportunities()
        
        # Generate proposals
        proposals = []
        for model_type, priority in opportunities[:self.config.max_concurrent_evolutions]:
            proposal = self.model_evolver.generate_evolution_proposal(model_type)
            proposals.append(proposal)
        
        # Test proposals
        test_results = []
        for proposal in proposals:
            success, performance = self.model_evolver.test_evolution(proposal, test_data=None)
            test_results.append({
                'proposal_id': proposal.proposal_id,
                'model_type': proposal.model_type.value,
                'success': success,
                'improvement': performance.overall_score() - proposal.baseline_performance.overall_score()
                    if proposal.baseline_performance else 0
            })
        
        return {
            'opportunities_found': len(opportunities),
            'proposals_generated': len(proposals),
            'tests_passed': sum(1 for r in test_results if r['success']),
            'test_results': test_results
        }
    
    async def _phase_cross_system_learning(self) -> Dict[str, Any]:
        """Phase 2: Cross-system knowledge transfer"""
        
        logger.info("Phase 2: Cross-System Learning")
        
        transfers = []
        
        # Discover transferable knowledge from each system
        for source_system in SystemType:
            if source_system not in self.system_integrator.systems:
                continue
            
            knowledge_items = self.system_integrator.discover_transferable_knowledge(source_system)
            
            for knowledge in knowledge_items:
                # Transfer to applicable systems
                for target_system in knowledge['applicable_to']:
                    if target_system in self.system_integrator.systems:
                        learning = self.system_integrator.transfer_knowledge(
                            source_system,
                            target_system,
                            knowledge['type'],
                            {'description': knowledge['description']}
                        )
                        if learning:
                            transfers.append(learning)
        
        # Optimize integration points
        self.system_integrator.optimize_integration_points()
        
        successful_transfers = sum(1 for t in transfers if t.success)
        
        return {
            'total_transfers': len(transfers),
            'successful_transfers': successful_transfers,
            'success_rate': successful_transfers / len(transfers) if transfers else 0,
            'avg_improvement': np.mean([t.improvement for t in transfers if t.success])
                if successful_transfers > 0 else 0
        }
    
    async def _phase_advanced_optimization(self) -> Dict[str, Any]:
        """Phase 3: Advanced hyperparameter optimization"""
        
        logger.info("Phase 3: Advanced Optimization")
        
        optimizations = []
        
        # Select models for optimization
        for model_type in [ModelType.ADAPTIVE_META, ModelType.ML_ENSEMBLE, ModelType.AAMIS_INTELLIGENCE]:
            if model_type not in self.model_evolver.models:
                continue
            
            # Define search space (simplified)
            search_space = [
                HyperparameterSpace(
                    name='learning_rate',
                    param_type='continuous',
                    min_value=1e-5,
                    max_value=1e-2,
                    distribution='log_uniform'
                ),
                HyperparameterSpace(
                    name='batch_size',
                    param_type='discrete',
                    min_value=16,
                    max_value=128
                ),
                HyperparameterSpace(
                    name='dropout_rate',
                    param_type='continuous',
                    min_value=0.1,
                    max_value=0.5
                )
            ]
            
            # Objective function (simplified)
            def objective(params):
                return np.random.uniform(0.6, 0.9)  # Simulate evaluation
            
            # Optimize
            result = self.optimizer.optimize(
                objective,
                search_space,
                self.config.default_optimization_method,
                max_iterations=50
            )
            
            optimizations.append({
                'model_type': model_type.value,
                'method': result.method.value,
                'best_score': result.best_score,
                'iterations': result.iterations
            })
        
        return {
            'optimizations_performed': len(optimizations),
            'optimization_details': optimizations
        }
    
    async def _phase_integration(self) -> Dict[str, Any]:
        """Phase 4: Integrate improvements"""
        
        logger.info("Phase 4: Integration")
        
        implemented = []
        
        # Implement approved evolutions
        for proposal in self.model_evolver.successful_evolutions:
            if proposal.status == "approved":
                success = self.model_evolver.implement_evolution(proposal)
                if success:
                    implemented.append(proposal.proposal_id)
        
        return {
            'implementations': len(implemented),
            'implemented_proposals': implemented
        }
    
    async def _phase_validation(self) -> Dict[str, Any]:
        """Phase 5: Validate performance"""
        
        logger.info("Phase 5: Validation")
        
        validation_results = {}
        
        # Check for performance degradation
        degradations = []
        improvements = []
        
        for model_type in ModelType:
            if model_type not in self.model_evolver.performance_history:
                continue
            
            history = self.model_evolver.performance_history[model_type]
            if len(history) < 2:
                continue
            
            current = history[-1].overall_score()
            previous = history[-2].overall_score()
            change = current - previous
            
            if change < -self.config.max_degradation_tolerance:
                degradations.append({
                    'model_type': model_type.value,
                    'degradation': change
                })
            elif change > 0.01:
                improvements.append({
                    'model_type': model_type.value,
                    'improvement': change
                })
        
        validation_results['degradations'] = degradations
        validation_results['improvements'] = improvements
        validation_results['status'] = 'passed' if not degradations else 'degraded'
        
        return validation_results
    
    def register_aamis_v3(self, aamis_system: Any):
        """Register AAMIS v3 system"""
        
        self.system_integrator.register_system(
            SystemType.AAMIS_V3,
            aamis_system,
            {'version': 'v3', 'capabilities': ['intelligence', 'detection', 'execution']}
        )
        
        # Register AAMIS models
        self.model_evolver.register_model(
            ModelType.AAMIS_INTELLIGENCE,
            None,  # Placeholder
            'aamis_v3',
            {'component': 'intelligence'}
        )
        
        logger.info("AAMIS v3 registered")
    
    def register_tamic(self, tamic_system: Any):
        """Register TAMIC system"""
        
        self.system_integrator.register_system(
            SystemType.TAMIC,
            tamic_system,
            {'capabilities': ['time_decay', 'confidence', 'horizon']}
        )
        
        # Register TAMIC models
        self.model_evolver.register_model(
            ModelType.TAMIC_TIME_DECAY,
            None,
            'tamic',
            {'component': 'time_decay'}
        )
        
        logger.info("TAMIC registered")
    
    def register_adaptive_systems(self, adaptive_system: Any):
        """Register Adaptive Systems"""
        
        self.system_integrator.register_system(
            SystemType.ADAPTIVE_SYSTEMS,
            adaptive_system,
            {'capabilities': ['regime', 'pattern', 'sentiment', 'orderflow', 'meta']}
        )
        
        # Register Adaptive models
        for model_type in [ModelType.ADAPTIVE_REGIME, ModelType.ADAPTIVE_PATTERN,
                          ModelType.ADAPTIVE_META]:
            self.model_evolver.register_model(
                model_type,
                None,
                'adaptive_systems',
                {'component': model_type.value}
            )
        
        logger.info("Adaptive Systems registered")
    
    def register_advanced_ml(self, ml_system: Any):
        """Register Advanced ML system"""
        
        self.system_integrator.register_system(
            SystemType.ADVANCED_ML,
            ml_system,
            {'capabilities': ['ensemble', 'deep_learning', 'reinforcement', 'transfer']}
        )
        
        # Register ML models
        for model_type in [ModelType.ML_ENSEMBLE, ModelType.ML_DEEP_LEARNING,
                          ModelType.ML_REINFORCEMENT]:
            self.model_evolver.register_model(
                model_type,
                None,
                'advanced_ml',
                {'component': model_type.value}
            )
        
        logger.info("Advanced ML registered")
    
    def register_adversarial_decision(self, adversarial_system: Any):
        """Register Adversarial Decision system"""
        
        self.system_integrator.register_system(
            SystemType.ADVERSARIAL_DECISION,
            adversarial_system,
            {'capabilities': ['robust', 'defense', 'detection']}
        )
        
        # Register Adversarial models
        self.model_evolver.register_model(
            ModelType.ADVERSARIAL_ROBUST,
            None,
            'adversarial_decision',
            {'component': 'robust'}
        )
        
        logger.info("Adversarial Decision registered")
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get unified evolution status"""
        
        return {
            'is_running': self.is_running,
            'evolution_cycles': self.evolution_cycles,
            'systems_registered': len(self.system_integrator.systems),
            'models_tracked': len(self.model_evolver.models),
            
            # Component stats
            'model_evolution': self.model_evolver.get_evolution_stats(),
            'system_integration': self.system_integrator.get_integration_stats(),
            'optimization': self.optimizer.get_optimization_stats(),
            'recursive_evolution': self.recursive_evolver.get_evolution_status()
        }
    
    def export_unified_report(self, filepath: str):
        """Export comprehensive unified evolution report"""
        
        import json
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'status': self.get_unified_status(),
            'model_evolution_stats': self.model_evolver.get_evolution_stats(),
            'integration_stats': self.system_integrator.get_integration_stats(),
            'optimization_stats': self.optimizer.get_optimization_stats(),
            'knowledge_graph': self.system_integrator.visualize_knowledge_graph()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Unified evolution report exported to {filepath}")


async def quick_start_unified(config: Optional[Dict[str, Any]] = None) -> UnifiedEvolutionOrchestrator:
    """Quick start function for unified evolution"""
    
    if config:
        evolution_config = EvolutionConfig(**config)
    else:
        evolution_config = EvolutionConfig()
    
    orchestrator = UnifiedEvolutionOrchestrator(evolution_config)
    
    # Auto-start if configured
    if config and config.get('auto_start', False):
        await orchestrator.start()
    
    return orchestrator
