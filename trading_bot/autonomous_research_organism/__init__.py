"""
Autonomous Research Organism
============================

A self-designing, self-innovative, self-programming AI research infrastructure
that operates within strict sandbox boundaries.

Components:
- SandboxEnvironment: Isolated execution environment for generated code
- ComputeBudgetController: Resource limits (CPU, Memory, Time, Storage)
- DataIntegrityFirewall: Protects critical data from modification
- CodeSafetyScanner: AST analysis and pattern detection for dangerous code
- ExperimentRegistry: Tracks all experiments with full audit trail
- SelfProgrammingEngine: Generates and evolves code safely
- ContinuousResearchOrganism: Main orchestrator for autonomous research

SAFETY PRINCIPLES:
1. All generated code runs in isolated sandbox
2. Compute resources are strictly budgeted
3. Critical data is protected by firewall
4. All code is scanned before execution
5. All experiments are registered and auditable
6. Human override is ALWAYS available
"""

import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
def _get_sandbox_environment():
    from .sandbox_environment import (
        SandboxEnvironment,
        SandboxConfig,
        SandboxResult,
        SandboxViolation,
    )
    return SandboxEnvironment, SandboxConfig, SandboxResult, SandboxViolation

def _get_compute_budget_controller():
    from .compute_budget_controller import (
        ComputeBudgetController,
        ResourceBudget,
        ResourceUsage,
        BudgetExceededError,
    )
    return ComputeBudgetController, ResourceBudget, ResourceUsage, BudgetExceededError

def _get_data_integrity_firewall():
    from .data_integrity_firewall import (
        DataIntegrityFirewall,
        ProtectedResource,
        AccessLevel,
        FirewallViolation,
    )
    return DataIntegrityFirewall, ProtectedResource, AccessLevel, FirewallViolation

def _get_code_safety_scanner():
    from .code_safety_scanner import (
        CodeSafetyScanner,
        ScanResult,
        ThreatLevel,
        CodePattern,
    )
    return CodeSafetyScanner, ScanResult, ThreatLevel, CodePattern

def _get_experiment_registry():
    from .experiment_registry import (
        ExperimentRegistry,
        Experiment,
        ExperimentPhase,
        ExperimentOutcome,
    )
    return ExperimentRegistry, Experiment, ExperimentPhase, ExperimentOutcome

def _get_self_programming_engine():
    from .self_programming_engine import (
        SelfProgrammingEngine,
        CodeGeneration,
        EvolutionStrategy,
    )
    return SelfProgrammingEngine, CodeGeneration, EvolutionStrategy

def _get_continuous_research_organism():
    from .continuous_research_organism import (
        ContinuousResearchOrganism,
        ResearchDirective,
        ResearchCycle,
        create_research_organism,
    )
    return ContinuousResearchOrganism, ResearchDirective, ResearchCycle, create_research_organism

# Direct imports for convenience
try:
    from .sandbox_environment import (
        SandboxEnvironment,
        SandboxConfig,
        SandboxResult,
        SandboxViolation,
    )
    from .compute_budget_controller import (
        ComputeBudgetController,
        ResourceBudget,
        ResourceUsage,
        BudgetExceededError,
    )
    from .data_integrity_firewall import (
        DataIntegrityFirewall,
        ProtectedResource,
        AccessLevel,
        FirewallViolation,
    )
    from .code_safety_scanner import (
        CodeSafetyScanner,
        ScanResult,
        ThreatLevel,
        CodePattern,
    )
    from .experiment_registry import (
        ExperimentRegistry,
        Experiment,
        ExperimentPhase,
        ExperimentOutcome,
    )
    from .self_programming_engine import (
        SelfProgrammingEngine,
        CodeGeneration,
        EvolutionStrategy,
    )
    from .continuous_research_organism import (
        ContinuousResearchOrganism,
        ResearchDirective,
        ResearchCycle,
        create_research_organism,
    )
except ImportError as e:
    logger.warning(f"Some imports failed (may be missing dependencies): {e}")

# Integration module
try:
    from .integration import (
        OrganismIntegrator,
        SafetyIntegration,
        ResearchLabIntegration,
        SelfImprovementIntegration,
        setup_organism_with_integrations,
        quick_start_organism,
    )
except ImportError as e:
    logger.warning(f"Integration imports failed: {e}")

__all__ = [
    # Sandbox
    'SandboxEnvironment',
    'SandboxConfig',
    'SandboxResult',
    'SandboxViolation',
    # Compute Budget
    'ComputeBudgetController',
    'ResourceBudget',
    'ResourceUsage',
    'BudgetExceededError',
    # Data Firewall
    'DataIntegrityFirewall',
    'ProtectedResource',
    'AccessLevel',
    'FirewallViolation',
    # Code Scanner
    'CodeSafetyScanner',
    'ScanResult',
    'ThreatLevel',
    'CodePattern',
    # Experiment Registry
    'ExperimentRegistry',
    'Experiment',
    'ExperimentPhase',
    'ExperimentOutcome',
    # Self Programming
    'SelfProgrammingEngine',
    'CodeGeneration',
    'EvolutionStrategy',
    # Research Organism
    'ContinuousResearchOrganism',
    'ResearchDirective',
    'ResearchCycle',
    'create_research_organism',
    # Integration
    'OrganismIntegrator',
    'SafetyIntegration',
    'ResearchLabIntegration',
    'SelfImprovementIntegration',
    'setup_organism_with_integrations',
    'quick_start_organism',
    # Utilities
    'get_organism_info',
]

__version__ = '1.0.0'


def get_organism_info() -> dict:
    """Get information about the Autonomous Research Organism."""
    return {
        'name': 'Autonomous Research Organism',
        'version': __version__,
        'components': [
            'SandboxEnvironment - Isolated code execution',
            'ComputeBudgetController - Resource management',
            'DataIntegrityFirewall - Data protection',
            'CodeSafetyScanner - Security analysis',
            'ExperimentRegistry - Experiment tracking',
            'SelfProgrammingEngine - Code evolution',
            'ContinuousResearchOrganism - Main orchestrator',
        ],
        'safety_principles': [
            'All generated code runs in isolated sandbox',
            'Compute resources are strictly budgeted',
            'Critical data is protected by firewall',
            'All code is scanned before execution',
            'All experiments are registered and auditable',
            'Human override is ALWAYS available',
        ],
    }
