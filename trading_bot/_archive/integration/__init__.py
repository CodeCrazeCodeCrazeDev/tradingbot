"""
integration package
"""

try:
    from .internet_integration import InternetIntegration, create_internet_integration
    from .market_analysis_dashboard import DashboardConfig, MarketAnalysisDashboard, create_market_analysis_dashboard
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in integration: {e}')

__all__ = [
    'DashboardConfig',
    'InternetIntegration',
    'MarketAnalysisDashboard',
    'create_internet_integration',
    'create_market_analysis_dashboard',
]