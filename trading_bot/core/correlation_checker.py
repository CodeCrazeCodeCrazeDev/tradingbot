"""
Correlation Checker for Pre-Trade Validation
Prevents opening highly correlated positions that increase portfolio risk.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """Result of correlation check."""
    symbol: str
    correlated_symbols: List[str]
    max_correlation: float
    total_correlated_exposure: float
    allowed: bool
    reason: str


@dataclass
class CorrelationConfig:
    """Configuration for correlation checking."""
    max_correlation: float = 0.7  # Maximum allowed correlation
    max_correlated_exposure_pct: float = 0.30  # 30% max correlated exposure
    lookback_periods: int = 100  # Periods for correlation calculation
    update_interval_seconds: int = 300  # 5 minutes
    min_data_points: int = 20  # Minimum data points for valid correlation


class CorrelationChecker:
    """
    Checks correlation between positions before allowing new trades.
    
    Features:
    - Real-time correlation matrix
    - Correlated exposure tracking
    - Pre-trade validation
    - Dynamic correlation updates
    """
    
    def __init__(self, config: Optional[CorrelationConfig] = None):
        self.config = config or CorrelationConfig()
        
        # Price history for correlation calculation
        self._price_history: Dict[str, deque] = {}
        
        # Cached correlation matrix
        self._correlation_matrix: Dict[Tuple[str, str], float] = {}
        self._last_update: Optional[datetime] = None
        
        # Known correlation pairs (static fallback)
        self._static_correlations = {
            ('EURUSD', 'GBPUSD'): 0.85,
            ('EURUSD', 'USDCHF'): -0.90,
            ('EURUSD', 'USDJPY'): -0.30,
            ('EURUSD', 'AUDUSD'): 0.70,
            ('GBPUSD', 'USDCHF'): -0.75,
            ('GBPUSD', 'USDJPY'): -0.25,
            ('GBPUSD', 'AUDUSD'): 0.65,
            ('USDCHF', 'USDJPY'): 0.60,
            ('USDCHF', 'AUDUSD'): -0.65,
            ('USDJPY', 'AUDUSD'): -0.20,
            ('BTCUSDT', 'ETHUSDT'): 0.85,
            ('BTCUSDT', 'BNBUSDT'): 0.75,
            ('ETHUSDT', 'BNBUSDT'): 0.80,
        }
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("CorrelationChecker initialized")
    
    async def check_correlation(
        self,
        symbol: str,
        proposed_size: float,
        proposed_direction: str,
        current_positions: List[Dict],
        account_equity: float
    ) -> CorrelationResult:
        """
        Check if a new position would create excessive correlated exposure.
        
        Args:
            symbol: Symbol to trade
            proposed_size: Proposed position size
            proposed_direction: 'buy' or 'sell'
            current_positions: List of current open positions
            account_equity: Current account equity
            
        Returns:
            CorrelationResult with decision
        """
        async with self._lock:
            correlated_symbols = []
            total_correlated_exposure = 0.0
            max_correlation = 0.0
            
            # Calculate proposed exposure
            proposed_exposure = proposed_size  # Simplified - should use notional value
            
            for position in current_positions:
                pos_symbol = position.get('symbol', '')
                pos_size = position.get('size', 0)
                pos_direction = position.get('side', position.get('direction', 'buy'))
                
                if pos_symbol == symbol:
                    continue  # Skip same symbol
                
                # Get correlation
                correlation = self._get_correlation(symbol, pos_symbol)
                abs_correlation = abs(correlation)
                
                if abs_correlation > self.config.max_correlation:
                    correlated_symbols.append(pos_symbol)
                    
                    # Calculate effective correlation based on direction
                    # Same direction with positive correlation = high risk
                    # Opposite direction with negative correlation = high risk
                    same_direction = (proposed_direction == pos_direction)
                    
                    if (same_direction and correlation > 0) or (not same_direction and correlation < 0):
                        # Positions are effectively correlated
                        total_correlated_exposure += pos_size * abs_correlation
                    
                    max_correlation = max(max_correlation, abs_correlation)
            
            # Add proposed position to correlated exposure
            if correlated_symbols:
                total_correlated_exposure += proposed_exposure
            
            # Calculate correlated exposure as percentage of equity
            correlated_exposure_pct = total_correlated_exposure / account_equity if account_equity > 0 else 0
            
            # Determine if allowed
            if correlated_exposure_pct > self.config.max_correlated_exposure_pct:
                allowed = False
                reason = (f"Correlated exposure {correlated_exposure_pct:.1%} exceeds limit "
                         f"{self.config.max_correlated_exposure_pct:.1%}")
            elif max_correlation > self.config.max_correlation and len(correlated_symbols) > 2:
                allowed = False
                reason = f"Too many highly correlated positions ({len(correlated_symbols)})"
            else:
                allowed = True
                reason = "Correlation check passed"
            
            result = CorrelationResult(
                symbol=symbol,
                correlated_symbols=correlated_symbols,
                max_correlation=max_correlation,
                total_correlated_exposure=total_correlated_exposure,
                allowed=allowed,
                reason=reason
            )
            
            if not allowed:
                logger.warning(f"Correlation check failed for {symbol}: {reason}")
            
            return result
    
    def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols."""
        # Check cached dynamic correlation
        key = tuple(sorted([symbol1, symbol2]))
        if key in self._correlation_matrix:
            return self._correlation_matrix[key]
        
        # Check static correlations
        if (symbol1, symbol2) in self._static_correlations:
            return self._static_correlations[(symbol1, symbol2)]
        if (symbol2, symbol1) in self._static_correlations:
            return self._static_correlations[(symbol2, symbol1)]
        
        # Calculate from price history if available
        if symbol1 in self._price_history and symbol2 in self._price_history:
            correlation = self._calculate_correlation(symbol1, symbol2)
            if correlation is not None:
                self._correlation_matrix[key] = correlation
                return correlation
        
        # Default to low correlation if unknown
        return 0.0
    
    def _calculate_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Calculate correlation from price history."""
        prices1 = list(self._price_history.get(symbol1, []))
        prices2 = list(self._price_history.get(symbol2, []))
        
        if len(prices1) < self.config.min_data_points or len(prices2) < self.config.min_data_points:
            return None
        
        # Align lengths
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        try:
            # Calculate returns
            returns1 = np.diff(prices1) / prices1[:-1]
            returns2 = np.diff(prices2) / prices2[:-1]
            
            # Calculate correlation
            if len(returns1) > 1 and len(returns2) > 1:
                correlation = np.corrcoef(returns1, returns2)[0, 1]
                if np.isnan(correlation):
                    return None
                return float(correlation)
        except Exception as e:
            logger.debug(f"Error calculating correlation: {e}")
        
        return None
    
    def update_price(self, symbol: str, price: float):
        """Update price history for a symbol."""
        if symbol not in self._price_history:
            self._price_history[symbol] = deque(maxlen=self.config.lookback_periods)
        
        self._price_history[symbol].append(price)
    
    async def update_correlation_matrix(self):
        """Update the full correlation matrix."""
        async with self._lock:
            symbols = list(self._price_history.keys())
            
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    correlation = self._calculate_correlation(sym1, sym2)
                    if correlation is not None:
                        key = tuple(sorted([sym1, sym2]))
                        self._correlation_matrix[key] = correlation
            
            self._last_update = datetime.now()
            logger.debug(f"Updated correlation matrix for {len(symbols)} symbols")
    
    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """Get the full correlation matrix as nested dict."""
        symbols = list(self._price_history.keys())
        matrix = {s: {} for s in symbols}
        
        for sym1 in symbols:
            for sym2 in symbols:
                if sym1 == sym2:
                    matrix[sym1][sym2] = 1.0
                else:
                    matrix[sym1][sym2] = self._get_correlation(sym1, sym2)
        
        return matrix
    
    def get_highly_correlated_pairs(self, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """Get all pairs with correlation above threshold."""
        pairs = []
        
        for (sym1, sym2), corr in self._correlation_matrix.items():
            if abs(corr) >= threshold:
                pairs.append((sym1, sym2, corr))
        
        # Add static correlations
        for (sym1, sym2), corr in self._static_correlations.items():
            if abs(corr) >= threshold and (sym1, sym2) not in [(p[0], p[1]) for p in pairs]:
                pairs.append((sym1, sym2, corr))
        
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def get_status(self) -> Dict:
        """Get correlation checker status."""
        return {
            'symbols_tracked': len(self._price_history),
            'correlation_pairs': len(self._correlation_matrix),
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'max_correlation_threshold': self.config.max_correlation,
            'max_correlated_exposure_pct': self.config.max_correlated_exposure_pct,
            'highly_correlated_pairs': len(self.get_highly_correlated_pairs())
        }


# Singleton instance
_correlation_checker: Optional[CorrelationChecker] = None


def get_correlation_checker(config: Optional[CorrelationConfig] = None) -> CorrelationChecker:
    """Get or create the correlation checker singleton."""
    global _correlation_checker
    if _correlation_checker is None:
        _correlation_checker = CorrelationChecker(config)
    return _correlation_checker


__all__ = [
    'CorrelationChecker',
    'CorrelationConfig',
    'CorrelationResult',
    'get_correlation_checker'
]
