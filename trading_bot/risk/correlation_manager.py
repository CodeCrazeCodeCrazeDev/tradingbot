"""
Correlation Manager - Rolling correlation matrix and exposure management

Replaces static correlation groups with dynamic rolling correlation matrix
and CVaR-based exposure constraints.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class CorrelationConstraint:
    """Correlation-based exposure constraint"""
    symbol1: str
    symbol2: str
    correlation: float
    max_combined_exposure: float
    current_exposure1: float = 0.0
    current_exposure2: float = 0.0
    
    @property
    def is_violated(self) -> bool:
        """Check if constraint is violated"""
        combined = abs(self.current_exposure1) + abs(self.current_exposure2)
        return combined > self.max_combined_exposure


class CorrelationManager:
    """Manages rolling correlation matrix and exposure constraints"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Correlation settings
        self.correlation_window = self.config.get('correlation_window', 30)  # days
        self.correlation_threshold = self.config.get('correlation_threshold', 0.7)
        self.update_frequency = self.config.get('update_frequency', 3600)  # 1 hour
        
        # Price history for correlation calculation
        self.price_history: Dict[str, deque] = {}
        self.max_history_length = self.correlation_window * 24  # Hourly data
        
        # Correlation matrix
        self.correlation_matrix: Optional[pd.DataFrame] = None
        self.last_update = None
        
        # Exposure tracking
        self.exposures: Dict[str, float] = {}
        
        # Constraints
        self.constraints: List[CorrelationConstraint] = []
        
        logger.info("Correlation manager initialized")
    
    def update_price(self, symbol: str, price: float, timestamp: Optional[datetime] = None):
        """
        Update price for correlation calculation
        
        Args:
            symbol: Trading symbol
            price: Current price
            timestamp: Price timestamp
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.max_history_length)
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': timestamp or datetime.now()
        })
    
    def calculate_correlation_matrix(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Calculate rolling correlation matrix
        
        Args:
            symbols: List of symbols (uses all if None)
            
        Returns:
            Correlation matrix as DataFrame
        """
        symbols = symbols or list(self.price_history.keys())
        
        if len(symbols) < 2:
            logger.warning("Need at least 2 symbols for correlation")
            return pd.DataFrame()
        
        # Build price DataFrame
        price_data = {}
        min_length = float('inf')
        
        for symbol in symbols:
            if symbol in self.price_history and len(self.price_history[symbol]) > 0:
                prices = [p['price'] for p in self.price_history[symbol]]
                price_data[symbol] = prices
                min_length = min(min_length, len(prices))
        
        if min_length < 10:
            logger.warning(f"Insufficient data for correlation: {min_length} points")
            return pd.DataFrame()
        
        # Truncate to common length
        for symbol in price_data:
            price_data[symbol] = price_data[symbol][-int(min_length):]
        
        # Create DataFrame and calculate returns
        df = pd.DataFrame(price_data)
        returns = df.pct_change().dropna()
        
        # Calculate correlation matrix
        self.correlation_matrix = returns.corr()
        self.last_update = datetime.now()
        
        logger.info(f"Updated correlation matrix for {len(symbols)} symbols")
        return self.correlation_matrix
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two symbols"""
        if self.correlation_matrix is None:
            return None
        try:
        
            return self.correlation_matrix.loc[symbol1, symbol2]
        except KeyError:
            return None
    
    def get_highly_correlated_pairs(self, threshold: Optional[float] = None) -> List[Tuple[str, str, float]]:
        """
        Get pairs with correlation above threshold
        
        Args:
            threshold: Correlation threshold (uses config default if None)
            
        Returns:
            List of (symbol1, symbol2, correlation) tuples
        """
        threshold = threshold or self.correlation_threshold
        
        if self.correlation_matrix is None:
            return []
        
        pairs = []
        symbols = self.correlation_matrix.columns.tolist()
        
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self.correlation_matrix.loc[sym1, sym2]
                if abs(corr) >= threshold:
                    pairs.append((sym1, sym2, corr))
        
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def update_constraints(self, max_combined_exposure: float = 0.15):
        """
        Update correlation constraints based on current matrix
        
        Args:
            max_combined_exposure: Maximum combined exposure for correlated pairs
        """
        self.constraints.clear()
        
        highly_correlated = self.get_highly_correlated_pairs()
        
        for sym1, sym2, corr in highly_correlated:
            constraint = CorrelationConstraint(
                symbol1=sym1,
                symbol2=sym2,
                correlation=corr,
                max_combined_exposure=max_combined_exposure,
                current_exposure1=self.exposures.get(sym1, 0.0),
                current_exposure2=self.exposures.get(sym2, 0.0)
            )
            self.constraints.append(constraint)
        
        logger.info(f"Updated {len(self.constraints)} correlation constraints")
    
    def check_exposure(self, symbol: str, additional_exposure: float) -> Dict[str, Any]:
        """
        Check if additional exposure violates correlation constraints
        
        Args:
            symbol: Symbol to check
            additional_exposure: Additional exposure amount
            
        Returns:
            Check result with approval status
        """
        # Update exposure temporarily
        current_exposure = self.exposures.get(symbol, 0.0)
        new_exposure = current_exposure + additional_exposure
        
        # Check all constraints involving this symbol
        violations = []
        
        for constraint in self.constraints:
            if constraint.symbol1 == symbol:
                # Check with new exposure for symbol1
                combined = abs(new_exposure) + abs(constraint.current_exposure2)
                if combined > constraint.max_combined_exposure:
                    violations.append({
                        'correlated_with': constraint.symbol2,
                        'correlation': constraint.correlation,
                        'combined_exposure': combined,
                        'max_allowed': constraint.max_combined_exposure
                    })
            
            elif constraint.symbol2 == symbol:
                # Check with new exposure for symbol2
                combined = abs(constraint.current_exposure1) + abs(new_exposure)
                if combined > constraint.max_combined_exposure:
                    violations.append({
                        'correlated_with': constraint.symbol1,
                        'correlation': constraint.correlation,
                        'combined_exposure': combined,
                        'max_allowed': constraint.max_combined_exposure
                    })
        
        if violations:
            return {
                'approved': False,
                'reason': 'Correlation constraint violation',
                'violations': violations,
                'symbol': symbol,
                'requested_exposure': additional_exposure
            }
        else:
            return {
                'approved': True,
                'symbol': symbol,
                'requested_exposure': additional_exposure,
                'new_total_exposure': new_exposure
            }
    
    def update_exposure(self, symbol: str, exposure: float):
        """Update exposure for a symbol"""
        self.exposures[symbol] = exposure
        
        # Update constraints with new exposure
        for constraint in self.constraints:
            if constraint.symbol1 == symbol:
                constraint.current_exposure1 = exposure
            elif constraint.symbol2 == symbol:
                constraint.current_exposure2 = exposure
    
    def get_portfolio_correlation_risk(self) -> Dict[str, Any]:
        """Calculate portfolio-level correlation risk"""
        if self.correlation_matrix is None or not self.exposures:
            return {'total_risk': 0, 'diversification_ratio': 1.0}
        
        # Get symbols with exposure
        symbols_with_exposure = [s for s in self.exposures if self.exposures[s] != 0]
        
        if len(symbols_with_exposure) < 2:
            return {'total_risk': sum(abs(e) for e in self.exposures.values()), 'diversification_ratio': 1.0}
        
        # Calculate portfolio variance considering correlations
        exposures_array = np.array([self.exposures.get(s, 0) for s in symbols_with_exposure])
        
        try:
            # Extract correlation submatrix
            corr_submatrix = self.correlation_matrix.loc[symbols_with_exposure, symbols_with_exposure].values
            
            # Portfolio variance = w^T * Corr * w (simplified, assuming equal volatility)
            portfolio_variance = exposures_array.T @ corr_submatrix @ exposures_array
            portfolio_risk = np.sqrt(max(portfolio_variance, 0))
            
            # Diversification ratio = sum of individual risks / portfolio risk
            individual_risk_sum = np.sum(np.abs(exposures_array))
            diversification_ratio = individual_risk_sum / max(portfolio_risk, 0.001)
            
            return {
                'total_risk': float(portfolio_risk),
                'individual_risk_sum': float(individual_risk_sum),
                'diversification_ratio': float(diversification_ratio),
                'num_positions': len(symbols_with_exposure)
            }
        except Exception as e:
            logger.error(f"Error calculating portfolio correlation risk: {e}")
            return {'total_risk': 0, 'diversification_ratio': 1.0}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get correlation manager statistics"""
        return {
            'correlation_window': self.correlation_window,
            'correlation_threshold': self.correlation_threshold,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'num_symbols': len(self.price_history),
            'num_constraints': len(self.constraints),
            'highly_correlated_pairs': len(self.get_highly_correlated_pairs()),
            'active_exposures': len([e for e in self.exposures.values() if e != 0]),
            'portfolio_risk': self.get_portfolio_correlation_risk()
        }
