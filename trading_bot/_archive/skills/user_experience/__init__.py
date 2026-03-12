"""
user_experience package
"""

try:
    from .alert_system import Alert, AlertResult, IntelligentAlertSystem
    from .dashboard_builder import DashboardBuilder, DashboardResult, Widget
    from .explainability import ExplainabilityEngine, ExplainabilityResult, Explanation
    from .natural_language import NLPResult, NaturalLanguageInterface
    from .notification_router import Notification, NotificationRouter, RouterResult
    from .report_generator import AutomatedReportGenerator, ReportResult
    from .trade_journal import JournalInsight, JournalResult, TradeJournalAnalyzer
    from .voice_assistant import VoiceAssistant, VoiceResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in user_experience: {e}')

__all__ = [
    'Alert',
    'AlertResult',
    'AutomatedReportGenerator',
    'DashboardBuilder',
    'DashboardResult',
    'ExplainabilityEngine',
    'ExplainabilityResult',
    'Explanation',
    'IntelligentAlertSystem',
    'JournalInsight',
    'JournalResult',
    'NLPResult',
    'NaturalLanguageInterface',
    'Notification',
    'NotificationRouter',
    'ReportResult',
    'RouterResult',
    'TradeJournalAnalyzer',
    'VoiceAssistant',
    'VoiceResult',
    'Widget',
]