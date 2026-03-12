"""
alternative_data package
"""

try:
    from .crypto_onchain import CryptoOnChainAnalyzer, OnChainResult
    from .dark_pool import DarkPoolPrintAnalyzer, DarkPoolResult
    from .earnings_nlp import EarningsCallNLPAnalyzer, EarningsNLPResult
    from .esg_integrator import ESGResult, ESGScoreIntegrator
    from .insider_tracker import InsiderResult, InsiderTradingTracker
    from .options_flow import OptionsFlowAnalyzer, OptionsFlowResult
    from .patent_tracker import PatentFilingTracker, PatentResult
    from .sec_parser import SECFilingParser, SECFilingResult
    from .social_sentiment import SocialSentimentResult, SocialSentimentVelocity
    from .supply_chain import SupplyChainMapper, SupplyChainResult
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in alternative_data: {e}')

__all__ = [
    'CryptoOnChainAnalyzer',
    'DarkPoolPrintAnalyzer',
    'DarkPoolResult',
    'ESGResult',
    'ESGScoreIntegrator',
    'EarningsCallNLPAnalyzer',
    'EarningsNLPResult',
    'InsiderResult',
    'InsiderTradingTracker',
    'OnChainResult',
    'OptionsFlowAnalyzer',
    'OptionsFlowResult',
    'PatentFilingTracker',
    'PatentResult',
    'SECFilingParser',
    'SECFilingResult',
    'SocialSentimentResult',
    'SocialSentimentVelocity',
    'SupplyChainMapper',
    'SupplyChainResult',
]