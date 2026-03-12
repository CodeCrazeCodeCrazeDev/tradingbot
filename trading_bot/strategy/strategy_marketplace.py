"""
Strategy Marketplace - Internal Market of Competing Strategies

This module implements an internal marketplace where AI agents compete to provide
the best trading strategies. Only the best-performing strategies get capital allocation.

Features:
- Strategy registration and ranking
- Performance-based capital allocation
- Real-time strategy auctions
- Dynamic resource allocation
- Integration with Offline RL

Author: Trading Bot Team
Date: 2025-10-23
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import heapq

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


class StrategyStatus(Enum):
    """Strategy status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    strategy_id: str
    returns: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    trades_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyListing:
    """Strategy marketplace listing"""
    strategy_id: str
    agent_id: str
    name: str
    description: str
    status: StrategyStatus = StrategyStatus.ACTIVE
    metrics: StrategyMetrics = field(default_factory=lambda: StrategyMetrics(""))
    capital_allocated: float = 0.0
    capital_requested: float = 0.0
    performance_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class StrategyMarketplace:
    """Internal marketplace for trading strategies"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Strategy registry
        self.strategies: Dict[str, StrategyListing] = {}
        self.strategy_history = deque(maxlen=1000)
        
        # Capital management
        self.total_capital = self.config.get('total_capital', 100000)
        self.allocated_capital = 0.0
        self.capital_history = deque(maxlen=100)
        
        # Auction settings
        self.auction_interval = self.config.get('auction_interval', 3600)  # 1 hour
        self.min_performance_score = self.config.get('min_performance_score', 0.5)
        self.capital_reallocation_threshold = self.config.get('reallocation_threshold', 0.1)
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        
        logger.info("Strategy Marketplace initialized")
    
    async def register_strategy(self, strategy: StrategyListing) -> bool:
        """Register a new strategy in the marketplace"""
        logger.info(f"Registering strategy: {strategy.strategy_id}")
        
        if strategy.strategy_id in self.strategies:
            logger.warning(f"Strategy already registered: {strategy.strategy_id}")
            return False
        
        self.strategies[strategy.strategy_id] = strategy
        self.strategy_history.append(strategy)
        
        logger.info(f"Strategy registered: {strategy.strategy_id}")
        return True
    
    async def update_strategy_metrics(self, strategy_id: str, metrics: StrategyMetrics) -> bool:
        """Update strategy performance metrics"""
        if strategy_id not in self.strategies:
            logger.warning(f"Strategy not found: {strategy_id}")
            return False
        
        strategy = self.strategies[strategy_id]
        strategy.metrics = metrics
        strategy.updated_at = datetime.now()
        
        # Recalculate performance score
        strategy.performance_score = self._calculate_performance_score(metrics)
        
        self.performance_history.append({
            'strategy_id': strategy_id,
            'score': strategy.performance_score,
            'timestamp': datetime.now()
        })
        
        logger.info(f"Updated metrics for strategy: {strategy_id} (score: {strategy.performance_score:.2f})")
        return True
    
    def _calculate_performance_score(self, metrics: StrategyMetrics) -> float:
        """Calculate composite performance score"""
        # Weighted scoring
        score = (
            (metrics.sharpe_ratio / 3.0) * 0.4 +  # Sharpe ratio weight
            (metrics.win_rate) * 0.3 +             # Win rate weight
            (1 - min(metrics.max_drawdown / 50, 1)) * 0.2 +  # Drawdown weight
            (min(metrics.profit_factor / 2.0, 1)) * 0.1      # Profit factor weight
        )
        
        return max(0, min(1, score))  # Normalize to 0-1
    
    async def run_auction(self) -> Dict[str, float]:
        """Run marketplace auction to allocate capital"""
        logger.info("Running marketplace auction...")
        
        # Get active strategies sorted by performance
        active_strategies = [
            s for s in self.strategies.values()
            if s.status == StrategyStatus.ACTIVE and s.performance_score > self.min_performance_score
        ]
        
        if not active_strategies:
            logger.warning("No eligible strategies for auction")
            return {}
        
        # Sort by performance score (highest first)
        active_strategies.sort(key=lambda s: s.performance_score, reverse=True)
        
        # Allocate capital based on performance
        capital_allocation = {}
        available_capital = self.total_capital
        
        for i, strategy in enumerate(active_strategies):
            # Top performers get more capital
            if i == 0:
                allocation_ratio = 0.4  # Top strategy gets 40%
            elif i == 1:
                allocation_ratio = 0.3  # Second gets 30%
            elif i == 2:
                allocation_ratio = 0.2  # Third gets 20%
            else:
                allocation_ratio = 0.1 / max(1, len(active_strategies) - 3)  # Rest share 10%
            
            allocated = available_capital * allocation_ratio
            capital_allocation[strategy.strategy_id] = allocated
            strategy.capital_allocated = allocated
            available_capital -= allocated
        
        self.allocated_capital = self.total_capital - available_capital
        self.capital_history.append({
            'timestamp': datetime.now(),
            'total_allocated': self.allocated_capital,
            'allocations': capital_allocation
        })
        
        logger.info(f"Auction completed. Allocated: ${self.allocated_capital:.2f}")
        return capital_allocation
    
    async def get_best_strategy(self) -> Optional[StrategyListing]:
        """Get the best performing strategy"""
        active_strategies = [
            s for s in self.strategies.values()
            if s.status == StrategyStatus.ACTIVE
        ]
        
        if not active_strategies:
            return None
        
        best = max(active_strategies, key=lambda s: s.performance_score)
        return best
    
    async def get_top_strategies(self, count: int = 5) -> List[StrategyListing]:
        """Get top N strategies by performance"""
        active_strategies = [
            s for s in self.strategies.values()
            if s.status == StrategyStatus.ACTIVE
        ]
        
        active_strategies.sort(key=lambda s: s.performance_score, reverse=True)
        return active_strategies[:count]
    
    async def suspend_strategy(self, strategy_id: str, reason: str = "") -> bool:
        """Suspend a strategy"""
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        strategy.status = StrategyStatus.SUSPENDED
        strategy.capital_allocated = 0.0
        
        logger.warning(f"Strategy suspended: {strategy_id} - {reason}")
        return True
    
    async def reactivate_strategy(self, strategy_id: str) -> bool:
        """Reactivate a suspended strategy"""
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        if strategy.status == StrategyStatus.SUSPENDED:
            strategy.status = StrategyStatus.ACTIVE
            logger.info(f"Strategy reactivated: {strategy_id}")
            return True
        
        return False
    
    async def get_marketplace_summary(self) -> Dict[str, Any]:
        """Get marketplace summary"""
        active_count = sum(1 for s in self.strategies.values() if s.status == StrategyStatus.ACTIVE)
        suspended_count = sum(1 for s in self.strategies.values() if s.status == StrategyStatus.SUSPENDED)
        
        top_strategies = await self.get_top_strategies(5)
        
        return {
            "total_strategies": len(self.strategies),
            "active_strategies": active_count,
            "suspended_strategies": suspended_count,
            "total_capital": self.total_capital,
            "allocated_capital": self.allocated_capital,
            "available_capital": self.total_capital - self.allocated_capital,
            "top_strategies": [
                {
                    "id": s.strategy_id,
                    "name": s.name,
                    "performance_score": s.performance_score,
                    "capital_allocated": s.capital_allocated
                }
                for s in top_strategies
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_strategy_rankings(self) -> List[Dict[str, Any]]:
        """Get all strategies ranked by performance"""
        active_strategies = [
            s for s in self.strategies.values()
            if s.status == StrategyStatus.ACTIVE
        ]
        
        active_strategies.sort(key=lambda s: s.performance_score, reverse=True)
        
        rankings = []
        for rank, strategy in enumerate(active_strategies, 1):
            rankings.append({
                "rank": rank,
                "strategy_id": strategy.strategy_id,
                "name": strategy.name,
                "agent_id": strategy.agent_id,
                "performance_score": strategy.performance_score,
                "capital_allocated": strategy.capital_allocated,
                "returns": strategy.metrics.returns,
                "sharpe_ratio": strategy.metrics.sharpe_ratio,
                "win_rate": strategy.metrics.win_rate
            })
        
        return rankings


# Singleton instance
_strategy_marketplace = None


def get_strategy_marketplace(config: Optional[Dict] = None) -> StrategyMarketplace:
    """Get or create singleton marketplace"""
    global _strategy_marketplace
    if _strategy_marketplace is None:
        _strategy_marketplace = StrategyMarketplace(config)
    return _strategy_marketplace
