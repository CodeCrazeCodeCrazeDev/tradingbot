"""
AAMIS Master Orchestrator Shim - UCA 2026 Core Component
======================================================

Provides backward compatibility for consolidated AAMIS systems.
Delegates cleanly to CognitiveSystemController.
"""

from trading_bot.core.csc.controller import CognitiveSystemController

class AAMISMasterOrchestrator:
    def __init__(self):
        self.csc = CognitiveSystemController()
