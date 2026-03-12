"""
Correlation Hedge Engine
Auto-hedge correlated exposure with basket/futures hedging and dynamic rebalancing
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class HedgeType(Enum):
    """Types of hedges"""
    INDEX_FUTURE = "index_future"
    SECTOR_ETF = "sector_etf"
    INVERSE_ETF = "inverse_etf"
    OPTIONS_PUT = "options_put"
    OPTIONS_COLLAR = "options_collar"
    PAIR_TRADE = "pair_trade"
    BASKET = "basket"
    CURRENCY = "currency"
    VOLATILITY = "volatility"


class HedgeStrategy(Enum):
    """Hedging strategies"""
    DELTA_NEUTRAL = "delta_neutral"
    BETA_NEUTRAL = "beta_neutral"
    SECTOR_NEUTRAL = "sector_neutral"
    TAIL_RISK = "tail_risk"
    VOLATILITY_TARGET = "volatility_target"
    CORRELATION_BASED = "correlation_based"


@dataclass
class HedgePosition:
    """Current hedge position"""
    hedge_id: str
    hedge_type: HedgeType
    instrument: str
    quantity: float
    entry_price: float
    current_price: float
    notional_value: float
    hedge_ratio: float
    target_exposure: float
    actual_exposure: float
    effectiveness: float  # R-squared of hedge
    created_at: datetime
    last_rebalanced: datetime
    cost: float = 0  # Total cost of hedge
    
    @property
    def pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def drift(self) -> float:
        """Hedge drift from target"""
        return abs(self.actual_exposure - self.target_exposure) / self.target_exposure if self.target_exposure > 0 else 0


@dataclass
class HedgeRecommendation:
    """Hedge recommendation"""
    hedge_type: HedgeType
    instrument: str
    action: str  # BUY, SELL, ADJUST
    quantity: float
    estimated_cost: float
    hedge_ratio: float
    expected_effectiveness: float
    reason: str
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hedge_type': self.hedge_type.value,
            'instrument': self.instrument,
            'action': self.action,
            'quantity': self.quantity,
            'estimated_cost': self.estimated_cost,
            'hedge_ratio': self.hedge_ratio,
            'expected_effectiveness': self.expected_effectiveness,
            'reason': self.reason,
            'urgency': self.urgency
        }


@dataclass
class PortfolioExposure:
    """Portfolio exposure analysis"""
    total_long: float
    total_short: float
    net_exposure: float
    gross_exposure: float
    beta_exposure: float
    sector_exposures: Dict[str, float]
    factor_exposures: Dict[str, float]
    correlation_clusters: List[List[str]]


class CorrelationHedgeEngine:
    """
    Correlation-based hedging engine with automatic hedge management
    """
    
    # Common hedge instruments
    HEDGE_INSTRUMENTS = {
        'SPY': {'type': HedgeType.INDEX_FUTURE, 'beta': 1.0, 'sector': 'broad_market'},
        'QQQ': {'type': HedgeType.SECTOR_ETF, 'beta': 1.2, 'sector': 'technology'},
        'IWM': {'type': HedgeType.SECTOR_ETF, 'beta': 1.3, 'sector': 'small_cap'},
        'XLF': {'type': HedgeType.SECTOR_ETF, 'beta': 1.1, 'sector': 'financials'},
        'XLE': {'type': HedgeType.SECTOR_ETF, 'beta': 1.4, 'sector': 'energy'},
        'XLK': {'type': HedgeType.SECTOR_ETF, 'beta': 1.2, 'sector': 'technology'},
        'XLV': {'type': HedgeType.SECTOR_ETF, 'beta': 0.8, 'sector': 'healthcare'},
        'XLU': {'type': HedgeType.SECTOR_ETF, 'beta': 0.5, 'sector': 'utilities'},
        'SH': {'type': HedgeType.INVERSE_ETF, 'beta': -1.0, 'sector': 'broad_market'},
        'PSQ': {'type': HedgeType.INVERSE_ETF, 'beta': -1.0, 'sector': 'technology'},
        'VXX': {'type': HedgeType.VOLATILITY, 'beta': -3.0, 'sector': 'volatility'},
        'UVXY': {'type': HedgeType.VOLATILITY, 'beta': -4.5, 'sector': 'volatility'},
        'ES': {'type': HedgeType.INDEX_FUTURE, 'beta': 1.0, 'sector': 'broad_market'},
        'NQ': {'type': HedgeType.INDEX_FUTURE, 'beta': 1.2, 'sector': 'technology'},
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Hedging parameters
        self.target_beta = self.config.get('target_beta', 0.0)  # Beta neutral by default
        self.max_hedge_cost_pct = self.config.get('max_hedge_cost_pct', 0.02)  # 2% max cost
        self.rebalance_threshold = self.config.get('rebalance_threshold', 0.10)  # 10% drift
        self.min_hedge_effectiveness = self.config.get('min_hedge_effectiveness', 0.70)
        
        # Active hedges
        self.active_hedges: Dict[str, HedgePosition] = {}
        self.hedge_history: List[HedgePosition] = []
        
        # Correlation matrix (would be updated with real data)
        self.correlation_matrix: Optional[np.ndarray] = None
        self.symbols: List[str] = []
        
        # Statistics
        self.stats = {
            'total_hedges_placed': 0,
            'total_hedge_cost': 0,
            'total_hedge_pnl': 0,
            'avg_effectiveness': 0,
            'rebalances': 0
        }
        
        logger.info("Correlation hedge engine initialized")
        
    def update_correlations(self, returns: np.ndarray, symbols: List[str]):
        """
        Update correlation matrix from returns data
        
        Args:
            returns: NxM array of returns (N periods, M symbols)
            symbols: List of symbol names
        """
        self.correlation_matrix = np.corrcoef(returns.T)
        self.symbols = symbols
        logger.info(f"Updated correlations for {len(symbols)} symbols")
        
    def analyze_exposure(
        self,
        positions: List[Dict[str, Any]],
        market_data: Optional[Dict[str, float]] = None
    ) -> PortfolioExposure:
        """
        Analyze portfolio exposure
        
        Args:
            positions: List of position dicts with symbol, quantity, price, beta, sector
            market_data: Current prices
        """
        total_long = 0
        total_short = 0
        beta_exposure = 0
        sector_exposures: Dict[str, float] = {}
        
        for pos in positions:
            value = pos['quantity'] * pos.get('price', 0)
            beta = pos.get('beta', 1.0)
            sector = pos.get('sector', 'unknown')
            
            if value > 0:
                total_long += value
            else:
                total_short += abs(value)
                
            beta_exposure += value * beta
            sector_exposures[sector] = sector_exposures.get(sector, 0) + value
            
        # Find correlation clusters
        clusters = self._find_correlation_clusters(positions)
        
        return PortfolioExposure(
            total_long=total_long,
            total_short=total_short,
            net_exposure=total_long - total_short,
            gross_exposure=total_long + total_short,
            beta_exposure=beta_exposure,
            sector_exposures=sector_exposures,
            factor_exposures={},  # Would need factor model
            correlation_clusters=clusters
        )
    
    def _find_correlation_clusters(
        self,
        positions: List[Dict[str, Any]],
        threshold: float = 0.7
    ) -> List[List[str]]:
        """Find highly correlated position clusters"""
        if self.correlation_matrix is None or len(positions) < 2:
            return []
            
        clusters = []
        symbols = [p['symbol'] for p in positions]
        visited = set()
        
        for i, sym1 in enumerate(symbols):
            if sym1 in visited:
                continue
                
            cluster = [sym1]
            visited.add(sym1)
            
            for j, sym2 in enumerate(symbols[i+1:], i+1):
                if sym2 in visited:
                    continue
                try:
                    
                # Get correlation
                    idx1 = self.symbols.index(sym1)
                    idx2 = self.symbols.index(sym2)
                    corr = self.correlation_matrix[idx1, idx2]
                    
                    if abs(corr) >= threshold:
                        cluster.append(sym2)
                        visited.add(sym2)
                except (ValueError, IndexError):
                    pass
                    
            if len(cluster) > 1:
                clusters.append(cluster)
                
        return clusters
    
    def calculate_hedge_ratio(
        self,
        portfolio_beta: float,
        hedge_instrument: str,
        target_beta: Optional[float] = None
    ) -> float:
        """
        Calculate optimal hedge ratio
        
        Args:
            portfolio_beta: Current portfolio beta
            hedge_instrument: Instrument to use for hedging
            target_beta: Target beta (default: self.target_beta)
        """
        target = target_beta if target_beta is not None else self.target_beta
        hedge_info = self.HEDGE_INSTRUMENTS.get(hedge_instrument, {})
        hedge_beta = hedge_info.get('beta', 1.0)
        
        if hedge_beta == 0:
            return 0
            
        # Hedge ratio = (current_beta - target_beta) / hedge_beta
        hedge_ratio = (portfolio_beta - target) / abs(hedge_beta)
        
        return hedge_ratio
    
    def get_hedge_recommendations(
        self,
        positions: List[Dict[str, Any]],
        strategy: HedgeStrategy = HedgeStrategy.BETA_NEUTRAL,
        portfolio_value: float = 0
    ) -> List[HedgeRecommendation]:
        """
        Get hedge recommendations based on strategy
        """
        exposure = self.analyze_exposure(positions)
        recommendations = []
        
        if portfolio_value == 0:
            portfolio_value = exposure.gross_exposure
            
        if strategy == HedgeStrategy.BETA_NEUTRAL:
            recommendations.extend(
                self._get_beta_neutral_hedges(exposure, portfolio_value)
            )
        elif strategy == HedgeStrategy.SECTOR_NEUTRAL:
            recommendations.extend(
                self._get_sector_neutral_hedges(exposure, portfolio_value)
            )
        elif strategy == HedgeStrategy.TAIL_RISK:
            recommendations.extend(
                self._get_tail_risk_hedges(exposure, portfolio_value)
            )
        elif strategy == HedgeStrategy.CORRELATION_BASED:
            recommendations.extend(
                self._get_correlation_hedges(exposure, positions, portfolio_value)
            )
            
        return recommendations
    
    def _get_beta_neutral_hedges(
        self,
        exposure: PortfolioExposure,
        portfolio_value: float
    ) -> List[HedgeRecommendation]:
        """Get hedges to achieve beta neutrality"""
        recommendations = []
        
        current_beta = exposure.beta_exposure / portfolio_value if portfolio_value > 0 else 0
        
        if abs(current_beta - self.target_beta) < 0.1:
            return recommendations
            
        # Use SPY or ES futures for broad market hedge
        hedge_ratio = self.calculate_hedge_ratio(current_beta, 'SPY')
        hedge_value = abs(hedge_ratio * portfolio_value)
        
        if hedge_value > portfolio_value * 0.01:  # Min 1% hedge
            recommendations.append(HedgeRecommendation(
                hedge_type=HedgeType.INDEX_FUTURE,
                instrument='SPY' if hedge_value < 100000 else 'ES',
                action='SELL' if hedge_ratio > 0 else 'BUY',
                quantity=hedge_value / 450,  # Approximate SPY price
                estimated_cost=hedge_value * 0.001,  # ~10bps
                hedge_ratio=hedge_ratio,
                expected_effectiveness=0.85,
                reason=f"Reduce beta from {current_beta:.2f} to {self.target_beta:.2f}",
                urgency='HIGH' if abs(current_beta) > 1.5 else 'MEDIUM'
            ))
            
        return recommendations
    
    def _get_sector_neutral_hedges(
        self,
        exposure: PortfolioExposure,
        portfolio_value: float
    ) -> List[HedgeRecommendation]:
        """Get hedges to neutralize sector exposure"""
        recommendations = []
        
        sector_etfs = {
            'technology': 'XLK',
            'financials': 'XLF',
            'healthcare': 'XLV',
            'energy': 'XLE',
            'utilities': 'XLU',
        }
        
        for sector, exp in exposure.sector_exposures.items():
            sector_pct = exp / portfolio_value if portfolio_value > 0 else 0
            
            # If sector > 20% of portfolio, recommend hedge
            if abs(sector_pct) > 0.20:
                etf = sector_etfs.get(sector.lower())
                if etf:
                    hedge_value = abs(exp) * 0.5  # Hedge 50% of excess
                    recommendations.append(HedgeRecommendation(
                        hedge_type=HedgeType.SECTOR_ETF,
                        instrument=etf,
                        action='SELL' if exp > 0 else 'BUY',
                        quantity=hedge_value / 100,  # Approximate ETF price
                        estimated_cost=hedge_value * 0.001,
                        hedge_ratio=0.5,
                        expected_effectiveness=0.75,
                        reason=f"Reduce {sector} exposure from {sector_pct*100:.1f}%",
                        urgency='MEDIUM'
                    ))
                    
        return recommendations
    
    def _get_tail_risk_hedges(
        self,
        exposure: PortfolioExposure,
        portfolio_value: float
    ) -> List[HedgeRecommendation]:
        """Get tail risk hedges (puts, VIX)"""
        recommendations = []
        
        # Recommend put protection if long exposure is high
        if exposure.net_exposure > portfolio_value * 0.5:
            put_cost = portfolio_value * 0.02  # ~2% for put protection
            
            recommendations.append(HedgeRecommendation(
                hedge_type=HedgeType.OPTIONS_PUT,
                instrument='SPY_PUT_OTM',
                action='BUY',
                quantity=exposure.net_exposure / 45000,  # SPY contract size
                estimated_cost=put_cost,
                hedge_ratio=0.3,  # Delta of OTM put
                expected_effectiveness=0.90,
                reason="Tail risk protection for long exposure",
                urgency='MEDIUM'
            ))
            
        # VIX hedge for volatility spike protection
        if exposure.gross_exposure > portfolio_value * 0.8:
            vix_allocation = portfolio_value * 0.02  # 2% VIX allocation
            
            recommendations.append(HedgeRecommendation(
                hedge_type=HedgeType.VOLATILITY,
                instrument='VXX',
                action='BUY',
                quantity=vix_allocation / 20,  # Approximate VXX price
                estimated_cost=vix_allocation * 0.05,  # VIX products have high carry cost
                hedge_ratio=0.1,
                expected_effectiveness=0.60,
                reason="Volatility spike protection",
                urgency='LOW'
            ))
            
        return recommendations
    
    def _get_correlation_hedges(
        self,
        exposure: PortfolioExposure,
        positions: List[Dict[str, Any]],
        portfolio_value: float
    ) -> List[HedgeRecommendation]:
        """Get hedges based on correlation analysis"""
        recommendations = []
        
        # Hedge correlation clusters
        for cluster in exposure.correlation_clusters:
            if len(cluster) >= 3:
                cluster_value = sum(
                    p['quantity'] * p.get('price', 0)
                    for p in positions if p['symbol'] in cluster
                )
                
                if cluster_value > portfolio_value * 0.3:
                    recommendations.append(HedgeRecommendation(
                        hedge_type=HedgeType.BASKET,
                        instrument=f"BASKET_{cluster[0]}",
                        action='SELL',
                        quantity=cluster_value * 0.3 / 100,
                        estimated_cost=cluster_value * 0.002,
                        hedge_ratio=0.3,
                        expected_effectiveness=0.80,
                        reason=f"Hedge correlated cluster: {', '.join(cluster[:3])}...",
                        urgency='MEDIUM'
                    ))
                    
        return recommendations
    
    async def execute_hedge(
        self,
        recommendation: HedgeRecommendation,
        execute_callback: Optional[callable] = None
    ) -> Optional[HedgePosition]:
        """
        Execute a hedge recommendation
        """
        hedge_id = f"HEDGE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{recommendation.instrument}"
        
        # Would execute via broker
        if execute_callback:
            try:
                result = await execute_callback(recommendation)
                fill_price = result.get('fill_price', 0)
            except Exception as e:
                logger.error(f"Failed to execute hedge: {e}")
                return None
        else:
            fill_price = 100  # Mock price
            
        hedge = HedgePosition(
            hedge_id=hedge_id,
            hedge_type=recommendation.hedge_type,
            instrument=recommendation.instrument,
            quantity=recommendation.quantity if recommendation.action == 'BUY' else -recommendation.quantity,
            entry_price=fill_price,
            current_price=fill_price,
            notional_value=abs(recommendation.quantity * fill_price),
            hedge_ratio=recommendation.hedge_ratio,
            target_exposure=recommendation.quantity * fill_price * recommendation.hedge_ratio,
            actual_exposure=recommendation.quantity * fill_price * recommendation.hedge_ratio,
            effectiveness=recommendation.expected_effectiveness,
            created_at=datetime.now(),
            last_rebalanced=datetime.now(),
            cost=recommendation.estimated_cost
        )
        
        self.active_hedges[hedge_id] = hedge
        self.stats['total_hedges_placed'] += 1
        self.stats['total_hedge_cost'] += recommendation.estimated_cost
        
        logger.info(f"Executed hedge {hedge_id}: {recommendation.action} {recommendation.quantity} {recommendation.instrument}")
        
        return hedge
    
    def check_rebalance_needed(self) -> List[HedgePosition]:
        """Check which hedges need rebalancing"""
        needs_rebalance = []
        
        for hedge in self.active_hedges.values():
            if hedge.drift > self.rebalance_threshold:
                needs_rebalance.append(hedge)
                
        return needs_rebalance
    
    async def rebalance_hedges(
        self,
        execute_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """Rebalance hedges that have drifted"""
        rebalanced = []
        
        for hedge in self.check_rebalance_needed():
            adjustment = hedge.target_exposure - hedge.actual_exposure
            
            if abs(adjustment) > hedge.notional_value * 0.05:  # Min 5% adjustment
                # Would execute adjustment
                hedge.actual_exposure = hedge.target_exposure
                hedge.last_rebalanced = datetime.now()
                self.stats['rebalances'] += 1
                
                rebalanced.append({
                    'hedge_id': hedge.hedge_id,
                    'instrument': hedge.instrument,
                    'adjustment': adjustment,
                    'new_exposure': hedge.actual_exposure
                })
                
                logger.info(f"Rebalanced hedge {hedge.hedge_id}: adjustment {adjustment:,.0f}")
                
        return rebalanced
    
    def update_hedge_prices(self, prices: Dict[str, float]):
        """Update current prices for hedges"""
        for hedge in self.active_hedges.values():
            if hedge.instrument in prices:
                hedge.current_price = prices[hedge.instrument]
                hedge.actual_exposure = hedge.quantity * hedge.current_price * hedge.hedge_ratio
                
    def get_hedge_pnl(self) -> Dict[str, float]:
        """Get P&L for all active hedges"""
        pnls = {}
        total_pnl = 0
        
        for hedge_id, hedge in self.active_hedges.items():
            pnl = hedge.pnl
            pnls[hedge_id] = pnl
            total_pnl += pnl
            
        self.stats['total_hedge_pnl'] = total_pnl
        return pnls
    
    def close_hedge(self, hedge_id: str) -> Optional[HedgePosition]:
        """Close a hedge position"""
        if hedge_id in self.active_hedges:
            hedge = self.active_hedges.pop(hedge_id)
            self.hedge_history.append(hedge)
            logger.info(f"Closed hedge {hedge_id}, P&L: {hedge.pnl:,.2f}")
            return hedge
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hedging statistics"""
        active_pnl = sum(h.pnl for h in self.active_hedges.values())
        
        return {
            **self.stats,
            'active_hedges': len(self.active_hedges),
            'active_notional': sum(h.notional_value for h in self.active_hedges.values()),
            'active_pnl': active_pnl,
            'avg_effectiveness': np.mean([h.effectiveness for h in self.active_hedges.values()]) if self.active_hedges else 0
        }
