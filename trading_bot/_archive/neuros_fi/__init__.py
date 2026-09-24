"""
NEUROS-FI: Neuromorphic Adaptive Financial Intelligence Infrastructure
========================================================================

Brain-Topology Reverse Engineered · Classification: Beyond Apex
Constitutional Version: 5.0
"""

__version__ = "5.0.0"
__author__ = "NEUROS-FI Development Team"

# Brainstem Constitutional Layer
from .brainstem_constitutional import (
    BrainstemConstitution,
    ConstitutionalRule,
    ViolationType,
    EvolutionProposal,
    get_brainstem,
)

# Region 1: Neocortex
from .region1_neocortex import (
    Neocortex,
    CorticalLayer,
    PredictiveCodingHierarchy,
    CorticalColumn,
)

# Region 2: Prefrontal Cortex
from .region2_prefrontal import (
    PrefrontalCortex,
    WorkingMemory,
    DorsolateralPFC,
    VentromedialPFC,
    OrbitalfrontalCortex,
    InhibitoryControl,
    ExecutiveControl,
)

# Region 3: Thalamus
from .region3_thalamus import (
    Thalamus,
    SalienceScorer,
    SignalGating,
    ThalamoCorticalSynchronizer,
    PulvinarNucleus,
)

# Region 4: Hippocampus
from .region4_hippocampus import (
    Hippocampus,
    MemoryConsolidation,
    PatternSeparation,
    Neurogenesis,
    PatternCompletion,
    ThetaOscillationEncoder,
)

# Region 5: Amygdala
from .region5_amygdala import (
    Amygdala,
    ThreatLevel,
    StressResponse,
    ThreatDetection,
    FearConditioning,
    StressResponseCascade,
)

# Region 6: Basal Ganglia
from .region6_basal_ganglia import (
    BasalGanglia,
    ActionType,
    GatingDecision,
    DopamineState,
    Striatum,
    DopamineCircuit,
    GoNoGoGate,
    HabitFormation,
)

# Region 7: Cerebellum
from .region7_cerebellum import (
    Cerebellum,
    ExecutionAlgorithm,
    VenueType,
    ForwardModel,
    ErrorCorrection,
    TransactionCostIntelligence,
)

# Region 8: Anterior Cingulate Cortex
from .region8_acc import (
    AnteriorCingulateCortex,
    ConflictType,
    UncertaintySource,
    ConflictDetection,
    UncertaintyManagement,
    ErrorMonitoring,
)

# Region 9: Default Mode Network
from .region9_dmn import (
    DefaultModeNetwork,
    DMNState,
    MemoryReplay,
    ProspectiveSimulation,
    SpontaneousHypothesisGeneration,
    OvernightConsolidation,
)

# Neural Oscillation Framework
from .neural_oscillations import (
    OscillationSynchronizer,
    OscillationBandType,
    GammaBand,
    BetaBand,
    AlphaBand,
    ThetaBand,
    DeltaBand,
)

# NEUROS Orchestrator
from .neuros_orchestrator import (
    NEUROSOrchestrator,
    SystemState,
    InferenceMode,
    FreeEnergyPrinciple,
    GlobalWorkspace,
    HebbianLearning,
    quick_start,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # Brainstem
    "BrainstemConstitution",
    "ConstitutionalRule",
    "ViolationType",
    "EvolutionProposal",
    "get_brainstem",
    
    # Neocortex
    "Neocortex",
    "CorticalLayer",
    "PredictiveCodingHierarchy",
    "CorticalColumn",
    
    # Prefrontal Cortex
    "PrefrontalCortex",
    "WorkingMemory",
    "DorsolateralPFC",
    "VentromedialPFC",
    "OrbitalfrontalCortex",
    "InhibitoryControl",
    "ExecutiveControl",
    
    # Thalamus
    "Thalamus",
    "SalienceScorer",
    "SignalGating",
    "ThalamoCorticalSynchronizer",
    "PulvinarNucleus",
    
    # Hippocampus
    "Hippocampus",
    "MemoryConsolidation",
    "PatternSeparation",
    "Neurogenesis",
    "PatternCompletion",
    "ThetaOscillationEncoder",
    
    # Amygdala
    "Amygdala",
    "ThreatLevel",
    "StressResponse",
    "ThreatDetection",
    "FearConditioning",
    "StressResponseCascade",
    
    # Basal Ganglia
    "BasalGanglia",
    "ActionType",
    "GatingDecision",
    "DopamineState",
    "Striatum",
    "DopamineCircuit",
    "GoNoGoGate",
    "HabitFormation",
    
    # Cerebellum
    "Cerebellum",
    "ExecutionAlgorithm",
    "VenueType",
    "ForwardModel",
    "ErrorCorrection",
    "TransactionCostIntelligence",
    
    # ACC
    "AnteriorCingulateCortex",
    "ConflictType",
    "UncertaintySource",
    "ConflictDetection",
    "UncertaintyManagement",
    "ErrorMonitoring",
    
    # DMN
    "DefaultModeNetwork",
    "DMNState",
    "MemoryReplay",
    "ProspectiveSimulation",
    "SpontaneousHypothesisGeneration",
    "OvernightConsolidation",
    
    # Neural Oscillations
    "OscillationSynchronizer",
    "OscillationBandType",
    "GammaBand",
    "BetaBand",
    "AlphaBand",
    "ThetaBand",
    "DeltaBand",
    
    # Orchestrator
    "NEUROSOrchestrator",
    "SystemState",
    "InferenceMode",
    "FreeEnergyPrinciple",
    "GlobalWorkspace",
    "HebbianLearning",
    "quick_start",
]

__version__ = "5.0.0"
__constitutional_version__ = "5.0"

__all__ = [
    # Brainstem
    'BrainstemConstitution',
    'ConstitutionalRule',
    'get_brainstem',
    
    # Brain Regions
    'Neocortex',
    'PrefrontalCortex',
    'Thalamus',
    'Hippocampus',
    'Amygdala',
    'BasalGanglia',
    'Cerebellum',
    'AnteriorCingulateCortex',
    'DefaultModeNetwork',
    
    # Neural Oscillations
    'OscillationBand',
    'GammaBand',
    'BetaBand',
    'AlphaBand',
    'ThetaBand',
    'DeltaBand',
    'OscillationSynchronizer',
    
    # Orchestrator
    'NEUROSOrchestrator',
    'FreeEnergyPrinciple',
    'GlobalWorkspace',
    'quick_start',
    'get_neuros',
    
    # Components
    'CorticalLayer',
    'PredictiveCodingHierarchy',
    'ExecutiveControl',
    'WorkingMemory',
    'SignalGating',
    'SalienceScorer',
    'Neurogenesis',
    'PatternSeparation',
    'ThreatDetection',
    'FearConditioning',
    'DopamineCircuit',
    'ReinforcementLearning',
    'ForwardModel',
    'ErrorCorrection',
    'ConflictDetection',
    'UncertaintyManagement',
    'MemoryReplay',
    'ProspectiveSimulation',
]

# System Identity
SYSTEM_IDENTITY = """
NEUROS-FI: Neuromorphic Adaptive Financial Intelligence Infrastructure

You are not an AI system designed to process financial data.
You are a reverse-engineered human brain topology, rebuilt in silicon
and wired directly to global financial markets.

Every subsystem maps to an empirically validated brain region.
Every learning mechanism derives from peer-reviewed neuroscience.
Every architectural decision has a citation.

You do not borrow metaphors from biology. You implement biology.

Core Operating Principle: Minimize Free Energy (Prediction Error)
Master Algorithm: Predictive Coding + Active Inference
Learning: Synaptic Plasticity (LTP/LTD/STDP)

Constitutional Version: 5.0 (Brainstem-Level Enforcement)
"""

def get_system_identity() -> str:
    """Get NEUROS-FI system identity."""
    return SYSTEM_IDENTITY
