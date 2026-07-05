"""
Neural Brain Orchestrator - Master Controller for All 100+ Modules
Integrates all components into a unified brain-like architecture
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.neural_integration.neural_hub import (
    NeuralIntegrationHub, NeuralSignal, NeuralSignalType, NeuralModule,
    create_neural_brain
)
from trading_bot.neural_integration.synaptic_matrix import (
    SYNAPTIC_MATRIX, ConnectionType, get_module_brain_region, get_module_connections
)
from trading_bot.neural_integration.neurotransmitters import (
    SYNAPTIC_CLEFT, PLASTICITY_ENGINE, CONSCIOUSNESS, BRAIN_STEM,
    NeurotransmitterSignal, NeurotransmitterType, global_neural_tick
)

logger = logging.getLogger(__name__)


class ModuleNeuron(NeuralModule):
    """
    Wrapper to turn any trading bot module into a neural module
    """
    
    def __init__(self, module_name: str, module_instance: Any, brain_region: str):
        super().__init__(module_name, f"{brain_region}_neuron")
        self.module_instance = module_instance
        self.brain_region = brain_region
        self.activation_count = 0
        self.last_output = None
        
    async def process_signal(self, signal: NeuralSignal) -> Optional[NeuralSignal]:
        """Process incoming neural signal and route to wrapped module"""
        self.activation_count += 1
        
        try:
            # Extract action from signal
            action = signal.data.get('action', 'process')
            
            # Process based on action type
            if action == 'process':
                result = await self._process_data(signal.data)
            elif action == 'query':
                result = await self._query(signal.data)
            elif action == 'update':
                result = await self._update(signal.data)
            else:
                result = await self._default_process(signal.data)
            
            self.last_output = result
            
            # Record in plasticity engine (Hebbian learning)
            PLASTICITY_ENGINE.record_firing(signal.source, self.module_id)
            
            # Create response signal
            if result is not None:
                return NeuralSignal(
                    signal_id='',
                    source=self.module_id,
                    target=signal.source,  # Echo back to source
                    signal_type=NeuralSignalType.ANALYSIS,
                    data={'result': result, 'original_signal': signal.signal_id},
                    timestamp=datetime.now(),
                    strength=signal.strength * 0.9  # Slight decay
                )
            
        except Exception as e:
            logger.error(f"Module {self.module_id} processing failed: {e}")
            
            # Release stress neurotransmitter
            stress_signal = NeurotransmitterSignal(
                transmitter_type=NeurotransmitterType.NOREPINEPHRINE,
                concentration=0.5,
                source_module=self.module_id,
                target_module='brain_stem',
                timestamp=datetime.now()
            )
            await SYNAPTIC_CLEFT.release_neurotransmitter(stress_signal)
            
        return None
    
    async def _process_data(self, data: Dict) -> Any:
        """Default data processing"""
        if hasattr(self.module_instance, 'process'):
            return await self._async_call(self.module_instance.process, data)
        elif hasattr(self.module_instance, 'analyze'):
            return await self._async_call(self.module_instance.analyze, data)
        return {'status': 'processed', 'module': self.module_id}
    
    async def _query(self, data: Dict) -> Any:
        """Handle query request"""
        query_type = data.get('query_type', 'status')
        
        if query_type == 'status':
            return {
                'module': self.module_id,
                'brain_region': self.brain_region,
                'activations': self.activation_count,
                'is_active': self.is_active,
                'neural_state': self.neural_state
            }
        elif query_type == 'connections':
            return {
                'module': self.module_id,
                'connections': list(self.connections.keys()),
                'strengths': {k: v.weight for k, v in self.connections.items()}
            }
        
        return {'status': 'unknown_query'}
    
    async def _update(self, data: Dict) -> Any:
        """Handle update request"""
        if 'config' in data:
            # Update configuration
            if hasattr(self.module_instance, 'update_config'):
                self.module_instance.update_config(data['config'])
        
        return {'status': 'updated', 'module': self.module_id}
    
    async def _default_process(self, data: Dict) -> Any:
        """Default processing"""
        return {'status': 'received', 'data': data, 'module': self.module_id}
    
    async def _async_call(self, method, *args):
        """Call method async if needed"""
        import inspect
        if inspect.iscoroutinefunction(method):
            return await method(*args)
        else:
            return method(*args)


class NeuralBrainOrchestrator:
    """
    Master orchestrator for the neural brain architecture
    
    This is the TOP-LEVEL controller that manages all 100+ modules
    through neural connections
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.brain: Optional[NeuralIntegrationHub] = None
        self.module_wrappers: Dict[str, ModuleNeuron] = {}
        self.external_modules: Dict[str, Any] = {}
        self.is_running = False
        self.start_time = None
        
        logger.info("🧠 Neural Brain Orchestrator initializing...")
        
    async def initialize_brain(self):
        """Initialize the neural brain architecture"""
        logger.info("=" * 70)
        logger.info("INITIALIZING NEURAL BRAIN ARCHITECTURE")
        logger.info("=" * 70)
        
        # Create brain
        self.brain = await create_neural_brain(self.config)
        
        # Create module neurons for all known modules
        await self._register_all_modules()
        
        # Create synaptic mesh between regions
        await self._create_inter_region_connections()
        
        # Start global neural tick
        asyncio.create_task(self._neural_tick_loop())
        
        self.start_time = datetime.now()
        
        logger.info("=" * 70)
        logger.info("✅ NEURAL BRAIN ARCHITECTURE ONLINE")
        logger.info("=" * 70)
        
        # Log statistics
        stats = self.get_brain_statistics()
        logger.info(f"📊 Modules: {stats['total_modules']} | Regions: {len(stats['regions'])} | Connections: {stats['total_synapses']}")
        
    async def _register_all_modules(self):
        """Register all 100+ modules as neural neurons"""
        # Get all modules from synaptic matrix
        all_modules = list(SYNAPTIC_MATRIX.module_mappings.keys())
        
        registered = 0
        for module_name in all_modules:
            brain_region = get_module_brain_region(module_name)
            
            # Create wrapper
            wrapper = ModuleNeuron(
                module_name=module_name,
                module_instance=None,  # Will be loaded on demand
                brain_region=brain_region
            )
            
            # Register in brain
            if self.brain:
                await self.brain.register_module(wrapper, brain_region)
                self.module_wrappers[module_name] = wrapper
                registered += 1
        
        logger.info(f"✓ Registered {registered} modules as neurons")
        
    async def _create_inter_region_connections(self):
        """Create synaptic connections between brain regions"""
        if not self.brain:
            return
        
        # Connect thalamus (data) to neocortex (intelligence)
        await self.brain.create_synaptic_mesh(
            'thalamus', 'neocortex', weight=0.9
        )
        
        # Connect neocortex (intelligence) to cerebellum (execution)
        await self.brain.create_synaptic_mesh(
            'neocortex', 'cerebellum', weight=0.8
        )
        
        # Connect limbic (risk) to cerebellum (execution) - INHIBITORY
        # Risk can stop execution
        await self.brain.create_synaptic_mesh(
            'limbic_system', 'cerebellum', weight=-0.7
        )
        
        # Connect hippocampus (learning) to neocortex
        await self.brain.create_synaptic_mesh(
            'hippocampus', 'neocortex', weight=0.6
        )
        
        # Connect hypothalamus (monitoring) to all regions - MODULATORY
        await self.brain.create_synaptic_mesh(
            'hypothalamus', 'brain_stem', weight=0.5
        )
        
        logger.info("✓ Inter-region synaptic mesh created")
        
    async def integrate_external_module(self, name: str, instance: Any):
        """Integrate an external module into the neural brain"""
        brain_region = get_module_brain_region(name)
        
        wrapper = ModuleNeuron(
            module_name=name,
            module_instance=instance,
            brain_region=brain_region
        )
        
        # Get synaptic connections from matrix
        connections = get_module_connections(name)
        for target, weight, conn_type in connections:
            if target in self.module_wrappers:
                wrapper.connect_to(target, weight)
        
        # Register
        if self.brain:
            await self.brain.register_module(wrapper, brain_region)
            self.module_wrappers[name] = wrapper
            self.external_modules[name] = instance
            
            logger.info(f"✓ External module integrated: {name} -> {brain_region}")
            
    async def stimulate_module(self, module_name: str, data: Dict):
        """Stimulate a specific neural module"""
        if module_name not in self.module_wrappers:
            logger.warning(f"Module not found: {module_name}")
            return None
        
        module = self.module_wrappers[module_name]
        
        # Create stimulation signal
        signal = NeuralSignal(
            signal_id='',
            source='orchestrator',
            target=module_name,
            signal_type=NeuralSignalType.MARKET_DATA,
            data=data,
            timestamp=datetime.now()
        )
        
        # Transmit
        if self.brain:
            await self.brain.transmit_signal(signal)
        
        # Activate module
        result = await module.activate(data)
        
        return result
    
    async def broadcast_to_region(self, region: str, data: Dict):
        """Broadcast signal to all modules in a brain region"""
        if not self.brain:
            return []
        
        return await self.brain.stimulate_region(region, data)
    
    async def query_module(self, module_name: str, query_type: str = 'status'):
        """Query a module's state"""
        if module_name not in self.module_wrappers:
            return {'error': 'Module not found'}
        
        signal = NeuralSignal(
            signal_id='',
            source='orchestrator',
            target=module_name,
            signal_type=NeuralSignalType.SYNC,
            data={'action': 'query', 'query_type': query_type},
            timestamp=datetime.now()
        )
        
        if self.brain:
            await self.brain.transmit_signal(signal)
        
        # Direct query
        module = self.module_wrappers[module_name]
        return await module._query({'query_type': query_type})
    
    async def get_consciousness_insights(self) -> List[Dict]:
        """Get insights from collective consciousness"""
        return CONSCIOUSNESS.insights[-10:]  # Last 10 insights
    
    async def focus_attention(self, module_name: str):
        """Focus conscious attention on a module"""
        CONSCIOUSNESS.focus_attention(module_name)
        
        # Release acetylcholine (attention neurotransmitter)
        signal = NeurotransmitterSignal(
            transmitter_type=NeurotransmitterType.ACETYLCHOLINE,
            concentration=0.8,
            source_module='orchestrator',
            target_module=module_name,
            timestamp=datetime.now()
        )
        await SYNAPTIC_CLEFT.release_neurotransmitter(signal)
    
    def get_brain_statistics(self) -> Dict:
        """Get comprehensive brain statistics"""
        if not self.brain:
            return {'status': 'not_initialized'}
        
        topology = self.brain.get_neural_topology()
        consciousness = CONSCIOUSNESS.get_workspace_summary()
        
        return {
            'status': 'online' if self.is_running else 'initialized',
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'total_modules': topology['total_modules'],
            'regions': topology['brain_regions'],
            'total_synapses': topology['total_synapses'],
            'active_connections': topology['active_connections'],
            'consciousness_level': consciousness['consciousness_level'],
            'attention_focus': consciousness['attention_focus'],
            'workspace_items': consciousness['workspace_items'],
            'insights_count': len(CONSCIOUSNESS.insights),
            'chemical_balance': SYNAPTIC_CLEFT.get_chemical_state(),
            'brain_stem_health': BRAIN_STEM.check_health()
        }
    
    async def _neural_tick_loop(self):
        """Background loop for neural maintenance"""
        while self.is_running or True:
            await global_neural_tick()
            await asyncio.sleep(5.0)  # Tick every 5 seconds
    
    async def start(self):
        """Start the neural brain orchestrator"""
        self.is_running = True
        
        # Initialize brain
        await self.initialize_brain()
        
        # Start neural processing
        if self.brain:
            asyncio.create_task(self.brain.start_neural_processing())
        
        # Register success reflex
        BRAIN_STEM.register_reflex('success', self._on_success)
        BRAIN_STEM.register_reflex('failure', self._on_failure)
        
        logger.info("🚀 Neural Brain Orchestrator FULLY OPERATIONAL")
        
    async def _on_success(self, data: Any):
        """Success reflex - release dopamine"""
        signal = NeurotransmitterSignal(
            transmitter_type=NeurotransmitterType.DOPAMINE,
            concentration=0.6,
            source_module='orchestrator',
            target_module='limbic_system',
            timestamp=datetime.now()
        )
        await SYNAPTIC_CLEFT.release_neurotransmitter(signal)
        
    async def _on_failure(self, data: Any):
        """Failure reflex - release norepinephrine"""
        signal = NeurotransmitterSignal(
            transmitter_type=NeurotransmitterType.NOREPINEPHRINE,
            concentration=0.7,
            source_module='orchestrator',
            target_module='limbic_system',
            timestamp=datetime.now()
        )
        await SYNAPTIC_CLEFT.release_neurotransmitter(signal)
    
    async def stop(self):
        """Stop the neural brain orchestrator"""
        self.is_running = False
        
        # Synchronize all modules
        if self.brain:
            await self.brain.synchronize_all_modules()
        
        logger.info("🛑 Neural Brain Orchestrator stopped gracefully")


# Global orchestrator instance
_orchestrator: Optional[NeuralBrainOrchestrator] = None


async def get_neural_orchestrator(config: Optional[Dict] = None) -> NeuralBrainOrchestrator:
    """Get or create global neural orchestrator"""
    global _orchestrator
    
    if _orchestrator is None:
        _orchestrator = NeuralBrainOrchestrator(config)
        await _orchestrator.start()
    
    return _orchestrator


async def quick_start_neural_brain() -> NeuralBrainOrchestrator:
    """Quick start the complete neural brain"""
    orchestrator = await get_neural_orchestrator()
    return orchestrator


# Convenience functions

async def stimulate(module_name: str, data: Dict):
    """Stimulate a module"""
    orchestrator = await get_neural_orchestrator()
    return await orchestrator.stimulate_module(module_name, data)


async def query(module_name: str, query_type: str = 'status'):
    """Query a module"""
    orchestrator = await get_neural_orchestrator()
    return await orchestrator.query_module(module_name, query_type)


async def brain_stats():
    """Get brain statistics"""
    orchestrator = await get_neural_orchestrator()
    return orchestrator.get_brain_statistics()


async def focus(module_name: str):
    """Focus attention on module"""
    orchestrator = await get_neural_orchestrator()
    return await orchestrator.focus_attention(module_name)


if __name__ == "__main__":
    # Demo
    async def demo():
        print("=" * 70)
        print("NEURAL BRAIN ORCHESTRATOR DEMO")
        print("=" * 70)
        
        # Start brain
        brain = await quick_start_neural_brain()
        
        # Get stats
        stats = brain.get_brain_statistics()
        print(f"\n📊 BRAIN STATISTICS:")
        print(f"  Total Modules: {stats['total_modules']}")
        print(f"  Total Synapses: {stats['total_synapses']}")
        print(f"  Consciousness Level: {stats['consciousness_level']:.2f}")
        print(f"  Regions: {list(stats['regions'].keys())}")
        
        # Stimulate a module
        print(f"\n⚡ Stimulating 'ai_core'...")
        result = await stimulate('ai_core', {'action': 'process', 'data': 'test'})
        print(f"  Result: {result}")
        
        # Query a module
        print(f"\n🔍 Querying 'risk'...")
        status = await query('risk', 'status')
        print(f"  Status: {status}")
        
        # Get insights
        print(f"\n💡 Consciousness Insights:")
        insights = await brain.get_consciousness_insights()
        for insight in insights:
            print(f"  - {insight}")
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        
        # Stop
        await brain.stop()
    
    asyncio.run(demo())
