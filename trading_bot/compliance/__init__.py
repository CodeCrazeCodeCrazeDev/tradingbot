"""
Compliance package for AlphaAlgo 2.0
"""

from .compliance_monitor import ComplianceMonitor

__all__ = ['ComplianceMonitor', 'ComplianceManager']

# Alias for backward compatibility
ComplianceManager = ComplianceMonitor

# === Auto-added missing module imports for compliance ===

try:
    from .trade_surveillance import *  # Auto-added: was missing from __init__.py
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed for trade_surveillance: {e}')

