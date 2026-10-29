"""
Institutional Research Lab sub-package.

Organizes the Sovereign Research OS kernel as an institution-grade research lab:
a fixed org chart of divisions, an auditable minutes ledger, and institutional
reporting per research program.
"""

from .divisions import (
    ResearchDivision,
    STAGE_TO_DIVISION,
    build_org_chart,
    division_for_stage,
)
from .minutes import LabMinute, LabMinutesLedger
from .institutional_lab import (
    DivisionReport,
    InstitutionalResearchLab,
    LabReport,
)

__all__ = [
    "ResearchDivision",
    "STAGE_TO_DIVISION",
    "build_org_chart",
    "division_for_stage",
    "LabMinute",
    "LabMinutesLedger",
    "DivisionReport",
    "InstitutionalResearchLab",
    "LabReport",
]
