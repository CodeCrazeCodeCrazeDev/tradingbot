"""
Liquidity Movement Classifier
=============================

Classifies signals related to liquidity flows:
- Dark pool prints
- Order book changes
- Flow data
- Bid-ask spread anomalies
- Volume concentration
"""

from typing import List, Optional
import logging

from ..classifier import ClassificationResult, ClassificationCategory
from ...signal_discovery.agents.base_agent import MarketAnomaly

logger = logging.getLogger(__name__)


class LiquidityMovementClassifier:
    """
    Specialized classifier for liquidity movement signals.
    
    Detects:
    - Liquidity inflows/outflows
    - Order book imbalances
    - Dark pool accumulation/distribution
    - Smart money positioning
    """
    
    def __init__(self):
        self.category = ClassificationCategory.LIQUIDITY_MOVEMENT
        logger.info("LiquidityMovementClassifier initialized")
    
    def classify(self, anomaly: MarketAnomaly) -> Optional[ClassificationResult]:
        """
        Classify a liquidity-related anomaly.
        
        Args:
            anomaly: Raw anomaly to classify
            
        Returns:
            ClassificationResult or None if not applicable
        """
        # Check if this is a liquidity signal
        liquidity_keywords = [
            'liquidity', 'flow', 'dark_pool', 'block_trade', 'volume',
            'spread', 'depth', 'order_book', 'bid_ask', 'slippage'
        ]
        
        desc_lower = anomaly.description.lower()
        has_liquidity = any(kw in desc_lower for kw in liquidity_keywords)
        
        if not has_liquidity and anomaly.anomaly_type.value not in [
            'volume_anomaly', 'liquidity_anomaly'
        ]:
            return None
        
        # Determine sub-category
        if 'inflow' in desc_lower or 'accumulation' in desc_lower:
            sub_category = "liquidity_inflow"
        elif 'outflow' in desc_lower or 'distribution' in desc_lower:
            sub_category = "liquidity_outflow"
        elif 'block' in desc_lower:
            sub_category = "block_trade"
        elif 'spread' in desc_lower or 'slippage' in desc_lower:
            sub_category = "spread_expansion"
        else:
            sub_category = "liquidity_shift"
        
        # Determine affected assets
        affected_assets = [anomaly.primary_asset] if anomaly.primary_asset else []
        
        # Add related assets based on sub-category
        if sub_category == "liquidity_inflow":
            affected_assets.extend(self._get_inflow_implications(anomaly))
        elif sub_category == "liquidity_outflow":
            affected_assets.extend(self._get_outflow_implications(anomaly))
        
        return ClassificationResult(
            category=self.category,
            confidence=min(1.0, anomaly.confidence * 1.1),
            sub_category=sub_category,
            key_indicators=['volume_spike', 'flow_direction', 'market_depth'],
            affected_assets=list(set(affected_assets)),
            time_horizon="immediate" if sub_category in ["block_trade", "spread_expansion"] else "short_term",
        )
    
    def _get_inflow_implications(self, anomaly: MarketAnomaly) -> List[str]:
        """Get assets likely affected by liquidity inflow."""
        implications = []
        
        # Inflow often precedes price appreciation
        if 'large_cap' in anomaly.description.lower():
            implications.extend(['SPY', 'QQQ', 'sector_leaders'])
        
        return implications
    
    def _get_outflow_implications(self, anomaly: MarketAnomaly) -> List[str]:
        """Get assets likely affected by liquidity outflow."""
        implications = []
        
        # Outflow often precedes price depreciation
        if 'institutional' in anomaly.description.lower():
            implications.extend(['sector_etfs', 'related_names'])
        
        return implications
