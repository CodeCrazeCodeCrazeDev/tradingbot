"""
Self-Coordinating AI Infrastructure
====================================

Autonomous financial intelligence infrastructure that:
- Discovers new market opportunities autonomously
- Self-programs and proposes improvements continuously
- Maintains an immutable Core Production System
- Runs all AI-generated changes in isolated sandboxes
- Controls compute budgets and resources
- Maintains an experiment registry
- Enforces data integrity through firewalls
- Scans all code for safety before execution
- Promotes validated changes through a rigorous system

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    SELF-COORDINATING AI                         │
    ├─────────────────────────────────────────────────────────────────┤
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │              CORE PRODUCTION SYSTEM (IMMUTABLE)           │  │
    │  │  - Live trading engine                                    │  │
    │  │  - Risk management                                        │  │
    │  │  - Portfolio management                                   │  │
    │  │  - CANNOT be modified by AI                               │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                              ↑                                  │
    │                    [Promotion System]                           │
    │                              ↑                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │              SANDBOX ENVIRONMENT                          │  │
    │  │  - Isolated execution                                     │  │
    │  │  - Resource limits                                        │  │
    │  │  - No production access                                   │  │
    │  │  - All AI changes run here first                          │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                              ↑                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │              SAFETY LAYER                                 │  │
    │  │  - Code Safety Scanner                                    │  │
    │  │  - Data Integrity Firewall                                │  │
    │  │  - Compute Budget Controller                              │  │
    │  └──────────────────────────────────────────────────────────┘  │
    │                              ↑                                  │
    │  ┌──────────────────────────────────────────────────────────┐  │
    │  │              SELF-PROGRAMMING ENGINE                      │  │
    │  │  - Improvement Proposer                                   │  │
    │  │  - Market Opportunity Discovery                           │  │
    │  │  - Experiment Registry                                    │  │
    │  └──────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘

Author: AlphaAlgo Trading System
"""

from .core_production_system import CoreProductionSystem, ProductionConfig
from .sandbox_executor import SandboxExecutor, SandboxConfig, ExecutionResult
from .compute_budget_controller import ComputeBudgetController, BudgetConfig, ResourceAllocation
from .experiment_registry import ExperimentRegistry, Experiment, ExperimentStatus
from .data_integrity_firewall import DataIntegrityFirewall, FirewallConfig, AccessRequest
from .code_safety_scanner import CodeSafetyScanner, ScanResult, SecurityLevel
from .promotion_system import PromotionSystem, PromotionRequest, PromotionStatus
from .market_opportunity_discovery import MarketOpportunityDiscovery, Opportunity, OpportunityType
from .self_programming_proposer import SelfProgrammingProposer, Improvement, ImprovementType
from .orchestrator import SelfCoordinatingAIOrchestrator


class HivemindSelfCoordinatingAdapter:
    """
    Adapter that connects Self-Coordinating AI to the Hivemind.
    
    This ensures the self-coordinating AI system is controlled by
    the central hivemind intelligence.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.orchestrator = None
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize Self-Coordinating AI under hivemind control."""
        from .orchestrator import OrchestratorConfig
        
        orch_config = OrchestratorConfig(**self.config)
        self.orchestrator = SelfCoordinatingAIOrchestrator(orch_config)
        self._initialized = True
    
    async def start(self):
        """Start the self-coordinating AI system."""
        if self.orchestrator:
            await self.orchestrator.start()
        self._running = True
    
    async def stop(self):
        """Stop the self-coordinating AI system."""
        if self.orchestrator:
            await self.orchestrator.stop()
        self._running = False
    
    def get_status(self):
        """Get status of the self-coordinating AI system."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'orchestrator_active': self.orchestrator is not None,
            'under_hivemind_control': self.hivemind is not None,
        }


__all__ = [
    # Core Systems
    'CoreProductionSystem',
    'ProductionConfig',
    
    # Sandbox
    'SandboxExecutor',
    'SandboxConfig',
    'ExecutionResult',
    
    # Budget Control
    'ComputeBudgetController',
    'BudgetConfig',
    'ResourceAllocation',
    
    # Experiment Registry
    'ExperimentRegistry',
    'Experiment',
    'ExperimentStatus',
    
    # Data Integrity
    'DataIntegrityFirewall',
    'FirewallConfig',
    'AccessRequest',
    
    # Code Safety
    'CodeSafetyScanner',
    'ScanResult',
    'SecurityLevel',
    
    # Promotion
    'PromotionSystem',
    'PromotionRequest',
    'PromotionStatus',
    
    # Market Discovery
    'MarketOpportunityDiscovery',
    'Opportunity',
    'OpportunityType',
    
    # Self-Programming
    'SelfProgrammingProposer',
    'Improvement',
    'ImprovementType',
    
    # Main Orchestrator
    'SelfCoordinatingAIOrchestrator',
    
    # Hivemind Adapter
    'HivemindSelfCoordinatingAdapter',
]

__version__ = '1.0.0'
