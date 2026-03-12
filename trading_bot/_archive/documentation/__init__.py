"""Documentation Module - Trade Documentation System."""

try:
    from .trade_documentation import (
        TradeJournal,
        TradeDocument,
        TradeReviewSystem,
        TradeEntry,
        TradeExit,
        RiskManagement,
        TradeReview,
        Screenshot,
        TradeQuality,
        SetupType,
        EmotionalState,
        MistakeType,
        create_trade_journal,
        quick_trade_entry
    )
except ImportError:
    TradeJournal = None

__all__ = [
    'TradeJournal',
    'TradeDocument',
    'TradeReviewSystem',
    'TradeEntry',
    'TradeExit',
    'RiskManagement',
    'TradeReview',
    'Screenshot',
    'TradeQuality',
    'SetupType',
    'EmotionalState',
    'MistakeType',
    'create_trade_journal',
    'quick_trade_entry',
]
