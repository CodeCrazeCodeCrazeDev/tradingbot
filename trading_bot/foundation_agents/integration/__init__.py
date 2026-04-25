"""
Integration Module - Bridges to Existing Systems
==================================================

Provides integration adapters for connecting Foundation Agents
with existing trading bot infrastructure.
"""

from .existing_systems_bridge import (
    ExistingSystemsBridge,
    IntegrationConfig,
    ImprovementOrchestratorAdapter,
    SelfAssemblyAdapter,
    AlphaDiscoveryAdapter
)

__all__ = [
    'ExistingSystemsBridge',
    'IntegrationConfig',
    'ImprovementOrchestratorAdapter',
    'SelfAssemblyAdapter',
    'AlphaDiscoveryAdapter'
]
