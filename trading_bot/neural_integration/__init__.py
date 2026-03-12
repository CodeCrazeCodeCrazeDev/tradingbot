"""
Neural Integration Package
Connects all 100+ trading bot modules through brain-like neural architecture

Usage:
    from trading_bot.neural_integration import quick_start_neural_brain, stimulate, query
    
    # Start the neural brain
    brain = await quick_start_neural_brain()
    
    # Stimulate any module
    result = await stimulate('ai_core', {'data': 'market_data'})
    
    # Query module status
    status = await query('risk', 'status')
"""

# Core neural components
from trading_bot.neural_integration.neural_hub import (
    NeuralIntegrationHub,
    NeuralModule,
    NeuralSignal,
    NeuralSignalType,
    SynapticConnection,
    create_neural_brain,
    quick_start_neural_integration,
    BRAIN_REGION_MAP
)

# Synaptic matrix
from trading_bot.neural_integration.synaptic_matrix import (
    ModuleSynapticMatrix,
    ConnectionType,
    ModuleMapping,
    SYNAPTIC_MATRIX,
    get_module_brain_region,
    get_module_connections
)

# Neurotransmitter system
from trading_bot.neural_integration.neurotransmitters import (
    SynapticCleft,
    NeuralPlasticityEngine,
    CollectiveConsciousness,
    BrainStem,
    NeurotransmitterSignal,
    NeurotransmitterType,
    SYNAPTIC_CLEFT,
    PLASTICITY_ENGINE,
    CONSCIOUSNESS,
    BRAIN_STEM,
    global_neural_tick
)

# Brain orchestrator
from trading_bot.neural_integration.brain_orchestrator import (
    NeuralBrainOrchestrator,
    ModuleNeuron,
    get_neural_orchestrator,
    quick_start_neural_brain,
    stimulate,
    query,
    brain_stats,
    focus
)

__version__ = "1.0.0"
__author__ = "AlphaAlgo Trading Bot"

__all__ = [
    # Core Hub
    'NeuralIntegrationHub',
    'NeuralModule',
    'NeuralSignal',
    'NeuralSignalType',
    'SynapticConnection',
    'create_neural_brain',
    'quick_start_neural_integration',
    'BRAIN_REGION_MAP',
    
    # Synaptic Matrix
    'ModuleSynapticMatrix',
    'ConnectionType',
    'ModuleMapping',
    'SYNAPTIC_MATRIX',
    'get_module_brain_region',
    'get_module_connections',
    
    # Neurotransmitters
    'SynapticCleft',
    'NeuralPlasticityEngine',
    'CollectiveConsciousness',
    'BrainStem',
    'NeurotransmitterSignal',
    'NeurotransmitterType',
    'SYNAPTIC_CLEFT',
    'PLASTICITY_ENGINE',
    'CONSCIOUSNESS',
    'BRAIN_STEM',
    'global_neural_tick',
    
    # Orchestrator
    'NeuralBrainOrchestrator',
    'ModuleNeuron',
    'get_neural_orchestrator',
    'quick_start_neural_brain',
    'stimulate',
    'query',
    'brain_stats',
    'focus'
]
