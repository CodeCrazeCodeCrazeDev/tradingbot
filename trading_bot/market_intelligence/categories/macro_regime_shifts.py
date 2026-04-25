"""
Macro Regime Shifts Classifier
==============================

Classifies signals related to macroeconomic regime changes.
"""

from typing import List, Optional
import logging

from ..classifier import ClassificationResult, ClassificationCategory
from ...signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class MacroRegimeShiftsClassifier:
    """Classifier for macroeconomic regime signals."""
    
    def __init__(self):
        self.category = ClassificationCategory.MACRO_REGIME_SHIFTS
        logger.info("MacroRegimeShiftsClassifier initialized")
    
    def classify(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify macro regime shift anomalies."""
        macro_keywords = [
            'inflation', 'recession', 'gdp', 'employment', 'unemployment', 'cpi', 'ppi',
            'yield_curve', 'fed', 'ecb', 'boj', 'nfp', 'jobs', 'rate', 'policy'
        ]
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_macro = any(kw in desc_lower or kw in source_str for kw in macro_keywords)
        is_regime_change = anomaly.anomaly_type.value == 'regime_change'
        
        if not (is_macro or is_regime_change):
            return None
        
        if 'inflation' in desc_lower or 'cpi' in desc_lower or 'ppi' in desc_lower:
            sub_category = "inflation_regime"
        elif 'recession' in desc_lower or 'gdp' in desc_lower:
            sub_category = "growth_regime"
        elif 'yield' in desc_lower or 'rate' in desc_lower:
            sub_category = "monetary_policy_regime"
        elif 'employment' in desc_lower or 'jobs' in desc_lower or 'nfp' in desc_lower:
            sub_category = "employment_regime"
        else:
            sub_category = "macro_shift"
        
        return ClassificationResult(
            category=self.category,
            confidence=anomaly.confidence,
            sub_category=sub_category,
            key_indicators=['regime_change', 'macro_indicator'],
            affected_assets=['macro_etfs', 'bonds', 'currencies', 'commodities'],
            time_horizon="long_term",
        )
