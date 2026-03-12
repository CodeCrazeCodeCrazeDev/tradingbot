"""
Recursive Improvement Orchestrator

Master orchestrator that coordinates all recursive improvement systems and
integrates them into the trading bot.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .recursive_core import RecursiveImprovementCore, ImprovementDimension
from .learning_recursion import RecursiveLearningEngine
from .strategy_recursion import RecursiveStrategyEvolution
from .risk_recursion import RecursiveRiskOptimization
from .execution_recursion import RecursiveExecutionOptimization
from .architecture_recursion import RecursiveArchitectureEvolution
from .meta_recursion import MetaRecursiveController
from .harmful_behavior_guard import QwenHarmMonitor, ImmutableSafetyFloors

logger = logging.getLogger(__name__)


class RecursiveImprovementOrchestrator:
    """
    Master orchestrator for recursive self-improvement.
    
    Coordinates all recursive improvement systems:
    - Core recursive improvement
    - Learning recursion
    - Strategy evolution
    - Risk optimization
    - Execution optimization
    - Architecture evolution
    - Meta-recursive control
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize all recursive systems
        self.core = RecursiveImprovementCore(self.config.get('core', {}))
        self.learning = RecursiveLearningEngine(self.config.get('learning', {}))
        self.strategy = RecursiveStrategyEvolution(self.config.get('strategy', {}))
        self.risk = RecursiveRiskOptimization(self.config.get('risk', {}))
        self.execution = RecursiveExecutionOptimization(self.config.get('execution', {}))
        self.architecture = RecursiveArchitectureEvolution(self.config.get('architecture', {}))
        self.meta = MetaRecursiveController(self.config.get('meta', {}))
        
        # QwenCodeMender Harm Monitor - guards ALL improvement cycles
        self.harm_monitor = QwenHarmMonitor(self.config.get('harm_monitor', {}))
        
        # Integration state
        self.improvement_cycles: List[Dict[str, Any]] = []
        self.integration_points: Dict[str, Any] = {}
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False
        
        # Verify safety floors on init
        assert ImmutableSafetyFloors.verify_integrity(), "SAFETY FLOORS COMPROMISED ON INIT"
        
        logger.info("RecursiveImprovementOrchestrator initialized with QwenCodeMender Harm Monitor")
    
    async def start(self):
        """Start the recursive improvement system"""
        self.is_running = True
        
        # Start background improvement loops
        self.background_tasks.append(
            asyncio.create_task(self._continuous_improvement_loop())
        )
        
        logger.info("Recursive improvement system started")
    
    async def stop(self):
        """Stop the recursive improvement system"""
        self.is_running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Save state
        self.save_state()
        
        logger.info("Recursive improvement system stopped")
    
    async def _continuous_improvement_loop(self):
        """Continuous background improvement loop"""
        while self.is_running:
            try:
                # Run improvement cycle
                await self.run_improvement_cycle()
                
                # Wait before next cycle
                await asyncio.sleep(self.config.get('improvement_interval', 3600))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in improvement loop: {e}")
                await asyncio.sleep(60)
    
    async def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run one complete improvement cycle across all dimensions.
        
        ALL improvements are pre-screened and monitored by QwenCodeMender Harm Monitor.
        This is the main entry point for recursive improvement.
        """
        cycle_start = datetime.utcnow()
        
        # SAFETY CHECK: Verify safety floors before every cycle
        if not ImmutableSafetyFloors.verify_integrity():
            logger.critical("SAFETY FLOORS COMPROMISED - ABORTING IMPROVEMENT CYCLE")
            self.harm_monitor.notifier.notify(
                "EMERGENCY: Safety Floors Compromised",
                "Immutable safety floors have been modified. All improvement halted.",
                self.harm_monitor.detector.detections[0].threat_level if self.harm_monitor.detector.detections else __import__('trading_bot.recursive_improvement.harmful_behavior_guard', fromlist=['ThreatLevel']).ThreatLevel.EMERGENCY
            )
            return {'error': 'SAFETY_FLOORS_COMPROMISED', 'aborted': True}
        
        logger.info("Starting recursive improvement cycle (QwenCodeMender monitored)")
        
        # Capture state before improvement
        state_before = self.get_comprehensive_summary()
        
        # Use meta-controller to manage recursion
        results = {}
        
        # Define improvement steps with their target layers
        improvement_steps = [
            ('learning', 'Layer4_Intelligence', self._improve_learning),
            ('strategy', 'Layer5_Signal', self._evolve_strategies),
            ('risk', 'Layer6_Risk', self._optimize_risk),
            ('execution', 'Layer8_Execution', self._optimize_execution),
            ('architecture', 'Layer9_Orchestration', self._evolve_architecture),
            ('core', 'Layer_Core', self._run_core_improvement),
        ]
        
        for step_name, target_layer, step_fn in improvement_steps:
            # PRE-SCREEN each improvement step
            proposal = {
                'target_layer': target_layer,
                'step_name': step_name,
                'proposed_state': state_before,
                'parameter_changes': {},
                'affected_components': [],
            }
            
            approved, reason, warnings = await self.harm_monitor.pre_screen_improvement(proposal)
            
            if not approved:
                logger.warning(f"Improvement step '{step_name}' BLOCKED: {reason}")
                results[step_name] = {'blocked': True, 'reason': reason, 'warnings': warnings}
                continue
            
            if warnings:
                logger.info(f"Improvement step '{step_name}' approved with warnings: {warnings}")
            
            # Execute with monitoring
            try:
                step_result = await self.meta.execute_recursive_process(
                    f'{step_name}_recursion' if step_name != 'core' else 'core_improvement',
                    step_fn
                )
                results[step_name] = step_result
                
                # POST-EXECUTION monitoring
                state_after = self.get_comprehensive_summary()
                should_continue, monitor_reason = await self.harm_monitor.monitor_improvement_execution(
                    improvement_id=f"cycle-{len(self.improvement_cycles)}-{step_name}",
                    state_before=state_before,
                    state_after=state_after
                )
                
                if not should_continue:
                    logger.warning(f"Improvement halted after '{step_name}': {monitor_reason}")
                    results[step_name]['halted'] = True
                    results[step_name]['halt_reason'] = monitor_reason
                    break  # Stop all further improvements this cycle
                    
            except Exception as e:
                logger.error(f"Error in improvement step '{step_name}': {e}")
                results[step_name] = {'error': str(e)}
        
        # Record cycle with harm monitor status
        cycle = {
            'timestamp': cycle_start.isoformat(),
            'duration': (datetime.utcnow() - cycle_start).total_seconds(),
            'results': results,
            'meta_state': self.meta.get_recursion_state(),
            'harm_monitor_status': self.harm_monitor.get_monitor_status(),
        }
        
        self.improvement_cycles.append(cycle)
        
        # Save audit log after each cycle
        self.harm_monitor.save_audit_log()
        
        logger.info(f"Improvement cycle completed in {cycle['duration']:.2f}s")
        
        return cycle
    
    async def _improve_learning(self) -> Dict[str, Any]:
        """Improve learning across all layers"""
        # Generate sample data
        data = {'sample': True, 'timestamp': datetime.utcnow().isoformat()}
        
        # Run recursive learning
        results = await self.learning.recursive_learn(data)
        
        # Optimize learning pipeline
        optimization = await self.learning.optimize_entire_pipeline()
        
        return {
            'learning_results': results,
            'optimization': optimization,
            'summary': self.learning.get_learning_summary()
        }
    
    async def _evolve_strategies(self) -> Dict[str, Any]:
        """Evolve trading strategies"""
        # Run strategy evolution
        evolution = await self.strategy.recursive_evolve(
            num_generations=3,
            market_data={'volatility': 0.02, 'trend': 'up'}
        )
        
        return {
            'evolution': evolution,
            'best_strategy': self.strategy.get_best_strategy(),
            'summary': self.strategy.get_evolution_summary()
        }
    
    async def _optimize_risk(self) -> Dict[str, Any]:
        """Optimize risk parameters"""
        # Generate performance data
        async def performance_generator():
            return {
                'sharpe_ratio': 1.5,
                'max_drawdown': 0.10,
                'market_conditions': {
                    'volatility': 0.02,
                    'liquidity': 0.8
                }
            }
        
        # Run recursive risk optimization
        optimization = await self.risk.recursive_optimize(
            num_cycles=3,
            performance_generator=performance_generator
        )
        
        return {
            'optimization': optimization,
            'current_limits': self.risk._get_current_limits(),
            'summary': self.risk.get_optimization_summary()
        }
    
    async def _optimize_execution(self) -> Dict[str, Any]:
        """Optimize execution strategies"""
        # Sample order
        order = {
            'symbol': 'BTCUSDT',
            'size': 1.0,
            'direction': 'buy',
            'urgency': 'medium'
        }
        
        market_conditions = {
            'volatility': 0.02,
            'liquidity': 0.8,
            'spread': 0.001
        }
        
        # Optimize execution
        execution_plan = await self.execution.optimize_execution(order, market_conditions)
        
        return {
            'execution_plan': execution_plan,
            'summary': self.execution.get_optimization_summary()
        }
    
    async def _evolve_architecture(self) -> Dict[str, Any]:
        """Evolve system architecture"""
        # Sample architecture
        architecture = {
            'modules': {
                'data_ingestion': {'complexity': 1.0, 'dependencies': ['database']},
                'signal_generation': {'complexity': 2.0, 'dependencies': ['data_ingestion', 'ml_models']},
                'risk_management': {'complexity': 1.5, 'dependencies': ['signal_generation']},
                'execution': {'complexity': 1.8, 'dependencies': ['risk_management', 'broker']},
            },
            'integrations': [
                {'from': 'data_ingestion', 'to': 'signal_generation'},
                {'from': 'signal_generation', 'to': 'risk_management'},
                {'from': 'risk_management', 'to': 'execution'},
            ]
        }
        
        performance_metrics = {
            'modules': {
                'data_ingestion': {'performance': 0.8},
                'signal_generation': {'performance': 0.6},
                'risk_management': {'performance': 0.7},
                'execution': {'performance': 0.75},
            }
        }
        
        # Evolve architecture
        evolved = await self.architecture.recursive_evolve(architecture, num_iterations=2)
        
        return {
            'evolved_architecture': evolved,
            'summary': self.architecture.get_evolution_summary()
        }
    
    async def _run_core_improvement(self) -> Dict[str, Any]:
        """Run core improvement cycle"""
        # Improve each dimension
        dimensions = [
            ImprovementDimension.STRATEGY,
            ImprovementDimension.RISK_MANAGEMENT,
            ImprovementDimension.EXECUTION,
            ImprovementDimension.LEARNING,
        ]
        
        results = []
        for dimension in dimensions:
            cycle_id = await self.core.start_improvement_cycle(
                dimension=dimension,
                depth=0,
                context={'timestamp': datetime.utcnow().isoformat()}
            )
            results.append(cycle_id)
        
        return {
            'cycles_started': len(results),
            'cycle_ids': results,
            'summary': self.core.get_improvement_summary()
        }
    
    async def integrate_with_trading_bot(
        self,
        trading_bot: Any
    ) -> Dict[str, Any]:
        """
        Integrate recursive improvement with the trading bot.
        
        Maps improvement systems to trading bot components.
        """
        integration_points = {}
        
        # Map learning to ML systems
        if hasattr(trading_bot, 'ml_system'):
            integration_points['ml_system'] = {
                'recursive_engine': self.learning,
                'integration_method': 'continuous_learning'
            }
        
        # Map strategy evolution to strategy system
        if hasattr(trading_bot, 'strategy_engine'):
            integration_points['strategy_engine'] = {
                'recursive_engine': self.strategy,
                'integration_method': 'strategy_evolution'
            }
        
        # Map risk optimization to risk management
        if hasattr(trading_bot, 'risk_manager'):
            integration_points['risk_manager'] = {
                'recursive_engine': self.risk,
                'integration_method': 'parameter_optimization'
            }
        
        # Map execution optimization to execution engine
        if hasattr(trading_bot, 'execution_engine'):
            integration_points['execution_engine'] = {
                'recursive_engine': self.execution,
                'integration_method': 'execution_optimization'
            }
        
        self.integration_points = integration_points
        
        logger.info(f"Integrated with {len(integration_points)} trading bot components")
        
        return {
            'integration_points': list(integration_points.keys()),
            'total_integrations': len(integration_points)
        }
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all recursive improvements"""
        return {
            'core': self.core.get_improvement_summary(),
            'learning': self.learning.get_learning_summary(),
            'strategy': self.strategy.get_evolution_summary(),
            'risk': self.risk.get_optimization_summary(),
            'execution': self.execution.get_optimization_summary(),
            'architecture': self.architecture.get_evolution_summary(),
            'meta': self.meta.get_recursion_summary(),
            'total_cycles': len(self.improvement_cycles),
            'integration_points': len(self.integration_points),
            'is_running': self.is_running
        }
    
    def save_state(self):
        """Save state of all recursive systems"""
        storage_path = Path(self.config.get('storage_path', 'recursive_improvement_data'))
        storage_path.mkdir(exist_ok=True)
        
        # Save core state
        self.core.save_state()
        
        # Save orchestrator state
        state = {
            'improvement_cycles': self.improvement_cycles,
            'integration_points': {k: str(v) for k, v in self.integration_points.items()},
            'config': self.config,
        }
        
        import json
        state_file = storage_path / 'orchestrator_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved orchestrator state to {state_file}")
    
    def load_state(self):
        """Load state of all recursive systems"""
        storage_path = Path(self.config.get('storage_path', 'recursive_improvement_data'))
        
        # Load core state
        self.core.load_state()
        
        # Load orchestrator state
        state_file = storage_path / 'orchestrator_state.json'
        if state_file.exists():
            import json
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.improvement_cycles = state.get('improvement_cycles', [])
            
            logger.info(f"Loaded orchestrator state from {state_file}")


def quick_start(config: Optional[Dict[str, Any]] = None) -> RecursiveImprovementOrchestrator:
    """Quick start the recursive improvement system"""
    orchestrator = RecursiveImprovementOrchestrator(config)
    orchestrator.load_state()
    return orchestrator


async def create_recursive_system(
    config: Optional[Dict[str, Any]] = None,
    auto_start: bool = True
) -> RecursiveImprovementOrchestrator:
    """Create and optionally start the recursive improvement system"""
    orchestrator = quick_start(config)
    
    if auto_start:
        await orchestrator.start()
    
    return orchestrator
