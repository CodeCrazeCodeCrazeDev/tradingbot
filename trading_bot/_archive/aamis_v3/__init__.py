"""
aamis_v3 package
"""

try:
    from .aamis_master_orchestrator import (
        AAMISDecision,
        AAMISMasterOrchestrator,
        AAMISReport,
        main
    )
    from .complete_aamis_system import (
        AAMISDecisionV3,
        AAMISReportV3,
        CompleteAAMISSystem,
        SystemMode,
        create_aamis_system
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in aamis_v3: {e}')

__all__ = [
    'AAMISDecision',
    'AAMISDecisionV3',
    'AAMISMasterOrchestrator',
    'AAMISReport',
    'AAMISReportV3',
    'CompleteAAMISSystem',
    'SystemMode',
    'create_aamis_system',
    'main',
]