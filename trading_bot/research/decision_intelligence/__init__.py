"""
Decision Intelligence and Auditing Sub-package for Research OS.
Generates immutable signed DecisionRecords and retroactively audits decision accuracy.
"""

from .auditor import SovereignDecisionAuditor

__all__ = [
    'SovereignDecisionAuditor'
]
