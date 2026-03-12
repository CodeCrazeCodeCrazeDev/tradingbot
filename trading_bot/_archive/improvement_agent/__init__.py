"""
Autonomous Improvement Agent
=============================

A self-directed AI agent that systematically analyzes, improves, and evolves
the trading bot codebase to become the absolute best trading system possible.

CORE MISSION:
Transform the existing codebase into a world-class trading system by:
1. Reading and understanding every line of code
2. Identifying weaknesses, gaps, and improvement opportunities
3. Proposing concrete improvements with full implementation
4. Generating comprehensive tests
5. Creating change proposals for human review
6. Learning from feedback to improve future proposals

WORKFLOW:
1. OBSERVE - Deep analysis of entire codebase
2. IDENTIFY - Find weak points, bugs, gaps, opportunities
3. PROPOSE - Generate improvement proposals with full code
4. TEST - Create comprehensive tests for all changes
5. REVIEW - Present changes for human approval
6. APPLY - Implement approved changes
7. LEARN - Improve from feedback

HUMAN OVERSIGHT:
- All changes require human approval before application
- Protected files have additional safeguards
- Agent can be directed and redirected at any time
- Full transparency in all decisions and proposals

Author: Autonomous Improvement Agent
Version: 1.0.0
"""

from .deep_analyzer import (
    DeepCodebaseAnalyzer,
    FileAnalysisResult,
    ModuleAnalysisResult,
    CodebaseSnapshot,
    AnalysisDepth,
)

from .weakness_detector import (
    WeaknessDetector,
    Weakness,
    WeaknessCategory,
    WeaknessSeverity,
    WeaknessReport,
)

from .improvement_proposer import (
    ImprovementProposer,
    Improvement,
    ImprovementType,
    ImprovementPriority,
    ImprovementProposal,
)

from .test_generator import (
    TestGenerator,
    GeneratedTest,
    TestType,
    TestSuite,
)

from .change_manager import (
    ChangeManager,
    ChangeRequest,
    ChangeStatus,
    ChangeHistory,
)

from .agent_orchestrator import (
    ImprovementAgent,
    AgentConfig,
    AgentMode,
    AgentState,
    AgentDirective,
)

from .agent_interface import (
    AgentInterface,
    AgentCommand,
    AgentResponse,
    ObservationReport,
)

__all__ = [
    # Deep Analyzer
    "DeepCodebaseAnalyzer",
    "FileAnalysisResult",
    "ModuleAnalysisResult",
    "CodebaseSnapshot",
    "AnalysisDepth",
    # Weakness Detector
    "WeaknessDetector",
    "Weakness",
    "WeaknessCategory",
    "WeaknessSeverity",
    "WeaknessReport",
    # Improvement Proposer
    "ImprovementProposer",
    "Improvement",
    "ImprovementType",
    "ImprovementPriority",
    "ImprovementProposal",
    # Test Generator
    "TestGenerator",
    "GeneratedTest",
    "TestType",
    "TestSuite",
    # Change Manager
    "ChangeManager",
    "ChangeRequest",
    "ChangeStatus",
    "ChangeHistory",
    # Agent Orchestrator
    "ImprovementAgent",
    "AgentConfig",
    "AgentMode",
    "AgentState",
    "AgentDirective",
    # Agent Interface
    "AgentInterface",
    "AgentCommand",
    "AgentResponse",
    "ObservationReport",
]

__version__ = "1.0.0"
