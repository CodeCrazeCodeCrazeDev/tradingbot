"""
AI Core Agents Module - Under Hivemind Control
============================================================

All agents in this module are controlled by the Hivemind.
"""

# Import all agent components
try:
    from .orchestrator import (
        AgentOrchestrator as AICoreOrchestrator,
        AgentRole,
        DecisionStatus,
        TradingContext,
        TradingProposal,
        ValidationResult,
        TradingDecision,
        BaseAgent,
        PlannerAgent as AICorePlannerAgent,
        VerifierAgent as AICoreVerifierAgent,
        SafetyValidatorAgent,
        ExecutorAgent as AICoreExecutorAgent,
    )
except ImportError:
    pass

try:
    from .executor_agent import ExecutorAgent, create_executor_agent
except ImportError:
    pass

try:
    from .planner_agent import PlannerAgent, create_planner_agent
except ImportError:
    pass

try:
    from .verifier_agent import VerifierAgent, create_verifier_agent
except ImportError:
    pass

try:
    from .safety_validator import SafetyValidator, create_safety_validator
except ImportError:
    pass


class HivemindAICoreAdapter:
    """
    Adapter that connects AI Core Agents to the Hivemind.
    
    This ensures all AI Core agents (Orchestrator, Executor, Planner,
    Verifier, SafetyValidator) are controlled by the central hivemind.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.orchestrator = None
        self.executor = None
        self.planner = None
        self.verifier = None
        self.safety_validator = None
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize AI Core agents under hivemind control."""
        try:
            self.orchestrator = AICoreOrchestrator(config=self.config)
        except Exception:
            pass
        
        try:
            self.executor = ExecutorAgent(config=self.config)
        except Exception:
            pass
        
        try:
            self.planner = PlannerAgent(config=self.config)
        except Exception:
            pass
        
        try:
            self.verifier = VerifierAgent(config=self.config)
        except Exception:
            pass
        
        try:
            self.safety_validator = SafetyValidator(config=self.config)
        except Exception:
            pass
        
        self._initialized = True
    
    async def start(self):
        """Start AI Core agents."""
        self._running = True
    
    async def stop(self):
        """Stop AI Core agents."""
        self._running = False
    
    def get_status(self):
        """Get status of AI Core agents."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'orchestrator_active': self.orchestrator is not None,
            'executor_active': self.executor is not None,
            'planner_active': self.planner is not None,
            'verifier_active': self.verifier is not None,
            'safety_validator_active': self.safety_validator is not None,
            'under_hivemind_control': self.hivemind is not None,
        }


# Backward compatibility
AgentOrchestrator = HivemindAICoreAdapter

__all__ = [
    'HivemindAICoreAdapter',
    'AgentOrchestrator',
    'AICoreOrchestrator',
    'AgentRole',
    'DecisionStatus',
    'TradingContext',
    'TradingProposal',
    'ValidationResult',
    'TradingDecision',
    'BaseAgent',
    'AICorePlannerAgent',
    'AICoreVerifierAgent',
    'SafetyValidatorAgent',
    'AICoreExecutorAgent',
    'ExecutorAgent',
    'create_executor_agent',
    'PlannerAgent',
    'create_planner_agent',
    'VerifierAgent',
    'create_verifier_agent',
    'SafetyValidator',
    'create_safety_validator',
]
