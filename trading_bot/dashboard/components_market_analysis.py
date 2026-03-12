"""
Market Analysis Dashboard Components
Reusable components for market analysis visualization
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChartComponent:
    """Chart component configuration"""
    chart_type: str = "line"
    title: str = "Market Chart"
    height: int = 400
    width: int = 800


@dataclass
class IndicatorComponent:
    """Indicator display component"""
    indicator_name: str
    value: float
    color: str = "green"
    format: str = ".2f"


class MarketAnalysisComponents:
    """
    Market Analysis Dashboard Components
    
    Provides reusable UI components for market analysis
    """
    
    def __init__(self):
        try:
            self.components = {}
            logger.info("Market analysis components initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def create_price_chart(self, data: List[Dict], config: Optional[ChartComponent] = None) -> Dict:
        """Create price chart component"""
        try:
            config = config or ChartComponent()
            return {
                'type': 'chart',
                'config': config,
                'data': data
            }
        except Exception as e:
            logger.error(f"Error in create_price_chart: {e}")
            raise
    
    def create_indicator_panel(self, indicators: List[IndicatorComponent]) -> Dict:
        """Create indicator panel"""
        return {
            'type': 'indicator_panel',
            'indicators': indicators
        }
    
    def create_order_book_view(self, bids: List, asks: List) -> Dict:
        """Create order book visualization"""
        return {
            'type': 'order_book',
            'bids': bids,
            'asks': asks
        }
    
    def create_trade_history(self, trades: List[Dict]) -> Dict:
        """Create trade history component"""
        return {
            'type': 'trade_history',
            'trades': trades
        }


def create_components() -> MarketAnalysisComponents:
    """Factory function"""
    return MarketAnalysisComponents()


__all__ = ['MarketAnalysisComponents', 'ChartComponent', 'IndicatorComponent', 'create_components']
