"""
Fundamental analysis for trading decisions
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
import numpy

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Analyzes fundamental data for trading decisions.
    """
    
    def __init__(self, config: Dict = None):
        try:
            self.config = config or {}
            self.fundamentals_cache = {}
        
            logger.info("✅ Fundamental Analyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, symbol: str, data: Dict = None) -> Dict:
        """
        Analyze fundamental data for a symbol.
        
        Args:
            symbol: Trading symbol
            data: Fundamental data dictionary
        
        Returns:
            Analysis results
        """
        try:
            if data is None:
                data = self._fetch_fundamentals(symbol)
        
            if not data:
                return {
                    'symbol': symbol,
                    'score': 0.5,
                    'signal': 'NEUTRAL',
                    'factors': {}
                }
        
            # Analyze various fundamental factors
            factors = {}
        
            # P/E Ratio
            if 'pe_ratio' in data:
                pe_score = self._analyze_pe_ratio(data['pe_ratio'])
                factors['pe_ratio'] = pe_score
        
            # Revenue Growth
            if 'revenue_growth' in data:
                revenue_score = self._analyze_revenue_growth(data['revenue_growth'])
                factors['revenue_growth'] = revenue_score
        
            # Profit Margin
            if 'profit_margin' in data:
                margin_score = self._analyze_profit_margin(data['profit_margin'])
                factors['profit_margin'] = margin_score
        
            # Debt to Equity
            if 'debt_to_equity' in data:
                debt_score = self._analyze_debt_to_equity(data['debt_to_equity'])
                factors['debt_to_equity'] = debt_score
        
            # Calculate overall score
            if factors:
                overall_score = np.mean(list(factors.values()))
            else:
                overall_score = 0.5
        
            # Determine signal
            if overall_score > 0.6:
                signal = 'BUY'
            elif overall_score < 0.4:
                signal = 'SELL'
            else:
                signal = 'NEUTRAL'
        
            return {
                'symbol': symbol,
                'score': overall_score,
                'signal': signal,
                'factors': factors,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _fetch_fundamentals(self, symbol: str) -> Dict:
        """Fetch fundamental data (placeholder)."""
        # In production, fetch from data provider
        try:
            if symbol in self.fundamentals_cache:
                return self.fundamentals_cache[symbol]
        
            return {}
        except Exception as e:
            logger.error(f"Error in _fetch_fundamentals: {e}")
            raise
    
    def _analyze_pe_ratio(self, pe_ratio: float) -> float:
        """
        Analyze P/E ratio.
        
        Returns score 0-1 (higher is better)
        """
        try:
            if pe_ratio <= 0:
                return 0.3
            elif pe_ratio < 15:
                return 0.8
            elif pe_ratio < 25:
                return 0.6
            elif pe_ratio < 35:
                return 0.4
            else:
                return 0.2
        except Exception as e:
            logger.error(f"Error in _analyze_pe_ratio: {e}")
            raise
    
    def _analyze_revenue_growth(self, growth: float) -> float:
        """
        Analyze revenue growth rate.
        
        Returns score 0-1 (higher is better)
        """
        try:
            if growth > 0.20:  # 20%+
                return 0.9
            elif growth > 0.10:  # 10-20%
                return 0.7
            elif growth > 0:  # Positive
                return 0.6
            elif growth > -0.05:  # Small decline
                return 0.4
            else:  # Significant decline
                return 0.2
        except Exception as e:
            logger.error(f"Error in _analyze_revenue_growth: {e}")
            raise
    
    def _analyze_profit_margin(self, margin: float) -> float:
        """
        Analyze profit margin.
        
        Returns score 0-1 (higher is better)
        """
        try:
            if margin > 0.20:  # 20%+
                return 0.9
            elif margin > 0.10:  # 10-20%
                return 0.7
            elif margin > 0.05:  # 5-10%
                return 0.6
            elif margin > 0:  # Positive
                return 0.5
            else:  # Negative
                return 0.2
        except Exception as e:
            logger.error(f"Error in _analyze_profit_margin: {e}")
            raise
    
    def _analyze_debt_to_equity(self, ratio: float) -> float:
        """
        Analyze debt to equity ratio.
        
        Returns score 0-1 (lower debt is better)
        """
        try:
            if ratio < 0.3:
                return 0.9
            elif ratio < 0.5:
                return 0.8
            elif ratio < 1.0:
                return 0.6
            elif ratio < 2.0:
                return 0.4
            else:
                return 0.2
        except Exception as e:
            logger.error(f"Error in _analyze_debt_to_equity: {e}")
            raise
    
    def update_fundamentals(self, symbol: str, data: Dict):
        """Update cached fundamental data."""
        try:
            self.fundamentals_cache[symbol] = data
            logger.info(f"✅ Updated fundamentals for {symbol}")
        except Exception as e:
            logger.error(f"Error in update_fundamentals: {e}")
            raise
    
    def get_cached_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get cached fundamental data."""
        return self.fundamentals_cache.get(symbol)
