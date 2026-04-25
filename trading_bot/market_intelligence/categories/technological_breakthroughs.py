"""
Technological Breakthroughs Classifier
=======================================

Classifies signals related to technological innovation.
"""

from typing import List, Optional
import logging

from ..classifier import ClassificationResult, ClassificationCategory
from ...signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class TechnologicalBreakthroughsClassifier:
    """Classifier for technology and innovation signals."""
    
    def __init__(self):
        self.category = ClassificationCategory.TECHNOLOGICAL_BREAKTHROUGHS
        logger.info("TechnologicalBreakthroughsClassifier initialized")
    
    def classify(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """Classify technology breakthrough anomalies."""
        tech_keywords = [
            'patent', 'github', 'protocol', 'upgrade', 'launch', 'product', 'ai',
            'ml', 'blockchain', 'defi', 'innovation', 'breakthrough', 'research'
        ]
        
        desc_lower = anomaly.description.lower()
        source_str = anomaly.data_source.value if anomaly.data_source else ""
        
        is_tech = any(kw in desc_lower or kw in source_str for kw in tech_keywords)
        
        if not is_tech:
            return None
        
        if 'patent' in desc_lower:
            sub_category = "patent_filing"
        elif 'github' in source_str or 'commit' in desc_lower:
            sub_category = "developer_activity"
        elif 'protocol' in desc_lower or 'upgrade' in desc_lower:
            sub_category = "protocol_upgrade"
        elif 'product' in desc_lower or 'launch' in desc_lower:
            sub_category = "product_launch"
        elif 'ai' in desc_lower or 'ml' in desc_lower:
            sub_category = "ai_breakthrough"
        else:
            sub_category = "tech_innovation"
        
        return ClassificationResult(
            category=self.category,
            confidence=anomaly.confidence * 0.9,
            sub_category=sub_category,
            key_indicators=['innovation', 'disruption', 'adoption'],
            affected_assets=[anomaly.primary_asset] if anomaly.primary_asset else ['tech_stocks'],
            time_horizon="medium_term",
        )
