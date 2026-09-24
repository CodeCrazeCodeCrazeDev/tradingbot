"""
Cognitive Core - Brain-Inspired Intelligence Module
====================================================

Implements brain-inspired cognitive architecture:
- Memory System: Episodic, semantic, procedural memory
- World Model: Market state representation & prediction
- Reward Processor: Multi-objective reward signals
- Goal Manager: Hierarchical goal decomposition
- Emotion Module: Risk sentiment & confidence states
- Attention Mechanism: Focus allocation
"""

from .memory_system import MemorySystem, EpisodicMemory, SemanticMemory, ProceduralMemory
from .world_model import WorldModel, MarketState, Prediction
from .reward_processor import RewardProcessor, RewardSignal
from .goal_manager import GoalManager, Goal, GoalHierarchy
from .emotion_module import EmotionModule, EmotionalState
from .attention_mechanism import AttentionMechanism, AttentionTarget, AttentionType, SalienceSource

__all__ = [
    'MemorySystem', 'EpisodicMemory', 'SemanticMemory', 'ProceduralMemory',
    'WorldModel', 'MarketState', 'Prediction',
    'RewardProcessor', 'RewardSignal',
    'GoalManager', 'Goal', 'GoalHierarchy',
    'EmotionModule', 'EmotionalState',
    'AttentionMechanism', 'AttentionTarget', 'AttentionType', 'SalienceSource'
]
