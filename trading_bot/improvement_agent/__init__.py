"""
Improvement Agent Module - Under Hivemind Control
============================================================

All improvement agents are controlled by the Hivemind.
"""

# change_manager
try:
    from .change_manager import ChangeManager
except ImportError:
    ChangeManager = None

# agent_orchestrator
try:
    from .agent_orchestrator import ImprovementAgent
except ImportError:
    ImprovementAgent = None

# Other components
try:
    from .deep_analyzer import DeepAnalyzer
except ImportError:
    DeepAnalyzer = None

try:
    from .weakness_detector import WeaknessDetector
except ImportError:
    WeaknessDetector = None

try:
    from .improvement_proposer import ImprovementProposer
except ImportError:
    ImprovementProposer = None


class HivemindImprovementAdapter:
    """
    Adapter that connects Improvement Agent to the Hivemind.
    
    This ensures all improvement agents are controlled by
    the central hivemind intelligence.
    """
    
    def __init__(self, hivemind_controller=None, config=None):
        self.hivemind = hivemind_controller
        self.config = config or {}
        self.improvement_agent = None
        self.change_manager = None
        self.deep_analyzer = None
        self.weakness_detector = None
        self.improvement_proposer = None
        self._initialized = False
        self._running = False
    
    async def initialize(self):
        """Initialize Improvement Agent under hivemind control."""
        try:
            self.improvement_agent = ImprovementAgent(config=self.config)
        except Exception:
            pass
        
        try:
            self.change_manager = ChangeManager(config=self.config)
        except Exception:
            pass
        
        try:
            self.deep_analyzer = DeepAnalyzer(config=self.config)
        except Exception:
            pass
        
        try:
            self.weakness_detector = WeaknessDetector(config=self.config)
        except Exception:
            pass
        
        try:
            self.improvement_proposer = ImprovementProposer(config=self.config)
        except Exception:
            pass
        
        self._initialized = True
    
    async def start(self):
        """Start the improvement agent system."""
        self._running = True
    
    async def stop(self):
        """Stop the improvement agent system."""
        self._running = False
    
    def get_status(self):
        """Get status of the improvement agent system."""
        return {
            'initialized': self._initialized,
            'running': self._running,
            'improvement_agent_active': self.improvement_agent is not None,
            'change_manager_active': self.change_manager is not None,
            'deep_analyzer_active': self.deep_analyzer is not None,
            'weakness_detector_active': self.weakness_detector is not None,
            'improvement_proposer_active': self.improvement_proposer is not None,
            'under_hivemind_control': self.hivemind is not None,
        }


# Backward compatibility
AgentOrchestrator = HivemindImprovementAdapter

__all__ = [
    'HivemindImprovementAdapter',
    'AgentOrchestrator',
    'ChangeManager',
    'ImprovementAgent',
    'DeepAnalyzer',
    'WeaknessDetector',
    'ImprovementProposer',
]

