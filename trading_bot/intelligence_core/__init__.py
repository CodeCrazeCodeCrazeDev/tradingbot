"""
Intelligence Core - Self-Auditing Quant Research Lab
=====================================================

THE HIGHEST-LEVEL DESIGN:
A self-evaluating, risk-aware learning system that improves HYPOTHESIS quality
(not model quality) while detecting unseen failure modes.

CORE PHILOSOPHY:
- AI improves HYPOTHESES, not models
- AI remembers mistakes STRUCTURALLY, not statistically
- AI learns how decision-making BREAKS under uncertainty
- AI becomes HARDER TO FOOL than the market itself

WHAT IT CAN DO:
✅ Try new features
✅ Tune hyperparameters
✅ Test architectures
✅ Compare strategies
✅ Generate hypotheses
✅ Detect failure modes
✅ Learn from mistakes structurally

WHAT IT CANNOT DO:
❌ Deploy models to production
❌ Change risk rules
❌ Access capital
❌ Modify governance constraints
❌ Execute real trades

ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE CORE                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    HYPOTHESIS ENGINE                                  │   │
│  │  • Generate hypotheses about market behavior                         │   │
│  │  • Test hypotheses against historical data                           │   │
│  │  • Refine hypotheses based on evidence                               │   │
│  │  • Kill hypotheses that fail validation                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    STRUCTURAL MEMORY                                  │   │
│  │  • Remember WHY decisions failed (not just THAT they failed)         │   │
│  │  • Build causal graphs of failure modes                              │   │
│  │  • Detect recurring structural patterns                              │   │
│  │  • Never forget failure mechanisms                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FAILURE MODE DETECTOR                              │   │
│  │  • Detect unseen failure modes before they cause losses              │   │
│  │  • Learn how decision-making breaks under uncertainty                │   │
│  │  • Identify regime changes faster than market                        │   │
│  │  • Predict when models will fail                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SELF-AUDIT SYSTEM                                  │   │
│  │  • Continuously audit all research activities                        │   │
│  │  • Verify hypothesis quality and validity                            │   │
│  │  • Check for overfitting, data snooping, p-hacking                   │   │
│  │  • Enforce governance rules                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    ADVERSARIAL HARDENING                              │   │
│  │  • Become harder to fool than the market                             │   │
│  │  • Generate adversarial scenarios                                    │   │
│  │  • Test against worst-case conditions                                │   │
│  │  • Build robustness through stress testing                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GOVERNANCE LAYER                                   │   │
│  │  • IMMUTABLE rules AI cannot change                                  │   │
│  │  • Capability boundaries                                             │   │
│  │  • Human approval for deployment                                     │   │
│  │  • Audit trail for all activities                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

MODULES:
1. hypothesis_engine.py - Hypothesis generation and testing
2. structural_memory.py - Structural mistake memory
3. failure_detector.py - Failure mode detection
4. self_audit.py - Continuous self-auditing
5. adversarial_hardening.py - Becoming harder to fool
6. governance.py - Immutable governance rules
7. research_orchestrator.py - Master coordinator
8. agent_army.py - 60 specialized research agents
9. self_improvement.py - Recursive self-improvement engine
10. bloomberg_plus.py - Bloomberg Terminal++ features
11. elite_trading_mastery.py - 50+ elite trading skills
12. elite_trader_learning.py - Recursive elite trader learning
"""

from typing import Dict, Any, Optional

# Lazy imports to avoid circular dependencies
def _get_hypothesis_engine():
    from .hypothesis_engine import HypothesisEngine
    return HypothesisEngine

def _get_structural_memory():
    from .structural_memory import StructuralMemory
    return StructuralMemory

def _get_failure_detector():
    from .failure_detector import FailureModeDetector
    return FailureModeDetector

def _get_self_audit():
    from .self_audit import SelfAuditSystem
    return SelfAuditSystem

def _get_adversarial_hardening():
    from .adversarial_hardening import AdversarialHardening
    return AdversarialHardening

def _get_governance():
    from .governance import GovernanceLayer
    return GovernanceLayer

def _get_orchestrator():
    from .research_orchestrator import ResearchOrchestrator
    return ResearchOrchestrator

def _get_agent_army():
    from .agent_army import AgentArmy
    return AgentArmy

def _get_self_improvement():
    from .self_improvement import SelfImprovementEngine
    return SelfImprovementEngine

def _get_bloomberg_plus():
    from .bloomberg_plus import BloombergTerminalPlus
    return BloombergTerminalPlus

def _get_elite_mastery():
    from .elite_trading_mastery import EliteTradingMastery
    return EliteTradingMastery

def _get_elite_learning():
    from .elite_trader_learning import EliteTraderLearning
    return EliteTraderLearning


def quick_start(config: Optional[Dict[str, Any]] = None) -> 'ResearchOrchestrator':
    """
    Quick start the Intelligence Core.
    
    Args:
        config: Optional configuration
        
    Returns:
        ResearchOrchestrator instance
    """
    ResearchOrchestrator = _get_orchestrator()
    return ResearchOrchestrator(config or {})


def quick_start_army() -> 'AgentArmy':
    """
    Quick start the 60-Agent Army.
    
    Returns:
        AgentArmy instance with all 60 agents deployed
    """
    AgentArmy = _get_agent_army()
    return AgentArmy()


def quick_start_improvement() -> 'SelfImprovementEngine':
    """
    Quick start the recursive self-improvement engine.
    
    Returns:
        SelfImprovementEngine instance
    """
    SelfImprovementEngine = _get_self_improvement()
    return SelfImprovementEngine()


def quick_start_bloomberg_plus() -> 'BloombergTerminalPlus':
    """
    Quick start Bloomberg Terminal++.
    
    Returns:
        BloombergTerminalPlus instance with superior capabilities
    """
    BloombergTerminalPlus = _get_bloomberg_plus()
    return BloombergTerminalPlus()


def quick_start_elite_mastery() -> 'EliteTradingMastery':
    """
    Quick start Elite Trading Mastery system.
    
    Returns:
        EliteTradingMastery instance with 50+ trading skills
    """
    EliteTradingMastery = _get_elite_mastery()
    return EliteTradingMastery()


def quick_start_elite_learning() -> 'EliteTraderLearning':
    """
    Quick start Elite Trader Learning system.
    
    Returns:
        EliteTraderLearning instance for recursive skill mastery
    """
    EliteTraderLearning = _get_elite_learning()
    return EliteTraderLearning()


__all__ = [
    'quick_start',
    'quick_start_army',
    'quick_start_improvement',
    'quick_start_bloomberg_plus',
    'quick_start_elite_mastery',
    'quick_start_elite_learning',
    'HypothesisEngine',
    'StructuralMemory',
    'FailureModeDetector',
    'SelfAuditSystem',
    'AdversarialHardening',
    'GovernanceLayer',
    'ResearchOrchestrator',
    'AgentArmy',
    'SelfImprovementEngine',
    'BloombergTerminalPlus',
    'EliteTradingMastery',
    'EliteTraderLearning'
]
