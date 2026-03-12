"""
wealth package
"""

try:
    from .comprehensive_wealth_manager import (
        AccountType,
        ClientProfile,
        ESGAnalyzer,
        ESGCategory,
        ESGScore,
        RiskProfile,
        TaxHarvestingOpportunity,
        TaxLot,
        TaxOptimizer,
        WealthManager
    )
    from .free_wealth_manager import (
        FreeClient,
        FreeESGScorer,
        FreePortfolioAnalyzer,
        FreeRiskProfile,
        FreeTaxOptimizer,
        FreeWealthManager
    )
    from .wealth_management import (
        ClientPortalManager,
        ClientProfile,
        ESGScore,
        ESGScoringSystem,
        RiskProfile,
        RiskProfileManager,
        TaxEvent,
        TaxOptimizationEngine,
        retry
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in wealth: {e}')

__all__ = [
    'AccountType',
    'ClientPortalManager',
    'ClientProfile',
    'ESGAnalyzer',
    'ESGCategory',
    'ESGScore',
    'ESGScoringSystem',
    'FreeClient',
    'FreeESGScorer',
    'FreePortfolioAnalyzer',
    'FreeRiskProfile',
    'FreeTaxOptimizer',
    'FreeWealthManager',
    'RiskProfile',
    'RiskProfileManager',
    'TaxEvent',
    'TaxHarvestingOpportunity',
    'TaxLot',
    'TaxOptimizationEngine',
    'TaxOptimizer',
    'WealthManager',
    'retry',
]