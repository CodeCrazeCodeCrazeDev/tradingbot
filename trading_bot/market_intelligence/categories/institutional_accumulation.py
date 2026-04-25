"""
Institutional Accumulation Classifier
======================================

Classifies signals related to institutional/smart money activity.
"""

from typing import List, Optional
import logging

from ..classifier import ClassificationResult, ClassificationCategory
from ...signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class InstitutionalAccumulationClassifier:
    """Classifier for institutional/smart money signals."""
    
    def __init__(self):
        self.category = ClassificationCategory.INSTITUTIONAL_ACCUMULATION
        logger.info("InstitutionalAccumulationClassifier initialized")
    
    def classify(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify institutional activity anomalies."""
        institutional_keywords = [
            'institutional', 'whale', '13f', '13d', '13g', 'otc', 'block',
            'smart_money', 'hedge_fund', 'mutual_fund', 'pension'
        ]
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_institutional = any(kw in desc_lower or kw in source_str for kw in institutional_keywords)
        
        if not is_institutional:
            return None
        
        if any(word in desc_lower for word in ['buy', 'accumulate', 'inflow', 'long']):
            sub_category = "institutional_accumulation"
        elif any(word in desc_lower for word in ['sell', 'distribute', 'outflow', 'short']):
            sub_category = "institutional_distribution"
        else:
            sub_category = "institutional_activity"
        
        return ClassificationResult(
            category=self.category,
            confidence=anomaly.confidence,
            sub_category=sub_category,
            key_indicators=['large_position', 'smart_money_flow'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else [],
            time_horizon="medium_term",
        )
