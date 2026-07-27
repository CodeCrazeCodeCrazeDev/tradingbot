"""
Orchestration Sub-package for Research OS.
Hosts the SovereignResearchOrchestrator kernel and CLI command handlers.
"""

from .kernel import SovereignResearchOrchestrator
from .cli import run_cli

__all__ = [
    'SovereignResearchOrchestrator',
    'run_cli'
]
