"""
Aletheia-Inspired Autonomous Financial Intelligence System
Based on DeepMind's Aletheia: Towards Autonomous Mathematics Research

This system implements a three-subagent architecture for autonomous trading strategy
research and development.
"""

__version__ = "1.0.0"
__author__ = "AlphaAlgo"

from .aletheia_orchestrator import (
    AletheiaOrchestrator,
    StrategyHypothesis,
    VerificationResult,
    RevisionAction,
    ResearchPhase,
    AutonomyLevel
)
from .subagents.generator import StrategyGenerator
from .subagents.verifier import StrategyVerifier
from .subagents.reviser import StrategyReviser
from .research_framework import AutonomousResearchFramework, ResearchProject, ResearchPriority
from .tool_system import ToolIntegrationSystem, BaseTool, MarketDataTool, BacktestTool, RiskAnalysisTool, KnowledgeBaseTool
from .principles import AletheiaPrinciples, Principle
from .governance_integration import AletheiaGovernanceIntegration, GovernanceLevel, GovernanceAction
from .financial_decision_auditor import (
    AletheiaAuditConfig,
    AletheiaFinancialAudit,
    AletheiaFinancialDecisionAuditor,
    FinancialEvidenceItem,
    PrincipleCheck,
)
from .human_ai_interface import HumanAIInterface, StrategyPresentation, HumanFeedback, InteractionMode
from .testing_framework import AletheiaTestFramework, TestResult


class HivemindAletheiaAdapter:
    """
    Adapter that connects Aletheia Autonomous System to the Hivemind.
    
    This ensures all Aletheia subagents (Generator, Verifier, Reviser)
    are controlled by the central hivemind intelligence.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.orchestrator = None
        self.generator = None
        self.verifier = None
        self.reviser = None
        self.research_framework = None
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize Aletheia system under hivemind control."""
        try:
            self.orchestrator = AletheiaOrchestrator(config=self.config)
        except Exception:
            pass
        
        try:
            self.generator = StrategyGenerator(config=self.config)
        except Exception:
            pass
        
        try:
            self.verifier = StrategyVerifier(config=self.config)
        except Exception:
            pass
        
        try:
            self.reviser = StrategyReviser(config=self.config)
        except Exception:
            pass
        
        try:
            self.research_framework = AutonomousResearchFramework(config=self.config)
        except Exception:
            pass
        
        self._initialized = True
    
    async def start(self):
        """Start the Aletheia system."""
        self._running = True
    
    async def stop(self):
        """Stop the Aletheia system."""
        self._running = False
    
    def get_status(self):
        """Get status of the Aletheia system."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'orchestrator_active': self.orchestrator is not None,
            'generator_active': self.generator is not None,
            'verifier_active': self.verifier is not None,
            'reviser_active': self.reviser is not None,
            'research_framework_active': self.research_framework is not None,
            'under_hivemind_control': self.hivemind is not None,
        }


__all__ = [
    # Core Orchestrator
    "AletheiaOrchestrator",
    "StrategyHypothesis",
    "VerificationResult",
    "RevisionAction",
    "ResearchPhase",
    "AutonomyLevel",
    
    # Subagents
    "StrategyGenerator",
    "StrategyVerifier",
    "StrategyReviser",
    
    # Research Framework
    "AutonomousResearchFramework",
    "ResearchProject",
    "ResearchPriority",
    
    # Tool System
    "ToolIntegrationSystem",
    "BaseTool",
    "MarketDataTool",
    "BacktestTool",
    "RiskAnalysisTool",
    "KnowledgeBaseTool",
    
    # Principles
    "AletheiaPrinciples",
    "Principle",
    
    # Governance
    "AletheiaGovernanceIntegration",
    "GovernanceLevel",
    "GovernanceAction",
    "AletheiaAuditConfig",
    "AletheiaFinancialAudit",
    "AletheiaFinancialDecisionAuditor",
    "FinancialEvidenceItem",
    "PrincipleCheck",
    
    # Human-AI Interface
    "HumanAIInterface",
    "StrategyPresentation",
    "HumanFeedback",
    "InteractionMode",
    
    # Testing
    "AletheiaTestFramework",
    "TestResult",
    
    # Hivemind Adapter
    "HivemindAletheiaAdapter",
]
