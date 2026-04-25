"""
Regulatory Change Classifier
=============================

Classifies signals related to regulatory and policy changes.
"""

from typing import List, Optional
import logging

from ..classifier import ClassificationResult, ClassificationCategory
from ...signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class RegulatoryChangeClassifier:
    """Classifier for regulatory and policy signals."""
    
    def __init__(self):
        self.category = ClassificationCategory.REGULATORY_CHANGE
        logger.info("RegulatoryChangeClassifier initialized")
    
    def classify(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify regulatory change anomalies."""
        regulatory_keywords = [
            'regulation', 'sec', 'fed', 'policy', 'legislation', 'compliance',
            'hearing', 'bill', 'law', 'rule', 'guidance', 'enforcement'
        ]
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_regulatory = any(kw in desc_lower or kw in source_str for kw in regulatory_keywords)
        
        if not is_regulatory:
            return None
        
        if any(word in desc_lower for word in ['approve', 'favorable', 'ease', 'deregulate', 'clear']):
            sub_category = "positive_regulatory"
        elif any(word in desc_lower for word in ['ban', 'restrict', 'crackdown', 'investigate', 'fine']):
            sub_category = "negative_regulatory"
        else:
            sub_category = "regulatory_development"
        
        return ClassificationResult(
            category=self.category,
            confidence=min(1.0, anomaly.confidence * 1.1),
            sub_category=sub_category,
            key_indicators=['policy_shift', 'regulatory_announcement'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else ['sector_etfs'],
            time_horizon="long_term",
        )
